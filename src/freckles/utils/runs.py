# -*- coding: utf-8 -*-
import abc
import csv
import io
import json
import os
import threading

import click
import fasteners
import six
from colorama import Fore
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from freckles.defaults import FRECKLES_RUN_LOG_FILE_PATH
from frutils.exceptions import FrklException


def convert_log_file_row(row):

    data = {}
    data["uuid"] = row[0]
    data["run_alias"] = row[1]
    data["frecklet_name"] = row[2]
    data["adapter"] = row[3]
    data["env_dir"] = row[4]
    data["state"] = row[5]
    data["timestamp"] = row[6]

    return data


def get_current_runs():

    if not os.path.exists(FRECKLES_RUN_LOG_FILE_PATH):
        return {}
    content = {}
    with io.open(FRECKLES_RUN_LOG_FILE_PATH, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            data = convert_log_file_row(row)
            if data["state"] == "started":
                content[data["uuid"]] = data
            else:
                if data["uuid"] in content:
                    content.pop(data["uuid"])

    return content


class RunWatchManager(object):
    def __init__(self, *run_watchers):

        self._run_watchers = run_watchers

        self._lock = threading.Lock()
        self._current_runs = None

        self._runs_event_handler = FrecklesRunsListFileHandler(
            callback=self.update_current_runs
        )
        self._runs_observer = None

        self._aliases = {}
        self._unique_index = {}

    def start(self):

        current_runs = get_current_runs()

        self.update_current_runs(current_runs)
        self._runs_observer = watch_runs(self._runs_event_handler)

    def stop(self):

        for watcher in self._run_watchers:
            watcher.stop()

        self._runs_observer.stop()

    def join_runs_watch(self):

        self._runs_observer.join()

    @fasteners.locked
    def update_current_runs(self, current_runs):

        if self._current_runs:
            old_current = self._current_runs
        else:
            old_current = {}
        self._current_runs = current_runs

        for uuid, r in self._current_runs.items():

            if uuid in old_current.keys():
                continue

            index = 0
            while index in self._unique_index.values():
                index = index + 1

            alias = r["run_alias"]
            if alias.startswith("__dyn_"):
                alias = "no_name"
            elif os.path.sep in alias:
                alias = "...{}{}".format(os.path.sep, os.path.basename(alias))

            if alias not in self._aliases.keys():
                self._aliases[alias] = 1
                alias_new = alias
            else:
                current = self._aliases[alias]
                current = current + 1
                alias_new = "{}_{}".format(alias, current)
                self._aliases[alias] = current

            self.task_started(uuid=uuid, alias=alias_new, run_data=r, index=index)
            old_current[uuid] = r
            self._unique_index[uuid] = index

        remove = []
        for uuid, run_data in old_current.items():

            if uuid in self._current_runs.keys():
                continue

            remove.append(uuid)

        for r in remove:
            self.task_finished(r)
            self._unique_index.pop(r)

        if not self._current_runs:
            self._aliases = {}
            self._unique_index = {}

    def task_started(self, uuid, alias, run_data, index):

        for watcher in self._run_watchers:
            watcher.task_started(uuid=uuid, alias=alias, run_data=run_data, index=index)

    def task_finished(self, uuid):

        for watcher in self._run_watchers:
            watcher.task_finished(uuid=uuid)


class FrecklesLogFileHander(FileSystemEventHandler):
    def __init__(
        self,
        run_alias,
        watch_path=None,
        created_callback=None,
        callback=None,
        finished_callback=None,
        adapter_log=None,
        index=0,
    ):

        if adapter_log and watch_path:
            raise FrklException(
                msg="Can only watch either the adapter log, or a specific path."
            )

        if watch_path is None:
            watch_path = "run_log.json"

        if run_alias.startswith("__dyn_"):
            run_alias = "_no_name_"
        self._alias = run_alias
        self._index = index
        self._watch_path = watch_path
        self._created_callback = created_callback
        self._callback = callback
        self._finished_callback = finished_callback
        self._last_file_pos = 0
        self._adapter_log = adapter_log
        if not self._adapter_log:
            self._log_file = os.path.join(self._env_dir, self._watch_path)
        else:
            if self._adapter == "nsbl":
                self._log_file = os.path.join(
                    self._env_dir, "nsbl/logs/ansible_run_log"
                )
            else:
                raise FrklException(msg="Watching logs for adapter '{}' not supported.")
        self._watch_dir = os.path.dirname(self._log_file)

    def on_created(self, event):

        if not self._created_callback:
            return

            if event.src_path != self._log_file:
                return

        self._created_callback(event.src_path)

    def on_modified(self, event):

        if not self._callback:
            return

        if event.src_path != self._log_file:
            return

        if not os.path.exists(event.src_path):
            return []

        with io.open(event.src_path, "r", encoding="utf-8") as f:
            f.seek(self._last_file_pos)
            data = f.readlines()
            self._last_file_pos = f.tell()

        if not self._adapter_log:
            result = []
            for line in data:
                d = json.loads(line)
                result.append(d)
        else:
            result = data

        return self._callback(result)

    def on_deleted(self, event):

        if not self._finished_callback:
            return

        if event.src_path != self._log_file:
            return

        self._finished_callback()


@six.add_metaclass(abc.ABCMeta)
class FrecklesRunWatcher(object):
    @abc.abstractmethod
    def task_started(self, uuid, alias, run_data, index):
        pass

    @abc.abstractmethod
    def task_finished(self, uuid):
        pass

    @abc.abstractmethod
    def stop(self):
        pass


class FrecklesRunsLogTerminalOutput(FrecklesRunWatcher):
    def __init__(self, watch_path=None, adapter_log=False):

        if adapter_log and watch_path:
            raise FrklException(
                msg="Can only watch either the adapter log, or a specific path."
            )

        self._watch_path = watch_path
        self._adapter_log = adapter_log
        self._log_file_printers = {}

    def task_started(self, uuid, alias, run_data, index):

        fw = FrecklesRunLogTerminalOutput(
            alias,
            run_data,
            watch_path=self._watch_path,
            adapter_log=self._adapter_log,
            index=index,
        )
        self._log_file_printers[uuid] = fw

    def task_finished(self, uuid):

        fw = self._log_file_printers[uuid]
        fw.finished()
        self._log_file_printers.pop(uuid)

    def stop(self):

        for uuid in self._log_file_printers.keys():
            fw = self._log_file_printers[uuid]
            fw.finished(print_status=False)

        self._log_file_printers = {}


class FrecklesRunLogTerminalOutput(FrecklesLogFileHander):

    COLORS = [Fore.BLUE, Fore.MAGENTA, Fore.GREEN, Fore.CYAN, Fore.RED, Fore.YELLOW]

    def __init__(self, run_alias, run_data, watch_path=None, adapter_log=None, index=0):

        self._run_data = run_data
        self._uuid = self._run_data["uuid"]
        self._adapter = self._run_data["adapter"]
        self._env_dir = self._run_data["env_dir"]
        self._started = self._run_data["timestamp"]

        super(FrecklesRunLogTerminalOutput, self).__init__(
            run_alias=run_alias,
            watch_path=watch_path,
            callback=self.updated,
            finished_callback=self.finished,
            adapter_log=adapter_log,
            index=index,
        )

        self._observer = watch_log_file(self._watch_dir, self)
        self._finished = False

    def updated(self, data):

        if not self._adapter_log:
            self.updated_log(data)
        else:
            self.updated_adapter(data)

    def updated_adapter(self, data):

        color_index = len(FrecklesRunLogTerminalOutput.COLORS) % self._index
        color = FrecklesRunLogTerminalOutput.COLORS[color_index]
        reset = Fore.RESET

        for line in data:
            click.echo("{}{}: {}{}".format(color, self._alias, line, reset), nl=False)

    def updated_log(self, data):

        color_index = len(FrecklesRunLogTerminalOutput.COLORS) % self._index
        color = FrecklesRunLogTerminalOutput.COLORS[color_index]
        reset = Fore.RESET

        for d in data:
            level = d["level"]
            msg = d["msg"]
            finished = d["finished"]
            success = d.get("success", None)
            skipped = d.get("skipped", None)
            # changed = d.get("changed", None)
            # messages = d["messages"]
            error_messages = d["error_messages"]
            padding = "  " * level

            if not finished:
                click.echo(
                    "{}{}: {}- {}{}".format(color, self._alias, padding, msg, reset)
                )
            else:
                if success:
                    if skipped:
                        status = "skipped"
                    else:
                        status = "ok"
                click.echo(
                    "{}{}: {}- {}: {}{}".format(
                        color, self._alias, padding, msg, status, reset
                    )
                )
                if not success:
                    click.echo(
                        "{}{}      -> {}{}".format(
                            color, self._alias, error_messages, reset
                        )
                    )

    def finished(self, print_status=True):

        if not self._finished:
            self._finished = True
            if print_status:
                click.echo("{}: finished".format(self._alias))
            self._observer.stop()


class FrecklesRunsListFileHandler(FileSystemEventHandler):
    def __init__(self, callback):

        self._callback = callback

    def on_any_event(self, event):

        if event.src_path == FRECKLES_RUN_LOG_FILE_PATH or (
            hasattr(event, "dest_path")
            and event.dest_path == FRECKLES_RUN_LOG_FILE_PATH
        ):

            content = get_current_runs()
            self._callback(content)


def watch_runs(event_handler):

    observer = Observer()
    observer.schedule(
        event_handler, os.path.dirname(FRECKLES_RUN_LOG_FILE_PATH), recursive=False
    )
    observer.start()

    return observer


def watch_log_file(env_dir, event_handler):

    observer = Observer()
    observer.schedule(event_handler, env_dir, recursive=False)
    observer.start()

    return observer
