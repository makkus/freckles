# -*- coding: utf-8 -*-

# python 3 compatibility
from __future__ import (absolute_import, division, print_function)

import logging

import click
from frkl.frkl import (EnsurePythonObjectProcessor,
                       EnsureUrlProcessor, Frkl, MergeDictResultCallback,
                       UrlAbbrevProcessor)

from .freckles_defaults import *
from .utils import create_and_run_nsbl_runner, create_cli_command, get_vars_from_cli_input, print_task_list_details, \
    render_dict

log = logging.getLogger("freckles")


COMMAND_SEPERATOR = "-"
DEFAULT_COMMAND_REPO = os.path.join(os.path.dirname(__file__), "external", "frecklecutables")
DEFAULT_COMMAND_EPILOG = "For more information about frecklecute and the freckles project, please visit: https://github.com/makkus/freckles"


def find_frecklecutable_dirs(path):

    result = []
    for root, dirnames, filenames in os.walk(os.path.realpath(path), topdown=True, followlinks=True):

        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]

        for dirname in dirnames:
            if dirname == "frecklecutables":
                result.append(os.path.join(root, dirname))

    return result

class CommandRepo(object):

    def __init__(self, paths=[], additional_commands=[]):
        if not isinstance(paths, (list, tuple)):
            paths = [paths]

        self.paths = [os.path.expanduser(p) for p in paths]

        # if DEFAULT_COMMAND_REPO not in self.paths:
            # self.paths.insert(0, DEFAULT_COMMAND_REPO)

        self.additional_commands = additional_commands

        self.commands = self.get_commands()

    def get_commands(self):

        command_folders = []
        for path in self.paths:

            if not os.path.exists(path):
                log.debug("Not using folder '{}' as it doesn't exist.".format(path))
                continue

            command_folders.append(path)

            root_dirs = find_frecklecutable_dirs(path)
            command_folders.extend(root_dirs)


        commands = {}

        for path in command_folders:

            path_tokens = len(path.split(os.sep))
            for child in os.listdir(path):

                file_path = os.path.realpath(os.path.join(path, child))

                if "." in child:
                    log.debug("Not using '{}' as frecklecutable: filename contains '.'".format(file_path))
                    continue

                if not os.path.isfile(file_path):
                    continue

                command_name = child
                command = self.create_command(command_name, file_path)
                if not command:
                    log.debug("Not using '{}' as frecklecutable: file couldn't be parsed".format(file_path))
                else:
                    commands[command_name] = command

        for command in self.additional_commands:

            command_name = command[0]
            command_file = command[1]
            if not command_name or not command_file:
                continue
            path = command_file.split(os.sep)
            command = self.create_command(command_file, command_file)
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
        metadata = self.commands[command_name]["metadata"]

        def command_callback(**kwargs):

            new_args, final_vars = get_vars_from_cli_input(kwargs, key_map, task_vars, default_vars, args_that_are_vars, value_vars)
            rendered_tasks = render_dict(tasks, new_args)

            # log.debug("Args: {}".format(new_args))
            log.debug("Vars: {}".format(final_vars))
            log.debug("Tasks to execute, with arguments replaced: {}".format(rendered_tasks))

            task_config = [{"vars": final_vars, "tasks": rendered_tasks}]

            log.debug("Final task config: {}".format(task_config))

            output = ctx.params["output"]
            ask_become_pass = ctx.params["ask_become_pass"]
            no_run = ctx.params["no_run"]

            if no_run:
                parameters = create_and_run_nsbl_runner(task_config, task_metadata=metadata, output_format=output, ask_become_pass=ask_become_pass, no_run=True)
                print_task_list_details(task_config, task_metadata=metadata, output_format=output, ask_become_pass=ask_become_pass, run_parameters=parameters)
            else:
                create_and_run_nsbl_runner(task_config, task_metadata=metadata, output_format=output, ask_become_pass=ask_become_pass)
            # create_and_run_nsbl_runner(task_config, output, ask_become_pass)

        help = doc.get("help", "n/a")
        short_help = doc.get("short_help", help)
        epilog = doc.get("epilog", DEFAULT_COMMAND_EPILOG)

        command = click.Command(command_name, params=options_list, help=help, short_help=short_help, epilog=epilog, callback=command_callback)
        return command

    def create_command(self, command_name, yaml_file):

        log.debug("Loading command file '{}'...".format(yaml_file))

        chain = [UrlAbbrevProcessor(), EnsureUrlProcessor(), EnsurePythonObjectProcessor()]

        try:
            frkl_obj = Frkl(yaml_file, chain)
            config_content = frkl_obj.process(MergeDictResultCallback())
        except:
            log.debug("Can't parse command file '{}'.".format(yaml_file))
            return None

        tasks = config_content.get("tasks", None)

        if not tasks:
            return None

        cli_command = create_cli_command(config_content, command_name=command_name, command_path=yaml_file)
        return cli_command

