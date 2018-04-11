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
from luci import Lucifier, DictletReader, DictletFinder, vars_file, TextFileDictletReader, parse_args_dict, output, JINJA_DELIMITER_PROFILES, replace_string, ordered_load, clean_user_input, convert_args_to_dict
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

    def format_help(self, ctx, formatter):
        """Writes the help into the formatter if it exists.
        This calls into the following methods:
        -   :meth:`format_usage`
        -   :meth:`format_help_text`
        -   :meth:`format_options`
        -   :meth:`format_epilog`
        """
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_options(ctx, formatter)
        self.format_details(ctx, formatter)
        self.format_epilog(ctx, formatter)

    def format_details(self, ctx, formatter):

        if self.freckles_cli_details:
            author = self.freckles_cli_details.get("author", None)
            path = self.freckles_cli_details.get("path", None)
            homepage = self.freckles_cli_details.get("homepage", None)

            details = []
            if author:
                details.append(("Author:", author))
            if homepage:
                details.append(("Homepage:", homepage))
            if path:
                details.append(("Local path:", path))

            with formatter.section("Details"):
                formatter.write_dl(details)


def generate_details(metadata, dictlet_details):

    result = {}
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
    host_option = click.Option(param_decls=["--host"], required=False, multiple=True, help="host(s) to freckelize (defaults to 'localhost')", is_eager=False, type=HostType(), default=["localhost"])
    output_option = click.Option(param_decls=["--output", "-o"], required=False, default="default", show_default=True,
                                 metavar="FORMAT", type=click.Choice(SUPPORTED_OUTPUT_FORMATS),
                                 help="format of the output", is_eager=True)
    ask_become_pass_option = click.Option(param_decls=["--ask-become-pass", "-pw"], show_default=True,
                                          help='whether to force ask for a password, force ask not to, or let try freckles decide (which might not always work)',
                                          type=click.Choice(["auto", "true", "false"]), default="auto")
    version_option = click.Option(param_decls=["--version"], help='prints the version of freckles', type=bool,
                                  is_flag=True, is_eager=True, expose_value=False, callback=print_version)
    no_run_option = click.Option(param_decls=["--no-run"],
                                 help='don\'t execute frecklecute, only prepare environment and print task list',
                                 type=bool, is_flag=True, flag_value=True, required=False)
    use_repo_option = click.Option(param_decls=["--use-repo", "-r"], required=False, multiple=True, help="extra context repos to use", is_eager=True, callback=download_extra_repos, expose_value=True)

    params = [defaults_option, use_repo_option, host_option, output_option, ask_become_pass_option, no_run_option, version_option]

    return params


class FrecklesLucifier(Lucifier):
    """Wrapper class to parse a frecklecutable dictlet and run it's instructions.
    """

    def __init__(self, name, command, extra_vars, parent_params, **kwargs):

        super(FrecklesLucifier, self).__init__(**kwargs)
        self.name = name
        self.command = command
        self.extra_vars = extra_vars
        self.parent_params = parent_params

    def get_default_metadata(self):

        return OrderedDict()

    def get_default_dictlet_reader(self):

        return self.command.get_dictlet_reader()

    def process_dictlet(self, metadata, dictlet_details):

        freckles_meta = metadata.get(FX_FRECKLES_META_KEY_NAME, {})
        defaults = metadata.get(FX_DEFAULTS_KEY_NAME, {})
        doc = metadata.get(FX_DOC_KEY_NAME, {})

        c_vars_dictlet = metadata.get(FX_ARGS_KEY_NAME, {})
        c_vars_command = self.command.get_additional_args()
        # adapter args take precedence
        if c_vars_command:
            c_vars = frkl.dict_merge(c_vars_dictlet, c_vars_command, copy_dct=True)
        else:
            c_vars = c_vars_dictlet

        if not isinstance(c_vars, dict):
            c_vars = convert_args_to_dict(c_vars)

        params = parse_args_dict(c_vars)
        @click.command(cls=FrecklesCliFormatter, name=self.name)
        @click.pass_context
        def command(ctx, *args, **kwargs):

            context_repos = freckles_meta.get("context_repos", [])
            if context_repos:
                output = ctx.parent.params.get("output", "default")
                download_repos(context_repos, self.command.get_config(), output)

            user_input = clean_user_input(kwargs, c_vars)

            result = self.command.freckles_process(self.name, defaults, self.extra_vars, user_input, metadata, dictlet_details, config=self.command.get_config(), parent_params=self.parent_params)
            return result

        command.params = params
        help_string = metadata.get(FX_DOC_KEY_NAME, {}).get("help", None)
        if help_string:
            command.help = help_string
        help_details = generate_details(metadata, dictlet_details)
        command.freckles_cli_details = help_details
        if "short_help" in doc.keys():
            command.short_help = doc.get("short_help")
        if "epilog" in doc.keys():
            command.epilog = doc.get("epilog", None)

        return command


@six.add_metaclass(abc.ABCMeta)
class FrecklesBaseCommand(click.MultiCommand):
    """Base class to provide a command-based (similar to e.g. git) cli for frecklecute.
    """

    def __init__(self, extra_params=None,**kwargs):

        super(FrecklesBaseCommand, self).__init__(**kwargs)
        if extra_params:
            self.params[:0] = extra_params
        self.params[:0] = get_common_options()
        self.config = DEFAULT_FRECKLES_CONFIG
        self.finder = None
        self.reader = None
        self.paths = None

    def get_config(self):
        return self.config

    @abc.abstractmethod
    def get_additional_args(self):
        pass

    @abc.abstractmethod
    def get_dictlet_reader(self):
        pass

    @abc.abstractmethod
    def get_dictlet_finder(self):
        pass

    @abc.abstractmethod
    def freckles_process(self, command_name, default_vars, extra_vars, user_input, metadata, dictlet_details, config, parent_params):
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
            result = self.finder.get_all_dictlets()
        else:
            result = {}
            result[name] = self.finder.get_dictlet(name)
        return result

    def list_commands(self, ctx):
        """Lists all frecklecutables it can find."""

        commands = self.init_command_cache(ctx).keys()
        commands.sort()
        return commands


    def get_command(self, ctx, name):

        details = self.init_command_cache(ctx, name).get(name)
        if not details:
            return None

        extra_defaults = ctx.params.get("defaults", {})

        if self.reader is None:
            self.reader = self.get_dictlet_reader()

        lucifier = FrecklesLucifier(name, self, extra_vars=extra_defaults, parent_params=ctx.params)
        log.debug("Processing command '{}' from: {}".format(name, details.get("path", "n/a")))
        try:
            lucifier.overlay_dictlet(name, details, add_dictlet=True)
        except (Exception) as e:
            log.debug("Processing failed:")
            log.debug(e, exc_info=True)
            log.warn("Can't parse adapter '{}', ignoring...".format(name))
            return None

        commands = lucifier.process()

        if len(commands) == 0:
            log.warn("Can't parse command: {}".format(name))
            return None
        elif len(commands) > 1:
            raise Exception("Need exactly 1 command to continue, got {}: {}".format(len(commands), commands))

        return commands[0]
