# -*- coding: utf-8 -*-

import os

from jinja2.nativetypes import NativeEnvironment

from frutils import JINJA_DELIMITER_PROFILES, jinja2_filters

# ---------------------------------------------------------------
# key names and value constants for use within dicts

TASK_KEY_NAME = "task"
FRECKLET_KEY_NAME = "frecklet"
FRECKLETS_KEY = "frecklets"
VARS_KEY = "vars"
ARGS_KEY = "args"
META_KEY = "meta"
MIXED_CONTENT_TYPE = "hodgepodge"
ACCEPT_FRECKLES_LICENSE_KEYNAME = "accept_freckles_license"

FRECKLES_DEFAULT_ARG_SCHEMA = {"required": True, "empty": False}

# ---------------------------------------------------------------
# folder / filesystem defaults

MODULE_FOLDER = os.path.join(os.path.dirname(__file__))
EXTERNAL_FOLDER = os.path.join(MODULE_FOLDER, "external")
DEFAULT_FRECKLETS_FOLDER = os.path.join(EXTERNAL_FOLDER, FRECKLETS_KEY)
FRECKLES_DOCS_FOLDER = os.path.join(MODULE_FOLDER, "doc")

FRECKLES_CONFIG_DIR = os.path.expanduser("~/.config/freckles")

FRECKLES_SHARE_DIR = os.path.join(
    os.path.expanduser("~"), ".local", "share", "freckles"
)
FRECKLES_RUN_INFO_FILE = os.path.join(FRECKLES_SHARE_DIR, ".run_info")
FRECKLES_CONFIG_PROFILES_DIR = FRECKLES_CONFIG_DIR
FRECKLES_RUN_DIR = os.path.expanduser("~/.local/share/freckles/runs/archive/run")
FRECKLES_CURRENT_RUN_SYMLINK = os.path.expanduser(
    "~/.local/share/freckles/runs/current"
)
FRECKLES_CACHE_BASE = os.path.join(FRECKLES_SHARE_DIR, "cache")

PASSWORD_ASK_MARKER = "ask"
# ---------------------------------------------------------------
# jinja-related defaults

DEFAULT_FRECKLES_JINJA_ENV = NativeEnvironment(**JINJA_DELIMITER_PROFILES["freckles"])
for filter_name, filter_details in jinja2_filters.ALL_FRUTIL_FILTERS.items():
    DEFAULT_FRECKLES_JINJA_ENV.filters[filter_name] = filter_details["func"]
