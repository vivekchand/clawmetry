"""Synthetic safety net for /api/usage/cache-trends DuckDB fast path.

Tier-1 surface #1 in the 2026-05-19 DuckDB coverage audit (issue #1778).
``_try_local_store_cache_trends`` aggregates per-(day, model) cache
hit-ratio + cost-split off the DuckDB ``events`` table — this file
pins the v3 event shape it must accept and guards the two failure
modes most likely to silently inflate the numbers:

  1. Real v3 ``assistant`` + ``model.completed`` sibling pairs (every
     billable turn emits both) must not double cache_read_tokens or
     total_cost.
  2. The full envelope shape must round-trip — daily[] bucket per day,
     by_model[] bucket per model, totals + recommendations.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

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
    # running clawmetry daemon (same trick as test_usage_forecast_...).
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


def _ingest_v3_assistant(
    store, *, sid, ts, ev_id, model="claude-opus-4-7",
    input_tokens=100, output_tokens=50,
    cache_read=200, cache_write=80,
    cost_total=0.02,
):
    """Real v3 ``assistant`` Anthropic-SDK envelope — carries every
    usage split + per-component cost breakdown. The richer of the
    sibling pair, so the dedupe MUST keep this one."""
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
                    "input_tokens":                input_tokens,
                    "output_tokens":               output_tokens,
                    "cache_read_input_tokens":     cache_read,
                    "cache_creation_input_tokens": cache_write,
                    "cost": {
                        "input":      cost_total * 0.4,
                        "output":     cost_total * 0.3,
                        "cacheRead":  cost_total * 0.2,
                        "cacheWrite": cost_total * 0.1,
                        "total":      cost_total,
                    },
                },
            },
        },
        "cost_usd":    cost_total,
        "token_count": input_tokens + output_tokens,
        "model":       model,
    })


def _ingest_v3_model_completed(
    store, *, sid, ts, ev_id, model="claude-opus-4-7",
    input_tokens=100, output_tokens=50, cost_total=0.02,
):
    """Slim ``model.completed`` sibling that races the ``assistant`` row
    by ~150 ms. Same cost stamped. Cache splits NOT carried — so if the
    dedupe accidentally picks this one, the cache_hit_ratio collapses
    to 0 (a useful failure-mode canary)."""
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
            "promptCache": {
                "lastCallUsage": {
                    "input":  input_tokens,
                    "output": output_tokens,
                    "total":  input_tokens + output_tokens,
                },
            },
        },
        "cost_usd":    cost_total,
        "token_count": input_tokens + output_tokens,
        "model":       model,
    })


# ── happy path: single assistant event lands in today's bucket ─────────────

def test_cache_trends_single_assistant_event(fast_path_app):
    """One assistant turn with 100 in / 50 out / 200 cache_read / 80
    cache_write — confirm the envelope round-trips and the values land
    in today's daily bucket + by-model bucket."""
    a, ls, _u = fast_path_app
    store = ls.get_store()

    _ingest_v3_assistant(
        store,
        sid="sess-single",
        ts=_iso(time.time()),
        ev_id="asst-single",
    )
    _wait_flush(store)

    body = a.test_client().get("/api/usage/cache-trends?days=7").get_json()
    assert body["_source"] == "local_store", body
    assert body["days"] == 7
    assert len(body["daily"]) == 7
    today = _today_iso()
    todays = [d for d in body["daily"] if d["date"] == today]
    assert len(todays) == 1, body["daily"]
    t = todays[0]
    assert t["input_tokens"] == 100, t
    assert t["output_tokens"] == 50, t
    assert t["cache_read_tokens"] == 200, t
    assert t["cache_write_tokens"] == 80, t
    # cache_hit_ratio_pct = 200 / (100 + 200) * 100 = 66.7
    assert abs(t["cache_hit_ratio_pct"] - 66.7) < 0.1, t

    assert len(body["by_model"]) == 1
    assert body["by_model"][0]["model"] == "claude-opus-4-7"
    assert body["by_model"][0]["cache_read_tokens"] == 200

    assert body["totals"]["label"] == "totals"
    assert body["totals"]["cache_read_tokens"] == 200
    assert isinstance(body["recommendations"], list)


# ── dedupe-pattern regression (feedback_usage_dedupe_pattern.md) ──────────

def test_cache_trends_dedupes_v3_sibling_pairs(fast_path_app):
    """Every real v3 LLM turn writes BOTH an ``assistant`` row AND a
    sibling ``model.completed`` row ~150 ms apart. Counting both:
      * doubles input/output tokens,
      * doubles total_cost,
      * silently drops the cache split (slim sibling has none).

    The dedupe must pick the richer ``assistant`` envelope and emit
    single-counted numbers."""
    a, ls, _u = fast_path_app
    store = ls.get_store()

    ts = _iso(time.time())
    _ingest_v3_assistant(
        store, sid="sess-pair", ts=ts, ev_id="a-1",
        input_tokens=100, output_tokens=50,
        cache_read=200, cache_write=80, cost_total=0.02,
    )
    _ingest_v3_model_completed(
        store, sid="sess-pair", ts=ts, ev_id="mc-1",
        input_tokens=100, output_tokens=50, cost_total=0.02,
    )
    _wait_flush(store)

    body = a.test_client().get("/api/usage/cache-trends?days=2").get_json()
    assert body["_source"] == "local_store"

    today = _today_iso()
    todays = [d for d in body["daily"] if d["date"] == today]
    assert len(todays) == 1
    t = todays[0]
    # Single-counted: 100/50/200/80. Double-counted (sibling bug) would
    # be 200/100/200/80 with cache_hit collapsing — both canaries.
    assert t["input_tokens"] == 100, (
        f"sibling-pair double-count: input_tokens={t['input_tokens']}"
    )
    assert t["output_tokens"] == 50, t
    assert t["cache_read_tokens"] == 200, t
    assert t["cache_write_tokens"] == 80, t
    # Cache hit ratio survives the dedupe (would collapse to 33% under
    # the bug if the slim sibling won and replaced the splits with 0).
    assert abs(t["cache_hit_ratio_pct"] - 66.7) < 0.1, t


# ── gate: env flag OFF ────────────────────────────────────────────────────

def test_cache_trends_falls_through_when_local_store_disabled(tmp_path, monkeypatch):
    """With ``CLAWMETRY_LOCAL_STORE_READ=0``, the fast path must be
    skipped entirely — the response is the legacy JSONL-walker shape
    WITHOUT the ``_source: local_store`` canary."""
    a, _ls, _u = _build_app(tmp_path, monkeypatch, enable_fast_path=False)

    body = a.test_client().get("/api/usage/cache-trends").get_json()
    assert body.get("_source") != "local_store", (
        f"gate honoured? body keys={list(body.keys())}"
    )
    # Legacy shape still has the core keys
    assert "daily" in body
    assert "by_model" in body
    assert "totals" in body
