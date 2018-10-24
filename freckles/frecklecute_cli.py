# -*- coding: utf-8 -*-

import logging
import sys

import click
import click_completion
import click_log

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
        allowed_tags = ["frecklecutable", "__empty__"]
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
        allowed_tags = ["frecklecutable", "__empty__"]
    else:
        allowed_tags = ["__all__"]

    ctx.obj["allowed_frecklet_tags"] = allowed_tags

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

        return self.context.get_frecklet_names(
            allowed_tags=ctx.obj["allowed_frecklet_tags"]
        )

    def get_freckles_command(self, ctx, name):

        try:
            try:
                frecklecutable = Frecklecutable.create_from_file_or_name(
                    name, context=self.context
                )
            except (FrecklesConfigException) as e:
                log.warn("Error creating command '{}': {}".format(name, e))
                return None
            # runner.init(name)
            # runner.add_extra_vars(self.extra_vars)

            @click.command(name=name)
            def command(*args, **kwargs):

                runner = FrecklesRunner(self.context)
                runner.set_frecklecutable(frecklecutable)
                runner.add_extra_vars(self.extra_vars)

                try:
                    run_config = FrecklesRunConfig(self.context, self.control_dict)
                    click.echo()
                    results = runner.run(run_config=run_config, user_input=kwargs)
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
            except (Exception) as e:
                log.warn("Error parsing frecklet '{}': {}".format(name, e))
                log.debug(e, exc_info=1)
                return None
            command.params = parameters
            command.help = frecklecutable.get_doc().get_help()
            command.short_help = frecklecutable.get_doc().get_short_help()
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
@click.option(
    "--help-all",
    help="Show this message, listing all possible commands.",
    is_flag="true",
    is_eager=True,
    callback=help_all,
)
@click_log.simple_verbosity_option(logging.getLogger(), "--verbosity")
@click.pass_context
def cli(ctx, vars, **kwargs):
    pass


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
