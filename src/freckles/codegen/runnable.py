# -*- coding: utf-8 -*-
import abc
from collections import OrderedDict

import six


def function_interface_filter(required_args, optional_args):

    required = []
    # first we get all non-default required vars
    for arg_name, arg in required_args.items():

        if arg.default is not None:
            continue
        required.append(arg_name)

    optional = OrderedDict()
    # then we get all required vars with default arguments
    for arg_name, arg in required_args.items():

        if arg.default is None:
            continue
        optional[arg_name] = arg.default

    # and finally we get the optional arguments
    for arg_name, arg in optional_args.items():
        optional_args[arg_name] = arg.default

    return required, optional_args


@six.add_metaclass(abc.ABCMeta)
class RunnableFrecklet(object):
    def __init__(self):

        pass

    @abc.abstractmethod
    def get_frecklet_list(self):

        pass

    def run(self, context):

        frecklet_list = self.get_frecklet_list()

        frecklet = context.load_frecklet(frecklet_list)

        import pp

        fx = context.create_frecklecutable(frecklet[1])

        pp(fx.__dict__)

        fx.run()


@six.add_metaclass(abc.ABCMeta)
class FreckletWrapper(RunnableFrecklet):
    def __init__(self, var_names):

        self.var_names = var_names

        super(FreckletWrapper, self).__init__()

    def get_frecklet_list(self):

        vars = {}
        for v in self.var_names:
            vars[v] = getattr(self, v)

        return [{self.__class__.FRECKLET_ID: vars}]
