# -*- coding: utf-8 -*-

import abc
import logging
import sys

import click
import click_completion
import click_log
import six
from .exceptions import FrecklesPermissionException, FrecklesConfigException

from frkl import VarsType
from frutils import merge_list_of_dicts
from luci.exceptions import NoSuchDictletException
from . import print_version
from .context import FrecklesContext

log = logging.getLogger("freckles")
click_log.basic_config()

# optional shell completion
click_completion.init()


def create_context(ctx, force=False):

    if ctx.obj is None:
        ctx.obj = {}

    config = ctx.obj.get("config", None)
    repos = ctx.obj.get("repos", None)
    allow_community = ctx.obj.get("allow_community", None)

    if (config is None or repos is None or allow_community is None) and not force:
        return False

    if config is None:
        config = []
        ctx.obj["config"] = config
    if repos is None:
        repos = []
        ctx.obj["repos"] = repos
    if allow_community is None:
        allow_community = False

    log.debug("Creating context...")
    log.debug("  config: {}".format(config))
    log.debug("  repos: {}".format(repos))
    log.debug("  allow_community: {}".format(allow_community))

    repos = list(repos)

    if allow_community:
        repos.append("community")

    try:
        ctx.obj["context"] = FrecklesContext(config, freckles_repos=repos)
    except (FrecklesPermissionException) as e:
        click.echo()
        click.echo(e)
        sys.exit(2)
    except (FrecklesConfigException) as e:
        click.echo()
        click.echo(e)
        sys.exit(2)
    except (Exception) as e:
        click.echo()
        click.echo(e)
        sys.exit(2)
    return True


def set_config(ctx, param, value):

    try:
        if ctx.obj is None:
            ctx.obj = {}
        ctx.obj["config"] = value
        create_context(ctx)
    except (Exception) as e:
        log.debug(e, exc_info=1)
        click.echo("Could not create context: {}".format(e))
        sys.exit(1)


def set_vars(ctx, param, value):

    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj["vars"] = value


def set_repos(ctx, param, value):
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj["repos"] = value
    try:
        create_context(ctx)
    except (NoSuchDictletException) as e:
        click.echo("No such repo: {}".format(e.dictlet))
        sys.exit()


def allow_community_repo(ctx, param, value):
    if ctx.obj is None:
        ctx.obj = {}
    if value is None:
        value = False
    ctx.obj["allow_community"] = value
    try:
        create_context(ctx)
    except (NoSuchDictletException) as e:
        click.echo("No such repo: {}".format(e.dictlet))
        sys.exit()


def get_common_options(print_version_callback=print_version):

    version_option = click.Option(
        param_decls=["--version"],
        help="the version of freckles you are using",
        type=bool,
        is_flag=True,
        is_eager=True,
        expose_value=False,
        callback=print_version_callback,
    )
    output_option = click.Option(
        param_decls=["--output", "-o"], help="the output format to use"
    )
    vars_option = click.Option(
        param_decls=["--vars", "-v"],
        help="additional vars, higher priority than frecklet vars, lower priority than potential user input",
        multiple=True,
        type=VarsType(),
        callback=set_vars,
        is_eager=True,
        expose_value=True,
    )
    community_option = click.Option(
        param_decls=["--community"],
        help="allow resources from the freckles community repo",
        multiple=False,
        callback=allow_community_repo,
        is_eager=True,
        expose_value=True,
        is_flag=True,
    )
    repo_option = click.Option(
        param_decls=["--repo", "-r"],
        help="additional repo(s) to use",
        multiple=True,
        callback=set_repos,
        is_eager=True,
        expose_value=True,
        default=[],
    )
    config_option = click.Option(
        param_decls=["--config", "-c"],
        help="select config profile(s)",
        multiple=True,
        type=str,
        callback=set_config,
        default=["default"],
        is_eager=True,
        expose_value=True,
    )
    host_option = click.Option(
        param_decls=["--host", "-h"],
        help="the host to use",
        multiple=False,
        type=str,
        default="localhost",
    )

    elevated_option = click.Option(
        param_decls=["--elevated", "-e", "elevated"],
        help="indicate that this run needs elevated permissions",
        flag_value="elevated",
        required=False,
    )
    not_elevated_option = click.Option(
        param_decls=["--not-elevated", "-ne", "elevated"],
        help="indicate that this run doesn't need elevated permissions",
        flag_value="not_elevated",
        required=False,
    )
    no_run_option = click.Option(
        param_decls=["--no-run"],
        help="create the run environment (if applicable), but don't run the frecklecutable",
        flag_value=True,
        default=None,
    )

    result = [
        config_option,
        community_option,
        repo_option,
        host_option,
        output_option,
        vars_option,
        elevated_option,
        not_elevated_option,
        no_run_option,
        version_option,
    ]
    return result


@six.add_metaclass(abc.ABCMeta)
class FrecklesBaseCommand(click.MultiCommand):
    """Base class to provide a command-based (similar to e.g. git) cli for frecklecute.
    """

    def __init__(
        self,
        print_version_callback=print_version,
        name=None,
        invoke_without_command=False,
        no_args_is_help=None,
        subcommand_metavar=None,
        chain=False,
        result_callback=None,
        **kwargs
    ):

        super(FrecklesBaseCommand, self).__init__(
            name=None,
            invoke_without_command=False,
            no_args_is_help=None,
            subcommand_metavar=None,
            chain=False,
            result_callback=None,
            **kwargs
        )

        self.print_version_callback = print_version_callback
        self.params[:0] = get_common_options(
            print_version_callback=self.print_version_callback
        )

        self.context = None
        self.config = None
        self.vars = None
        self.repos = None
        self.no_run = None
        self.host = None
        self.output_format = None
        self.elevated = None

        self.extra_vars = None

        self.control_dict = None

    def init_parent_command(self, ctx):

        if self.control_dict is not None:
            return

        self.no_run = ctx.params.get("no_run", None)
        self.host = ctx.params.get("host")
        self.output_format = ctx.params.get("output")
        self.elevated = ctx.params.get("elevated", None)
        if ctx.obj is None:
            create_context(ctx, force=True)

        self.context = ctx.obj["context"]
        self.config = ctx.obj["config"]
        self.repos = ctx.obj["repos"]

        self.extra_vars = merge_list_of_dicts(ctx.obj.get("vars", []))

        self.control_dict = self.get_control_dict()

    def get_control_dict(self):

        control_dict = {}
        if self.no_run is not None:
            control_dict["no_run"] = self.no_run
        if self.host:
            control_dict["host"] = self.host
        if self.output_format:
            control_dict["output"] = self.output_format
        if self.elevated is not None:
            control_dict["elevated"] = self.elevated

        return control_dict

    @abc.abstractmethod
    def list_freckles_commands(self, ctx):

        pass

    @abc.abstractmethod
    def get_freckles_command(self, ctx, command_name):

        pass

    def list_commands(self, ctx):

        self.init_parent_command(ctx)
        return self.list_freckles_commands(ctx)

    def get_command(self, ctx, name):
        try:
            self.init_parent_command(ctx)
            return self.get_freckles_command(ctx, name)
        except (FrecklesPermissionException) as e:
            click.echo()
            click.echo(e)
            sys.exit(2)
