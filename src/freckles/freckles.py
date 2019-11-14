# -*- coding: utf-8 -*-
import atexit
from collections import Mapping

from freckles.context.run_config import FrecklesRunConfig
from freckles.utils.runs import clean_runs_log_file
from .context.config import ContextConfigs
from .context.freckles_context import FrecklesContext

atexit.register(clean_runs_log_file)

# def show_cursor():
#     cursor.show()
# atexit.register(show_cursor)


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
        default_context_name="default",
    ):

        self._context_configs = ContextConfigs.load_user_context_configs(
            repos=config_repos
        )

        self._contexts = {}
        self._current_context = None

        self.create_context(
            context_name=default_context_name,
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


class FrecklesDesc(object):
    @classmethod
    def from_dict(cls, context_config=None, extra_repos=None, context_alias="default"):

        return FrecklesDesc(
            context_config=context_config,
            extra_repos=extra_repos,
            context_alias=context_alias,
        )

    def __init__(self, context_config=None, extra_repos=None, context_alias=None):

        self._context_config = context_config
        self._extra_repos = extra_repos
        if not context_alias:
            context_alias = "default"
        self._context_alias = context_alias
        self._freckles_obj = None
        self._context = None

    def to_dict(self):

        return {
            "context_config": self.context_config,
            "extra_repos": self.extra_repos,
            "context_alias": self.context_alias,
        }

    @property
    def context_config(self):
        return self._context_config

    @property
    def extra_repos(self):
        return self._extra_repos

    @property
    def context_alias(self):
        return self._context_alias

    @property
    def freckles_obj(self):

        if self._freckles_obj is not None:
            return self._freckles_obj

        freckles = Freckles(
            context_config=self.context_config,
            extra_repos=self.extra_repos,
            default_context_name=self.context_alias,
        )
        self._context = freckles.get_context(self.context_alias)

    def context(self):

        if self._context is None:
            self.freckles_obj

        return self._context


class FrecklesRunDesc(object):
    @classmethod
    def from_dict(
        cls,
        frecklet_name,
        vars=None,
        run_config=None,
        context_config=None,
        extra_repos=None,
        context_alias=None,
    ):

        freckles_desc = FrecklesDesc(
            context_config=context_config,
            extra_repos=extra_repos,
            context_alias=context_alias,
        )
        return FrecklesRunDesc(
            frecklet_name=frecklet_name,
            vars=vars,
            run_config=run_config,
            freckles_desc=freckles_desc,
        )

    def __init__(self, frecklet_name, vars=None, run_config=None, freckles_desc=None):

        self._frecklet_name = frecklet_name
        if vars is None:
            vars = {}
        self._vars = vars
        self._run_config = FrecklesRunConfig.create(run_config)
        if freckles_desc is None:
            freckles_desc = FrecklesDesc()
        elif isinstance(freckles_desc, Mapping):
            freckles_desc = FrecklesDesc.from_dict(**freckles_desc)
        self._freckles_desc = freckles_desc

    @property
    def frecklet_name(self):
        return self._frecklet_name

    @frecklet_name.setter
    def frecklet_name(self, frecklet_name):
        self._frecklet_name = frecklet_name

    @property
    def vars(self):
        return self._vars

    @vars.setter
    def vars(self, vars):

        if vars is None:
            vars = {}
        self._vars = vars

    @property
    def run_config(self):

        return self._run_config

    def to_dict(self):

        return {
            "frecklet_name": self._frecklet_name,
            "vars": self._vars,
            "run_config": self._run_config.config,
            "freckles_desc": self._freckles_desc.to_dict(),
        }

    def run_frecklet(self, password_callback=None):

        context = self._freckles_desc.context()
        frecklet, _ = context.load_frecklet(self._frecklet_name)

        fx = frecklet.create_frecklecutable(context=self._freckles_desc.context())

        run_record = fx.run_frecklecutable(
            inventory=self.vars,
            run_config=self.run_config,
            password_callback=password_callback,
        )

        return run_record
