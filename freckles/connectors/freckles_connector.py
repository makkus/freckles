# -*- coding: utf-8 -*-

from freckles.freckles_runner import FrecklesRunner

from .connectors import FrecklesConnector


class FrecklesChildConnector(FrecklesConnector):
    def __init__(self, connector_name="freckles"):

        super(FrecklesChildConnector, self).__init__(connector_name=connector_name)

        self.require_absolute_path = None
        self.context = None

    def set_context(self, context):

        self.context = context

    def get_frecklet_metadata(self, name):

        return None

    def get_supported_task_types(self):

        result = ["frecklecutable"]
        return result

    def run(self, tasklist, config=None, result_callback=None, output_callback=None):

        callback_adapter = FrecklesCallbackAdapter(
            result_callback=result_callback, output_callback=output_callback
        )
        for task in tasklist:

            command = task["task"]["command"]
            vars = task.get("vars", {})
            runner = FrecklesRunner(self.context, is_sub_task=True)
            runner.load_frecklecutable_from_name_or_file(command)
            callback_adapter.add_command_started(task)
            result_dict = runner.run(vars)
            callback_adapter.add_command_result(result_dict)

    def get_cnf_schema(self):

        return {}

    def get_indexes(self):

        return None


class FrecklesCallbackAdapter(object):
    def __init__(self, result_callback=None, output_callback=None):

        self.result_callback = result_callback
        self.output_callback = output_callback

    #
    # def execution_started(self):
    #
    #     self.output_callback.execution_started()
    #
    # def execution_finished(self):
    #
    #     self.output_callback.execution_finished()

    def add_command_started(self, task):

        details = {}
        # details["task_id"] = task["task"]["_task_id"]
        details["name"] = task["task"]["name"]
        self.output_callback.task_started(details)

    def add_command_result(self, result_dict):

        success = True

        for tl_id, results in result_dict.items():
            result_vars = results["result"]
            self.result_callback.add_result(result_vars)

            return_code = results["run_properties"]["return_code"]
            if return_code != 0:
                success = False

        self.output_callback.task_finished(success, {})
