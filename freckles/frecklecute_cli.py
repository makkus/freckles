# -*- coding: utf-8 -*-

import logging
import os
import sys
from pydoc import locate

import click

import yaml
from frkl.frkl import PLACEHOLDER, Frkl, UrlAbbrevProcessor
from nsbl.nsbl import Nsbl, NsblRunner

from . import __version__ as VERSION

DEFAULT_ABBREVIATIONS = {
    'gh':
        ["https://github.com/", PLACEHOLDER, "/", PLACEHOLDER, ".git"],
    'bb': ["https://bitbucket.org/", PLACEHOLDER, "/", PLACEHOLDER, ".git"]
}

log = logging.getLogger("freckles")

@click.group()
@click.option('--role-repo', '-r', help='path to a local folder containing ansible roles', multiple=True)
# @click.option('--task-desc', '-t', help='path to a local task description yaml file', multiple=True)
# @click.option('--version', help='the version of freckles you are running', is_flag=True)
# @click.option('--stdout-callback', '-c', help='name of or path to callback plugin to be used as default stdout plugin', default="nsbl_internal")
# # @click.option('--static/--dynamic', default=True, help="whether to render a dynamic inventory script using the provided config files instead of a plain ini-type config file and group_vars and host_vars folders, default: static")
#@click.argument("config", nargs=-1)
# def cli(version, config, stdout_callback, role_repo, task_desc):
def cli(role_repo):

    # if version:
        # click.echo(VERSION)
        # sys.exit(0)

    # target = os.path.expanduser("~/.freckles/run")
    # force = True
    # nsbl = Nsbl.create(config, role_repo, task_desc, wrap_into_localhost_env=True)

    # runner = NsblRunner(nsbl)
    # runner.run(target, force, "", stdout_callback)
    pass


class RepoType(click.ParamType):

    name = 'repo'

    def convert(self, value, param, ctx):

        try:
            frkl_obj = Frkl(value, [UrlAbbrevProcessor(init_params={"abbrevs": DEFAULT_ABBREVIATIONS, "add_default_abbrevs": False})])
            return frkl_obj.process()
        except:
            self.fail('%s is not a valid repo url' % value, param, ctx)

FRECKLES_REPO = RepoType()

class FrecklesCommand(click.MultiCommand):

    def __init__(self, current_command, **kwargs):

        super(FrecklesCommand, self).__init__(kwargs)
        self.current_command = current_command

    def list_commands(self, ctx):

        if not self.current_command:
            return []
        else:
            return [self.current_command]

    def get_command(self, ctx, name):

        def callb(**kwargs):
            # replacing the 'pretty' args with the ones the role needs
            for key, value in ctx.obj["key_map"].items():
                temp = kwargs.pop(key)
                kwargs[value] = temp
            print(kwargs)

        key_map = {}
        with open("/freckles/freckles/commands/freckles", 'r') as stream:
            try:
                config_content = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        arg_used = False
        options_list = []
        for opt, opt_details in config_content.get("vars", {}).items():
            opt_type = opt_details.get("type", None)
            if opt_type:
                opt_type_converted = locate(opt_type)
                if not opt_type_converted:
                    raise Exception("No type found for: {}".format(opt_type))
                opt_details['type'] = opt_type_converted

            key = opt_details.pop('key', opt)
            key_map[opt] = key

            is_argument = opt_details.pop('is_argument', False)
            if is_argument:
                if arg_used:
                    raise Exception("Multiple arguments are not supported (yet): {}".format(config_content["vars"]))
                required = opt_details.pop("required", None)
                o = click.Argument(param_decls=[opt], required=required, **opt_details)
            else:
                o = click.Option(param_decls=["--{}".format(opt)], **opt_details)
            options_list.append(o)

        ctx.obj = {}
        ctx.obj["key_map"] = key_map
        command = click.Command(name, params=options_list, help="command help", epilog="epilog", callback=callb)

        #print(command.collect_usage_pieces(ctx))
        return command




# test1 = create_command("test1", test1_opts)
# cli.add_command(test1)
# test2 = create_command("test2", test1_opts)
# cli.add_command(test2)

# we need the current command to dynamically add it to the available ones
current_command = None
for arg in sys.argv[1:]:

    if arg.startswith("-"):
        continue

    current_command = arg
    break

cli = FrecklesCommand(current_command, help="Test")

if __name__ == "__main__":
    cli()
