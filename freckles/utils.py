from __future__ import (absolute_import, division, print_function)

import copy
import json
import re
from collections import OrderedDict

import yaml
from jinja2 import Environment
from six import string_types

from frkl.frkl import Frkl, UrlAbbrevProcessor, dict_merge, EnsureUrlProcessor, EnsurePythonObjectProcessor, \
    LoadMoreConfigsProcessor
from nsbl import nsbl, ansible_extensions, inventory, output
from nsbl import tasks as nsbl_tasks
from nsbl import defaults as nsbl_defaults
from .config import FrecklesConfig

try:
    set
except NameError:
    from sets import Set as set

from .freckles_defaults import *
import logging

log = logging.getLogger("freckles")

# from: https://gist.github.com/miracle2k/3184458
def represent_odict(dump, tag, mapping, flow_style=None):
    """Like BaseRepresenter.represent_mapping, but does not issue the sort().
    """
    value = []
    node = yaml.MappingNode(tag, value, flow_style=flow_style)
    if dump.alias_key is not None:
        dump.represented_objects[dump.alias_key] = node
    best_style = True
    if hasattr(mapping, 'items'):
        mapping = mapping.items()
    for item_key, item_value in mapping:
        node_key = dump.represent_data(item_key)
        node_value = dump.represent_data(item_value)
        if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
            best_style = False
        if not (isinstance(node_value, yaml.ScalarNode) and not node_value.style):
            best_style = False
        value.append((node_key, node_value))
    if flow_style is None:
        if dump.default_flow_style is not None:
            node.flow_style = dump.default_flow_style
        else:
            node.flow_style = best_style
    return node

yaml.SafeDumper.add_representer(OrderedDict,
lambda dumper, value: represent_odict(dumper, u'tag:yaml.org,2002:map', value))

# def to_freckle_desc_filter(url, target, target_is_parent, profiles, include, exclude):


# class FrecklesUtilsExtension(Extension):
#     def __init__(self, environment):
#         super(Extension, self).__init__()
#         fm = FilterModule()
#         filters = fm.filters()
#         filters["to_freckle_desc"] = to_freckle_desc_filter
#         environment.filters.update(filters)

# freckles_jinja_utils = FrecklesUtilsExtension
# freckles_jinja_extensions = [freckles_jinja_utils, ansible_extensions.utils]
freckles_jinja_extensions = [ansible_extensions.utils]

DEFAULT_FRECKLES_CONFIG = FrecklesConfig()

class VarsType(click.ParamType):

    name = 'vars_type'

    def convert(self, value, param, ctx):

        chain = [
            UrlAbbrevProcessor(), EnsureUrlProcessor(), EnsurePythonObjectProcessor(), LoadMoreConfigsProcessor()]

        try:
            if not isinstance(value, (list, tuple)):
                value = [value]

            frkl_obj = Frkl(value, chain)
            result = frkl_obj.process()

            if isinstance(result[0], (list, tuple)):

                result_dict = {}
                for item in result[0]:
                    dict_merge(result_dict, item, copy_dct=False)

                return result_dict
            else:
                return result[0]

        except (Exception) as e:
            self.fail("Can't read vars '{}': {}".format(value, str(e)))


class VarsTypeJson(click.ParamType):
    name = 'vars_type_json'

    def convert(self, value, param, ctx):

        if os.path.exists(value):
            if not os.path.isfile(value):
                self.fail("Can't open file to read vars: {}".format(value))

            with open(value, 'r') as f:
                file_vars = yaml.safe_load(f)
                if not file_vars:
                    file_vars = {}

                return file_vars

        else:
            try:
                string_vars = json.loads(value)
                if not string_vars:
                    string_vars = {}
                return string_vars
            except (ValueError) as e:
                self.fail("Can't read vars: {}".format(value))


class RepoType(click.ParamType):
    name = 'repo'

    def convert(self, value, param, ctx):
        try:
            result = nsbl_tasks.expand_string_to_git_details(value, DEFAULT_ABBREVIATIONS)
            print_repos_expand(value, warn=True, default_local_path=False)
            return result
        except (Exception) as e:
            self.fail("{}: {}".format(value, e.message))


class HostType(click.ParamType):
    name = 'host_type'

    def convert(self, value, param, ctx):

        try:
            details = inventory.parse_host_string(value)
            return details
        except:
            self.fail('%s is not a valid host string' % value, param, ctx)


class FreckleUrlType(click.ParamType):
    name = 'repo'

    def convert(self, value, param, ctx):

        if not isinstance(value, string_types):
            raise Exception("freckle url needs to a string: {}".format(value))
        try:
            frkl_obj = Frkl(value, [
                UrlAbbrevProcessor(init_params={"abbrevs": DEFAULT_ABBREVIATIONS, "add_default_abbrevs": False, "verbose": True})])
            result = frkl_obj.process()
            return result[0]
        except:
            self.fail('%s is not a valid repo url' % value, param, ctx)


FRECKLES_REPO = RepoType()
FRECKLES_URL = FreckleUrlType()


def url_is_local(url):
    if url.startswith("~") or url.startswith(os.sep):
        return True
    return os.path.exists(os.path.expanduser(url))


# def create_freckle_desc(freckle_url, target, target_is_parent=True, profiles=[], includes=[], excludes=[]):
#     freckle_repo = {}

#     if isinstance(profiles, string_types):
#         profiles = [profiles]
#     if isinstance(includes, string_types):
#         includes = [includes]
#     if isinstance(excludes, string_types):
#         excludes = [excludes]

#     if not freckle_url:
#         if not target:
#             raise Exception("Need either url or target for freckle")
#         freckle_url = target
#         is_local = True
#     else:
#         is_local = url_is_local(freckle_url)

#     if is_local:
#         freckle_repo["path"] = os.path.abspath(os.path.expanduser(freckle_url))
#         freckle_repo["url"] = None
#     else:
#         repo = nsbl.ensure_git_repo_format(freckle_url, target, target_is_parent)
#         freckle_repo["path"] = repo["dest"]
#         freckle_repo["url"] = repo["repo"]

#     freckle_repo["profiles"] = profiles
#     freckle_repo["include"] = includes
#     freckle_repo["exclude"] = excludes

#     return freckle_repo


def replace_string(template_string, replacement_dict):

    use_environment_vars = True
    if use_environment_vars:
        sub_dict = copy.deepcopy({"LOCAL_ENV": os.environ})
        dict_merge(sub_dict, replacement_dict, copy_dct=False)
    else:
        sub_dict = replacement_dict

    trim_blocks = True
    block_start_string = '{%::'
    block_end_string = '::%}'
    variable_start_string = '{{::'
    variable_end_string = '::}}'

    result = Environment(extensions=[freckles_jinja_utils, ansible_extensions.utils], trim_blocks=trim_blocks, block_start_string=block_start_string, block_end_string=block_end_string, variable_start_string=variable_start_string, variable_end_string=variable_end_string).from_string(template_string).render(sub_dict)

    return result

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


# def find_supported_blueprints(config=None):

#     if not config:
#         config = DEFAULT_FRECKLES_CONFIG

#     trusted_repos = config.trusted_repos
#     repos = nsbl_tasks.get_local_repos(trusted_repos, "blueprints", DEFAULT_LOCAL_REPO_PATH_BASE, DEFAULT_REPOS, DEFAULT_ABBREVIATIONS)

#     result = {}
#     for r in repos:
#         p = get_blueprints_from_repo(r)
#         result.update(p)
#     return result


# def create_cli_command(config, command_name=None, command_path=None, extra_options={}):
#     doc = config.get("doc", {})
#     # TODO: check format of config
#     options = config.get("args", {})
#     vars = config.get("vars", {})
#     tasks = config.get("tasks", None)
#     default_vars = config.get("defaults", {})

#     key_map = {}
#     argument_key = None

#     options_list = []
#     args_that_are_vars = []
#     value_vars = []  # vars where we add all values seperately to the 'vars' instead of as a single value

#     options_all = copy.deepcopy(extra_options)
#     options_all.update(options)

#     for opt, opt_details in options_all.items():

#         opt_type = opt_details.get("type", None)
#         if isinstance(opt_type, string_types):
#             opt_type_converted = locate(opt_type)
#             if not opt_type_converted:
#                 raise Exception("No type found for: {}".format(opt_type))
#             if issubclass(opt_type_converted, click.ParamType):
#                 opt_details['type'] = opt_type_converted()
#             else:
#                 opt_details['type'] = opt_type_converted

#         key = opt_details.pop('arg_name', opt)
#         extra_arg_names = opt_details.pop('extra_arg_names', [])
#         if isinstance(extra_arg_names, string_types):
#             extra_arg_names = [extra_arg_names]
#         key_map[key] = opt

#         is_var = opt_details.pop('is_var', True)
#         if is_var:
#             args_that_are_vars.append(key)

#         use_value = opt_details.pop('use_value', False)
#         if use_value:
#             value_vars.append(key)

#         # cli arguments
#         is_argument = opt_details.pop('is_argument', False)
#         if is_argument:
#             if argument_key:
#                 raise Exception("Multiple arguments are not supported (yet): {}".format(config["vars"]))
#             argument_key = key
#             required = opt_details.pop("required", None)

#             o = click.Argument(param_decls=[key], required=required, **opt_details)
#         else:

#             arg_names_for_option = ["--{}".format(key)] + extra_arg_names
#             o = click.Option(param_decls=arg_names_for_option, **opt_details)
#         options_list.append(o)

#     return {"options": options_list, "key_map": key_map, "command_path": command_path, "tasks": tasks, "vars": vars,
#             "default_vars": default_vars, "doc": doc, "args_that_are_vars": args_that_are_vars,
#             "value_vars": value_vars,
#             "metadata": {"extra_options": extra_options, "command_path": command_path, "command_name": command_name,
#                          "config": config}}


# def get_vars_from_cli_input(input_args, key_map, task_vars, default_vars, args_that_are_vars, value_vars):
#     # exchange arg_name with var name
#     new_args = {}

#     for key, value in key_map.items():
#         temp = input_args.pop(key.replace('-', '_'))
#         if key not in args_that_are_vars:
#             if isinstance(temp, tuple):
#                 temp = list(temp)
#             new_args[value] = temp
#         else:
#             task_vars[value] = temp

#         # replace all matching strings in value_vars
#         for i, var_name in enumerate(value_vars):
#             if var_name == key:
#                 value_vars[i] = value

#     # now overimpose the new_args over template_vars
#     new_args = dict_merge(default_vars, new_args)

#     final_vars = {}
#     sub_dict = copy.deepcopy(new_args)

#     # inject subdict (args and envs) in vars
#     for key, template in task_vars.items():
#         if isinstance(template, string_types):
#             template_var_string = replace_string(template, sub_dict)
#             if template_var_string.startswith('{') and not \
#                template_var_string.startswith('{{') and not \
#                template_var_string.startswith('{%'):
#                 # if template_var_string is json, load value
#                 # (but do not handle {{ ansible-side substitution)
#                 try:
#                     template_var_new = yaml.safe_load(template_var_string)
#                     final_vars[key] = template_var_new
#                 except (Exception) as e:
#                     raise Exception("Could not convert template '{}': {}".format(template_var_string, e.message))
#             else:
#                 # else push value
#                 final_vars[key] = template_var_string
#         else:
#             final_vars[key] = template

#     new_vars = {}

#     for key in value_vars:

#         values = final_vars.pop(key, {})

#         if values and not isinstance(values, dict):
#             raise Exception("value for '{}' not a dict: {}".format(key, values))
#         if values:
#             dict_merge(new_vars, values, copy_dct=False)

#     dict_merge(new_vars, final_vars, copy_dct=False)

#     return new_args, new_vars


def download_repos(repos_to_download, config, output_value):

    expanded_download = expand_repos(repos_to_download)
    expanded_trusted = expand_repos(config.trusted_urls)

    no_url = True
    for ex_rep in expanded_download:
        url = ex_rep.get("url", None)
        if not url:
            continue
        no_url = False
        trusted = False
        for ex_trust in expanded_trusted:
            url_trust = ex_trust.get("url", None)
            url_trust_temp = re.sub('//+', '/', url_trust)
            if url_trust_temp.count('/') < 3:
                log.debug("Ignoring trusted url '{}': not long enough, needs at least")
                continue
            if not url_trust:
                continue
            if url.startswith(url_trust):
                trusted = True
                break
        if not trusted:
            raise Exception("Context repository not trusted: '{}'. Check XXX for details.".format(url))

    repos = []
    for repo in repos_to_download:
        if os.path.exists(repo):
            temp = os.path.abspath(repo)
            repos.append(temp)
        else:
            repos.append(repo)

    print_repos_expand(repos, repo_source="using runtime context repo(s)", warn=False)

    config.add_repo(repos)

    if no_url:
        return repos

    output.print_title("processing extra repos...")

    task_config = [{'tasks':
                    [{'freckles-io.freckles-config': {
                        'freckles_extra_repos': repos,
                        'freckles_config_update_repos': True,
                        'freckles_checkout_config_file_repos': False
                    }
                    }]
    }]


    create_and_run_nsbl_runner(task_config, task_metadata={}, output_format=output_value, ask_become_pass=False)

    return repos

def download_extra_repos(ctx, param, value):

    output = ctx.find_root().params.get("output", "default")

    if not value:
        return []
    # repos = list(value)

    if hasattr(ctx.find_root().command, "config"):
        config = ctx.find_root().command.config
    elif hasattr(ctx.find_root(), "obj"):
        config = ctx.find_root().obj["config"]

    result = download_repos(value, config, output)
    return result


def execute_run_box_basics(output="default", ask_become_pass=None, password=None):

    if os.path.exists(DEFAULT_LOCAL_FRECKLES_BOX_BASICS_MARKER):
        return {"return_code": -1}

    task_config = [{'tasks':
                    ['freckles-io.box-basics']
    }]

    if password is not None:
        ask_become_pass = False
    else:
        if not ask_become_pass:
            log.debug("Changing ask_become_pass for box basics to: True")
            ask_become_pass = True

    result = create_and_run_nsbl_runner(task_config, task_metadata={}, output_format=output, ask_become_pass=ask_become_pass, password=password, run_box_basics=False)

    if result["return_code"] == 0:
        with open(DEFAULT_LOCAL_FRECKLES_BOX_BASICS_MARKER, 'a'):
            os.utime(DEFAULT_LOCAL_FRECKLES_BOX_BASICS_MARKER, None)


    return result


def print_repos_expand(repos, repo_source=None, verbose=True, warn=False, default_local_path=True):
    """Expands repo urls.
    """

    expanded = expanded_repos_dict(repos)

    exp = False

    if not expanded:
        return

    click.echo("")

    if repo_source:
        output.print_title("{}:".format(repo_source), title_char="-")
    else:
        output.print_title("using freckle repo/folder(s):", title_char="-")

    click.echo("")

    for r, value in expanded.items():
        click.echo(" - {}".format(r))
        for v in value:

            if v["url"]:
                if r != v["url"]:
                    exp = True
                    click.echo("     -> remote: '{}'".format(v["url"]))
            if v["path"] and default_local_path:
                if r != v["path"]:
                    exp = True
                    click.echo("     -> local: '{}'".format(v["path"]))
        click.echo()

    if warn and exp:
        click.echo(" * NOTE: don't rely on abbreviated urls for anything important as that feature might change in a future release, use full urls if in doubt\n")

def expanded_repos_dict(repos, alias_dict=DEFAULT_ROLE_REPOS):

    if isinstance(repos, string_types):
        repos = [repos]

    result = {}
    for p in repos:
        expanded = expand_repos(p)
        if p not in alias_dict.keys() and p != expanded[0]:
            result[p] = expanded

    return result

def expand_repos(repos, alias_dict=DEFAULT_ROLE_REPOS):
    """Expands a list of stings to a list of tuples (repo_url, repo_path).
    """

    if isinstance(repos, string_types):
        repos = [repos]

    result = []
    for repo in repos:
        fields = ["url", "path"]

        r = alias_dict.get(repo, None)
        if not r:
            if os.path.exists(repo):
                temp = {"url": None, "path": repo}
            else:
                repo_details = nsbl_tasks.expand_string_to_git_details(repo, DEFAULT_ABBREVIATIONS)
                repo_url = repo_details["url"]
                repo_branch = repo_details.get("branch", None)
                relative_repo_path = nsbl_tasks.calculate_local_repo_path(repo_url, repo_branch)
                repo_path = os.path.join(DEFAULT_LOCAL_REPO_PATH_BASE, relative_repo_path)
                # temp = {"url": repo_url, "path": repo_path}
                repo_details["path"] = repo_path
                temp = repo_details
            result.append(temp)
        else:
            result.append(r)

    return result


# def find_supported_profile_names(config=None, additional_context_repos=[]):
    # return sorted(list(set(find_supported_profiles(config, additional_context_repos).keys())))


# def get_all_adapters_in_repos(repos):

#     result = []
#     repos = nsbl_tasks.get_local_repos(repos, "adapters", DEFAULT_LOCAL_REPO_PATH_BASE, DEFAULT_REPOS, DEFAULT_ABBREVIATIONS)
#     for repo in repos:
#         adapters = get_adapters_from_repo(repo)
#         result.extend(adapters)

#     return result


# def extract_all_used_profiles(freckle_repos):
#     all_profiles = []
#     for fr in freckle_repos:
#         all_profiles.extend(fr.get("profiles", []))

#     return list(set(all_profiles))


def create_and_run_nsbl_runner(task_config, task_metadata={}, output_format="default", ask_become_pass=False, password=None,
                               pre_run_callback=None, no_run=False, additional_roles=[], config=None, run_box_basics=False, additional_repo_paths=[], hosts_list=["localhost"]):

    if run_box_basics:
        result = execute_run_box_basics(output_format, ask_become_pass, password)

        if result["return_code"] > 0:
            return result

    if not config:
        config = DEFAULT_FRECKLES_CONFIG

    if additional_repo_paths:
        if config.use_freckle_as_repo:
            config.add_repo(additional_repo_paths)

    config_trusted_repos = config.trusted_repos

    local_role_repos = []
    for repo_name in config_trusted_repos:

        repo = DEFAULT_ROLE_REPOS.get(repo_name)
        if not repo:
            if not os.path.exists(repo_name):
                repo_details = nsbl_tasks.expand_string_to_git_details(repo_name, DEFAULT_ABBREVIATIONS)
                repo_url = repo_details["url"]
                repo_branch = repo_details.get('branch', None)
                relative_repo_path = nsbl_tasks.calculate_local_repo_path(repo_url, repo_branch)
                repo_path = os.path.join(DEFAULT_LOCAL_REPO_PATH_BASE, relative_repo_path)
            else:
                local_role_repos.append(repo_name)
        else:
            repo_path = repo["path"]
            local_role_repos.append(repo_path)

    role_repos = nsbl_defaults.calculate_role_repos(local_role_repos)
    task_descs = config.task_descs

    global_vars = {}
    for tc in task_config:
        v = tc.get("vars", {})
        if v:
            dict_merge(global_vars, v, copy_dct=False)

    nsbl_obj = nsbl.Nsbl.create(task_config, role_repos, task_descs, wrap_into_hosts=hosts_list, pre_chain=[],
                                additional_roles=additional_roles)

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
    elif output_format == "yaml":
        stdout_callback = "yaml"
    else:
        raise Exception("Invalid output format: {}".format(output_format))

    force = True

    extra_paths = "$HOME/.local/share/inaugurate/virtualenvs/freckles/bin:$HOME/.local/share/inaugurate/conda/envs/freckles/bin"
    return runner.run(run_target, global_vars=global_vars, force=force, ansible_verbose=ansible_verbose, ask_become_pass=ask_become_pass, password=password,
                      extra_plugins=EXTRA_FRECKLES_PLUGINS, callback=stdout_callback, add_timestamp_to_env=True,
                      add_symlink_to_env=DEFAULT_RUN_SYMLINK_LOCATION, no_run=no_run,
                      display_sub_tasks=display_sub_tasks, display_skipped_tasks=display_skipped_tasks,
                      display_ignore_tasks=ignore_task_strings, pre_run_callback=pre_run_callback, extra_paths=extra_paths)
