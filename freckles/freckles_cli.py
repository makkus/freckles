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
from .profiles import ProfileRepo, assemble_freckle_run, get_freckelize_option_set, BREAK_COMMAND_NAME
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

def create_cli_list(task_vars):

    if not isinstance(task_vars, dict):
        raise Exception("task vars need to be of type dict, not '{}'".format(type(task_vars)))

    result = []
    for key, value in task_vars.items():
        if key == "args":
            continue

        if not key.startswith("-"):
            key = "--{}".format(key)

        if key == "--ask-become-pass" or key == "-pw":
            value = str(value).lower()

        if isinstance(value, (list, dict)):
            for v in value:
                result.append(key)
                result.append(v)
        else:
            result.append(key)
            if value != "FLAG":
                result.append(value)

    if "ARGS" in task_vars.keys():
        for a in task_vars["ARGS"]:
            result.append(a)

    return result


@click.command()
@click.option('--use-repo', '-r', multiple=True, required=False, help="extra context repos to use")
@click.option("--no-run", help='don\'t execute frecklecute, only prepare environment and print task list', type=bool, is_flag=True, default=False, required=False)
@click.option("--output", "-o", required=False, default="default", metavar="FORMAT", type=click.Choice(SUPPORTED_OUTPUT_FORMATS), help="format of the output")
@click.option("--version", help='prints the version of freckles', type=bool, is_flag=True, is_eager=True, expose_value=False, callback=print_version)

@click.argument('script', nargs=-1, required=True)
@click.pass_context
def cli(ctx, use_repo, no_run, output, script):
    """'freckles' command line interface"""

    ctx.obj = {}
    ctx.obj["config"] = DEFAULT_FRECKLES_CONFIG
    download_extra_repos(ctx, None, use_repo)
    current_command = None
    current_command_path = None

    chain = [frkl.UrlAbbrevProcessor(), frkl.EnsureUrlProcessor(), frkl.EnsurePythonObjectProcessor(), frkl.FrklProcessor(DEFAULT_FRECKLES_COMMAND_FORMAT)]

    frkl_obj = frkl.Frkl(script, chain)
    commands = frkl_obj.process()

    for item in commands:

        command = item["command"]
        command_name = command["name"]
        command_type = command.get("type", None)

        if not command_type:
            if "freckle" in item.get("vars", {}).keys():
                command_type = 'freckelize'
            else:
                command_type = 'frecklecute'

        # ask_become_pass = item.get("vars", {}).pop("ask-become-pass", False)
        # if not ask_become_pass:
        #     ask_become_pass = item.get("vars", {}).pop("--ask-become-pass", False)
        #     if not ask_become_pass:
        #         ask_become_pass = item.get("vars", {}).pop("-pw", False)

        arguments = create_cli_list(item.get("vars", {}))

        if command_type == 'frecklecute':

            command_title = command.get("title", "frecklecutable: {}".format(command_name))
            if os.path.exists(command_name):
                command_path = os.path.abspath(command_name)
            else:
                command_path = None

            cli_command = FrecklecuteCommand((command_name, command_path), config=DEFAULT_FRECKLES_CONFIG, help=FRECKLECUTE_HELP_TEXT, epilog=FRECKLECUTE_EPILOG_TEXT)

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
                vars_msg = "     x> " + pprint.pformat(item.get("vars", {})).replace("\n", "     x> \n")
                click.echo(vars_msg)
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


        if exit_code > 0 and no_run != True:
            if command_type == "frecklecute":
                msg = "   xxx> 'frecklecutable' '{}' failed. Used vars:\n".format(command_name)
            else:
                msg = "   xxx> 'freckelize' using adapter '{}' failed. Used vars:\n".format(command_name)

            click.echo(msg)
            vars_msg = "     x> " + pprint.pformat(item.get("vars", {})).replace('\n', '\n     x> ')
            click.echo(vars_msg)
            click.echo("\nExiting...\n")

            sys.exit(exit_code)

if __name__ == "__main__":
    cli()
