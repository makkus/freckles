# -*- coding: utf-8 -*-

import logging

from collections import OrderedDict

from frutils import dict_merge

log = logging.getLogger("freckles")

RESULT_STRATEGIES = ["merge", "update", "append", "ordered_merge", "ordered_update"]


# TODO: make it possible to add one or more callback functions
# instead of predefined strategies
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
