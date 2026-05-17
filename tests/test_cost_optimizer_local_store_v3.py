"""Synthetic safety net for /api/cost-optimizer DuckDB fast path.

Tier-1 surface #12 in the 2026-05-17 DuckDB coverage audit (issue #1565).
The legacy ``/api/cost-optimizer`` handler computed ``todayCost`` /
``projectedMonthlyCost`` from ``dashboard._metrics_store`` (an in-memory
ring populated by the HTTP interceptor) and ``expensiveOps`` from the
same ring. The ring resets on every dashboard restart — the optimizer
renders $0 / no candidates even when DuckDB holds weeks of real usage
rows. ``_try_local_store_cost_optimizer`` closes that gap by reading
``query_aggregates`` for the daily cost rollup (SQL-deduped, covers
non-message cost-bearing rows) and ``query_events`` for the top recent
high-cost rows.

This file pins the three failure modes:

  1. Real v3 ``assistant`` + ``model.completed`` sibling pairs (every
     billable turn emits both) must not double the projection. ``query_
     aggregates`` dedupes at SQL level (see
     ``feedback_usage_dedupe_pattern.md``).
  2. Non-message rows that carry ``cost_usd`` (tool retries / fallback
     turns) MUST be counted toward today/projected — query_aggregates
     covers them; the splits walker doesn't.
  3. Empty DuckDB store → ``_source`` absent so the route falls back to
     the legacy in-memory values. A fresh install with no daemon ingest
     yet still works.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask


def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _wait_flush(store, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _build_app(tmp_path, monkeypatch, *, enable_fast_path: bool = True):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_READ", "1" if enable_fast_path else "0"
    )

    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Issue #1538: isolate the fixture from a contributor's locally-
    # running clawmetry daemon. Without this, ``_ls_call`` proxies
    # through ``~/.clawmetry/local_query.json`` and the daemon queries
    # its OWN production DuckDB instead of our tmp_path fixture.
    import routes.local_query as lq
    monkeypatch.setattr(
        lq, "_DISCOVERY_PATH", str(tmp_path / "no-such-discovery.json")
    )
    lq._invalidate_daemon_cache()

    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    import routes.infra as infra_mod
    importlib.reload(infra_mod)

    a = Flask(__name__)
    a.register_blueprint(infra_mod.bp_config)
    return a, ls, infra_mod


@pytest.fixture
def fast_path_app(tmp_path, monkeypatch):
    a, ls, m = _build_app(tmp_path, monkeypatch, enable_fast_path=True)
    yield a, ls, m
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def legacy_path_app(tmp_path, monkeypatch):
    a, ls, m = _build_app(tmp_path, monkeypatch, enable_fast_path=False)
    yield a, ls, m
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ingest_v3_assistant(store, *, sid, ts, ev_id, cost_usd,
                          input_tokens=6, output_tokens=7,
                          model="claude-opus-4-7"):
    """The ``assistant`` Anthropic-SDK envelope row the daemon writes
    for every real LLM turn (see ``clawmetry/sync.py``)."""
    store.ingest({
        "id":         ev_id,
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "assistant",
        "ts":         ts,
        "data": {
            "type":    "assistant",
            "version": 3,
            "message": {
                "role":  "assistant",
                "model": model,
                "type":  "message",
                "usage": {
                    "input_tokens":               input_tokens,
                    "output_tokens":              output_tokens,
                    "cache_read_input_tokens":    0,
                    "cache_creation_input_tokens": 0,
                },
            },
        },
        "cost_usd":    cost_usd,
        "token_count": input_tokens + output_tokens,
        "model":       model,
    })


def _ingest_v3_model_completed(store, *, sid, ts, ev_id, cost_usd,
                                input_tokens=6, output_tokens=7,
                                model="claude-opus-4-7"):
    """Slim ``model.completed`` sibling that races the ``assistant`` row
    ~100-300 ms later. Both rows carry the same ``cost_usd``; the fast
    path must dedupe."""
    store.ingest({
        "id":         ev_id,
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "model.completed",
        "ts":         ts,
        "data": {
            "type":     "model.completed",
            "modelId":  model,
            "provider": "claude-cli",
        },
        "cost_usd":    cost_usd,
        "token_count": input_tokens + output_tokens,
        "model":       model,
    })


def _ingest_tool_result(store, *, sid, ts, ev_id, cost_usd=0.0):
    """Non-billable-turn event row that may still carry cost (tool
    retries the daemon stamps with fallback pricing). Optimizer must
    include it — splits-walker silently drops these."""
    store.ingest({
        "id":         ev_id,
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "tool.result",
        "ts":         ts,
        "data":       {"type": "tool.result", "tool_use_id": "toolu_x"},
        "cost_usd":   cost_usd,
        "token_count": 0,
        "model":       "claude-opus-4-7",
    })


# ── canary: empty store ───────────────────────────────────────────────────

def test_empty_store_omits_canary_and_keeps_legacy_payload(fast_path_app):
    """When DuckDB holds zero cost-bearing rows the helper returns None
    and the route keeps its legacy in-memory ``costs`` slice. No
    ``_source`` tag fires (no canary, no false positive). The base
    payload shape (system, taskRecommendations, …) must still render."""
    a, ls, _m = fast_path_app
    _wait_flush(ls.get_store())

    r = a.test_client().get("/api/cost-optimizer")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    # Legacy payload always renders the host-state slice.
    assert "system" in body
    assert "taskRecommendations" in body
    assert "todayCost" in body
    assert "projectedMonthlyCost" in body
    # No DuckDB rows → no canary.
    assert body.get("_source") != "local_store", body


# ── happy path: today + projected from query_aggregates ───────────────────

def test_today_cost_derived_from_duckdb(fast_path_app):
    """A real assistant turn today must surface as ``todayCost`` even
    when the in-memory metrics_store ring is empty (fresh dashboard
    restart). Closes the bug class the audit flagged."""
    a, ls, _m = fast_path_app
    store = ls.get_store()

    # One $1 turn at noon UTC TODAY.
    today = _today_iso()
    _ingest_v3_assistant(
        store, sid="sess-today",
        ts=f"{today}T12:00:00+00:00",
        ev_id="asst-today", cost_usd=1.0,
    )
    _wait_flush(store)

    body = a.test_client().get("/api/cost-optimizer").get_json()
    assert body.get("_source") == "local_store", (
        f"audit canary missing on populated store: {body!r}"
    )
    assert abs(body["todayCost"] - 1.0) < 0.01, (
        f"todayCost not derived from DuckDB: {body['todayCost']}"
    )
    # projectedMonthlyCost = (month_cost / days_observed) * 30
    # = ($1 / 1 day) * 30 = $30
    assert abs(body["projectedMonthlyCost"] - 30.0) < 0.01, (
        f"projectedMonthlyCost off: {body['projectedMonthlyCost']}"
    )


# ── dedupe-pattern regression (feedback_usage_dedupe_pattern.md) ──────────

def test_dedupes_v3_sibling_pairs(fast_path_app):
    """Every real v3 LLM turn writes BOTH an ``assistant`` row and a
    sibling ``model.completed`` row ~150 ms apart, BOTH stamped with the
    same ``cost_usd``. A blind SUM doubles today/projected. The fast
    path uses ``query_aggregates`` which dedupes at SQL level."""
    a, ls, _m = fast_path_app
    store = ls.get_store()

    today = _today_iso()
    ts = f"{today}T10:00:00+00:00"

    # Single turn at $0.50. Sibling-doubling would inflate to $1.00.
    _ingest_v3_assistant(
        store, sid="sess-pair", ts=ts, ev_id="a-pair", cost_usd=0.50,
    )
    _ingest_v3_model_completed(
        store, sid="sess-pair", ts=ts, ev_id="mc-pair", cost_usd=0.50,
    )
    _wait_flush(store)

    body = a.test_client().get("/api/cost-optimizer").get_json()
    assert body.get("_source") == "local_store"
    # Single-counted: $0.50. Double-counted would be $1.00.
    assert abs(body["todayCost"] - 0.50) < 0.01, (
        f"sibling-pair double-count regression: todayCost={body['todayCost']}"
    )


# ── dedupe-pattern regression: non-message rows must NOT be dropped ─────

def test_counts_cost_from_non_message_rows(fast_path_app):
    """``feedback_usage_dedupe_pattern.md``: the splits walker only
    knows billable-turn event types — it silently drops cost stamped on
    ``tool.result`` / retry rows. The optimizer uses
    ``query_aggregates`` first (covers ALL cost-bearing rows) so those
    costs survive into ``todayCost`` / ``projectedMonthlyCost``.
    """
    a, ls, _m = fast_path_app
    store = ls.get_store()

    today = _today_iso()
    # One assistant turn at $0.10 + one tool.result that carries $0.05
    # of fallback-pricing cost. Total today = $0.15.
    _ingest_v3_assistant(
        store, sid="sess-nm", ts=f"{today}T10:00:00+00:00",
        ev_id="asst-nm", cost_usd=0.10,
    )
    _ingest_tool_result(
        store, sid="sess-nm", ts=f"{today}T10:00:30+00:00",
        ev_id="tr-nm", cost_usd=0.05,
    )
    _wait_flush(store)

    body = a.test_client().get("/api/cost-optimizer").get_json()
    assert body.get("_source") == "local_store"
    assert abs(body["todayCost"] - 0.15) < 0.005, (
        f"non-message cost rows silently dropped: todayCost="
        f"{body['todayCost']} (expected 0.15)"
    )


# ── expensiveOps: top recent rows by cost ─────────────────────────────────

def test_expensive_ops_populated_from_duckdb(fast_path_app):
    """``expensiveOps`` must surface the top-cost recent rows from
    DuckDB (each at >$0.01, descending). Lets users see *which* turns
    are eating spend even on a freshly-restarted dashboard."""
    a, ls, _m = fast_path_app
    store = ls.get_store()

    today = _today_iso()
    _ingest_v3_assistant(
        store, sid="sess-exp-1", ts=f"{today}T09:00:00+00:00",
        ev_id="asst-exp-1", cost_usd=0.20,
        model="claude-opus-4-7",
    )
    _ingest_v3_assistant(
        store, sid="sess-exp-2", ts=f"{today}T10:00:00+00:00",
        ev_id="asst-exp-2", cost_usd=0.50,
        model="claude-sonnet-4-5",
    )
    # Below threshold — must NOT appear in expensiveOps.
    _ingest_v3_assistant(
        store, sid="sess-exp-cheap", ts=f"{today}T11:00:00+00:00",
        ev_id="asst-exp-cheap", cost_usd=0.005,
    )
    _wait_flush(store)

    body = a.test_client().get("/api/cost-optimizer").get_json()
    assert body.get("_source") == "local_store"
    ops = body.get("expensiveOps") or []
    assert ops, f"expensiveOps not hydrated from DuckDB: {body!r}"
    # Sorted descending by cost; sub-cent row filtered out.
    assert ops[0]["cost"] >= ops[-1]["cost"], (
        f"expensiveOps not sorted desc: {ops!r}"
    )
    assert all(o["cost"] > 0.01 for o in ops), (
        f"sub-threshold row leaked: {ops!r}"
    )
    models = {o["model"] for o in ops}
    assert "claude-opus-4-7" in models or "claude-sonnet-4-5" in models, (
        f"model column not propagated: {ops!r}"
    )


# ── gate: env flag OFF ────────────────────────────────────────────────────

def test_falls_through_when_local_store_disabled(legacy_path_app):
    """With ``CLAWMETRY_LOCAL_STORE_READ=0`` the fast path must be
    skipped — no ``_source`` tag, even if the store has rows. So the
    audit can see the gate is respected."""
    a, ls, _m = legacy_path_app
    store = ls.get_store()

    today = _today_iso()
    _ingest_v3_assistant(
        store, sid="sess-gate", ts=f"{today}T10:00:00+00:00",
        ev_id="asst-gate", cost_usd=1.0,
    )
    _wait_flush(store)

    body = a.test_client().get("/api/cost-optimizer").get_json()
    assert body.get("_source") != "local_store", (
        f"gate honoured? body={body!r}"
    )
