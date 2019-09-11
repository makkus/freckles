# -*- coding: utf-8 -*-

import io
import json
import os
from collections import Mapping, Iterable

from ruamel.yaml import YAML

from freckles.defaults import FRECKLES_CONFIG_DIR, FRECKLES_CONFIG_UNLOCK_FILES
from freckles.exceptions import FrecklesUnlockException
from freckles.frecklet.arguments import *  # noqa
from freckles.schemas import FRECKLES_CONTEXT_SCHEMA, PROFILE_LOAD_CONFIG_SCHEMA
from frutils.config.cnf import Cnf

from frutils.exceptions import FrklException
from ting.ting_attributes import (
    FrontmatterAndContentAttribute,
    DictContentAttribute,
    FileStringContentAttribute,
    ValueAttribute,
)
from ting.ting_cast import TingCast
from ting.tings import TingTings

log = logging.getLogger("freckles")

yaml = YAML()

UNLOCK_STRING = "I know what I'm doing and this is not just copy and pasted from a random blog post on the internet. Also, I accept the freckles license."


def is_unlocked():

    unlocked = False

    for f in FRECKLES_CONFIG_UNLOCK_FILES:

        if not os.path.isfile(f):
            continue

        with io.open(f, "r", encoding="utf-8") as uf:
            content = uf.read()

            if UNLOCK_STRING.lower() in content.lower():
                unlocked = True
                break
    return unlocked


def unlock():

    f = FRECKLES_CONFIG_UNLOCK_FILES[0]
    with io.open(f, "w", encoding="utf-8") as uf:
        uf.write(UNLOCK_STRING)


def lock():

    for f in FRECKLES_CONFIG_UNLOCK_FILES:

        if os.path.isfile(f):
            os.unlink(f)


DEFAULT_CONFIG_DICTS = {
    "default": {"parents": [{"repos": ["default", "user", "./.freckles"]}]},
    "community": {
        "parents": [
            "default",
            {"repos": ["default", "community", "user", "./.freckles"]},
        ]
    },
    "latest": {
        "parents": [
            "default",
            {
                "repos": [
                    "frecklet::gl:frecklets/frecklets-nsbl-default::develop::",
                    "tempting::gl:frecklets/temptings-default::develop::",
                    "ansible-role::gl:frecklets/frecklets-nsbl-default-resources::develop::",
                    "ansible-tasklist::gl:frecklets/frecklets-nsbl-default-resources::develop::",
                    "user",
                    "./.freckles",
                ]
            },
        ]
    },
    "latest-community": {
        "parents": [
            "default",
            {
                "repos": [
                    "frecklet::gl:frecklets/frecklets-nsbl-default::develop::",
                    "tempting::gl:frecklets/temptings-default::develop::",
                    "ansible-role::gl:frecklets/frecklets-nsbl-default-resources::develop::",
                    "ansible-tasklist::gl:frecklets/frecklets-nsbl-default-resources::develop::",
                    "frecklet::gl:frecklets/frecklets-nsbl-community::develop::",
                    "ansible-role::gl:frecklets/frecklets-nsbl-community-resources::develop::",
                    "ansible-tasklist::gl:frecklets/frecklets-nsbl-community::develop::",
                    "user",
                    "./.freckles",
                ]
            },
        ]
    },
    "shell": {"parents": ["default", {"adapters": ["shell", "freckles"]}]},
    "debug": {
        "parents": [
            "default",
            {
                "keep_run_folder": True,
                "force_show_log": True,
                "create_current_symlink": True,
                "callback": "default::full",
            },
        ]
    },
    "empty": {"parents": [{"repos": []}]},
}


class ContextConfigTingCast(TingCast):
    """A :class:`TingCast` to create freckles profiles by reading yaml files."""

    CNF_PROFILE_ATTRIBUTES = [
        FileStringContentAttribute(target_attr_name="ting_content"),
        FrontmatterAndContentAttribute(
            content_name="content", source_attr_name="ting_content"
        ),
        ValueAttribute("config_dict", source_attr_name="content"),
        # CnfTingAttribute(),
        DictContentAttribute(
            source_attr_name="content",
            dict_name="config_dict",
            default={},
            copy_default=True,
        ),
    ]

    def __init__(self):

        super(ContextConfigTingCast, self).__init__(
            class_name="ContextConfigProfile",
            ting_attributes=ContextConfigTingCast.CNF_PROFILE_ATTRIBUTES,
            ting_id_attr="filename_no_ext",
        )


class ContextConfigs(TingTings):
    """A class to manage freckles profiles.

    This reads all '*.profile' files in the freckles config folder. Those are later used to create a freckles context
    (per profile). It also checks whether there exists a 'default.profile' file with the 'accept_freckles_license' value
    set to 'true'. Only if that is the case will it allow custom profiles (mainly for security reasons - the user should
    explicitely accept that certain configurations can be insecure).

    Args:
        repos (str, list): a list of local folders containing '*.context' files
    Returns:
        TingTings: an index of config files
    """

    DEFAULT_TING_CAST = ContextConfigTingCast

    @classmethod
    def load_user_context_configs(cls, repos=None):

        if repos is None:
            repos = FRECKLES_CONFIG_DIR

        cnf = Cnf({})
        # this is the 'root' configuration for the actual config objectx
        cnf.add_interpreter("root_config", FRECKLES_CONTEXT_SCHEMA)

        profile_load_config = cnf.add_interpreter(
            "profile_load", PROFILE_LOAD_CONFIG_SCHEMA
        )

        configs = ContextConfigs.from_folders(
            "user_contexts", repos, load_config=profile_load_config, cnf=cnf
        )

        return configs

    def __init__(self, repo_name, tingsets, cnf, default_config_dicts=None, **kwargs):

        if default_config_dicts is None:
            default_config_dicts = DEFAULT_CONFIG_DICTS

        self.default_config_dicts = copy.deepcopy(default_config_dicts)

        invalid = []
        for tings in tingsets:
            for ting in tings.values():
                if ting.id in self.default_config_dicts.keys():
                    invalid.append(ting.id)

        if invalid:
            raise FrklException(
                msg="Invalid context name(s) for '{}': {}".format(
                    repo_name, ", ".join(invalid)
                ),
                reason="Context config files named after reserved context names in repo: {}".format(
                    ", ".join(repo_name)
                ),
                solution="Rename affected context configs.",
            )

        if cnf is None:
            raise Exception("Base configuration object can't be None.")

        if "profile_load" not in cnf.get_interpreter_names():
            raise Exception("No 'profile_load' cnf interpreter available.")
        load_config = cnf.get_interpreter("profile_load")

        if "root_config" not in cnf.get_interpreter_names():
            raise Exception("No root_config profile interpreter in cnf.")

        self._cnf = cnf
        self._root_config = cnf.get_interpreter("root_config").config

        super(ContextConfigs, self).__init__(
            repo_name=repo_name,
            tingsets=tingsets,
            load_config=load_config,
            indexes=["filename_no_ext"],
        )

    def get_config_type(self, config_obj):

        if isinstance(config_obj, string_types):
            config_obj = config_obj.strip()
            if config_obj.startswith("{") and config_obj.endswith("}"):
                return "json"
            elif "=" in config_obj:
                return "key_value"
            elif config_obj in self.default_config_dicts.keys():
                return "default_config_dict"
            elif config_obj in self.keys():
                return "user_config_dict"
            else:
                all_context_names = list(self.default_config_dicts.keys()) + list(
                    self.keys()
                )
                raise FrklException(
                    msg="Can't determine config type for string '{}'".format(
                        config_obj
                    ),
                    solution="Value needs to be either json string, key/value pair (separated with '='), or the name of a default or user context config: {}".format(
                        ", ".join(all_context_names)
                    ),
                )
        elif isinstance(config_obj, Mapping):
            return "dict"
        else:
            raise FrklException(
                msg="Invalid config type '{}' for object: {}".format(
                    type(config_obj), config_obj
                ),
                solution="Needs to be either string, or dict.",
            )

    def resolve_context_config_dict(self, config_chain, current_config_dict=None):

        if current_config_dict is None:
            current_config_dict = {}

        for config in config_chain:

            config_type = self.get_config_type(config)

            if config_type == "dict":
                config_dict = copy.deepcopy(config)

            elif config_type == "json":
                try:
                    config_dict = json.loads(config)
                except (Exception):
                    raise FrklException(
                        msg="Can't parse json config object: {}".format(config),
                        solution="Check json format.",
                    )

            elif config_type == "key_value":
                key, value = config.split("=", 1)
                if value == "":
                    raise FrklException(
                        msg="No value provided for key/value config object: {}".format(
                            config
                        )
                    )
                if value.lower() in ["true", "yes"]:
                    value = True
                elif value.lower() in ["false", "no"]:
                    value = False
                else:
                    try:
                        value = int(value)
                    except (Exception):
                        # fine, we'll just use the string
                        # TODO: support lists
                        pass
                config_dict = {key: value}

            elif config_type == "default_config_dict":
                config_dict = copy.deepcopy(self.default_config_dicts[config])
            elif config_type == "user_config_dict":
                config_dict = copy.deepcopy(self[config])
            else:
                raise FrklException(msg="Invalid config type: {}".format(config_type))

            config_parents = config_dict.pop("parents", [])
            config_extra_repos = config_dict.pop("extra_repos", [])
            if isinstance(config_extra_repos, string_types) or not isinstance(
                config_extra_repos, Sequence
            ):
                config_extra_repos = [config_extra_repos]

            self.resolve_context_config_dict(
                config_chain=config_parents, current_config_dict=current_config_dict
            )
            dict_merge(current_config_dict, config_dict, copy_dct=False)

            if config_extra_repos:
                current_config_dict.setdefault("repos", []).extend(config_extra_repos)

        return current_config_dict

    def create_context_config(self, context_name, config_chain=None, extra_repos=None):
        """Creates a new context configuration out of the provided config_chain and extra repos.

        If the config_chain argument is empty, the 'default' profile will be used.
        """

        if config_chain is None:
            config_chain = []
        elif isinstance(config_chain, tuple):
            config_chain = list(config_chain)

        if isinstance(config_chain, (string_types, Mapping)):
            config_chain = [config_chain]
        elif not isinstance(config_chain, Iterable):
            config_chain = [config_chain]

        if not config_chain or config_chain[0] != "default":
            config_chain.insert(0, "default")

        final_config = self.resolve_context_config_dict(config_chain=config_chain)

        cc = ContextConfig(
            alias=context_name, config_dict=final_config, extra_repos=extra_repos
        )

        return cc


class ContextConfig(object):
    def __init__(self, alias, config_dict, extra_repos=None, config_unlocked=None):

        self._default_config = Cnf({})
        self._root_config = Cnf(config_dict)

        if isinstance(config_unlocked, bool):
            self._config_unlocked = config_unlocked
        else:
            self._config_unlocked = is_unlocked()

        self._alias = alias
        if not extra_repos:
            extra_repos = []

        if isinstance(extra_repos, string_types) or not isinstance(
            extra_repos, Sequence
        ):
            extra_repos = [extra_repos]

        self._extra_repos = extra_repos

        config_dict.setdefault("repos", [])
        for r in self._extra_repos:
            if r not in config_dict["repos"]:
                config_dict["repos"].append(r)
        self._config_dict = config_dict

        self._cnf = Cnf(self._config_dict)

        self.add_cnf_interpreter("context", FRECKLES_CONTEXT_SCHEMA)

    @property
    def cnf(self):
        return self._cnf

    def add_cnf_interpreter(self, interpreter_name, schema):

        # we need that to compare with 'no config' option
        self._root_config.add_interpreter(interpreter_name, schema)
        self._default_config.add_interpreter(interpreter_name, schema)
        self._cnf.add_interpreter(interpreter_name, schema)

    def config(self, interpreter_name, *overlays):

        if interpreter_name is None:
            interpreter_name = "context"

        interpreter = self._cnf.get_interpreter(interpreter_name)

        config = interpreter.overlay(*overlays)

        if self._config_unlocked:
            return config

        not_allowed = []
        for k, v in config.items():
            tags = interpreter.get_tags(k)

            value = interpreter.get(k)
            if "safe" not in tags:
                orig_value = self._root_config.get_interpreter_value(
                    interpreter_name, k, None
                )
                if value != orig_value:
                    not_allowed.append(k)

        if not_allowed:
            raise FrecklesUnlockException(
                "Access prevented to configuration key(s): {}.".format(
                    ", ".join(not_allowed)
                )
            )

        return config

    def config_value(self, key, interpreter_name=None):

        if interpreter_name is None:
            interpreter_name = "context"

        # print(interpreter_name)
        interpreter = self._cnf.get_interpreter(interpreter_name)

        if self._config_unlocked:
            return interpreter.get(key)

        # check whether this config value is 'safe'
        try:
            tags = interpreter.get_tags(key)
        except (Exception):
            tags = []

        value = interpreter.get(key)
        if "safe" not in tags:

            orig_value = self._default_config.get_interpreter_value(
                interpreter_name, key, None
            )

            if value != orig_value:
                val = str(value)
                if len(val) < 12:
                    val = " with (non-default) value '{}'".format(val)
                raise FrecklesUnlockException(
                    "Setting of configuration key '{}'{} not allowed.".format(key, val)
                )

        return value
