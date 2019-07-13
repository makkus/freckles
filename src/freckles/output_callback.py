# -*- coding: utf-8 -*-
import logging

import colorama
import dpath
from ruamel.yaml.comments import CommentedMap

from frutils import readable_yaml, dict_merge
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

    def add_result(self, result_var, result, query=None):

        if query is not None:
            try:
                result = dpath.util.get(result, query)
            except (Exception):
                raise FrklException(
                    msg="Could not query registered result using query string '{}'".format(
                        query
                    ),
                    solution="Check query string and make sure the format of the result is supported",
                    references={
                        "dpath documentation": "https://github.com/akesterson/dpath-python"
                    },
                )

        new_value = {result_var: result}

        dict_merge(self._result, new_value, copy_dct=False)

    @property
    def result(self):
        return self._result
