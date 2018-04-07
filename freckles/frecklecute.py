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
from .commands import CommandRepo
from .freckles_defaults import *
from .utils import DEFAULT_FRECKLES_CONFIG, download_extra_repos, HostType, print_repos_expand, expand_repos,  create_and_run_nsbl_runner, freckles_jinja_extensions, download_repos

log = logging.getLogger("freckles")
click_log.basic_config(log)

# optional shell completion
click_completion.init()

# TODO: this is a bit ugly, probably have refactor how role repos are used
nsbl.defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")

VARS_HELP = "variables to be used for templating, can be overridden by cli options if applicable"
DEFAULTS_HELP = "default variables, can be used instead (or in addition) to user input via command-line parameters"
KEEP_METADATA_HELP = "keep metadata in result directory, mostly useful for debugging"
FRECKLECUTE_HELP_TEXT = """Executes a list of tasks specified in a (yaml-formated) text file (called a 'frecklecutable').

*frecklecute* comes with a few default frecklecutables that are used to manage itself (as well as its sister application *freckles*) as well as a few useful generic ones. Visit the online documentation for more details: https://docs.freckles.io/en/latest/frecklecute_command.html
"""
FRECKLECUTE_EPILOG_TEXT = "frecklecute is free and open source software and part of the 'freckles' project, for more information visit: https://docs.freckles.io"


def get_common_options():
    """Returns a list of options that are shared between all of the freckles command-line applications.
    """

    defaults_option = click.Option(param_decls=["--defaults", "-d"], required=False, multiple=True, help=DEFAULTS_HELP, type=vars_file, metavar="VARS")
    host_option = click.Option(param_decls=["--host"], required=False, multiple=True, help="host(s) to freckelize (defaults to 'localhost')", is_eager=False, type=HostType())
    output_option = click.Option(param_decls=["--output", "-o"], required=False, default="default",
                                 metavar="FORMAT", type=click.Choice(SUPPORTED_OUTPUT_FORMATS),
                                 help="format of the output", is_eager=True)
    ask_become_pass_option = click.Option(param_decls=["--ask-become-pass", "-pw"],
                                          help='whether to force ask for a password, force ask not to, or let try freckles decide (which might not always work)',
                                          type=click.Choice(["auto", "true", "false"]), default="auto")
    version_option = click.Option(param_decls=["--version"], help='prints the version of freckles', type=bool,
                                  is_flag=True, is_eager=True, expose_value=False, callback=print_version)
    no_run_option = click.Option(param_decls=["--no-run"],
                                 help='don\'t execute frecklecute, only prepare environment and print task list',
                                 type=bool, is_flag=True, default=False, required=False)
    use_repo_option = click.Option(param_decls=["--use-repo", "-r"], required=False, multiple=True, help="extra context repos to use", is_eager=True, callback=download_extra_repos, expose_value=True)

    params = [defaults_option, use_repo_option, host_option, output_option, ask_become_pass_option, no_run_option, version_option]

    return params


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

    def __init__(self, paths, **kwargs):

        super(FrecklecutableFinder, self).__init__(**kwargs)
        self.paths = paths
        self.frecklecutable_cache = None
        self.path_cache = {}

    def get_all_dictlet_names(self):
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

        return dictlet_names

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


class FrecklecuteLucifier(Lucifier):

    def __init__(self, name, config, extra_vars, hosts, output, ask_become_pass, no_run, **kwargs):

        super(FrecklecuteLucifier, self).__init__(**kwargs)
        self.reader = FrecklecutableReader()
        self.name = name
        self.config = config
        self.extra_vars = extra_vars
        self.hosts = hosts
        self.output = output
        self.ask_become_pass = ask_become_pass
        self.no_run = no_run

    def get_default_metadata(self):

        return OrderedDict()

    def get_default_dictlet_reader(self):

        return self.reader

    def process_dictlet(self, metadata, dictlet_details):

        # pprint(metadata["doc"])
        # print("------------")
        # pprint(metadata["args"])
        # print("------------")
        # pprint(self.__dict__)

        freckles_meta = metadata.pop(FX_FRECKLES_META_KEY_NAME, {})
        defaults = metadata.pop(FX_DEFAULTS_KEY_NAME, {})
        doc = metadata.pop(FX_DOC_KEY_NAME, {})
        c_vars = metadata.pop(FX_ARGS_KEY_NAME, {})
        params = parse_args_dict(c_vars)
        tasks_string = metadata.pop(FX_TASKS_KEY_NAME, "")

        @click.command(name=self.name)
        @click.pass_context
        def command(ctx, *args, **kwargs):

            context_repos = freckles_meta.get("context_repos", [])

            output = ctx.parent.params.get("output", "default")

            download_repos(context_repos, self.config, output)

            all_vars = OrderedDict()
            frkl.dict_merge(all_vars, defaults, copy_dct=False)
            for ev in self.extra_vars:
                frkl.dict_merge(all_vars, ev, copy_dct=False)
            user_input = clean_user_input(kwargs, c_vars)
            frkl.dict_merge(all_vars, user_input, copy_dct=False)

            replaced_tasks = replace_string(tasks_string, all_vars, additional_jinja_extensions=freckles_jinja_extensions, **JINJA_DELIMITER_PROFILES["luci"])
            try:
                tasks = yaml.safe_load(replaced_tasks)
            except (Exception) as e:
                raise Exception("Can't parse tasks list: {}".format(e))

            task_config = [{"tasks": tasks}]

            # placeholder, for maybe later
            metadata = {}

            if self.no_run:
                parameters = create_and_run_nsbl_runner(task_config, task_metadata=metadata, output_format=self.output,
                                                        ask_become_pass=self.ask_become_pass, no_run=True, config=self.config, hosts_list=self.hosts)
                print_task_list_details(task_config, task_metadata=metadata, output_format=self.output,
                                        ask_become_pass=self.ask_become_pass, run_parameters=parameters)
                result = None
            else:
                result = create_and_run_nsbl_runner(task_config, task_metadata=metadata, output_format=self.output,
                                                    ask_become_pass=self.ask_become_pass, config=self.config, run_box_basics=True, hosts_list=self.hosts)
                # create_and_run_nsbl_runner(task_config, output, ask_become_pass)

            return result

            output(tasks, output_type="yaml")

        command.params = params
        command.help = doc.get("help", "n/a")
        if "short_help" in doc.keys():
            command.short_help = doc.get("short_help")
        if "epilog" in doc.keys():
            command.epilog = doc.get("epilog", None)

        return command


class FrecklecuteCommand(click.MultiCommand):
    """Base class to provide a command-based (similar to e.g. git) cli for frecklecute.
    """

    def __init__(self, **kwargs):

        super(FrecklecuteCommand, self).__init__(**kwargs)
        self.params[:0] = get_common_options()
        self.config = DEFAULT_FRECKLES_CONFIG
        self.frecklecutable_finder = None
        self.paths = None
        self.command_cache = {}

    def init_command_cache(self, ctx, name=None):

        # we only now all paths in question once we have the context
        # repo_source = "using repo(s) from '{}'".format(self.config.config_file)
        # print_repos_expand(self.config.trusted_repos, repo_source=repo_source, warn=True)

        if self.paths is None:
            self.paths = [p['path'] for p in expand_repos(self.config.trusted_repos)]
        if self.frecklecutable_finder is None:
            self.frecklecutable_finder = FrecklecutableFinder(self.paths)

        if name is None:
            result = self.frecklecutable_finder.get_all_dictlet_names()
        else:
            #TODO: make efficient
            result = {}
            result[name] = self.frecklecutable_finder.get_dictlet(name)
            # result = OrderedDict()

            # # we only need to load one command
            # command = self.command_cache.get(name, None)
            # if command is None:
            #     command = self.frecklecutable_finder.get_dictlet(name)
            #     self.command_cache[name] = command

            # result[name] = command

        return result

    def list_commands(self, ctx):
        """Lists all frecklecutables it can find."""

        commands = list(self.init_command_cache(ctx).keys())
        commands.sort()
        return commands


    def get_command(self, ctx, name):

        self.init_command_cache(ctx, name)
        details = self.frecklecutable_finder.get_dictlet(name)
        if not details:
            return None

        extra_defaults = ctx.params.get("defaults", {})
        no_run = ctx.params.get("no_run", False)
        output = ctx.params.get("output", "default")
        ask_become_pass = ctx.params.get("ask_become_pass", "auto")
        hosts = list(ctx.params.get("host", ()))
        if not hosts:
            hosts = ["localhost"]

        lucifier = FrecklecuteLucifier(name, config=self.config, extra_vars=extra_defaults, hosts=hosts, output=output, ask_become_pass=ask_become_pass, no_run=no_run)
        lucifier.overlay_dictlet(name, details, add_dictlet=True)

        commands = lucifier.process()

        if len(commands) == 0:
            print("Can't parse command: {}".format(name))
            return None
        elif len(commands) > 1:
            raise Exception("Need exactly 1 command to continue, got {}: {}".format(len(commands), commands))

        return commands[0]




@click.command(name="frecklecute", cls=FrecklecuteCommand, epilog=FRECKLECUTE_EPILOG_TEXT, subcommand_metavar="FRECKLECUTEABLE")
@click_log.simple_verbosity_option(log, "--verbosity")
@click.pass_context
def cli(ctx, **kwargs):
    """"""
    pass

if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
