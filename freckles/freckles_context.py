import collections
import json
import os
from collections import Mapping, Iterable

from six import string_types

from freckles.defaults import FRECKLES_CONFIG_DIR, MIXED_CONTENT_TYPE
from freckles.frecklet.frecklet_new import FreckletTings
from freckles.schemas import FRECKLES_CONTEXT_CONFIG_SCHEMA, FRECKLET_LOAD_CONFIG_SCHEMA, PROFILE_LOAD_CONFIG_SCHEMA, \
    FRECKLES_GLOBAL_CONFIG_SCHEMA
from frutils import dict_merge
from frutils.config.cnf import Cnf
from ting.ting_attributes import TingAttribute, MetadataAndContentAttribute, DictContentTingAttribute, \
    FileStringContentAttribute, ValueAttribute
from ting.ting_cast import TingCast
from ting.tings import TingTings


class CnfTingAttribute(TingAttribute):
    """Creates a :class:`Cnf` attribute from the dict value of the 'config_dict' attribute."""

    def requires(self):

        return ["config_dict"]

    def provides(self):

        return ["cnf"]

    def get_attribute(self, ting, attribute_name=None):

        return Cnf(config_dict=ting.config_dict)


class CnfProfileTingCast(TingCast):
    """A :class:`TingCast` to create freckles profiles by reading yaml files."""

    CNF_PROFILE_ATTRIBUTES = [
        FileStringContentAttribute(target_attr_name="ting_content"),
        MetadataAndContentAttribute(content_name="content", source_attr_name="ting_content"),
        ValueAttribute("config_dict", source_attr_name="content"),
        CnfTingAttribute(),
        DictContentTingAttribute(source_attr_name="content", dict_name="config_dict", default={}, copy_default=True),
    ]

    def __init__(self):

        super(CnfProfileTingCast, self).__init__(class_name="CnfProfile", ting_attributes=CnfProfileTingCast.CNF_PROFILE_ATTRIBUTES, ting_id_attr="filename_no_ext")


class CnfProfiles(TingTings):
    """A class to manage freckles profiles.

    This reads all '*.profile' files in the freckles config folder. Those are later used to create a freckles context
    (per profile). It also checks whether there exists a 'default.profile' file with the 'accept_freckles_license' value
    set to 'true'. Only if that is the case will it allow custom profiles (mainly for security reasons - the user should
    explicitely accept that certain configurations can be insecure).
    """

    DEFAULT_TING_CAST = CnfProfileTingCast

    LOAD_CONFIG_SCHEMA = PROFILE_LOAD_CONFIG_SCHEMA

    def __init__(self, repo_name, tingsets, global_config=None, load_config=None):

        super(CnfProfiles, self).__init__(repo_name=repo_name, tingsets=tingsets, load_config=load_config)

        if global_config is not None and not isinstance(global_config, Mapping):
            raise Exception("Default configuration needs to be a dictionary: {}".format(global_config))

        if global_config is not None:
            if isinstance(global_config, Cnf):
                pass
            elif isinstance(global_config, collections.Mapping):
                global_config = Cnf(config_dict=global_config)

            global_config.add_interpreter("global", FRECKLES_GLOBAL_CONFIG_SCHEMA)

        self._global_config = global_config

    @property
    def global_config(self):
        if self._global_config is None:
            init_config = self.get("default", None)
            if init_config is None:
                config_dict = {}
            else:
                config_dict = init_config.config_dict
            self._global_config = Cnf(config_dict=config_dict)
            self._global_config.add_interpreter("global", FRECKLES_GLOBAL_CONFIG_SCHEMA)

        return self._global_config.get_interpreter("global")

    def config_unlocked(self):
        license_accepted = self.global_config.get("accept_freckles_license", False)
        return license_accepted

    def get_profile(self, profile_name="default"):

        if not self.config_unlocked() and profile_name != "default":
            raise Exception("The initial freckles configuration is locked. Use the following command to unlock:\n\nfreckles config unlock\n\nFor more information, please visit: https://freckles.io/docs/configuration.")

        if not self.config_unlocked() and profile_name == "default":
            return self.global_config

        result = self.get(profile_name)

        if not result and profile_name == "default":
            return self.default_config
        return result

    def get_profile_cnf(self, profile_name="default"):

        profile = self.get_profile(profile_name)

        return profile.cnf

    def create_profile_cnf(self, profile_configs):

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
                if profile in self.get_profile_names():
                    profile = self.get_profile_cnf(profile).config
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
                            raise Exception("Can't assemble profile configuration, unknown type for: {}".format(value))
                    profile = {key, value}
                elif profile.startswith("{"):
                    # trying to read json
                    try:
                        profile = json.loads(profile)
                    except (Exception):
                        raise Exception("Can't assemble profile configuration, don't know how to handle: {}".format(profile))

            if isinstance(profile, Mapping):
                dict_merge(result, dict(profile), copy_dct=False)
            else:
                raise Exception("Can't assemble profile configuration, unknown type '{}' for value '{}'".format(type(profile), profile))

        return Cnf(config_dict=result)

    def get_profile_names(self):

        if not self.config_unlocked():
            return ["default"]

        else:
            names = list(self.get_ting_names())
            if "default" not in names:
                names.append("default")

            return sorted(names)


class FrecklesNew(object):

    def __init__(self):
        cnf = Cnf()
        interpreter = cnf.add_interpreter("profile_load", PROFILE_LOAD_CONFIG_SCHEMA)
        self.cnf_profiles = CnfProfiles.from_folders('cnf_profiles', FRECKLES_CONFIG_DIR, load_config=interpreter)
        self.global_config = self.cnf_profiles.global_config
        self._contexts = {}

    def get_context(self, context_name="default", profile_configs="default"):

        if context_name not in self._contexts.keys():
            cnf = self.cnf_profiles.create_profile_cnf(profile_configs=profile_configs)
            context = FrecklesContextNew(context_name, cnf)
            self._contexts[context_name] = context

        return self._contexts[context_name]


class FrecklesContextNew(object):

    def __init__(self, context_name, cnf):

        self._context_name = context_name
        self._cnf = cnf.add_interpreter("freckles_profile", FRECKLES_CONTEXT_CONFIG_SCHEMA)
        self._folder_load_config = cnf.add_interpreter("frecklet_load", FRECKLET_LOAD_CONFIG_SCHEMA)

        self._frecklet_index = None

    @property
    def cnf(self):
        return  self._cnf

    @property
    def context_name(self):
        return self._context_name

    @property
    def frecklet_index(self):

        if self._frecklet_index is not None:
            return self._frecklet_index

        repos = self.cnf.get("repos")
        repo_aliases = self.cnf.get("repo_aliases")
        repo_map = {}
        for repo in repos:
            types = repo["types"]
            if MIXED_CONTENT_TYPE in types or "frecklets":
                urls = repo["repos"]
                for url in urls:
                    if "/" not in url:
                        # assume this is an alias
                        if url not in repo_aliases.keys():
                            #raise Exception("Could not find repo(s) for  alias '{}'".format(url))
                            print("Could not find repo(s) for  alias '{}'".format(url))
                    else:
                        alias = os.path.basename(url).split('.')[0]
                        if alias in repo_map.keys():
                            i = 2
                            temp = "{}_{}".format(alias, i)
                            while temp in repo_map.keys():
                                i = i + 1
                                temp = "{}_{}".format(alias, i)
                            alias = temp

                        repo_map[alias] = url

        self._frecklet_index = FreckletTings.from_folders("frecklets", repo_map=repo_map, add_current_dir=False, load_config=self._folder_load_config)
        return self._frecklet_index

    def create_frecklecutable(self, name):

        frecklet = self.frecklet_index.get_frecklet(name, None)
        if frecklet is None:
            raise Exception("No frecklet named '{}' in context '{}'".format(name, self._context_name))

        frecklecutable = frecklet.create_frecklecutable()
