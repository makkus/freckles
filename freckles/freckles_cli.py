# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
import os
import pprint
import sys

import click
from six import string_types

import yaml

from . import __version__ as VERSION
from .commands import CommandRepo
from .utils import (RepoType, create_and_run_nsbl_runner, create_freckle_desc,
                    find_profile_files_callback, find_supported_profiles,
                    get_profile_dependency_roles, url_is_local)

try:
    set
except NameError:
    from sets import Set as set

log = logging.getLogger("freckles")

# TODO: this is ugly, probably have refactor how role repos are used
SUPPORTED_PKG_MGRS = ["auto", "conda", "nix"]
SUPPORTED_OUTPUT_FORMATS = ["default", "ansible", "skippy", "verbose", "default_full"]

@click.command()
@click.version_option(version=VERSION, message="%(version)s")
@click.option('--no-run', help='only creates the playbook environment, does not run it)', is_flag=True, default=False, flag_value=True)
@click.option('--no-ask-pass', help='force not asking the user for a sudo password, if not specified freckles will try to do an educated guess (which could potentially fail)', is_flag=True, default=False, flag_value=True)
@click.option('--force-ask-pass', help='force asking the user for a sudo password, if not specified freckles will try to do an educated guess (which could potentially fail)', is_flag=True, default=False, flag_value=True)
@click.option('--profile', '-p', help='ignore remote freckle profile(s), force using this/those one(s)', multiple=True, metavar='PROFILE', default=[], type=click.Choice(find_supported_profiles()))
@click.option('--format', '-f', help='format of the output', multiple=False, metavar='FORMAT', default="default", type=click.Choice(SUPPORTED_OUTPUT_FORMATS))
@click.option('--target', '-t', help='target folder for freckle checkouts (if remote url provided), defaults to folder \'freckles\' in users home', type=str, metavar='PATH')
@click.option('--local-target-folder', help='in case only one freckle url is provided and the target folder should have a different basename, this option can be used to specify the full local path', required=False)
@click.option('--include', '-i', help='if specified, only process folders that end with one of the specified strings', type=str, metavar='FILTER_STRING', default=[], multiple=True)
@click.option('--exclude', '-e', help='if specified, omit process folders that end with one of the specified strings, takes precedence over the include option if in doubt', type=str, metavar='FILTER_STRING', default=[], multiple=True)
@click.option('--pkg-mgr', '-p', help="default package manager to use", type=click.Choice(SUPPORTED_PKG_MGRS), default="auto", multiple=False, required=False)
@click.argument("freckle_urls", required=True, type=RepoType(), nargs=-1, metavar="URL_OR_PATH")
def cli(freckle_urls, profile, include, exclude, target, local_target_folder, pkg_mgr, no_ask_pass, force_ask_pass, format, no_run):
    """Freckles manages your dotfiles (and other aspects of your local machine).

    For information about how to use and configure Freckles, please visit: XXX
    """

    if force_ask_pass and no_ask_pass:
        click.echo("'--force-ask-pass' and '--no-ask-pass' can't be specified at the same time.")
        sys.exit(1)

    target_is_parent = True

    if local_target_folder:

        if target:
            click.echo("'--target/-t' and '--local-target-folder' options can't be used at the same time")
            sys.exit(1)
        if len(freckle_urls) > 1:
            click.echo("'--local-target-folder' can only be used when exactly one freckle url is provided")
            sys.exit(1)

        else:
            target = local_target_folder
            target_is_parent = False

    if not target:
        target = "~/freckles"

    repos = []

    for freckle_url in freckle_urls:

        freckle_repo = create_freckle_desc(freckle_url, target, target_is_parent, profiles=profile, includes=include, excludes=exclude)
        repos.append(freckle_repo)

    callback = find_profile_files_callback("tasks.yml")
    additional_roles = get_profile_dependency_roles(profile)

    sys.exit(0)

    task_config = [{"vars": {"freckles": repos, "pkg_mgr": pkg_mgr}, "tasks": ["freckles"]}]

    if force_ask_pass:
        n_ask_pass = False
    elif no_ask_pass:
        n_ask_pass = True
    else:
        n_ask_pass = False

    create_and_run_nsbl_runner(task_config, format, no_ask_pass=n_ask_pass, pre_run_callback=callback, no_run=no_run, additional_roles=additional_roles)

if __name__ == "__main__":
    cli()
