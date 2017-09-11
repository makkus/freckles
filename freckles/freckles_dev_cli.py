# -*- coding: utf-8 -*-

import json
import os
import pprint
import subprocess
import sys

import click
from frkl import frkl

import click_log
import yaml

from nsbl import defaults, tasks
from .freckles_defaults import *
from . import __version__ as VERSION
from .utils import get_all_roles_in_repos, get_all_adapters_in_repos, find_adapter_files, get_adapter_dependency_roles
from .commands import CommandRepo


def output(python_object, format="raw", pager=False):

    if format == 'yaml':
        output_string = yaml.safe_dump(python_object, default_flow_style=False, encoding='utf-8', allow_unicode=True)
    elif format == 'json':
        output_string = json.dumps(python_object, sort_keys=4, indent=4)
    elif format == 'raw':
        output_string = str(python_object)
    elif format == 'pformat':
        output_string = pprint.pformat(python_object)
    else:
        raise Exception("No valid output format provided. Supported: 'yaml', 'json', 'raw', 'pformat'")

    if pager:
        click.echo_via_pager(output_string)
    else:
        click.echo(output_string)


@click.group(invoke_without_command=True)
@click.option('--version', help='the version of frkl you are using', is_flag=True)
@click.pass_context
def cli(ctx, version):
    """Console script for nsbl"""

    if version:
        click.echo(VERSION)
        sys.exit(0)


@cli.command('debug-last')
@click.option('--pager', '-p', required=False, default=False, is_flag=True, help='output via pager')
@click.pass_context
def debug_last(ctx, pager):
    """Lists all groups and their variables"""

    last_run_folder = os.path.expanduser("~/.freckles/runs/current")

    last_run_debug_folder = os.path.join(last_run_folder, "debug")
    last_run_debug_script = os.path.join(last_run_debug_folder, "debug_all_plays.sh")

    run_env = os.environ.copy()

    proc = subprocess.Popen(last_run_debug_script, stdout=subprocess.PIPE, stderr=sys.stdout.fileno(), stdin=subprocess.PIPE, shell=True, env=run_env)

    for line in iter(proc.stdout.readline, ''):
        click.echo(line, nl=False)

@cli.command('list-roles')
@click.pass_context
def list_roles(ctx):

    repos = ["default"]
    # role_repos = defaults.calculate_role_repos([get_real_repo_path(REPO_ABBREVS, r) for r in repos], use_default_roles=False)

    roles = get_all_roles_in_repos(repos)

    print("Roles:")
    pprint.pprint(roles)

    print("")
    adapters = get_all_adapters_in_repos(repos)
    print("Adapters")
    pprint.pprint(adapters)


@cli.command('frecklecute-command')
@click.option('--command', '-c', help="the command to debug", required=True)
@click.option('--args-file', '-f', help="the file containing example args", type=click.File(), required=False, default=None)
@click.pass_context
def debug_frecklecute_command(ctx, command, args_file):

    if args_file:
        args = yaml.safe_load(args_file)
        print(args)
    else:
        args = {}

    if os.path.exists(command):
        current_command = command
        current_command_path = os.path.abspath(command)
    else:
        current_command = None
        current_command_path = None

    repo = CommandRepo(no_run=True, additional_commands=[(current_command, current_command_path)])
    command = repo.get_command(None, command)

    command.callback(**args)
