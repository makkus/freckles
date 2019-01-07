# -*- coding: utf-8 -*-
import copy
import logging
from collections import OrderedDict

from ruamel.yaml.comments import CommentedMap

from frutils import dict_merge, get_template_keys, replace_strings_in_obj
from frutils.exceptions import ParametersException
from frutils.parameters import FrutilsNormalizer
from .defaults import DEFAULT_FRECKLES_JINJA_ENV, FRECKLET_NAME, TASK_INSTANCE_NAME
from .exceptions import FrecklesConfigException

log = logging.getLogger("freckles")

DEFAULT_INHERIT_ARGS_LEVEL = 0


def get_parent_chain(task_item):

    start = task_item
    chain = [start["meta"]["__name__"]]
    while "parent" in start.keys() and start["parent"]:
        start = start["parent"]
        chain.append(start["meta"]["__name__"])

    return chain


def create_vars_for_task_item(task_item, user_input, base_args, frecklet):
    """Calculates all necessary values for vars in a task item.

    Args:
      tasklist (list): a list of dicts, describing one task each
      user_input (dict): the user input
      base_args (dict): a dictionary of argument descriptions

    Returns:
      dict: the values
    """

    # the arg tree is a dict that contains details for every var required for a var
    vars = {}
    # pp(task_item)
    # print("--------")
    # pp(base_args)
    # sys.exit()
    # TODO: prevent duplicate processing for base args that end up in a single var
    for var_name, var_details in task_item["arg_tree"].items():

        try:
            # print(var_name)
            # pp(var_details)
            # print(task_item["vars"])
            # print(task_item["aux_vars"])
            # print(task_item["parent"]["args"])

            vars_new = create_var_value(var_name, var_details, user_input)

        except (Exception) as e:

            # control = task_item.get(TASK_INSTANCE_NAME, {})
            # skip = task_item.get("skip", None)

            if (
                "skip" in task_item.get(TASK_INSTANCE_NAME, {}).keys()
                or "skip"
                in task_item.get(TASK_INSTANCE_NAME, {})
                .get("inherited_keys", {})
                .keys()
            ):
                log.debug("Invalid var, assuming this task will be skipped later on.")
                continue
            else:
                # TODO: attach task information
                log.warning("Invalid task item: {}".format(task_item[FRECKLET_NAME]))
                log.debug(e, exc_info=True)
                log.debug(
                    "Issue with task item: {}".format(task_item["meta"]["__name__"])
                )
                log.debug("Task chain: {}".format(get_parent_chain(task_item)))
                raise e

        # TODO: check for duplicates
        dict_merge(vars, vars_new, copy_dct=False)

    # # now validating the whole task item, in case there was something not forwarded in the chain
    # for n, d in task_item["arg_tree"].items():
    #     required = d["arg"].get("required", True)
    #     if required:
    #         if n not in vars.keys():
    #             import pp
    #             print("TASK\n\n\n\n\n\n\n\n\n\n")
    #             pp(task_item)
    #             print('-------')
    #             print(user_input)
    #             raise FreckletException("Required task variable '{}' not available for task '{}', this indicates it hasn't been forwarded from a parent task.".format(n, d["meta"].get("__parent_name__", "n/a")), frecklet)
    #     empty = d["arg"].get("empty", False)
    #     if not empty:
    #         if vars.get(n, None) is not None and not isinstance(vars[n], bool) and not vars[n]:
    #             raise FreckletException("Task argument '{}' empty, this is not allowed by its schema: '{}'.".format(n, d["arg"]), frecklet)

    return vars


def validate_var(key_name, value, schema, password_coerced=True):

    schema = copy.deepcopy(schema)
    schema.pop("doc", None)
    schema.pop("cli", None)
    schema.pop("__meta__", None)
    schema.pop("__auto_generated__", None)
    schema.pop("__is_arg__", None)
    schema.pop("dependencies", None)  # we only validate a single argument here

    if password_coerced:
        schema.pop("coerce", None)

    if schema.get("type", "string") == "password":
        schema["type"] = "string"

    s = {key_name: schema}
    if value is not None:
        d = {key_name: value}
    else:
        d = {}

    val = FrutilsNormalizer(s)
    # import pp, traceback
    # print(key_name)
    # print(value)
    # pp(d)
    # traceback.print_stack()
    valid = val.validated(d)
    if valid is None:
        raise ParametersException(d, val.errors)

    return valid.get(key_name, None)


def get_paths_for_level(level, paths):

    relevant_paths = {}
    for p in paths:
        path_level = p[1]["meta"]["__frecklet_level__"]
        if level == path_level:
            relevant_paths[p[0]] = p[1]
            continue
        # we don't need higher-order paths
        if level < path_level:
            break

    if not relevant_paths:
        return None

    return relevant_paths


# def get_vars_for_level(relevant_paths, input):
#
#     import pp
#     print("REL PATHS")
#     pp(relevant_paths)
#     print("INPUT: {}".format(input))
#
#     result = {}
#     for k, v in relevant_paths.items():
#
#         parent_var = v["parent_var"]
#         if parent_var is None:
#             v_new = input.get(k, None)
#         else:
#             v_new = replace_strings_in_obj(parent_var, input, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
#
#         arg = v["arg"]
#         # arg_type = arg.get("type", "unknown")
#         # if arg_type == "unknown":
#         #     validated = validate_var(k, v_new, arg)
#         #     result[k] = validated
#         #     continue
#
#         try:
#             validated = validate_var(k, v_new, arg)
#             print("--------")
#             print(v["meta"]["__name__"])
#             import pp
#             pp(v)
#             print("KEY: {}".format(k))
#             print("VALIDATED: {}".format(validated))
#             print("================")
#             result[k] = validated
#         except (ParametersException) as pe:
#             log.debug("Invalid input for '{}': {}".format(k, input))
#             log.debug(pe, exc_info=1)
#             raise pe
#
#     return result


def create_var_value(var_name, var_details, input):
    """Calculates the value for a var (within a task).

    Takes into consideration the user input, the parent task value, and potential defaults.

    Args:
      var_name (string): the top-level var name
      var_details (dict): the var details from the arg_tree
      user_input (dict): the user input
      task_item (dict): the current task item

    Returns:
        tuple: a tuple in the form: (key, value)
    """

    arg = var_details["arg"]

    if "parent" in var_details.keys():

        if "parent_var" not in var_details.keys():
            raise Exception(
                "Missing parent var value, this is probably a bug: {}".format(
                    var_details
                )
            )

        parent = var_details["parent"]
        parent_var = var_details["parent_var"]

        repl = {}
        for k, v in parent.items():
            temp = create_var_value(k, v, input)
            dict_merge(repl, temp, copy_dct=False)

        replaced = replace_strings_in_obj(
            parent_var, repl, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
        )
        result = {var_name: replaced}

    else:
        if "parent_var" in var_details.keys() and var_details["parent_var"] is not None:
            result = {var_name: var_details["parent_var"]}
        else:
            result = {var_name: input.get(var_name, None)}

    try:
        validated = validate_var(var_name, result.get(var_name, None), arg)
        return {var_name: validated}

    except (ParametersException) as pe:
        log.debug("Invalid input for '{}': {}".format(var_name, input))
        log.debug(pe, exc_info=1)
        raise pe


def new_arg_is_better(old_arg, new_arg, default=False):
    """
    Picks the more current, non-autogenerated of the two.

    Returns None if it can't decide. If both are equal in all relevant ways, returns the default (or the old one, if that isn't specified.).

    Args:
        old_arg (dict): the old arg
        new_arg (dict: the new arg

    Returns:
        bool: whether the new arg is a better choice (True) or not (False), or None if they are equal
    """

    if old_arg.get("__auto_generated__", False) and not new_arg.get(
        "__auto_generated__", False
    ):
        # use copy new
        return True
    elif not old_arg.get("__auto_generated__", False) and new_arg.get(
        "__auto_generated__", False
    ):
        # all good
        return False

    copy_old = copy.copy(old_arg)
    copy_new = copy.copy(new_arg)

    copy_old.pop("doc", None)
    copy_old.pop("cli", None)
    copy_new.pop("doc", None)
    copy_new.pop("cli", None)

    if copy_old != copy_new:
        return None
    else:
        return default


def add_arguments(result_args, arg_path, arg_inherit_strategy="none"):

    # now we determine the arg schema (in case it's not declared in level 0
    for p in arg_path:
        arg_name = p[0]
        min_level = p[1]["meta"]["__frecklet_level__"]

        if min_level > 0:
            # this means this isn't a top-order argument
            continue

        # TODO: check if already added
        result_args[arg_name] = {"path": arg_path}

        arg_type = p[1]["arg"].get("type", "unknown")
        if arg_type != "unknown":

            arg = copy.deepcopy(p[1]["arg"])
            level = p[1]["meta"]["__frecklet_level__"]
            if level > 0:
                arg.setdefault("cli")["param_type"] = "option"

        else:
            temp_arg_name = arg_name
            arg = None
            # here we try whether we can auto-determine the arg schema,
            # based on the childs of this arg
            for path in arg_path:
                path_arg_name = path[0]
                path_details = path[1]
                path_level = path_details["meta"]["__frecklet_level__"]
                if path_level == 0:
                    continue
                parent_var = path_details["parent_var"]

                if not parent_var:
                    break
                if temp_arg_name not in parent_var:
                    break

                if parent_var != "{{{{:: {} ::}}}}".format(temp_arg_name):
                    break

                arg_temp = path_details["arg"]
                type_temp = arg_temp.get("type", "unknown")
                if type_temp != "unknown":
                    arg = copy.deepcopy(arg_temp)
                    arg.setdefault("cli", {})["param_type"] = "option"

                    break
                else:
                    temp_arg_name = path_arg_name

            if arg is None:
                arg = get_default_arg()

        if "required" not in arg.keys():
            arg["required"] = True
        if "empty" not in arg.keys():
            arg["empty"] = False

        result_args[arg_name]["arg"] = arg

    return True


def consolidate_arguments(argument_lists, arg_inherit_strategy="none"):

    result = {}
    other_required = {}

    for args in argument_lists:

        for arg_name, path in args.items():

            if add_arguments(result, path, arg_inherit_strategy=arg_inherit_strategy):
                continue

            # arg = path[0][1]["arg"]
            #
            # if arg.get("type", "unknown") == "unknown":
            #     # we assume this is not required
            #     continue
            #
            # required = arg.get("required", True)
            # if required:
            #     other_required.setdefault(path[0][0], []).append(path)

    if other_required:
        raise FrecklesConfigException(
            "One or more required vars don't are not set within the chain: {}".format(
                other_required.keys()
            )
        )

    return result


# def get_unknown_arg():
#
#     return {"required": True, "empty": False}


def get_default_arg():

    return {"required": True, "empty": False}


def extract_base_args(task_list):
    """Extract the base args that are needed as input for this tasklist.

    Args:
        tasklist (list): the tasklist

    Returns:
        dict: the args dict
    """

    result = []
    for task in task_list:
        arg_tree = create_arg_tree_for_task(task)
        task["arg_tree"] = arg_tree
        flatten = flatten_arg_tree(arg_tree)
        result.append(flatten)

    args = consolidate_arguments(result)

    return args


def find_leaf_node_paths_old(arg_tree):

    leafs = []

    def _get_leaf_nodes(node):

        for var_name, var_details in node.items():

            arg_parent = None

            item = (var_name, var_details, arg_parent)

            if not isinstance(
                var_details, (dict, CommentedMap, OrderedDict)
            ) or not var_details.get("__is_arg_tree__", False):
                # adding fixed values
                leafs.append(item)
            else:
                if "parent" in var_details.keys():
                    # recursing
                    _get_leaf_nodes(var_details["parent"])
                else:
                    # adding leaf node
                    leafs.append(item)

    _get_leaf_nodes(arg_tree)

    return leafs


def find_leaf_node_paths(arg_name, arg_details):

    if not isinstance(
        arg_details, (dict, CommentedMap, OrderedDict)
    ) or not arg_details.get("__is_arg_tree__", False):
        # means we have a 'value'
        return [(arg_name, arg_details)]

    if "parent" not in arg_details:
        return [(arg_name, arg_details)]

    parent_args = arg_details["parent"]
    result = []
    for a_name, arg in parent_args.items():
        ln = find_leaf_node_paths(a_name, arg)
        result.extend(ln)
    result.append((arg_name, arg_details))
    return result


def flatten_arg_tree(arg_tree):

    args = {}
    for arg_name, arg_details in arg_tree.items():
        path = find_leaf_node_paths(arg_name, arg_details)
        temp = []
        # clean up list
        for p in path:
            d = copy.copy(p[1])
            d.pop("parent", None)
            temp.append((p[0], d))
        args[arg_name] = temp

    return args


def create_arg_tree_for_task(task_item, task_cache={}):
    """Extract args needed for a task item.

    Args:
        task_item (dict): the task item

    Returns:
        dict: the args
    """

    task_id = task_item["meta"]["__id__"]

    if task_id in task_cache.keys():
        return task_cache[task_id]

    template_keys = task_item["meta"]["__template_keys__"]

    arg_tree = {}

    for key in template_keys["all"]:
        if key in task_item["args"].keys():
            arg = task_item["args"][key]
        else:
            arg = get_default_arg()

        if "required" not in arg.keys():
            arg["required"] = True
        if "empty" not in arg.keys():
            arg["empty"] = False

        if task_item["parent"] is None:
            arg_tree[key] = {
                "arg": arg,
                "meta": task_item["meta"],
                "__is_arg_tree__": True,
                "parent_var": None,
            }
        else:
            parent_tree = create_arg_tree_for_task(task_item["parent"])
            parent_var = task_item["parent"]["vars"].get(key, None)
            temp_var = parent_var
            if not parent_var:
                parent_var = task_item["parent"].get("aux_vars", {}).get(key, None)
                temp_var = parent_var

            if not parent_var:
                parent_var_template_keys = []
            else:

                parent_var_template_keys = get_template_keys(
                    parent_var, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
                )
                # parent_var_template_keys = []

            parent_relevant_tree = {}
            for pvtk in parent_var_template_keys:
                parent_relevant_tree[pvtk] = parent_tree[pvtk]

            arg_tree[key] = {
                "parent_var": temp_var,
                "arg": arg,
                "meta": task_item["meta"],
                "__is_arg_tree__": True,
            }
            if parent_relevant_tree:
                arg_tree[key]["parent"] = parent_relevant_tree

    task_cache[task_id] = arg_tree
    # import pp
    # pp(arg_tree)
    return arg_tree
