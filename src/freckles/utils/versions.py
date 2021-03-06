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
        from freckles_adapter_terraform import (
            __version__ as freckles_adapter_terraform_version,
        )
    except (Exception):
        freckles_adapter_terraform_version = "0.0.0"
    try:
        from freckworks import __version__ as freckworks_version
    except (Exception):
        freckworks_version = "0.0.0"
    try:
        from freckles_cli import __version__ as freckles_cli_version
    except (Exception):
        freckles_cli_version = "0.0.0"
    try:
        from pyckles import __version__ as pyckles_version
    except (Exception):
        pyckles_version = "0.0.0"
    try:
        from shellting import __version__ as shellting_version
    except (Exception):
        shellting_version = "0.0.0"

    versions = CommentedMap()
    versions["freckles"] = freckles_version
    versions["frutils"] = frutils_version
    versions["frkl"] = frkl_version
    versions["frkl_pkg"] = frkl_pkg_version
    versions["ting"] = ting_version
    versions["pyckles"] = pyckles_version
    versions["freckles_cli"] = freckles_cli_version
    if freckworks_version != "0.0.0":
        versions["freckworks"] = freckworks_version
    versions["tempting"] = tempting_version
    if shellting_version != "0.0.0":
        versions["shellting"] = shellting_version
    versions["freckles_adapter_nsbl"] = freckles_adapter_nsbl_version
    versions["nsbl"] = nsbl_version
    if freckles_adapter_terraform_version != "0.0.0":
        versions["freckles_adapter_terraform"] = freckles_adapter_terraform_version

    return versions
