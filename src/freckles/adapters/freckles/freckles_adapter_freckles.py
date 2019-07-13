# -*- coding: utf-8 -*-
import copy
import logging
import os
import sys

from ruamel.yaml import YAML

from freckles.adapters import FrecklesAdapter
from freckles.defaults import VARS_KEY, FRECKLES_PROPERTIES_ELEVATED_METADATA_KEY
from freckles.exceptions import InvalidFreckletException
from freckles.frecklet.vars import VarsInventory
from freckles.context.run_config import FrecklesRunTarget
from frutils import dict_merge

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

            frecklet_name = vars_dict["frecklet"]
            frecklet = self.context.get_frecklet(frecklet_name=frecklet_name)

            if frecklet is None:
                raise InvalidFreckletException(frecklet_name=frecklet_name)

            # f_type = task["type"]  # always 'frecklecute' for now

            elevated = vars_dict.get(FRECKLES_PROPERTIES_ELEVATED_METADATA_KEY, None)
            if elevated is None:
                elevated = run_elevated
            target = vars_dict.get("target", "localhost")

            run_target = FrecklesRunTarget(target_string=target)
            run_target.login_pass = vars_dict.get("login_pass", None)
            run_target.become_pass = vars_dict.get("become_pass", None)

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
