"""Tests for LocalStore.prune_events_by_age (per-tier retention, #2262).

Covers:
* Deletes only events older than the cutoff
* None / 0 / negative retention is a no-op
* Read-only stores refuse
* Returns the expected stats shape
* End-to-end retention values via Entitlement.event_retention_days()
"""
from __future__ import annotations

import importlib
import time
import uuid

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=True)


def _ev(**overrides):
    base = {
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "session_id": "sess-1",
        "event_type": "tool_call",
        "ts": "2026-05-10T12:00:00Z",
        "data": {"x": 1},
    }
    base.update(overrides)
    return base


def _wait_for_flush(s, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if s.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError("flusher did not drain ring in time")


# ── no-op contracts ───────────────────────────────────────────────────────────


def test_none_retention_is_noop(store):
    store.ingest(_ev())
    _wait_for_flush(store)
    res = store.prune_events_by_age(None)
    assert res["deleted_rows"] == 0
    assert res.get("skipped") is True


def test_zero_retention_is_noop(store):
    store.ingest(_ev())
    _wait_for_flush(store)
    res = store.prune_events_by_age(0)
    assert res["deleted_rows"] == 0
    assert res.get("skipped") is True


def test_negative_retention_is_noop(store):
    res = store.prune_events_by_age(-1)
    assert res["deleted_rows"] == 0


# ── delete-by-age happy path ─────────────────────────────────────────────────


def test_prunes_only_rows_older_than_cutoff(store):
    # Insert two events; back-date one's created_at to 10 days ago.
    e_old = _ev(id="old-1")
    e_new = _ev(id="new-1")
    store.ingest(e_old)
    store.ingest(e_new)
    _wait_for_flush(store)

    # Back-date the "old" row in place so we don't have to mock time.time
    # inside the flusher. created_at is BIGINT millis.
    ten_days_ago_ms = int((time.time() - 10 * 86400) * 1000)
    with store._write_lock:
        store._conn.execute(
            "UPDATE events SET created_at = ? WHERE id = ?",
            [ten_days_ago_ms, "old-1"],
        )

    # Retention = 7 days → "old" must go, "new" stays.
    res = store.prune_events_by_age(7)
    assert res["deleted_rows"] == 1
    assert res["before_rows"] == 2
    assert res["after_rows"] == 1

    rows = store._fetch("SELECT id FROM events ORDER BY id", [])
    remaining = {r[0] for r in rows}
    assert "new-1" in remaining
    assert "old-1" not in remaining


def test_prune_keeps_everything_when_cutoff_is_in_the_past(store):
    store.ingest(_ev(id="a"))
    store.ingest(_ev(id="b"))
    _wait_for_flush(store)
    # 365-day retention with all fresh rows → nothing to delete.
    res = store.prune_events_by_age(365)
    assert res["deleted_rows"] == 0
    assert res["before_rows"] == res["after_rows"] == 2


def test_prune_uses_explicit_now_argument(store):
    store.ingest(_ev(id="x"))
    _wait_for_flush(store)
    # Set "now" 30 days in the future relative to the row's actual
    # created_at — the row is now "30 days old" from the prune's
    # perspective, so a 7-day retention should delete it.
    future_now = time.time() + 30 * 86400
    res = store.prune_events_by_age(7, now=future_now)
    assert res["deleted_rows"] == 1
    assert res["after_rows"] == 0


# ── stats shape ──────────────────────────────────────────────────────────────


def test_returns_expected_stats_shape(store):
    res = store.prune_events_by_age(90)
    assert set(res.keys()) >= {"deleted_rows", "before_rows", "after_rows", "cutoff_ts"}


# ── read-only safety ─────────────────────────────────────────────────────────


def test_read_only_store_refuses(store):
    store._read_only = True
    with pytest.raises(RuntimeError):
        store.prune_events_by_age(7)


# ── end-to-end via Entitlement ───────────────────────────────────────────────


def test_entitlement_retention_value_drives_prune(store, monkeypatch, tmp_path):
    """Pass Entitlement.event_retention_days() straight in — the prune
    must accept it and behave per the catalogue."""
    import clawmetry.entitlements as _ent

    monkeypatch.setenv("HOME", str(tmp_path / "hm"))
    importlib.reload(_ent)
    _ent.invalidate()

    en = _ent.get_entitlement(force=True)
    days = en.event_retention_days()
    assert days == 7  # OSS default
    # No rows yet; just confirms the integration call path works.
    res = store.prune_events_by_age(days)
    assert "deleted_rows" in res
