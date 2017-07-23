# -*- coding: utf-8 -*-

# python 3 compatibility
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import os
from pydoc import locate

import click
from six import string_types

import yaml
from frkl.frkl import PLACEHOLDER, Frkl, UrlAbbrevProcessor
from nsbl.nsbl import Nsbl, NsblRunner

log = logging.getLogger("freckles")

COMMAND_SEPERATOR = "-"
DEFAULT_ABBREVIATIONS = {
    'gh':
        ["https://github.com/", PLACEHOLDER, "/", PLACEHOLDER, ".git"],
    'bb': ["https://bitbucket.org/", PLACEHOLDER, "/", PLACEHOLDER, ".git"]
}



class RepoType(click.ParamType):

    name = 'repo'

    def convert(self, value, param, ctx):

        try:
            frkl_obj = Frkl(value, [UrlAbbrevProcessor(init_params={"abbrevs": DEFAULT_ABBREVIATIONS, "add_default_abbrevs": False})])
            return frkl_obj.process()
        except:
            self.fail('%s is not a valid repo url' % value, param, ctx)
FRECKLES_REPO = RepoType()

DEFAULT_COMMAND_REPO = os.path.join(os.path.dirname(__file__), "commands")

class CommandRepo(object):

    def __init__(self, paths):
        if not isinstance(paths, (list, tuple)):
            paths = [paths]

        self.paths = [os.path.expanduser(p) for p in paths]

        if DEFAULT_COMMAND_REPO not in self.paths:
            self.paths.insert(0, DEFAULT_COMMAND_REPO)

        self.commands = self.get_commands()

    def get_commands(self):

        commands = {}
        for path in self.paths:

            path_tokens = len(path.split(os.sep))
            for root, dirs, files in os.walk(path):
                if not files:
                    continue

                path = root.split(os.sep)
                for f in files:
                    command_name = COMMAND_SEPERATOR.join(path[path_tokens:] + [f])
                    command = self.create_command(command_name, os.path.join(root, f))
                    commands[command_name] = command

        return commands

    def get_command(self, ctx, command_name):

        options_list = self.commands[command_name]["options"]
        key_map = self.commands[command_name]["key_map"]
        tasks = self.commands[command_name]["tasks"]

        def command_callback(**kwargs):

            for key, value in key_map.items():
                temp = kwargs.pop(key)
                kwargs[value] = temp

            task_config = [{"vars": kwargs, "tasks": tasks}]

            nsbl_obj = Nsbl.create(task_config, [], [], wrap_into_localhost_env=True, pre_chain=[])
            runner = NsblRunner(nsbl_obj)
            target = os.path.expanduser("~/.freckles/runs/archive/run")
            ask_become_pass = True
            stdout_callback = "nsbl_internal"
            no_run = False
            force = True
            display_sub_tasks = True
            display_skipped_tasks = False
            runner.run(target, force=force, ansible_verbose="", ask_become_pass=ask_become_pass, callback=stdout_callback, add_timestamp_to_env=True, add_symlink_to_env="~/.freckles/runs/current", no_run=no_run, display_sub_tasks=display_sub_tasks, display_skipped_tasks=display_skipped_tasks)


        command = click.Command(command_name, params=options_list, help="command help", epilog="epilog", callback=command_callback)
        return command

    def create_command(self, command_name, yaml_file):

        log.debug("Loading command file '{}'...".format(yaml_file))

        with open(yaml_file, 'r') as stream:
            try:
                config_content = yaml.load(stream)
            except yaml.YAMLError as exc:
                log.info("Could not parse command file '{}', ignoring...".format(yaml_file))
                return None

        # TODO: check format of config
        options = config_content.get("vars", {})

        key_map = {}
        argument_key = None

        options_list = []
        for opt, opt_details in options.items():
            opt_type = opt_details.get("type", None)
            if opt_type:
                opt_type_converted = locate(opt_type)
                if not opt_type_converted:
                    raise Exception("No type found for: {}".format(opt_type))
                opt_details['type'] = opt_type_converted

            key = opt_details.pop('key', opt)
            key_map[key] = opt

            is_argument = opt_details.pop('is_argument', False)
            if is_argument:
                if argument_key:
                    raise Exception("Multiple arguments are not supported (yet): {}".format(config_content["vars"]))
                argument_key = key
                required = opt_details.pop("required", None)

                o = click.Argument(param_decls=[key], required=required, **opt_details)
            else:
                o = click.Option(param_decls=["--{}".format(key)], **opt_details)
            options_list.append(o)

        return {"options": options_list, "key_map": key_map, "command_file": yaml_file, "tasks": config_content["tasks"]}
