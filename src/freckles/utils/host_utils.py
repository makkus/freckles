# -*- coding: utf-8 -*-
import logging
import sys
from distutils.spawn import find_executable

import click
from plumbum import local

from frutils import dict_merge
from frutils.frutils_cli import check_local_executable

log = logging.getLogger("freckles")


def parse_target_string(target_string, context):

    if target_string == "vagrant" or target_string.startswith("vagrant:"):
        details = get_vagrant_details(target_string, context)

    elif "find-pi" in target_string:
        details = get_pi_details(target_string)

    else:
        details = get_host_details(target_string)

    return details


def get_vagrant_details(target_string, context):

    if target_string == "vagrant":
        host = "default"
    else:
        host = target_string.split(":")[1]

    if host != "default":
        hosts = list_vagrant_hosts()
        if hosts is None:
            raise Exception("Not in a Vagrant folder, or Vagrant not installed.")

        if host not in hosts.keys():
            raise Exception(
                "No Vagrant host '{}' available. Are you in the right folder?".format(
                    host
                )
            )
        if not hosts[host]:
            raise Exception("Vagrant host '{}' not running.".format(host))

    rc, config, stderr = context.execute_external_command(
        "vagrant", args=["ssh-config", host]
    )
    # config = subprocess.check_output(["vagrant", "ssh-config", host]).decode(
    #     "utf-8"
    # )  # nosec

    host_details = parse_vagrant_ssh_config_string(config)
    host_details["connection_type"] = "ssh"
    host_details["is_vagrant"] = True
    return host_details


def parse_vagrant_ssh_config_string(config_string):

    host = None
    port = None
    user = None
    ssh_key = None

    for line in config_string.split("\n"):

        line = line.strip()

        if line.startswith("HostName "):
            host = line.split()[1]
        elif line.startswith("User "):
            user = line.split()[1]
        elif line.startswith("Port "):
            port = int(line.split()[1])
        elif line.startswith("IdentityFile "):
            ssh_key = line.split()[1]

    result = {}
    if host:
        result["host"] = host
    if user:
        result["user"] = user
    if port:
        result["port"] = port
    if ssh_key:
        result["ssh_key"] = ssh_key

    return result


def list_vagrant_hosts():
    try:
        vagrant_path = find_executable("vagrant")
        vagrant_exe = local[vagrant_path]
        rc, stdout, stderr = vagrant_exe.run(["status", "--machine-readable"])

        status_out = stdout.rstrip()
        # status_out = (
        #     subprocess.check_output(  # nosec
        #         ["vagrant", "status", "--machine-readable"]
        #     )
        #     .decode("utf-8")
        #     .rstrip()
        # )
    except (Exception):
        return None

    hosts = {}
    for line in status_out.split("\n"):
        tokens = line.split(",")
        # timestamp = tokens[0]
        hostname = tokens[1]
        data_type = tokens[2]
        data = tokens[3:]
        if data_type == "state":
            if data[0] == "running":
                hosts[hostname] = True
            else:
                hosts[hostname] = False

    return hosts


def get_pi_details(target_string):

    if target_string == "find-pi":
        host = "default"
        user = "pi"
    else:
        if "@" in target_string:
            user, host = target_string.split("@")
        else:
            click.echo(
                "Can't parse Raspberry pi host-value, '{}', please use '<user>@find-pi".format(
                    target_string
                )
            )
            sys.exit(1)

    log.debug("Raspberry Pi user: '{}', host alias: '{}'".format(user, host))

    nmap_available = check_local_executable("arp")

    if not nmap_available:

        click.echo(
            "\n'arp' is not installed on this machine, can't discover Rasperry Pis on this network. Either install it manually, or use the 'pkg-arp-installed' frecklecutable:\n\nfrecklecute pkg-arp-installed\n"
        )
        sys.exit(1)

    arp = local["arp"]
    awk = local["awk"]

    chain = arp["-n"] | awk["/b8:27:eb/ {print $1}"]

    result = chain()

    addresses = result.strip().split("\n")

    if len(addresses) == 0:
        click.echo(
            "No Raspberry Pi found in this network, you'll have to specify the ip address manually..."
        )
        sys.exit()
    if len(addresses) > 1:
        click.echo("\nMore than one IP addresses for Raspbery pi's found:")
        for a in addresses:
            click.echo("  - {}".format(a))
        click.echo()
        click.echo("Using first one: {}".format(addresses[0]))
    else:
        click.echo(
            "\nFound exactly one IP belonging to a Raspberry Pi: {}".format(
                addresses[0]
            )
        )

    address = addresses[0]

    host_details = {"host": address, "user": user, "connection_type": "ssh"}

    return host_details


def get_host_details(host_string):
    """Parse a string to get user, protocol, host, etc.

    Args:
        host_string (str): the string
    Returns:
        dict: a dict containing the differnt parts
    """

    if not host_string:
        return {}

    username = None
    protocol = None
    host = None
    port = None

    if "://" in host_string:
        protocol, host = host_string.split("://")
    else:
        host = host_string

    if "@" in host:
        username, host = host.split("@")

    if ":" in host:
        host, port = host.split(":")

    result = {}
    if protocol:
        result["protocol"] = protocol

    if username:
        result["user"] = username

    if host:
        result["host"] = host

    if port:
        result["port"] = int(port)

    return result


class FrecklesRunTarget(object):
    def __init__(self, context, target_dict=None, target_string=None):

        self.context = context
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
        self._ssh_pass = None

    def _init_config(self):

        if self._target_string is not None:
            self._target_dict_base = parse_target_string(
                self._target_string, context=self.context
            )
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
        self._ssh_pass = self._config.get("ssh_pass", None)

    @property
    def connection_type(self):

        if self._target_dict_base is None:
            self._init_config()

        return self._connection_type

    @property
    def ssh_key(self):

        if self._target_dict_base is None:
            self._init_config()

        return self._ssh_key

    @property
    def become_pass(self):

        if self._target_dict_base is None:
            self._init_config()

        return self._become_pass

    @become_pass.setter
    def become_pass(self, become_pass):

        if self._target_dict_base is None:
            self._init_config()

        self._become_pass = become_pass
        self._config["become_pass"] = become_pass

    @property
    def ssh_pass(self):

        if self._target_dict_base is None:
            self._init_config()

        return self._ssh_pass

    @ssh_pass.setter
    def ssh_pass(self, ssh_pass):

        if self._target_dict_base is None:
            self._init_config()

        self._ssh_pass = ssh_pass
        self._config["ssh_pass"] = ssh_pass

    @property
    def protocol(self):

        if self._target_dict_base is None:
            self._init_config()
        return self._protocol

    @property
    def user(self):

        if self._target_dict_base is None:
            self._init_config()

        return self._user

    @property
    def port(self):

        if self._target_dict_base is None:
            self._init_config()

        return self._port

    @property
    def host(self):

        if self._target_dict_base is None:
            self._init_config()

        return self._host

    @property
    def config(self):

        if self._target_dict_base is None:
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
        if self.ssh_pass is not None:
            result["ssh_key"] = self.ssh_pass

        return result
