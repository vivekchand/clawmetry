"""Tests for epic #964 — local-store fast path on the overview routes.

Covers three handlers:
  - /api/overview          (routes/overview.py)
  - /api/timeline          (routes/overview.py)
  - /api/heartbeat-status  (routes/health.py)

The fast path is opt-in via CLAWMETRY_LOCAL_STORE_READ=1 so the legacy
gateway/JSONL paths stay the default until ≥80% adoption (epic's gate).
For each route we cover:
  1. populated store + flag set    → fast path, response tagged _source=local_store
  2. empty store + flag set        → falls through (no _source tag)
  3. populated store + flag unset  → falls through (no _source tag)
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


# ─────────────────────────────────────────────────────────────────────────────
# fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def overview_app(tmp_path, monkeypatch):
    """Flask app + reloaded local_store + reloaded routes.overview blueprint."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.overview as ov
    importlib.reload(ov)

    a = Flask(__name__)
    a.register_blueprint(ov.bp_overview)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def health_app(tmp_path, monkeypatch):
    """Flask app + reloaded local_store + reloaded routes.health blueprint."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.health as hh
    importlib.reload(hh)

    a = Flask(__name__)
    a.register_blueprint(hh.bp_health)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


def _wait_flush(store, t=2.0):
    """Wait until the ring is drained to disk so SELECTs see the rows."""
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


# ─────────────────────────────────────────────────────────────────────────────
# /api/overview
# ─────────────────────────────────────────────────────────────────────────────


def test_overview_fast_path_returns_local_store_data(overview_app):
    """Populated `sessions` table → fast path serves directly from DuckDB
    and returns the documented /api/overview response shape."""
    a, ls = overview_app
    store = ls.get_store()

    store.ingest_session({
        "session_id": "sess-main-A",
        "agent_type": "openclaw",
        "title": "Refactoring overview",
        "started_at": "2026-05-11T10:00:00+00:00",
        "last_active_at": "2026-05-11T11:00:00+00:00",
        "status": "active",
        "total_tokens": 12500,
        "cost_usd": 0.42,
        "message_count": 17,
        "metadata": {"model": "claude-opus-4-7"},
    })
    store.ingest_session({
        "session_id": "sess-main-B",
        "agent_type": "openclaw",
        "title": "Older",
        "started_at": "2026-05-10T09:00:00+00:00",
        "last_active_at": "2026-05-10T10:00:00+00:00",
        "status": "ended",
        "total_tokens": 50000,
        "cost_usd": 1.7,
        "message_count": 30,
    })

    c = a.test_client()
    r = c.get("/api/overview")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()

    # Tag confirms fast path took the wheel.
    assert body.get("_source") == "local_store"

    # Shape matches the legacy contract.
    for key in (
        "model", "provider", "sessionCount", "sessions", "activeSessions",
        "mainSessionUpdated", "mainTokens", "contextWindow",
        "cronCount", "cronEnabled", "cronDisabled",
        "memoryCount", "memorySize", "system", "infra",
    ):
        assert key in body, f"missing key: {key}"

    # Content checks.
    assert body["sessionCount"] == 2
    assert body["sessions"] == 2  # alias
    assert body["activeSessions"] == 1  # only sess-main-A is active
    # Most-recent main session = sess-main-A → its total_tokens flows through.
    assert body["mainTokens"] == 12500
    assert body["model"] == "claude-opus-4-7"
    # System + infra blocks are arrays/dicts even when their subprocess probes fail.
    assert isinstance(body["system"], list)
    assert isinstance(body["infra"], dict)


def test_overview_fast_path_falls_back_when_store_empty(overview_app):
    """Empty store → fast path returns None → legacy handler runs.
    Without a gateway+sessions dir we still get a non-`_source` response."""
    a, _ls = overview_app
    c = a.test_client()
    r = c.get("/api/overview")
    body = r.get_json() or {}
    # Fast path returned None → fell through to legacy gateway path, which
    # does NOT add the _source tag.
    assert body.get("_source") != "local_store"


def test_overview_fast_path_disabled_without_flag(tmp_path, monkeypatch):
    """No CLAWMETRY_LOCAL_STORE_READ → fast path never runs even with a
    populated store. Defaults to legacy behavior so existing deploys see
    zero change without explicit opt-in."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.overview as ov
    importlib.reload(ov)

    store = ls.get_store()
    store.ingest_session({
        "session_id": "sess-noflag",
        "agent_type": "openclaw",
        "title": "Should not appear via fast path",
        "started_at": "2026-05-11T10:00:00+00:00",
        "last_active_at": "2026-05-11T10:30:00+00:00",
        "status": "active",
        "total_tokens": 999,
        "metadata": {"model": "noflag-model"},
    })

    a = Flask(__name__)
    a.register_blueprint(ov.bp_overview)
    r = a.test_client().get("/api/overview")
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"
    try:
        store.stop(flush=True)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# /api/timeline
# ─────────────────────────────────────────────────────────────────────────────


def test_timeline_fast_path_returns_local_store_data(overview_app):
    """Populated `events` table → fast path returns per-day aggregates from
    DuckDB. Today (UTC date) should appear with our seeded event count."""
    a, ls = overview_app
    store = ls.get_store()

    today = datetime.now().strftime("%Y-%m-%d")
    # Seed 4 events on today's date, two distinct hours.
    for i, hour in enumerate([9, 9, 14, 14]):
        store.ingest({
            "id": f"ev-tl-{i}",
            "node_id": "agent+test",
            "agent_id": "main",
            "session_id": "sess-tl",
            "event_type": "tool_call",
            "ts": f"{today}T{hour:02d}:30:0{i}+00:00",
            "data": {"tool": "Bash"},
            "cost_usd": 0.001,
            "token_count": 10,
            "model": "claude-opus-4-7",
        })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/timeline")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()

    assert body.get("_source") == "local_store"
    assert "days" in body
    assert "today" in body
    assert body["today"] == today

    days = body["days"]
    assert isinstance(days, list)
    # Today should be one of the days returned.
    today_entry = next((d for d in days if d["date"] == today), None)
    assert today_entry is not None, f"today {today} missing from days {[d['date'] for d in days]}"
    assert today_entry["events"] == 4
    # Per-hour bucketing should pick up our two distinct hours.
    assert today_entry["hours"].get(9) == 2 or today_entry["hours"].get("9") == 2
    assert today_entry["hours"].get(14) == 2 or today_entry["hours"].get("14") == 2
    # Shape essentials.
    assert "label" in today_entry
    assert "hasMemory" in today_entry


def test_timeline_fast_path_falls_back_when_store_empty(overview_app):
    """Empty events table → fast path returns None → legacy JSONL scanner
    runs and returns a `days` array (possibly empty) without _source tag."""
    a, _ls = overview_app
    c = a.test_client()
    r = c.get("/api/timeline")
    assert r.status_code == 200
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"
    assert "days" in body


def test_timeline_fast_path_disabled_without_flag(tmp_path, monkeypatch):
    """No CLAWMETRY_LOCAL_STORE_READ → fast path never runs even with
    populated events store."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.overview as ov
    importlib.reload(ov)

    store = ls.get_store()
    store.ingest({
        "id": "ev-tl-noflag",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "sess-tl",
        "event_type": "tool_call",
        "ts": "2026-05-11T12:00:00+00:00",
        "data": {"tool": "Bash"},
        "cost_usd": 0.001,
        "token_count": 5,
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    a = Flask(__name__)
    a.register_blueprint(ov.bp_overview)
    r = a.test_client().get("/api/timeline")
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"
    try:
        store.stop(flush=True)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# /api/heartbeat-status
# ─────────────────────────────────────────────────────────────────────────────


def test_heartbeat_status_fast_path_returns_local_store_data(health_app):
    """Populated `heartbeats` table → fast path returns the same status shape
    as the in-memory `_get_heartbeat_status()` helper."""
    a, ls = health_app
    store = ls.get_store()

    now = time.time()
    # Recent heartbeat → status "ok".
    store.ingest_heartbeat({
        "node_id": "agent+test",
        "ts": _iso(now - 30),
        "version": "0.12.162",
        "e2e": True,
    })

    c = a.test_client()
    r = c.get("/api/heartbeat-status")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()

    assert body.get("_source") == "local_store"
    # Shape matches the legacy `_get_heartbeat_status()` output.
    for key in (
        "status", "last_heartbeat_ts", "gap_seconds",
        "interval_seconds", "threshold_seconds", "silent_since",
    ):
        assert key in body, f"missing key: {key}"
    assert body["status"] == "ok"
    assert body["gap_seconds"] is not None
    assert body["gap_seconds"] < 120


def test_heartbeat_status_fast_path_node_filter(health_app):
    """?node=<id> scopes the lookup to one fleet node."""
    a, ls = health_app
    store = ls.get_store()

    now = time.time()
    # Node A: very recent → ok
    store.ingest_heartbeat({
        "node_id": "node-a",
        "ts": _iso(now - 10),
        "version": "0.12.162",
        "e2e": True,
    })
    # Node B: 2h ago → silent (gap > 1.5×30m)
    store.ingest_heartbeat({
        "node_id": "node-b",
        "ts": _iso(now - 7200),
        "version": "0.12.162",
        "e2e": True,
    })

    c = a.test_client()

    r_a = c.get("/api/heartbeat-status?node=node-a")
    body_a = r_a.get_json()
    assert body_a.get("_source") == "local_store"
    assert body_a["status"] == "ok"

    r_b = c.get("/api/heartbeat-status?node=node-b")
    body_b = r_b.get_json()
    assert body_b.get("_source") == "local_store"
    assert body_b["status"] == "silent"


def test_heartbeat_status_fast_path_falls_back_when_store_empty(health_app):
    """Empty heartbeats table → fast path returns None → legacy in-memory
    `_get_heartbeat_status()` runs (returns "unknown" when never seen)."""
    a, _ls = health_app
    c = a.test_client()
    r = c.get("/api/heartbeat-status")
    assert r.status_code == 200
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"


def test_heartbeat_status_fast_path_disabled_without_flag(tmp_path, monkeypatch):
    """No CLAWMETRY_LOCAL_STORE_READ → fast path never runs even with
    populated heartbeats store."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.health as hh
    importlib.reload(hh)

    store = ls.get_store()
    store.ingest_heartbeat({
        "node_id": "agent+noflag",
        "ts": _iso(time.time()),
        "version": "0.12.162",
        "e2e": True,
    })

    a = Flask(__name__)
    a.register_blueprint(hh.bp_health)
    r = a.test_client().get("/api/heartbeat-status")
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"
    try:
        store.stop(flush=True)
    except Exception:
        pass
