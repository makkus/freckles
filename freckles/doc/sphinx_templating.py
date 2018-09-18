# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import os
from freckles.frecklet import FRECKLET_SCHEMA
from frutils import readable, StringYAML
from freckles_connector_nsbl.defaults import NSBL_INTERNAL_FRECKLET_REPO

ensure_user_example_path = os.path.join(
    NSBL_INTERNAL_FRECKLET_REPO, "system", "users", "ensure-user-exists.frecklet"
)
with open(ensure_user_example_path) as f:
    ensure_user_frecklet_string = f.read()

yaml = StringYAML()

ensure_user_data = yaml.load(ensure_user_frecklet_string)

ensure_user_doc_section = ensure_user_data.get("doc")
ensure_user_args_section = ensure_user_data.get("args")
ensure_user_tasks_section = ensure_user_data.get("tasks")
ensure_user_doc_string = readable({"doc": ensure_user_doc_section}, out="yaml", sort_keys=True)
ensure_user_args_string = readable({"args": ensure_user_args_section}, out="yaml", sort_keys=True)
ensure_user_tasks_string = readable({"tasks": ensure_user_tasks_section}, out="yaml")

FRECKLET_SCHEMA_STRING = readable(FRECKLET_SCHEMA, out="yaml", sort_keys=True)

REPL_DICT = {
    "__frecklet_schema__": FRECKLET_SCHEMA,
    "__frecklet_schema_string__": FRECKLET_SCHEMA_STRING,
    "__ensure_user_frecklet_string__": ensure_user_frecklet_string,
    "__ensure_user_doc_string__": ensure_user_doc_string,
    "__ensure_user_args_string__": ensure_user_args_string,
    "__ensure_user_tasks_string__": ensure_user_tasks_string,
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
        rendered = app.builder.templates.render_string(src, REPL_DICT)
    except:
        rendered = src
    source[0] = rendered


def setup(app):
    app.connect("source-read", rstjinja)
