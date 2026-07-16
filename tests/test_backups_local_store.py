"""Tests for issue #3696 — OpenClaw backup/snapshot lifecycle observability.

Verifies that:
  1. ingest_backup_record() stores records with correct fields.
  2. query_backups() returns them sorted newest-first and honours filters.
  3. Re-ingesting the same backup_id updates verify_status without duplicating.
  4. GET /api/backups returns the expected JSON shape and derives
     last_backup_ts / last_verify_status correctly.
  5. An empty DuckDB (no backups) returns a valid empty response.
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store_and_app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.health as rh
    importlib.reload(rh)

    store = ls.get_store()
    _seed_store(store)

    app = Flask(__name__)
    app.register_blueprint(rh.bp_health)
    yield store, app
    try:
        store.stop(flush=True)
    except Exception:
        pass


@pytest.fixture()
def empty_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "empty.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.health as rh
    importlib.reload(rh)

    store = ls.get_store()
    app = Flask(__name__)
    app.register_blueprint(rh.bp_health)
    yield store, app
    try:
        store.stop(flush=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def _seed_store(store, *, node_id: str = "node-1") -> None:
    """Seed three backup records:
      - global ok  (2026-07-10)
      - per-agent pending (2026-07-12, newer)
      - global failed (2026-07-08, oldest)
    """
    store.ingest_backup_record({
        "backup_id":       "global_backup_20260710_120000",
        "node_id":         node_id,
        "ts":              "2026-07-10T12:00:00",
        "backup_type":     "global",
        "agent_id":        None,
        "scope":           "sqlite",
        "file_path":       "/home/user/.openclaw/backups/global_backup_20260710_120000.sqlite",
        "file_size_bytes": 1048576,
        "verify_status":   "ok",
        "verify_ts":       "2026-07-10T12:01:00",
    })
    store.ingest_backup_record({
        "backup_id":       "agent_backup_20260712_090000_main",
        "node_id":         node_id,
        "ts":              "2026-07-12T09:00:00",
        "backup_type":     "agent",
        "agent_id":        "main",
        "scope":           "sqlite",
        "file_path":       "/home/user/.openclaw/backups/agent_backup_20260712_090000_main.sqlite",
        "file_size_bytes": 524288,
        "verify_status":   "pending",
        "verify_ts":       None,
    })
    store.ingest_backup_record({
        "backup_id":       "global_backup_20260708_080000",
        "node_id":         node_id,
        "ts":              "2026-07-08T08:00:00",
        "backup_type":     "global",
        "agent_id":        None,
        "scope":           "sqlite",
        "file_path":       "/home/user/.openclaw/backups/global_backup_20260708_080000.sqlite",
        "file_size_bytes": 1000000,
        "verify_status":   "failed",
        "verify_ts":       "2026-07-08T08:02:00",
    })


# ---------------------------------------------------------------------------
# Unit tests — query_backups()
# ---------------------------------------------------------------------------

def test_query_backups_returns_three_rows(store_and_app):
    store, _ = store_and_app
    rows = store.query_backups()
    assert len(rows) == 3


def test_query_backups_sorted_newest_first(store_and_app):
    store, _ = store_and_app
    rows = store.query_backups()
    timestamps = [r["ts"] for r in rows]
    assert timestamps == sorted(timestamps, reverse=True)


def test_query_backups_filter_by_backup_type(store_and_app):
    store, _ = store_and_app
    global_rows = store.query_backups(backup_type="global")
    assert all(r["backup_type"] == "global" for r in global_rows)
    assert len(global_rows) == 2

    agent_rows = store.query_backups(backup_type="agent")
    assert len(agent_rows) == 1
    assert agent_rows[0]["agent_id"] == "main"


def test_query_backups_filter_by_node_id(store_and_app):
    store, _ = store_and_app
    rows = store.query_backups(node_id="node-1")
    assert len(rows) == 3

    rows_none = store.query_backups(node_id="node-nonexistent")
    assert rows_none == []


def test_query_backups_limit(store_and_app):
    store, _ = store_and_app
    rows = store.query_backups(limit=2)
    assert len(rows) == 2
    # Should be the two newest
    assert rows[0]["ts"] == "2026-07-12T09:00:00"
    assert rows[1]["ts"] == "2026-07-10T12:00:00"


def test_query_backups_correct_fields(store_and_app):
    store, _ = store_and_app
    rows = store.query_backups(backup_type="global", limit=1)
    row = rows[0]  # newest global = 2026-07-10
    assert row["backup_id"] == "global_backup_20260710_120000"
    assert row["verify_status"] == "ok"
    assert row["file_size_bytes"] == 1048576
    assert row["scope"] == "sqlite"


def test_ingest_backup_record_idempotent_verify_update(store_and_app):
    """Re-ingesting the same backup_id with a new verify_status must update
    the status without creating a duplicate row."""
    store, _ = store_and_app
    store.ingest_backup_record({
        "backup_id":      "agent_backup_20260712_090000_main",
        "node_id":        "node-1",
        "ts":             "2026-07-12T09:00:00",
        "backup_type":    "agent",
        "verify_status":  "ok",
        "verify_ts":      "2026-07-12T09:01:30",
    })
    rows = store.query_backups()
    assert len(rows) == 3  # still 3, not 4
    agent_row = next(r for r in rows if r["backup_id"] == "agent_backup_20260712_090000_main")
    assert agent_row["verify_status"] == "ok"
    assert agent_row["verify_ts"] == "2026-07-12T09:01:30"


def test_ingest_backup_record_missing_id_raises(store_and_app):
    store, _ = store_and_app
    with pytest.raises(ValueError, match="backup_id"):
        store.ingest_backup_record({"node_id": "node-1", "ts": "2026-07-13T00:00:00"})


# ---------------------------------------------------------------------------
# API tests — GET /api/backups
# ---------------------------------------------------------------------------

def test_api_backups_returns_200(store_and_app):
    _, app = store_and_app
    with app.test_client() as c:
        resp = c.get("/api/backups")
    assert resp.status_code == 200


def test_api_backups_response_shape(store_and_app):
    _, app = store_and_app
    with app.test_client() as c:
        data = c.get("/api/backups").get_json()
    assert "backups" in data
    assert "count" in data
    assert "last_backup_ts" in data
    assert "last_verify_status" in data


def test_api_backups_derives_last_backup_ts(store_and_app):
    _, app = store_and_app
    with app.test_client() as c:
        data = c.get("/api/backups").get_json()
    # Newest record is 2026-07-12
    assert data["last_backup_ts"] == "2026-07-12T09:00:00"


def test_api_backups_derives_last_verify_status(store_and_app):
    _, app = store_and_app
    with app.test_client() as c:
        data = c.get("/api/backups").get_json()
    # First record with a non-null verify_status (newest-first = pending)
    assert data["last_verify_status"] == "pending"


def test_api_backups_empty_store(empty_store):
    _, app = empty_store
    with app.test_client() as c:
        resp = c.get("/api/backups")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["backups"] == []
    assert data["count"] == 0
    assert data["last_backup_ts"] is None
    assert data["last_verify_status"] is None


def test_api_backups_limit_param(store_and_app):
    _, app = store_and_app
    with app.test_client() as c:
        data = c.get("/api/backups?limit=1").get_json()
    assert data["count"] == 1


def test_api_backups_backup_type_filter(store_and_app):
    _, app = store_and_app
    with app.test_client() as c:
        data = c.get("/api/backups?backup_type=agent").get_json()
    assert data["count"] == 1
    assert data["backups"][0]["backup_type"] == "agent"
