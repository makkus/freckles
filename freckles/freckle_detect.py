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
                    get_vars_from_cli_input, print_repos_expand, get_available_blueprints)

log = logging.getLogger("freckles")


def create_freckle_descs(repos, config=None):
    """Augments freckle urls provided by the user via cli (if necessary).
    """

    for temp_url, metadata in repos.items():

        target = metadata["target"]

        if target == DEFAULT_FRECKLE_TARGET_MARKER or target.startswith("~") or target.startswith("/home"):
            target_become = False
        else:
            target_become = True

        if temp_url.startswith(BLUEPRINT_URL_PREFIX):

            blueprint_name = ":".join(temp_url.split(":")[1:])
            blueprints = get_available_blueprints(config)
            match = blueprints.get(blueprint_name, False)

            if not match:
                raise Exception("No blueprint with name '{}' available.".format(blueprint_name))

            if target == DEFAULT_FRECKLE_TARGET_MARKER:
                raise Exception("No target directory specified when using blueprint.")

            url = match
        else:
            url = temp_url

        if os.path.exists(os.path.expanduser(url)):

            # TODO: check whether host is local
            repo_desc = {"type": "local"}
            repo_desc["remote_url"] = os.path.abspath(os.path.expanduser(url))
            repo_desc["checkout_become"] = target_become
            repo_desc["local_name"] = os.path.basename(repo_desc["remote_url"])
            if target == DEFAULT_FRECKLE_TARGET_MARKER:
                repo_desc["checkout_skip"] = True
                repo_desc["local_parent"] = os.path.dirname(repo_desc["remote_url"])
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
