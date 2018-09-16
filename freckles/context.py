# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import copy
import logging
import os
from collections import OrderedDict

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from six import string_types

from frutils.cnf import get_cnf
from luci.exceptions import NoSuchDictletException
from luci.luitem_index import LuItemIndex, LuItemMultiIndex, LuItemFolderIndex
from luci.readers import add_luitem_reader_profile
from .connectors.connectors import get_connectors
from .defaults import FRECKLES_CONFIG_PROFILES_DIR, MODULE_FOLDER, COMMUNITY_FOLDER, COMMUNITY_REPO_DESC
from .defaults import (
    FRECKLES_CONFIG_SCHEMA,
    FRECKLET_DEFAULT_READER_PROFILE,
    FRECKLET_PATH_DEFAULT_READER_PROFILE,
    FRECKLES_CNF_PROFILES,
    REPO_MANAGER_CONFIG_SCHEMA,
    DEFAULT_FRECKLES_ALIASES,
)
from .exceptions import FrecklesConfigException, FrecklesPermissionException
from .frecklet import Frecklet
from .repo_management import RepoManager

yaml = YAML(typ="safe")


log = logging.getLogger("freckles")

# FRECKLES_EXTRA_ABBREVS = {
#     "freckles-included": [MODULE_FOLDER, "/"],
# }
# FRECKLES_ABBREVS = generate_custom_abbrevs(FRECKLES_EXTRA_ABBREVS)


add_luitem_reader_profile("frecklets", FRECKLET_DEFAULT_READER_PROFILE)
add_luitem_reader_profile("frecklets_path", FRECKLET_PATH_DEFAULT_READER_PROFILE)


class FreckletConnectorIndex(LuItemIndex):
    """Special index to catch non-indexed files/frecklets"""

    def __init__(self, connectors, task_type_whitelist=None, task_type_blacklist=None):

        super(FreckletConnectorIndex, self).__init__(
            item_type="frecklet", alias="freckles_catchall"
        )

        self.connectors = connectors
        self.allow_multipe_matches = False
        self.task_type_whitelist = task_type_whitelist
        self.task_type_blacklist = task_type_blacklist

    def update_index(self):

        pass

    def get_pkg_metadata(self, name):
        log.debug("Trying to find dynamic frecklet named: {}".format(name))
        results = OrderedDict()
        for c_name, connector in self.connectors.items():

            log.debug("Using connector: {}".format(c_name))
            if not connector.supports_allowed_task_type(
                task_type_whitelist=self.task_type_whitelist,
                task_type_blacklist=self.task_type_blacklist,
            ):
                log.debug("... not used because of black/whitelist")
                continue

            frecklet_md = connector.get_frecklet_metadata(name)
            if frecklet_md is not None:
                results[c_name] = frecklet_md

        result = None
        if len(results) > 1:
            first_key = next(iter(results))
            msg = "Multiple connectors produced frecklets for item '{}': {}. Using first match: {}".format(
                name, results.keys(), first_key
            )
            if self.allow_multipe_matches:
                log.warn(msg)
            else:
                raise Exception(msg)
            result = results[first_key]
            return result
        elif len(results) == 1:
            result = results[next(iter(results))]
            return result
        else:
            return None

    def get_available_packages(self):

        return None

    # def calculate_control_vars(self):
    #
    #     result = {}
    #
    #     no_run = self.current_control_vars.get("no_run", None)
    #
    #     if no_run is None:
    #         if "no_run" not in self.context.cnf.config_dict.keys():
    #             no_run = False
    #         else:
    #             no_run = self.context.cnf.config_dict["no_run"]
    #     else:
    #         no_run = no_run
    #
    #     result["no_run"] = no_run
    #
    #     host = self.current_control_vars.get("host", None)
    #     if host is not None:
    #         result["host"] = host
    #
    #     output_format = self.current_control_vars.get("output", None)
    #     if output_format is None:
    #         output_format = "default"
    #     result["run_callback"] = output_format
    #
    #     elevated = self.current_control_vars.get("elevated", None)
    #     if elevated is not None:
    #         if elevated == "elevated":
    #             result["elevated"] = True
    #         elif elevated == "not_elevated":
    #             result["elevated"] = False
    #         else:
    #             log.warn("Invalid value for 'elevated' key: {}".format(elevated))
    #
    #     return result


def load_profile_from_disk(profile_name):

    abs_path = os.path.abspath(
        os.path.join(
            FRECKLES_CONFIG_PROFILES_DIR, "{}.{}".format(profile_name, "profile")
        )
    )
    if os.path.exists(abs_path) and os.path.isfile(abs_path):
        log.debug("Loading profile from file: {}".format(abs_path))
        with open(abs_path, "r") as f:
            profile_dict = yaml.load(f)  # nosec
    else:
        profile_dict = None

    return profile_dict


class FrecklesContext(object):
    """Wrapper object to hold connectors as well as global & connector-specific configurations.

    Args:
        config_profiles (list): list of profile names, which will be merged on top of each other
        **kwargs: additional configuration which will be layered on top of the merged profiles
    """

    def __init__(self, config_profiles, freckles_repos=None, **kwargs):

        self.default_profile = load_profile_from_disk("default")
        self.vanilla_profile = False
        if self.default_profile is None:
            self.vanilla_profile = True
            self.default_profile = FRECKLES_CNF_PROFILES["default"]

            for t_config in config_profiles:
                if t_config != "default":
                    raise FrecklesPermissionException(
                        "No permission to change configuration. Create a custom default profile first. Check https://freckles.io/configuration for more details."
                    )

            if freckles_repos and freckles_repos != ["community"]:
                raise FrecklesPermissionException(
                    "No permission to use custom repositories. Create a custom default profile first. Check https://freckles.io/configuration for more details."
                )

        self.cnf = get_cnf(
            config_profiles=config_profiles,
            additional_values=kwargs,
            available_profiles_dict={"default": self.default_profile},
            profiles_dir=FRECKLES_CONFIG_PROFILES_DIR,
        )
        # self.current_control_vars = None
        self.cnf_interpreter = self.cnf.add_cnf_interpreter(
            "global", FRECKLES_CONFIG_SCHEMA
        )

        self.ignore_invalid_repos = self.cnf.config_dict.get(
            "ignore_invalid_repos", True
        )

        rm_cnf_interpreter = self.cnf.add_cnf_interpreter(
            "repo_manager", REPO_MANAGER_CONFIG_SCHEMA
        )
        self.repo_interpreter = rm_cnf_interpreter

        # if freckles_repos is None or not freckles_repos:
        #     freckles_repos = DEFAULT_FRECKLES_REPOS
        default_freckles_repos = rm_cnf_interpreter.get_cnf_value("context_repos")

        self.set_config_value(
            "context_repos", default_freckles_repos + list(freckles_repos)
        )

        self.repo_manager = RepoManager(rm_cnf_interpreter)
        self.repo_manager.add_alias_map(DEFAULT_FRECKLES_ALIASES)

        # special case for community
        if "community" in freckles_repos:
            self.repo_manager.get_repo(COMMUNITY_REPO_DESC)

        self.connectors = OrderedDict()
        self.indexes = []
        self.connector_map = {}
        temp_connectors = {}

        for connector in get_connectors():

            # connector.set_config(self.connector_config.get(connector.name, {}))
            temp_connectors[connector.name] = connector

        allowed_connectors = self.cnf_interpreter.get_cnf_value(
            "allowed_connectors", list(temp_connectors.keys())
        )

        for c_name in allowed_connectors:

            temp = temp_connectors.get(c_name, None)
            if temp is None:
                continue
            self.connectors[c_name] = temp
            # special case for the internal 'freckles' connector
            if c_name == "freckles":
                temp.set_context(self)

            interpreter = self.cnf.add_cnf_interpreter(c_name, temp.get_cnf_schema())
            temp.set_cnf_interpreter(interpreter)
            supported_types = temp.get_supported_task_types()
            for t in supported_types:
                if t not in self.connector_map.keys():
                    self.connector_map[t] = c_name
                else:
                    log.warn(
                        "More than one connector supports task type '{}', ignoring: {}".format(
                            t, connector.name
                        )
                    )

            aliases = temp.get_repo_aliases()
            supported_types = temp.get_supported_repo_content_types()
            self.repo_manager.add_alias_map(aliases, content_types=supported_types)

        self.connector_indexes = {}

        included_frecklets = os.path.join(MODULE_FOLDER, "external", "frecklets")
        try:
            index = LuItemFolderIndex(
                url=included_frecklets,
                pkg_base_url=included_frecklets,
                item_type="frecklet",
                reader_params={
                    "reader_profile": "frecklets",
                    "ignore_invalid_dictlets": True,
                },
                ignore_invalid_pkg_metadata=True,
            )
            self.indexes.append(index)

        except (NoSuchDictletException) as e:
            log.debug(
                "Can't create index '{}': {}".format(included_frecklets, e),
                exc_info=True,
            )
            if not self.ignore_invalid_repos:
                raise e

        frecklet_repos = self.repo_manager.get_repo_descs(
            only_content_types=["frecklets"],
            ignore_invalid_repos=self.ignore_invalid_repos,
        )

        for repo in frecklet_repos:

            path = self.repo_manager.get_repo(repo)
            if path is None:
                log.debug("Not a valid repo, or repo doesn't exist: {}".format(repo))
                continue

            try:
                index = LuItemFolderIndex(
                    url=path,
                    pkg_base_url=path,
                    item_type="frecklet",
                    reader_params={
                        "reader_profile": "frecklets",
                        "ignore_invalid_dictlets": True,
                    },
                    ignore_invalid_pkg_metadata=True,
                )
                self.indexes.append(index)
            except (Exception) as e:
                log.debug("Can't create index '{}': {}".format(path, e), exc_info=True)
                log.warn("Error parsing frecklet repo '{}': {}".format(path, e))
                if not self.ignore_invalid_repos:
                    raise e

        for c_name, connector in self.connectors.items():

            supported_types = connector.get_supported_repo_content_types()
            if "frecklets" in supported_types:
                supported_types.remove("frecklets")

            if not supported_types:
                continue
            repos = self.repo_manager.get_repo_descs(
                only_content_types=supported_types,
                ignore_invalid_repos=self.ignore_invalid_repos,
            )

            # TODO: don't do this multiple time for the same repo
            for r in repos:
                path = self.repo_manager.get_repo(r)
                if path is None:
                    log.debug("Not a valid repo, or repo doesn't exist: {}".format(r))
                    continue
            connector.set_content_repos(repos)

            indexes = connector.get_indexes()
            self.connector_indexes[c_name] = indexes

            if not indexes:
                continue

            self.indexes.extend(indexes)

        task_type_whitelist = self.cnf_interpreter.get_cnf_value("task_type_whitelist")
        task_type_blacklist = self.cnf_interpreter.get_cnf_value("task_type_blacklist")
        allow_dynamic_frecklets = self.cnf_interpreter.get_cnf_value(
            "allow_dynamic_frecklets"
        )

        if allow_dynamic_frecklets:
            # last index is the one that catches everything that wasn't caught before
            self.indexes.append(
                FreckletConnectorIndex(
                    self.connectors,
                    task_type_whitelist=task_type_whitelist,
                    task_type_blacklist=task_type_blacklist,
                )
            )

        self.index = LuItemMultiIndex(
            item_type="frecklet",
            indexes=self.indexes,
            alias="freckles_multi",
            ignore_invalid_pkg_metadata=True,
        )

    def get_interpreter_map(self):

        result = OrderedDict()
        result["global"] = {"interpreter": self.cnf_interpreter, "type": "global"}
        result["repo_manager"] = {
            "interpreter": self.repo_interpreter,
            "type": "repo_manager",
        }
        for key, connector in self.connectors.items():
            result[key] = {
                "interpreter": connector.cnf_interpreter,
                "type": "connector",
            }

        return result

    def set_config_value(self, key, value):
        """Sets a configuration value.

        Args:
            key (str): the key
            value: the value
        """

        self.cnf.set_cnf_key(key, value)

    def create_frecklet(self, frecklet_path_or_name_or_metadata):

        if isinstance(frecklet_path_or_name_or_metadata, string_types):

            # if is_url_or_abbrev(frecklet_path_or_name_or_metadata):
            #     self.repo_manager.get_remote_dict()

            if os.path.isfile(frecklet_path_or_name_or_metadata):
                path = os.path.abspath(frecklet_path_or_name_or_metadata)
                index = LuItemFolderIndex(
                    url=path,
                    item_type="frecklet",
                    alias=frecklet_path_or_name_or_metadata,
                    pkg_base_url=frecklet_path_or_name_or_metadata,
                    reader_params={"reader_profile": "frecklets_path"},
                )
                frecklet = index.get_pkg(path)
                frecklet.set_index(self.index)
            else:
                frecklet = self.index.get_pkg(frecklet_path_or_name_or_metadata)
            if frecklet is None:
                try:
                    frecklet_metadata = self.repo_manager.get_remote_dict(
                        frecklet_path_or_name_or_metadata
                    )
                except (FrecklesConfigException):
                    raise FrecklesConfigException(
                        "No such frecklet or invalid metadata."
                    )

                frecklet = Frecklet(frecklet_metadata, index=self.index)
        elif isinstance(
            frecklet_path_or_name_or_metadata, (dict, OrderedDict, CommentedMap)
        ):
            frecklet = Frecklet(frecklet_path_or_name_or_metadata, index=self.index)
        else:
            log.debug(
                "Invalid object type: {}".format(frecklet_path_or_name_or_metadata)
            )
            raise Exception(
                "Invalid object type '{}', can't create frecklet.".format(
                    type(frecklet_path_or_name_or_metadata)
                )
            )

        if frecklet is None:
            raise FrecklesConfigException(
                "Could not find frecklet '{}'".format(frecklet_path_or_name_or_metadata)
            )

        return copy.deepcopy(frecklet)

    def get_frecklet_names(self):

        return self.index.get_pkg_names()

    def get_connector(self, name):

        return self.connectors.get(name, None)

    # def set_control_vars(self, control_vars):
    #
    #     self.current_control_vars = control_vars

    def calculate_control_vars(self):

        result = {}

        no_run = self.current_control_vars.get("no_run", None)

        if no_run is None:
            if "no_run" not in self.context.cnf.config_dict.keys():
                no_run = False
            else:
                no_run = self.context.cnf.config_dict["no_run"]
        else:
            no_run = no_run

        result["no_run"] = no_run

        host = self.current_control_vars.get("host", None)
        if host is not None:
            result["host"] = host

        output_format = self.current_control_vars.get("output", None)
        if output_format is None:
            output_format = "default"
        result["run_callback"] = output_format

        elevated = self.current_control_vars.get("elevated", None)
        if elevated is not None:
            if elevated == "elevated":
                result["elevated"] = True
            elif elevated == "not_elevated":
                result["elevated"] = False
            else:
                log.warn("Invalid value for 'elevated' key: {}".format(elevated))

        return result
