"""Generic configuration class."""
import copy
import logging

from jinja2 import PackageLoader
from jinja2.nativetypes import NativeEnvironment
from ruamel.yaml.comments import CommentedMap

from freckles.defaults import FRECKLET_NAME
from freckles.utils.doc_utils import get_task_plan_string, describe_tasklist_string
from frutils import dict_merge, JINJA_DELIMITER_PROFILES, readable, readable_yaml

log = logging.getLogger("freckles")

DOC_TEMPLATE_LOADER = PackageLoader("freckles", "templates")
DOC_JINJA_ENV = NativeEnvironment(
    extensions=["jinja2.ext.do"],
    loader=DOC_TEMPLATE_LOADER,
    **JINJA_DELIMITER_PROFILES["documentation"]
)


def create_doc_env(freckles_obj, jinja_env=None):

    if jinja_env is None:
        jinja_env = DOC_JINJA_ENV

    # filters
    def get_frecklet_filter(frecklet_name):
        return freckles_obj.get_frecklet(frecklet_name)

    def get_cli_help_filter(frecklet_name):
        help = freckles_obj.get_frecklet_cli_doc_string(frecklet_name)
        return help

    def get_frecklet_help_filter(frecklet_name, default="n/a", use_short_help=True):
        return (
            freckles_obj.get_frecklet(frecklet_name)
            .get_doc()
            .get_help(default=default, use_short_help=use_short_help)
        )

    def get_frecklet_long_help_filter(frecklet_name):
        return freckles_obj.get_frecklet(frecklet_name).get_doc().get_long_help()

    def get_frecklet_short_help_filter(frecklet_name):
        return freckles_obj.get_frecklet(frecklet_name).get_doc().get_short_help()

    def get_further_reading_filter(frecklet_name):
        further_reading = (
            freckles_obj.get_frecklet(frecklet_name).get_doc().get_further_reading()
        )
        return further_reading

    def get_examples_filter(frecklet_name):
        return freckles_obj.get_frecklet(frecklet_name).get_doc().get_examples()

    def get_parameters_filter(frecklet_name):
        return freckles_obj.get_frecklet(frecklet_name).get_parameters()

    def get_task_plan(frecklet_name):
        task_plan = freckles_obj.get_task_plan(frecklet_name)
        task_plan_string = get_task_plan_string(task_plan, indent=0)
        return task_plan_string

    def get_task_plan_for_vars(frecklet_name, vars):

        task_plan = freckles_obj.get_task_plan(frecklet_name, vars=vars)

        md = describe_tasklist_string(task_plan)

        return md

    def get_task_list(frecklet_name):

        frecklet = freckles_obj.get_frecklet(frecklet_name)
        task_list = frecklet.get_tasklist()
        result = []
        for t in task_list:
            temp = CommentedMap()
            temp[FRECKLET_NAME] = t[FRECKLET_NAME]
            if "task" in t.keys() and t["task"]:
                tt = copy.copy(t["task"])
                tt.pop("msg", None)
                tt.pop("desc", None)
                temp["task"] = tt
            if "vars" in t.keys() and t["vars"]:
                temp["vars"] = t["vars"]
            result.append(temp)

        return result

    def get_task_list_for_vars(frecklet_name, vars):

        fx = freckles_obj.get_frecklecutable(frecklet_name)
        tasklists = fx.process_tasklist(vars=vars)

        result = []
        for tl_id, tasklist_details in tasklists.items():

            tl_temp = CommentedMap()
            temp_result = []

            tl = tasklist_details["task_list"]

            for t in tl:
                temp = CommentedMap()
                temp[FRECKLET_NAME] = t[FRECKLET_NAME]
                task = t.get("task", None)
                if task:
                    tt = copy.copy(task)
                    tt.pop("msg", None)
                    tt.pop("desc", None)
                    temp["task"] = task
                vars = t.get("vars, None")
                if vars:
                    temp["vars"] = vars

                temp_result.append(temp)

            tl_temp["tasklist_{}".format(tl_id)] = temp_result
            result.append(tl_temp)

        output = []
        for tl in result:
            tl_string = readable_yaml(tl, ignore_aliases=True)
            output.append(tl_string)

        return "\n".join(output)

    def get_frecklet_metadata_filter(frecklet_name, key=None):
        md = freckles_obj.get_frecklet(frecklet_name).metadata_raw
        if key is not None:
            return md.get(key, {})
        else:
            return md

    def to_yaml_filter(obj, empty_string=None, indent=0):

        if not obj:
            return empty_string

        return readable(obj, out="yaml", ignore_aliases=True, indent=indent)

    def to_code_block_filter(obj, format=None):

        if format is None:
            format = ""

        return "```{}\n{}\n```".format(format, obj)

    jinja_env.filters["frecklet_obj"] = get_frecklet_filter
    jinja_env.filters["frecklet_cli_help"] = get_cli_help_filter
    jinja_env.filters["frecklet_help"] = get_frecklet_help_filter
    jinja_env.filters["frecklet_short_help"] = get_frecklet_short_help_filter
    jinja_env.filters["frecklet_long_help"] = get_frecklet_long_help_filter
    jinja_env.filters["frecklet_further_reading"] = get_further_reading_filter
    jinja_env.filters["frecklet_parameters"] = get_parameters_filter
    jinja_env.filters["frecklet_examples"] = get_examples_filter
    jinja_env.filters["frecklet_task_plan"] = get_task_plan
    jinja_env.filters["frecklet_task_plan_for_vars"] = get_task_plan_for_vars
    jinja_env.filters["frecklet_task_list"] = get_task_list
    jinja_env.filters["frecklet_task_list_for_vars"] = get_task_list_for_vars
    jinja_env.filters["frecklet_raw"] = get_frecklet_metadata_filter
    jinja_env.filters["to_code_block"] = to_code_block_filter
    jinja_env.filters["to_yaml"] = to_yaml_filter

    return jinja_env


def render_frecklet(
    frecklet_name,
    freckles_obj,
    extra_vars=None,
    template_name="frecklet_doc/markdown/layout.md.j2",
    markdown_renderer=None,
):

    if extra_vars is None:
        extra_vars = {}

    repl_dict = dict_merge(
        extra_vars,
        {"freckles": freckles_obj, "frecklet_name": frecklet_name},
        copy_dct=True,
    )

    jinja_env = freckles_obj.get_doc_env()
    filter_backup = jinja_env.filters
    try:
        filters_copy = copy.copy(filter_backup)
        filters_copy["from_markdown"] = markdown_renderer
        jinja_env.filters = filters_copy
        template = freckles_obj.get_doc_env().get_template(template_name)
        rendered = template.render(**repl_dict)
        return rendered
    finally:
        jinja_env.filters = filter_backup


def render_cnf(
    context,
    freckles_obj,
    extra_vars=None,
    template_name="cnf_doc/markdown/layout.md.j2",
    markdown_renderer=None,
):

    if extra_vars is None:
        extra_vars = {}

    repl_dict = dict_merge(extra_vars, {"context": context}, copy_dct=True)

    jinja_env = freckles_obj.get_doc_env()
    filter_backup = jinja_env.filters
    try:
        filters_copy = copy.copy(filter_backup)
        filters_copy["from_markdown"] = markdown_renderer
        jinja_env.filters = filters_copy
        template = freckles_obj.get_doc_env().get_template(template_name)
        rendered = template.render(**repl_dict)
        return rendered
    finally:
        jinja_env.filters = filter_backup
