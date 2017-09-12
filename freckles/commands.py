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
                    url_is_local, create_cli_command, get_vars_from_cli_input)

log = logging.getLogger("freckles")


COMMAND_SEPERATOR = "-"
DEFAULT_COMMAND_REPO = os.path.join(os.path.dirname(__file__), "external", "frecklecutables")
DEFAULT_COMMAND_EPILOG = "For more information about frecklecute and the freckles project, please visit: https://github.com/makkus/freckles"

class CommandRepo(object):

    def __init__(self, paths=[DEFAULT_COMMAND_REPO], no_run=False, additional_commands=[]):
        if not isinstance(paths, (list, tuple)):
            paths = [paths]

        self.paths = [os.path.expanduser(p) for p in paths]

        if DEFAULT_COMMAND_REPO not in self.paths:
            self.paths.insert(0, DEFAULT_COMMAND_REPO)

        self.additional_commands = additional_commands

        self.commands = self.get_commands(no_run)

    def get_commands(self, no_run=False):

        commands = {}
        for path in self.paths:

            path_tokens = len(path.split(os.sep))
            for root, dirs, files in os.walk(path):
                if not files:
                    continue

                path = root.split(os.sep)
                for f in files:
                    command_name = COMMAND_SEPERATOR.join(path[path_tokens:] + [f])
                    command = self.create_command(command_name, os.path.join(root, f), no_run)
                    commands[command_name] = command



        for command in self.additional_commands:

            command_name = command[0]
            command_file = command[1]
            if not command_name or not command_file:
                continue
            path = command_file.split(os.sep)
            command = self.create_command(command_file, command_file, no_run)
            commands[command_name] = command

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
        no_run = self.commands[command_name]["no_run"]

        def command_callback(**kwargs):

            new_args, final_vars = get_vars_from_cli_input(kwargs, key_map, task_vars, default_vars, args_that_are_vars, value_vars)
            rendered_tasks = render_dict(tasks, new_args)

            # log.debug("Args: {}".format(new_args))
            log.debug("Vars: {}".format(final_vars))
            log.debug("Tasks to execute, with arguments replaced: {}".format(rendered_tasks))

            task_config = [{"vars": final_vars, "tasks": rendered_tasks}]

            if no_run:
                click.echo("")
                click.echo("Task config:")
                click.echo("")
                pprint.pprint(task_config)
                click.echo("")
                return

            log.debug("Final task config: {}".format(task_config))

            output = ctx.params["output"]
            ask_become_pass = ctx.params["ask_become_pass"]


            create_and_run_nsbl_runner(task_config, output, ask_become_pass)

        help = doc.get("help", "n/a")
        short_help = doc.get("short_help", help)
        epilog = doc.get("epilog", DEFAULT_COMMAND_EPILOG)

        command = click.Command(command_name, params=options_list, help=help, short_help=short_help, epilog=epilog, callback=command_callback)
        return command

    def create_command(self, command_name, yaml_file, no_run=False):

        log.debug("Loading command file '{}'...".format(yaml_file))

        #split_config = {"keywords": ["args", "doc", "tasks"]}
        #chain = [UrlAbbrevProcessor(), EnsureUrlProcessor(), YamlTextSplitProcessor(init_params=split_config), EnsurePythonObjectProcessor()]
        chain = [UrlAbbrevProcessor(), EnsureUrlProcessor(), EnsurePythonObjectProcessor()]
        frkl_obj = Frkl(yaml_file, chain)

        config_content = frkl_obj.process(MergeDictResultCallback())
        # with open(yaml_file, 'r') as stream:
            # try:
                # config_content = yaml.safe_load(stream)
            # except yaml.YAMLError as exc:
                # raise exc
                # log.info("Could not parse command file '{}', ignoring...".format(yaml_file))
                # return None

        # doc = config_content.get("doc", {})
        # TODO: check format of config
        # options = config_content.get("args", {})
        # vars = config_content.get("vars", {})
        tasks = config_content.get("tasks", None)
        # default_vars = config_content.get("defaults", {})

        if not tasks:
            click.echo("No tasks included in command, doing nothing.")
            sys.exit(1)

        cli_command = create_cli_command(config_content, yaml_file, no_run)
        return cli_command
