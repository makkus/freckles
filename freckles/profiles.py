# -*- coding: utf-8 -*-

# python 3 compatibility
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import os
import pprint
import sys
from pydoc import locate
from frkl import frkl
import click
from frkl.frkl import (PLACEHOLDER, EnsurePythonObjectProcessor,
                       EnsureUrlProcessor, Frkl, MergeDictResultCallback,
                       UrlAbbrevProcessor, YamlTextSplitProcessor, dict_merge)
from jinja2 import Environment, PackageLoader, Template
from six import string_types

import yaml

from .utils import (FRECKLES_REPO, FRECKLES_URL, RepoType,
                    create_and_run_nsbl_runner, create_freckle_desc,
                    render_dict, render_vars_template,
                    url_is_local, find_supported_profiles, PROFILE_MARKER_FILENAME, create_cli_command, create_freckles_run, get_vars_from_cli_input)

log = logging.getLogger("freckles")


COMMAND_SEPERATOR = "-"
DEFAULT_COMMAND_REPO = os.path.join(os.path.dirname(__file__), "frecklecutables")


def assemble_freckle_run(*args, **kwargs):


    # print("ARGS")
    # pprint.pprint(args)
    # print("KWARGS")
    # pprint.pprint(kwargs)

    target = kwargs.get("target", None)
    if not target:
        target = "~/freckles"

    freckle_urls = kwargs["freckle"]
    output_format = kwargs["output"]

    include = kwargs["include"]
    exclude = kwargs["exclude"]

    ask_become_pass = kwargs["ask_become_pass"]

    profile_names = []
    extra_profile_vars = {}
    for p in args[0]:
        pn = p["name"]
        if pn not in profile_names:
            profile_names.append(pn)
        else:
            raise Exception("Profile '{}' specified twice. I don't think that makes sense. Exiting...".format(pn))
        pvars = p["vars"]
        if pvars:
            extra_profile_vars[pn] = pvars

    # profile_vars_new = []
    # for profile, p_vars in profile_vars.items():
    #     chain = [frkl.FrklProcessor(DEFAULT_PROFILE_VAR_FORMAT)]
    #     try:
    #         frkl_obj = frkl.Frkl(p_vars, chain)
    #         frkl_callback = frkl.MergeResultCallback()
    #         vars_new = frkl_obj.process(frkl_callback)
    #         profile_vars_new[profile] = vars_new
    #         # result.setdefault(freckle_folder, {})["vars"] = profile_vars_new
    #         # result[freckle_folder]["extra_vars"] = extra_vars.get(freckle_folder, {})
    #         # result[freckle_folder]["folder_metadata"] = folders_metadata[freckle_folder]
    #     except (frkl.FrklConfigException) as e:
    #         raise Exception(
    #             "Can't read vars for profile '{}': {}".format(profile, e.message))

    repos = []
    for freckle_url in freckle_urls:
        freckle_repo = create_freckle_desc(freckle_url, target, True, profiles=profile_names, includes=include, excludes=exclude)
        repos.append(freckle_repo)

    create_freckles_run(repos, extra_profile_vars, ask_become_pass=ask_become_pass, no_run=False, output_format=output_format)

class ProfileRepo(object):

    def __init__(self, config, no_run=False):

        self.profiles = find_supported_profiles(config)
        self.commands = self.get_commands(no_run)

    def get_commands(self, no_run=False):

        commands = {}

        for profile_name, profile_path in self.profiles.items():
            command = self.create_command(profile_name, profile_path, no_run)
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
        no_run = self.commands[command_name]["no_run"]

        def command_callback(**kwargs):
            new_args, final_vars = get_vars_from_cli_input(kwargs, key_map, task_vars, default_vars, args_that_are_vars)
            return {"name": command_name, "vars": final_vars}

        help = doc.get("help", "n/a")
        short_help = doc.get("short_help", help)
        epilog = doc.get("epilog", None)

        command = click.Command(command_name, params=options_list, help=help, short_help=short_help, epilog=epilog, callback=command_callback)
        return command


    def create_command(self, command_name, command_path, no_run=False):

        log.debug("Creating command for profile: '{}...'".format(command_name))
        profile_metadata_file = os.path.join(command_path, PROFILE_MARKER_FILENAME)
        with open(profile_metadata_file, 'r') as f:
            md = yaml.safe_load(f)

        if not md:
            md = {}

        cli_command = create_cli_command(md, command_path, no_run)
        return cli_command
