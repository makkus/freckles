from __future__ import absolute_import, division, print_function

import inspect

import click
import sys

from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.python import PythonLexer
from ruamel.yaml import YAML

from frutils import reindent
from frutils.jinja2_filters import (
    ALL_FILTERS,
    ALL_DEFAULT_JINJA2_FILTERS,
    ALL_FRUTIL_FILTERS,
)

yaml = YAML()


@click.group(name="filter")
@click.pass_context
def filter(ctx):
    """jinja2-related tasks and information"""

    pass
    # context = ctx.obj["context"]
    # control_dict = ctx.obj["control_dict"]
    #
    # context.set_control_vars(control_vars=control_dict)


@filter.command("list", short_help="list all jinja filters")
@click.option(
    "--all", "-a", help="also show default jinja2 filters", is_flag=True, required=False
)
@click.option(
    "--only-jinja-default",
    "-j",
    help="only show default jinja2 filters",
    is_flag=True,
    required=False,
)
@click.pass_context
def list_filters(ctx, all, only_jinja_default):

    if all and only_jinja_default:
        click.echo(
            "'--all' and '--only-jinja-default' options can't be used together. Choose one."
        )
        sys.exit(1)

    if all:
        filters = ALL_FILTERS
    elif only_jinja_default:
        filters = ALL_DEFAULT_JINJA2_FILTERS
    else:
        filters = ALL_FRUTIL_FILTERS

    click.echo()

    for filter_name, filter_details in sorted(filters.items()):
        print(filter_name)


@filter.command("info", short_help="show filter information")
@click.option("--details", "-d", help="show full details for this filter", is_flag=True)
@click.argument("filter_name", nargs=1, required=True)
def filter_info(filter_name, details):
    """Shows information about a jinja filter.
    """

    filter = ALL_FILTERS.get(filter_name, None)

    click.echo()
    if filter is None:
        click.echo("No filter '{}' available.")
        sys.exit()

    click.secho(filter_name, bold=True)
    click.echo()
    if details:
        click.secho("  Description:", bold=True)
    click.echo(filter["doc"].get_help())
    if details:
        click.secho("  Source:", bold=True)
        src = inspect.getsource(filter["func"])
        click.echo()
        if not src:
            click.echo("n/a")
        else:
            indented = reindent(src, 4)
            click.echo(highlight(indented, PythonLexer(), Terminal256Formatter()))
