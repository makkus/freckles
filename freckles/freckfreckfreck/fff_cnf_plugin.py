from __future__ import absolute_import, division, print_function

import os
import sys

import click
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from freckles.defaults import FRECKLES_CONFIG_PROFILES_DIR
from frutils import readable, unsorted_to_sorted_dict
from frutils.frutils_cli import output

yaml = YAML(typ="safe")


@click.group()
@click.pass_context
def cnf(ctx):
    """command-group for config-related tasks"""

    # context = ctx.obj["context"]
    # control_dict = ctx.obj["control_dict"]

    # context.set_control_vars(control_vars=control_dict)


@cnf.command("show-current", short_help="print current configuration")
@click.option(
    "--full", "-f", help="display all keys, including default values", is_flag=True
)
@click.option("--show-interpreters", "-i", help="show interpreted data", is_flag=True)
@click.option(
    "--limit-interpreters",
    "-l",
    help="only display interpreter data for interpreters that contain this string",
)
@click.pass_context
def show_current(ctx, full, show_interpreters, limit_interpreters):
    """Print the current configuration, including documentation (optional).

    This will print the global configuration key/value pairs, as well as the interpreted ones for each added
    configuration interperter.
    """
    output_format = "yaml"

    context = ctx.obj["context"]
    cnf = context.cnf

    config_values = cnf.config_dict
    indent = 0
    if show_interpreters:
        indent = 2
    config_values_string = readable(
        unsorted_to_sorted_dict(config_values), out=output_format, indent=indent
    )

    click.echo()
    if show_interpreters:
        click.secho("Configuration", bold=True)
        click.secho("-------------", bold=True)
        click.echo()

    click.echo(config_values_string)
    click.echo()

    if not show_interpreters:
        sys.exit()

    click.secho("Interpreters", bold=True)
    click.secho("------------", bold=True)
    click.echo()

    for c_name, interpreter in context.get_interpreter_map().items():

        if limit_interpreters and limit_interpreters not in c_name:
            continue

        click.secho("  {}".format(c_name), bold=True)
        click.echo()

        validated = interpreter.get_validated_cnf()

        if not validated:
            click.echo("    No configuration data.")
            click.echo()
            continue

        if not full:
            validated_string = readable(
                unsorted_to_sorted_dict(validated), out=output_format, indent=4
            )
            click.echo(validated_string)
        else:
            details = CommentedMap()

            for k, schema in sorted(interpreter.get_schema().items()):
                v = validated.get(k, None)
                full = interpreter.get_doc_for_key(k)
                short_help = full.get_short_help()
                details[k] = CommentedMap()
                details[k]["desc"] = short_help
                if v is None:
                    v = "n/a"
                details[k]["current value"] = v
                details[k]["default"] = schema.get("default", "n/a")
            for k, v in details.items():
                click.secho("    {}:".format(k), bold=True)
                temp = readable(v, out=output_format, indent=6)
                click.echo(temp.rstrip())
        click.echo()

    # click.echo()


@cnf.command("doc")
@click.argument("key", required=False, nargs=1)
@click.pass_context
def config_doc(ctx, key):

    # output_format = "yaml"
    context = ctx.obj["context"]
    cnf = context.cnf

    click.echo()
    click.secho("Interpreters", bold=True)
    click.echo("-------------")
    click.echo()

    for c_name, interpreter in context.get_interpreter_map().items():

        click.secho("{}".format(c_name), bold=True)
        click.echo()
        schema = interpreter.get_schema()

        if not schema:
            click.echo("  No config schema")

        elif key is None:
            for c_key in sorted(interpreter.get_keys()):
                doc = interpreter.get_doc_for_key(c_key)
                click.secho(" {} ".format(c_key), bold=True, nl=False)
                key_schema = interpreter.get_schema_for_key(c_key)
                value_type = key_schema.get("type", "unknown_type")
                click.echo("({})".format(value_type))
                click.echo("    {}".format(doc.get_short_help()))
        else:
            doc = interpreter.get_doc_for_key(key)
            click.secho(" {} ".format(key), bold=True, nl=False)
            key_schema = interpreter.get_schema_for_key(key)
            value_type = key_schema.get("type", "unknown_type")
            click.echo("({})".format(value_type))
            click.echo()
            click.secho("    desc: ", bold=True, nl=False)
            click.echo("{}".format(doc.get_short_help()))
            click.secho("    default: ", bold=True, nl=False)
            default = key_schema.get("default", "n/a")
            click.echo(default)
            current = cnf.get_value(c_name, key, default="n/a")
            click.secho("    current: ", bold=True, nl=False)
            click.echo(current)

        click.echo()


@cnf.command("copy")
@click.argument("profile_name", nargs=1)
@click.option(
    "--edit",
    "-e",
    is_flag=True,
    default=False,
    help="open new profile in editor after copying",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="overwrite profile if already exists",
)
@click.pass_context
def copy(ctx, profile_name, edit, force):

    cnf = ctx.obj["context"].cnf

    target = os.path.join(
        FRECKLES_CONFIG_PROFILES_DIR, "{}.profile".format(profile_name)
    )
    try:
        cnf.save_current(target, force=force)
    except (Exception) as e:
        click.echo(e)
        sys.exit()

    if edit:
        click.edit(filename=target)


@cnf.command("list-user-profiles")
@click.option(
    "--details", "-d", help="print content of profiles", is_flag=True, default=False
)
@click.pass_context
def list_profiles(ctx, details):
    """lists user profiles

    Lists available user profiles in ~/.freckles/profiles"""

    click.echo()

    if not os.path.exists(FRECKLES_CONFIG_PROFILES_DIR):
        return

    files = os.listdir(FRECKLES_CONFIG_PROFILES_DIR)
    profile_files = [x for x in files if x.endswith(".profile")]

    for p in profile_files:
        p_name = os.path.splitext(p)[0]
        if not details:
            click.echo(p_name)
        else:
            click.secho(p_name, bold=True)
            click.echo()
            pfile = os.path.join(FRECKLES_CONFIG_PROFILES_DIR, p)
            with open(pfile, "r") as f:
                content = yaml.load(f)
            output(content, output_type="yaml", indent=2)


@cnf.command("delete-user-profile")
@click.argument("profile_name", metavar="PROFILE_NAME", nargs=1)
@click.pass_context
def delete_profile(ctx, profile_name):

    file = os.path.join(FRECKLES_CONFIG_PROFILES_DIR, "{}.profile".format(profile_name))

    if os.path.exists(file):
        os.remove(file)


@cnf.command("edit-user-profile")
@click.argument("profile_name", metavar="PROFILE_NAME", nargs=1)
@click.pass_context
def edit_profile(ctx, profile_name):

    path = os.path.join(FRECKLES_CONFIG_PROFILES_DIR, "{}.profile".format(profile_name))
    click.edit(filename=path)
