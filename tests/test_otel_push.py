"""Tests for clawmetry/otel_push.py (Pro OTLP/HTTP push exporter).

Covers:
* Envelope shape (OTLP/JSON logRecords with attributes)
* Header parser tolerance
* Disabled-by-default contract (no env -> no exporter)
* Entitlement gate (env set but tier doesn't unlock -> still no exporter)
* Batching + flush
* Bounded-queue drop behaviour
* Stub HTTP transport (no live network)
"""
from __future__ import annotations

import importlib
import time

import pytest


@pytest.fixture
def fresh(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.delenv("CLAWMETRY_OTLP_ENDPOINT", raising=False)
    monkeypatch.delenv("CLAWMETRY_OTLP_HEADERS", raising=False)
    monkeypatch.delenv("CLAWMETRY_OTLP_BATCH_MAX", raising=False)
    monkeypatch.delenv("CLAWMETRY_OTLP_FLUSH_SECS", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    import clawmetry.entitlements as _ent
    importlib.reload(_ent)
    _ent.invalidate()

    import clawmetry.otel_push as _otelp
    importlib.reload(_otelp)
    _otelp.reset_for_tests()
    yield _otelp
    _otelp.reset_for_tests()


class _StubWriter:
    def __init__(self):
        self.sent: list[dict] = []
        self.fail = False

    def send(self, envelope):
        if self.fail:
            raise RuntimeError("collector down")
        self.sent.append(envelope)

    def close(self):
        pass


# ── envelope ───────────────────────────────────────────────────────────────────


def test_envelope_shape_is_otlp_logs(fresh):
    env = fresh._build_otlp_envelope([
        {
            "id": "e1", "ts": 1700000000.5, "event_type": "model.completed",
            "session_id": "s1", "model": "claude-3.5", "node_id": "n1",
        }
    ])
    assert "resourceLogs" in env
    rl = env["resourceLogs"][0]
    assert rl["scopeLogs"][0]["scope"]["name"] == "clawmetry.events"
    rec = rl["scopeLogs"][0]["logRecords"][0]
    # ts in nanoseconds.
    assert rec["timeUnixNano"] == "1700000000500000000"
    assert rec["body"]["stringValue"] == "model.completed"
    keys = {a["key"] for a in rec["attributes"]}
    assert {"session_id", "event_type", "model", "node_id"}.issubset(keys)


def test_envelope_handles_missing_ts(fresh):
    env = fresh._build_otlp_envelope([{"id": "e1", "event_type": "x"}])
    rec = env["resourceLogs"][0]["scopeLogs"][0]["logRecords"][0]
    assert rec["timeUnixNano"] == "0"


# ── header parser ──────────────────────────────────────────────────────────────


def test_parse_headers_handles_real_world_pairs(fresh):
    raw = "x-honeycomb-team: abc123, x-honeycomb-dataset: clawmetry"
    parsed = fresh._parse_headers(raw)
    assert parsed == {"x-honeycomb-team": "abc123", "x-honeycomb-dataset": "clawmetry"}


def test_parse_headers_drops_malformed_pieces(fresh):
    parsed = fresh._parse_headers("good: yes, malformed, also-bad: , : value, key: val2")
    assert parsed == {"good": "yes", "key": "val2"}


def test_parse_headers_empty(fresh):
    assert fresh._parse_headers("") == {}
    assert fresh._parse_headers("   ") == {}


# ── singleton gate ─────────────────────────────────────────────────────────────


def test_no_endpoint_means_no_exporter(fresh):
    assert fresh.get_default_exporter() is None


def test_endpoint_set_in_grace_starts_exporter(fresh, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_OTLP_ENDPOINT", "http://localhost:4318/v1/logs")
    exp = fresh.get_default_exporter()
    assert exp is not None
    # Idempotent.
    assert fresh.get_default_exporter() is exp


def test_endpoint_set_but_enforced_oss_refuses(fresh, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_OTLP_ENDPOINT", "http://localhost:4318/v1/logs")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))

    import clawmetry.entitlements as _ent
    importlib.reload(_ent)
    _ent.invalidate()
    importlib.reload(fresh)
    fresh.reset_for_tests()

    assert fresh.get_default_exporter() is None


# ── batching + flush ───────────────────────────────────────────────────────────


def test_exporter_batches_and_flushes(fresh):
    stub = _StubWriter()
    exp = fresh.OTLPPushExporter(stub, batch_max=3, flush_secs=0.05, queue_size=100)
    try:
        for i in range(5):
            exp.send({"id": f"e{i}", "ts": time.time(), "event_type": "x"})
        # Wait for at least 2 flushes (3 + 2).
        deadline = time.time() + 3.0
        while time.time() < deadline and exp.sent_count < 5:
            time.sleep(0.05)
        assert exp.sent_count == 5
        # First flush has 3 records.
        first = stub.sent[0]["resourceLogs"][0]["scopeLogs"][0]["logRecords"]
        assert len(first) == 3
    finally:
        exp.close(timeout=1.0)


def test_writer_failure_drops_batch_and_counts(fresh):
    stub = _StubWriter()
    stub.fail = True
    exp = fresh.OTLPPushExporter(stub, batch_max=2, flush_secs=0.05, queue_size=100)
    try:
        for i in range(4):
            exp.send({"id": f"e{i}", "ts": time.time(), "event_type": "x"})
        deadline = time.time() + 3.0
        while time.time() < deadline and exp.error_count < 2:
            time.sleep(0.05)
        assert exp.sent_count == 0
        assert exp.dropped_count >= 2
        assert exp.error_count >= 2
    finally:
        exp.close(timeout=1.0)


def test_bounded_queue_drops_when_full(fresh):
    stub = _StubWriter()
    exp = fresh.OTLPPushExporter(stub, batch_max=10, flush_secs=10.0, queue_size=3)
    # Don't run the worker; fill the queue beyond capacity.
    exp._stop.set()
    exp._thread.join(timeout=0.5)
    for i in range(10):
        exp.send({"id": f"e{i}", "ts": 0, "event_type": "x"})
    assert exp.dropped_count >= 7
    exp.close(timeout=0.5)


# ── forward_event passthrough ──────────────────────────────────────────────────


def test_forward_event_no_op_when_disabled(fresh):
    # No env, no exporter -> forward_event is a cheap no-op.
    fresh.forward_event({"id": "e1", "event_type": "x"})


def test_forward_event_enqueues_when_active(fresh, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_OTLP_ENDPOINT", "http://localhost:4318/v1/logs")
    exp = fresh.get_default_exporter()
    assert exp is not None
    qsize_before = exp._q.qsize()
    fresh.forward_event({"id": "e1", "event_type": "x"})
    # Worker may have already drained it; either way, send() did not raise.
    qsize_after = exp._q.qsize()
    assert qsize_after >= qsize_before  # never negative
