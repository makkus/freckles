# -*- coding: utf-8 -*-

# python 3 compatibility
from __future__ import (absolute_import, division, print_function)

import collections
import logging

import click
import os
import pprint
import sys
import yaml

from frkl import frkl
from nsbl import tasks as nsbl_tasks
from .freckles_defaults import *

try:
    set
except NameError:
    from sets import Set as set

from .freckles_defaults import *
from .utils import (RepoType,
                    create_freckle_desc,
                    find_supported_profiles, ADAPTER_MARKER_EXTENSION, create_cli_command, create_freckles_run,
                    get_vars_from_cli_input, print_repos_expand)

log = logging.getLogger("freckles")


def create_freckle_descs(repos):
    """Augments freckle urls provided by the user via cli (if necessary).
    """

    for url, metadata in repos.items():

        target = metadata["target"]

        if target == DEFAULT_FRECKLE_TARGET_MARKER or target.startswith("~") or target.startswith("/home"):
            target_become = False
        else:
            target_become = True

        if os.path.exists(os.path.expanduser(url)):

            repo_desc = {"type": "local"}
            repo_desc["remote_url"] = os.path.abspath(os.path.expanduser(url))
            repo_desc["checkout_become"] = target_become
            repo_desc["local_name"] = os.path.basename(repo_desc["remote_url"])
            if target == DEFAULT_FRECKLE_TARGET_MARKER:
                repo_desc["checkout_skip"] = True
                pass
            else:
                repo_desc["local_parent"] = target
                repo_desc["checkout_skip"] = False

        elif url.endswith(".git"):

            repo_desc = {"type": "git"}
            repo_desc["remote_url"] = url
            repo_desc["checkout_become"] = target_become
            repo_desc["local_name"] = os.path.basename(repo_desc["remote_url"])[:-4]
            repo_desc["checkout_skip"] = False
            if target == DEFAULT_FRECKLE_TARGET_MARKER:
                repo_desc["local_parent"] = "~/freckles"
            else:
                repo_desc["local_parent"] = target


        frkl.dict_merge(metadata, repo_desc, copy_dct=False)
