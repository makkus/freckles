# -*- coding: utf-8 -*-
import copy
import logging
import os

from six import string_types

from frkl import dict_from_url
from frkl.helpers import content_from_url
from .defaults import MODULE_FOLDER, FRECKLES_CACHE_BASE
from .exceptions import FrecklesConfigException

log = logging.getLogger("freckles")


MIXED_CONTENT_TYPE = "hodgepodge"

DEFAULT_URLS = {"frecklets": [os.path.join(MODULE_FOLDER, "external", "frecklets")]}


class FrecklesRepo(object):
    @classmethod
    def create_repo_desc(self, name, content_type=None, alias=None):

        if content_type is None:
            content_type = MIXED_CONTENT_TYPE

        repo_desc = {}
        repo_desc["path"] = name
        repo_desc["content_type"] = content_type
        if alias is not None:
            repo_desc["alias"] = alias

        return repo_desc

    def __init__(self, repo_desc):

        self.id = repo_desc["id"]
        self.url = repo_desc["url"]
        self.content_type = repo_desc["content_type"]


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

    def get_repos(self, only_content_types=None, ignore_invalid_repos=True):
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
                    _content_type, _name = name_or_url.split("::", 1)
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

        try:
            content = dict_from_url(url, update=update, cache_base=FRECKLES_CACHE_BASE)
        except (Exception) as e:
            raise FrecklesConfigException(str(e))

        return content
