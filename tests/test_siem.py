"""Tests for clawmetry/siem.py — daemon-side SIEM/syslog exporter.

Covers the pure formatters (CEF + JSON), RFC 5424 framing, severity mapping,
CEF escaping rules, the event-taxonomy → sigId map, the bounded-queue
exporter with a stub writer (no real sockets), env-var driven singleton
construction, and the no-op behaviour when disabled. Issue #2199.
"""

from __future__ import annotations

import json
import threading
import time

import pytest

from clawmetry import siem


@pytest.fixture(autouse=True)
def _isolate_singleton(monkeypatch):
    """Each test starts with no SIEM env vars and a fresh singleton."""
    for var in (
        "CLAWMETRY_SIEM_HOST",
        "CLAWMETRY_SIEM_PORT",
        "CLAWMETRY_SIEM_PROTOCOL",
        "CLAWMETRY_SIEM_FORMAT",
        "CLAWMETRY_SIEM_FACILITY",
        "CLAWMETRY_SIEM_APPNAME",
    ):
        monkeypatch.delenv(var, raising=False)
    siem.reset_for_tests()
    yield
    siem.reset_for_tests()


# ── CEF formatting ────────────────────────────────────────────────────────
def test_format_cef_tool_call_basics():
    ev = {
        "id": "evt-1",
        "event_type": "tool.call",
        "ts": "2026-05-28T07:00:00Z",
        "session_id": "sess-abc",
        "agent_id": "main",
        "node_id": "node-7",
        "data": {"name": "bash", "input": {"cmd": "ls"}},
    }
    line = siem.format_cef(ev)
    assert line.startswith("CEF:0|ClawMetry|clawmetry|1.0|1001|Tool Call|")
    assert "rt=2026-05-28T07:00:00Z" in line
    assert "cs1=sess-abc" in line
    assert "cs1Label=sessionId" in line
    assert "cs2=main" in line
    assert "deviceExternalId=node-7" in line
    assert "act=bash" in line


def test_format_cef_tool_result_failure_is_high_severity():
    ev = {
        "id": "evt-2",
        "event_type": "tool.result",
        "ts": "2026-05-28T07:00:01Z",
        "data": {"name": "bash", "is_error": True, "duration_ms": 42},
    }
    line = siem.format_cef(ev)
    # CEF severity column is the 7th pipe-delimited field; 7 means high.
    parts = line.split("|")
    assert parts[6] == "7", line
    assert "outcome=failure" in line
    assert "cn1=42" in line
    assert "cn1Label=durationMs" in line


def test_format_cef_tool_result_success_is_info_severity():
    ev = {
        "id": "evt-3",
        "event_type": "tool.result",
        "ts": "2026-05-28T07:00:02Z",
        "data": {"name": "bash", "duration_ms": 12},
    }
    line = siem.format_cef(ev)
    parts = line.split("|")
    assert parts[6] == "3", line  # 3 = info-ish in our mapping
    assert "outcome=success" in line


def test_format_cef_llm_usage_carries_tokens_and_cost():
    ev = {
        "id": "evt-4",
        "event_type": "model.completed",
        "ts": "2026-05-28T07:00:03Z",
        "model": "claude-sonnet-4-6",
        "cost_usd": 0.0123,
        "data": {"input_tokens": 1200, "output_tokens": 340},
    }
    line = siem.format_cef(ev)
    assert "|3001|" in line
    assert "deviceCustomString3=claude-sonnet-4-6" in line
    assert "cn1=1200" in line
    assert "cn2=340" in line
    assert "cfp1=0.0123" in line


def test_format_cef_security_threat_is_high_severity():
    ev = {
        "id": "evt-5",
        "event_type": "security_threat",
        "ts": "2026-05-28T07:00:04Z",
        "data": {"signature_id": "SEC-001", "description": "reverse shell"},
    }
    line = siem.format_cef(ev)
    parts = line.split("|")
    assert parts[4] == "6001"
    assert parts[6] == "7"
    assert "act=SEC-001" in line
    assert "reason=reverse shell" in line


def test_format_cef_unknown_event_type_falls_through_to_9999():
    ev = {"id": "x", "event_type": "totally.new.thing", "ts": "2026-05-28T07:00:05Z"}
    line = siem.format_cef(ev)
    assert "|9999|totally.new.thing|" in line


def test_format_cef_carries_hash_chain_fields_when_present():
    ev = {
        "id": "evt-6",
        "event_type": "tool.call",
        "ts": "2026-05-28T07:00:06Z",
        "data": {"name": "bash"},
        "chain_prev_hash": "0" * 64,
        "chain_hash": "a" * 64,
    }
    line = siem.format_cef(ev)
    assert "cs5=" + ("a" * 64) in line
    assert "cs5Label=chainHash" in line
    assert "cs6=" + ("0" * 64) in line


# ── CEF escaping ──────────────────────────────────────────────────────────
def test_cef_escape_handles_pipe_equals_backslash_newline():
    assert siem._cef_escape("a|b") == "a\\|b"
    assert siem._cef_escape("a=b") == "a\\=b"
    assert siem._cef_escape("a\\b") == "a\\\\b"
    assert siem._cef_escape("a\nb") == "a\\nb"


def test_cef_escape_handles_none_and_numbers():
    assert siem._cef_escape(None) == ""
    assert siem._cef_escape(42) == "42"


# ── JSON format ───────────────────────────────────────────────────────────
def test_format_json_round_trips():
    ev = {
        "id": "evt-7",
        "event_type": "tool.call",
        "ts": "2026-05-28T07:00:07Z",
        "data": {"name": "bash", "input": {"cmd": "ls"}},
    }
    line = siem.format_json(ev)
    parsed = json.loads(line)
    assert parsed["id"] == "evt-7"
    assert parsed["data"]["name"] == "bash"


def test_format_json_drops_non_serialisable_via_str():
    class Weird:
        def __str__(self) -> str:
            return "weird-thing"

    ev = {"id": "evt-8", "event_type": "x", "ts": "2026-05-28T07:00:08Z", "data": Weird()}
    line = siem.format_json(ev)
    # default=str coerces; line is valid JSON
    parsed = json.loads(line)
    assert parsed["data"] == "weird-thing"


# ── RFC 5424 framing ──────────────────────────────────────────────────────
def test_format_syslog_line_priority_and_layout():
    ev = {"id": "evt-9", "event_type": "tool.call", "ts": "2026-05-28T07:00:09Z", "data": {"name": "bash"}}
    line = siem.format_syslog_line(ev, fmt="cef", facility=16, app_name="clawmetry")
    # facility(16)*8 + severity(6 info) = 134
    assert line.startswith("<134>1 2026-05-28T07:00:09Z - clawmetry - tool.call - CEF:0|")


def test_format_syslog_line_error_severity_changes_priority():
    ev = {"id": "evt-10", "event_type": "daemon.error", "ts": "2026-05-28T07:00:10Z", "data": {}}
    line = siem.format_syslog_line(ev, fmt="json", facility=16)
    # facility(16)*8 + severity(3 error) = 131
    assert line.startswith("<131>1 ")


def test_format_syslog_line_falls_back_to_now_on_missing_ts():
    ev = {"id": "evt-11", "event_type": "x", "data": {}}
    line = siem.format_syslog_line(ev)
    # Just assert the frame is well-formed and contains a Zulu timestamp.
    assert line.startswith("<")
    assert "Z " in line


# ── SIEMExporter (no real sockets) ────────────────────────────────────────
class _Capture:
    """Stub writer that records every line."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.lock = threading.Lock()
        self.fail_first: int = 0  # set > 0 to simulate writer errors

    def write(self, line: str) -> None:
        with self.lock:
            if self.fail_first > 0:
                self.fail_first -= 1
                raise OSError("simulated write failure")
            self.lines.append(line)


def test_exporter_drains_queue_to_writer():
    cap = _Capture()
    exp = siem.SIEMExporter(cap, fmt="cef")
    try:
        for i in range(5):
            exp.send({"id": f"e{i}", "event_type": "tool.call", "ts": "2026-05-28T07:01:00Z", "data": {"name": "bash"}})
        # Allow worker thread to drain.
        deadline = time.time() + 2.0
        while exp.sent_count < 5 and time.time() < deadline:
            time.sleep(0.02)
        assert exp.sent_count == 5
        assert all("CEF:0|ClawMetry" in ln for ln in cap.lines)
    finally:
        exp.close(timeout=1.0)


def test_exporter_drops_when_queue_full_without_blocking():
    cap = _Capture()
    # Tiny queue + a writer that hangs forever forces overflow.
    blocker = threading.Event()

    def slow_write(_line: str) -> None:
        blocker.wait()

    exp = siem.SIEMExporter(slow_write, fmt="json", queue_size=2)
    try:
        # Send more than queue can hold; send() must return immediately.
        t0 = time.time()
        for i in range(20):
            exp.send({"id": f"e{i}", "event_type": "x", "ts": "2026-05-28T07:01:00Z"})
        assert time.time() - t0 < 1.0, "send() blocked the caller"
        # At least some events should have been dropped.
        assert exp.dropped_count > 0
    finally:
        blocker.set()
        exp.close(timeout=1.0)


def test_exporter_writer_failure_is_counted_not_raised():
    cap = _Capture()
    cap.fail_first = 3
    exp = siem.SIEMExporter(cap, fmt="cef")
    try:
        for i in range(5):
            exp.send({"id": f"e{i}", "event_type": "tool.call", "ts": "2026-05-28T07:01:00Z", "data": {"name": "bash"}})
        deadline = time.time() + 2.0
        while (exp.sent_count + exp.error_count) < 5 and time.time() < deadline:
            time.sleep(0.02)
        assert exp.error_count == 3
        assert exp.sent_count == 2
    finally:
        exp.close(timeout=1.0)


# ── Singleton + env wiring ────────────────────────────────────────────────
def test_get_default_exporter_returns_none_when_disabled():
    assert siem.get_default_exporter() is None


def test_forward_event_is_noop_when_disabled():
    # Must not raise, must not log scarily — just return.
    siem.forward_event({"id": "ev", "event_type": "x", "ts": "2026-05-28T07:01:00Z"})
    assert siem.get_default_exporter() is None


def test_get_default_exporter_builds_udp_when_host_set(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_SIEM_HOST", "127.0.0.1")
    monkeypatch.setenv("CLAWMETRY_SIEM_PORT", "5514")
    monkeypatch.setenv("CLAWMETRY_SIEM_PROTOCOL", "udp")
    exp = siem.get_default_exporter()
    assert exp is not None
    # Singleton is cached on second call.
    assert siem.get_default_exporter() is exp


def test_unknown_protocol_disables_exporter(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_SIEM_HOST", "127.0.0.1")
    monkeypatch.setenv("CLAWMETRY_SIEM_PROTOCOL", "carrier-pigeon")
    assert siem.get_default_exporter() is None
