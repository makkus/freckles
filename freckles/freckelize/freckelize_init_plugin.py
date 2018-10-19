from __future__ import absolute_import, division, print_function

import logging
import os
import sys
from collections import OrderedDict
from copy import deepcopy

import click
from ruamel.yaml import YAML

import frkl
from freckles.defaults import DEFAULT_FRECKLES_JINJA_ENV
from freckles.exceptions import FrecklesConfigException
from freckles.frecklecutable import Frecklecutable
from freckles.freckles_runner import (
    FrecklesRunner,
    FrecklesRunConfig,
    print_no_run_info,
)
from frutils import (
    add_key_to_dict,
    dict_merge,
    replace_strings_in_obj,
    is_url_or_abbrev,
    DEFAULT_URL_ABBREVIATIONS_REPO,
)
from frkl.utils import expand_string_to_git_details

yaml = YAML(typ="safe")

log = logging.getLogger("freckles")

FRECKLE_PROFILE_FORMAT = {
    "child_marker": "profiles",
    "default_leaf": "profile",
    "default_leaf_key": "name",
    "key_move_map": {"*": "vars"},
}
FRECKLE_PROFILE_CHAIN = [frkl.FrklProcessor(**FRECKLE_PROFILE_FORMAT)]


def process_copy_folders(copy_folders):

    result = []

    for cf in copy_folders:
        f = process_copy_folder(cf[0], cf[1])
        result.append(f)

    return result


def process_copy_folder(src, dest):

    if is_url_or_abbrev(dest):
        raise FrecklesConfigException("Destination is url or abbrev: {}".format(dest))

    result = {"src": src, "dest": dest}

    if is_url_or_abbrev(src):
        git_details = expand_string_to_git_details(
            src, default_abbrevs=DEFAULT_URL_ABBREVIATIONS_REPO
        )
        result["git"] = git_details
        result["src_type"] = "git"
    else:
        if not os.path.exists(src):
            raise FrecklesConfigException("Local path '{}' does not exist.".format(src))
        else:
            result["src_type"] = "local"

    return result


def read_metadata(result_string):
    try:
        result = yaml.load(result_string["stdout"])
    except (Exception) as e:
        raise Exception("Error trying to parse freckle metadata: {}".format(e))

    can_pwless_sudo = result.pop("can_passwordless_sudo")
    if can_pwless_sudo == 1 or can_pwless_sudo == 127:
        result["can_passwordless_sudo"] = False
    elif can_pwless_sudo == 0:
        result["can_passwordless_sudo"] = True
    else:
        raise Exception(
            "Invalid value for 'can_passwordless_sudo' key: {}".format(can_pwless_sudo)
        )

    git_xcode = result.pop("git_xcode")
    if git_xcode == 1:
        result["git_on_mac_available"] = True
    elif git_xcode == 0:
        result["git_on_mac_available"] = False
    else:
        raise Exception("Invalid value for 'git_xcode' key: {}".format(can_pwless_sudo))

    path = result.pop("path")
    result["path"] = path.split(":")

    freckle_files_dict = result.pop("freckle_files")
    dirs = {}
    for parent_path, f_files_dict in freckle_files_dict.items():
        freckle_files_invalid = {}
        freckle_files = {}
        for path, content in f_files_dict.items():
            if not content:
                freckle_files[path] = {}
                continue
            try:
                if "{{" in content or "{%" in content:
                    raise Exception(
                        "Metadata contains template string, this is not allowed."
                    )
                c = yaml.load(content)
                freckle_files[path] = c
            except (Exception) as e:
                log.warn("Ignoring metadata file '{}': {}".format(path, e))
                freckle_files_invalid[path] = {"content": content, "exception": e}

        dirs[parent_path] = {}
        dirs[parent_path]["freckle_files"] = freckle_files
        dirs[parent_path]["freckle_files_invalid"] = freckle_files_invalid
    result["freckle_files"] = dirs
    # executables = result.pop("executables")
    # temp = {}
    # for name, paths in executables.items():
    #     p = paths.split(":")
    #     p.remove("")
    #     temp[name] = list(set(p))
    # result["executables"] = temp

    # folders = result.pop("directories")
    # temp = {}
    # for name, paths in folders.items():
    #     p = paths.split("\n")

    return result


def assembly_profile_metadata(freckle_files, dir_metadata):

    folder_list = []
    extra_vars = {}
    for path, f_files in freckle_files.items():

        freckle_files = f_files["freckle_files"]
        # invalid_freckle_files = f_files["freckle_files_invalid"]

        for path, md in freckle_files.items():

            if not os.path.basename(path).startswith("."):
                log.debug(
                    "Ignoring freckle file '{}': doesn't start with a '.'".format(path)
                )
                continue

            if os.path.basename(path) != ".freckle":
                extra_vars[path] = md
                continue

            # frklizing profile list
            f = frkl.Frkl([md], FRECKLE_PROFILE_CHAIN)
            temp = f.process()
            for p in temp:
                p["profile"]["path"] = path
                p["profile"]["parent_path"] = os.path.dirname(path)
            folder_list.extend(temp)

    profile_list = []
    for folder in folder_list:

        profile = folder["profile"]["name"]
        parent_path = folder["profile"]["parent_path"]
        path = folder["profile"]["path"]

        if profile not in profile_list:
            profile_list.append(profile)

        parent = folder["profile"]["parent_path"]
        for p, md in extra_vars.items():

            if not p.startswith(parent):
                continue

            file_name = os.path.basename(p)[1:-8]
            rel = os.path.relpath(p, parent)

            dir = os.path.dirname(rel)

            if not md:
                if file_name.startswith("no_") or rel.startswith("no-"):
                    var_name = file_name[3:]
                    value = False
                else:
                    var_name = file_name
                    value = True
            else:
                var_name = file_name
                value = md

            key_path = os.path.join(dir, var_name)
            ed = {}
            add_key_to_dict(ed, key_path, value, split_token=os.path.sep, ordered=False)

            dict_merge(folder.setdefault("extra_vars", {}), ed, copy_dct=False)

        folder_files = []
        for parent, files in dir_metadata.items():

            if parent not in path:
                # wrong path tree
                continue

            for f in files:
                if parent_path in f:
                    folder_files.append(f)

        folder["files"] = folder_files

    return (profile_list, folder_list)


def check_valid_args(arg_list):

    for arg in arg_list:

        name = arg.name
        if name in [
            "freckle",
            "f",
            "profile_help",
            "copy_freckle",
            "c",
            "ignore_unsupported_profiles",
            "i",
        ]:
            raise Exception("Conflicting argument var name: {}".format(name))
        for opt in arg.opts:
            if opt in [
                "--freckle",
                "-f",
                "--profile-help",
                "--copy-freckle",
                "-c",
                "--ignore-unsupported-profiles",
                "-i",
            ]:
                raise Exception(
                    "Conflicting argument name '{}' for var '{}'".format(opt, name)
                )

    return True


@click.command(
    "init", context_settings=dict(ignore_unknown_options=True, allow_extra_args=True)
)
@click.option(
    "--freckle",
    "-f",
    multiple=True,
    help="a (base) folder to process",
    metavar="FRECKLE_FOLDER_PATH",
)
@click.option(
    "--copy-freckle",
    "-c",
    help="before starting to process the freckle folder(s), copy/update this folder/url, the target folder will be added as a freckle folder automatically",
    type=(str, str),
    metavar="SOURCE TARGET_FOLDER",
    required=False,
    nargs=2,
    multiple=True,
    default=[],
)
@click.option(
    "--ignore-unsupported-profiles",
    "-i",
    is_flag=True,
    required=False,
    help="ignore profiles for which there isn't an adapter frecklet",
)
@click.option(
    "--profile-help",
    help="Show freckle folder specific help, this will do change the target system by copying all specified source/target pairs.",
    is_flag=True,
)
@click.option("--help", help="Show this message and exit.", is_flag=True)
@click.pass_context
def init_freckle(
    ctx, copy_freckle, freckle, ignore_unsupported_profiles, help, profile_help
):
    """Setup a new project from a folder, repo or archive."""

    if not freckle and not copy_freckle:

        if help:
            click.echo(ctx.command.get_help(ctx))
        else:
            click.echo("No folders specified, doing nothing...")
        sys.exit()

    context = ctx.obj["context"]
    control_dict = ctx.obj["control_dict"]
    freckelize_extra_vars = ctx.obj["freckelize_extra_vars"]

    control_dict_temp = deepcopy(control_dict)
    control_dict_temp["output"] = "minimal"
    control_dict_temp["no_run"] = False
    control_dict_temp["elevated"] = False
    control_dict_temp["minimal_facts_only"] = True

    frecklecutable = Frecklecutable.create_from_file_or_name(
        "freckelize-init", context=context
    )
    runner = FrecklesRunner(context)
    runner.set_frecklecutable(frecklecutable)

    if copy_freckle and help:

        click.echo()
        click.echo(ctx.command.get_help(ctx))
        click.echo()
        click.secho("Note:", bold=True)
        click.echo()
        click.echo(
            "'--help' specified in combination with '--copy'. This won't display profile-specific argument help as it would require potentially changing the target filesystem."
        )
        click.echo("If you are ok with this, use the '--profile-help' option instead.")
        click.echo()
        sys.exit()

    if freckle:
        all_freckle_folders = list(deepcopy(freckle))
    else:
        all_freckle_folders = []
        for src, target in copy_freckle:

            if target not in all_freckle_folders:
                all_freckle_folders.append(target)

    # TODO: remove duplicate childs

    click.echo("\nGetting folder information...\n")
    run_config = FrecklesRunConfig(context, control_dict_temp)

    copy_folders = process_copy_folders(copy_freckle)

    results = runner.run(
        run_config=run_config,
        user_input={
            "force_copy": True,
            "folders": all_freckle_folders,
            "copy_folders": copy_folders,
        },
    )

    rc = results[0]["run_properties"]["return_code"]

    if rc != 0:
        click.echo("\nError: freckelize pre-processing step failed. Exiting...")
        sys.exit(rc)

    folder_facts_raw = results[0]["result"]["freckle_folder_facts_raw"]
    try:
        result = read_metadata(folder_facts_raw)
        freckle_metadata = result["freckle_files"]
        dir_metadata = result["directories"]
    except (Exception) as e:
        log.debug("===============================================")
        log.debug("Raw metadata:")
        log.debug(folder_facts_raw)
        log.debug("===============================================")
        log.debug("Error processing freckle folder", exc_info=1)
        log.debug("===============================================")
        click.echo(
            "Failed to parse remote freckle folder metadata. Unfortunately it's hard to say which folder/file the culprit was, use the '--verbosity DEBUG' option for more details"
        )
        click.echo("Error: {}".format(e))
        sys.exit(1)
    profile_list, folder_list = assembly_profile_metadata(
        freckle_metadata, dir_metadata
    )

    if not profile_list:
        click.echo("")
        click.echo("No freckle folders found, doing nothing...")
        sys.exit()

    all_frecklet_names = context.get_frecklet_names()

    profiles = {}

    for profile in profile_list:

        if profile not in all_frecklet_names:
            if ignore_unsupported_profiles:
                continue
            else:
                click.echo(
                    "Can't freckelize using specified folder(s), no frecklet for profile '{}' available.".format(
                        profile
                    )
                )
                # TODO: link to explanation
                sys.exit()

        frecklet = context.create_frecklet(profile)

        can_freckelize = frecklet.meta.get("freckelize", None)
        try:
            if can_freckelize is None:
                if ignore_unsupported_profiles:
                    continue
                else:
                    raise FrecklesConfigException(
                        "Frecklet found for profile '{}', but it isn't freckelize-enabled: {}".format(
                            profile, frecklet.get_urls()
                        )
                    )

            handles_multiple_folders = frecklet.meta["freckelize"].get(
                "handles_multiple_fodlers", False
            )
            if handles_multiple_folders:
                raise FrecklesConfigException(
                    "Multi-folder adapters not supported yet."
                )

            var_map = frecklet.meta["freckelize"].get("var_map", {})
            profiles[profile] = var_map
        except (FrecklesConfigException) as e:
            click.echo()
            click.echo(e)
            sys.exit(1)
    #
    tasklist = []
    # all_vars = {}
    for folder in folder_list:

        profile = folder["profile"]["name"]
        if profile not in profiles.keys():
            log.debug(
                "Ignoring folder '{}', not a supported profile ({}).".format(
                    folder["profile"]["path"], profile
                )
            )
            continue

        folder_vars = folder.get("vars", {})

        repl_dict = {
            "path": os.path.dirname(folder["profile"]["path"]),
            "vars": folder_vars,
            "extra_vars": folder.get("extra_vars", {}),
            "files": folder.get("files", []),
            "action": "init",
        }

        replaced = replace_strings_in_obj(
            profiles[profile],
            replacement_dict=repl_dict,
            jinja_env=DEFAULT_FRECKLES_JINJA_ENV,
        )

        merged_folder_vars = dict_merge(folder_vars, freckelize_extra_vars, copy_dct=True)
        final_vars = dict_merge(merged_folder_vars, replaced, copy_dct=True)

        tasklist.append({profile: final_vars})
        # dict_merge(all_vars, replaced, copy_dct=False)

    click.echo()
    if ignore_unsupported_profiles:
        click.echo("(Valid) profiles found:")
    else:
        click.echo("Profiles found:")

    click.echo()

    # getting folder profile dict
    folder_map = OrderedDict()
    for f in folder_list:
        profile_name = f["profile"]["name"]
        folder_path = f["profile"]["path"]
        folder_map.setdefault(profile_name, []).append(folder_path)

    no_profiles = True
    for profile, paths in folder_map.items():
        if profile not in profiles.keys():
            continue
        no_profiles = False
        click.echo("  * {}:".format(profile))
        for p in paths:
            click.echo("     - {}".format(os.path.dirname(p)))

    if no_profiles:
        click.echo("  * none")
        click.echo()
        click.echo("Invalid profiles found:\n")
        for profile, paths in folder_map.items():
            click.echo("  * {}:".format(profile))
            for p in paths:
                click.echo("     - {}".format(os.path.dirname(p)))
        click.echo()

        click.echo("Nothing to do, exiting...")
        sys.exit()
    # for p in profiles.keys():
    #     click.echo("  - {}".format(p))

    frecklet_metadata = {"tasks": tasklist}
    frecklet = context.create_frecklet(frecklet_metadata)
    frecklecutable = Frecklecutable("freckelize-profiles", frecklet, context=context)

    arg_list = frecklecutable.generate_click_parameters()
    try:
        check_valid_args(arg_list)
    except (Exception) as e:
        click.echo(
            "Argument definition error, one of the involved frecklets contains reserved arg/parameter names."
        )
        click.echo("{}".format(e.message))
        # TODO: provide link to explanation
        click.echo("Exiting...")

        sys.exit()

    pars = ctx.command.params + arg_list

    @click.command("init")
    def dummy(*args, **kwargs):

        runner.set_frecklecutable(frecklecutable)
        run_config = FrecklesRunConfig(context, control_dict)
        click.echo()
        try:
            results = runner.run(run_config=run_config, user_input=kwargs)
        except (Exception) as e:
            log.debug(e, exc_info=1)
            click.echo()
            click.echo("error: {}".format(e))
            sys.exit(1)

        if run_config.get_config_value("no_run"):
            print_no_run_info(results)
            sys.exit()

        # import pp
        #
        # pp(results)

    dummy.params = pars

    if help or profile_help:
        click.echo(dummy.get_help(ctx))
        sys.exit()

    new_ctx = dummy.make_context("init", ctx.args, ctx.parent)
    dummy.invoke(new_ctx)


@click.command("update")
def update_freckle():

    pass


# @init_freckle.command("describe")
# @click.pass_context
# def describe_frecklecutable(ctx):
#
#     context = ctx.obj["context"]
#     control_dict = {
#         "no_run": True,
#         "host": "localhost",
#         "output": "default",
#         "elevated": "not_elevated",
#     }
#
#     print("XXXX")
