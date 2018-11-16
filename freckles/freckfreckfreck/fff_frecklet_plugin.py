from __future__ import absolute_import, division, print_function

import logging
import sys

import click
from pygments import highlight
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers.data import YamlLexer
from rst2ansi import rst2ansi
from ruamel.yaml import YAML
from terminaltables import SingleTable

from freckles.defaults import FRECKLET_NAME
from freckles.doc import utils
from freckles.freckles_runner import FrecklesRunner
from frutils import readable_yaml
from frutils.doc import Doc

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
        doc = p.doc
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
def frecklets(ctx, filter_names=None, apropos=None):
    """Lists all available frecklets."""

    click.echo()

    context = ctx.obj["context"]
    print_available_tasks(context, filter_names=filter_names, apropos=apropos)


# ===============================================
@click.group("frecklet")
def frecklet():

    pass


@frecklet.command("help")
@click.option("--hide-vars", help="hide task variables", is_flag=True, default=False)
@click.option(
    "--hide-links", help="hide 'further reading'-links", is_flag=True, default=False
)
@click.argument("frecklet_name", metavar=FRECKLET_NAME, nargs=1, required=True)
@click.pass_context
def frecklet_help(ctx, frecklet_name, hide_vars, hide_links):
    """Displays full help about a frecklet."""

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

    show = {"variables": not hide_vars, "show_links": not hide_links}
    rst = utils.render_frecklet(frecklet_name, p, show=show)
    rendered = rst2ansi(rst)
    click.echo(rendered)


@frecklet.command("info")
@click.argument("frecklet_name", metavar=FRECKLET_NAME, nargs=1, required=False)
@click.pass_context
def info(ctx, frecklet_name):
    """Displays frecklet description."""

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

    show = {"variables": False, "show_links": False}

    rst = utils.render_frecklet(frecklet_name, p, show=show)
    rendered = rst2ansi(rst)

    click.echo(rendered)


@frecklet.command("print")
@click.argument("frecklet_name", metavar=FRECKLET_NAME, nargs=1, required=False)
@click.pass_context
def print_frecklet(ctx, frecklet_name):
    """Prints the (raw) frecklet."""

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

    output_string = readable_yaml(p.metadata_raw, sort_keys=False)
    output_string = highlight(output_string, YamlLexer(), Terminal256Formatter())
    click.echo(output_string)


@frecklet.command("debug")
@click.argument("frecklet_name", metavar=FRECKLET_NAME, nargs=1, required=False)
@click.pass_context
def debug(ctx, frecklet_name):
    """Prints the (raw) frecklet."""

    click.echo()
    context = ctx.obj["context"]

    if not frecklet_name:
        print_available_tasks(context)
        sys.exit()

    # index = context.index

    md = context.get_frecklet_metadata(frecklet_name)
    print(md)
    # p = index.get_pkg(frecklet_name)
    # if p is None:
    #     click.echo("No frecklet available for name: {}".format(frecklet_name))
    #     sys.exit(1)

    # output_string = readable_yaml(p.metadata_raw, sort_keys=False)
    # output_string = highlight(output_string, YamlLexer(), Terminal256Formatter())
    # click.echo(output_string)


@frecklet.command("vars")
@click.option(
    "--only-names",
    "-n",
    help="only display variable names",
    is_flag=True,
    default=False,
)
@click.argument("vars", metavar=FRECKLET_NAME, nargs=-1, required=True)
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

    rst = utils.render_frecklet(
        frecklet_name, p, template_name="frecklet_template_args.rst.j2", show=show
    )

    rendered = rst2ansi(rst)
    click.echo(rendered)


@frecklet.command("describe")
@click.argument("frecklecutable", metavar="FRECKLECUTABLE", nargs=1)
@click.pass_context
def describe_frecklecutable(ctx, frecklecutable):

    context = ctx.obj["context"]
    # control_dict = {
    #     "no_run": True,
    #     "host": "localhost",
    #     "output": "default",
    #     "elevated": "not_elevated",
    # }

    try:
        runner = FrecklesRunner(context)
        runner.load_frecklecutable_from_name_or_file(frecklecutable)

        runner.describe_tasklist()
        sys.exit(0)
    except (Exception) as e:
        click.echo()
        click.echo(e)
