# -*- coding: utf-8 -*-

# python 3 compatibility
from __future__ import (absolute_import, division, print_function)

import collections
import logging

import click
import copy
import json
import os
import sys
import yaml

from frkl.frkl import dict_merge

try:
    set
except NameError:
    from sets import Set as set

from .utils import (RepoType, VarsType,
                    create_freckle_desc,
                    find_supported_profiles, ADAPTER_MARKER_EXTENSION, create_cli_command, create_freckles_run,
                    create_freckles_checkout_run, get_vars_from_cli_input, print_repos_expand, get_adapter_profile_priorities)
from .freckle_detect import create_freckle_descs
from .freckles_defaults import *

log = logging.getLogger("freckles")

COMMAND_SEPERATOR = "-"
BREAK_COMMAND_NAME = "[new]"

DEFAULT_COMMAND_REPO = os.path.join(os.path.dirname(__file__), "frecklecutables")

FRECKLE_ARG_HELP = "the url or path to the freckle(s) to use, if specified here, before any commands, all profiles will be applied to it"
FRECKLE_ARG_METAVAR = "URL_OR_PATH"
TARGET_ARG_HELP = 'target folder for freckle checkouts (if remote url provided), defaults to folder \'freckles\' in users home'
TARGET_ARG_METAVAR = "PATH"
INCLUDE_ARG_HELP = 'if specified, only process folders that end with one of the specified strings, only applicable for multi-freckle folders'
INCLUDE_ARG_METAVAR = 'FILTER_STRING'
EXCLUDE_ARG_HELP = 'if specified, omit process folders that end with one of the specified strings, takes precedence over the include option if in doubt, only applicable for multi-freckle folders'
EXCLUDE_ARG_METAVAR = 'FILTER_STRING'
ASK_PW_HELP = 'whether to force ask for a password, force ask not to, or let freckles decide (which might not always work)'
ASK_PW_CHOICES = click.Choice(["auto", "true", "false"])
EXTRA_VARS_ARG_HELP = "extra vars, overlayed on top of potential folder/adapter variables"
EXTRA_VARS_METAVAR = "EXTRA_VARS_FILE"
NON_RECURSIVE_HELP = "whether to exclude all freckle child folders, default: false"

def get_freckelize_option_set():
    """Helper method to create some common cli options."""

    freckle_option = click.Option(param_decls=["--freckle", "-f"], required=False, multiple=True, type=RepoType(),
                                  metavar=FRECKLE_ARG_METAVAR, help=FRECKLE_ARG_HELP)
    target_option = click.Option(param_decls=["--target-folder", "-t"], required=False, multiple=False, type=str,
                                 metavar=TARGET_ARG_METAVAR,
                                 help=TARGET_ARG_HELP)
    include_option = click.Option(param_decls=["--include", "-i"],
                                  help=INCLUDE_ARG_HELP,
                                  type=str, metavar=INCLUDE_ARG_METAVAR, default=[], multiple=True)
    exclude_option = click.Option(param_decls=["--exclude", "-e"],
                                  help=EXCLUDE_ARG_HELP,
                                  type=str, metavar=EXCLUDE_ARG_METAVAR, default=[], multiple=True)
    ask_become_pass_option = click.Option(param_decls=["--ask-become-pass", "-pw"],
                                          help=ASK_PW_HELP,
                                          type=ASK_PW_CHOICES, default="true")
    extra_vars_option = click.Option(param_decls=["--extra-vars", "-v"],
                                     help=EXTRA_VARS_ARG_HELP,
                                     multiple=True,
                                     type=VarsType(),
                                     metavar=EXTRA_VARS_METAVAR,
                                     required=False)
    parent_only_option = click.Option(param_decls=["--non-recursive"],
                                      help=NON_RECURSIVE_HELP,
                                      is_flag=True,
                                      default=False,
                                      required=False,
                                      type=bool
    )

    params = [freckle_option, extra_vars_option, target_option, include_option, exclude_option,
                       ask_become_pass_option, parent_only_option]

    return params


def execute_freckle_run(repos, profiles, metadata, extra_profile_vars={}, no_run=False, output_format="default", ask_become_pass="auto", hosts_list=["localhost"]):
    """Executes a freckles run using the provided run details.

    Args:
      repos (dict): dict with freckle urls as key, and details about (optional) include/excludes and target directory.
      profiles (list): list of adapters to use with these freckle repos
      hosts_list (list): a list of hosts to run this run on
    """

    all_freckle_repos = []

    # augment repo data
    create_freckle_descs(repos)

    repo_metadata_file = "repo_metadata"

    extra_profile_vars.setdefault("freckle", {})["no_run"] = bool(no_run)

    result_checkout = create_freckles_checkout_run(repos, repo_metadata_file, extra_profile_vars, ask_become_pass=ask_become_pass, output_format=output_format, hosts_list=hosts_list)

    playbook_dir = result_checkout["playbook_dir"]
    repo_metadata_file_abs = os.path.join(playbook_dir, os.pardir, "logs", repo_metadata_file)

    return_code = result_checkout["return_code"]

    if return_code != 0:
        click.echo("Checkout phase failed, not continuing...")
        sys.exit(1)

    all_repo_metadata = json.load(open(repo_metadata_file_abs))
    add_paths = list(all_repo_metadata.keys())

    if not profiles:

        profiles = []

        for repo, metadata in all_repo_metadata.items():

            for vars in metadata["vars"]:
                profile_temp = vars["profile"]["name"]
                if not vars.get("vars", {}).get(FRECKELIZE_PROFILE_ACTIVE_KEY, True):
                    continue
                if profile_temp not in profiles:
                    profiles.append(profile_temp)

        sorted_profiles = get_adapter_profile_priorities(profiles, additional_context_repos=add_paths)
        click.echo("\n# no adapters specified, using defaults from .freckle file:\n")
    else:
        sorted_profiles = profiles
        click.echo("\n# using specified adapter(s):\n")

    # TODO: maybe sort profile order also when specified manually?

    return create_freckles_run(sorted_profiles, repo_metadata_file_abs, extra_profile_vars, ask_become_pass=ask_become_pass,
                               output_format=output_format, no_run=no_run, additional_repo_paths=add_paths, hosts_list=hosts_list)


def assemble_freckle_run(*args, **kwargs):

    try:
        result = []
        no_run = kwargs.get("no_run")

        hosts = list(kwargs["host"])
        if not hosts:
            hosts = ["localhost"]

        default_target = kwargs.get("target_folder", None)
        if not default_target:
            default_target = DEFAULT_FRECKLE_TARGET_MARKER

        default_freckle_urls = list(kwargs.get("freckle", []))
        default_output_format = kwargs.get("output", "default")

        default_include = list(kwargs.get("include", []))
        default_exclude = list(kwargs.get("exclude", []))

        default_ask_become_pass = kwargs.get("ask_become_pass", True)

        default_extra_vars_raw = list(kwargs.get("extra_vars", []))

        default_non_recursive = kwargs.get("non_recursive", False)
        if not default_non_recursive:
            default_non_recursive = False

        default_extra_vars = {}

        for ev in default_extra_vars_raw:
            dict_merge(default_extra_vars, ev, copy_dct=False)

        extra_profile_vars = {}
        repos = collections.OrderedDict()
        profiles = []

        metadata = {}

        if not args[0]:
            # auto-detect

            metadata["__auto__"] = {}

            fr = {
                "target_folder": default_target,
                "includes": default_include,
                "excludes": default_exclude,
                "password": default_ask_become_pass,
                "non_recursive": default_non_recursive
                }

            for f in default_freckle_urls:
                repos[f] = copy.deepcopy(fr)
                repos[f]["profiles"] = ["__auto__"]

            extra_profile_vars = default_extra_vars

        else:

            for p in args[0]:

                pn = p["name"]

                metadata[pn] = p["metadata"]

                if pn in profiles:
                    raise Exception("Profile '{}' specified twice. I don't think that makes sense. Exiting...".format(pn))
                else:
                    profiles.append(pn)

                pvars = p["vars"]
                freckles = list(pvars.pop("freckle", []))
                include = set(pvars.pop("include", []))
                exclude = set(pvars.pop("exclude", []))
                target = pvars.pop("target-folder", None)
                ask_become_pass = pvars.pop("ask_become_pass", "auto")
                non_recursive = pvars.pop("non_recursive", False)

                if non_recursive == None:
                    non_recursive = default_non_recursive

                if ask_become_pass == "auto" and default_ask_become_pass != "auto":
                    ask_become_pass = default_ask_become_pass

                extra_profile_vars[pn] = copy.deepcopy(default_extra_vars.get(pn, {}))
                if pvars:
                    for pk, pv in pvars.items():
                        if pv != None:
                            extra_profile_vars[pn][pk] = pv

                all_freckles_for_this_profile = list(set(default_freckle_urls + freckles))
                for freckle_url in all_freckles_for_this_profile:
                    if target:
                        t = target
                    else:
                        t = default_target

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

        if (repos):
            click.echo("\n# starting ansible run(s)...")
            temp = execute_freckle_run(repos, profiles, metadata, extra_profile_vars=extra_profile_vars, no_run=no_run, output_format=default_output_format, ask_become_pass=default_ask_become_pass, hosts_list=hosts)
            result.append(temp)
            click.echo("")
        return result
    except (Exception) as e:
        click.echo("\n{}\nExiting...".format(e.message))
        sys.exit(1)



class ProfileRepo(object):
    def __init__(self, config):

        self.config = config
        print_repos_expand(self.config.trusted_repos, repo_source=config.config_file, warn=True)
        self.profiles = None
        self.commands = None

    def get_profiles(self):

        if not self.profiles:
            self.profiles = find_supported_profiles(self.config)

        return self.profiles

    def get_commands(self):

        if not self.commands:

            # commands = {"BREAK": None}
            self.commands = {}

            for profile_name, profile_path in self.get_profiles().items():
                command = self.create_command(profile_name, profile_path)
                self.commands[profile_name] = command

        return self.commands

    def get_command(self, ctx, command_name):

        # if command_name == "BREAK":
            # return click.Command("BREAK", help="marker")

        options_list = self.get_commands()[command_name]["options"]
        key_map = self.commands[command_name]["key_map"]
        tasks = self.commands[command_name]["tasks"]
        task_vars = self.commands[command_name]["vars"]
        default_vars = self.commands[command_name]["default_vars"]
        doc = self.commands[command_name]["doc"]
        args_that_are_vars = self.commands[command_name]["args_that_are_vars"]
        value_vars = self.commands[command_name]["value_vars"]
        metadata = self.commands[command_name]["metadata"]

        def command_callback(**kwargs):
            new_args, final_vars = get_vars_from_cli_input(kwargs, key_map, task_vars, default_vars, args_that_are_vars,
                                                           value_vars)
            return {"name": command_name, "vars": final_vars, "metadata": metadata}

        help = doc.get("help", "n/a")
        short_help = doc.get("short_help", help)
        epilog = doc.get("epilog", None)

        command = click.Command(command_name, params=options_list, help=help, short_help=short_help, epilog=epilog,
                                callback=command_callback)
        return command

    def create_command(self, command_name, command_path):

        log.debug("Creating command for profile: '{}...'".format(command_name))
        profile_metadata_file = os.path.join(command_path, "{}.{}".format(command_name, ADAPTER_MARKER_EXTENSION))
        with open(profile_metadata_file, 'r') as f:
            md = yaml.safe_load(f)

        if not md:
            md = {}

        extra_options = collections.OrderedDict()
        extra_options["freckle"] = {
            "help": "the url or path to the freckle(s) to use",
            "required": False,
            "type": RepoType(),
            "multiple": True,
            "arg_name": "freckle",
            "extra_arg_names": ["-f"],
            "is_var": True
        }

        extra_options["target-folder"] = {
            "help": TARGET_ARG_HELP,
            "extra_arg_names": ["-t"],
            "required": False,
            "is_var": True,
            "multiple": False
        }

        extra_options["include"] = {
            "help": INCLUDE_ARG_HELP,
            "extra_arg_names": ["-i"],
            "metavar": 'FILTER_STRING',
            "is_var": True,
            "multiple": True,
            "required": False
        }

        extra_options["exclude"] = {
            "help": EXCLUDE_ARG_HELP,
            "extra_arg_names": ["-e"],
            "metavar": 'FILTER_STRING',
            "multiple": True,
            "required": False,
            "is_var": True
        }

        extra_options["ask_become_pass"] = {
            "arg_name": "ask-become-pass",
            "help": ASK_PW_HELP,
            "extra_arg_names": ["-pw"],
            "type": ASK_PW_CHOICES,
            "default": "auto"
        }

        extra_options["non_recursive"] = {
            "arg_name": "non-recursive",
            "help": NON_RECURSIVE_HELP,
            "type": bool,
            "required": False,
            "default": False,
            "is_flag": True
        }

        cli_command = create_cli_command(md, command_name=command_name, command_path=command_path,
                                         extra_options=extra_options)
        return cli_command
