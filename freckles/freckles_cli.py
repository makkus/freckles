# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
import os
import pprint
import sys

import click
from six import string_types

import yaml
from .freckles_defaults import *
from . import __version__ as VERSION
from .profiles import ProfileRepo, assemble_freckle_run
from .utils import (RepoType, create_and_run_nsbl_runner, create_freckle_desc,
                    find_profile_files_callback, find_supported_profiles,
                    get_profile_dependency_roles, url_is_local, DEFAULT_FRECKLES_CONFIG)

try:
    set
except NameError:
    from sets import Set as set

log = logging.getLogger("freckles")

FRECKLES_HELP_TEXT = "n/a"
FRECKLES_EPILOG_TEXT = "n/a"

# TODO: this is ugly, probably have refactor how role repos are used
SUPPORTED_PKG_MGRS = ["auto", "conda", "nix"]

class FrecklesProfiles(click.MultiCommand):

    def __init__(self, config, **kwargs):

        click.MultiCommand.__init__(self, "freckles", result_callback=assemble_freckle_run, invoke_without_command=True, **kwargs)

        output_option = click.Option(param_decls=["--output", "-o"], required=False, default="default", metavar="FORMAT", type=click.Choice(SUPPORTED_OUTPUT_FORMATS), help="format of the output")
        freckle_option = click.Option(param_decls=["--freckle", "-f"], required=True, multiple=True, type=RepoType(), metavar="URL_OR_PATH", help="the url or path to the freckle(s) to use")
        target_option = click.Option(param_decls=["--target", "-t"], required=False, multiple=False, type=str, metavar="PATH", help='target folder for freckle checkouts (if remote url provided), defaults to folder \'freckles\' in users home')
        include_option = click.Option(param_decls=["--include", "-i"], help='if specified, only process folders that end with one of the specified strings, only applicable for multi-freckle folders', type=str, metavar='FILTER_STRING', default=[], multiple=True)
        exclude_option = click.Option(param_decls=["--exclude", "-e"], help='if specified, omit process folders that end with one of the specified strings, takes precedence over the include option if in doubt, onlyapplicable for multi-freckle folders', type=str, metavar='FILTER_STRING', default=[], multiple=True)

        ask_become_pass_option = click.Option(param_decls=["--ask-become-pass"], help='whether to force ask for a password, force ask not to, or let try freckles decide (which might not always work)', type=click.Choice(["auto", "true", "false"]), default="true")

        self.params = [freckle_option, target_option, include_option, exclude_option, output_option, ask_become_pass_option]
        self.profile_repo = ProfileRepo(config, no_run=False)
        self.command_names = self.profile_repo.profiles.keys()
        self.command_names.sort()

    def list_commands(self, ctx):

        return self.command_names

    def get_command(self, ctx, name):

        if name in self.profile_repo.profiles.keys():
            return self.profile_repo.get_command(ctx, name)
        else:
            return None

cli = FrecklesProfiles(DEFAULT_FRECKLES_CONFIG, chain=True,  help=FRECKLES_HELP_TEXT, epilog=FRECKLES_EPILOG_TEXT)

print

if __name__ == "__main__":
    cli()
