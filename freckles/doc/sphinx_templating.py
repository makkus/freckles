# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import os

from jinja2.nativetypes import NativeEnvironment

from freckles.frecklet import FRECKLET_SCHEMA
from frutils import readable, StringYAML, JINJA_DELIMITER_PROFILES, replace_string
from freckles_connector_nsbl.defaults import NSBL_INTERNAL_FRECKLET_REPO
from .utils import get_frecklecute_help_text
from freckles.defaults import FRECKLETS_KEY

DOC_JINJA_ENV = NativeEnvironment(**JINJA_DELIMITER_PROFILES["documentation"])

ensure_user_example_path = os.path.join(
    NSBL_INTERNAL_FRECKLET_REPO, "system", "users", "user-exists.frecklet"
)
with open(ensure_user_example_path) as f:
    ensure_user_frecklet_string = f.read()

yaml = StringYAML()

ensure_user_data = yaml.load(ensure_user_frecklet_string)

ensure_user_doc_section = ensure_user_data.get("doc")
ensure_user_args_section = ensure_user_data.get("args")
ensure_user_tasks_section = ensure_user_data.get(FRECKLETS_KEY)
ensure_user_doc_string = readable(
    {"doc": ensure_user_doc_section}, out="yaml", sort_keys=True
)
ensure_user_args_string = readable(
    {"args": ensure_user_args_section}, out="yaml", sort_keys=True
)
ensure_user_tasks_string = readable(
    {FRECKLETS_KEY: ensure_user_tasks_section}, out="yaml"
)

frecklecute_help_text = get_frecklecute_help_text()

FRECKLET_SCHEMA_STRING = readable(FRECKLET_SCHEMA, out="yaml", sort_keys=True)

REPL_DICT = {
    "__frecklet_schema__": FRECKLET_SCHEMA,
    "__frecklet_schema_string__": FRECKLET_SCHEMA_STRING,
    "__ensure_user_frecklet_string__": ensure_user_frecklet_string,
    "__ensure_user_doc_string__": ensure_user_doc_string,
    "__ensure_user_args_string__": ensure_user_args_string,
    "__ensure_user_tasks_string__": ensure_user_tasks_string,
    "__frecklecute_help_text__": frecklecute_help_text,
}


def rstjinja(app, docname, source):
    """
    Render our pages as a jinja template for fancy templating goodness.
    """
    # Make sure we're outputting HTML
    if app.builder.format != "html":
        return
    src = source[0]
    try:
        rendered = replace_string(src, REPL_DICT, DOC_JINJA_ENV)
        # rendered = app.builder.templates.render_string(src, REPL_DICT)
    except (Exception) as e:
        print(e)
        rendered = src
    source[0] = rendered


def setup(app):
    app.connect("source-read", rstjinja)
