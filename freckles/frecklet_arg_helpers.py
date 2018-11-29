# -*- coding: utf-8 -*-
import copy
import logging
import pprint
from collections import OrderedDict

from ruamel.yaml.comments import CommentedMap

from frutils import replace_string
from frutils.defaults import OMIT_VALUE
from frutils.exceptions import ParametersException
from frutils.parameters import FrutilsNormalizer
from .defaults import DEFAULT_FRECKLES_JINJA_ENV, FRECKLET_NAME
from .exceptions import FrecklesConfigException

log = logging.getLogger("freckles")

DEFAULT_INHERIT_ARGS_LEVEL = 0


def add_user_input(tasklist, user_input):
    """Augments a task item with user input.

    If there is no user input for a var, the value will be calculated out of the 'arg_tree', which includes looking at
    parent values and defaults.

    Args:
      tasklist (list): a list of dicts, describing one task each
      user_input (dict): the user input

    """
    for task in tasklist:
        vars, omit_keys = create_vars_for_task_item(task, user_input)
        task["input"] = vars
        task["omit_keys"] = omit_keys


def create_vars_for_task_item(task_item, user_input):
    """Calculates all necessary values for vars in a task item.

    Args:
      tasklist (list): a list of dicts, describing one task each
      user_input (dict): the user input

    Returns:
      dict: the values
    """

    # the arg tree is a dict that contains details for every var required for a var
    arg_tree = task_item["arg_tree"]
    vars = {}
    omit_keys = []

    for var_name, var_details in arg_tree.items():

        try:
            key, value = create_var_value(var_name, var_details, user_input, task_item=task_item)
            if value == OMIT_VALUE or value is None:
                omit_keys.append(key)
                continue
            vars[key] = value
        except (Exception) as e:
            # TODO: double check this is ok
            if "__skip__" in task_item[FRECKLET_NAME].keys():
                log.debug("Invalid var, assuming this task will be skipped later on.")
            else:
                # TODO: attach task information
                raise e

    return vars, omit_keys


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
    valid = val.validated(d)

    if valid is None:
        raise ParametersException(d, val.errors)

    if value is not None:
        return valid[key_name]
    else:
        return None


def create_var_value(var_name, var_details, user_input, task_item):
    """Calculates the value for a var (within a task).

    Takes into consideration the user input, the parent task value, and potential defaults.

    Args:
      var_name (string): the var name
      var_details (dict): the var details
      user_input (dict): the user input
      task_item (dict): the current task item

    Returns:
        tuple: a tuple in the form: (key, value)
    """

    parent_values = var_details.get("parent", None)
    arg = var_details["arg"]

    if parent_values is not None:

        # this means parents have something to say about the value of this var
        # so we recursively check whether there is anything relevant in there
        # and build a dictionary we can use to replace the value recursively, until
        # we end up at the user input

        p_var_name = parent_values["var_name"]
        p_vars = parent_values["vars"]

        repl = {}
        none_value = False
        for pk, pv in p_vars.items():
            k, v = create_var_value(pk, pv, user_input, task_item)
            if v == OMIT_VALUE or v is None:
                # means it's a non-required var, with no default value
                none_value = True
            else:
                repl[k] = v

        if none_value:
            replaced = None
        else:
            replaced = replace_string(p_var_name, repl, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)

        try:
            validated = validate_var(var_name, replaced, arg)
        except (ParametersException) as pe:
            if not none_value:
                raise pe
            else:
                msg = str(pe)
                parameters = pe.parameters
                new_msg = msg + ". This is most likely because a parent frecklet does not forward a required var to this frecklet. Be aware that every non-defined parent var does invalidate a whoe child var, even if it contains other content (strings/template vars)."
                new_pe = ParametersException(parameters=parameters, errors=new_msg)
                raise new_pe
        if none_value:
            return (var_name, OMIT_VALUE)
        return (var_name, validated)

    else:

        if not isinstance(arg, (dict, CommentedMap, OrderedDict)) or not arg.get("__is_arg__", False):
            value = arg
        else:
            value = user_input.get(var_name, None)
            default = arg.get("default", None)

            if value is None:

                if arg.get("required", True):

                    if default is None:
                        raise Exception("No value provided for required arg '{}'".format(var_name))
                    else:
                        value = default
                else:
                    if default is None:
                        return (var_name, None)
                    else:
                        value = default
        try:
            validated = validate_var(var_name, value, arg)
            return (var_name, validated)
        except (ParametersException) as e:

            raise FrecklesConfigException(
                "Invalid or missing argument '{}':\n\nvalue:\n{}\n\nschema:\n{}\n\n  => {}".format(
                    var_name, pprint.pformat(value), pprint.pformat(arg), e.errors
                )
            )


def calculate_required_user_input(args):

    result = []
    for a_name, details in args.items():

        end_nodes = get_end_nodes(a_name, details)
        result.append(end_nodes)

    return result

def get_end_nodes(arg, var_tree, end_nodes=None):

    if end_nodes is None:
        end_nodes = {}

    for var_name, var_details in var_tree.items():
        if "parent" in var_details.keys():

            p_var_name = var_details["parent"]["var_name"]
            p_vars = var_details["parent"]["vars"]

            get_end_nodes(p_var_name, p_vars, end_nodes=end_nodes)

        else:
            # if not, we use a default
            if "value" not in var_details.keys():

                arg = var_details["arg"]
                if var_name in end_nodes.keys():
                    raise Exception("End node key '{}' already in list of keys.".format(var_name))
                end_nodes[var_name] = arg

    return end_nodes


def consolidate_arguments(argument_lists):

    result = {}

    for arg_list in argument_lists:

        for args in arg_list:
            for arg_name, details in args.items():

                if arg_name in result.keys():
                    raise Exception("Duplicate argument: {}".format(arg_name))

                if not isinstance(details, (dict, CommentedMap, OrderedDict)):
                    continue

                if not details.get("__is_arg__", False):
                    continue

                result[arg_name] = details

    return result



def extract_base_args(tasklist, inherit_args_mode=DEFAULT_INHERIT_ARGS_LEVEL):
    """Extract the base args that are needed as input for this tasklist.

    Args:
        tasklist (list): the tasklist

    Returns:
        dict: the args dict
    """
    result = []
    for task in tasklist:
        args = extract_base_args_from_task_item(task)
        req = calculate_required_user_input(args)
        result.append(req)

    args = consolidate_arguments(result)

    # sort order
    sorted_args = OrderedDict()
    for n in sorted(args.keys()):
        sorted_args[n] = args[n]

    return sorted_args


def extract_base_args_from_task_item(task_item):
    """Extract args needed for a task item.

    Args:
        task_item (dict): the task item

    Returns:
        dict: the args
    """

    args_tree = task_item["arg_tree"]

    args = {}

    for var_name, item in args_tree.items():

        args_temp = parse_arg_tree_branch(var_name, item, base_args={})

        for k, v in args_temp.items():
            if k in args:
                raise Exception("Key '{}' already in args list".format(k))

        args[k] = v

    return args


def parse_arg_tree_branch(var_name, var_tree, base_args={}):
    """Parses a single arg tree branch.

    Args:
        branch (dict): the arg_tree branch

    Returns:
        the parent leaf or value
    """

    if "parent" in var_tree.keys():

        parent = var_tree["parent"]
        # parent_var_name = parent["var_name"]
        parent_vars = parent["vars"]
        parse_arg_tree_branch(var_name, parent_vars, base_args=base_args)

    else:
        if var_name in base_args.keys():
            raise Exception("Key '{}' already in args list".format(var_name))

        base_args[var_name] = var_tree

    return base_args
