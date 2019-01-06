# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging

import click
from click import Context
from ruamel.yaml import YAML

from freckles.frecklecutable import Frecklecutable
from freckles.utils.doc_templating import create_doc_env, render_frecklet, render_cnf
from freckles.utils.doc_utils import flatten_task_hierarchy
from .context import FrecklesContext

# from luci.exceptions import NoSuchDictletException

yaml = YAML(typ="safe")


log = logging.getLogger("freckles")


class Freckles(object):
    def __init__(self, context=None):

        if context is None:
            context = FrecklesContext.create_context(config_profiles=["default"])

        self.context = context
        self.frecklet_cache = {}
        self.doc_env = None

    def _get_from_cache(self, frecklet_name, thing_type):

        f = self.frecklet_cache.get(frecklet_name, None)
        if f is None:
            self.frecklet_cache[frecklet_name] = {}

        thing = self.frecklet_cache[frecklet_name].get(thing_type, None)
        return thing

    def _add_to_cache(self, frecklet_name, thing_type, thing):

        self.frecklet_cache.setdefault(frecklet_name, {})[thing_type] = thing

    def get_frecklet(self, frecklet_name):

        thing_type = "frecklet"
        frecklet = self._get_from_cache(frecklet_name, thing_type)
        if frecklet is not None:
            return frecklet

        frecklet = self.context.create_frecklet(frecklet_name)
        self._add_to_cache(frecklet_name, thing_type, frecklet)

        return frecklet

    def get_frecklecutable(self, frecklet_name):

        thing_type = "frecklecutable"
        fx = self._get_from_cache(frecklet_name, thing_type)
        if fx is not None:
            return fx

        frecklet = self.get_frecklet(frecklet_name)
        fx = Frecklecutable(frecklet_name, frecklet, context=self.context)
        self._add_to_cache(frecklet_name=frecklet_name, thing_type=thing_type, thing=fx)
        return fx

    def get_task_plan(self, frecklet_name, vars=None):

        fx = self.get_frecklecutable(frecklet_name)

        hierarchy = fx.get_task_hierarchy(vars=vars, minimal=True)
        plan = []
        for tl in hierarchy:

            flattened = flatten_task_hierarchy(tl["hierarchy"])
            plan.extend(flattened)

        return plan

    def get_frecklet_metadata(self, frecklet_name):

        # this is already cached in the context object (or rather, the underlying index)
        md = self.context.get_frecklet_metadata(frecklet_name)
        return md

    def get_frecklet_names(
        self, tag_whitelist=None, tag_blacklist=None, apropos=None, check_valid=False
    ):
        """Lists all available frecklet names, filtered by tags or strings in the description.

        Args:
          tag_whitelist (list): a list of tags to include
          tag_blacklist (list): a list of tags to exclude, will be run after the whitelist filer, and before apropos
          apropos (list): a list of strings, filters out everything that doesn't match all of them in description/help of the frecklet (if provided)
          check_valid (bool): checks whether the frecklets are valid (takes longer)
        """

        return self.context.get_frecklet_names(
            tag_whitelist=tag_whitelist,
            tag_blacklist=tag_blacklist,
            apropos=apropos,
            check_valid=False,
        )

    def get_frecklet_cli_doc_string(self, frecklet_name):

        thing_type = "cli_doc_string"
        cli_doc_string = self._get_from_cache(frecklet_name, thing_type)
        if cli_doc_string is not None:
            return cli_doc_string

        frecklet = self.get_frecklet(frecklet_name)
        cli_paramters = frecklet.generate_click_parameters()

        @click.command(name=frecklet_name)
        def dummy(*args, **kwargs):
            pass

        dummy.params = cli_paramters
        dummy.help = frecklet.get_doc().get_help()
        dummy.short_help = frecklet.get_doc().get_short_help()

        ctx = Context(dummy.__class__, info_name="frecklecute {}".format(frecklet_name))

        cli_help = dummy.get_help(ctx)
        self._add_to_cache(frecklet_name, thing_type, cli_help)

        return cli_help

    def get_cnf(self):

        return self.context.cnf

    def render_cnf(self, template=None, markdown_renderer=None):

        if template is None:
            template = "cnf_doc/markdown/layout.md.j2"

        rendered = render_cnf(
            context=self.context,
            freckles_obj=self,
            template_name=template,
            markdown_renderer=markdown_renderer,
        )

        return rendered

    def render_frecklet_help(
        self, frecklet_name, template=None, markdown_renderer=None
    ):

        if template is None:
            template = "frecklet_doc/markdown/layout.md.j2"

        if markdown_renderer is None:
            thing_type = "render_help_{}".format(template)
            rendered = self._get_from_cache(frecklet_name, thing_type)
            if rendered is not None:
                return rendered

        rendered = render_frecklet(
            frecklet_name=frecklet_name,
            freckles_obj=self,
            template_name=template,
            markdown_renderer=markdown_renderer,
        )

        return rendered

    def get_doc_env(self):

        if self.doc_env is None:
            self.doc_env = create_doc_env(freckles_obj=self)

        return self.doc_env
