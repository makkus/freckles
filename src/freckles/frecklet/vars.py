# -*- coding: utf-8 -*-
import abc
import logging
import sys

import click
import six
from colorama import Style
from stevedore import ExtensionManager

from freckles.exceptions import FrecklesVarException
from freckles.frecklet.arguments import FRECKLES_CLICK_CEREBUS_ARG_MAP
from frutils import dict_merge
from ting.ting_attributes import TingAttribute
from ting.ting_cast import TingCast

log = logging.getLogger("freckles")


# extensions
# ------------------------------------------------------------------------
def load_var_adapters():
    """Loading a dictlet finder extension.

    Returns:
      ExtensionManager: the extension manager holding the extensions
    """

    log2 = logging.getLogger("stevedore")
    out_hdlr = logging.StreamHandler(sys.stdout)
    out_hdlr.setFormatter(logging.Formatter("load adapter plugin error -> %(message)s"))
    out_hdlr.setLevel(logging.DEBUG)
    log2.addHandler(out_hdlr)
    log2.setLevel(logging.INFO)

    log.debug("Loading var adapters...")

    mgr = ExtensionManager(
        namespace="freckles.var_adapters",
        invoke_on_load=True,
        propagate_map_exceptions=True,
    )

    result = {}
    for plugin in mgr:
        name = plugin.name
        ep = plugin.entry_point
        adapter = ep.load()
        result[name] = adapter()

    return result


@six.add_metaclass(abc.ABCMeta)
class VarAdapter(object):
    def __init__(self):

        pass

    @abc.abstractmethod
    def retrieve_value(
        self, key_name, arg, frecklet, is_secret=False, profile_names=None
    ):

        pass


class AskVarAdapter(object):
    def __init__(self):

        pass

    def retrieve_value(
        self, key_name, arg, frecklet, is_secret=False, profile_names=None
    ):

        arg_type = arg.type
        click_type = FRECKLES_CLICK_CEREBUS_ARG_MAP.get(arg_type, None)

        if click_type is None:
            msg = "Don't use the 'ask' variable adapter for this argument."

            references = {
                "freckles cli documentation (not yet written)": "https://freckles.io/doc/cli/usage"
            }

            if not is_secret:
                msg = (
                    msg
                    + "\n\nAs this argument is not a secret, you could use the '-v <var> commandline option."
                )
            else:
                msg = (
                    msg
                    + "\n\nThis argument is a secret, maybe you could supply it via the '-v <var>' option in combination with a variable file? Make sure you set secure file permissions for the var file in question ('chmod +x 0700 <var_file>'). Other options to supply passwords are not yet implemented unfortunately, but will be soon."
                )

                references[
                    "freckles security documentation"
                ] = "https://freckles.io/doc/security"

            raise FrecklesVarException(
                frecklet=frecklet,
                var_name=key_name,
                errors={
                    key_name: "the 'ask' variable adapter does not support argument type '{}'".format(
                        arg_type
                    )
                },
                solution=msg,
                references=references,
            )

        short_help = arg.doc.get_short_help(list_item_format=True, use_help=True)
        click.echo(
            "Input needed for '"
            + Style.BRIGHT
            + key_name
            + Style.RESET_ALL
            + "': "
            + Style.DIM
            + short_help
            + Style.RESET_ALL
        )

        arg_default = arg.default

        if arg_default:
            value = click.prompt(
                "  {}".format(key_name),
                hide_input=is_secret,
                type=click_type,
                default=arg_default,
            )
        else:
            value = click.prompt(
                "  {}".format(key_name),
                hide_input=is_secret,
                type=click_type,
                default=arg_default,
            )

        click.echo()

        return value


class VarPathAttribute(TingAttribute):
    def __init__(self, prefix):

        self.prefix = prefix

    def provides(self):

        return ["var_path"]

    def requires(self):

        return ["var", "prefix"]

    def get_attribute(self, ting, attribute_name=None):

        return "{}/{}".format(self.prefix, ting.var)


class VarCast(TingCast):

    VAR_ATTRS = []

    def __init__(self, prefix):

        var_path_attr = VarPathAttribute(prefix)
        super(VarCast, self).__init__(
            "VarTing",
            ting_attributes=[var_path_attr],
            ting_id_attr="var_path",
            mixins=[],
        )


@six.add_metaclass(abc.ABCMeta)
class Inventory(object):
    def __init__(self):
        pass

    @abc.abstractmethod
    def retrieve_value(self, var_name, **task_context):

        pass

    @abc.abstractmethod
    def set_value(self, var_name, new_value, is_secret=False, **task_context):

        pass

    def get_vars(self, hide_secrets=False, **task_context):

        if not hide_secrets:
            return self._get_vars()

        result = {}
        secret_keys = self.secret_keys()
        for k, v in self._get_vars():
            if k in secret_keys:
                v = "__secret__"
            result[k] = v

        return result

    @abc.abstractmethod
    def secret_keys(self, **task_context):

        pass

    @abc.abstractmethod
    def _get_vars(self, **task_context):
        pass


class VarsInventory(Inventory):
    def __init__(self, *vars, secret_keys=None):

        super(VarsInventory, self).__init__()

        self._init_vars_list = vars
        if secret_keys is None:
            secret_keys = []
        self._secrets = secret_keys

        self._vars = {}
        for v in self._init_vars_list:
            dict_merge(self._vars, v, copy_dct=False)

    def retrieve_value(self, var_name, **task_context):

        return self._vars.get(var_name, None)

    def set_value(self, var_name, new_value, is_secret=False, **task_context):

        self._vars[var_name] = new_value
        if is_secret:
            self._secrets.append(var_name)
        if not is_secret and var_name in self._secrets:
            self._secrets.remove(var_name)

    def secret_keys(self, **task_context):

        return self._secrets

    def _get_vars(self, **task_context):

        return self._vars


try:
    VAR_ADAPTERS = load_var_adapters()
except (Exception) as e:
    log.error("Could not load var adapters: {}".format(e))
    VAR_ADAPTERS = {}
