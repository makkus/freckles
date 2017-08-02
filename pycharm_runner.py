#!/usr/bin/env python

from __future__ import print_function

import sys
import traceback
from argparse import ArgumentParser
from importlib import import_module


NOTHING = object()


class PycharmRunnerException(Exception):
    pass


def run(args, module_args):
    parts = args.target.split(':')
    if len(parts) != 2:
        raise PycharmRunnerException('Bad target definition: {}. Expected: package.module:function.'.format(args.target))
    (module_name, func_name) = parts
    module = import_module(module_name)
    func = getattr(module, func_name, NOTHING)
    if func is NOTHING:
        raise PycharmRunnerException('Module "{}" does not contain function "{}"'.format(module_name, func_name))
    if not callable(func):
        raise PycharmRunnerException('Target "{}" is not callable. Got: {!r}'.format(args.target, func))
    sys.argv[0] = module.__file__
    sys.argv[1:] = module_args
    return func()


def main():
    parser = ArgumentParser(add_help=False)
    parser.add_argument('target', help='Fully qualified entry point path, e.g.: package.module:function')
    args, module_args = parser.parse_known_args()

    try:
        return run(args, module_args)
    except PycharmRunnerException as e:
        print(e, file=sys.stderr)

    return 1


if __name__ == '__main__':
    sys.exit(main())

