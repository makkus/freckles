import logging

from freckles.defaults import FRECKLETS_KEY, FRECKLET_KEY_NAME, TASK_KEY_NAME, DEFAULT_FRECKLES_JINJA_ENV
from freckles.frecklecutable_new import FrecklecutableNew, FrecklecutableMixin
from freckles.frecklet.arguments import ArgsAttribute, RequiredVariablesAttribute, CliArgumentsAttribute
from freckles.frecklet.tasks import FreckletsAttribute, TaskListAttribute, TaskTreeAttribute
from ting.ting_attributes import (
    ValueAttribute,
    TingAttribute, FileStringContentAttribute, DictContentTingAttribute)
from frutils import get_template_keys
from frutils.doc import Doc
from ting.ting_cast import TingCast
from ting.tings import TingTings, FileTings

log = logging.getLogger("freckles")


class TemplateKeysAttribute(TingAttribute):

    def requires(self):
        return ["_metadata_raw"]

    def provides(self):
        return ["template_keys"]

    def get_attribute(self, ting, attribute_name=None):

        template_keys = get_template_keys(ting._metadata_raw[FRECKLETS_KEY], jinja_env=DEFAULT_FRECKLES_JINJA_ENV)

        return template_keys


class DocAttribute(ValueAttribute):
    def __init__(self):

        super(DocAttribute, self).__init__(
            target_attr_name="doc", source_attr_name="_metadata_raw"
        )

    def get_attribute(self, ting, attribute_name=None):

        result = ValueAttribute.get_attribute(
            self, ting, attribute_name=attribute_name
        )

        doc = Doc(result)
        return doc


class FreckletMetaAttribute(ValueAttribute):
    def __init__(self):

        super(FreckletMetaAttribute, self).__init__(
            target_attr_name="meta", source_attr_name="_metadata_raw"
        )

    def get_attribute(self, ting, attribute_name=None):

        result = ValueAttribute.get_attribute(
            self, ting, attribute_name=attribute_name
        )
        return result


class FreckletCast(TingCast):

    FRECKLET_ATTRS = [
        FileStringContentAttribute(),
        DictContentTingAttribute(
            dict_name="_metadata_raw", source_attr_name="ting_content"
        ),
        ArgsAttribute(),
        DocAttribute(),
        FreckletMetaAttribute(),
        FreckletsAttribute(),
        TaskListAttribute(),
        TaskTreeAttribute(),
        RequiredVariablesAttribute(),
        TemplateKeysAttribute(),
        CliArgumentsAttribute()
    ]

    def __init__(self):

        super(FreckletCast, self).__init__(
            "FreckletTing",
            ting_attributes=FreckletCast.FRECKLET_ATTRS,
            ting_id_attr="filename_no_ext",
            mixins=[FrecklecutableMixin]
        )


class FreckletTings(TingTings):

    DEFAULT_TING_CAST = FreckletCast

    LOAD_CONFIG_SCHEMA = FileTings.LOAD_CONFIG_SCHEMA

    DEFAULT_LOAD_CONFIG = {
        "file_match_regex": "\.frecklet$",
        "subfolders": True,
        "ignore_hidden_files": True
    }

    def __init__(self, repo_name, tingsets, load_config=None, **kwargs):

        super(FreckletTings, self).__init__(
            repo_name=repo_name, tingsets=tingsets, load_config=load_config
        )

    # def get_frecklet(self, name):
    #
    #     return self.get(name, index_name="id")
