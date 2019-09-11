# -*- coding: utf-8 -*-
import atexit

from cursor import cursor

from freckles.utils.runs import clean_runs_log_file
from .context.config import ContextConfigs
from .context.freckles_context import FrecklesContext

atexit.register(clean_runs_log_file)
atexit.register(cursor.show)


class Freckles(object):
    """The main class to encapsulate most things a developer would want to achieve with 'freckles'.

       This has a fairly complex configuration processing mechanism in-built, which is mainly used to enable maximum
       flexibility when building user-facing apps on top of 'freckles'. In most cases, you can safely ignore all that, and
       set the 'config_repos' value to 'None', and use 'default_context_config' to set the context defaults you want to
       use.

       In case you want to utilize the config processing feature (but really, best to just ignore it, it is probably too
       complex for what it does and will be re-written and simplified at some stage):

       The 'default_context_config', can be either a string, a dict or a dict. If a list, every element will be merged
       on-top of the previous (merged) dict. If a string, the 'config_repos' will be checked whether they contain a file
       with that name and a '.context' file extension, if there is, the content of that file will be used, if not, the string
       must either be 'default', in which case an empty dict will be returned, or it must contain a '=', in which case a
       one-item dict will be created with the left side (before '=') used as key, and the right one as value (some simple
       auto-parsing will be used to determine whether the value is a bool or integer).

       Args:
         context_config: the default configuration that underlies everything
         extra_repos (list): a list of extra repositories to search for frecklets and resources (see above for format)
         config_repos (dict, string): a single path or a dictionary of alias/path to point to folders containing context configurations
    """

    def __init__(
        self,
        context_config=None,
        extra_repos=None,
        config_repos=None,
        default__context_name="default",
    ):

        self._context_configs = ContextConfigs.load_user_context_configs(
            repos=config_repos
        )

        self._contexts = {}
        self._current_context = None

        self.create_context(
            context_name=default__context_name,
            context_config=context_config,
            extra_repos=extra_repos,
        )

    def create_context(
        self, context_name, context_config, set_current=False, extra_repos=None
    ):

        if not context_name:
            raise Exception("Context name can't be empty")

        if context_name in self._contexts.keys():
            raise Exception("Context '{}' already exists.".format((context_name)))

        context_config = self._context_configs.create_context_config(
            context_name=context_name,
            config_chain=context_config,
            extra_repos=extra_repos,
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
