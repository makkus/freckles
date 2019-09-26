# -*- coding: utf-8 -*-
import copy
import logging
import os
import sys

from ruamel.yaml import YAML
from six import string_types

from freckles.adapters import FrecklesAdapter
from freckles.defaults import (
    VARS_KEY,
    FRECKLES_PROPERTIES_ELEVATED_METADATA_KEY,
    FRECKLET_KEY_NAME,
)
from freckles.exceptions import InvalidFreckletException
from freckles.frecklet.vars import VarsInventory
from freckles.context.run_config import FrecklesRunTarget
from frutils import dict_merge, readable
from frutils.exceptions import FrklException

log = logging.getLogger("freckles")

FRECKLES_ADAPTER_CONFIG_SCHEMA = {}
FRECKLES_ADAPTER_RUN_CONFIG_SCHEMA = {}

yaml = YAML()


class FrecklesAdapterFreckles(FrecklesAdapter):
    def __init__(self, name, context):

        super(FrecklesAdapterFreckles, self).__init__(
            adapter_name=name,
            context=context,
            config_schema=FRECKLES_ADAPTER_CONFIG_SCHEMA,
            run_config_schema=FRECKLES_ADAPTER_RUN_CONFIG_SCHEMA,
        )

    def get_resources_for_task(self, task):

        pass

    def get_folders_for_alias(self, alias):

        if alias != "default":
            return []

        if not hasattr(sys, "frozen"):
            frecklet_dir = os.path.realpath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "external",
                    "freckles_frecklets",
                )
            )
        else:
            frecklet_dir = os.path.join(
                sys._MEIPASS, "freckles", "external", "freckles_frecklets"
            )

        return ["frecklet::{}".format(frecklet_dir)]

    def get_supported_resource_types(self):

        return []

    def get_supported_task_types(self):

        return ["frecklecutable"]

    def get_extra_frecklets(self):

        return {}

    def prepare_execution_requirements(self, run_config, task_list, parent_task):

        pass

    def _run(
        self,
        tasklist,
        run_vars,
        run_config,
        run_secrets,
        run_env,
        result_callback,
        parent_task,
    ):

        tl = copy.deepcopy(tasklist)

        return self.run(
            tasklist=tl,
            run_vars=run_vars,
            run_config=run_config,
            run_secrets=run_secrets,
            run_env=run_env,
            result_callback=result_callback,
            parent_task=parent_task,
        )

    def run(
        self,
        tasklist,
        run_vars,
        run_config,
        run_secrets,
        run_env,
        result_callback,
        parent_task,
    ):

        # run_elevated = run_config["elevated"]
        # we are not using the forwarded elevated here, better to let freckles figure it out
        run_elevated = None

        current_result = None

        for task_nr, task in enumerate(tasklist):

            vars_dict = task[VARS_KEY]

            frecklet_dict = task[FRECKLET_KEY_NAME]
            frecklet_name = frecklet_dict.get("name", None)

            if frecklet_name is None:
                raise FrklException(
                    "Can't parse task for frecklet type 'frecklecutable'.".format(task),
                    reason="Missing 'frecklet.name' key: \n\n{}".format(
                        readable(task, out="yaml", indent=2)
                    ),
                    solution="Provide a valid frecklet name for the 'frecklet.name' key.",
                )

            frecklet = self.context.get_frecklet(frecklet_name=frecklet_name)

            if frecklet is None:
                raise InvalidFreckletException(frecklet_name=frecklet_name)

            # f_type = task["type"]  # always 'frecklecute' for now

            elevated = vars_dict.get(FRECKLES_PROPERTIES_ELEVATED_METADATA_KEY, None)
            if elevated is None:
                elevated = run_elevated
            target = vars_dict.get("target", "localhost")

            if isinstance(target, string_types):
                run_target = FrecklesRunTarget(target_string=target)
            else:
                run_target = FrecklesRunTarget(target_dict=target)

            login_pass = vars_dict.get("login_pass", None)
            become_pass = vars_dict.get("become_pass", None)
            if (
                run_target.login_pass
                and login_pass
                and run_target.login_pass != login_pass
            ):
                raise FrklException(
                    msg="Can't assemble run configuration.",
                    reason="Two different login passwords provided.",
                    solution="Either use the root-level 'login_pass' key, or 'target.login_pass', but not both.",
                )
            if (
                run_target.become_pass
                and become_pass
                and run_target.become_pass != become_pass
            ):
                raise FrklException(
                    msg="Can't assemble run configuration.",
                    reason="Two different become passwords provided.",
                    solution="Either use the root-level 'become_pass' key, or 'target.become_pass', but not both.",
                )
            if not run_target.login_pass:
                run_target.login_pass = login_pass
            if not run_target.become_pass:
                run_target.become_pass = become_pass

            task_run_config = dict_merge(run_config, run_target.config, copy_dct=True)
            fx = frecklet.create_frecklecutable(self.context)

            vars = vars_dict.get(VARS_KEY, {})

            run_env_task = copy.deepcopy(run_env)
            env_dir = os.path.join(run_env_task["env_dir"], "task_{}".format(task_nr))

            current_result = fx.run_frecklecutable(
                inventory=VarsInventory(vars),
                run_config=task_run_config,
                run_vars=run_vars,
                parent_task=parent_task,
                elevated=elevated,
                env_dir=env_dir,
                result_callback=result_callback,
            )

        return current_result
