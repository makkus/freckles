from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import fnmatch
import logging
import os
import pprint
import shutil
import sys
from pydoc import locate
from .config import FrecklesConfig

import click
from ansible.plugins.filter.core import FilterModule
from frkl.frkl import (PLACEHOLDER, EnsurePythonObjectProcessor,
                       EnsureUrlProcessor, Frkl, MergeDictResultCallback,
                       UrlAbbrevProcessor, YamlTextSplitProcessor)
from jinja2 import Environment, PackageLoader, Template
from jinja2.ext import Extension
from nsbl import defaults, nsbl
from six import string_types

try:
    set
except NameError:
    from sets import Set as set

import yaml
from .freckles_defaults import *

DEFAULT_EXCLUDE_DIRS = [".git", ".tox", ".cache"]
PROFILE_MARKER_FILENAME = "profile.yml"

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

DEFAULT_FRECKLES_CONFIG = FrecklesConfig()

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

PROFILE_CACHE = {}

def find_supported_profiles(config=None):

    if not config:
        config = DEFAULT_FRECKLES_CONFIG

    repos = config.get_profile_repos()

    result = {}
    for r in repos:
        p = get_profiles_from_repo(r)
        result.update(p)

    return result

def create_cli_command(config, command_path=None, no_run=False):

    doc = config.get("doc", {})
    # TODO: check format of config
    options = config.get("args", {})
    vars = config.get("vars", {})
    tasks = config.get("tasks", None)
    default_vars = config.get("defaults", {})

    key_map = {}
    argument_key = None

    options_list = []
    args_that_are_vars = []
    for opt, opt_details in options.items():
        opt_type = opt_details.get("type", None)
        if opt_type:
            opt_type_converted = locate(opt_type)
            if not opt_type_converted:
                raise Exception("No type found for: {}".format(opt_type))
            opt_details['type'] = opt_type_converted

        key = opt_details.pop('arg_name', opt)
        key_map[key] = opt

        is_argument = opt_details.pop('is_argument', False)
        is_var = opt_details.pop('is_var', True)
        if is_var:
            args_that_are_vars.append(key)
        if is_argument:
            if argument_key:
                raise Exception("Multiple arguments are not supported (yet): {}".format(config["vars"]))
            argument_key = key
            required = opt_details.pop("required", None)

            o = click.Argument(param_decls=[key], required=required, **opt_details)
        else:
            o = click.Option(param_decls=["--{}".format(key)], **opt_details)
        options_list.append(o)

    return {"options": options_list, "key_map": key_map, "command_path": command_path, "tasks": tasks, "vars": vars, "default_vars": default_vars, "doc": doc, "args_that_are_vars": args_that_are_vars, "no_run": no_run}

def find_supported_profile_names(config=None):

    return sorted(list(set(find_supported_profiles(config).keys())))

def get_profiles_from_repo(profile_repo):

    if not os.path.exists(profile_repo) or not os.path.isdir(os.path.realpath(profile_repo)):
        return {}

    if profile_repo in PROFILE_CACHE.keys():
        return PROFILE_CACHE[profile_repo]

    result = {}
    for root, dirnames, filenames in os.walk(os.path.realpath(profile_repo), topdown=True, followlinks=True):

        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]

        for filename in fnmatch.filter(filenames, PROFILE_MARKER_FILENAME):

            profile_file = os.path.realpath(os.path.join(root, PROFILE_MARKER_FILENAME))
            profile_folder = os.path.abspath(os.path.dirname(profile_file))
            profile_name = os.path.basename(profile_folder)

            result[profile_name] = profile_folder

    PROFILE_CACHE[profile_repo] = result
    return result

def find_profile_files(filename, valid_profiles=None, config=None):

    profiles = find_supported_profiles(config)

    task_files_to_copy = {}

    for profile_name, profile_path in profiles.items():

        if valid_profiles and profile_name not in valid_profiles:
            continue

        profile_child_file = os.path.join(profile_path, filename)

        if not os.path.exists(profile_child_file) or not os.path.isfile(profile_child_file):
            continue

        task_files_to_copy[profile_name] = profile_child_file

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

    dep_files = find_profile_files("profile.yml", profiles)
    all_deps = set()
    for profile_name, dep_file in dep_files.items():

        with open(dep_file, 'r') as f:
            deps = yaml.safe_load(f)
            if not deps:
                deps = {}
            all_deps |= set(deps.get("role-dependencies", {}))

    return list(all_deps)


def extract_all_used_profiles(freckle_repos):

    all_profiles = []
    for fr in freckle_repos:
        all_profiles.extend(fr.get("profiles", []))

    return list(set(all_profiles))


def create_freckles_run(freckle_repos, ask_become_pass="auto", no_run=False, output_format="default"):

    profiles = extract_all_used_profiles(freckle_repos)
    callback = find_profile_files_callback(["tasks.yml", "init.yml"], profiles)

    additional_roles = get_profile_dependency_roles(profiles)

    task_config = [{"vars": {"freckles": freckle_repos}, "tasks": ["freckles"]}]

    create_and_run_nsbl_runner(task_config, output_format, ask_become_pass=ask_become_pass, pre_run_callback=callback, no_run=no_run, additional_roles=additional_roles)



def create_and_run_nsbl_runner(task_config, output_format="default", ask_become_pass="auto", pre_run_callback=None, no_run=False, additional_roles=[], config=None):

    if not config:
        config = DEFAULT_FRECKLES_CONFIG

    role_repos = config.get_role_repos()
    task_descs = config.get_task_descs()

    nsbl_obj = nsbl.Nsbl.create(task_config, role_repos, task_descs, wrap_into_localhost_env=True, pre_chain=[], additional_roles=additional_roles)

    runner = nsbl.NsblRunner(nsbl_obj)
    run_target = os.path.expanduser(DEFAULT_RUN_LOCATION)
    ansible_verbose = ""
    stdout_callback = "nsbl_internal"
    ignore_task_strings = []
    display_sub_tasks = True
    display_skipped_tasks = False

    if output_format == "verbose":
        stdout_callback = "default"
        ansible_verbose = "-vvvv"
    elif output_format == "ansible":
        stdout_callback = "default"
    elif output_format == "skippy":
        stdout_callback = "skippy"
    elif output_format == "default_full":
        stdout_callback = "nsbl_internal"
        display_skipped_tasks = True
    elif output_format == "default":
        ignore_task_strings = DEFAULT_IGNORE_STRINGS
        stdout_callback = "nsbl_internal"
    else:
        raise Exception("Invalid output format: {}".format(output_format))

    force = True

    runner.run(run_target, force=force, ansible_verbose=ansible_verbose, ask_become_pass=ask_become_pass, extra_plugins=EXTRA_FRECKLES_PLUGINS, callback=stdout_callback, add_timestamp_to_env=True, add_symlink_to_env=DEFAULT_RUN_SYMLINK_LOCATION, no_run=no_run, display_sub_tasks=display_sub_tasks, display_skipped_tasks=display_skipped_tasks, display_ignore_tasks=ignore_task_strings, pre_run_callback=pre_run_callback)
