# -*- coding: utf-8 -*-

import logging
import sys

import click
import click_completion
import click_log
from stevedore import ExtensionManager

from freckles.freckles_base_cli import FrecklesBaseCommand

log = logging.getLogger("freckles")
click_log.basic_config()

# optional shell completion
click_completion.init()

VARS_HELP = "variables to be used for templating, can be overridden by cli options if applicable"
DEFAULTS_HELP = "default variables, can be used instead (or in addition) to user input via command-line parameters"
KEEP_METADATA_HELP = "keep metadata in result directory, mostly useful for debugging"
FRECKLECUTE_EPILOG_TEXT = "frecklecute is free to use in combination with open source software and part of the 'freckles' project, for more information visit: https://docs.freckles.io"


# extensions
# ------------------------------------------------------------------------
def load_plugins():
    """Loading a dictlet finder extension.

    Returns:
      ExtensionManager: the extension manager holding the extensions
    """

    log2 = logging.getLogger("stevedore")
    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(logging.Formatter("freckelize plugin error -> %(message)s"))
    out_hdlr.setLevel(logging.DEBUG)
    log2.addHandler(out_hdlr)
    log2.setLevel(logging.INFO)

    log.debug("Loading freckfreckfreck connector...")

    mgr = ExtensionManager(
        namespace="freckelize.plugins",
        invoke_on_load=False,
        propagate_map_exceptions=True,
    )

    return mgr


class FrecklecuteCommand(FrecklesBaseCommand):
    def __init__(self, *args, **kwargs):
        super(FrecklecuteCommand, self).__init__(**kwargs)

        self.plugins = load_plugins()
        self.commands = {}
        for plugin in self.plugins:
            name = plugin.name
            ep = plugin.entry_point
            command = ep.load()
            self.commands[name] = command

    def list_freckles_commands(self, ctx):

        return sorted(self.commands.keys())

    def get_freckles_command(self, ctx, name):

        ctx.obj["control_dict"] = self.control_dict
        ctx.obj["freckelize_extra_vars"] = self.extra_vars
        command = self.commands[name]

        return command


@click.command(
    name="frecklecute",
    cls=FrecklecuteCommand,
    epilog=FRECKLECUTE_EPILOG_TEXT,
    subcommand_metavar="FRECKLECUTEABLE",
)
# @click.option("--vars", "-v", help="additional vars", multiple=True, type=VarsType())
@click_log.simple_verbosity_option(logging.getLogger(), "--verbosity")
@click.pass_context
def cli(ctx, vars, **kwargs):
    pass


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
