"""Tests for issue #5193 — nemoclaw: onboarding OTel trace artifacts not ingested.

Verifies that _nemoclaw_onboard_trace() reads the trace file written by the
NemoClaw harness (NEMOCLAW_TRACE_FILE / NEMOCLAW_TRACE_DIR / .e2e/traces/trace.json)
and surfaces nemoclawOnboardTraceStatus, nemoclawOnboardTraceSpanCount,
nemoclawOnboardTraceErrors, and nemoclawOnboardSlowSpans on DetectResult.meta.

Fingerprint: hgap-1f53053124 (used to dedupe — keep it in the body).
"""
from __future__ import annotations

import importlib
import json
import os
import sys

import pytest


@pytest.fixture(autouse=True)
def _restore_sys_modules():
    saved = sys.modules.get("clawmetry.adapters.openclaw")
    yield
    if saved is None:
        sys.modules.pop("clawmetry.adapters.openclaw", None)
    else:
        sys.modules["clawmetry.adapters.openclaw"] = saved


def _reload_adapter():
    import clawmetry.adapters.openclaw as oc_mod
    importlib.reload(oc_mod)
    return oc_mod


def _write_trace(path, spans, summary=None):
    data: dict = {"spans": spans}
    if summary is not None:
        data["summary"] = summary
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh)


def test_disabled_when_env_not_set(monkeypatch):
    """Returns {} when NEMOCLAW_TRACE is absent."""
    monkeypatch.delenv("NEMOCLAW_TRACE", raising=False)
    oc = _reload_adapter()
    assert oc._nemoclaw_onboard_trace() == {}


def test_disabled_when_env_zero(monkeypatch):
    """Returns {} when NEMOCLAW_TRACE=0 (explicitly disabled)."""
    monkeypatch.setenv("NEMOCLAW_TRACE", "0")
    oc = _reload_adapter()
    assert oc._nemoclaw_onboard_trace() == {}


def test_returns_empty_when_file_missing(monkeypatch, tmp_path):
    """Returns {} gracefully when trace file does not exist — never raises."""
    monkeypatch.setenv("NEMOCLAW_TRACE", "1")
    monkeypatch.setenv("NEMOCLAW_TRACE_FILE", str(tmp_path / "no_such_file.json"))
    monkeypatch.delenv("NEMOCLAW_TRACE_DIR", raising=False)
    monkeypatch.chdir(tmp_path)  # prevents fallback to .e2e/traces/trace.json
    oc = _reload_adapter()
    assert oc._nemoclaw_onboard_trace() == {}


def test_ok_spans_surface_status_and_count(monkeypatch, tmp_path):
    """All-OK spans produce status=OK and the correct span count."""
    trace_file = tmp_path / "trace.json"
    _write_trace(str(trace_file), [
        {"name": "nemoclaw.onboard.phase.gateway", "status": "OK", "duration_ms": 120},
        {"name": "nemoclaw.onboard.phase.inference", "status": "OK", "duration_ms": 340},
    ])
    monkeypatch.setenv("NEMOCLAW_TRACE", "1")
    monkeypatch.setenv("NEMOCLAW_TRACE_FILE", str(trace_file))
    monkeypatch.delenv("NEMOCLAW_TRACE_DIR", raising=False)
    oc = _reload_adapter()
    result = oc._nemoclaw_onboard_trace()
    assert result["nemoclawOnboardTraceStatus"] == "OK"
    assert result["nemoclawOnboardTraceSpanCount"] == 2
    assert "nemoclawOnboardTraceErrors" not in result


def test_error_span_surfaces_status_and_name(monkeypatch, tmp_path):
    """An ERROR span sets worst-case status=ERROR and includes the phase name."""
    trace_file = tmp_path / "trace.json"
    _write_trace(str(trace_file), [
        {"name": "nemoclaw.onboard.phase.gateway", "status": "OK", "duration_ms": 80},
        {"name": "nemoclaw.onboard.phase.inference", "status": "ERROR", "duration_ms": 5000},
    ])
    monkeypatch.setenv("NEMOCLAW_TRACE", "1")
    monkeypatch.setenv("NEMOCLAW_TRACE_FILE", str(trace_file))
    monkeypatch.delenv("NEMOCLAW_TRACE_DIR", raising=False)
    oc = _reload_adapter()
    result = oc._nemoclaw_onboard_trace()
    assert result["nemoclawOnboardTraceStatus"] == "ERROR"
    assert result["nemoclawOnboardTraceSpanCount"] == 2
    assert "nemoclaw.onboard.phase.inference" in result["nemoclawOnboardTraceErrors"]


def test_slowest_spans_forwarded_from_summary(monkeypatch, tmp_path):
    """summary.slowest_spans is forwarded as nemoclawOnboardSlowSpans (capped at 5)."""
    slow = [
        {"name": "nemoclaw.onboard.phase.inference", "duration_ms": 4200},
        {"name": "nemoclaw.onboard.phase.gateway", "duration_ms": 900},
    ]
    trace_file = tmp_path / "trace.json"
    _write_trace(str(trace_file), [
        {"name": "nemoclaw.onboard.phase.inference", "status": "OK", "duration_ms": 4200},
    ], summary={"slowest_spans": slow})
    monkeypatch.setenv("NEMOCLAW_TRACE", "1")
    monkeypatch.setenv("NEMOCLAW_TRACE_FILE", str(trace_file))
    monkeypatch.delenv("NEMOCLAW_TRACE_DIR", raising=False)
    oc = _reload_adapter()
    result = oc._nemoclaw_onboard_trace()
    assert result["nemoclawOnboardSlowSpans"] == slow


def test_trace_dir_env_resolves_to_trace_json(monkeypatch, tmp_path):
    """NEMOCLAW_TRACE_DIR is used as a directory and trace.json is appended."""
    trace_dir = tmp_path / "traces"
    trace_dir.mkdir()
    _write_trace(str(trace_dir / "trace.json"), [
        {"name": "nemoclaw.onboard.phase.gateway", "status": "OK", "duration_ms": 50},
    ])
    monkeypatch.setenv("NEMOCLAW_TRACE", "1")
    monkeypatch.delenv("NEMOCLAW_TRACE_FILE", raising=False)
    monkeypatch.setenv("NEMOCLAW_TRACE_DIR", str(trace_dir))
    oc = _reload_adapter()
    result = oc._nemoclaw_onboard_trace()
    assert result["nemoclawOnboardTraceStatus"] == "OK"
    assert result["nemoclawOnboardTraceSpanCount"] == 1
