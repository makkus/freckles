# -*- coding: utf-8 -*-

"""Generic configuration class."""
import logging

import click
from ruamel.yaml import YAML
from termcolor import colored

from frutils.doc import Doc

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

    def augment_tasks(self):

        result = []

        current_frecklet_name = None
        current_task_list = []
        current_frecklet_info = {}

        for task in self.tasklist:

            frecklet_name = task["task"]["_parent_frecklet"]["name"]

            if current_frecklet_name is None or frecklet_name != current_frecklet_name:
                if current_frecklet_name is not None:
                    current_frecklet_info["tasks"] = current_task_list
                    result.append(current_frecklet_info)

                current_frecklet_info = {}
                current_task_list = []
                current_frecklet_info["frecklet"] = self.context.create_frecklet(
                    frecklet_name
                )
                current_frecklet_info["name"] = frecklet_name

            current_frecklet_name = frecklet_name

            # task_id = task["task"]["_task_id"]
            name = task["task"]["name"]
            task_type = task["task"]["type"]
            command = task["task"]["command"]
            doc = task.get("doc", {})

            current_task = {}
            current_task["name"] = name
            current_task["type"] = task_type
            current_task["command"] = command
            current_task["doc"] = Doc(doc)

            current_task_list.append(current_task)

        current_frecklet_info["tasks"] = current_task_list
        result.append(current_frecklet_info)

        return result

    def describe(self):

        frecklets = self.augment_tasks()

        click.echo()
        click.echo(
            u"{}{} frecklecutable: {}".format(
                ARC_DOWN_RIGHT, END, colored(self.name, attrs=["bold"])
            )
        )
        line = u"{}".format(HORIZONTAL) * (
            len("frecklecutable: {}".format(self.name)) + 3
        )
        click.echo(u"{}{}".format(VERTICAL_RIGHT, line))
        f_max = len(frecklets)
        for f_idx, frecklet in enumerate(frecklets):
            click.echo(u"{}".format(VERTICAL))
            if f_idx == (f_max - 1):
                f_end = ARC_UP_RIGHT
                f_line = " "
            else:
                f_end = VERTICAL_RIGHT
                f_line = VERTICAL

            name = frecklet["name"]
            help = frecklet["frecklet"].get_doc().get_short_help()
            click.echo(
                u"{}{} frecklet: {}".format(f_end, END, colored(name, attrs=["bold"]))
            )
            click.echo(u"{}   {}{} desc: {}".format(f_line, VERTICAL_RIGHT, END, help))
            click.echo(u"{}   {}{} tasks:".format(f_line, ARC_UP_RIGHT, END))
            t_max = len(frecklet["tasks"])
            for t_idx, t in enumerate(frecklet["tasks"]):
                if t_idx == (t_max - 1):
                    t_end = ARC_UP_RIGHT
                    t_line = " "
                else:
                    t_end = VERTICAL_RIGHT
                    t_line = VERTICAL

                desc = t["name"]
                click.echo(
                    u"{}       {}{} command: {}".format(
                        f_line, t_end, END, colored(t["command"], attrs=["bold"])
                    )
                )
                click.echo(
                    u"{}       {}  {}{} desc: {}".format(
                        f_line, t_line, VERTICAL_RIGHT, END, desc
                    )
                )
                click.echo(
                    u"{}       {}  {}{} type: {}".format(
                        f_line, t_line, ARC_UP_RIGHT, END, t["type"]
                    )
                )
