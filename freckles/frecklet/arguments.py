import click

from freckles.defaults import DEFAULT_FRECKLES_JINJA_ENV, FRECKLES_DEFAULT_ARG_SCHEMA
from freckles.exceptions import FreckletException
from frutils import get_template_keys, dict_merge
from frutils.parameters import VarsTypeSimple
from ting.ting_attributes import TingAttribute, Arg
from ting.ting_cast import MultiCacheResult


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

    DEFAULT_CLI_SCHEMA = {
        "show_default": True,
        "param_type": "option",
    }

    def __init__(self, target_attr_name="cli_arguments", source_attr_name="required_vars"):

        self.target_attr_name = target_attr_name
        self.source_attr_name = source_attr_name

    def provides(self):

        return [self.target_attr_name]

    def requires(self):

        return [self.source_attr_name]

    def get_attribute(self, ting, attribute_name=None):

        # TODO: validate

        required_vars = getattr(ting, self.source_attr_name)

        result = []
        for var in required_vars.values():
            parameter = self.create_parameter(var)
            if parameter is not None:
                result.append(parameter)

        return result

    def create_parameter(self, var):

        if not var.cli.get("enabled", True):
            return None

        option_properties = dict_merge(CliArgumentsAttribute.DEFAULT_CLI_SCHEMA, var.cli, copy_dct=True)

        param_type = option_properties.pop("param_type")

        option_properties["required"] = var.required
        if var.default is not None:
            option_properties["default"] = var.default

        if "param_decls" not in option_properties.keys():
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

        replacement = CliArgumentsAttribute.CLICK_CEREBUS_ARG_MAP.get(cerberus_type, None)
        if replacement is not None:
            if replacement == bool:
                if "is_flag" not in option_properties.keys():
                    option_properties["is_flag"] = True
                    # we don't add the type here, otherwise click fails for whatever reason
            else:
                option_properties["type"] = replacement

        elif cerberus_type == "list":
            arg_schema = var.schema.get("schema", {})
            schema_type = arg_schema.get("type", "string")
            replacement = CliArgumentsAttribute.CLICK_CEREBUS_ARG_MAP.get(schema_type, click.STRING)
            option_properties["type"] = replacement
            if param_type == "option":
                option_properties["multiple"] = True
            else:
                option_properties["nargs"] = -1
        else:
            raise Exception("Type '{}' not implemented yet.".format(cerberus_type))

        if param_type == "option":
            option_properties["help"] = var.doc.get_short_help()
            p = click.Option(**option_properties)
        else:
            option_properties.pop("show_default", None)
            if (
                "nargs" in option_properties.keys()
                and "default" in option_properties.keys()
            ):
                option_properties.pop("nargs")
            p = click.Argument(**option_properties)

        return p

class RequiredVariablesAttribute(TingAttribute):

    def __init__(self, target_attr_name="required_vars"):

        self.target_attr_name = target_attr_name

    def provides(self):

        return [self.target_attr_name, "{}_tree".format(self.target_attr_name)]

    def requires(self):

        return ["task_tree"]

    def get_attribute(self, ting, attribute_name=None):

        task_tree = ting.task_tree
        paths_to_leaves = task_tree.paths_to_leaves()
        required_vars_tree = {}
        for path in paths_to_leaves:
            leaf_node_id = path[-1]
            args = self.get_required_vars_from_path(path_to_leaf=path, tree=task_tree, ting=ting)
            required_vars_tree[leaf_node_id] = args


        required_vars = self.consolidate_vars(required_vars_tree, ting)

        result = {
            "{}_tree".format(self.target_attr_name): required_vars_tree,
            self.target_attr_name: required_vars,
        }
        return MultiCacheResult(**result)


    def consolidate_vars(self, required_vars_tree, ting):

        result = {}
        for args in required_vars_tree.values():

            for arg_name, arg in args.items():

                if arg in result.keys():
                    raise FreckletException("Duplicate arg '{}' in frecklet '{}'".format(arg_name, ting.id))

                result[arg_name] = arg

        return result

    def resolve_required_vars(self, current_args, rest_path, last_node, tree):

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
                    raise FreckletException("Invalid frecklet-task '{}' in '{}': does not provide required/non-defaulted var '{}' for child frecklet '{}'.".format(current_node.tag, tree.get_node(0).tag, key, last_node.tag), tree.get_node(0).tag)

                # means we don't have to worry about this key, as it is not used and not required
                continue
            else:
                parent_var = vars[key]
                # print("PARENT VAR: {}".format(parent_var))
                if parent_var == "{{{{:: {} ::}}}}".format(key):
                    # print("MATCH")
                    # this means the var is just being carried forward, from the point of view of the parent frecklet task
                    arg_config = available_args.get(key, None)
                    if arg_config is None:
                        # print("USING CHILD ARG")
                        new_arg = arg
                    else:
                        new_arg = Arg(key, arg_config, default_schema=FRECKLES_DEFAULT_ARG_SCHEMA)
                        new_arg.add_child(arg)
                        new_arg.var_template = parent_var

                    args[key] = new_arg
                else:
                    template_keys = get_template_keys(parent_var, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
                    for tk in template_keys:
                        arg_config = available_args.get(tk, None)
                        if arg_config is None:
                            if tk == key:
                                new_arg = arg
                            else:
                                new_arg = Arg(key, {}, default_schema=FRECKLES_DEFAULT_ARG_SCHEMA)
                                new_arg.add_child(arg)
                        else:
                            new_arg = Arg(key, arg_config, default_schema=FRECKLES_DEFAULT_ARG_SCHEMA)
                            new_arg.add_child(arg)

                        new_arg.var_template = parent_var
                        args[tk] = new_arg

        if current_node_id != 0:
            return self.resolve_required_vars(current_args=args, rest_path=rest_path, last_node=current_node, tree=tree)
        else:
            return args



    def get_required_vars_from_path(self, path_to_leaf, tree, ting):

        root = path_to_leaf[-1]
        root_node = tree.get_node(root)
        # end = path_to_leave[0]

        available_args = root_node.data["root_frecklet"].args
        template_keys = root_node.data["root_frecklet"].template_keys
        args = Arg.from_keys(template_keys, available_args, default_schema=FRECKLES_DEFAULT_ARG_SCHEMA)
        rest_path = reversed(path_to_leaf[0:-1])

        return self.resolve_required_vars(current_args=args, rest_path=rest_path, last_node=root_node, tree=tree)


