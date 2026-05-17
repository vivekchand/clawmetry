"""Synthetic safety net for /api/token-velocity DuckDB fast path
(Tier-1 surface #5 in issue #1565).

``routes/usage.py::_try_local_store_token_velocity`` reads the trailing
~5 min of events from DuckDB to detect runaway agent loops without
walking N session JSONLs on every poll (the legacy path opens every
file mtime'd within 5 min — up to 20 files per request).

This file seeds DuckDB with the SAME daemon-normalised event shapes the
OSS sync daemon writes for real OpenClaw v3 sessions
(``reference_openclaw_v3_event_types.md``) and asserts:

1. Populated store within the 2-min window returns ``_source='local_store'``
   with summed tokens, alert level, and flagged sessions.
2. Empty store returns None so the legacy JSONL fallback fires for
   fresh installs whose daemon hasn't ingested anything yet.
3. Reachable store with rows but none in the trailing 5 min returns
   None — the legacy JSONL walker is cheap on a quiet system (mtime
   filter skips every file with no recent writes) so we don't try to
   short-circuit it with a zero shell.
4. Dedupe-pattern guard: a v3 sibling pair (``assistant`` + sibling
   ``model.completed`` ~100ms apart with identical ``token_count``)
   must NOT double-count. Same risk class as
   ``feedback_usage_dedupe_pattern.md`` (Eng G hit it on
   /api/usage/forecast in PR #1571).
5. Tool-chain length: a long run of tool.call rows on one session
   trips ``level=critical`` even when token volume alone is low —
   matches the legacy ``CRIT_TOOLS=20`` rule.
"""

from __future__ import annotations

import importlib
import json
import time
from datetime import datetime, timedelta, timezone

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
    # running clawmetry daemon. Without this, ``_ls_call`` proxies through
    # ``~/.clawmetry/local_query.json`` and queries the daemon's
    # production DuckDB instead of our tmp_path fixture, so seeded rows
    # are invisible to the fast path.
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


def _row(event_id, sid, event_type, ts, data, **extra):
    """Build a DuckDB events row matching what
    ``clawmetry/sync.py::_parse_v3_event`` produces for v3 sessions."""
    base = {
        "id":           event_id,
        "node_id":      "node-test",
        "agent_type":   "openclaw",
        "agent_id":     "main",
        "session_id":   sid,
        "workspace_id": None,
        "event_type":   event_type,
        "ts":           ts,
        "data":         json.dumps(data),
    }
    base.update(extra)
    return base


def test_populated_store_returns_local_store_source(app):
    """A single hot session burning >WARN_TOKENS in the trailing 2 min
    should surface ``_source='local_store'`` + a populated
    ``flagged_sessions`` list with the right token total."""
    a, ls, _usage = app
    store = ls.get_store()
    sid = "sess-velocity-hot"
    now = time.time()

    # Three model.completed events within the last 2 min, ~3000 tok each
    # → 9000 total → trips WARN_TOKENS (8000) but not CRIT_TOKENS (15000).
    for i, dt in enumerate([90, 60, 30]):
        store.ingest(_row(
            f"e{i}", sid, "model.completed", _iso(now - dt),
            {"_v3_type": "message", "type": "model.completed",
             "provider": "anthropic", "modelId": "claude-opus-4-7"},
            cost_usd=0.012, token_count=3000, model="claude-opus-4-7",
        ))
    _drain(store)

    r = a.test_client().get("/api/token-velocity")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"_source must be local_store; got {body.get('_source')!r}"
    )
    assert body.get("velocity_2min") == 9000, (
        f"expected 9000 tokens in 2-min window, got {body.get('velocity_2min')}"
    )
    assert body.get("level") == "warning", (
        f"9000 tokens should bucket as warning; got {body.get('level')!r}"
    )
    assert body.get("alert") is True
    flagged = body.get("flagged_sessions") or []
    assert len(flagged) == 1
    assert flagged[0]["id"] == sid
    assert flagged[0]["tokens_2min"] == 9000


def test_empty_store_returns_none_for_legacy_fallback(app):
    """No rows at all → helper returns None so the legacy JSONL walker
    fires. Critical for fresh installs whose daemon hasn't snapshotted
    anything yet — without this guard, brand-new dashboards would
    silently render an empty velocity panel even when session JSONLs
    on disk DO contain recent activity."""
    a, ls, usage_mod = app
    # Sanity: store is empty.
    assert ls.get_store().query_events(limit=10) == []

    fast = usage_mod._try_local_store_token_velocity()
    assert fast is None, (
        f"empty store must return None for legacy fallback; got {fast!r}"
    )


def test_store_with_only_old_events_returns_none(app):
    """Store has rows but ALL of them are >5 min old → helper returns
    None so the legacy JSONL walker fires. The walker is cheap on a
    quiet system (mtime filter skips every file with no recent writes)
    so we don't try to short-circuit with a zero shell."""
    a, ls, usage_mod = app
    store = ls.get_store()
    now = time.time()
    # 10 minutes old → outside the 5-min query window.
    store.ingest(_row(
        "e-old", "sess-cold", "model.completed", _iso(now - 600),
        {"_v3_type": "message", "type": "model.completed"},
        cost_usd=0.01, token_count=2000, model="claude-opus-4-7",
    ))
    _drain(store)

    fast = usage_mod._try_local_store_token_velocity()
    assert fast is None, (
        f"old events only → must return None for legacy fallback; got {fast!r}"
    )


def test_v3_sibling_pair_does_not_double_count(app):
    """v3 dedupe guard (matches ``feedback_usage_dedupe_pattern.md``).

    Real OpenClaw v3 emits an ``assistant`` row AND a sibling
    ``model.completed`` ~100 ms later, both stamped with the same
    ``token_count``. A naive sum doubles every billable turn — same
    bug class that bit /api/usage and /api/usage/forecast.

    Seed: one assistant + one model.completed sibling, both with
    token_count=5000 within the 2-min window. Expected: velocity_2min
    == 5000 (NOT 10000), level=='ok' (below 8000 WARN).
    """
    a, ls, _usage = app
    store = ls.get_store()
    sid = "sess-sibling"
    now = time.time()
    ts_iso = _iso(now - 30)
    # Sibling pair on the SAME second so build_sibling_bucket_max
    # collapses them.
    store.ingest(_row(
        "e-assistant", sid, "assistant", ts_iso,
        {"_v3_type": "message", "type": "assistant",
         "modelId": "claude-opus-4-7"},
        cost_usd=0.02, token_count=5000, model="claude-opus-4-7",
    ))
    store.ingest(_row(
        "e-completed", sid, "model.completed", ts_iso,
        {"_v3_type": "message", "type": "model.completed",
         "modelId": "claude-opus-4-7"},
        cost_usd=0.02, token_count=5000, model="claude-opus-4-7",
    ))
    _drain(store)

    fast = _app_get_fast(a, _usage)
    assert fast.get("_source") == "local_store"
    assert fast.get("velocity_2min") == 5000, (
        "v3 sibling pair double-counted — dedupe regression; "
        f"got velocity_2min={fast.get('velocity_2min')}"
    )
    assert fast.get("level") == "ok"


def test_long_tool_chain_trips_critical(app):
    """A session burning a long tool chain (>=CRIT_TOOLS=20 consecutive
    tool calls without a user prompt break) should classify as
    ``level='critical'`` even when token volume is below CRIT_TOKENS.
    This matches the legacy JSONL handler's ``max_chain >= CRIT_TOOLS``
    branch — runaway-loop detection without waiting for the cost spike."""
    a, ls, _usage = app
    store = ls.get_store()
    sid = "sess-loop"
    now = time.time()
    # 25 tool.call rows in the last 90s → max_chain >= 20.
    for i in range(25):
        store.ingest(_row(
            f"e-tool-{i}", sid, "tool.call", _iso(now - 90 + i),
            {"_v3_type": "tool_call", "type": "tool.call",
             "tool_name": "Bash"},
        ))
    _drain(store)

    fast = _app_get_fast(a, _usage)
    assert fast.get("_source") == "local_store"
    assert fast.get("level") == "critical", (
        f"long tool chain should trip critical; got {fast.get('level')!r}"
    )
    assert fast.get("alert") is True
    flagged = fast.get("flagged_sessions") or []
    assert any(s["id"] == sid and s["tool_chain_len"] >= 20 for s in flagged), (
        f"flagged_sessions missing the looping session: {flagged!r}"
    )


def _app_get_fast(a, usage_mod):
    """Helper: call the fast path directly so we can introspect the dict
    shape (rather than reaching through the JSON envelope)."""
    fast = usage_mod._try_local_store_token_velocity()
    assert fast is not None
    return fast
