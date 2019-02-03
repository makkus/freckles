import logging

from freckles.frecklecutable_new import TEST_INVENTORY
from ting.ting_attributes import TingAttribute
from ting.ting_cast import TingCast
from ting.tings import TingTings, DictTings

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

    VAR_ATTRS = [
    ]

    def __init__(self, prefix):

        var_path_attr = VarPathAttribute(prefix)
        super(VarCast, self).__init__(
            "VarTing",
            ting_attributes=[var_path_attr],
            ting_id_attr="var_path",
            mixins=[]
        )


inv_1_dict = {
    "name": "markus"
}

inv_2_dict = {
    "name": "theresa"
}

cast_1 = VarCast(prefix="inv_1")
cast_2 = VarCast(prefix="inv_2")
INV_1 = DictTings("inv_1", data=inv_1_dict, ting_cast=cast_1, indexes=["var_path"], key_name="var", meta_name="value")
INV_2 = DictTings("inv_2", data=inv_2_dict, ting_cast=cast_2, indexes=["var_path"], key_name="var", meta_name="value")


class Inventory(TingTings):

    # DEFAULT_TING_CAST = VarCast

    def __init__(self, repo_name, tingsets, load_config=None, **kwargs):

        super(Inventory, self).__init__(
            repo_name=repo_name, tingsets=tingsets, load_config=load_config, indexes=["var_path"]
        )


    def retrieve_value(self, var_name,  **task_context):

        var = self.vars.get(var_name, None)
        if var is None:
            return None

        return var.get_value(**task_context)


