from __future__ import absolute_import, division, print_function

import click
from passlib.handlers.sha2_crypt import sha512_crypt
from ruamel.yaml import YAML

yaml = YAML(typ="safe")


@click.group(name="utils")
@click.pass_context
def utils(ctx):
    """command-group for repo management tasks"""

    pass
    # context = ctx.obj["context"]
    # control_dict = ctx.obj["control_dict"]
    #
    # context.set_control_vars(control_vars=control_dict)


@utils.command("mkpasswd", short_help="create a crypted password")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.pass_context
def list_repos(ctx, password):

    print()
    print(sha512_crypt.using(rounds=5000).hash(password))
