from collections import Sequence

from six import string_types

from freckles.defaults import MIXED_CONTENT_TYPE
from frutils import is_url_or_abbrev


def ensure_alias_dict(value):

    if isinstance(value, string_types):
        return {"types": [MIXED_CONTENT_TYPE], "repos": [value]}
    elif isinstance(value, Sequence):
        return {"types": [MIXED_CONTENT_TYPE], "repos": value}

    return value


def ensure_repo_dict(value):

    if isinstance(value, string_types):
        if "::" in value:
            ting_type, url = value.split("::", 1)
            return {"types": [ting_type], "repos": [url]}
        else:
            return {"types": [MIXED_CONTENT_TYPE], "repos": [value]}
    return value

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
        "target_key": "folder_load_ignore_file_postfixes"
    },
    "profile_load_file_match_regex": {
        "type": "string",
        "required": False,
        "target_key": "folder_load_file_match_regex",
        "default": "\.context$",
    },
    "profile_load_use_subfolders": {
        "type": "boolean",
        "default": False,
        "required": False,
        "target_key": "folder_load_use_subfolders"
    },
    "profile_load_ignore_hidden_files": {
        "type": "boolean",
        "default": True,
        "required": False,
        "target_key": "frecklet_load_use_subfolders"
    },
}
FRECKLET_LOAD_CONFIG_SCHEMA = {
    "frecklet_load_ignore_prefixes": {
        "type": "list",
        "default": [],
        "empty": True,
        "schema": {"type": "string"},
        "required": False,
        "target_key": "folder_load_ignore_file_prefixes",
    },
    "frecklet_load_ignore_postfixes": {
        "type": "list",
        "default": [],
        "empty": True,
        "schema": {"type": "string"},
        "required": False,
        "target_key": "folder_load_ignore_file_postfixes"
    },
    "frecklet_load_file_match_regex": {
        "type": "string",
        "required": False,
        "target_key": "folder_load_file_match_regex",
        "default": "\.frecklet$",
    },
    "frecklet_load_use_subfolders": {
        "type": "boolean",
        "default": True,
        "required": False,
        "target_key": "folder_load_use_subfolders"
    },
    "frecklet_load_ignore_hidden_files": {
        "type": "boolean",
        "default": True,
        "required": False,
        "target_key": "frecklet_load_use_subfolders"
    },
}

USE_COMMUNITY_CONF_ITEM = {
    "type": "boolean",
    "default": False,
    "doc": """Whether to allow the freckles community repositories.

The freckles community repositories are a collection of community-created and curated frecklets and resources.

TODO: list all repository urls        
""",
}

FRECKLES_GLOBAL_CONFIG_SCHEMA = {
    "accept_freckles_license": {
        "type": "boolean",
        "default": False,
        "doc": "Accept the license and acknowledge to not use the publicly licensed version of 'freckles' in combination with non-free software.",
    },
    "allow_remote": {
        "type": "boolean",
        "default": False,
        "doc": "Whether to allow remote repositories and resources.",
    },
    "use_community": USE_COMMUNITY_CONF_ITEM
}

FRECKLES_CONTEXT_CONFIG_SCHEMA = {
    "use_community": USE_COMMUNITY_CONF_ITEM,
    "adapters": {
        "type": "list",
        "default": ["nsbl"],
        "doc": "A list of freckles adapters to use in this context.",
    },
    "repo_aliases": {
        "doc": """A dict of repository aliases which can be used in the "repos" key.

        The dict is in the form: alias: list_of_urls.
        """,
        "type": "dict",
        "keyschema": {
            "type": "string",
            "empty": False,
            "forbidden": ["default", "community"],
        },
        "valueschema": {
            "type": "dict",
            "coerce": ensure_repo_dict,
            "schema": {
                "types": {"type": "list", "schema": {"type": "string"}},
                "repos": {"type": "list", "schema": {"type": "string"}},
            },
        },
    },
    "repos": {
        "type": "list",
        "schema": {
            "type": "dict",
            "coerce": ensure_repo_dict,
            "schema": {
                "types": {"type": "list", "schema": {"type": "string"}},
                "repos": {"type": "list", "schema": {"type": "string"}},
            },
        },
    },
}
