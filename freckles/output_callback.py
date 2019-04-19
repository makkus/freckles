# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict

import colorama

from frutils import readable_yaml, dict_merge

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
    ):

        self.run_id = run_id
        self.adapter_name = adapter_name
        self.task_list = task_list
        self.run_vars = run_vars
        self.run_config = run_config
        self.run_env = run_env

        self.run_properties = run_properties

    def __str__(self):

        return readable_yaml(
            {
                "name": self.frecklet_name,
                "run_properties": self.run_properties,
                "task_list": self.task_list,
            }
        )


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
