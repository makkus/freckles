# -*- coding: utf-8 -*-
from freckles.defaults import FRECKLET_KEY_NAME
from frutils import readable


class FrecklesException(Exception):
    """Base exception class for nsbl."""

    def __init__(self, message):

        super(FrecklesException, self).__init__(message)


class FrecklesConfigException(FrecklesException):
    def __init__(self, message):

        super(FrecklesConfigException, self).__init__(message)

class FrecklesVarException(FrecklesException):

    def __init__(self, frecklet=None, var_name=None, message=None, error=None, task_path=None, vars=None, task=None):
        super(FrecklesVarException, self).__init__(message=message)

        self.var_name = var_name
        self.frecklet = frecklet
        self.error = error
        self.task_path = task_path
        self.vars = vars
        self.task = task

    def __str__(self):

        msg = "Error processing variables:\n"
        msg = msg + "  frecklet: {}\n".format(self.frecklet.id)
        if self.task_path is not None:
          msg = msg + "  task path: {}\n".format(self.task_path)
        msg = msg + "  vars:\n    "
        msg = msg + readable(self.vars, out="yaml", indent=4).strip()
        if self.task is not None:
            msg = msg + "\n  frecklet:\n    "
            msg = msg + readable(self.task["frecklet"], out="yaml", indent=4).strip()
        msg = msg + "\n  error: {}".format(str(self.error))
        return msg

class FreckletException(FrecklesException):
    def __init__(self, message, frecklet):

        super(FreckletException, self).__init__(message)
        self.frecklet = frecklet


class FrecklesPermissionException(FrecklesException):
    def __init__(self, message):

        super(FrecklesPermissionException, self).__init__(message)
