from __future__ import absolute_import, division, print_function

import logging
import sys

import click
from rst2ansi import rst2ansi
from ruamel.yaml import YAML

from freckles.defaults import FRECKLET_NAME
from freckles.doc import utils

yaml = YAML(typ="safe")

log = logging.getLogger("freckles")


def print_frecklet_help(
    frecklet_name, pkg, show_vars=False, show_links=False, show_desc=True
):

    show = {"variables": show_vars, "show_links": show_links, "desc": show_desc}
    rst = utils.render_frecklet(frecklet_name, pkg, show=show)

    # otherwise Python 3 fails
    if hasattr(rst, "encode"):
        rst = rst.encode("utf-8")

    rendered = rst2ansi(rst)
    click.echo(rendered)


@click.command("doc")
@click.option("--full", "-f", help="show all information", is_flag=True, default=False)
@click.option("--show-vars", "-v", help="show variables", is_flag=True, default=False)
@click.option("--show-desc", "-d", help="show description", is_flag=True, default=False)
@click.option(
    "--show-links",
    "-l",
    help="show 'further reading'-links",
    is_flag=True,
    default=False,
)
@click.argument("frecklet_name", metavar=FRECKLET_NAME, nargs=1, required=True)
@click.pass_context
def doc(ctx, frecklet_name, full, show_vars, show_links, show_desc):
    """Displays full help about a frecklet."""

    click.echo()
    context = ctx.obj["context"]

    if full:
        show_vars = True
        show_links = True
        show_desc = True

    if not show_vars and not show_links and not show_desc:
        show_desc = True

    if not frecklet_name:
        # will launch tui in the future
        sys.exit()

    index = context.index

    p = index.get_pkg(frecklet_name)
    if p is not None:
        f_name = frecklet_name
    else:
        names = context.get_frecklet_names(apropos=[frecklet_name])

        if len(names) == 0:
            click.echo(
                "No frecklet named (or containing) '{}' found.".format(frecklet_name)
            )
            sys.exit(0)
        elif len(names) == 1:
            f_name = names[0]
            p = index.get_pkg(f_name)
        else:
            click.echo(
                "Multiple frecklets containing the term '{}' found, please select one:\n".format(
                    frecklet_name
                )
            )
            sel_map = {}
            for i, name in enumerate(sorted(names), start=1):
                sel_map[i] = name
                click.echo("[{}] {}".format(i, name))

            click.echo("\n[0] exit")
            click.echo()

            choice = click.prompt("Choice", default=0, type=int)
            if choice == 0 or choice > len(names):
                sys.exit(0)

            f_name = sel_map[choice]
            p = index.get_pkg(f_name)
            click.echo()

    print_frecklet_help(
        f_name, p, show_vars=show_vars, show_links=show_links, show_desc=show_desc
    )
