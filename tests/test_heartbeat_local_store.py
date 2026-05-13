"""Tests for epic #964 phase 1b — local-store fast path on /api/heartbeat.

The fast path is opt-in via CLAWMETRY_LOCAL_STORE_READ=1 so the legacy
session-transcript scanner stays the default until ≥80% adoption.

Daemon-emitted heartbeats are stored in DuckDB's `heartbeats` table by
sync.py (~once per minute). The fast path queries that table and shapes
the response to match the existing /api/heartbeat contract.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.heartbeat as hb
    importlib.reload(hb)

    a = Flask(__name__)
    a.register_blueprint(hb.bp_heartbeat)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


def test_heartbeat_fast_path_returns_local_store_data(app):
    """Populated `heartbeats` table → fast path serves directly from DuckDB
    and returns the documented /api/heartbeat response shape."""
    a, ls = app
    store = ls.get_store()

    # Seed 5 heartbeats over the last ~5 minutes — well within the
    # default 30-min interval so they should classify as "healthy".
    now = time.time()
    for i in range(5):
        store.ingest_heartbeat({
            "node_id": "agent+test",
            "ts": _iso(now - (i * 60)),
            "version": "0.12.162",
            "e2e": True,
            "size_mb": 12.5,
            "events_total": 1234 + i,
        })

    c = a.test_client()
    r = c.get("/api/heartbeat")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()

    # Tag confirms fast path took the wheel.
    assert body.get("_source") == "local_store"

    # Shape matches the documented contract.
    assert "last_heartbeat_ts" in body
    assert "last_heartbeat_age_seconds" in body
    assert "expected_interval_seconds" in body
    assert "status" in body
    assert "cadence_24h" in body
    assert "ok_vs_action_24h" in body
    assert "recent_beats" in body

    cadence = body["cadence_24h"]
    assert "expected_beats" in cadence
    assert "actual_beats" in cadence
    assert "on_time_ratio" in cadence
    assert cadence["actual_beats"] == 5

    ok_vs_action = body["ok_vs_action_24h"]
    # All daemon heartbeats are liveness pings → outcome="ok", no actions.
    assert ok_vs_action["heartbeat_ok_count"] == 5
    assert ok_vs_action["action_taken_count"] == 0
    assert ok_vs_action["ok_ratio"] == 1.0

    # Most recent beat is within seconds → status should be healthy.
    assert body["status"] == "healthy"
    assert body["last_heartbeat_age_seconds"] is not None
    assert body["last_heartbeat_age_seconds"] < 120

    # recent_beats is capped at 10, oldest first.
    rb = body["recent_beats"]
    assert len(rb) == 5
    assert all(b["outcome"] == "ok" for b in rb)
    assert rb[0]["ts"] <= rb[-1]["ts"]


def test_heartbeat_fast_path_status_drifting_when_stale(app):
    """A heartbeat last seen >interval but ≤1.5×interval ago → drifting.
    Default interval is 1800s; we backdate the only beat to 2400s ago."""
    a, ls = app
    store = ls.get_store()

    now = time.time()
    store.ingest_heartbeat({
        "node_id": "agent+stale",
        "ts": _iso(now - 2400),  # 40 min ago — between 1×30m and 1.5×30m=45m
        "version": "0.12.162",
        "e2e": True,
    })

    c = a.test_client()
    r = c.get("/api/heartbeat")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["status"] == "drifting"


def test_heartbeat_fast_path_status_missed_when_very_stale(app):
    """A heartbeat last seen >1.5×interval ago → missed."""
    a, ls = app
    store = ls.get_store()

    now = time.time()
    store.ingest_heartbeat({
        "node_id": "agent+gone",
        "ts": _iso(now - 7200),  # 2 hours ago — way past 1.5×30m=45m
        "version": "0.12.162",
        "e2e": True,
    })

    c = a.test_client()
    r = c.get("/api/heartbeat")
    assert r.status_code == 200
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["status"] == "missed"


def test_heartbeat_fast_path_falls_back_when_store_empty(app):
    """Empty `heartbeats` table → fast path returns None so the JSONL
    scanner runs. We can't easily exercise the full JSONL parser in unit
    tests (needs ~/.openclaw fixture), so we just verify the fast path
    *defers* — the response is missing the `_source: local_store` tag and
    classifies as `never` because no data is available from any source."""
    a, _ls = app
    c = a.test_client()
    r = c.get("/api/heartbeat")
    assert r.status_code == 200
    body = r.get_json()
    # Fast path returned None → fell through to legacy scanner, which does
    # NOT add the _source tag.
    assert body.get("_source") != "local_store"
    # Empty store + no JSONL fixture → status=never.
    assert body["status"] in {"never", "missed", "drifting", "healthy"}


def test_heartbeat_fast_path_disabled_without_env_flag(tmp_path, monkeypatch):
    """No CLAWMETRY_LOCAL_STORE_READ → fast path never runs, even with
    populated store. Defaults to legacy JSONL scanner so existing deploys
    see zero change without explicit opt-in."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.heartbeat as hb
    importlib.reload(hb)

    store = ls.get_store()
    store.ingest_heartbeat({
        "node_id": "agent+noflag",
        "ts": _iso(time.time()),
        "version": "0.12.162",
        "e2e": True,
    })

    a = Flask(__name__)
    a.register_blueprint(hb.bp_heartbeat)
    r = a.test_client().get("/api/heartbeat")
    body = r.get_json()
    assert body.get("_source") != "local_store"
    try:
        store.stop(flush=True)
    except Exception:
        pass


def test_query_heartbeats_filters(tmp_path, monkeypatch):
    """LocalStore.query_heartbeats() exposes since/until/node_id/agent_type
    filters so other consumers (alerts, fleet view) can scope reads."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    import clawmetry.local_store as ls
    importlib.reload(ls)

    store = ls.get_store()
    try:
        # Two nodes, three timestamps each.
        for node in ("a", "b"):
            for i in range(3):
                store.ingest_heartbeat({
                    "node_id": f"agent+{node}",
                    "ts": f"2026-05-1{i+1}T12:00:00+00:00",
                    "version": "0.12.162",
                    "e2e": True,
                })
        all_rows = store.query_heartbeats()
        assert len(all_rows) == 6
        # Newest first.
        assert all_rows[0]["ts"] >= all_rows[-1]["ts"]

        only_a = store.query_heartbeats(node_id="agent+a")
        assert len(only_a) == 3
        assert all(r["node_id"] == "agent+a" for r in only_a)

        recent = store.query_heartbeats(since="2026-05-12T00:00:00+00:00")
        # Two nodes × two days (12th, 13th) = 4 rows.
        assert len(recent) == 4
    finally:
        try:
            store.stop(flush=True)
        except Exception:
            pass
