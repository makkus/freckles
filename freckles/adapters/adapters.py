# -*- coding: utf-8 -*-

import abc
import copy
import logging
import sys

import six
from stevedore.extension import ExtensionManager

log = logging.getLogger("freckles")


# extensions
# ------------------------------------------------------------------------
def load_adapters():
    """Loading a dictlet finder extension.

    Returns:
      ExtensionManager: the extension manager holding the extensions
    """

    log2 = logging.getLogger("stevedore")
    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(
        logging.Formatter("freckles connector plugin error -> %(message)s")
    )
    out_hdlr.setLevel(logging.DEBUG)
    log2.addHandler(out_hdlr)
    log2.setLevel(logging.INFO)

    log.debug("Loading freckles adapter...")

    mgr = ExtensionManager(
        namespace="freckles.adapters",
        invoke_on_load=True,
        propagate_map_exceptions=True,
    )

    for name, ext in mgr.items():
        ext.obj.set_adapter_name(name)

    return mgr


# CONNECTOR_MANAGER = None
#
# def get_connector(connector_name, context):
#
#     global CONNECTOR_MANAGER
#
#     if CONNECTOR_MANAGER is None:
#         CONNECTOR_MANAGER = load_connectors(context)
#
#     return CONNECTOR_MANAGER[connector_name].obj


def get_adapters():

    result = []

    for name, ext in load_adapters().items():
        result.append(ext.obj)

    return result


@six.add_metaclass(abc.ABCMeta)
class FrecklesAdapter(object):
    def __init__(self, adapter_name=None, config=None):

        self.name = adapter_name
        self.config = config
        self.cnf_interpreter = None
        self.run_config_interpreter = None
        self.content_repos = []
        # self.callback = FrecklesCallback()

    # def set_callback(self, callback):
    #
    #     self.callback = callback
    #
    # def get_callback(self):
    #
    #     return self.callback

    def set_adapter_name(self, adapter_name):

        self.name = adapter_name

    # def set_config(self, config):
    #
    #     self.config = config

    @abc.abstractmethod
    def get_frecklet_metadata(self, name):
        """Dynamically generate frecklets from a name for non-indexed frecklets.

        This is not really properly implemented/supported yet.
        """

        pass

    @abc.abstractmethod
    def get_supported_task_types(self):
        """Get a list of supported task types of this adapter."""

        pass

    def get_supported_repo_content_types(self):
        """Returns a list of supported types of urls.

        Typically, each adapter supports different backend-building blocks.
        For example Ansible supports roles, task_lists, and modules.
        This function returns a list of the supported types of this adapter.
        """

        return []

    def get_repo_aliases(self):
        """Return a map of repo aliases/repo urls per content type"""

        return {}

    def set_content_repos(self, content_repos):
        """Sets all content repos this adapter is allowed to use.

        Args:
            content_repos (dict): a dictionary of allowed content repos per content type
        """

        self.content_repos = content_repos
        self.content_repos_updated()

    def content_repos_updated(self):
        """Informs the object that we have new/changed content_repos."""

        pass

    def get_indexes(self):
        """Returns all extra indexes related to this adapter.

        Typically it'll be possible to enable/disable the creation of those indexes in
        the global configuration.

        This will take into account the content repos set in :func:`set_content_repos`.
        """

        return []

    def get_cnf_schema(self):

        return {}

    def get_run_config_schema(self):

        return {}

    def get_config(self):

        return self.cnf_interpreter.get_validated_cnf()

    def get_cnf_value(self, key, default=None):

        return self.cnf_interpreter.get_cnf_value(key, default=default)

    def set_cnf_interpreter(self, cnf_interpreter):

        self.cnf_interpreter = cnf_interpreter

    #
    # def set_run_config_interpreter(self, cnf_interpreter):
    #
    #     self.run_config_interpreter = cnf_interpreter

    def supports_allowed_task_type(
        self, task_type_whitelist=None, task_type_blacklist=None
    ):

        if task_type_whitelist is not None:
            match = False
            for tt in task_type_whitelist:
                if tt in self.get_supported_task_types():
                    match = True
                    break
            return match
        elif task_type_blacklist is not None:
            sup_types = copy.deepcopy(self.get_supported_task_types())
            for tt in task_type_blacklist:
                if tt in sup_types:
                    sup_types.remove(tt)

            if sup_types:
                return True
            else:
                return False

        else:
            return True

    @abc.abstractmethod
    def run(self, tasklist, context_config, run_config):

        pass
