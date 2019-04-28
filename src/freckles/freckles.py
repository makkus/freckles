# -*- coding: utf-8 -*-

from .context.config import ContextConfigs
from .context.freckles_context import FrecklesContext


class Freckles(object):
    def __init__(
        self, use_community=False, default_context_config=None, extra_repos=None
    ):

        # self._root_config = Cnf(init_dict)
        # profile_load_config = self._root_config.add_interpreter(
        #     "profile_load", PROFILE_LOAD_CONFIG_SCHEMA
        # )
        # self._root_config.add_interpreter("root_config", FRECKLES_DEFAULT_CONFIG_SCHEMA)

        self._context_configs = ContextConfigs.load_configs()
        # self._cnf_profiles = CnfProfiles.from_folders(
        #     "cnf_profiles",
        #     FRECKLES_CONFIG_DIR,
        #     load_config=profile_load_config,
        #     cnf=self._root_config,
        # )

        self._contexts = {}
        self._current_context = None

        self.create_context(
            context_name="default",
            context_config=default_context_config,
            extra_repos=extra_repos,
            use_community=use_community,
        )

    def create_context(
        self,
        context_name,
        context_config,
        set_current=False,
        extra_repos=None,
        use_community=False,
    ):

        if not context_name:
            raise Exception("Context name can't be empty")

        if context_name in self._contexts.keys():
            raise Exception("Context '{}' already exists.".format((context_name)))

        context_config = self._context_configs.create_context_config(
            context_name=context_name,
            config_chain=context_config,
            extra_repos=extra_repos,
            use_community=use_community,
        )

        context = FrecklesContext(context_name=context_name, config=context_config)

        self._contexts[context_name] = context

        if set_current or self._current_context is None:
            self._current_context = context_name

        return context

    @property
    def current_context(self):

        return self._contexts[self._current_context]

    @current_context.setter
    def current_context(self, context_name):

        if context_name not in self._contexts.keys():
            raise Exception("No context with name '{}' available.".format(context_name))

        self._current_context = context_name

    def get_context(self, context_name=None):

        if context_name is None:
            context_name = self._current_context

        if context_name not in self._contexts.keys():
            raise Exception("No context with name '{}' available.".format(context_name))

        return self._contexts[context_name]

    @property
    def frecklets(self):

        ctx = self.get_context()

        return ctx.frecklet_index

    def get_frecklet_index(self, context_name=None):

        if context_name is None:
            context_name = self._current_context

        ctx = self.get_context(context_name)
        return ctx.frecklet_index

    def get_frecklet(self, frecklet_name, context_name=None):

        ctx = self.get_context(context_name)
        return ctx.get_frecklet(frecklet_name)

    def create_frecklecutable(self, frecklet_name, context_name=None):

        ctx = self.get_context(context_name)
        return ctx.create_frecklecutable(frecklet_name)
