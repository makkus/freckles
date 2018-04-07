# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import abc
import logging
import os
import six
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

class FrecklesCliFormatter(click.Command):

    def format_help_text(self, ctx, formatter):

        if self.help:
            help_string = self.help.get("help", "No information provided.")
            author = self.help.get("author", None)
            path = self.help.get("path", None)
            homepage = self.help.get("homepage", None)

            formatter.write_paragraph()
            with formatter.indentation():
                formatter.write_text(help_string)

            details = []
            if author:
                details.append(("Author:", author))
            if homepage:
                details.append(("Homepage:", homepage))
            if path:
                details.append(("Local path:", path))

            with formatter.section("Details"):
                formatter.write_dl(details)


def generate_help(metadata, dictlet_details):

    result = {}
    help_string = metadata.get(FX_DOC_KEY_NAME, {}).get("help", None)
    if help_string:
        result["help"] = help_string
    author = metadata.get(FX_DOC_KEY_NAME, {}).get("author", None)
    if author:
        result["author"] = author
    homepage = metadata.get(FX_DOC_KEY_NAME, {}).get("homepage", None)
    if homepage:
        result["homepage"] = homepage
    path = dictlet_details.get("path", "n/a")
    if path:
        result["path"] = path

    return result

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


class FrecklesLucifier(Lucifier):
    """Wrapper class to parse a frecklecutable dictlet and run it's instructions.
    """

    def __init__(self, name, reader, process_function, config, extra_vars, hosts, output, ask_become_pass, no_run, **kwargs):

        super(FrecklesLucifier, self).__init__(**kwargs)
        self.reader = reader
        self.process_function = process_function
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

        freckles_meta = metadata.get(FX_FRECKLES_META_KEY_NAME, {})
        defaults = metadata.get(FX_DEFAULTS_KEY_NAME, {})
        doc = metadata.get(FX_DOC_KEY_NAME, {})
        c_vars = metadata.get(FX_ARGS_KEY_NAME, {})
        params = parse_args_dict(c_vars)

        @click.command(cls=FrecklesCliFormatter, name=self.name)
        @click.pass_context
        def command(ctx, *args, **kwargs):

            context_repos = freckles_meta.get("context_repos", [])
            if context_repos:
                output = ctx.parent.params.get("output", "default")
                download_repos(context_repos, self.config, output)

            all_vars = OrderedDict()
            frkl.dict_merge(all_vars, defaults, copy_dct=False)
            for ev in self.extra_vars:
                frkl.dict_merge(all_vars, ev, copy_dct=False)
            user_input = clean_user_input(kwargs, c_vars)
            frkl.dict_merge(all_vars, user_input, copy_dct=False)

            result = self.process_function(all_vars, metadata, config=self.config, hosts=self.hosts, output=self.output, ask_become_pass=self.ask_become_pass, no_run=self.no_run)
            # replaced_tasks = replace_string(tasks_string, all_vars, additional_jinja_extensions=freckles_jinja_extensions, **JINJA_DELIMITER_PROFILES["luci"])
            # try:
            #     tasks = yaml.safe_load(replaced_tasks)
            # except (Exception) as e:
            #     raise Exception("Can't parse tasks list: {}".format(e))

            # task_config = [{"tasks": tasks}]

            # # placeholder, for maybe later
            # metadata = {}

            # if self.no_run:
            #     parameters = create_and_run_nsbl_runner(task_config, task_metadata=metadata, output_format=self.output,
            #                                             ask_become_pass=self.ask_become_pass, no_run=True, config=self.config, hosts_list=self.hosts)
            #     print_task_list_details(task_config, task_metadata=metadata, output_format=self.output,
            #                             ask_become_pass=self.ask_become_pass, run_parameters=parameters)
            #     result = None
            # else:
            #     result = create_and_run_nsbl_runner(task_config, task_metadata=metadata, output_format=self.output,
            #                                         ask_become_pass=self.ask_become_pass, config=self.config, run_box_basics=True, hosts_list=self.hosts)
            #     # create_and_run_nsbl_runner(task_config, output, ask_become_pass)

            return result

            # output(tasks, output_type="yaml")

        command.params = params
        help_details = generate_help(metadata, dictlet_details)
        command.help = help_details
        if "short_help" in doc.keys():
            command.short_help = doc.get("short_help")
        if "epilog" in doc.keys():
            command.epilog = doc.get("epilog", None)

        return command


@six.add_metaclass(abc.ABCMeta)
class FrecklesBaseCommand(click.MultiCommand):
    """Base class to provide a command-based (similar to e.g. git) cli for frecklecute.
    """

    def __init__(self, **kwargs):

        super(FrecklesBaseCommand, self).__init__(**kwargs)
        self.params[:0] = get_common_options()
        self.config = DEFAULT_FRECKLES_CONFIG
        self.finder = None
        self.reader = None
        self.paths = None
        self.command_cache = {}


    @abc.abstractmethod
    def get_dictlet_reader(self):
        pass

    @abc.abstractmethod
    def get_dictlet_finder(self):
        pass

    @abc.abstractmethod
    def freckles_process(self, all_vars, metadata, config, hosts, output, ask_become_pass, no_run):
        pass

    def init_command_cache(self, ctx, name=None):

        # we only now all paths in question once we have the context
        # repo_source = "using repo(s) from '{}'".format(self.config.config_file)
        # print_repos_expand(self.config.trusted_repos, repo_source=repo_source, warn=True)

        if self.paths is None:
            self.paths = [p['path'] for p in expand_repos(self.config.trusted_repos)]
        if self.finder is None:
            self.finder = self.get_dictlet_finder()

        if name is None:
            result = self.finder.get_all_dictlet_names()
        else:
            #TODO: make efficient
            result = {}
            result[name] = self.finder.get_dictlet(name)
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
        details = self.finder.get_dictlet(name)
        if not details:
            return None

        extra_defaults = ctx.params.get("defaults", {})
        no_run = ctx.params.get("no_run", False)
        output = ctx.params.get("output", "default")
        ask_become_pass = ctx.params.get("ask_become_pass", "auto")
        hosts = list(ctx.params.get("host", ()))
        if not hosts:
            hosts = ["localhost"]

        if self.reader is None:
            self.reader = self.get_dictlet_reader()

        lucifier = FrecklesLucifier(name, self.reader, self.freckles_process, config=self.config, extra_vars=extra_defaults, hosts=hosts, output=output, ask_become_pass=ask_become_pass, no_run=no_run)
        lucifier.overlay_dictlet(name, details, add_dictlet=True)

        commands = lucifier.process()

        if len(commands) == 0:
            print("Can't parse command: {}".format(name))
            return None
        elif len(commands) > 1:
            raise Exception("Need exactly 1 command to continue, got {}: {}".format(len(commands), commands))

        return commands[0]



