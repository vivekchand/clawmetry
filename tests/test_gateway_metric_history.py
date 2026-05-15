"""Tests for the gateway.metric history surface (issue #852 follow-up).

PR #1146 added the live ``compute_gateway_health()`` snapshot. This PR
persists that snapshot every 30s into DuckDB as ``event_type="gateway.metric"``
events and exposes a 24h history endpoint for the dashboard sparkline.

Coverage:

  1. ``capture_gateway_metric()`` writes one row per call when conditions are
     met (gateway running, rate window elapsed, not deduped).
  2. Dedupe logic — a near-identical sample within the 5-min window is a
     no-op; a PID change / large RSS swing / 5 min elapsed all trigger a
     write.
  3. ``/api/gateway-health/history`` returns daemon-written rows sorted ASC,
     and an empty list (not a 4xx) when no events exist.
  4. The PR #1146 live snapshot endpoint (``/api/gateway-health``) keeps
     working — regression check that the new field/endpoint didn't break
     the existing surface.
  5. ``/api/system-health`` carries the new ``gateway.history`` summary
     (count/min/max/avg rss_mb).
"""
from __future__ import annotations

import importlib
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Helpers ────────────────────────────────────────────────────────────────


def _wait_flush(store, t=2.0):
    """Block until the local-store ring has drained to DuckDB."""
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _seed_metric_event(store, *, ts_iso, rss_mb, cpu_pct=1.0, pid=4242):
    """Insert a single ``gateway.metric`` event at the given ISO timestamp.

    Mirrors what ``sync.capture_gateway_metric`` writes so the read-side
    tests don't have to monkeypatch the daemon helper.
    """
    store.ingest({
        "id":         uuid.uuid4().hex,
        "node_id":    "test-node",
        "agent_id":   "openclaw-gateway",
        "agent_type": "openclaw",
        "event_type": "gateway.metric",
        "ts":         ts_iso,
        "data":       {
            "rss_mb":         rss_mb,
            "cpu_pct":        cpu_pct,
            "pid":            pid,
            "uptime_seconds": 60,
        },
    })


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Reload ``clawmetry.local_store`` against a fresh DuckDB file."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    store = ls.get_store()
    yield ls, store
    try:
        store.stop(flush=False)
    except Exception:
        pass


@pytest.fixture
def health_app(fresh_store, tmp_path, monkeypatch):
    """Flask app with ``bp_health`` registered against the fresh DuckDB."""
    # Force daemon-discovery path to a non-existent file so
    # ``local_store_via_daemon`` always punts to the in-process store
    # instead of crossing the wire to a developer's locally-running
    # ClawMetry daemon (which would have different data). Mirrors the
    # pattern documented in tests/test_moat_send_message_e2e.py.
    sys.modules.pop("routes.local_query", None)
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(
        lq, "_DISCOVERY_PATH", str(tmp_path / "no-such-discovery.json"),
        raising=True,
    )
    lq._invalidate_daemon_cache()

    # Ensure routes.health doesn't accidentally find a stale local_store
    # module pointing at the previous DB file.
    sys.modules.pop("routes.health", None)
    import routes.health as health_mod
    importlib.reload(health_mod)
    app = Flask(__name__)
    app.register_blueprint(health_mod.bp_health)
    yield app, health_mod, fresh_store[1]


# ── 1. Daemon capture path ─────────────────────────────────────────────────


def test_capture_gateway_metric_writes_row_when_gateway_running(fresh_store, monkeypatch):
    ls, store = fresh_store
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    # Reset module-level rate-cap state for a clean run.
    sync_mod._LAST_GATEWAY_METRIC_TS = None
    sync_mod._LAST_GATEWAY_METRIC = None
    # Stub compute_gateway_health to return a known-healthy snapshot.
    snap = {
        "pid": 4242,
        "uptime_seconds": 120,
        "rss_mb": 250.0,
        "cpu_pct": 1.5,
        "status": "healthy",
        "memory_threshold_mb": 900,
    }
    import routes.health as health_mod
    monkeypatch.setattr(health_mod, "compute_gateway_health", lambda: snap)

    assert sync_mod.capture_gateway_metric({"node_id": "test-node"}) is True

    _wait_flush(store)
    rows = store.query_events(event_type="gateway.metric", limit=10)
    assert len(rows) == 1
    assert rows[0]["agent_id"] == "openclaw-gateway"
    assert rows[0]["data"]["rss_mb"] == 250.0
    assert rows[0]["data"]["pid"] == 4242


def test_capture_gateway_metric_skips_when_not_running(fresh_store, monkeypatch):
    ls, store = fresh_store
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    sync_mod._LAST_GATEWAY_METRIC_TS = None
    sync_mod._LAST_GATEWAY_METRIC = None
    import routes.health as health_mod
    monkeypatch.setattr(health_mod, "compute_gateway_health", lambda: {
        "pid": None,
        "uptime_seconds": None,
        "rss_mb": None,
        "cpu_pct": None,
        "status": "not_running",
        "memory_threshold_mb": 900,
    })
    assert sync_mod.capture_gateway_metric({"node_id": "n"}) is False
    _wait_flush(store)
    rows = store.query_events(event_type="gateway.metric", limit=10)
    assert rows == []


def test_capture_gateway_metric_rate_cap_skips_second_call(fresh_store, monkeypatch):
    ls, store = fresh_store
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    sync_mod._LAST_GATEWAY_METRIC_TS = None
    sync_mod._LAST_GATEWAY_METRIC = None
    import routes.health as health_mod
    monkeypatch.setattr(health_mod, "compute_gateway_health", lambda: {
        "pid": 1, "uptime_seconds": 1, "rss_mb": 100.0, "cpu_pct": 0.0,
        "status": "healthy", "memory_threshold_mb": 900,
    })

    # First write succeeds, second within the 30s window is a no-op.
    assert sync_mod.capture_gateway_metric({"node_id": "n"}) is True
    assert sync_mod.capture_gateway_metric({"node_id": "n"}) is False
    _wait_flush(store)
    rows = store.query_events(event_type="gateway.metric", limit=10)
    assert len(rows) == 1


def test_should_dedupe_returns_true_for_near_identical_sample():
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    prev = {"pid": 1, "rss_mb": 200.0, "cpu_pct": 1.0, "uptime_seconds": 60}
    curr = {"pid": 1, "rss_mb": 202.0, "cpu_pct": 2.5, "uptime_seconds": 90}
    # Within 5MB / 2% CPU → dedupe.
    assert sync_mod._should_dedupe_gateway_metric(prev, curr) is True


def test_should_dedupe_returns_false_for_large_rss_swing():
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    prev = {"pid": 1, "rss_mb": 200.0, "cpu_pct": 1.0}
    curr = {"pid": 1, "rss_mb": 250.0, "cpu_pct": 1.0}
    # 50 MB swing >> 5MB tolerance → write.
    assert sync_mod._should_dedupe_gateway_metric(prev, curr) is False


def test_should_dedupe_returns_false_on_pid_change():
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    prev = {"pid": 100, "rss_mb": 200.0, "cpu_pct": 1.0}
    curr = {"pid": 200, "rss_mb": 200.0, "cpu_pct": 1.0}
    # PID changed → gateway restarted → always write.
    assert sync_mod._should_dedupe_gateway_metric(prev, curr) is False


def test_should_dedupe_first_sample_writes():
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    # No prior sample → never dedupe.
    assert sync_mod._should_dedupe_gateway_metric(
        None, {"pid": 1, "rss_mb": 100.0, "cpu_pct": 0}
    ) is False


# ── 2. Read endpoint contract ──────────────────────────────────────────────


def test_history_endpoint_returns_rows_sorted_ascending(health_app):
    app, health_mod, store = health_app
    # Seed three samples; insert them OUT OF ORDER to prove the endpoint sorts.
    now = datetime.now(timezone.utc)
    _seed_metric_event(store, ts_iso=(now - timedelta(hours=1)).isoformat(),
                       rss_mb=250.0)
    _seed_metric_event(store, ts_iso=(now - timedelta(hours=3)).isoformat(),
                       rss_mb=200.0)
    _seed_metric_event(store, ts_iso=(now - timedelta(hours=2)).isoformat(),
                       rss_mb=225.0)
    _wait_flush(store)

    with app.test_client() as c:
        resp = c.get("/api/gateway-health/history?hours=24")
        assert resp.status_code == 200
        data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 3
    # Sorted oldest → newest.
    assert data[0]["rss_mb"] == 200.0
    assert data[1]["rss_mb"] == 225.0
    assert data[2]["rss_mb"] == 250.0
    # Each row only carries ts/rss_mb/cpu_pct (small wire payload).
    for r in data:
        assert set(r.keys()) == {"ts", "rss_mb", "cpu_pct"}


def test_history_endpoint_empty_when_no_data_is_not_error(health_app):
    app, health_mod, store = health_app
    with app.test_client() as c:
        resp = c.get("/api/gateway-health/history")
        assert resp.status_code == 200
        assert resp.get_json() == []


def test_history_endpoint_honours_hours_window(health_app):
    app, health_mod, store = health_app
    now = datetime.now(timezone.utc)
    # 1 row inside the 1h window, 1 row outside (5h ago).
    _seed_metric_event(store, ts_iso=(now - timedelta(minutes=30)).isoformat(),
                       rss_mb=300.0)
    _seed_metric_event(store, ts_iso=(now - timedelta(hours=5)).isoformat(),
                       rss_mb=100.0)
    _wait_flush(store)

    with app.test_client() as c:
        resp = c.get("/api/gateway-health/history?hours=1")
        data = resp.get_json()
    assert len(data) == 1
    assert data[0]["rss_mb"] == 300.0


def test_history_endpoint_clamps_invalid_hours(health_app):
    app, health_mod, store = health_app
    with app.test_client() as c:
        # Garbage param doesn't 500 — falls back to default (24h).
        resp = c.get("/api/gateway-health/history?hours=garbage")
        assert resp.status_code == 200
        # Way-too-large value gets clamped to 168 (1 week) instead of OOMing.
        resp = c.get("/api/gateway-health/history?hours=999999")
        assert resp.status_code == 200


# ── 3. Live snapshot regression (PR #1146 still works) ─────────────────────


def test_live_snapshot_endpoint_still_works(health_app, monkeypatch):
    app, health_mod, store = health_app
    # The endpoint must keep returning the canonical 6-field shape even when
    # the history table is empty AND psutil/ps both fail.
    monkeypatch.setattr(health_mod, "compute_gateway_health", lambda: {
        "pid": None,
        "uptime_seconds": None,
        "rss_mb": None,
        "cpu_pct": None,
        "status": "not_running",
        "memory_threshold_mb": health_mod.GATEWAY_MEMORY_THRESHOLD_MB,
    })
    with app.test_client() as c:
        resp = c.get("/api/gateway-health")
        assert resp.status_code == 200
        data = resp.get_json()
    for key in ("pid", "uptime_seconds", "rss_mb", "cpu_pct", "status",
                "memory_threshold_mb"):
        assert key in data


# ── 4. /api/system-health.gateway.history summary ──────────────────────────


def test_recent_summary_helper_aggregates_last_hour(health_app):
    app, health_mod, store = health_app
    now = datetime.now(timezone.utc)
    # 3 in-window + 1 out-of-window. Min/max/avg should ignore the old one.
    _seed_metric_event(store, ts_iso=(now - timedelta(minutes=10)).isoformat(),
                       rss_mb=200.0)
    _seed_metric_event(store, ts_iso=(now - timedelta(minutes=30)).isoformat(),
                       rss_mb=300.0)
    _seed_metric_event(store, ts_iso=(now - timedelta(minutes=50)).isoformat(),
                       rss_mb=400.0)
    _seed_metric_event(store, ts_iso=(now - timedelta(hours=5)).isoformat(),
                       rss_mb=1000.0)
    _wait_flush(store)
    out = health_mod._summarise_gateway_metric_recent(minutes=60)
    assert out["count"] == 3
    assert out["min_rss_mb"] == 200.0
    assert out["max_rss_mb"] == 400.0
    assert out["avg_rss_mb"] == 300.0


def test_recent_summary_helper_returns_zero_when_no_rows(health_app):
    app, health_mod, store = health_app
    out = health_mod._summarise_gateway_metric_recent(minutes=60)
    assert out == {
        "count": 0,
        "min_rss_mb": None,
        "max_rss_mb": None,
        "avg_rss_mb": None,
    }
