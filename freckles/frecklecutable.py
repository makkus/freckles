# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import copy
import logging
import os
from collections import OrderedDict

from ruamel.yaml.comments import CommentedSeq, CommentedMap

from frutils import get_template_keys, replace_strings_in_obj
from .context import FrecklesContext
from .defaults import FRECKLET_NAME, TASK_INSTANCE_NAME, DEFAULT_FRECKLES_JINJA_ENV
from .exceptions import FrecklesConfigException

log = logging.getLogger("freckles")


def get_task_hierarchy(root_tasks, used_ids, task_map, context, level=0, minimal=False):

    result = []

    for id, childs in root_tasks.items():

        info = assemble_info(task_map[id], context=context)
        # f_name = task_map[id]["frecklet"]["command"]
        # f_type = task_map[id]["frecklet"]["type"]
        # if f_type == "frecklet":
        #     md = context.get_frecklet_metadata(f_name)
        #     doc = md["doc"]
        # else:
        #     f = task_map[id]["frecklet"]
        #     v = task_map[id].get("vars", {})
        #     t_dict = {"frecklet": f}
        #     if v:
        #         t_dict["vars"] = v
        #     doc = readable(t_dict, out="yaml", ignore_aliases=True)

        if childs:
            temp_childs = get_task_hierarchy(
                childs,
                used_ids=used_ids,
                task_map=task_map,
                context=context,
                level=level + 1,
                minimal=minimal,
            )

            if not temp_childs:
                continue

            d = {"children": temp_childs, "level": level, "info": info}
            if minimal:
                d["child"] = task_map[id]["frecklet"]["command"]
            else:
                d["child"] = task_map[id]
            result.append(d)
        else:
            if id not in used_ids:
                continue
            d = {"children": [], "level": level, "info": info}
            if minimal:
                d["child"] = task_map[id]["frecklet"]["command"]
            else:
                d["child"] = task_map[id]
            result.append(d)

    return result


def assemble_info(task, context):

    command = task[FRECKLET_NAME]["command"]
    f_name = command
    f_type = task[FRECKLET_NAME]["type"]

    msg = task.get("task", {}).get("msg", None)
    if msg and msg.startswith("[") and msg.endswith("]"):
        msg = msg[1:-1].strip()

    desc = task.get("task", {}).get("desc", None)

    if f_type == "frecklet":

        try:
            md = context.get_frecklet_metadata(f_name)
            doc = md.get("doc", None)
        except (FrecklesConfigException):
            pass
    else:
        doc = None

    return {
        "command": command,
        "frecklet_name": f_name,
        "doc": doc,
        "frecklet_type": f_type,
        "msg": msg,
        "desc": desc,
    }


def clean_omit_values(d, non_value_keys):

    if isinstance(d, (list, tuple, CommentedSeq)):

        for item in d:
            clean_omit_values(item, non_value_keys=non_value_keys)

    elif isinstance(d, (dict, OrderedDict, CommentedMap)):

        for key in list(d):
            val = d[key]
            if isinstance(val, (dict, OrderedDict, CommentedMap, list, tuple)):
                clean_omit_values(val, non_value_keys=non_value_keys)
            else:
                t_keys = get_template_keys(val, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
                if len(t_keys) == 1:
                    t = list(t_keys)[0]
                    if t in non_value_keys:
                        del d[key]


def remove_none_values(input):

    if isinstance(input, (list, tuple, set, CommentedSeq)):
        result = []
        for item in input:
            temp = remove_none_values(item)
            result.append(temp)
        return result
    elif isinstance(input, (dict, OrderedDict, CommentedMap)):
        result = CommentedMap()
        for k, v in input.items():
            if v is not None:
                temp = remove_none_values(v)
                result[k] = temp
        return result
    else:
        return input


def is_disabled(task):

    skip = task.get(TASK_INSTANCE_NAME, {}).get("skip", [])

    # print("---")
    # print(task["meta"]["__name__"])
    # print(skip)

    for s in skip:

        if s is True:
            return True

    return False


def cleanup_tasklist(tasklist):

    replaced = []
    for task in tasklist:
        input = copy.copy(task["input"])

        none_value_keys = []

        for k, v in input.items():
            if v is None:
                none_value_keys.append(k)

        input_clean = remove_none_values(copy.deepcopy(input))

        clean_omit_values(task[FRECKLET_NAME], none_value_keys)
        clean_omit_values(task["vars"], none_value_keys)

        r = replace_strings_in_obj(
            task, input_clean, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
        )

        # also remove None values after filters were applied
        r = remove_none_values(r)

        replaced.append(r)

    # filter disabled tasks
    final = []
    for t in replaced:
        # import sys, pp
        # pp(replaced)
        # sys.exit()
        if is_disabled(t):
            log.debug("Skipping task: {}".format(t))
            continue

        final.append(t)

    # final = remove_idempotent_duplicates(final)

    return final


def remove_idempotent_duplicates(tasklist):

    temp = []
    compare_list = []
    for t in tasklist:

        idempotent = t.get(TASK_INSTANCE_NAME, {}).get("idempotent", False)
        if not idempotent:
            temp.append(t)
            continue

        tf = copy.copy(t[FRECKLET_NAME])
        tf.pop("_task_id", None)
        tf.pop("_task_list_id", None)
        control = copy.copy(t.get(TASK_INSTANCE_NAME, {}))

        control.pop("skip", None)

        t_compare = {FRECKLET_NAME: tf, TASK_INSTANCE_NAME: control, "vars": t["vars"]}

        if t_compare in compare_list:
            import pp

            pp(t_compare.keys())
            # sys.exit()
            continue

        compare_list.append(t_compare)
        temp.append(t)
    return temp


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
            context = FrecklesContext.create_context()

        name = os.path.splitext(os.path.basename(frecklet_path_or_name))[0]
        frecklet = context.create_frecklet(frecklet_path_or_name)

        return Frecklecutable(name, frecklet, vars=vars, context=context)

    def __init__(self, name, frecklet, vars=None, context=None):

        self.name = name

        if context is None:
            context = FrecklesContext.create_context()

        self.context = context
        if vars is None:
            vars = {}

        # for k, v in frecklet.args.items():
        #     v.setdefault("__meta__", {})["root_frecklet"] = True
        self.frecklet = frecklet

        # self.tasklist_cache = {}  # not used currently
        self.tasklist_cache_no_user_input = None
        self.task_hierarchy = None

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

    def get_task_hierarchy(self, vars=None, minimal=False):
        """
        Get the task hierarchy for the frecklet.

        If vars is None, the 'pure' frecklet tasklist will be used. Otherwise the tasklist will be rendered with the provided
        user input (or the empty dict).

        Args:
            vars: the (empty or non-empty) user_input, or None

        Returns:
            dict: the task hierarchy
        """

        if vars is None:
            if self.task_hierarchy:
                return self.task_hierarchy

        process = True
        if vars is None:
            process = False

        tasklists = self.process_tasklist(vars, process_user_input=process)

        result = []
        for tl_id, tasklist_details in tasklists.items():

            ids = []

            if vars is not None:
                # we replace the task items with the rendered one
                task_map = copy.deepcopy(self.frecklet.get_task_map())
            else:
                task_map = self.frecklet.get_task_map()

            for t in tasklist_details["task_list"]:
                id = t["meta"]["__id__"]
                ids.append(id)
                if vars is not None:
                    task_map[id] = t

            task_hierarchy = get_task_hierarchy(
                self.frecklet.get_task_tree(),
                used_ids=ids,
                task_map=task_map,
                context=self.context,
                minimal=minimal,
            )
            result.append(
                {"id": tl_id, "hierarchy": task_hierarchy, "details": tasklist_details}
            )

        if vars is None:
            self.task_hierarchy = result

        return result

    def process_tasklist(self, vars=None, process_user_input=True):
        """
        Processes a tasklist.

        You can choose to not process user input, in case this is run for documentation generation purposes.

        Args:
            vars: the user input
            process_user_input: whether to process user input

        Returns:
            list: a list of processed task-lists
        """

        # frecklet = copy.deepcopy(self.frecklet)
        # for k, v in frecklet.args.items():
        #     v.setdefault("__meta__", {})["root_frecklet"] = True
        #     frecklet.meta["__frecklet_level__"] = 0

        if process_user_input:
            tl = None
        else:
            tl = self.tasklist_cache_no_user_input

        if tl is None:
            tl = self.frecklet.render_tasklist(
                vars, process_user_input=process_user_input
            )
            if not process_user_input:
                self.tasklist_cache_no_user_input = tl

        remove_skipped = False
        if remove_skipped:
            temp = []
            for t in tl:
                skip = t.get(TASK_INSTANCE_NAME, {}).get("skip", False)
                if isinstance(skip, bool) and skip:
                    continue

                temp.append(t)
            tl = temp

        # this doesn't work properly yet
        remove_idempotent = False
        # if user input is not processed, we can't know which tasks are the same
        # because vars have not been resolved
        if process_user_input and remove_idempotent:
            temp = []
            compare_list = []
            for t in tl:
                idempotent = t.get(TASK_INSTANCE_NAME, {}).get("idempotent", False)
                if not idempotent:
                    temp.append(t)
                    continue

                tf = copy.copy(t[FRECKLET_NAME])
                tf.pop("_task_id", None)
                tf.pop("_task_list_id", None)
                control = copy.copy(t.get(TASK_INSTANCE_NAME, {}))

                if not process_user_input:
                    # we can't know whether it'll be skipped or not, but in either case we only need the first time
                    control.pop("skip", None)

                t_compare = {
                    FRECKLET_NAME: tf,
                    TASK_INSTANCE_NAME: control,
                    "vars": t["vars"],
                }

                if t_compare in compare_list:
                    continue

                compare_list.append(t_compare)
                temp.append(t)

            tl = temp

        unknowns = []
        for item in tl:
            task_type = item[FRECKLET_NAME].get("type", "unknown")
            if task_type == "unknown":
                unknowns.append(item[FRECKLET_NAME]["name"])

        if unknowns:
            raise FrecklesConfigException(
                "One or more task items with unknown task type: {}".format(unknowns)
            )

        current_adapter = None
        task_lists = OrderedDict()
        current_task_list = []
        task_list_index = 0
        for index, task in enumerate(tl):

            task[FRECKLET_NAME]["_task_id"] = index

            task_type = task[FRECKLET_NAME]["type"]
            adapter_task = self.context.adapter_map.get(task_type, None)
            if adapter_task is None:
                raise FrecklesConfigException(
                    "No adapter for task type '{}': {}".format(task_type, task)
                )

            if current_adapter is None:
                current_adapter = adapter_task

            if current_adapter != adapter_task:
                # new frecklecutable run
                for t in current_task_list:
                    t[FRECKLET_NAME]["_task_list_id"] = task_list_index
                task_lists[task_list_index] = {
                    "task_list": current_task_list,
                    "adapter": current_adapter,
                    "name": self.name,
                }
                current_adapter = adapter_task
                current_task_list = []
                task_list_index = task_list_index + 1

            current_task_list.append(task)

        if current_task_list:
            for t in current_task_list:
                t[FRECKLET_NAME]["_task_list_id"] = task_list_index
            task_lists[task_list_index] = {
                "task_list": current_task_list,
                "adapter": current_adapter,
                "name": self.name,
            }

        if process_user_input:
            for tl_id, details in task_lists.items():
                t = cleanup_tasklist(details["task_list"])
                details["task_list"] = t

        return task_lists
