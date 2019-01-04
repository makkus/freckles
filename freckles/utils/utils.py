from __future__ import absolute_import, division, print_function

import click


def print_template_error(template_error):

    msg = template_error.message
    lineno = template_error.lineno
    name = template_error.name
    filename = template_error.filename

    click.echo("Error in template '{}': {}".format(name, msg))
    click.echo("  -> path: {}".format(filename))
    click.echo("  -> lineno: {}".format(lineno))
