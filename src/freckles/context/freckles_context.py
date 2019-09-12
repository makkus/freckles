# -*- coding: utf-8 -*-
import fnmatch
import io
import os
import shutil
import time
import uuid
from collections import Mapping
from datetime import datetime

from plumbum import local
from ruamel.yaml import YAML

from freckles.adapters.adapters import create_adapter
from freckles.defaults import (
    MIXED_CONTENT_TYPE,
    FRECKLES_CACHE_BASE,
    FRECKLES_RUN_INFO_FILE,
    FRECKLES_SHARE_DIR,
    FRECKLES_CONFIG_DIR,
    FRECKLES_EXTRA_LOOKUP_PATHS,
)
from freckles.exceptions import FrecklesConfigException, FrecklesPermissionException
from freckles.frecklet.arguments import *  # noqa
from freckles.frecklet.frecklet import FRECKLET_LOAD_CONFIG
from freckles.utils.utils import augment_meta_loader_conf
from frkl import content_from_url
from frkl.utils import expand_string_to_git_details
from frkl_pkg import FrklPkg
from frutils import (
    is_url_or_abbrev,
    DEFAULT_URL_ABBREVIATIONS_REPO,
    calculate_cache_location_for_url,
)
from frutils.exceptions import FrklException

from frutils.frutils import auto_parse_string
from frutils.tasks.callback import load_callback
from frutils.tasks.tasks import Tasks
from ting.tings import TingTings

log = logging.getLogger("freckles")

yaml = YAML()
yaml.default_flow_style = False
yaml.preserve_quotes = True
yaml.width = 4096


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

    os.chmod(FRECKLES_SHARE_DIR, 0o0755)

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

        use_stderr = self.config_value("use_stderr")
        for cc in callback_config:

            if isinstance(cc, string_types):
                if "::" in cc:
                    cc, _p = cc.split("::")
                    c = load_callback(cc, callback_config={"profile": _p})
                else:
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

            c.use_stderr = use_stderr
            self._callbacks.append(c)

        result = self.config_value("result")
        if isinstance(result, bool):
            if result:
                result = [("pretty", {})]
            else:
                result = []
        elif isinstance(result, string_types):
            result = [(result, {})]
        elif isinstance(result, dict):
            temp = []
            for k, v in result.items():
                temp.append((k, v))
            result = temp
        elif isinstance(result, Sequence):
            tmp = []
            for r in result:
                if isinstance(r, string_types):
                    tmp.append((r, {}))
                elif isinstance(r, Mapping):
                    for k, v in r.items():
                        tmp.append((k, v))
            result = tmp

        self.result_callback = result

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

        self._frecklet_load_config = copy.deepcopy(FRECKLET_LOAD_CONFIG)

        # ----------------------------------
        # changing load_config using context config

        # interactive_input_strategy = self.config_value("ask_user", "context")
        #
        # for attr in self._frecklet_load_config["attributes"]:
        #     if isinstance(attr, Mapping) and "VariablesAttribute" in attr.keys():
        #         attr["VariablesAttribute"][
        #             "interactive_input_strategy"
        #         ] = interactive_input_strategy
        #         break

        self.dynamic_frecklet_loader = augment_meta_loader_conf(
            self._frecklet_load_config
        )

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

    def export(
        self, dest_path, delete_destination_before_copy=False, ignore_errors=False
    ):

        if os.path.exists(dest_path):
            if delete_destination_before_copy:
                shutil.rmtree(dest_path, ignore_errors=False)
        else:
            os.makedirs(dest_path)

        for f_name in self.get_frecklet_names():

            try:

                self.copy_frecklet(f_name, dest_path=dest_path)
                log.debug("Exported frecklet: {}".format(f_name))

            except (Exception) as e:
                if ignore_errors:
                    log.warning("Export failed for frecklet '{}': {}".format(f_name, e))
                else:
                    raise e

    def copy_frecklet(self, frecklet_name, dest_path):

        frecklet_path = os.path.join(dest_path, "frecklet")
        self._copy_frecklet_content(
            frecklet_name=frecklet_name, dest_path=frecklet_path
        )

        self._copy_resources_for_frecklet(
            frecklet_name=frecklet_name, dest_path=dest_path
        )

    def _copy_frecklet_content(self, frecklet_name, dest_path, use_exploded=False):

        f = self.get_frecklet(frecklet_name=frecklet_name)

        dest_path_frecklet = os.path.join(
            dest_path, "{}.frecklet".format(frecklet_name)
        )

        log.debug("Render frecklet '{}': {}".format(frecklet_name, dest_path_frecklet))
        os.makedirs(dest_path, exist_ok=True)

        if use_exploded:
            content = f.exploded
        else:
            content = f._metadata_raw

        with io.open(dest_path_frecklet, "w", encoding="utf-8") as f:
            yaml.dump(content, f)

    def _copy_resources_for_frecklet(self, frecklet_name, dest_path):

        os.makedirs(dest_path, exist_ok=True)

        ignore_types = ["python-package"]

        for res_type, urls in self.get_frecklet(frecklet_name).resources.items():

            for u in urls:
                copied = False
                dest_path_res_type = os.path.join(dest_path, res_type)
                os.makedirs(dest_path_res_type, exist_ok=True)
                for t, adapters in self._adapter_tasktype_map.items():
                    if t == res_type:
                        for a in adapters:
                            adapter = self._adapters[a]
                            copied = adapter.copy_resource(
                                resource_name=u,
                                resource_type=res_type,
                                dest_path=dest_path_res_type,
                            )
                            if copied:
                                break
                    if copied:
                        break

                if not copied:
                    if res_type in ignore_types:
                        continue
                    raise Exception(
                        "Could not copy resource (type: {}): {}".format(res_type, u)
                    )

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

            if not os.path.exists(repo["path"]) and repo["path"] != "./.freckles":

                if self.config_value("ignore_empty_repos"):
                    if not repo["path"].endswith("{}.freckles".format(os.path.sep)):
                        log.info(
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
        if self.config_value("allow_remote"):
            return repo

        if repo.get("alias", None) == "community":
            return repo

        url = repo.get("url", None)
        if url is not None:

            whitelist = self.config_value("allow_remote_whitelist")
            matches = False
            for entry in whitelist:
                if fnmatch.fnmatch(url, entry):
                    matches = True
                    break

            if matches:
                return repo

        if url is None:
            url = str(repo)
        raise FrecklesPermissionException(
            msg="Use of repo '{}' is not allowed.".format(url),
            reason="Repo not in 'allow_remote_whitelist' or 'allow_remote' not set to 'true'.",
            key="repos",
            solution="Add the repo to the 'allow_remote_whiltelist', or set configuration option 'allow_remote' to 'true'.",
        )

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

        frecklet_folders = self._get_resources_of_type("frecklet")

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

        disable_duplicate_index_key_warning = self.config_value("disable_warnings")
        self._frecklet_index = TingTings.from_config(
            "frecklets",
            folder_index_conf,
            self._frecklet_load_config,
            indexes=["frecklet_name", "class_name"],
            disable_duplicate_index_key_warning=disable_duplicate_index_key_warning,
        )
        return self._frecklet_index

    def load_frecklet(self, frecklet_full_path_or_name_or_content, validate=False):
        """Loads a frecklet.

        First, checksi if argument is a path and exists. If that is the case, uses that to create the frecklet. If not, tries
        to find a frecklet with the provided name. If that doesn't exists either, it tries to interprete the string as frecklet content.
        """

        if isinstance(frecklet_full_path_or_name_or_content, string_types):

            full_path = os.path.realpath(
                os.path.expanduser(frecklet_full_path_or_name_or_content)
            )

            if os.path.isfile(frecklet_full_path_or_name_or_content):
                frecklet_name = self.add_dynamic_frecklet(
                    path_or_frecklet_content=full_path, validate=validate
                )
                frecklet = self.get_frecklet(frecklet_name, validate=validate)
                return (frecklet, frecklet_name)

            if is_url_or_abbrev(frecklet_full_path_or_name_or_content):

                if not self.config_value("allow_remote"):
                    raise FrklException(
                        msg="Loading remote frecklet from not allowed: {}".format(
                            frecklet_full_path_or_name_or_content
                        ),
                        reason="Context config value 'allow_remote' set to 'false'.",
                        solution="Set config value 'allow_remote' to 'true', e.g. via the '--context allow_remote=true' cli argument.",
                        references={
                            "freckles remote configuration": "https://freckles.io/doc/security#remote-repo-permission-config"
                        },
                    )

                content = content_from_url(
                    frecklet_full_path_or_name_or_content,
                    update=True,
                    cache_base=os.path.join(FRECKLES_CACHE_BASE, "remote_frecklets"),
                )
                frecklet_name = self.add_dynamic_frecklet(
                    path_or_frecklet_content=content, validate=validate
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

    def get_frecklet(self, frecklet_name, validate=False, index_name=None):

        result = self.frecklet_index.get_from_index(
            frecklet_name, index_name=index_name
        )

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
        if isinstance(path_or_frecklet_content, string_types) and check_path:
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
                    self.dynamic_frecklet_loader,
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
                if isinstance(path_or_frecklet_content, string_types):
                    frecklet_data = auto_parse_string(path_or_frecklet_content)
                else:
                    frecklet_data = path_or_frecklet_content

                id = "__dyn_" + str(uuid.uuid4())

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
                    self.dynamic_frecklet_loader,
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

    def create_run_environment(self, adapter, env_dir=None):

        result = {}
        symlink = self.config_value("create_current_symlink")
        symlink_path = os.path.expanduser(self.config_value("current_run_folder"))

        run_uuid = str(uuid.uuid4())
        result["uuid"] = run_uuid

        if env_dir is None:

            env_dir = os.path.expanduser(self.config_value("run_folder"))
            force = self.config_value("force")
            add_timestamp = self.config_value("add_timestamp_to_env")
            adapter_name = self.config_value("add_adapter_name_to_env")
            add_uuid = self.config_value("add_uuid_to_env")

            if adapter_name:
                dirname, basename = os.path.split(env_dir)
                env_dir = os.path.join(dirname, "{}_{}".format(basename, adapter.name))

            if add_timestamp:
                start_date = datetime.now()
                date_string = start_date.strftime("%y%m%d_%H_%M_%S")
                dirname, basename = os.path.split(env_dir)
                env_dir = os.path.join(dirname, "{}_{}".format(basename, date_string))

            if add_uuid:
                env_dir = "{}_{}".format(env_dir, run_uuid)

            if os.path.exists(env_dir):
                if not force:
                    raise Exception("Run folder '{}' already exists.".format(env_dir))
                else:
                    shutil.rmtree(env_dir)

        os.makedirs(env_dir)
        os.chmod(env_dir, 0o0700)
        result["env_dir"] = env_dir

        if symlink:
            try:
                link_path = os.path.expanduser(symlink_path)
                if os.path.exists(link_path) or os.path.islink(link_path):
                    os.unlink(link_path)
                link_parent = os.path.abspath(os.path.join(link_path, os.pardir))
                try:
                    os.makedirs(link_parent)
                except (Exception):
                    pass

                os.symlink(env_dir, link_path)

                result["env_dir_link"] = link_path
            except (Exception) as e:
                log.debug(
                    "Could not create symlink to current run folder: {}".format(e)
                )
                pass

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

    # def load_as_python_object(self, frecklet_name, module_path):
    #
    #     f = self.get_frecklet(frecklet_name=frecklet_name)
    #
    #     m = ModuleType(module_path)
    #     sys.modules[module_path] = m
    #
    #     exec(f.python_src, m.__dict__)
