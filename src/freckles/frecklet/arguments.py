# -*- coding: utf-8 -*-
import logging
from collections import OrderedDict, Sequence

import click
from jinja2 import TemplateSyntaxError
from six import string_types

from freckles.defaults import DEFAULT_FRECKLES_JINJA_ENV, FRECKLES_DEFAULT_ARG_SCHEMA
from freckles.exceptions import FreckletBuildException, FreckletException
from frutils import get_template_keys, dict_merge
from frutils.parameters import VarsTypeSimple
from ting.ting_attributes import TingAttribute, Arg
from ting.ting_cast import MultiCacheResult

log = logging.getLogger("freckles")


class CliArgumentsAttribute(TingAttribute):

    CLICK_CEREBUS_ARG_MAP = {
        "string": str,
        "float": float,
        "integer": int,
        "boolean": bool,
        "dict": VarsTypeSimple(),
        "password": str,
        # "list": list
    }

    DEFAULT_CLI_SCHEMA = {"show_default": True, "param_type": "option"}

    def __init__(
        self, target_attr_name="cli_arguments", source_attr_name="vars_frecklet"
    ):

        self.target_attr_name = target_attr_name
        self.source_attr_name = source_attr_name

    def provides(self):

        return [self.target_attr_name]

    def requires(self):

        return [self.source_attr_name]

    def get_attribute(self, ting, attribute_name=None):

        # TODO: validate

        vars = getattr(ting, self.source_attr_name)

        result = []
        for var_name, var in vars.items():
            parameter = self.create_parameter(var_name, var)
            if parameter is not None:
                result.append(parameter)

        required = []
        optional = []
        for p in result:
            if p.required:
                required.append(p)
            else:
                optional.append(p)

        return required + optional

    def create_parameter(self, var_name, var):

        if not var.cli.get("enabled", True):
            return None

        option_properties = dict_merge(
            CliArgumentsAttribute.DEFAULT_CLI_SCHEMA, var.cli, copy_dct=True
        )

        param_type = option_properties.pop("param_type")

        if var.default is not None:
            option_properties["default"] = var.default

        option_properties["required"] = var.required

        auto_param_decls = False
        if "param_decls" not in option_properties.keys():
            auto_param_decls = True
            if param_type == "option":
                decls = []
                for a in var.aliases:
                    if len(a) == 1:
                        decls.append("-{}".format(a))
                    else:
                        a = a.replace("_", "-")
                        decls.append("--{}".format(a))
                option_properties["param_decls"] = decls
            else:
                option_properties["param_decls"] = [var.key]

        if "metavar" not in option_properties.keys():
            option_properties["metavar"] = var.key.upper()

        # setting type
        cerberus_type = var.type

        if not isinstance(cerberus_type, string_types) and isinstance(
            cerberus_type, Sequence
        ):
            replacement = None
            cerberus_type = "multi"
        else:
            replacement = CliArgumentsAttribute.CLICK_CEREBUS_ARG_MAP.get(
                cerberus_type, None
            )
        if replacement is not None:
            if replacement == bool:
                option_properties["type"] = None
                option_properties["default"] = None
                if "is_flag" not in option_properties.keys():
                    option_properties["is_flag"] = True
                    # we don't add the type here, otherwise click fails for whatever reason

                if "param_decls" not in option_properties.keys() or auto_param_decls:

                    temp = var.key.replace("_", "-")
                    option_properties["param_decls"] = [
                        "--{}/--no-{}".format(temp, temp)
                    ]
            else:
                option_properties["type"] = replacement

        elif cerberus_type == "list":
            arg_schema = var.schema.get("schema", {})
            schema_type = arg_schema.get("type", "string")
            replacement = CliArgumentsAttribute.CLICK_CEREBUS_ARG_MAP.get(
                schema_type, click.STRING
            )
            option_properties["type"] = replacement
            if param_type == "option":
                option_properties["multiple"] = True
            else:
                if (
                    "nargs" not in option_properties.keys()
                    and "default" not in option_properties.keys()
                ):
                    option_properties["nargs"] = -1
        elif cerberus_type != "multi":
            raise Exception("Type '{}' not implemented yet.".format(cerberus_type))

        if var.secret:
            if "default" not in option_properties.keys():
                if option_properties["required"]:
                    option_properties["default"] = "ask"
                    option_properties["show_default"] = True

        if param_type == "option":
            option_properties["help"] = var.doc.get_short_help()
            p = click.Option(**option_properties)
        else:
            option_properties.pop("show_default", None)
            if (
                "nargs" in option_properties.keys()
                and "default" in option_properties.keys()
            ):
                log.warning(
                    "Removing 'nargs' property from argument '{}' ('nargs' & 'default' are not allowed together)".format(
                        var_name
                    )
                )
                option_properties.pop("nargs")
            p = click.Argument(**option_properties)

        return p


class VariablesFilterAttribute(TingAttribute):
    def __init__(
        self,
        source_attr_name="vars_frecklet",
        target_attr_name="vars_required",
        required=True,
    ):

        self.source_attr_name = source_attr_name
        self.target_attr_name = target_attr_name
        self.required = required

    def requires(self):

        return [self.source_attr_name]

    def provides(self):

        return [self.target_attr_name]

    def get_attribute(self, ting, attribute_name=None):

        vars = getattr(ting, self.source_attr_name)
        result = OrderedDict()
        for var_name, arg_obj in vars.items():

            req = arg_obj.required

            if req and self.required:
                result[var_name] = arg_obj
            elif not req and not self.required:
                result[var_name] = arg_obj

        return result


class VariablesAttribute(TingAttribute):
    def __init__(
        self, target_attr_name="vars_frecklet", default_argument_description=None
    ):

        self.target_attr_name = target_attr_name
        self.default_argument_description = default_argument_description

    def provides(self):

        return [self.target_attr_name, "{}_tree".format(self.target_attr_name)]

    def requires(self):

        return ["task_tree"]

    def get_attribute(self, ting, attribute_name=None):

        task_tree = ting.task_tree
        paths_to_leaves = task_tree.paths_to_leaves()
        vars_tree = {}
        for path in paths_to_leaves:
            leaf_node_id = path[-1]
            args = self.get_vars_from_path(path_to_leaf=path, tree=task_tree, ting=ting)
            vars_tree[leaf_node_id] = args

        vars = self.consolidate_vars(vars_tree, ting)

        result = {
            "{}_tree".format(self.target_attr_name): vars_tree,
            self.target_attr_name: vars,
        }

        return MultiCacheResult(**result)

    def consolidate_vars(self, vars_tree, ting):

        result = {}
        for args in vars_tree.values():

            for arg_name, arg in args.items():

                if (
                    arg_name in result.keys()
                    and not result[arg_name].is_auto_arg
                    and not arg.is_auto_arg
                    and result[arg_name].schema != arg.schema
                ):
                    # import pp
                    # pp(arg.__dict__)
                    # pp(result[arg_name].__dict__)
                    raise FreckletBuildException(
                        frecklet=ting,
                        msg="Duplicate arg '{}'.".format(arg_name),
                        solution="Check format of frecklet '{}'.".format(ting.id),
                        references={
                            "frecklet documentation": "https://freckles.io/doc/frecklets/anatomy"
                        },
                    )

                if arg_name not in result.keys() or not arg.is_auto_arg:
                    result[arg_name] = arg

        ordered = OrderedDict()
        for k in sorted(result.keys()):
            ordered[k] = result[k]

        return ordered

    def resolve_vars(self, current_args, rest_path, last_node, tree, ting):

        current_node_id = next(rest_path)

        # print("CURRENT: {}".format(current_node_id))
        current_node = tree.get_node(current_node_id)

        if current_node_id == 0:
            vars = {}

            for key in current_args.keys():
                vars[key] = "{{{{:: {} ::}}}}".format(key)
        else:
            vars = current_node.data["task"]["vars"]

        if current_node_id == 0:
            available_args = current_node.data.args
        else:
            available_args = current_node.data["task"]["args"]

        args = {}

        for key, arg in current_args.items():

            if key not in vars.keys():

                if arg.required and arg.default is None:
                    # relevant frecklet root name: tree.get_node(0).tag,
                    raise FreckletBuildException(
                        frecklet=ting,
                        msg="Invalid frecklet-task '{}' in '{}': does not provide required/non-defaulted var '{}' for child frecklet '{}'.".format(
                            current_node.tag, tree.get_node(0).tag, key, last_node.tag
                        ),
                        solution="Check format of frecklet '{}'.".format(
                            current_node.tag
                        ),
                        references={
                            "frecklet documentation": "https://freckles.io/doc/frecklets/anatomy"
                        },
                    )

                # means we don't have to worry about this key, as it is not used and not required
                continue
            else:
                parent_var = vars[key]

                # print("PARENT VAR: {}".format(parent_var))
                if parent_var == "{{{{:: {} ::}}}}".format(key):

                    # this means the var is just being carried forward, from the point of view of the parent frecklet task
                    arg_config = available_args.get(key, None)
                    if arg_config is None:
                        # print("USING CHILD ARG")
                        new_arg = arg
                    else:
                        new_arg = Arg(
                            key, arg_config, default_schema=FRECKLES_DEFAULT_ARG_SCHEMA
                        )
                        new_arg.add_child(arg)
                        new_arg.var_template = parent_var

                    args[key] = new_arg
                else:
                    template_keys = get_template_keys(
                        parent_var, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
                    )
                    for tk in template_keys:
                        arg_config = available_args.get(tk, None)
                        if arg_config is None:
                            if tk == key:
                                new_arg = arg
                            else:
                                new_arg = Arg(
                                    tk,
                                    {},
                                    default_schema=FRECKLES_DEFAULT_ARG_SCHEMA,
                                    is_auto_arg=True,
                                )
                                new_arg.add_child(arg)
                        else:
                            new_arg = Arg(
                                tk,
                                arg_config,
                                default_schema=FRECKLES_DEFAULT_ARG_SCHEMA,
                            )
                            new_arg.add_child(arg)

                        new_arg.var_template = parent_var
                        args[tk] = new_arg

        if current_node_id != 0:

            r = self.resolve_vars(
                current_args=args,
                rest_path=rest_path,
                last_node=current_node,
                tree=tree,
                ting=ting,
            )

            return r
        else:

            root_task = last_node.data["task"]
            try:
                tks = get_template_keys(root_task, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
            except (TemplateSyntaxError) as e:
                raise FreckletException(ting, e, ting.id)

            root_tks = {}
            for tk in tks:
                if tk in args.keys():
                    continue

                # add a template key that is under either 'frecklet' or 'task' of the root task of a frecklet
                arg = available_args.get(tk, None)

                auto_arg = False
                if arg is None:
                    if self.default_argument_description is None:
                        f_name = current_node.data.id
                        raise Exception(
                            "No argument description for argument '{}' in frecklet '{}'".format(
                                tk, f_name
                            )
                        )
                    else:
                        arg = self.default_argument_description
                        auto_arg = True

                arg = Arg(
                    tk,
                    arg,
                    default_schema=FRECKLES_DEFAULT_ARG_SCHEMA,
                    is_auto_arg=auto_arg,
                )
                root_tks[tk] = arg

            dict_merge(args, root_tks, copy_dct=False)

            return args

    def get_vars_from_path(self, path_to_leaf, tree, ting):

        root = path_to_leaf[-1]
        root_node = tree.get_node(root)
        # end = path_to_leave[0]

        available_args = root_node.data["root_frecklet"].args
        template_keys = root_node.data["root_frecklet"].template_keys

        args = Arg.from_keys(
            template_keys, available_args, default_schema=FRECKLES_DEFAULT_ARG_SCHEMA
        )
        rest_path = reversed(path_to_leaf[0:-1])

        return self.resolve_vars(
            current_args=args,
            rest_path=rest_path,
            last_node=root_node,
            tree=tree,
            ting=ting,
        )
