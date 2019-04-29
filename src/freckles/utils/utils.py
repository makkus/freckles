# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import textwrap

import click
import tabulate

from frutils import get_terminal_size


def print_template_error(template_error):

    msg = template_error.message
    lineno = template_error.lineno
    name = template_error.name
    filename = template_error.filename

    click.echo("Error in template '{}': {}".format(name, msg))
    click.echo("  -> path: {}".format(filename))
    click.echo("  -> lineno: {}".format(lineno))


def print_two_column_table(data, header_one, header_two):

    max_width = 0
    for f_name in data.keys():
        w = len(f_name)
        if w > max_width:
            max_width = w

    terminal_size = get_terminal_size()

    rest_width = terminal_size[0] - max_width - 3
    max_rest = 20

    new_data = []
    for key in data.keys():
        val = data[key]

        if rest_width > max_rest:
            val = "\n".join(textwrap.wrap(val, rest_width))
        new_data.append([key, val])

    if rest_width > max_rest:
        click.echo(tabulate.tabulate(new_data, headers=[header_one, header_two]))
    else:
        for row in new_data:
            click.secho(header_one, bold=True, nl=False)
            click.echo(": {}".format(row[0]))
            click.secho(header_two, bold=True, nl=False)
            click.echo(": {}".format(row[1]))
            click.echo()


def print_frecklet_list(frecklet_dict):

    data = {}
    for f_name in sorted(frecklet_dict.keys()):
        f = frecklet_dict[f_name]
        desc = f.doc.get_short_help(list_item_format=True)
        data[f_name] = desc

    click.echo()
    print_two_column_table(data, "frecklet", "desc")
