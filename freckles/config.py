from __future__ import (absolute_import, division, print_function)

import click

from .freckles_defaults import *

try:
    set
except NameError:
    from sets import Set as set

import yaml


class FrecklesConfig(object):
    def __init__(self):

        self.config_file = os.path.join(click.get_app_dir('freckles', force_posix=True), 'config.yml')
        if os.path.exists(self.config_file):
            with open(self.config_file) as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}

        self.trusted_repos = self.config.get("trusted-repos", ["default", "user"])
        self.trusted_urls = self.config.get("trusted-urls",
                                            ["https://github.com/makkus", "https:/github.com/freckles-io"])
        self.task_descs = self.config.get("task-descs", [])
