# -*- coding: utf-8 -*-
import logging
import os
from collections import OrderedDict
from typing import Callable, Mapping

from ariadne import load_schema_from_path
from graphql import GraphQLResolveInfo
from tsks.tsks import Tsk

from freckles.defaults import FRECKLES_FREQL_GRAPHQL_FILES
from freckles.freckles import FrecklesRunDesc
from freql.freql import FreQLPlugin
from freql.utils import generate_arg, ARG_TYPE_MAP
from frutils.exceptions import generate_exception_dict

log = logging.getLogger("freql")


class FreckletObject(object):
    @classmethod
    def create(cls, name, frecklet):

        if frecklet is None:
            return FreckletObject(name=name, valid=False, frecklet=None)

        return FreckletObject(name=name, valid=None, frecklet=frecklet)

    def __init__(self, name, valid=None, frecklet=None, error=None):

        self._name = name
        self._valid = valid
        self._exists = True
        self._frecklet = frecklet
        if frecklet is None:
            self._valid = False
            self._exists = False

        self._error = error

    def name(self, *args):
        return self._name

    def get_attribute(self, f):

        if self._valid is False:
            return None
        try:
            if f == "name":
                # print("name")
                return self._name
            elif f == "doc":
                # print("doc")
                return self._frecklet.doc.exploded_dict()
            elif f == "args":
                args = []
                for arg_name, arg in self._frecklet.vars.items():
                    args.append(generate_arg(arg_name=arg_name, arg=arg))
                return args
        except (Exception) as e:
            self._valid = False
            self._error = generate_exception_dict(e)

    def valid(self, *args):

        if self._valid is not None:
            return self._valid

        try:
            self._frecklet.valid
            self._valid = True
        except (Exception) as e:
            self._error = generate_exception_dict(e)
            self._valid = False

        return self._valid

    def args(self, *args):
        return self.get_attribute("args")

    def doc(self, *args):
        return self.get_attribute("doc")

    def error(self, *args):
        return self._error

    def exists(self, *args):
        return self._exists


class FreckletPlugin(FreQLPlugin):
    def __init__(
        self,
        freckles_context,
        tsk_manager,
        exposed_frecklet_tasks=None,
        allow_arbitrary_frecklet_runs=True,
    ):

        # type_defs = load_schema_from_path(os.path.join(FREQL_GRAPHQL_FILES, "frecklets.graphql"))
        super(FreckletPlugin, self).__init__()
        self._freckles_context = freckles_context
        self._tsk_manager = tsk_manager

        self._allow_arbitrary_frecklet_runs = allow_arbitrary_frecklet_runs

    def get_type_defs(self):

        type_defs = load_schema_from_path(
            os.path.join(FRECKLES_FREQL_GRAPHQL_FILES, "frecklets.graphql")
        )
        return type_defs

    def get_mutations(self):

        result = {}

        if self._allow_arbitrary_frecklet_runs:

            def run_frecklet(_, __, frecklet, run_config=None, vars=None):
                run_desc = {
                    "frecklet_name": frecklet,
                    "run_config": run_config,
                    "vars": vars,
                    "context_config": ["callback=silent", "dev"],
                }
                run_tsk = FreckletRunTsk(run_desc)
                self._tsk_manager.submit(run_tsk)
                return run_tsk.to_dict()

            doc = {
                "short_help": "Run an arbitrary frecklet that is not exposed via the schema."
            }

            args = {
                "frecklet": {
                    "required": True,
                    "type": "String",
                    "doc": {"short_help": "The name of the frecklet."},
                },
                "run_config": {
                    "required": False,
                    "type": "RunConfig",
                    "doc": {"short_help": "The configuration for this run."},
                },
                "vars": {
                    "type": "JSON",
                    "required": False,
                    "empty": True,
                    "doc": {"short_help": "The variables for this run."},
                },
            }
            res = {"type": "Tsk", "required": True}
            result["run_frecklet"] = {
                "metadata": {"doc": doc, "args": args, "result": res},
                "resolver": run_frecklet,
            }

        if self._freckles_context.get_frecklet_names():

            registered_frecklet_names = {}

            def frecklet_run_task(_, info: GraphQLResolveInfo, **args):

                run_config = args.pop("run_config", None)
                frecklet_name = registered_frecklet_names[info.field_name]
                run_desc = {
                    "frecklet_name": frecklet_name,
                    "run_config": run_config,
                    "vars": args,
                    "context_config": ["callback=silent", "dev"],
                }

                run_tsk = FreckletRunTsk(run_desc)
                self._tsk_manager.submit(run_tsk)
                return run_tsk.to_dict()

            failed = []
            for frecklet_name in self._freckles_context.get_frecklet_names():
                try:
                    frecklet = self._freckles_context.get_frecklet(
                        frecklet_name=frecklet_name
                    )
                    field_name = frecklet_name.replace("-", "_")
                    registered_frecklet_names[field_name] = frecklet_name
                    doc = frecklet.doc.exploded_dict(
                        default_not_available_string="No description available."
                    )
                    args = OrderedDict()
                    for arg_name, arg in frecklet.vars_required.items():
                        args[arg_name] = {
                            "type": ARG_TYPE_MAP[arg.type],
                            "required": arg.required,
                            "empty": arg.empty,
                            "schema": arg.schema,
                            "doc": arg.doc.exploded_dict(
                                default_not_available_string="No descripition available."
                            ),
                        }
                    for arg_name, arg in frecklet.vars_optional.items():
                        args[arg_name] = {
                            "type": ARG_TYPE_MAP[arg.type],
                            "required": arg.required,
                            "empty": arg.empty,
                            "schema": arg.schema,
                            "doc": arg.doc.exploded_dict(
                                default_not_available_string="No description available."
                            ),
                        }
                    res = {"type": "Tsk", "required": True}

                    result[field_name] = {
                        "metadata": {"doc": doc, "args": args, "result": res},
                        "resolver": frecklet_run_task,
                    }
                except (Exception) as e:
                    failed.append(frecklet_name)
                    log.error(e)

        return result

    def get_queries(self):
        def query_frecklet(_, __, name):

            if name not in self._freckles_context.get_frecklet_names():
                raise ValueError("No frecklet with name '{}' available.".format(name))
            frecklet = self._freckles_context.get_frecklet(name)

            return FreckletObject.create(name, frecklet)

        def query_frecklets(_, __):

            # result = []
            for frecklet_name in self._freckles_context.get_frecklet_names():
                frecklet = self._freckles_context.get_frecklet(frecklet_name)
                fo = FreckletObject.create(frecklet_name, frecklet)
                yield fo

        return {
            "frecklet": {
                "metadata": {
                    "doc": {"short_help": "Query frecklet properties."},
                    "args": {
                        "name": {
                            "doc": {"short_help": "The name of the frecklet"},
                            "type": "String",
                            "required": True,
                        }
                    },
                    "result": {"type": "Frecklet", "required": True},
                },
                "resolver": query_frecklet,
            },
            "frecklets": {
                "metadata": {
                    "doc": {"short_help": "List available frecklets."},
                    "result": {"type": "[Frecklet]", "required": True},
                },
                "resolver": query_frecklets,
            },
        }


class FreckletRunTsk(Tsk):
    def __init__(self, run_desc, result_callbacks: Callable = None):

        super(FreckletRunTsk, self).__init__(
            task_func=self.run_frecklet, result_callbacks=result_callbacks
        )

        if isinstance(run_desc, FrecklesRunDesc):
            run_desc = run_desc.to_dict()
        if not isinstance(run_desc, Mapping):
            raise TypeError(
                "run_desc needs to be a Mapping, not '{}'.".format(type(run_desc))
            )

        self._run_desc = run_desc

    def run_frecklet(self):

        freckles_run_desc = FrecklesRunDesc.from_dict(**self._run_desc)
        run_record = freckles_run_desc.run_frecklet()

        return run_record.result
