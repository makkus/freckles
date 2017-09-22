# -*- coding: utf-8 -*-

# python 3 compatibility
from __future__ import (absolute_import, division, print_function)

import collections
import logging

import click
import os
import sys
import yaml

try:
    set
except NameError:
    from sets import Set as set

from .utils import (RepoType,
                    create_freckle_desc,
                    find_supported_profiles, ADAPTER_MARKER_EXTENSION, create_cli_command, create_freckles_run,
                    get_vars_from_cli_input)

log = logging.getLogger("freckles")

COMMAND_SEPERATOR = "-"
DEFAULT_COMMAND_REPO = os.path.join(os.path.dirname(__file__), "frecklecutables")


def assemble_freckle_run(*args, **kwargs):

    no_run = kwargs.get("no_run")

    default_target = kwargs.get("target", None)
    if not default_target:
        default_target = "~/freckles"

    default_freckle_urls = kwargs["freckle"]
    output_format = kwargs["output"]

    default_include = kwargs["include"]
    default_exclude = kwargs["exclude"]

    ask_become_pass = kwargs["ask_become_pass"]

    extra_profile_vars = {}
    repos = collections.OrderedDict()
    profiles = []

    metadata = {}
    for p in args[0]:
        pn = p["name"]
        metadata[pn] = p["metadata"]

        if pn in profiles:
            raise Exception("Profile '{}' specified twice. I don't think that makes sense. Exiting...".format(pn))
        else:
            profiles.append(pn)

        pvars = p["vars"]
        freckles = pvars.pop("freckle", [])
        # include = pvars.pop("include", [])
        # exclude = pvars.pop("exclude", [])
        # target = pvars.pop("target", None)

        if pvars:
            extra_profile_vars[pn] = {}
            for pk, pv in pvars.items():
                if pv != None:
                    extra_profile_vars[pn][pk] = pv

        all_freckles_for_this_profile = list(set(default_freckle_urls + freckles))
        for freckle_url in all_freckles_for_this_profile:
            fr = {
                "target": default_target,
                "includes": default_include,
                "excludes": default_exclude
            }
            repos.setdefault(freckle_url, fr)
            repos[freckle_url].setdefault("profiles", []).append(pn)

            # freckle_repo = create_freckle_desc(freckle_url, target, True, profiles=profile_names, includes=include_all, excludes=exclude_all)

    all_freckle_repos = []
    for freckle_url, freckle_details in repos.items():
        freckle_repo = create_freckle_desc(freckle_url, freckle_details["target"], True,
                                           profiles=freckle_details["profiles"], includes=freckle_details["includes"],
                                           excludes=freckle_details["excludes"])
        all_freckle_repos.append(freckle_repo)


    if not all_freckle_repos:
        click.echo("No adapters specified, doing nothing. Use '--help' to display this tools help as well as available adapters.")
        sys.exit(0)

    if no_run:
        run_parameters = create_freckles_run(all_freckle_repos, extra_profile_vars, ask_become_pass=ask_become_pass,
                                             output_format=output_format, no_run=True)

        click.echo("")
        click.echo("Used adapters:")
        for p in profiles:
            click.echo("\tadapter: {}".format(p))
            click.echo("\tpath: {}".format(metadata[p]["command_path"]))
        click.echo("")
        click.echo("generated ansible environment: {}".format(run_parameters.get("env_dir", "n/a")))
        click.echo("")
    else:
        create_freckles_run(all_freckle_repos, extra_profile_vars, ask_become_pass=ask_become_pass,
                            output_format=output_format)


class ProfileRepo(object):
    def __init__(self, config):

        self.profiles = find_supported_profiles(config)
        self.commands = self.get_commands()

    def get_commands(self):

        commands = {}

        for profile_name, profile_path in self.profiles.items():
            command = self.create_command(profile_name, profile_path)
            commands[profile_name] = command

        return commands

    def get_command(self, ctx, command_name):

        options_list = self.commands[command_name]["options"]
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

        extra_options = {}
        extra_options["freckle"] = {
            "help": "the url or path to the freckle(s) to use",
            "required": False,
            "type": RepoType(),
            "multiple": True,
            "arg_name": "freckle",
            "extra_arg_names": ["-f"],
            "is_var": True
        }

        # extra_options["target"] = {
        #     "help": "target folder for freckle checkouts (if remote url provided), defaults to folder 'freckles' in users home",
        #     "extra_arg_names": ["-t"],
        #     "required": False,
        #     "is_var": True,
        #     "multiple": False
        # }

        # extra_options["include"] = {
        #     "help": "if specified, only process folders that end with one of the specified strings, only applicable for multi-freckle folders",
        #     "extra_arg_names": ["-i"],
        #     "metavar": 'FILTER_STRING',
        #     "is_var": True,
        #     "multiple": True,
        #     "required": False
        # }

        # extra_options["exclude"] = {
        #     "help": "if specified, omit process folders that end with one of the specified strings, takes precedence over the include option if in doubt, only applicable for multi-freckle folders",
        #     "extra_arg_names": ["-e"],
        #     "metavar": 'FILTER_STRING',
        #     "multiple": True,
        #     "required": False,
        #     "is_var": True
        # }

        cli_command = create_cli_command(md, command_name=command_name, command_path=command_path,
                                         extra_options=extra_options)
        return cli_command
