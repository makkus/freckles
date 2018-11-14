from __future__ import absolute_import, division, print_function

import click
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

yaml = YAML(typ="safe")


@click.group(name="repos")
@click.pass_context
def repos(ctx):
    """command-group for repo management tasks"""

    pass
    # context = ctx.obj["context"]
    # control_dict = ctx.obj["control_dict"]
    #
    # context.set_control_vars(control_vars=control_dict)


@repos.command("list", short_help="list all repos")
@click.pass_context
def list_repos(ctx):

    context = ctx.obj["context"]
    repo_manager = context.repo_manager

    repos_per_type = CommentedMap()

    click.echo()

    for r in repo_manager.get_repo_descs():
        c_type = r["content_type"]
        repos_per_type.setdefault(c_type, []).append(r)

    for c_type, repos in repos_per_type.items():

        click.echo("- type: ", nl=False)
        click.secho(c_type, bold=True)
        click.echo()

        for r in repos:
            click.echo("  - {}".format(r["path"]), nl=False)
            alias = r.get("alias", None)
            if alias is not None and alias != r["path"]:
                click.echo(" (from alias: {})".format(alias))
            else:
                click.echo()

        click.echo()
