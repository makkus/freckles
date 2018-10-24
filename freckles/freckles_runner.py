# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
import os
import uuid
from collections import OrderedDict

import click
import pprintpp
from ruamel.yaml.comments import CommentedMap
from six import string_types

from .frecklet import Frecklet
from frutils import dict_merge, replace_strings_in_obj
from frutils.cnf import CnfPlugin
from frutils.cnf import get_cnf
from frutils.frutils_cli import HostTypePlus, OMIT_VALUE
from .defaults import (
    FRECKLES_RUN_CONTROL_PROFILES,
    FRECKLES_RUN_CONFIG_PROFILES_DIR,
    FRECKLES_CONTROL_CONFIG_SCHEMA,
    DEFAULT_FRECKLES_JINJA_ENV,
)
from .exceptions import FrecklesConfigException
from .frecklecutable import Frecklecutable, needs_elevated_permissions, is_disabled
from .freckles_doc import FrecklesDoc
# from .frecklet_arg_helpers import remove_omit_values
from .output_callback import load_callback_classes, DISPLAY_PROFILES
from .result_callback import FrecklesResultCallback

log = logging.getLogger("freckles")

CALLBACK_CLASSES = load_callback_classes()

def clean_omit_values(d):

    if isinstance(d, (list, tuple)):

        for item in d:
            clean_omit_values(item)

    elif isinstance(d, (dict, OrderedDict, CommentedMap)):

        for key, val in d.items():
            if isinstance(val, (dict, OrderedDict, CommentedMap, list, tuple)):
                clean_omit_values(val)
            elif val == OMIT_VALUE:
                del d[key]


def print_no_run_info(results):

    click.echo("Not running task-list(s). Expanded task-list(s) information:")
    click.echo()
    if len(results.items()) > 1:
        for tl_id, result in results.items():
            click.echo("frecklet: {}".format(result["name"]))
            click.echo()
            click.echo("  tasklist_id: {}".format(tl_id))
            generated_env = result["run_properties"].get("env_dir", None)
            if generated_env is not None:
                click.echo("  generated env dir: {}".format(generated_env))

            tasklist = result["task_list"]
            click.echo("  tasklist:")
            Frecklet.pprint(tasklist, indent=4)
    else:
        result = results[0]
        click.echo("frecklet: {}".format(result["name"]))
        click.echo()
        generated_env = result["run_properties"].get("env_dir", None)
        if generated_env is not None:
            click.echo("  generated env dir: {}".format(generated_env))
        click.echo("  tasklist:")
        tasklist = result["task_list"]
        Frecklet.pprint(tasklist, indent=4)


class ElevatedConfigPlugin(CnfPlugin):
    def __init__(self, **kwars):

        super(ElevatedConfigPlugin, self).__init__(**kwars)

    def handles_keys(self):

        return "elevated"

    def set_value(self, key, value, current_conf):

        return {"elevated": value == "elevated"}


class HostConfigContextPlugin(CnfPlugin):
    def __init__(self, **kwargs):

        super(HostConfigContextPlugin, self).__init__(**kwargs)

    def handles_keys(self):

        return ["host"]

    def set_value(self, key, host, current_conf):
        """Parses host dict and augments it with sensible defaults if necessary.

        Args:
            key (str): 'host' string
            host (str, dict): dictionary of host details
            current_config (dict): copy of current config, for read purposes
        Returns:
            dict: augmented host details, will bo overlayed on top of current cnf
        """

        if not host:
            raise FrecklesConfigException("No value for host specified.")

        if isinstance(host, string_types):
            host_type_plus = HostTypePlus()
            try:
                host = host_type_plus.convert(host, None, None)
            except (Exception) as e:
                log.debug(e)
                msg = e.message
                raise FrecklesConfigException(
                    "Error with host string '{}': {}".format(host, msg)
                )

        hostname = host.get("host", "localhost")
        user = host.get("user", os.getcwd())
        port = host.get("port", None)
        connection_type = host.get("connection_type", None)
        ssh_key = host.get("ssh_key", None)

        vagrant = host.get("is_vagrant", False)
        if vagrant and "passwordless_sudo" not in current_conf.keys():
            passwordless_sudo = True
        else:
            passwordless_sudo = None

        if vagrant:
            host_ip = hostname
            hostname = "vagrant_local"
        else:
            host_ip = None

        if connection_type is None:
            if port is None and hostname in ["localhost", "127.0.0.1"]:
                connection_type = "local"
            elif port is None:
                connection_type = "ssh"
                port = 22
            else:
                connection_type = "ssh"

        overlay = {"user": user, "connection_type": connection_type, "host": hostname}
        if passwordless_sudo is not None:
            overlay["passwordless_sudo"] = passwordless_sudo
        if port is not None:
            overlay["ssh_port"] = port

        if ssh_key is not None:
            overlay["ssh_key"] = ssh_key
        if host_ip is not None:
            overlay["host_ip"] = host_ip
        if user == "root" and "passwordless_sudo" not in overlay.keys():
            overlay["passwordless_sudo"] = True

        return overlay


class FrecklesRunConfig(object):
    """The object holding configuration for a freckles run."""

    def __init__(self, context, config_dict, callback_details=None, **kwargs):

        self.context = context

        self.run_cnf = get_cnf(
            config_profiles=["default"],
            additional_values={},
            available_profiles_dict=FRECKLES_RUN_CONTROL_PROFILES,
            profiles_dir=FRECKLES_RUN_CONFIG_PROFILES_DIR,
            cnf_plugins=[HostConfigContextPlugin(), ElevatedConfigPlugin()],
        )

        self.cnf_interpreter = self.run_cnf.add_cnf_interpreter(
            "freckles_run", FRECKLES_CONTROL_CONFIG_SCHEMA
        )
        for c_name, con in self.context.connectors.items():
            self.run_cnf.add_cnf_interpreter(c_name, con.get_run_config_schema())

        for k, v in config_dict.items():
            self.run_cnf.set_cnf_key(k, v)

        if callback_details is not None:
            self.callback_details = callback_details
        else:
            self.callback_details = self.create_callback_details()

    def get_config_value(self, key):

        return self.run_cnf.get_value("freckles_run", key)

    def set_config_value(self, key, value):

        self.run_cnf.set_cnf_key(key, value)

    def create_callback_details(self):
        # import pp
        # print("CREATING C D")
        # pp(self.run_cnf)
        # print("XXXXXx")
        callback = self.get_config_value("run_callback")
        callback_config = self.get_config_value("run_callback_config")

        no_run = self.run_cnf.get_value("freckles_run", "no_run")
        if no_run is not None:
            callback_config["no_run"] = no_run

        if callback.startswith("freckles:"):
            profile = callback[9:]
            callback = "freckles"
            callback_config["profile"] = profile

        if callback is not None and callback in CALLBACK_CLASSES.names():

            callback_adapter = CALLBACK_CLASSES[callback].plugin(**callback_config)
            callback_name = "freckles_callback"
            callback_backend_name = None

        elif callback is not None and callback in DISPLAY_PROFILES.keys():

            callback_config["profile"] = callback
            callback = "freckles"
            callback_adapter = CALLBACK_CLASSES[callback].plugin(**callback_config)
            callback_name = "freckles_callback"
            callback_backend_name = None

        elif callback is None:
            callback_adapter = CALLBACK_CLASSES["default"].plugin(**callback_config)
            callback_name = "freckles_callback"
            callback_backend_name = None

        elif callback.startswith("backend"):
            callback_adapter = None
            callback_name = "backend"
            if callback.startswith("backend:"):
                callback = callback[8:]
                callback_backend_name = callback
            else:
                callback_backend_name = None
        else:
            callback_adapter = None
            callback_name = None
            callback_backend_name = None

        result = {
            "adapter": callback_adapter,
            "name": callback_name,
            "backend_name": callback_backend_name,
        }

        return result


class TaskDetail(object):
    def __init__(
        self,
        task_name,
        task_type,
        task_parent,
        msg=None,
        ignore_errors=False,
        detail_level=0,
        task_title=None,
        **kwargs
    ):

        self.task_name = task_name
        self.task_type = task_type
        self.task_id = uuid.uuid4()
        self.task_parent = task_parent
        self.msg = msg
        self.ignore_errors = ignore_errors
        self.detail_level = detail_level
        self.task_details = kwargs

        self.task_title = task_title

        self.success = True
        self.skipped = True
        self.changed = False

        self.result_data = {}
        self.debug_data = {}

    def set_success(self, success):

        if not success:
            self.success = False
            if not self.ignore_errors:
                if self.task_parent is not None:
                    self.task_parent.set_success(False)

    def set_skipped(self, skipped):

        if not skipped:
            self.skipped = False
            if self.task_parent is not None:
                self.task_parent.set_skipped(False)

    def set_changed(self, changed):

        if changed:
            self.changed = True
            if self.task_parent is not None:
                self.task_parent.set_changed(True)

    def get_task_title(self):

        if self.task_title is not None:
            return self.task_title

        return self.task_name

    def __repr__(self):

        return pprintpp.pformat(self.__dict__)


class FrecklesRunner(object):
    """Object to start and monitor one or several freckles runs.

    Args:
        context (FrecklesContext): the context
        control_varls (dict): variables to control the execution of this runners runs
        is_sub_task (bool): whether this is used within a freckles run
    """

    def __init__(self, context, is_sub_task=False):

        self.context = context
        self.frecklecutable = None
        self.is_sub_task = is_sub_task

        self.extra_vars = {}

        # self.run_config = FrecklesRunConfig(context, self.control_vars)

    def load_frecklecutable_from_name_or_file(self, frecklecutable):
        """Loads a frecklecutable from a name or file."""

        if not isinstance(frecklecutable, string_types):
            raise Exception(
                "Invalid type for frecklecutable: {}".format(frecklecutable)
            )

        frecklecutable = Frecklecutable.create_from_file_or_name(
            frecklecutable, context=self.context
        )
        self.set_frecklecutable(frecklecutable)

    def set_frecklecutable(self, frecklecutable):
        """Sets the frecklecutable object."""

        self.frecklecutable = frecklecutable

    def add_extra_vars(self, overlay_dict):

        dict_merge(self.extra_vars, overlay_dict, copy_dct=False)

    def get_doc(self):

        return self.frecklecutable.get_doc()

    def generate_click_parameters(self, default_vars=None):

        if self.frecklecutable is None:
            raise FrecklesConfigException("No frecklecutable set yet.")

        parameters = self.frecklecutable.generate_click_parameters(
            default_vars=default_vars
        )
        return parameters

    def postprocess_user_input(self, user_input):

        log.debug("pre-cleaned user input: {}".format(user_input))

        cleaned = {}
        # TODO: handle empty lists and empty strings here
        for k, v in user_input.items():
            if v is not None and (isinstance(v, bool) or v):
                cleaned[k] = v

        if self.extra_vars:
            temp = dict_merge(self.extra_vars, cleaned, copy_dct=True)
        else:
            temp = cleaned

        temp.pop("omit", None)
        log.debug("post-cleaned user input: {}".format(temp))

        return temp

    def describe_tasklist(self):

        tasklists = self.frecklecutable.process_tasklist()

        for tl_id, tl in tasklists.items():
            tasklist = tl["task_list"]
            doc = FrecklesDoc(
                name=self.frecklecutable.name, tasklist=tasklist, context=self.context
            )
            doc.describe()

    def run(self, run_config, user_input=None):

        if not user_input:
            user_input = {}

        if self.frecklecutable is None:
            raise FrecklesConfigException("No frecklecutable set yet.")

        cleaned_user_input = self.postprocess_user_input(user_input)
        processed = self.frecklecutable.postprocess_click_input(cleaned_user_input)

        result = self.execute_tasklist(vars=processed, run_config=run_config)

        # result = self.frecklecutable.execute_tasklist(
        #     vars=processed, context=self.context, run_config=self.run_config, is_sub_task=self.is_sub_task
        # )

        # log.debug("execute tasklist result:\n\n{}".format(pprintpp.pformat(result)))
        return result

    def execute_tasklist(self, run_config, vars=None):

        parent_task = TaskDetail(self.frecklecutable.name, "run", task_parent=None)

        if run_config is None:
            # TODO: use default values
            raise Exception("No run config provided")

        if vars is None:
            vars = {}

        callback_adapter = run_config.callback_details["adapter"]
        if callback_adapter is not None:
            callback_adapter.task_started(parent_task)

        results = OrderedDict()
        result_callback = FrecklesResultCallback()

        try:
            # validated = self.frecklet.get_parameters().validate(vars)

            tasklists = self.frecklecutable.process_tasklist(vars=vars)

            for tasklist_id, tasklist_item in tasklists.items():

                connector = tasklist_item["connector"]
                tasklist = tasklist_item["task_list"]

                replaced = []
                for task in tasklist:
                    task.pop("arg_tree")
                    input = task["input"]
                    input["omit"] = OMIT_VALUE

                    # import pp
                    # print("---------------")
                    # print("TASK")
                    # pp(task)
                    # print("INPUT")
                    # pp(input)

                    r = replace_strings_in_obj(
                        task, input, jinja_env=DEFAULT_FRECKLES_JINJA_ENV
                    )
                    # r = remove_omit_values(r)
                    clean_omit_values(r["vars"])
                    # sys.exit()
                    replaced.append(r)

                connector_obj = self.context.get_connector(connector)

                elevated = run_config.get_config_value("elevated")
                if elevated is None:
                    elevated = needs_elevated_permissions(tasklist)
                    run_config.set_config_value("elevated_tasklist", elevated)

                # callback_adapter.set_tasklist(replaced)
                # callback_adapter.set_run_config(run_config)
                # callback_adapter.set_connector(connector)
                # callback_adapter.set_run_name(self.frecklecutable.name)

                # filter disabled tasks
                final = []
                for t in replaced:
                    # import sys, pp
                    # pp(replaced)
                    # sys.exit()
                    if not is_disabled(t["task"]):
                        final.append(t)
                    else:
                        log.debug("Skipping task: {}".format(t))

                # connector_config = self.context.cnf.get_validated_cnf(connector)
                # log.debug("Connector config: {}".format(connector_config))
                # connector_run_config = run_config.rn_cnf.get_validated_cnf(connector)
                # log.debug("Connector run config: {}".format(connector_run_config))
                if len(tasklists) == 1:
                    tasklist_name = "connector: {}".format(connector)
                else:
                    tasklist_name = "tasklist part {}, connector: {}".format(
                        tasklist_id, connector
                    )
                task_details = TaskDetail(
                    task_name=tasklist_name,
                    task_type="frecklecutable",
                    task_parent=parent_task,
                )

                if callback_adapter is not None:
                    # callback_adapter.execution_started(final, connector, run_config)
                    # else:
                    #     task_details = {
                    #         "name": "{}_{}".format(self.name, tasklist_id)
                    #     }
                    #     callback_adapter.task_started(task_details)

                    callback_adapter.task_started(task_details)

                run_properties = connector_obj.run(
                    final,
                    context_config=self.context.cnf.get_interpreter(connector),
                    run_config=run_config.run_cnf.get_interpreter(connector),
                    result_callback=result_callback,
                    output_callback=callback_adapter,
                    parent_task=task_details,
                )

                if callback_adapter is not None:
                    # callback_adapter.execution_finished()
                    # else:
                    #     callback_adapter.task_finished(True, {})
                    callback_adapter.task_finished(task_details)
                results[tasklist_id] = {
                    "run_properties": run_properties,
                    "task_list": final,
                    "result": result_callback.result,
                    "connector": connector,
                    "name": self.frecklecutable.name,
                }

        finally:
            if callback_adapter is not None:
                callback_adapter.task_finished(parent_task)

        return results
