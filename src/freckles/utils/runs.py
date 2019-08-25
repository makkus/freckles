# -*- coding: utf-8 -*-
import abc
import csv
import io
import json
import logging
import os
import threading
import time
from collections import OrderedDict

import click
import fasteners
import psutil
import six
from colorama import Fore
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from freckles.defaults import (
    FRECKLES_RUN_LOG_FILE_PATH,
    FRECKLES_RUN_LOG_FILE_LOCK,
    FRECKLES_LAST_RUN_FILE_PATH,
)
from frutils.exceptions import FrklException

run_log_lock = threading.Lock()


log = logging.getLogger("freckles")


def convert_log_file_row(row):

    data = {}
    data["uuid"] = row[0]
    data["run_alias"] = row[1]
    data["frecklet_name"] = row[2]
    data["adapter"] = row[3]
    data["env_dir"] = row[4]
    data["state"] = row[5]
    data["timestamp"] = float(row[6])
    data["pid"] = int(row[7])
    data["proc_name"] = row[8].strip()

    return data


def freckles_run_process_exists(run_data):

    if isinstance(run_data, int):
        pid = run_data
    else:
        pid = run_data["pid"]

    if pid < 0:
        return False

    running = psutil.pid_exists(pid)
    if not running:
        return False

    proc = psutil.Process(pid)

    if proc.name().strip() != run_data["proc_name"]:
        return False

    return True


# This should never be called manually, only once using the 'atexit' register method in freckles.py
@fasteners.interprocess_locked(path=FRECKLES_RUN_LOG_FILE_LOCK)
def clean_runs_log_file():

    try:
        with run_log_lock:

            with io.open(FRECKLES_RUN_LOG_FILE_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()

            result = []
            for line in lines:
                if not line.strip():
                    continue
                data = convert_log_file_row(line.split(","))
                if data["state"] != "started":
                    continue
                # if data["pid"] == os.getpid():
                #     continue
                if not freckles_run_process_exists(data):
                    continue

                result.append(line)

            with io.open(FRECKLES_RUN_LOG_FILE_PATH, "w", encoding="utf-8") as f:
                f.write("".join(result))

    except (Exception) as e:
        log.debug("Could not clean up runs log file: {}".format(e))


@fasteners.interprocess_locked(path=FRECKLES_RUN_LOG_FILE_LOCK)
def write_runs_log(properties, adapter_name, state):

    try:

        # currently, keeping logs is not supported
        # the cleanup function above needs to be adjusted for that
        keep_logs = False

        with run_log_lock:

            if state == "started":
                pid = os.getpid()
                proc_name = psutil.Process(pid).name()
            else:
                pid = -1
                proc_name = "-"

            if keep_logs:
                row = [
                    properties["uuid"],
                    properties["run_metadata"].get(
                        "run_alias", properties["frecklet_name"]
                    ),
                    properties["frecklet_name"],
                    adapter_name,
                    properties["env_dir"],
                    state,
                    time.time(),
                    pid,
                    proc_name,
                ]
                with io.open(
                    FRECKLES_LAST_RUN_FILE_PATH, "w", encoding="utf-8", buffering=1
                ) as f:
                    writer = csv.writer(f)
                    writer.writerow(row)

                with io.open(
                    FRECKLES_RUN_LOG_FILE_PATH, "a", encoding="utf-8", buffering=1
                ) as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
            else:
                if state == "started":
                    row = [
                        properties["uuid"],
                        properties["run_metadata"].get(
                            "run_alias", properties["frecklet_name"]
                        ),
                        properties["frecklet_name"],
                        adapter_name,
                        properties["env_dir"],
                        state,
                        time.time(),
                        pid,
                        proc_name,
                    ]
                    with io.open(
                        FRECKLES_RUN_LOG_FILE_PATH, "a", encoding="utf-8", buffering=1
                    ) as f:
                        writer = csv.writer(f)
                        writer.writerow(row)

                    with io.open(
                        FRECKLES_LAST_RUN_FILE_PATH, "w", encoding="utf-8", buffering=1
                    ) as f:
                        writer = csv.writer(f)
                        writer.writerow(row)
                else:
                    with open(FRECKLES_RUN_LOG_FILE_PATH, "r") as inp, open(
                        FRECKLES_RUN_LOG_FILE_PATH + ".tmp", "w", buffering=1
                    ) as out:
                        writer = csv.writer(out)
                        for row in csv.reader(inp):
                            if not row:
                                continue
                            if row[0] != properties["uuid"]:
                                writer.writerow(row)
                    os.rename(
                        FRECKLES_RUN_LOG_FILE_PATH + ".tmp", FRECKLES_RUN_LOG_FILE_PATH
                    )
    except (Exception) as e:
        log.debug("Could not write run log file: {}".format(e))


def get_current_runs():

    if not os.path.exists(FRECKLES_RUN_LOG_FILE_PATH):
        return {}
    content = OrderedDict()
    with io.open(FRECKLES_RUN_LOG_FILE_PATH, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row:
                continue
            data = convert_log_file_row(row)
            if data["state"] == "started":
                content[data["uuid"]] = data
            else:
                if data["uuid"] in content:
                    content.pop(data["uuid"])

    result = OrderedDict()
    for uuid, data in content.items():
        if not freckles_run_process_exists(data):
            continue
        result[uuid] = data
    return result


def get_last_run():

    if not os.path.exists(FRECKLES_LAST_RUN_FILE_PATH):
        return None

    with io.open(FRECKLES_LAST_RUN_FILE_PATH, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row:
                continue
            data = convert_log_file_row(row)
            break

    if not os.path.exists(data["env_dir"]):
        return None

    return data


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

            if uuid not in self._current_runs.keys():
                remove.append(uuid)
                continue
            if not freckles_run_process_exists(run_data):
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


def print_task_detail(run_detail, alias=None, color=None):

    if color is None:
        color = ""
        reset = ""
    else:
        reset = Fore.RESET

    if alias:
        alias = "{}: ".format(alias)
    else:
        alias = ""

    level = run_detail["level"]
    msg = run_detail["msg"]
    finished = run_detail["finished"]
    success = run_detail.get("success", None)
    skipped = run_detail.get("skipped", None)
    # changed = d.get("changed", None)
    # messages = d["messages"]
    error_messages = run_detail["error_messages"]
    padding = "  " * level

    if not finished:
        click.echo("{}{}{}- {}{}".format(color, alias, padding, msg, reset))
    else:
        if success:
            if skipped:
                status = "skipped"
            else:
                status = "ok"
        click.echo("{}{}{}- {}: {}{}".format(color, alias, padding, msg, status, reset))
        if not success:
            if alias:
                alias = alias[0:-1]
            click.echo("{}{}      -> {}{}".format(color, alias, error_messages, reset))


class FrecklesRunLogTerminalOutput(FrecklesLogFileHander):

    COLORS = [
        Fore.BLUE,
        Fore.GREEN,
        Fore.CYAN,
        Fore.LIGHTRED_EX,
        Fore.MAGENTA,
        Fore.YELLOW,
        Fore.RED,
    ]

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

        if self._index < len(FrecklesRunLogTerminalOutput.COLORS):
            color_index = self._index
        else:
            color_index = self._index % len(FrecklesRunLogTerminalOutput.COLORS)

        color = FrecklesRunLogTerminalOutput.COLORS[color_index]

        for d in data:
            print_task_detail(d, alias=self._alias, color=color)

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
