from treelib import Tree
import logging

from freckles.defaults import TASK_KEY_NAME, FRECKLET_KEY_NAME, ARGS_KEY, VARS_KEY, META_KEY, \
    DEFAULT_FRECKLES_JINJA_ENV, FRECKLETS_KEY
from freckles.exceptions import FrecklesConfigException, FreckletException
from frkl import FrklProcessor, Frkl
from frkl.defaults import CHILD_MARKER_NAME, DEFAULT_LEAF_NAME, DEFAULT_LEAFKEY_NAME, OTHER_KEYS_NAME, KEY_MOVE_MAP_NAME
from frkl.processors import ConfigProcessor
from frutils import add_key_to_dict, get_template_keys, special_dict_to_dict
from ting.ting_attributes import ValueAttribute, TingAttribute


log = logging.getLogger("freckles")

class FreckletsAttribute(ValueAttribute):
    def __init__(self):

        super(FreckletsAttribute, self).__init__(
            target_attr_name="frecklets", source_attr_name="_metadata_raw"
        )

    def get_attribute(self, ting, attribute_name=None):

        result = ValueAttribute.get_attribute(
            self, ting, attribute_name=attribute_name
        )
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
                task_tree.create_node(identifier=counter.current_count, tag="{}:{}".format(task_type, task_name), data=task, parent=parent_id)
                continue

            task_ting = ting._meta_parent_repo.get(task_name)
            if task_ting is None:
                raise FreckletException("Can't build frecklet '{}': no child named '{}' available".format(ting.id, task_name), frecklet=ting.id)

            counter.up()
            task_tree.create_node(identifier=counter.current_count, tag="{}:{}".format(task_type, task_name), data=task, parent=parent_id)
            self._build_tree(task_tree=task_tree, ting=task_ting, counter=counter)


class TaskListDetailedAttribute(TingAttribute):

    FRECKLET_FORMAT = {
        CHILD_MARKER_NAME: FRECKLETS_KEY,
        DEFAULT_LEAF_NAME: FRECKLET_KEY_NAME,
        DEFAULT_LEAFKEY_NAME: "name",
        OTHER_KEYS_NAME: [
            "args",
            "doc",
            "frecklet_meta",
            "meta",
            FRECKLET_KEY_NAME,
            TASK_KEY_NAME,
        ],
        KEY_MOVE_MAP_NAME: {"*": ("vars", "default")},
        "use_context": True,
    }

    PROCESS_CHAIN = [
        FrklProcessor(**FRECKLET_FORMAT),
        CommandNameProcessor(),
        TaskTypePrefixProcessor(),
        MoveEmbeddedTaskKeysProcessor(),
        # TaskPathProcessor(index=self.index)
    ]


    def provides(self):

        return ["tasklist_detailed"]

    def requires(self):

        return ["args", "_meta_parent_repo"]

    def get_attribute(self, ting, attribute_name=None):

        log.debug("Processing tasklist for frecklet: {}".format(ting.id))
        chain = TaskListDetailedAttribute.PROCESS_CHAIN + [AddRootFreckletProcessor(ting=ting)]

        f = Frkl(ting._metadata_raw, chain)
        tasklist_detailed = f.process()

        return tasklist_detailed


def prettyfiy_task(task_detailed):

    t = {}
    t[FRECKLET_KEY_NAME] = task_detailed[FRECKLET_KEY_NAME]
    if TASK_KEY_NAME in task_detailed.keys():
        t[TASK_KEY_NAME] = task_detailed[TASK_KEY_NAME]
    if VARS_KEY in task_detailed.keys():
        t[VARS_KEY] = task_detailed[VARS_KEY]

    tks = get_template_keys(t, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
    args = {}
    for tk in tks:
        temp = task_detailed[ARGS_KEY][tk]
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
            t = prettyfiy_task(td)
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
            t = prettyfiy_task(td)
            tasklist.append(t)

        return tasklist
