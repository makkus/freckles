# -*- coding: utf-8 -*-
import copy
import logging
import os
from collections import Mapping

from colorama import Style
from six import string_types
from treelib import Tree

from freckles.defaults import (
    TASK_KEY_NAME,
    FRECKLET_KEY_NAME,
    ARGS_KEY,
    VARS_KEY,
    DEFAULT_FRECKLES_JINJA_ENV,
    FRECKLETS_KEY,
    FRECKLES_DEFAULT_ARG_SCHEMA,
)
from freckles.exceptions import FrecklesConfigException, FreckletBuildException
from frkl import FrklProcessor, Frkl
from frkl.defaults import (
    CHILD_MARKER_NAME,
    DEFAULT_LEAF_NAME,
    DEFAULT_LEAFKEY_NAME,
    OTHER_KEYS_NAME,
    KEY_MOVE_MAP_NAME,
)
from frkl.processors import ConfigProcessor
from frutils import add_key_to_dict, get_template_keys, special_dict_to_dict
from ting.ting_attributes import ValueAttribute, TingAttribute

log = logging.getLogger("freckles")


class FreckletsAttribute(ValueAttribute):
    def __init__(self):

        super(FreckletsAttribute, self).__init__(
            target_attr_name="frecklets", source_attr_name="_metadata"
        )

    def get_attribute(self, ting, attribute_name=None):

        result = ValueAttribute.get_attribute(self, ting, attribute_name=attribute_name)
        return result


def fill_defaults(task_item):

    if FRECKLET_KEY_NAME not in task_item.keys():
        task_item[FRECKLET_KEY_NAME] = {}

    if TASK_KEY_NAME not in task_item.keys():
        task_item[TASK_KEY_NAME] = {}

    if (
        "name" not in task_item[FRECKLET_KEY_NAME].keys()
        and "command" not in task_item[TASK_KEY_NAME].keys()
    ):
        ti = {}
        ti[TASK_KEY_NAME] = task_item[TASK_KEY_NAME]
        ti[FRECKLET_KEY_NAME] = task_item[FRECKLET_KEY_NAME]

        raise FrecklesConfigException(
            "Neither 'task/command' nor 'frecklet/name' key in task config: {}".format(
                ti
            )
        )

    if "name" not in task_item[FRECKLET_KEY_NAME].keys():
        task_item[FRECKLET_KEY_NAME]["name"] = task_item[TASK_KEY_NAME]["command"]
    elif "command" not in task_item[TASK_KEY_NAME].keys():
        task_item[TASK_KEY_NAME]["command"] = task_item[FRECKLET_KEY_NAME]["name"]

    if "type" not in task_item[FRECKLET_KEY_NAME].keys():
        task_item[FRECKLET_KEY_NAME]["type"] = "frecklet"


class ExplodedArgsProcessor(ConfigProcessor):
    """Sets the exploded args property."""

    def __init__(self, **init_params):

        self.args = init_params["args"]

    def process_current_config(self):

        new_config = self.current_input_config
        new_config["args"] = self.args
        return new_config


class SpecialCaseProcessor(ConfigProcessor):
    """Makes sure that no keywords are in vars."""

    def process_current_config(self):

        new_config = self.current_input_config

        frecklets = new_config.pop("frecklets", [])
        new_config["frecklets"] = []

        for task in frecklets:

            if (
                isinstance(task, Mapping)
                and "target" in task.keys()
                and FRECKLET_KEY_NAME in task.keys()
            ):

                # this is a frecklecutable, let's wrap it in one so users don't have to do it
                task = {"frecklecute": task}

            elif (
                isinstance(task, Mapping)
                and FRECKLET_KEY_NAME in task.keys()
                and isinstance(task[FRECKLET_KEY_NAME], string_types)
            ):

                frecklet_name = task.pop(FRECKLET_KEY_NAME)
                task[FRECKLET_KEY_NAME] = {"name": frecklet_name}

            if isinstance(task, Mapping) and len(task) == 1:

                task_name = list(task.keys())[0]
                value = task[task_name]

                if (
                    FRECKLET_KEY_NAME in value.keys()
                    or TASK_KEY_NAME in value.keys()
                    or VARS_KEY in value.keys()
                ):
                    new_task = {
                        FRECKLET_KEY_NAME: {"name": task_name},
                        VARS_KEY: task[task_name],
                    }
                    task = new_task

            new_config["frecklets"].append(task)

            # if task.get(FRECKLET_KEY_NAME, {}).get("name", None) == "frecklecute":
            #     print("HIT")
            #     import sys
            #     sys.exit()
            #     task[FRECKLET_KEY_NAME]["type"] = "frecklecutable"

        return new_config


class CommandNameProcessor(ConfigProcessor):
    """Adds potential missing command/name keys."""

    def process_current_config(self):

        new_config = self.current_input_config

        fill_defaults(new_config)
        return new_config


class DirectParentArgsProcessor(ConfigProcessor):
    """Adds arguments for 'direct' parents.

    For example if a frecklet has something like:

        - user-exists:
           name: "{{:: name ::}}"

    Where the variable name stays the same, and no filter is involved, the args will be inherited directly.
    """

    def __init__(self, **init_params):

        self.index = init_params["index"]

    def process_current_config(self):
        new_config = self.current_input_config

        args = new_config.setdefault("args", {})

        vars = new_config.get("vars", {})
        for k, v in vars.items():

            if k in args.keys():
                continue

            if "{{{{:: {} ::}}}}".format(k) == v:

                parent_name = new_config[FRECKLET_KEY_NAME]["name"]
                parent = self.index.get(parent_name)
                if parent is None:
                    raise FreckletBuildException(
                        "Can't assemble frecklet.",
                        reason="Parent frecklet '{}' not available.".format(
                            parent_name
                        ),
                    )

                p_args = parent.args
                a = p_args.get(k, None)
                if a is not None:
                    args[k] = a
                else:
                    args[k] = copy.deepcopy(FRECKLES_DEFAULT_ARG_SCHEMA)

        return new_config


class TaskTypePrefixProcessor(ConfigProcessor):
    """Adds a 'become': True key/value pair if the task name is all uppercase."""

    def process_current_config(self):

        new_config = self.current_input_config

        command_name = new_config[TASK_KEY_NAME].get("command", None)
        task_type = new_config[FRECKLET_KEY_NAME].get("type", None)

        if "::" in command_name:

            if task_type is not None:
                raise FrecklesConfigException(
                    "Invalid task item '{}': command name contains '::', but type is already specified.".format(
                        new_config
                    )
                )

            task_type, command_name = command_name.split("::", 1)

            new_config[TASK_KEY_NAME]["command"] = command_name
            new_config[FRECKLET_KEY_NAME]["type"] = task_type

        become = new_config[TASK_KEY_NAME].get("become", None)

        if task_type and task_type.isupper() and become is None:
            new_config[TASK_KEY_NAME]["become"] = True
            new_config[FRECKLET_KEY_NAME]["type"] = task_type.lower()

        if command_name.isupper() and become is None:
            new_config[TASK_KEY_NAME]["become"] = True
            new_config[TASK_KEY_NAME]["command"] = command_name.lower()
            name = new_config[FRECKLET_KEY_NAME].get("name")
            if name.isupper():
                name = name.lower()
                new_config[FRECKLET_KEY_NAME]["name"] = name

        return new_config


class MoveEmbeddedTaskKeysProcessor(ConfigProcessor):
    """Moves keys that start with __task__ from the vars to the task sub-dict."""

    def process_current_config(self):

        new_config = self.current_input_config

        vars = new_config.get("vars", None)
        if vars is None:
            vars = {}
            new_config["vars"] = vars

        vars_to_move = {}
        for k in list(vars.keys()):
            if "::" in k:
                vars_to_move[k] = vars.pop(k)
        for k, v in vars_to_move.items():
            add_key_to_dict(new_config, k, v, split_token="::")

        return new_config


class AddRootFreckletProcessor(ConfigProcessor):
    def __init__(self, **init_params):

        self.ting = init_params["ting"]

    def process_current_config(self):

        new_config = self.current_input_config
        return {"root_frecklet": self.ting, "task": new_config}

        # return {"task": new_config}


class CleanupFreckletProcessor(ConfigProcessor):
    def __init__(self, **init_params):

        pass

    def process_current_config(self):

        new_config = self.current_input_config
        new_config["task"].pop("doc", None)
        return new_config


class NodeCounter(object):
    def __init__(self):

        self._current = 0

    def up(self):

        self._current = self._current + 1

    @property
    def current_count(self):

        return self._current


class TaskTreeAttribute(TingAttribute):
    def provides(self):

        return ["task_tree"]

    def requires(self):

        return ["tasklist_detailed"]

    def get_attribute(self, ting, attribute_name=None):

        counter = NodeCounter()

        task_tree = Tree()
        task_tree.create_node(identifier=counter.current_count, tag=ting.id, data=ting)
        self._build_tree(task_tree=task_tree, ting=ting, counter=counter)

        return task_tree

    def _build_tree(self, task_tree, ting, counter):

        parent_id = counter.current_count

        for task in ting.tasklist_detailed:

            task_name = task["task"][FRECKLET_KEY_NAME]["name"]
            task_type = task["task"][FRECKLET_KEY_NAME].get("type", "frecklet")

            if task_type != "frecklet":
                counter.up()
                task_tree.create_node(
                    identifier=counter.current_count,
                    tag="{}:{}".format(task_type, task_name),
                    data=task,
                    parent=parent_id,
                )
                continue

            task_ting = ting._meta_parent_repo.get(task_name)
            if task_ting is None:
                if os.path.exists(ting.id):
                    f_name = os.path.basename(ting.id)
                else:
                    f_name = ting.id
                raise FreckletBuildException(
                    frecklet=ting.id,
                    msg="No child-frecklet named '{}' in context.".format(task_name),
                    solution="""Make sure the frecklet '{}' is contained in one of the repos of this context.

If the frecklet is in the current path, you can add the current path to the context via the '--repo' argument:

    {}frecklecute {}--repo .{} {}{} <arg> ...{}
""".format(
                        task_name,
                        Style.DIM,
                        Style.BRIGHT,
                        Style.RESET_ALL,
                        Style.DIM,
                        f_name,
                        Style.RESET_ALL,
                    ),
                    references={
                        "Context documentation": "https://freckles.io/doc/configuration#context"
                    },
                )

            counter.up()
            task_tree.create_node(
                identifier=counter.current_count,
                tag="{}:{}".format(task_type, task_name),
                data=task,
                parent=parent_id,
            )
            self._build_tree(task_tree=task_tree, ting=task_ting, counter=counter)


class TaskListDetailedAttribute(TingAttribute):

    FRECKLET_FORMAT = {
        CHILD_MARKER_NAME: FRECKLETS_KEY,
        DEFAULT_LEAF_NAME: FRECKLET_KEY_NAME,
        DEFAULT_LEAFKEY_NAME: "name",
        OTHER_KEYS_NAME: [
            "args",
            "doc",
            # "frecklet_meta",
            "meta",
            FRECKLET_KEY_NAME,
            TASK_KEY_NAME,
        ],
        KEY_MOVE_MAP_NAME: {"*": ("vars", "default")},
        "use_context": False,
    }

    def provides(self):

        return ["tasklist_detailed"]

    def requires(self):

        return ["args", "_meta_parent_repo", "_metadata"]

    def get_attribute(self, ting, attribute_name=None):

        log.debug("Processing tasklist for frecklet: {}".format(ting.id))
        chain = [
            ExplodedArgsProcessor(args=ting.args),
            SpecialCaseProcessor(),
            FrklProcessor(**TaskListDetailedAttribute.FRECKLET_FORMAT),
            # DirectParentArgsProcessor(index=ting._meta_parent_repo),
            CommandNameProcessor(),
            TaskTypePrefixProcessor(),
            MoveEmbeddedTaskKeysProcessor(),
            # TaskPathProcessor(index=self.index),
            AddRootFreckletProcessor(ting=ting),
            CleanupFreckletProcessor(),
        ]

        f = Frkl([ting._metadata], chain)
        tasklist_detailed = f.process()

        # import pp
        # pp(tasklist_detailed)

        return tasklist_detailed


def prettyfiy_task(task_detailed, arg_map):

    t = {}
    t[FRECKLET_KEY_NAME] = task_detailed[FRECKLET_KEY_NAME]
    if TASK_KEY_NAME in task_detailed.keys():
        t[TASK_KEY_NAME] = task_detailed[TASK_KEY_NAME]
    if VARS_KEY in task_detailed.keys():
        t[VARS_KEY] = task_detailed[VARS_KEY]

    tks = get_template_keys(t, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
    args = {}

    for tk in tks:
        temp = arg_map[tk]
        # temp = task_detailed[ARGS_KEY][tk]
        args[tk] = special_dict_to_dict(temp)
    t[ARGS_KEY] = args

    return t


class TaskListAttribute(TingAttribute):
    def provides(self):
        return ["tasklist"]

    def requires(self):

        return ["tasklist_detailed"]

    def get_attribute(self, ting, attribute_name=None):

        tasklist = []

        for td_node in ting.tasklist_detailed:
            td = td_node["task"]
            t = prettyfiy_task(td, ting.vars_frecklet)
            tasklist.append(t)

        return tasklist


class TaskListResolvedAttribute(TingAttribute):
    def provides(self):
        return ["tasklist_resolved"]

    def requires(self):

        return ["task_tree"]

    def get_attribute(self, ting, attribute_name=None):

        tasklist = []
        for td_node in ting.task_tree.leaves():
            td = td_node.data["task"]
            t = prettyfiy_task(td, ting.vars_frecklet)
            tasklist.append(t)

        return tasklist
