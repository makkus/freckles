# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging

import click

from . import print_version
from .freckles_defaults import *
from .profiles import ProfileRepo, assemble_freckle_run, get_freckelize_option_set, BREAK_COMMAND_NAME
from .utils import DEFAULT_FRECKLES_CONFIG, RepoType, download_extra_repos, HostType

try:
    set
except NameError:
    from sets import Set as set

log = logging.getLogger("freckles")

FRECKELIZE_HELP_TEXT = """Downloads a remote dataset or code (called a 'freckle') and sets up your local environment to be able to handle the data, according to the data's profile.

Ideally the remote dataset includes all the metadata that is needed to setup the environment, but it's possible to provide some directives using commandline options globally (--target, --include, --exclude), or per adapter (use the --help function on each adapter to view those).

Locally available adapters for supported profiles are listed below, each having their own configuration. You can specify a 'global' url by adding it's '--freckle' option before any of the subsequently specified adapters, prompting any of those adapters to apply their tasks to it. Or you can assign one (or multiple) freckle to an adapter by providing it after the adapter name.

For more details, visit the online documentation: https://docs.freckles.io/en/latest/freckelize_command.html
"""

FRECKELIZE_EPILOG_TEXT = "freckelize is free and open source software and part of the 'freckles' project, for more information visit: https://docs.freckles.io"


class FreckelizeCommand(click.MultiCommand):


    def __init__(self, config, **kwargs):
        """Base class to provide a command-based (similar to e.g. git) cli for freckles.

        This class parses the folders in the paths provided by the config
        element for so-called 'freckle adapters'. A freckle adapter is a
        collection of files that describe commandline-arguments and tasks lists
        to execute on a folder (more information: https://docs.freckles.io/en/latest/freckelize_command.html#adapters-profiles)

        Args:
          config (FrecklesConfig): the config wrapper object
          kwargs (dict): additional arguments that are forwarded to the partent click.MultiCommand constructor

        """

        click.MultiCommand.__init__(self, "freckles", result_callback=assemble_freckle_run, invoke_without_command=True,
                                    **kwargs)

        host_option = click.Option(param_decls=["--host"], required=False, multiple=True, help="host(s) to freckelize (defaults to 'localhost')", is_eager=False, type=HostType())
        use_repo_option = click.Option(param_decls=["--use-repo", "-r"], required=False, multiple=True, help="extra context repos to use", is_eager=True, callback=download_extra_repos)
        output_option = click.Option(param_decls=["--output", "-o"], required=False, default="default",
                                     metavar="FORMAT", type=click.Choice(SUPPORTED_OUTPUT_FORMATS), is_eager=True,
                                     help="format of the output")
        no_run_option = click.Option(param_decls=["--no-run"],
                                     help='don\'t execute frecklecute, only prepare environment and print task list',
                                     type=bool, is_flag=True, default=False, required=False)
        version_option = click.Option(param_decls=["--version"], help='prints the version of freckles', type=bool,
                                      is_flag=True, is_eager=True, expose_value=False, callback=print_version)


        self.params = get_freckelize_option_set()
        self.params.extend([ host_option, use_repo_option, output_option,  no_run_option, version_option])
        self.config = config

        self.profile_repo = ProfileRepo(self.config)

        # self.command_names.append(BREAK_COMMAND_NAME)


    def list_commands(self, ctx):

        self.command_names = self.profile_repo.get_profiles().keys()
        self.command_names.sort()

        self.commands = {}
        for name in self.command_names:
            self.commands[name] = self.get_command(None, name)

        return self.command_names

    def get_command(self, ctx, name):

        # if name == BREAK_COMMAND_NAME:
        #     def break_callback(**kwargs):
        #         return {"name": BREAK_COMMAND_NAME}
        #     return click.Command(BREAK_COMMAND_NAME, help="marker to start a new run", callback=break_callback)

        if name in self.profile_repo.get_profiles().keys():
            return self.profile_repo.get_command(ctx, name)
        else:
            return None


click.core.SUBCOMMAND_METAVAR = 'ADAPTER [ARGS]...'
click.core.SUBCOMMANDS_METAVAR = 'ADAPTER1 [ARGS]... [ADAPTER2 [ARGS]...]...'

cli = FreckelizeCommand(DEFAULT_FRECKLES_CONFIG, chain=True, help=FRECKELIZE_HELP_TEXT, epilog=FRECKELIZE_EPILOG_TEXT)

if __name__ == "__main__":
    cli()
