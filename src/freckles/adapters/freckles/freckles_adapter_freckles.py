# -*- coding: utf-8 -*-
import copy
import logging
import os

from ruamel.yaml import YAML

from freckles.adapters import FrecklesAdapter
from freckles.defaults import VARS_KEY
from freckles.frecklet.vars import VarsInventory
from freckles.utils.host_utils import FrecklesRunTarget
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

        return []

    def get_supported_resource_types(self):

        return []

    def get_supported_task_types(self):

        return ["frecklecutable"]

    def get_extra_frecklets(self):

        extra = {}

        frecklecutable_string = """---
doc:
  short_help: Execute a frecklet indirectly.
  help: |
    Execute a frecklet within another frecklet.

    This is useful, for example, to do some basic installation
    tasks on a freshly installed machine, harden it, add an admin user. After this, 'normal' frecklet tasks can be run.
args:
  frecklet:
    doc:
      short_help: The name of the frecklet.
    type: string
    required: true
    empty: false
    cli:
      param_decls:
        - "--frecklet"
        - "-f"
  elevated:
    doc:
      short_help: "Whether this frecklet needs elevated permissions."
    type: boolean
    required: false
    cli:
      param_decls:
        - "--elevated/--not-elevated"
        - "-e/-ne"
  target:
    doc:
      short_help: "The target string for this run."
    type: string
    required: false
    default: localhost
    cli:
      param_decls:
        - "--target"
        - "-t"
  ssh_pass:
    doc:
      short_help: "The ssh password to connect to the password."
    type: string
    secret: true
    required: false
  become_pass:
    doc:
      short_help: "The password to gain elevated privileges on the password."
    type: string
    secret: true
    required: false
  vars:
    doc:
      short_help: The parameters for this frecklet.
    type: dict
    required: false
    empty: true
frecklets:
 - frecklet:
     name: frecklecute
     type: frecklecutable
     elevated: "{{:: elevated ::}}"
   vars:
     frecklet: "{{:: frecklet ::}}"
     target: "{{:: target ::}}"
     become_pass: "{{:: become_pass ::}}"
     ssh_pass: "{{:: ssh_pass ::}}"
     elevated: "{{:: elevated ::}}"
     vars: "{{:: vars ::}}"
"""

        extra["frecklecute"] = yaml.load(frecklecutable_string)

        return extra

    def prepare_execution_requirements(self, run_config, parent_task):

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

        run_elevated = run_config["elevated"]

        result_list = []

        for task_nr, task in enumerate(tasklist):

            vars_dict = task[VARS_KEY]

            frecklet_name = vars_dict["frecklet"]
            frecklet = self.context.get_frecklet(frecklet_name=frecklet_name)

            # f_type = task["type"]  # always 'frecklecute' for now

            elevated = vars_dict.get("elevated", None)
            if elevated is None:
                elevated = run_elevated
            target = vars_dict.get("target", "localhost")

            run_target = FrecklesRunTarget(context=self.context, target_string=target)
            run_target.ssh_pass = vars_dict.get("ssh_pass", None)
            run_target.become_pass = vars_dict.get("become_pass", None)

            task_run_config = dict_merge(run_config, run_target.config, copy_dct=True)

            fx = frecklet.create_frecklecutable(self.context)

            vars = vars_dict.get(VARS_KEY, {})

            run_env_task = copy.deepcopy(run_env)
            env_dir = os.path.join(run_env_task["env_dir"], "task_{}".format(task_nr))

            result = fx.run(
                inventory=VarsInventory(vars),
                run_config=task_run_config,
                run_vars=run_vars,
                parent_task=parent_task,
                elevated=elevated,
                env_dir=env_dir,
            )

            result_list.append(result)

        return {"subtask_results": result_list}
