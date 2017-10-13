# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging

import click
from  frkl import frkl
import nsbl
import pprint
import textwrap
import sys

from . import print_version
from .freckles_defaults import *
from .frecklecute_cli import FrecklecuteCommand, FRECKLECUTE_HELP_TEXT, FRECKLECUTE_EPILOG_TEXT
from .freckelize_cli import FreckelizeCommand, FRECKELIZE_HELP_TEXT, FRECKELIZE_EPILOG_TEXT
from .profiles import ProfileRepo, assemble_freckle_run, get_freckles_option_set, BREAK_COMMAND_NAME
from .utils import DEFAULT_FRECKLES_CONFIG, RepoType, download_extra_repos

try:
    set
except NameError:
    from sets import Set as set

log = logging.getLogger("freckles")

# TODO: this is a bit ugly, probably have refactor how role repos are used
nsbl.defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")

FRECKLES_HELP_TEXT = """Run a series of freckelize and/or frecklecute commands as a script."""

FRECKLES_EPILOG_TEXT = "freckles is free and open source software, for more information visit: https://docs.freckles.io"

def create_cli_list(vars, current_result):

    if isinstance(vars, dict):

        for key, value in vars.items():
            if key != "args":
                if not key.startswith("-"):
                    key = "--{}".format(key)
                current_result.append(key)
                current_result.append(value)

        if "args" in vars.keys():
            if not isinstance(vars["args"], (list, tuple)):
                current_result.append(vars["args"])
            else:
                for v in vars["args"]:
                    current_result.append(v)

    elif isinstance(vars, (list, tuple)):

        for v in vars:
            if isinstance(v, dict):
                create_cli_list(v, current_result)
            elif isinstance(v, string_types):
                if not v.startswith("-"):
                    v = "--{}".format(v)

                current_result.append(v)


@click.command()
@click.option('--use-repo', '-r', multiple=True, required=False, help="extra context repos to use")
@click.option("--ask-become-pass", "-pw", help='whether to force ask for a password, force ask not to, or let try freckles decide (which might not always work)', type=click.Choice(["auto", "true", "false"]), default="auto")
@click.option("--no-run", help='don\'t execute frecklecute, only prepare environment and print task list', type=bool, is_flag=True, default=False, required=False)
@click.option("--output", "-o", required=False, default="default", metavar="FORMAT", type=click.Choice(SUPPORTED_OUTPUT_FORMATS), help="format of the output")
@click.argument('script', nargs=-1, required=True)
@click.pass_context
def cli(ctx, use_repo, ask_become_pass, no_run, output, script):
    """'freckles' command line interface"""

    ctx.obj = {}
    ctx.obj["config"] = DEFAULT_FRECKLES_CONFIG
    download_extra_repos(ctx, None, use_repo)
    current_command = "create-adapter"
    current_command_path = None

    chain = [frkl.UrlAbbrevProcessor(), frkl.EnsureUrlProcessor(), frkl.EnsurePythonObjectProcessor(), frkl.FrklProcessor(DEFAULT_FRECKLES_COMMAND_FORMAT)]

    frkl_obj = frkl.Frkl(script, chain)
    commands = frkl_obj.process()

    pprint.pprint(commands)

    for item in commands:

        command = item["command"]
        command_name = command["name"]
        command_type = command.get("type", None)

        if not command_type:
            if "freckle" in item.get("vars", {}).keys():
                command_type = 'freckelize'
            else:
                command_type = 'frecklecute'

        arguments = []
        create_cli_list(item.get("vars", {}), arguments)

        if command_type == 'frecklecute':

            command_title = command.get("title", "frecklecutable: {}".format(command_name))

            cli_command = FrecklecuteCommand((current_command, current_command_path), config=DEFAULT_FRECKLES_CONFIG, help=FRECKLECUTE_HELP_TEXT, epilog=FRECKLECUTE_EPILOG_TEXT)

            click.echo("\n# Executing {}...".format(command_title))
            c = cli_command.get_command(ctx, command_name)
            if not c:
                click.echo("Could not find frecklecutable '{}'. Exiting...".format(command_name))
                sys.exit(1)
            r = c.main(args=arguments, prog_name=command_title, standalone_mode=False)
            exit_code = r["return_code"]

        elif command_type == 'freckelize':
            command_title = command.get("title", "freckelize adapter '{}'".format(command_name))

            cli_command = FreckelizeCommand(DEFAULT_FRECKLES_CONFIG, chain=True, help=FRECKELIZE_HELP_TEXT, epilog=FRECKELIZE_EPILOG_TEXT)

            c = cli_command.get_command(ctx, command_name)
            if not c:
                click.echo("Could not find adapter '{}'. Exiting...".format(command_name))
                sys.exit(1)
            parse_cli_result = c.main(args=arguments, prog_name=command_title, standalone_mode=False)

            if not parse_cli_result.get("vars", {}).get("freckle", False):

                msg = "   xxx> no value for key 'freckle' specified in freckelize run '{}'".format(command_name)
                click.echo(msg)
                vars_msg = pprint.pformat(item.get("vars", {}))
                wrapper=textwrap.TextWrapper(initial_indent='      x> ', subsequent_indent='      x> ')
                click.echo(wrapper.fill(vars_msg))
                click.echo("\nExiting...\n")
                sys.exit(1)

            click.echo("\n# Applying {}...".format(command_title))
            result = cli_command.result_callback(*[[parse_cli_result]])

            if not result:
                raise Exception("No result")
            if no_run != True:
                exit_code = result[0]["return_code"]

        else:
            click.echo("Command type '{}' not supported.".format(command_type))
            sys.exit(1)


        if exit_code != 0 and no_run != True:
            if command_type == "frecklecute":
                msg = "   xxx> 'frecklecutable' '{}' failed. Used vars:\n".format(command_name)
            else:
                msg = "   xxx> 'freckelize' using adapter '{}' failed. Used vars:\n".format(command_name)

            click.echo(msg)
            vars_msg = pprint.pformat(vars)
            wrapper=textwrap.TextWrapper(initial_indent='      x> ', subsequent_indent='      x> ')
            click.echo(wrapper.fill(vars_msg))
            click.echo("\nExiting...\n")

            sys.exit(exit_code)

if __name__ == "__main__":
    cli()
