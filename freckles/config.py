from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import os
import pprint
import shutil
import sys
from pydoc import locate

import click
from ansible.plugins.filter.core import FilterModule
from frkl.frkl import (PLACEHOLDER, EnsurePythonObjectProcessor,
                       EnsureUrlProcessor, Frkl, MergeDictResultCallback,
                       UrlAbbrevProcessor, YamlTextSplitProcessor)
from jinja2 import Environment, PackageLoader, Template
from jinja2.ext import Extension
from nsbl import defaults, nsbl
from six import string_types
from .freckles_defaults import *
from nsbl import defaults

try:
    set
except NameError:
    from sets import Set as set

import yaml



class FrecklesConfig(object):

    def __init__(self):

        self.config_file = os.path.join(click.get_app_dir('freckles', force_posix=True), 'config.yml')
        if os.path.exists(self.config_file):
            with open(self.config_file) as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}

        self.trusted_repos = self.config.get("trusted-repos", ["default", "user"])
        self.trusted_urls = self.config.get("trusted-urls", ["https://github.com/makkus", "https:/github.com/freckles-io"])
        self.task_descs = self.config.get("task-descs", [])

    def get_role_repos(self):

        local_repos = get_local_repos(self.trusted_repos, "roles")

        role_repos = defaults.calculate_role_repos(local_repos, use_default_roles=False)
        return role_repos

    def get_task_descs(self):

        return self.task_descs

    def get_adapter_repos(self):

        profile_repos = get_local_repos(self.trusted_repos, "adapters")

        return profile_repos

    def get_frecklecutables_repos(self):

        f_repos = get_local_repos(self.trusted_repos, "frecklecutables")
        return f_repos
