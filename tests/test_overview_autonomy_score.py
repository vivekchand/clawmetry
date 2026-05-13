"""Tests for issue #688 — autonomy score on /api/overview.

Verifies the new top-level ``autonomy`` field that surfaces the north-star
metric (median seconds between human nudges, 7d) as a primary KPI.

The autonomy block is computed from ``prompt.submitted`` events in the local
DuckDB store. Each test seeds a fresh in-memory store with known timestamps
and asserts the derived metrics. Edge cases covered:

  * empty store                       → median=None, ratio=0, samples=0
  * one event only (no gap to compute)→ median=None, ratio=1.0, samples=1
  * every session has <=1 user turn   → ratio=1.0 (perfect autonomy)
  * known per-session gaps            → median matches expected value
  * trend: current 7d longer than prior 7d → trend_pct > 0
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask


# ─────────────────────────────────────────────────────────────────────────────
# fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def overview_app(tmp_path, monkeypatch):
    """Flask app + reloaded local_store + reloaded routes.overview.

    Each test gets its OWN duckdb file (tmp_path) so cached autonomy data
    from a previous test can't leak in via the module-level cache. We also
    short-circuit the daemon HTTP proxy (``local_store_via_daemon``) so the
    test never accidentally talks to a live developer daemon and reads the
    real ``~/.clawmetry/events.duckdb`` instead of our tmp file.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Reload local_query AFTER local_store so its in-memory caches start fresh
    # and so we can monkeypatch the daemon proxy to a no-op (forces tests to
    # use the direct-open path against our tmp duckdb file).
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)

    import routes.overview as ov
    importlib.reload(ov)
    # Reset the 60s cache between tests so the per-test data is honoured.
    ov._AUTONOMY_OVERVIEW_CACHE["ts"] = 0.0
    ov._AUTONOMY_OVERVIEW_CACHE["data"] = None

    a = Flask(__name__)
    a.register_blueprint(ov.bp_overview)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _ingest_prompt(store, *, eid, sid, ts_epoch):
    """Ingest a single v3-shape ``prompt.submitted`` event."""
    store.ingest({
        "id": eid,
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": "prompt.submitted",
        "ts": _iso(ts_epoch),
        "data": {"type": "prompt.submitted", "finalPromptText": "hi"},
        "cost_usd": None,
        "token_count": None,
        "model": None,
    })


# ─────────────────────────────────────────────────────────────────────────────
# response-shape tests
# ─────────────────────────────────────────────────────────────────────────────


def test_overview_response_includes_autonomy_field(overview_app):
    """/api/overview always exposes the four documented autonomy keys."""
    a, _ = overview_app
    r = a.test_client().get("/api/overview")
    assert r.status_code == 200
    body = r.get_json() or {}
    assert "autonomy" in body, f"missing autonomy field; body keys: {list(body.keys())}"
    autonomy = body["autonomy"]
    for key in ("median_gap_seconds", "autonomy_ratio", "trend_pct", "sample_size_7d"):
        assert key in autonomy, f"autonomy missing key: {key}"


def test_overview_autonomy_empty_store(overview_app):
    """No events at all → median=None, ratio=0, trend=0, samples=0.

    The placeholder keeps the UI from breaking on a fresh install before any
    ``prompt.submitted`` events have landed in DuckDB.
    """
    a, _ = overview_app
    body = a.test_client().get("/api/overview").get_json() or {}
    autonomy = body["autonomy"]
    assert autonomy["median_gap_seconds"] is None
    assert autonomy["autonomy_ratio"] == 0.0
    assert autonomy["trend_pct"] == 0.0
    assert autonomy["sample_size_7d"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# metric-correctness tests
# ─────────────────────────────────────────────────────────────────────────────


def test_overview_autonomy_single_event_no_gap(overview_app):
    """A single user message → no consecutive-gap pair → median stays None.

    ``autonomy_ratio`` jumps to 1.0 (the session completed with exactly one
    nudge, which is the "perfect autonomy" definition).
    """
    a, ls = overview_app
    store = ls.get_store()
    now = datetime.now(tz=timezone.utc).timestamp()
    _ingest_prompt(store, eid="ev-1", sid="sess-a", ts_epoch=now - 3600)
    _wait_flush(store)

    body = a.test_client().get("/api/overview").get_json() or {}
    autonomy = body["autonomy"]
    assert autonomy["median_gap_seconds"] is None, "single event has no gap to median"
    assert autonomy["autonomy_ratio"] == 1.0, "one event = one nudge = perfect"
    assert autonomy["sample_size_7d"] == 1


def test_overview_autonomy_known_median(overview_app):
    """Two sessions with known gaps → median matches the expected midpoint.

    Session A: gaps [60, 120, 180]   (3 user turns spaced 60-300s apart)
    Session B: gaps [600]            (2 user turns 10m apart)

    Combined sorted gaps: [60, 120, 180, 600] → median = (120+180)/2 = 150s.
    """
    a, ls = overview_app
    store = ls.get_store()
    now = datetime.now(tz=timezone.utc).timestamp()

    # Session A: 4 events with consecutive gaps 60s, 120s, 180s.
    base_a = now - 3600
    for i, offset in enumerate([0, 60, 60 + 120, 60 + 120 + 180]):
        _ingest_prompt(store, eid=f"a-{i}", sid="sess-A", ts_epoch=base_a + offset)

    # Session B: 2 events 600s apart.
    base_b = now - 7200
    _ingest_prompt(store, eid="b-0", sid="sess-B", ts_epoch=base_b)
    _ingest_prompt(store, eid="b-1", sid="sess-B", ts_epoch=base_b + 600)

    _wait_flush(store)

    body = a.test_client().get("/api/overview").get_json() or {}
    autonomy = body["autonomy"]
    # Tolerance: timestamps round-trip through ISO strings so allow ±2s drift.
    assert autonomy["median_gap_seconds"] is not None
    assert abs(autonomy["median_gap_seconds"] - 150.0) < 2.0, (
        f"expected median ~150s, got {autonomy['median_gap_seconds']}"
    )
    # 2 sessions total, neither is single-prompt, so ratio = 0.
    assert autonomy["autonomy_ratio"] == 0.0
    # 4 + 2 = 6 user turns
    assert autonomy["sample_size_7d"] == 6


def test_overview_autonomy_ratio_all_one_nudge(overview_app):
    """Three sessions, each with exactly one user message → ratio = 1.0.

    This is the canonical "agent ran to completion without further input"
    pattern — the headline KPI the card emphasises.
    """
    a, ls = overview_app
    store = ls.get_store()
    now = datetime.now(tz=timezone.utc).timestamp()
    for i, sid in enumerate(["s1", "s2", "s3"]):
        _ingest_prompt(store, eid=f"ev-{i}", sid=sid, ts_epoch=now - (i + 1) * 600)
    _wait_flush(store)

    body = a.test_client().get("/api/overview").get_json() or {}
    autonomy = body["autonomy"]
    assert autonomy["autonomy_ratio"] == 1.0
    assert autonomy["sample_size_7d"] == 3
    # No gaps to median across three single-event sessions.
    assert autonomy["median_gap_seconds"] is None


def test_overview_autonomy_trend_pct_improves(overview_app):
    """Current 7d gaps wider than prior 7d → trend_pct > 0 (improving).

    Prior window (8-14d ago): consecutive 60s gaps.
    Current window (0-7d):    consecutive 600s gaps.

    The ratio is ~10x so trend_pct lands well above zero — we just check
    the sign here since the exact value depends on how the medians line up.
    """
    a, ls = overview_app
    store = ls.get_store()
    now = datetime.now(tz=timezone.utc).timestamp()

    # Prior 7d window: 2 events 60s apart, 10 days ago.
    prior_base = now - 10 * 86400
    _ingest_prompt(store, eid="p-0", sid="sess-prior", ts_epoch=prior_base)
    _ingest_prompt(store, eid="p-1", sid="sess-prior", ts_epoch=prior_base + 60)

    # Current 7d window: 2 events 600s apart, 1 day ago.
    cur_base = now - 86400
    _ingest_prompt(store, eid="c-0", sid="sess-cur", ts_epoch=cur_base)
    _ingest_prompt(store, eid="c-1", sid="sess-cur", ts_epoch=cur_base + 600)

    _wait_flush(store)

    body = a.test_client().get("/api/overview").get_json() or {}
    autonomy = body["autonomy"]
    assert autonomy["trend_pct"] > 0, (
        f"expected positive trend (current gaps longer than prior); "
        f"got trend_pct={autonomy['trend_pct']}"
    )
    # Only the current-window events count toward sample_size_7d.
    assert autonomy["sample_size_7d"] == 2


def test_overview_autonomy_ignores_other_event_types(overview_app):
    """Only ``prompt.submitted`` events feed the metric — tool_calls etc.
    must not pollute the gap distribution or the sample count."""
    a, ls = overview_app
    store = ls.get_store()
    now = datetime.now(tz=timezone.utc).timestamp()

    # 1 user turn that should count.
    _ingest_prompt(store, eid="real", sid="sess-real", ts_epoch=now - 3600)

    # 5 noise events of other types that must be ignored.
    for i, etype in enumerate(["tool.call", "tool.result", "model.completed",
                                "model.changed", "session.started"]):
        store.ingest({
            "id": f"noise-{i}",
            "node_id": "agent+test",
            "agent_id": "main",
            "session_id": "sess-real",
            "event_type": etype,
            "ts": _iso(now - 1800 + i),
            "data": {},
            "cost_usd": None,
            "token_count": None,
            "model": None,
        })

    _wait_flush(store)

    body = a.test_client().get("/api/overview").get_json() or {}
    autonomy = body["autonomy"]
    assert autonomy["sample_size_7d"] == 1, "only prompt.submitted should count"
