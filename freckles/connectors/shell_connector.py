from plumbum import local

from freckles.exceptions import FrecklesConfigException
from freckles.freckles_runner import TaskDetail
from frkl import FrklistContext
from .connectors import FrecklesConnector

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
        }
    },
}

# class ExecutablesIndex(LuItemIndex):
#
#     def __init__(self, base_path, require_full_paths=False):
#
#         super(ExecutablesIndex, self).__init__(url=base_path, item_type="frecklet")
#         self.require_full_paths = require_full_paths


class ShellContext(FrklistContext):
    def __init__(self, **kwargs):

        super(ShellContext, self).__init__(**kwargs)


class ShellConnector(FrecklesConnector):
    def __init__(self, connector_name="shell"):

        super(ShellConnector, self).__init__(connector_name=connector_name)

        self.require_absolute_path = None
        self.shell_context = None

    def get_frecklet_metadata(self, name):

        return None

    def get_shell_context(self):

        if self.shell_context is None:

            self.shell_context = ShellContext()

        return self.shell_context

    def get_supported_task_types(self):

        result = ["shell-command", "shell-pipe", "shell-script"]
        return result

    def run(self, tasklist, context_config=None, run_config=None,
            result_callback=None, output_callback=None,
            sudo_password=None,
            parent_task=None):

        callback_adapter = ShellFrecklesCallbackAdapter(
            parent_task=parent_task,
            result_callback=result_callback, output_callback=output_callback
        )

        no_run = self.get_cnf_value("no_run")
        no_run_list = []
        result_list = []

        for task in tasklist:

            if "command" in task["task"].keys():
                command = task["task"]["command"]
            else:
                command = task["task"].get("name")

            if command is None:
                raise FrecklesConfigException(
                    "Neither 'name' nor 'command' key specified in task: {}".format(
                        task
                    )
                )

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

    def get_cnf_schema(self):

        return {}

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

        self.output_callback.task_finished(self.latest_task, success=success, msg=msg, skipped=skipped, changed=changed)
        self.latest_task = None
