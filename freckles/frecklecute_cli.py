# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
import sys

import click
import nsbl
from frkl import frkl

from . import print_version
from .commands import CommandRepo
from .freckles_defaults import *
from .utils import DEFAULT_FRECKLES_CONFIG, download_extra_repos, HostType

log = logging.getLogger("freckles")

# TODO: this is a bit ugly, probably have refactor how role repos are used
nsbl.defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")
# EXTRA_FRECKLES_PLUGINS = os.path.abspath(os.path.join(os.path.dirname(__file__), "external", "freckles_extra_plugins"))

FRECKLECUTE_HELP_TEXT = """Executes a list of tasks specified in a (yaml-formated) text file (called a 'frecklecutable').

*frecklecute* comes with a few default frecklecutables that are used to manage itself (as well as its sister application *freckles*) as well as a few useful generic ones. Visit the online documentation for more details: https://docs.freckles.io/en/latest/frecklecute_command.html
"""
FRECKLECUTE_EPILOG_TEXT = "frecklecute is free and open source software and part of the 'freckles' project, for more information visit: https://docs.freckles.io"

COMMAND_PROCESSOR_CHAIN = [
    frkl.UrlAbbrevProcessor()
]

# we need the current command to dynamically add it to the available ones
current_command = None
current_command_path = None

# temp_repo = CommandRepo(paths=[], additional_commands=[], no_run=True)
# command_list = temp_repo.get_commands().keys()

VALID_CLI_OPTIONS = ["-r", "--use-repo", "-o", "--output", "-pw", "--ask-become-pass", "--host"]


if sys.argv[0].endswith("frecklecute"):

    last_opt = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    for arg in sys.argv[1:]:

        if arg.startswith("-"):
            last_opt = arg
            continue

            # if arg in command_list:
            # current_command = None
            # current_command_path = None
            # break

        if last_opt in VALID_CLI_OPTIONS:
            last_opt = arg
            continue

        if os.path.exists(arg) and os.path.isfile(os.path.abspath(arg)):
            current_command = arg
            current_command_path = os.path.abspath(arg)
            # frkl_obj = frkl.Frkl(current_command, COMMAND_PROCESSOR_CHAIN)
            # current_command = frkl_obj.process()[0]
            break

        # frkl_obj = frkl.Frkl(arg, [
            # frkl.UrlAbbrevProcessor(init_params={"abbrevs": frkl.DEFAULT_ABBREVIATIONS, "add_default_abbrevs": False, "verbose": True})])
        # result = frkl_obj.process()

        current_command = arg
        current_command_path = None
        break

class FrecklecuteCommand(click.MultiCommand):

    def __init__(self, current_command, config, **kwargs):
        """Base class to provide a command-based (similar to e.g. git) cli for frecklecute.

        This class parses the folders in the paths provided by the config
        element for so-called 'frecklecutables', (yaml) text files that contain a list of tasks and optionally command-line argument descriptions. More information: XXX

        Args:
          current_command (tuple): a tuple in the format (command_name, command_path), which is used for commands that are paths, instead of filenames in one of the known frecklecutable paths. Can be (None, None) if not a path.
          config (FrecklesConfig): the config wrapper object
          kwargs (dict): additional arguments that are forwarded to the partent click.MultiCommand constructor
        """

        click.MultiCommand.__init__(self, "freckles", **kwargs)

        host_option = click.Option(param_decls=["--host"], required=False, multiple=True, help="host(s) to freckelize (defaults to 'localhost')", is_eager=False, type=HostType())
        output_option = click.Option(param_decls=["--output", "-o"], required=False, default="default",
                                     metavar="FORMAT", type=click.Choice(SUPPORTED_OUTPUT_FORMATS),
                                     help="format of the output", is_eager=True)
        ask_become_pass_option = click.Option(param_decls=["--ask-become-pass", "-pw"],
                                              help='whether to force ask for a password, force ask not to, or let try freckles decide (which might not always work)',
                                              type=click.Choice(["auto", "true", "false"]), default="auto")
        version_option = click.Option(param_decls=["--version"], help='prints the version of freckles', type=bool,
                                      is_flag=True, is_eager=True, expose_value=False, callback=print_version)
        no_run_option = click.Option(param_decls=["--no-run"],
                                     help='don\'t execute frecklecute, only prepare environment and print task list',
                                     type=bool, is_flag=True, default=False, required=False)
        use_repo_option = click.Option(param_decls=["--use-repo", "-r"], required=False, multiple=True, help="extra context repos to use", is_eager=True, callback=download_extra_repos, expose_value=True)

        self.params = [use_repo_option, host_option, output_option, ask_become_pass_option, no_run_option, version_option]

        self.config = config
        # .trusted_repos = DEFAULT_FRECKLES_CONFIG.trusted_repos
        # local_paths = get_local_repos(trusted_repos, "frecklecutables")

        self.command_repo = CommandRepo(config=self.config, additional_commands=[current_command])
        self.current_command = current_command[0]


    def list_commands(self, ctx):
        """Lists all commands (frecklecutables) that are available
        """

        self.command_names = self.command_repo.get_commands().keys()
        self.command_names.sort()
        if self.current_command:
            self.command_names.insert(0, self.current_command)

        self.commands = {}
        for name in self.command_names:
            self.commands[name] = self.get_command(None, name)


        return self.command_names

    def get_command(self, ctx, name):
        """Return details about the provided command."""

        if name in self.command_repo.get_commands().keys():
            return self.command_repo.get_command(ctx, name)

        else:
            return None


click.core.SUBCOMMAND_METAVAR = 'FRECKLECUTABLE [ARGS]...'
click.core.SUBCOMMANDS_METAVAR = 'FRECKLECUTABLE1 [ARGS]... [FRECKLECUTABLE2 [ARGS]...]...'

cli = FrecklecuteCommand((current_command, current_command_path), config=DEFAULT_FRECKLES_CONFIG, help=FRECKLECUTE_HELP_TEXT,
                      epilog=FRECKLECUTE_EPILOG_TEXT)

if __name__ == "__main__":
    cli()
