# -*- coding: utf-8 -*-

import copy
import logging

import m2r
from ruamel.yaml.comments import CommentedSeq

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
from .frecklet_arg_helpers import (
    extract_base_args,
    get_var_item_from_arg_tree,
    DEFAULT_INHERIT_ARGS_LEVEL,
)

log = logging.getLogger("freckles")

DEFAULT_KEY_KEY = "default-key"
FRECKLET_FORMAT = {
    CHILD_MARKER_NAME: FRECKLETS_KEY,
    DEFAULT_LEAF_NAME: FRECKLET_NAME,
    DEFAULT_LEAFKEY_NAME: "name",
    OTHER_KEYS_NAME: ["args", "doc", "frecklet_meta", "meta"],
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


def get_default_schema():

    return copy.deepcopy(DEFAULT_ARG_SCHEMA)


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
            if "." in k:
                vars_to_move[k] = vars.pop(k)
        for k, v in vars_to_move.items():
            add_key_to_dict(new_config, k, v)

        return new_config


class InheritedTaskKeyProcessor(ConfigProcessor):
    """Processor to set properties that are inherited from a parent frecklet."""

    INHERITED_TASK_KEYS = ["__skip__"]

    def __init__(self, **init_params):

        super(InheritedTaskKeyProcessor, self).__init__(**init_params)
        self.parent_metadata = self.init_params.get("parent_metadata", {})

    def process_current_config(self):

        new_config = self.current_input_config

        if self.parent_metadata:

            # task = new_config[FRECKLET_NAME]

            for ik, ikv in (
                self.parent_metadata[FRECKLET_NAME]
                .get("__inherited_keys__", {})
                .items()
            ):
                new_config.setdefault(FRECKLET_NAME, {}).setdefault(
                    "__inherited_keys__", {}
                ).setdefault(ik, []).extend(ikv)

            for key in InheritedTaskKeyProcessor.INHERITED_TASK_KEYS:

                if key not in self.parent_metadata[FRECKLET_NAME].keys():
                    continue

                # if key in task.keys():
                #
                #     log.debug(
                #         "Overwriting parent key '{}': {} -> {}".format(
                #             key, task[key], "XXX"
                #         )
                #     )
                parent_key = self.parent_metadata[FRECKLET_NAME][key]

                new_config.setdefault(FRECKLET_NAME, {}).setdefault(
                    "__inherited_keys__", {}
                ).setdefault(key, []).append(parent_key)

                # get all required arguments for this task
                # and set and associate an arg-list with
                # arg metadata to it
                required_keys = get_template_keys(
                    parent_key, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
                )

                for k in required_keys:
                    temp = get_var_item_from_arg_tree(
                        self.parent_metadata.get("arg_tree", []), k
                    )
                    temp = temp["schema"]
                    if temp is None:
                        temp = get_default_schema()
                    new_config.setdefault("args", {})[k] = temp

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

    def process_current_config(self):

        new_config = self.current_input_config

        # frecklet_level = new_config["meta"]["frecklet_level"]
        if not self.parent_metadata:
            frecklet_level = 0
        else:
            frecklet_level = self.parent_metadata["meta"]["__frecklet_level__"] + 1
        new_config["meta"]["__frecklet_level__"] = frecklet_level
        new_config["meta"]["__frecklet_name__"] = new_config["frecklet"]["name"]

        # the frecklets defined arguments, to pick from if we encounter a template key
        args = new_config.pop("args", None)

        # maybe, just in case, store the meta-info, but not at root level
        frecklet = new_config.pop("frecklet_meta", None)
        # new_config.pop("meta", None)
        new_config[FRECKLET_NAME]["_parent_frecklet"] = frecklet

        # get all template keys from this frecklet
        template_keys = sorted(
            get_template_keys(new_config, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
        )
        # if frecklet_level == 0 and new_config[FRECKLET_NAME].get("__skip__", None) is not None:
        #     new_config["meta"]["__root_skip__"] = new_config[FRECKLET_NAME]["__skip__"]

        # the arg_tree is a tree-like structure that stores each 'root' argument,
        # including all the required child args to construct it, including the ones
        # that the user interacts with
        arg_tree = []

        # now let's go through all the required template keys

        for key in template_keys:

            arg_tree_item = {
                "var": key,
                "__meta__": new_config["meta"],
                FRECKLET_NAME: new_config[FRECKLET_NAME],
            }

            schema = args.get(key, None)
            if schema is None:
                schema = get_default_schema()

            arg_tree_item["schema"] = schema

            if self.parent_metadata:

                # if this frecklet has a parent, we try to use vars that come from there
                parent_value = self.parent_metadata["arg_tree"]
                parent_vars = self.parent_metadata.get("vars", {}).get(key, None)
                parent_frecklet = self.parent_metadata.get("frecklet", None)

                # now we check whether the vars themselves contain template keys
                # if not parent_vars:
                #     values = None
                #     value = None
                # else:
                parent_template_keys = sorted(
                    get_template_keys(
                        {"vars": parent_vars, "frecklet": parent_frecklet},
                        jinja_env=DEFAULT_FRECKLES_JINJA_ENV,
                    )
                )
                value = parent_vars
                if parent_template_keys:
                    values = []
                    for ptk in parent_template_keys:
                        v = get_var_item_from_arg_tree(parent_value, ptk)
                        values.append(v)
                else:
                    values = None

                if values is not None:
                    arg_tree_item["values"] = values

                if value is not None:
                    arg_tree_item["value"] = value

            arg_tree.append(arg_tree_item)

        new_config["arg_tree"] = arg_tree
        task_type = new_config[FRECKLET_NAME].get("type", None)
        if task_type is not None and task_type != "frecklet":
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

        for t in child.process_tasklist(parent=new_config):
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
        task.pop("_parent_frecklet")
        result[FRECKLET_NAME] = task

        vars = frecklet_metadata.get("vars", {})
        result["vars"] = vars

        return result

    def __init__(self, metadata, base_url=None, index=None):

        self.processed_tasklist = None
        super(Frecklet, self).__init__(metadata, base_url=base_url, index=index)

        self.tasklist_cache = None

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

    def get_parameters(self, default_vars=None):

        tl = self.process_tasklist(parent=None)

        # inherit_non_required_args = (
        #     self.metadata["meta"]
        #     .get("cli", {})
        #     .get("inherit_non_required_args", DEFAULT_INHERIT_ARGS_MODE)
        # )
        inherit_args_mode = self.metadata["meta"].get(
            "inherit-child-args", DEFAULT_INHERIT_ARGS_LEVEL
        )

        args = extract_base_args(tl, inherit_args_mode=inherit_args_mode)

        # 'omit' is a special key
        args.pop("omit", None)

        # print(args)
        # print(default_vars)
        parameters = create_parameters(
            copy.deepcopy(args),
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

        args_raw = metadata.get("args", None)

        meta = metadata.get("meta", {})
        if args_raw is None:
            args_raw_temp = list(
                get_template_keys(
                    {FRECKLETS_KEY: tasks, "vars": vars},
                    jinja_env=DEFAULT_FRECKLES_JINJA_ENV,
                )
            )
            args_raw = {}
            for a in args_raw_temp:
                args_raw[a] = {"type": "string"}

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

    def process_tasklist(self, parent=None):

        log.debug("Processing tasklist for frecklet: {}".format(self.frecklet_meta))

        # process_metadata = False
        if parent is None:
            # process_metadata = True
            parent = {}

        # task_format = generate_tasks_format(self.index)
        task_format = FRECKLET_FORMAT
        chain = [
            FrklProcessor(**task_format),
            CommandNameProcessor(),
            TaskTypePrefixProcessor(),
            MoveEmbeddedTaskKeysProcessor(),
            InheritedTaskKeyProcessor(parent_metadata=parent),
            AugmentingTaskProcessor(frecklet_index=self.index, parent_metadata=parent),
        ]

        f = Frkl(self.metadata, chain)

        tasklist = f.process()

        # if process_metadata:
        #     for t in tasklist:
        #         import pp, sys
        #         pp(t)
        #         sys.exit()

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
