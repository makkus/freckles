# -*- coding: utf-8 -*-

from colorama import Style
from jinja2.exceptions import TemplateSyntaxError
from six import string_types

from frutils import readable, reindent
from frutils.exceptions import FrklException
from ting.exceptions import TingException


class FrecklesConfigException(FrklException):
    def __init__(
        self, keys=None, msg=None, solution=None, reason=None, references=None
    ):

        if keys and isinstance(keys, string_types):
            keys = [keys]
        if not msg:
            if not keys:
                message = "Configuration error."
            else:
                message = "Error with configuration option(s): {}.".format(
                    ", ".join(keys)
                )
        else:
            message = msg

        if solution is None:
            if not keys:
                solution = "Check documentaiton for configuration key."
            else:
                solution = "Check documentaiton for configuration key(s): {}.".format(
                    ", ".join(keys)
                )

        references_default = {
            "freckles configuration documentation": "https://freckles.io/doc/configuration"
        }
        if references:
            references.update(references_default)

        super(FrecklesConfigException, self).__init__(
            msg=message, solution=solution, references=references, reason=reason
        )
        self.keys = keys
        self.msg = msg


class FrecklesVarException(FrklException):
    def __init__(
        self,
        frecklet=None,
        var_name=None,
        message=None,
        errors=None,
        task_path=None,
        vars=None,
        task=None,
    ):

        self.var_name = var_name
        self.frecklet = frecklet
        self.errors = errors
        self.task_path = task_path
        self.vars = vars
        self.task = task

        msg = "Error validating input for frecklet '{}'.".format(frecklet.id)

        if len(self.errors) == 1:
            reason = Style.BRIGHT + "Var:" + Style.RESET_ALL + "\n\n"
        else:
            reason = Style.BRIGHT + "Vars:" + Style.RESET_ALL + "\n\n"

        for var, error in self.errors.items():
            reason = "  " + Style.DIM + "{}:".format(var) + Style.RESET_ALL
            if len(error) == 1:
                reason = reason + " " + error[0]
            else:
                reason = reason + "\n"
                for e in error:
                    reason = reason + "    - {}".format(e)

        super(FrecklesVarException, self).__init__(msg=msg, reason=reason)

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
        msg = msg + "\n  error: {}".format(str(self.errors))
        return msg


class FreckletBuildException(FrklException):
    def __init__(self, frecklet, msg, solution=None, reason=None, references=None):

        self.frecklet = frecklet
        super(FreckletBuildException, self).__init__(
            msg, solution=solution, reason=reason, references=references
        )


class InvalidFreckletException(FrklException):
    def __init__(self, frecklet, parent_exception, frecklet_name=None):

        self.frecklet = frecklet
        self.parent_exception = parent_exception

        if frecklet_name is None:
            if self.frecklet is not None:
                self.frecklet_name = self.frecklet.id
            else:
                self.frecklet_name = None
        else:
            self.frecklet_name = frecklet_name

        if self.frecklet_name is None:
            msg = "Invalid or missing frecklet"
        else:
            msg = "Invalid or missing frecklet: '{}'.".format(self.frecklet_name)

        reason = None
        if self.frecklet_name is not None:
            solution = "Check '{}' is a frecklet in any of the repositories of this context, or is a local file. In case you provided a yaml/json/toml string, check it's syntax.\n\nIf the frecklet was created dynamically, check the upstream adapter whether there was an error.".format(
                frecklet_name
            )
        else:
            solution = "Check frecklet is in any of the repositories of this context, or is a local file. In case you provided a yaml/json/toml string, check it's syntax.\n\nIf the frecklet was created dynamically, check the upstream adapter whether there was an error.".format(
                frecklet_name
            )
        references = {"frecklet documentation": "https://freckles.io/doc/frecklets"}
        super(InvalidFreckletException, self).__init__(
            msg, solution=solution, reason=reason, references=references
        )


class FreckletException(FrklException):
    def __init__(self, frecklet, parent_exception, frecklet_name):
        """

        Args:
            frecklet:
            parent_exception:
            frecklet_name: optional frecklet name a command was called with
        """

        self.frecklet = frecklet
        self.parent_exception = parent_exception
        if frecklet_name is not None:
            self.frecklet_name = frecklet_name
        elif frecklet is not None:
            self.frecklet_name = frecklet.id
        else:
            self.frecklet_name = "n/a"

        msg = "Can't process frecklet: '{}'".format(self.frecklet_name)
        if isinstance(parent_exception, TingException):

            if len(parent_exception.attribute_chain) == 1:
                reason = "Error when processing frecklet property:\n"
            else:
                reason = "Error when processing frecklet properties:\n"
            for index, attr in enumerate(parent_exception.attribute_chain):

                padding = "  " * (index + 1)
                reason = reason + "\n{}-> {}".format(padding, attr)

            reason = reason + ": {}".format(parent_exception.root_exc)

            if hasattr(parent_exception.root_exc, "solution"):
                solution = parent_exception.root_exc.solution
            else:
                solution = "Check format of frecklet '{}'.".format(
                    parent_exception.ting.id
                )
            if hasattr(parent_exception.root_exc, "references"):
                references = parent_exception.root_exc.references
            else:
                references = {
                    "frecklet documentation": "https://freckles.io/doc/frecklets"
                }
        elif isinstance(parent_exception, TemplateSyntaxError):

            reason = "Template syntax error: {}".format(str(parent_exception))
            solution = "Check format of frecklet '{}' (probably line {}):\n\n".format(
                frecklet.id, parent_exception.lineno
            )
            solution = solution + reindent(parent_exception.source, 4, line_nrs=1)
            references = {
                "frecklet documentation": "https://freckles.io/doc/frecklets",
                "jinja2 documentation": "http://jinja.pocoo.org/docs",
            }

        else:
            if self.frecklet_name == "n/a":
                solution = "Check format of frecklets. Can't say which ones, too little information."
            else:
                solution = "Check format of frecklet '{}' and all of its childs.".format(
                    self.frecklet_name
                )
            references = {"frecklet documentation": "https://freckles.io/doc/frecklets"}
            reason = None

        super(FreckletException, self).__init__(
            msg, solution=solution, reason=reason, references=references
        )


class FrecklesPermissionException(FrklException):
    def __init__(
        self, key=None, msg=None, solution=None, reason=None, addition_references=None
    ):

        if not msg:
            if not key:
                message = "Access to context config key denied."
            else:
                message = "Access to context config key '{}' denied.".format(key)
        else:
            message = msg

        if solution is None:
            solution = "Adjust configuration to allow permissions to this key"

        references = {
            "freckles configuration documentation": "https://freckles.io/doc/configuration"
        }
        if addition_references:
            references.update(addition_references)

        super(FrecklesPermissionException, self).__init__(
            message, solution=solution, reason=reason, references=references
        )
        self.key = key
        self.msg = msg


class FrecklesUnlockException(FrklException):
    def __init__(self, message):

        if not message:
            message = "Access to context config denied."

        solution = "Unlock freckles configuration with: 'freckles context unlock'"
        references = {
            "freckles configuration documentation": "https://freckles.io/doc/configuration"
        }

        super(FrecklesUnlockException, self).__init__(
            message,
            solution=solution,
            references=references,
            reason="freckles config not unlocked.",
        )
