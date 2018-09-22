# -*- coding: utf-8 -*-

# python 3 compatibility
from __future__ import absolute_import, division, print_function, unicode_literals

import abc
import datetime

import logging
import os
import shutil

import six
from cookiecutter.main import cookiecutter
from jinja2 import Environment, PackageLoader
from plumbum import local

from freckles.defaults import MIXED_CONTENT_TYPE, FRECKLES_RUN_DIR, FRECKLES_CURRENT_RUN_SYMLINK
from freckles.exceptions import FrecklesConfigException
from freckles.freckles_runner import TaskDetail
from frkl import FrklistContext
from frutils import DEFAULT_EXCLUDE_DIRS, dict_merge, replace_string, JINJA_DELIMITER_PROFILES
from .connectors import FrecklesConnector

log = logging.getLogger("freckles")

FRECKLES_SHELL_CONNTECTOR_MODULE_FOLDER = os.path.dirname(__file__)
SHELL_CONNECTOR_ENVIRONMENT_TEMPLATE = os.path.join(FRECKLES_SHELL_CONNTECTOR_MODULE_FOLDER, "..",
                                                    "external", "shell-environment-template")
SHELL_INTERNAL_SCRIPT_TEMPLATE_REPO = os.path.join(
    FRECKLES_SHELL_CONNTECTOR_MODULE_FOLDER, "..", "external", "script-templates"
)
SHELL_DEFAULT_REPO_ALIASES = {
    "default": {
        "script-templates": [SHELL_INTERNAL_SCRIPT_TEMPLATE_REPO]
    }
}

SHELL_JINJA_ENV = Environment(**JINJA_DELIMITER_PROFILES["shell"])

SHELL_CONFIG_SCHEMA = {
    "run_folder": {
        "type": "string",
        "default": FRECKLES_RUN_DIR,
        "__doc__": {"short_help": "the target for the generated shell execution bundle"}
    },
    "current_run_folder": {
        "type": "string",
        "default": FRECKLES_CURRENT_RUN_SYMLINK,
        "__doc__": {
            "short_help": "target of a symlink the current shell execution bundle"
        },
        "__alias__": "add_symlink_to_env",
    },
    "force_run_folder": {
        "type": "boolean",
        "default": True,
        "__alias__": "force",
        "__doc__": {
            "short_help": "overwrite a potentially already existing execution bundle"
        },
    },
    "add_timestamp_to_env": {
        "type": "boolean",
        "default": True,
        "__doc__": {
            "short_help": "whether to add a timestamp to the execution bundle folder name"
        },
    },
    "allow_remote": {
        "type": "boolean",
        "default": False,
        "__doc__": {
            "short_help": "whether to allow remote resources (binaries, script-templates, etc..."
        }

    },
    "allow_remote_script_templates": {
        "type": "boolean",
        "default": False,
        "__doc__": {
            "short_help": "whether to allow remote script templates, overwrites 'allow_remote'"
        }

    }
}

SHELL_RUN_CONFIG_SCHEMA = {
    "ssh_key": {
        "type": "string",
        "__doc__": {"short_help": "the path to a ssh key identity file"},
    },
    "user": {
        "type": "string",
        "__doc__": {"short_help": "the user name to use for the connection"},
    },
    "host": {
        "type": "string",
        "__doc__": {"short_help": "the host to connect to"},
        "default": "localhost",
    },
    "host_ip": {"type": "string", "__doc__": {"short_help": "the host ip, optional"}},
    "no_run": {
        "type": "boolean",
        "coerce": bool,
        "__doc__": {
            "short_help": "only create the shell environment, don't execute anything"
        },
    },
}

# class ExecutablesIndex(LuItemIndex):
#
#     def __init__(self, base_path, require_full_paths=False):
#
#         super(ExecutablesIndex, self).__init__(url=base_path, item_type="frecklet")
#         self.require_full_paths = require_full_paths

def find_script_templates_in_repos(script_template_repos):

    if isinstance(script_template_repos, six.string_types):
        script_template_repos = [script_template_repos]

    result = {}
    for strepo in script_template_repos:
        templates = find_script_templates_in_repo(strepo)
        dict_merge(result, templates, copy_dct=False)

    return result


SCRIPT_TEMPLATE_REPO_CACHE = {}
SCRIPT_TEMPLATE_EXTENSIONS = [".script-template"]
def find_script_templates_in_repo(script_template_repo):

    if script_template_repo in SCRIPT_TEMPLATE_REPO_CACHE.keys():
        return SCRIPT_TEMPLATE_REPO_CACHE[script_template_repo]

    result = {}
    try:
        for root, dirnames, filenames in os.walk(
            os.path.realpath(script_template_repo), topdown=True, followlinks=True
        ):
            dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]
            # check for extensions

            for filename in filenames:

                match = False
                for ext in SCRIPT_TEMPLATE_EXTENSIONS:
                    if filename.endswith("{}".format(ext)):
                        match = True
                        break
                if not match:
                    continue

                st_file = os.path.join(root, filename)
                st_name = os.path.splitext(filename)[0]
                result[st_name] = st_file
    except (Exception) as e:
        log.warn("Can't retrieve script-templates from repo '{}': {}".format(script_template_repo, e))
        log.debug(e, exc_info=1)

    SCRIPT_TEMPLATE_REPO_CACHE[script_template_repo] = result
    return result


class ShellContext(FrklistContext):
    def __init__(self, allow_remote_script_templates=None, **kwargs):

        super(ShellContext, self).__init__(**kwargs)

        if allow_remote_script_templates is None:
            allow_remote_script_templates = self.allow_remote

        self.allow_remote_script_templates = allow_remote_script_templates
        self.script_template_repos = self.urls.get("script-templates")
        self.available_script_templates = find_script_templates_in_repos(self.script_template_repos)

@six.add_metaclass(abc.ABCMeta)
class ShellTaskTypeProcessor(object):

    def __init__(self, connector):

        self.connector = connector

    @abc.abstractmethod
    def process_task(self, task):
        """Takes a task description, returns a shell command incl. context."""

        pass


class ShellCommandProcessor(ShellTaskTypeProcessor):

    def process_task(self, task):

        # if "command" in task["task"].keys():
        #     command = task["task"]["command"]
        # else:
        #     command = task["task"].get("name")
        command = task["task"]["command"]

        # if command is None:
        #     raise FrecklesConfigException(
        #         "Neither 'name' nor 'command' key specified in task: {}".format(
        #             task
        #         )
        #     )

        if "command_tokens" in task["task"].keys():
            command_tokens = task["task"]["command_tokens"]
        else:
            command_tokens = []

        vars = task.get("vars", {})
        args = []
        for token in command_tokens:
            if token not in vars.keys():
                raise Exception("Token '{}' not available in vars")
            if vars[token]:
                args.append(vars[token])

        return {"command": command, "args": args, "ext_files": {}}

class ShellScriptTemplateProcessor(ShellTaskTypeProcessor):

    def __init__(self, connector):

        super(ShellScriptTemplateProcessor, self).__init__(connector)

        self.command_proc = ShellCommandProcessor(connector)

    def process_task(self, task):

        template_script = task["task"]["command"]
        context = self.connector.get_shell_context()

        template_script_path = context.available_script_templates.get(template_script, None)
        if template_script_path is None:
            raise FrecklesConfigException("No script-template '{}' available.".format(template_script))

        with open(template_script_path, 'r') as ts:
            ts_content = ts.read()

        replaced_script = replace_string(ts_content, task.get("vars", {}), SHELL_JINJA_ENV)

        command_desc = self.command_proc.process_task(task)
        command_desc["script_content"] = replaced_script
        command_desc["extra_files"] = {
            template_script: {
                "type": "content",
                "content": replaced_script,
            }
        }

        return command_desc

class ShellConnector(FrecklesConnector):

    def __init__(self, connector_name="shell"):

        super(ShellConnector, self).__init__(connector_name=connector_name)

        self.require_absolute_path = None
        self.shell_context = None
        self.processors = {}
        self.processors["shell-command"] = ShellCommandProcessor(self)
        self.processors["script-template"] = ShellScriptTemplateProcessor(self)

    def get_shell_context(self):

        if self.shell_context is None:
            script_template_repos = [
                r["path"]
                for r in self.content_repos
                if r["content_type"] == "script-templates"
                or r["content_type"] == MIXED_CONTENT_TYPE
            ]

            urls = {"script-templates": script_template_repos}
            allow_remote = self.get_cnf_value("allow_remote")
            allow_remote_script_templates = self.get_cnf_value("allow_remote_script_templates")

            if allow_remote_script_templates is None:
                allow_remote_script_templates = allow_remote

            self.shell_context = ShellContext(
                urls=urls,
                allow_remote_script_templates=allow_remote_script_templates
            )

        return self.shell_context

    def get_frecklet_metadata(self, name):

        return None

    def get_supported_task_types(self):

        result = ["shell-command", "script-template"]
        return result

    def get_supported_repo_content_types(self):

        return ["script-templates"]

    def generate_shell_script(self, script_task_list):

        jinja_env = Environment(loader=PackageLoader("freckles", "templates"))
        template = jinja_env.get_template("shell_script_template.sh")

        output_text = template.render(tasklist=script_task_list)
        return output_text

    def render_environment(self, env_dir, tasklist, force, add_timestamp_to_env):

        env_dir = os.path.expanduser(env_dir)
        if add_timestamp_to_env:
            start_date = datetime.now()
            date_string = start_date.strftime("%y%m%d_%H_%M_%S")
            dirname, basename = os.path.split(env_dir)
            env_dir = os.path.join(dirname, "{}_{}".format(basename, date_string))

        result = {}
        result["env_dir"] = env_dir

        working_dir = os.path.join(env_dir, "working_dir")
        executables_dir = os.path.join(env_dir, "executables")
        run_script = os.path.join(env_dir, "run.sh")

        result["working_dir"] = working_dir
        result["executables_dir"] = executables_dir
        result["run_script"] = run_script

        if os.path.exists(env_dir) and force:
            shutil.rmtree(env_dir)

        cookiecutter_details = {
            "tasklist": tasklist,
        }

        log.debug("Creating shell environment from template...")
        log.debug("Using cookiecutter details: {}".format(cookiecutter_details))

        cookiecutter(SHELL_CONNECTOR_ENVIRONMENT_TEMPLATE, extra_context=cookiecutter_details, no_input=True)

    def run(
        self,
        tasklist,
        context_config=None,
        run_config=None,
        result_callback=None,
        output_callback=None,
        sudo_password=None,
        parent_task=None,
    ):

        callback_adapter = ShellFrecklesCallbackAdapter(
            parent_task=parent_task,
            result_callback=result_callback,
            output_callback=output_callback,
        )

        script_task_list = []
        for task in tasklist:

            tasktype = task["task"]["type"]
            msg = task["task"].get("__msg__", task["task"]["name"])

            proc = self.processors.get(tasktype, None)
            if proc is None:
                raise FrecklesConfigException("No task processor for task type '{}' implemented (yet).".format(tasktype))

            c_r = proc.process_task(task)
            command = c_r["command"]
            args = c_r["args"]
            ext_files = c_r["ext_files"]
            script_task_list.append({"command": command, "args": args, "msg": msg})



        script = self.generate_shell_script(script_task_list)

        no_run = self.get_cnf_value("no_run")
        no_run_list = []
        result_list = []

        if not no_run:
            cmd = local[command]
            callback_adapter.add_command_started(task)
            rc, stdout, stderr = cmd.run(args, retcode=None)

            callback_adapter.add_command_result(
                rc=rc, stdout=stdout, stderr=stderr, task=task
            )
            result_list.append({"rc": rc, "stdout": stdout, "stderr": stderr})
        else:
            no_run_list.append(command)

        if not no_run:
            result = {"result": result_list}
        else:
            result = {"result": no_run_list}
        return result

    def get_repo_aliases(self):

        return SHELL_DEFAULT_REPO_ALIASES

    def get_indexes(self):

        return []

    def get_cnf_schema(self):

        return SHELL_CONFIG_SCHEMA

    def get_run_config_schema(self):

        return SHELL_RUN_CONFIG_SCHEMA

    def get_indexes(self):

        return None


class ShellFrecklesCallbackAdapter(object):
    def __init__(self, parent_task, result_callback=None, output_callback=None):

        self.parent_task = parent_task
        self.result_callback = result_callback
        self.output_callback = output_callback
        self.latest_task = None

    def add_command_started(self, task):

        td = TaskDetail(
            task_name=task["task"]["name"],
            task_type=task["task"]["type"],
            task_parent=self.parent_task,
        )

        self.output_callback.task_started(td)
        self.latest_task = td

    def add_command_result(self, rc, stdout, stderr, task):

        expected = task.get("expected_exit_code", 0)
        success = True
        changed = True
        skipped = False

        if expected != rc:
            success = False
            changed = False

        msg = ""
        if stdout:
            msg = "{}\nstdout:\n{}".format(msg, stdout)
        if stderr:
            msg = "{}\nstderr:\n{}".format(msg, stderr)

        self.output_callback.task_finished(
            self.latest_task, success=success, msg=msg, skipped=skipped, changed=changed
        )
        self.latest_task = None
