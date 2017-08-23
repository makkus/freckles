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

import yaml


defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")
DEFAULT_PROFILES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_profile_repo")
DEFAULT_USER_PROFILES_PATH = os.path.join(os.path.expanduser("~"), ".freckles", "profiles")
DEFAULT_USER_ROLE_REPO_PATH = os.path.join(os.path.expanduser("~"), ".freckles", "trusted_roles")
EXTRA_FRECKLES_PLUGINS = os.path.abspath(os.path.join(os.path.dirname(__file__), "external", "freckles_extra_plugins"))
DEFAULT_IGNORE_STRINGS = ["pre-checking", "finding freckles", "processing freckles", "retrieving freckles", "calculating", "check required", "augmenting", "including ansible role", "checking for", "preparing profiles", "starting profile execution", "auto-detect package managers", "setting executable:"]

DEFAULT_RUN_BASE_LOCATION = os.path.expanduser("~/.local/freckles/runs")
DEFAULT_RUN_SYMLINK_LOCATION = os.path.join(DEFAULT_RUN_BASE_LOCATION, "current")
DEFAULT_RUN_LOCATION = os.path.join(DEFAULT_RUN_BASE_LOCATION, "archive", "run")

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


def get_profiles_from_folder(profile_folder):

    if os.path.exists(profile_folder) and os.path.isdir(os.path.realpath(profile_folder)):
        files = os.listdir(os.path.realpath(profile_folder))
        profiles = [f for f in files if os.path.isdir(os.path.realpath(os.path.join(profile_folder, f))) and not f.startswith(".")]
        return profiles
    else:
        return []


def find_supported_profiles(profile_folders=[DEFAULT_PROFILES_PATH, DEFAULT_USER_PROFILES_PATH]):

    result = []
    for pf in profile_folders:
        profiles = get_profiles_from_folder(pf)
        result.extend(profiles)

    return list(set(result))


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

def find_profile_files(filename, valid_profiles=None, profile_repos=[DEFAULT_PROFILES_PATH, DEFAULT_USER_PROFILES_PATH]):

    task_files_to_copy = {}
    for profile_repo in profile_repos:
        if os.path.exists(profile_repo) and os.path.isdir(profile_repo):
            for subfolder in os.listdir(profile_repo):

                if valid_profiles and subfolder not in valid_profiles:
                    continue

                profiles_folder = os.path.join(profile_repo, subfolder)
                profile_tasks = os.path.join(profiles_folder, filename)

                if not os.path.isdir(profiles_folder) or not os.path.exists(profile_tasks) or not os.path.isfile(profile_tasks):
                    continue

                task_files_to_copy[subfolder] = profile_tasks

    return task_files_to_copy

def find_profile_files_callback(filenames, valid_profiles=None):

    if isinstance(filenames, string_types):
        filenames = [filenames]

    task_files_to_copy = {}
    for filename in filenames:
        files = find_profile_files(filename, valid_profiles)
        for key, value in files.items():
            task_files_to_copy.setdefault(filename, {})[key] = value

    def copy_callback(ansible_environment_root):

        for name, path in task_files_to_copy.get("init.yml", {}).items():

            target_path = os.path.join(ansible_environment_root, "roles", "internal", "makkus.freckles", "tasks", "init-{}.yml".format(name))
            shutil.copyfile(path, target_path)

        for name, path in task_files_to_copy.get("tasks.yml", {}).items():

            target_path = os.path.join(ansible_environment_root, "roles", "internal", "makkus.freckles", "tasks", "items-{}.yml".format(name))
            shutil.copyfile(path, target_path)

    return copy_callback


def get_profile_dependency_roles(profiles):

    dep_files = find_profile_files("meta.yml", profiles)
    all_deps = set()
    for profile_name, dep_file in dep_files.items():

        with open(dep_file, 'r') as f:
            deps = yaml.safe_load(f)
            all_deps |= set(deps.get("role-dependencies", {}))

    return list(all_deps)


def create_and_run_nsbl_runner(task_config, format="default", no_ask_pass=False, pre_run_callback=None, no_run=False, additional_roles=[]):

    role_repos = defaults.calculate_role_repos([DEFAULT_USER_ROLE_REPO_PATH], use_default_roles=True)

    nsbl_obj = nsbl.Nsbl.create(task_config, role_repos, [], wrap_into_localhost_env=True, pre_chain=[], additional_roles=additional_roles)
    runner = nsbl.NsblRunner(nsbl_obj)
    run_target = os.path.expanduser(DEFAULT_RUN_LOCATION)
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

    force = True
    ask_become_pass = not no_ask_pass

    runner.run(run_target, force=force, ansible_verbose=ansible_verbose, ask_become_pass=ask_become_pass, extra_plugins=EXTRA_FRECKLES_PLUGINS, callback=stdout_callback, add_timestamp_to_env=True, add_symlink_to_env=DEFAULT_RUN_SYMLINK_LOCATION, no_run=no_run, display_sub_tasks=display_sub_tasks, display_skipped_tasks=display_skipped_tasks, display_ignore_tasks=ignore_task_strings, pre_run_callback=pre_run_callback)
