# -*- coding: utf-8 -*-
import copy
import os

from freckles.adapters import FrecklesAdapter
from freckles.adapters.shell.processors import ShellScriptProcessor
from freckles.adapters.shell.shell_runner import ShellRunner
from freckles.defaults import (
    DEFAULT_FRECKLES_JINJA_ENV,
    FRECKLETS_KEY,
    TASK_KEY_NAME,
    VARS_KEY,
    FRECKLET_KEY_NAME,
)
from frutils import dict_merge
from frutils.config import Cnf
from ting.tings import TingTings

SHELL_CONFIG_SCHEMA = {}
SHELL_RUN_CONFIG_SCHEMA = {
    "ssh_key": {
        "type": "string",
        "doc": {"short_help": "the path to a ssh key identity file"},
        # "target_key": "ansible_ssh_private_key_file",
    },
    "user": {
        "type": "string",
        "doc": {"short_help": "the user name to use for the connection"},
    },
    "connection_type": {
        "type": "string",
        "doc": {"short_help": "the connection type, probably 'ssh' or 'local'"},
        # "target_key": "ansible_connection",
    },
    "port": {
        "type": "integer",
        "default": 22,
        "doc": {"short_help": "the ssh port to connect to in case of a ssh connection"},
        "target_key": "ssh_port",
    },
    "host": {
        "type": "string",
        "doc": {"short_help": "the host to connect to"},
        "default": "localhost",
        # "target_key": "host"
    },
    "host_ip": {"type": "string", "doc": {"short_help": "the host ip, optional"}},
    "elevated": {
        "type": "boolean",
        "doc": {"short_help": "this run needs elevated permissions"},
        "target_key": "elevated_permissions_required",
    },
    "passwordless_sudo": {
        "type": "boolean",
        "target_key": "passwordless_sudo_possible",
        "doc": {
            "short_help": "the user can do passwordless sudo on the host where those tasks are run"
        },
    },
    "no_run": {
        "type": "boolean",
        "coerce": bool,
        "doc": {
            "short_help": "only create the Ansible environment, don't execute any playbooks"
        },
    },
}

SCRIPTLING_LOAD_CONFIG = {
    "class_name": "Scriptling",
    "attributes": [
        {
            "FrontmatterAndContentAttribute": {
                "metadata_name": "meta",
                "content_name": "scriptling_content",
                "source_attr_name": "ting_content",
                "metadata_strategies": ["comments"],
            }
        },
        {"FileStringContentAttribute": {"target_attr_name": "ting_content"}},
        # {
        #     "ArgsAttribute": {
        #         "source_attr_name": "meta",
        #         "target_attr_name": "args",
        #         "index_attr_name": "_meta_parent_repo",
        #         "default_arg": {
        #             "required": True,
        #             "empty": False
        #         }
        #     }
        # },
        {
            "ValueAttribute": {
                "target_attr_name": TASK_KEY_NAME,
                "source_attr_name": "meta",
                "default": {},
            }
        },
        {
            "ValueAttribute": {
                "target_attr_name": FRECKLET_KEY_NAME,
                "source_attr_name": "meta",
                "default": {},
            }
        },
        {
            "TemplateKeysAttribute": {
                "source_attr_name": "scriptling_content",
                "target_attr_name": "template_keys_content",
                "jinja_env": DEFAULT_FRECKLES_JINJA_ENV,
            }
        },
        {
            "TemplateKeysAttribute": {
                "source_attr_name": "task",
                "target_attr_name": "template_keys_task",
                "jinja_env": DEFAULT_FRECKLES_JINJA_ENV,
            }
        },
        # {
        #     "CliArgsAttribute": {
        #         "target_attr_name": "cli_args",
        #         "var_names_attr_name": "template_keys",
        #         "args_attr_name": "args",
        #         "default_arg": {
        #             "required": True,
        #             "empty": False
        #         }
        #     }
        # },
        {"DocAttribute": {"target_attr_name": "doc", "source_attr_name": "meta"}},
    ],
    "ting_id_attr": "scriptling_name",
    "mixins": [],
    "loaders": {
        "script_files": {
            "class": "ting.tings.FileTings",
            "load_config": {"folder_load_file_match_regex": "(\\.sh\\.j2$|\\.sh$)"},
            "attributes": [
                "FileStringContentAttribute",
                {
                    "MirrorAttribute": {
                        "source_attr_name": "filename_no_ext",
                        "target_attr_name": "scriptling_name",
                    }
                },
            ],
        }
    },
}


class ScriptlingContext(object):
    def __init__(self, context_name, cnf, repos):

        self._context_name = context_name
        self._cnf = cnf
        self.repos = repos
        self.repos = ["/home/markus/projects/repos/shell/frecklets-default-shell"]
        self._scriptling_index = None

    @property
    def scriptling_index(self):

        if self._scriptling_index is not None:
            return self._scriptling_index

        folder_index_conf = []
        used_aliases = []

        for f in self.repos:

            url = f

            alias = os.path.basename(url).split(".")[0]
            i = 1
            while alias in used_aliases:
                i = i + 1
                alias = "{}_{}".format(alias, i)

            used_aliases.append(alias)
            folder_index_conf.append(
                {"repo_name": alias, "folder_url": url, "loader": "script_files"}
            )

        self._scriptling_index = TingTings.from_config(
            "shell-scripts",
            folder_index_conf,
            SCRIPTLING_LOAD_CONFIG,
            indexes=["scriptling_name"],
        )
        return self._scriptling_index


class FrecklesAdapterShell(FrecklesAdapter):
    def __init__(self, name, context):

        super(FrecklesAdapterShell, self).__init__(
            adapter_name=name,
            context=context,
            config_schema=SHELL_CONFIG_SCHEMA,
            run_config_schema=SHELL_RUN_CONFIG_SCHEMA,
        )

        self._shell_context = None
        self._processors = {}
        # self.processors["script-template"] = ShellScriptTemplateProcessor(self)
        # self.processors["exodus-binary"] = ShellExodusTemplateProcessor(self)

    def get_processor(self, proc_name):

        if proc_name in self._processors.keys():

            return self._processors[proc_name]

        if proc_name == "scriptling-template" or "scriptling":
            # proc = ShellScriptTemplateProcessor()
            # elif proc_name == "scriptling":
            proc = ShellScriptProcessor(self.shell_adapter_contex.scriptling_index)
        else:
            raise Exception("No processor for type: {}".format(proc_name))

        self._processors[proc_name] = proc

        return self._processors[proc_name]

    @property
    def shell_adapter_contex(self):

        if self._shell_context is not None:
            return self._shell_context

        cnf = Cnf(self.context.config)
        self._shell_context = ScriptlingContext("default", cnf, None)

        return self._shell_context

    def get_resources_for_task(self, task):

        pass

    def get_folders_for_alias(self, alias):

        if alias == "default":
            return ["/home/markus/temp/scriptlings"]
        return []

    def get_supported_resource_types(self):

        return ["scripts"]

    def get_supported_task_types(self):

        return ["scriptling", "scriptling-template"]

    def get_extra_frecklets(self):

        result = {}
        for (
            scriptling_name,
            scriptling,
        ) in self.shell_adapter_contex.scriptling_index.items():

            frecklet = {}
            frecklet["args"] = scriptling.meta.get("args", {})
            frecklet["doc"] = scriptling.meta.get("doc", {})

            if scriptling.template_keys_content:
                f_type = "scriptling-template"
            else:
                f_type = "scriptling"

            f_dict = copy.deepcopy(scriptling.frecklet)
            dict_merge(
                f_dict, {"type": f_type, "name": scriptling_name}, copy_dct=False
            )
            f = {
                FRECKLET_KEY_NAME: f_dict,
                TASK_KEY_NAME: scriptling.task,
                VARS_KEY: {},
            }

            f[TASK_KEY_NAME]["script"] = scriptling.scriptling_content

            frecklet[FRECKLETS_KEY] = [f]

            result[scriptling_name] = frecklet

        # import pp
        # pp(result)

        return result

    def prepare_execution_requirements(self, run_config, parent_task):

        pass

    def run(
        self,
        tasklist,
        run_vars,
        run_config,
        run_secrets,
        run_env,
        result_callback,
        parent_task,
    ):

        # import pp
        # output(tasklist, output_type="yaml")

        runner = ShellRunner()

        shell_run_dir = os.path.join(run_env["env_dir"], "shell")
        os.makedirs(shell_run_dir)

        shell_tasks = []
        for task in tasklist:

            task_type = task[FRECKLET_KEY_NAME]["type"]

            proc = self.get_processor(task_type)
            processed = proc.process_task(task)

            processed["_id"] = task[FRECKLET_KEY_NAME]["_task_id"]
            processed["_name"] = task[FRECKLET_KEY_NAME]["name"]
            processed["_msg"] = task[FRECKLET_KEY_NAME].get("msg", processed["_name"])

            # tasks = processed["tasks"]
            # functions = processed["functions"]
            # ext_files = processed["ext_files"]

            shell_tasks.append(processed)

        run_properties = runner.render_environment(
            run_env_dir=shell_run_dir, tasklist=shell_tasks
        )

        run_properties = runner.run(
            run_cnf=run_config,
            run_properties=run_properties,
            result_callback=result_callback,
            parent_task=parent_task,
        )

        return run_properties
