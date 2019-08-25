# -*- coding: utf-8 -*-
import copy
import csv
import io
import logging
import os
import shutil
import threading
import time
from collections import OrderedDict, Mapping

import click
from fasteners import interprocess_locked
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from six import string_types
from treelib import Tree

from frutils.tasks.callback import load_callback
from .frecklet.vars import (
    VarsInventory,
    is_var_adapter,
    get_resolved_var_adapter_object,
)
from .context.run_config import FrecklesRunConfig
from frutils import (
    replace_strings_in_obj,
    get_template_keys,
    can_passwordless_sudo,
    dict_merge,
    special_dict_to_dict,
)
from frutils.exceptions import FrklException
from frutils.tasks.tasks import Tasks
from ting.defaults import TingValidator
from .defaults import (
    FRECKLET_KEY_NAME,
    VARS_KEY,
    TASK_KEY_NAME,
    DEFAULT_FRECKLES_JINJA_ENV,
    FRECKLES_DESC_METADATA_KEY,
    FRECKLES_PROPERTIES_METADATA_KEY,
    FRECKLES_PROPERTIES_IDEMPOTENT_METADATA_KEY,
    FRECKLES_PROPERTIES_ELEVATED_METADATA_KEY,
    DEFAULT_RUN_CONFIG_JINJA_ENV,
    FRECKLES_RUN_LOG_FILE_LOCK,
    FRECKLES_RUN_LOG_FILE_PATH,
    FRECKLES_LAST_RUN_FILE_PATH,
)
from .exceptions import FrecklesVarException
from .output_callback import FrecklesRun, FrecklesResultCallback

log = logging.getLogger("freckles")

run_log_lock = threading.Lock()


def ask_password(prompt):

    pw = click.prompt(prompt, type=str, hide_input=True)
    return pw


class FrecklecutableMixin(object):
    def __init__(self, *args, **kwargs):
        pass

    def create_frecklecutable(self, context):
        return Frecklecutable(frecklet=self, context=context)


def is_duplicate_task(new_task, idempotency_cache):

    if (
        not new_task[FRECKLET_KEY_NAME]
        .get(FRECKLES_PROPERTIES_METADATA_KEY, {})
        .get(FRECKLES_PROPERTIES_IDEMPOTENT_METADATA_KEY, False)
    ):
        return False

    temp = {}
    temp[FRECKLET_KEY_NAME] = copy.copy(new_task[FRECKLET_KEY_NAME])
    temp[FRECKLET_KEY_NAME].pop(FRECKLES_DESC_METADATA_KEY, None)
    temp[FRECKLET_KEY_NAME].pop(FRECKLES_PROPERTIES_METADATA_KEY, None)
    temp[FRECKLET_KEY_NAME].pop("skip", None)

    temp[TASK_KEY_NAME] = copy.copy(new_task[TASK_KEY_NAME])
    temp[VARS_KEY] = copy.copy(new_task[VARS_KEY])

    if temp in idempotency_cache:
        return True
    else:
        idempotency_cache.append(temp)
        return False


def remove_none_values(input):

    if isinstance(input, (list, tuple, set, CommentedSeq)):
        result = []
        for item in input:
            temp = remove_none_values(item)
            if temp is not None and temp != "":
                result.append(temp)
        return result
    elif isinstance(input, (dict, OrderedDict, CommentedMap)):
        result = CommentedMap()
        for k, v in input.items():
            if v is not None:
                temp = remove_none_values(v)
                if temp is not None and temp != "":
                    result[k] = temp

        return result
    else:
        return input


def set_run_defaults(inventory=None, run_config=None, run_vars=None):

    if inventory is None:
        inventory = VarsInventory()

    if isinstance(inventory, Mapping):
        inventory = VarsInventory(vars=inventory)

    if run_config is None:
        run_config = FrecklesRunConfig()

    if isinstance(run_config, string_types):
        run_config = FrecklesRunConfig(target_string=run_config)

    if isinstance(run_config, FrecklesRunConfig):
        run_config = run_config.config

    default_run_config = {"host": "localhost"}
    run_config = dict_merge(default_run_config, run_config, copy_dct=False)

    if run_vars is None:
        run_vars = {}

    return inventory, run_config, run_vars


class Frecklecutable(object):
    def __init__(self, frecklet, context):

        self._frecklet = frecklet
        self._context = context
        self._callbacks = context.callbacks

    @property
    def frecklet(self):
        return self._frecklet

    @property
    def context(self):
        return self._context

    def _retrieve_var_value_from_inventory(
        self, inventory, var_value, template_keys=None
    ):
        """Retrieves all template keys contained in a value from the inventory.

        Args:
            var_value: the value of a var
        Returns:
            dict: a dict with keyname/inventory_value pairs
        """

        if template_keys is None:
            template_keys = get_template_keys(
                var_value, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
            )

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
            repl_dict = self._retrieve_var_value_from_inventory(
                inventory=inventory, var_value=var_value
            )

        processed = replace_strings_in_obj(
            var_value, replacement_dict=repl_dict, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
        )
        return processed

    def _generate_schema(self, var_value_map, args, const_args, template_keys=None):

        if template_keys is None:

            template_keys = get_template_keys(
                var_value_map, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
            )

        schema = {}
        secret_keys = set()

        for key in template_keys:

            arg_obj = const_args.get(key, None)
            if arg_obj is None:
                arg_obj = args[key]

            schema[key] = copy.copy(arg_obj.schema)
            # schema[key].pop("doc", None)
            # schema[key].pop("cli", None)
            secret = arg_obj.secret
            if secret is True:
                secret_keys.add(key)

        return schema, secret_keys

    def _validate_processed_vars(
        self,
        var_value_map,
        schema,
        allow_unknown=False,
        purge_unknown=True,
        task_path=None,
        vars_pre_clean=None,
        task=None,
    ):
        _schema = copy.deepcopy(schema)
        _var_value_map = copy.deepcopy(var_value_map)

        _schema = special_dict_to_dict(schema)
        _var_value_map = special_dict_to_dict(_var_value_map)
        validator = TingValidator(
            _schema, purge_unknown=purge_unknown, allow_unknown=allow_unknown
        )

        valid = validator.validated(_var_value_map)

        if valid is None:
            if vars_pre_clean is None:
                vars_pre_clean = var_value_map
            raise FrecklesVarException(
                frecklet=self.frecklet,
                errors=validator.errors,
                task_path=task_path,
                vars=vars_pre_clean,
                task=task,
            )
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

            result.append(task)

        return result

    def _calculate_task_plan(self, inventory):

        task_tree = self.frecklet.task_tree

        processed_tree = Tree()

        root_frecklet = task_tree.get_node(0)

        task_path = []

        const_cache = {}
        for tn in task_tree.all_nodes():

            task_id = tn.identifier

            if task_id == 0:

                processed_tree.create_node(
                    identifier=0,
                    tag=task_tree.get_node(0).tag,
                    data={"frecklet": root_frecklet.data, "inventory": inventory},
                )

                continue

            task_node = tn.data["task"]

            root_vars = task_tree.get_node(task_id).data["root_frecklet"].vars_frecklet
            const_vars = task_tree.get_node(task_id).data["root_frecklet"].vars_const
            const = task_tree.get_node(task_id).data["root_frecklet"].const

            parent_id = task_tree.parent(task_id).identifier
            task_level = task_tree.level(task_id)
            root_frecklet_id = task_tree.get_node(task_id).data["root_frecklet"].id

            if parent_id == 0:

                parent = {}
                # template_keys = task_tree.get_node(0).data.template_keys
                repl_vars = {}
                # import pp
                # print("INV")
                # pp(inventory.get_vars())
                for k, v in inventory.get_vars(hide_secrets=False).items():
                    repl_vars[k] = v
                # for tk in template_keys:
                #     v = inventory.retrieve_value(tk)
                #     if v is not None:
                #         repl_vars[tk] = v
                task_path = []
                parent_secret_keys = set()
                parent_desc = {}
            else:
                parent = processed_tree.get_node(parent_id).data
                repl_vars = parent["processed"].get("vars", {})

                parent_secret_keys = parent["processed"][FRECKLET_KEY_NAME].get(
                    "secret_vars", set()
                )
                parent_desc = parent["processed"][FRECKLET_KEY_NAME].get(
                    FRECKLES_DESC_METADATA_KEY, {}
                )

            if (
                parent.get("processed", {})
                .get(FRECKLET_KEY_NAME, {})
                .get("skip", False)
            ):
                processed_tree.create_node(
                    identifier=task_id,
                    tag=task_tree.get_node(task_id).tag,
                    data={
                        "frecklet": root_frecklet.data,
                        "inventory": inventory,
                        "processed_vars": {},
                        "processed": {FRECKLET_KEY_NAME: {"skip": True}},
                    },
                    parent=parent_id,
                )
                continue

            if parent_id > 0:

                if is_var_adapter(const):
                    if (
                        const_cache.get(task_level, {}).get(root_frecklet_id, None)
                        is not None
                    ):
                        const = const_cache[task_level][root_frecklet_id]
                    else:
                        resolved_const = {}
                        for k, v in const.items():
                            if is_var_adapter(v):
                                arg = const_vars.get(k, None)
                                if arg is None:
                                    arg = root_vars[k]
                                new_value, is_sec, changed = get_resolved_var_adapter_object(
                                    value=v,
                                    key=k,
                                    arg=arg,
                                    frecklet=self.frecklet,
                                    is_secret=arg.secret,
                                    inventory=None,
                                )
                                v = new_value
                            resolved_const[k] = v
                            const_cache.setdefault(task_level, {})[
                                root_frecklet_id
                            ] = resolved_const
                        const = resolved_const

                for k, v in const.items():

                    tks = get_template_keys(v, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
                    if tks:
                        v = replace_strings_in_obj(
                            v,
                            replacement_dict=repl_vars,
                            jinja_env=DEFAULT_FRECKLES_JINJA_ENV,
                        )
                    repl_vars[k] = v

            for k, v in repl_vars.items():
                if is_var_adapter(v):
                    arg = const_vars.get(k, None)
                    if arg is None:
                        arg = root_vars[k]
                    new_value, is_sec, changed = get_resolved_var_adapter_object(
                        value=v,
                        key=k,
                        arg=arg,
                        root_arg=True,
                        frecklet=self.frecklet,
                        is_secret=arg.secret,
                        inventory=inventory,
                    )
                    repl_vars[k] = new_value

            # output(task_node, output_type="yaml")
            vars = copy.copy(task_node.get(VARS_KEY, {}))
            frecklet = copy.copy(task_node[FRECKLET_KEY_NAME])
            task = copy.copy(task_node.get(TASK_KEY_NAME, {}))

            target = frecklet.get("target", None)

            # first we get our target variable, as this will most likely determine the value of the var later on

            if target is not None:
                template_keys = get_template_keys(
                    target, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
                )

                if template_keys:
                    target_value = self._replace_templated_var_value(
                        var_value=target, repl_dict=repl_vars, inventory=inventory
                    )
                else:
                    target_value = target
                # TODO: 'resolve' target
                # TODO: validate target schema
                frecklet["target"] = target_value

            # then we check if we can skip the task. For that we already need the target variable ready, as it might
            # be used for variable selection
            skip = frecklet.get("skip", None)
            if skip is not None:
                # TODO: validate vars against schema
                skip_tks = get_template_keys(skip, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)

                skip_schema, _ = self._generate_schema(
                    var_value_map=task,
                    args=root_vars,
                    const_args=const_vars,
                    template_keys=skip_tks,
                )
                val_map = {}

                for tk in skip_tks:
                    val = repl_vars.get(tk, None)
                    if val is not None:
                        val_map[tk] = val

                for k, v in inventory.get_vars().items():
                    if k not in val_map.keys() and v is not None and v != "":
                        val_map[k] = v

                validated_val_map = self._validate_processed_vars(
                    var_value_map=val_map,
                    schema=skip_schema,
                    task_path=task_path,
                    vars_pre_clean=repl_vars,
                    task=task_node,
                )

                skip_value = self._replace_templated_var_value(
                    var_value=skip, repl_dict=validated_val_map, inventory=inventory
                )
                frecklet["skip"] = skip_value
                if isinstance(skip_value, bool) and skip_value:
                    processed_tree.create_node(
                        identifier=task_id,
                        tag=task_tree.get_node(task_id).tag,
                        data={
                            "frecklet": root_frecklet.data,
                            "inventory": inventory,
                            "processed_vars": {},
                            "processed": {FRECKLET_KEY_NAME: {"skip": True}},
                        },
                        parent=parent_id,
                    )

                    # print("SKIPPPPED")
                    continue

            # now we replace the whole rest of the task
            desc = frecklet.get(FRECKLES_DESC_METADATA_KEY, {})

            if parent_desc:
                spd = parent_desc.get("short", None)
                if spd:
                    desc["short"] = spd

                lpd = parent_desc.get("long", None)
                if lpd:
                    desc["long"] = lpd

            frecklet[FRECKLES_DESC_METADATA_KEY] = desc
            task = {FRECKLET_KEY_NAME: frecklet, TASK_KEY_NAME: task, VARS_KEY: vars}

            template_keys = get_template_keys(
                task, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
            )

            schema, secret_keys = self._generate_schema(
                var_value_map=task,
                args=root_vars,
                const_args=const_vars,
                template_keys=template_keys,
            )

            secret_keys.update(parent_secret_keys)
            val_map = {}

            for tk in template_keys:
                val = repl_vars.get(tk, None)
                if val is not None:
                    val_map[tk] = val

            for k, v in inventory.get_vars().items():
                if k not in val_map.keys() and v is not None and v != "":
                    val_map[k] = v

            # import pp
            # pp(tn.data["task"]["frecklet"]["name"])
            # pp(tn.data["task"]["frecklet"])

            validated_val_map = self._validate_processed_vars(
                var_value_map=val_map,
                schema=schema,
                task_path=task_path,
                vars_pre_clean=repl_vars,
                task=task_node,
            )

            new_secret_keys = set()
            for var_name, var in task.get(VARS_KEY, {}).items():

                tk = get_template_keys(var, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
                intersection = secret_keys.intersection(tk)
                if intersection:
                    new_secret_keys.add(var_name)

            task_processed = self._replace_templated_var_value(
                var_value=task, repl_dict=validated_val_map, inventory=inventory
            )
            task_processed = remove_none_values(task_processed)

            task_processed[FRECKLET_KEY_NAME]["secret_vars"] = list(new_secret_keys)

            processed_tree.create_node(
                identifier=task_id,
                tag=task_tree.get_node(task_id).tag,
                data={
                    "frecklet": root_frecklet.data,
                    "inventory": inventory,
                    "processed": task_processed,
                },
                parent=parent_id,
            )

        return processed_tree

    def check_become_pass(self, run_config, run_secrets, parent_task):

        if parent_task is not None:
            return

        if run_config.get("host", None) != "localhost":
            return

        if run_config.get("no_run", False):
            return

        if can_passwordless_sudo():
            return

        if run_secrets.get("become_pass", None) is not None:
            return

        msg = ""
        if run_config.get("user", None):
            msg = "{}@".format(run_config["user"])
        msg = msg + run_config.get("host", "localhost")
        prompt = "SUDO PASS (for '{}')".format(msg)
        run_secrets["become_pass"] = ask_password(prompt)

    def create_run_inventory(self, inventory=None, run_config=None, run_vars=None):

        inventory, run_config, run_vars = set_run_defaults(
            inventory=inventory, run_config=run_config, run_vars=run_vars
        )

        run_vars.setdefault("__freckles_run__", {})["pwd"] = os.path.realpath(
            os.getcwd()
        )

        secret_args = []

        for arg_name, arg in self.frecklet.vars_frecklet.items():

            if arg.secret:
                secret_args.append(arg_name)

        # paused = False
        # if parent_task is not None and (
        #     secret_args
        #     or run_config.get("become_pass", None) == "::ask::"
        #     or run_config.get("login_pass", None) == "::ask::"
        # ):
        #     # we need to pause our task callback because of user input
        #     parent_task.pause()
        #     paused = True

        run_inventory = VarsInventory()

        # process constants
        const_schema, sk = self._generate_schema(
            var_value_map=self.frecklet.const,
            args={},
            const_args=self.frecklet.vars_const,
        )

        new_vars = self._validate_processed_vars(
            var_value_map=inventory.get_vars(hide_secrets=False), schema=const_schema
        )

        consts_processed = self._replace_templated_var_value(
            var_value=copy.deepcopy(self.frecklet.const),
            repl_dict=new_vars,
            inventory=inventory,
        )

        inventory_secrets = inventory.secret_keys()

        for k, v in consts_processed.items():

            arg = self.frecklet.vars_const.get(k, None)
            if arg is None:
                arg = self.frecklet.vars_frecklet[k]

            secret = k in secret_args or k in inventory_secrets

            is_va = is_var_adapter(v)

            if not is_va:
                run_inventory.set_value(k, v, is_secret=secret)
                continue

            # otherwise, we load the var adapter and execute its 'retrive' method

            var_value, var_is_sec, _ = get_resolved_var_adapter_object(
                value=v,
                key=k,
                arg=arg,
                frecklet=self.frecklet,
                is_secret=secret,
                inventory=inventory,
            )

            run_inventory.set_value(k, var_value, is_secret=secret)

        for key, arg in self.frecklet.vars_frecklet.items():
            value = inventory.retrieve_value(key)
            if value is None:
                continue

            secret = key in secret_args or key in inventory_secrets

            is_va = is_var_adapter(value)

            if not is_va:
                run_inventory.set_value(key, value, is_secret=secret)
                continue

            # otherwise, we load the var adapter and execute its 'retrive' method

            var_value, var_is_sec, _ = get_resolved_var_adapter_object(
                value=value,
                key=key,
                arg=arg,
                frecklet=self.frecklet,
                is_secret=secret,
                inventory=inventory,
            )

            run_inventory.set_value(key, var_value, is_secret=var_is_sec)

        return run_inventory, secret_args

    @interprocess_locked(path=FRECKLES_RUN_LOG_FILE_LOCK)
    def write_runs_log(self, properties, adapter_name, state):

        keep_logs = False

        with run_log_lock:

            if keep_logs:
                row = [
                    properties["uuid"],
                    properties["run_metadata"].get(
                        "run_alias", properties["frecklet_name"]
                    ),
                    properties["frecklet_name"],
                    adapter_name,
                    properties["env_dir"],
                    state,
                    time.time(),
                ]
                with io.open(
                    FRECKLES_LAST_RUN_FILE_PATH, "w", encoding="utf-8", buffering=1
                ) as f:
                    writer = csv.writer(f)
                    writer.writerow(row)

                with io.open(
                    FRECKLES_RUN_LOG_FILE_PATH, "a", encoding="utf-8", buffering=1
                ) as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
            else:
                if state == "started":
                    row = [
                        properties["uuid"],
                        properties["run_metadata"].get(
                            "run_alias", properties["frecklet_name"]
                        ),
                        properties["frecklet_name"],
                        adapter_name,
                        properties["env_dir"],
                        state,
                        time.time(),
                    ]
                    with io.open(
                        FRECKLES_RUN_LOG_FILE_PATH, "a", encoding="utf-8", buffering=1
                    ) as f:
                        writer = csv.writer(f)
                        writer.writerow(row)
                else:
                    with open(FRECKLES_RUN_LOG_FILE_PATH, "r") as inp, open(
                        FRECKLES_RUN_LOG_FILE_PATH + ".tmp", "w", buffering=1
                    ) as out:
                        writer = csv.writer(out)
                        for row in csv.reader(inp):
                            if row[0] != properties["uuid"]:
                                writer.writerow(row)
                    os.rename(
                        FRECKLES_RUN_LOG_FILE_PATH + ".tmp", FRECKLES_RUN_LOG_FILE_PATH
                    )

    def run_frecklecutable(
        self,
        inventory=None,
        run_config=None,
        run_vars=None,
        parent_task=None,
        result_callback=None,
        elevated=None,
        env_dir=None,
    ):

        inventory, run_config, run_vars = set_run_defaults(
            inventory=inventory, run_config=run_config, run_vars=run_vars
        )

        run_inventory, secret_args = self.create_run_inventory(
            inventory=inventory, run_config=run_config, run_vars=run_vars
        )

        if parent_task is None:
            i_am_root = True
            result_callback = FrecklesResultCallback()
        else:
            i_am_root = False
            if result_callback is None:
                raise Exception("No result callback. This is a bug")

        # paused = False
        # if parent_task is not None and (
        #     secret_args
        #     or run_config.get("become_pass", None) == "::ask::"
        #     or run_config.get("login_pass", None) == "::ask::"
        #     ):
        #     paused = True
        asked = False

        run_secrets = {}

        # if parent_task is not None:
        #     parent_task.pause()

        run_secrets["become_pass"] = run_config.pop("become_pass", None)
        if (
            not run_config.get("no_run", False)
            and run_secrets["become_pass"] == "::ask::"
        ):
            msg = ""
            if run_config.get("user", None):
                msg = "{}@".format(run_config["user"])
            msg = msg + run_config.get("host", "localhost")

            prompt = "SUDO PASS (for '{}')".format(msg)

            run_secrets["become_pass"] = ask_password(prompt)
            asked = True

        run_secrets["login_pass"] = run_config.pop("login_pass", None)
        if (
            not run_config.get("no_run", False)
            and run_secrets["login_pass"] == "::ask::"
        ):
            msg = ""
            if run_config.get("user", None):
                msg = "{}@".format(run_config["user"])
            msg = msg + run_config.get("host", "localhost")

            prompt = "LOGIN/SSH PASS (for '{}')".format(msg)

            run_secrets["login_pass"] = ask_password(prompt)
            asked = True

        # if paused:
        #     parent_task.resume()

        if asked:
            click.echo()

        frecklet_name = self.frecklet.id
        log.debug("Running frecklecutable: {}".format(frecklet_name))

        tasks = self.process_tasks(inventory=run_inventory)

        current_tasklist = []
        idempotent_cache = []
        current_adapter = None

        # all_resources = {}
        tasks_elevated = False

        task_lists = []

        for task in tasks:

            elv = (
                task[FRECKLET_KEY_NAME]
                .get(FRECKLES_PROPERTIES_METADATA_KEY, {})
                .get(FRECKLES_PROPERTIES_ELEVATED_METADATA_KEY, False)
            )
            # just converting from string to boolean
            if isinstance(elv, string_types):
                if elv.lower() in ["true", "1", "yes"]:
                    elv = True

                task[FRECKLET_KEY_NAME][FRECKLES_PROPERTIES_METADATA_KEY][
                    FRECKLES_PROPERTIES_ELEVATED_METADATA_KEY
                ] = True

            if elv:
                tasks_elevated = True

            tt = task[FRECKLET_KEY_NAME]["type"]

            adapter_name = self.context._adapter_tasktype_map.get(tt, None)

            if adapter_name is None:
                raise Exception("No adapter registered for task type: {}".format(tt))
            if len(adapter_name) > 1:
                raise Exception(
                    "Multiple adapters registered for task type '{}', that is not supported yet.".format(
                        tt
                    )
                )

            adapter_name = adapter_name[0]

            if current_adapter is None:
                current_adapter = adapter_name

            if current_adapter != adapter_name:

                if elevated is not None:
                    tasks_elevated = elevated

                new_tasklist = {
                    "tasklist": current_tasklist,
                    "adapter": current_adapter,
                    "elevated": tasks_elevated,
                }
                if tasks_elevated:
                    self.check_become_pass(run_config, run_secrets, parent_task)
                task_lists.append(new_tasklist)
                current_adapter = adapter_name
                idempotent_cache = []
                current_tasklist = []
                tasks_elevated = False

            if is_duplicate_task(task, idempotent_cache):
                log.debug(
                    "Idempotent, duplicate task, ignoring: {}".format(
                        task[FRECKLET_KEY_NAME]["name"]
                    )
                )
                continue

            current_tasklist.append(task)

        if elevated is not None:
            tasks_elevated = elevated
        new_tasklist = {
            "tasklist": current_tasklist,
            "adapter": current_adapter,
            "elevated": tasks_elevated,
        }
        if tasks_elevated:
            self.check_become_pass(run_config, run_secrets, parent_task)
        task_lists.append(new_tasklist)

        current_run_result = None
        root_task = None
        run_env_properties = None

        try:
            for run_nr, tl_details in enumerate(task_lists):

                current_adapter = tl_details["adapter"]
                current_tasklist = tl_details["tasklist"]
                run_elevated = tl_details["elevated"]

                if not current_tasklist:
                    continue

                adapter = self.context._adapters[current_adapter]
                run_env_properties = self.context.create_run_environment(
                    adapter, env_dir=env_dir
                )
                run_env_properties["frecklet_name"] = self.frecklet.id
                run_env_properties["run_metadata"] = run_config.get("metadata", {})

                # preparing execution environment...
                self._context._run_info.get("prepared_execution_environments", {}).get(
                    current_adapter, None
                )

                cbs = self._callbacks
                if self.context.config_value("write_run_log"):
                    c_config = {
                        "path": os.path.join(
                            run_env_properties["env_dir"], "run_log.json"
                        )
                    }
                    log_file_callback = load_callback(
                        "logfile", callback_config=c_config
                    )

                    cbs = cbs + [log_file_callback]

                if parent_task is None:
                    root_task = Tasks(
                        "env_prepare_adapter_{}".format(adapter_name),
                        msg="starting run",
                        category="run",
                        callbacks=cbs,
                        is_utility_task=False,
                    )
                    parent_task = root_task.start()

                prepare_root_task = parent_task.add_subtask(
                    task_name="env_prepare_adapter_{}".format(adapter_name),
                    msg="preparing adapter: {}".format(adapter_name),
                )

                try:
                    adapter.prepare_execution_requirements(
                        run_config=run_config,
                        task_list=current_tasklist,
                        parent_task=prepare_root_task,
                    )
                    prepare_root_task.finish(success=True)

                except (Exception) as e:
                    prepare_root_task.finish(success=False, error_msg=str(e))
                    raise e

                host = run_config["host"]

                if adapter_name == "freckles":
                    msg = "running frecklecutable: {}".format(frecklet_name)
                else:
                    msg = "running frecklet: {} (on: {})".format(frecklet_name, host)
                root_run_task = parent_task.add_subtask(
                    task_name=frecklet_name, msg=msg
                )

                run_config["elevated"] = run_elevated

                run_vars = dict_merge(result_callback.result, run_vars, copy_dct=True)

                if not i_am_root:
                    r_tks = get_template_keys(
                        run_config, jinja_env=DEFAULT_RUN_CONFIG_JINJA_ENV
                    )
                    if r_tks:
                        for k in r_tks:
                            if k not in result_callback.result.keys():
                                raise Exception(
                                    "Could not find result key for subsequent run: {}".format(
                                        k
                                    )
                                )

                        run_config = replace_strings_in_obj(
                            run_config,
                            replacement_dict=result_callback.result,
                            jinja_env=DEFAULT_RUN_CONFIG_JINJA_ENV,
                        )

                run_properties = None
                try:
                    self.write_runs_log(
                        properties=run_env_properties,
                        adapter_name=adapter_name,
                        state="started",
                    )
                    # from random import randint
                    # from time import sleep
                    # sec = randint(1, 10)
                    # print("SLEEPING: {}".format(sec))
                    # sleep(sec)

                    run_properties = adapter._run(
                        tasklist=current_tasklist,
                        run_vars=run_vars,
                        run_config=run_config,
                        run_secrets=run_secrets,
                        run_env=run_env_properties,
                        result_callback=result_callback,
                        parent_task=root_run_task,
                    )

                    if not root_run_task.finished:
                        root_run_task.finish()

                    run_result = FrecklesRun(
                        run_id=run_nr,
                        adapter_name=adapter_name,
                        task_list=current_tasklist,
                        run_vars=run_vars,
                        run_config=run_config,
                        run_env=run_env_properties,
                        run_properties=run_properties,
                        result=copy.deepcopy(result_callback.result),
                        success=root_run_task.success,
                        root_task=root_run_task,
                        parent_result=current_run_result,
                    )
                    current_run_result = run_result
                    self.write_runs_log(
                        properties=run_env_properties,
                        adapter_name=adapter_name,
                        state="success",
                    )

                    if not root_run_task.success:
                        break

                except (Exception) as e:

                    # import traceback
                    # traceback.print_exc()
                    self.write_runs_log(
                        properties=run_env_properties,
                        adapter_name=adapter_name,
                        state="failed",
                    )

                    if isinstance(e, FrklException):
                        msg = e.message
                    else:
                        msg = str(e)
                    if not root_run_task.finished:
                        root_run_task.finish(success=False, error_msg=msg)
                    # click.echo("frecklecutable run failed: {}".format(e))
                    log.debug(e, exc_info=1)

                    run_result = FrecklesRun(
                        run_id=run_nr,
                        adapter_name=adapter_name,
                        task_list=current_tasklist,
                        run_vars=run_vars,
                        run_config=run_config,
                        run_env=run_env_properties,
                        run_properties=run_properties,
                        result=copy.deepcopy(result_callback.result),
                        success=root_run_task.success,
                        root_task=root_run_task,
                        parent_result=current_run_result,
                        exception=e,
                    )
                    current_run_result = run_result

                    break

        finally:
            if root_task is None:
                return current_run_result

            if i_am_root:
                root_task.finish()

            keep_run_folder = self.context.config_value("keep_run_folder", "context")

            if i_am_root and not keep_run_folder:

                env_dir = run_env_properties["env_dir"]
                env_dir_link = run_env_properties.get("env_dir_link", None)

                if env_dir_link and os.path.realpath(env_dir_link) == env_dir:
                    try:
                        log.debug("removing env dir symlink: {}".format(env_dir_link))
                        os.unlink(env_dir_link)
                    except (Exception):
                        log.debug("Could not remove symlink.")

                try:
                    log.debug("removing env dir: {}".format(env_dir))
                    shutil.rmtree(env_dir)
                except (Exception) as e:
                    log.warning(
                        "Could not remove environment folder '{}': {}".format(
                            env_dir, e
                        )
                    )

        return current_run_result
