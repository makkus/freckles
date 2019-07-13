# -*- coding: utf-8 -*-
import logging
import os
import sys
from distutils.spawn import find_executable

import click
from plumbum import local

from frutils.exceptions import FrklException
from frutils.frutils_cli import check_local_executable

log = logging.getLogger("freckles")


def parse_target_string(target_string):

    if target_string == "vagrant" or target_string.startswith("vagrant:"):
        details = get_vagrant_details(target_string)

    elif "find-pi" in target_string:
        details = get_pi_details(target_string)

    elif "::" in target_string:
        c_type, target_string = target_string.split("::", 1)

        if c_type == "lxd":
            details = get_lxd_details(target_string=target_string)
        elif c_type == "docker":
            details = get_docker_details(target_string=target_string)
        else:
            raise FrklException(
                msg="Can't parse target string.",
                reason="Unknown connection type: {}".format(c_type),
            )

        return details
    else:
        details = get_host_details(target_string)

    return details


def get_lxd_details(target_string):

    if "@" in target_string:
        log.warning(
            "'@' detected in 'lxd' target string. Most likley this won't work, the 'lxd' connection plugin only supports the 'root' user."
        )

    details = {}
    details["connection_type"] = "lxd"
    details["host"] = target_string
    details["user"] = "root"

    return details


def get_docker_details(target_string):

    if "@" in target_string:
        user, host = target_string.split("@", 1)
    else:
        user = "root"
        host = target_string

    details = {}
    details["connection_type"] = "docker"
    details["host"] = host
    details["user"] = user

    return details


def get_vagrant_details(target_string):

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

    env = dict(os.environ)  # make a copy of the environment
    lp_key = "LD_LIBRARY_PATH"  # for Linux and *BSD.
    lp_orig = env.get(lp_key + "_ORIG")  # pyinstaller >= 20160820 has this

    with local.env():

        if lp_orig is not None:
            local.env[lp_key] = lp_orig  # restore the original, unmodified value
        else:
            local.env.pop(lp_key, None)  # last resort: remove the env var

        vagrant = local["vagrant"]
        rc, config, stderr = vagrant.run(["ssh-config", host])

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

        env = dict(os.environ)  # make a copy of the environment
        lp_key = "LD_LIBRARY_PATH"  # for Linux and *BSD.
        lp_orig = env.get(lp_key + "_ORIG")  # pyinstaller >= 20160820 has this

        with local.env():

            if lp_orig is not None:
                local.env[lp_key] = lp_orig  # restore the original, unmodified value
            else:
                local.env.pop(lp_key, None)  # last resort: remove the env var

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
