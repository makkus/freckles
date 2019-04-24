# -*- coding: utf-8 -*-
import textwrap

import click
from colorama import Fore, Style
from six import string_types

from frutils import readable, reindent, get_terminal_size


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
        msg = textwrap.fill(msg, width=cols, subsequent_indent="       ")
        click.echo(msg)
        click.echo()
        if self.reason:
            click.echo(Style.BRIGHT + "  Reason: " + Style.RESET_ALL)
            msg = reindent(self.reason, 4)
            msg = textwrap.fill(msg, width=cols, subsequent_indent="    ")
            click.echo(msg)
            click.echo()
        if self.solution:
            click.echo(Style.BRIGHT + "  Solution: " + Style.RESET_ALL)
            msg = reindent(self.solution, 4)
            msg = textwrap.fill(msg, width=cols, subsequent_indent="    ")
            click.echo(msg)
            click.echo()
        if self.references:
            if len(self.references) == 1:
                url = self.references[list(self.references.keys())[0]]
                click.echo(Style.BRIGHT + "  Reference: " + Style.RESET_ALL + url)
            else:
                click.echo(Style.BRIGHT + "  References:" + Style.RESET_ALL)
                for k, v in self.references.items():
                    click.echo("    " + Style.DIM + k + ": " + Style.RESET_ALL + v)

        click.echo()


class FrecklesConfigException(FrecklesException):
    def __init__(
        self, keys=None, msg=None, solution=None, reason=None, addition_references=None
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

        references = {
            "freckles configuration documentation": "https://freckles.io/doc/configuration"
        }
        if addition_references:
            references.update(addition_references)

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
        error=None,
        task_path=None,
        vars=None,
        task=None,
    ):
        super(FrecklesVarException, self).__init__(msg=message)

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
