"""Synthetic safety net for /api/token-attribution DuckDB fast path
(Tier-1 surface #7 in issue #1565).

``routes/usage.py::_try_local_store_token_attribution`` returns per-LLM-
turn token + cost rows from DuckDB, replacing a JSONL walker whose
``ev['type'] == 'message'`` filter silently misses every v3 install
(real OpenClaw v3 emits ``assistant`` / ``model.completed`` after the
daemon's namespace rewrite — see ``reference_openclaw_v3_event_types.md``).

This file seeds DuckDB with the SAME daemon-normalised event shapes
that ``clawmetry/sync.py::_parse_v3_event`` writes and asserts:

1. Populated store returns ``_source='local_store'`` with one row per
   billable turn and correct token/cost totals.
2. Empty store → None so the legacy JSONL walker fires.
3. v3 sibling pair (``assistant`` + slim ``model.completed`` ~100 ms apart,
   identical ``token_count``) must NOT double-count. Same risk class as
   ``feedback_usage_dedupe_pattern.md`` (PR #1444, PR #1571).
4. ``session_id=`` query filter restricts the result set.
5. Slim ``model.completed`` row with no rich sibling still surfaces via
   the scalar-column fallback (defends against Eng G's "blind-replace-
   aggregate-with-deduped-subset" failure mode).
"""

from __future__ import annotations

import importlib
import json
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.usage as usage_mod
    importlib.reload(usage_mod)

    # Issue #1538 pattern: isolate fixture from a developer's locally
    # running clawmetry daemon. Without this the proxy reaches into
    # ``~/.clawmetry/local_query.json`` and queries the dev daemon's
    # production DuckDB instead of our tmp_path fixture.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(usage_mod.bp_usage)
    yield a, ls, usage_mod
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _drain(store):
    store._flush_now()
    for _ in range(20):
        if not store._ring:
            break
        time.sleep(0.05)


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def _assistant_row(event_id, sid, ts, *, input_t, output_t,
                   cache_read=0, cache_write=0, cost_total=0.0,
                   model="claude-opus-4-7"):
    """Build the v3 ``assistant`` event row the daemon writes for one
    LLM turn — Anthropic-SDK envelope under data.message.usage."""
    data = {
        "_v3_type": "message",
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": model,
            "usage": {
                "input_tokens": input_t,
                "output_tokens": output_t,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_write,
                "cost": {
                    "input": cost_total * 0.4,
                    "output": cost_total * 0.5,
                    "cacheRead": cost_total * 0.05,
                    "cacheWrite": cost_total * 0.05,
                    "total": cost_total,
                },
            },
        },
    }
    return {
        "id":           event_id,
        "node_id":      "node-test",
        "agent_type":   "openclaw",
        "agent_id":     "main",
        "session_id":   sid,
        "workspace_id": None,
        "event_type":   "assistant",
        "ts":           ts,
        "data":         json.dumps(data),
        "cost_usd":     cost_total,
        "token_count":  input_t + output_t + cache_read + cache_write,
        "model":        model,
    }


def _model_completed_row(event_id, sid, ts, *, tokens, cost,
                         model="claude-opus-4-7"):
    """Slim ``model.completed`` sibling — no usage splits, just the
    daemon-stamped scalar token_count / cost_usd columns."""
    data = {
        "_v3_type": "message",
        "type": "model.completed",
        "modelId": model,
    }
    return {
        "id":           event_id,
        "node_id":      "node-test",
        "agent_type":   "openclaw",
        "agent_id":     "main",
        "session_id":   sid,
        "workspace_id": None,
        "event_type":   "model.completed",
        "ts":           ts,
        "data":         json.dumps(data),
        "cost_usd":     cost,
        "token_count":  tokens,
        "model":        model,
    }


def test_populated_store_returns_local_store_source(app):
    """Two assistant turns on one session — fast path must return both,
    correctly summed, with ``_source='local_store''."""
    a, ls, _usage = app
    store = ls.get_store()
    sid = "sess-token-attr"
    now = time.time()

    store.ingest(_assistant_row(
        "e1", sid, _iso(now - 120),
        input_t=1000, output_t=500, cache_read=200, cache_write=100,
        cost_total=0.012,
    ))
    store.ingest(_assistant_row(
        "e2", sid, _iso(now - 60),
        input_t=2000, output_t=800, cache_read=400, cache_write=0,
        cost_total=0.025,
    ))
    _drain(store)

    r = a.test_client().get("/api/token-attribution")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"expected _source=local_store; got {body.get('_source')!r}"
    )
    msgs = body.get("messages") or []
    assert len(msgs) == 2, f"expected 2 attributed turns; got {len(msgs)}"
    totals = body.get("totals") or {}
    assert totals.get("input_tokens") == 3000
    assert totals.get("output_tokens") == 1300
    assert totals.get("cache_read_tokens") == 600
    assert totals.get("cache_write_tokens") == 100
    assert totals.get("total_tokens") == 5000
    # Cost totals (allow tiny float wobble).
    assert abs(totals.get("total_cost", 0) - 0.037) < 1e-6
    assert totals.get("cache_hit_ratio_pct") == round(600 / 3600 * 100, 1)


def test_empty_store_returns_none_for_legacy_fallback(app):
    """No events at all → helper must return None so the legacy JSONL
    walker fires. Without this guard, a brand-new install would render
    a falsely-tagged ``_source='local_store'`` empty shell even when
    session JSONLs on disk DO carry attributable rows."""
    a, ls, usage_mod = app
    assert ls.get_store().query_events(limit=10) == []

    fast = usage_mod._try_local_store_token_attribution()
    assert fast is None, (
        f"empty store must return None; got {fast!r}"
    )


def test_v3_sibling_pair_does_not_double_count(app):
    """v3 dedupe guard (matches ``feedback_usage_dedupe_pattern.md``).

    A rich ``assistant`` row + a slim sibling ``model.completed`` ~0 s
    apart, both stamped with the same ``token_count``, must NOT yield
    two attribution rows or doubled totals. ``build_sibling_bucket_max``
    drops the slim sibling.
    """
    a, ls, usage_mod = app
    store = ls.get_store()
    sid = "sess-sibling"
    now = time.time()
    ts_iso = _iso(now - 30)

    store.ingest(_assistant_row(
        "e-rich", sid, ts_iso,
        input_t=3000, output_t=1500, cost_total=0.02,
    ))
    store.ingest(_model_completed_row(
        "e-slim", sid, ts_iso,
        tokens=4500, cost=0.02,
    ))
    _drain(store)

    fast = usage_mod._try_local_store_token_attribution()
    assert fast is not None
    msgs = fast.get("messages") or []
    assert len(msgs) == 1, (
        f"sibling pair double-counted; got {len(msgs)} rows: {msgs!r}"
    )
    totals = fast.get("totals") or {}
    assert totals.get("total_tokens") == 4500, (
        f"sibling double-count: expected 4500 total tokens, "
        f"got {totals.get('total_tokens')}"
    )
    assert abs(totals.get("total_cost", 0) - 0.02) < 1e-6


def test_session_id_filter_restricts_rows(app):
    """``?session_id=X`` must restrict the result to that session's
    turns only — query param is the explicit single-session drill-down
    contract the legacy handler offered."""
    a, ls, _usage = app
    store = ls.get_store()
    now = time.time()

    store.ingest(_assistant_row(
        "e-a", "sess-A", _iso(now - 60),
        input_t=1000, output_t=500, cost_total=0.01,
    ))
    store.ingest(_assistant_row(
        "e-b", "sess-B", _iso(now - 30),
        input_t=2000, output_t=1000, cost_total=0.02,
    ))
    _drain(store)

    r = a.test_client().get("/api/token-attribution?session_id=sess-A")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body.get("session_id") == "sess-A"
    msgs = body.get("messages") or []
    assert len(msgs) == 1
    assert msgs[0]["session_id"] == "sess-A"
    assert msgs[0]["tokens"]["total"] == 1500


def test_slim_completed_without_sibling_still_surfaces(app):
    """A standalone ``model.completed`` row (no rich sibling within the
    ±1 s window) must still produce an attribution row via the scalar-
    column fallback. Guards against the Eng G failure mode: don't
    silently drop tokens just because the rich envelope is absent."""
    a, ls, _usage = app
    store = ls.get_store()
    sid = "sess-slim-only"
    now = time.time()

    store.ingest(_model_completed_row(
        "e-solo", sid, _iso(now - 45),
        tokens=2500, cost=0.015,
    ))
    _drain(store)

    r = a.test_client().get("/api/token-attribution")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    msgs = body.get("messages") or []
    assert len(msgs) == 1, (
        f"slim model.completed dropped silently; got {msgs!r}"
    )
    totals = body.get("totals") or {}
    assert totals.get("total_tokens") == 2500
    assert abs(totals.get("total_cost", 0) - 0.015) < 1e-6
    # Role inferred from event_type when message envelope is absent.
    assert msgs[0]["role"] == "assistant"
