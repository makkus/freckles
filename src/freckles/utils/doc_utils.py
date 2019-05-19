# -*- coding: utf-8 -*-

"""Generic configuration class."""
import copy
import logging

import click

from freckles.defaults import DEFAULT_FRECKLES_JINJA_ENV
from frutils import string_is_templated, reindent
from frutils.doc import Doc

log = logging.getLogger("freckles")


def flatten_task_hierarchy(
    task_hierarchy, result=None, remove_children_from_items=True
):

    if result is None:
        result = []

    for task_item in task_hierarchy:

        childs = task_item.get("children", None)
        if remove_children_from_items:
            temp = copy.copy(task_item)
            temp.pop("children", None)
            result.append(temp)
        else:
            result.append(task_item)
        if childs is not None:
            flatten_task_hierarchy(task_hierarchy=childs, result=result)

    return result


def get_task_plan_string(tasklist, indent=0):

    result = []
    for task in tasklist:

        level = task["level"]
        padding_amount = indent + (level * 2)
        padding = " " * padding_amount

        info = task["info"]

        if info["doc"] is not None:
            doc = Doc(info["doc"])
            msg = doc.get_short_help(list_item_format=True)
        else:
            f_name = info["frecklet_name"]
            f_type = info["frecklet_type"]

            if f_type == "frecklet":
                msg = f_name
            else:
                msg = "{}: {}".format(f_type, f_name)

        result.append("{}- {}".format(padding, msg))

    return "\n".join(result)


def print_task_plan(tasklist, indent=0):

    click.echo(get_task_plan_string(tasklist=tasklist, indent=indent))


def describe_tasklist_in_markdown(tasklist, use_short_help_name_as_title=False):

    result = []
    for task in tasklist:

        level = task["level"]
        padding = "#" * (level + 1)

        info = task["info"]

        desc = info["desc"]
        msg = info["msg"]
        doc = info["doc"]
        if doc:
            d = Doc(doc)
            short_help = d.get_short_help(
                list_item_format=True, default=None, use_help=True
            )
            # help = d.get_help(use_short_help=False, default=None)

        f_name = info["frecklet_name"]
        f_type = info["frecklet_type"]

        title = None
        if use_short_help_name_as_title:
            title = short_help

        if not title:
            if f_type == "frecklet":
                title = "``{}``".format(f_name)
            else:
                title = "{}: ``{}``".format(f_type, f_name)

        # result.append(msg)
        if f_type == "frecklet":
            result.append("{} {}".format(padding, title))

        if desc and not string_is_templated(desc, jinja_env=DEFAULT_FRECKLES_JINJA_ENV):
            result.append("\n{}\n".format(desc))
        elif msg and not string_is_templated(msg, jinja_env=DEFAULT_FRECKLES_JINJA_ENV):
            result.append("\n{}\n".format(msg))

    return "\n".join(result)


def describe_tasklist_string(tasklist, use_short_help_name_as_title=False):

    result = []
    for task in tasklist:

        level = task["level"]
        padding = "  " * (level + 1)

        info = task["info"]

        desc = info["desc"]
        msg = info["msg"]
        doc = info["doc"]
        if doc:
            d = Doc(doc)
            short_help = d.get_short_help(
                list_item_format=True, default=None, use_help=True
            )
            # help = d.get_help(use_short_help=False, default=None)

        f_name = info["frecklet_name"]
        f_type = info["frecklet_type"]

        title = None
        if use_short_help_name_as_title:
            title = short_help

        if not title:
            if f_type == "frecklet":
                title = "{}".format(f_name)
            else:
                title = "{}: {}".format(f_type, f_name)

        # result.append(msg)
        if f_type == "frecklet":
            result.append("{}- {}\n".format(padding, title))

        if desc and not string_is_templated(desc, jinja_env=DEFAULT_FRECKLES_JINJA_ENV):
            result.append("{}\n".format(reindent(desc, (level + 1) * 2 + 2)))
        elif msg and not string_is_templated(msg, jinja_env=DEFAULT_FRECKLES_JINJA_ENV):
            result.append("{}\n".format(reindent(msg, (level + 1) * 2 + 2)))

    return "\n".join(result)
