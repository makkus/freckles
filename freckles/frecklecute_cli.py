# -*- coding: utf-8 -*-

import logging
import os
import sys

import click

from nsbl.nsbl import Nsbl, NsblRunner

from . import __version__ as VERSION

log = logging.getLogger("freckles")

@click.command()
@click.option('--role-repo', '-r', help='path to a local folder containing ansible roles', multiple=True)
@click.option('--task-desc', '-t', help='path to a local task description yaml file', multiple=True)
@click.option('--version', help='the version of freckles you are running', is_flag=True)
@click.option('--stdout-callback', '-c', help='name of or path to callback plugin to be used as default stdout plugin', default="nsbl_internal")
# @click.option('--static/--dynamic', default=True, help="whether to render a dynamic inventory script using the provided config files instead of a plain ini-type config file and group_vars and host_vars folders, default: static")
@click.argument("config", nargs=-1)
def cli(version, config, stdout_callback, role_repo, task_desc):

    if version:
        click.echo(VERSION)
        sys.exit(0)

    target = os.path.expanduser("~/.freckles/run")
    force = True
    nsbl = Nsbl.create(config, role_repo, task_desc, wrap_into_localhost_env=True)

    runner = NsblRunner(nsbl)
    runner.run(target, force, "", stdout_callback)


if __name__ == "__main__":
    cli()
