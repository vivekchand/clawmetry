"""Regression guard for /api/sessions/<sid>/model-transitions DuckDB fast path (Tier-1 #1565).

``routes/sessions.py:_try_local_store_model_transitions`` reads
``event_type='model.changed'`` rows for a single session out of the
DuckDB ``events`` table and folds them into the same ``transitions``
shape the legacy JSONL walker produces (``_detect_model_transitions``).

Real OpenClaw v3 emits an explicit ``model_change`` JSONL event for
every model switch which the sync daemon namespaces to ``model.changed``
(see ``tests/test_v3_schema_parser.py::test_v3_model_change_becomes_model_changed``
and ``reference_openclaw_v3_event_types.md``). Each row's ``data`` blob
carries ``modelId`` + ``provider`` — the only fields the response needs.

This file asserts:

1. Populated path → fast path returns ``_source='local_store'`` and the
   exact ``{turn, ts, from_model, from_provider, to_model, to_provider}``
   shape the legacy JSONL walker emits.
2. Single-model session (one model.changed event, never switched) →
   returns ``transitions=[]`` with ``_source='local_store'`` (NOT None —
   we proved DuckDB has the row, so don't fall through to JSONL).
3. Empty-store path → returns ``None`` so the legacy JSONL walker
   fallback fires (fresh installs whose daemon hasn't snapshotted
   model.changed events yet still see transitions via the disk file).
4. Chronological ordering — ``query_events`` returns most-recent first
   but transitions need ascending; the fast path must re-sort before
   walking. Guards against the silent-drop pattern from
   ``feedback_usage_dedupe_pattern.md``.
"""

from __future__ import annotations

import importlib
import uuid

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

    # Issue #1538 pattern: isolate the fixture from a contributor's locally
    # running clawmetry daemon. Without this, ``_ls_call`` proxies through
    # ``~/.clawmetry/local_query.json`` and the daemon queries its OWN
    # production DuckDB instead of our tmp_path fixture.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _wait_for_flush(store, timeout=2.0):
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)
    raise AssertionError("flusher did not drain the ring within timeout")


def _model_changed(sid: str, ts: str, *, model: str, provider: str):
    """Construct a ``model.changed`` event matching the v3 daemon's output
    shape (see ``tests/test_v3_schema_parser.py::test_v3_model_change_becomes_model_changed``).
    The ``data`` blob carries ``modelId`` + ``provider``; the top-level
    ``model`` column is the daemon-promoted convenience field."""
    return {
        "id":         str(uuid.uuid4()),
        "node_id":    "agent+test-node",
        "agent_type": "openclaw",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "model.changed",
        "ts":         ts,
        "data":       {"modelId": model, "provider": provider},
        "model":      model,
    }


def test_model_transitions_local_store_returns_local_store_source(app):
    """Two model switches → two transitions, tagged with ``_source='local_store'``
    and carrying the legacy {turn, ts, from_model, from_provider, to_model,
    to_provider} shape exactly. ``turn`` is the 1-based ordinal of the
    model.changed event in chronological order."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-transitions-a"

    store.ingest(_model_changed(sid, "2026-05-17T10:00:00Z",
                                model="claude-sonnet-4-5", provider="anthropic"))
    store.ingest(_model_changed(sid, "2026-05-17T10:05:00Z",
                                model="claude-opus-4-7", provider="anthropic"))
    store.ingest(_model_changed(sid, "2026-05-17T10:12:00Z",
                                model="gpt-4o", provider="openai"))
    _wait_for_flush(store)

    r = a.test_client().get(f"/api/sessions/{sid}/model-transitions")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"_source must be local_store; got {body.get('_source')!r}"
    )
    assert body.get("sessionId") == sid
    assert body.get("has_transitions") is True
    assert body.get("count") == 2

    transitions = body.get("transitions") or []
    assert len(transitions) == 2, transitions

    t1 = transitions[0]
    assert t1["turn"] == 2, t1["turn"]
    assert t1["from_model"] == "claude-sonnet-4-5"
    assert t1["to_model"] == "claude-opus-4-7"
    assert t1["from_provider"] == "anthropic"
    assert t1["to_provider"] == "anthropic"
    assert t1["ts"] == "2026-05-17T10:05:00Z"

    t2 = transitions[1]
    assert t2["turn"] == 3, t2["turn"]
    assert t2["from_model"] == "claude-opus-4-7"
    assert t2["to_model"] == "gpt-4o"
    assert t2["from_provider"] == "anthropic"
    assert t2["to_provider"] == "openai"
    assert t2["ts"] == "2026-05-17T10:12:00Z"


def test_model_transitions_local_store_single_model_returns_empty_list(app):
    """One ``model.changed`` event, no subsequent switches → fast path
    returns ``transitions=[]`` with ``_source='local_store'`` and
    ``has_transitions=False``. Critical: must NOT return None — the
    DuckDB row exists, so we KNOW there were no transitions and should
    keep the route off the legacy JSONL walker."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-single-model"

    store.ingest(_model_changed(sid, "2026-05-17T11:00:00Z",
                                model="claude-opus-4-7", provider="anthropic"))
    _wait_for_flush(store)

    r = a.test_client().get(f"/api/sessions/{sid}/model-transitions")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body.get("transitions") == []
    assert body.get("count") == 0
    assert body.get("has_transitions") is False


def test_model_transitions_local_store_returns_none_when_empty(app):
    """No ``model.changed`` rows for the session in DuckDB → fast path
    returns ``None`` so the legacy JSONL walker fallback fires. The
    handler must NOT short-circuit to an empty payload here: older
    OpenClaw installs whose daemon hasn't ingested model.changed yet
    need the on-disk JSONL walker to find their transitions."""
    _, ls = app
    import routes.sessions as sessions_mod
    fast = sessions_mod._try_local_store_model_transitions("never-seen")
    assert fast is None, (
        f"empty store must return None for legacy fallback; got {fast!r}"
    )


def test_model_transitions_local_store_orders_chronologically(app):
    """``query_events`` returns rows most-recent first; the fast path
    must re-sort ascending by ``ts`` before walking, otherwise the
    from/to pairing is inverted (last-ingested model becomes the start
    state, oldest becomes the destination). Ingest out of order to
    prove the sort. Guards against the silent-drop pattern from
    ``feedback_usage_dedupe_pattern.md``."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-out-of-order"

    # Ingest in REVERSE chronological order.
    store.ingest(_model_changed(sid, "2026-05-17T12:30:00Z",
                                model="gpt-4o", provider="openai"))
    store.ingest(_model_changed(sid, "2026-05-17T12:00:00Z",
                                model="claude-sonnet-4-5", provider="anthropic"))
    store.ingest(_model_changed(sid, "2026-05-17T12:15:00Z",
                                model="claude-opus-4-7", provider="anthropic"))
    _wait_for_flush(store)

    r = a.test_client().get(f"/api/sessions/{sid}/model-transitions")
    body = r.get_json()
    transitions = body.get("transitions") or []
    assert len(transitions) == 2

    # Chronological ordering: sonnet → opus → gpt-4o.
    assert transitions[0]["from_model"] == "claude-sonnet-4-5"
    assert transitions[0]["to_model"] == "claude-opus-4-7"
    assert transitions[1]["from_model"] == "claude-opus-4-7"
    assert transitions[1]["to_model"] == "gpt-4o"
    # Each transition's ts should be ascending too.
    assert transitions[0]["ts"] < transitions[1]["ts"]
