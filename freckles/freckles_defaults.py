import os
import click
from nsbl import defaults
from frkl.frkl import PLACEHOLDER

FRECKLE_MARKER_FILE_NAME = ".freckle"
SUPPORTED_OUTPUT_FORMATS = ["default", "ansible", "skippy", "verbose", "default_full"]

FRECKLES_DEFAULT_CONFIG_FOLDER = click.get_app_dir('freckles', force_posix=True)
FRECKLES_DEFAULT_CONFIG_FILE = os.path.join(FRECKLES_DEFAULT_CONFIG_FOLDER, FRECKLE_MARKER_FILE_NAME)

defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")
DEFAULT_ADAPTERS_PATH = os.path.join(os.path.dirname(__file__), "external", "default_adapter_repo")
DEFAULT_FRECKLECUTABLES_PATH = os.path.join(os.path.dirname(__file__), "external", "frecklecutables")
DEFAULT_BLUEPRINTS_PATH = os.path.join(os.path.dirname(__file__), "external", "blueprints")

DEFAULT_USER_ADAPTERS_PATH = os.path.join(os.path.expanduser("~"), ".freckles", "adapters")
DEFAULT_USER_ROLE_REPO_PATH = os.path.join(os.path.expanduser("~"), ".freckles", "roles")
DEFAULT_USER_FRECKLECUTABLES_PATH = os.path.join(os.path.expanduser("~"), ".freckles", "frecklecutables")
DEFAULT_USER_BLUEPRINTS_PATH = os.path.join(os.path.expanduser("~"), ".freckles", "blueprints")

DEFAULT_LOCAL_FRECKLES_BASE = os.path.join(os.path.expanduser("~"), ".local", "freckles")
DEFAULT_LOCAL_FRECKLES_BOX_BASICS_MARKER = os.path.join(os.path.expanduser("~"), ".local", "freckles", ".box_basics_run_successfully")
DEFAULT_LOCAL_REPO_PATH_BASE = os.path.join(os.path.expanduser("~"), ".local", "freckles", "repos")
DEFAULT_FRECKLES_IO_ROLES_REPO_PATH = os.path.join(DEFAULT_LOCAL_REPO_PATH_BASE, "freckles_io_extra")
DEFAULT_FRECKLES_IO_ADAPTERS_PATH = os.path.join(DEFAULT_LOCAL_REPO_PATH_BASE, "freckles_io_adapters")
DEFAULT_FRECKLES_IO_FRECKLECUTABLES_PATH = os.path.join(DEFAULT_LOCAL_REPO_PATH_BASE, "freckles_io_frecklecutables")
DEFAULT_FRECKLES_IO_BLUEPRINTS_PATH = os.path.join(DEFAULT_LOCAL_REPO_PATH_BASE, "freckles_io_blueprints")

DEFAULT_FRECKLES_IO_ROLES_REPO_URL = "https://github.com/freckles-io/extra.git"
DEFAULT_FRECKLES_IO_ADAPTERS_REPO_URL = "https://github.com/freckles-io/adapters.git"
DEFAULT_FRECKLES_IO_FRECKLECUTABLES_REPO_URL = "https://github.com/freckles-io/frecklecutables.git"
DEFAULT_FRECKLES_IO_BLUEPRINTS_REPO_URL = "https://github.com/freckles-io/blueprints.git"

ARK_REPO_PATH = os.path.join(DEFAULT_LOCAL_REPO_PATH_BASE, "ark")
ARK_REPO_URL = "https://github.com/freckles-io/ark.git"

TESTING_REPO_PATH = os.path.join(DEFAULT_LOCAL_REPO_PATH_BASE, "testing")
TESTING_REPO_URL = "https://github.com/freckles-io/testing.git"

EXTRA_FRECKLES_PLUGINS = os.path.abspath(os.path.join(os.path.dirname(__file__), "external", "freckles_extra_plugins"))
# DEFAULT_IGNORE_STRINGS = ["pre-checking", "finding freckles", "processing freckles", "retrieving freckles", "calculating", "check required", "augmenting", "including ansible role", "checking for", "preparing profiles", "starting profile execution", "auto-detect package managers", "setting executable:"]
DEFAULT_IGNORE_STRINGS = []

DEFAULT_RUN_BASE_LOCATION = os.path.expanduser("~/.local/freckles/runs")
DEFAULT_RUN_SYMLINK_LOCATION = os.path.join(DEFAULT_RUN_BASE_LOCATION, "current")
DEFAULT_RUN_LOCATION = os.path.join(DEFAULT_RUN_BASE_LOCATION, "archive", "run")

DEFAULT_EXCLUDE_DIRS = [".git", ".tox", ".cache"]
ADAPTER_MARKER_EXTENSION = "adapter.freckle"
ADAPTER_TASKS_EXTENSION = "tasks.adapter.freckle"
ADAPTER_INIT_EXTENSION = "init.adapter.freckle"

BLUEPRINT_URL_PREFIX = "blueprint:"
BLUEPRINT_MARKER_EXTENSION = "blueprint.freckle"

DEFAULT_FRECKLE_TARGET_MARKER = "__auto__"

DEFAULT_FRECKELIZE_PROFILE_PRIORITY = 100
FRECKELIZE_PROFILE_ACTIVE_KEY = "freckle_profile_active"

DEFAULT_REPOS = {
    "default": {"roles": [(None, defaults.DEFAULT_ROLES_PATH)],
                "adapters": [(None, DEFAULT_ADAPTERS_PATH)],
                "frecklecutables": [(None, DEFAULT_FRECKLECUTABLES_PATH)],
                "blueprints": [(None, DEFAULT_BLUEPRINTS_PATH)]
    },
    "user": {"roles": [(None, DEFAULT_USER_ROLE_REPO_PATH)],
             "adapters": [(None, DEFAULT_USER_ADAPTERS_PATH)],
             "frecklecutables": [(None, DEFAULT_USER_FRECKLECUTABLES_PATH)],
             "blueprints": [(None, DEFAULT_USER_BLUEPRINTS_PATH)]
    },
    # "freckles-io": {"roles": [(DEFAULT_FRECKLES_IO_ROLES_REPO_URL, DEFAULT_FRECKLES_IO_ROLES_REPO_PATH)],
                  # "adapters": [
                      # (DEFAULT_FRECKLES_IO_ADAPTERS_REPO_URL, DEFAULT_FRECKLES_IO_ADAPTERS_PATH),
                      # (DEFAULT_FRECKLES_IO_ROLES_REPO_URL, DEFAULT_FRECKLES_IO_ROLES_REPO_PATH)
                  # ],
                  # "frecklecutables": [
                      # (DEFAULT_FRECKLES_IO_FRECKLECUTABLES_REPO_URL, DEFAULT_FRECKLES_IO_FRECKLECUTABLES_PATH)],
                  # "blueprints": [
                      # (DEFAULT_FRECKLES_IO_BLUEPRINTS_REPO_URL, DEFAULT_FRECKLES_IO_BLUEPRINTS_PATH),
                      # (DEFAULT_FRECKLES_IO_ROLES_REPO_URL, DEFAULT_FRECKLES_IO_ROLES_REPO_PATH)
                  # ],
                  # },
    "testing": {"roles": [(TESTING_REPO_URL, TESTING_REPO_PATH)],
            "adapters": [(None, TESTING_REPO_PATH)],
            "frecklecutables": [(None, TESTING_REPO_PATH)],
            "blueprints": [(None, TESTING_REPO_PATH)]
            },
    "ark": {"roles": [(ARK_REPO_URL, ARK_REPO_PATH)],
            "adapters": [(None, ARK_REPO_PATH)],
            "frecklecutables": [(None, ARK_REPO_PATH)],
            "blueprints": [(None, ARK_REPO_PATH)]
            }
}

# url abbreviations
DEFAULT_ABBREVIATIONS = {
    'gh':
        ["https://github.com/", PLACEHOLDER, "/", PLACEHOLDER, ".git"],
    'bb': ["https://bitbucket.org/", PLACEHOLDER, "/", PLACEHOLDER, ".git"],
    'frkl': ["https://github.com/freckles-io/", PLACEHOLDER, ".git"]
}


# .freckle (raw) format
DEFAULT_PROFILE_VAR_FORMAT = {"child_marker": "profiles",
                              "default_leaf": "profile",
                              "default_leaf_key": "name",
                              "key_move_map": {'*': "vars"}}

# .freckle format
DEFAULT_VAR_FORMAT = {"child_marker": "childs",
                      "default_leaf": "vars",
                      "default_leaf_key": "name",
                      "key_move_map": {'*': "vars"}}

# .freckle package format
DEFAULT_PACKAGE_FORMAT = {"child_marker": "packages",
                          "default_leaf": "vars",
                          "default_leaf_key": "name",
                           "key_move_map": {'*': "vars"}}

DEFAULT_FRECKLES_COMMAND_FORMAT = {"child_marker": "commands",
                                   "default_leaf": "command",
                                   "default_leaf_key": "name",
                                   "key_move_map": {'*': "vars"}}

# def get_default_repo(repo_name):
    # repo = DEFAULT_REPOS.get(repo_name, None)
    # return repo

    # default = {"roles": (repo_name, repo_name), "adapters": (repo_name, repo_name), "frecklecutables": (repo_name_repo_name)}
