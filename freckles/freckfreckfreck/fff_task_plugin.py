from __future__ import absolute_import, division, print_function

import logging
import sys

import click
from frutils.doc import Doc
from rst2ansi import rst2ansi
from ruamel.yaml import YAML

from freckles.freckles_runner import FrecklesRunner
from freckles.doc import utils
from frutils.frutils_cli import output
from luci.luitem_index import LuItemMultiIndex
from terminaltables import SingleTable

yaml = YAML(typ="safe")

log = logging.getLogger("freckles")


def print_available_tasks(context, filter_names=[], apropos=[]):

    index = context.index

    pkgs_filter = []
    for r in index.get_pkg_names():
        match = True
        for f in filter_names:
            if f not in r:
                match = False
                break
        if match:
            pkgs_filter.append(r)

    pkgs = []
    for p in pkgs_filter:
        match = True
        for a in apropos:
            if a not in p:
                match = False
                break

        if not match:
            pkg = index.get_pkg(p)
            doc = Doc(pkg.doc)

            match = doc.matches_apropos(apropos)

        if match:
            pkgs.append(p)

    data = []

    for n in pkgs:

        p = index.get_pkg(n)
        doc = Doc(p.doc)
        temp = [n, doc.get_short_help()]
        data.append(temp)

    table = SingleTable(data)
    table.outer_border = False
    table.inner_column_border = False
    table.padding_left = 0
    table.padding_right = 4
    table.inner_heading_row_border = False
    table.inner_row_border = False

    click.echo(table.table)


@click.command()
@click.option(
    "--filter-names",
    "-f",
    help="only display frecklets whose name matches the provided filter(s)",
    multiple=True,
)
@click.option(
    "--apropos",
    "-a",
    help="only displays frecklets whose name or description matches the provided filter(s)",
    multiple=True,
)
@click.pass_context
def tasks(ctx, filter_names=None, apropos=None):
    """Lists all available frecklets."""

    click.echo()

    context = ctx.obj["context"]
    print_available_tasks(context, filter_names=filter_names, apropos=apropos)


# ===============================================
@click.group("task")
def task():

    pass


@task.command("info")
@click.option(
    "--show-vars", "-v", help="show task variables", is_flag=True, default=False
)
@click.option(
    "--show-references", "-r", help="show references", is_flag=True, default=False
)
@click.argument("frecklet_name", metavar="TASK", nargs=1, required=False)
@click.pass_context
def info(ctx, frecklet_name, show_vars, show_references):

    click.echo()
    context = ctx.obj["context"]

    if not frecklet_name:
        print_available_tasks(context)
        sys.exit()

    index = context.index

    p = index.get_pkg(frecklet_name)
    if p is None:
        click.echo("No frecklet available for name: {}".format(frecklet_name))
        sys.exit(1)

    show = {"variables": show_vars, "references": show_references}

    rst = utils.render_frecklet_to_rst(frecklet_name, p, show=show)

    rendered = rst2ansi(rst)
    click.echo(rendered)


@task.command("vars")
@click.option(
    "--only-names",
    "-n",
    help="only display variable names",
    is_flag=True,
    default=False,
)
@click.argument("vars", metavar="TASK", nargs=-1, required=True)
@click.pass_context
def vars(ctx, vars, only_names):

    click.echo()

    context = ctx.obj["context"]
    index = context.index

    frecklet_name = vars[0]

    show_args = []
    if len(vars) > 1:
        show_args = vars[1:]

    p = index.get_pkg(frecklet_name)
    if p is None:
        click.echo("No frecklet available for name: {}".format(frecklet_name))
        sys.exit(1)

    show = {"arg_list_filter": show_args, "only_names": only_names}

    rst = utils.render_frecklet_to_rst(
        frecklet_name, p, template_name="frecklet_template_args.rst.j2", show=show
    )

    rendered = rst2ansi(rst)
    click.echo(rendered)


@task.command("describe")
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
