# -*- coding: utf-8 -*-

import io
import json
import os
from collections import Mapping, Iterable

from ruamel.yaml import YAML
from six import string_types

from freckles.defaults import ACCEPT_FRECKLES_LICENSE_KEYNAME, FRECKLES_CONFIG_DIR
from freckles.exceptions import FrecklesConfigException, FrecklesUnlockException
from freckles.frecklet.arguments import *  # noqa
from freckles.schemas import FRECKLES_CONTEXT_SCHEMA, PROFILE_LOAD_CONFIG_SCHEMA
from frutils.config.cnf import Cnf

# from .output_callback import DefaultCallback
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
    """

    DEFAULT_TING_CAST = ContextConfigTingCast

    @classmethod
    def load_configs(cls):

        cnf = Cnf({})
        cnf.add_interpreter("root_config", FRECKLES_CONTEXT_SCHEMA)

        profile_load_config = cnf.add_interpreter(
            "profile_load", PROFILE_LOAD_CONFIG_SCHEMA
        )
        configs = ContextConfigs.from_folders(
            "cnf_profiles",
            FRECKLES_CONFIG_DIR,
            load_config=profile_load_config,
            cnf=cnf,
        )

        return configs

    def __init__(self, repo_name, tingsets, cnf, **kwargs):

        # check whether freckles license is accepted
        self._default_config_path = os.path.join(FRECKLES_CONFIG_DIR, "default.context")
        try:
            with io.open(self._default_config_path, "r", encoding="utf-8") as f:
                default_context_dict = yaml.load(f)
                self._config_unlocked = (
                    default_context_dict.get(ACCEPT_FRECKLES_LICENSE_KEYNAME, False)
                    is True
                )
        except (Exception):
            self._config_unlocked = False

        if cnf is None:
            raise Exception("Base configuration object can't be None.")

        if "profile_load" not in cnf.get_interpreter_names():
            raise Exception("No 'profile_load' cnf interpreter available.")
        load_config = cnf.get_interpreter("profile_load")

        if "root_config" not in cnf.get_interpreter_names():
            raise Exception("No root_config profile interpreter in cnf.")

        self._cnf = cnf
        self._root_config = cnf.get_interpreter("root_config").config

        self._default_profile_values = None

        super(ContextConfigs, self).__init__(
            repo_name=repo_name,
            tingsets=tingsets,
            load_config=load_config,
            indexes=["filename_no_ext"],
        )

    def create_context_config(
        self, context_name, config_chain=None, extra_repos=None, use_community=False
    ):

        if config_chain is None:
            config_chain = []
        elif isinstance(config_chain, tuple):
            config_chain = list(config_chain)

        if isinstance(config_chain, (string_types, Mapping)):
            config_chain = [config_chain]
        elif not isinstance(config_chain, Iterable):
            config_chain = [config_chain]

        dict_chain = [self._root_config]
        if os.path.exists(self._default_config_path):
            # always use default config
            config_chain.insert(0, "default")

        for index, config in enumerate(config_chain):

            # check if string
            if isinstance(config, string_types):
                config = config.strip()

                if config in self.keys():

                    if not self._config_unlocked and config != "default":
                        raise FrecklesUnlockException(
                            "Access to context '{}' not allowed.".format(config)
                        )
                    # means we want the config from the file
                    config = self.get(config).config_dict

                elif not config.startswith("{") and "=" in config:
                    key, value = config.split("=", 1)
                    if value.lower() in ["true", "yes"]:
                        value = True
                    elif value.lower() in ["false", "no"]:
                        value = False
                    # elif "::" in value:
                    #     value = value.split("::")
                    else:
                        try:
                            value = int(value)
                        except (Exception):
                            # fine, we'll just use the string
                            # TODO: support lists
                            pass
                    config = {key: value}
                elif config.startswith("{"):
                    # trying to read json
                    try:
                        config = json.loads(config)
                    except (Exception):
                        raise Exception(
                            "Can't assemble profile configuration, don't know how to handle: {}".format(
                                config
                            )
                        )
                else:
                    if "=" not in config:
                        raise FrecklesConfigException(
                            msg="Could not assemble context configuration.",
                            reason="No configuration file '{}.context' in config dir.".format(
                                config
                            ),
                            solution="Create context config '{}.context' in '{}' or use correct configuration syntax if that is not what you intended.".format(
                                config, FRECKLES_CONFIG_DIR
                            ),
                            references={
                                "freckles configuration documentation": "https://freckles.io/doc/configuration"
                            },
                        )
                    raise Exception(
                        "Can't create profile configuration, invalid config: {}.".format(
                            config
                        )
                    )

            if isinstance(config, Mapping):
                dict_chain.append(config)
            else:
                raise Exception(
                    "Can't assemble profile configuration, unknown type '{}' for value '{}'".format(
                        type(config), config
                    )
                )

        cc = ContextConfig(
            alias=context_name,
            config_chain=dict_chain,
            extra_repos=extra_repos,
            use_community=use_community,
            config_unlocked=self._config_unlocked,
        )

        return cc


class ContextConfig(object):
    def __init__(
        self,
        alias,
        config_chain=None,
        extra_repos=None,
        use_community=False,
        config_unlocked=False,
    ):

        if config_chain is None:
            config_chain = []

        if len(config_chain) > 0:
            self._root_config = Cnf(config_chain[0])
        else:
            self._root_config = Cnf({})

        self._config_unlocked = config_unlocked
        self._alias = alias
        self._config_chain = config_chain
        self._extra_repos = extra_repos
        self._use_community = use_community

        merged = {}
        for d in config_chain:
            dict_merge(merged, d, copy_dct=False)

        repos_to_add = []
        if use_community:
            repos_to_add.append("community")

        if extra_repos:
            if isinstance(extra_repos, string_types):
                repos_to_add.append(extra_repos)
            else:
                repos_to_add.extend(list(extra_repos))

        merged.setdefault("repos", [])
        for repo in repos_to_add:
            merged["repos"].append(repo)

        self._config_dict = merged

        self._cnf = Cnf(self._config_dict)

        self.add_cnf_interpreter("context", FRECKLES_CONTEXT_SCHEMA)

    @property
    def cnf(self):
        return self._cnf

    @property
    def config_unlocked(self):
        return self._config_unlocked

    def add_cnf_interpreter(self, interpreter_name, schema):

        # we need that to compare with 'no config' option
        self._root_config.add_interpreter(interpreter_name, schema)
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

            orig_value = self._root_config.get_interpreter_value(
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
