import copy
import logging
import os
from collections import OrderedDict

import click
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from treelib import Tree

from freckles.defaults import FRECKLET_KEY_NAME, VARS_KEY, TASK_KEY_NAME, DEFAULT_FRECKLES_JINJA_ENV, \
    FRECKLES_DEFAULT_ARG_SCHEMA
from freckles.exceptions import FrecklesVarException
from freckles.output_callback import DefaultCallback, TaskDetail, FrecklesRun, FrecklesResultCallback
from frutils import replace_strings_in_obj, get_template_keys
from frutils.frutils_cli import output
from frutils.parameters import FrutilsNormalizer

log = logging.getLogger("freckles")

class FrecklecutableMixin(object):

    def __init__(self, *args, **kwargs):
        pass

    def create_frecklecutable(self, context):
        return Frecklecutable(frecklet=self, context=context)

def is_duplicate_task(new_task, idempotency_cache):

        if not new_task[FRECKLET_KEY_NAME].get("idempotent", False):
            return False

        temp  = {}
        temp[FRECKLET_KEY_NAME] = copy.copy(new_task[FRECKLET_KEY_NAME])
        temp[FRECKLET_KEY_NAME].pop("msg", None)
        temp[FRECKLET_KEY_NAME].pop("desc", None)
        temp[FRECKLET_KEY_NAME].pop("skip", None)

        temp[TASK_KEY_NAME] = copy.copy(new_task[TASK_KEY_NAME])
        temp[VARS_KEY] = copy.copy(new_task[VARS_KEY])

        if temp in idempotency_cache:
            return True
        else:
            idempotency_cache.append(temp)
            return False

def remove_none_values(input, args=None, convert_empty_to_none=False):

    if isinstance(input, (list, tuple, set, CommentedSeq)):
        result = []
        for item in input:
            temp = remove_none_values(item, convert_empty_to_none=convert_empty_to_none)
            if temp:
                result.append(temp)
        return result
    elif isinstance(input, (dict, OrderedDict, CommentedMap)):
        result = CommentedMap()
        for k, v in input.items():
            if v is not None:
                temp = remove_none_values(v, convert_empty_to_none=convert_empty_to_none)
                if not temp:
                    if convert_empty_to_none:
                        temp = None
                        result[k] = temp
                else:
                    result[k] = temp

        return result
    else:
        return input


class Frecklecutable(object):

    def __init__(self, frecklet, context):

        self._frecklet = frecklet
        self._context = context

    @property
    def frecklet(self):
        return self._frecklet

    @property
    def context(self):
        return self._context

    def _retrieve_var_value_from_inventory(self, inventory, var_value, template_keys=None):
        """Retrieves all template keys contained in a value from the inventory.

        Args:
            var_value: the value of a var
        Returns:
            dict: a dict with keyname/inventory_value pairs
        """

        if template_keys is None:
            template_keys = get_template_keys(var_value, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)


        if not template_keys:
            return {}

        result = {}
        for tk in template_keys:
            val = inventory.retrieve_value(tk)
            result[tk] = val

        return result

    def _replace_templated_var_value(self, var_value, repl_dict=None, inventory=None):
        """Replace a templated (or not) var value using a replacement dict or the inventory.

        Args:
            var_value: the value of a var
            repl_dict: the key/value pairs to use for the templating
        Returns:
            The processed object.
        """

        if repl_dict is None:
            repl_dict = self._retrieve_var_value_from_inventory(inventory=inventory, var_value=var_value)

        processed = replace_strings_in_obj(var_value, replacement_dict=repl_dict, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
        return processed

    def _generate_schema(self, var_value_map, args, template_keys=None):

        if template_keys is None:

            template_keys = get_template_keys(var_value_map, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)

        schema = {}
        for key in template_keys:
            schema[key] = copy.copy(args.get(key, FRECKLES_DEFAULT_ARG_SCHEMA))
            schema[key].pop("doc", None)
            schema[key].pop("cli", None)

        return schema

    def _validate_processed_vars(self, var_value_map, schema, allow_unknown=False, purge_unknown=True, task_path=None, vars_pre_clean=None, task=None):

        validator = FrutilsNormalizer(schema, purge_unknown=purge_unknown, allow_unknown=allow_unknown)
        valid = validator.validated(var_value_map)
        if valid is None:
            if vars_pre_clean is None:
                vars_pre_clean = var_value_map
            raise FrecklesVarException(self.frecklet, error=validator.errors, task_path=task_path, vars=vars_pre_clean, task=task)
        return valid

    def process_tasks(self, inventory):
        """Calculates the tasklist for a given inventory."""

        processed_tree = self._calculate_task_plan(inventory=inventory)

        task_nodes = processed_tree.leaves()
        result = []
        task_id = 0
        for t in task_nodes:

            if t.data["processed"][FRECKLET_KEY_NAME].get("skip", False):
                continue

            task = t.data["processed"]
            task[FRECKLET_KEY_NAME]["_task_id"] = task_id
            task_id = task_id + 1
            # vars = t.data["args"]
            # print(vars)
            # output(task, output_type="yaml")
            result.append(task)

        return result

    def _calculate_task_plan(self, inventory):

        task_tree = self.frecklet.task_tree
        processed_tree = Tree()

        root_frecklet = task_tree.get_node(0)

        task_path = []

        for tn in task_tree.all_nodes():

            task_id = tn.identifier
            if task_id == 0:

                processed_tree.create_node(identifier=0, tag=task_tree.get_node(0).tag, data={"frecklet": root_frecklet.data, "inventory": inventory})

                continue


            task_node = tn.data["task"]

            task_name = task_node[FRECKLET_KEY_NAME]["name"]

            args = task_tree.get_node(task_id).data["root_frecklet"].args
            parent_id = task_tree.parent(task_id).identifier
            if parent_id == 0:
                parent = {}
                template_keys = task_tree.get_node(0).data.template_keys
                repl_vars = {}
                for tk in template_keys:
                    v = inventory.retrieve_value(tk)
                    if v is not None:
                        repl_vars[tk] = v
                task_path = []
            else:
                parent = processed_tree.get_node(parent_id).data
                repl_vars = parent["processed"].get("vars", {})

            # level = task_tree.level(task_id)
            # padding = "    " * level
            # print("{}vars:".format(padding))
            # print(readable(repl_vars, out="yaml", indent=(level*4)+4).rstrip())
            # print("{}task:".format(padding))
            # print("{}    name: {}".format(padding, task_name))

            if parent.get("processed", {}).get(FRECKLET_KEY_NAME, {}).get("skip", False):
                processed_tree.create_node(identifier=task_id, tag=task_tree.get_node(task_id).tag,
                                           data={"frecklet": root_frecklet.data, "inventory": inventory, "processed_vars": {},
                                                 "processed": {FRECKLET_KEY_NAME: {"skip": True}}}, parent=parent_id)
                continue

            # output(task_node, output_type="yaml")
            vars = copy.copy(task_node.get(VARS_KEY, {}))
            frecklet = copy.copy(task_node[FRECKLET_KEY_NAME])
            task = copy.copy(task_node.get(TASK_KEY_NAME, {}))


            skip = frecklet.get("skip", None)


            # print('=======================')
            # print("FRECKLET")
            # output(frecklet, output_type="yaml")
            # output(task, output_type="yaml")
            # output(vars, output_type="yaml")
            # print("PARENT")
            # import pp
            # pp(parent)
            # print("REPL")
            # pp(repl_vars)
            # print('---------------------------')

            # first we get our target variable, as this will most likley determine the value of the var later on
            target = frecklet.get("target", None)
            if target is not None:
                template_keys = get_template_keys(target, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
                if template_keys:
                    target_value = self._replace_templated_var_value(var_value=target, repl_dict=repl_vars,
                                                                 inventory=inventory)
                else:
                    target_value = target
                # TODO: 'resolve' target
                # TODO: validate target schema
                frecklet["target"] = target_value

            # then we check if we can skip the task. For that we already need the target variable ready, as it might
            # be used for variable selection
            if skip is not None:
                skip_value = self._replace_templated_var_value(var_value=skip, repl_dict=repl_vars, inventory=inventory)
                frecklet["skip"] = skip_value
                if isinstance(skip_value, bool) and skip_value:
                    processed_tree.create_node(identifier=task_id, tag=task_tree.get_node(task_id).tag,
                                               data={"frecklet": root_frecklet.data, "inventory": inventory, "processed_vars": {},
                                                     "processed": {FRECKLET_KEY_NAME: {"skip": True}}}, parent=parent_id)

                    # print("SKIPPPPED")
                    continue


            # now we replace the whole rest of the task



            # if not task_tree.get_node(task_id).is_leaf():
            #     print("NOT LEAF")
            #     print(vars)
            #     vars_processed = self._replace_templated_var_value(var_value=vars, repl_dict=repl_vars,
            #                                                        inventory=inventory)
            #     vars_processed_cleaned = remove_none_values(vars_processed, args=args)
            #     schema = self._generate_schema(var_value_map=vars, args=args, template_keys=None)
            #
            #     validated = self._validate_processed_vars(var_value_map=vars_processed_cleaned, schema=schema,
            #                                                   task_path=task_path, vars_pre_clean=vars_processed,
            #                                                   task=task_node)
            #
            #
            #     processed = {
            #         FRECKLET_KEY_NAME: frecklet,
            #         TASK_KEY_NAME: task
            #     }
            #     processed = self._replace_templated_var_value(var_value=processed, repl_dict=repl_vars,
            #                                                   inventory=inventory)
            #     processed = remove_none_values(processed, convert_empty_to_none=False)
            #     processed[VARS_KEY] = validated
            #
            #     processed_tree.create_node(identifier=task_id, tag=task_tree.get_node(task_id).tag,
            #                                data={"frecklet": root_frecklet.data, "inventory": inventory,
            #                                      "processed": processed}, parent=parent_id)
            # else:

            task = {
                FRECKLET_KEY_NAME: frecklet,
                TASK_KEY_NAME: task,
                VARS_KEY: vars
            }


            template_keys = get_template_keys(task, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
            schema = self._generate_schema(var_value_map=task, args=args, template_keys=template_keys)
            val_map = {}
            for tk in template_keys:
                val = repl_vars.get(tk, None)
                if val is not None:
                    val_map[tk] = val

            validated_val_map = self._validate_processed_vars(var_value_map=val_map, schema=schema, task_path=task_path, vars_pre_clean=repl_vars, task=task_node)

            task_processed = self._replace_templated_var_value(var_value=task, repl_dict=validated_val_map,
                                                               inventory=inventory)
            task_processed = remove_none_values(task_processed, args=args)


            processed_tree.create_node(identifier=task_id, tag=task_tree.get_node(task_id).tag,
                                       data={"frecklet": root_frecklet.data, "inventory": inventory,
                                             "processed": task_processed}, parent=parent_id)

        return processed_tree


    def run(self, inventory, run_config, run_vars):

        frecklet_name = self.frecklet.id
        log.debug("Running frecklecutable: {}".format(frecklet_name))

        tasks = self.process_tasks(inventory=inventory)

        current_tasklist = []
        idempotent_cache = []
        current_adapter = None

        for task in tasks:
            tt = task[FRECKLET_KEY_NAME]["type"]

            adapter = self.context._adapter_tasktype_map.get(tt, None)

            if adapter is None:
                raise Exception("No adapter registered for task type: {}".format(tt))
            if len(adapter) > 1:
                raise Exception("Multiple adapters registered for task type '{}', that is not supported yet.".format(tt))

            adapter = adapter[0]

            if current_adapter is None:
                current_adapter = adapter

            if current_adapter != adapter:
                raise Exception("Multiple adapters for a single frecklet, this is not supported yet: {} / {}".format(current_adapter, adapter))

            if is_duplicate_task(task, idempotent_cache):
                log.debug("Idempotent, duplicate task, ignoring: {}".format(task[FRECKLET_KEY_NAME]["name"]))
                continue
            current_tasklist.append(task)

        adapter = self.context._adapters[current_adapter]

        callback = DefaultCallback()
        result_callback = FrecklesResultCallback()
        parent_task = TaskDetail(frecklet_name, "run", task_parent=None)
        callback.task_started(parent_task)
        task_details = TaskDetail(
                    task_name=frecklet_name,
                    task_type="frecklecutable",
                    task_parent=parent_task,
                )
        callback.task_started(task_details)

        secure_vars = {}

        try:
            run_properties = adapter.run(tasklist=current_tasklist, run_vars=run_vars, run_config=run_config, secure_vars=secure_vars, output_callback=callback, result_callback=result_callback, parent_task=task_details)

            callback.task_finished(task_details, success=True)
            callback.task_finished(parent_task, success=True)

            result = {
                    "run_properties": run_properties,
                    "task_list": current_tasklist,
                    "result": result_callback.result,
                    "adapter": adapter,
                    "name": frecklet_name,
                }

            run_result = FrecklesRun(0, result)
            return run_result

        except (Exception) as e:
            click.echo("frecklecutable run failed: {}".format(e))
            log.debug(e)

