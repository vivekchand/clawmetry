"""Synthetic regression guard for /api/sessions/<id>/export DuckDB fast path
on real OpenClaw v3 event shapes (closes issue #1588, bug 1/2).

Before this PR ``routes/sessions.py::_try_local_store_session_export``
filtered ``ev_type == 'message'`` against DuckDB rows. On v3 installs the
daemon writes ``assistant`` / ``model.completed`` / ``prompt.submitted``
event types after normalising (see
``reference_openclaw_v3_event_types.md``), so the helper silently returned
an empty ``messages`` array AND the JSONL fallback never fired because the
helper still returned a populated wrapper object. Result: every real-v3
user's ``/api/sessions/<id>/export.json`` was empty.

This file seeds DuckDB with the SAME daemon-normalised event shapes that
``clawmetry/sync.py::_parse_v3_event`` writes and asserts:

1. Populated v3 store returns ``_source='local_store'`` with one
   ``messages[]`` row per billable turn (assistant + user) and correct
   token/cost totals.
2. Empty store → ``None`` so the legacy JSONL parser fires (the precise
   regression that bit the prior 6 fixes per PR #1583 / #1571 / etc.).
3. v3 sibling pair (``assistant`` + slim ``model.completed`` ~100 ms
   apart) must NOT double-count — single ``messages[]`` entry only.
4. Slim ``model.completed`` row with no rich sibling still surfaces via
   the scalar-column fallback (defends against Eng G's
   "blind-replace-aggregate-with-deduped-subset" failure mode).
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
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    # Issue #1538: isolate fixture from a developer's locally running
    # daemon (otherwise ``_ls_call`` proxies to prod DuckDB and our
    # seeded rows are invisible to the fast path).
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls, sessions_mod
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
                   model="claude-opus-4-7", text="ok"):
    """v3 ``assistant`` event the daemon writes for one LLM turn —
    Anthropic-SDK envelope under data.message.usage. See
    ``reference_openclaw_v3_event_types.md``."""
    data = {
        "_v3_type": "message",
        "type": "assistant",
        "message": {
            "role": "assistant",
            "model": model,
            "content": [{"type": "text", "text": text}],
            "usage": {
                "input": input_t,
                "output": output_t,
                "cacheRead": cache_read,
                "cacheWrite": cache_write,
                "cost": {"total": cost_total},
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
    data = {"_v3_type": "message", "type": "model.completed", "modelId": model}
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


def _prompt_submitted_row(event_id, sid, ts, *, prompt_text):
    """v3 ``prompt.submitted`` row — user turn. Text lives under
    ``data.finalPromptText`` per reference_openclaw_v3_event_types.md."""
    data = {
        "_v3_type": "message",
        "type": "prompt.submitted",
        "finalPromptText": prompt_text,
    }
    return {
        "id":           event_id,
        "node_id":      "node-test",
        "agent_type":   "openclaw",
        "agent_id":     "main",
        "session_id":   sid,
        "workspace_id": None,
        "event_type":   "prompt.submitted",
        "ts":           ts,
        "data":         json.dumps(data),
        "cost_usd":     0.0,
        "token_count":  0,
        "model":        None,
    }


def test_v3_populated_store_emits_messages_and_costs(app):
    """v3 ``prompt.submitted`` + ``assistant`` turns must populate the
    ``messages[]`` array. This is the bug the PR fixes: pre-fix this
    returned ``messages == []`` because the filter was ``ev_type ==
    'message'`` only."""
    a, ls, _sess = app
    store = ls.get_store()
    sid = "sess-v3-populated"
    now = time.time()

    store.ingest(_prompt_submitted_row(
        "e0", sid, _iso(now - 120),
        prompt_text="hello world",
    ))
    store.ingest(_assistant_row(
        "e1", sid, _iso(now - 119),
        input_t=1000, output_t=500, cache_read=200, cache_write=100,
        cost_total=0.012, text="hi",
    ))
    store.ingest(_assistant_row(
        "e2", sid, _iso(now - 60),
        input_t=2000, output_t=800, cache_read=400, cache_write=0,
        cost_total=0.025, text="thinking",
    ))
    _drain(store)

    r = a.test_client().get(f"/api/sessions/{sid}/export?format=json")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = json.loads(r.get_data(as_text=True))
    assert body.get("_source") == "local_store", (
        f"expected _source=local_store; got {body.get('_source')!r}"
    )
    msgs = body.get("messages") or []
    # 1 user + 2 assistant = 3 rows in chronological order (forward).
    assert len(msgs) == 3, f"expected 3 message rows; got {len(msgs)}: {msgs!r}"
    roles = [m["role"] for m in msgs]
    assert roles == ["user", "assistant", "assistant"], (
        f"role ordering mismatch: {roles!r}"
    )
    assert msgs[0]["content"] == "hello world", (
        f"prompt.submitted text not surfaced; got {msgs[0]!r}"
    )
    cost_data = body.get("cost_data") or {}
    assert cost_data.get("input_tokens") == 3000
    assert cost_data.get("output_tokens") == 1300
    assert cost_data.get("cache_read_tokens") == 600
    assert cost_data.get("cache_write_tokens") == 100
    assert abs(cost_data.get("total_cost_usd", 0) - 0.037) < 1e-6


def test_empty_store_returns_none_for_jsonl_fallback(app):
    """No events at all → helper must return ``None`` (not an empty-
    messages shell). This was the headline bug: the pre-fix helper
    returned ``{"messages": [], "_source": "local_store"}`` which
    SUPPRESSED the JSONL fallback so users who actually had on-disk
    transcripts still saw an empty export."""
    a, ls, sessions_mod = app
    assert ls.get_store().query_events(session_id="nope", limit=10) == []

    fast = sessions_mod._try_local_store_session_export("nope")
    assert fast is None, (
        f"empty store must return None; got {fast!r} "
        f"(this is the exact failure mode the 6 prior fixes shipped with)"
    )


def test_v3_sibling_pair_does_not_double_count(app):
    """A rich ``assistant`` + a slim sibling ``model.completed`` ~0 s
    apart with identical ``token_count`` must NOT yield two ``messages[]``
    entries. ``build_sibling_bucket_max`` drops the slim sibling.

    Same risk class as ``feedback_usage_dedupe_pattern.md``.
    """
    a, ls, sessions_mod = app
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

    fast = sessions_mod._try_local_store_session_export(sid)
    assert fast is not None
    msgs = fast.get("messages") or []
    assert len(msgs) == 1, (
        f"sibling pair double-counted in export; got {len(msgs)} "
        f"rows: {msgs!r}"
    )
    cost_data = fast.get("cost_data") or {}
    assert cost_data.get("total_tokens") == 4500, (
        f"sibling double-count: expected 4500 tokens, "
        f"got {cost_data.get('total_tokens')}"
    )
    assert abs(cost_data.get("total_cost_usd", 0) - 0.02) < 1e-6


def test_slim_model_completed_without_sibling_uses_scalar_fallback(app):
    """Standalone ``model.completed`` row (no rich sibling in ±1 s
    window) must still surface via the scalar-column fallback. Guards
    against Eng G's failure mode: don't silently drop tokens just
    because the rich envelope is missing.

    This is the second protection from the canonical pattern.
    """
    a, ls, sessions_mod = app
    store = ls.get_store()
    sid = "sess-slim-only"
    now = time.time()

    store.ingest(_model_completed_row(
        "e-solo", sid, _iso(now - 45),
        tokens=2500, cost=0.015,
    ))
    _drain(store)

    fast = sessions_mod._try_local_store_session_export(sid)
    assert fast is not None, (
        "slim model.completed dropped silently — scalar-column "
        "fallback missing"
    )
    msgs = fast.get("messages") or []
    assert len(msgs) == 1, (
        f"slim model.completed dropped silently; got {msgs!r}"
    )
    assert msgs[0]["role"] == "assistant"
    cost_data = fast.get("cost_data") or {}
    assert cost_data.get("total_tokens") == 2500
    assert abs(cost_data.get("total_cost_usd", 0) - 0.015) < 1e-6
