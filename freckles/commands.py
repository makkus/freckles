# -*- coding: utf-8 -*-

# python 3 compatibility
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import os
import pprint
import sys
from pydoc import locate

import click
from jinja2 import Environment, PackageLoader, Template
from six import string_types

import yaml
from frkl.frkl import (PLACEHOLDER, EnsurePythonObjectProcessor,
                       EnsureUrlProcessor, Frkl, MergeDictResultCallback,
                       UrlAbbrevProcessor, YamlTextSplitProcessor)
from nsbl.nsbl import Nsbl, NsblRunner

log = logging.getLogger("freckles")

COMMAND_SEPERATOR = "-"
DEFAULT_ABBREVIATIONS = {
    'gh':
        ["https://github.com/", PLACEHOLDER, "/", PLACEHOLDER, ".git"],
    'bb': ["https://bitbucket.org/", PLACEHOLDER, "/", PLACEHOLDER, ".git"]
}


def replace_string(template_string, replacement_dict):

    return Environment().from_string(template_string).render(replacement_dict)

def render_dict(obj, replacement_dict):

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
FRECKLES_REPO = RepoType()

DEFAULT_COMMAND_REPO = os.path.join(os.path.dirname(__file__), "commands")

class CommandRepo(object):

    def __init__(self, paths):
        if not isinstance(paths, (list, tuple)):
            paths = [paths]

        self.paths = [os.path.expanduser(p) for p in paths]

        if DEFAULT_COMMAND_REPO not in self.paths:
            self.paths.insert(0, DEFAULT_COMMAND_REPO)

        self.commands = self.get_commands()

    def get_commands(self):

        commands = {}
        for path in self.paths:

            path_tokens = len(path.split(os.sep))
            for root, dirs, files in os.walk(path):
                if not files:
                    continue

                path = root.split(os.sep)
                for f in files:
                    command_name = COMMAND_SEPERATOR.join(path[path_tokens:] + [f])
                    command = self.create_command(command_name, os.path.join(root, f))
                    commands[command_name] = command

        return commands

    def get_command(self, ctx, command_name):

        options_list = self.commands[command_name]["options"]
        key_map = self.commands[command_name]["key_map"]
        tasks = self.commands[command_name]["tasks"]
        task_vars = self.commands[command_name]["vars"]
        doc = self.commands[command_name]["doc"]
        args_that_are_vars = self.commands[command_name]["args_that_are_vars"]

        def command_callback(**kwargs):

            # exchange arg_name with var name
            new_args = {}
            for key, value in key_map.items():
                temp = kwargs.pop(key)
                if key not in args_that_are_vars:
                    new_args[value] = temp
                else:
                    task_vars[value] = temp

            rendered_vars = render_dict(task_vars, new_args)
            rendered_tasks = render_dict(tasks, new_args)

            log.debug("Args: {}".format(new_args))
            log.debug("Vars: {}".format(rendered_vars))
            log.debug("Tasks to execute, with arguments replaced: {}".format(rendered_tasks))

            # print("ARGS")
            # pprint.pprint(new_args)
            # print("VARS")
            # pprint.pprint(rendered_vars)
            # print("TASKS")
            # pprint.pprint(rendered_tasks)
            # sys.exit(0)

            # if not rendered_vars:
                # rendered_vars = kwargs

            task_config = [{"vars": rendered_vars, "tasks": rendered_tasks}]

            debug = ctx.params["debug"]
            nsbl_obj = Nsbl.create(task_config, [], [], wrap_into_localhost_env=True, pre_chain=[])
            runner = NsblRunner(nsbl_obj)
            target = os.path.expanduser("~/.freckles/runs/archive/run")
            ask_become_pass = True
            if debug:
                stdout_callback = "default"
                ansible_verbose = "-vvvv"
            else:
                stdout_callback = "nsbl_internal"
                ansible_verbose = ""
            no_run = False
            force = True
            display_sub_tasks = True
            display_skipped_tasks = False
            runner.run(target, force=force, ansible_verbose=ansible_verbose, ask_become_pass=ask_become_pass, callback=stdout_callback, add_timestamp_to_env=True, add_symlink_to_env="~/.freckles/runs/current", no_run=no_run, display_sub_tasks=display_sub_tasks, display_skipped_tasks=display_skipped_tasks)

        help = doc.get("help", "n/a")
        short_help = doc.get("short_help", help)
        epilog = doc.get("epilog", None)

        command = click.Command(command_name, params=options_list, help=help, short_help=short_help, epilog=epilog, callback=command_callback)
        return command

    def create_command(self, command_name, yaml_file):

        log.debug("Loading command file '{}'...".format(yaml_file))

        #split_config = {"keywords": ["args", "doc", "tasks"]}
        #chain = [UrlAbbrevProcessor(), EnsureUrlProcessor(), YamlTextSplitProcessor(init_params=split_config), EnsurePythonObjectProcessor()]
        chain = [UrlAbbrevProcessor(), EnsureUrlProcessor(), EnsurePythonObjectProcessor()]
        frkl_obj = Frkl(yaml_file, chain)

        config_content = frkl_obj.process(MergeDictResultCallback())
        # with open(yaml_file, 'r') as stream:
            # try:
                # config_content = yaml.safe_load(stream)
            # except yaml.YAMLError as exc:
                # raise exc
                # log.info("Could not parse command file '{}', ignoring...".format(yaml_file))
                # return None

        doc = config_content.get("doc", {})
        # TODO: check format of config
        options = config_content.get("args", {})
        vars = config_content.get("vars", {})
        tasks = config_content.get("tasks", None)

        if not tasks:
            click.echo("No tasks included in command, doing nothing.")
            sys.exit(1)

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
                    raise Exception("Multiple arguments are not supported (yet): {}".format(config_content["vars"]))
                argument_key = key
                required = opt_details.pop("required", None)

                o = click.Argument(param_decls=[key], required=required, **opt_details)
            else:
                o = click.Option(param_decls=["--{}".format(key)], **opt_details)
            options_list.append(o)

        return {"options": options_list, "key_map": key_map, "command_file": yaml_file, "tasks": tasks, "vars": vars, "doc": doc, "args_that_are_vars": args_that_are_vars}
