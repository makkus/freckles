# -*- coding: utf-8 -*-

"""Generic configuration class."""
import logging

from ruamel.yaml import YAML

from freckles.defaults import FRECKLET_NAME
from freckles.exceptions import FrecklesConfigException
from freckles.utils.doc_templating import DOC_JINJA_ENV
from frutils import readable

log = logging.getLogger("frutils")

yaml = YAML(typ="safe")

CURSOR_UP_ONE = "\x1b[1A"
ERASE_LINE = "\x1b[2K"

BOLD = "\033[1m"
UNBOLD = "\033[0m"

ARC_DOWN_RIGHT = u"\u256d"
ARC_UP_RIGHT = u"\u2570"
VERTICAL_RIGHT = u"\u251C"
VERTICAL = u"\u2502"
HORIZONTAL = u"\u2500"
END = u"\u257C"
ARROW = u"\u279B"
OK = u"\u2713"


# def sanitize_rst_filter(value):
#
#     if not isinstance(value, string_types):
#         return value
#
#     if value.endswith("_"):
#         value = "{}\\_".format(value[0:-1])
#     return value
#
#
# def make_sentence_filter(value):
#
#     if not isinstance(value, string_types):
#         return value
#
#     if not value.endswith("."):
#         value = value + "."
#
#     value = value.capitalize()
#     return value
#
#
# DOC_JINJA_FILTERS = {
#     "sanitize_rst": sanitize_rst_filter,
#     "make_sentence": make_sentence_filter,
# }
#
# for key, value in DOC_JINJA_FILTERS.items():
#     DOC_JINJA_ENV.filters[key] = value


def render_frecklet(
    frecklet_name,
    frecklet,
    show=None,
    template_name="frecklet_template_default.md.j2",
    jinja_env=None,
    extra_vars=None,
):

    if extra_vars is None:
        extra_vars = {}

    if jinja_env is None:
        jinja_env = DOC_JINJA_ENV

    if show is None:
        show = {"arguments": False, "references": False, "arg_list_filter": []}

    repl_dict = {
        "frecklet_name": frecklet_name,
        "frecklet": frecklet,
        "show": show,
        "extra": extra_vars,
    }

    template = jinja_env.get_template(template_name)
    rendered = template.render(**repl_dict)

    return rendered


def get_desc(task_details, context, use_frecklet_name=True):

    command = task_details[FRECKLET_NAME]["command"]
    f_name = command
    f_type = task_details[FRECKLET_NAME]["type"]

    desc = None
    if not use_frecklet_name:
        desc = task_details.get("task", {}).get("msg", None)

        # if desc is None:
        #     desc = task_details.get("task", {}).get("msg", None)

        if desc is None and f_type == "frecklet":

            try:
                md = context.get_frecklet_metadata(f_name)
                desc = md.get("doc", {}).get("short_help", None)
            except (FrecklesConfigException):
                pass

    desc_is_command = False
    if desc is None:
        desc = f_name
        desc_is_command = True

    if desc.startswith("[") and desc.endswith("]"):
        desc = desc[1:-1]

    if f_type != "frecklet":
        if desc_is_command:
            desc = "{} (type: {})".format(desc, f_type)
        else:
            desc = "{} ({}: {})".format(desc, f_type, command)

    return desc.strip()


def get_task_hierarchy(root_tasks, used_ids, task_map, context, level=0):

    minimal = False
    result = []

    for id, childs in root_tasks.items():

        desc = get_desc(task_map[id], context=context)
        f_name = task_map[id]["frecklet"]["command"]
        f_type = task_map[id]["frecklet"]["type"]
        if f_type == "frecklet":
            md = context.get_frecklet_metadata(f_name)
            doc = md["doc"]
        else:
            f = task_map[id]["frecklet"]
            v = task_map[id].get("vars", {})
            t_dict = {"frecklet": f}
            if v:
                t_dict["vars"] = v
            doc = readable(t_dict, out="yaml", ignore_aliases=True)

        if childs:
            temp_childs = get_task_hierarchy(
                childs,
                used_ids=used_ids,
                task_map=task_map,
                context=context,
                level=level + 1,
            )

            if not temp_childs:
                continue

            d = {"children": temp_childs, "level": level, "desc": desc, "doc": doc}
            if minimal:
                d["child"] = task_map[id]["frecklet"]["command"]
            else:
                d["child"] = task_map[id]
            result.append(d)
        else:
            if id not in used_ids:
                continue
            d = {"children": [], "level": level, "desc": desc, "doc": doc}
            if minimal:
                d["child"] = task_map[id]["frecklet"]["command"]
            else:
                d["child"] = task_map[id]
            result.append(d)

    return result


# class FrecklesDoc:
#     def __init__(self, frecklet_name, frecklet, context):
#
#         self.frecklet_name = frecklet_name
#         self.frecklet = frecklet
#         self.context = context
#
#         self.tasklist = frecklet.get_tasklist()
#
#         ids = []
#
#         for t in self.tasklist:
#             id = t["meta"]["__id__"]
#             ids.append(id)
#         self.task_tree = frecklet.get_task_tree()
#         self.task_map = frecklet.get_task_map()
#
#         self.hierarchy = get_task_hierarchy(
#             self.task_tree, used_ids=ids, task_map=self.task_map, context=self.context
#         )
#
#         # output(hierarchy, output_type="yaml", ignore_aliases=True)
#
#     def create_tasklist(self, vars={}):
#
#         frecklecutable = Frecklecutable(
#             name=self.frecklet_name, frecklet=self.frecklet, context=self.context
#         )
#
#         tasklists = frecklecutable.process_tasklist(vars, process_user_input=True)
#
#         task_list = tasklists[0]["task_list"]
#         task_list = cleanup_tasklist(task_list)
#
#         return task_list
#
#     def create_rendered_hierarchy(self, vars={}):
#
#         task_list = self.create_tasklist(vars=vars)
#         ids = []
#
#         task_map = copy.deepcopy(self.task_map)
#
#         for t in task_list:
#             id = t["meta"]["__id__"]
#             ids.append(id)
#             task_map[id] = t
#
#         hierarchy = get_task_hierarchy(
#             self.task_tree, used_ids=ids, task_map=task_map, context=self.context
#         )
#         return hierarchy
#
#     def create_rendered(self, vars={}, render_markdown=False):
#
#         hierarchy = self.create_rendered_hierarchy(vars)
#
#         show = {"details": False}
#
#         extra = {"task_hierarchy": hierarchy}
#
#         rendered = render_frecklet(
#             frecklet_name=self.frecklet_name,
#             frecklet=self.frecklet,
#             show=show,
#             template_name="frecklet_overview.md.j2",
#             extra_vars=extra,
#         )
#         # rendered = render_frecklet(frecklet_name=self.frecklet_name, frecklet=self.frecklet, show=show, template_name="frecklet_debug.md.j2", extra_vars=extra)
#
#         if render_markdown:
#             # rendered = mdvl.main(rendered, no_print=True)[0]
#             rendered = mdv.main(rendered, no_colors=True, header_nrs="1-")
#
#         return rendered
#
#     def print_rendered(self, vars={}):
#
#         rendered = self.create_rendered(vars, render_markdown=True)
#         click.echo(rendered)
#
#     def create_description(self):
#
#         # self.print_task_hierarchy(self.hierarchy, task_map=self.task_map)
#
#         show = {"details": True}
#
#         extra = {"task_hierarchy": self.hierarchy}
#
#         rendered = render_frecklet(
#             frecklet_name=self.frecklet_name,
#             frecklet=self.frecklet,
#             show=show,
#             template_name="frecklet_overview.md.j2",
#             extra_vars=extra,
#         )
#         # rendered = render_frecklet(frecklet_name=self.frecklet_name, frecklet=self.frecklet, show=show, template_name="frecklet_debug.md.j2", extra_vars=extra)
#
#         render = True
#         if render:
#             # rendered = mdvl.main(rendered, no_print=True)[0]
#             rendered = mdv.main(rendered, no_colors=True, header_nrs="1-")
#
#         return rendered
#
#     def describe(self):
#
#         result = self.create_description()
#         click.echo(result)
#
#     def print_task_hierarchy(self, hierarchy, task_map, level=0):
#
#         for id, children in hierarchy.items():
#             f = task_map[id]
#             f_name = f[FRECKLET_NAME]["command"]
#             desc = f.get("task", {}).get("msg", None)
#             task_type = f[FRECKLET_NAME]["type"]
#             if desc is None:
#                 try:
#                     md = self.context.get_frecklet_metadata(f_name)
#                     desc = md.get("doc", {}).get("short_help", None)
#                 except (FrecklesConfigException):
#                     pass
#
#                 if desc is None:
#                     desc = "frecklet: {}".format(f_name)
#             padding = "  " * level
#             # desc = "{}: {}".format(f_name, desc)
#             msg = "{}{}".format(padding, desc)
#             if task_type != "frecklet":
#                 msg = "{} (frecklet: {}/{})".format(msg, task_type, f_name)
#             else:
#                 msg = "{} (frecklet: {})".format(msg, f_name)
#
#             self.print_task_hierarchy(children, task_map, level=level + 1)
