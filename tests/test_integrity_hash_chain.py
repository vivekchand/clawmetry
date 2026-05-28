"""Unit tests for the tamper-evident hash chain (Issue #2200)."""

from __future__ import annotations

import importlib
import os
import time
import uuid

import pytest


@pytest.fixture
def store_with_integrity(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_INTEGRITY", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=True)


@pytest.fixture
def store_no_integrity(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_INTEGRITY", "0")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=True)


def _ev(node_id="node-a", **kw):
    return {
        "id": str(uuid.uuid4()),
        "node_id": node_id,
        "agent_id": "main",
        "event_type": "tool_call",
        "ts": "2026-01-01T00:00:00Z",
        **kw,
    }


def _flush(store):
    store._flush_now()
    time.sleep(0.1)


class TestIntegrityDisabled:
    def test_verify_returns_empty_when_no_hashes(self, store_no_integrity):
        s = store_no_integrity
        s.ingest(_ev())
        _flush(s)
        result = s.verify_integrity()
        assert result["status"] == "empty"
        assert result["checked"] == 0

    def test_events_have_no_hash_columns(self, store_no_integrity):
        s = store_no_integrity
        s.ingest(_ev())
        _flush(s)
        rows = s._fetch("SELECT chain_hash FROM events WHERE chain_hash IS NOT NULL", [])
        assert rows == []


class TestIntegrityEnabled:
    def test_single_event_chain_is_valid(self, store_with_integrity):
        s = store_with_integrity
        s.ingest(_ev())
        _flush(s)
        result = s.verify_integrity()
        assert result["status"] == "valid"
        assert result["checked"] == 1
        assert result["broken_at"] is None

    def test_multiple_events_chain_is_valid(self, store_with_integrity):
        s = store_with_integrity
        for _ in range(5):
            s.ingest(_ev())
        _flush(s)
        result = s.verify_integrity()
        assert result["status"] == "valid"
        assert result["checked"] == 5

    def test_genesis_prev_hash_is_zeros(self, store_with_integrity):
        s = store_with_integrity
        s.ingest(_ev())
        _flush(s)
        rows = s._fetch(
            "SELECT chain_prev_hash FROM events WHERE chain_hash IS NOT NULL ORDER BY created_at ASC LIMIT 1",
            [],
        )
        assert rows[0][0] == "0" * 64

    def test_chain_links_are_sequential(self, store_with_integrity):
        s = store_with_integrity
        for _ in range(3):
            s.ingest(_ev())
        _flush(s)
        rows = s._fetch(
            "SELECT chain_prev_hash, chain_hash FROM events WHERE chain_hash IS NOT NULL ORDER BY created_at ASC, id ASC",
            [],
        )
        # Each row's prev_hash must equal the previous row's hash
        for i in range(1, len(rows)):
            assert rows[i][0] == rows[i - 1][1], f"Link broken between row {i-1} and {i}"

    def test_cost_backfill_does_not_break_chain(self, store_with_integrity):
        s = store_with_integrity
        s.ingest(_ev())
        _flush(s)
        # Simulate a cost backfill: update cost_usd on the event
        with s._write_lock:
            s._conn.execute("UPDATE events SET cost_usd = 0.042 WHERE cost_usd IS NULL")
        result = s.verify_integrity()
        assert result["status"] == "valid", "Cost backfill must not break the chain"

    def test_verify_detects_tampered_immutable_field(self, store_with_integrity):
        import clawmetry.local_store as ls
        s = store_with_integrity
        s.ingest(_ev())
        _flush(s)
        # Tamper with event_type — this is an immutable field in the hash
        with s._write_lock:
            s._conn.execute("UPDATE events SET event_type = 'tampered' WHERE event_type = 'tool_call'")
        result = s.verify_integrity()
        assert result["status"] == "invalid"
        assert result["broken_at"] is not None

    def test_verify_node_id_filter(self, store_with_integrity):
        s = store_with_integrity
        for _ in range(2):
            s.ingest(_ev(node_id="node-a"))
        for _ in range(2):
            s.ingest(_ev(node_id="node-b"))
        _flush(s)
        r_a = s.verify_integrity(node_id="node-a")
        r_b = s.verify_integrity(node_id="node-b")
        assert r_a["status"] == "valid"
        assert r_b["status"] == "valid"
        assert r_a["checked"] == 2
        assert r_b["checked"] == 2

    def test_pre_chain_count_reported(self, store_with_integrity, store_no_integrity):
        # Events inserted without integrity have chain_hash=NULL → pre_chain
        s = store_with_integrity
        # Directly insert a row without hashes to simulate pre-chain events
        with s._write_lock:
            s._conn.execute(
                "INSERT INTO events (id, agent_type, node_id, agent_id, event_type, ts, created_at) "
                "VALUES ('pre-chain-id', 'openclaw', 'node-x', 'main', 'message', '2025-01-01', 0)"
            )
        s.ingest(_ev())
        _flush(s)
        result = s.verify_integrity()
        assert result["pre_chain"] >= 1
