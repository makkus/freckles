# -*- coding: utf-8 -*-
import copy
import logging
import os
import sys
import textwrap

import click
import tabulate
from click import Context
from jinja2 import Environment, FileSystemLoader
from markdown import Markdown
from six import string_types

from frutils import readable, reindent, get_terminal_size, StringYAML

log = logging.getLogger("freckles")

yaml = StringYAML()

DOC_JINJA_ENV_CACHE = {}

extensions = [
    "codehilite",
    "admonition",
    "pymdownx.extra",
    "pymdownx.details",
    "tables",
    "attr_list",
    "toc",
    "def_list",
]
extension_configs = {
    "codehilite": {"css_class": "codehilite"},
    # "outline": {
    #     "wrapper_cls": "doc-section"
    # }
}

# extensions = []
extension_configs = {}
markdown_renderer = Markdown(extensions=extensions, extension_configs=extension_configs)


def to_code_block_filter(obj, format=None):
    if format is None:
        format = ""

    return "```{}\n{}\n```".format(format, obj)


def to_yaml_filter(obj, empty_string=None, indent=0):
    if not obj:
        return empty_string

    return readable(obj, out="yaml", ignore_aliases=True, indent=indent)


def to_cli_help_string_filter(frecklet):
    cli_paramters = frecklet.cli_arguments

    @click.command(name=frecklet.id)
    def dummy(*args, **kwargs):
        pass

    dummy.params = cli_paramters
    dummy.help = frecklet.doc.get_help()
    dummy.short_help = frecklet.doc.get_short_help()

    ctx = Context(dummy.__class__, info_name="frecklecute {}".format(frecklet.id))
    cli_help = dummy.get_help(ctx)
    return cli_help


HTML_TEMPLATE_FILTERS = {
    "from_markdown": markdown_renderer.convert,
    "to_code_block": to_code_block_filter,
    "to_yaml": to_yaml_filter,
    "to_cli_help_string": to_cli_help_string_filter,
}


def vars_markdown_table(vars, vars_optional=None):

    data = []
    max_width = 0

    vars = copy.copy(vars)
    if vars_optional:
        for k, v in vars_optional.items():
            vars[k] = v

    terminal = get_terminal_size()[0]

    for var_name, var in vars.items():
        v_type = var.schema.get("type", "n/a")
        v_default = var.schema.get("default", "")
        if not isinstance(v_default, string_types):
            if isinstance(v_default, bool):
                # not sure why this doesn't produce good output otherwise
                if v_default:
                    v_default = "true"
                else:
                    v_default = "false"
            else:
                v_default = yaml.dump(v_default)

        if terminal < 60:
            v_default = "\n".join(textwrap.wrap(v_default, 18))
        v_help = var.doc.get_short_help(list_item_format=True)
        req = var.schema.get("required")
        if req:
            v_help = "{} [required]".format(v_help)

        w = len(v_type) + len(v_default) + len(var_name)
        if w > max_width:
            max_width = w
        data.append([var_name, v_type, v_default, v_help])

    avail = terminal - max_width - 20

    for row in data:
        row[3] = "\n".join(textwrap.wrap(row[3], avail))
    result = tabulate.tabulate(
        data, headers=["Name", "Type", "Default", "Description"], tablefmt="simple"
    )

    result = reindent(result, 4)
    return result


MARKDOWN_TEMPLATE_FILTERS = {
    "vars_markdown_table": vars_markdown_table,
    "to_yaml": to_yaml_filter,
}


def create_doc_jinja_env(name, template_dir, template_filters=None):

    global DOC_JINJA_ENV_CACHE

    if DOC_JINJA_ENV_CACHE.get(name, None) is None:
        jinja_env = Environment(loader=FileSystemLoader(template_dir))

        if template_filters:
            for tn, tf in template_filters.items():
                jinja_env.filters[tn] = tf

        DOC_JINJA_ENV_CACHE[name] = jinja_env
    else:
        jinja_env = DOC_JINJA_ENV_CACHE[name]

    return jinja_env


class FreckletDocRenderMixin(object):
    def __init__(self, *args, **kwargs):
        pass

    def render_doc(self, template_name):

        # jinja_env = create_doc_jinja_env()
        pass


def render_html(frecklet):

    repl_dict = {"frecklet_name": frecklet.id, "frecklet": frecklet}

    if not hasattr(sys, "frozen"):
        template_dir = os.path.join(
            os.path.dirname(__file__), "..", "templates", "frecklet_doc", "html"
        )
    else:
        template_dir = os.path.join(
            sys._MEIPASS, "freckles", "templates", "frecklet_doc", "html"
        )
    template = create_doc_jinja_env(
        "html_doc_frecklet",
        template_dir=template_dir,
        template_filters=HTML_TEMPLATE_FILTERS,
    ).get_template("layout.html")

    try:
        rendered = template.render(**repl_dict)
    except (Exception) as e:
        import traceback

        traceback.print_exc()
        raise e

    return rendered


def render_markdown(frecklet):

    repl_dict = {"frecklet_name": frecklet.id, "frecklet": frecklet}

    if not hasattr(sys, "frozen"):
        template_dir = os.path.join(
            os.path.dirname(__file__), "..", "templates", "frecklet_doc", "markdown"
        )
    else:
        template_dir = os.path.join(
            sys._MEIPASS, "freckles", "templates", "frecklet_doc", "markdown"
        )

    template = create_doc_jinja_env(
        "markdown_doc_frecklet",
        template_dir=template_dir,
        template_filters=MARKDOWN_TEMPLATE_FILTERS,
    ).get_template("layout.md.j2")

    try:
        rendered = template.render(**repl_dict)
    except (Exception) as e:
        import traceback

        traceback.print_exc()
        raise e

    return rendered
