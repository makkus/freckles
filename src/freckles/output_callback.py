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
    ):

        self.run_id = run_id
        self.adapter_name = adapter_name
        self.task_list = task_list
        self.run_vars = run_vars
        self.run_config = run_config
        self.run_env = run_env

        self.run_properties = run_properties

        self.result = result

    def __str__(self):

        return readable_yaml(
            {
                "name": self.frecklet_name,
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

        result_key_val = self._result.setdefault(result_var, CommentedMap())

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

        dict_merge(result_key_val, result, copy_dct=False)

    @property
    def result(self):
        return self._result
