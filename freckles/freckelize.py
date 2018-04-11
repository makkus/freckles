# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
import os
import sys
import json
import click
import click_completion
import click_log
import copy
import fnmatch
import nsbl
from nsbl.output import print_title
import shutil
import yaml
from collections import OrderedDict
from six import string_types
from pprint import pprint, pformat
from frkl import frkl
from luci import Lucifier, DictletReader, DictletFinder, vars_file, TextFileDictletReader, parse_args_dict, output, JINJA_DELIMITER_PROFILES, replace_string, ordered_load, clean_user_input, readable_json, readable_yaml
from . import print_version
from .freckles_defaults import *
from .utils import DEFAULT_FRECKLES_CONFIG, download_extra_repos, HostType, print_repos_expand, expand_repos,  create_and_run_nsbl_runner, freckles_jinja_extensions, download_repos, RepoType
from .freckles_base_cli import FrecklesBaseCommand, FrecklesLucifier
from .freckle_detect import create_freckle_descs

log = logging.getLogger("freckles")
click_log.basic_config(log)

# optional shell completion
click_completion.init()

# TODO: this is a bit ugly, probably have refactor how role repos are used
nsbl.defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")

VARS_HELP = "variables to be used for templating, can be overridden by cli options if applicable"
DEFAULTS_HELP = "default variables, can be used instead (or in addition) to user input via command-line parameters"
KEEP_METADATA_HELP = "keep metadata in result directory, mostly useful for debugging"
FRECKELIZE_EPILOG_TEXT = "frecklecute is free and open source software and part of the 'freckles' project, for more information visit: https://docs.freckles.io"

FRECKLE_ARG_HELP = "the url or path to the freckle(s) to use, if specified here, before any commands, all profiles will be applied to it"
FRECKLE_ARG_METAVAR = "URL_OR_PATH"
TARGET_ARG_HELP = 'target folder for freckle checkouts (if remote url provided), defaults to folder \'freckles\' in users home'
TARGET_ARG_METAVAR = "PATH"
TARGET_NAME_ARG_HELP = "target name for freckle checkouts (if remote url provided), can not be used when multiple freckle folders are specified"
TARGET_NAME_ARG_METAVAR = "FOLDER_NAME"
INCLUDE_ARG_HELP = 'if specified, only process folders that end with one of the specified strings, only applicable for multi-freckle folders'
INCLUDE_ARG_METAVAR = 'FILTER_STRING'
EXCLUDE_ARG_HELP = 'if specified, omit process folders that end with one of the specified strings, takes precedence over the include option if in doubt, only applicable for multi-freckle folders'
EXCLUDE_ARG_METAVAR = 'FILTER_STRING'
ASK_PW_HELP = 'whether to force ask for a password, force ask not to, or let freckles decide (which might not always work)'
ASK_PW_CHOICES = click.Choice(["auto", "true", "false"])
NON_RECURSIVE_HELP = "whether to exclude all freckle child folders, default: false"

ADAPTER_CACHE = {}
def find_freckelize_adapters(path):
    """Helper method to find freckelize adapters.

    Adapter files are named in the format: <adapter_name>.adapter.freckle

    Args:
      path (str): the root path (usually the path to a 'trusted repo').
    Returns:
      list: a list of valid freckelize adapters under this path
    """

    log.debug("Finding adapters in: {}".format(path))
    if not os.path.exists(path) or not os.path.isdir(os.path.realpath(path)):
        return {}

    if path in ADAPTER_CACHE.keys():
        return ADAPTER_CACHE[path]

    result = {}
    try:
        for root, dirnames, filenames in os.walk(os.path.realpath(path), topdown=True, followlinks=True):

            dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]

            for filename in fnmatch.filter(filenames, "*.{}".format(ADAPTER_MARKER_EXTENSION)):
                adapter_metadata_file = os.path.realpath(os.path.join(root, filename))
                # adapter_folder = os.path.abspath(os.path.dirname(adapter_metadata_file))
                # profile_name = ".".join(os.path.basename(adapter_metadata_file).split(".")[1:2])

                profile_name = os.path.basename(adapter_metadata_file).split(".")[0]

                result[profile_name] = {"path": adapter_metadata_file, "type": "file"}

    except (UnicodeDecodeError) as e:
        click.echo(" X one or more filenames in '{}' can't be decoded, ignoring. This can cause problems later. ".format(root))

    ADAPTER_CACHE[path] = result

    return result

class FreckelizeAdapterFinder(DictletFinder):
    """Finder class for freckelize adapters.


    """

    def __init__(self, paths, **kwargs):

        super(FreckelizeAdapterFinder, self).__init__(**kwargs)
        self.paths = paths
        self.adapter_cache = None
        self.path_cache = {}

    def get_all_dictlet_names(self):

        return self.get_all_dictlets().keys()

    def get_all_dictlets(self):
        """Find all freckelize adapters."""

        log.debug("Retrieving all dictlets")

        if self.adapter_cache is None:
            self.adapter_cache = {}
        dictlet_names = OrderedDict()

        all_adapters = OrderedDict()
        for path in self.paths:
            if path not in self.path_cache.keys():

                adapters = find_freckelize_adapters(path)
                self.path_cache[path] = adapters
                frkl.dict_merge(all_adapters, adapters, copy_dct=False)
                frkl.dict_merge(self.adapter_cache, adapters, copy_dct=False)

        return all_adapters

    def get_dictlet(self, name):

        log.debug("Retrieving adapter: {}".format(name))
        if self.adapter_cache is None:
            self.get_all_dictlet_names()

        dictlet = self.adapter_cache.get(name, None)

        if dictlet is None:
            return None
        else:
            return dictlet

class FreckelizeAdapterReader(TextFileDictletReader):
    """Reads a text file and generates metadata for freckelize.

    The file needs to be in yaml format, if it contains a key 'args' the value of
    that is used to generate the freckelize command-line interface.
    The key 'defaults' is used for, well, default values.

    Read more about how the adapter file format: XXX

    Args:
      delimiter_profile (dict): a map describing the delimiter used for templating.
      **kwargs (dict): n/a
    """

    def __init__(self, delimiter_profile=JINJA_DELIMITER_PROFILES["luci"], **kwargs):

        super(FreckelizeAdapterReader, self).__init__(**kwargs)
        self.delimiter_profile = delimiter_profile
        self.tasks_keyword = FX_TASKS_KEY_NAME

    def process_lines(self, content, current_vars):

        log.debug("Processing content: {}".format(content))

        # now, I know this isn't really the most
        # optimal way of doing this,
        # but I don't really care that much about execution speed yet,
        # plus I really want to be able to use variables used in previous
        # lines of the content
        last_whitespaces = 0
        current_lines = ""
        temp_vars = copy.deepcopy(current_vars)

        for line in content:

            if line.strip().startswith("#"):
                continue

            whitespaces = len(line) - len(line.lstrip(' '))
            current_lines = "{}{}\n".format(current_lines, line)
            if whitespaces <= last_whitespaces:

                temp = replace_string(current_lines, temp_vars, **self.delimiter_profile)

                if not temp.strip():
                    continue

                temp_dict = ordered_load(temp)
                if temp_dict:
                    temp_vars = frkl.dict_merge(temp_vars, temp_dict, copy_dct=False)

            last_whitespaces = whitespaces

        if current_lines:
            temp = replace_string(current_lines, temp_vars, additional_jinja_extensions=freckles_jinja_extensions, **self.delimiter_profile)
            temp_dict = ordered_load(temp)
            temp_vars = frkl.dict_merge(temp_vars, temp_dict, copy_dct=False)

        frkl.dict_merge(current_vars, temp_vars, copy_dct=False)
        log.debug("Vars after processing:\n{}".format(readable_json(current_vars, indent=2)))

        return current_vars


class FreckelizeCommand(FrecklesBaseCommand):
    """Class to build the frecklecute command-line interface."""

    FRECKELIZE_ARGS = [(
        "freckle", {
            "required": False,
            "alias": "freckle",
            "doc": {
                "help": FRECKLE_ARG_HELP
            },
            "click": {
                "option": {
                    "multiple": True,
                    "param_decls": ["--freckle", "-f"],
                    "type": RepoType(),
                    "metavar": FRECKLE_ARG_METAVAR
                }
            }
        }),
        ("target_folder", {
            "alias": "target-folder",
            "required": False,
            # "default": "~/freckles",
            "type": str,
            "doc": {
                "help": TARGET_ARG_HELP
            },
            "click": {
                "option": {
                    "param_decls": ["--target-folder", "-t"],
                    "metavar": TARGET_ARG_METAVAR
                }
            }
        }),
        ("target_name", {
            "alias": "target-name",
            "required": False,
            "type": str,
            "doc": {
                "help": TARGET_NAME_ARG_HELP
            },
            "click": {
                "option": {
                    "metavar": TARGET_NAME_ARG_METAVAR
                }
            }
        }),
        ("include", {
            "alias": "include",
            "required": False,
            "doc": {
                "help": INCLUDE_ARG_HELP
            },
            "click": {
                "option": {
                    "param_decls": ["--include", "-i"],
                    "multiple": True,
                    "metavar": INCLUDE_ARG_METAVAR
                }
            }
        }),
        ("exclude", {
            "alias": "exclude",
            "required": False,
            "doc": {
                "help": EXCLUDE_ARG_HELP
            },
            "click": {
                "option": {
                    "param_decls": ["--exclude", "-e"],
                    "multiple": True,
                    "metavar": EXCLUDE_ARG_METAVAR
                }
            }
        }),
        ("ask_become_pass", {
            "alias": "ask-become-pass",
            "default": "auto",
            "doc": {
                "help": ASK_PW_HELP
            },
            "click": {
                "option": {
                    "param_decls": ["--ask-become-pass", "-pw"],
                    "type": ASK_PW_CHOICES
                }
            }
        }),
        ("non_recursive", {
            "alias": "non-recursive",
            "type": bool,
            "required": False,
            "default": False,
            "doc": {
                "help": NON_RECURSIVE_HELP
            },
            "click": {
                "option": {
                    "is_flag": True
                }
            }
        })
    ]

    @staticmethod
    def freckelize_extra_params():

        freckle_option = click.Option(param_decls=["--freckle", "-f"], required=False, multiple=True, type=RepoType(),
                                  metavar=FRECKLE_ARG_METAVAR, help=FRECKLE_ARG_HELP)
        target_option = click.Option(param_decls=["--target-folder", "-t"], required=False, multiple=False, type=str,
                                     metavar=TARGET_ARG_METAVAR,
                                     help=TARGET_ARG_HELP)
        target_name_option = click.Option(param_decls=["--target-name"], required=False, multiple=False, type=str,
                                     metavar=TARGET_NAME_ARG_METAVAR,
                                     help=TARGET_NAME_ARG_HELP)
        include_option = click.Option(param_decls=["--include", "-i"],
                                      help=INCLUDE_ARG_HELP,
                                      type=str, metavar=INCLUDE_ARG_METAVAR, default=[], multiple=True)
        exclude_option = click.Option(param_decls=["--exclude", "-e"],
                                      help=EXCLUDE_ARG_HELP,
                                      type=str, metavar=EXCLUDE_ARG_METAVAR, default=[], multiple=True)
        parent_only_option = click.Option(param_decls=["--non-recursive"],
                                          help=NON_RECURSIVE_HELP,
                                          is_flag=True,
                                          default=False,
                                          required=False,
                                          type=bool
        )

        params = [freckle_option, target_option, target_name_option, include_option, exclude_option,
                           parent_only_option]

        return params


    def __init__(self, **kwargs):

        extra_params = FreckelizeCommand.freckelize_extra_params()
        super(FreckelizeCommand, self).__init__(extra_params=extra_params, **kwargs)
        self.config = DEFAULT_FRECKLES_CONFIG
        self.reader = FreckelizeAdapterReader()
        self.finder = None

    def get_dictlet_finder(self):

        if self.finder is None:
            # need to wait for paths to be initialized
            self.finder =  FreckelizeAdapterFinder(self.paths)

        return self.finder

    def get_dictlet_reader(self):

        return self.reader

    def get_additional_args(self):

        return OrderedDict(FreckelizeCommand.FRECKELIZE_ARGS)

    def freckles_process(self, command_name, default_vars, extra_vars, user_input, metadata, dictlet_details, config, parent_params):

        return {"name": command_name, "default_vars": default_vars, "extra_vars": extra_vars, "user_input": user_input, "adapter_metadata": metadata, "adapter_details": dictlet_details}

def assemble_freckelize_run(*args, **kwargs):

    try:
        result = []
        no_run = kwargs.get("no_run")

        hosts = list(kwargs["host"])
        if not hosts:
            hosts = ["localhost"]

        default_target = kwargs.get("target_folder", None)

        default_target_name = kwargs.get("target_name", None)

        default_freckle_urls = list(kwargs.get("freckle", []))
        default_output_format = kwargs.get("output", "default")

        default_include = list(kwargs.get("include", []))
        default_exclude = list(kwargs.get("exclude", []))

        default_ask_become_pass = kwargs.get("ask_become_pass", None)

        # default_extra_vars_raw = list(kwargs.get("extra_vars", []))

        default_non_recursive = kwargs.get("non_recursive", None)


        default_extra_vars = {}
        # for ev in default_extra_vars_raw:
            # dict_merge(default_extra_vars, ev, copy_dct=False)

        extra_profile_vars = {}
        repos = OrderedDict()
        profiles = []

        metadata = {}
        parent_command_vars = {}

        if default_target:
            parent_command_vars["target_folder"] = default_target
        if default_target_name:
            parent_command_vars["target_folder_name"] = default_target_name
        if default_include:
            parent_command_vars["includes"] = default_include
        if default_exclude:
            parent_command_vars["includes"] = default_include
        if default_ask_become_pass is not None:
            parent_command_vars["password"] = default_ask_become_pass
        if default_non_recursive is not None:
            parent_command_vars["non_recursive"] = default_non_recursive

        if not args[0]:
            # fill missing keys with default values
            if "target_folder" not in parent_command_vars.keys():
                parent_command_vars["target_folder"] = DEFAULT_FRECKLE_TARGET_MARKER
            if "target_folder_name" not in parent_command_vars.keys():
                parent_command_vars["target_folder_name"] = None
            if "include" not in parent_command_vars.keys():
                parent_command_vars["include"] = []
            if "exclude" not in parent_command_vars.keys():
                parent_command_vars["exclude"] = []
            if "password" not in parent_command_vars.keys():
                parent_command_vars["password"] = "auto"
            if "non_recursive" not in parent_command_vars.keys():
                parent_command_vars["non_recursive"] = False

            metadata["__auto__"] = {}

            for details in default_freckle_urls:
                f = details["url"]
                repos[f] = copy.deepcopy(parent_command_vars)
                repos[f]["profiles"] = ["__auto__"]
                repos[f]["repo_details"] = details

            extra_profile_vars = default_extra_vars

        else:

            for p in args[0]:
                pn = p["name"]
                if pn in profiles:
                    raise Exception("Profile '{}' specified twice. I don't think that makes sense. Exiting...".format(pn))
                else:
                    profiles.append(pn)

                metadata[pn] = {}
                metadata[pn]["metadata"] = p["adapter_metadata"]
                metadata[pn]["details"] = p["adapter_details"]

                pvars_defaults = p["default_vars"]
                pvars_extra_vars = p["extra_vars"]
                pvars_user_input = p["user_input"]

                pvars = OrderedDict()
                frkl.dict_merge(pvars, pvars_defaults, copy_dct=False)
                for ev in pvars_extra_vars:
                    frkl.dict_merge(pvars, ev, copy_dct=False)
                frkl.dict_merge(pvars, parent_command_vars, copy_dct=False)
                frkl.dict_merge(pvars, pvars_user_input, copy_dct=False)

                freckles = list(pvars.pop("freckle", []))
                include = set(pvars.pop("include", []))
                exclude = set(pvars.pop("exclude", []))
                target = pvars.pop("target_folder", None)
                ask_become_pass = pvars.pop("ask_become_pass", "auto")
                non_recursive = pvars.pop("non_recursive", False)

                if non_recursive is None:
                    non_recursive = default_non_recursive

                if ask_become_pass == "auto" and default_ask_become_pass != "auto":
                    ask_become_pass = default_ask_become_pass

                extra_profile_vars[pn] = copy.deepcopy(default_extra_vars.get(pn, {}))
                if pvars:
                    for pk, pv in pvars.items():
                        if pv != None:
                            extra_profile_vars[pn][pk] = pv

                # TODO: could check whether there are duplicates, but can't be bothered at the moment

                all_freckles_for_this_profile = default_freckle_urls + freckles

                for freckle_details in all_freckles_for_this_profile:
                    freckle_url = freckle_details["url"]
                    if target:
                        t = target
                    else:
                        t = default_target

                    if t is None:
                        t = DEFAULT_FRECKLE_TARGET_MARKER

                    for i in default_include:
                        if i not in include:
                            include.add(i)
                    for e in default_exclude:
                        if e not in exclude:
                            exclude.add(e)
                    fr = {
                        "target_folder": t,
                        "includes": list(include),
                        "excludes": list(exclude),
                        "password": ask_become_pass,
                        "non_recursive": non_recursive
                    }
                    repos.setdefault(freckle_url, fr)
                    repos[freckle_url].setdefault("profiles", []).append(pn)
                    repos[freckle_url]["repo_details"] = freckle_details

        if (repos):
            print_title("starting freckelize run(s)...")
            temp = execute_freckelize_run(repos, profiles, metadata, extra_profile_vars=extra_profile_vars, no_run=no_run, output_format=default_output_format, ask_become_pass=default_ask_become_pass, hosts_list=hosts)
            result.append(temp)
            click.echo("")

        else:
            click.echo("\nNo repos specified. Doing nothing.")

        return result

    except (Exception) as e:
        log.debug("Error assembling configuration:")
        log.debug(e, exc_info=True)
        message = e.message
        if not message:
            if not e.reason:
                message = "n/a"
            else:
                message = "Reason: {}".format(e.reason)
        click.echo("\nError assembling configuration.\nMessage:  {}\nExiting...".format(message))
        sys.exit(1)


def execute_freckelize_run(repos, profiles, adapter_metadata, extra_profile_vars={}, no_run=False, output_format="default", ask_become_pass="auto", hosts_list=["localhost"]):
    """Executes a freckles run using the provided run details.

    Args:
      repos (dict): dict with freckle urls as key, and details about (optional) include/excludes and target directory.
      profiles (list): list of adapters to use with these freckle repos
      hosts_list (list): a list of hosts to run this run on
    """

    log.debug("Starting freckelize run")
    all_freckle_repos = []

    # augment repo data
    create_freckle_descs(repos)

    repo_metadata_file = "repo_metadata"

    extra_profile_vars.setdefault("freckle", {})["no_run"] = bool(no_run)

    result_checkout = create_freckelize_checkout_run(repos, repo_metadata_file, extra_profile_vars, ask_become_pass=ask_become_pass, output_format=output_format, hosts_list=hosts_list)

    playbook_dir = result_checkout["playbook_dir"]

    repo_metadata_file_abs = os.path.join(playbook_dir, os.pardir, "logs", repo_metadata_file)

    return_code = result_checkout["return_code"]

    if return_code != 0:
        click.echo("Checkout phase failed, not continuing...")
        sys.exit(1)

    all_repo_metadata = json.load(open(repo_metadata_file_abs))

    #TODO: config option to allow freckle folders to contain context
    # add_paths = list(all_repo_metadata.keys())
    add_paths = []
    if not profiles:

        profiles = []

        for repo, metadata in all_repo_metadata.items():

            for vars in metadata["vars"]:
                profile_temp = vars["profile"]["name"]
                if profile_temp == "freckle":
                    continue
                if not vars.get("vars", {}).get(FRECKELIZE_PROFILE_ACTIVE_KEY, True):
                    continue
                if profile_temp not in profiles:
                    profiles.append(profile_temp)

        config = DEFAULT_FRECKLES_CONFIG
        paths = [p['path'] for p in expand_repos(config.trusted_repos)]
        finder = FreckelizeAdapterFinder(paths)
        reader = FreckelizeAdapterReader()

        all_dictlets = finder.get_all_dictlets()
        adapter_metadata = {}
        for profile in profiles:
            dictlet_details = all_dictlets.get(profile, None)
            if not dictlet_details:
                adapter_metadata[profile] = {"metadata": {}}
            else:
                log.debug("Reading adapter: {}".format(dictlet_details["path"]))
                adapter_det = {"metadata": reader.read_dictlet(dictlet_details, {}, {})}
                adapter_metadata[profile] = adapter_det
            adapter_metadata[profile]["details"] = dictlet_details
        sorted_profiles = get_adapter_profile_priorities(profiles, adapter_metadata)
        click.echo()
        print_title("no adapters selected, using folder defaults:\n", title_char="-")
    else:
        sorted_profiles = profiles
        click.echo()
        print_title("using user-selected adapter(s):\n", title_char="-")

    # TODO: maybe sort profile order also when specified manually?
    result = create_freckelize_run(sorted_profiles, repo_metadata_file_abs, adapter_metadata, extra_profile_vars, ask_become_pass=ask_become_pass,
                               output_format=output_format, no_run=no_run, additional_repo_paths=add_paths, hosts_list=hosts_list)

    return result

def create_freckelize_run(profiles, repo_metadata_file, adapter_metadata, extra_profile_vars, ask_become_pass="true", no_run=False,
                        output_format="default", additional_repo_paths=[], hosts_list=["localhost"]):

    # profiles = extract_all_used_profiles(freckle_repos)

    adapters_files_map = create_adapters_files_map(profiles, adapter_metadata)
    callback = add_adapter_files_callback(profiles, adapter_metadata, adapters_files_map, additional_context_repos=additional_repo_paths)

    additional_roles = get_adapter_dependency_roles(profiles, adapter_metadata)

    task_config = [{"vars": {"user_vars": extra_profile_vars, "repo_metadata_file": repo_metadata_file, "profile_order": profiles, "adapters_files_map": adapters_files_map}, "tasks": ["freckles"]}]

    result = create_and_run_nsbl_runner(task_config, output_format=output_format, ask_become_pass=ask_become_pass,
                                      pre_run_callback=callback, no_run=no_run, additional_roles=additional_roles, run_box_basics=True, additional_repo_paths=additional_repo_paths, hosts_list=hosts_list)

    if no_run:

        click.echo()
        click.secho("========================================================", bold=True)
        click.echo()
        click.echo("'no-run' was specified, not executing freckelize run.")
        click.echo()
        click.echo("Variables that would have been used for an actual run:")
        click.echo()
        click.secho("Defaults/User input:", bold=True)
        click.secho("--------------------", bold=True)
        click.echo()
        output(extra_profile_vars, output_type="yaml", indent=2)
        click.echo()
        with open(repo_metadata_file) as metadata_file:
            metadata = json.load(metadata_file)

        click.secho("Folders:", bold=True)
        click.secho("--------", bold=True)
        for folder, details in metadata.items():
            click.echo()
            click.secho("path: ", bold=True, nl=False)
            click.echo("{}:".format(folder))
            click.echo()
            for p_vars in details["vars"]:
                p_name = p_vars["profile"]["name"]
                if p_name in profiles:
                    click.secho("  profile: ", bold=True, nl=False)
                    click.echo(p_name)
                    output(p_vars["vars"], output_type="yaml", indent=4)
            if details["extra_vars"]:
                click.secho("  extra vars:", bold=True)
                output(details["extra_vars"], output_type="yaml", indent=4)
            else:
                click.secho("  extra_vars: ", bold=True, nl=False)
                click.echo("none")

        click.echo()

        sys.exit(0)


def create_freckelize_checkout_run(freckle_repos, repo_metadata_file, extra_profile_vars, ask_become_pass="true", no_run=False, output_format="default", hosts_list=["localhost"]):

    repos_list = [(k, v) for k, v in freckle_repos.items()]

    task_config = [{"vars": {"freckles": repos_list, "user_vars": extra_profile_vars, "repo_metadata_file": repo_metadata_file}, "tasks": ["freckles_checkout"]}]

    result = create_and_run_nsbl_runner(task_config, output_format=output_format, ask_become_pass=ask_become_pass,
                                        no_run=no_run, run_box_basics=True, hosts_list=hosts_list)

    # this isn't really used, as we want to run at least the checkout run to be able to parse .freckle files
    if no_run:
        click.echo("'no-run' option specified, finished")
        sys.exit()

    return result

def get_adapter_profile_priorities(profiles, adapter_metadata):

    if not profiles:
        return []
    prios = []

    for adapter in profiles:

        metadata = adapter_metadata[adapter]["metadata"]
        priority = metadata.get("__freckles__", {}).get("adapter_priority", DEFAULT_FRECKELIZE_PROFILE_PRIORITY)

        prios.append([priority, adapter])

    profiles_sorted = sorted(prios, key=lambda tup: tup[0])

    return [item[1] for item in profiles_sorted]

# def find_adapter_files(extension, valid_profiles=None, config=None, additional_context_repos=[]):

#     profiles = find_supported_profiles(config, additional_context_repos)
#     task_files_to_copy = {}

#     for profile_name, profile_details in profiles.items():

#         if valid_profiles and profile_name not in valid_profiles:
#             continue

#         profile_path = profile_details["path"]
#         profile_child_file = os.path.join(profile_path, "{}.{}".format(profile_name, extension))

#         if not os.path.exists(profile_child_file) or not os.path.isfile(profile_child_file):
#             continue

#         task_files_to_copy[profile_name] = profile_child_file

#     return task_files_to_copy

def create_adapters_files_map(adapters, adapters_metadata):

    files_map = {}

    for adapter in adapters:
        adapter_metadata = adapters_metadata[adapter]
        adapter_path = adapter_metadata["details"]["path"]
        tasks_init = adapter_metadata["metadata"].get("tasks_init", [])
        tasks_folder = adapter_metadata["metadata"].get("tasks_folder", [])
        files_map[adapter] = create_adapter_files_list(adapter, adapter_path, tasks_init, tasks_folder)

    return files_map

def create_adapter_files_list(adapter_name, adapter_path, init_task_files, freckle_task_files):

    base_dir = os.path.dirname(adapter_path)
    result = {}
    result["init"] = []
    for f in init_task_files:
        if not os.path.isabs(f):
            f = os.path.join(base_dir, f)

        if not os.path.exists(f):
            raise Exception("Invalid adapter '{}', can't find file: {}".format(adapter_name, f))

        file_details = {}
        file_details["source"] = os.path.join(base_dir, f)
        file_details["target"] = os.path.join(adapter_name, "init", os.path.basename(f))
        # file_details["target"] = "{}/{}/{}".format(adapter_name, "init", os.path.basename(f))

        result["init"].append(file_details)

    result["freckle"] = []
    for f in freckle_task_files:
        if not os.path.isabs(f):
            f = os.path.join(base_dir, f)

        if not os.path.exists(f):
            raise Exception("Invalid adapter '{}', can't find file: {}".format(adapter_name, f))

        file_details = {}
        file_details["source"] = os.path.join(base_dir, f)
        # file_details["target"] = "{}/{}/{}".format(adapter_name, "freckle", os.path.basename(f))
        file_details["target"] = os.path.join(adapter_name, "freckle", os.path.basename(f))
        result["freckle"].append(file_details)

    return result


def add_adapter_files_callback(profiles, adapter_metadata, files_map, additional_context_repos=[], print_used_adapter=True):

    print_cache = {}


    # check for 'active' adapters, i.e. ones that have at least one tasks file
    no_valid_profiles = True
    for profile in profiles:
        if files_map.get(profile, {}).get("init", None) or files_map.get(profile, {}).get("freckle", None):
            path = adapter_metadata[profile]["details"]["path"]
            print_cache[profile] = path
            no_valid_profiles = False

    if no_valid_profiles:
        click.echo("  - no adapters with any task files found, only executing basic folder tasks")
    else:
        if profiles and print_used_adapter:
            for p in profiles:
                if p in print_cache.keys():
                    click.echo("  - ", nl=False)
                    click.secho(p, bold=True, nl=False)
                    click.echo(": {}".format(print_cache[p]))

    def copy_callback(ansible_environment_root):
        target_path = os.path.join(ansible_environment_root, "task_lists")
        for adapter, files in files_map.items():
            for f in files["init"]:
                source_file = f["source"]
                target_file = os.path.join(target_path, f["target"])
                os.makedirs(os.path.dirname(target_file))
                shutil.copyfile(source_file, target_file)
            for f in files["freckle"]:
                source_file = f["source"]
                target_file = os.path.join(target_path, f["target"])
                os.makedirs(os.path.dirname(target_file))
                shutil.copyfile(source_file, target_file)

    return copy_callback

def find_supported_profiles(config=None, additional_context_repos=[]):

    if not config:
        config = DEFAULT_FRECKLES_CONFIG

    trusted_repos = copy.copy(config.trusted_repos)
    if additional_context_repos:
        trusted_repos.extend(additional_context_repos)

    repos = nsbl.tasks.get_local_repos(trusted_repos, "adapters", DEFAULT_LOCAL_REPO_PATH_BASE, DEFAULT_REPOS, DEFAULT_ABBREVIATIONS)

    result = {}
    for r in repos:
        p = find_freckelize_adapters(r)
        result.update(p)

    return result

def get_adapter_dependency_roles(profiles, adapter_metadata):

    if not profiles:
        return []

    # dep_files = find_adapter_files(ADAPTER_MARKER_EXTENSION, profiles, additional_context_repos=additional_context_repos)

    all_deps = set()

    for adapter in profiles:

        metadata = adapter_metadata[adapter]["metadata"]
        roles = metadata.get("__freckles__", {}).get("roles", [])
        all_deps |= set(roles)

    return list(all_deps)

@click.command(name="freckelize", cls=FreckelizeCommand, epilog=FRECKELIZE_EPILOG_TEXT, subcommand_metavar="ADAPTER", invoke_without_command=True, result_callback=assemble_freckelize_run, chain=True)
@click_log.simple_verbosity_option(log, "--verbosity")
@click.pass_context
def cli(ctx, **kwargs):
    """Downloads a remote dataset or code (called a 'freckle') and sets up your local environment to be able to handle the data, according to the data's profile.

    Ideally the remote dataset includes all the metadata that is needed to setup the environment, but it's possible to provide some directives using commandline options globally (--target, --include, --exclude), or per adapter (use the --help function on each adapter to view those).

    Locally available adapters for supported profiles are listed below, each having their own configuration. You can specify a 'global' url by adding it's '--freckle' option before any of the subsequently specified adapters, prompting any of those adapters to apply their tasks to it. Or you can assign one (or multiple) freckle to an adapter by providing it after the adapter name.

    For more details, visit the online documentation: https://docs.freckles.io/en/latest/freckelize_command.html
    """

if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
