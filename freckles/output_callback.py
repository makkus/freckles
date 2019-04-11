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
