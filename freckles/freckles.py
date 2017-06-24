# -*- coding: utf-8 -*-
import os

from frkl.frkl import PLACEHOLDER, Frkl, UrlAbbrevProcessor
from nsbl.nsbl import Nsbl, NsblRunner

DEFAULT_ABBREVIATIONS = {
    'gh':
        ["https://github.com/", PLACEHOLDER, "/", PLACEHOLDER, ".git"],
    'bb': ["https://bitbucket.org/", PLACEHOLDER, "/", PLACEHOLDER, ".git"]
}

def freckles(repo_urls, role_repos=[], task_descs=[], target=None):

        if not target:
            target = os.path.expanduser("~/.nsbl/runs")

        if not isinstance(repo_urls, (list, tuple)):
            repo_urls = [repo_urls]

        frkl_obj = Frkl(repo_urls, [UrlAbbrevProcessor(init_params={"abbrevs": DEFAULT_ABBREVIATIONS, "add_default_abbrevs": False})])
        expanded_repos = frkl_obj.process()
        repo_vars = [{"vars": {"freckles_repo": expanded_repos}, "tasks": ["freckles"]}]

        nsbl_obj = Nsbl.create(repo_vars, role_repos, task_descs, wrap_into_localhost_env=True, pre_chain=[])
        runner = NsblRunner(nsbl_obj)

        return runner
