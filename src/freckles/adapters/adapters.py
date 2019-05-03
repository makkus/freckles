# -*- coding: utf-8 -*-

import abc
import copy
import logging
import sys

import six
from stevedore import driver

log = logging.getLogger("freckles")


# extensions
# ------------------------------------------------------------------------
def create_adapter(adapter_name, context):
    """Loading a dictlet finder extension.

    Returns:
      ExtensionManager: the extension manager holding the extensions
    """

    log2 = logging.getLogger("stevedore")
    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(
        logging.Formatter("freckles connector plugin error -> %(message)s")
    )
    out_hdlr.setLevel(logging.INFO)
    log2.addHandler(out_hdlr)
    log2.setLevel(logging.INFO)

    log.debug("Loading freckles adapter...")

    mgr = driver.DriverManager(
        namespace="freckles.adapters",
        name=adapter_name,
        invoke_on_load=True,
        invoke_args=(adapter_name, context),
    )

    return mgr.driver


@six.add_metaclass(abc.ABCMeta)
class FrecklesAdapter(object):
    def __init__(self, adapter_name, context, config_schema, run_config_schema):

        self._name = adapter_name
        self._context = context
        self._context.add_config_interpreter(
            "adapter_config_{}".format(adapter_name), config_schema
        )
        self._context.add_config_interpreter(
            "adapter_run_config_{}".format(adapter_name), run_config_schema
        )

        self.resource_folder_map = None

    def config_value(self, key):

        return self._context.config_value(
            key, interpreter_name="adapter_config_{}".format(self._name)
        )

    def run_config_value(self, key):

        return self._context.config_value(
            key, interpreter_name="adapter_run_config_{}".format(self._name)
        )

    def run_config(self, *overlays):

        return self._context.config(
            "adapter_run_config_{}".format(self._name), *overlays
        )

    def config(self, *overlays):

        return self._context.config("adapter_config_{}".format(self._name), *overlays)

    @property
    def name(self):
        return self._name

    @property
    def context(self):
        return self._context

    # @abc.abstractmethod
    # def get_config_schema(self):
    #     pass
    #
    # @abc.abstractmethod
    # def get_run_config_schema(self):
    #     pass

    # @abc.abstractmethod
    # def get_supported_task_types(self):
    #     pass

    @abc.abstractmethod
    def get_folders_for_alias(self, alias):

        pass

    def get_extra_frecklets(self):

        return {}

    @abc.abstractmethod
    def get_supported_resource_types(self):

        pass

    def set_resource_folder_map(self, resource_folders):

        self.resource_folder_map = resource_folders

    @abc.abstractmethod
    def get_supported_task_types(self):
        """Return a list of supported frecklet types to run."""

        pass

    def get_resources_for_task(self, task):
        """Return a map of paths to all resources that are necessary for this task."""

        return {}

    def prepare_execution_requirements(self, run_config, parent_task):
        """Prepares all external dependencies that are needed for this adapter to successfully run an execution.

        Should throw an exception if it fails.

        Returns:
            int: a version indicator
        """

        pass

    @abc.abstractmethod
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

        final_run_config = self.run_config(run_config)

        tasklist = copy.deepcopy(tasklist)

        result = self.run(
            tasklist=tasklist,
            run_vars=run_vars,
            run_config=final_run_config,
            run_secrets=run_secrets,
            run_env=run_env,
            result_callback=result_callback,
            parent_task=parent_task,
        )

        return result
