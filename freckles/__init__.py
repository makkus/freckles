# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

"""Top-level package for freckles."""

__author__ = """Markus Binsteiner"""
__email__ = "makkus@frkl.io"
__version__ = "0.6.0"

import click


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(__version__)
    ctx.exit()
