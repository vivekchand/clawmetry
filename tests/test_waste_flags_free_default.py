"""``waste_flags.event_is_real_error`` OSS default is a real structured check.

Before: the free default returned ``False`` for every event, so every OSS error
counter read zero. Now: flags, status codes, exit codes and explicit error
event types count; free text never does (that inference stays in Pro), and
Pro still wins when installed.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def wf(monkeypatch):
    import clawmetry.waste_flags as _w
    importlib.reload(_w)
    monkeypatch.setattr(_w, "_pro", lambda: None)
    return _w


@pytest.mark.parametrize("event", [
    {"event_type": "tool_result", "data": {"is_error": True}},
    {"event_type": "tool.result", "data": {"isError": True}},
    {"event_type": "tool_result", "data": {"message": {"is_error": True}}},
    {"event_type": "tool_result", "data": {"error": "ENOENT"}},
    {"event_type": "tool_result", "data": {"error": {"code": "E1"}}},
    {"event_type": "tool_result", "data": {"exit_code": 2}},
    {"event_type": "tool_result", "data": {"status": 500}},
    {"event_type": "tool_result", "data": {"status_code": 404}},
    {"event_type": "api.error", "data": {}},
    {"event_type": "model_error", "data": {}},
    {"event_type": "error", "data": {"message": "boom"}},
    {"event_type": "tool_result", "data": '{"is_error": true}'},
    {"event_type": "tool_result", "data": b'{"status": 503}'},
])
def test_structured_errors_count(wf, event):
    assert wf.event_is_real_error(event) is True


@pytest.mark.parametrize("event", [
    {"event_type": "tool_result", "data": {"is_error": False, "output": "error: nope"}},
    {"event_type": "message", "data": {"content": "there was an error yesterday"}},
    {"event_type": "tool_result", "data": {"status": 200}},
    {"event_type": "tool_result", "data": {"exit_code": 0}},
    {"event_type": "tool_result", "data": {"error": None}},
    {"event_type": "tool_result", "data": {"error": ""}},
    {"event_type": "error_rate", "data": {}},  # a metric name, not an error
    {"is_error": True},  # no event shape at all
    {"event_type": "tool_result"},
    {"event_type": "tool_result", "data": "not json"},
    None,
    "string",
    42,
])
def test_text_and_shapeless_inputs_do_not_count(wf, event):
    assert wf.event_is_real_error(event) is False


def test_is_error_false_flag_wins_over_status(wf):
    """An adapter that set is_error=False knows better than a stray field."""
    assert wf.event_is_real_error(
        {"event_type": "tool_result", "data": {"is_error": False, "status": 500}}) is False


def test_pro_still_takes_precedence(monkeypatch):
    import clawmetry.waste_flags as _w
    importlib.reload(_w)

    class _Pro:
        @staticmethod
        def event_is_real_error(event):
            return "pro-says-yes"

    monkeypatch.setattr(_w, "_pro", lambda: _Pro)
    assert _w.event_is_real_error({"event_type": "message", "data": {}}) == "pro-says-yes"


def test_pro_failure_falls_back_to_the_free_check(monkeypatch):
    import clawmetry.waste_flags as _w
    importlib.reload(_w)

    class _Pro:
        @staticmethod
        def event_is_real_error(event):
            raise RuntimeError("pro broke")

    monkeypatch.setattr(_w, "_pro", lambda: _Pro)
    assert _w.event_is_real_error(
        {"event_type": "tool_result", "data": {"is_error": True}}) is True
