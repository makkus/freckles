# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import os
from freckles.frecklet import FRECKLET_SCHEMA
from frutils import readable
from freckles_connector_nsbl.defaults import NSBL_INTERNAL_FRECKLET_REPO

ensure_user_example_path = os.path.join(NSBL_INTERNAL_FRECKLET_REPO, "system", "users", "ensure-user-exists.frecklet")
with open(ensure_user_example_path) as f:
    ensure_user_frecklet_string = f.read()

FRECKLET_SCHEMA_STRING = readable(FRECKLET_SCHEMA, out="yaml")
REPL_DICT = {
    "__frecklet_schema__": FRECKLET_SCHEMA,
    "__frecklet_schema_string__": FRECKLET_SCHEMA_STRING,
    "__ensure_user_frecklet_string__": ensure_user_frecklet_string
}

def rstjinja(app, docname, source):
    """
    Render our pages as a jinja template for fancy templating goodness.
    """
    # Make sure we're outputting HTML
    if app.builder.format != 'html':
        return
    src = source[0]
    rendered = app.builder.templates.render_string(
        src, REPL_DICT
    )
    source[0] = rendered

def setup(app):
    app.connect("source-read", rstjinja)
