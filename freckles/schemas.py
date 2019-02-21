from frutils import dict_merge

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
    "use_community": {
        "type": "boolean",
        "default": False,
        "doc": """Whether to allow the freckles community repositories.

The freckles community repositories are a collection of community-created and curated frecklets and resources.

TODO: list all repository urls
""",
    },
    "adapters": {
        "type": "list",
        "default": ["nsbl"],
        "doc": "A list of freckles adapters to use in this context.",
    },
    "repos": {
        "empty": False,
        "default": ["default", "user"],
        "type": "list",
        "schema": {"type": "string"},
    },
    "resources": {
        "empty": True,
        "default": {},
        "type": "dict",
        "keyschema": {"type": "string"},
        "valueschema": {"type": "dict"},
    },
    "allow_remote": {
        "type": "boolean",
        "default": False,
        "doc": "Whether to allow remote repositories and resources.",
    },
    "ignore_nonexistent_repos": {
        "type": "boolean",
        "default": True,
        "doc": "Whether to ignore non-existent local repos or fail if one such is encountered.",
    },
    "always_update_remote_repos": {
        "type": "boolean",
        "default": True,
        "doc": "Whether to always update remote repos, even if they are already checked out.",
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
FRECKLES_DEFAULT_CONFIG_SCHEMA = dict_merge(
    FRECKLES_CONTEXT_SCHEMA, FRECKLES_PERMISSION_SCHEMA, copy_dct=True
)


# FRECKLES_CONFIG_SCHEMA = {
#     "allow_dynamic_frecklets": {
#         "type": "boolean",
#         "default": False,
#         "__doc__": {
#             "short_help": "allow the dynamic creation of frecklets from a string (if the adapter allows it). This is not implemented yet."
#         },
#     },
#     "task_type_whitelist": {
#         "type": "list",
#         "schema": {"type": "string"},
#         "__doc__": {
#             "short_help": "only allow a certain type of tasks (not implemented yet)"
#         },
#     },
#     "task_type_blacklist": {
#         "type": "list",
#         "schema": {"type": "string"},
#         "__doc__": {"short_help": "block certain types of tasks (not implemented yet)"},
#     },
#     "allowed_adapters": {
#         "type": "list",
#         "schema": {"type": "string"},
#         "__doc__": {"short_help": "a list of allowed adapters"},
#     },
# }
#
# FRECKLES_CONTROL_CONFIG_SCHEMA = {
#     "target": {
#         "type": "string",
#         "default": "boolean",
#         "__doc__": {"short_help": "the target to run the command on"},
#     },
#     "port": {
#         "type": "integer",
#         "__doc__": {"short_help": "the port to connect to (if appropriate)"},
#     },
#     "user": {"type": "string", "__doc__": {"short_help": "the user to connect as"}},
#     "output": {
#         "type": "string",
#         "default": "freckles",
#         "__alias__": "run_callback",
#         "__doc__": {
#             "short_help": "the name of the run callback to use (advanced, you most likely should not touch this)"
#         },
#     },
#     "run_callback_config": {
#         "type": "dict",
#         "__doc__": {
#             "short_help": "the configuration for the run used run callback (advanced, you most likely should not touch this)"
#         },
#     },
#     "no_run": {
#         "type": "boolean",
#         "default": False,
#         "__doc__": {
#             "short_help": "whether to actually run the task list (for debugging/information purposes)"
#         },
#     },
#     "elevated": {
#         "type": "boolean",
#         "__doc__": {"short_help": "whether this run needs elevated permissions"},
#     },
#     "keep_run_folders": {
#         "type": "integer",
#         "__doc__": {"short_help": "how many run folders to keep (per connector)"},
#         "default": 1,
#     },
# }
#
# REPO_MANAGER_CONFIG_SCHEMA = {
#     "context_repos": {
#         "type": "list",
#         "default": DEFAULT_FRECKLES_REPOS,
#         "schema": {"type": "string"},
#     },
#     "allow_remote": {
#         "type": "boolean",
#         "default": False,
#         "__doc__": {
#             "short_help": "allow external (remote) resources (frecklets, adapter-specific resources, ...)"
#         },
#     },
#     "allow_community": {
#         "type": "boolean",
#         "default": True,
#         "__doc__": {
#             "short_help": "allow resources from the community repo (https://gitlab.com/freckles-io/freckles-community)"
#         },
#     },
#     "remote_whitelist": {
#         "type": "list",
#         "schema": {"type": "string"},
#         "__doc__": {
#             "short_help": "list of regular expressions of allowed external urls"
#         },
#     },
#     "remote_blacklist": {
#         "type": "list",
#         "schema": {"type": "string"},
#         "__doc__": {
#             "short_help": "list of regular expressions of prohibitet external urls"
#         },
#     },
#     "local_whitelist": {
#         "type": "list",
#         "schema": {"type": "string"},
#         "__doc__": {"short_help": "list of regular expressions of allowed local paths"},
#     },
#     "local_blacklist": {
#         "type": "list",
#         "schema": {"type": "string"},
#         "__doc__": {
#             "short_help": "list of regular expressions of prohibited local paths"
#         },
#     },
# }
