# -*- coding: utf-8 -*-

import json
import os
import pprint
import subprocess
import sys

import click

import click_log
import yaml
from frkl import frkl

from . import __version__ as VERSION


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
@click_log.simple_verbosity_option()
@click.pass_context
@click_log.init("freckles")
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
