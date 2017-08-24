# -*- coding: utf-8 -*-

# python 3 compatibility
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import os
import pprint
import sys
from pydoc import locate

import click
from frkl.frkl import (PLACEHOLDER, EnsurePythonObjectProcessor,
                       EnsureUrlProcessor, Frkl, MergeDictResultCallback,
                       UrlAbbrevProcessor, YamlTextSplitProcessor, dict_merge)
from jinja2 import Environment, PackageLoader, Template
from six import string_types

import yaml

from .utils import (FRECKLES_REPO, FRECKLES_URL, RepoType,
                    create_and_run_nsbl_runner, create_freckle_desc,
                    render_dict, render_vars_template,
                    url_is_local, find_supported_profiles, PROFILE_MARKER_FILENAME)

log = logging.getLogger("freckles")


COMMAND_SEPERATOR = "-"
DEFAULT_COMMAND_REPO = os.path.join(os.path.dirname(__file__), "frecklecutables")

class ProfileRepo(object):

    def __init__(self, config, no_run=False):

        self.profiles = find_supported_profiles(config)


    def get_commands(self):

        commands = {}

        for profile_name, profile_path in self.profiles.items():

            profile_metadata_file = os.path.join(profile_path, PROFILE_MARKER_FILENAME)
            with open(profile_metadata_file, 'r') as f:
                md = yaml.safe_load(f)
