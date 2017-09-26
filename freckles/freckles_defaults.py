import os
import click
from nsbl import defaults

FRECKLE_MARKER_FILE_NAME = ".freckle"
SUPPORTED_OUTPUT_FORMATS = ["default", "ansible", "skippy", "verbose", "default_full"]

FRECKLES_DEFAULT_CONFIG_FOLDER = click.get_app_dir('freckles', force_posix=True)
FRECKLES_DEFAULT_CONFIG_FILE = os.path.join(FRECKLES_DEFAULT_CONFIG_FOLDER, FRECKLE_MARKER_FILE_NAME)

defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")
DEFAULT_ADAPTERS_PATH = os.path.join(os.path.dirname(__file__), "external", "default_adapter_repo")
DEFAULT_FRECKLECUTABLES_PATH = os.path.join(os.path.dirname(__file__), "external", "frecklecutables")

DEFAULT_USER_ADAPTERS_PATH = os.path.join(os.path.expanduser("~"), ".freckles", "adapters")
DEFAULT_USER_ROLE_REPO_PATH = os.path.join(os.path.expanduser("~"), ".freckles", "roles")
DEFAULT_USER_FRECKLECUTABLES_PATH = os.path.join(os.path.expanduser("~"), ".freckles", "frecklecutables")

DEFAULT_LOCAL_REPO_PATH_BASE = os.path.join(os.path.expanduser("~"), ".local", "freckles", "repos")
DEFAULT_FRECKLES_IO_ROLES_REPO_PATH = os.path.join(DEFAULT_LOCAL_REPO_PATH_BASE, "freckles_io_roles")
DEFAULT_FRECKLES_IO_ADAPTERS_PATH = os.path.join(DEFAULT_LOCAL_REPO_PATH_BASE, "freckles_io_adapters")
DEFAULT_FRECKLES_IO_FRECKLECUTABLES_PATH = os.path.join(DEFAULT_LOCAL_REPO_PATH_BASE, "freckles_io_frecklecutables")

DEFAULT_FRECKLES_IO_ROLES_REPO_URL = "https://github.com/freckles-io/roles.git"
DEFAULT_FRECKLES_IO_ADAPTERS_REPO_URL = "https://github.com/freckles-io/adapters.git"
DEFAULT_FRECKLES_IO_FRECKLECUTABLES_REPO_URL = "https://github.com/freckles-io/frecklecutables.git"

ARK_REPO_PATH = os.path.join(DEFAULT_LOCAL_REPO_PATH_BASE, "ark")
ARK_REPO_URL = "https://github.com/freckles-io/ark.git"

EXTRA_FRECKLES_PLUGINS = os.path.abspath(os.path.join(os.path.dirname(__file__), "external", "freckles_extra_plugins"))
# DEFAULT_IGNORE_STRINGS = ["pre-checking", "finding freckles", "processing freckles", "retrieving freckles", "calculating", "check required", "augmenting", "including ansible role", "checking for", "preparing profiles", "starting profile execution", "auto-detect package managers", "setting executable:"]
DEFAULT_IGNORE_STRINGS = []

DEFAULT_RUN_BASE_LOCATION = os.path.expanduser("~/.local/freckles/runs")
DEFAULT_RUN_SYMLINK_LOCATION = os.path.join(DEFAULT_RUN_BASE_LOCATION, "current")
DEFAULT_RUN_LOCATION = os.path.join(DEFAULT_RUN_BASE_LOCATION, "archive", "run")

DEFAULT_EXCLUDE_DIRS = [".git", ".tox", ".cache"]
ADAPTER_MARKER_EXTENSION = "freckle-adapter"
ADAPTER_TASKS_EXTENSION = "freckle-tasks"
ADAPTER_INIT_EXTENSION = "freckle-init"

DEFAULT_REPOS = {
    "default": {"roles": [(None, defaults.DEFAULT_ROLES_PATH)],
                "adapters": [(None, DEFAULT_ADAPTERS_PATH)],
                "frecklecutables": [(None, DEFAULT_FRECKLECUTABLES_PATH)]},
    "user": {"roles": [(None, DEFAULT_USER_ROLE_REPO_PATH)],
             "adapters": [(None, DEFAULT_USER_ADAPTERS_PATH)],
             "frecklecutables": [(None, DEFAULT_USER_FRECKLECUTABLES_PATH)]},
    "freckles_io": {"roles": [(DEFAULT_FRECKLES_IO_ROLES_REPO_URL, DEFAULT_FRECKLES_IO_ROLES_REPO_PATH)],
                  "adapters": [(DEFAULT_FRECKLES_IO_ADAPTERS_REPO_URL, DEFAULT_FRECKLES_IO_ADAPTERS_PATH)],
                  "frecklecutables": [
                      (DEFAULT_FRECKLES_IO_FRECKLECUTABLES_REPO_URL, DEFAULT_FRECKLES_IO_FRECKLECUTABLES_PATH)]
                  },
    "ark": {"roles": [(ARK_REPO_URL, ARK_REPO_PATH)],
            "adapters": [(None, ARK_REPO_PATH)],
            "frecklecutables": [(None, ARK_REPO_PATH)]
            }
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

def get_default_repo(repo_name):
    repo = DEFAULT_REPOS.get(repo_name, None)
    return repo

    # default = {"roles": (repo_name, repo_name), "adapters": (repo_name, repo_name), "frecklecutables": (repo_name_repo_name)}
