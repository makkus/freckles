# -*- coding: utf-8 -*-

# python 3 compatibility
from __future__ import (absolute_import, division, print_function)

import collections
from cookiecutter.main import cookiecutter
import logging

import click
import tempfile
import os
import pprint
import sys
import yaml
from os import listdir
from os.path import isdir, join

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

        target = metadata["target_folder"]
        source_delete = False

        if target != DEFAULT_FRECKLE_TARGET_MARKER and not target.startswith("~") and not target.startswith("/"):
            raise Exception("Relative path not supported for target option, please use an absolute one")

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

            cookiecutter_file = os.path.join(match, "cookiecutter.json")

            if os.path.exists(cookiecutter_file):

                click.secho("\nFound interactive blueprint, please enter approriate values below:\n", bold=True)

                temp_path = tempfile.mkdtemp(prefix='frkl.')
                cookiecutter(match, output_dir=temp_path)


                subdirs = [os.path.join(temp_path, f) for f in listdir(temp_path) if isdir(join(temp_path, f))]

                if len(subdirs) != 1:
                    raise Exception("More than one directories created by interactive template '{}'. Can't deal with that.".format(match))

                url = subdirs[0]
                source_delete = True


            else:

                url = match

        else:
            url = temp_url

        if os.path.exists(os.path.expanduser(url)):
            # assuming archive
            if os.path.isfile(os.path.expanduser(url)):
                # TODO: check whether host is local
                repo_desc = {"type": "local_archive"}
                repo_desc["remote_url"] = os.path.abspath(os.path.expanduser(url))
                repo_desc["checkout_become"] = target_become
                #repo_desc["local_name"] = os.path.basename(url).split('.')[0]
                repo_desc["source_delete"] = False
                if target == DEFAULT_FRECKLE_TARGET_MARKER:
                    raise Exception("No target directory specified when using archive file.")
                repo_desc["local_parent"] = target
                repo_desc["checkout_skip"] = False
            else:
                # TODO: check whether host is local
                repo_desc = {"type": "local"}
                repo_desc["remote_url"] = os.path.abspath(os.path.expanduser(url))
                repo_desc["checkout_become"] = target_become
                repo_desc["local_name"] = os.path.basename(repo_desc["remote_url"])
                repo_desc["source_delete"] = source_delete
                if target == DEFAULT_FRECKLE_TARGET_MARKER:
                    repo_desc["checkout_skip"] = True
                    repo_desc["local_parent"] = os.path.dirname(repo_desc["remote_url"])
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

        elif url.startswith("http://") or url.startswith("https://"):
            # TODO: check whether host is local
            repo_desc = {"type": "remote_archive"}
            repo_desc["remote_url"] = url
            repo_desc["checkout_become"] = target_become
            #repo_desc["local_name"] = os.path.basename(url).split('.')[0]
            repo_desc["source_delete"] = False
            if target == DEFAULT_FRECKLE_TARGET_MARKER:
                raise Exception("No target directory specified when using archive file.")
            repo_desc["local_parent"] = target
            repo_desc["checkout_skip"] = False

        else:
            raise Exception("freckle url format unknown, don't know how to handle that: {}".format(url))

        repo_desc["blueprint"] = temp_url.startswith(BLUEPRINT_URL_PREFIX)

        frkl.dict_merge(metadata, repo_desc, copy_dct=False)
