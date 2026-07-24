"""Tests for #3991 — gateway structured/subsystem log lines parsed into events.

Verifies _gateway_log_events() reads the most-recent gateway log file, parses
each JSON line, and surfaces ts/level/msg/subsystem into event dicts, newest-first.

Fingerprint: hgap-646613da33
"""
from __future__ import annotations

import json

import pytest

from clawmetry.adapters.openclaw import _gateway_log_events


def _write_log(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_well_formed_lines_parsed(monkeypatch, tmp_path):
    """Standard log lines surface level, msg, and subsystem."""
    log = tmp_path / "openclaw-2026-07-24.log"
    events_in = [
        {"time": 1721808000, "level": "info",  "msg": "gateway started", "subsystem": "core"},
        {"time": 1721808001, "level": "warn",  "msg": "high latency",    "subsystem": "llm"},
        {"time": 1721808002, "level": "error", "msg": "tool failed",     "subsystem": "tools"},
    ]
    _write_log(log, [json.dumps(e) for e in events_in])
    monkeypatch.setattr(
        "clawmetry.adapters.openclaw._gateway_log_files",
        lambda: [str(log)],
    )

    result = _gateway_log_events()

    assert len(result) == 3
    # newest-first order
    assert result[0]["msg"] == "tool failed"
    assert result[0]["level"] == "error"
    assert result[0]["subsystem"] == "tools"
    assert result[0]["ts"] == 1721808002
    assert result[2]["msg"] == "gateway started"


def test_non_json_lines_silently_skipped(monkeypatch, tmp_path):
    """Non-JSON lines (plain text, truncated) are dropped without error."""
    log = tmp_path / "openclaw-2026-07-24.log"
    _write_log(log, [
        "plain text line",
        json.dumps({"level": "info", "msg": "ok", "subsystem": "core"}),
        "{broken json",
    ])
    monkeypatch.setattr(
        "clawmetry.adapters.openclaw._gateway_log_files",
        lambda: [str(log)],
    )

    result = _gateway_log_events()

    assert len(result) == 1
    assert result[0]["msg"] == "ok"


def test_missing_log_file_returns_empty(monkeypatch):
    """No log files found → empty list, no exception."""
    monkeypatch.setattr(
        "clawmetry.adapters.openclaw._gateway_log_files",
        lambda: [],
    )
    assert _gateway_log_events() == []


def test_count_limits_returned_events(monkeypatch, tmp_path):
    """Only the last ``count`` events are returned."""
    log = tmp_path / "openclaw-2026-07-24.log"
    lines = [json.dumps({"level": "info", "msg": f"line {i}"}) for i in range(20)]
    _write_log(log, lines)
    monkeypatch.setattr(
        "clawmetry.adapters.openclaw._gateway_log_files",
        lambda: [str(log)],
    )

    result = _gateway_log_events(count=5)

    assert len(result) == 5
    # newest first → "line 19" comes first
    assert result[0]["msg"] == "line 19"


def test_alternate_timestamp_keys_accepted(monkeypatch, tmp_path):
    """``ts`` and ``timestamp`` keys are also accepted as the event timestamp."""
    log = tmp_path / "openclaw-2026-07-24.log"
    _write_log(log, [
        json.dumps({"ts": 111, "level": "info", "msg": "ts key"}),
        json.dumps({"timestamp": 222, "level": "info", "msg": "timestamp key"}),
    ])
    monkeypatch.setattr(
        "clawmetry.adapters.openclaw._gateway_log_files",
        lambda: [str(log)],
    )

    result = _gateway_log_events()

    assert len(result) == 2
    tss = {e["ts"] for e in result}
    assert tss == {111, 222}
