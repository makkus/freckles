# -*- coding: utf-8 -*-
from ruamel.yaml.comments import CommentedMap


def get_versions():

    try:
        from frutils import __version__ as frutils_version
    except (Exception):
        frutils_version = "0.0.0"
    try:
        from frkl import __version__ as frkl_version
    except (Exception):
        frkl_version = "0.0.0"
    try:
        from frkl_pkg import __version__ as frkl_pkg_version
    except (Exception):
        frkl_pkg_version = "0.0.0"
    try:
        from ting import __version__ as ting_version
    except (Exception):
        ting_version = "0.0.0"
    try:
        from freckles import __version__ as freckles_version
    except (Exception):
        freckles_version = "0.0.0"
    try:
        from nsbl import __version__ as nsbl_version
    except (Exception):
        nsbl_version = "0.0.0"
    try:
        from tempting import __version__ as tempting_version
    except (Exception):
        tempting_version = "0.0.0"
    try:
        from freckles_adapter_nsbl import __version__ as freckles_adapter_nsbl_version
    except (Exception):
        freckles_adapter_nsbl_version = "0.0.0"
    try:
        from freckles_cli import __version__ as freckles_cli_version
    except (Exception):
        freckles_cli_version = "0.0.0"

    versions = CommentedMap()
    versions["freckles"] = freckles_version
    versions["frutils"] = frutils_version
    versions["frkl"] = frkl_version
    versions["frkl_pkg"] = frkl_pkg_version
    versions["ting"] = ting_version
    versions["nsbl"] = nsbl_version
    versions["tempting"] = tempting_version
    versions["freckles_adapter_nsbl"] = freckles_adapter_nsbl_version
    versions["freckles_cli"] = freckles_cli_version

    return versions
