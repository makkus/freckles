# -*- coding: utf-8 -*-

# python 3 compatibility
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import os
import pprint
import sys
from pydoc import locate

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
                    url_is_local, find_supported_profiles, PROFILE_MARKER_FILENAME, create_cli_command, create_freckles_run)

log = logging.getLogger("freckles")


COMMAND_SEPERATOR = "-"
DEFAULT_COMMAND_REPO = os.path.join(os.path.dirname(__file__), "frecklecutables")

def assemble_freckle_run(*args, **kwargs):

    target = kwargs.get("target", None)
    if not target:
        target = "~/freckles"

    freckle_urls = kwargs["freckle"]
    output_format = kwargs["output"]

    include = kwargs["include"]
    exclude = kwargs["exclude"]

    ask_become_pass = kwargs["ask_become_pass"]

    profile_names = []
    for p in args:
        pn = p[0]["name"]
        if pn not in profile_names:
            profile_names.append(pn)

    repos = []
    for freckle_url in freckle_urls:
        freckle_repo = create_freckle_desc(freckle_url, target, True, profiles=profile_names, includes=include, excludes=exclude)
        repos.append(freckle_repo)

    create_freckles_run(repos, ask_become_pass=ask_become_pass, no_run=False, output_format=output_format)

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
            return {"name": command_name, "vars": kwargs}

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
