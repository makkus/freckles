# -*- coding: utf-8 -*-
import abc
import logging

import six

from freckles.defaults import TASK_KEY_NAME, VARS_KEY, FRECKLET_KEY_NAME

log = logging.getLogger("freckles")


@six.add_metaclass(abc.ABCMeta)
class ShellTaskTypeProcessor(object):
    def __init__(self):
        pass

    @abc.abstractmethod
    def process_task(self, task):
        """Takes a task description, returns a list of shell script parts incl. optional external dependencies."""

        pass


class ShellCommandProcessor(ShellTaskTypeProcessor):
    def __init__(self):

        super(ShellCommandProcessor, self).__init__()

    def process_task(self, task):

        # if "command" in task["task"].keys():
        #     command = task["task"]["command"]
        # else:
        #     command = task["task"].get("name")
        command = task[TASK_KEY_NAME]["command"]

        task_id = task[TASK_KEY_NAME]["_task_id"]

        command_tokens = task[TASK_KEY_NAME].get("command_tokens", [])

        vars = task.get(VARS_KEY, {})
        args = []
        for token in command_tokens:
            if token not in vars.keys():
                raise Exception("Token '{}' not available in vars")
            if vars[token]:
                args.append(vars[token])

        msg = task[FRECKLET_KEY_NAME].get("msg", command)
        return {
            "tasks": [
                {
                    "command": command,
                    "args": args,
                    "type": task[FRECKLET_KEY_NAME]["type"],
                    "msg": msg,
                    "id": task_id,
                }
            ],
            "files": {},
            "functions": {},
        }


class ShellScriptProcessor(ShellTaskTypeProcessor):
    def __init__(self, scriptling_index):
        super(ShellScriptProcessor, self).__init__()
        self.scriptling_index = scriptling_index

    def get_all_dependency_functions(self, functions, scriptling_name, result=None):

        if result is None:
            result = {}

        for f in functions:
            scriptling = self.scriptling_index.get(f)
            if scriptling.template_keys_content:
                raise Exception(
                    "Can't use scriptling '{}' as function (from: {}) as it has templated content.".format(
                        f, scriptling_name
                    )
                )

            if f in result.keys():
                continue

            result[f] = scriptling.scriptling_content
            child_functions = scriptling.task.get("functions", [])
            self.get_all_dependency_functions(child_functions, scriptling.id, result)

        return result

    def process_task(self, task):

        script_name = task[TASK_KEY_NAME]["command"]
        params = task[TASK_KEY_NAME].get("params", [])

        content = task[TASK_KEY_NAME]["script"]

        task_functions = task[TASK_KEY_NAME].get("functions", [])
        functions = self.get_all_dependency_functions(task_functions, script_name)
        files = {}

        command_name = task[TASK_KEY_NAME].get("command_name", None)
        if command_name is None:

            is_idempotent = False
            if is_idempotent:
                command_name = script_name
            else:
                task_id = task[FRECKLET_KEY_NAME]["_task_id"]
                command_name = "{}_{}".format(script_name, task_id)

        commands = [command_name]
        for p in params:
            commands.append('"{}"'.format(p))

        use_function = True
        if use_function:
            functions[command_name] = content
        else:
            ext_file = {}
            ext_file["type"] = "string_content"
            if not content.strip().startswith("#!/"):
                content = "#!/usr/bin/env bash\n\n" + content
            ext_file["content"] = content

            files[command_name] = ext_file

        command_desc = {"commands": [commands], "files": files, "functions": functions}

        return command_desc


class ShellScriptTemplateProcessor(ShellTaskTypeProcessor):
    def __init__(self):
        super(ShellScriptTemplateProcessor, self).__init__()

        # self.scrptling_index = scriptling_index

    def process_task(self, task):

        template_script = task[TASK_KEY_NAME]["command"]

        content = task[TASK_KEY_NAME]["script"]

        task_id = task[FRECKLET_KEY_NAME]["_task_id"]

        command_name = "{}_{}".format(template_script, task_id)

        ext_file = {}
        ext_file["type"] = "string_content"
        ext_file["content"] = content

        command_desc = {"commands": [], "files": {}, "functions": {}}
        command_desc["commands"].append([command_name])
        command_desc["files"][command_name] = ext_file

        return command_desc
