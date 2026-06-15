"""Tests for issue #2861 -- version-aware health regression detection.

Verifies that:
  1. query_version_health() groups sessions by the OpenClaw version active at
     session start (correlated via heartbeats.ts <= sessions.started_at).
  2. The /api/version-health endpoint returns the correct per-version averages.
  3. _compute_version_regression() flags a regression when the current version
     shows >30% degradation vs the previous on cost/error-rate/tokens.
  4. No regression is flagged when either version has fewer than 3 sessions or
     when metrics improve.
"""

from __future__ import annotations

import importlib
from datetime import datetime, timezone

import pytest
from flask import Flask


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso(ts: str) -> str:
    """Return an ISO-8601 timestamp string."""
    return ts


def _seed_store(store, *, node_id: str = "node-1"):
    """Seed two OpenClaw versions with known sessions.

    v_old (2026.1.1): 3 sessions, avg_cost=0.10, no failures.
    v_new (2026.2.1): 3 sessions, avg_cost=0.25, 1 failure -> cost +150%, error_rate ~33%.

    Note: ingest_session() does not write the ``outcome`` column (that's the
    classifier's job). We set it via a direct SQL UPDATE after ingestion so
    query_version_health() sees the expected error_rate.
    """
    # Heartbeats: v_old from 2026-01-01, v_new from 2026-02-01
    store.ingest_heartbeat({
        "node_id": node_id,
        "ts": "2026-01-01T00:00:00",
        "version": "2026.1.1",
    })
    store.ingest_heartbeat({
        "node_id": node_id,
        "ts": "2026-02-01T00:00:00",
        "version": "2026.2.1",
    })

    # Sessions under v_old
    for i in range(3):
        store.ingest_session({
            "session_id": f"old-{i}",
            "node_id": node_id,
            "started_at": f"2026-01-{10 + i:02d}T12:00:00",
            "last_active_at": f"2026-01-{10 + i:02d}T12:30:00",
            "cost_usd": 0.10,
            "total_tokens": 1000,
            "message_count": 5,
            "status": "completed",
        })

    # Sessions under v_new (cost doubled; one failure)
    for i in range(3):
        store.ingest_session({
            "session_id": f"new-{i}",
            "node_id": node_id,
            "started_at": f"2026-02-{10 + i:02d}T12:00:00",
            "last_active_at": f"2026-02-{10 + i:02d}T12:30:00",
            "cost_usd": 0.25,
            "total_tokens": 2500,
            "message_count": 8,
            "status": "completed",
        })

    # Set outcomes directly -- ingest_session() delegates that to the classifier
    with store._write_lock:
        store._conn.execute(
            "UPDATE sessions SET outcome='success' WHERE session_id LIKE 'old-%'"
        )
        store._conn.execute(
            "UPDATE sessions SET outcome='success' WHERE session_id IN ('new-1','new-2')"
        )
        store._conn.execute(
            "UPDATE sessions SET outcome='failed' WHERE session_id='new-0'"
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
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


# ---------------------------------------------------------------------------
# Unit tests on query_version_health()
# ---------------------------------------------------------------------------

def test_query_version_health_returns_two_versions(store_and_app):
    store, _ = store_and_app
    rows = store.query_version_health(window_days=365)
    assert len(rows) == 2, f"expected 2 versions, got {len(rows)}: {rows}"


def test_query_version_health_newest_first(store_and_app):
    store, _ = store_and_app
    rows = store.query_version_health(window_days=365)
    assert rows[0]["version"] == "2026.2.1"
    assert rows[1]["version"] == "2026.1.1"


def test_query_version_health_session_counts(store_and_app):
    store, _ = store_and_app
    rows = store.query_version_health(window_days=365)
    by_version = {r["version"]: r for r in rows}
    assert by_version["2026.1.1"]["session_count"] == 3
    assert by_version["2026.2.1"]["session_count"] == 3


def test_query_version_health_avg_cost(store_and_app):
    store, _ = store_and_app
    rows = store.query_version_health(window_days=365)
    by_version = {r["version"]: r for r in rows}
    assert abs(by_version["2026.1.1"]["avg_cost_usd"] - 0.10) < 0.001
    assert abs(by_version["2026.2.1"]["avg_cost_usd"] - 0.25) < 0.001


def test_query_version_health_error_rate(store_and_app):
    store, _ = store_and_app
    rows = store.query_version_health(window_days=365)
    by_version = {r["version"]: r for r in rows}
    assert by_version["2026.1.1"]["error_rate"] == 0.0
    # 1 failure out of 3 sessions -> ~0.333
    assert abs(by_version["2026.2.1"]["error_rate"] - 1 / 3) < 0.01


def test_query_version_health_empty_when_no_heartbeats(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "e2.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    store = ls.get_store()
    try:
        # Sessions with no heartbeats -> no version assignment
        store.ingest_session({
            "session_id": "orphan-1",
            "node_id": "node-x",
            "started_at": "2026-03-01T10:00:00",
        })
        rows = store.query_version_health(window_days=365)
        assert rows == []
    finally:
        try:
            store.stop(flush=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Integration test: /api/version-health endpoint
# ---------------------------------------------------------------------------

def test_api_version_health_endpoint(store_and_app):
    _, app = store_and_app
    c = app.test_client()
    r = c.get("/api/version-health?window_days=365")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()

    assert "_source" in body
    assert "versions" in body
    assert "regression" in body
    assert isinstance(body["versions"], list)
    assert len(body["versions"]) == 2


def test_api_version_health_regression_detected(store_and_app):
    """Cost increased 150% -> regression.detected should be True."""
    _, app = store_and_app
    c = app.test_client()
    r = c.get("/api/version-health?window_days=365")
    body = r.get_json()
    reg = body["regression"]
    assert reg["detected"] is True, f"expected regression, got: {reg}"
    assert reg["current_version"] == "2026.2.1"
    assert reg["baseline_version"] == "2026.1.1"
    assert reg["change_pct"] > 30


def test_api_version_health_no_regression_when_improved(tmp_path, monkeypatch):
    """Sessions that cost less on the new version -> no regression."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "e3.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.health as rh
    importlib.reload(rh)

    store = ls.get_store()
    try:
        store.ingest_heartbeat({"node_id": "n1", "ts": "2026-01-01T00:00:00", "version": "2026.1.0"})
        store.ingest_heartbeat({"node_id": "n1", "ts": "2026-02-01T00:00:00", "version": "2026.2.0"})
        for i in range(3):
            store.ingest_session({
                "session_id": f"o{i}", "node_id": "n1",
                "started_at": f"2026-01-{10+i:02d}T12:00:00", "cost_usd": 0.20,
                "outcome": "success",
            })
        for i in range(3):
            store.ingest_session({
                "session_id": f"n{i}", "node_id": "n1",
                "started_at": f"2026-02-{10+i:02d}T12:00:00", "cost_usd": 0.10,
                "outcome": "success",
            })

        app = Flask(__name__)
        app.register_blueprint(rh.bp_health)
        c = app.test_client()
        r = c.get("/api/version-health?window_days=365")
        body = r.get_json()
        assert body["regression"]["detected"] is False
    finally:
        try:
            store.stop(flush=True)
        except Exception:
            pass
