# -*- coding: utf-8 -*-

import os

from jinja2.nativetypes import NativeEnvironment

from frutils import JINJA_DELIMITER_PROFILES, jinja2_filters

# ---------------------------------------------------------------
# key names and value constants for use within dicts
from frutils.defaults import REFERENCES_KEY

TASK_KEY_NAME = "task"
FRECKLET_KEY_NAME = "frecklet"
FRECKLETS_KEY = "frecklets"
VARS_KEY = "vars"
ARGS_KEY = "args"
META_KEY = "meta"
MIXED_CONTENT_TYPE = "hodgepodge"
ACCEPT_FRECKLES_LICENSE_KEYNAME = "accept_freckles_license"
USE_COMMUNITY_KEYNAME = "use_community"

FRECKLES_DESC_METADATA_KEY = "desc"
FRECKLES_DESC_SHORT_METADATA_KEY = "short"
FRECKLES_DESC_LONG_METADATA_KEY = "long"
FRECKLES_DESC_REFERENCES_METADATA_KEY = REFERENCES_KEY
FRECKLES_PROPERTIES_METADATA_KEY = "properties"
FRECKLES_PROPERTIES_IDEMPOTENT_METADATA_KEY = "idempotent"
FRECKLES_PROPERTIES_INTERNET_METADATA_KEY = "internet"
FRECKLES_PROPERTIES_ELEVATED_METADATA_KEY = "elevated"


FRECKLES_DEFAULT_ARG_SCHEMA = {"required": True, "empty": False}


# ---------------------------------------------------------------
# folder / filesystem defaults

MODULE_FOLDER = os.path.join(os.path.dirname(__file__))
EXTERNAL_FOLDER = os.path.join(MODULE_FOLDER, "external")
DEFAULT_FRECKLETS_FOLDER = os.path.join(EXTERNAL_FOLDER, FRECKLETS_KEY)
FRECKLES_DOCS_FOLDER = os.path.join(MODULE_FOLDER, "doc")

XDG_CONFIG_HOME = os.getenv("XDG_CONFIG_HOME")
if XDG_CONFIG_HOME:
    FRECKLES_CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, "freckles")
else:
    FRECKLES_CONFIG_DIR = os.path.expanduser("~/.config/freckles")

XDG_DATA_HOME = os.getenv("XDG_DATA_HOME")
if XDG_DATA_HOME:
    FRECKLES_SHARE_DIR = os.path.join(XDG_DATA_HOME, "freckles")
else:
    FRECKLES_SHARE_DIR = os.path.join(
        os.path.expanduser("~"), ".local", "share", "freckles"
    )

XDG_CACHE_HOME = os.getenv("XDG_CACHE_HOME")
if XDG_CACHE_HOME:
    FRECKLES_CACHE_BASE = os.path.join(XDG_CACHE_HOME, "freckles")
else:
    FRECKLES_CACHE_BASE = os.path.expanduser("~/.cache/freckles")


FRECKLES_RUN_INFO_FILE = os.path.join(FRECKLES_SHARE_DIR, ".run_info")

FRECKLES_CONDA_ENV_PATH = os.path.join(FRECKLES_SHARE_DIR, "envs", "conda", "freckles")
FRECKLES_CONDA_INSTALL_PATH = os.path.join(FRECKLES_SHARE_DIR, "opt", "conda")
FRECKLES_VENV_ENV_PATH = os.path.join(
    FRECKLES_SHARE_DIR, "envs", "virtualenv", "freckles"
)

# FRECKLES_LOOKUP_PATHS = LOOKUP_PATHS + ":" + ":".join(os.path.join(FRECKLES_VENV_ENV_PATH, "bin"), os.path.join(FRECKLES_CONDA_ENV_PATH, "bin"), os.path.join(FRECKLES_CONDA_INSTALL_PATH, "bin"))

FRECKLES_RUN_DIR = os.path.expanduser("~/.local/share/freckles/runs/archive/run")
FRECKLES_CURRENT_RUN_SYMLINK = os.path.expanduser(
    "~/.local/share/freckles/runs/current"
)

FRECKLES_EXTRA_LOOKUP_PATHS = [
    os.path.join(FRECKLES_CONDA_ENV_PATH, "bin"),
    os.path.join(FRECKLES_VENV_ENV_PATH, "bin"),
    os.path.join(
        os.path.expanduser("~/.local/share/inaugurate/conda/envs/freckles/bin")
    ),
    os.path.join(
        os.path.expanduser("~/.local/share/inaugurate/virtualenvs/freckles/bin")
    ),
]

# ---------------------------------------------------------------
# jinja-related defaults

DEFAULT_FRECKLES_JINJA_ENV = NativeEnvironment(**JINJA_DELIMITER_PROFILES["freckles"])
for filter_name, filter_details in jinja2_filters.ALL_FRUTIL_FILTERS.items():
    DEFAULT_FRECKLES_JINJA_ENV.filters[filter_name] = filter_details["func"]

DEFAULT_RUN_CONFIG_JINJA_ENV = NativeEnvironment(**JINJA_DELIMITER_PROFILES["default"])
