#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Setup file for freckles.
    Use setup.cfg to configure your project.

    This file was generated with PyScaffold 3.1.
    PyScaffold helps you to put up the scaffold of your new Python project.
    Learn more under: https://pyscaffold.org/
"""
import sys
from pkg_resources import VersionConflict, require
from setuptools import setup

try:
    require("setuptools>=38.3")
except VersionConflict:
    print("Error: version of setuptools is too old (<38.3)!")
    sys.exit(1)


if __name__ in ["__main__", "builtins", "__builtin__"]:
    setup(use_scm_version={"write_to": "src/freckles/version.txt"})
