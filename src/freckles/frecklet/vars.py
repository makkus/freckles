# -*- coding: utf-8 -*-
import abc
import logging

import six

from frutils import dict_merge
from ting.ting_attributes import TingAttribute
from ting.ting_cast import TingCast

log = logging.getLogger("freckles")


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

    def retrive_arg_schema(self, var_name, **task_context):

        if not self.args:
            return None

        return self.args.get(var_name, None)

    def get_secret_args(self):

        if self.args is None:
            return None

        result = []

        for arg_name, arg in self.args.items():
            if arg.secret:
                result.append(arg)

        return result

    @abc.abstractmethod
    def get_all(self, hide_secret=False):
        pass


class VarsInventory(Inventory):
    def __init__(self, *vars):

        super(VarsInventory, self).__init__()

        self.vars_list = vars
        self._secrets = []

        self._vars = {}
        for v in self.vars_list:
            dict_merge(self.vars, v, copy_dct=False)

    def retrieve_value(self, var_name, **task_context):

        return self._vars.get(var_name, None)

    def set_value(self, var_name, new_value, is_secret=False):

        self._vars[var_name] = new_value
        if is_secret:
            self._secrets.append(var_name)

    @property
    def vars(self):
        return self._vars

    def get_all(self, hide_secret=False):

        result = {}
        for k, v in self.vars.items():
            if hide_secret and k in self._secrets:
                result[k] = "__secret__"
            else:
                result[k] = v

        return result


# class TingsInventory(TingTings):
#
#     # DEFAULT_TING_CAST = VarCast
#
#     def __init__(self, repo_name, tingsets, load_config=None, **kwargs):
#
#         super(Inventory, self).__init__(
#             repo_name=repo_name,
#             tingsets=tingsets,
#             load_config=load_config,
#             indexes=["var_path"],
#         )
#
#     def retrieve_value(self, var_name, **task_context):
#
#         var = self.vars.get(var_name, None)
#         if var is None:
#             return None
#
#         return var.get_value(**task_context)
