# -*- coding: utf-8 -*-

from frutils import JINJA_DELIMITER_PROFILES
from plumbum import local
from jinja2 import PackageLoader
from jinja2.nativetypes import NativeEnvironment
from six import string_types

DOC_TEMPLATE_LOADER = PackageLoader("freckles", "templates")
DOC_JINJA_ENV = NativeEnvironment(
    loader=DOC_TEMPLATE_LOADER, **JINJA_DELIMITER_PROFILES["documentation"]
)


def sanitize_rst_filter(value):

    if not isinstance(value, string_types):
        return value

    if value.endswith("_"):
        value = "{}\\_".format(value[0:-1])
    return value


def make_sentence_filter(value):

    if not isinstance(value, string_types):
        return value

    if not value.endswith("."):
        value = value + "."

    value = value.capitalize()
    return value

DOC_JINJA_FILTERS = {
    "sanitize_rst": sanitize_rst_filter,
    "make_sentence": make_sentence_filter,
}

for key, value in DOC_JINJA_FILTERS.items():
    DOC_JINJA_ENV.filters[key] = value


def get_frecklecute_help_text():

    command = "frecklecute"
    args = "--help"
    cmd = local[command]

    rc, stdout, stderr = cmd.run(args, retcode=None)

    return stdout


def render_frecklet(
    frecklet_name, frecklet, show=None, template_name="frecklet_template_default.rst.j2", jinja_env=None
):

    if jinja_env is None:
        jinja_env = DOC_JINJA_ENV

    if show is None:
        show = {"arguments": False, "references": False, "arg_list_filter": []}

    repl_dict = {"frecklet_name": frecklet_name, "frecklet": frecklet, "show": show}
    template = jinja_env.get_template(template_name)
    rendered = template.render(**repl_dict)
    return rendered
