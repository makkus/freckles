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

REPO_ABBREVS = {
    "default": defaults.DEFAULT_ROLES_PATH,
    "user": DEFAULT_USER_ROLE_REPO_PATH,
    "community": DEFAULT_COMMUNITY_ROLES_REPO_PATH
}

PROFILE_ABBREVS= {
    "default": DEFAULT_PROFILES_PATH,
    "user": DEFAULT_USER_PROFILES_PATH,
    "community": DEFAULT_COMMUNITY_PROFILES_PATH
}

FRECKLECUTABLES_ABBREV = {
    "default": DEFAULT_FRECKLECUTABLES_PATH,
    "user": DEFAULT_USER_FRECKLECUTABLES_PATH,
    "community": DEFAULT_COMMUNITY_FRECKLECUTABLES_PATH
}

def get_real_repo_path(abbrevs, repo_name):

    return abbrevs.get(repo_name, repo_name)


class FrecklesConfig(object):

    def __init__(self):

        self.config_file = os.path.join(click.get_app_dir('freckles', force_posix=True), 'config.yml')
        if os.path.exists(self.config_file):
            with open(self.config_file) as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}

        self.trusted_repos = self.config.get("trusted-repos", ["default", "user"])
        self.trusted_profiles = self.config.get("trusted-profiles", ["default", "user"])
        self.trusted_frecklecutables = self.config.get("trusted-frecklecutables", ["default", "user"])
        self.trusted_urls = self.config.get("trusted-urls", ["https://github.com/makkus"])
        self.task_descs = self.config.get("task-descs", [])


    def get_role_repos(self):

        role_repos = defaults.calculate_role_repos([get_real_repo_path(REPO_ABBREVS, r) for r in self.trusted_repos], use_default_roles=False)
        return role_repos

    def get_task_descs(self):

        return self.task_descs

    def get_profile_repos(self):

        profile_repos = [get_real_repo_path(PROFILE_ABBREVS, r) for r in self.trusted_profiles]
        return profile_repos

    def get_frecklecutables_repos(self):

        f_repos = [get_real_repo_path(FRECKLECUTABLES_ABBREV, r) for r in self.trusted_frecklecutables]
