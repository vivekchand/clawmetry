"""Synthetic safety net for /api/usage/forecast DuckDB fast path.

Tier-1 surface #4 in the 2026-05-17 DuckDB coverage audit (issue #1565).
``_try_local_store_usage_forecast`` projects current spend trajectory to
end-of-month from the DuckDB ``events`` table — this file pins the v3
event shape it must accept and guards the three failure modes the
``feedback_usage_dedupe_pattern.md`` memory flagged:

  1. Real v3 ``assistant`` + ``model.completed`` sibling pairs (every
     billable turn emits both) must not double the projection.
  2. Non-message rows that carry ``cost_usd`` (tool retries, fallback
     turns) MUST be counted toward the projection. The fast path uses
     ``query_aggregates`` first precisely because the splits walker
     would silently drop them.
  3. Zero events → ``available: False`` with ``_source: local_store``
     still tagged so the audit canary fires.
"""

from __future__ import annotations

import importlib
import json
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
    # Steer the daemon-proxy discovery away from a contributor's locally
    # running clawmetry daemon. Without this, ``_ls_call`` proxies through
    # ``~/.clawmetry/local_query.json`` and the daemon queries its OWN
    # production DuckDB instead of our tmp_path fixture (issue #1538).
    import routes.local_query as lq
    monkeypatch.setattr(
        lq, "_DISCOVERY_PATH", str(tmp_path / "no-such-discovery.json")
    )
    lq._invalidate_daemon_cache()

    import routes.usage as usage_mod
    importlib.reload(usage_mod)

    a = Flask(__name__)
    a.register_blueprint(usage_mod.bp_usage)
    return a, ls, usage_mod


@pytest.fixture
def fast_path_app(tmp_path, monkeypatch):
    a, ls, u = _build_app(tmp_path, monkeypatch, enable_fast_path=True)
    yield a, ls, u
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def legacy_path_app(tmp_path, monkeypatch):
    a, ls, u = _build_app(tmp_path, monkeypatch, enable_fast_path=False)
    yield a, ls, u
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ingest_v3_assistant(store, *, sid, ts, ev_id, cost_usd,
                          input_tokens=6, output_tokens=7):
    """Insert the ``assistant`` Anthropic-SDK envelope row that the daemon
    writes for every real LLM turn (see ``clawmetry/sync.py``)."""
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
                "model": "claude-opus-4-7",
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
        "model":       "claude-opus-4-7",
    })


def _ingest_v3_model_completed(store, *, sid, ts, ev_id, cost_usd,
                                input_tokens=6, output_tokens=7):
    """Slim ``model.completed`` sibling that races the ``assistant`` row
    by ~100-300 ms. Both rows carry the same ``cost_usd``; the fast path
    must dedupe so the forecast doesn't run 2× hot."""
    store.ingest({
        "id":         ev_id,
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "model.completed",
        "ts":         ts,
        "data": {
            "type":     "model.completed",
            "modelId":  "claude-opus-4-7",
            "provider": "claude-cli",
        },
        "cost_usd":    cost_usd,
        "token_count": input_tokens + output_tokens,
        "model":       "claude-opus-4-7",
    })


def _ingest_tool_result(store, *, sid, ts, ev_id, cost_usd=0.0):
    """A non-billable-turn event row that may still carry cost (think
    tool retries that the daemon stamps with a fallback price). Forecast
    must include it — the splits-walker path silently drops these, which
    is exactly the bug class ``feedback_usage_dedupe_pattern.md`` flags."""
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

def test_forecast_empty_store_still_tags_local_store(fast_path_app):
    """Audit canary: a store that's been opened but holds zero usage
    rows must still respond with the ``_source: 'local_store'`` tag
    (and ``available: False``). Without the tag, the audit grep at
    ``reference_duckdb_coverage_audit.md`` would mis-categorise the
    surface as ``JSONL_FALLBACK_ONLY`` again."""
    a, ls, _u = fast_path_app
    # Touch the store so the DuckDB file exists on disk — without
    # this the read-only opener returns None and the route falls
    # through to the generic "no_data" reply (no canary).
    _wait_flush(ls.get_store())

    r = a.test_client().get("/api/usage/forecast")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"empty-store forecast lost the canary: {body!r}"
    )
    assert body.get("available") is False


# ── happy path: 7-day linear projection ───────────────────────────────────

def test_forecast_projects_seven_day_baseline(fast_path_app):
    """Seven days of $1/day → daily_rate = $1, projection extends through
    end-of-month."""
    a, ls, _u = fast_path_app
    store = ls.get_store()

    now = time.time()
    for i in range(7):
        _ingest_v3_assistant(
            store,
            sid=f"sess-day-{i}",
            ts=_iso(now - i * 86400),
            ev_id=f"asst-{i}",
            cost_usd=1.0,
        )
    _wait_flush(store)

    body = a.test_client().get("/api/usage/forecast").get_json()
    assert body["_source"] == "local_store"
    assert body["available"] is True
    # 7×$1 / 7 = $1.00/day
    assert abs(body["daily_rate_usd"] - 1.0) < 0.01, body
    assert body["window_days"] == 7
    assert len(body["daily_window"]) == 7
    # Projection >= cost_this_month (it adds days_remaining * rate on top).
    assert body["projected_month_usd"] >= body["cost_this_month_usd"]


# ── dedupe-pattern regression (feedback_usage_dedupe_pattern.md) ──────────

def test_forecast_dedupes_v3_sibling_pairs(fast_path_app):
    """Every real v3 LLM turn writes BOTH an ``assistant`` row and a
    sibling ``model.completed`` row ~150 ms apart, BOTH stamped with the
    same ``cost_usd``. A blind SUM doubles the projection. The fast path
    uses ``query_aggregates`` which dedupes at SQL level — confirm the
    forecast doesn't run 2× hot."""
    a, ls, _u = fast_path_app
    store = ls.get_store()

    today = _today_iso()
    base = f"{today}T10:00"

    # Seven days of one turn each, $0.50 per turn. Sibling-doubling
    # would inflate to $1.00/day → projection 2×.
    now = time.time()
    for i in range(7):
        sid = f"sess-pair-{i}"
        ts = _iso(now - i * 86400)
        _ingest_v3_assistant(
            store, sid=sid, ts=ts, ev_id=f"a-{i}", cost_usd=0.50,
        )
        # Sibling ~150ms later (within the SQL dedupe window).
        _ingest_v3_model_completed(
            store, sid=sid, ts=ts, ev_id=f"mc-{i}", cost_usd=0.50,
        )
    _wait_flush(store)

    body = a.test_client().get("/api/usage/forecast").get_json()
    assert body["_source"] == "local_store"
    # Single-counted: 7×$0.50 / 7 = $0.50/day. Double-counted would
    # be $1.00 — the canary that catches the bug class.
    assert abs(body["daily_rate_usd"] - 0.50) < 0.01, (
        f"sibling-pair double-count regression: daily_rate={body['daily_rate_usd']}"
    )


# ── dedupe-pattern regression: non-message rows must NOT be dropped ─────

def test_forecast_counts_cost_from_non_message_rows(fast_path_app):
    """``feedback_usage_dedupe_pattern.md``: the splits walker only knows
    about billable-turn event types — it silently drops cost stamped on
    ``tool.result`` / retry rows. The forecast helper uses
    ``query_aggregates`` first (which covers ALL cost-bearing rows) so
    those costs survive into the projection.
    """
    a, ls, _u = fast_path_app
    store = ls.get_store()

    today = _today_iso()
    base = f"{today}T10:00"

    # One assistant turn at $0.10 + one tool.result that carries $0.05
    # of fallback-pricing cost, every day for 7 days. Total daily = $0.15.
    now = time.time()
    for i in range(7):
        ts_iso = _iso(now - i * 86400)
        _ingest_v3_assistant(
            store, sid=f"sess-nm-{i}", ts=ts_iso,
            ev_id=f"asst-nm-{i}", cost_usd=0.10,
        )
        _ingest_tool_result(
            store, sid=f"sess-nm-{i}", ts=_iso(now - i * 86400 + 30),
            ev_id=f"tr-nm-{i}", cost_usd=0.05,
        )
    _wait_flush(store)

    body = a.test_client().get("/api/usage/forecast").get_json()
    assert body["_source"] == "local_store"
    # Daily rate must reflect BOTH the message AND tool.result costs.
    # Splits-walker-only would return $0.10 — that's the silent drop bug.
    assert abs(body["daily_rate_usd"] - 0.15) < 0.005, (
        f"non-message cost rows silently dropped: daily_rate="
        f"{body['daily_rate_usd']} (expected 0.15)"
    )


# ── gate: env flag OFF ────────────────────────────────────────────────────

def test_forecast_falls_through_when_local_store_disabled(legacy_path_app):
    """With ``CLAWMETRY_LOCAL_STORE_READ=0``, the fast path must be
    skipped entirely — the response is the legacy ``available: False``
    shape WITHOUT the canary tag (so the audit can see the gate is
    respected)."""
    a, _ls, _u = legacy_path_app

    body = a.test_client().get("/api/usage/forecast").get_json()
    assert body.get("_source") != "local_store", (
        f"gate honoured? body={body!r}"
    )
    assert body.get("available") is False
