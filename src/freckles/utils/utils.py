# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import textwrap

import click
import tabulate
from colorama import Style, Fore

from frutils import get_terminal_size


def print_template_error(template_error):

    msg = template_error.message
    lineno = template_error.lineno
    name = template_error.name
    filename = template_error.filename

    click.echo("Error in template '{}': {}".format(name, msg).encode("utf-8"))
    click.echo("  -> path: {}".format(filename).encode("utf-8"))
    click.echo("  -> lineno: {}".format(lineno).encode("utf-8"))


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
    toggle = True
    for key in data.keys():
        val = data[key]

        if rest_width > max_rest:
            val = "\n".join(textwrap.wrap(val, rest_width))

        if toggle:
            key = Style.DIM + key + Style.RESET_ALL
            val = Style.DIM + val + Style.RESET_ALL

        toggle = not toggle
        new_data.append([key, val])

    if rest_width > max_rest:

        click.echo(
            tabulate.tabulate(
                new_data,
                headers=[
                    Style.BRIGHT + header_one + Style.RESET_ALL,
                    Style.BRIGHT + header_two + Style.RESET_ALL,
                ],
            )
        )
    else:
        for row in new_data:
            header_one_str = "{}{}{}".format(
                Style.DIM, header_one, Style.RESET_ALL
            ).encode("utf-8")
            click.secho(header_one_str, bold=True, nl=False)
            click.echo(": {}".format(row[0]).encode("utf-8"))
            click.secho(header_two.encode("utf-8"), bold=True, nl=False)
            click.echo(": {}".format(row[1]).encode("utf-8"))
            click.echo()


def print_multi_column_table(data, headers):

    max_width = 0
    for row in data:
        w = 0
        for index, word in enumerate(row[0:-1]):

            header_len = len(headers[index])
            wl = len(str(word))
            if header_len > wl:
                wl = header_len
            w = w + wl + 3
        if w > max_width:
            max_width = w

    terminal_size = get_terminal_size()

    rest_width = terminal_size[0] - max_width - 3
    max_rest = 20

    new_data = []
    toggle = True
    for row in data:
        val = row[-1]

        if rest_width > max_rest:
            val = "\n".join(textwrap.wrap(val, rest_width))

        if toggle:
            new_row = []
            for word in row[0:-1]:
                new_row.append(Style.DIM + str(word) + Style.RESET_ALL)
            new_row.append(Style.DIM + val + Style.RESET_ALL)
            row = new_row
        else:
            new_row = row[0:-1]
            new_row.append(val)
            row = new_row

        toggle = not toggle
        new_data.append(row)

    if rest_width > max_rest:

        new_headers = []
        for h in headers:
            new_headers.append(Style.BRIGHT + h + Style.RESET_ALL)

        click.echo(tabulate.tabulate(new_data, headers=new_headers))
    else:
        for row in new_data:

            for index, word in enumerate(row):
                header_str = "{}{}{}".format(Style.DIM, headers[index], Style.RESET_ALL)
                click.secho(header_str, bold=True, nl=False)
                click.echo(": {}".format(word).encode("utf-8"))
            click.echo()


def print_frecklet_list(frecklet_dict):

    data = {}
    for f_name in sorted(frecklet_dict.keys()):
        f = frecklet_dict[f_name]
        try:
            desc = f.doc.get_short_help(list_item_format=True)
            data[f_name] = desc
        except (Exception) as e:
            msg = str(e)
            if len(msg) > 44:
                msg = msg[0:42] + "..."
            data[f_name] = (
                Fore.RED
                + "parse error: "
                + Style.RESET_ALL
                + Style.DIM
                + msg
                + Style.RESET_ALL
            )

    click.echo()
    print_two_column_table(data, "frecklet", "desc")
    click.echo()
