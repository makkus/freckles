# -*- coding: utf-8 -*-
import copy
import logging
import pprint
from collections import OrderedDict

from ruamel.yaml.comments import CommentedMap

from frutils import replace_string
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
        vars = create_vars_for_task_item(task, user_input)
        task["input"] = vars


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

    for var_name, var_details in arg_tree.items():

        try:
            key, value = create_var_value(
                var_name, var_details, user_input, task_item=task_item
            )

            vars[key] = value
        except (Exception) as e:

            control = task_item.get("control", {})
            skip = task_item.get("skip", None)

            print("KEY: {}".format(var_name))
            print("skip: {}".format(skip))

            if (
                "skip" in task_item.get("control", {}).keys()
                or "skip"
                in task_item.get("control", {}).get("inherited_keys", {}).keys()
            ):
                log.debug("Invalid var, assuming this task will be skipped later on.")
            else:
                # TODO: attach task information
                log.warning("Invalid task item: {}".format(task_item[FRECKLET_NAME]))
                raise e

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
        for pk, pv in p_vars.items():
            k, v = create_var_value(pk, pv, user_input, task_item)
            repl[k] = v

        replaced = replace_string(
            p_var_name, repl, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
        )

        try:
            # print("XXX")
            # print("VAR_NAME: {}".format(var_name))
            # import pp
            # pp(task_item)
            # pp(replaced)
            # pp(repl)
            validated = validate_var(var_name, replaced, arg)
        except (ParametersException) as pe:
            # if not none_value:
            raise pe
            # else:
            #     msg = str(pe)
            #     parameters = pe.parameters
            #     new_msg = (
            #         msg
            #         + ". This is most likely because a parent frecklet does not forward a required var to this frecklet. Be aware that every non-defined parent var does invalidate the whole child var, even if it contains other content (strings/template vars)."
            #     )
            #     new_pe = ParametersException(parameters=parameters, errors=new_msg)
            #     raise new_pe

        return (var_name, validated)

    else:

        if not isinstance(arg, (dict, CommentedMap, OrderedDict)) or not arg.get(
            "__is_arg__", False
        ):
            value = arg
        else:
            value = user_input.get(var_name, None)
            default = arg.get("default", None)

            if value is None:

                if arg.get("required", True):

                    if default is None:
                        raise Exception(
                            "No value provided for required arg '{}'".format(var_name)
                        )
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


def consolidate_arguments(argument_lists):

    result = {}
    meta_dict = {}

    for args in argument_lists:

        for arg_name, d in args.items():
            details = d["arg"]
            meta = d["meta"]

            level_new = meta["__frecklet_level__"]

            if level_new > 0:
                continue
            if not isinstance(details, (dict, CommentedMap, OrderedDict)):
                continue

            if not details.get("__is_arg__", False):
                continue

            if arg_name in result.keys():

                level_current = meta_dict.get(arg_name, {}).get(
                    "__frecklet_level__", None
                )

                if level_new < level_current:
                    meta_dict[arg_name] = meta
                    result[arg_name] = details

                elif level_new == level_current:

                    use_new_arg = new_arg_is_better(result[arg_name], details)

                    if use_new_arg is None:

                        raise Exception(
                            "Duplicate argument, not sure which one to use: {}".format(
                                arg_name
                            )
                        )
                    else:
                        if use_new_arg:
                            result[arg_name] = details
                            meta_dict[arg_name] = meta
                        continue

            result[arg_name] = details
            meta_dict[arg_name] = meta

    return result


def extract_base_args(tasklist):
    """Extract the base args that are needed as input for this tasklist.

    Args:
        tasklist (list): the tasklist

    Returns:
        dict: the args dict
    """
    result = []
    for task in tasklist:
        args = extract_base_args_from_task_item(task)
        # req = calculate_required_user_input(args)
        result.append(args)

    args = consolidate_arguments(result)
    return args


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
            if k in args.keys():
                old = args[k]
                new = v

                old_level = old["meta"]["__frecklet_level__"]
                new_level = new["meta"]["__frecklet_level__"]

                if old_level < new_level:
                    continue

                elif old_level == new_level:

                    use_new_arg = new_arg_is_better(old["arg"], new["arg"])
                    if use_new_arg is None:

                        raise Exception(
                            "Key '{}' already in args list, and different metadata".format(
                                k
                            )
                        )
                    else:
                        if use_new_arg:
                            args[k] = new
                        continue
            else:
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
        for k, v in parent_vars.items():

            parse_arg_tree_branch(k, v, base_args=base_args)

    elif "arg" in var_tree.keys():
        meta = var_tree["__meta__"]
        if var_name in base_args.keys():
            old = base_args[var_name]
            new = {"arg": var_tree["arg"], "meta": meta}
            if old != new:
                raise Exception(
                    "Key '{}' already in args list, with different metadata".format(
                        var_name
                    )
                )
        base_args[var_name] = {"arg": var_tree["arg"], "meta": meta}

    return base_args
