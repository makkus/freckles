# -*- coding: utf-8 -*-
from collections import Sequence

from ruamel.yaml.comments import CommentedMap

from freckles.frecklecutable import FrecklecutableMixin
from freckles.frecklet.doc import render_html, render_markdown
from frutils import dict_merge
from frutils.jinja2_filters import camelize_filter
from ting.ting_attributes import MultiCacheResult, Arg
from .tasks import *  # noqa
from ting.attributes.rendering import JinjaTemplateMixin  # noqa

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

        return ["vars_frecklet", "doc", "tasklist", "const"]

    def get_attribute(self, ting, attribute_name=None):

        result = CommentedMap()

        result["doc"] = ting.doc.exploded_dict()
        result["const"] = ting.const

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


class FreckletConstAttribute(TingAttribute):
    def __init__(self):
        pass

    def provides(self):
        return [CONST_KEY_NAME]

    def requires(self):
        return ["_metadata"]

    def get_attribute(self, ting, attribute_name=None):

        result = ting._metadata.get(CONST_KEY_NAME, {})
        return result


class FreckletConstArgsAttribute(TingAttribute):
    def __init__(self):
        pass

    def provides(self):
        return ["vars_{}".format(CONST_KEY_NAME)]

    def requires(self):
        return ["const", "args"]

    def get_attribute(self, ting, attribute_name=None):

        result = {}
        for k, v in ting.const.items():

            tks = get_template_keys(v, jinja_env=DEFAULT_FRECKLES_JINJA_ENV)
            for tk in tks:
                if tk in result.keys():
                    continue

                arg = Arg(
                    key=tk,
                    arg_dict=ting.args.get(tk, None),
                    default_schema=FRECKLES_DEFAULT_ARG_SCHEMA,
                )
                result[tk] = arg

        return result


class FreckletMetaAttribute(TingAttribute):
    def __init__(self, default=None):

        if default is None:
            default = {}

        self.default = default

    def requires(self):
        return ["_metadata"]

    def provides(self):
        return ["meta"]

    def get_attribute(self, ting, attribute_name=None):

        metadata = ting._metadata.get("meta", {})

        merged = dict_merge(self.default, metadata, copy_dct=True)
        return merged


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


class FreckletClassNameAttribute(TingAttribute):
    def __init__(self):
        pass

    def provides(self):
        return ["class_name"]

    def requires(self):
        return ["id"]

    def get_attribute(self, ting, attribute_name=None):

        return camelize_filter(ting.id, replace_dashes=True)


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
        {"FreckletMetaAttribute": {"default": {}}},
        "FreckletConstAttribute",
        "FreckletConstArgsAttribute",
        "FreckletClassNameAttribute",
        "FreckletAugmentMetadataAttribute",
        "FreckletsAttribute",
        "TaskListDetailedAttribute",
        "FreckletHtmlAttribute",
        "FreckletMarkdownAttribute",
        "FreckletExplodedAttribute",
        "FreckletValidAttribute",
        "VarsAttribute",
        "TaskTreeAttribute",
        {
            "VariablesAttribute": {
                "target_attr_name": "vars_frecklet",
                "default_argument_description": FRECKLES_DEFAULT_ARG_SCHEMA,
            }
        },
        {
            "VariablesFilterAttribute": {
                "target_attr_name": "vars_required",
                "source_attr_name": "vars",
                "required": True,
            }
        },
        {
            "VariablesFilterAttribute": {
                "target_attr_name": "vars_optional",
                "source_attr_name": "vars",
                "required": False,
            }
        },
        # {
        #     "JinjaTemplateAttribute": {
        #         "template": "python_src.j2",
        #         "template_dir": "/home/markus/projects/freckles-dev/freckles/src/freckles/templates/src",
        #         "target_attr_name": "python_src",
        #         "required_attrs": [
        #             "class_name",
        #             "id",
        #             # "args",
        #             "vars_frecklet",
        #             "vars_required",
        #             "vars_optional",
        #         ],
        #     }
        # },
        "FreckletsTemplateKeysAttribute",
        "CliArgumentsAttribute",
        "TaskListAttribute",
        "TaskListResolvedAttribute",
    ],
    "ting_id_attr": "frecklet_name",
    "mixins": [FrecklecutableMixin, JinjaTemplateMixin],
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
