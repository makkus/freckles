import logging
import os

import click
from click import Context
from jinja2 import Environment, FileSystemLoader
from markdown import Markdown

from frutils import readable

log = logging.getLogger("freckles")


def create_doc_jinja_env():

    template_dir = os.path.join(
        os.path.dirname(__file__), "..", "templates", "frecklet_doc", "html"
    )
    jinja_env = Environment(loader=FileSystemLoader(template_dir))

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

    markdown_renderer = Markdown(
        extensions=extensions, extension_configs=extension_configs
    )

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

    jinja_env.filters["from_markdown"] = markdown_renderer.convert
    jinja_env.filters["to_code_block"] = to_code_block_filter
    jinja_env.filters["to_yaml"] = to_yaml_filter
    jinja_env.filters["to_cli_help_string"] = to_cli_help_string_filter

    return jinja_env


DOC_JINJA_ENV = create_doc_jinja_env()


def render_html(frecklet):

    repl_dict = {"frecklet_name": frecklet.id, "frecklet": frecklet}

    template = DOC_JINJA_ENV.get_template("layout.html")

    try:
        rendered = template.render(**repl_dict)
    except (Exception) as e:
        import traceback

        traceback.print_exc()
        raise e

    return rendered
