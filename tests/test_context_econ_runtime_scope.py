"""/api/context-economics must honour ?runtime= server-side (no leak).

Shipped with the "LLM Context → Context usage" merge (2026-08-01): the old
LLM Context tab was the last _CM_RT_AGGREGATE entry (node-wide numbers under
a runtime filter, plus fabricated composition estimates). Context usage is
now the single context surface, so its route has to scope server-side by
runtime the way the cloud interceptor already does via the snapshot's
``contextEconomics.byRuntime`` slice.

Asserts, against a real DuckDB fixture:
  1. Unscoped call returns utilization for every runtime's sessions.
  2. ``runtime=claude_code`` returns ONLY ``claude_code:*`` sessions —
     utilization, session chips and compactions all scope.
  3. ``runtime=openclaw`` returns only bare-uuid (non-prefixed) sessions.
  4. An unknown runtime label returns EMPTY lists, never the node-wide
     totals (the silent-leak contract from FLYWHEEL hard gate 2).
  5. ``runtime=all`` behaves exactly like no filter.

Revert-proof: on pre-merge code (no ``runtime`` kwarg on
``query_context_economics``) case 2 fails with a leak — verified red before
the fix, green after.
"""

from __future__ import annotations

import importlib
import time

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Flask app with bp_context_economics registered, fresh DuckDB per test."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Hermetic isolation from a dev machine's live daemon (same pattern as
    # tests/test_context_anatomy_local_store.py): force the writer-owner
    # path + stub discovery so reads open the tmp_path store in-process.
    ls.mark_writer_owner()
    import routes.local_query as _lq
    monkeypatch.setattr(_lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(_lq, "_cached_discovery", lambda: None)
    import routes.context_economics as ce_mod
    importlib.reload(ce_mod)

    a = Flask(__name__)
    a.register_blueprint(ce_mod.bp_context_economics)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _ingest_turn(store, *, sid: str, ts: str, input_tokens: int):
    store.ingest({
        "id":         f"turn-{sid}-{ts}",
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "message",
        "ts":         ts,
        "data":       {"message": {"role": "assistant",
                                   "usage": {"input_tokens": input_tokens,
                                             "output_tokens": 50}}},
        "cost_usd":   0.001,
        "token_count": input_tokens,
        "model":      "claude-opus-4-7",
    })


def _ingest_compaction(store, *, sid: str, ts: str, tokens_before: int):
    store.ingest({
        "id":         f"comp-{sid}-{ts}",
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "compaction",
        "ts":         ts,
        "data":       {"tokensBefore": tokens_before, "fromHook": True,
                       "summary": "compacted", "timestamp": ts},
    })


def _seed(store):
    # claude_code runtime (prefixed session ids)
    _ingest_turn(store, sid="claude_code:aaa", ts="2026-08-01T10:00:00Z", input_tokens=40_000)
    _ingest_turn(store, sid="claude_code:aaa", ts="2026-08-01T10:01:00Z", input_tokens=55_000)
    _ingest_compaction(store, sid="claude_code:aaa", ts="2026-08-01T10:02:00Z", tokens_before=150_000)
    # openclaw runtime (bare uuid, no prefix)
    _ingest_turn(store, sid="bare-uuid-1", ts="2026-08-01T11:00:00Z", input_tokens=20_000)
    _ingest_compaction(store, sid="bare-uuid-1", ts="2026-08-01T11:02:00Z", tokens_before=90_000)
    _wait_flush(store)


def _sids(body):
    return {str(u["session_id"]) for u in body["utilization"]}


def test_unscoped_returns_all_runtimes(app):
    a, ls = app
    _seed(ls.get_store())
    body = a.test_client().get("/api/context-economics").get_json()
    assert _sids(body) == {"claude_code:aaa", "bare-uuid-1"}
    assert body["summary"]["compaction_count"] == 2


def test_runtime_scopes_to_claude_code_only(app):
    a, ls = app
    _seed(ls.get_store())
    body = a.test_client().get("/api/context-economics?runtime=claude_code").get_json()
    assert _sids(body) == {"claude_code:aaa"}, (
        "runtime=claude_code leaked other runtimes' utilization"
    )
    assert {c["session_id"] for c in body["session_chips"]} == {"claude_code:aaa"}
    assert {c["session_id"] for c in body["compactions"]} == {"claude_code:aaa"}
    assert body["summary"]["compaction_count"] == 1


def test_runtime_scopes_to_openclaw_bare_sessions(app):
    a, ls = app
    _seed(ls.get_store())
    body = a.test_client().get("/api/context-economics?runtime=openclaw").get_json()
    assert _sids(body) == {"bare-uuid-1"}
    assert {c["session_id"] for c in body["compactions"]} == {"bare-uuid-1"}


def test_unknown_runtime_returns_empty_not_nodewide(app):
    a, ls = app
    _seed(ls.get_store())
    body = a.test_client().get("/api/context-economics?runtime=not-a-runtime").get_json()
    assert body["utilization"] == []
    assert body["compactions"] == []
    assert body["summary"]["compaction_count"] == 0


def test_runtime_all_is_unscoped(app):
    a, ls = app
    _seed(ls.get_store())
    body = a.test_client().get("/api/context-economics?runtime=all").get_json()
    assert _sids(body) == {"claude_code:aaa", "bare-uuid-1"}
