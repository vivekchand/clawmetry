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


def test_integrity_on_by_default(tmp_path, monkeypatch):
    """The tamper-evident chain is a Free, always-on feature: with no
    CLAWMETRY_INTEGRITY env var set it must default ON and stamp new events
    (regression for the Security integrity card showing a perpetual 'empty'
    state because the chain was opt-in / off by default)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.delenv("CLAWMETRY_INTEGRITY", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    assert ls._INTEGRITY_ENABLED is True, "integrity must be ON by default"
    s = ls.LocalStore()
    s.start()
    try:
        for _ in range(3):
            s.ingest(_ev(node_id="node-a"))
        _flush(s)
        res = s.verify_integrity()
        assert res["status"] == "valid", res
        assert res["checked"] >= 3, res
    finally:
        s.stop(flush=True)


def test_batched_dedup_redelivery_keeps_chain_valid(store_with_integrity):
    """The batched dedup (one IN(...) lookup per flush instead of a SELECT per
    event) must behave like the per-event version: a re-delivered, already
    stamped event is NOT re-stamped, so the chain stays valid and length is
    unchanged. Exercises a flush batch with both fresh and already-stamped ids."""
    s = store_with_integrity
    evs = [_ev(node_id="node-a") for _ in range(8)]
    for e in evs:
        s.ingest(e)
    _flush(s)
    first = s.verify_integrity()
    assert first["status"] == "valid", first
    n1 = first["checked"]
    # Re-deliver the SAME events (idempotent INSERT OR IGNORE) plus a couple new
    # ones in one batch: the already-stamped ids must be skipped, not re-stamped.
    for e in evs:
        s.ingest(dict(e))
    for _ in range(2):
        s.ingest(_ev(node_id="node-a"))
    _flush(s)
    second = s.verify_integrity()
    assert second["status"] == "valid", second
    # Only the 2 genuinely new events get stamped; re-deliveries are skipped.
    assert second["checked"] == n1 + 2, (n1, second["checked"])


def test_multi_runtime_batch_verifies_regardless_of_arrival_order(store_with_integrity):
    """The false positive that painted "Tampered" on healthy nodes.

    The chain is BUILT per flush batch sorted by ``id`` (lexicographic); the
    verifier used to WALK rows ordered by ``created_at`` (arrival order). On a
    multi-runtime node those orders differ — ids like ``claude_code:…`` <
    ``hermes:…`` < ``picoclaw:…`` chain in one order while arriving in another
    — so the walk hit a row whose ``chain_prev_hash`` was not the previous
    row's hash and reported a break at the first boundary. Verification now
    follows the ``chain_prev_hash`` links, so arrival order cannot matter.
    """
    s = store_with_integrity
    # Ingest in an order deliberately REVERSED from the id sort the stamper uses.
    for prefix in ("picoclaw", "hermes", "claude_code"):
        for i in range(4):
            s.ingest(_ev(node_id="node-a", id="{}:{:02d}".format(prefix, i)))
    _flush(s)
    result = s.verify_integrity()
    assert result["status"] == "valid", result
    assert result["checked"] == 12, result


def test_redelivery_mid_batch_does_not_fork_the_chain(store_with_integrity):
    """Second break generator: an already-stamped id inside a fresh batch used
    to rewind the running head to that row's stored hash, so every later NEW
    row in the batch chained off an old predecessor — forking the chain against
    the row that already claimed it. Re-delivery is routine here (the daemon
    re-tails JSONL, family adapters re-scan the most recent N sessions each
    tick, numbat's HTTP sink retries by design)."""
    s = store_with_integrity
    old = [_ev(node_id="node-a", id="aaa:{:02d}".format(i)) for i in range(3)]
    for e in old:
        s.ingest(e)
    _flush(s)
    assert s.verify_integrity()["status"] == "valid"
    # A batch that INTERLEAVES a re-delivery with new rows sorting after it.
    s.ingest(dict(old[0]))
    for i in range(3):
        s.ingest(_ev(node_id="node-a", id="zzz:{:02d}".format(i)))
    s.ingest(dict(old[2]))
    _flush(s)
    result = s.verify_integrity()
    assert result["status"] == "valid", result
    assert result["checked"] == 6, result


def test_verify_still_catches_a_deleted_event(store_with_integrity):
    """Link-following must not be softer than the old walk: removing an event
    from the middle orphans its successors and has to be reported."""
    s = store_with_integrity
    for i in range(6):
        s.ingest(_ev(node_id="node-a", id="ev:{:02d}".format(i)))
    _flush(s)
    assert s.verify_integrity()["status"] == "valid"
    s._conn.execute("DELETE FROM events WHERE id = 'ev:02'")
    result = s.verify_integrity()
    assert result["status"] == "invalid", result
    assert result["broken_at"], result


def test_two_batches_in_one_millisecond_are_not_reported_as_tampering(store_with_integrity):
    """The false positive the founder hit, reproduced exactly.

    Each flush batch is chained independently, sorted by ``id``. The verifier
    used to walk ``ORDER BY node_id, created_at, id`` and assert row N+1's
    ``chain_prev_hash`` equalled row N's ``chain_hash`` — which silently
    assumed one batch per ``created_at`` millisecond. When two batches land in
    the SAME millisecond, that ORDER BY interleaves two independently chained
    runs by id, so the links no longer line up and the tab painted "Tampered ·
    the activity log may have been altered" over a log where nothing had been
    touched. Live evidence on the reporter's node: 42,110 stamped events, 0
    content mismatches, 4,510 fork points.

    ``created_at`` is not part of the hash, so forcing it equal here changes no
    fingerprint — it just makes the millisecond collision deterministic.
    """
    s = store_with_integrity
    for eid in ("a:1", "c:1"):          # batch 1 chains a:1 -> c:1
        s.ingest(_ev(node_id="node-a", id=eid))
    _flush(s)
    for eid in ("b:1", "d:1"):          # batch 2 chains b:1 -> d:1
        s.ingest(_ev(node_id="node-a", id=eid))
    _flush(s)
    # Same millisecond for every row: id order (a, b, c, d) now interleaves the
    # two chained runs (a->c and b->d).
    s._conn.execute("UPDATE events SET created_at = 1000")
    result = s.verify_integrity()
    assert result["status"] == "valid", result
    assert result["checked"] == 4, result


def test_forked_chain_is_degraded_not_tampered(store_with_integrity):
    """A fork means the ordering is unprovable, NOT that data changed.

    Forks are what ClawMetry's own writer produced for months, so reporting
    them as tampering cried wolf. Every event still has to match its own hash;
    the verdict says the ordering is incomplete and says so separately.
    """
    s = store_with_integrity
    for i in range(4):
        s.ingest(_ev(node_id="node-a", id="ev:{:02d}".format(i)))
    _flush(s)
    assert s.verify_integrity()["status"] == "valid"
    # Re-point one event at an earlier predecessor, re-stamping its own hash so
    # the CONTENT check still passes — a pure linkage fork.
    row = s._conn.execute(
        "SELECT id, node_id, agent_type, agent_id, session_id, workspace_id,"
        " event_type, ts FROM events WHERE id = 'ev:03'"
    ).fetchone()
    genesis_hash = s._conn.execute(
        "SELECT chain_hash FROM events WHERE id = 'ev:00'"
    ).fetchone()[0]
    ed = dict(zip(
        ("id", "node_id", "agent_type", "agent_id", "session_id",
         "workspace_id", "event_type", "ts"), row,
    ))
    import clawmetry.local_store as _ls
    s._conn.execute(
        "UPDATE events SET chain_prev_hash = ?, chain_hash = ? WHERE id = 'ev:03'",
        [genesis_hash, _ls._integrity_hash(genesis_hash, ed)],
    )
    result = s.verify_integrity()
    assert result["status"] == "degraded", result
    assert result["unlinked"] == 1, result
    assert result["fork_points"] == 1, result
    assert result["broken_at"] is None
    assert "altered or removed" in (result["error"] or "")
