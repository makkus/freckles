# -*- coding: utf-8 -*-
import io
import logging
import os
import stat
import sys

from jinja2 import Environment, FileSystemLoader
from plumbum import SshMachine, local

from freckles.defaults import MODULE_FOLDER
from freckles.exceptions import FrecklesConfigException

log = logging.getLogger("freckles")


class ShellRunner(object):
    def __init__(self):

        if not hasattr(sys, "frozen"):
            template_dir = os.path.join(MODULE_FOLDER, "templates", "shell_adapter")
        else:
            template_dir = os.path.join(
                sys._MEIPASS, "freckles", "templates", "shell_adapter"
            )

        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def render_environment(self, run_env_dir, tasklist, skip_exodus=True):

        # making the run environment user accessible only
        os.chmod(run_env_dir, 0o0700)

        result = {"run_dir": run_env_dir, "run_dir_name": os.path.basename(run_env_dir)}

        working_dir = os.path.join(run_env_dir, "working_dir")
        os.mkdir(working_dir)
        executables_dir = os.path.join(run_env_dir, "executables")
        os.mkdir(executables_dir)
        result["working_dir"] = working_dir
        result["executables_dir"] = executables_dir

        log.debug("Creating shell script from template...")
        template = self.jinja_env.get_template("shell_runner.sh.j2")

        extra_paths = []
        functions = {}

        all_exodus_binaries = []
        for task in tasklist:
            for f_name, f_details in task.get("files", {}).items():

                target = os.path.join(executables_dir, f_name)
                f_type = f_details["type"]

                if f_type == "string_content":

                    content = f_details["content"]
                    with io.open(target, "w", encoding="utf-8") as f:
                        f.write(content)

                    # make executable
                    st = os.stat(target)
                    os.chmod(target, st.st_mode | stat.S_IEXEC)

                elif f_type == "exodus-binary":

                    name = f_details["binary-name"]
                    if name not in all_exodus_binaries:
                        all_exodus_binaries.append(name)

                else:
                    raise FrecklesConfigException(
                        "Unknown external file type: {}".format(f_type)
                    )

            for f_name, f_details in task.get("functions", {}).items():

                if f_name in functions.keys():
                    log.warning("Duplicate function: {}".format(f_name))

                functions[f_name] = f_details

        if not skip_exodus:
            exodus_bundle = os.path.join(run_env_dir, "exodus-binaries", "bundle.sh")
            exodus_cmd = local["exodus"]
            exodus_args = ["-o", exodus_bundle]
            exodus_args.append(all_exodus_binaries)
            rc, stdout, stderr = exodus_cmd.run(exodus_args)

        result["tasklist"] = tasklist

        repl_dict = {
            "extra_paths": extra_paths,
            "functions": functions,
            "tasklist": tasklist,
        }
        rendered = template.render(repl_dict)

        run_script = os.path.join(run_env_dir, "run.sh")
        with io.open(run_script, "w", encoding="utf-8") as rs:
            rs.write(rendered)

        # make run.sh executable
        st = os.stat(run_script)
        os.chmod(run_script, st.st_mode | stat.S_IEXEC)
        result["run_script"] = run_script

        return result

    def run(
        self,
        run_properties,
        run_cnf,
        # output_callback,
        result_callback,
        parent_task,
        # callback_adapter,
        delete_env=False,
    ):

        # run_dir = run_properties["run_dir"]

        hostname = run_cnf.get("host")
        connection_type = run_cnf.get("connection_type", None)
        if connection_type is None:
            if hostname in ["localhost", "127.0.0.1"]:
                connection_type = "local"
            else:
                connection_type = "ssh"

        if connection_type == "ssh":

            remote = True
            ssh_key = run_cnf.get("ssh_key")
            user = run_cnf.get("user")
            host_ip = run_cnf.get("host_ip")
            ssh_port = run_cnf.get("ssh_port")

            # otherwise we run into problems with Vagrant
            if host_ip:
                h = host_ip
            else:
                h = hostname

            machine = SshMachine(h, port=ssh_port, user=user, keyfile=ssh_key)
        else:
            remote = False
            machine = local

        no_run = run_cnf.get("no_run")

        if no_run:
            return run_properties

        if remote:
            raise Exception("Not implemented yet")
            # copy execution environment
            # td = TaskDetail(
            #     "uploading execution environment", task_type="upload", task_parent=td
            # )
            # upload_task = td.add_subtask(
            #     "uploading execution environment", category="upload"
            # )
            # machine.upload(run_dir, "/tmp")
            # upload_task.finish(success=True, changed=True, skipped=False)
            # run_script = os.path.join("/tmp", run_properties["run.sh"])
        else:
            run_script = run_properties["run_script"]

        machine.env["ECHO_TASK_START"] = "true"
        machine.env["ECHO_TASK_FINISHED"] = "true"
        cmd = machine["bash"]

        # rc, stdout, stderr = cmd.run([run_script], retcode=None)
        current_task = parent_task
        popen = cmd.popen(run_script)

        current_task_stdout = []
        current_task_stderr = []
        current_task_id = -1

        log.debug("Reading command output...")
        for line in popen.iter_lines():

            log.debug(line)
            # print(line)
            stdout = line[0]
            if stdout:
                if stdout.startswith("STARTING_TASK["):
                    index = stdout.index("]")
                    task_id = int(stdout[14:index])
                    current_msg = stdout[index + 2 :].strip()  # noqa
                    # print(stdout)
                    if task_id > current_task_id:
                        # print("starting: {}".format(msg))
                        # td = TaskDetail(
                        #     task_name=current_msg,
                        #     task_type="script-command",
                        #     task_parent=current_task,
                        #     task_title=current_msg,
                        #     freckles_task_id=task_id,
                        # )
                        current_task = current_task.add_subtask(
                            task_name=current_msg,
                            category="script-command",
                            reference=task_id,
                        )
                        # output_callback.task_started(td)
                        current_task_id = task_id

                elif stdout.startswith("FINISHED_TASK["):
                    # print("finished")
                    index = stdout.index("]")
                    task_id = int(stdout[14:index])
                    rc = int(stdout[index + 2 :])  # noqa
                    success = rc == 0
                    stdout = "\n".join(current_task_stdout)
                    stderr = "\n".join(current_task_stderr)
                    # msg = ""
                    # if stdout and not stderr:
                    #     msg = "stdout:\n{}".format(stdout)
                    # elif stderr and not stdout:
                    #     msg = "stderr:\n{}".format(stderr)
                    # elif stdout and stderr:
                    #     msg = "stdout:\n{}\nstderr:\n{}".format(stdout, stderr)

                    current_task = current_task.finish(
                        success=success,
                        changed=True,
                        skipped=False,
                        msg=stdout,
                        error_msg=stderr,
                    )
                    # output_callback.task_finished(
                    #     current_task,
                    #     success=success,
                    #     changed=True,
                    #     skipped=False,
                    #     msg=msg,
                    # )
                    current_task_stdout = []
                    current_task_stderr = []
                    # current_task = current_task.task_parent
                    current_msg = None
                else:
                    if stdout and current_task_id is not None:
                        current_task_stdout.append(stdout)

            stderr = line[1]
            if stderr:
                current_task_stderr.append(stderr)

        rc = popen._proc.returncode

        run_properties["return_code"] = rc
        run_properties["signal_status"] = -1

        if remote:
            raise Exception("not implemented yet")
            # if delete_env:
            #     td = TaskDetail(
            #         "deleting execution environment",
            #         task_type="delete",
            #         task_parent=current_task,
            #     )
            #     task_
            #     output_callback.task_started(td)
            #     delete = machine["rm"]
            #     rc, stdout, stderr = delete.run(
            #         ["-r", os.path.join("/tmp", run_properties["env_dir_name"])]
            #     )
            #     success = rc == 0
            #     output_callback.register_task_finished(td, success=success)
            # machine.close()

        return run_properties
