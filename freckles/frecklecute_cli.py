# -*- coding: utf-8 -*-
from __future__ import print_function

import logging
import os
import sys

import click
import click_completion
import click_log

from freckles.frecklet_arg_helpers import validate_var
from frutils.doc import Doc
from .exceptions import FrecklesConfigException
from .frecklecutable import Frecklecutable
from .freckles_base_cli import FrecklesBaseCommand, create_context
from .freckles_runner import FrecklesRunner, FrecklesRunConfig, print_no_run_info

log = logging.getLogger("freckles")
click_log.basic_config()

# optional shell completion
click_completion.init()

VARS_HELP = "variables to be used for templating, can be overridden by cli options if applicable"
DEFAULTS_HELP = "default variables, can be used instead (or in addition) to user input via command-line parameters"
KEEP_METADATA_HELP = "keep metadata in result directory, mostly useful for debugging"
FRECKLECUTE_EPILOG_TEXT = "frecklecute is free to use in combination with open source software and part of the 'freckles' project, for more information visit: https://docs.freckles.io"


def help_all(ctx, param, value):

    if ctx.obj is None:
        ctx.obj = {}
    if not value:
        allowed_tags = ["featured-frecklecutable", "__empty__"]
    else:
        allowed_tags = ["__all__"]
    ctx.obj["allowed_frecklet_tags"] = allowed_tags

    if value:
        command = ctx.command

        create_context(ctx, force=True)

        help = command.get_help(ctx)
        click.echo(help)

        sys.exit(0)


def help_with(ctx, param, value):

    if ctx.obj is None:
        ctx.obj = {}

    if not value:
        allowed_tags = ["featured-frecklecutable", "__empty__"]
    else:
        allowed_tags = list(value)

    ctx.obj["allowed_frecklet_tags"] = allowed_tags

    if value:
        command = ctx.command

        create_context(ctx, force=True)

        help = command.get_help(ctx)
        click.echo(help)

        sys.exit(0)


def apropos(ctx, param, value):

    if ctx.obj is None:
        ctx.obj = {}

    if not value:
        apropos = None
    else:
        apropos = list(value)

    if apropos is not None:
        ctx.obj["apropos"] = [a.lower() for a in apropos]
    else:
        ctx.obj["apropos"] = apropos

    if value:
        command = ctx.command

        create_context(ctx, force=True)

        help = command.get_help(ctx)
        click.echo(help)

        sys.exit(0)


class FrecklecuteCommand(FrecklesBaseCommand):
    def __init__(self, *args, **kwargs):
        super(FrecklecuteCommand, self).__init__(**kwargs)

    def list_freckles_commands(self, ctx):
        try:
            return self.context.get_frecklet_names(
                tag_whitelist=ctx.obj.get("allowed_frecklet_tags", None),
                apropos=ctx.obj.get("apropos", None),
            )
        except (Exception) as e:
            log.debug(e, exc_info=1)
            log.warn("Error creating commands: {}".format(e))
            sys.exit(1)

    def get_freckles_command(self, ctx, name):

        try:
            try:
                frecklecutable = Frecklecutable.create_from_file_or_name(
                    name, context=self.context
                )
            except (Exception) as e:
                log.debug(e, exc_info=1)
                log.warn("Error creating command '{}': {}".format(name, e))
                return None
            # runner.init(name)
            # runner.add_extra_vars(self.extra_vars)

            @click.command(name=name)
            def command(*args, **kwargs):

                for arg, details in frecklecutable.frecklet.args.items():

                    if details.get("type", "string") == "password":
                        coerce = "coerce" in details.keys()
                        if details["required"] is True:
                            click.echo(
                                "Please provide a value for arg '{}'.".format(arg)
                            )
                            if details.get("doc", {}).get("short_help", "n/a") != "n/a":
                                msg = details["doc"]["short_help"]
                            else:
                                msg = arg
                            msg = Doc.to_list_item_format(
                                msg, first_char_lowercase=False
                            )
                            pw = click.prompt(msg, type=str, hide_input=True)
                            if coerce:
                                pw = validate_var(
                                    arg, pw, details, password_coerced=False
                                )

                            kwargs[arg] = pw
                        else:
                            if arg in kwargs.keys() and kwargs[arg] is True:
                                click.echo(
                                    "Please provide a value for arg '{}'.".format(arg)
                                )
                                if (
                                    details.get("doc", {}).get("short_help", "n/a")
                                    != "n/a"
                                ):
                                    msg = details["doc"]["short_help"]
                                else:
                                    msg = arg
                                msg = Doc.to_list_item_format(
                                    msg, first_char_lowercase=False
                                )
                                pw = click.prompt(msg, type=str, hide_input=True)
                                if coerce:
                                    pw = validate_var(
                                        arg, pw, details, password_coerced=False
                                    )

                                kwargs[arg] = pw

                            elif arg in kwargs.keys() and not kwargs[arg]:
                                kwargs.pop(arg, None)

                runner = FrecklesRunner(self.context)

                runner.set_frecklecutable(frecklecutable)
                runner.add_extra_vars(self.extra_vars)

                run_vars = {"__freckles_run__": {"pwd": os.path.realpath(os.getcwd())}}

                ssh_pass, sudo_pass = self.ask_ssh_and_sudo_passwords(ctx)
                if sudo_pass is not None:
                    run_vars["__freckles_run__"]["sudo_pass"] = sudo_pass
                if ssh_pass is not None:
                    run_vars["__freckles_run__"]["ssh_pass"] = ssh_pass

                try:
                    run_config = FrecklesRunConfig(self.context, self.control_dict)
                    click.echo()
                    results = runner.run(
                        run_config=run_config, run_vars=run_vars, user_input=kwargs
                    )
                except (Exception) as e:
                    log.debug(e, exc_info=1)
                    click.echo()
                    click.echo("error: {}".format(e))
                    sys.exit(1)

                if run_config.get_config_value("no_run"):
                    print_no_run_info(results)
                    sys.exit()

                # import pprintpp
                #
                # for tl_id, result in results.items():
                #     if result["result"]:
                #         print("Result:\n")
                #         pprintpp.pprint(result["result"])

            try:
                parameters = frecklecutable.generate_click_parameters(
                    default_vars=self.extra_vars
                )
                # parameters = []
            except (Exception) as e:
                log.warn("Error parsing frecklet '{}': {}".format(name, e))
                log.debug(e, exc_info=1)
                return None
            command.params = parameters
            command.help = frecklecutable.get_doc().get_help()
            command.short_help = frecklecutable.get_doc().get_short_help(
                list_item_format=True
            )
            # command.epilog = XXX

            return command
        except (FrecklesConfigException) as e:
            log.debug(e, exc_info=1)
            click.echo(e)
            sys.exit(1)


@click.command(
    name="frecklecute",
    cls=FrecklecuteCommand,
    epilog=FRECKLECUTE_EPILOG_TEXT,
    subcommand_metavar="FRECKLECUTEABLE",
)
# @click.option("--vars", "-v", help="additional vars", multiple=True, type=VarsType())
@click_log.simple_verbosity_option(logging.getLogger(), "--verbosity")
@click.option(
    # "--help-with",
    "--apropos",
    help="Show this message, listing all commands that contain this value in their name or description.",
    metavar="TAG",
    multiple=True,
    is_eager=True,
    callback=apropos,
)
# @click.option(
#     "--help-with",
#     help="Show this message, listing all commands tagged with this value(s).",
#     metavar="TAG",
#     multiple=True,
#     is_eager=True,
#     callback=help_with,
# )
@click.option(
    "--help-all",
    help="Show this message, listing all possible commands.",
    is_flag="true",
    is_eager=True,
    callback=help_all,
)
@click.pass_context
def cli(ctx, vars, **kwargs):

    pass


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
