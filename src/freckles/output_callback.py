# -*- coding: utf-8 -*-
import logging
import uuid
from collections import Mapping

import colorama
import dpath
from ruamel.yaml.comments import CommentedMap
from six import string_types
from slugify import slugify

from freckles.defaults import DEFAULT_RUN_CONFIG_JINJA_ENV
from frutils import readable_yaml, dict_merge, replace_strings_in_obj
from frutils.exceptions import FrklException

colorama.init()

log = logging.getLogger("freckles")

ALLOWED_STATUS = ["ok", "skipped", "changed", "failed"]


# extensions


# ------------------------------------------------------------------------


class FrecklesRun(object):
    def __init__(
        self,
        run_id,
        adapter_name,
        task_list,
        run_vars,
        run_config,
        run_env,
        run_properties,
        result,
        success,
        parent_result,
        root_task,
        exception=None,
    ):

        self.run_id = run_id
        self.adapter_name = adapter_name
        self.task_list = task_list
        self.run_vars = run_vars
        self.run_config = run_config
        self.run_env = run_env

        self.run_properties = run_properties

        self.result = result

        self.success = success

        self.parent_result = parent_result
        self.root_task = root_task
        self.exception = exception

    def __str__(self):

        return readable_yaml(
            {
                "success": self.success,
                "result": self.result,
                "run_properties": self.run_properties,
                "task_list": self.task_list,
            }
        )


class FrecklesResultCallback(object):
    """ Class to gather results of a frecklecute run.
    """

    def __init__(self):

        self._result = CommentedMap()
        self._registers = {}

    def register_task(self, frecklet_metadata):

        register = frecklet_metadata.get("register", None)
        if register is None:
            return

        if isinstance(register, string_types):
            register = {"target": register}

        if not isinstance(register, Mapping):
            raise TypeError(
                "Invalid type for 'register' value: {}".format(type(register))
            )

        if not register.get("target", None):
            frecklet_metadata.pop("register", None)
            return

        if "value" not in register.keys():
            register["value"] = None

        if "id" not in register.keys():
            register_id = str(uuid.uuid4())
            register_id = slugify("result_" + register_id, separator="_")
            register_id.replace("-", "_")
            register["id"] = register_id

        if register["id"] in self._registers.keys():
            raise FrklException(
                "Can't register result with 'id': {}".format(register["id"]),
                reason="Id already registered.",
                solution="Specify a different id.",
            )

        self._registers[register["id"]] = register

        frecklet_metadata["register"] = register

    def add_result(self, result_id, result):

        try:
            registered = self._registers.get(result_id, None)
            if registered is None:
                raise FrklException(
                    msg="Result for id '{}' not registered, this is most likely a bug.".format(
                        result_id
                    )
                )

            value_template = registered.get("value", None)
            if value_template is not None:
                new_value = replace_strings_in_obj(
                    value_template,
                    replacement_dict={"__result__": result},
                    jinja_env=DEFAULT_RUN_CONFIG_JINJA_ENV,
                )
            else:
                new_value = result

            target = registered.get("target", None)
            if target is None:
                if not isinstance(result, Mapping):
                    raise FrklException(
                        msg="Can't merge result id '{}'".format(result_id),
                        reason="Value for result-id '{}' not a mapping, and no 'target' provided.",
                        solution="Either provide a 'target' value, or use the 'value' template to convert the result.",
                    )
                dict_merge(self._result, new_value, copy_dct=False)
            else:
                temp = {}
                dpath.new(temp, target, new_value, separator=".")
                dict_merge(self._result, temp, copy_dct=False)
        except (Exception) as e:
            log.error("Could not register result '{}': {}".format(result_id, e))

    @property
    def result(self):
        return self._result
