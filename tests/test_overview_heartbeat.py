"""Tests for issue #686 — heartbeat block on /api/overview.

The handler computes a 5-field `heartbeat` block from DuckDB events where the
session looks like an OpenClaw heartbeat (`data.session_type == "heartbeat"`,
event_type == "heartbeat", or session_id containing "heartbeat"). It surfaces:

  - expected_cadence_seconds (default 1800)
  - last_heartbeat_ts (ISO-8601 UTC, or None)
  - gap_seconds (now - last beat, or None)
  - ok_ratio (HEARTBEAT_OK / total over last 20 beats)
  - sample_size
  - status: "green" | "amber" | "red" | None

This suite exercises the pure compute function `_compute_overview_heartbeat`
directly so we don't have to bring up a Flask app + reload the dashboard
module just to verify the math. A separate end-to-end test confirms the
block flows through the Flask handler.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture
def overview_module(tmp_path, monkeypatch):
    """Fresh local_store + routes.overview against a tmpdir DuckDB."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.overview as ov
    importlib.reload(ov)

    yield ov, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


def _wait_flush(store, t=2.0):
    """Wait for the ring to drain to disk so SELECTs see the rows."""
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _ingest_heartbeat(store, *, ts_epoch: float, outcome: str = "ok",
                      session_id: str = "heartbeat-2026-05-13"):
    """Ingest one heartbeat event tagged by data.session_type=='heartbeat'.

    ``outcome='ok'`` => the agent replied HEARTBEAT_OK (no action needed).
    ``outcome='action'`` => any other reply.
    """
    if outcome == "ok":
        data = {"session_type": "heartbeat", "response": "HEARTBEAT_OK"}
    else:
        data = {
            "session_type": "heartbeat",
            "response": "Looked at the alerts dashboard, all green.",
        }
    store.ingest({
        "id": f"ev-hb-{ts_epoch}",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": session_id,
        "event_type": "message",
        "ts": _iso(ts_epoch),
        "data": data,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Pure compute function
# ─────────────────────────────────────────────────────────────────────────────


def test_heartbeat_empty_store_returns_unknown_status(overview_module):
    """No heartbeats observed → status=None, all metrics None/0."""
    ov, _ls = overview_module
    out = ov._compute_overview_heartbeat()
    assert out["status"] is None
    assert out["last_heartbeat_ts"] is None
    assert out["gap_seconds"] is None
    assert out["ok_ratio"] is None
    assert out["sample_size"] == 0
    assert out["expected_cadence_seconds"] == 1800


def test_heartbeat_recent_beat_is_green(overview_module):
    """A heartbeat that fired within 1.5× cadence → status='green'."""
    ov, ls = overview_module
    store = ls.get_store()
    now = time.time()
    # Fired 5 minutes ago — well within 1.5×1800s = 45 minutes.
    _ingest_heartbeat(store, ts_epoch=now - 5 * 60, outcome="ok")
    _wait_flush(store)
    out = ov._compute_overview_heartbeat(now=now)
    assert out["status"] == "green"
    assert out["gap_seconds"] is not None
    assert 240 <= out["gap_seconds"] <= 360
    assert out["sample_size"] == 1
    assert out["ok_ratio"] == 1.0
    assert out["last_heartbeat_ts"] is not None
    assert out["last_heartbeat_ts"].endswith("+00:00")


def test_heartbeat_drifting_is_amber(overview_module):
    """Last beat 50 minutes ago (1.5×–3× cadence) → status='amber'."""
    ov, ls = overview_module
    store = ls.get_store()
    now = time.time()
    _ingest_heartbeat(store, ts_epoch=now - 50 * 60, outcome="ok")
    _wait_flush(store)
    out = ov._compute_overview_heartbeat(now=now)
    assert out["status"] == "amber"


def test_heartbeat_missed_is_red(overview_module):
    """Last beat >3× cadence ago → status='red'."""
    ov, ls = overview_module
    store = ls.get_store()
    now = time.time()
    # 4 hours ago is way past 3*1800s = 90 minutes.
    _ingest_heartbeat(store, ts_epoch=now - 4 * 3600, outcome="ok")
    _wait_flush(store)
    out = ov._compute_overview_heartbeat(now=now)
    assert out["status"] == "red"
    assert out["gap_seconds"] >= 3 * 1800


def test_heartbeat_ok_ratio_over_last_20(overview_module):
    """ok_ratio = HEARTBEAT_OK count / sample_size over the 20 most recent."""
    ov, ls = overview_module
    store = ls.get_store()
    now = time.time()
    # 15 beats: 3 actions, 12 ok. Ratio over a 15-beat window = 12/15 = 0.8.
    # Use distinct session_ids so each is treated as its own beat.
    for i in range(15):
        outcome = "action" if i < 3 else "ok"
        _ingest_heartbeat(
            store,
            ts_epoch=now - (i + 1) * 60,
            outcome=outcome,
            session_id=f"heartbeat-{i}",
        )
    _wait_flush(store)
    out = ov._compute_overview_heartbeat(now=now)
    assert out["sample_size"] == 15
    assert out["ok_ratio"] == pytest.approx(12 / 15, abs=1e-3)
    assert out["status"] == "green"


def test_heartbeat_ratio_caps_sample_at_20(overview_module):
    """sample_size never exceeds 20 even when more beats exist."""
    ov, ls = overview_module
    store = ls.get_store()
    now = time.time()
    # 25 beats, all ok.
    for i in range(25):
        _ingest_heartbeat(
            store,
            ts_epoch=now - (i + 1) * 60,
            outcome="ok",
            session_id=f"heartbeat-cap-{i}",
        )
    _wait_flush(store)
    out = ov._compute_overview_heartbeat(now=now)
    assert out["sample_size"] == 20
    assert out["ok_ratio"] == 1.0


def test_heartbeat_ignores_non_heartbeat_events(overview_module):
    """A non-heartbeat event (e.g. tool_call) must not be counted as a beat."""
    ov, ls = overview_module
    store = ls.get_store()
    now = time.time()
    store.ingest({
        "id": "ev-tool",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "sess-tool",
        "event_type": "tool_call",
        "ts": _iso(now - 60),
        "data": {"tool": "Bash"},
    })
    _wait_flush(store)
    out = ov._compute_overview_heartbeat(now=now)
    # Only the tool_call exists — no heartbeat. Status stays unknown.
    assert out["status"] is None
    assert out["sample_size"] == 0


def test_heartbeat_detects_via_event_type(overview_module):
    """Falls back to event_type='heartbeat' when data.session_type missing."""
    ov, ls = overview_module
    store = ls.get_store()
    now = time.time()
    store.ingest({
        "id": "ev-hb-via-type",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "regular-session-id",
        "event_type": "heartbeat",
        "ts": _iso(now - 60),
        "data": {"response": "HEARTBEAT_OK"},
    })
    _wait_flush(store)
    out = ov._compute_overview_heartbeat(now=now)
    assert out["status"] == "green"
    assert out["sample_size"] == 1


def test_heartbeat_detects_via_session_id(overview_module):
    """Falls back to session_id containing 'heartbeat' when other tags absent."""
    ov, ls = overview_module
    store = ls.get_store()
    now = time.time()
    store.ingest({
        "id": "ev-hb-via-sid",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "heartbeat-2026-05-13-12-00",
        "event_type": "message",
        "ts": _iso(now - 120),
        "data": {"text": "HEARTBEAT_OK"},
    })
    _wait_flush(store)
    out = ov._compute_overview_heartbeat(now=now)
    assert out["status"] == "green"
    assert out["ok_ratio"] == 1.0


def test_heartbeat_picks_most_recent_as_last(overview_module):
    """gap_seconds reflects the most recent heartbeat, not the oldest."""
    ov, ls = overview_module
    store = ls.get_store()
    now = time.time()
    # 6 hours ago + 3 minutes ago — latter must win.
    _ingest_heartbeat(store, ts_epoch=now - 6 * 3600, outcome="action",
                      session_id="heartbeat-old")
    _ingest_heartbeat(store, ts_epoch=now - 3 * 60, outcome="ok",
                      session_id="heartbeat-new")
    _wait_flush(store)
    out = ov._compute_overview_heartbeat(now=now)
    assert out["status"] == "green"
    assert 120 <= out["gap_seconds"] <= 240


# ─────────────────────────────────────────────────────────────────────────────
# Flask handler integration
# ─────────────────────────────────────────────────────────────────────────────


def test_api_overview_includes_heartbeat_block(tmp_path, monkeypatch):
    """End-to-end: /api/overview JSON response contains the `heartbeat` block."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.overview as ov
    importlib.reload(ov)

    # Seed a session so the fast path engages, and a heartbeat event.
    store = ls.get_store()
    store.ingest_session({
        "session_id": "sess-main-X",
        "agent_type": "openclaw",
        "title": "Main session",
        "started_at": "2026-05-13T10:00:00+00:00",
        "last_active_at": "2026-05-13T11:00:00+00:00",
        "status": "active",
        "total_tokens": 100,
        "message_count": 1,
        "metadata": {"model": "claude-opus-4-7"},
    })
    now = time.time()
    _ingest_heartbeat(store, ts_epoch=now - 60, outcome="ok")
    _wait_flush(store)

    from flask import Flask
    a = Flask(__name__)
    a.register_blueprint(ov.bp_overview)
    # Reset the module-level cache so this test sees fresh data.
    ov._heartbeat_cache["ts"] = 0.0
    ov._heartbeat_cache["value"] = None

    r = a.test_client().get("/api/overview")
    assert r.status_code == 200
    body = r.get_json()
    assert "heartbeat" in body, "overview JSON missing `heartbeat` block"
    hb = body["heartbeat"]
    for key in (
        "expected_cadence_seconds",
        "last_heartbeat_ts",
        "gap_seconds",
        "ok_ratio",
        "sample_size",
        "status",
    ):
        assert key in hb, f"heartbeat block missing key: {key}"
    assert hb["expected_cadence_seconds"] == 1800
    assert hb["status"] == "green"
    assert hb["sample_size"] == 1


def test_heartbeat_cache_returns_cached_value(overview_module):
    """The 30s memo wrapper returns the same dict on rapid back-to-back calls."""
    ov, ls = overview_module
    store = ls.get_store()
    now = time.time()
    _ingest_heartbeat(store, ts_epoch=now - 30, outcome="ok")
    _wait_flush(store)
    # Reset cache.
    ov._heartbeat_cache["ts"] = 0.0
    ov._heartbeat_cache["value"] = None

    first = ov._get_overview_heartbeat_cached()
    second = ov._get_overview_heartbeat_cached()
    # Same object identity proves the cache returned the memoised dict.
    assert first is second
