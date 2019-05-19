# -*- coding: utf-8 -*-
import logging
from collections import Mapping

import click

from freckles.defaults import FRECKLET_KEY_NAME, VARS_KEY, TASK_KEY_NAME
from freckles.frecklet.vars import VarsInventory
from frutils import dict_merge, reindent, readable
from frutils.doc import Doc

log = logging.getLogger("freckles")


def print_task_descriptions(task_desc_list):

    for td in task_desc_list:

        title = td["title"]
        desc = td["desc"]
        alt_title = td["alt_title"]
        alt_desc = td["alt_desc"]

        if not title:
            title = alt_title

        if not desc:
            desc = alt_desc

        click.echo("- ", nl=False)
        click.secho(title, bold=True)
        click.echo()
        click.echo(reindent(desc, 4))
        click.echo()
        if td["references"]:
            click.echo(reindent("References:\n", 4))
            for key, value in td["references"].items():
                click.echo(reindent("{}: {}".format(key, value), 6))
            click.echo()


def describe_frecklet(context, frecklet, vars, auto_vars=False):

    fx = frecklet.create_frecklecutable(context=context)

    var_all = {}

    if isinstance(vars, Mapping):
        vars = [vars]
    for v in vars:
        dict_merge(var_all, v, copy_dct=False)

    auto_vars_dict = None
    if auto_vars:
        params = fx.frecklet.vars_frecklet
        auto_vars_dict = create_auto_vars(
            params, existing_vars=var_all, frecklet=fx.frecklet
        )
        var_all = dict_merge(auto_vars_dict, var_all, copy_dct=True)

    inv = VarsInventory(var_all)
    tasks = fx.process_tasks(inventory=inv)

    result = []
    for task in tasks:

        # output(task, output_type="yaml")
        f_type = task[FRECKLET_KEY_NAME]["type"]
        name = task[FRECKLET_KEY_NAME]["name"]

        f_doc = Doc(
            task[FRECKLET_KEY_NAME],
            short_help_key="msg",
            help_key="desc",
            further_reading_key="references",
        )

        title = f_doc.get_short_help(
            default=None, use_help=False, list_item_format=True
        )
        if title:
            if title.startswith("["):
                title = title[1:]
            if title.endswith("]"):
                title = title[0:-1]
        else:
            title = None

        if f_type == "frecket":
            alt_title = context.get_frecklet(name).doc.get_short_help(
                list_item_format=True
            )

            alt_desc = context.get_frecklet(name).doc.get_short_help(
                list_item_format=False
            )
            if alt_desc:
                alt_desc = alt_desc.strip()
        else:
            alt_title = "execute {}: {}".format(f_type, name)
            alt_desc = "Run {} '{}'".format(f_type, name)

        desc = f_doc.get_help(default=None, use_short_help=False)
        if desc:
            desc = desc.strip()

        if not task.get(VARS_KEY):
            alt_desc = alt_desc + " (no variables used)."
        else:
            vars_string = readable(task[VARS_KEY], out="yaml")
            alt_desc = alt_desc + " using variables:\n\n" + reindent(vars_string, 2)
            alt_desc = alt_desc.strip()
            if task.get(TASK_KEY_NAME, None):
                task_string = readable(task[TASK_KEY_NAME], out="yaml")
                alt_desc = (
                    alt_desc + "\n\nand task metadata:\n\n" + reindent(task_string, 2)
                )
                alt_desc = alt_desc.strip()

        task_md = {}
        task_md["title"] = title
        task_md["alt_title"] = alt_title
        task_md["desc"] = desc
        task_md["alt_desc"] = alt_desc
        task_md["references"] = f_doc.get_further_reading()

        result.append(task_md)

    return result, auto_vars_dict


def create_auto_vars(params, existing_vars={}, frecklet=None):

    if frecklet is not None:

        examples = frecklet.doc.get_examples()
        if examples:
            vars = examples[0].get("vars")
            return vars

    required = []

    for name, p in params.items():

        if name in existing_vars.keys():
            continue

        if p._schema.get("required", True) and p._schema.get("default", None) is None:
            required.append((name, p))

    add_vars = {}
    for p in required:

        val = None
        name = p[0]
        scheme = p[1]._schema
        empty = scheme.get("empty", False)
        p_type = scheme.get("type", "string")

        if empty:
            if p_type == "string":
                val = ""
            elif p_type == "list":
                val = []
            elif p_type == "dict":
                val = {}

        if val is None:
            if p_type == "string":
                if "path" in name:
                    val = "/tmp/parent-folder/var--{}--example".format(name)
                elif "content" in name:
                    val = """Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s.

Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s."""
                else:
                    val = "[var--{}--]".format(name)
            elif p_type == "list":
                val = ["[var--{}--]".format(name)]
            elif p_type == "dict":
                val = {"[var--key-{}--]".format(name): "[var--val-{}--]".format(name)}
            elif p_type == "integer":
                val = "1"
            elif p_type == "boolean":
                val = True
            elif p_type == "password":
                val = "[var--password-{}--]".format(name)
            else:
                val = "[var--unknown_type-{}--[".format(name)

        add_vars[name] = val

    return add_vars
