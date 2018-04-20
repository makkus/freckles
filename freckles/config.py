from __future__ import (absolute_import, division, print_function)

from six import string_types
from .freckles_defaults import *
from frkl import frkl

try:
    set
except NameError:
    from sets import Set as set

import yaml

DEFAULT_ROLE_REPOS = ['default', 'user']
DEFAULT_TRUSTED_URLS = ['https://github.com/makkus/', 'https://github.com/freckles-io/']
# DEFAULT_TRUSTED_URLS = ['https://github.com/freckles-io/']

def parse_config_file(path):

    chain = [frkl.EnsureUrlProcessor(), frkl.EnsurePythonObjectProcessor(), frkl.FrklProcessor(DEFAULT_PROFILE_VAR_FORMAT)]

    frkl_obj = frkl.Frkl(path, chain)
    # mdrc_init = {"append_keys": "vars/packages"}
    # frkl_callback = frkl.MergeDictResultCallback(mdrc_init)
    frkl_callback = frkl.MergeResultCallback()
    configs = frkl_obj.process(frkl_callback)
    repos = DEFAULT_ROLE_REPOS
    urls = DEFAULT_TRUSTED_URLS
    aliases = []

    for c in configs:

        if c.get("profile", {}).get("name", None) == "config":
            temp = c.get("vars", {}).get("trusted-repos", [])
            for r in temp:
                if os.path.exists(os.path.expanduser(r)):
                    expanded = os.path.abspath(os.path.expanduser(r))
                else:
                    expanded = r

                if expanded not in repos:
                    repos.append(expanded)

            temp = c.get("vars", {}).get("trusted-urls", [])
            for u in temp:
                if u not in urls:
                    urls.append(u)
            temp = c.get("vars", {}).get("task-aliases", [])
            for a in temp:
                if a not in aliases:
                    aliases.append(a)

    return {'trusted-repos': repos, "trusted-urls": urls, "task-aliases": aliases}



class FrecklesConfig(object):
    """
    TODO

    additional options: use_freckle_as_repo
    """
    def __init__(self, config_file="default"):

        if config_file is None:
            config_file = False
        elif config_file == "default":
            config_file = FRECKLES_DEFAULT_CONFIG_FILE

        self.config_file = config_file
        if self.config_file and os.path.exists(self.config_file):
            self.config = parse_config_file(self.config_file)
        else:
            self.config = {}

        self.trusted_repos = self.config.get("trusted-repos", DEFAULT_ROLE_REPOS)
        self.trusted_urls = self.config.get("trusted-urls", DEFAULT_TRUSTED_URLS)
        self.task_descs = self.config.get("task-aliases", [])
        self.use_freckle_as_repo = self.config.get("use_freckle_as_repo", True)
        self.default_freckelize_target = DEFAULT_FRECKELIZE_TARGET_FOLDER

    def __repr__(self):

        return "FrecklesConfig(trusted_repos={}, trusted_urls={}, task_descs={})".format(self.trusted_repos, self.trusted_urls, self.task_descs)

    def add_user_repo(self, repo):
        """Adds a repo path (or list of paths) with hightest priority."""

        if isinstance(repo, string_types):
            repo = [repo]

        for r in repo:
            self.trusted_repos.append(r)

    def add_repo(self, repo):
        """Adds a repo path (or list of paths)."""

        if isinstance(repo, string_types):
            repo = [repo]

        for r in repo:
            self.trusted_repos.insert(-1, r)
