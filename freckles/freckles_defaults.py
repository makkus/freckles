from nsbl import defaults
import os

SUPPORTED_OUTPUT_FORMATS = ["default", "ansible", "skippy", "verbose", "default_full"]

defaults.DEFAULT_ROLES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_role_repo")
DEFAULT_PROFILES_PATH = os.path.join(os.path.dirname(__file__), "external", "default_profile_repo")
DEFAULT_FRECKLECUTABLES_PATH = os.path.join(os.path.dirname(__file__), "external", "frecklecutables")
DEFAULT_USER_PROFILES_PATH = os.path.join(os.path.expanduser("~"), ".freckles", "profiles")
DEFAULT_USER_ROLE_REPO_PATH = os.path.join(os.path.expanduser("~"), ".freckles", "trusted_roles")
DEFAULT_USER_FRECKLECUTABLES_PATH = os.path.join(os.path.expanduser("~"), ".freckles", "frecklecutables")

EXTRA_FRECKLES_PLUGINS = os.path.abspath(os.path.join(os.path.dirname(__file__), "external", "freckles_extra_plugins"))
#DEFAULT_IGNORE_STRINGS = ["pre-checking", "finding freckles", "processing freckles", "retrieving freckles", "calculating", "check required", "augmenting", "including ansible role", "checking for", "preparing profiles", "starting profile execution", "auto-detect package managers", "setting executable:"]
DEFAULT_IGNORE_STRINGS = []

DEFAULT_RUN_BASE_LOCATION = os.path.expanduser("~/.local/freckles/runs")
DEFAULT_RUN_SYMLINK_LOCATION = os.path.join(DEFAULT_RUN_BASE_LOCATION, "current")
DEFAULT_RUN_LOCATION = os.path.join(DEFAULT_RUN_BASE_LOCATION, "archive", "run")
DEFAULT_COMMUNITY_ROLES_REPO_PATH = os.path.join(os.path.expanduser("~"), ".local", "freckles", "community-roles")
DEFAULT_COMMUNITY_PROFILES_PATH = os.path.join(os.path.expanduser("~"), ".local", "freckles", "community-profiles")

DEFAULT_COMMUNITY_FRECKLECUTABLES_PATH = os.path.join(os.path.expanduser("~"), ".local", "freckles", "community-frecklecutables")
