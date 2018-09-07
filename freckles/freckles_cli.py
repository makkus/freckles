# -*- coding: utf-8 -*-

import logging
import os
import sys

import click
import click_log

from . import __version__ as VERSION
from .freckles_base_cli import FrecklesBaseCommand
from .freckles_runner import FrecklesRunner

log = logging.getLogger("freckles")
click_log.basic_config()

FRECKLES_EPILOG_TEXT = "this application is free to use in combination with open source software and part of the 'freckles' project, for more information visit: https://docs.freckles.io"

DEFAULT_FRECKLECUTABLES_PATH = os.path.join(
    os.path.dirname(__file__), "external", "frecklecutables"
)
DEFAULT_USER_FRECKLECUTABLES_PATH = os.path.join(
    os.path.expanduser("~"), ".freckles", "frecklecutables"
)


class FrecklesCommand(FrecklesBaseCommand):
    def __init__(self, **kwargs):

        super(FrecklesCommand, self).__init__(**kwargs)

    def list_freckles_commands(self, ctx):

        return self.context.get_frecklet_names()

    def get_freckles_command(self, ctx, name):

        runner = FrecklesRunner(self.context, control_vars=self.control_dict)
        runner.load_frecklecutable_from_name_or_file(name)
        runner.add_extra_vars(self.extra_vars)

        @click.command(name=name)
        def command(*args, **kwargs):
            click.echo()
            try:
                results = runner.run(kwargs)
            except (Exception) as e:
                log.debug(e, exc_info=1)
                click.echo()
                click.echo(e)
                sys.exit(1)

            import pprintpp

            if runner.no_run:
                for tl_id, result in results.items():
                    pprintpp.pprint(result["run_properties"])

            for tl_id, result in results.items():
                if result["result"]:
                    print("Result:\n")
                    pprintpp.pprint(result["result"])

        parameters = runner.generate_click_parameters(default_vars=self.extra_vars)
        command.params = parameters
        command.help = runner.get_doc().get_help()
        command.short_help = runner.get_doc().get_short_help()
        # command.epilog = XXX

        return command


@click.command(
    name="freckles",
    cls=FrecklesCommand,
    epilog=FRECKLES_EPILOG_TEXT,
    subcommand_metavar="COMMAND",
)
@click_log.simple_verbosity_option(log, "--verbosity")
@click.pass_context
def cli(ctx, output, config, elevated, vars, host, no_run, version):

    if version:
        click.echo(VERSION)
        sys.exit(0)

    # ctx.obj = {}
    # ctx.obj["profiles"] = profile
    # ctx.obj["extra_vars"] = vars
    #
    # ctx.obj["context"] = FrecklesContext(profile)


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
