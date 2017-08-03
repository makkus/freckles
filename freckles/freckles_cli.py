# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
import os
import pprint
import sys

import click
import nsbl
from nsbl.nsbl import Nsbl, NsblRunner, ensure_git_repo_format

import yaml

from . import __version__ as VERSION
from .commands import CommandRepo, RepoType

log = logging.getLogger("freckles")

# TODO: this is ugly, probably have refactor how role repos are used
nsbl.defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")

SUPPORTED_PKG_MGRS = ["auto", "conda", "nix"]

def url_is_local(url):

    if url.startswith("~") or url.startswith(os.sep):
        return True
    return os.path.exists(os.path.expanduser(url))

def find_supported_profiles():

    task_folder = os.path.join(os.path.dirname(__file__), "external", "default_role_repo", "makkus.freckles", "tasks")

    files = os.listdir(task_folder)

    profiles = [f[:-4] for f in files if os.path.isfile(os.path.join(task_folder, f)) and f.endswith("yml") and f != "main.yml"]
    return profiles

@click.command()
@click.version_option(version=VERSION, message="%(version)s")
@click.option('--no-ask-pass', help='force not asking the user for a sudo password, if not specified freckles will try to do an educated guess (which could potentially fail)', is_flag=True, default=False, flag_value=True)
@click.option('--profile', '-p', help='ignore remote freckle profile(s), force using this/those one(s)', multiple=True, metavar='PROFILE', default=[], type=click.Choice(find_supported_profiles()))
@click.option('--target', '-t', help='target folder for freckle checkouts (if remote url provided), defaults to folder \'freckles\' in users home', type=str, metavar='PATH')
@click.option('--local-target-folder', help='in case only one freckle url is provided and the target folder should have a different basename, this option can be used to specify the full local path', required=False)
@click.option('--folder_filter', '-f', help='if specified, only process folders that end with one of the specified strings', type=str, metavar='FILTER_STRING', default=[])
@click.option('--debug', '-d', help="debug output, using ansible default callback", default=False, is_flag=True)
@click.option('--pkg-mgr', '-p', help="default package manager to use", type=click.Choice(SUPPORTED_PKG_MGRS), default="auto", multiple=False, required=False)
@click.argument("freckle_urls", required=True, type=RepoType(), nargs=-1, metavar="URL_OR_PATH")
def cli(freckle_urls, profile, folder_filter, target, local_target_folder, pkg_mgr, no_ask_pass, debug):
    """Freckles manages your dotfiles (and other aspects of your local machine).

    For information about how to use and configure Freckles, please visit: XXX
    """

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

        freckle_repo = {}

        is_local = url_is_local(freckle_url)

        if is_local:
            freckle_repo["path"] = os.path.abspath(freckle_url)
            freckle_repo["url"] = None
        else:
            repo = ensure_git_repo_format(freckle_url, target, target_is_parent)
            freckle_repo["path"] = repo["dest"]
            freckle_repo["url"] = repo["repo"]

        freckle_repo["profiles"] = profile
        freckle_repo["folder_filter"] = folder_filter

        repos.append(freckle_repo)

    # pprint.pprint(repos)
    # sys.exit(0)

    task_config = [{"vars": {"freckles": repos, "pkg_mgr": pkg_mgr}, "tasks": ["freckles"]}]

    nsbl_obj = Nsbl.create(task_config, [], [], wrap_into_localhost_env=True, pre_chain=[])
    runner = NsblRunner(nsbl_obj)
    run_target = os.path.expanduser("~/.freckles/runs/archive/run")
    if debug:
        stdout_callback = "default"
        ansible_verbose = "-vvvv"
    else:
        stdout_callback = "nsbl_internal"
        ansible_verbose = ""
    no_run = False
    force = True
    display_sub_tasks = True
    display_skipped_tasks = False
    ask_become_pass = not no_ask_pass
    runner.run(run_target, force=force, ansible_verbose=ansible_verbose, ask_become_pass=ask_become_pass, callback=stdout_callback, add_timestamp_to_env=True, add_symlink_to_env="~/.freckles/runs/current", no_run=no_run, display_sub_tasks=display_sub_tasks, display_skipped_tasks=display_skipped_tasks)

if __name__ == "__main__":
    cli()
