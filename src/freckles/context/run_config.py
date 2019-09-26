# -*- coding: utf-8 -*-
import abc

import six
import logging

from freckles.utils.host_utils import parse_target_string
from frutils import dict_merge

log = logging.getLogger("freckles")


@six.add_metaclass(abc.ABCMeta)
class FrecklesRunTarget(object):
    def __init__(self, target_dict=None, target_string=None):

        self._target_string = target_string
        if target_dict is None:
            target_dict = {}
        self._target_dict = target_dict

        self._target_dict_base = None

        self._config = None

        self._protocol = None
        self._user = None
        self._port = None
        self._host = None
        self._connection_type = None
        self._ssh_key = None
        self._become_pass = None
        self._login_pass = None

        self._warning_showed = False

        self._invalidated = True

    def _init_config(self):

        if self._target_string is not None:
            self._target_dict_base = parse_target_string(self._target_string)
        else:
            self._target_dict_base = {}

        self._config = dict_merge(
            self._target_dict_base, self._target_dict, copy_dct=False
        )

        if "host" not in self._config.keys():
            self._config["host"] = "localhost"

        self._protocol = self._config.get("protocol", None)
        self._user = self._config.get("user", None)
        self._port = self._config.get("port", None)
        self._host = self._config.get("host", None)
        self._connection_type = self._config.get("connection_type", None)
        self._ssh_key = self._config.get("ssh_key", None)
        self._become_pass = self._config.get("become_pass", None)
        self._login_pass = self._config.get("login_pass", None)

        if self._connection_type == "lxd":
            if self._user is None:
                self._user = "root"

            if self._user != "root":
                if not self._warning_showed:
                    log.warning(
                        "lxd connection type does not support different user than 'root', ignoring specified user: {}".format(
                            self._user
                        )
                    )
                    self._warning_showed = True
                self._user = "root"

        self._invalidated = False

    @property
    def connection_type(self):

        if self._invalidated:
            self._init_config()

        return self._connection_type

    @connection_type.setter
    def connection_type(self, connection_type):

        self._target_dict["connection_type"] = connection_type
        self._invalidated = True

    @property
    def ssh_key(self):

        if self._invalidated:
            self._init_config()

        return self._ssh_key

    @ssh_key.setter
    def ssh_key(self, ssh_key):

        self._target_dict["ssh_key"] = ssh_key
        self._invalidated = True

    @property
    def become_pass(self):

        if self._invalidated:
            self._init_config()

        return self._become_pass

    @become_pass.setter
    def become_pass(self, become_pass):

        self._target_dict["become_pass"] = become_pass
        self._invalidated = True

    @property
    def login_pass(self):

        if self._invalidated:
            self._init_config()

        return self._login_pass

    @login_pass.setter
    def login_pass(self, login_pass):

        self._target_dict["login_pass"] = login_pass
        self._invalidated = True

    @property
    def protocol(self):

        if self._invalidated:
            self._init_config()
        return self._protocol

    @protocol.setter
    def protocol(self, protocol):

        self._target_dict["protocol"] = protocol
        self._invalidated = True

    @property
    def user(self):

        if self._invalidated:
            self._init_config()

        return self._user

    @user.setter
    def user(self, user):

        self._target_dict["user"] = user
        self._invalidated = True

    @property
    def port(self):

        if self._invalidated:
            self._init_config()

        return self._port

    @port.setter
    def port(self, port):

        self._target_dict["port"] = port
        self._invalidated = True

    @property
    def host(self):

        if self._invalidated:
            self._init_config()

        return self._host

    @host.setter
    def host(self, host):

        self._target_dict["host"] = host
        self._invalidated = True

    @property
    def config(self):

        if self._invalidated:
            self._init_config()

        result = {}
        if self.protocol is not None:
            result["protocol"] = self.protocol
        if self.user is not None:
            result["user"] = self.user
        if self.port is not None:
            result["port"] = self.port
        if self.host is not None:
            result["host"] = self.host
        if self.connection_type is not None:
            result["connection_type"] = self.connection_type
        if self.ssh_key is not None:
            result["ssh_key"] = self.ssh_key
        if self.become_pass is not None:
            result["become_pass"] = self.become_pass
        if self.login_pass is not None:
            result["login_pass"] = self.login_pass

        return result


class FrecklesRunConfig(FrecklesRunTarget):
    def __init__(
        self,
        target_dict=None,
        target_string=None,
        elevated=None,
        no_run=False,
        metadata=None,
    ):

        super(FrecklesRunConfig, self).__init__(
            target_dict=target_dict, target_string=target_string
        )
        self._elevated = elevated
        self._no_run = no_run
        if metadata is None:
            metadata = {}
        self._metadata = metadata

    def _init_config(self):

        super(FrecklesRunConfig, self)._init_config()

    @property
    def elevated(self):

        return self._elevated

    @elevated.setter
    def elevated(self, elevated):

        self._elevated = elevated

    @property
    def no_run(self):

        return self._no_run

    @no_run.setter
    def no_run(self, no_run):

        self._no_run = no_run

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata

    @property
    def config(self):

        temp = super(FrecklesRunConfig, self).config
        temp["no_run"] = self.no_run
        temp["metadata"] = self.metadata
        if self.elevated is not None:
            temp["elevated"] = self.elevated

        return temp
