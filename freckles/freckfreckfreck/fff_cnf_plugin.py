from __future__ import absolute_import, division, print_function

import os
import sys

import click
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from freckles.defaults import FRECKLES_CONFIG_PROFILES_DIR, FRECKLES_CNF_PROFILES
from frutils import readable, unsorted_to_sorted_dict, dict_merge
from frutils.frutils_cli import output

yaml = YAML(typ="safe")


@click.group()
@click.pass_context
def cnf(ctx):
    """command-group for config-related tasks"""

    # context = ctx.obj["context"]
    # control_dict = ctx.obj["control_dict"]

    # context.set_control_vars(control_vars=control_dict)


@cnf.command("show", short_help="print current configuration")
@click.option(
    "--full", "-f", help="display all keys, including default values", is_flag=True
)
@click.option("--show-interpreters", "-i", help="show interpreted data", is_flag=True)
@click.option(
    "--limit-interpreters",
    "-l",
    help="only display interpreter data for interpreters that contain this string",
)
@click.pass_context
def show_current(ctx, full, show_interpreters, limit_interpreters):
    """Print the current configuration, including documentation (optional).

    This will print the global configuration key/value pairs, as well as the interpreted ones for each added
    configuration interperter.
    """
    output_format = "yaml"

    context = ctx.obj["context"]
    cnf = context.cnf

    config_values = cnf.config_dict
    indent = 0
    if show_interpreters:
        indent = 2
    config_values_string = readable(
        unsorted_to_sorted_dict(config_values), out=output_format, indent=indent
    )

    click.echo()
    if show_interpreters:
        click.secho("Configuration", bold=True)
        click.secho("-------------", bold=True)
        click.echo()

    click.echo(config_values_string)
    click.echo()

    if not show_interpreters:
        sys.exit()

    click.secho("Interpreters", bold=True)
    click.secho("------------", bold=True)
    click.echo()

    for c_name, interpreter_details in context.get_interpreter_map().items():

        interpreter = interpreter_details["interpreter"]
        i_type = interpreter_details["type"]

        if limit_interpreters and limit_interpreters not in c_name:
            continue

        if i_type == "connector":
            title = "Connector: {}".format(c_name)
        else:
            title = c_name
        click.secho("  {}".format(title), bold=True)
        click.echo()

        validated = interpreter.get_validated_cnf()

        if not validated:
            click.echo("    No configuration schema.")
            click.echo()
            continue

        if not full:
            validated_string = readable(
                unsorted_to_sorted_dict(validated), out=output_format, indent=4
            )
            click.echo(validated_string)
        else:
            details = CommentedMap()

            for k, schema in sorted(interpreter.get_schema().items()):
                v = validated.get(k, None)
                full = interpreter.get_doc_for_key(k)
                short_help = full.get_short_help()
                details[k] = CommentedMap()
                details[k]["desc"] = short_help
                if v is None:
                    v = "n/a"
                details[k]["current value"] = v
                details[k]["default"] = schema.get("default", "n/a")
            for k, v in details.items():
                click.secho("    {}:".format(k), bold=True)
                temp = readable(v, out=output_format, indent=6)
                click.echo(temp.rstrip())
        click.echo()

    # click.echo()


@cnf.command("doc", short_help="display documentation for config keys")
@click.option(
    "--limit-interpreters",
    "-l",
    help="only display interpreter data for interpreters that contain this string",
)
@click.argument("key", required=False, nargs=-1)
@click.pass_context
def config_doc(ctx, key, limit_interpreters):
    """
    Displays documentation for configuration keys.
    """

    # output_format = "yaml"
    context = ctx.obj["context"]
    cnf = context.cnf

    click.echo()

    for c_name, interpreter_details in context.get_interpreter_map().items():
        if limit_interpreters and limit_interpreters not in c_name:
            continue

        interpreter = interpreter_details["interpreter"]
        # interpreter_type = interpreter_details["type"]

        click.secho("{}".format(c_name), bold=True)
        click.echo()
        schema = interpreter.get_schema()

        if not key:

            if not schema:
                click.echo("  No config schema")
                continue

            for c_key in sorted(interpreter.get_keys()):
                doc = interpreter.get_doc_for_key(c_key)
                click.secho(" {} ".format(c_key), bold=True, nl=False)
                key_schema = interpreter.get_schema_for_key(c_key)
                value_type = key_schema.get("type", "unknown_type")
                click.echo("({})".format(value_type))
                click.echo("    {}".format(doc.get_short_help()))
        else:
            for doc_key in key:
                doc = interpreter.get_doc_for_key(doc_key)
                click.secho(" {} ".format(doc_key), bold=True, nl=False)
                if not schema or doc is None:
                    click.echo("not used")
                else:

                    if doc_key in interpreter.keymap.values():
                        # temp = []
                        # for k, v in interpreter.keymap.items():
                        #     if v == key:
                        #         temp.append(k)
                        # click.echo("not used, but alias for: {}".format(", ".join(temp)))
                        click.echo("not used")
                        continue

                    key_schema = interpreter.get_schema_for_key(doc_key)
                    value_type = key_schema.get("type", "unknown_type")
                    click.echo("({})".format(value_type))
                    click.echo()
                    click.secho("    desc: ", bold=True, nl=False)
                    click.echo("{}".format(doc.get_short_help()))
                    click.secho("    default: ", bold=True, nl=False)
                    default = key_schema.get("default", "n/a")
                    click.echo(default)
                    current = cnf.get_value(c_name, doc_key, default="n/a")
                    click.secho("    current: ", bold=True, nl=False)
                    click.echo(current)
                click.echo()

        click.echo()


@cnf.command("copy", short_help="copy current configuration to new profile")
@click.argument("profile_name", nargs=1)
@click.option(
    "--edit",
    "-e",
    is_flag=True,
    default=False,
    help="open new profile in editor after copying",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="overwrite profile if already exists",
)
@click.pass_context
def copy(ctx, profile_name, edit, force):
    """Copies the current configuration into a new profile.
    """

    cnf = ctx.obj["context"].cnf

    target = os.path.join(
        FRECKLES_CONFIG_PROFILES_DIR, "{}.profile".format(profile_name)
    )
    try:
        cnf.save_current(target, force=force)
    except (Exception) as e:
        click.echo(e)
        sys.exit()

    if edit:
        click.edit(filename=target)


@cnf.command("list", short_help="list available configuration profiles")
@click.option(
    "--details", "-d", help="print content of profiles", is_flag=True, default=False
)
@click.option(
    "--no-merge",
    "-n",
    help="only display 'raw' profile data, don't merge with 'default' profile",
    is_flag=True,
)
@click.pass_context
def list_profiles(ctx, details, no_merge):
    """Lists configuration profiles.

    Lists default as well as user profiles (located in ~/.config/freckles/ or ~/.freckles).
    """

    click.echo()

    files = os.listdir(FRECKLES_CONFIG_PROFILES_DIR)
    profile_files = [x for x in files if x.endswith(".profile")]

    profiles = CommentedMap()
    for pf in profile_files:
        p_name = os.path.splitext(pf)[0]
        pfile = os.path.join(FRECKLES_CONFIG_PROFILES_DIR, pf)
        with open(pfile, "r") as f:
            content = yaml.load(f)
            profiles[p_name] = content

    default_profile = profiles.pop("default", FRECKLES_CNF_PROFILES["default"])
    default_profile = CommentedMap(sorted(default_profile.items(), key=lambda x: x[0]))

    if not details:
        click.echo("default")
    else:
        click.secho("default", bold=True)
        click.echo()
        output(default_profile, output_type="yaml", indent=2)

    for p_name in sorted(profiles.keys()):

        if not details:
            click.echo(p_name)
        else:
            click.secho(p_name, bold=True)
            click.echo()
            if no_merge:
                content = profiles[p_name]
            else:
                content = dict_merge(default_profile, profiles[p_name], copy_dct=True)
            content = CommentedMap(sorted(content.items(), key=lambda x: x[0]))
            output(content, output_type="yaml", indent=2)


@cnf.command("delete", short_help="delete configuration profile")
@click.argument("profile_name", metavar="PROFILE_NAME", nargs=1)
@click.pass_context
def delete_profile(ctx, profile_name):
    """Deletes a configuration profile.

    Deletes a configuration profile with the specified name in $HOME/.config/freckles (or $HOME/.freckles)
    """

    file = os.path.join(FRECKLES_CONFIG_PROFILES_DIR, "{}.profile".format(profile_name))

    if os.path.exists(file):
        os.remove(file)


@cnf.command("edit", short_help="edit a configuration profile")
@click.argument("profile_name", metavar="PROFILE_NAME", nargs=1)
@click.pass_context
def edit_profile(ctx, profile_name):
    """Edits a configuration profile with the default editor.

    """

    path = os.path.join(FRECKLES_CONFIG_PROFILES_DIR, "{}.profile".format(profile_name))
    click.edit(filename=path)
