# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict

import colorama
from colorama import Fore, Style

from frutils import readable_yaml, dict_merge

colorama.init()

log = logging.getLogger("freckles")

ALLOWED_STATUS = ["ok", "skipped", "changed", "failed"]


# extensions


# ------------------------------------------------------------------------


class FrecklesRun(object):
    def __init__(self, run_id, result_dict):

        self.run_id = run_id
        self.result_dict = result_dict

        self.adapter = self.result_dict["adapter"]
        self.frecklet_name = self.result_dict["name"]
        self.outcome = self.result_dict["result"]
        self.run_properties = self.result_dict["run_properties"]
        self.task_list = self.result_dict["task_list"]

    def __str__(self):

        return readable_yaml(
            {
                "name": self.frecklet_name,
                "run_properties": self.run_properties,
                "task_list": self.task_list,
            }
        )


CURSOR_UP_ONE = "\x1b[1A"
ERASE_LINE = "\x1b[2K"

BOLD = "\033[1m"
UNBOLD = "\033[0m"

ARC_DOWN_RIGHT = u"\u256d"
ARC_UP_RIGHT = u"\u2570"
VERTICAL_RIGHT = u"\u251C"
VERTICAL = u"\u2502"
HORIZONTAL = u"\u2500"
END = u"\u257C"
ARROW = u"\u279B"
OK = u"\u2713"


def colorize_status(status, ignore_errors=False):

    result = None
    if status == "ok":
        result = Fore.GREEN + status + Style.RESET_ALL
    elif status == "changed":
        result = Fore.GREEN + status + Style.RESET_ALL
    elif status == "skipped":
        result = Fore.YELLOW + status + Style.RESET_ALL
    elif status == "failed":
        if not ignore_errors:
            result = Fore.RED + status + Style.RESET_ALL
        else:
            result = (
                Fore.YELLOW
                + "{} (but 'ignore_errors' set)".format(status)
                + Style.RESET_ALL
            )
    else:
        result = status

    return result


DISPLAY_PROFILES = {
    "minimal": {
        "display_skipped": False,
        "display_unchanged": False,
        "display_msg_when_successful": False,
        "display_ok_status": False,
        "display_detail_level": 0,
        "display_nothing": False,
        "display_run_parameters": False,
        "display_adapter_run_parameters": False,
        "display_system_messages": False,
    },
    "verbose": {
        "display_skipped": True,
        "display_unchanged": True,
        "display_msg_when_successful": True,
        "display_ok_status": True,
        "display_detail_level": 10,
        "display_nothing": False,
        "display_run_parameters": True,
        "display_adapter_run_parameters": True,
        "display_system_messages": True,
    },
    "default": {
        "display_skipped": False,
        "display_unchanged": True,
        "display_msg_when_successful": False,
        "display_ok_status": True,
        "display_detail_level": 1,
        "display_nothing": False,
        "display_run_parameters": False,
        "display_adapter_run_parameters": False,
        "display_system_messages": False,
    },
    "detailed": {
        "display_skipped": False,
        "display_unchanged": True,
        "display_msg_when_successful": True,
        "display_ok_status": True,
        "display_detail_level": 2,
        "display_nothing": False,
        "display_run_parameters": True,
        "display_adapter_run_parameters": True,
        "display_system_messages": True,
    },
    "info": {
        "display_skipped": False,
        "display_unchanged": True,
        "display_msg_when_successful": True,
        "display_ok_status": True,
        "display_detail_tasks": False,
        "display_detail_level": 0,
        "display_nothing": False,
        "display_run_parameters": False,
        "display_adapter_run_parameters": True,
        "display_system_messages": False,
    },
    "silent": {
        "display_skipped": False,
        "display_unchanged": False,
        "display_msg_when_successful": False,
        "display_ok_status": False,
        "display_detail_level": 0,
        "display_detail_tasks": False,
        "display_nothing": True,
        "display_run_parameters": False,
        "display_adapter_run_parameters": False,
        "display_system_messages": False,
    },
}

#
# class DefaultCallback(TasksCallback):
#     """Default callback for freckles output.
#
#     This is more complicated than it needed to be. Mainly because it's quite hard
#     to parse and display Ansible output in a nice, compact format.
#     """
#
#     def __init__(self, **kwargs):
#
#         super(DefaultCallback, self).__init__()
#
#         profile = kwargs.get("profile", None)
#
#         profile_dict = DISPLAY_PROFILES.get(profile, None)
#         if profile_dict is None:
#             log.debug(
#                 "No callback profile '{}' available, using defaults...".format(profile)
#             )
#             profile_dict = DISPLAY_PROFILES["default"]
#
#         self.display_skipped = kwargs.get(
#             "display_skipped", profile_dict["display_skipped"]
#         )
#         self.display_unchanged = kwargs.get(
#             "display_unchanged", profile_dict["display_unchanged"]
#         )
#         self.display_messages_when_successful = kwargs.get(
#             "display_msg_when_successful", profile_dict["display_msg_when_successful"]
#         )
#         self.display_ok_status = kwargs.get(
#             "display_ok_status", profile_dict["display_ok_status"]
#         )
#         self.display_detail_level = kwargs.get(
#             "display_detail_level", profile_dict["display_detail_level"]
#         )
#         self.display_nothing = kwargs.get(
#             "display_nothing", profile_dict["display_nothing"]
#         )
#         self.display_run_parameters = kwargs.get(
#             "display_run_parameters", profile_dict["display_run_parameters"]
#         )
#         self.display_adapter_run_parameters = kwargs.get(
#             "display_adapter_run_parameters",
#             profile_dict["display_adapter_run_parameters"],
#         )
#         self.display_system_messages = kwargs.get(
#             "display_system_messages", profile_dict["display_system_messages"]
#         )
#
#     def add_system_message(self, message):
#
#         if self.display_system_messages:
#
#             click.echo("MESSAGE: {}".format(message))
#
#     def output(self, line, nl=True):
#
#         if self.display_nothing:
#             return
#
#         click.echo(line.encode("utf-8"), nl=nl)
#
#     def delete_last_line(self):
#
#         if self.display_nothing:
#             return
#
#         sys.stdout.write(CURSOR_UP_ONE)
#         sys.stdout.write(ERASE_LINE)
#
#     def execution_started(self):
#
#         pass
#
#     def execution_finished(self):
#
#         pass
#
#     def task_started_action(self, details):
#
#         task_name = details.task_name
#         # task_type = details.task_type
#
#         level = self.get_level_current_task()
#
#         if level == 0:
#             self.current_message = u"{}{} starting: {}{}{}".format(
#                 ARC_DOWN_RIGHT, HORIZONTAL, BOLD, task_name, UNBOLD
#             )
#             self.output(self.current_message)
#             return
#
#         padding = u"{}  ".format(VERTICAL) * (level - 1)
#         msg = details.get_task_title()
#         self.current_message = u"{}{}{} {}".format(padding, VERTICAL_RIGHT, END, msg)
#         self.output(self.current_message)
#
#     def task_finished_action(self, details):
#
#         level = self.get_level_current_task()
#         padding = u"{}  ".format(VERTICAL) * (level - 1)
#
#         if details.success:
#             if details.skipped:
#                 status = "skipped"
#             else:
#                 status = "ok"
#         else:
#             status = "failed"
#
#         if not self.display_skipped and status == "skipped":
#             self.delete_last_line()
#             self.current_message = None
#             return
#
#         if not self.display_unchanged and (details.success and not details.changed):
#             self.delete_last_line()
#             self.current_message = None
#             return
#
#         # detail_level = details.detail_level
#         # if self.display_detail_level < detail_level and details.success:
#         #
#         #     self.delete_last_line()
#         #     self.current_message = None
#         #     return
#         if details.msg:
#             msg = details.msg
#
#             # TODO: make that more generic
#             if "Permission denied (publickey,password)" in msg:
#                 msg = msg + (
#                     "\n\nBy default 'freckles' is trying to connect via ssh keys. Maybe try to use the '--ask-pass' flag to enable password authentication."
#                 )
#
#             if not details.success or (
#                 details.success and self.display_messages_when_successful
#             ):
#                 first_line = True
#                 for line in msg.strip().split("\n"):
#                     line = line.rstrip()
#                     if (
#                         first_line
#                         or line.startswith("stdout")
#                         or line.startswith("stderr")
#                     ):
#                         self.output(
#                             u"{}{}  {}{} {}".format(
#                                 padding, VERTICAL, VERTICAL_RIGHT, END, line
#                             )
#                         )
#                         first_line = False
#                     else:
#                         self.output(
#                             u"{}{}  {}  {}".format(padding, VERTICAL, VERTICAL, line)
#                         )
#         if details.debug_data:
#             data = details.debug_data
#             data_lines = readable_yaml(data).strip().split("\n")
#             first_line = True
#             for line in data_lines:
#                 line = line.rstrip()
#                 if first_line:
#                     self.output(
#                         u"{}{}  {}{} {}".format(
#                             padding, VERTICAL, VERTICAL_RIGHT, END, line
#                         )
#                     )
#                     first_line = False
#                 else:
#                     self.output(
#                         u"{}{}  {}  {}".format(padding, VERTICAL, VERTICAL, line)
#                     )
#
#         if details.result_data:
#             data = details.result_data
#
#             data_lines = readable_yaml(data).strip().split("\n")
#             first_line = True
#             for line in data_lines:
#                 line = line.rstrip()
#                 if first_line:
#                     self.output(
#                         u"{}{}  {}{} {}".format(
#                             padding, VERTICAL, VERTICAL_RIGHT, END, line
#                         )
#                     )
#                     first_line = False
#                 else:
#                     self.output(
#                         u"{}{}  {}  {}".format(padding, VERTICAL, VERTICAL, line)
#                     )
#
#         if level == 0:
#             self.output(
#                 u"{}{} {}".format(
#                     ARC_UP_RIGHT,
#                     HORIZONTAL,
#                     colorize_status(status, ignore_errors=details.ignore_errors),
#                 )
#             )
#             return
#
#         self.output(
#             u"{}{}  {}{} {}".format(
#                 padding,
#                 VERTICAL,
#                 ARC_UP_RIGHT,
#                 END,
#                 colorize_status(status, ignore_errors=details.ignore_errors),
#             )
#         )
#
#         # self.output(self.current_message)
#         self.current_message = None
#
#         # print(level)
#         # padding = "  " * (level)
#         # # click.echo(
#         # #     "{}details: {} - {}".format(padding, details.task_name, details.task_type)
#         # # )
#         # click.echo("{}success: {}".format(padding, details.success))
#         # if self.display_changed:
#         #     click.echo("{}changed: {}".format(padding, details.changed))
#         # if self.display_skipped:
#         #     click.echo("{}skipped: {}".format(padding, details.skipped))
#         # if details.debug_data:
#         #     click.echo("{}debug data:".format(padding))
#         #     readable = readable_yaml(details.debug_data, indent=(len(padding) + 2))
#         #     click.echo(readable)
#         # if details.result_data:
#         #     click.echo("{}result data:".format(padding))
#         #     readable = readable_yaml(details.result_data, indent=(len(padding)+2))
#         #     click.echo(readable)
#
#         # click.echo()
#         pass


# class DefaultCallbackOld(TasksCallback):
#     """Default callback for freckles output.
#
#     This is more complicated than it needed to be. Mainly because it's quite hard
#     to parse and display Ansible output in a nice, compact format.
#     """
#
#     def __init__(self, **kwargs):
#
#         super(DefaultCallback, self).__init__()
#
#         self.current_no_run = kwargs.get("no_run", False)
#
#         self.current_task_list = None
#         self.current_adapter = None
#         self.current_adapter_config = None
#         self.current_task_id = None
#
#         self.current_execution_id = 1
#         # self.current_task_id = None
#         self.current_task = {
#             "root": False,
#             "failed": False,
#             "skipped": False,
#             "changed": False,
#             "level": 0,
#             "id": -1,
#             "parent": {
#                 "failed": False,
#                 "root": True,
#                 "skipped": True,
#                 "changed": False,
#                 "id": -2,
#             },
#         }
#         self.current_env = None
#
#         if self.current_no_run:
#             profile = "silent"
#         else:
#             profile = kwargs.get("profile", None)
#
#         profile_dict = DISPLAY_PROFILES.get(profile, None)
#         if profile_dict is None:
#             log.debug(
#                 "No callback profile '{}' available, using defaults...".format(profile)
#             )
#             profile_dict = DISPLAY_PROFILES["default"]
#
#         self.display_skipped = kwargs.get(
#             "display_skipped", profile_dict["display_skipped"]
#         )
#         self.display_unchanged = kwargs.get(
#             "display_unchanged", profile_dict["display_unchanged"]
#         )
#         self.display_messages_when_successful = kwargs.get(
#             "display_msg_when_successful", profile_dict["display_msg_when_successful"]
#         )
#         self.display_ok_status = kwargs.get(
#             "display_ok_status", profile_dict["display_ok_status"]
#         )
#         self.display_detail_tasks = kwargs.get(
#             "display_detail_tasks", profile_dict["display_detail_tasks"]
#         )
#         self.display_nothing = kwargs.get(
#             "display_nothing", profile_dict["display_nothing"]
#         )
#         self.display_run_parameters = kwargs.get(
#             "display_run_parameters", profile_dict["display_run_parameters"]
#         )
#         self.display_adapter_run_parameters = kwargs.get(
#             "display_adapter_run_parameters",
#             profile_dict["display_adapter_run_parameters"],
#         )
#
#     def execution_started(self, tasklist, adapter_name, run_config):
#
#         self.current_task_list = tasklist
#         self.current_adapter = adapter_name
#         # TODO: change to run_config
#         self.run_config = run_config
#
#         env_name = self.run_name
#         len_title = len("{}/{}".format(env_name, self.current_execution_id)) + 11
#
#         title = u"{} starting: {}'{}/{}'{}".format(
#             ARC_DOWN_RIGHT, BOLD, env_name, self.current_execution_id, UNBOLD
#         )
#
#         self.output(title)
#         self.output(u"{}{}{}".format(VERTICAL_RIGHT, (HORIZONTAL * len_title), END))
#         self.output(
#             u"{}{} adapter: {}".format(VERTICAL_RIGHT, END, self.current_adapter)
#         )
#
#         # if self.display_run_parameters:
#         #     current_config = copy.deepcopy(self.run_config.run_cnf.get_validated_cnf("freckles"))
#         #     # current_config.pop("callback_adapter", None)
#         #     self.output(u"{}{} config:".format(VERTICAL_RIGHT, END))
#         #     config_lines = readable_yaml(current_config).rstrip().split("\n")
#         #
#         #     for index, line in enumerate(config_lines):
#         #         if index == 0:
#         #             self.output(
#         #                 u"{}  {}{} {}".format(
#         #                     VERTICAL, ARC_UP_RIGHT, END, line.rstrip()
#         #                 )
#         #             )
#         #         else:
#         #             self.output(u"{}     {}".format(VERTICAL, line.rstrip()))
#         #     self.output(u"{}{}{}".format(VERTICAL_RIGHT, (HORIZONTAL * len_title), END))
#         #
#         # if self.display_adapter_run_parameters:
#         #     current_adapter_config = self.run_config.run_cnf.get_validated_cnf(adapter_name)
#         #     self.output(u"{}{} adapter config:".format(VERTICAL_RIGHT, END))
#         #     config_lines = readable_yaml(current_adapter_config).rstrip().split("\n")
#         #
#         #     for index, line in enumerate(config_lines):
#         #         if index == 0:
#         #             self.output(
#         #                 u"{}  {}{} {}".format(
#         #                     VERTICAL, ARC_UP_RIGHT, END, line.rstrip()
#         #                 )
#         #             )
#         #         else:
#         #             self.output(u"{}     {}".format(VERTICAL, line.rstrip()))
#         #     self.output(u"{}{}{}".format(VERTICAL_RIGHT, (HORIZONTAL * len_title), END))
#
#     def execution_finished(self):
#
#         if self.current_task["id"] >= -1:
#             success = not self.current_task["failed"]
#             if success:
#                 status = u"ok"
#             else:
#                 status = u"failed"
#
#             self.output(
#                 u"{}  {}{} {}".format(
#                     VERTICAL, ARC_UP_RIGHT, END, colorize_status(status)
#                 )
#             )
#         task = self.current_task["parent"]
#
#         task = self.current_task.get("parent", None)
#         if task is None:
#             task = self.current_task
#
#         success = not task["failed"]
#
#         # self.display_ok_status = True
#         # self.display_unchanged = True
#         # self.display_skipped = True
#         #
#         # while task["id"] > -2:
#         #
#         #     success = not task["failed"]
#         #     changed = task["changed"]
#         #     # skipped = task["skipped"]
#         #     details = {"changed": changed}
#         #     self.task_finished(success, details)
#         #     task = task["parent"]
#
#         if success:
#             status = u"ok"
#         else:
#             status = u"failed"
#
#         self.output(u"{}{} {}".format(ARC_UP_RIGHT, END, colorize_status(status)))
#         self.current_execution_id = self.current_execution_id + 1
#         self.current_task_id = None
#
#     def task_started(self, details):
#
#         # self.current_task_id = details.get("task_id", None)
#
#         task_id = details["task_id"]
#
#         msg = details["name"]
#
#         item = details.get("item", None)
#
#         if task_id > self.current_task_id:
#             self.current_task_id = task_id
#             msg = "Task: {}".format(msg)
#             level = 0
#         else:
#             level = self.current_task["level"] + 2
#
#         if item is not None:
#             level = level + 1
#
#         self.current_task = {
#             "root": False,
#             # "id": self.current_task_id,
#             "parent": self.current_task,
#             "level": level,
#             "failed": False,
#             "changed": False,
#             "skipped": True,
#             "id": self.current_task_id,
#         }
#
#         padding = u"{}  ".format(VERTICAL) * (level - 1)
#
#         if not isinstance(msg, string_types):
#
#             if isinstance(msg, dict):
#                 temp = {}
#                 for k, v in msg.items():
#                     if isinstance(v, string_types):
#                         v = v.strip()
#                     else:
#                         v = str(v).strip()
#                     if "\n" in v:
#                         v = '"{} ...'.format(v.strip().split("\n")[0])
#                     temp[k] = v
#                 msg = temp
#
#             msg = readable_yaml(msg).strip()
#
#         if "\n" in msg:
#             first_line = True
#             for line in msg.split("\n"):
#                 if first_line:
#                     self.output(u"{}{}{} {}".format(padding, VERTICAL_RIGHT, END, line))
#                     first_line = False
#                 else:
#                     self.output(u"{}{}  {}".format(padding, VERTICAL, line))
#         else:
#             self.output(u"{}{}{} {}".format(padding, VERTICAL_RIGHT, END, msg))
#
#     def set_parent_property(self, child, prop_name, value):
#
#         parent = child["parent"]
#         while not parent["root"]:
#             parent[prop_name] = value
#             parent = parent["parent"]
#
#     def output(self, line, nl=True):
#
#         if self.display_nothing:
#             return
#
#         click.echo(line, nl=nl)
#
#     def delete_last_line(self):
#
#         if self.display_nothing:
#             return
#
#         sys.stdout.write(CURSOR_UP_ONE)
#         sys.stdout.write(ERASE_LINE)
#
#     def task_finished(self, success, details):
#
#         # print(details)
#         # print(self.current_task_id)
#
#         if success:
#             if details.get("skipped", False):
#                 status = "skipped"
#             else:
#                 status = "ok"
#         else:
#             self.set_parent_property(self.current_task, "failed", True)
#             status = "failed"
#
#         if status != "skipped":
#             self.set_parent_property(self.current_task, "skipped", False)
#
#         if not self.display_skipped and status == "skipped":
#             self.delete_last_line()
#             self.current_task = self.current_task["parent"]
#             # self.current_task_id = self.current_task["id"]
#             return
#
#         changed = details.get("changed", False)
#         if changed:
#             self.set_parent_property(self.current_task, "changed", True)
#
#         if not self.display_unchanged and (success and not changed):
#             self.delete_last_line()
#             self.current_task = self.current_task["parent"]
#             # self.current_task_id = self.current_task["id"]
#             return
#
#         is_detail = details.get("task_is_detail", False)
#         if not self.display_detail_tasks and is_detail and success:
#             self.delete_last_line()
#             self.current_task = self.current_task["parent"]
#             # self.current_task_id = self.current_task["id"]
#             return
#
#         level = self.current_task["level"]
#         padding = u"{}  ".format(VERTICAL) * (level - 1)
#
#         msg = details.get("msg", None)
#         if msg is not None:
#             if not success or (success and self.display_messages_when_successful):
#                 first_line = True
#                 for line in msg.strip().split("\n"):
#                     line = line.rstrip()
#                     if (
#                         first_line
#                         or line.startswith("stdout")
#                         or line.startswith("stderr")
#                     ):
#                         self.output(
#                             u"{}{}  {}{} {}".format(
#                                 padding, VERTICAL, VERTICAL_RIGHT, END, line
#                             )
#                         )
#                         first_line = False
#                     else:
#                         self.output(
#                             u"{}{}  {}  {}".format(padding, VERTICAL, VERTICAL, line)
#                         )
#
#         if "debug_data" in details.keys() and details["debug_data"]:
#             data = details["debug_data"]
#             data_lines = readable_yaml(data).strip().split("\n")
#             first_line = True
#             for line in data_lines:
#                 line = line.rstrip()
#                 if first_line:
#                     self.output(
#                         u"{}{}  {}{} {}".format(
#                             padding, VERTICAL, VERTICAL_RIGHT, END, line
#                         )
#                     )
#                     first_line = False
#                 else:
#                     self.output(
#                         u"{}{}  {}  {}".format(padding, VERTICAL, VERTICAL, line)
#                     )
#
#         if "result_data" in details.keys() and details["result_data"]:
#             data = details["result_data"]
#
#             data_lines = readable_yaml(data).strip().split("\n")
#             first_line = True
#             for line in data_lines:
#                 line = line.rstrip()
#                 if first_line:
#                     self.output(
#                         u"{}{}  {}{} {}".format(
#                             padding, VERTICAL, VERTICAL_RIGHT, END, line
#                         )
#                     )
#                     first_line = False
#                 else:
#                     self.output(
#                         u"{}{}  {}  {}".format(padding, VERTICAL, VERTICAL, line)
#                     )
#
#         if self.display_ok_status or (not self.display_ok_status and status != "ok"):
#             if not success:
#                 status_string = "failed"
#             elif changed:
#                 status_string = "changed"
#             else:
#                 status_string = "ok"
#             self.output(
#                 u"{}{}  {}{} {}".format(
#                     padding, VERTICAL, ARC_UP_RIGHT, END, colorize_status(status_string)
#                 )
#             )
#
#         self.current_task = self.current_task["parent"]
#         self.current_task_id = self.current_task["id"]
#         # self.current_task_id = self.current_task["id"]
#
#     def task_update(self, msg):
#
#         # self.output("     -> {}".format(msg))
#         pass
#
#     def finish_up(self):
#
#         pass
RESULT_STRATEGIES = ["merge", "update", "append", "ordered_merge", "ordered_update"]


class FrecklesResultCallback(object):
    """ Class to gather results of a frecklecute run.

    Args:
        add_strategy:
    """

    def __init__(self, result_strategy="merge"):

        if result_strategy not in RESULT_STRATEGIES:
            raise Exception(
                "result_stragegy '{}' not supported.".format(result_strategy)
            )

        self.result_strategy = result_strategy
        if result_strategy == "append":
            self.result = []
        else:
            if "ordered" in result_strategy:
                self.result = OrderedDict()
            else:
                self.result = {}

    def add_result(self, overlay_dict):

        if "merge" in self.result_strategy:
            dict_merge(self.result, overlay_dict, copy_dct=False)
        elif "update" in self.result_strategy:
            self.result.update(overlay_dict)
        else:
            self.result.append(overlay_dict)

    def finish_up(self):

        pass
