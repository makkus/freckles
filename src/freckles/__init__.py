# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import io
import os

from pkg_resources import get_distribution, DistributionNotFound

"""Top-level package for freckles."""

__author__ = """Markus Binsteiner"""
__email__ = "markus@frkl.io"

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:

    try:
        version_file = os.path.join(os.path.dirname(__file__), "version.txt")

        if os.path.exists(version_file):
            with io.open(version_file, encoding="utf-8") as vf:
                __version__ = vf.read()
        else:
            __version__ = "unknown"

    except (Exception):
        pass

    if __version__ is None:
        __version__ = "unknown"

finally:
    del get_distribution, DistributionNotFound


import click
from .freckles import Freckles  # noqa
from .frecklecutable import Frecklecutable  # noqa


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(__version__)
    ctx.exit()
