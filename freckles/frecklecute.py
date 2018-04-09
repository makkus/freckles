# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
import os
import sys

import click
import click_completion
import click_log
import copy
import nsbl
import yaml
from collections import OrderedDict
from pprint import pprint
from frkl import frkl
from luci import Lucifier, DictletReader, DictletFinder, vars_file, TextFileDictletReader, parse_args_dict, output, JINJA_DELIMITER_PROFILES, replace_string, ordered_load, clean_user_input
from . import print_version
from .freckles_defaults import *
from .utils import DEFAULT_FRECKLES_CONFIG, download_extra_repos, HostType, print_repos_expand, expand_repos,  create_and_run_nsbl_runner, freckles_jinja_extensions, download_repos
from .freckles_base_cli import FrecklesBaseCommand, FrecklesLucifier

log = logging.getLogger("freckles")
click_log.basic_config(log)

# optional shell completion
click_completion.init()

# TODO: this is a bit ugly, probably have refactor how role repos are used
nsbl.defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")

VARS_HELP = "variables to be used for templating, can be overridden by cli options if applicable"
DEFAULTS_HELP = "default variables, can be used instead (or in addition) to user input via command-line parameters"
KEEP_METADATA_HELP = "keep metadata in result directory, mostly useful for debugging"
FRECKLECUTE_EPILOG_TEXT = "frecklecute is free and open source software and part of the 'freckles' project, for more information visit: https://docs.freckles.io"


def find_frecklecutable_dirs(path, use_root_path=True):
    """Helper method to find 'child' frecklecutable dirs.

    Frecklecutables can either be in the root of a provided 'trusted-repo', or
    in any subfolder within, as long as the subfolder is called 'frecklecutables'.
    Also, if a subfolder contains a marker file called '.frecklecutables'.

    Args:
      path (str): the root path (usually the path to a 'trusted repo').
      use_root_path (bool): whether to include the supplied path
    Returns:
      list: a list of valid 'frecklecutable' paths
    """

    if not os.path.isdir(path):
        return []

    if use_root_path:
        result = [path]
    else:
        result = []

    for root, dirnames, filenames in os.walk(os.path.realpath(path), topdown=True, followlinks=True):

        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]

        for dirname in dirnames:
            if dirname == "frecklecutables" or dirname == ".frecklecutables":
                dir_path = os.path.join(root, dirname)
                if dir_path not in result:
                    result.append(dir_path)

        for filename in filenames:
            if filename == ".frecklecutables":
                if root not in result:
                    result.append(root)

    return result

def is_frecklecutable(file_path, allow_dots_in_filename=False):

    if not allow_dots_in_filename and "." in os.path.basename(file_path):
        log.debug("Not using '{}' as frecklecutable: filename contains '.'".format(file_path))
        return False

    if not os.path.isfile(file_path):
        return False

    return True

def find_frecklecutables_in_folder(path, allow_dots_in_filename=False):

    result = OrderedDict()
    for child in os.listdir(path):

        file_path = os.path.realpath(os.path.join(path, child))

        if not is_frecklecutable(file_path):
            continue

        result[child] = {"path": file_path, "type": "file"}

    return result

class FrecklecutableFinder(DictletFinder):
    """Finder class for frecklecutables.

    First it checks whether there exists a file with the provided name.
    If that is not the case, it checks all configured context repos and tries
    to find the requested file in the root of the context repo, or in any subfolder that
    is called 'frecklecutables', or that has a marker file called '.frecklecutables' in
    it.

    Frecklecutables are not allowed to have a '.' in their file name (for now anyway).
    """

    def __init__(self, paths, **kwargs):

        super(FrecklecutableFinder, self).__init__(**kwargs)
        self.paths = paths
        self.frecklecutable_cache = None
        self.path_cache = {}

    def get_all_dictlet_names(self):

        return self.get_all_dictlets().keys()

    def get_all_dictlets(self):
        """Find all frecklecutables."""

        if self.frecklecutable_cache is None:
            self.frecklecutable_cache = {}
        dictlet_names = OrderedDict()
        for path in self.paths:
            if path not in self.path_cache.keys():
                commands = OrderedDict()
                dirs = find_frecklecutable_dirs(path)

                for f_dir in dirs:
                    fx = find_frecklecutables_in_folder(f_dir)
                    frkl.dict_merge(commands, fx, copy_dct=False)

                self.path_cache[path] = commands
                frkl.dict_merge(self.frecklecutable_cache, commands, copy_dct=False)

            frkl.dict_merge(dictlet_names, self.path_cache[path], copy_dct=False)

        return dictlet_names.keys()

    def get_dictlet(self, name):

        dictlet = None
        if self.frecklecutable_cache is None:
            # try path first
            abs_file = os.path.realpath(name)
            if os.path.isfile(abs_file) and is_frecklecutable(abs_file):
                dictlet = {"path": abs_file, "type": "file"}

        if dictlet is None:
            self.get_all_dictlet_names()
            dictlet = self.frecklecutable_cache.get(name, None)

        if dictlet is None:
            return None
        else:
            return dictlet

class FrecklecutableReader(TextFileDictletReader):
    """Reads a text file and generates metadata for frecklecute.

    The file needs to be in yaml format, if it contains a key 'args' the value of
    that is used to generate the frecklecutables command-line interface.
    The key 'defaults' is used for, well, default values. The most important key, and only
    required one is 'tasks'. The value of this is read as a string, which will then be used
    as a jinja2 template to create a valid task list, after overlaying several levels of default
    values if necessary.
    """

    def __init__(self, delimiter_profile=JINJA_DELIMITER_PROFILES["luci"], **kwargs):

        super(FrecklecutableReader, self).__init__(**kwargs)
        self.delimiter_profile = delimiter_profile
        self.tasks_keyword = FX_TASKS_KEY_NAME

    def process_lines(self, content, current_vars):

        log.debug("Processing: {}".format(content))

        # now, I know this isn't really the most
        # optimal way of doing this,
        # but I don't really care that much about execution speed yet,
        # plus I really want to be able to use variables used in previous
        # lines of the content
        last_whitespaces = 0
        current_lines = ""
        temp_vars = copy.deepcopy(current_vars)
        tasks_started = False
        tasks_string = ""

        for line in content:

            if not tasks_started:
                if line.strip().startswith("#"):
                    continue

                if line.startswith(self.tasks_keyword):
                    tasks_started = True
                    continue

                whitespaces = len(line) - len(line.lstrip(' '))
                current_lines = "{}{}\n".format(current_lines, line)
                if whitespaces <= last_whitespaces:

                    temp = replace_string(current_lines, temp_vars, **self.delimiter_profile)

                    if not temp.strip():
                        continue

                    temp_dict = ordered_load(temp)
                    temp_vars = frkl.dict_merge(temp_vars, temp_dict, copy_dct=False)

                last_whitespaces = whitespaces
            else:
                tasks_string = ("{}\n{}".format(tasks_string, line))

        if current_lines:
            temp = replace_string(current_lines, temp_vars, additional_jinja_extensions=freckles_jinja_extensions, **self.delimiter_profile)
            temp_dict = ordered_load(temp)
            temp_vars = frkl.dict_merge(temp_vars, temp_dict, copy_dct=False)

        frkl.dict_merge(current_vars, temp_vars, copy_dct=False)

        current_vars[self.tasks_keyword] = tasks_string

        log.debug("Vars after processing: {}".format(current_vars))
        return current_vars


class FrecklecuteCommand(FrecklesBaseCommand):
    """Class to build the frecklecute command-line interface."""

    def get_dictlet_finder(self):

        return FrecklecutableFinder(self.paths)

    def get_dictlet_reader(self):

        return FrecklecutableReader()

    def get_additional_args(self):
        pass

    def freckles_process(self, command_name, all_vars, metadata, dictlet_details, config, parent_params):

        hosts = parent_params.get("hosts", None)
        output = parent_params.get("output", "default")
        ask_become_pass = parent_params.get("ask_become_pass", "auto")
        no_run = parent_params.get("no_run", False)
        tasks_string = metadata.get(FX_TASKS_KEY_NAME, "")

        replaced_tasks = replace_string(tasks_string, all_vars, additional_jinja_extensions=freckles_jinja_extensions, **JINJA_DELIMITER_PROFILES["luci"])
        try:
            tasks = yaml.safe_load(replaced_tasks)
        except (Exception) as e:
            raise Exception("Can't parse tasks list: {}".format(e))

        task_config = [{"tasks": tasks}]

        # placeholder, for maybe later
        task_metadata = {}

        if no_run:
            parameters = create_and_run_nsbl_runner(task_config, task_metadata=task_metadata, output_format=output,
                                                    ask_become_pass=ask_become_pass, no_run=True, config=config, hosts_list=hosts)
            print_task_list_details(task_config, task_metadata=metadata, output_format=output,
                                    ask_become_pass=ask_become_pass, run_parameters=parameters)
            result = None
        else:
            result = create_and_run_nsbl_runner(task_config, task_metadata=metadata, output_format=output,
                                                ask_become_pass=ask_become_pass, config=config, run_box_basics=True, hosts_list=hosts)
            # create_and_run_nsbl_runner(task_config, output, ask_become_pass)

        return result


@click.command(name="frecklecute", cls=FrecklecuteCommand, epilog=FRECKLECUTE_EPILOG_TEXT, subcommand_metavar="FRECKLECUTEABLE")
@click_log.simple_verbosity_option(log, "--verbosity")
@click.pass_context
def cli(ctx, **kwargs):
    """Executes a list of tasks specified in a (yaml-formated) text file (called a 'frecklecutable').

    *frecklecute* comes with a few default frecklecutables that are used to manage itself (as well as its sister application *freckles*) as well as a few useful generic ones. Visit the online documentation for more details: https://docs.freckles.io/en/latest/frecklecute_command.html
    """
    pass

if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
