import json
import logging
import os
import time
from collections import Mapping, Iterable

import click
from plumbum import local
from six import string_types

from freckles.exceptions import FrecklesConfigException
from frkl.utils import expand_string_to_git_details
from .adapters.adapters import create_adapter
from .defaults import MIXED_CONTENT_TYPE, FRECKLES_CACHE_BASE
from .frecklet.frecklet import FRECKLET_LOAD_CONFIG
from .schemas import FRECKLES_CONTEXT_SCHEMA
from frutils import (
    dict_merge,
    is_url_or_abbrev,
    DEFAULT_URL_ABBREVIATIONS_REPO,
    calculate_cache_location_for_url,
)
from frutils.config.cnf import Cnf
from ting.ting_attributes import (
    FrontmatterAndContentAttribute,
    DictContentAttribute,
    FileStringContentAttribute,
    ValueAttribute,
)
from ting.ting_cast import TingCast
from ting.tings import TingTings

log = logging.getLogger("freckles")

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


class CnfProfileTingCast(TingCast):
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

        super(CnfProfileTingCast, self).__init__(
            class_name="CnfProfile",
            ting_attributes=CnfProfileTingCast.CNF_PROFILE_ATTRIBUTES,
            ting_id_attr="filename_no_ext",
        )


class CnfProfiles(TingTings):
    """A class to manage freckles profiles.

    This reads all '*.profile' files in the freckles config folder. Those are later used to create a freckles context
    (per profile). It also checks whether there exists a 'default.profile' file with the 'accept_freckles_license' value
    set to 'true'. Only if that is the case will it allow custom profiles (mainly for security reasons - the user should
    explicitely accept that certain configurations can be insecure).
    """

    DEFAULT_TING_CAST = CnfProfileTingCast

    # LOAD_CONFIG_SCHEMA = PROFILE_LOAD_CONFIG_SCHEMA

    def __init__(self, repo_name, tingsets, cnf, **kwargs):

        if cnf is None:
            raise Exception("Base configuration object can't be None.")

        if "profile_load" not in cnf.get_interpreter_names():
            raise Exception("No 'profile_load' cnf interpreter available.")
        load_config = cnf.get_interpreter("profile_load")

        if "root_config" not in cnf.get_interpreter_names():
            raise Exception("No root_config profile interpreter in cnf.")

        if (
            "default_profile"
            in cnf.get_interpreter("root_config").get_interpreter_names()
        ):
            # not sure if this is necessary, might take that out later
            raise Exception(
                "Configuration already contains a 'default_profile' interpreter."
            )

        self._root_config = cnf.get_interpreter("root_config")

        self._default_profile_values = None

        super(CnfProfiles, self).__init__(
            repo_name=repo_name,
            tingsets=tingsets,
            load_config=load_config,
            indexes=["filename_no_ext"],
        )

    @property
    def root_config(self):

        return self._root_config

    @property
    def default_profile_dict(self):

        if self._default_profile_values is not None:
            return self._default_profile_values

        if "default" not in self.keys():
            return self._root_config.config

        default_config = self["default"].config_dict

        license_accepted = default_config.get("accept_freckles_license", False)
        if not license_accepted:
            raise Exception(
                "The initial freckles configuration is locked. Use the following command to unlock:\n\nfreckles config unlock\n\nFor more information, please visit: https://freckles.io/docs/configuration."
            )

        self._default_profile_values = dict(default_config)
        for k, v in self._root_config.config.items():
            if k not in self._default_profile_values.keys():
                self._default_profile_values[k] = v

        return self._default_profile_values

    def license_accepted(self):

        if "default" not in self.keys():
            return False

        default_config = self["default"].config_dict
        license_accepted = default_config.get("accept_freckles_license", False)
        return license_accepted

    def _get_profile_dict(self, profile_name="default"):

        if profile_name == "default":
            return self.default_profile_dict

        if not self.license_accepted() and profile_name != "default":
            raise Exception(
                "The initial freckles configuration is locked. Use the following command to unlock:\n\nfreckles config unlock\n\nFor more information, please visit: https://freckles.io/docs/configuration."
            )

        result = self.get(profile_name)

        if not result:
            raise Exception("No context named '{}' available.".format(profile_name))

        return result.config_dict

    def create_profile_cnf(
        self, profile_configs, extra_repos=None, use_community=False
    ):

        if isinstance(profile_configs, (string_types, Mapping)):
            profile_configs = [profile_configs]
        elif not isinstance(profile_configs, Iterable):
            profile_configs = [profile_configs]

        # if len(profile_list) == 1 and isinstance(profile_list[0], string_types) and profile_list[0] in self.get_profile_names():
        #     return self.get_profile_cnf(profile_list[0])

        result = {}
        for profile in profile_configs:

            if isinstance(profile, string_types):
                profile = profile.strip()
                if not self.license_accepted() and profile == "default":
                    profile = self.default_profile_dict
                elif not self.license_accepted() and profile in self.keys():
                    raise Exception(
                        "The initial freckles configuration is locked, so can't open context configuration '{}'. Use the following command to unlock:\n\nfreckles config unlock\n\nFor more information, please visit: https://freckles.io/docs/configuration.".format(
                            profile
                        )
                    )
                elif self.license_accepted() and profile in self.get_profile_names():
                    profile = self._get_profile_dict(profile)
                elif not profile.startswith("{") and "=" in profile:
                    key, value = profile.split("=", 1)
                    if value.lower() in ["true", "yes"]:
                        value = True
                    elif value.lower() in ["false", "no"]:
                        value = False
                    elif "::" in value:
                        value = value.splt("::")
                    else:
                        try:
                            value = int(value)
                        except (Exception):
                            raise Exception(
                                "Can't assemble profile configuration, unknown type for: {}".format(
                                    value
                                )
                            )
                    profile = {key, value}
                elif profile.startswith("{"):
                    # trying to read json
                    try:
                        profile = json.loads(profile)
                    except (Exception):
                        raise Exception(
                            "Can't assemble profile configuration, don't know how to handle: {}".format(
                                profile
                            )
                        )
                else:
                    raise Exception(
                        "Can't create profile configuration, invalid config: {}.".format(
                            profile
                        )
                    )

            if isinstance(profile, Mapping):
                dict_merge(result, dict(profile), copy_dct=False)
            else:
                raise Exception(
                    "Can't assemble profile configuration, unknown type '{}' for value '{}'".format(
                        type(profile), profile
                    )
                )

        if extra_repos:
            if isinstance(extra_repos, string_types):
                extra_repos = [extra_repos]
            else:
                extra_repos = list(extra_repos)
            result["repos"] = list(result["repos"]) + extra_repos

        result["use_community"] = use_community

        return Cnf(config_dict=result)

    def get_profile_names(self):

        if not self.license_accepted():
            return ["default"]

        else:
            names = list(self.get_ting_names())
            if "default" not in names:
                names.append("default")

            return sorted(names)


class FrecklesContext(object):
    def __init__(self, context_name, cnf):

        self._context_name = context_name
        self._cnf = cnf
        self._context_config = cnf.add_interpreter("context", FRECKLES_CONTEXT_SCHEMA)
        # self._folder_load_config = cnf.add_interpreter("frecklet_load", FRECKLET_LOAD_CONFIG_SCHEMA)

        self._frecklet_index = None
        self._pull_cache = {}

        # from config

        self._adapters = {}
        self._adapter_tasktype_map = {}
        for adapter_name in self._context_config.config.get("adapters"):
            adapter = create_adapter(adapter_name, self._cnf)
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

    def ensure_local_repos(self, repo_list):

        to_download = []
        for repo in repo_list:

            r = self.check_repo(repo)
            if r is not None:
                to_download.append(r)

        for repo in to_download:

            self.download_repo(repo, url_cache=self._pull_cache)

    def download_repo(self, repo, url_cache=None):

        force_update = self._context_config.get("always_update_remote_repos")
        exists = os.path.exists(repo["path"])
        if exists and not force_update:
            return

        branch = None
        if repo.get("branch", None) is not None:
            branch = repo["branch"]
        url = repo["url"]

        if url_cache is not None:
            if branch is None:
                cache_key = url
            else:
                cache_key = "{}_{}".format(url, branch)

        if not exists:

            click.echo("- cloning repo: {}...".format(repo["url"]))
            git = local["git"]
            cmd = ["clone"]
            if branch is not None:
                cmd.append("-b")
                cmd.append(branch)
            cmd.append(url)
            cmd.append(repo["path"])
            rc, stdout, stderr = git.run(cmd)

            if rc != 0:
                raise FrecklesConfigException(
                    "Could not clone repository '{}': {}".format(url, stderr)
                )

            if url_cache is not None:
                url_cache[cache_key] = time.time()

        else:
            if url_cache is not None and cache_key in url_cache.keys():
                log.debug("Not pulling again: {}".format(url))
                return

            # TODO: check if remote/branch is right?
            click.echo("- pulling from remote: {}...".format(url))
            git = local["git"]
            cmd = ["pull", "origin"]
            if branch is not None:
                cmd.append(branch)
            with local.cwd(repo["path"]):
                rc, stdout, stderr = git.run(cmd)

                if rc != 0:
                    raise FrecklesConfigException(
                        "Could not pull repository '{}': {}".format(url, stderr)
                    )
            if url_cache is not None:
                url_cache[cache_key] = time.time()

    def check_repo(self, repo):

        if not repo["remote"]:

            if not os.path.exists(repo["path"]):
                if self._context_config.get("ignore_nonexistent_repos"):
                    log.warning(
                        "Local repo '{}' empty, ignoring...".format(repo["path"])
                    )
                else:
                    raise Exception(
                        "Local repo '{}' does not exists, exiting...".format(
                            repo["path"]
                        )
                    )

            return None

        # remote repo
        if not self._context_config.get("allow_remote"):

            if repo.get("alias", None) != "community" or not self._context_config.get(
                "use_community"
            ):
                raise Exception(
                    "Remote repos not allowed in config, can't load repo '{}'. Exiting...".format(
                        repo["url"]
                    )
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
            repo_desc["path"] = url
            repo_desc["remote"] = False

        if "alias" in repo_orig.keys():
            repo_desc["alias"] = repo_orig["alias"]

        repo_desc["type"] = repo_orig["type"]
        return repo_desc

    def _create_resources_repo_list(self):

        use_community = self._context_config.config.get("use_community")
        repo_list = self._context_config.config.get("repos")

        resources_list = []

        if use_community and "community" not in repo_list:
            repo_list = repo_list + ["community"]

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

                if not temp_list:
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
    def cnf(self):
        return self._cnf

    @property
    def context_name(self):
        return self._context_name

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

    def get_frecklet(self, frecklet_name):

        return self.frecklet_index.get(frecklet_name)

    def get_frecklet_names(self, **kwargs):

        return self.frecklet_index.keys()

    def create_frecklecutable(self, frecklet_name):

        frecklet = self.frecklet_index.get(frecklet_name, None)
        if frecklet is None:
            raise Exception(
                "No frecklet named '{}' in context '{}'".format(
                    frecklet_name, self._context_name
                )
            )

        frecklecutable = frecklet.create_frecklecutable(context=self)
        return frecklecutable

    # def run(self, frecklet_name, inventory):
    #
    #     log.debug("Running frecklecutable: {}".format(frecklet_name))
    #
    #     fx = self.create_frecklecutable(frecklet_name=frecklet_name)
    #     tasks = fx.process_tasks(inventory=inventory)
    #
    #     current_tasklist = []
    #     idempotent_cache = []
    #     current_adapter = None
    #
    #     for task in tasks:
    #         tt = task[FRECKLET_KEY_NAME]["type"]
    #
    #         adapter = self._adapter_tasktype_map.get(tt, None)
    #
    #         if adapter is None:
    #             raise Exception("No adapter registered for task type: {}".format(tt))
    #         if len(adapter) > 1:
    #             raise Exception("Multiple adapters registered for task type '{}', that is not supported yet.".format(tt))
    #
    #         adapter = adapter[0]
    #
    #         if current_adapter is None:
    #             current_adapter = adapter
    #
    #         if current_adapter != adapter:
    #             raise Exception("Multiple adapters for a single frecklet, this is not supported yet: {} / {}".format(current_adapter, adapter))
    #
    #         if is_duplicate_task(task, idempotent_cache):
    #             log.debug("Idempotent, duplicate task, ignoring: {}".format(task[FRECKLET_KEY_NAME]["name"]))
    #             continue
    #         current_tasklist.append(task)
    #
    #     adapter = self._adapters[current_adapter]
    #
    #     callback = DefaultCallback()
    #     parent_task = TaskDetail(frecklet_name, "run", task_parent=None)
    #     callback.task_started(parent_task)
    #     task_details = TaskDetail(
    #                 task_name=frecklet_name,
    #                 task_type="frecklecutable",
    #                 task_parent=parent_task,
    #             )
    #     callback.task_started(task_details)
    #
    #     run_vars = {
    #         "__freckles_run__": {
    #             # "sudo_pass": "vagrant",
    #             # "ssh_pass": "vagrant",
    #             "pwd": os.getcwd(),
    #         }
    #     }
    #     secure_vars = {}
    #
    #     run_config = {
    #         # "current_run_folder"
    #         # "add_timestamp_to_env"
    #         # "allow_remote"
    #         "connection_type": "local",
    #         "ssh_port": 22,
    #         "callback": "freckles_callback",
    #         # "convert_ansible_template_markers"
    #         "elevated": True,
    #         # "force_run_folder"
    #         # "generate_role_frecklets"
    #         # "generate_tasklist_frecklets"
    #         # "guess_args_for_roles"
    #         "target": "localhost",
    #         "minimal_facts_only": False,
    #         "no_run": False,
    #         "output": "freckles",
    #         # "run_folder"
    #         # "show_tasks_with_password_in_log"
    #         # "user":
    #
    #     }
    #
    #
    #     result = adapter.run(tasklist=current_tasklist, run_vars=run_vars, run_config=run_config, secure_vars=secure_vars, output_callback=callback, result_callback=None, parent_task=task_details)
    #
    #     import pp
    #     pp(result)
