# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy
import logging
import os
from collections import OrderedDict

from ruamel.yaml import YAML, CommentToken

from freckles.adapters import FrecklesAdapter
from freckles.defaults import (
    EXTERNAL_FOLDER as FRECKLES_EXTERNAL_FOLDER,
    FRECKLETS_KEY,
    FRECKLES_CLICK_CEREBUS_ARG_MAP,
    FRECKLET_KEY_NAME)
from freckles.defaults import TASK_KEY_NAME
from freckles.exceptions import FrecklesConfigException
from freckles.repo_management import MIXED_CONTENT_TYPE
from frutils import dict_merge
from frutils import is_sequence
from frutils.parameters import get_type_string_for_class
from luci.luitem_index import LuItemFolderIndex, LuItemIndex
from luci.readers import add_luitem_reader_profile
from nsbl.defaults import (
    ADD_TYPE_CALLBACK,
    ADD_TYPE_ACTION,
    ADD_TYPE_LIBRARY,
    ADD_TYPE_FILTER,
    ADD_TYPE_FILES,
    ADD_TYPE_TASK_LIST_FILE,
    DEFAULT_INCLUDE_TYPE,
)
from nsbl.nsbl import create_single_host_nsbl_env_from_tasklist
from nsbl.nsbl_tasklist import NsblContext
from nsbl.role_utils import find_roles_in_repo
from nsbl.runner import NsblRunner
from nsbl.tasklist_utils import get_tasklist_format
from .defaults import (
    NSBL_EXTRA_PLUGINS,
    NSBL_EXTRA_CALLBACKS,
    NSBL_DEFAULT_REPO_ALIASES,
    NSBL_DEFAULT_READER_PROFILE,
    NSBL_CONFIG_SCHEMA,
    NSBL_RUN_CONTROL_SCHEMA,
    NSBL_INTERNAL_TASKLIST_REPO,
)
from .nsbl_freckles_callback import NsblFrecklesCallbackAdapter

yaml = YAML(typ="rt")

log = logging.getLogger("freckles")

add_luitem_reader_profile("nsbl", NSBL_DEFAULT_READER_PROFILE)

DEFAULT_ADDITIONAL_FILES = [
    {
        "path": os.path.join(FRECKLES_EXTERNAL_FOLDER, "scripts", "freckles_facts.sh"),
        "type": ADD_TYPE_FILES,
    },
    {
        "path": os.path.join(FRECKLES_EXTERNAL_FOLDER, "scripts", "freckle_folders.sh"),
        "type": ADD_TYPE_FILES,
    },
    {
        "path": os.path.join(NSBL_EXTRA_CALLBACKS, "default_to_file.py"),
        "type": ADD_TYPE_CALLBACK,
    },
    {
        "path": os.path.join(NSBL_EXTRA_CALLBACKS, "freckles_callback.py"),
        "type": ADD_TYPE_CALLBACK,
    },
    {
        "path": os.path.join(NSBL_EXTRA_PLUGINS, "action_plugins", "install.py"),
        "type": ADD_TYPE_ACTION,
    },
    {
        "path": os.path.join(NSBL_EXTRA_PLUGINS, "library", "install.py"),
        "type": ADD_TYPE_LIBRARY,
    },
    {
        "path": os.path.join(NSBL_EXTRA_PLUGINS, "library", "stow.py"),
        "type": ADD_TYPE_LIBRARY,
    },
    {
        "path": os.path.join(NSBL_EXTRA_PLUGINS, "library", "vagrant_plugin.py"),
        "type": ADD_TYPE_LIBRARY,
    },
    {
        "path": os.path.join(
            NSBL_EXTRA_PLUGINS, "action_plugins", "frecklet_result.py"
        ),
        "type": ADD_TYPE_ACTION,
    },
    {
        "path": os.path.join(NSBL_EXTRA_PLUGINS, "library", "frecklet_result.py"),
        "type": ADD_TYPE_LIBRARY,
    },
    {
        "path": os.path.join(
            NSBL_EXTRA_PLUGINS, "action_plugins", "set_platform_fact.py"
        ),
        "type": ADD_TYPE_ACTION,
    },
    {
        "path": os.path.join(NSBL_EXTRA_PLUGINS, "library", "set_platform_fact.py"),
        "type": ADD_TYPE_LIBRARY,
    },
    {
        "path": os.path.join(NSBL_EXTRA_PLUGINS, "library", "freckles_facts.py"),
        "type": ADD_TYPE_LIBRARY,
    },
    {
        "path": os.path.join(NSBL_EXTRA_PLUGINS, "action_plugins", "freckles_facts.py"),
        "type": ADD_TYPE_ACTION,
    },
    {
        "path": os.path.join(NSBL_EXTRA_PLUGINS, "library", "conda.py"),
        "type": ADD_TYPE_LIBRARY,
    },
    {
        "path": os.path.join(NSBL_EXTRA_PLUGINS, "library", "nix.py"),
        "type": ADD_TYPE_LIBRARY,
    },
    {
        "path": os.path.join(NSBL_EXTRA_PLUGINS, "library", "asdf.py"),
        "type": ADD_TYPE_LIBRARY,
    },
    # {
    #     "path": os.path.join(NSBL_EXTRA_PLUGINS, "module_utils", "freckles_utils.py"),
    #     "type": ADD_TYPE_MODULE_UTIL,
    # },
    # {
    #     "path": os.path.join(NSBL_ROLES, "package-management", "freckfrackery.install"),
    #     "type": ADD_TYPE_ROLE,
    # },
    # {
    #     "path": os.path.join(NSBL_ROLES, "package-management", "freckfrackery.install-pkg-mgrs"),
    #     "type": ADD_TYPE_ROLE,
    # },
    {
        "path": os.path.join(
            NSBL_EXTRA_PLUGINS, "filter_plugins", "freckles_filters.py"
        ),
        "type": ADD_TYPE_FILTER,
    },
    {
        "path": os.path.join(NSBL_INTERNAL_TASKLIST_REPO, "box_basics.yml"),
        "type": ADD_TYPE_TASK_LIST_FILE,
    },
    {
        "path": os.path.join(NSBL_INTERNAL_TASKLIST_REPO, "box_basics_root.yml"),
        "type": ADD_TYPE_TASK_LIST_FILE,
    },
    {
        "path": os.path.join(NSBL_INTERNAL_TASKLIST_REPO, "freckles_basic_facts.yml"),
        "type": ADD_TYPE_TASK_LIST_FILE,
    },
]


def generate_additional_files_dict():

    additional_files = {}

    for f in DEFAULT_ADDITIONAL_FILES:

        path = f["path"]
        if not os.path.exists(path):
            raise FrecklesConfigException("File '{}' not available".format(path))

        f_type = f["type"]
        target_name = f.get("target_name", os.path.basename(path))

        additional_files[path] = {"type": f_type, "target_name": target_name}

        license_path = path + ".license"
        if os.path.exists(license_path):
            target_name_license = target_name + ".license"
            additional_files[license_path] = {
                "type": f["type"],
                "target_name": target_name_license,
            }

    return additional_files


def generate_pre_tasks(
    minimal_facts=True, box_basics=True, box_basics_non_sudo=False, freckles_facts=True
):
    """Generates a list of tasks that will end up in a playbooks pre_tasks variable.

    Args:
        minimal_facts (bool): whether to run a basic shell script to gather some basic facts (this doesn't require Python on the target machine, but can find out whether Python is available.
        box_basics (bool): whether to install a minimal set to be able to run common Ansible modules on this machine
        box_basics_non_sudo (bool): whether to run the 'non-sudo' version of box basics (not implemented yet)
        freckles_facts (bool): whether to run the freckles facts module

    Returns:
        tuple: a tuple in the form: (task_list, gather_facts_included), gather_facts_included indicates whether the pre_tasks will run gather_facts at some stage (so it doesn't need to be executed twice.
    """

    gather_facts_included = False
    pre_tasks = []

    # check_script_location = os.path.join(
    #     "{{ playbook_dir }}", "..", "files", "freckles_facts.sh"
    # )

    # TODO: this doesn't really do anything at the moment, vars are hardcoded in freckles_facts.sh
    check_executables = [
        "cat",
        "wget",
        "curl",
        "python",
        "python2",
        "python2.7",
        "python3",
        "python3.6",
        "vagrant",
        "pip",
        "conda",
        "nix",
        "asdf",
        "rsync",
    ]
    check_python_modules = ["zipfile"]
    pre_path = []
    post_path = []
    check_freckle_files = []
    check_directories = []
    freckles_facts_environment = (
        {
            "FRECKLES_CHECK_EXECUTABLES": ":".join(check_executables),
            "FRECKLES_CHECK_DIRECTORIES": ":".join(check_directories),
            "FRECKLES_PRE_PATH": ":".join(pre_path),
            "FRECKLES_POST_PATH": ":".join(post_path),
            "FRECKLES_CHECK_FRECKLE_FILES": ":".join(check_freckle_files),
            "FRECKLES_CHECK_PYTHON_MODULES": ":".join(check_python_modules),
        },
    )

    if minimal_facts or box_basics:
        temp = [
            {
                "name": "[-1000][testing connectivity]",
                "raw": 'sh -c "true"',
                "ignore_errors": False,
            },
            {
                "name": "[-1000][checking whether box already prepared]",
                "raw": 'sh -c "test -e $HOME/.local/share/nsbl/.nsbl_box_basics_root_done && echo 1 || echo 0"',
                "ignore_errors": True,
                "register": "box_basics_exists",
            },
            {
                "name": "[setting box_basics var]",
                "set_fact": {
                    "box_basics": "{{ box_basics_exists.stdout_lines[0] | bool }}",
                    "freckles_environment": freckles_facts_environment,
                },
            },
            {
                "name": "[getting box basic facts]",
                "include_tasks": "{{ playbook_dir }}/../task_lists/freckles_basic_facts.yml",
            },
        ]
        pre_tasks.extend(temp)

    if box_basics:

        gather_facts_included = True
        temp = [
            {
                "name": "[preparing box basics]",
                "include_tasks": "{{ playbook_dir }}/../task_lists/box_basics_root.yml",
                "when": "not box_basics",
            },
            {
                "name": "[gathering facts]",
                "setup": {},
                "tags": "always",
                "when": "box_basics",
            },
        ]
        pre_tasks.extend(temp)

    if freckles_facts:

        pre_tasks.append(
            {
                "name": "[gathering freckles-specific facts]",
                "freckles_facts": {"executables": ["unzip"]},
            }
        )

    return {"pre_tasks": pre_tasks, "gather_facts": not gather_facts_included}


class NsblRolesIndex(LuItemIndex):
    def __init__(self, url, guess_args_for_roles=True):

        super(NsblRolesIndex, self).__init__(url=url, item_type="frecklet")
        self.roles = find_roles_in_repo(url)
        self.guess_args_for_roles = guess_args_for_roles

        self.role_cache = {}

    def get_available_packages(self):

        # TODO: uppercase
        return self.roles.keys()

    def get_pkg_metadata(self, name):

        if name not in self.roles.keys():
            return None

        if name in self.role_cache:
            return self.role_cache[name]

        metadata_file = os.path.join(self.roles[name], "meta", "main.yml")
        defaults_file = os.path.join(self.roles[name], "defaults", "main.yml")

        with open(metadata_file) as f:
            role_metadata = yaml.load(f)

        if not os.path.exists(defaults_file) or not os.path.isfile(
            os.path.realpath(defaults_file)
        ):
            role_defaults = {}

        galaxy_info = role_metadata.get("galaxy_info", {})
        description = galaxy_info.get("description", "n/a")
        if description != "n/a":
            desc = description
        else:
            desc = name
        # license = galaxy_info.get("license", "n/a")
        # platforms = galaxy_info.get("platforms", [])
        # dependencies = galaxy_info.get("dependencies", [])

        if self.guess_args_for_roles:
            with open(defaults_file) as f:
                role_defaults = yaml.load(f)
            args = OrderedDict()

            if role_defaults is None:
                role_defaults = {}

            for key, value in role_defaults.items():

                short_help = role_defaults.ca.items.get(key, None)
                short_help_string = "n/a"
                if short_help is not None:
                    for item in short_help:
                        if isinstance(item, CommentToken):
                            short_help_string = item.value.strip()[1:].strip()
                            break

                # if not value:
                #     args[key] = {"__doc__": {"short_help": short_help_string}, "required": False}
                # else:

                args[key] = {
                    "doc": {"short_help": short_help_string},
                    "required": False,
                    "empty": True,
                    "cli": {"show_default": True},
                }
                if is_sequence(value):
                    arg_type = "list"
                else:
                    arg_type = get_type_string_for_class(
                        value.__class__, None, type_map=FRECKLES_CLICK_CEREBUS_ARG_MAP
                    )
                if value:
                    args[key]["default"] = value
                if arg_type is not None:
                    args[key]["type"] = arg_type

        else:
            args = None

        result = {
            "doc": {"short_help": description},
            FRECKLETS_KEY: [{
                TASK_KEY_NAME: {
                    "command": name,
                    "role_path": self.roles[name],
                },
                FRECKLET_KEY_NAME: {
                    "type": "ansible-role",
                    "name": desc,
                }
            }],
        }
        if args:
            result["args"] = args

        self.role_cache[name] = result

        return result


class NsblTasklistIndex(LuItemIndex):
    def __init__(self, url, convert_ansible_template_markers_to_freckles=False):

        self.wrapped = LuItemFolderIndex(
            url=url,
            pkg_base_url=url,
            item_type="frecklet",
            reader_params={"reader_profile": "nsbl"},
        )
        self.convert_ansible_template_markers_to_freckles = (
            convert_ansible_template_markers_to_freckles
        )

    def get_name(self):

        return self.wrapped.name

    def update_index(self):

        return self.wrapped.update_index()

    def get_available_packages(self):

        # TODO: upper-case
        return self.wrapped.get_available_packages()

    def get_pkg_metadata(self, name):

        # TODO: upper-case

        md = self.wrapped.get_pkg_metadata(name)
        if md is None:
            return None

        # TODO: check whether ansible tasklist in the first place
        frecklets = md.get(FRECKLETS_KEY, None)
        if not frecklets:
            return None

        tasklist_format = get_tasklist_format(md[FRECKLETS_KEY])

        if tasklist_format == "freckles":
            raise Exception("'freckles' tasklist format not supported yet.")
            # return md
        elif tasklist_format == "ansible":
            if self.convert_ansible_template_markers_to_freckles:
                raise NotImplementedError(
                    "Converting ansible template markers not implemented yet."
                )

            # importing a tasklist doesn't work very well currently without workaround,
            # of including an extra task, as the task_id var can't be accessed
            result = {
                "name": name,
                "command": name,
                "include-type": DEFAULT_INCLUDE_TYPE,
                "type": "ansible-tasklist",
                "tasklist": md[FRECKLETS_KEY],
                "tasklist_var": "ansible_tasklist_{}".format(name),
            }
            # converted = convert_ansible_tasklist(
            #     name,
            #     md[FRECKLETS_KEY],
            #     import_type="include",
            #     convert_ansible_template_markers_to_freckles=self.convert_ansible_template_markers_to_freckles,
            # )
            md[FRECKLETS_KEY] = [{TASK_KEY_NAME: result}]

            return md

        else:
            log.warn(
                "Can't determine ansible tasklist format for sure, assuming 'freckles'..."
            )
            return md


class FrecklesAdapterNsbl(FrecklesAdapter):
    def __init__(self, adapter_name="nsbl"):
        super(FrecklesAdapterNsbl, self).__init__(adapter_name=adapter_name)

        self.nsbl_context = None

    def get_nsbl_context(self):
        """Calculate the context from the available repositories and config."""

        if self.nsbl_context is None:
            role_repos = [
                r["path"]
                for r in self.content_repos
                if r["content_type"] == "roles"
                or r["content_type"] == MIXED_CONTENT_TYPE
            ]
            tasklist_repos = [
                r["path"]
                for r in self.content_repos
                if r["content_type"] == "ansible-tasklists"
                or r["content_type"] == MIXED_CONTENT_TYPE
            ]

            urls = {"roles": role_repos, "tasklists": tasklist_repos}
            allow_remote = self.get_cnf_value("allow_remote")
            allow_remote_roles = self.get_cnf_value("allow_remote_roles")
            allow_remote_tasklists = self.get_cnf_value("allow_remote_tasklists")

            if allow_remote_roles is None:
                allow_remote_roles = allow_remote
            if allow_remote_tasklists is None:
                allow_remote_tasklists = allow_remote

            self.nsbl_context = NsblContext(
                urls=urls,
                allow_external_roles=allow_remote_roles,
                allow_external_tasklists=allow_remote_tasklists,
            )

        return self.nsbl_context

    def content_repos_updated(self):

        self.nsbl_context = None

    def get_repo_aliases(self):

        return NSBL_DEFAULT_REPO_ALIASES

    def get_indexes(self):

        result = []

        guess_args = self.get_cnf_value("guess_args_for_roles")
        generate_role_frecklets = self.get_cnf_value("generate_role_frecklets")
        generate_tasklist_frecklets = self.get_cnf_value("generate_tasklist_frecklets")

        if generate_role_frecklets:
            log.debug("Adding dynamic role frecklets.")
            role_paths = self.get_nsbl_context().role_repo_paths

            for role_repo in role_paths:
                index = NsblRolesIndex(role_repo, guess_args_for_roles=guess_args)
                result.append(index)

        else:
            log.debug("Dyanmic frecklets not allowed, not adding role frecklets.")

        if generate_tasklist_frecklets:
            convert_template_markers = self.cnf_interpreter.get_cnf_value(
                "convert_ansible_template_markers"
            )
            log.debug("Adding dynamic tasklist frecklets.")
            tasklist_paths = self.get_nsbl_context().tasklist_paths
            for tasklist_repo in tasklist_paths:
                index = NsblTasklistIndex(
                    url=tasklist_repo,
                    convert_ansible_template_markers_to_freckles=convert_template_markers,
                )
                result.append(index)
        else:
            log.debug("Dynamic frecklets not allowed, not adding tasklist frecklets.")

        return result

    def get_cnf_schema(self):

        return NSBL_CONFIG_SCHEMA

    def get_run_config_schema(self):

        return NSBL_RUN_CONTROL_SCHEMA

    def get_frecklet_metadata(self, name):

        if name.isupper():
            return {
                FRECKLETS_KEY: [
                    {
                        TASK_KEY_NAME: {
                            "command": name.lower(),
                            "become": True,
                        },
                        FRECKLET_KEY_NAME: {
                            "name": name,
                            "type": "ansible-module",
                        }
                    }
                ]
            }
        else:
            return {
                FRECKLETS_KEY: [
                    {
                        TASK_KEY_NAME: {
                            "command": name,
                        },
                        FRECKLET_KEY_NAME: {
                            "type": "ansible-module",
                            "name": name,
                        }
                    }
                ]
            }

    def get_supported_task_types(self):

        return ["ansible-module", "ansible-role", "ansible-tasklist"]

    def get_supported_repo_content_types(self):

        return ["roles", "ansible-tasklists"]

    def run(
        self,
        tasklist,
        context_config=None,
        run_config=None,
        run_vars=None,
        passwords=None,
        result_callback=None,
        output_callback=None,
        parent_task=None,
    ):

        if context_config is None:
            raise Exception("No context config provided")

        if run_config is None:
            raise Exception("No run config provided")

        if parent_task is None:
            raise Exception("No parent task provided")

        final_config = copy.deepcopy(context_config.get_validated_cnf())

        ask_become_pass = run_config.get_cnf_value("elevated_permissions_required")
        if ask_become_pass is None:
            log.debug("Autodetecting whether elevated permissions are required...")
            for task in tasklist:
                become = task[TASK_KEY_NAME].get("become", False)
                e = task[FRECKLET_KEY_NAME].get("elevated", False)
                if become is not False or e is not False:
                    ask_become_pass = True
                    break

            if ask_become_pass is None:
                ask_become_pass = False

            log.debug("Detected 'ask-become-pass': {}".format(ask_become_pass))
            final_config["elevated_permissions_required"] = ask_become_pass

        dict_merge(final_config, run_config.get_validated_cnf(), copy_dct=False)
        log.debug("Final run config: {}".format(final_config))

        if run_config.get_cnf_value("minimal_facts_only", False):
            pre_tasks = generate_pre_tasks(
                minimal_facts=True,
                box_basics=False,
                box_basics_non_sudo=False,
                freckles_facts=False,
            )
        else:
            pre_tasks = generate_pre_tasks(
                minimal_facts=True,
                box_basics=True,
                box_basics_non_sudo=False,
                freckles_facts=True,
            )
        additional_files = generate_additional_files_dict()

        nsbl_env = create_single_host_nsbl_env_from_tasklist(
            tasklist,
            self.get_nsbl_context(),
            pre_tasks=pre_tasks["pre_tasks"],
            gather_facts=pre_tasks["gather_facts"],
            additional_files=additional_files,
            task_marker="task",
            meta_marker="frecklet",
            **final_config
        )

        if output_callback is not None:
            callback_adapter = NsblFrecklesCallbackAdapter(
                nsbl_env,
                parent_task=parent_task,
                result_callback=result_callback,
                output_callback=output_callback,
            )
            final_config["callback"] = "freckles_callback"
        else:

            if result_callback is not None:
                result_callback.add_result(
                    {
                        "WARNING": "No results are recorded because a non-freckles callback was used. Don't use the '-o backend[:XXX]' argument if you need results in this run."
                    }
                )

            output_name = run_config.get_cnf_value("output")
            if ":" in output_name:
                callback_name, ansible_callback_name = output_name.split(":")
            else:
                callback_name = output_name
                ansible_callback_name = "default"

            if not callback_name == "backend":
                raise Exception("Invalid callback: {}".format(callback_name))

            warn = True
            callback_adapter = None
            if ansible_callback_name == "verbose":
                final_config["callback"] = "default"
                final_config["ansible_args"] = (
                    final_config.get("ansible_args", "") + " -vvvv "
                )
            else:
                if ansible_callback_name == "freckles_callback":
                    warn = False

                final_config["callback"] = ansible_callback_name

            if warn:
                log.warning(
                    "Backend callback selected, this is good for debugging, but means that this run won't return any results."
                )
        sudo_password = None
        ssh_password = None

        if "sudo_pass" in run_vars.get("__freckles_run__", {}).keys():
            sudo_password = run_vars["__freckles_run__"]["sudo_pass"]
        if "ssh_pass" in run_vars.get("__freckles_run__", {}).keys():
            ssh_password = run_vars["__freckles_run__"]["ssh_pass"]

        extra_env_vars = {}
        if "pwd" in run_vars["__freckles_run__"].keys():
            extra_env_vars["NSBL_RUN_PWD"] = run_vars["__freckles_run__"]["pwd"]

        nsbl_runner = NsblRunner(nsbl_env)

        result = nsbl_runner.run(
            callback_adapter=callback_adapter,
            sudo_password=sudo_password,
            ssh_password=ssh_password,
            extra_env_vars=extra_env_vars,
            secure_vars=passwords,
            **final_config
        )

        return result
