# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import abc
import copy
import logging
import shutil
from collections import OrderedDict

import click_completion
import click_log
import six
from six import string_types

import nsbl
from frkl import frkl
from luci import Lucifier, vars_file, parse_args_dict, JINJA_DELIMITER_PROFILES, replace_string, ordered_load, \
    clean_user_input, convert_args_to_dict
from . import print_version
from .freckles_defaults import *
from .utils import DEFAULT_FRECKLES_CONFIG, download_extra_repos, HostType, expand_repos, freckles_jinja_extensions, \
    download_repos

log = logging.getLogger("freckles")
click_log.basic_config(log)

# optional shell completion
click_completion.init()

# TODO: this is a bit ugly, probably have refactor how role repos are used
nsbl.defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")

VARS_HELP = "extra variables, can be used instead (or in addition) to user input via command-line parameters"
KEEP_METADATA_HELP = "keep metadata in result directory, mostly useful for debugging"
FRECKLECUTE_HELP_TEXT = """Executes a list of tasks specified in a (yaml-formated) text file (called a 'frecklecutable').

*frecklecute* comes with a few default frecklecutables that are used to manage itself (as well as its sister application *freckles*) as well as a few useful generic ones. Visit the online documentation for more details: https://docs.freckles.io/en/latest/frecklecute_command.html
"""
FRECKLECUTE_EPILOG_TEXT = "frecklecute is free and open source software and part of the 'freckles' project, for more information visit: https://docs.freckles.io"

ANSIBLE_FORMAT_MARKER_KEYS = set(["when", "become", "name", "register", "with_items", "with_dict", "loop", "with_list", "until", "retries", "delay", "changed_when", "loop_control", "block", "become_user", "rescue", "always", "notify", "ignore_errors", "failed_when", "changed_when"])


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

def parse_tasks_dictlet(content, current_vars, tasks_keyword = FX_TASKS_KEY_NAME, vars_keyword = None, delimiter_profile=JINJA_DELIMITER_PROFILES["luci"]):

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

            if line.startswith("{}:".format(tasks_keyword)):
                tasks_started = True
                continue
            elif vars_keyword and line.startswith("{}:".format(vars_keyword)):
                vars_started = True
                continue

            if not meta_started:
                if "defaults:" in line:
                    ignore_prefix = line.partition("defaults:")[0]
                elif "__freckles__:" in line:
                    ignore_prefix = line.partition("__freckles__:")[0]
                elif "doc:" in line:
                    ignore_prefix = line.partition("doc:")[0]
                elif "args:" in line:
                    ignore_prefix = line.partition("args:")[0]
                elif vars_keyword and "{}:".format(vars_keyword) in line:
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

            if vars_keyword and line_new.startswith("{}:".format(vars_keyword)):
                vars_meta_started = True
                continue

            if vars_meta_started:
                vars_string = "{}\n{}".format(vars_string, line_new)
                continue

            whitespaces = len(line_new) - len(line_new.lstrip(' '))
            current_lines = "{}{}\n".format(current_lines, line_new)
            if whitespaces <= last_whitespaces:

                if delimiter_profile:
                    temp = replace_string(current_lines, temp_vars, **delimiter_profile)
                else:
                    temp = current_lines

                if not temp.strip():
                    continue

                temp_dict = ordered_load(temp)
                temp_vars = frkl.dict_merge(temp_vars, temp_dict, copy_dct=False)

            last_whitespaces = whitespaces
        else:
            if vars_keyword and line.startswith("{}:".format(vars_keyword)):
                if tasks_started:
                    tasks_finished = True

                tasks_started = False
                if vars_finished:
                    raise Exception("Can't have two segments starting with '{}' in frecklecutable.".format(self.vars_keyword))
                vars_started = True

            elif line.startswith("{}:".format(tasks_keyword)):
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
        if delimiter_profile:
            temp = replace_string(current_lines, temp_vars, additional_jinja_extensions=freckles_jinja_extensions, **delimiter_profile)
        else:
            temp = current_lines

        if temp.strip():
            temp_dict = ordered_load(temp)
            temp_vars = frkl.dict_merge(temp_vars, temp_dict, copy_dct=False)

    frkl.dict_merge(current_vars, temp_vars, copy_dct=False)
    current_vars[tasks_keyword] = tasks_string
    current_vars[vars_keyword] = vars_string

    log.debug("Vars after processing: {}".format(current_vars))
    return current_vars


def get_task_list_format(task_list):
    """This is a not quite 100% method to check whether a task list is in ansbile format, or freckle.
    """

    for item in task_list:

        if isinstance(item, string_types):
            log.debug("task item '{}' is string, determining this is a 'freckles' task list".format(item))
            return "freckles"
        elif isinstance(item, dict):
            keys = set(item.keys())
            if (keys & ANSIBLE_FORMAT_MARKER_KEYS):
                log.debug("task item keys ({}) contain at least one known Ansible keyword , determining this is 'ansible' task list format".format(keys))
                return "ansible"
        else:
            raise Exception("Not a valid task-list item: {}".format(item))

    # TODO: log outupt
    # could check for 'meta' key above, but 'meta' can be a keyword in ansible too,
    # so figured I check for everything else first
    for item in task_list:
        if "meta" in item.keys():
            log.debug("task item '{}' has 'meta' key, determining this is a 'freckles' task list".format(item["meta"].get("name", item)))
            return "freckles"
        for key  in item.keys():
            if key.isupper():
                log.debug("task item key '{}' is all uppercase, determining this is a 'freckles' task list".format(key))
                return "freckles"
    return None

def create_external_task_list_callback(external_task_list_map, tasks_callback_map):

    def copy_task_list_callback(ansible_environment_root):

        target_path = os.path.join(ansible_environment_root, "task_lists")
        os.makedirs(target_path)

        for name, details in external_task_list_map.items():
            source_name = details["filename"]
            source = details["source"]
            target_file = os.path.join(target_path, source_name)
            log.debug("Copying: {} -> {}".format(source, target_file))
            shutil.copyfile(source, target_file)

        for task_details in tasks_callback_map:
            task_list_format = task_details["tasks_format"]

            if task_list_format == "ansible":
                tasks_filename = task_details["target_name"]
                target_file = os.path.join(target_path, tasks_filename)
                tasks_string = task_details["tasks_string"]
                with open(target_file, 'w') as f:
                    f.write("{}\n".format(tasks_string))
                    # yaml.safe_dump(tasks, f, default_flow_style=False, allow_unicode=True, encoding="utf-8")

    callback = copy_task_list_callback

    return callback


def process_extra_task_lists(dictlet_metadata, dictlet_path):

    extra_task_lists = dictlet_metadata.get("__freckles__", {}).get("task_lists", [])
    if isinstance(extra_task_lists, string_types):
        extra_task_lists = [extra_task_lists]
    elif isinstance(extra_task_lists, dict):
        task_lists_temp = []
        for name, path in extra_task_lists.items():
            task_lists_temp.append({name: path})
        extra_task_lists = task_lists_temp
    dictlet_parent = os.path.dirname(dictlet_path)

    result_task_list = {}
    for task_list in extra_task_lists:
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
            raise Exception("Can't parse task list: {}".format(extra_task_lists))

    return result_task_list

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

def get_common_options(print_version_callback=print_version):
    """Returns a list of options that are shared between all of the freckles command-line applications.
    """

    defaults_option = click.Option(param_decls=["--vars", "-v"], required=False, multiple=True, help=VARS_HELP, type=vars_file, metavar="VARS")
    host_option = click.Option(param_decls=["--host"], required=False, multiple=True, help="host(s) to freckelize (defaults to 'localhost')", is_eager=False, type=HostType(), default=["localhost"])
    output_option = click.Option(param_decls=["--output", "-o"], required=False, default="default", show_default=True,
                                 metavar="FORMAT", type=click.Choice(SUPPORTED_OUTPUT_FORMATS),
                                 help="format of the output", is_eager=True)
    ask_become_pass_option = click.Option(param_decls=["--password", "-pw"],
                                          help='whether to force ask for a password, force ask not to, or let try freckles decide (which might not always work)',
                                           show_default=True, type=click.Choice(["no", "ask", "ansible"]), default="no")
    version_option = click.Option(param_decls=["--version"], help='prints the version of freckles', type=bool,
                                  is_flag=True, is_eager=True, expose_value=False, callback=print_version_callback)
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

            result = self.command.freckles_process(self.name, defaults, self.extra_vars, user_input, metadata, dictlet_details, config=self.command.get_config(), parent_params=self.parent_params, command_var_spec=c_vars)
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

    def __init__(self, config=None, extra_params=None, print_version_callback=print_version, **kwargs):

        super(FrecklesBaseCommand, self).__init__(**kwargs)
        self.print_version_callback = print_version_callback
        self.params[:0] = get_common_options(print_version_callback=self.print_version_callback)
        if extra_params:
            self.params[:0] = extra_params
        if config is None:
            self.config = DEFAULT_FRECKLES_CONFIG
        else:
            self.config = config
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
    def freckles_process(self, command_name, default_vars, extra_vars, user_input, metadata, dictlet_details, config, parent_params, command_var_spec):
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

        extra_defaults = ctx.params.get("vars", {})

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
