from __future__ import absolute_import, division, print_function

import importlib
import os
import sys

import click
from plumbum import local, CommandNotFound
from ruamel.yaml import YAML

# from . import __version__ as VERSION
from freckles.exceptions import FrecklesException

FRKL_INDEX_URL = "https://pkgs.frkl.io"
DEV_INDEX = "frkl/dev"
STAGING_INDEX = "frkl/staging"
STABLE_INDEX = "frkl/stable"
yaml = YAML(typ="safe")

CONNECTOR_PLUGINS = ["nsbl"]


def get_install_method():

    try:
        frecklecute = local["frecklecute"]

        path = str(frecklecute)

        if path == os.path.expanduser(
            "~/.local/share/inaugurate/virtualenvs/freckles/bin/frecklecute"
        ):
            return ("virtualenv", False)
        elif path == os.path.expanduser(
            "~/.local/share/inaugurate/conda/envs/freckles/bin/frecklecute"
        ):
            return ("conda", False)

    except (CommandNotFound) as cnf:
        raise FrecklesException(
            "Can't determine 'freckles' installation. Please update manually: {}".format(
                cnf
            )
        )


def get_pip_path():

    python_path = sys.executable
    pip_path = os.path.join(os.path.dirname(python_path), "pip")

    return pip_path


@click.command("update-freckles")
@click.option(
    "--force-reinstall",
    "-f",
    help="reinstall freckles and it's dependencies, even if it is up to date",
    is_flag=True,
)
@click.argument("path_or_name", metavar="VERSION", nargs=1, required=False)
@click.pass_context
def update_freckles(ctx, path_or_name, force_reinstall):
    """update freckles itself"""

    # old_version = VERSION

    pip = local[get_pip_path()]

    index = DEV_INDEX
    force_reinstall_basic = False

    command = [
        "install",
        "--extra-index-url",
        "{}/{}".format(FRKL_INDEX_URL, index),
        "--upgrade-strategy",
        "only-if-needed",
        "--upgrade",
    ]

    path = []

    if not path_or_name:
        path.append("freckles")

    else:
        force_reinstall_basic = True
        p = os.path.realpath(path_or_name)

        if os.path.exists(p):
            if os.path.isdir(p):
                path.append("-e")
            path.append(p)

    if force_reinstall or force_reinstall_basic:
        command.append("--force-reinstall")

    command.extend(path)

    rc, stdout, stderr = pip.run(command)

    if rc != 0:
        print(stdout)
        print("---------")
        print(stderr)

        sys.exit(1)

    globals()["freckles"] = importlib.import_module("freckles")
