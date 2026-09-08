"""Tests for #5411 — NemoClaw onboarding OTel-format trace ingestion.

Verifies that ``_read_onboard_otel_trace()`` surfaces ``onboardOtelTraceId``,
``onboardOtelTotalMs``, ``onboardOtelSlowestSpans``, and ``onboardOtelHasError``
from the artifact written by the harness (``src/lib/trace.ts``) when
``NEMOCLAW_TRACE=1``.  The function must return ``{}`` silently on any failure
(absent file, corrupt JSON, unexpected structure).
"""
from __future__ import annotations

import json
import pytest

from clawmetry.adapters.nemo import _read_onboard_otel_trace


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content), encoding="utf-8")


def _otel_artifact(trace_id="t1", total_ms=5000, slowest=None, spans=None):
    return {
        "trace_id": trace_id,
        "total_duration_ms": total_ms,
        "slowest_spans": slowest or [{"name": "phase.inference", "duration_ms": total_ms}],
        "resource_spans": [
            {
                "resource": {"attributes": {"service.name": "nemoclaw.onboard"}},
                "scope_spans": [{"spans": spans or []}],
            }
        ],
    }


# ── path resolution ──────────────────────────────────────────────────────────

def test_absent_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("NEMOCLAW_TRACE_FILE", raising=False)
    monkeypatch.delenv("NEMOCLAW_TRACE_DIR", raising=False)
    assert _read_onboard_otel_trace() == {}


def test_trace_file_env_var(tmp_path, monkeypatch):
    artifact = tmp_path / "trace.json"
    _write(artifact, _otel_artifact())
    monkeypatch.setenv("NEMOCLAW_TRACE_FILE", str(artifact))
    monkeypatch.delenv("NEMOCLAW_TRACE_DIR", raising=False)
    result = _read_onboard_otel_trace()
    assert result["onboardOtelTraceId"] == "t1"
    assert result["onboardOtelTotalMs"] == 5000


def test_trace_dir_env_var(tmp_path, monkeypatch):
    trace_dir = tmp_path / "traces"
    trace_dir.mkdir()
    artifact = trace_dir / "run1.json"
    _write(artifact, _otel_artifact(trace_id="dir-trace", total_ms=3000))
    monkeypatch.delenv("NEMOCLAW_TRACE_FILE", raising=False)
    monkeypatch.setenv("NEMOCLAW_TRACE_DIR", str(trace_dir))
    result = _read_onboard_otel_trace()
    assert result["onboardOtelTraceId"] == "dir-trace"
    assert result["onboardOtelTotalMs"] == 3000


def test_default_nemoclaw_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("NEMOCLAW_TRACE_FILE", raising=False)
    monkeypatch.delenv("NEMOCLAW_TRACE_DIR", raising=False)
    trace_dir = tmp_path / ".nemoclaw" / ".e2e" / "traces"
    artifact = trace_dir / "trace.json"
    _write(artifact, _otel_artifact(trace_id="default-home", total_ms=7000))
    result = _read_onboard_otel_trace()
    assert result["onboardOtelTraceId"] == "default-home"
    assert result["onboardOtelTotalMs"] == 7000


# ── field extraction ─────────────────────────────────────────────────────────

def test_slowest_spans_surfaced(tmp_path, monkeypatch):
    slowest = [
        {"name": "phase.inference", "duration_ms": 4000},
        {"name": "phase.gateway", "duration_ms": 1000},
    ]
    artifact = tmp_path / "trace.json"
    _write(artifact, _otel_artifact(slowest=slowest))
    monkeypatch.setenv("NEMOCLAW_TRACE_FILE", str(artifact))
    result = _read_onboard_otel_trace()
    assert result["onboardOtelSlowestSpans"] == slowest


def test_no_error_spans_returns_false(tmp_path, monkeypatch):
    spans = [{"name": "phase.gateway", "duration_ms": 500,
              "status": {"code": "OK"}}]
    artifact = tmp_path / "trace.json"
    _write(artifact, _otel_artifact(spans=spans))
    monkeypatch.setenv("NEMOCLAW_TRACE_FILE", str(artifact))
    result = _read_onboard_otel_trace()
    assert result["onboardOtelHasError"] is False


def test_error_span_sets_flag(tmp_path, monkeypatch):
    spans = [
        {"name": "phase.preflight", "duration_ms": 200, "status": {"code": "OK"}},
        {"name": "phase.inference", "duration_ms": 8000, "status": {"code": "ERROR"}},
    ]
    artifact = tmp_path / "trace.json"
    _write(artifact, _otel_artifact(spans=spans))
    monkeypatch.setenv("NEMOCLAW_TRACE_FILE", str(artifact))
    result = _read_onboard_otel_trace()
    assert result["onboardOtelHasError"] is True


# ── error tolerance ──────────────────────────────────────────────────────────

def test_corrupt_json_returns_empty(tmp_path, monkeypatch):
    artifact = tmp_path / "trace.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("{not valid", encoding="utf-8")
    monkeypatch.setenv("NEMOCLAW_TRACE_FILE", str(artifact))
    assert _read_onboard_otel_trace() == {}


def test_non_dict_json_returns_empty(tmp_path, monkeypatch):
    artifact = tmp_path / "trace.json"
    _write(artifact, [1, 2, 3])
    monkeypatch.setenv("NEMOCLAW_TRACE_FILE", str(artifact))
    assert _read_onboard_otel_trace() == {}


def test_missing_fields_returns_partial(tmp_path, monkeypatch):
    artifact = tmp_path / "trace.json"
    _write(artifact, {"trace_id": "partial", "resource_spans": []})
    monkeypatch.setenv("NEMOCLAW_TRACE_FILE", str(artifact))
    result = _read_onboard_otel_trace()
    assert result["onboardOtelTraceId"] == "partial"
    assert "onboardOtelTotalMs" not in result
    assert result["onboardOtelHasError"] is False
