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
from .freckles_base_cli import FrecklesBaseCommand, FrecklesLucifier, process_extra_task_lists, create_external_task_list_callback, get_task_list_format, parse_tasks_dictlet
# from .freckle_detect import create_freckle_descs

log = logging.getLogger("freckles")
click_log.basic_config(log)

# optional shell completion
click_completion.init()

# TODO: this is a bit ugly, probably have refactor how role repos are used
nsbl.defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")

VARS_ARG_HELP = "extra variables for this adapter, can be overridden by cli options if applicable"
VARS_ARG_METAVAR = "VARS"
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

# for debug purposes, sometimes it's easier to read the output if list of files is not present in folder metadata. This will make some adapters not work though.
ADD_FILES = True

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
      non_recursive (bool): whether to only use the source base folder, not any containing sub-folders that contain a '.freckle' marker file
      priority (int): the priority of this repo (determines the order in which it gets processed)
      default_vars (dict): default values to be used for this repo (key: profile_name, value: vars)
      overlay_vars (dict): overlay values to be used for this repo (key: profile_name, value: vars), those will be overlayed after the checkout process
    """
    def __init__(self, source, target_folder=None, target_name=None, include=None, exclude=None, non_recursive=False, priority=DEFAULT_REPO_PRIORITY, default_vars=None, overlay_vars=None):

        if not source:
            raise Exception("No source provided")

        if isinstance(source, string_types):
            temp_source = DEFAULT_REPO_TYPE.convert(source, None, None)
        else:
            temp_source = source

        self.id = str(uuid.uuid4())

        # self.id = temp_source["url"]

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

    def add_default_vars(self, vars_dict):

        frkl.dict_merge(self.default_vars, vars_dict, copy_dct=False)

    def add_overlay_vars(self, vars_dict):

        frkl.dict_merge(self.overlay_vars, vars_dict, copy_dct=False)

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
                    click.echo()


                subdirs = [os.path.join(temp_path, f) for f in os.listdir(temp_path) if os.path.isdir(os.path.join(temp_path, f))]

                if len(subdirs) != 1:
                    raise Exception("More than one directories created by interactive template '{}'. Can't deal with that.".format(match))

                url = subdirs[0]
                self.source_delete = True

            else:
                url = match

            if self.target_folder == DEFAULT_FRECKLE_TARGET_MARKER:
                self.target_folder = default_target

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
            elif isinstance(r, FreckleRepo):
                self.freckle_repos.append(r)
            else:
                raise Exception("Can't add object of type '{}' to FreckleDetails.".format(type(r)))

        if isinstance(profiles_to_run, string_types):
            profiles_to_run = [profiles_to_run]
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

    def __repr__(self):

        return("{}: {}".format("FreckleDetails", readable_raw(self.__dict__)))

class Freckelize(object):
    """Class to configure and execute a freckelize run.

    A freckelize run consists of two 'sub-runs': the checkout run, which (if necessary) checks-out/copies
    the repo/folder in question and reads it's metadata, and the actual processing run, which
    installs and configures the environment using that metadata as configuration.

    If the provided 'freckle_details' value is a single item, it gets converted into a list. If one of
    the items is a string, it gets converted into a :class:`FreckleDetails` object.

    Args:
      freckle_details (list): a list of :class:`FreckleDetails` objects
      config (FreckleConfig): the configuration to use for this run
      ask_become_pass (bool): whether Ansible should ask the user for a password if necessary
      password (str): the password to use
    """
    def __init__(self, freckle_details, config=None, ask_become_pass=False, password=None):

        if isinstance(freckle_details, string_types):
            temp_freckle_details = [FreckleDetails(freckle_details)]
        elif isinstance(freckle_details, FreckleRepo):
            temp_freckle_details = [FreckleDetails(freckle_details)]
        elif isinstance(freckle_details, FreckleDetails):
            temp_freckle_details = [freckle_details]
        else:
            temp_freckle_details = freckle_details

        self.ask_become_pass = ask_become_pass
        self.password = password

        self.freckle_details = []

        # to be populated after checkout
        self.freckles_metadata = None
        self.profiles = None
        self.freckle_profile = None
        self.repo_lookup = None

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

    def start_checkout_run(self, hosts=None, no_run=False, output_format="default"):

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
        click.echo()
        extra_profile_vars = {}

        repo_metadata_file = "repo_metadata"

        extra_profile_vars = {}
        # extra_profile_vars.setdefault("freckle", {})["no_run"] = bool(no_run)

        repos = []
        for id, r in self.all_repos.items():
            repos.append(r.repo_desc)

        task_config = [{"vars": {"freckles": repos, "user_vars": extra_profile_vars, "repo_metadata_file": repo_metadata_file}, "tasks": ["freckles_checkout"]}]

        result_checkout = create_and_run_nsbl_runner(task_config, output_format=output_format, ask_become_pass=self.ask_become_pass, password=self.password,
                                            no_run=no_run, run_box_basics=True, hosts_list=hosts)

        playbook_dir = result_checkout["playbook_dir"]

        repo_metadata_file_abs = os.path.join(playbook_dir, os.pardir, "logs", repo_metadata_file)

        return_code = result_checkout["return_code"]

        if return_code != 0:
            click.echo("Checkout phase failed, not continuing...")
            sys.exit(1)

        click.echo()

        all_repo_metadata = json.load(open(repo_metadata_file_abs))
        # TODO: delete file?
        folders_metadata = self.read_checkout_metadata(all_repo_metadata)
        (self.freckles_metadata, self.repo_lookup) = self.prepare_checkout_metadata(folders_metadata)

        # allow for multiple hosts in the future

        freckle_profile_folders = self.freckles_metadata.get("freckle")

        freckle_profile = {}  # this is just for easy lookup by path
        for folder in freckle_profile_folders:
            freckle_profile[folder["folder_metadata"]["full_path"]] = folder
            repo = self.all_repos[folder["folder_metadata"]["parent_repo_id"]]
            default_vars = repo.default_vars.get("freckle", {})
            overlay_vars = repo.overlay_vars.get("freckle", {})
            final_vars = self.process_folder_vars(folder["folder_vars"], default_vars, overlay_vars)
            folder["default_vars"] = default_vars
            folder["overlay_vars"] = overlay_vars
            folder["vars"] = final_vars

        profiles_map = self.calculate_profiles_to_run()
        for profile, folders in profiles_map.items():

            for folder in folders:
                repo = self.all_repos[folder["folder_metadata"]["parent_repo_id"]]
                default_vars = repo.default_vars.get(profile, {})
                overlay_vars = repo.overlay_vars.get(profile, {})
                path = folder["folder_metadata"]["full_path"]
                base_vars = freckle_profile[path]["vars"]
                folder["base_vars"] = base_vars
                folder["default_vars"] = default_vars
                folder["overlay_vars"] = overlay_vars

                final_vars = self.process_folder_vars(folder["folder_vars"], default_vars, overlay_vars, base_vars)
                folder["vars"] = final_vars

        self.profiles = [(hosts[0], profiles_map)]
        self.freckle_profile = [(hosts[0], freckle_profile)]

        log.debug("Using freckle details:")
        log.debug(readable_json(self.freckle_profile, indent=2))
        log.debug("Using profile details:")
        log.debug(readable_json(self.profiles, indent=2))

        return (self.freckle_profile, self.profiles)

    def process_folder_vars(self, folder_vars, default_vars, overlay_vars, base_vars={}):

        final_vars = frkl.dict_merge(default_vars, folder_vars, copy_dct=True)
        if base_vars:
            frkl.dict_merge(final_vars, base_vars, copy_dct=False)
        frkl.dict_merge(final_vars, overlay_vars, copy_dct=False)

        return final_vars

    def execute(self, hosts=["localhost"], no_run=False, output_format="default"):

        metadata = self.start_checkout_run(hosts=hosts, no_run=False, output_format=output_format)
        self.start_freckelize_run(no_run=no_run, output_format=output_format)

    def start_freckelize_run(self, no_run=False, output_format="default"):

        if self.freckles_metadata is None:
            raise Exception("Checkout not run yet, can't continue.")

        log.debug("Starting freckelize run...")

        host = self.profiles[0][0]
        hosts_list = [host]
        freckelize_metadata = self.profiles[0][1]
        freckelize_freckle_metadata = self.freckle_profile[0][1]
        valid_adapters, adapters_files_map = self.create_adapters_files_map(freckelize_metadata.keys())

        task_list_aliases = {}
        for name, details in adapters_files_map.items():
            task_list_aliases[name] = details["play_target"]

        if not valid_adapters:
            click.echo("No valid adapters found, doing nothing...")
            return None

        # special case for 'ansible-tasks'
        if "ansible-tasks" in valid_adapters.keys():
            # it's still possible to add the confirmation via an extra var file,
            # but I think that's ok. Happy to hear suggestions if you think this is
            # too risky though.
            p_md = freckelize_metadata["ansible-tasks"]
            confirmation = False
            for md in p_md:
                if md["overlay_vars"].get("ansible_tasks_user_confirmation", False):
                    confirmation = True
                    break;
            if not confirmation:
                raise click.ClickException("As the ansible-tasks adapter can execute arbitrary code, user confirmation is necessary to  use this adatper. Consult the output of 'freckelize ansible-tasks --help' or XXX for more information.")

        tasks_for_callback = []
        for ad, details in valid_adapters.items():
            tasks_for_callback.append(details)

        callback = create_external_task_list_callback(adapters_files_map, tasks_for_callback)
        additional_roles = self.get_adapter_dependency_roles(valid_adapters.keys())

        sorted_adapters = self.sort_adapters_by_priority(valid_adapters.keys())

        click.echo()
        print_title("using adapters:", title_char="-")
        for a in sorted_adapters:
            click.echo()
            click.echo("  - ", nl=False)
            click.secho(a, bold=True, nl=False)
            click.echo(":")
            click.secho("      path", bold=True, nl=False)
            click.echo(": {}".format(valid_adapters[a]["path"]))
            click.secho("      folders", bold=True, nl=False)
            click.echo(":")
            for folder in freckelize_metadata[a]:
                full_path = folder["folder_metadata"]["full_path"]
                click.echo("         - {}".format(full_path))

        click.echo()

        task_config = [
            {"vars": {},
             "tasks": [{"freckles":
                        # {"user_vars": {},
                         {"freckelize_profiles_metadata": freckelize_metadata,
                         "freckelize_freckle_metadata": freckelize_freckle_metadata,
                         "profile_order": sorted_adapters,
                          "task_list_aliases": task_list_aliases}}]}]

        additional_repo_paths = []

        result = create_and_run_nsbl_runner(
            task_config, output_format=output_format, ask_become_pass=self.ask_become_pass, password=self.password,
            pre_run_callback=callback, no_run=no_run, additional_roles=additional_roles,
            run_box_basics=True, additional_repo_paths=additional_repo_paths, hosts_list=hosts_list)

        click.echo()
        if no_run:

            click.secho("========================================================", bold=True)
            click.echo()
            click.echo("'no-run' was specified, not executing freckelize run.")
            click.echo()
            click.echo("Variables that would have been used for an actual run:")
            click.echo()

            click.secho("Profiles:", bold=True)
            click.secho("--------", bold=True)
            for profile, folders in freckelize_metadata.items():
                click.echo()
                click.secho("profile: ", bold=True, nl=False)
                click.echo("{}".format(profile))
                click.echo()
                for folder in folders:
                    folder_metadata = folder["folder_metadata"]
                    click.secho("  path: ", bold=True, nl=False)
                    click.echo(folder_metadata["full_path"])
                    if folder["vars"]:
                        click.secho("  vars: ", bold=True, nl=True)
                        output(folder["vars"], output_type="yaml", indent=4, nl=False)
                        click.echo(u"\u001b[2K\r", nl=False)
                    else:
                        click.secho("  vars: ", bold=True, nl=False)
                        click.echo("none")
                    if folder["extra_vars"]:
                        click.secho("  extra vars:", bold=True)
                        output(folder["extra_vars"], output_type="yaml", indent=4)
                    else:
                        click.secho("  extra_vars: ", bold=True, nl=False)
                        click.echo("none")
            click.echo()


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
            extra_task_lists_map = process_extra_task_lists(adapter_metadata, adapter_path)

            tasks = adapter_metadata.get("tasks", [])
            try:
                tasks_dict = yaml.safe_load(tasks)
            except (Exception) as e:
                raise Exception("Could not parse tasks string: {}".format(tasks))

            if not tasks_dict:
                log.warn("Adapter '{}' doesn't specify any tasks: skipping".format(adapter))
                continue

            task_list_format = get_task_list_format(tasks_dict)
            if task_list_format == "freckles":
                log.warning("Task list for adapter '{}' is 'freckles' format, this is not supported (for now). Ignoring...".format(adapter))
                continue

            intersection = set(files_map.keys()) & set(extra_task_lists_map.keys())
            if intersection:
                raise Exception("Can't execute frecklecute run, adapters {} share the same task_list keys: {}".format(adapters, intersection))

            files_map.update(extra_task_lists_map)

            valid_adapters[adapter] = {"path": adapter_path, "tasks": tasks_dict, "tasks_string": tasks, "tasks_format": "ansible", "target_name": "task_list_{}.yml".format(adapter)}

        return (valid_adapters, files_map)

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
                        if p == "freckle":
                            continue
                        for folder in folders:
                            if not folder["folder_vars"].get("__auto_run__", True):
                                click.echo("  - auto-run disabled for profile '{}' in folder '{}', ignoring...".format(p, folder["folder_metadata"]["folder_name"]))
                            else:
                                all_profiles.setdefault(p, []).append(folder)
            else:
                for profile in fd.profiles_to_run:
                    for repo in fd.freckle_repos:
                        paths_to_get = copy.deepcopy(self.repo_lookup[repo.id])
                        profile_folders = self.get_freckle_folders_for_repo(repo.id)
                        # first check if there is a folder that has profile-specific vars
                        for f in profile_folders.get(profile, []):
                            full_path = f["folder_metadata"]["full_path"]
                            if full_path in paths_to_get:
                                log.debug("Using '{}' profile folder for path: {}".format(profile, full_path))
                                all_profiles.setdefault(profile, []).append(f)
                                paths_to_get.remove(full_path)

                        # if there are still folders left, we use the 'freckle' ones
                        if paths_to_get:
                            for f in profile_folders.get("freckle", []):
                                full_path = f["folder_metadata"]["full_path"]
                                if full_path in paths_to_get:
                                    log.debug("Using 'freckle' profile folder for path: {}".format(full_path))
                                    all_profiles.setdefault(profile, []).append(f)
                                    paths_to_get.remove(full_path)

                        if paths_to_get:
                            raise Exception("Could not find all folders for profile '{}'. Leftover: {}".format(profile, paths_to_get))

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
        all_folders = []

        repo_lookup = OrderedDict()

        for details in folders_metadata:
            extra_vars = details["extra_vars"]
            folder_metadata = details["folder_metadata"]
            folder_vars = details["vars"]

            repo_id = folder_metadata["parent_repo_id"]
            full_path = folder_metadata["full_path"]
            if full_path not in repo_lookup.setdefault(repo_id, []):
                repo_lookup[repo_id].append(full_path)

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

        return (profiles_available, repo_lookup)

    def read_checkout_metadata(self, folders_metadata):

        temp_vars = OrderedDict()
        extra_vars = OrderedDict()
        folder_metadata_lookup = {}

        for metadata in folders_metadata:

            repo_id = metadata["parent_repo_id"]
            folder = metadata["full_path"]

            folder_metadata_lookup.setdefault(repo_id, {})[folder] = metadata

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

            temp_vars.setdefault(repo_id, {}).setdefault(folder, []).append(md)

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
                    add_key_to_dict(extra_vars.setdefault(repo_id, {}).setdefault(folder, {}), ".".join(tokens), extra_metadata)
                    # extra_vars.setdefault(folder, {}).setdefault(sub_path, {})[filename[1:-8]] = extra_metadata

        result = []
        for repo_id, folder_map in temp_vars.items():
            for freckle_folder, metadata_list in folder_map.items():
                chain = [frkl.FrklProcessor(DEFAULT_PROFILE_VAR_FORMAT)]
                try:
                    frkl_obj = frkl.Frkl(metadata_list, chain)
                    # mdrc_init = {"append_keys": "vars/packages"}
                    # frkl_callback = frkl.MergeDictResultCallback(mdrc_init)
                    frkl_callback = frkl.MergeResultCallback()
                    profile_vars_new = frkl_obj.process(frkl_callback)
                    item = {}
                    item["vars"] = profile_vars_new
                    item["extra_vars"] = extra_vars.get(repo_id, {}).get(freckle_folder, {})
                    item["folder_metadata"] = folder_metadata_lookup[repo_id][freckle_folder]
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

        result = parse_tasks_dictlet(content, current_vars)
        return result


    def process_lines_old(self, content, current_vars):

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
        ("profile_extra_vars", {
            "alias": "vars",
            "required": False,
            "type": list,
            "doc": {
                "help": VARS_ARG_HELP
            },
            "click": {
                "option": {
                    "metavar": VARS_ARG_METAVAR,
                    "multiple": True,
                    "type": vars_file
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
        # ("ask_become_pass", {
        #     "alias": "ask-become-pass",
        #     "doc": {
        #         "help": ASK_PW_HELP
        #     },
        #     "click": {
        #         "option": {
        #             "param_decls": ["--ask-become-pass", "-pw"],
        #             "type": ASK_PW_CHOICES
        #         }
        #     }
        # }),
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

    def freckles_process(self, command_name, default_vars, extra_vars, user_input, metadata, dictlet_details, config, parent_params, command_var_spec):

        result = {"name": command_name, "default_vars": default_vars, "extra_vars": extra_vars, "user_input": user_input, "adapter_metadata": metadata, "adapter_details": dictlet_details}

        return result

def assemble_freckelize_run(*args, **kwargs):

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

    default_password = kwargs.get("password", None)
    default_non_recursive = kwargs.get("non_recursive", None)

    default_extra_vars_list = list(kwargs.get("vars", []))
    default_extra_vars = OrderedDict()
    for ev in default_extra_vars_list:
        frkl.dict_merge(default_extra_vars, ev, copy_dct=False)

    parent_command_vars = {}
    if default_target:
        parent_command_vars["target_folder"] = default_target
    if default_target_name:
        parent_command_vars["target_folder_name"] = default_target_name
    if default_include:
        parent_command_vars["includes"] = default_include
    if default_exclude:
        parent_command_vars["includes"] = default_include
    if default_non_recursive is not None:
        parent_command_vars["non_recursive"] = default_non_recursive

    freckle_details = []
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
        if "non_recursive" not in parent_command_vars.keys():
            parent_command_vars["non_recursive"] = False

        prio = 1000
        freckle_repos = []
        # TODO: pre-fill with adapter-defaults?
        for freckle in default_freckle_urls:
            repo = FreckleRepo(freckle, target_folder=parent_command_vars["target_folder"], target_name=parent_command_vars["target_folder_name"], include=parent_command_vars["include"], exclude=parent_command_vars["exclude"], non_recursive=parent_command_vars["non_recursive"], priority=prio, default_vars={}, overlay_vars={"freckle": default_extra_vars})
            prio = prio + 100
            freckle_repos.append(repo)

        details = FreckleDetails(freckle_repos, profiles_to_run=None)
        freckle_details.append(details)
    else:

        multi_freckle_repos = OrderedDict()
        det_prio = 10000
        for p in args[0]:
            pn = p["name"]
            # if pn in profiles.keys():
                # raise Exception("Profile '{}' specified twice. I don't think that makes sense. Exiting...".format(pn))
            metadata = {}
            metadata = {}
            metadata["metadata"] = p["adapter_metadata"]
            metadata["details"] = p["adapter_details"]

            pvars_adapter_defaults = p["default_vars"]

            pvars_extra_vars = p["extra_vars"]
            pvars_user_input = p["user_input"]

            pvars_profile_extra_vars = pvars_user_input.pop("profile_extra_vars", ())

            freckle_default_vars = OrderedDict()
            for ev in pvars_extra_vars:
                frkl.dict_merge(freckle_default_vars, ev, copy_dct=False)

            pvars = OrderedDict()
            for ev in pvars_profile_extra_vars:
                frkl.dict_merge(pvars, ev, copy_dct=False)
            frkl.dict_merge(pvars, pvars_user_input, copy_dct=False)

            freckles = list(pvars.pop("freckle", []))
            include = list(set(pvars.pop("include", [])))
            exclude = list(set(pvars.pop("exclude", [])))
            target_folder = pvars.pop("target_folder", None)
            target_name = pvars.pop("target_name", None)

            # ask_become_pass = pvars.pop("ask_become_pass", None)
            # if ask_become_pass is None:
                # ask_become_pass = default_ask_become_pass

            non_recursive = pvars.pop("non_recursive", False)

            if non_recursive is None:
                non_recursive = default_non_recursive

            log.debug("Merged vars for profile: freckle".format(pn))
            log.debug(readable_json(freckle_default_vars, indent=2))
            log.debug("Merged vars for profile: {}".format(pn))
            log.debug(readable_json(pvars, indent=2))

            all_freckles_for_this_profile = freckles + default_freckle_urls
            if len(all_freckles_for_this_profile) > 1 and target_name is not None:
                raise Exception("Can't use 'target_name' if more than one folders are specified")

            prio = 1000
            freckle_repos = []
            for freckle in all_freckles_for_this_profile:

                repo = FreckleRepo(freckle, target_folder=target_folder, target_name=target_name, include=include, exclude=exclude, non_recursive=non_recursive, priority=prio, default_vars={pn: pvars_adapter_defaults}, overlay_vars={pn: pvars, "freckle": freckle_default_vars})
                prio = prio + 100
                freckle_repos.append(repo)

            details = FreckleDetails(freckle_repos, profiles_to_run=pn, detail_priority=det_prio)
            freckle_details.append(details)
            det_prio = det_prio + 1000

    if default_password is None:
        default_password = "no"

    if default_password == "ask":
        password = click.prompt("Please enter sudo password for this run", hide_input=True)
        click.echo()
        default_password = False
        # TODO: check password valid
    elif default_password == "ansible":
        default_password = True
        password = None
    elif default_password == "no":
        default_password = False
        password = None
    else:
        raise click.ClickException("Can't process password: {}".format(default_password))

    try:
        f = Freckelize(freckle_details, ask_become_pass=default_password, password=password)
        f.execute(hosts=hosts, no_run=no_run, output_format=default_output_format)
    except (Exception) as e:
        raise click.ClickException(str(e))

    sys.exit(0)

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
