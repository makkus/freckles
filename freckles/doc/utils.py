# -*- coding: utf-8 -*-

from plumbum import local


def get_frecklecute_help_text():

    command = "frecklecute"
    args = "--help"
    cmd = local[command]

    rc, stdout, stderr = cmd.run(args, retcode=None)

    return stdout
