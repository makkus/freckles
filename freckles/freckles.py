# -*- coding: utf-8 -*-
import os

import nsbl.defaults
from frkl.frkl import PLACEHOLDER, Frkl, UrlAbbrevProcessor
from nsbl.nsbl import Nsbl, NsblRunner

# TODO: this is ugly, probably have refactor how role repos are used
nsbl.defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")

DEFAULT_ABBREVIATIONS = {
    'gh':
        ["https://github.com/", PLACEHOLDER, "/", PLACEHOLDER, ".git"],
    'bb': ["https://bitbucket.org/", PLACEHOLDER, "/", PLACEHOLDER, ".git"]
}

def freckles(repo_urls, profiles=[], role_repos=[], task_descs=[], target=None):

        if not target:
            target = os.path.expanduser("~/.nsbl/runs")

        if not isinstance(repo_urls, (list, tuple)):
            repo_urls = [repo_urls]

        frkl_obj = Frkl(repo_urls, [UrlAbbrevProcessor(init_params={"abbrevs": DEFAULT_ABBREVIATIONS, "add_default_abbrevs": False})])
        expanded_repos = frkl_obj.process()

        temp = []
        if profiles:
                all_profiles = []
                for p in profiles:
                        all_profiles.extend(p.split(","))
                for r in expanded_repos:
                        temp.append({"repo": r, "profiles": all_profiles})
        else:
                temp = expanded_repos

        repo_vars = [{"vars": {"freckles_repos": temp}, "tasks": ["freckles"]}]

        #runner.run(target, force=force, ansible_verbose="", ask_become_pass=ask_become_pass, callback=stdout_callback, add_timestamp_to_env=True, add_symlink_to_env="~/.nsbl/runs/current", no_run=no_run)
        nsbl_obj = Nsbl.create(repo_vars, role_repos, task_descs, wrap_into_localhost_env=True, pre_chain=[])
        runner = NsblRunner(nsbl_obj)

        return runner
