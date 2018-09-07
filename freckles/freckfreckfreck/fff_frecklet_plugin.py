from __future__ import absolute_import, division, print_function

import logging
import sys

import click
from ruamel.yaml import YAML

from freckles.freckles_runner import FrecklesRunner
from frutils.frutils_cli import output
from luci.luitem_index import LuItemMultiIndex

yaml = YAML(typ="safe")

log = logging.getLogger("freckles")


@click.group("frecklet")
def frecklet():
    """command-group for tasks related to the last run"""

    pass


@frecklet.command("describe")
@click.argument("frecklecutable", metavar="FRECKLECUTABLE", nargs=1)
@click.pass_context
def describe_frecklecutable(ctx, frecklecutable):

    context = ctx.obj["context"]
    control_dict = {
        "no_run": True,
        "host": "localhost",
        "output": "default",
        "elevated": "not_elevated",
    }

    try:
        runner = FrecklesRunner(context, control_vars=control_dict)
        runner.load_frecklecutable_from_name_or_file(frecklecutable)

        runner.describe_tasklist()
        sys.exit(0)
    except (Exception) as e:
        click.echo()
        click.echo(e)


@frecklet.command("print")
@click.argument("frecklet_name", metavar="FRECKLET_NAME", nargs=1)
@click.pass_context
def print(ctx, frecklet_name):

    click.echo()

    context = ctx.obj["context"]
    index = context.index

    p = index.get_pkg(frecklet_name)
    if p is None:
        click.echo("No frecklet available for name: {}".format(frecklet_name))
        sys.exit(1)

    output(p.metadata, output_type="yaml")


@frecklet.command("list")
@click.option(
    "--connector",
    "-c",
    help="only list frecklets for specified connector",
    required=False,
)
@click.option(
    "--details", "-d", help="display frecklet details", is_flag=True, default=False
)
@click.option(
    "--filter",
    "-f",
    help="only display frecklets that match the provided filter(s)",
    multiple=True,
)
@click.pass_context
def list_frecklets(ctx, connector, details, filter):
    """Lists all available frecklets."""

    click.echo()

    context = ctx.obj["context"]

    if connector:
        indexes = context.connector_indexes.get(connector, [])
        index = LuItemMultiIndex(
            item_type="frecklet", indexes=indexes, alias="nsbl_indexes"
        )
    else:
        index = context.index

    pkgs = []
    for r in index.get_pkg_names():
        match = True
        for f in filter:
            if f not in r:
                match = False
                break
        if match:
            pkgs.append(r)

    for n in pkgs:

        if not details:
            click.echo(n)
        else:
            click.secho(n, bold=True)
            click.echo()
            p = index.get_pkg(n)
            output(p.metadata, output_type="yaml", indent=2)
