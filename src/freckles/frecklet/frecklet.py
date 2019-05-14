# -*- coding: utf-8 -*-
import os
from collections import Sequence

from ruamel.yaml.comments import CommentedMap

from freckles.frecklecutable import FrecklecutableMixin
from freckles.frecklet.doc import render_html, render_markdown
from ting.ting_attributes import MultiCacheResult
from .tasks import *  # noqa

log = logging.getLogger("freckles")


class FreckletsTemplateKeysAttribute(TingAttribute):
    def requires(self):
        return ["_metadata"]

    def provides(self):
        return ["template_keys"]

    def get_attribute(self, ting, attribute_name=None):

        template_keys = get_template_keys(
            ting._metadata[FRECKLETS_KEY], jinja_env=DEFAULT_FRECKLES_JINJA_ENV
        )

        return template_keys


class FreckletAugmentMetadataAttribute(TingAttribute):
    def requires(self):

        return ["_metadata_raw"]

    def provides(self):

        return ["_metadata"]

    def get_attribute(self, ting, attribute_name=None):

        raw = ting._metadata_raw

        if isinstance(raw, string_types):
            raise Exception(
                "Invalid frecklet: content needs to be a list or dict: {}".format(raw)
            )
        if isinstance(raw, Sequence):
            md = {"frecklets": raw}
        elif not isinstance(raw, Mapping):
            raise Exception("Invalid frecklet: content needs to be a list or dict")
        else:
            md = raw

        if "frecklets" not in md.keys():
            raise Exception("Invalid frecklet: no frecklets task list")

        if "meta" not in md.keys():
            md["meta"] = {}

        if "doc" not in md.keys():
            md["doc"] = {}

        if "args" not in md.keys():
            md["args"] = {}

        return md


class FreckletValidAttribute(TingAttribute):
    def __init__(self):
        pass

    def provides(self):
        return ["valid", "invalid_exception"]

    def requires(self):
        return ["exploded"]

    def get_attribute(self, ting, attribute_name=None):

        try:
            exploded = ting.exploded
            log.debug("checking exploded data structure: {}".format(exploded))
            result = {"valid": True, "invalid_exception": None}
        except (Exception) as e:
            log.debug("Validation for frecklet failed.")
            log.debug(e, exc_info=1)
            result = {"valid": False, "invalid_exception": e}

        return MultiCacheResult(**result)


class FreckletExplodedAttribute(TingAttribute):
    def __init__(self):
        pass

    def provides(self):
        return ["exploded"]

    def requires(self):

        return ["vars_frecklet", "doc", "tasklist"]

    def get_attribute(self, ting, attribute_name=None):

        result = CommentedMap()

        result["doc"] = ting.doc.exploded_dict()

        result["args"] = CommentedMap()

        for k, arg in ting.vars_frecklet.items():
            details = arg.pretty_print_dict(full_details=True)
            result["args"][k] = details

        result["frecklets"] = []
        for task in ting.tasklist:
            r = CommentedMap()
            r[FRECKLET_KEY_NAME] = task[FRECKLET_KEY_NAME]
            if TASK_KEY_NAME in task.keys() and task[TASK_KEY_NAME]:
                r[TASK_KEY_NAME] = task[TASK_KEY_NAME]
            if VARS_KEY in task.keys() and task[VARS_KEY]:
                r[VARS_KEY] = task[VARS_KEY]
            result["frecklets"].append(r)

        return result


class FreckletMetaAttribute(ValueAttribute):
    def __init__(self):

        super(FreckletMetaAttribute, self).__init__(
            target_attr_name="meta_frecklet", source_attr_name="_metadata", default={}
        )

    def get_attribute(self, ting, attribute_name=None):

        result = ValueAttribute.get_attribute(self, ting, attribute_name=attribute_name)
        return result


class FreckletHtmlAttribute(TingAttribute):
    def __init__(self):

        pass

    def provides(self):

        return ["html"]

    def requires(self):

        return []

    def get_attribute(self, ting, attribute_name=None):

        try:
            html = render_html(ting)
            return html
        except (Exception) as e:

            return "<p>Can't render frecklet {}: {}".format(ting.id, e)


class FreckletMarkdownAttribute(TingAttribute):
    def __init__(self):

        pass

    def provides(self):

        return ["markdown"]

    def requires(self):

        return []

    def get_attribute(self, ting, attribute_name=None):

        try:
            markdown = render_markdown(ting)
            return markdown
        except (Exception) as e:

            import traceback

            traceback.print_exc()

            return "Can't render frecklet {}: {}".format(ting.id, e)


class PagelingMetadataAttribute(TingAttribute):
    def __init__(self):

        pass

    def provides(self):

        return ["pageling_metadata"]

    def requires(self):

        return ["wrapped"]

    def get_attribute(self, ting, attribute_name=None):

        frecklet = ting.wrapped
        result = {}
        result["title"] = frecklet.id
        result["is_draft"] = frecklet.meta.get("draft", False)

        return result


class PagelingContentAttribute(TingAttribute):
    def __init__(self):

        pass

    def provides(self):

        return ["pageling_content"]

    def requires(self):

        return ["wrapped"]

    def get_attribute(self, ting, attribute_name=None):

        frecklet = ting.wrapped
        return str(frecklet.doc)


class PagelingNavPathAttribute(TingAttribute):
    def __init__(self):

        pass

    def provides(self):

        return ["tree_path"]

    def requires(self):

        return ["wrapped"]

    def get_attribute(self, ting, attribute_name=None):

        frecklet = ting.wrapped
        if hasattr(frecklet, "rel_path_no_ext"):
            rel_path = frecklet.rel_path_no_ext
        else:
            rel_path = "misc/{}".format(frecklet.id)

        tokens = rel_path.split(os.path.sep)

        if len(tokens) == 1:
            return "/" + tokens[0]
        else:
            return "/" + tokens[0] + "/" + tokens[-1]


FRECKLET_LOAD_CONFIG = {
    "class_name": "Frecklet",
    "attributes": [
        {
            "ArgsAttribute": {
                "source_attr_name": "_metadata",
                "target_attr_name": "args",
                "index_attr_name": "_meta_parent_repo",
                # "validate_list_attr": "template_keys",
            }
        },
        {"DocAttribute": {"source_attr_name": "_metadata"}},
        "FreckletMetaAttribute",
        "FreckletAugmentMetadataAttribute",
        "FreckletsAttribute",
        "TaskListDetailedAttribute",
        "FreckletHtmlAttribute",
        "FreckletMarkdownAttribute",
        "FreckletExplodedAttribute",
        "FreckletValidAttribute",
        "TaskTreeAttribute",
        {
            "VariablesAttribute": {
                "target_attr_name": "vars_frecklet",
                "default_argument_description": {"required": True, "empty": False},
            }
        },
        {
            "VariablesFilterAttribute": {
                "target_attr_name": "vars_required",
                "source_attr_name": "vars_frecklet",
                "required": True,
            }
        },
        {
            "VariablesFilterAttribute": {
                "target_attr_name": "vars_optional",
                "source_attr_name": "vars_frecklet",
                "required": False,
            }
        },
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
        "frecklet_file": {
            "class": "ting.tings.FileTings",
            "load_config": {},
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
                        "source_attr_name": "full_path",
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

# FRECKLET_LOAD_CONFIG_FILE = copy.deepcopy(FRECKLET_LOAD_CONFIG)
# FRECKLET_LOAD_CONFIG_FILE["loaders"]["frecklet_files"]["load_config"] = {}
# FRECKLET_LOAD_CONFIG_FILE["loaders"]["frecklet_files"]["attributes"] = [
#     {
#         "DictContentAttribute": {
#             "dict_name": "_metadata_raw",
#             "source_attr_name": "ting_content",
#         }
#     },
#     "FileStringContentAttribute",
#     {
#         "MirrorAttribute": {
#             "source_attr_name": "full_path",
#             "target_attr_name": "frecklet_name",
#         }
#     },
# ]


# class FreckletCast(TingCast):
#
#     FRECKLET_ATTRS = [
#         FileStringContentAttribute(),
#         DictContentAttribute(
#             dict_name="_metadata_raw", source_attr_name="ting_content"
#         ),
#         ArgsAttribute(
#             source_attr_name="_metadata_raw",
#             target_attr_name="args",
#             index_attr_name="_meta_parent_repo",
#             validate_list_attr="template_keys",
#         ),
#         DocAttribute(),
#         FreckletMetaAttribute(),
#         FreckletsAttribute(),
#         TaskListDetailedAttribute(),
#         TaskTreeAttribute(),
#         RequiredVariablesAttribute(),
#         FreckletsTemplateKeysAttribute(),
#         CliArgumentsAttribute(),
#         TaskListAttribute(),
#         TaskListResolvedAttribute(),
#     ]
#
#     def __init__(self):
#
#         super(FreckletCast, self).__init__(
#             "Frecklet",
#             ting_attributes=FreckletCast.FRECKLET_ATTRS,
#             ting_id_attr="filename_no_ext",
#             mixins=[FrecklecutableMixin],
#         )
#
#
# class FreckletTings(TingTings):
#
#     DEFAULT_TING_CAST = FreckletCast
#
#     def __init__(self, repo_name, tingsets, load_config=None, **kwargs):
#
#         super(FreckletTings, self).__init__(
#             repo_name=repo_name, tingsets=tingsets, load_config=load_config
#         )
