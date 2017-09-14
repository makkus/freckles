from nsbl.defaults import calculate_role_repos, calculate_task_descs
from nsbl.nsbl import Nsbl, NsblRunner


class FrecklesTasks(object):
    def __init__(self, config, role_repos=None, task_descs=None, stdout_callback='nsbl_internal', target=None,
                 force=False):

        role_repos = calculate_role_repos(role_repos, use_default_roles=True)
        task_descs = calculate_task_descs(task_descs, role_repos)

        if not target:
            self.target = "/tmp/test_env"
        else:
            self.target = target

        self.force = force
        self.stdout_callback = stdout_callback

        self.nsbl = Nsbl.create(config, role_repos, task_descs, wrap_into_localhost_env=True)

        self.runner = NsblRunner(self.nsbl)

    def run(self):

        self.runner.run(self.target, self.force, "", self.stdout_callback)
