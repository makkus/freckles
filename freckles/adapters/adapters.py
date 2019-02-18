# -*- coding: utf-8 -*-

import abc
import copy
import logging
import sys

import six
from stevedore import driver
from stevedore.extension import ExtensionManager

from frutils.config.cnf import Cnf

log = logging.getLogger("freckles")

# extensions
# ------------------------------------------------------------------------
def create_adapter(adapter_name, cnf):
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
        invoke_args=(adapter_name, cnf, ),
    )


    return mgr.driver


@six.add_metaclass(abc.ABCMeta)
class FrecklesAdapter(object):
    def __init__(self, adapter_name, cnf):

        self._name = adapter_name
        self._cnf_interpreter = cnf.add_interpreter("adapter_config_{}".format(adapter_name), self.get_config_schema())
        self.resource_folder_map = None

    @property
    def cnf(self):
        return self._cnf_interpreter

    @property
    def name(self):
        return self._name

    @abc.abstractmethod
    def get_config_schema(self):
        pass

    @abc.abstractmethod
    def get_run_config_schema(self):
        pass

    # @abc.abstractmethod
    # def get_supported_task_types(self):
    #     pass

    @abc.abstractmethod
    def get_folders_for_alias(self, alias):

        pass

    @abc.abstractmethod
    def get_supported_resource_types(self):

        pass

    def set_resource_folder_map(self, resource_folders):

        self.resource_folder_map = resource_folders


    @abc.abstractmethod
    def get_supported_task_types(self):
        """Return a list of supported frecklet types to run."""

        pass

    @abc.abstractmethod
    def _run(self, tasklist, run_vars, run_cnf, secure_vars, output_callback, result_callback, parent_task):

        pass

    def run(self, tasklist, run_vars, run_config, secure_vars, output_callback, result_callback, parent_task):

        cnf = Cnf(run_config)

        run_cnf = cnf.add_interpreter("adapter_{}_run_config".format(self.name), schema=self.get_run_config_schema())

        result = self._run(tasklist=tasklist, run_vars=run_vars, run_cnf=run_cnf, secure_vars=secure_vars, output_callback=output_callback, result_callback=result_callback, parent_task=parent_task)

        return result

