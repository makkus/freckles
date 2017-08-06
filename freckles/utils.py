from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import os
import pprint
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

import yaml


defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")
EXTRA_FRECKLES_PLUGINS = os.path.abspath(os.path.join(os.path.dirname(__file__), "external", "freckles_extra_plugins"))
DEFAULT_IGNORE_STRINGS = ["pre-checking", "finding freckles", "processing freckles", "retrieving freckles", "calculating", "check required", "augmenting", "including ansible role", "checking for executable", "preparing profiles", "starting profile execution", "auto-detect package managers"]

def to_freckle_desc_filter(url, target, target_is_parent, profiles, include, exclude):
    return create_freckle_desc(url, target, target_is_parent, profiles, include, exclude)

class FrecklesUtilsExtension(Extension):

    def __init__(self, environment):
        super(Extension, self).__init__()
        fm = FilterModule()
        filters = fm.filters()
        filters["to_freckle_desc"] = to_freckle_desc_filter
        environment.filters.update(filters)

freckles_jinja_utils = FrecklesUtilsExtension


def find_supported_profiles():

    task_folder = os.path.join(os.path.dirname(__file__), "external", "default_role_repo", "makkus.freckles", "tasks")

    files = os.listdir(task_folder)

    profiles = [f[:-4] for f in files if os.path.isfile(os.path.join(task_folder, f)) and f.endswith("yml") and f != "main.yml"]
    return profiles

class RepoType(click.ParamType):

    name = 'repo'

    def convert(self, value, param, ctx):

        if isinstance(value, string_types):
            is_string = True
        elif isinstance(value, (list, tuple)):
            is_string = False
        else:
            raise Exception("Not a supported type (only string or list are accepted): {}".format(value))
        try:
            frkl_obj = Frkl(value, [UrlAbbrevProcessor(init_params={"abbrevs": DEFAULT_ABBREVIATIONS, "add_default_abbrevs": False})])
            result = frkl_obj.process()
            if is_string:
                return result[0]
            else:
                return result
        except:
            self.fail('%s is not a valid repo url' % value, param, ctx)

class FreckleUrlType(click.ParamType):

    name = 'repo'

    def convert(self, value, param, ctx):

        if not isinstance(value, string_types):
            raise Exception("freckle url needs to a string: {}".format(value))
        try:
            frkl_obj = Frkl(value, [UrlAbbrevProcessor(init_params={"abbrevs": DEFAULT_ABBREVIATIONS, "add_default_abbrevs": False})])
            result = frkl_obj.process()
            return result[0]
        except:
            self.fail('%s is not a valid repo url' % value, param, ctx)

FRECKLES_REPO = RepoType()
FRECKLES_URL = FreckleUrlType()


DEFAULT_ABBREVIATIONS = {
    'gh':
        ["https://github.com/", PLACEHOLDER, "/", PLACEHOLDER, ".git"],
    'bb': ["https://bitbucket.org/", PLACEHOLDER, "/", PLACEHOLDER, ".git"]
}

def url_is_local(url):

    if url.startswith("~") or url.startswith(os.sep):
        return True
    return os.path.exists(os.path.expanduser(url))

def create_freckle_desc(freckle_url, target, target_is_parent=True, profiles=[], includes=[], excludes=[]):

    freckle_repo = {}

    if isinstance(profiles, string_types):
        profiles = [profiles]
    if isinstance(includes, string_types):
        includes = [includes]
    if isinstance(excludes, string_types):
        excludes = [excludes]

    if not freckle_url:
        if not target:
            raise Exception("Need either url or target for freckle")
        freckle_url = target
        is_local = True
    else:
        is_local = url_is_local(freckle_url)

    if is_local:
        freckle_repo["path"] = os.path.abspath(os.path.expanduser(freckle_url))
        freckle_repo["url"] = None
    else:
        repo = nsbl.ensure_git_repo_format(freckle_url, target, target_is_parent)
        freckle_repo["path"] = repo["dest"]
        freckle_repo["url"] = repo["repo"]

    freckle_repo["profiles"] = profiles
    freckle_repo["include"] = includes
    freckle_repo["exclude"] = excludes

    return freckle_repo

def replace_string(template_string, replacement_dict):

    result = Environment(extensions=[freckles_jinja_utils]).from_string(template_string).render(replacement_dict)
    return result

def render_dict(obj, replacement_dict):

    # print("OBJ")
    # pprint.pprint(obj)
    # print("REPLACEMNT")
    # pprint.pprint(replacement_dict)
    # print("")
    # print("")
    if isinstance(obj, dict):
        # dictionary
        ret = {}
        for k, v in obj.iteritems():
            ret[render_dict(k, replacement_dict)] = render_dict(v, replacement_dict)
        return ret
    elif isinstance(obj, string_types):
        # string
        return replace_string(obj, replacement_dict)
    elif isinstance(obj, (list, tuple)):
        # list (or the like)
        ret = []
        for item in obj:
            ret.append(render_dict(item, replacement_dict))
        return ret
    else:
        # anything else
        return obj

def render_vars_template(vars_template, replacement_dict):

    result = Environment(extensions=[freckles_jinja_utils]).from_string(vars_template).render(replacement_dict)
    return result


def create_and_run_nsbl_runner(task_config, format="default", no_ask_pass=False):

    nsbl_obj = nsbl.Nsbl.create(task_config, [], [], wrap_into_localhost_env=True, pre_chain=[])
    runner = nsbl.NsblRunner(nsbl_obj)
    run_target = os.path.expanduser("~/.freckles/runs/archive/run")
    ansible_verbose = ""
    stdout_callback = "nsbl_internal"
    ignore_task_strings = []
    display_sub_tasks = True
    display_skipped_tasks = False

    if format == "verbose":
        stdout_callback = "default"
        ansible_verbose = "-vvvv"
    elif format == "ansible":
        stdout_callback = "default"
    elif format == "skippy":
        stdout_callback = "skippy"
    elif format == "default_full":
        stdout_callback = "nsbl_internal"
        display_skipped_tasks = True
    elif format == "default":
        ignore_task_strings = DEFAULT_IGNORE_STRINGS
        stdout_callback = "nsbl_internal"
    else:
        raise Exception("Invalid output format: {}".format(format))

    no_run = False
    force = True
    ask_become_pass = not no_ask_pass

    runner.run(run_target, force=force, ansible_verbose=ansible_verbose, ask_become_pass=ask_become_pass, extra_plugins=EXTRA_FRECKLES_PLUGINS, callback=stdout_callback, add_timestamp_to_env=True, add_symlink_to_env="~/.freckles/runs/current", no_run=no_run, display_sub_tasks=display_sub_tasks, display_skipped_tasks=display_skipped_tasks, display_ignore_tasks=ignore_task_strings)
