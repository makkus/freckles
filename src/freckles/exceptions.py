# -*- coding: utf-8 -*-
import textwrap

import click
from colorama import Fore, Style
from six import string_types

from frutils import readable, reindent, get_terminal_size
from ting.exceptions import TingException


def output_to_terminal(line, nl=True, no_output=False):

    if no_output:
        return

    click.echo(line.encode("utf-8"), nl=nl)


class FrecklesException(Exception):
    """Base exception class for nsbl."""

    def __init__(
        self, msg=None, solution=None, references=None, reason=None, parent=None, *args
    ):

        if isinstance(msg, Exception):
            if parent is None:
                parent = msg
            msg = str(msg)

        if msg is None:
            msg = "freckles internal error"

        super(FrecklesException, self).__init__(msg, *args)
        self.msg = msg
        self.solution = solution
        self.reason = reason
        self.references = references
        self.parent = parent

    @property
    def message(self):

        msg = self.msg + "\n"
        if self.reason:
            msg = msg + "\n  Reason: {}".format(self.reason)
        if self.solution:
            msg = msg + "\n  Solution: {}".format(self.solution)
        if self.references:
            if len(self.references) == 1:
                url = self.references[list(self.references.keys())[0]]
                msg = msg + "\n  Reference: {}".format(url)
            else:
                msg = msg + "\n  References\n"
                for k, v in self.references.items():
                    msg = msg + "\n    {}: {}".format(k, v)

        return msg.rstrip()

    def print_message(self):

        cols, _ = get_terminal_size()

        msg = Fore.RED + "Error: " + Style.RESET_ALL + self.msg
        for m in msg.split("\n"):
            m = textwrap.fill(m, width=cols, subsequent_indent="       ")
            output_to_terminal(m)
        click.echo()
        if self.reason:
            output_to_terminal(Style.BRIGHT + "  Reason: " + Style.RESET_ALL)
            msg = reindent(self.reason, 4)
            for m in msg.split("\n"):
                m = textwrap.fill(m, width=cols, subsequent_indent="    ")
                output_to_terminal(m)
            click.echo()
        if self.solution:
            output_to_terminal(Style.BRIGHT + "  Solution: " + Style.RESET_ALL)
            msg = reindent(self.solution, 4)
            for m in msg.split("\n"):
                m = textwrap.fill(m, width=cols, subsequent_indent="    ")
                output_to_terminal(m)
            click.echo()
        if self.references:
            if len(self.references) == 1:
                url = self.references[list(self.references.keys())[0]]
                output_to_terminal(
                    Style.BRIGHT + "  Reference: " + Style.RESET_ALL + url
                )
            else:
                output_to_terminal(Style.BRIGHT + "  References:" + Style.RESET_ALL)
                for k, v in self.references.items():
                    output_to_terminal(
                        "    " + Style.DIM + k + ": " + Style.RESET_ALL + v
                    )

        click.echo()


class FrecklesConfigException(FrecklesException):
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


class FrecklesVarException(FrecklesException):
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


class FreckletBuildException(FrecklesException):
    def __init__(self, frecklet, msg, solution=None, reason=None, references=None):

        self.frecklet = frecklet
        super(FreckletBuildException, self).__init__(
            msg, solution=solution, reason=reason, references=references
        )


class InvalidFreckletException(FrecklesException):
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
            solution = "Check '{}' is a frecklet in any of the repositories of this context, or is a local file. In case you provided a yaml/json/toml string, check it's syntax.".format(
                frecklet_name
            )
        else:
            solution = "Check frecklet is in any of the repositories of this context, or is a local file. In case you provided a yaml/json/toml string, check it's syntax.".format(
                frecklet_name
            )
        references = {"frecklet documentation": "https://freckles.io/doc/frecklets"}
        super(InvalidFreckletException, self).__init__(
            msg, solution=solution, reason=reason, references=references
        )


class FreckletException(FrecklesException):
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


class FrecklesPermissionException(FrecklesException):
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


class FrecklesUnlockException(FrecklesException):
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
