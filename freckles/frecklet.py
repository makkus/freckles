# -*- coding: utf-8 -*-

import copy
import itertools
import logging
import uuid
from collections import OrderedDict

import m2r
from ruamel.yaml.comments import CommentedSeq, CommentedMap

from frkl import FrklProcessor, Frkl
from frkl.defaults import (
    KEY_MOVE_MAP_NAME,
    CHILD_MARKER_NAME,
    DEFAULT_LEAF_NAME,
    DEFAULT_LEAFKEY_NAME,
    OTHER_KEYS_NAME,
)
from frkl.processors import ConfigProcessor
from frutils import (
    get_template_keys,
    readable_yaml,
    add_key_to_dict,
    replace_string,
    DEFAULT_ENV,
)
from frutils.frutils_cli import create_parameters
from luci.luitem import LuItem
from .defaults import (
    DEFAULT_FRECKLES_JINJA_ENV,
    FRECKLET_NAME,
    FRECKLETS_KEY,
    FRECKLES_CLICK_CEREBUS_ARG_MAP,
)
from .exceptions import FrecklesConfigException
from .frecklet_arg_helpers import extract_base_args, create_vars_for_task_item

log = logging.getLogger("freckles")

DEFAULT_KEY_KEY = "default-key"
FRECKLET_FORMAT = {
    CHILD_MARKER_NAME: FRECKLETS_KEY,
    DEFAULT_LEAF_NAME: FRECKLET_NAME,
    DEFAULT_LEAFKEY_NAME: "name",
    OTHER_KEYS_NAME: ["args", "doc", "frecklet_meta", "meta", "control"],
    KEY_MOVE_MAP_NAME: {"*": ("vars", "default")},
    "use_context": True,
}


def generate_tasks_format(frecklet_index):
    """Utility method to populate the KEY_MOVE_MAP key for the tasks """

    result = copy.deepcopy(FRECKLET_FORMAT)
    for frecklet_name in frecklet_index.get_pkg_names():

        frecklet = frecklet_index.get_pkg(frecklet_name)
        if frecklet is None:
            continue

        if DEFAULT_KEY_KEY in frecklet.frecklet_meta.keys():
            # TODO: check for duplicate keys?
            result[KEY_MOVE_MAP_NAME][frecklet_name] = "vars/{}".format(
                frecklet.frecklet_meta[DEFAULT_KEY_KEY]
            )

    # result["key_move_map"]["skip"] = (FRECKLET_NAME, "skip")

    return result


def fill_defaults(task_item):

    if (
        "name" not in task_item[FRECKLET_NAME].keys()
        and "command" not in task_item[FRECKLET_NAME].keys()
    ):
        raise FrecklesConfigException(
            "Neither 'command' nor 'name' key in task config: {}".format(
                task_item[FRECKLET_NAME]
            )
        )

    if "name" not in task_item[FRECKLET_NAME].keys():
        task_item[FRECKLET_NAME]["name"] = task_item[FRECKLET_NAME]["command"]
    elif "command" not in task_item[FRECKLET_NAME].keys():
        task_item[FRECKLET_NAME]["command"] = task_item[FRECKLET_NAME]["name"]


DEFAULT_ARG_SCHEMA = {"type": "string", "required": True, "doc": {"help": "n/a"}}


# def get_default_schema():
#
#     result = copy.deepcopy(DEFAULT_ARG_SCHEMA)
#     result["__auto_generated__"] = True
#     return result
#
#
# def get_default_arg():
#
#     arg = get_default_schema()
#     arg["doc"] = {"short_help": "n/a", "help": "n/a"}
#
#     return arg


class CommandNameProcessor(ConfigProcessor):
    """Adds potential missing command/name keys."""

    def process_current_config(self):

        new_config = self.current_input_config

        fill_defaults(new_config)
        return new_config


class TaskTypePrefixProcessor(ConfigProcessor):
    """Adds a 'become': True key/value pair if the task name is all uppercase."""

    def process_current_config(self):

        new_config = self.current_input_config

        command_name = new_config[FRECKLET_NAME].get("command", None)
        task_type = new_config[FRECKLET_NAME].get("type", None)

        if "::" in command_name:

            if task_type is not None:
                raise FrecklesConfigException(
                    "Invalid task item '{}': command name contains '::', but type is already specified.".format(
                        new_config
                    )
                )

            task_type, command_name = command_name.split("::", 1)

            new_config[FRECKLET_NAME]["command"] = command_name
            new_config[FRECKLET_NAME]["type"] = task_type

        become = new_config[FRECKLET_NAME].get("become", None)

        if task_type and task_type.isupper() and become is None:
            new_config[FRECKLET_NAME]["become"] = True
            new_config[FRECKLET_NAME]["type"] = task_type.lower()

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


class InheritedTaskKeyProcessor(ConfigProcessor):
    """Processor to set properties that are inherited from a parent frecklet."""

    def __init__(self, **init_params):

        super(InheritedTaskKeyProcessor, self).__init__(**init_params)
        self.parent_metadata = self.init_params.get("parent_metadata", {})

    def process_current_config(self):

        new_config = self.current_input_config

        if self.parent_metadata:

            for ik, ikv in (
                self.parent_metadata.get("control", {})
                .get("inherited_keys", {})
                .items()
            ):
                new_config.setdefault("control", {}).setdefault(
                    "inherited_keys", {}
                ).setdefault(ik, []).extend(ikv)

            if "skip" in self.parent_metadata.get("control", {}).keys():

                parent_key = self.parent_metadata["control"]["skip"]
                if not isinstance(parent_key, (list, tuple, CommentedSeq)):
                    parent_key = [parent_key]
                new_config.setdefault("control", {}).setdefault(
                    "inherited_keys", {}
                ).setdefault("skip", []).extend(parent_key)

        return new_config


FRECKLET_SCHEMA = {
    "doc": {"type": "dict", "schema": {"short_help": {"type": "string"}}},
    "meta": {
        "type": "dict",
        "schema": {
            "tags": {"type": "list", "schema": {"type": "string"}},
            "inherit-child-args": {"type": "integer"},
        },
    },
    "args": {"type": "dict", "schema": {"type": "string"}},
    FRECKLETS_KEY: {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {FRECKLET_NAME: {"type": "dict"}, "vars": {"type": "dict"}},
        },
    },
}

def find_frecklet_in_tree(task_tree, id):

    if id in task_tree: return task_tree[id]

    for k, v in task_tree.items():
        if isinstance(v, (dict, OrderedDict, CommentedMap)):
            item = find_frecklet_in_tree(v, id)
            if item is not None:
                return item


    # raise Exception("Could not find id '{}' in task tree.".format(id))

class AugmentingTaskProcessor(ConfigProcessor):
    """Processor to augment a basic task list.

    This will augment tasks that have a 'name' property which can be found in the task aliases list with the
    content of this task alias entry. Existing task properties won't be overwritten.

    This will also make sure that the task description has a 'meta/task-name' and 'vars' key/value pair.
    """

    def __init__(self, **init_params):

        super(AugmentingTaskProcessor, self).__init__(**init_params)

        self.frecklet_index = self.init_params.get("frecklet_index", None)
        self.parent_metadata = self.init_params.get("parent_metadata", {})
        # self.frecklet_meta = self.init_params.get("frecklet_meta")
        self.task_tree = self.init_params.get("task_tree")

    def process_current_config(self):

        new_config = self.current_input_config

        if not self.parent_metadata:
            frecklet_level = 0
        else:
            frecklet_level = self.parent_metadata["meta"]["__frecklet_level__"] + 1

        task = new_config[FRECKLET_NAME]
        task_type = task.get("type", None)
        if task_type is None:
            task_type = "frecklet"
            task["type"] = task_type
        doc = new_config.get("doc", None)
        if doc is None:
            doc = {}
            new_config["doc"] = doc
        vars = new_config.get("vars", None)
        if vars is None:
            vars = {}
            new_config["vars"] = vars
        control = new_config.get("control", None)
        if control is None:
            control = {}
            new_config["control"] = control
        args = new_config.get("args", None)
        if args is None:
            args = {}
            new_config["args"] = args
        meta = new_config.get("meta", None)
        if meta is None:
            meta = {}
            new_config["meta"] = meta
        # 'meta' is the key where we store anything additional we come up with here
        meta["__frecklet_level__"] = frecklet_level
        frecklet_uuid = str(uuid.uuid4())
        meta["__id__"] = frecklet_uuid

        if not self.parent_metadata:
            new_config["parent"] = None
            parent_id = None
            p_node = self.task_tree
        else:
            new_config["parent"] = self.parent_metadata
            parent_id = self.parent_metadata["meta"]["__id__"]
            p_node = find_frecklet_in_tree(self.task_tree, parent_id)

        var_template_keys = get_template_keys(vars, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
        control_template_keys = get_template_keys(control, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
        task_template_keys = get_template_keys(task, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)

        all_keys = set(itertools.chain(var_template_keys, control_template_keys, task_template_keys))
        meta["__template_keys__"] = {"all": all_keys, "vars": var_template_keys, "control": control_template_keys, "task": task_template_keys}

        if task_type is not None and task_type != "frecklet":
            p_node[frecklet_uuid] = None
            yield new_config
            return

        child_name = new_config[FRECKLET_NAME].get("name", None)
        if child_name is None:
            raise FrecklesConfigException(
                "No 'name' key found in processed task metadata: {}".format(new_config)
            )


        child = self.frecklet_index.get_pkg(child_name)
        if child is None:
            raise Exception(
                "No child frecklet with name '{}' found.".format(child_name)
            )

        p_node[frecklet_uuid] = OrderedDict()

        for t in child.process_tasklist(
            parent=new_config, task_tree=self.task_tree
        ):
            yield t


class Frecklet(LuItem):
    @classmethod
    def load_from_file(cls, url_or_path):
        pass

    @classmethod
    def pprint(cls, frecklet_metadata, indent=0):

        pdicts = []
        if isinstance(frecklet_metadata, (list, tuple, CommentedSeq)):
            for f in frecklet_metadata:
                pdict = cls.pdict(f)
                pdicts.append(pdict)
        else:
            pdicts = cls.pdict(frecklet_metadata)

        formatted = cls.pformat(pdicts, indent=indent)
        print(formatted)

    @classmethod
    def pformat(cls, frecklet_metadata, indent=0):

        result = readable_yaml(frecklet_metadata, safe=False, indent=indent)
        return result

    @classmethod
    def pdict(cls, frecklet_metadata):

        task = frecklet_metadata.get(FRECKLET_NAME, None)
        if task is None:
            raise FrecklesConfigException("No 'task' key in frecklet metadata.")

        result = {}

        task = copy.deepcopy(task)
        task.pop("_task_id")
        task.pop("_task_list_id")
        # task.pop("_parent_frecklet")
        result[FRECKLET_NAME] = task

        vars = frecklet_metadata.get("vars", {})
        result["vars"] = vars

        return result

    def __init__(self, metadata, base_url=None, index=None):

        self.processed_tasklist = None
        super(Frecklet, self).__init__(metadata, base_url=base_url, index=index)

        self.task_list = None
        self.task_tree = None
        self.base_args = None

    def get_urls(self):

        urls = self.frecklet_meta.get("urls")
        result = []
        for u in urls:
            url_raw = u["url"]
            url = replace_string(
                url_raw, {"base_url": self.base_url}, jinja_env=DEFAULT_ENV
            )
            result.append(url)

        return result

    def set_index(self, index):
        self.index = index

    def render_tasklist(self, user_input):
        """Augments a task item with user input.

        If there is no user input for a var, the value will be calculated out of the 'arg_tree', which includes looking at
        parent values and defaults.

        Args:
          tasklist (list): a list of dicts, describing one task each
          user_input (dict): the user input

        """

        if user_input is None:
            user_input = {}

        if not isinstance(user_input, (dict, CommentedMap, OrderedDict)):
            raise Exception("Invalid user input type: {}".format((type(user_input))))

        tasklist = copy.deepcopy(self.get_tasklist())

        for task in tasklist:
            vars = create_vars_for_task_item(task, user_input, self.get_base_args())
            task["input"] = vars

        return tasklist


    def get_base_args(self):

        if self.base_args is None:
            tl = self.get_tasklist()
            base_args = extract_base_args(tl)
            # sort order
            self.base_args = OrderedDict()
            for n in sorted(base_args.keys()):
                self.base_args[n] = base_args[n]

        return self.base_args

    def get_parameters(self, default_vars=None):


        base_args = self.get_base_args()


        param_raw = OrderedDict()
        for k, v in base_args.items():

            arg = v["arg"]
            param_raw[k] = arg

        parameters = create_parameters(
            param_raw,
            default_vars=default_vars,
            type_map=FRECKLES_CLICK_CEREBUS_ARG_MAP,
        )
        return parameters

    def process_metadata(self, metadata):

        tasks = metadata.get(FRECKLETS_KEY, None)
        if tasks is None:
            raise FrecklesConfigException(
                "No tasks specified in frecklet: {}".format(metadata)
            )

        vars = metadata.get("vars", {})

        args_raw = metadata.get("args", {})

        meta = metadata.get("meta", {})
        # if args_raw is None:
        #     args_raw_temp = list(
        #         get_template_keys(
        #             {FRECKLETS_KEY: tasks, "vars": vars},
        #             jinja_env=DEFAULT_FRECKLES_JINJA_ENV,
        #         )
        #     )
        #     args_raw = {}
        #     for a in args_raw_temp:
        #         args_raw[a] = get_default_arg()
        #         args_raw[a]["__is_arg__"] = True

        doc = metadata.get("doc", {})

        frecklet_meta = metadata.get("frecklet_meta", {})

        return {
            FRECKLETS_KEY: tasks,
            "args": args_raw,
            "doc": doc,
            "frecklet_meta": frecklet_meta,
            "vars": vars,
            "meta": meta,
        }

    def get_tasklist(self):

        if self.task_list is None:
            self.task_tree = OrderedDict()
            self.task_list = self.process_tasklist(self.task_tree)
        return self.task_list

    def process_tasklist(self, task_tree, parent=None):

        if task_tree is None:
            raise Exception("'task_tree' can't be 'None'")

        log.debug("Processing tasklist for frecklet: {}".format(self.frecklet_meta))

        # task_format = generate_tasks_format(self.index)
        task_format = FRECKLET_FORMAT
        chain = [
            FrklProcessor(**task_format),
            CommandNameProcessor(),
            TaskTypePrefixProcessor(),
            MoveEmbeddedTaskKeysProcessor(),
            # InheritedTaskKeyProcessor(parent_metadata=parent),
            AugmentingTaskProcessor(
                frecklet_index=self.index,
                parent_metadata=parent,
                # frecklet_meta=self.frecklet_meta,
                task_tree=task_tree
            ),
        ]

        f = Frkl(self.metadata, chain)

        tasklist = f.process()

        return tasklist

    def generate_click_parameters(self, default_vars=None):

        parameters = self.get_parameters(default_vars=default_vars)
        result = parameters.generate_click_parameters(use_defaults=True)
        return result

    def postprocess_click_input(self, user_input):

        processed = self.get_parameters().translate_args(user_input)
        return processed

    # def generate_final_tasklist(self, input):
    #
    #     tl = self.process_tasklist(parent=None)
    #
    #     add_user_input(tl, input)
    #
    #     return tl

    # def validate_vars(self, vars=None):
    #
    #     if vars is None:
    #         vars = {}
    #
    #     validated = self.get_parameters().validate(vars)
    #     return validated

    def get_doc(self):

        return self.doc

    def get_help_string(self, out_format="md"):

        help_string = self.doc.get_help()

        help_format = self.meta.get("help_format", "markdown")
        if help_format == "markdown" and out_format == "rst":

            help_string = m2r.convert(help_string)

        return help_string

    def get_short_help_string(self, list_item_format=False):

        return self.doc.get_short_help(list_item_format=list_item_format)

    def __str__(self):

        return readable_yaml(self.metadata)

    def __repr__(self):

        return readable_yaml(self.metadata)
