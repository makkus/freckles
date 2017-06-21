# -*- coding: utf-8 -*-

import click
import click_log
import logging
import sys

from freckles import Freckles

from . import __version__ as VERSION

log = logging.getLogger("freckles")

@click.group(invoke_without_command=True)
@click.pass_context
@click_log.simple_verbosity_option()
@click.option('--version', help='the version of freckles you are running', is_flag=True)
@click_log.init("freckles")
def cli(ctx, freckles_config, version):
    """Freckles manages your dotfiles (and other aspects of your local machine).

    The base options here are forwarded to all the sub-commands listed below. Not all of the sub-commands will use all of the options you can specify though.

    For information about how to use and configure Freckles, please visit: XXX
    """

    if version:
        click.echo(VERSION)
        sys.exit(0)

    freckles_config.load()

@cli.command("print-config")
@click.argument('config', required=False, nargs=-1)
def print_config(freckles_config, config):
    """Flattens overlayed configs and prints result.
       This is useful mostly for debugging purposes, when creating the configuration.

       The output to this command could be piped into a yaml file, and then used with the ``run`` command. Although, in practice that doesn't make much sense of course. """

    freckles = Freckles(*config)
    leafs = freckles.leafs


    # if ctx.invoked_subcommand is None:
        # run(config)

if __name__ == "__main__":
    cli()
