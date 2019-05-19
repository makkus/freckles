# -*- coding: utf-8 -*-
import io
import os
import shutil
import time
import uuid
from collections import Mapping, Sequence
from datetime import datetime

from plumbum import local
from ruamel.yaml import YAML
from six import string_types

from freckles.adapters.adapters import create_adapter
from freckles.defaults import (
    MIXED_CONTENT_TYPE,
    FRECKLES_CACHE_BASE,
    FRECKLES_RUN_INFO_FILE,
    ACCEPT_FRECKLES_LICENSE_KEYNAME,
    FRECKLES_SHARE_DIR,
    FRECKLES_CONFIG_DIR,
    FRECKLES_EXTRA_LOOKUP_PATHS,
)
from freckles.exceptions import FrecklesConfigException, FrecklesPermissionException
from freckles.frecklet.arguments import *  # noqa
from freckles.frecklet.frecklet import FRECKLET_LOAD_CONFIG
from frkl.utils import expand_string_to_git_details
from frkl_pkg import FrklPkg
from frutils import (
    is_url_or_abbrev,
    DEFAULT_URL_ABBREVIATIONS_REPO,
    calculate_cache_location_for_url,
    readable,
)

# from .output_callback import DefaultCallback
from frutils.frutils import auto_parse_string
from frutils.tasks.callback import load_callback
from frutils.tasks.tasks import Tasks
from ting.tings import TingTings

log = logging.getLogger("freckles")

yaml = YAML()

# class CnfTingAttribute(TingAttribute):
#     """Creates a :class:`Cnf` attribute from the dict value of the 'config_dict' attribute."""
#
#     def requires(self):
#
#         return ["config_dict"]
#
#     def provides(self):
#
#         return ["cnf"]
#
#     def get_attribute(self, ting, attribute_name=None):
#
#         return Cnf(config_dict=ting.config_dict)


# class CnfProfileTingCast(TingCast):
#     """A :class:`TingCast` to create freckles profiles by reading yaml files."""
#
#     CNF_PROFILE_ATTRIBUTES = [
#         FileStringContentAttribute(target_attr_name="ting_content"),
#         FrontmatterAndContentAttribute(
#             content_name="content", source_attr_name="ting_content"
#         ),
#         ValueAttribute("config_dict", source_attr_name="content"),
#         # CnfTingAttribute(),
#         DictContentAttribute(
#             source_attr_name="content",
#             dict_name="config_dict",
#             default={},
#             copy_default=True,
#         ),
#     ]
#
#     def __init__(self):
#
#         super(CnfProfileTingCast, self).__init__(
#             class_name="CnfProfile",
#             ting_attributes=CnfProfileTingCast.CNF_PROFILE_ATTRIBUTES,
#             ting_id_attr="filename_no_ext",
#         )
#
#
# class CnfProfiles(TingTings):
#     """A class to manage freckles profiles.
#
#     This reads all '*.profile' files in the freckles config folder. Those are later used to create a freckles context
#     (per profile). It also checks whether there exists a 'default.profile' file with the 'accept_freckles_license' value
#     set to 'true'. Only if that is the case will it allow custom profiles (mainly for security reasons - the user should
#     explicitely accept that certain configurations can be insecure).
#     """
#
#     DEFAULT_TING_CAST = CnfProfileTingCast
#
#     # LOAD_CONFIG_SCHEMA = PROFILE_LOAD_CONFIG_SCHEMA
#
#     def __init__(self, repo_name, tingsets, cnf, **kwargs):
#
#         if cnf is None:
#             raise Exception("Base configuration object can't be None.")
#
#         if "profile_load" not in cnf.get_interpreter_names():
#             raise Exception("No 'profile_load' cnf interpreter available.")
#         load_config = cnf.get_interpreter("profile_load")
#
#         if "root_config" not in cnf.get_interpreter_names():
#             raise Exception("No root_config profile interpreter in cnf.")
#
#         if (
#             "default_profile"
#             in cnf.get_interpreter("root_config").get_interpreter_names()
#         ):
#             # not sure if this is necessary, might take that out later
#             raise Exception(
#                 "Configuration already contains a 'default_profile' interpreter."
#             )
#
#         self._root_config = cnf.get_interpreter("root_config")
#
#         self._default_profile_values = None
#
#         super(CnfProfiles, self).__init__(
#             repo_name=repo_name,
#             tingsets=tingsets,
#             load_config=load_config,
#             indexes=["filename_no_ext"],
#         )
#
#     @property
#     def root_config(self):
#
#         return self._root_config
#
#     @property
#     def default_profile_dict(self):
#
#         if self._default_profile_values is not None:
#             return self._default_profile_values
#
#         if "default" not in self.keys():
#             return self._root_config.config
#
#         default_config = self["default"].config_dict
#
#         license_accepted = default_config.get("accept_freckles_license", False)
#         if not license_accepted:
#             raise Exception(
#                 "The initial freckles configuration is locked. Use the following command to unlock:\n\nfreckles config unlock\n\nFor more information, please visit: https://freckles.io/docs/configuration."
#             )
#
#         self._default_profile_values = dict(default_config)
#         for k, v in self._root_config.config.items():
#             if k not in self._default_profile_values.keys():
#                 self._default_profile_values[k] = v
#
#         return self._default_profile_values
#
#     def license_accepted(self):
#
#         if "default" not in self.keys():
#             return False
#
#         default_config = self["default"].config_dict
#         license_accepted = default_config.get("accept_freckles_license", False)
#         return license_accepted
#
#     def _get_profile_dict(self, profile_name="default"):
#
#         if profile_name == "default":
#             return self.default_profile_dict
#
#         if not self.license_accepted() and profile_name != "default":
#             raise Exception(
#                 "The initial freckles configuration is locked. Use the following command to unlock:\n\nfreckles config unlock\n\nFor more information, please visit: https://freckles.io/docs/configuration."
#             )
#
#         result = self.get(profile_name)
#
#         if not result:
#             raise Exception("No context named '{}' available.".format(profile_name))
#
#         return result.config_dict
#
#     def create_profile_cnf(self, profile_configs, extra_repos=None):
#
#         if isinstance(profile_configs, (string_types, Mapping)):
#             profile_configs = [profile_configs]
#         elif not isinstance(profile_configs, Iterable):
#             profile_configs = [profile_configs]
#
#         # if len(profile_list) == 1 and isinstance(profile_list[0], string_types) and profile_list[0] in self.get_profile_names():
#         #     return self.get_profile_cnf(profile_list[0])
#
#         result = {}
#         for profile in profile_configs:
#
#             if isinstance(profile, string_types):
#                 profile = profile.strip()
#                 if not self.license_accepted() and profile == "default":
#                     profile = self.default_profile_dict
#                 elif not self.license_accepted() and profile in self.keys():
#                     raise Exception(
#                         "The initial freckles configuration is locked, so can't open context configuration '{}'. Use the following command to unlock:\n\nfreckles config unlock\n\nFor more information, please visit: https://freckles.io/docs/configuration.".format(
#                             profile
#                         )
#                     )
#                 elif self.license_accepted() and profile in self.get_profile_names():
#                     profile = self._get_profile_dict(profile)
#                 elif not profile.startswith("{") and "=" in profile:
#                     key, value = profile.split("=", 1)
#                     if value.lower() in ["true", "yes"]:
#                         value = True
#                     elif value.lower() in ["false", "no"]:
#                         value = False
#                     # elif "::" in value:
#                     #     value = value.split("::")
#                     else:
#                         try:
#                             value = int(value)
#                         except (Exception):
#                             # raise Exception(
#                             #     "Can't assemble profile configuration, unknown type for: {}".format(
#                             #         value
#                             #     )
#                             # )
#                             pass
#                     profile = {key: value}
#
#                 elif profile.startswith("{"):
#                     # trying to read json
#                     try:
#                         profile = json.loads(profile)
#                     except (Exception):
#                         raise Exception(
#                             "Can't assemble profile configuration, don't know how to handle: {}".format(
#                                 profile
#                             )
#                         )
#                 else:
#                     raise Exception(
#                         "Can't create profile configuration, invalid config: {}.".format(
#                             profile
#                         )
#                     )
#
#             if isinstance(profile, Mapping):
#
#                 dict_merge(result, dict(profile), copy_dct=False)
#             else:
#                 raise Exception(
#                     "Can't assemble profile configuration, unknown type '{}' for value '{}'".format(
#                         type(profile), profile
#                     )
#                 )
#
#         if extra_repos:
#             if isinstance(extra_repos, string_types):
#                 extra_repos = [extra_repos]
#             else:
#                 extra_repos = list(extra_repos)
#             result["repos"] = list(result["repos"]) + extra_repos
#
#         return Cnf(config_dict=result)
#
#     def get_profile_names(self):
#
#         if not self.license_accepted():
#             return ["default"]
#
#         else:
#             names = list(self.get_ting_names())
#             if "default" not in names:
#                 names.append("default")
#
#             return sorted(names)


def startup_housekeeping():

    if not os.path.exists(FRECKLES_CONFIG_DIR):
        os.makedirs(FRECKLES_CONFIG_DIR)
    else:
        if not os.path.isdir(os.path.realpath(FRECKLES_CONFIG_DIR)):
            raise Exception(
                "Freckles config location exists and is not a directory: '{}'".format(
                    FRECKLES_CONFIG_DIR
                )
            )

    if not os.path.exists(FRECKLES_SHARE_DIR):
        os.makedirs(FRECKLES_SHARE_DIR)
    else:
        if not os.path.isdir(os.path.realpath(FRECKLES_SHARE_DIR)):
            raise Exception(
                "Freckles runtime data folder exists and is not a directory: '{}'".format(
                    FRECKLES_SHARE_DIR
                )
            )

    os.chmod(FRECKLES_SHARE_DIR, 0o0700)

    if os.path.exists(FRECKLES_CONFIG_DIR):
        os.chmod(FRECKLES_CONFIG_DIR, 0o0700)


class FrecklesContext(object):
    def __init__(self, context_name, config):

        startup_housekeeping()

        self._context_name = context_name
        self._config = config

        self._frecklet_index = None
        self._run_info = {}

        if os.path.exists(FRECKLES_RUN_INFO_FILE):
            with io.open(FRECKLES_RUN_INFO_FILE, encoding="utf-8") as f:

                self._run_info = yaml.load(f)

        # from config
        # self._callback = DefaultCallback(profile="verbose")
        # self._callback = SimpleCallback()
        self._callbacks = []
        callback_config = self.config_value("callback")

        if isinstance(callback_config, string_types):
            if "::" in callback_config:
                callback_config, profile = callback_config.split("::")
                callback_config = [{callback_config: {"profile": profile}}]
            else:
                callback_config = [callback_config]

        if isinstance(callback_config, Mapping):
            temp = []
            for key, value in callback_config:
                if not isinstance(key, string_types):
                    raise Exception(
                        "Invalid callback config value: {}".format(callback_config)
                    )
                temp.append({key: value})

            callback_config = temp

        if not isinstance(callback_config, Sequence):
            callback_config = [callback_config]
            # raise Exception(
            #     "Invalid callback config type '{}': {}".format(
            #         type(callback_config, callback_config)
            #     )
            # )

        for cc in callback_config:
            if isinstance(cc, string_types):
                c = load_callback(cc)
            elif isinstance(cc, Mapping):
                if len(cc) != 1:
                    raise Exception(
                        "Invalid callback configuration, only one key allowed: {}".format(
                            cc
                        )
                    )
                c_name = list(cc.keys())[0]
                c_config = cc[c_name]
                c = load_callback(c_name, callback_config=c_config)
            else:
                raise Exception("Invalid callback config: {}".format(cc))

            self._callbacks.append(c)

        self._adapters = {}
        self._adapter_tasktype_map = {}
        for adapter_name in self.config_value("adapters"):
            adapter = create_adapter(adapter_name, self)
            self._adapters[adapter_name] = adapter
            for tt in adapter.get_supported_task_types():
                self._adapter_tasktype_map.setdefault(tt, []).append(adapter_name)

        repo_list = self._create_resources_repo_list()

        self._resource_repo_list = self.augment_repos(repo_list)

        self.ensure_local_repos(self._resource_repo_list)

        # now set all resource folders for every supported adapter
        for adapter in self._adapters.values():

            resource_types = adapter.get_supported_resource_types()
            map = {}
            for rt in resource_types:
                folders = self._get_resources_of_type(rt)
                map[rt] = folders

            adapter.set_resource_folder_map(map)

        self._frkl_pkg = FrklPkg(extra_lookup_paths=FRECKLES_EXTRA_LOOKUP_PATHS)

    def update_repos(self, force=False, timeout=-1):

        self.ensure_local_repos(self._resource_repo_list)

    @property
    def frkl_pkg(self):

        return self._frkl_pkg

    @property
    def adapters(self):

        return self._adapters

    def execute_external_command(self, command, args=None, parent_task=None):

        return self.frkl_pkg.execute_external_comand(
            command, args=args, parent_task=parent_task
        )

    def add_config_interpreter(self, interpreter_name, schema):

        return self._config.add_cnf_interpreter(
            interpreter_name=interpreter_name, schema=schema
        )

    def config_value(self, key, interpreter_name=None):

        return self._config.config_value(key=key, interpreter_name=interpreter_name)

    def config(self, interpreter_name, *overlays):

        return self._config.config(interpreter_name, *overlays)

    def ensure_local_repos(self, repo_list):

        to_download = []
        for repo in repo_list:

            r = self.check_repo(repo)
            if r is not None:
                to_download.append(r)

        if to_download:
            sync_tasks = Tasks(
                "preparing context",
                category="internal",
                callbacks=self._callbacks,
                is_utility_task=True,
            )
            sync_root_task = sync_tasks.start()

            cleaned = []
            for r in to_download:
                url = r["url"]
                path = r["path"]
                branch = r.get("branch", None)
                temp = {"url": url, "path": path}
                if branch is not None:
                    temp["branch"] = branch

                if temp not in cleaned:
                    cleaned.append(temp)

            for repo in cleaned:

                self.download_repo(repo, task_parent=sync_root_task)

            sync_tasks.finish()

    def update_pull_cache(self, path):

        self._run_info.setdefault("pull_cache", {})[path] = time.time()
        self.save_run_info_file()

    def save_run_info_file(self, new_data=None):
        """Save the run info file, optionally merge it with new data beforehand.

        Args:
            new_data (dict): new data to be merged on top of current dict, will be ignored if None

        """

        if new_data is not None:
            self._run_info = dict_merge(self._run_info, new_data, copy_dct=False)

        with io.open(FRECKLES_RUN_INFO_FILE, "w", encoding="utf-8") as f:
            yaml.dump(self._run_info, f)

    def download_repo(self, repo, task_parent):

        exists = os.path.exists(repo["path"])

        branch = None
        if repo.get("branch", None) is not None:
            branch = repo["branch"]
        url = repo["url"]

        if branch is None:
            cache_key = url
        else:
            cache_key = "{}_{}".format(url, branch)

        if not exists:
            clone_task = task_parent.add_subtask(
                task_name="clone {}".format(repo["url"]),
                msg="cloning repo: {}".format(repo["url"]),
                category="internal",
            )
            git = local["git"]
            cmd = ["clone"]
            if branch is not None:
                cmd.append("-b")
                cmd.append(branch)
            cmd.append(url)
            cmd.append(repo["path"])
            rc, stdout, stderr = git.run(cmd)

            if rc != 0:
                clone_task.finish(success=False, changed=True, skipped=False)
                raise FrecklesConfigException(
                    "Could not clone repository '{}': {}".format(url, stderr)
                )
            else:
                clone_task.finish(success=True, skipped=False, changed=True)

            self.update_pull_cache(cache_key)

        else:
            pull_task = task_parent.add_subtask(
                task_name="pull {}".format(url),
                msg="pulling remote: {}".format(url),
                category="internal",
            )

            if cache_key in self._run_info.get("pull_cache", {}).keys():
                last_time = self._run_info["pull_cache"][cache_key]
                valid = self.config_value("remote_cache_valid_time")

                if valid < 0:
                    pull_task.finish(success=True, skipped=True)
                    log.debug(
                        "Not pulling again, updating repo disabled: {}".format(url)
                    )
                    return
                now = time.time()

                if now - last_time < valid:
                    # click.echo("  - using cached repo: {}".format(url))
                    pull_task.finish(success=True, skipped=True)
                    log.debug("Not pulling again, using cached repo: {}".format(url))
                    return

            # TODO: check if remote/branch is right?
            # click.echo("  - pulling remote: {}...".format(url))
            git = local["git"]
            cmd = ["pull", "origin"]
            if branch is not None:
                cmd.append(branch)
            with local.cwd(repo["path"]):
                rc, stdout, stderr = git.run(cmd)

                if rc != 0:
                    pull_task.finish(success=False)
                    raise FrecklesConfigException(
                        "Could not pull repository '{}': {}".format(url, stderr)
                    )
                else:
                    pull_task.finish(success=True, skipped=False)
            self.update_pull_cache(cache_key)

    def check_repo(self, repo):

        if not repo["remote"]:

            if not os.path.exists(repo["path"]):

                if self.config_value("ignore_empty_repos"):
                    log.warning(
                        "Local repo '{}' empty, ignoring...".format(repo["path"])
                    )
                else:
                    raise FrecklesConfigException(
                        keys="repos",
                        msg="Local repository folder '{}' does not exists.".format(
                            repo["path"]
                        ),
                        solution="Fix repository path in your configuration, create repository folder, or change 'ignore_empty_repos' configuration option to 'true'.",
                    )

            return None

        # remote repo
        if not self.config_value("allow_remote"):

            if repo.get("alias", None) != "community":
                url = repo.get("url", None)
                if url is None:
                    url = str(repo)
                raise FrecklesPermissionException(
                    msg="Use of repo '{}' is not allowed.".format(url),
                    reason="Repo not in 'allow_remote_whitelist' or 'allow_remote' not set to 'true'.",
                    key="repos",
                    solution="Add the repo to the 'allow_remote_whiltelist', or set configuration option 'allow_remote' to 'true'.",
                )

        return repo

    def augment_repos(self, repo_list):

        result = []

        for repo in repo_list:

            r = self.augment_repo(repo)
            result.append(r)

        return result

    def augment_repo(self, repo_orig):

        repo_desc = {}

        if "type" not in repo_orig.keys():
            repo_orig["type"] = MIXED_CONTENT_TYPE

        url = repo_orig["url"]

        if is_url_or_abbrev(url):

            git_details = expand_string_to_git_details(
                url, default_abbrevs=DEFAULT_URL_ABBREVIATIONS_REPO
            )
            full = git_details["url"]
            if full != url:
                abbrev = url
            else:
                abbrev = None

            basename = os.path.basename(full)
            if basename.endswith(".git"):
                basename = basename[0:-4]
            branch = git_details.get("branch", "master")

            postfix = os.path.join(branch, basename)

            if not os.path.exists(FRECKLES_CACHE_BASE):
                os.makedirs(FRECKLES_CACHE_BASE)

            os.chmod(FRECKLES_CACHE_BASE, 0o0700)

            cache_location = calculate_cache_location_for_url(full, postfix=postfix)
            cache_location = os.path.join(FRECKLES_CACHE_BASE, cache_location)

            repo_desc["path"] = cache_location
            repo_desc["url"] = full
            if branch is not None:
                repo_desc["branch"] = branch
            repo_desc["remote"] = True
            if abbrev is not None:
                repo_desc["abbrev"] = abbrev

        else:
            repo_desc["path"] = os.path.expanduser(url)
            repo_desc["remote"] = False

        if "alias" in repo_orig.keys():
            repo_desc["alias"] = repo_orig["alias"]

        repo_desc["type"] = repo_orig["type"]
        return repo_desc

    def _create_resources_repo_list(self):

        repo_list = self.config_value("repos")

        resources_list = []

        # move resource repos
        for repo in repo_list:

            temp_path = os.path.realpath(os.path.expanduser(repo))
            if os.path.exists(temp_path) and os.path.isdir(temp_path):
                repo = temp_path

            if os.path.sep in repo:

                if "::" in repo:
                    resource_type, url = repo.split("::", 1)
                else:
                    resource_type = MIXED_CONTENT_TYPE
                    url = repo

                r = {"url": url, "type": resource_type}
                resources_list.append(r)
            else:
                temp_list = []
                # it's an alias
                for a in self._adapters.values():
                    r = a.get_folders_for_alias(repo)

                    for u in r:
                        if "::" in u:
                            resource_type, url = u.split("::", 1)
                        else:
                            resource_type = MIXED_CONTENT_TYPE
                            url = u

                        temp_list.append(
                            {"url": url, "type": resource_type, "alias": repo}
                        )

                if not temp_list and not repo == "user":
                    log.warning(
                        "No repository folders found for alias '{}', ignoring...".format(
                            repo
                        )
                    )
                else:
                    resources_list.extend(temp_list)

        return resources_list

    def _get_resources_of_type(self, res_type):

        result = []
        for r in self._resource_repo_list:

            r_type = r["type"]
            if r_type == MIXED_CONTENT_TYPE or r_type == res_type:
                result.append(r)

        return result

    @property
    def context_name(self):
        return self._context_name

    @property
    def callbacks(self):
        return self._callbacks

    @property
    def frecklet_index(self):

        if self._frecklet_index is not None:
            return self._frecklet_index

        frecklet_folders = self._get_resources_of_type("frecklets")

        folder_index_conf = []
        used_aliases = []

        for f in frecklet_folders:
            url = f["path"]
            if "alias" in f.keys():
                alias = f["alias"]
            else:
                alias = os.path.basename(url).split(".")[0]
            i = 1
            while alias in used_aliases:
                i = i + 1
                alias = "{}_{}".format(alias, i)

            used_aliases.append(alias)
            folder_index_conf.append(
                {"repo_name": alias, "folder_url": url, "loader": "frecklet_files"}
            )

        for a_name, a in self._adapters.items():

            extra_frecklets_adapter = a.get_extra_frecklets()
            # print(extra_frecklets_adapter)
            if not extra_frecklets_adapter:
                continue
            folder_index_conf.append(
                {
                    "repo_name": "extra_frecklets_adapter_{}".format(a_name),
                    "loader": "frecklet_dicts",
                    "data": extra_frecklets_adapter,
                    "key_name": "frecklet_name",
                    "meta_name": "_metadata_raw",
                }
            )

        self._frecklet_index = TingTings.from_config(
            "frecklets",
            folder_index_conf,
            FRECKLET_LOAD_CONFIG,
            indexes=["frecklet_name"],
        )
        return self._frecklet_index

    def load_frecklet(self, frecklet_full_path_or_name_or_content, validate=False):
        """Loads a frecklet.

        First, checksi if argument is a path and exists. If that is the case, uses that to create the frecklet. If not, tries
        to find a frecklet with the provided name. If that doesn't exists either, it tries to interprete the string as frecklet content.
        """

        full_path = os.path.realpath(
            os.path.expanduser(frecklet_full_path_or_name_or_content)
        )

        if os.path.isfile(frecklet_full_path_or_name_or_content):
            frecklet_name = self.add_dynamic_frecklet(
                path_or_frecklet_content=full_path, validate=validate
            )
            frecklet = self.get_frecklet(frecklet_name, validate=validate)
            return (frecklet, frecklet_name)

        if frecklet_full_path_or_name_or_content in self.get_frecklet_names():
            frecklet = self.get_frecklet(
                frecklet_full_path_or_name_or_content, validate=validate
            )
            return (frecklet, frecklet_full_path_or_name_or_content)

        frecklet_name = self.add_dynamic_frecklet(frecklet_full_path_or_name_or_content)
        if frecklet_name:
            frecklet = self.get_frecklet(frecklet_name, validate=validate)
            return (frecklet, frecklet_name)

        return None, None

    def get_frecklet(self, frecklet_name, validate=False):

        result = self.frecklet_index.get(frecklet_name)

        if validate:
            valid = result.valid
            if not valid:

                raise FreckletException(
                    frecklet=result,
                    parent_exception=result.invalid_exception,
                    frecklet_name=frecklet_name,
                )

        return result

    def get_frecklet_names(self):

        return self.frecklet_index.keys()

    def add_dynamic_frecklet(
        self, path_or_frecklet_content, validate=False, check_path=True
    ):

        local_frecklet_name = None
        if check_path:
            full_path = os.path.realpath(os.path.expanduser(path_or_frecklet_content))

            if os.path.isfile(full_path):

                index_conf = {
                    "repo_name": full_path,
                    "folder_url": full_path,
                    "loader": "frecklet_file",
                }

                index = TingTings.from_config(
                    "frecklecutable",
                    [index_conf],
                    FRECKLET_LOAD_CONFIG,
                    indexes=["frecklet_name"],
                )

                names = list(index.get_ting_names())
                if len(names) == 1:
                    local_frecklet_name = names[0]
                else:
                    raise Exception(
                        "Multiple frecklets found for name '{}', this is a bug: {}".format(
                            path_or_frecklet_content, full_path
                        )
                    )

        if local_frecklet_name is None:

            # try to parse string into a dict/list
            try:
                frecklet_data = auto_parse_string(path_or_frecklet_content)

                id = str(uuid.uuid4())

                data = {id: frecklet_data}

                index_conf = {
                    "repo_name": id,
                    "data": data,
                    "loader": "frecklet_dicts",
                    "key_name": "frecklet_name",
                    "meta_name": "_metadata_raw",
                }

                index = TingTings.from_config(
                    "frecklecutable",
                    [index_conf],
                    FRECKLET_LOAD_CONFIG,
                    indexes=["frecklet_name"],
                )

                names = list(index.get_ting_names())
                if len(names) == 1:
                    local_frecklet_name = names[0]
                else:
                    raise Exception(
                        "Multiple frecklets found for name '{}', this is a bug: {}".format(
                            path_or_frecklet_content, frecklet_data
                        )
                    )

            except (Exception) as e:
                log.debug(
                    "Could not parse content into frecklet: {}".format(
                        path_or_frecklet_content
                    )
                )
                raise e

        # init, just in case
        _ = self.frecklet_index.tings

        self.frecklet_index.add_tings(index)

        if validate:
            f = self.get_frecklet(local_frecklet_name)
            f.valid

        return local_frecklet_name

    def create_frecklecutable(self, frecklet_name, only_from_index=True):

        if only_from_index:

            frecklet = self.frecklet_index.get(frecklet_name, None)
            if frecklet is None:
                raise Exception(
                    "No frecklet named '{}' in context '{}'".format(
                        frecklet_name, self._context_name
                    )
                )
        else:
            frecklet, internal_name = self.load_frecklet(frecklet_name)

        frecklecutable = frecklet.create_frecklecutable(context=self)
        return frecklecutable

    def unlock_config(self, user_accepts=False, use_community=False, save=True):

        if not user_accepts:
            raise Exception(
                "Need user acceptance of freckles license to unlock configuration."
            )

        target = os.path.join(FRECKLES_CONFIG_DIR, "default.context")

        if os.path.exists(target):
            with io.open(target, "r", encoding="utf-8") as f:
                current_content = yaml.load(f)
        else:
            current_content = {}

        current_content[ACCEPT_FRECKLES_LICENSE_KEYNAME] = user_accepts
        if use_community:
            repos = current_content.setdefault("repos", [])
            if "community" not in repos:
                repos.append("community")

        if save:
            with io.open(target, "w", encoding="utf-8") as f:
                f.write(
                    readable(
                        current_content, out="yaml", sort_keys=True, ignore_aliases=True
                    )
                )

    def create_run_environment(self, adapter, env_dir=None):

        result = {}

        symlink = os.path.expanduser(self.config_value("current_run_folder"))

        if env_dir is None:

            env_dir = os.path.expanduser(self.config_value("run_folder"))
            force = self.config_value("force")
            add_timestamp = self.config_value("add_timestamp_to_env")
            adapter_name = self.config_value("add_adapter_name_to_env")

            if adapter_name:
                dirname, basename = os.path.split(env_dir)
                env_dir = os.path.join(dirname, "{}_{}".format(basename, adapter.name))

            if add_timestamp:
                start_date = datetime.now()
                date_string = start_date.strftime("%y%m%d_%H_%M_%S")
                dirname, basename = os.path.split(env_dir)
                env_dir = os.path.join(dirname, "{}_{}".format(basename, date_string))

            if os.path.exists(env_dir):
                if not force:
                    raise Exception("Run folder '{}' already exists.".format(env_dir))
                else:
                    shutil.rmtree(env_dir)

        os.makedirs(env_dir)
        result["env_dir"] = env_dir

        if symlink:
            link_path = os.path.expanduser(symlink)
            if os.path.exists(link_path) or os.path.islink(link_path):
                os.unlink(link_path)
            link_parent = os.path.abspath(os.path.join(link_path, os.pardir))
            try:
                os.makedirs(link_parent)
            except (Exception):
                pass

            os.symlink(env_dir, link_path)

            result["env_dir_link"] = link_path

        # resource_path = os.path.join(env_dir, "resources")
        # os.mkdir(resource_path)
        # result["resource_path"] = resource_path
        #
        # for r_type, r_paths in all_resources.items():
        #
        #     r_target = os.path.join(resource_path, r_type)
        #     os.mkdir(r_target)
        #
        #     for path in r_paths:
        #         basename = os.path.basename(path)
        #         target = os.path.join(r_target, basename)
        #         if os.path.isdir(os.path.realpath(path)):
        #             shutil.copytree(path, target)
        #         else:
        #             shutil.copyfile(path, target)

        return result
