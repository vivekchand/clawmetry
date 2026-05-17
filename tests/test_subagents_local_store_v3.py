"""Regression guard for /api/subagents DuckDB fast path (Tier-1 #1565).

``routes/sessions.py:_try_local_store_subagents`` reads the
pre-aggregated ``subagents`` table that the sync daemon snapshots on
every pass (``clawmetry/sync.py`` -> ``ingest_subagent``). Before the
fast path, the route always walked up to 120 session JSONLs to pair
``subagents action=spawn`` toolCall/toolResult rows. With the fast
path, a healthy daemon serves the Subagent Tracker tab from one
DuckDB query.

This file seeds DuckDB via the daemon's canonical
``LocalStore.ingest_subagent`` helper (same shape sync.py uses) and
asserts:

1. A parent session with two children + tokens + statuses → fast path
   returns ``_source='local_store'`` and the correct status buckets.
2. Empty-store edge case → returns ``None`` so the legacy fallback
   keeps working for fresh installs whose daemon hasn't snapshotted
   any subagents yet.
3. Subagent with no explicit status / no extra data → derives status
   from ``updated_at`` age and surfaces zero tokens cleanly.
"""

from __future__ import annotations

import importlib
import time

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


def test_subagents_local_store_returns_local_store_source(app):
    """Two children for one parent → fast path returns both rows tagged
    with ``_source='local_store'`` and the parent/child relationship
    preserved on each row."""
    a, ls = app
    store = ls.get_store()
    parent_sid = "parent-session-xyz"

    store.ingest_subagent({
        "subagent_id":       "child-a",
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-17T10:00:00Z",
        "task":              "refactor auth.py",
        "status":            "active",
        "cost_usd":          0.0234,
        "token_count":       4200,
        "model":             "claude-opus-4-7",
        "label":             "auth-refactor",
        "displayName":       "auth-refactor",
        "runtime_ms":        15000,
        "updated_at_ms":     int(time.time() * 1000),
    })
    store.ingest_subagent({
        "subagent_id":       "child-b",
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-17T10:01:00Z",
        "task":              "summarise transcripts",
        "status":            "completed",
        "cost_usd":          0.0089,
        "token_count":       1800,
        "model":             "claude-opus-4-7",
        "label":             "summariser",
        "runtime_ms":        8000,
        "updated_at_ms":     int(time.time() * 1000),
    })

    r = a.test_client().get("/api/subagents")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"_source must be local_store; got {body.get('_source')!r}"
    )
    subs = body.get("subagents") or []
    ids = {s["sessionId"] for s in subs}
    assert ids == {"child-a", "child-b"}, f"expected both children, got {ids!r}"

    by_id = {s["sessionId"]: s for s in subs}
    assert by_id["child-a"]["parent"] == parent_sid
    assert by_id["child-a"]["totalTokens"] == 4200
    assert by_id["child-a"]["task"] == "refactor auth.py"
    assert by_id["child-a"]["model"] == "claude-opus-4-7"
    assert by_id["child-a"]["status"] == "active"
    # Canonical OpenClaw key shape — Active-Tasks modal lookups depend on it.
    assert by_id["child-a"]["key"].startswith("agent:main:subagent:")
    # ``completed`` is not in the legacy status bucket — fast path keeps
    # the daemon's classification verbatim so the UI can switch on it.
    assert by_id["child-b"]["status"] == "completed"

    counts = body.get("counts") or {}
    assert counts.get("total") == 2
    assert counts.get("active") == 1


def test_subagents_local_store_returns_none_when_empty(app):
    """No rows in the ``subagents`` table → fast path returns None so
    the legacy gateway-RPC + JSONL fallback fires. ``_try_local_store_subagents``
    must NOT swallow the empty case as a populated zero-shell here:
    older OpenClaw installs that don't write to the table need the
    fallback path to find spawn events on disk."""
    a, ls = app
    # Sanity: store is empty.
    assert ls.get_store().query_subagents(limit=10) == []

    import routes.sessions as sessions_mod
    fast = sessions_mod._try_local_store_subagents()
    assert fast is None, (
        f"empty store must return None for legacy fallback; got {fast!r}"
    )


def test_subagents_local_store_derives_status_from_age(app):
    """A subagent ingested without an explicit status field and with an
    old ``updated_at_ms`` should bucket as ``stale`` via the
    age-based fallback (same buckets as the legacy path)."""
    a, ls = app
    store = ls.get_store()
    # ~30 min old → stale (>10 min threshold).
    old_ms = int(time.time() * 1000) - 30 * 60 * 1000
    store.ingest_subagent({
        "subagent_id":       "lonely-child",
        "agent_type":        "openclaw",
        "parent_session_id": "parent-lonely",
        "spawned_at":        "2026-05-17T09:00:00Z",
        "task":              "long-running deep dive",
        # NOTE: no ``status`` field — daemon may omit when it doesn't
        # know the classification (e.g. registry not yet polled).
        "token_count":       0,
        "updated_at_ms":     old_ms,
    })

    import routes.sessions as sessions_mod
    fast = sessions_mod._try_local_store_subagents()
    assert fast is not None
    assert fast.get("_source") == "local_store"
    subs = fast.get("subagents") or []
    assert len(subs) == 1
    s = subs[0]
    assert s["sessionId"] == "lonely-child"
    assert s["status"] == "stale", (
        f"old subagent without explicit status must derive to stale; got {s['status']!r}"
    )
    assert s["totalTokens"] == 0
    # ``runtimeMs`` should be populated from spawn time even when the
    # daemon didn't stamp ``runtime_ms`` explicitly.
    assert s["runtimeMs"] >= 0
    assert s["runtime"], f"runtime string must be set; got {s['runtime']!r}"
