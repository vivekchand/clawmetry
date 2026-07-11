"""Tests for #3651 — NemoClaw onboarding trace-timing ingestion.

Verifies that ``_read_onboard_trace_timing()`` surfaces
``onboardTotalDurationMs`` and ``onboardPhases`` from the
``nemoclaw.trace_timing.v1`` artifact written by the harness during
onboarding.  The function must return ``{}`` silently on any failure
(absent file, schema mismatch, corrupt JSON).
"""
from __future__ import annotations

import json
import pytest

from clawmetry.adapters.nemo import _read_onboard_trace_timing

_SCHEMA = "nemoclaw.trace_timing.v1"


def _write_artifact(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content), encoding="utf-8")


def test_absent_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("NEMOCLAW_TRACE_TIMING_PATH", raising=False)
    assert _read_onboard_trace_timing() == {}


def test_schema_mismatch_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("NEMOCLAW_TRACE_TIMING_PATH", raising=False)
    artifact = tmp_path / ".nemoclaw" / "onboard-trace-timing.json"
    _write_artifact(artifact, {"schema_version": "nemoclaw.trace_timing.v0", "total_duration_ms": 1000})
    assert _read_onboard_trace_timing() == {}


def test_dict_format_phases(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("NEMOCLAW_TRACE_TIMING_PATH", raising=False)
    artifact = tmp_path / ".nemoclaw" / "onboard-trace-timing.json"
    _write_artifact(artifact, {
        "schema_version": _SCHEMA,
        "total_duration_ms": 4200,
        "phases": {
            "nemoclaw.onboard.phase.preflight": 800,
            "nemoclaw.onboard.phase.install": 3400,
        },
    })
    result = _read_onboard_trace_timing()
    assert result["onboardTotalDurationMs"] == 4200
    assert result["onboardPhases"]["nemoclaw.onboard.phase.preflight"] == 800
    assert result["onboardPhases"]["nemoclaw.onboard.phase.install"] == 3400


def test_list_format_phases(tmp_path, monkeypatch):
    """List-of-objects phase format is supported defensively."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("NEMOCLAW_TRACE_TIMING_PATH", raising=False)
    artifact = tmp_path / ".nemoclaw" / "onboard-trace-timing.json"
    _write_artifact(artifact, {
        "schema_version": _SCHEMA,
        "total_duration_ms": 2000,
        "phases": [
            {"name": "nemoclaw.onboard.phase.preflight", "duration_ms": 500},
            {"name": "nemoclaw.onboard.phase.validate", "duration_ms": 1500},
        ],
    })
    result = _read_onboard_trace_timing()
    assert result["onboardTotalDurationMs"] == 2000
    assert result["onboardPhases"]["nemoclaw.onboard.phase.preflight"] == 500
    assert result["onboardPhases"]["nemoclaw.onboard.phase.validate"] == 1500


def test_corrupt_json_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("NEMOCLAW_TRACE_TIMING_PATH", raising=False)
    artifact = tmp_path / ".nemoclaw" / "onboard-trace-timing.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("{not valid json{{", encoding="utf-8")
    assert _read_onboard_trace_timing() == {}


def test_env_var_override_path(tmp_path, monkeypatch):
    """NEMOCLAW_TRACE_TIMING_PATH overrides the default candidate list."""
    custom = tmp_path / "custom" / "trace.json"
    _write_artifact(custom, {
        "schema_version": _SCHEMA,
        "total_duration_ms": 999,
        "phases": {"nemoclaw.onboard.phase.preflight": 999},
    })
    monkeypatch.setenv("NEMOCLAW_TRACE_TIMING_PATH", str(custom))
    monkeypatch.setenv("HOME", str(tmp_path / "empty_home"))
    result = _read_onboard_trace_timing()
    assert result["onboardTotalDurationMs"] == 999
