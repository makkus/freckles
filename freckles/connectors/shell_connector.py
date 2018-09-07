from plumbum import local

from freckles.exceptions import FrecklesConfigException
from frkl import FrklistContext
from .connectors import FrecklesConnector

SHELL_CONFIG_SCHEMA = {
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

    def run(self, tasklist, config=None, result_callback=None, output_callback=None):

        callback_adapter = ShellFrecklesCallbackAdapter(
            result_callback=result_callback, output_callback=output_callback
        )

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

            cmd = local[command]
            callback_adapter.add_command_started(task)
            rc, stdout, stderr = cmd.run(args, retcode=None)

            callback_adapter.add_command_result(
                rc=rc, stdout=stdout, stderr=stderr, task=task
            )

    def get_cnf_schema(self):

        return SHELL_CONFIG_SCHEMA

    def get_indexes(self):

        return None


class ShellFrecklesCallbackAdapter(object):
    def __init__(self, result_callback=None, output_callback=None):

        self.result_callback = result_callback
        self.output_callback = output_callback

    def add_command_started(self, task):

        details = {}
        details["task_id"] = task["task"]["_task_id"]
        details["name"] = task["task"]["name"]
        self.output_callback.task_started(details)

    def add_command_result(self, rc, stdout, stderr, task):

        details = {}

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

        details["changed"] = changed
        details["skipped"] = skipped
        details["msg"] = msg

        self.output_callback.task_finished(success, details)
