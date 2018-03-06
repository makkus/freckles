# -*- coding: utf-8 -*-

# python 3 compatibility
from __future__ import (absolute_import, division, print_function)

import logging

import click
import yaml
from six import string_types
from frkl.frkl import (EnsurePythonObjectProcessor,
                       EnsureUrlProcessor, Frkl, MergeDictResultCallback,
                       UrlAbbrevProcessor)

from .freckles_defaults import *
from .utils import create_and_run_nsbl_runner, create_cli_command, get_vars_from_cli_input, print_task_list_details, \
    render_dict, expand_repos, print_repos_expand

log = logging.getLogger("freckles")

COMMAND_SEPERATOR = "-"
DEFAULT_COMMAND_REPO = os.path.join(os.path.dirname(__file__), "external", "frecklecutables")
DEFAULT_COMMAND_EPILOG = "For more information about frecklecute and the freckles project, please visit: https://github.com/makkus/freckles"


def find_frecklecutable_dirs(path):
    """Helper method to find 'child' frecklecutable dirs.

    Frecklecutables can either be in the root of a provided 'trusted-repo', or
    in any subfolder within, as long as the subfolder is called 'frecklecutables'.

    Args:
      path (str): the root path (usually the path to a 'trusted repo').
    Returns:
      list: a list of valid 'frecklecutable' paths
    """
    result = []
    for root, dirnames, filenames in os.walk(os.path.realpath(path), topdown=True, followlinks=True):

        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]

        for dirname in dirnames:
            if dirname == "frecklecutables":
                result.append(os.path.join(root, dirname))

    return result


class CommandRepo(object):

    def __init__(self, config, additional_commands=[]):
        """Wrapper class to find all frecklecutables that are specified/allowed by the current configuration, and create and parse command-line options from them.

        Args:
          config (FrecklesConfig): the configuration to use
          additional_commands (list): list of tuples in the format (command_name, command_path) for extra frecklecutables that are not located within any of the valid frecklecutable paths
        """

        self.config = config
        repo_source = "using repo(s) from '{}'".format(config.config_file)
        print_repos_expand(self.config.trusted_repos, repo_source=repo_source, warn=True)

        self.commands = None
        self.additional_commands = additional_commands
        self.paths = None

    def get_commands(self):
        """Returns all valid frecklecutables."""

        repos = self.config.trusted_repos
        self.paths = [p['path'] for p in expand_repos(repos)]

        if not self.commands:

            command_folders = []
            for path in self.paths:

                if not os.path.exists(path):
                    log.debug("Not using folder '{}' as it doesn't exist.".format(path))
                    continue

                command_folders.append(path)

                root_dirs = find_frecklecutable_dirs(path)
                command_folders.extend(root_dirs)

            self.commands = {}

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
                        self.commands[command_name] = command


            for command in self.additional_commands:

                command_name = command[0]
                command_file = command[1]

                if not command_name and not command_file:
                    continue
                elif command_name and not command_file:
                    # in repo or remote
                    if command_name in self.commands.keys():
                        # in one of the repos
                        continue

                    self.commands[command_name] = self.create_command(command_name, command_name)
                    continue
                elif not command_name and command_file:
                    # not possible (I think)
                    continue
                else:
                    # local file
                    path = command_file.split(os.sep)
                    command = self.create_command(command_file, command_file)

                    self.commands[command_name] = command

        return self.commands

    def get_command(self, ctx, command_name):
        """Returns details about the specified command.

        Details include the callback to use when executing it, as well as other metadata.
        """

        if command_name not in self.commands.keys() or not self.commands[command_name]:
            return None

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
            rendered_tasks = render_dict(tasks, new_args)

            if isinstance(rendered_tasks, string_types):
                rendered_tasks = yaml.safe_load(rendered_tasks)

            # log.debug("Args: {}".format(new_args))
            log.debug("Vars: {}".format(final_vars))
            log.debug("Tasks to execute, with arguments replaced: {}".format(rendered_tasks))

            task_config = [{"vars": final_vars, "tasks": rendered_tasks}]

            log.debug("Final task config: {}".format(task_config))

            if ctx:
                hosts = list(ctx.params.get("host", ()))
                output = ctx.params.get("output", "default")
                ask_become_pass = ctx.params.get("ask_become_pass", "auto")
                no_run = ctx.params.get("no_run", False)

                if not hosts:
                    hosts = ["localhost"]

            else:
                output = "default"
                ask_become_pass = "auto"
                no_run = False
                hosts = ["localhost"]

            if no_run:
                parameters = create_and_run_nsbl_runner(task_config, task_metadata=metadata, output_format=output,
                                                        ask_become_pass=ask_become_pass, no_run=True, config=self.config, host_list=hosts)
                print_task_list_detaizls(task_config, task_metadata=metadata, output_format=output,
                                        ask_become_pass=ask_become_pass, run_parameters=parameters)
                result = None
            else:
                result = create_and_run_nsbl_runner(task_config, task_metadata=metadata, output_format=output,
                                                    ask_become_pass=ask_become_pass, config=self.config, run_box_basics=True, hosts_list=hosts)
                # create_and_run_nsbl_runner(task_config, output, ask_become_pass)

            return result

        help = doc.get("help", "n/a")
        short_help = doc.get("short_help", help)
        epilog = doc.get("epilog", DEFAULT_COMMAND_EPILOG)

        command = click.Command(command_name, params=options_list, help=help, short_help=short_help, epilog=epilog,
                                callback=command_callback)
        return command

    def create_command(self, command_name, yaml_file):
        """Created the commandline options and arguments out of a frecklecutable."""

        log.debug("Loading command file '{}'...".format(yaml_file))

        chain = [UrlAbbrevProcessor(), EnsureUrlProcessor(), EnsurePythonObjectProcessor()]

        try:
            frkl_obj = Frkl(yaml_file, chain)
            config_content = frkl_obj.process(MergeDictResultCallback())
        except (Exception) as e:
            log.debug("Can't parse command file '{}'".format(yaml_file))
            click.echo("- can't parse command file '{}'".format(yaml_file))
            return None

        tasks = config_content.get("tasks", None)

        if not tasks:
            return None

        # extra_options = {'jack': 4098, 'sape': 4139}
        freck_defaults = {
                "path": os.path.abspath(yaml_file),
                "dir": os.path.abspath(os.path.dirname(yaml_file))
        }

        config_content.setdefault("defaults", {})["frecklecutable"] = freck_defaults

        cli_command = create_cli_command(config_content, command_name=command_name, command_path=yaml_file)
        return cli_command
