# -*- coding: utf-8 -*-
import csv
import io
import json
import os
import threading

import click
import fasteners
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from freckles.defaults import FRECKLES_RUN_LOG_FILE_PATH


def convert_log_file_row(row):

    data = {}
    data["uuid"] = row[0]
    data["frecklet_name"] = row[1]
    data["adapter"] = row[2]
    data["env_dir"] = row[3]
    data["state"] = row[4]
    data["timestamp"] = row[5]

    return data


def get_current_runs():

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


class RunsWatcher(object):
    def __init__(self):

        self._lock = threading.Lock()
        self._current_runs = None

        self._runs_event_handler = FrecklesRunsListFileHandler(
            callback=self.update_current_runs
        )
        self._runs_observer = None

        self._log_file_watchers = {}

        self._aliases = {}

    def start(self):

        current_runs = get_current_runs()

        self.update_current_runs(current_runs)
        self._runs_observer = watch_runs(self._runs_event_handler)

    def stop(self):

        for fw in self._log_file_watchers.values():
            fw.finished()

        self._log_file_watchers = {}
        self._runs_observer.stop()

    def join_runs_watch(self):

        self._runs_observer.join()

    @fasteners.locked
    def update_current_runs(self, current_runs):

        self._current_runs = current_runs

        for uuid, r in self._current_runs.items():

            if uuid in self._log_file_watchers.keys():
                continue

            alias = r["frecklet_name"]
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
            self._log_file_watchers[uuid] = FrecklesRunLogWatcher(alias_new, r)

        remove = []
        for uuid, fw in self._log_file_watchers.items():

            if uuid in self._current_runs.keys():
                continue

            fw.finished()
            remove.append(uuid)

        for r in remove:
            self._log_file_watchers.pop(r)

        if not self._log_file_watchers:
            self._aliases = {}


class FrecklesLogFileHander(FileSystemEventHandler):
    def __init__(self, created_callback=None, callback=None, finished_callback=None):

        self._created_callback = created_callback
        self._callback = callback
        self._finished_callback = finished_callback
        self._last_file_pos = 0

    def on_created(self, event):

        if not self._created_callback:
            return

        if not event.src_path.endswith(os.path.sep + "run_log.json"):
            return

        self._created_callback(event.src_path)

    def on_modified(self, event):

        if not self._callback:
            return

        if not event.src_path.endswith(os.path.sep + "run_log.json"):
            return

        if not os.path.exists(event.src_path):
            return []

        with io.open(event.src_path, "r", encoding="utf-8") as f:
            f.seek(self._last_file_pos)
            data = f.readlines()
            self._last_file_pos = f.tell()

        result = []
        for line in data:
            d = json.loads(line)
            result.append(d)

        return self._callback(result)

    def on_deleted(self, event):

        if not self._finished_callback:
            return

        if not event.src_path.endswith(os.path.sep + "run_log.json"):
            return

        self._finished_callback()


class FrecklesRunLogWatcher(FrecklesLogFileHander):
    def __init__(self, alias, run_data):

        self._alias = alias
        self._run_data = run_data
        self._uuid = self._run_data["uuid"]
        self._frecklet_name = self._run_data["frecklet_name"]
        if self._frecklet_name.startswith("__dyn_"):
            self._frecklet_name = "_no_name_"
        self._adapter = self._run_data["adapter"]
        self._env_dir = self._run_data["env_dir"]
        self._started = self._run_data["timestamp"]
        self._log_file = os.path.join(self._env_dir, "run_log.json")

        super(FrecklesRunLogWatcher, self).__init__(
            callback=self.updated, finished_callback=self.finished
        )

        self._observer = watch_log_file(self._env_dir, self)
        self._finished = False

    def updated(self, data):

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
                click.echo("{}: {}- {}".format(self._alias, padding, msg))
            else:
                if success:
                    if skipped:
                        status = "skipped"
                    else:
                        status = "ok"
                click.echo("{}: {}- {}: {}".format(self._alias, padding, msg, status))
                if not success:
                    click.echo("{}      -> {}".format(error_messages))

    def finished(self):

        if not self._finished:
            self._finished = True
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
