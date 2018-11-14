# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import copy
import logging
import os
from collections import OrderedDict

from .defaults import FRECKLET_NAME
from .context import FrecklesContext
from .exceptions import FrecklesConfigException
from .frecklet_arg_helpers import add_user_input

log = logging.getLogger("freckles")


def is_disabled(task):

    disabled = task.get("__skip__", None)
    if disabled is None:
        return False

    if disabled is True:
        return True

    if disabled is not False and disabled:

        log.debug("Adding downstream skip condition: {}".format(disabled))
        task.setdefault("__skip_internal__", []).append(disabled)
        # raise FrecklesConfigException(
        #     "value for 'disabled' key needs to be of type 'bool': {}".format(disabled)
        # )

    for skip in task.get("__inherited_keys__", {}).get("__skip__", []):

        if skip is True:
            return True

        if skip is not False and skip:
            log.debug("Adding downstream skip condition: {}".format(disabled))
            task.setdefault("__skip_internal__", []).append(skip)

    return False


def needs_elevated_permissions(tasklist):

    for task in tasklist:
        become = task[FRECKLET_NAME].get("become", False) or task[FRECKLET_NAME].get(
            "needs_become", False
        )
        if become:
            return True

    return False


class Frecklecutable(object):
    @classmethod
    def create_from_file_or_name(cls, frecklet_path_or_name, vars=None, context=None):

        if context is None:
            context = FrecklesContext()

        name = os.path.splitext(os.path.basename(frecklet_path_or_name))[0]
        frecklet = context.create_frecklet(frecklet_path_or_name)

        return Frecklecutable(name, frecklet, vars=vars, context=context)

    def __init__(self, name, frecklet, vars=None, context=None):

        self.name = name

        if context is None:
            context = FrecklesContext()

        self.context = context
        if vars is None:
            vars = {}

        # for k, v in frecklet.args.items():
        #     v.setdefault("__meta__", {})["root_frecklet"] = True
        self.frecklet = frecklet

    def generate_click_parameters(self, default_vars=None):
        # frecklet = copy.deepcopy(self.frecklet)
        params = self.frecklet.generate_click_parameters(default_vars=default_vars)
        return params

    def postprocess_click_input(self, user_input):

        processed = self.frecklet.postprocess_click_input(user_input)
        return processed

    def get_doc(self):

        return self.frecklet.get_doc()

    def get_help_string(self):

        return self.frecklet.get_help_string()

    def get_short_help_string(self, list_item_format=False):

        return self.frecklet.get_short_help_string(list_item_format=list_item_format)

    def process_tasklist(self, vars=None):

        frecklet = copy.deepcopy(self.frecklet)
        # for k, v in frecklet.args.items():
        #     v.setdefault("__meta__", {})["root_frecklet"] = True
        #     frecklet.meta["__frecklet_level__"] = 0


        tl = frecklet.process_tasklist()
        # sys.exit()
        if vars is not None:
            add_user_input(tl, vars)

            # self.frecklet.validate_vars(vars)
            # TODO validate

        unknowns = []
        for item in tl:
            task_type = item[FRECKLET_NAME].get("type", "unknown")
            if task_type == "unknown":
                unknowns.append(item[FRECKLET_NAME]["name"])

        if unknowns:
            raise FrecklesConfigException(
                "One or more task items with unknown task type: {}".format(unknowns)
            )

        current_connector = None
        task_lists = OrderedDict()
        current_task_list = []
        task_list_index = 0
        for index, task in enumerate(tl):

            task[FRECKLET_NAME]["_task_id"] = index

            task_type = task[FRECKLET_NAME]["type"]
            connector_task = self.context.connector_map.get(task_type, None)
            if connector_task is None:
                raise FrecklesConfigException(
                    "No connector for task type '{}': {}".format(task_type, task)
                )

            if current_connector is None:
                current_connector = connector_task

            if current_connector != connector_task:
                # new frecklecutable run
                for t in current_task_list:
                    t[FRECKLET_NAME]["_task_list_id"] = task_list_index
                task_lists[task_list_index] = {
                    "task_list": current_task_list,
                    "connector": current_connector,
                    "name": self.name,
                }
                current_connector = connector_task
                current_task_list = []
                task_list_index = task_list_index + 1

            current_task_list.append(task)

        if current_task_list:
            for t in current_task_list:
                t[FRECKLET_NAME]["_task_list_id"] = task_list_index
            task_lists[task_list_index] = {
                "task_list": current_task_list,
                "connector": current_connector,
                "name": self.name,
            }

        return task_lists

    # def create_callback_adapter(self, run_cnf):
    #
    #     callback = run_cnf.config_dict.get("run_callback", "freckles")
    #     callback_config = run_cnf.get_value("freckles", "run_callback_config", {})
    #
    #     no_run = run_cnf.config_dict.get("no_run", None)
    #     if no_run is not None:
    #         callback_config["no_run"] = no_run
    #
    #     if callback.startswith("freckles:"):
    #         profile = callback[9:]
    #         callback = "freckles"
    #         callback_config["profile"] = profile
    #
    #     if callback is not None and callback in CALLBACK_CLASSES.names():
    #
    #         callback_adapter = CALLBACK_CLASSES[callback].plugin(**callback_config)
    #         run_cnf.set_cnf_key("callback", "freckles_callback")
    #
    #     elif callback is not None and callback in DISPLAY_PROFILES.keys():
    #
    #         callback_config["profile"] = callback
    #         callback = "freckles"
    #         callback_adapter = CALLBACK_CLASSES[callback].plugin(**callback_config)
    #         run_cnf.set_cnf_key("callback", "freckles_callback")
    #
    #     elif callback is None:
    #         callback_adapter = CALLBACK_CLASSES["default"].plugin(**callback_config)
    #         run_cnf.set_cnf_key("callback", "freckles_callback")
    #
    #     elif callback.startswith("backend"):
    #         callback_adapter = None
    #         if callback.startswith("backend:"):
    #             callback = callback[8:]
    #             run_cnf.set_cnf_key("run_callback", callback)
    #         else:
    #             callback = None
    #             run_cnf.remove_cnf_key("run_callback")
    #     else:
    #         callback_adapter = None
    #         # run_cnf.set_cnf_key("callback", callback)
    #
    #     run_cnf.set_cnf_key("callback_adapter", callback_adapter)
    #
    # def execute_tasklist(self, vars=None, context=None, run_config=None, is_sub_task=False):
    #
    #     if vars is None:
    #         vars = {}
    #
    #     if run_config is not None:
    #         run_cnf = run_config.run_cnf
    #     else:
    #         # TODO: default config
    #         run_cnf = Cnf()
    #         raise Exception("No run config provided")
    #
    #     if run_config.get_config_value("callback_adapter", None) is None:
    #         self.create_callback_adapter(run_cnf)
    #
    #     callback_adapter = context.get_config_value("callback_adapter")
    #
    #     results = OrderedDict()
    #     result_callback = FrecklesResultCallback()
    #
    #     try:
    #         # validated = self.frecklet.get_parameters().validate(vars)
    #
    #         tasklists = self.process_tasklist(vars=vars)
    #
    #         for tasklist_id, tasklist_item in tasklists.items():
    #
    #             connector = tasklist_item["connector"]
    #             tasklist = tasklist_item["task_list"]
    #
    #             replaced = []
    #             for task in tasklist:
    #                 task.pop("arg_tree")
    #                 input = task["input"]
    #                 input["omit"] = OMIT_VALUE
    #
    #                 r = replace_strings_in_obj(
    #                     task, input, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
    #                 )
    #                 r = remove_omit_values(r)
    #                 replaced.append(r)
    #
    #             connector_obj = self.context.get_connector(connector)
    #
    #             if "elevated" not in run_cnf.config_dict.keys():
    #                 elevated = needs_elevated_permissions(tasklist)
    #                 context.set_config_value("elevated", elevated)
    #
    #             if callback_adapter is not None:
    #                 callback_adapter.set_tasklist(replaced)
    #                 callback_adapter.set_cnf(run_cnf)
    #                 callback_adapter.set_connector(connector)
    #                 callback_adapter.set_run_name(self.name)
    #
    #             # filter disabled tasks
    #             final = []
    #             for t in replaced:
    #                 # import sys, pp
    #                 # pp(replaced)
    #                 # sys.exit()
    #                 if not is_disabled(t[FRECKLET_NAME]):
    #                     final.append(t)
    #                 else:
    #                     log.debug("Skipping task: {}".format(t))
    #
    #             connector_config = run_cnf.get_validated_cnf(connector)
    #             if callback_adapter is not None:
    #                 if not is_sub_task:
    #                     callback_adapter.execution_started(final, connector, run_cnf)
    #                 # else:
    #                 #     task_details = {
    #                 #         "name": "{}_{}".format(self.name, tasklist_id)
    #                 #     }
    #                 #     callback_adapter.task_started(task_details)
    #
    #             run_properties = connector_obj.run(
    #                 final,
    #                 config=connector_config,
    #                 result_callback=result_callback,
    #                 output_callback=callback_adapter,
    #             )
    #
    #             if callback_adapter is not None:
    #                 if not is_sub_task:
    #                     callback_adapter.execution_finished()
    #                 # else:
    #                 #     callback_adapter.task_finished(True, {})
    #
    #             results[tasklist_id] = {
    #                 "run_properties": run_properties,
    #                 "task_list": final,
    #                 "result": result_callback.result,
    #                 "connector": connector,
    #                 "name": self.name,
    #             }
    #
    #     finally:
    #         if not is_sub_task:
    #             if callback_adapter is not None:
    #                 callback_adapter.finish_up()
    #             if result_callback is not None:
    #                 result_callback.finish_up()
    #
    #     return results
