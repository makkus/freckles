# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging

import click

from . import print_version
from .freckles_defaults import *
from .profiles import ProfileRepo, assemble_freckle_run, get_freckles_option_set, BREAK_COMMAND_NAME
from .utils import DEFAULT_FRECKLES_CONFIG, RepoType, download_extra_repos

try:
    set
except NameError:
    from sets import Set as set

log = logging.getLogger("freckles")

FRECKLES_HELP_TEXT = """Run a series of freckelize and/or frecklecute commands as a script."""

FRECKLES_EPILOG_TEXT = "freckles is free and open source software, for more information visit: https://docs.freckles.io"


if __name__ == "__main__":
    cli()
