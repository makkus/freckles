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
import shutil
import yaml
from collections import OrderedDict
from six import string_types
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

DEFAULT_TASK_LIST_FORMAT = "ansible"

ANSIBLE_FORMAT_MARKER_KEYS = set(["when", "become", "name", "register", "with_items", "with_dict", "loop", "with_list", "until", "retries", "delay", "changed_when", "loop_control", "block", "become_user", "rescue", "always", "notify", "ignore_errors", "failed_when", "changed_when"])

def get_task_list_format(task_list):
    """This is a not quite 100% method to check whether a task list is in ansbile format, or freckle.
    """

    for item in task_list:

        if isinstance(item, string_types):
            return "freckles"
        elif isinstance(item, dict):
            keys = set(item.keys())
            if (keys & ANSIBLE_FORMAT_MARKER_KEYS):
                return "ansible"
        else:
            raise Exception("Not a valid task-list item: {}".format(item))

    # TODO: log outupt
    # could check for 'meta' key above, but 'meta' can be a keyword in ansible too,
    # so figured I check for everything else first
    for item in task_list:
        if "meta" in item.keys():
            return "freckles"

    return None

def print_task_list_details(task_config, task_metadata={}, output_format="default", ask_become_pass="auto",
                            run_parameters={}):
    """Prints the details of a frecklecutable run (if started with the 'no-run' option).
    """

    click.echo()
    click.secho("========================================================", bold=True)
    click.echo()
    click.echo("'no-run' was specified, not executing frecklecute run.")
    click.echo()
    click.echo("Details about this run:")
    click.echo()
    click.secho("frecklecutable:", bold=True, nl=False)
    click.echo(" {}".format(task_metadata.get("command_name", "n/a")))
    click.echo()
    click.secho("Path:", bold=True, nl=False)
    click.echo(" {}".format(task_metadata.get("command_path", "n/a")))
    click.secho("Generated ansible environment:", bold=True, nl=False)
    click.echo(" {}".format(run_parameters.get("env_dir", "n/a")))
    # click.echo("config:")
    # output = yaml.safe_dump(task_config, default_flow_style=False, allow_unicode=True)
    # click.echo()
    # click.echo(output)
    #click.echo(pprint.pformat(task_config))
    # click.echo("")

    # pprint.pprint(run_parameters)
    click.echo("")
    click.secho("Tasks:", bold=True)
    for task in run_parameters["task_details"]:
        details = task.pretty_details()

        # pprint.pprint(details)
        output = yaml.safe_dump(details, default_flow_style=False)

        click.echo("")
        click.echo(output)
        click.echo("")

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
        all_frecklecutables = OrderedDict()
        for path in self.paths:
            if path not in self.path_cache.keys():
                commands = OrderedDict()
                dirs = find_frecklecutable_dirs(path)

                for f_dir in dirs:
                    fx = find_frecklecutables_in_folder(f_dir)
                    frkl.dict_merge(commands, fx, copy_dct=False)

                self.path_cache[path] = commands
                frkl.dict_merge(self.frecklecutable_cache, commands, copy_dct=False)

            frkl.dict_merge(all_frecklecutables, self.path_cache[path], copy_dct=False)

        return all_frecklecutables

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
        self.vars_keyword = FX_VARS_KEY_NAME

    def process_lines(self, content, current_vars):
        """Process a frecklecutable line-by-line.

        The main purpose of this is to extract a task list and vars, as well as
        potential other metadata ('defaults', '__freckle__').

        The parsing is a bit convoluted, as the metadata as well as 'vars' can be in a commented section,
        so 'valid' ansible tasks lists can be used here.

        The 'vars' and 'tasks' keys need to be at the lasts ones (in this order, preferrably).
        The 'vars' key can either be in a commented section, or not.

        If using comments, all the keys in commented section need to have the same comment prefix.
        """

        log.debug("Processing: {}".format(content))

        # now, I know this isn't really the most
        # optimal way of doing this,
        # but I don't really care that much about execution speed yet,
        # plus I really want to be able to use variables used in previous
        # lines of the content
        last_whitespaces = 0
        current_lines = ""
        temp_vars = copy.deepcopy(current_vars)

        meta_started = False

        tasks_started = False
        tasks_finished = False

        vars_started = False
        vars_finished = False
        vars_meta_started = False
        vars_meta_finished = False
        tasks_string = ""
        vars_string = ""

        for line in content:

            # print("LINE: "+line)

            if not tasks_started and not vars_started:

                if line.startswith("{}:".format(self.tasks_keyword)):
                    tasks_started = True
                    continue
                elif line.startswith("{}:".format(self.vars_keyword)):
                    vars_started = True
                    continue

                if not meta_started:
                    if "defaults:" in line:
                        ignore_prefix = line.partition("defaults:")[0]
                    elif "__freckles__:" in line:
                        ignore_prefix = line.partition("__freckles__:")[0]
                    elif "args:" in line:
                        ignore_prefix = line.partition("args:")[0]
                    elif "{}:".format(self.vars_keyword) in line:
                        ignore_prefix = line.partition("vars:")[0]
                        vars_meta_started = True
                        meta_started = True
                        continue
                    else:
                        continue

                    meta_started = True
                else:
                    if ignore_prefix and not line.startswith(ignore_prefix) and not (ignore_prefix.strip() and line.startswith(ignore_prefix.strip())):
                        meta_started = False
                        continue

                line_new = line[len(ignore_prefix):]

                if line_new.startswith("{}:".format(self.vars_keyword)):
                    vars_meta_started = True
                    continue

                if vars_meta_started:
                    vars_string = "{}\n{}".format(vars_string, line_new)
                    continue

                whitespaces = len(line_new) - len(line_new.lstrip(' '))
                current_lines = "{}{}\n".format(current_lines, line_new)
                if whitespaces <= last_whitespaces:

                    temp = replace_string(current_lines, temp_vars, **self.delimiter_profile)

                    if not temp.strip():
                        continue

                    temp_dict = ordered_load(temp)
                    temp_vars = frkl.dict_merge(temp_vars, temp_dict, copy_dct=False)

                last_whitespaces = whitespaces
            else:
                if line.startswith("{}:".format(self.vars_keyword)):
                    if tasks_started:
                        tasks_finished = True

                    tasks_started = False
                    if vars_finished:
                        raise Exception("Can't have two segments starting with '{}' in frecklecutable.".format(self.vars_keyword))
                    vars_started = True

                elif line.startswith("{}:".format(self.tasks_keyword)):
                    if vars_started:
                        vars_finished = True

                    vars_started = False
                    if tasks_finished:
                        raise Exception("Can't have two segments starting with '{}' in frecklecutable".format(self.tasks_keyword))

                    tasks_started = True
                else:
                    if vars_started:
                        vars_string = "{}\n{}".format(vars_string, line)
                    elif tasks_started:
                        tasks_string = "{}\n{}".format(tasks_string, line)
                    else:
                        raise Exception("Internal error in frecklecutable reader. Please report an issue.")

        if current_lines:
            temp = replace_string(current_lines, temp_vars, additional_jinja_extensions=freckles_jinja_extensions, **self.delimiter_profile)
            temp_dict = ordered_load(temp)
            temp_vars = frkl.dict_merge(temp_vars, temp_dict, copy_dct=False)

        frkl.dict_merge(current_vars, temp_vars, copy_dct=False)
        current_vars[self.tasks_keyword] = tasks_string
        current_vars[self.vars_keyword] = vars_string

        log.debug("Vars after processing: {}".format(current_vars))
        return current_vars


class FrecklecuteCommand(FrecklesBaseCommand):
    """Class to build the frecklecute command-line interface."""

    def get_dictlet_finder(self):

        return FrecklecutableFinder(self.paths)

    def get_dictlet_reader(self):

        return FrecklecutableReader()

    def get_additional_args(self):
        return {}

    def freckles_process(self, command_name, default_vars, extra_vars, user_input, metadata, dictlet_details, config, parent_params):

        all_vars = OrderedDict()
        frkl.dict_merge(all_vars, default_vars, copy_dct=False)
        for ev in extra_vars:
            frkl.dict_merge(all_vars, ev, copy_dct=False)
        frkl.dict_merge(all_vars, user_input, copy_dct=False)

        hosts = parent_params.get("hosts", ["localhost"])
        output_format = parent_params.get("output", "default")
        ask_become_pass = parent_params.get("ask_become_pass", "auto")
        no_run = parent_params.get("no_run", False)
        tasks_string = metadata.get(FX_TASKS_KEY_NAME, "")
        vars_string = metadata.get(FX_VARS_KEY_NAME, "")

        replaced_vars = replace_string(vars_string, all_vars, additional_jinja_extensions=freckles_jinja_extensions, **JINJA_DELIMITER_PROFILES["luci"])
        try:
            vars_dictlet = yaml.safe_load(replaced_vars)
        except (Exception) as e:
            raise Exception("Can't parse vars: {}".format(e))

        if vars_dictlet:
            temp_new_all_vars = frkl.dict_merge(all_vars, vars_dictlet, copy_dct=True)
        else:
            temp_new_all_vars = all_vars

        replaced_tasks = replace_string(tasks_string, temp_new_all_vars, additional_jinja_extensions=freckles_jinja_extensions, **JINJA_DELIMITER_PROFILES["luci"])
        try:
            tasks_list = ordered_load(replaced_tasks)
        except (Exception) as e:

            raise click.ClickException("Could not parse frecklecutable '{}': {}".format(comamnd_name, e))

        # assuming this is an ansible task list
        # pprint(replaced_tasks)
        # TODO: confirm this is ansible task list
        # getting additional task lists

        task_lists = metadata.get("__freckles__", {}).get("task_lists", [])
        if isinstance(task_lists, string_types):
            task_lists = [task_lists]
        elif isinstance(task_lists, dict):
            task_lists_temp = []
            for name, path in task_lists.items():
                task_lists_temp.append({name: path})
            task_lists = task_lists_temp

        dictlet_path = dictlet_details["path"]
        dictlet_parent = os.path.dirname(dictlet_path)

        result_task_list = {}
        for task_list in task_lists:
            if isinstance(task_list, string_types):
                raise Exception("Invalid specification of task list, need key/value: {}".format(task_list))
            elif isinstance(task_list, dict):
                for name, path in task_list.items():
                    if os.path.isabs(path):
                        file_path = path
                    else:
                        file_path = os.path.join(dictlet_parent, path)

                    if not os.path.exists(file_path) or not os.path.isfile(file_path):
                        raise Exception("Can't load task list: {}".format(file_path))

                    filename = os.path.basename(path)
                    play_target = os.path.join("{{ playbook_dir}}", "..", "task_lists", filename)
                    result_task_list[name] = {"source": file_path, "play_target": play_target, "filename": filename}
            else:
                raise Exception("Can't parse task list: {}".format(task_lists))

        # check for hardcoded task_list_format:
        task_list_format = metadata.get("__freckles__", {}).get("task_list_format", None)
        if task_list_format is None:
            # check whether task list is freckles or ansible style
            task_list_format = get_task_list_format(tasks_list)
            if task_list_format == None:
                log.info("Could not determine task list format for sure, falling back to 'ansible'.")
                task_list_format = DEFAULT_TASK_LIST_FORMAT

        if task_list_format == "freckles":
            ansible = False
        elif task_list_format == "ansible":
            ansible = True
        else:
            raise Exception("Invalid task list format: {}".format(task_list_format))

        def copy_task_list_callback(ansible_environment_root):

            target_path = os.path.join(ansible_environment_root, "task_lists")
            os.makedirs(target_path)

            for name, details in result_task_list.items():
                source_name = details["filename"]
                source = details["source"]
                target_file = os.path.join(target_path, source_name)
                log.debug("Copying: {} -> {}".format(source, target_file))
                shutil.copyfile(source, target_file)

            if ansible:
                target_file = os.path.join(target_path, "frecklecutable_default_tasks.yml")
                with open(target_file, 'w') as f:
                    yaml.safe_dump(tasks_list, f, default_flow_style=False, allow_unicode=True, encoding="utf-8")

        callback = copy_task_list_callback

        task_list_aliases = {}
        for name, details in result_task_list.items():
            task_list_aliases[name] = details["play_target"]

        if ansible:
            relative_target_file = os.path.join("{{ playbook_dir }}", "..", "task_lists", "frecklecutable_default_tasks.yml")
            tasks = [
                {"meta": {
                    "name": "include_tasks",
                    "var-keys": ["free_form"],
                },
                 "vars": {
                     "free_form": relative_target_file
                 }}]


            # getting ansible roles, this is not necessary for the minimal configuration format
            additional_roles = metadata.get("__freckles__", {}).get("roles", [])
        else:
            tasks = tasks_list
            additional_roles = []


        frkl.dict_merge(temp_new_all_vars, task_list_aliases, copy_dct=False)
        task_config = [{"tasks": tasks, "vars": temp_new_all_vars}]

        # placeholder, for maybe later
        task_metadata = {}

        if no_run:
            parameters = create_and_run_nsbl_runner(task_config, task_metadata=task_metadata, output_format=output_format, pre_run_callback=callback,
                                                    ask_become_pass=ask_become_pass, no_run=True, config=config, hosts_list=hosts, additional_roles=additional_roles)
            print_task_list_details(task_config, task_metadata=metadata, output_format=output_format,
                        ask_become_pass=ask_become_pass, run_parameters=parameters)
            result = None
        else:
            result = create_and_run_nsbl_runner(task_config, task_metadata=metadata, output_format=output_format, pre_run_callback=callback,
                                                ask_become_pass=ask_become_pass, config=config, run_box_basics=True, hosts_list=hosts, additional_roles=additional_roles)
            # create_and_run_nsbl_runner(task_config, output, ask_become_pass)

            click.echo()

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
