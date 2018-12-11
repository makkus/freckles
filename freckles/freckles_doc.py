# -*- coding: utf-8 -*-

"""Generic configuration class."""
import logging

from ruamel.yaml import YAML

from freckles.defaults import TASK_INSTANCE_NAME

log = logging.getLogger("frutils")

yaml = YAML(typ="safe")

CURSOR_UP_ONE = "\x1b[1A"
ERASE_LINE = "\x1b[2K"

BOLD = "\033[1m"
UNBOLD = "\033[0m"

ARC_DOWN_RIGHT = u"\u256d"
ARC_UP_RIGHT = u"\u2570"
VERTICAL_RIGHT = u"\u251C"
VERTICAL = u"\u2502"
HORIZONTAL = u"\u2500"
END = u"\u257C"
ARROW = u"\u279B"
OK = u"\u2713"


class FrecklesDoc:
    def __init__(self, name, tasklist, context):

        self.name = name
        self.tasklist = tasklist
        self.context = context

    def describe(self):

        for t in self.tasklist:
            desc = t.get(TASK_INSTANCE_NAME, {}).get("desc", "n/a")
            f_type = t["frecklet"]["type"]
            f_command = t["frecklet"]["command"]

            print("- {} ({}/{})".format(desc, f_command, f_type))
