# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
import os
import sys

import click
import nsbl

import yaml

from . import __version__ as VERSION
from .commands import CommandRepo
from .freckles import freckles

log = logging.getLogger("freckles")

# TODO: this is ugly, probably have refactor how role repos are used
nsbl.defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")
EXTRA_FRECKLES_PLUGINS = os.path.abspath(os.path.join(os.path.dirname(__file__), "external", "freckles_extra_plugins"))

# we need the current command to dynamically add it to the available ones
current_command = None
for arg in sys.argv[1:]:

    if arg.startswith("-"):
        continue

    current_command = arg
    break

FRECKLES_HELP_TEXT = "TO BE DONE"
FRECKLES_EPILOG_TEXT = "For more information please visit: https://frkl.io"

class FrecklesCommand(click.MultiCommand):

    def __init__(self, current_command, command_repos=[], **kwargs):

        click.MultiCommand.__init__(self, "freckles", **kwargs)

        debug_option = click.Option(param_decls=["--debug", "-d"], required=False, default=False, is_flag=True)
        self.params = [debug_option]

        self.command_repo = CommandRepo(command_repos)
        self.current_command = current_command
        self.command_names = self.command_repo.commands.keys()
        self.command_names.sort()
        if self.current_command:
            self.command_names.insert(0, self.current_command)

    def list_commands(self, ctx):

        return self.command_names

    def get_command(self, ctx, name):

        if name in self.command_repo.commands.keys():
            return self.command_repo.get_command(ctx, name)

        else:
            return None

cli = FrecklesCommand(current_command, help=FRECKLES_HELP_TEXT, epilog=FRECKLES_EPILOG_TEXT)

if __name__ == "__main__":
    cli()
