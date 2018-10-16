from __future__ import absolute_import, division, print_function

import click

# from . import __version__ as VERSION

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


@click.command("template")
@click.argument("metadata", metavar="METADATA", nargs=1, required=True)
@click.pass_context
def template(ctx, metadata):
    """Replace the template marker with constumized environment variables in the 'inaugurate' script."""

    metadata = {
        "exec": False,
        "pip_extra_url": "https://pkgs.frkl.io/frkl/dev",
        "prefix_command": None,
        "template_init_function": None,
        "default_profile": {
            "profile_name": "freckles",
            "profile_env_name": "freckles",
            "conda_python_version": "2.7",
            "conda_dependencies": ["git"],
            "executables_to_link": [
                "freckles",
                "frecklecute",
                "freckelize",
                "freckfreckfreck",
            ],
            "extra_executables": [
                "ansible",
                "ansible-playbook",
                "ansible-galaxy",
                "git",
            ],
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
            ],
            "pip_dependencies": [
                "freckles>=0.6.0",
                "freckles-connector-nsbl[ansible]==0.1.0",
            ],
        },
    }

    click.echo(metadata)
