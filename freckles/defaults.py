# -*- coding: utf-8 -*-

import os

from jinja2.nativetypes import NativeEnvironment

from frutils import JINJA_DELIMITER_PROFILES, jinja2_filters

from luci.readers import PICK_ALL_FILES_FUNCTION_PATH_AS_PKG_NAME

FRECKLET_NAME = "frecklet"
FRECKLETS_KEY = "frecklets"

MODULE_FOLDER = os.path.join(os.path.dirname(__file__))
EXTERNAL_FOLDER = os.path.join(MODULE_FOLDER, "external")
DEFAULT_FRECKLETS_FOLDER = os.path.join(EXTERNAL_FOLDER, FRECKLETS_KEY)

if os.path.exists(os.path.expanduser("~/.freckles")):
    FRECKLES_CONFIG_DIR = os.path.expanduser("~/.freckles")
else:
    FRECKLES_CONFIG_DIR = os.path.expanduser("~/.config/freckles")

FRECKLES_SHARE_DIR = os.path.join(
    os.path.expanduser("~"), ".local", "share", "freckles"
)

MIXED_CONTENT_TYPE = "hodgepodge"

# COMMUNITY_REPO_URL = "https://gitlab.com/freckles-io/freckles-community.git"
# COMMUNITY_FOLDER = os.path.join(FRECKLES_SHARE_DIR, "community")
# COMMUNITY_FRECKLETS_FOLDER = os.path.join(COMMUNITY_FOLDER, FRECKLETS_KEY)
# COMMUNITY_ROLES_FOLDER = os.path.join(COMMUNITY_FOLDER, "roles")
# COMMUNITY_REPO_DESC = {
#     "path": COMMUNITY_FOLDER,
#     "url": COMMUNITY_REPO_URL,
#     "alias": "community",
#     "remote": True,
#     "content_type": MIXED_CONTENT_TYPE,
# }

FRECKLES_CONFIG_PROFILES_DIR = FRECKLES_CONFIG_DIR
FRECKLES_RUN_CONFIG_PROFILES_DIR = os.path.expanduser(
    os.path.join(FRECKLES_CONFIG_DIR, "run-profiles")
)
USER_FRECKLETS_FOLDER = os.path.join(FRECKLES_CONFIG_DIR, FRECKLETS_KEY)

FRECKLES_RUN_DIR = os.path.expanduser("~/.local/share/freckles/runs/archive/run")
FRECKLES_CURRENT_RUN_SYMLINK = os.path.expanduser(
    "~/.local/share/freckles/runs/current"
)

FRECKLES_CACHE_BASE = os.path.join(FRECKLES_SHARE_DIR, "cache")

DEFAULT_FRECKELIZE_DIR = os.path.expanduser("~/freckles")
DEFAULT_FRECKELIZE_SYSTEM_DIR = "/var/lib/freckles"


def PICK_ALL_FRECKLET_FILES_FUNCTION(path):
    """Default implementation of an 'is_*_file' method."""

    if os.path.basename(path) == ".meta.frecklet":
        return False

    if path.endswith(".frecklet"):
        return os.path.splitext(os.path.basename(path))[0]
    else:
        return False


DEFAULT_FRECKLES_REPOS = ["default", "user"]

DEFAULT_FRECKLES_ALIASES = {
    "default": {FRECKLETS_KEY: [DEFAULT_FRECKLETS_FOLDER]},
    "user": {FRECKLETS_KEY: [USER_FRECKLETS_FOLDER]},
    # "community": {
    #     FRECKLETS_KEY: [COMMUNITY_FRECKLETS_FOLDER],
    #     "roles": [COMMUNITY_ROLES_FOLDER],
    # },
}

FRECKLES_CONFIG_SCHEMA = {
    "allow_dynamic_frecklets": {
        "type": "boolean",
        "default": False,
        "__doc__": {
            "short_help": "allow the dynamic creation of frecklets from a string (if the connector allows it). This is not implemented yet."
        },
    },
    "task_type_whitelist": {
        "type": "list",
        "schema": {"type": "string"},
        "__doc__": {
            "short_help": "only allow a certain type of tasks (not implemented yet)"
        },
    },
    "task_type_blacklist": {
        "type": "list",
        "schema": {"type": "string"},
        "__doc__": {"short_help": "block certain types of tasks (not implemented yet)"},
    },
    "allowed_connectors": {
        "type": "list",
        "schema": {"type": "string"},
        "__doc__": {"short_help": "a list of allowed connectors"},
    },
}

FRECKLES_CONTROL_CONFIG_SCHEMA = {
    "host": {
        "type": "string",
        "default": "boolean",
        "__doc__": {"short_help": "the host to run the command on"},
    },
    "port": {
        "type": "integer",
        "__doc__": {"short_help": "the port to connect to (if appropriate)"},
    },
    "user": {"type": "string", "__doc__": {"short_help": "the user to connect as"}},
    "output": {
        "type": "string",
        "default": "freckles",
        "__alias__": "run_callback",
        "__doc__": {
            "short_help": "the name of the run callback to use (advanced, you most likely should not touch this)"
        },
    },
    "run_callback_config": {
        "type": "dict",
        "__doc__": {
            "short_help": "the configuration for the run used run callback (advanced, you most likely should not touch this)"
        },
    },
    "no_run": {
        "type": "boolean",
        "default": False,
        "__doc__": {
            "short_help": "whether to actually run the task list (for debugging/information purposes)"
        },
    },
    "elevated": {
        "type": "boolean",
        "__doc__": {"short_help": "whether this run needs elevated permissions"},
    },
}

REPO_MANAGER_CONFIG_SCHEMA = {
    "context_repos": {
        "type": "list",
        "default": DEFAULT_FRECKLES_REPOS,
        "schema": {"type": "string"},
    },
    "allow_remote": {
        "type": "boolean",
        "default": False,
        "__doc__": {
            "short_help": "allow external (remote) resources (frecklets, connector-specific resources, ...)"
        },
    },
    "allow_community": {
        "type": "boolean",
        "default": True,
        "__doc__": {
            "short_help": "allow resources from the community repo (https://gitlab.com/freckles-io/freckles-community)"
        },
    },
    "remote_whitelist": {
        "type": "list",
        "schema": {"type": "string"},
        "__doc__": {
            "short_help": "list of regular expressions of allowed external urls"
        },
    },
    "remote_blacklist": {
        "type": "list",
        "schema": {"type": "string"},
        "__doc__": {
            "short_help": "list of regular expressions of prohibitet external urls"
        },
    },
    "local_whitelist": {
        "type": "list",
        "schema": {"type": "string"},
        "__doc__": {"short_help": "list of regular expressions of allowed local paths"},
    },
    "local_blacklist": {
        "type": "list",
        "schema": {"type": "string"},
        "__doc__": {
            "short_help": "list of regular expressions of prohibited local paths"
        },
    },
}

FRECKLET_DEFAULT_READER_PROFILE = {
    "use_files": True,
    "use_metadata_files": True,
    "use_parent_metadata_files": False,
    "use_subfolders_as_tags": True,
    "get_pkg_name_function": PICK_ALL_FRECKLET_FILES_FUNCTION,
    "get_pkg_name_function_metadata": PICK_ALL_FRECKLET_FILES_FUNCTION,
    "default_metadata_key": "frecklet_meta",
    "move_list_to_dict_key": FRECKLETS_KEY,
}
FRECKLET_PATH_DEFAULT_READER_PROFILE = {
    "use_files": True,
    "use_metadata_files": True,
    "use_parent_metadata_files": False,
    "use_subfolders_as_tags": True,
    "get_pkg_name_function": PICK_ALL_FILES_FUNCTION_PATH_AS_PKG_NAME,
    "get_pkg_name_function_metadata": PICK_ALL_FILES_FUNCTION_PATH_AS_PKG_NAME,
    "default_metadata_key": "frecklet_meta",
    "move_list_to_dict_key": FRECKLETS_KEY,
}
FRECKLES_CNF_PROFILES = {
    "default": {
        # "convert_ansible_template_markers": False,
        "context_repos": DEFAULT_FRECKLES_REPOS,
        # "allow_dynamic_frecklets": False,
        # "guess_args_for_roles": False,
        # "require_absolute_path": True,
        "allowed_connectors": ["freckles", "shell", "nsbl", "templig"],
        # "current_run_folder": FRECKLES_CURRENT_RUN_SYMLINK,
        # "run_folder": FRECKLES_RUN_DIR,
        "ignore_invalid_repos": True,
        "allow_remote": False,
        "allow_community": True,
        # "freckelize_target_dir": DEFAULT_FRECKELIZE_DIR,
    },
    "empty": {"context_repos": []},
}

FRECKLES_RUN_CONTROL_PROFILES = {
    "default": {
        "host": "localhost",
        "no_run": False,
        "output": "freckles",
        "run_callback_config": {"profile": "default"},
    }
}

DEFAULT_FRECKLES_JINJA_ENV = NativeEnvironment(**JINJA_DELIMITER_PROFILES["freckles"])
for filter_name, filter_details in jinja2_filters.ALL_FRUTIL_FILTERS.items():
    DEFAULT_FRECKLES_JINJA_ENV.filters[filter_name] = filter_details["func"]
