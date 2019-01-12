# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging
import os
import uuid
from collections import OrderedDict

import click
import pprintpp
from six import string_types

from freckles.context import FrecklesContext
from frutils import dict_merge
from frutils.cnf import CnfPlugin
from frutils.cnf import get_cnf
from frutils.frutils_cli import HostTypePlus
from .defaults import (
    FRECKLES_RUN_CONTROL_PROFILES,
    FRECKLES_RUN_CONFIG_PROFILES_DIR,
    FRECKLES_CONTROL_CONFIG_SCHEMA,
)
from .exceptions import FrecklesConfigException
from .frecklecutable import Frecklecutable, needs_elevated_permissions
from .frecklet import Frecklet

# from .frecklet_arg_helpers import remove_omit_values
from .output_callback import load_callback_classes, DISPLAY_PROFILES
from .result_callback import FrecklesResultCallback

log = logging.getLogger("freckles")

CALLBACK_CLASSES = load_callback_classes()


def print_no_run_info(results):

    click.echo("Not running task-list(s). Expanded task-list(s) information:")
    click.echo()
    if len(results.result_dict.items()) > 1:
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
        result = results.result_dict[0]
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

        return ["target"]

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
                if hasattr(e, "message"):
                    msg = e.message
                elif hasattr(e, "msg"):
                    msg = e.msg
                else:
                    msg = "n/a"
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

    def __init__(self, context, config_dict=None, callback_details=None, **kwargs):

        if config_dict is None:
            config_dict = {}
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
        for c_name, con in self.context.adapters.items():
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


class FrecklesRun(object):
    def __init__(self, run_id, result_dict):

        self.run_id = run_id
        self.result_dict = result_dict

        self.adapter = self.result_dict["adapter"]
        self.frecklet_name = self.result_dict["name"]
        self.outcome = self.result_dict["result"]
        self.run_properties = self.result_dict["run_properties"]
        self.task_list = self.result_dict["task_list"]


class FrecklesRuns(object):
    def __init__(self, result_dict):
        self.result_dict = result_dict
        self.run_results = OrderedDict()
        for id, details in result_dict.items():
            frr = FrecklesRun(id, details)
            self.run_results[id] = frr

    def get_run(self, id):
        return self.run_results.get(id, None)


class FrecklesRunner(object):
    """Object to start and monitor one or several freckles runs.

    Args:
        context (FrecklesContext): the context
        control_varls (dict): variables to control the execution of this runners runs
        is_sub_task (bool): whether this is used within a freckles run
    """

    @classmethod
    def from_frecklet(cls, frecklet_name_or_path, context=None):
        """
        Creates a :class:`FrecklesRunner` object from a single frecklet.

        Args:
            frecklet_name_or_path (str): the frecklet name or path
            context (FrecklesContext): the context, if not provided  context will be created with all default values

        Returns:
            FrecklesRunner: the runner
        """

        if context is None:
            context = FrecklesContext.create_context()

        frecklcutable = Frecklecutable.create_from_file_or_name(
            frecklet_name_or_path, context=context
        )
        runner = FrecklesRunner(context)
        runner.set_frecklecutable(frecklcutable)
        return runner

    @classmethod
    def run_frecklet(
        cls,
        frecklet_name_or_path,
        context=None,
        user_input=None,
        run_config=None,
        no_run=False,
    ):
        """
        Creates a temporary :class:`FrecklesRunner` object from a frecklet, and runs the frecklet.

        Args:
            frecklet_name_or_path (str): the frecklet name or path
            context (FrecklesContext): the context, if not provided  context will be created with all default values
            user_input (dict): the user input vars
            run_config: the run config
            no_run: whether to run with the 'no_run' option, convenience flag, overwrites whatever is in 'run_config'

        Returns:
            dict: the result dict
        """

        runner = cls.from_frecklet(
            frecklet_name_or_path=frecklet_name_or_path, context=context
        )
        if run_config is None:
            run_config = {}

        if no_run:
            run_config["no_run"] = no_run

        if user_input is None:
            user_input = {}

        run_cfg = FrecklesRunConfig(context, run_config)

        results = runner.run(user_input=user_input, run_config=run_cfg)

        return results

    def __init__(self, context, is_sub_task=False):

        self.context = context
        self.frecklecutable = None
        self.is_sub_task = is_sub_task

        self.password_store_method = "environment"

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

        # process passwords
        passwords = {}
        password_vars = self.frecklecutable.frecklet.get_parameters().get_all_varnames_of_type(
            "password"
        )

        for varname in password_vars:
            if varname in temp.keys():
                password_wrap = self.process_password_var(varname, temp[varname])
                temp[varname] = password_wrap["alias"]
                passwords[password_wrap["alias"]] = password_wrap

        return (temp, passwords)

    def process_password_var(self, var_name, value):

        result = {"type": self.password_store_method}

        if self.password_store_method == "environment":
            result["password"] = value
            # random_string = "".join(
            #     random.choice(string.ascii_lowercase) for _ in range(14)
            # )
            result["alias"] = "__{}__".format(var_name)
            result["var"] = var_name
        else:
            raise FrecklesConfigException(
                "Password-wrap-method '{}' not supported.".format(
                    self.password_store_method
                )
            )

        return result

    # def describe_tasklist(self):
    #
    #     freckles_doc = FrecklesDoc(self.frecklecutable)
    #
    #     # tasklists = self.frecklecutable.process_tasklist(process_user_input=False)
    #     #
    #     # for tl_id, tl in tasklists.items():
    #     #     tasklist = tl["task_list"]
    #     #     doc = FrecklesDoc(
    #     #         name=self.frecklecutable.name, tasklist=tasklist, context=self.context
    #     #     )
    #     #     doc.describe()

    def run(self, run_config, run_vars=None, user_input=None):

        if run_vars is None:
            run_vars = {}
        if user_input is None:
            user_input = {}

        if self.frecklecutable is None:
            raise FrecklesConfigException("No frecklecutable set yet.")

        cleaned_user_input, passwords = self.postprocess_user_input(user_input)
        processed = self.frecklecutable.postprocess_click_input(cleaned_user_input)
        result = self.execute_tasklist(
            vars=processed,
            run_config=run_config,
            passwords=passwords,
            run_vars=run_vars,
        )

        result_obj = FrecklesRuns(result)
        return result_obj

    def execute_tasklist(self, run_config, vars=None, passwords=None, run_vars=None):

        if run_vars is None:
            run_vars = {}

        if "pwd" not in run_vars.get("__freckles_run__", {}).keys():
            run_vars.setdefault("__freckles_run__", {})["pwd"] = os.path.realpath(
                os.getcwd()
            )

        parent_task = TaskDetail(self.frecklecutable.name, "run", task_parent=None)

        if run_config is None:
            # TODO: use default values
            raise Exception("No run config provided")

        if vars is None:
            vars = {}

        callback_adapter = run_config.callback_details.get("adapter", None)
        if callback_adapter is not None:
            callback_adapter.task_started(parent_task)

        results = OrderedDict()
        result_callback = FrecklesResultCallback()

        try:
            # validated = self.frecklet.get_parameters().validate(vars)

            tasklists = self.frecklecutable.process_tasklist(vars=vars)

            for tasklist_id, tasklist_item in tasklists.items():

                adapter = tasklist_item["adapter"]
                final = tasklist_item["task_list"]

                # final = cleanup_tasklist(tasklist)

                adapter_obj = self.context.get_adapter(adapter)

                elevated = run_config.get_config_value("elevated")
                if elevated is None:
                    elevated = needs_elevated_permissions(final)
                    run_config.set_config_value("elevated_tasklist", elevated)

                if len(tasklists) == 1:
                    tasklist_name = "adapter: {}".format(adapter)
                else:
                    tasklist_name = "tasklist part {}, adapter: {}".format(
                        tasklist_id, adapter
                    )
                task_details = TaskDetail(
                    task_name=tasklist_name,
                    task_type="frecklecutable",
                    task_parent=parent_task,
                )

                if callback_adapter is not None:
                    callback_adapter.task_started(task_details)

                run_properties = adapter_obj.run(
                    final,
                    context_config=self.context.cnf.get_interpreter(adapter),
                    run_config=run_config.run_cnf.get_interpreter(adapter),
                    passwords=passwords,
                    result_callback=result_callback,
                    output_callback=callback_adapter,
                    parent_task=task_details,
                    run_vars=run_vars,
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
                    "adapter": adapter,
                    "name": self.frecklecutable.name,
                }

        finally:
            if callback_adapter is not None:
                callback_adapter.task_finished(parent_task)

        return results
