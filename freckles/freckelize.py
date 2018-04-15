# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
import os
import sys
import json
import click
import click_completion
import click_log
import copy
import uuid
import fnmatch
import operator
import tempfile
from cookiecutter.main import cookiecutter
import nsbl
from nsbl.output import print_title
import shutil
import yaml
from collections import OrderedDict
from six import string_types
from pprint import pprint, pformat
from frkl import frkl
from luci import Lucifier, DictletReader, DictletFinder, vars_file, TextFileDictletReader, parse_args_dict, output, JINJA_DELIMITER_PROFILES, replace_string, ordered_load, clean_user_input, readable_json, readable_yaml, readable_raw, add_key_to_dict
from . import print_version
from .freckles_defaults import *
from .utils import DEFAULT_FRECKLES_CONFIG, download_extra_repos, HostType, print_repos_expand, expand_repos,  create_and_run_nsbl_runner, freckles_jinja_extensions, download_repos, RepoType
from .freckles_base_cli import FrecklesBaseCommand, FrecklesLucifier
# from .freckle_detect import create_freckle_descs

log = logging.getLogger("freckles")
click_log.basic_config(log)

# optional shell completion
click_completion.init()

# TODO: this is a bit ugly, probably have refactor how role repos are used
nsbl.defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")

VARS_HELP = "variables to be used for templating, can be overridden by cli options if applicable"
DEFAULTS_HELP = "default variables, can be used instead (or in addition) to user input via command-line parameters"
KEEP_METADATA_HELP = "keep metadata in result directory, mostly useful for debugging"
FRECKELIZE_EPILOG_TEXT = "frecklecute is free and open source software and part of the 'freckles' project, for more information visit: https://docs.freckles.io"

FRECKLE_ARG_HELP = "the url or path to the freckle(s) to use, if specified here, before any commands, all profiles will be applied to it"
FRECKLE_ARG_METAVAR = "URL_OR_PATH"
TARGET_ARG_HELP = 'target folder for freckle checkouts (if remote url provided), defaults to folder \'freckles\' in users home'
TARGET_ARG_METAVAR = "PATH"
TARGET_NAME_ARG_HELP = "target name for freckle checkouts (if remote url provided), can not be used when multiple freckle folders are specified"
TARGET_NAME_ARG_METAVAR = "FOLDER_NAME"
INCLUDE_ARG_HELP = 'if specified, only process folders that end with one of the specified strings, only applicable for multi-freckle folders'
INCLUDE_ARG_METAVAR = 'FILTER_STRING'
EXCLUDE_ARG_HELP = 'if specified, omit process folders that end with one of the specified strings, takes precedence over the include option if in doubt, only applicable for multi-freckle folders'
EXCLUDE_ARG_METAVAR = 'FILTER_STRING'
ASK_PW_HELP = 'whether to force ask for a password, force ask not to, or let freckles decide (which might not always work)'
ASK_PW_CHOICES = click.Choice(["auto", "true", "false"])
NON_RECURSIVE_HELP = "whether to exclude all freckle child folders, default: false"

ADD_FILES = False

ADAPTER_CACHE = {}
DEFAULT_REPO_TYPE = RepoType()
DEFAULT_REPO_PRIORITY = 10000
METADATA_CONTENT_KEY = "freckle_metadata_file_content"

BLUEPRINT_CACHE = {}
def get_available_blueprints(config=None):
    """Find all available blueprints."""

    log.debug("Looking for blueprints...")
    if not config:
        config = DEFAULT_FRECKLES_CONFIG

    repos = nsbl.tasks.get_local_repos(config.trusted_repos, "blueprints", DEFAULT_LOCAL_REPO_PATH_BASE, DEFAULT_REPOS, DEFAULT_ABBREVIATIONS)

    result = {}
    for repo in repos:

        blueprints = get_blueprints_from_repo(repo)
        for name, path in blueprints.items():
            result[name] = path

    log.debug("Found blueprints:")
    log.debug(readable_json(result, indent=2))

    return result

def get_blueprints_from_repo(blueprint_repo):
    """Find all blueprints under a folder.

    A blueprint is a folder that has a .blueprint.freckle marker file in it's root.
    """
    if not os.path.exists(blueprint_repo) or not os.path.isdir(os.path.realpath(blueprint_repo)):
        return {}

    if blueprint_repo in BLUEPRINT_CACHE.keys():
        return BLUEPRINT_CACHE[blueprint_repo]

    result = {}

    try:

        for root, dirnames, filenames in os.walk(os.path.realpath(blueprint_repo), topdown=True, followlinks=True):
            dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]
            for filename in fnmatch.filter(filenames, "*.{}".format(BLUEPRINT_MARKER_EXTENSION)):
                blueprint_metadata_file = os.path.realpath(os.path.join(root, filename))
                blueprint_folder = os.path.abspath(os.path.dirname(blueprint_metadata_file))

                #profile_name = ".".join(os.path.basename(blueprint_metadata_file).split(".")[1:2])
                profile_name = os.path.basename(blueprint_metadata_file).split(".")[0]

                result[profile_name] = blueprint_folder

    except (UnicodeDecodeError) as e:
        click.echo(" X one or more filenames in '{}' can't be decoded, ignoring. This can cause problems later. ".format(root))

    BLUEPRINT_CACHE[blueprint_repo] = result

    return result

def find_freckelize_adapters(path):
    """Helper method to find freckelize adapters.

    Adapter files are named in the format: <adapter_name>.adapter.freckle

    Args:
      path (str): the root path (usually the path to a 'trusted repo').
    Returns:
      list: a list of valid freckelize adapters under this path
    """

    log.debug("Finding adapters in: {}".format(path))
    if not os.path.exists(path) or not os.path.isdir(os.path.realpath(path)):
        return {}

    if path in ADAPTER_CACHE.keys():
        return ADAPTER_CACHE[path]

    result = {}
    try:
        for root, dirnames, filenames in os.walk(os.path.realpath(path), topdown=True, followlinks=True):

            dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]

            for filename in fnmatch.filter(filenames, "*.{}".format(ADAPTER_MARKER_EXTENSION)):
                adapter_metadata_file = os.path.realpath(os.path.join(root, filename))
                # adapter_folder = os.path.abspath(os.path.dirname(adapter_metadata_file))
                # profile_name = ".".join(os.path.basename(adapter_metadata_file).split(".")[1:2])

                profile_name = os.path.basename(adapter_metadata_file).split(".")[0]

                result[profile_name] = {"path": adapter_metadata_file, "type": "file"}

    except (UnicodeDecodeError) as e:
        click.echo(" X one or more filenames in '{}' can't be decoded, ignoring. This can cause problems later. ".format(root))

    ADAPTER_CACHE[path] = result

    return result

class FreckleRepo(object):
    """Model class containing all relevant freckle repo paramters.

    If providing a string as 'source' argument, it'll be converted into a dictionary using :meth:`freckles.utils.RepoType.convert`.

    The format of the source dictionary is::

        {"url": <freckle_repo_url_or_path>,
         "branch": <optional branch if git repo>}

    Args:
      source (str, dict): the source repo/path
      target_path (str): the local target path
      target_name (str): the local target name
      include (list): a list of strings that specify which sub-freckle folders to use (TODO: include link to relevant documetnation)
      exclude (list): a list of strings that specify which sub-freckle folders to exclude from runs (TODO: include link to relevant documetnation)
      branch (str): the source branch/version (or None, if default branch)
      non_recursive (bool): whether to only use the source base folder, not any containing sub-folders that contain a '.freckle' marker file
      priority (int): the priority of this repo (determines the order in which it gets processed)
      default_vars (dict): default values to be used for this repo (key: profile_name, value: vars)
      overlay_vars (dict): overlay values to be used for this repo (key: profile_name, value: vars), those will be overlayed after the checkout process
    """
    def __init__(self, source, target_folder=None, target_name=None, include=None, exclude=None, branch=None, non_recursive=False, priority=DEFAULT_REPO_PRIORITY, default_vars=None, overlay_vars=None):

        self.id = str(uuid.uuid4())

        if not source:
            raise Exception("No source provided")

        if isinstance(source, string_types):
            temp_source = DEFAULT_REPO_TYPE.convert(source, None, None)
        else:
            temp_source = source

        self.priority = DEFAULT_REPO_PRIORITY
        self.source = temp_source
        if target_folder is None:
            target_folder = DEFAULT_FRECKLE_TARGET_MARKER
        self.target_folder = target_folder
        self.target_name = target_name
        if include is None:
            include = []
        self.include = include
        if exclude is None:
            exculde = []
        self.exclude = exclude
        self.non_recursive = non_recursive

        if default_vars is None:
            default_vars = OrderedDict()
        self.default_vars = default_vars
        if overlay_vars is None:
            overlay_vars = OrderedDict()
        self.overlay_vars = overlay_vars

        self.target_become = False
        self.source_delete = False

        self.repo_desc = None

    def set_priority(self, priority):

        self.priority = priority

    def __repr__(self):

        return("{}: {}".format("FreckleRepo", readable_raw(self.__dict__)))

    def expand(self, config, default_target=None):
        """Expands or fills in details using the provided configuration.

        Args:
          config (FrecklesConfig): the freckles configuration object
        """
        log.debug("Expanding repo: {}".format(self.source))

        if default_target is None:
            default_target = config.default_freckelize_target

        if self.source["url"].startswith("{}:".format(BLUEPRINT_URL_PREFIX)) or self.source["url"].startswith("{}:".format(BLUEPRINT_DEFAULTS_URL_PREFIX)):

            blueprint_type = self.source["url"].split(":")[0]
            if blueprint_type == BLUEPRINT_DEFAULTS_URL_PREFIX:
                blueprint_defaults = True
            else:
                blueprint_defaults = False

            blueprint_name = ":".join(self.source["url"].split(":")[1:])
            blueprints = get_available_blueprints(config)
            match = blueprints.get(blueprint_name, False)

            if not match:
                raise Exception("No blueprint with name '{}' available.".format(blueprint_name))

            cookiecutter_file = os.path.join(match, "cookiecutter.json")

            if os.path.exists(cookiecutter_file):

                temp_path = tempfile.mkdtemp(prefix='frkl.')

                if blueprint_defaults:
                    log.debug("Found interactive blueprints, but using defaults...")
                    cookiecutter(match, output_dir=temp_path, no_input=True)
                else:
                    click.secho("\nFound interactive blueprint, please enter approriate values below:\n", bold=True)

                    cookiecutter(match, output_dir=temp_path)


                subdirs = [os.path.join(temp_path, f) for f in os.listdir(temp_path) if os.path.isdir(os.path.join(temp_path, f))]

                if len(subdirs) != 1:
                    raise Exception("More than one directories created by interactive template '{}'. Can't deal with that.".format(match))

                url = subdirs[0]
                self.source_delete = True

            else:

                url = match
        else:
            url = self.source["url"]

        repo_desc = {}
        repo_desc["blueprint"] = False

        if os.path.exists(os.path.realpath(os.path.expanduser(url))):

            p = os.path.realpath(os.path.expanduser(url))
            if os.path.isfile(p):
                # assuming archive
                repo_desc["type"] = "local_archive"
                repo_desc["remote_url"] = p
                repo_desc["source_delete"] = False
                if self.target_folder == DEFAULT_FRECKLE_TARGET_MARKER:
                    repo_desc["local_parent"] = default_target
                else:
                    repo_desc["local_parent"] = self.target_folder
                repo_desc["checkout_skip"] = False
                if self.target_name is None:
                    repo_desc["local_name"] = os.path.basename(p).split(".")[0]
                else:
                    repo_desc["local_name"] = self.target_name
            else:
                repo_desc["type"] = "local_folder"
                repo_desc["remote_url"] = p
                if self.target_folder == DEFAULT_FRECKLE_TARGET_MARKER:
                    if self.target_name is None:
                        repo_desc["local_parent"] = os.path.dirname(p)
                        repo_desc["checkout_skip"] = True
                    else:
                        repo_desc["local_parent"] = default_target
                        repo_desc["checkout_skip"] = False
                else:
                    repo_desc["local_parent"] = self.target_folder
                    repo_desc["checkout_skip"] = False
                if self.target_name is None:
                    repo_desc["local_name"] = os.path.basename(p)
                else:
                    repo_desc["local_name"] = self.target_name
                repo_desc["source_delete"] = self.source_delete

        elif url.endswith(".git"):

            repo_desc["type"] = "git"
            repo_desc["remote_url"] = url
            if self.target_name is None:
                repo_desc["local_name"] = os.path.basename(repo_desc["remote_url"])[:-4]
            else:
                repo_desc["local_name"] = self.target_name
            repo_desc["checkout_skip"] = False
            if self.target_folder == DEFAULT_FRECKLE_TARGET_MARKER:
                repo_desc["local_parent"] = DEFAULT_FRECKELIZE_TARGET_FOLDER
            else:
                repo_desc["local_parent"] = self.target_folder

            if self.source.get("branch", False):
                repo_desc["remote_branch"] = self.source["branch"]

        elif url.startswith("http://") or url.startswith("https://"):
            # TODO: check whether host is local
            repo_desc["type"] = "remote_archive"
            repo_desc["remote_url"] = url
            if self.local_name is None:
                repo_desc["local_name"] = os.path.basename(url).split('.')[0]
            else:
                repo_desc["local_name"] = self.local_name
            repo_desc["source_delete"] = False
            if self.target_folder == DEFAULT_FRECKLE_TARGET_MARKER:
                repo_desc["local_parent"] = default_target
            else:
                repo_desc["local_parent"] = self.target_folder

            repo_desc["checkout_skip"] = False

        else:
            raise Exception("freckle url format unknown, and no valid local path, don't know how to handle that: {}".format(url))


        if repo_desc["local_parent"] == DEFAULT_FRECKLE_TARGET_MARKER:
            raise Exception("default_target can't be set to '{}'".format(DEFAULT_FRECKLE_TARGET_MARKER))
        if not os.path.isabs(repo_desc["local_parent"]) and not repo_desc["local_parent"].startswith("~"):
            raise Exception("Relative path not supported for target folder option, please use an absolute one (or use '~' to indicate a home directory): {}".format(default_target))

        if repo_desc["local_parent"].startswith("~") or repo_desc["local_parent"].startswith("/home"):
            repo_desc["checkout_become"] = False
        else:
            repo_desc["checkout_become"] = True

        repo_desc["include"] = self.include
        repo_desc["exclude"] = self.exclude
        repo_desc["non_recursive"] = self.non_recursive
        repo_desc["id"] = self.id
        repo_desc["priority"] = self.priority

        repo_desc["add_file_list"] = ADD_FILES

        self.repo_desc = repo_desc

        return repo_desc


class FreckleDetails(object):
    """Model class containing all relevant freckle run parameters for a repo.

    If 'freckle_repos' is not a list, it'll be converted into one with itsel as the only item.
    If one of the itesm in the 'freckle_repos' list is a string, it'll be converted to a :class:`FreckleRepo` using default arguments.

    Args:
      freckle_repos (str, list): a list of :class:`FreckleRepo` objects
      profiles_to_run (OrderedDict): an ordered dict with the profile names to run as keys, and potential overlay vars as value
    """

    def __init__(self, freckle_repos, profiles_to_run=None, detail_priority=DEFAULT_REPO_PRIORITY):

        self.freckle_repos = []
        if not isinstance(freckle_repos, (list, tuple)):
            temp_freckle_repos = [freckle_repos]
        else:
            temp_freckle_repos = freckle_repos

        for r in temp_freckle_repos:
            if isinstance(r, string_types):
                r = FreckleRepo(r)
            self.freckle_repos.append(r)

        self.profiles_to_run = profiles_to_run
        self.set_priority(detail_priority)

    def set_priority(self, priority):

        self.priority = priority
        p = 0
        for fr in self.freckle_repos:
            fr.set_priority(self.priority+p)
            p = p + 1000

    def expand_repos(self, config, default_target=None):

        result = []
        for repo in self.freckle_repos:
            result.append(repo.expand(config, default_target))

        return result


class Freckelize(object):
    """Class to configure and execute a freckelize run.

    A freckelize run consists of two 'sub-runs': the checkout run, which (if necessary) checks-out/copies
    the repo/folder in question and reads it's metadata, and the actual processing run, which
    installs and configures the environment using that metadata as configuration.

    If the provided 'freckle_details' value is a single item, it gets converted into a list. If one of
    the items is a string, it gets converted into a :class:`FreckleDetails` object.

    Args:
      freckle_details (list): a list of :class:`FreckleDetails` objects

    """
    def __init__(self, freckle_details, config=None):

        if isinstance(freckle_details, string_types):
            temp_freckle_details = [FreckleDetails(freckle_details)]
        elif isinstance(freckle_details, FreckleRepo):
            temp_freckle_details = [FreckleDetails(freckle_details)]
        elif isinstance(freckle_details, FreckleDetails):
            temp_freckle_details = [freckle_details]
        else:
            temp_freckle_details = [FreckleDetails(freckle_details)]
        self.freckle_details = []

        # to be populated after checkout
        self.freckles_metadata = None
        self.profiles = None
        self.freckle_profile = None

        base_priority = 0
        p = 0
        for d in temp_freckle_details:
            if isinstance(d, string_types):
                d = FreckleDetails(d)

            d.set_priority(base_priority+p)
            self.freckle_details.append(d)
            p = p + 10000

        if config is None:
            config = DEFAULT_FRECKLES_CONFIG
        self.config = config

        paths = [p['path'] for p in expand_repos(config.trusted_repos)]
        self.finder = FreckelizeAdapterFinder(paths)
        self.reader = FreckelizeAdapterReader()
        self.all_repos = OrderedDict()

        for f in self.freckle_details:
            f.expand_repos(self.config)
            for fr in f.freckle_repos:
                self.all_repos[fr.id] = fr

    def start_checkout_run(self, hosts=None, ask_become_pass="auto", no_run=False, output_format="default"):

        if hosts is None:
            hosts = ["localhost"]

        if isinstance(hosts, (list, tuple)):
            if len(hosts) > 1:
                raise Exception("More than one host not supported (for now).")

        log.debug("Starting checkout run, using those repos:")
        for id, r in self.all_repos.items():
            log.debug(readable_json(r.repo_desc, indent=2))

        if not self.all_repos:
            log.info("No freckle repositories specified, doing nothing...")
            return

        print_title("starting freckelize run(s)...")
        extra_profile_vars = {}

        repo_metadata_file = "repo_metadata"

        extra_profile_vars = {}
        # extra_profile_vars.setdefault("freckle", {})["no_run"] = bool(no_run)

        repos = []
        for id, r in self.all_repos.items():
            repos.append(r.repo_desc)

        task_config = [{"vars": {"freckles": repos, "user_vars": extra_profile_vars, "repo_metadata_file": repo_metadata_file}, "tasks": ["freckles_checkout"]}]

        result_checkout = create_and_run_nsbl_runner(task_config, output_format=output_format, ask_become_pass=ask_become_pass,
                                            no_run=no_run, run_box_basics=True, hosts_list=hosts)


        playbook_dir = result_checkout["playbook_dir"]

        repo_metadata_file_abs = os.path.join(playbook_dir, os.pardir, "logs", repo_metadata_file)

        return_code = result_checkout["return_code"]

        if return_code != 0:
            click.echo("Checkout phase failed, not continuing...")
            sys.exit(1)

        all_repo_metadata = json.load(open(repo_metadata_file_abs))
        # TODO: delete file?
        folders_metadata = self.read_checkout_metadata(all_repo_metadata)
        self.freckles_metadata = self.prepare_checkout_metadata(folders_metadata)

        # allow for multiple hosts in the future
        profiles_map = self.calculate_profiles_to_run()

        for profile, folders in profiles_map.items():

            for folder in folders:
                repo = self.all_repos[folder["folder_metadata"]["parent_repo_id"]]
                default_vars = repo.default_vars.get(profile, {})
                overlay_vars = repo.overlay_vars.get(profile, {})
                final_vars = self.process_folder_vars(folder["folder_vars"], default_vars, overlay_vars)
                folder["default_vars"] = default_vars
                folder["overlay_vars"] = overlay_vars
                folder["vars"] = final_vars

        freckle_profile_folders = profiles_map.pop("freckle")
        freckle_profile = {}
        for folder in freckle_profile_folders:
            freckle_profile[folder["folder_metadata"]["full_path"]] = folder

        # now merge the 'freckle' profile vars with the profile vars
        for profile, folders in profiles_map.items():
            for folder in folders:
                path = folder["folder_metadata"]["full_path"]
                base_vars = freckle_profile[path]["vars"]
                temp = frkl.dict_merge(base_vars, folder["vars"], copy_dct=True)
                folder["vars"] = temp

        self.profiles = [(hosts[0], profiles_map)]
        self.freckle_profile = [(hosts[0], freckle_profile)]

        return (self.freckle_profile, self.profiles)

    def process_folder_vars(self, folder_vars, default_vars, overlay_vars):


        final_vars = frkl.dict_merge(default_vars, folder_vars, copy_dct=True)
        frkl.dict_merge(final_vars, overlay_vars, copy_dct=False)

        return final_vars

    def start_freckelize_run(self, ask_become_pass="auto", no_run=False, output_format="default"):

        if self.freckles_metadata is None:
            raise Exception("Checkout not run yet, can't continue.")

        log.debug("Starting freckelize run...")

        host = self.profiles[0][0]
        hosts_list = [host]
        freckelize_metadata = self.profiles[0][1]
        freckelize_freckle_metadata = self.freckle_profile[0][1]
        valid_adapters, adapters_files_map = self.create_adapters_files_map(freckelize_metadata.keys())

        if not valid_adapters:
            click.echo("No valid adapters found, doing nothing...")
            return None

        callback = self.create_adapter_files_callback(valid_adapters.keys(), adapters_files_map)
        additional_roles = self.get_adapter_dependency_roles(valid_adapters.keys())

        sorted_adapters = self.sort_adapters_by_priority(valid_adapters.keys())

        print_title("Using adapters:", title_char="-")
        click.echo()
        for a in sorted_adapters:
            click.echo("  - ", nl=False)
            click.secho(a, bold=True, nl=False)
            click.echo(": {}".format(valid_adapters[a]))
        click.echo()

        task_config = [
            {"vars": {},
             "tasks": [{"freckles":
                        {"user_vars": {},
                         "freckelize_profiles_metadata": freckelize_metadata,
                         "freckelize_freckle_metadata": freckelize_freckle_metadata,
                         "profile_order": sorted_adapters,
                         "adapters_files_map": adapters_files_map}}]}]

        additional_repo_paths = []

        result = create_and_run_nsbl_runner(
            task_config, output_format=output_format, ask_become_pass=ask_become_pass,
            pre_run_callback=callback, no_run=no_run, additional_roles=additional_roles,
            run_box_basics=True, additional_repo_paths=additional_repo_paths, hosts_list=hosts_list)


    def sort_adapters_by_priority(self, adapters):

        if not adapters:
            return []

        prios = []

        for adapter in adapters:

            metadata = self.get_adapter_metadata(adapter)
            priority = metadata.get("__freckles__", {}).get("adapter_priority", DEFAULT_FRECKELIZE_PROFILE_PRIORITY)
            prios.append([priority, adapter])

        profiles_sorted = sorted(prios, key=lambda tup: tup[0])
        return [item[1] for item in profiles_sorted]

    def get_adapter_dependency_roles(self, adapters):

        if not adapters:
            return []

        all_deps = set()
        for adapter in adapters:

            metadata = self.get_adapter_metadata(adapter)
            roles = metadata.get("__freckles__", {}).get("roles", [])
            all_deps |= set(roles)

        return list(all_deps)

    def get_adapter_details(self, adapter):

        adapter_details = self.finder.get_dictlet(adapter)
        return adapter_details

    def get_adapter_metadata(self, adapter):

        adapter_details = self.get_adapter_details(adapter)
        if adapter_details is None:
            return None
        adapter_metadata = self.reader.read_dictlet(adapter_details, {}, {})

        return adapter_metadata

    def create_adapters_files_map(self, adapters):

        files_map = {}
        valid_adapters = OrderedDict()

        for adapter in adapters:
            adapter_metadata = self.get_adapter_metadata(adapter)
            if adapter_metadata is None:
                log.warn("No adapter '{}' found: skipping".format(adapter))
                continue
            adapter_path = self.get_adapter_details(adapter)["path"]
            tasks_init = adapter_metadata.get("tasks_init", [])
            tasks_folder = adapter_metadata.get("tasks_folder", [])
            if not tasks_init and not tasks_folder:
                log.warn("Adapter description for '{}' does not specify any tasks to execute, ignoring...".format(adapter))
            else:
                files_map[adapter] = create_adapter_files_list(adapter, adapter_path, tasks_init, tasks_folder)
                valid_adapters[adapter] = adapter_path

        return (valid_adapters, files_map)

    def create_adapter_files_callback(self, profiles, files_map):

        def copy_callback(ansible_environment_root):
            target_path = os.path.join(ansible_environment_root, "task_lists")
            for adapter, files in files_map.items():
                for f in files["init"]:
                    source_file = f["source"]
                    target_file = os.path.join(target_path, f["target"])
                    os.makedirs(os.path.dirname(target_file))
                    shutil.copyfile(source_file, target_file)
                for f in files["freckle"]:
                    source_file = f["source"]
                    target_file = os.path.join(target_path, f["target"])
                    os.makedirs(os.path.dirname(target_file))
                    shutil.copyfile(source_file, target_file)

        return copy_callback


    def calculate_profiles_to_run(self):

        if self.freckles_metadata is None:
            raise Exception("Checkout not run yet, can't calculate profiles to run.")

        all_profiles = OrderedDict()
        for fd in self.freckle_details:

            if fd.profiles_to_run is None:
                # run all __auto_run__ profiles
                run_map = OrderedDict()

                for repo in fd.freckle_repos:
                    fd_folders = self.get_freckle_folders_for_repo(repo.id)
                    for p, folders in fd_folders.items():
                        for folder in folders:
                            if not folder["folder_vars"].get("__auto_run__", True):
                                log.info("auto-run disabled for profile '{}' in folder '{}', ignoring...".format(p, folder["folder_metadata"]["folder_name"]))
                            else:
                                all_profiles.setdefault(p, []).append(folder)

            else:
                for repo in fd.freckle_repos:
                    fd_folders = self.get_freckle_folders_for_repo(repo.id)
                    for profile, folders in fd_folders.items():
                        for folder in folders:
                            for p in fd.profiles_to_run:
                                all_profiles.setdefault(p, []).append(folder)

        return all_profiles

    def get_freckle_folders_for_repo(self, repo_id):

        if self.freckles_metadata is None:
            raise Exception("Checkout not run yet, can't calculate freckle folders.")

        repos = OrderedDict()

        for profile, details_list in self.freckles_metadata.items():

            for details in details_list:
                if details["folder_metadata"]["parent_repo_id"] == repo_id:
                    repos.setdefault(profile, []).append(details)

        return repos

    def prepare_checkout_metadata(self, folders_metadata):


        profiles_available = OrderedDict()

        for details in folders_metadata:
            extra_vars = details["extra_vars"]
            folder_metadata = details["folder_metadata"]
            folder_vars = details["vars"]

            profile_folder_vars = OrderedDict()
            for v in folder_vars:
                profile = v["profile"]["name"]
                if profile in profile_folder_vars.keys():
                    log.warn("Profile '{}' specified more than once in '{}', ignoring all but the last instance. Please check '{}' for details.".format(profile, os.path.join(folder_metadata["full_path"], ".freckle"), "https://XXX"))

                p_vars = v.get("vars", {})
                profile_folder_vars[profile] = p_vars


            for key, value in profile_folder_vars.items():
                profiles_available.setdefault(key, []).append({"folder_metadata": folder_metadata, "folder_vars": value, "extra_vars": extra_vars})

            if not "freckle" in profile_folder_vars.keys():
                profiles_available.setdefault("freckle", []).append({"folder_metadata": folder_metadata, "folder_vars": {}, "extra_vars": extra_vars})

        return profiles_available

    def read_checkout_metadata(self, folders_metadata):

        temp_vars = OrderedDict()
        extra_vars = OrderedDict()

        for folder, metadata in folders_metadata.items():

            raw_metadata = metadata.pop(METADATA_CONTENT_KEY, False)
            if raw_metadata:
                # md = yaml.safe_load(raw_metadata)
                md = ordered_load(raw_metadata)
                if not md:
                    md = []
                if isinstance(md, dict):
                    md_temp = []
                    for key, value in md.items():
                        md_temp.append({key: value})
                    md = md_temp
                    # if isinstance(md, (list, tuple)):
                    # md = {"vars": md}
            else:
                md = [{"profile": {"name": "freckle"}, "vars": {}}]

            temp_vars.setdefault(folder, []).append(md)

            extra_vars_raw = metadata.pop("extra_vars", False)
            if extra_vars_raw:
                for rel_path, extra_metadata_raw in extra_vars_raw.items():
                    extra_metadata = ordered_load(extra_metadata_raw)
                    if not extra_metadata:
                        # this means there was an empty file. We interprete that as setting a flag to true
                        extra_metadata = True

                    #sub_path, filename = os.path.split(rel_path)
                    tokens = rel_path.split(os.path.sep)
                    last_token = tokens[-1]
                    if last_token.startswith("."):
                        last_token = last_token[1:]
                    else:
                        continue
                    if last_token.endswith(".freckle"):
                        last_token = last_token[0:-8]
                    else:
                        continue
                    tokens[-1] = last_token
                    add_key_to_dict(extra_vars.setdefault(folder, {}), ".".join(tokens), extra_metadata)
                    # extra_vars.setdefault(folder, {}).setdefault(sub_path, {})[filename[1:-8]] = extra_metadata

        result = []
        for freckle_folder, metadata_list in temp_vars.items():

            chain = [frkl.FrklProcessor(DEFAULT_PROFILE_VAR_FORMAT)]
            try:
                frkl_obj = frkl.Frkl(metadata_list, chain)
                # mdrc_init = {"append_keys": "vars/packages"}
                # frkl_callback = frkl.MergeDictResultCallback(mdrc_init)
                frkl_callback = frkl.MergeResultCallback()
                profile_vars_new = frkl_obj.process(frkl_callback)
                item = {}
                item["vars"] = profile_vars_new
                item["extra_vars"] = extra_vars.get(freckle_folder, {})
                item["folder_metadata"] = folders_metadata[freckle_folder]
                result.append(item)
            except (frkl.FrklConfigException) as e:
                raise Exception(
                    "Can't read freckle metadata file '{}/.freckle': {}".format(freckle_folder, e.message))

        result.sort(key=lambda k: operator.itemgetter(k["folder_metadata"]["repo_priority"]))

        return result


class FreckelizeAdapterFinder(DictletFinder):
    """Finder class for freckelize adapters.

    """

    def __init__(self, paths, **kwargs):

        super(FreckelizeAdapterFinder, self).__init__(**kwargs)
        self.paths = paths
        self.adapter_cache = None
        self.path_cache = {}

    def get_all_dictlet_names(self):

        return self.get_all_dictlets().keys()

    def get_all_dictlets(self):
        """Find all freckelize adapters."""

        log.debug("Retrieving all dictlets")

        if self.adapter_cache is None:
            self.adapter_cache = {}
        dictlet_names = OrderedDict()

        all_adapters = OrderedDict()
        for path in self.paths:
            if path not in self.path_cache.keys():

                adapters = find_freckelize_adapters(path)
                self.path_cache[path] = adapters
                frkl.dict_merge(all_adapters, adapters, copy_dct=False)
                frkl.dict_merge(self.adapter_cache, adapters, copy_dct=False)

        return all_adapters

    def get_dictlet(self, name):

        log.debug("Retrieving adapter: {}".format(name))
        if self.adapter_cache is None:
            self.get_all_dictlet_names()

        dictlet = self.adapter_cache.get(name, None)

        if dictlet is None:
            return None
        else:
            return dictlet

class FreckelizeAdapterReader(TextFileDictletReader):
    """Reads a text file and generates metadata for freckelize.

    The file needs to be in yaml format, if it contains a key 'args' the value of
    that is used to generate the freckelize command-line interface.
    The key 'defaults' is used for, well, default values.

    Read more about how the adapter file format: XXX

    Args:
      delimiter_profile (dict): a map describing the delimiter used for templating.
      **kwargs (dict): n/a
    """

    def __init__(self, delimiter_profile=JINJA_DELIMITER_PROFILES["luci"], **kwargs):

        super(FreckelizeAdapterReader, self).__init__(**kwargs)
        self.delimiter_profile = delimiter_profile
        self.tasks_keyword = FX_TASKS_KEY_NAME

    def process_lines(self, content, current_vars):

        log.debug("Processing content: {}".format(content))

        # now, I know this isn't really the most
        # optimal way of doing this,
        # but I don't really care that much about execution speed yet,
        # plus I really want to be able to use variables used in previous
        # lines of the content
        last_whitespaces = 0
        current_lines = ""
        temp_vars = copy.deepcopy(current_vars)

        for line in content:

            if line.strip().startswith("#"):
                continue

            whitespaces = len(line) - len(line.lstrip(' '))
            current_lines = "{}{}\n".format(current_lines, line)
            if whitespaces <= last_whitespaces:

                temp = replace_string(current_lines, temp_vars, **self.delimiter_profile)

                if not temp.strip():
                    continue

                temp_dict = ordered_load(temp)
                if temp_dict:
                    temp_vars = frkl.dict_merge(temp_vars, temp_dict, copy_dct=False)

            last_whitespaces = whitespaces

        if current_lines:
            temp = replace_string(current_lines, temp_vars, additional_jinja_extensions=freckles_jinja_extensions, **self.delimiter_profile)
            temp_dict = ordered_load(temp)
            temp_vars = frkl.dict_merge(temp_vars, temp_dict, copy_dct=False)

        frkl.dict_merge(current_vars, temp_vars, copy_dct=False)
        log.debug("Vars after processing:\n{}".format(readable_json(current_vars, indent=2)))

        return current_vars


class FreckelizeCommand(FrecklesBaseCommand):
    """Class to build the frecklecute command-line interface."""

    FRECKELIZE_ARGS = [(
        "freckle", {
            "required": False,
            "alias": "freckle",
            "doc": {
                "help": FRECKLE_ARG_HELP
            },
            "click": {
                "option": {
                    "multiple": True,
                    "param_decls": ["--freckle", "-f"],
                    "type": RepoType(),
                    "metavar": FRECKLE_ARG_METAVAR
                }
            }
        }),
        ("target_folder", {
            "alias": "target-folder",
            "required": False,
            # "default": "~/freckles",
            "type": str,
            "doc": {
                "help": TARGET_ARG_HELP
            },
            "click": {
                "option": {
                    "param_decls": ["--target-folder", "-t"],
                    "metavar": TARGET_ARG_METAVAR
                }
            }
        }),
        ("target_name", {
            "alias": "target-name",
            "required": False,
            "type": str,
            "doc": {
                "help": TARGET_NAME_ARG_HELP
            },
            "click": {
                "option": {
                    "metavar": TARGET_NAME_ARG_METAVAR
                }
            }
        }),
        ("include", {
            "alias": "include",
            "required": False,
            "doc": {
                "help": INCLUDE_ARG_HELP
            },
            "click": {
                "option": {
                    "param_decls": ["--include", "-i"],
                    "multiple": True,
                    "metavar": INCLUDE_ARG_METAVAR
                }
            }
        }),
        ("exclude", {
            "alias": "exclude",
            "required": False,
            "doc": {
                "help": EXCLUDE_ARG_HELP
            },
            "click": {
                "option": {
                    "param_decls": ["--exclude", "-e"],
                    "multiple": True,
                    "metavar": EXCLUDE_ARG_METAVAR
                }
            }
        }),
        ("ask_become_pass", {
            "alias": "ask-become-pass",
            "default": "auto",
            "doc": {
                "help": ASK_PW_HELP
            },
            "click": {
                "option": {
                    "param_decls": ["--ask-become-pass", "-pw"],
                    "type": ASK_PW_CHOICES
                }
            }
        }),
        ("non_recursive", {
            "alias": "non-recursive",
            "type": bool,
            "required": False,
            "default": False,
            "doc": {
                "help": NON_RECURSIVE_HELP
            },
            "click": {
                "option": {
                    "is_flag": True
                }
            }
        })
    ]

    @staticmethod
    def freckelize_extra_params():

        freckle_option = click.Option(param_decls=["--freckle", "-f"], required=False, multiple=True, type=RepoType(),
                                  metavar=FRECKLE_ARG_METAVAR, help=FRECKLE_ARG_HELP)
        target_option = click.Option(param_decls=["--target-folder", "-t"], required=False, multiple=False, type=str,
                                     metavar=TARGET_ARG_METAVAR,
                                     help=TARGET_ARG_HELP)
        target_name_option = click.Option(param_decls=["--target-name"], required=False, multiple=False, type=str,
                                     metavar=TARGET_NAME_ARG_METAVAR,
                                     help=TARGET_NAME_ARG_HELP)
        include_option = click.Option(param_decls=["--include", "-i"],
                                      help=INCLUDE_ARG_HELP,
                                      type=str, metavar=INCLUDE_ARG_METAVAR, default=[], multiple=True)
        exclude_option = click.Option(param_decls=["--exclude", "-e"],
                                      help=EXCLUDE_ARG_HELP,
                                      type=str, metavar=EXCLUDE_ARG_METAVAR, default=[], multiple=True)
        parent_only_option = click.Option(param_decls=["--non-recursive"],
                                          help=NON_RECURSIVE_HELP,
                                          is_flag=True,
                                          default=False,
                                          required=False,
                                          type=bool
        )

        params = [freckle_option, target_option, target_name_option, include_option, exclude_option,
                           parent_only_option]

        return params


    def __init__(self, **kwargs):

        extra_params = FreckelizeCommand.freckelize_extra_params()
        super(FreckelizeCommand, self).__init__(extra_params=extra_params, **kwargs)
        self.config = DEFAULT_FRECKLES_CONFIG
        self.reader = FreckelizeAdapterReader()
        self.finder = None

    def get_dictlet_finder(self):

        if self.finder is None:
            # need to wait for paths to be initialized
            self.finder =  FreckelizeAdapterFinder(self.paths)

        return self.finder

    def get_dictlet_reader(self):

        return self.reader

    def get_additional_args(self):

        return OrderedDict(FreckelizeCommand.FRECKELIZE_ARGS)

    def freckles_process(self, command_name, default_vars, extra_vars, user_input, metadata, dictlet_details, config, parent_params):

        return {"name": command_name, "default_vars": default_vars, "extra_vars": extra_vars, "user_input": user_input, "adapter_metadata": metadata, "adapter_details": dictlet_details}

def assemble_freckelize_run(*args, **kwargs):

    try:
        result = []
        no_run = kwargs.get("no_run")

        hosts = list(kwargs["host"])
        if not hosts:
            hosts = ["localhost"]

        default_target = kwargs.get("target_folder", None)

        default_target_name = kwargs.get("target_name", None)

        default_freckle_urls = list(kwargs.get("freckle", []))
        default_output_format = kwargs.get("output", "default")

        default_include = list(kwargs.get("include", []))
        default_exclude = list(kwargs.get("exclude", []))

        default_ask_become_pass = kwargs.get("ask_become_pass", None)

        # default_extra_vars_raw = list(kwargs.get("extra_vars", []))

        default_non_recursive = kwargs.get("non_recursive", None)


        default_extra_vars = {}
        # for ev in default_extra_vars_raw:
            # dict_merge(default_extra_vars, ev, copy_dct=False)

        extra_profile_vars = {}
        repos = OrderedDict()
        profiles = []

        metadata = {}
        parent_command_vars = {}

        if default_target:
            parent_command_vars["target_folder"] = default_target
        if default_target_name:
            parent_command_vars["target_folder_name"] = default_target_name
        if default_include:
            parent_command_vars["includes"] = default_include
        if default_exclude:
            parent_command_vars["includes"] = default_include
        if default_ask_become_pass is not None:
            parent_command_vars["password"] = default_ask_become_pass
        if default_non_recursive is not None:
            parent_command_vars["non_recursive"] = default_non_recursive

        if not args[0]:
            # fill missing keys with default values
            if "target_folder" not in parent_command_vars.keys():
                parent_command_vars["target_folder"] = DEFAULT_FRECKLE_TARGET_MARKER
            if "target_folder_name" not in parent_command_vars.keys():
                parent_command_vars["target_folder_name"] = None
            if "include" not in parent_command_vars.keys():
                parent_command_vars["include"] = []
            if "exclude" not in parent_command_vars.keys():
                parent_command_vars["exclude"] = []
            if "password" not in parent_command_vars.keys():
                parent_command_vars["password"] = "auto"
            if "non_recursive" not in parent_command_vars.keys():
                parent_command_vars["non_recursive"] = False

            metadata["__auto__"] = {}

            for details in default_freckle_urls:
                f = details["url"]
                repos[f] = copy.deepcopy(parent_command_vars)
                repos[f]["profiles"] = ["__auto__"]
                repos[f]["repo_details"] = details

            extra_profile_vars = default_extra_vars

        else:

            for p in args[0]:
                pn = p["name"]
                if pn in profiles:
                    raise Exception("Profile '{}' specified twice. I don't think that makes sense. Exiting...".format(pn))
                else:
                    profiles.append(pn)

                metadata[pn] = {}
                metadata[pn]["metadata"] = p["adapter_metadata"]
                metadata[pn]["details"] = p["adapter_details"]

                pvars_defaults = p["default_vars"]
                pvars_extra_vars = p["extra_vars"]
                pvars_user_input = p["user_input"]

                pvars = OrderedDict()
                frkl.dict_merge(pvars, pvars_defaults, copy_dct=False)
                for ev in pvars_extra_vars:
                    frkl.dict_merge(pvars, ev, copy_dct=False)
                frkl.dict_merge(pvars, parent_command_vars, copy_dct=False)
                frkl.dict_merge(pvars, pvars_user_input, copy_dct=False)

                freckles = list(pvars.pop("freckle", []))
                include = set(pvars.pop("include", []))
                exclude = set(pvars.pop("exclude", []))
                target = pvars.pop("target_folder", None)
                ask_become_pass = pvars.pop("ask_become_pass", "auto")
                non_recursive = pvars.pop("non_recursive", False)

                if non_recursive is None:
                    non_recursive = default_non_recursive

                if ask_become_pass == "auto" and default_ask_become_pass != "auto":
                    ask_become_pass = default_ask_become_pass

                extra_profile_vars[pn] = copy.deepcopy(default_extra_vars.get(pn, {}))
                if pvars:
                    for pk, pv in pvars.items():
                        if pv != None:
                            extra_profile_vars[pn][pk] = pv

                # TODO: could check whether there are duplicates, but can't be bothered at the moment

                all_freckles_for_this_profile = default_freckle_urls + freckles

                for freckle_details in all_freckles_for_this_profile:
                    freckle_url = freckle_details["url"]
                    if target:
                        t = target
                    else:
                        t = default_target

                    if t is None:
                        t = DEFAULT_FRECKLE_TARGET_MARKER

                    for i in default_include:
                        if i not in include:
                            include.add(i)
                    for e in default_exclude:
                        if e not in exclude:
                            exclude.add(e)
                    fr = {
                        "target_folder": t,
                        "includes": list(include),
                        "excludes": list(exclude),
                        "password": ask_become_pass,
                        "non_recursive": non_recursive
                    }
                    repos.setdefault(freckle_url, fr)
                    repos[freckle_url].setdefault("profiles", []).append(pn)
                    repos[freckle_url]["repo_details"] = freckle_details

        if (repos):
            print_title("starting freckelize run(s)...")
            temp = execute_freckelize_run(repos, profiles, metadata, extra_profile_vars=extra_profile_vars, no_run=no_run, output_format=default_output_format, ask_become_pass=default_ask_become_pass, hosts_list=hosts)
            result.append(temp)
            click.echo("")

        else:
            click.echo("\nNo repos specified. Doing nothing.")

        return result

    except (Exception) as e:
        log.debug("Error assembling configuration:")
        log.debug(e, exc_info=True)
        message = e.message
        if not message:
            if not e.reason:
                message = "n/a"
            else:
                message = "Reason: {}".format(e.reason)
        click.echo("\nError assembling configuration.\nMessage:  {}\nExiting...".format(message))
        sys.exit(1)


def execute_freckelize_run(repos, profiles, adapter_metadata, extra_profile_vars={}, no_run=False, output_format="default", ask_become_pass="auto", hosts_list=["localhost"]):
    """Executes a freckles run using the provided run details.

    Args:
      repos (dict): dict with freckle urls as key, and details about (optional) include/excludes and target directory.
      profiles (list): list of adapters to use with these freckle repos
      hosts_list (list): a list of hosts to run this run on
    """

    log.debug("Starting freckelize run")
    all_freckle_repos = []

    # augment repo data
    create_freckle_descs(repos)

    repo_metadata_file = "repo_metadata"

    extra_profile_vars.setdefault("freckle", {})["no_run"] = bool(no_run)

    result_checkout = create_freckelize_checkout_run(repos, repo_metadata_file, extra_profile_vars, ask_become_pass=ask_become_pass, output_format=output_format, hosts_list=hosts_list)

    playbook_dir = result_checkout["playbook_dir"]

    repo_metadata_file_abs = os.path.join(playbook_dir, os.pardir, "logs", repo_metadata_file)

    return_code = result_checkout["return_code"]

    if return_code != 0:
        click.echo("Checkout phase failed, not continuing...")
        sys.exit(1)

    all_repo_metadata = json.load(open(repo_metadata_file_abs))

    #TODO: config option to allow freckle folders to contain context
    # add_paths = list(all_repo_metadata.keys())
    add_paths = []
    if not profiles:

        profiles = []

        for repo, metadata in all_repo_metadata.items():

            for vars in metadata["vars"]:
                profile_temp = vars["profile"]["name"]
                if profile_temp == "freckle":
                    continue
                if not vars.get("vars", {}).get(FRECKELIZE_PROFILE_ACTIVE_KEY, True):
                    continue
                if profile_temp not in profiles:
                    profiles.append(profile_temp)

        config = DEFAULT_FRECKLES_CONFIG
        paths = [p['path'] for p in expand_repos(config.trusted_repos)]
        finder = FreckelizeAdapterFinder(paths)
        reader = FreckelizeAdapterReader()

        all_dictlets = finder.get_all_dictlets()
        adapter_metadata = {}
        for profile in profiles:
            dictlet_details = all_dictlets.get(profile, None)
            if not dictlet_details:
                adapter_metadata[profile] = {"metadata": {}}
            else:
                log.debug("Reading adapter: {}".format(dictlet_details["path"]))
                adapter_det = {"metadata": reader.read_dictlet(dictlet_details, {}, {})}
                adapter_metadata[profile] = adapter_det
            adapter_metadata[profile]["details"] = dictlet_details
        sorted_profiles = get_adapter_profile_priorities(profiles, adapter_metadata)
        click.echo()
        print_title("no adapters selected, using folder defaults:\n", title_char="-")
    else:
        sorted_profiles = profiles
        click.echo()
        print_title("using user-selected adapter(s):\n", title_char="-")

    # TODO: maybe sort profile order also when specified manually?
    result = create_freckelize_run(sorted_profiles, repo_metadata_file_abs, adapter_metadata, extra_profile_vars, ask_become_pass=ask_become_pass,
                               output_format=output_format, no_run=no_run, additional_repo_paths=add_paths, hosts_list=hosts_list)

    return result

def create_freckelize_run(profiles, repo_metadata_file, adapter_metadata, extra_profile_vars, ask_become_pass="true", no_run=False,
                        output_format="default", additional_repo_paths=[], hosts_list=["localhost"]):

    # profiles = extract_all_used_profiles(freckle_repos)

    adapters_files_map = create_adapters_files_map(profiles, adapter_metadata)
    callback = add_adapter_files_callback(profiles, adapter_metadata, adapters_files_map, additional_context_repos=additional_repo_paths)

    additional_roles = get_adapter_dependency_roles(profiles, adapter_metadata)

    task_config = [{"vars": {"user_vars": extra_profile_vars, "repo_metadata_file": repo_metadata_file, "profile_order": profiles, "adapters_files_map": adapters_files_map}, "tasks": ["freckles"]}]

    result = create_and_run_nsbl_runner(task_config, output_format=output_format, ask_become_pass=ask_become_pass,
                                      pre_run_callback=callback, no_run=no_run, additional_roles=additional_roles, run_box_basics=True, additional_repo_paths=additional_repo_paths, hosts_list=hosts_list)

    if no_run:

        click.echo()
        click.secho("========================================================", bold=True)
        click.echo()
        click.echo("'no-run' was specified, not executing freckelize run.")
        click.echo()
        click.echo("Variables that would have been used for an actual run:")
        click.echo()
        click.secho("Defaults/User input:", bold=True)
        click.secho("--------------------", bold=True)
        click.echo()
        output(extra_profile_vars, output_type="yaml", indent=2)
        click.echo()
        with open(repo_metadata_file) as metadata_file:
            metadata = json.load(metadata_file)

        click.secho("Folders:", bold=True)
        click.secho("--------", bold=True)
        for folder, details in metadata.items():
            click.echo()
            click.secho("path: ", bold=True, nl=False)
            click.echo("{}:".format(folder))
            click.echo()
            for p_vars in details["vars"]:
                p_name = p_vars["profile"]["name"]
                if p_name in profiles:
                    click.secho("  profile: ", bold=True, nl=False)
                    click.echo(p_name)
                    output(p_vars["vars"], output_type="yaml", indent=4)
            if details["extra_vars"]:
                click.secho("  extra vars:", bold=True)
                output(details["extra_vars"], output_type="yaml", indent=4)
            else:
                click.secho("  extra_vars: ", bold=True, nl=False)
                click.echo("none")

        click.echo()

        sys.exit(0)


def create_freckelize_checkout_run(freckle_repos, repo_metadata_file, extra_profile_vars, ask_become_pass="true", no_run=False, output_format="default", hosts_list=["localhost"]):

    repos_list = [(k, v) for k, v in freckle_repos.items()]

    task_config = [{"vars": {"freckles": repos_list, "user_vars": extra_profile_vars, "repo_metadata_file": repo_metadata_file}, "tasks": ["freckles_checkout"]}]

    result = create_and_run_nsbl_runner(task_config, output_format=output_format, ask_become_pass=ask_become_pass,
                                        no_run=no_run, run_box_basics=True, hosts_list=hosts_list)

    # this isn't really used, as we want to run at least the checkout run to be able to parse .freckle files
    if no_run:
        click.echo("'no-run' option specified, finished")
        sys.exit()

    return result


# def find_adapter_files(extension, valid_profiles=None, config=None, additional_context_repos=[]):

#     profiles = find_supported_profiles(config, additional_context_repos)
#     task_files_to_copy = {}

#     for profile_name, profile_details in profiles.items():

#         if valid_profiles and profile_name not in valid_profiles:
#             continue

#         profile_path = profile_details["path"]
#         profile_child_file = os.path.join(profile_path, "{}.{}".format(profile_name, extension))

#         if not os.path.exists(profile_child_file) or not os.path.isfile(profile_child_file):
#             continue

#         task_files_to_copy[profile_name] = profile_child_file

#     return task_files_to_copy


def create_adapter_files_list(adapter_name, adapter_path, init_task_files, freckle_task_files):

    base_dir = os.path.dirname(adapter_path)
    result = {}
    result["init"] = []
    for f in init_task_files:
        if not os.path.isabs(f):
            f = os.path.join(base_dir, f)

        if not os.path.exists(f):
            raise Exception("Invalid adapter '{}', can't find file: {}".format(adapter_name, f))

        file_details = {}
        file_details["source"] = os.path.join(base_dir, f)
        file_details["target"] = os.path.join(adapter_name, "init", os.path.basename(f))
        # file_details["target"] = "{}/{}/{}".format(adapter_name, "init", os.path.basename(f))

        result["init"].append(file_details)

    result["freckle"] = []
    for f in freckle_task_files:
        if not os.path.isabs(f):
            f = os.path.join(base_dir, f)

        if not os.path.exists(f):
            raise Exception("Invalid adapter '{}', can't find file: {}".format(adapter_name, f))

        file_details = {}
        file_details["source"] = os.path.join(base_dir, f)
        # file_details["target"] = "{}/{}/{}".format(adapter_name, "freckle", os.path.basename(f))
        file_details["target"] = os.path.join(adapter_name, "freckle", os.path.basename(f))
        result["freckle"].append(file_details)

    return result



def find_supported_profiles(config=None, additional_context_repos=[]):

    if not config:
        config = DEFAULT_FRECKLES_CONFIG

    trusted_repos = copy.copy(config.trusted_repos)
    if additional_context_repos:
        trusted_repos.extend(additional_context_repos)

    repos = nsbl.tasks.get_local_repos(trusted_repos, "adapters", DEFAULT_LOCAL_REPO_PATH_BASE, DEFAULT_REPOS, DEFAULT_ABBREVIATIONS)

    result = {}
    for r in repos:
        p = find_freckelize_adapters(r)
        result.update(p)

    return result


@click.command(name="freckelize", cls=FreckelizeCommand, epilog=FRECKELIZE_EPILOG_TEXT, subcommand_metavar="ADAPTER", invoke_without_command=True, result_callback=assemble_freckelize_run, chain=True)
@click_log.simple_verbosity_option(log, "--verbosity")
@click.pass_context
def cli(ctx, **kwargs):
    """Downloads a remote dataset or code (called a 'freckle') and sets up your local environment to be able to handle the data, according to the data's profile.

    Ideally the remote dataset includes all the metadata that is needed to setup the environment, but it's possible to provide some directives using commandline options globally (--target, --include, --exclude), or per adapter (use the --help function on each adapter to view those).

    Locally available adapters for supported profiles are listed below, each having their own configuration. You can specify a 'global' url by adding it's '--freckle' option before any of the subsequently specified adapters, prompting any of those adapters to apply their tasks to it. Or you can assign one (or multiple) freckle to an adapter by providing it after the adapter name.

    For more details, visit the online documentation: https://docs.freckles.io/en/latest/freckelize_command.html
    """

if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
