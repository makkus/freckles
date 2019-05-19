# -*- coding: utf-8 -*-
from .defaults import FRECKLES_RUN_DIR, FRECKLES_CURRENT_RUN_SYMLINK

# schema to load '*.context' files in $HOME/.config/freckles
PROFILE_LOAD_CONFIG_SCHEMA = {
    "profile_load_ignore_prefixes": {
        "type": "list",
        "default": [],
        "empty": True,
        "schema": {"type": "string"},
        "required": False,
        "target_key": "folder_load_ignore_file_prefixes",
    },
    "profile_load_ignore_postfixes": {
        "type": "list",
        "default": [],
        "empty": True,
        "schema": {"type": "string"},
        "required": False,
        "target_key": "folder_load_ignore_file_postfixes",
    },
    "profile_load_file_match_regex": {
        "type": "string",
        "required": False,
        "target_key": "folder_load_file_match_regex",
        "default": "\\.context$",
    },
    "profile_load_use_subfolders": {
        "type": "boolean",
        "default": False,
        "required": False,
        "target_key": "folder_load_use_subfolders",
    },
    "profile_load_ignore_hidden_files": {
        "type": "boolean",
        "default": True,
        "required": False,
        "target_key": "frecklet_load_use_subfolders",
    },
}


# Default freckles context configuration schema. This contains all configuration  pertaining to a single freckles
# context, like which repositories to use, which adapters, etc.
FRECKLES_CONTEXT_SCHEMA = {
    "adapters": {
        "type": "list",
        "default": ["nsbl", "tempting", "freckles"],
        "doc": "A list of freckles adapters to use in this context.",
    },
    "repos": {
        "empty": False,
        "default": ["default", "user"],
        "type": "list",
        "schema": {"type": "string"},
        "doc": {
            "short_help": "A list of repositories containing frecklets and/or associated resources.",
            "help": """"A list of repositories containing frecklets and/or associated resources.

The value of this option is of the 'list' type, the items can either be plain paths or urls, in which case freckles will look for all types of resources included in them (which might be time-consuming), or pre-pended with a '[resource-type]::' string, in which case freckles will only look for the specified resource type.

There are 3 special repository aliases that can be used instead of a path:

- 'default': the default frecklets and resources included with each freckles adapter
- 'community': the default community frecklets and resources (check: https://gitlab.com/frecklets )
- 'user': user specific frecklets and resources (adapter-dependent, usually a sub-directory of ~/.config/freckles/
""",
            "examples": [
                {
                    "title": "Use 'default' and 'community' repos.",
                    "vars": {"repos": ["default", "community"]},
                }
            ],
        },
    },
    "allow_remote": {
        "type": "boolean",
        "default": False,
        "doc": "Allow all remote repositories (except ones that match an item in 'allow_remote_blacklist').",
    },
    "allow_remote_whitelist": {
        "type": "list",
        "default": [],
        "doc": "List of urls (or url regexes) of allowed remote repositories.",
    },
    "ignore_empty_repos": {
        "type": "boolean",
        "default": True,
        "doc": "Whether to ignore non-existent or empty local repos or fail if one such is encountered.",
        "tags": ["safe"],
    },
    "remote_cache_valid_time": {
        "type": "integer",
        "default": 0,
        "doc": "Update remote repos if their last checkout was longer ago than this threshold.",
        "tags": ["safe"],
    },
    "run_folder": {
        "type": "string",
        "default": FRECKLES_RUN_DIR,
        "doc": {"short_help": "the target for the generated run environment"},
        "tags": ["safe"],
    },
    "current_run_folder": {
        "type": "string",
        "default": FRECKLES_CURRENT_RUN_SYMLINK,
        "doc": {"short_help": "target of a symlink the current run environment"},
        "tags": ["safe"],
    },
    "force_run_folder": {
        "type": "boolean",
        "default": True,
        "target_key": "force",
        "doc": {
            "short_help": "overwrite a potentially already existing run environment"
        },
        "tags": ["safe"],
    },
    "add_timestamp_to_env": {
        "type": "boolean",
        "default": True,
        "doc": {
            "short_help": "whether to add a timestamp to the run environment folder name"
        },
        "tags": ["safe"],
    },
    "add_adapter_name_to_env": {
        "type": "boolean",
        "default": True,
        "doc": {
            "short_help": "whether to add the adapter name to the run environment folder name"
        },
        "tags": ["safe"],
    },
    "callback": {
        "type": ["string", "dict", "list"],
        "default": ["auto"],
        "doc": {"short_help": "a list of callbacks to attach to a freckles run"},
        "tags": ["safe"],
    },
}


# Schema to contain all the settings that can only be set in the 'default' context. Mainly used to give the user
# contol about what other, imported context configurations are allowed to do or not.
FRECKLES_PERMISSION_SCHEMA = {
    "accept_freckles_license": {
        "type": "boolean",
        "default": False,
        "doc": "Accept the license and acknowledge to not use the publicly licensed version of 'freckles' in combination with non-free software.",
    }
}

# Merged schema, contains all high-level permission variables, as well as the default context config ones.
FRECKLES_DEFAULT_CONFIG_SCHEMA = FRECKLES_CONTEXT_SCHEMA
