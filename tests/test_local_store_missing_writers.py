"""Tests for the 4 ingest helpers + query methods that close the
schema-vs-writer gap Engineer B found in the e2e audit:

  openclaw_channels  — ingest_channel + query_channels
  crons              — ingest_cron + query_crons
  subagents          — ingest_subagent + query_subagents
  system_snapshots   — ingest_system_snapshot + query_system_snapshots

Each round-trips a typical row, verifies upsert semantics, JSON-blob
decoding on read, and filter combinations the dashboard will use.
"""

from __future__ import annotations

import importlib
import time

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh isolated DuckDB per test."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=False)


# ── openclaw_channels ──────────────────────────────────────────────────────

def test_ingest_channel_round_trip(store):
    store.ingest_channel({
        "session_id": "s1",
        "channel": "telegram",
        "chat_type": "private",
        "subject": "Vivek",
        "origin_label": "Vivek Chand id:1532693273",
    })
    rows = store.query_channels(session_id="s1")
    assert len(rows) == 1
    r = rows[0]
    assert r["channel"] == "telegram"
    assert r["chat_type"] == "private"
    assert r["subject"] == "Vivek"
    assert r["origin_label"] == "Vivek Chand id:1532693273"


def test_ingest_channel_upsert_partial(store):
    """Subsequent ingest with subset of fields should COALESCE — not null
    out the columns we didn't include."""
    store.ingest_channel({"session_id": "s1", "channel": "slack",
                          "subject": "#engineering"})
    store.ingest_channel({"session_id": "s1", "subject": "#prod-incidents"})
    rows = store.query_channels(session_id="s1")
    assert rows[0]["channel"] == "slack"  # COALESCE preserved
    assert rows[0]["subject"] == "#prod-incidents"  # overwritten


def test_ingest_channel_requires_session_id(store):
    with pytest.raises(ValueError, match="session_id"):
        store.ingest_channel({"channel": "telegram"})


def test_query_channels_filter_by_channel(store):
    store.ingest_channel({"session_id": "s1", "channel": "telegram"})
    store.ingest_channel({"session_id": "s2", "channel": "slack"})
    store.ingest_channel({"session_id": "s3", "channel": "telegram"})
    tg = store.query_channels(channel="telegram")
    assert {r["session_id"] for r in tg} == {"s1", "s3"}


# ── crons ──────────────────────────────────────────────────────────────────

def test_ingest_cron_round_trip(store):
    store.ingest_cron({
        "cron_id": "daily-backup",
        "name": "Daily Backup",
        "schedule": "0 3 * * *",
        "enabled": True,
        "last_run_at": "2026-05-12T03:00:00Z",
        "last_status": "success",
        "next_run_at": "2026-05-13T03:00:00Z",
        "anchor_ms": 1715479200000,
    })
    rows = store.query_crons()
    assert len(rows) == 1
    r = rows[0]
    assert r["cron_id"] == "daily-backup"
    assert r["name"] == "Daily Backup"
    assert r["schedule"] == "0 3 * * *"
    assert r["enabled"] is True
    assert r["last_status"] == "success"
    # Freeform extras land in `data` and decode back to dict
    assert isinstance(r["data"], dict)
    assert r["data"]["anchor_ms"] == 1715479200000


def test_ingest_cron_upsert_changes_status(store):
    store.ingest_cron({"cron_id": "c1", "enabled": True, "last_status": "running"})
    store.ingest_cron({"cron_id": "c1", "enabled": True, "last_status": "success"})
    rows = store.query_crons()
    assert len(rows) == 1
    assert rows[0]["last_status"] == "success"


def test_query_crons_enabled_only(store):
    store.ingest_cron({"cron_id": "c1", "enabled": True})
    store.ingest_cron({"cron_id": "c2", "enabled": False})
    enabled = store.query_crons(enabled_only=True)
    assert {r["cron_id"] for r in enabled} == {"c1"}
    all_ = store.query_crons()
    assert {r["cron_id"] for r in all_} == {"c1", "c2"}


# ── subagents ──────────────────────────────────────────────────────────────

def test_ingest_subagent_round_trip(store):
    store.ingest_subagent({
        "subagent_id": "sa-1",
        "parent_session_id": "parent-s1",
        "spawned_at": "2026-05-12T07:00:00Z",
        "task": "deep-dive: refactor auth",
        "status": "running",
        "cost_usd": 0.045,
        "token_count": 8500,
    })
    rows = store.query_subagents(parent_session_id="parent-s1")
    assert len(rows) == 1
    r = rows[0]
    assert r["subagent_id"] == "sa-1"
    assert r["task"] == "deep-dive: refactor auth"
    assert r["status"] == "running"
    assert r["cost_usd"] == 0.045
    assert r["token_count"] == 8500


def test_subagent_status_filter(store):
    store.ingest_subagent({"subagent_id": "a", "status": "running"})
    store.ingest_subagent({"subagent_id": "b", "status": "completed"})
    store.ingest_subagent({"subagent_id": "c", "status": "running"})
    running = store.query_subagents(status="running")
    assert {r["subagent_id"] for r in running} == {"a", "c"}


def test_subagent_upsert_preserves_spawned_at(store):
    """spawned_at should be COALESCEd (first-write-wins); status should
    update on each ingest."""
    store.ingest_subagent({"subagent_id": "x", "spawned_at": "T1", "status": "running"})
    store.ingest_subagent({"subagent_id": "x", "status": "completed"})
    rows = store.query_subagents()
    assert rows[0]["spawned_at"] == "T1"
    assert rows[0]["status"] == "completed"


# ── system_snapshots ───────────────────────────────────────────────────────

def test_ingest_system_snapshot_round_trip(store):
    snap = {
        "node_id": "agent+macbook",
        "ts": "2026-05-12T07:00:00Z",
        "kind": "cpu",
        "load_1": 1.23,
        "load_5": 0.95,
        "load_15": 0.80,
        "cores": 12,
    }
    store.ingest_system_snapshot(snap)
    rows = store.query_system_snapshots()
    assert len(rows) == 1
    r = rows[0]
    assert r["node_id"] == "agent+macbook"
    assert r["kind"] == "cpu"
    assert isinstance(r["data"], dict)
    assert r["data"]["load_1"] == 1.23
    assert r["data"]["cores"] == 12


def test_snapshot_pk_dedup(store):
    """Same (agent_type, node_id, ts, kind) tuple — second insert is silently
    ignored (INSERT OR IGNORE)."""
    snap = {"node_id": "n1", "ts": "T1", "kind": "mem", "used_gb": 8}
    store.ingest_system_snapshot(snap)
    store.ingest_system_snapshot({**snap, "used_gb": 999})  # dup PK
    rows = store.query_system_snapshots(node_id="n1", kind="mem")
    assert len(rows) == 1
    assert rows[0]["data"]["used_gb"] == 8  # original kept


def test_snapshot_filter_by_kind(store):
    store.ingest_system_snapshot({"node_id": "n", "ts": "T1", "kind": "cpu"})
    store.ingest_system_snapshot({"node_id": "n", "ts": "T2", "kind": "mem"})
    store.ingest_system_snapshot({"node_id": "n", "ts": "T3", "kind": "cpu"})
    cpu = store.query_system_snapshots(kind="cpu")
    assert len(cpu) == 2
    assert all(r["kind"] == "cpu" for r in cpu)


def test_snapshot_requires_node_id_ts_kind(store):
    with pytest.raises(ValueError):
        store.ingest_system_snapshot({"node_id": "n", "ts": "T1"})  # no kind
    with pytest.raises(ValueError):
        store.ingest_system_snapshot({"node_id": "n", "kind": "cpu"})  # no ts
    with pytest.raises(ValueError):
        store.ingest_system_snapshot({"ts": "T1", "kind": "cpu"})  # no node


# ── parity sanity: existing tables still work ──────────────────────────────

def test_existing_ingest_paths_unaffected(store):
    """The new helpers shouldn't have broken the existing event/session paths."""
    store.ingest({"id": "e1", "node_id": "n", "event_type": "tool_call",
                  "session_id": "ses1",
                  "ts": str(int(time.time() * 1000))})
    store.ingest_session({"session_id": "ses1", "title": "test"})
    time.sleep(0.2)
    assert len(store.query_events(limit=10)) == 1
    # query_sessions reads from events GROUPed by session_id (not the
    # sessions table) — so we need an event with a session_id to see it.
    assert len(store.query_sessions(limit=10)) == 1
