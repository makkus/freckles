from __future__ import absolute_import, division, print_function

import sys

from collections import OrderedDict

import click

# from . import __version__ as VERSION
from jinja2 import Environment, Template, FileSystemLoader
from ruamel.yaml.comments import CommentedMap

from frutils import dict_merge, JINJA_DELIMITER_PROFILES

TEMPLATE_METADATA_SCHEMA = {
    "exec": {"type": "boolean"},
    "pip_extra_url": {"type": "string"},
    "prefix_command": {"type": "string"},
    "template_init_function": {"type": "string"},
    "default_profile": {
        "type": "dict",
        "schema": {
            "profile_name": {"type": "string"},
            "profile_env_name": {"type": "string"},
            "conda_python_version": {"type": "string"},
            "conda_dependencies": {"type": "string"},
            "executables_to_link": {"type": "list", "schema": {"type": "string"}},
            "extra_executables": {"type": "list", "schema": {"type": "string"}},
            "debian_dependencies": {"type": "list", "schema": {"type": "string"}},
            "rpm_dependencies": {"type": "list", "schema": {"type": "string"}},
            "pip_dependencies": {"type": "list", "schema": {"type": "string"}},
        },
    },
}

DEFAULT_METADATA = {
    "exec": False,
    "pip_extra_url": "https://pkgs.frkl.io/frkl/dev",
    "prefix_command": None,
    "template_init_function": None,
    "no_exec": False,
    "default_profile": {
        "profile_name": "freckles",
        "profile_env_name": "freckles",
        "conda_python_version": "2.7",
        "conda_dependencies": ["git", "rsync"],
        "executables_to_link": ["frecklecute", "freckelize", "freckfreckfreck", "fff"],
        "extra_executables": ["ansible", "ansible-playbook", "ansible-galaxy", "git"],
        "debian_dependencies": [
            "curl",
            "build-essential",
            "git",
            "python-dev",
            "python-pip",
            "python-virtualenv",
            "virtualenv",
            "libssl-dev",
            "libffi-dev",
            "rsync",
        ],
        "rpm_dependencies": [
            "wget",
            "git",
            "python-pip",
            "python-virtualenv",
            "openssl-devel",
            "gcc",
            "libffi-devel",
            "python-devel",
            "rsync",
        ],
        "pip_dependencies": [
            "freckles>=0.6.0",
            "freckles-connector-nsbl[ansible]==0.1.0",
            "freckles-manager==0.1.0",
        ],
    },
}


TEMPLATE_STRING = """
# =================================================================
# Inserted template string

DEFAULT_PROFILE="{{ metadata['default_profile']['profile_name'] }}"
# conda
DEFAULT_PROFILE_CONDA_PYTHON_VERSION="{{ metadata['default_profile']['conda_python_version'] }}"
DEFAULT_PROFILE_CONDA_DEPENDENCIES="{{ metadata['default_profile']['conda_dependencies'] | join(' ') }}"
DEFAULT_PROFILE_EXECUTABLES_TO_LINK="{{ metadata['default_profile']['executables_to_link'] | join(' ') }}"
DEFAULT_PROFILE_EXTRA_EXECUTABLES="{{ metadata['default_profile']['extra_executables'] | join(' ') }}"
# deb
DEFAULT_PROFILE_DEB_DEPENDENCIES="{{ metadata['default_profile']['debian_dependencies'] | join(' ') }}"
# rpm
DEFAULT_PROFILE_RPM_DEPENDENCIES="{{ metadata['default_profile']['rpm_dependencies'] | join(' ') }}"
# pip requirements
DEFAULT_PROFILE_PIP_DEPENDENCIES="{{ metadata['default_profile']['pip_dependencies'] | join(' ') }}"
DEFAULT_PROFILE_ENV_NAME="{{ metadata['default_profile']['profile_name'] }}"
{% if metadata.get('pip_extra_url', False) %}

export PIP_EXTRA_INDEX_URL="{{ metadata["pip_extra_url"] }}"
{% endif %}{% if metadata.get('template_init_function', False) %}

{{ metadata['template_init_function'] }}
{% endif %}{% if metadata.get('prefix_command', False) %}

{{ metadata['prefix_command'] }}
{% endif %}{% if metadata.get('no_exec', False) == True %}

NO_EXEC=true{% endif %}

# End inserted template string
# =================================================================
"""


def generate_template_string(metadata=None):

    if metadata:
        if not isinstance(metadata, (dict, OrderedDict, CommentedMap)):
            click.echo("Invalid metadata: {}".format(metadata))
            sys.exit(1)

        metadata = dict_merge(DEFAULT_METADATA, metadata, copy_dct=True)
    else:
        metadata = DEFAULT_METADATA

    t = Template(TEMPLATE_STRING)
    rendered = t.render(metadata=metadata)

    return rendered


def generate_inaugurate_script(additions):

    loader = FileSystemLoader(searchpath="./../external/scripts/inaugurate")
    DOC_JINJA_ENV = Environment(
        loader=loader, **JINJA_DELIMITER_PROFILES["documentation"]
    )


@click.group("inaugurate")
@click.pass_context
def inaugurate(ctx):

    pass


@inaugurate.command("template")
@click.argument("metadata", metavar="METADATA", nargs=1, required=False)
@click.pass_context
def template(ctx, metadata=None):
    """Replace the template marker with constumized environment variables in the 'inaugurate' script."""

    rendered = generate_template_string(metadata=metadata)

    print(rendered)
