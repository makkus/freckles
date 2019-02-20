import abc
import logging

import six

from frutils import dict_merge
from ting.ting_attributes import TingAttribute
from ting.ting_cast import TingCast
from ting.tings import TingTings

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


class VarsInventory(Inventory):
    def __init__(self, *vars):

        self.vars_list = vars

        self.vars = {}
        for v in self.vars_list:
            dict_merge(self.vars, v, copy_dct=False)

    def retrieve_value(self, var_name, **task_context):

        return self.vars.get(var_name, None)


class TingsInventory(TingTings):

    # DEFAULT_TING_CAST = VarCast

    def __init__(self, repo_name, tingsets, load_config=None, **kwargs):

        super(Inventory, self).__init__(
            repo_name=repo_name,
            tingsets=tingsets,
            load_config=load_config,
            indexes=["var_path"],
        )

    def retrieve_value(self, var_name, **task_context):

        var = self.vars.get(var_name, None)
        if var is None:
            return None

        return var.get_value(**task_context)
