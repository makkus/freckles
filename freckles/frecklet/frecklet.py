import logging

from freckles.defaults import FRECKLETS_KEY, DEFAULT_FRECKLES_JINJA_ENV
from freckles.frecklecutable import FrecklecutableMixin
from freckles.frecklet.arguments import (
    RequiredVariablesAttribute,
    CliArgumentsAttribute,
)
from freckles.frecklet.tasks import (
    FreckletsAttribute,
    TaskListDetailedAttribute,
    TaskTreeAttribute,
    TaskListAttribute,
    TaskListResolvedAttribute,
)
from frutils import get_template_keys
from ting.ting_attributes import (
    ValueAttribute,
    TingAttribute,
    FileStringContentAttribute,
    DictContentAttribute,
    ArgsAttribute,
    DocAttribute,
)
from ting.ting_cast import TingCast
from ting.tings import TingTings

log = logging.getLogger("freckles")


class FreckletsTemplateKeysAttribute(TingAttribute):
    def requires(self):
        return ["_metadata_raw"]

    def provides(self):
        return ["template_keys"]

    def get_attribute(self, ting, attribute_name=None):

        template_keys = get_template_keys(
            ting._metadata_raw[FRECKLETS_KEY], jinja_env=DEFAULT_FRECKLES_JINJA_ENV
        )

        return template_keys


class FreckletMetaAttribute(ValueAttribute):
    def __init__(self):

        super(FreckletMetaAttribute, self).__init__(
            target_attr_name="meta", source_attr_name="_metadata_raw"
        )

    def get_attribute(self, ting, attribute_name=None):

        result = ValueAttribute.get_attribute(self, ting, attribute_name=attribute_name)
        return result


FRECKLET_LOAD_CONFIG = {
    "class_name": "Frecklet",
    "attributes": [
        {
            "ArgsAttribute": {
                "source_attr_name": "_metadata_raw",
                "target_attr_name": "args",
                "index_attr_name": "_meta_parent_repo",
                "validate_list_attr": "template_keys",
            }
        },
        "DocAttribute",
        "FreckletMetaAttribute",
        "FreckletsAttribute",
        "TaskListDetailedAttribute",
        "TaskTreeAttribute",
        "RequiredVariablesAttribute",
        "FreckletsTemplateKeysAttribute",
        "CliArgumentsAttribute",
        "TaskListAttribute",
        "TaskListResolvedAttribute",
    ],
    "ting_id_attr": "frecklet_name",
    "mixins": [FrecklecutableMixin],
    "loaders": {
        "frecklet_files": {
            "class": "ting.tings.FileTings",
            "load_config": {"folder_load_file_match_regex": "\\.frecklet$"},
            "attributes": [
                {
                    "DictContentAttribute": {
                        "dict_name": "_metadata_raw",
                        "source_attr_name": "ting_content",
                    }
                },
                "FileStringContentAttribute",
                {
                    "MirrorAttribute": {
                        "source_attr_name": "filename_no_ext",
                        "target_attr_name": "frecklet_name",
                    }
                },
            ],
        },
        "frecklet_dicts": {
            "class": "ting.tings.DictTings",
            "load_config": {},
            "attributes": [],
        },
    },
}


class FreckletCast(TingCast):

    FRECKLET_ATTRS = [
        FileStringContentAttribute(),
        DictContentAttribute(
            dict_name="_metadata_raw", source_attr_name="ting_content"
        ),
        ArgsAttribute(
            source_attr_name="_metadata_raw",
            target_attr_name="args",
            index_attr_name="_meta_parent_repo",
            validate_list_attr="template_keys",
        ),
        DocAttribute(),
        FreckletMetaAttribute(),
        FreckletsAttribute(),
        TaskListDetailedAttribute(),
        TaskTreeAttribute(),
        RequiredVariablesAttribute(),
        FreckletsTemplateKeysAttribute(),
        CliArgumentsAttribute(),
        TaskListAttribute(),
        TaskListResolvedAttribute(),
    ]

    def __init__(self):

        super(FreckletCast, self).__init__(
            "Frecklet",
            ting_attributes=FreckletCast.FRECKLET_ATTRS,
            ting_id_attr="filename_no_ext",
            mixins=[FrecklecutableMixin],
        )


class FreckletTings(TingTings):

    DEFAULT_TING_CAST = FreckletCast

    def __init__(self, repo_name, tingsets, load_config=None, **kwargs):

        super(FreckletTings, self).__init__(
            repo_name=repo_name, tingsets=tingsets, load_config=load_config
        )
