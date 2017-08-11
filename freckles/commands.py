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
                    find_supported_profiles, render_dict, render_vars_template,
                    url_is_local)

log = logging.getLogger("freckles")


COMMAND_SEPERATOR = "-"
DEFAULT_COMMAND_REPO = os.path.join(os.path.dirname(__file__), "frecklecutables")

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
        no_run = self.commands[command_name]["no_run"]

        def command_callback(**kwargs):
            # exchange arg_name with var name

            new_args = {}
            for key, value in key_map.items():
                temp = kwargs.pop(key)
                if key not in args_that_are_vars:
                    if isinstance(temp, tuple):
                        temp = list(temp)
                    new_args[value] = temp
                else:
                    task_vars[value] = temp

            # now overimpose the new_args over template_vars
            new_args = dict_merge(default_vars, new_args)

            final_vars = {}

            for key, template in task_vars.items():
                if isinstance(template, string_types) and "{" in template:
                    template_var_string = render_vars_template(template, new_args)
                    try:
                        template_var_new = yaml.safe_load(template_var_string)
                        final_vars[key] = template_var_new
                    except (Exception) as e:
                        raise Exception("Could not convert template '{}': {}".format(template_var_string, e.message))
                else:
                    final_vars[key] = template

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

            create_and_run_nsbl_runner(task_config, "default", False)

        help = doc.get("help", "n/a")
        short_help = doc.get("short_help", help)
        epilog = doc.get("epilog", None)

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

        doc = config_content.get("doc", {})
        # TODO: check format of config
        options = config_content.get("args", {})
        vars = config_content.get("vars", {})
        tasks = config_content.get("tasks", None)
        default_vars = config_content.get("defaults", {})

        if not tasks:
            click.echo("No tasks included in command, doing nothing.")
            sys.exit(1)

        key_map = {}
        argument_key = None

        options_list = []
        args_that_are_vars = []
        for opt, opt_details in options.items():
            opt_type = opt_details.get("type", None)
            if opt_type:
                opt_type_converted = locate(opt_type)
                if not opt_type_converted:
                    raise Exception("No type found for: {}".format(opt_type))
                opt_details['type'] = opt_type_converted

            key = opt_details.pop('arg_name', opt)
            key_map[key] = opt

            is_argument = opt_details.pop('is_argument', False)
            is_var = opt_details.pop('is_var', True)
            if is_var:
                args_that_are_vars.append(key)
            if is_argument:
                if argument_key:
                    raise Exception("Multiple arguments are not supported (yet): {}".format(config_content["vars"]))
                argument_key = key
                required = opt_details.pop("required", None)

                o = click.Argument(param_decls=[key], required=required, **opt_details)
            else:
                o = click.Option(param_decls=["--{}".format(key)], **opt_details)
            options_list.append(o)

        return {"options": options_list, "key_map": key_map, "command_file": yaml_file, "tasks": tasks, "vars": vars, "default_vars": default_vars, "doc": doc, "args_that_are_vars": args_that_are_vars, "no_run": no_run}
