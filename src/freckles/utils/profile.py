#!/home/markus/.virtualenvs/frkl/bin/python2.7
# -*- coding: utf-8 -*-
# EASY-INSTALL-ENTRY-SCRIPT: 'freckles','console_scripts','frecklecute'

__requires__ = "freckles"
import re
import sys

from pkg_resources import load_entry_point

if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\.pyw?|\.exe)?$", "", sys.argv[0])
    sys.exit(load_entry_point("freckles-cli", "console_scripts", "frecklecute")())
