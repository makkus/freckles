# -*- coding: utf-8 -*-

import copy
import logging
from collections import OrderedDict

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
from .exceptions import FrecklesConfigException, FreckletException
from .frecklet_arg_helpers import extract_base_args

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


def get_default_schema():

    result = copy.deepcopy(DEFAULT_ARG_SCHEMA)
    result["__auto_generated__"] = True
    return result


def get_default_arg():

    arg = get_default_schema()
    arg["doc"] = {"short_help": "n/a", "help": "n/a"}

    return arg


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
        self.frecklet_meta = self.init_params.get("frecklet_meta")
        self.tree_properties = self.init_params.get("tree_properties", {})

    # def add_argument_backlink(self, new_config, key):
    #     inherit_uuid = None
    #     if self.parent_metadata:
    #         parent_arg = (
    #             self.parent_metadata["arg_tree"]
    #             .get(key, {})
    #             .get("arg", {})
    #             .get("uuid", None)
    #         )
    #         if parent_arg is not None:
    #             inherit_uuid = parent_arg
    #
    #     if inherit_uuid is None:
    #         inherit_uuid = str(uuid.uuid4())
    #
    #     new_config["vars"][key] = "{{{{:: {} ::}}}}".format(key)
    #     arg = {"uuid": inherit_uuid}
    #     new_config.setdefault("args", {})[key] = arg
    #     self.tree_properties.setdefault("inherit_vars", {}).setdefault(
    #         inherit_uuid, {}
    #     ).setdefault("backlinks", []).append({key: arg})
    #     return inherit_uuid

    def process_current_config(self):

        new_config = self.current_input_config

        if not self.parent_metadata:
            frecklet_level = 0
        else:
            frecklet_level = self.parent_metadata["meta"]["__frecklet_level__"] + 1

        frecklet_name = self.frecklet_meta.get("name", "n/a")

        # 'meta' is the key where we store anything additional we come up with here
        new_config["meta"]["__frecklet_level__"] = frecklet_level
        new_config["meta"]["__frecklet_name__"] = frecklet_name

        # the frecklets defined arguments, to pick from if we encounter a template key
        args = new_config.get("args", None)

        # maybe, just in case, store the meta-info, but not at root level
        # frecklet = new_config.pop("frecklet_meta", None)

        # the arg_tree is a tree-like structure that stores each 'root' argument,
        # including all the required child args to construct it, including the ones
        # that the user interacts with
        arg_tree = {}

        # get all template keys from this frecklet
        control_dict = copy.deepcopy(new_config.get("control", {}))
        control_dict_template_keys = get_template_keys(control_dict, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)

        # inherit_map = {}
        # for k, v in new_config.get("vars", {}).items():
        #     if v == "__inherit__":
        #         i_uuid = self.add_argument_backlink(new_config, k)
        #         inherit_map[k] = i_uuid


        inherited_control = control_dict.pop("inherited_keys", {})
        template_keys = sorted(
            get_template_keys(
                {
                    "vars": new_config["vars"],
                    FRECKLET_NAME: new_config[FRECKLET_NAME],
                    "control": control_dict,
                },
                jinja_env=DEFAULT_FRECKLES_JINJA_ENV,
            )
            # get_template_keys(new_config,
            #              jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
        )
        new_config["meta"]["__template_keys__"] = template_keys

        # now let's go through all the required template keys
        for key in template_keys:
            meta = new_config["meta"]
            arg_tree_item = {
                "__meta__": meta
            }

            arg = args.get(key, None)
            if arg is None:
                arg = get_default_arg()

            arg["__is_arg__"] = True
            arg_tree_item["arg"] = arg

            if self.parent_metadata:

                # if this frecklet has a parent, we try to use vars that come from there
                parent_var = self.parent_metadata.get("vars", {}).get(key, None)
                parent_name = self.parent_metadata["meta"]["__frecklet_name__"]
                parent_arg_tree = self.parent_metadata["arg_tree"]

                parent_vars = {}

                if parent_var is not None:

                    tpks = get_template_keys(
                        parent_var, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
                    )
                    for tpk in tpks:
                        if tpk in parent_arg_tree.keys():
                            parent_vars[tpk] = parent_arg_tree[tpk]


                    arg_tree_item["parent"] = {
                        "var_name": parent_var,
                        "vars": parent_vars,
                    }

                else:

                        # we don't look for anything apart from the default
                        default = arg.get("default", None)
                        if arg.get("required", True):

                            if default is None:

                                    raise FreckletException(
                                        "Argument '{}' for frecklet '{}' is required (and no 'default' set), but not specified in parent: '{}'.".format(
                                            key, frecklet_name, parent_name
                                        ),
                                        new_config,
                                    )
                            else:
                                arg_tree_item["value"] = default

                        else:
                            if default is not None:
                                arg_tree_item["value"] = default
                            else:
                                # non-required argument, not specified in parent, means we will remove the var from the child when it comes to replacing the strings
                                pass

            else:
                # means we're at level 0
                pass

            if arg_tree_item is not None:
                arg_tree[key] = arg_tree_item

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

        for t in child.process_tasklist(
            parent=new_config, tree_properties=self.tree_properties
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

        args = extract_base_args(tl)

        # sort order
        sorted_args = OrderedDict()
        for n in sorted(args.keys()):
            sorted_args[n] = args[n]

        parameters = create_parameters(
            copy.deepcopy(sorted_args),
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
                args_raw[a] = get_default_arg()
                args_raw[a]["__is_arg__"] = True

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

    def process_tasklist(self, parent=None, tree_properties=None):

        log.debug("Processing tasklist for frecklet: {}".format(self.frecklet_meta))

        # process_metadata = False
        initial_tree_properties = None
        if parent is None:
            # process_metadata = True

            parent = {}
            initial_tree_properties = {}
            tree_properties = initial_tree_properties

        # task_format = generate_tasks_format(self.index)
        task_format = FRECKLET_FORMAT
        chain = [
            FrklProcessor(**task_format),
            CommandNameProcessor(),
            TaskTypePrefixProcessor(),
            MoveEmbeddedTaskKeysProcessor(),
            InheritedTaskKeyProcessor(parent_metadata=parent),
            AugmentingTaskProcessor(
                frecklet_index=self.index,
                parent_metadata=parent,
                tree_properties=tree_properties,
                frecklet_meta=self.frecklet_meta,
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
