# -*- coding: utf-8 -*-
import copy
import logging
import os

import click
from frutils import (
    is_url_or_abbrev,
    calculate_cache_location_for_url,
    DEFAULT_URL_ABBREVIATIONS_REPO,
)
from plumbum import local
from six import string_types

from frkl import dict_from_url
from frkl.helpers import content_from_url
from frkl.utils import expand_string_to_git_details

from .defaults import FRECKLES_CACHE_BASE, COMMUNITY_REPO_DESC, MIXED_CONTENT_TYPE
from .exceptions import FrecklesConfigException, FrecklesPermissionException

log = logging.getLogger("freckles")


# DEFAULT_URLS = {"frecklets": [os.path.join(MODULE_FOLDER, "external", "frecklets")]}


class FrecklesRepo(object):
    @classmethod
    def create_repo_desc(self, name, content_type=None, alias=None):

        if content_type is None:
            content_type = MIXED_CONTENT_TYPE

        repo_desc = {}
        if is_url_or_abbrev(name):
            git_details = expand_string_to_git_details(
                name, default_abbrevs=DEFAULT_URL_ABBREVIATIONS_REPO
            )
            # full = get_full_url(name, abbrevs=DEFAULT_URL_ABBREVIATIONS_REPO)
            full = git_details["url"]
            if full != git_details["url"]:
                abbrev = git_details["url"]
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
            repo_desc["path"] = name
            repo_desc["remote"] = False

        repo_desc["content_type"] = content_type
        if alias is not None:
            repo_desc["alias"] = alias

        return repo_desc

    def __init__(self, repo_desc):

        self.alias = repo_desc.get("alias", None)
        self.url = repo_desc.get("url", None)
        self.path = repo_desc["path"]
        self.content_type = repo_desc["content_type"]
        self.branch = repo_desc.get("branch", None)
        self.remote = repo_desc["remote"]
        self.abbrev = repo_desc.get("abbrev", None)

    def ensure_local(self, force_update=False):

        if not self.remote or not force_update:
            if os.path.exists(self.path):
                return

            if not self.remote:
                raise FrecklesConfigException(
                    "Repo folder '{}' does not exist.", self.path
                )

        if os.path.exists(self.path) and not force_update:
            return
        elif not os.path.exists(self.path):

            # TODO: figure out a way to do this with callbacks or something
            click.echo("- cloning repo: {}...".format(self.url))
            git = local["git"]
            rc, stdout, stderr = git.run(["clone", self.url, self.path])

            if rc != 0:
                raise FrecklesConfigException(
                    "Could not clone repository '{}': {}".format(self.url, stderr)
                )

        else:
            # TODO: check if remote/branch is right?
            click.echo("- pulling from remote: {}...".format(self.url))
            git = local["git"]
            cmd = ["pull", "origin"]
            if self.branch is not None:
                cmd.append(self.branch)
            with local.cwd(self.path):
                rc, stdout, stderr = git.run(cmd)

                if rc != 0:
                    raise FrecklesConfigException(
                        "Could not pull repository '{}': {}".format(self.url, stderr)
                    )


class RepoManager(object):
    def __init__(self, cnf_interpreter):

        self.cnf_interpreter = cnf_interpreter
        self.aliases = {}
        self.all_content_types_so_far = []

    def add_alias_map(self, alias_map, content_types=None):

        for alias, repos in alias_map.items():
            for repo_type, repo_urls in repos.items():
                if (
                    content_types
                    and repo_type not in content_types
                    and repo_type != "frecklets"
                ):
                    continue
                for repo_url in repo_urls:
                    if repo_url not in self.aliases.get(alias, {}).get(repo_type, {}):
                        self.aliases.setdefault(alias, {}).setdefault(
                            repo_type, []
                        ).append(repo_url)

    def is_alias(self, name):

        if ":" in name or os.sep in name:
            return False

        return name in self.aliases.keys()

    def check_permission_for_url(self, url):

        allow_remote = self.cnf_interpreter.get_cnf_value("allow_remote")

        if is_url_or_abbrev(url) and not allow_remote:
            return (False, "No remote files allowed.")

        return (True, "External files allowed.")

    def check_permission_for_repo(self, repo_desc):

        if repo_desc == COMMUNITY_REPO_DESC:
            allow_community = self.cnf_interpreter.get_cnf_value("allow_community")
            if allow_community:
                return (True, "Community repo allowed.")
            else:
                return (False, "Community repo not allowed")

        allow_remote = self.cnf_interpreter.get_cnf_value("allow_remote")

        if repo_desc["remote"] and not allow_remote:
            return (False, "No remote repos allowed.")

        return (True, "Remote repos allowed.")

    def get_repo(self, repo_desc, force_update=True):

        path = repo_desc["path"]
        exists = False
        allowed, msg = self.check_permission_for_repo(repo_desc)
        if not allowed:
            log.warn("Not using repo '{}': {}".format(repo_desc["url"], msg))
            return None

        if repo_desc["remote"]:
            r = FrecklesRepo(repo_desc)
            r.ensure_local(force_update=force_update)

        if os.path.exists(path):
            exists = True

        if exists:
            return path
        else:
            return None

    def get_repo_descs(self, only_content_types=None, ignore_invalid_repos=True):
        """Returns the repo desc dictionary for the provided name or url.

        'only_content_types' should be a list of allowed content types. If that's the case,
        hodgepodge repos will be added for every type that was requested. If it is None,
        this function will use all content types that this class has encountered up to this point.

        Args:
            only_content_types (list): a list of allowed content types or None or True
            ignore_invalid_repos (bool): whether to continue execution if an invalid repository is encountered

        Returns:
            list: a list of repository descriptions
        """
        repo_urls = self.cnf_interpreter.get_cnf_value("context_repos")

        if isinstance(repo_urls, string_types):
            repo_urls = [repo_urls]
        if isinstance(only_content_types, string_types):
            only_content_types = [only_content_types]

        if only_content_types is not None:
            for ct in only_content_types:
                if ct not in self.all_content_types_so_far:
                    self.all_content_types_so_far.append(ct)

        all_repos = []

        for name_or_url in repo_urls:

            try:
                if "::" in name_or_url:
                    # just checking if it's an alias
                    _temp_content_type, _temp_name = name_or_url.split("::", 1)
                    if is_url_or_abbrev(
                        _temp_content_type, abbrevs=DEFAULT_URL_ABBREVIATIONS_REPO
                    ):
                        _name = name_or_url
                        _content_type = MIXED_CONTENT_TYPE
                    else:
                        _content_type = _temp_content_type
                        _name = _temp_name

                    is_alias = self.is_alias(_name)
                else:
                    _name = name_or_url
                    _content_type = MIXED_CONTENT_TYPE
                    is_alias = self.is_alias(name_or_url)

                if is_alias:
                    all_urls = self.aliases[_name]
                    alias = _name

                    for c_type, urls in all_urls.items():
                        if c_type not in self.all_content_types_so_far:
                            self.all_content_types_so_far.append(c_type)

                        for url in urls:
                            r = FrecklesRepo.create_repo_desc(
                                url, alias=alias, content_type=c_type
                            )
                            all_repos.append(r)

                else:
                    url = _name
                    r = FrecklesRepo.create_repo_desc(
                        url, alias=None, content_type=_content_type
                    )
                    all_repos.append(r)

            except (Exception) as e:
                log.warn(
                    "Could not create repo for '{}': {}".format(name_or_url, e),
                    exc_info=1,
                )
                if not ignore_invalid_repos:
                    raise e

        result = []

        for r in all_repos:

            c_type = r["content_type"]
            if c_type == MIXED_CONTENT_TYPE:
                if only_content_types is None:
                    cts = self.all_content_types_so_far
                else:
                    cts = only_content_types

                for ct in cts:
                    temp = copy.deepcopy(r)
                    temp["content_type"] = ct
                    result.append(temp)
            else:
                if only_content_types is not None:
                    if c_type in only_content_types:
                        result.append(r)
                else:
                    result.append(r)

        # now we transform the mixed content type to
        return result

    # def download_frecklet_into_cache(self, frecklet_url, force_update=True):
    #     """Downloads a frecklet to a local url.
    #     """
    #
    #     path = download_cached_file(frecklet_url)

    def get_file_content(self, url, update=True):
        """Gets the content of the file sitting at the provided url.

        Args:
            url (str): the url or path

        Returns:
            str: the content of the file
        """

        content = content_from_url(url, update=update, cache_base=FRECKLES_CACHE_BASE)

        return content

    def get_remote_dict(self, url, update=True):
        """Gets the content of the file sitting at the provided url.

        Args:
            url (str): the url or path

        Returns:
            str: the content of the file
        """

        allowed, msg = self.check_permission_for_url(url)

        if not allowed:
            raise FrecklesPermissionException(
                "Can't use remote frecklet '{}': {}".format(url, msg)
            )

        try:
            content = dict_from_url(url, update=update, cache_base=FRECKLES_CACHE_BASE)
        except (Exception) as e:
            raise FrecklesConfigException(str(e))

        return content
