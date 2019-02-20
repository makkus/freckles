#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `freckles` package."""
import os

import pytest

# from freckles.frecklecute_cli import cli
from frutils.config import Cnf

THIS_DIR = os.path.dirname(__file__)
FRECKLES_TEST_RUN_DIR = os.path.expanduser("/tmp/freckle_tests/archive/run")
FRECKLES_TEST_CURRENT_RUN_SYMLINK = os.path.expanduser("/tmp/freckle_tests/current")

TEST_CNF_PROFILES = {
    "default": {
        "context_repos": [],
        "allowed_adapters": ["freckles", "shell", "nsbl", "templig"],
        "current_run_folder": FRECKLES_TEST_CURRENT_RUN_SYMLINK,
        "run_folder": FRECKLES_TEST_RUN_DIR,
        "ignore_invalid_repos": True,
        "allow_remote": False,
        "allow_community": True,
    },
    "empty": {"context_repos": []},
}

#
# @pytest.fixture(scope="class")
# def freckles_test_config():
#
#     cnf = Cnf(TEST_CNF_PROFILES["default"])
#
#     return cnf
#
#
# @pytest.fixture(scope="class")
# def ctx_non_typed(freckles_test_config):
#
#     repos = [os.path.join(THIS_DIR, "frecklet_repos", "non_typed")]
#     context = FrecklesContext(freckles_test_config, freckles_repos=repos)
#
#     return context
#
#
# @pytest.fixture(scope="class")
# def ctx_task_key(freckles_test_config):
#
#     repos = [os.path.join(THIS_DIR, "frecklet_repos", "task_key")]
#     context = FrecklesContext(freckles_test_config, freckles_repos=repos)
#
#     return context
#
#
# @pytest.fixture(scope="class")
# def ctx_control_vars(freckles_test_config):
#
#     repos = [os.path.join(THIS_DIR, "frecklet_repos", "control_vars")]
#     context = FrecklesContext(freckles_test_config, freckles_repos=repos)
#
#     return context
#
#
# class TestNonTyped(object):
#     def test_context(self, ctx_non_typed):
#
#         names = ctx_non_typed.get_frecklet_names()
#         assert len(names) >= 4
#
#     def test_no_child_no_var(self, ctx_non_typed):
#
#         frecklet = ctx_non_typed.create_frecklet("grand-child-1")
#         params = frecklet.get_parameters()
#         assert len(params.param_list) == 0
#
#     def test_rendered_no_child_no_var(self, ctx_non_typed):
#
#         result = FrecklesRunner.run_frecklet(
#             "grand-child-1", context=ctx_non_typed, no_run=True
#         )
#
#         task_list = result.get_run(0).task_list
#
#         assert len(task_list) == 1
#         assert task_list[0]["vars"] == {"msg": "{{ ansible_env.USER }}"}
#
#     def test_params_no_child_one_var(self, ctx_non_typed):
#
#         frecklet = ctx_non_typed.create_frecklet("grand-child-2")
#         params = frecklet.get_parameters()
#         assert len(params.param_list) == 1
#         assert "grand_child_2_var_1" in [str(p) for p in params.param_list]
#
#     def test_rendered_no_child_one_var(self, ctx_non_typed):
#
#         result = FrecklesRunner.run_frecklet(
#             "grand-child-2",
#             context=ctx_non_typed,
#             no_run=True,
#             user_input={"grand_child_2_var_1": "xxx"},
#         )
#         task_list = result.get_run(0).task_list
#
#         assert len(task_list) == 1
#         assert task_list[0]["vars"] == {"msg": "xxx"}
#
#     def test_rendered_no_child_one_var_no_input(self, ctx_non_typed):
#
#         with pytest.raises(ParametersException):
#             FrecklesRunner.run_frecklet(
#                 "grand-child-2", context=ctx_non_typed, no_run=True, user_input={}
#             )
#
#     def test_rendered_no_child_one_var_non_string_input_type(self, ctx_non_typed):
#
#         result = FrecklesRunner.run_frecklet(
#             "grand-child-2",
#             context=ctx_non_typed,
#             no_run=True,
#             user_input={"grand_child_2_var_1": 11},
#         )
#         task_list = result.get_run(0).task_list
#         assert len(task_list) == 1
#         assert task_list[0]["vars"] == {"msg": 11}
#
#     def test_rendered_no_child_one_var_wrong_var_name(self, ctx_non_typed):
#
#         with pytest.raises(ParametersException):
#             FrecklesRunner.run_frecklet(
#                 "grand-child-2",
#                 context=ctx_non_typed,
#                 no_run=True,
#                 user_input={"grand_child_2_var_11": "XXX"},
#             )
#
#     def test_params_no_child_two_vars(self, ctx_non_typed):
#
#         frecklet = ctx_non_typed.create_frecklet("grand-child-4")
#         params = frecklet.get_parameters()
#         assert len(params.param_list) == 2
#         assert "grand_child_4_var_1" in [str(p) for p in params.param_list]
#         assert "grand_child_4_var_1" in [str(p) for p in params.param_list]
#
#     def test_rendered_no_child_two_vars(self, ctx_non_typed):
#
#         result = FrecklesRunner.run_frecklet(
#             "grand-child-4",
#             context=ctx_non_typed,
#             no_run=True,
#             user_input={"grand_child_4_var_1": "xxx", "grand_child_4_var_2": "yyy"},
#         )
#         task_list = result.get_run(0).task_list
#
#         assert len(task_list) == 1
#         assert task_list[0]["vars"] == {"msg": "xxx - yyy"}
#
#     def test_rendered_one_child_no_var(self, ctx_non_typed):
#
#         result = FrecklesRunner.run_frecklet(
#             "child-1", context=ctx_non_typed, no_run=True
#         )
#
#         task_list = result.get_run(0).task_list
#
#         assert len(task_list) == 1
#         assert task_list[0]["vars"] == {"msg": "{{ ansible_env.USER }}"}
#
#     def test_rendered_two_childs_no_var(self, ctx_non_typed):
#
#         result = FrecklesRunner.run_frecklet(
#             "parent-1", context=ctx_non_typed, no_run=True
#         )
#
#         task_list = result.get_run(0).task_list
#
#         assert len(task_list) == 1
#         assert task_list[0]["vars"] == {"msg": "{{ ansible_env.USER }}"}
#
#     def test_rendered_three_childs_no_var(self, ctx_non_typed):
#
#         result = FrecklesRunner.run_frecklet(
#             "grand-parent-1", context=ctx_non_typed, no_run=True
#         )
#
#         task_list = result.get_run(0).task_list
#
#         assert len(task_list) == 1
#         assert task_list[0]["vars"] == {"msg": "{{ ansible_env.USER }}"}
#
#     def test_rendered_one_child_one_var_missing(self, ctx_non_typed):
#
#         with pytest.raises(ParametersException):
#             FrecklesRunner.run_frecklet("child-2", context=ctx_non_typed, no_run=True)
#
#     def test_rendered_one_child_one_var_default(self, ctx_non_typed):
#
#         result = FrecklesRunner.run_frecklet(
#             "child-3", context=ctx_non_typed, no_run=True
#         )
#         task_list = result.get_run(0).task_list
#
#         assert len(task_list) == 1
#         assert task_list[0]["vars"] == {"msg": "grand_child_3_var_1_default"}
#
#
# class TestTaskKey(object):
#     def test_skip(self, ctx_task_key):
#
#         fx = Frecklecutable.create_from_file_or_name("child-1", context=ctx_task_key)
#
#         processed = fx.process_tasklist(vars={})
#
#         assert len(processed[0]["task_list"]) == 0
#
#     def test_skip_with_auto_arg(self, ctx_task_key):
#
#         fx = Frecklecutable.create_from_file_or_name("child-2", context=ctx_task_key)
#
#         processed = fx.process_tasklist(vars={"skip": "x"})
#
#         assert len(processed[0]["task_list"]) == 0
#
#     def test_skip_with_auto_arg_non_skip(self, ctx_task_key):
#
#         fx = Frecklecutable.create_from_file_or_name("child-2", context=ctx_task_key)
#
#         processed = fx.process_tasklist(vars={"skip": "xx"})
#
#         assert len(processed[0]["task_list"]) == 1
#
#     def test_skip_with_typed_arg(self, ctx_task_key):
#
#         fx = Frecklecutable.create_from_file_or_name("child-3", context=ctx_task_key)
#
#         processed = fx.process_tasklist(vars={"skip": True})
#
#         assert len(processed[0]["task_list"]) == 0
#
#     def test_skip_with_typed_arg_non_skip(self, ctx_task_key):
#
#         fx = Frecklecutable.create_from_file_or_name("child-3", context=ctx_task_key)
#
#         processed = fx.process_tasklist(vars={"skip": False})
#
#         assert len(processed[0]["task_list"]) == 1
#
#     def test_skip_with_typed_arg_default(self, ctx_task_key):
#
#         fx = Frecklecutable.create_from_file_or_name("child-3", context=ctx_task_key)
#
#         processed = fx.process_tasklist(vars={})
#
#         assert len(processed[0]["task_list"]) == 0
