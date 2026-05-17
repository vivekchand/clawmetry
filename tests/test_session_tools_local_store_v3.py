"""Synthetic regression guard for /api/session-tools on v3 sessions.

Closes the MOAT coverage gap exposed by PR #1559's live-OpenClaw E2E:
``_try_local_store_session_tools`` used to filter on
``event_type='message'`` (legacy) or ``event_type='tool_call'``. Real
OpenClaw v3 emits NEITHER for the common no-tool turn shape — sessions
only carry ``session.started`` / ``prompt.submitted`` / ``model.completed``
rows, so the fast path returned ``None`` and the route silently fell
through to the legacy JSONL parser. That bypass meant a DuckDB regression
would never visibly break the session-tools surface.

This file seeds DuckDB with the SAME event shapes the OSS sync daemon
writes for real v3 sessions (see ``clawmetry/sync.py::_parse_v3_event``)
and asserts:

1. A session with ONLY lifecycle events (no tool calls) returns
   ``_source='local_store'`` with an empty ``tools[]``.
2. A session whose ``model.completed`` event carries a ``toolMetas``
   block (the daemon's projection of Anthropic-shape ``tool_use``)
   surfaces those tool calls AND pairs them with a sibling
   ``tool.result`` event.
"""

from __future__ import annotations

import importlib
import json
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
    # production DuckDB instead of our tmp_path fixture — seeded rows
    # become invisible to the fast path.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _drain(store):
    store._flush_now()
    for _ in range(10):
        if not store._ring:
            break
        time.sleep(0.05)


def _row(event_id, sid, event_type, ts, data, **extra):
    """Build a DuckDB events row that matches what
    ``clawmetry/sync.py::_parse_v3_event`` produces for v3 sessions."""
    base = {
        "id":          event_id,
        "node_id":     "node-test",
        "agent_type":  "openclaw",
        "agent_id":    "main",
        "session_id":  sid,
        "workspace_id": None,
        "event_type":  event_type,
        "ts":          ts,
        "data":        json.dumps(data),
    }
    base.update(extra)
    return base


def test_v3_session_with_no_tools_serves_from_local_store(app):
    """An auth-failed / chat-only v3 session has session.started +
    prompt.submitted + model.completed in DuckDB but ZERO tool events.
    The fast path must return an empty-but-correctly-tagged payload."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-v3-notools"

    store.ingest(_row("e1", sid, "session.started", "2026-05-17T10:00:00Z",
                      {"_v3_type": "session", "type": "session.started",
                       "id": sid, "version": "3"}))
    store.ingest(_row("e2", sid, "prompt.submitted", "2026-05-17T10:00:01Z",
                      {"_v3_type": "message", "type": "prompt.submitted",
                       "finalPromptText": "hello"}))
    store.ingest(_row("e3", sid, "model.completed", "2026-05-17T10:00:02Z",
                      {"_v3_type": "message", "type": "model.completed",
                       "completionText": "hi back",
                       "modelId": "claude-opus-4-7",
                       "provider": "anthropic"},
                      model="claude-opus-4-7"))
    _drain(store)

    r = a.test_client().get(f"/api/session-tools?session_id={sid}&include_unpaired=1")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"_source must be local_store for v3 lifecycle-only session; "
        f"got {body.get('_source')!r}"
    )
    assert body.get("tools") == [], f"expected empty tools, got {body.get('tools')!r}"
    assert body.get("by_tool") == []
    stats = body.get("stats") or {}
    assert stats.get("total_calls") == 0
    assert stats.get("distinct_tools") == 0
    # first_start_ms must be populated from session.started so the UI has
    # an anchor for the empty timeline.
    assert stats.get("first_start_ms", 0) > 0, (
        f"first_start_ms not set from lifecycle ts: {stats!r}"
    )


def test_v3_session_with_tool_use_in_model_completed_pairs_results(app):
    """Real v3 tool calls land as ``toolMetas`` ({id, name, input}) inside
    ``model.completed.data`` and the matching result is a top-level
    ``tool.result`` event with ``data.tool_use_id``. Both shapes must be
    parsed and paired."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-v3-withtool"
    tcid = "toolu_abc123"

    store.ingest(_row("e1", sid, "session.started", "2026-05-17T11:00:00Z",
                      {"_v3_type": "session", "type": "session.started",
                       "id": sid}))
    store.ingest(_row("e2", sid, "prompt.submitted", "2026-05-17T11:00:01Z",
                      {"_v3_type": "message", "type": "prompt.submitted",
                       "finalPromptText": "read /etc/hosts"}))
    store.ingest(_row(
        "e3", sid, "model.completed", "2026-05-17T11:00:02Z",
        {
            "_v3_type": "message", "type": "model.completed",
            "completionText": "I'll read that file.",
            "modelId": "claude-opus-4-7",
            "provider": "anthropic",
            "toolMetas": [
                {"id": tcid, "name": "Read",
                 "input": {"path": "/etc/hosts"}},
            ],
        },
        model="claude-opus-4-7", cost_usd=0.0034,
    ))
    store.ingest(_row(
        "e4", sid, "tool.result", "2026-05-17T11:00:03Z",
        {
            "_v3_type": "tool_use_result", "type": "tool.result",
            "tool_use_id": tcid,
            "output": "127.0.0.1 localhost\n",
            "result": "127.0.0.1 localhost\n",
            "is_error": False,
        },
    ))
    _drain(store)

    r = a.test_client().get(f"/api/session-tools?session_id={sid}&include_unpaired=1")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"_source must be local_store; got {body.get('_source')!r}"
    )

    tools = body.get("tools") or []
    assert len(tools) == 1, f"expected 1 tool, got {len(tools)}: {tools!r}"
    rec = tools[0]
    assert rec.get("tool_call_id") == tcid
    assert rec.get("tool_name") == "Read"
    assert rec.get("model") == "claude-opus-4-7"
    assert rec.get("provider") == "anthropic"
    assert rec.get("paired") is True, f"tool not paired with result: {rec!r}"
    assert rec.get("is_error") is False
    assert "127.0.0.1" in (rec.get("result_preview") or "")

    by_tool = body.get("by_tool") or []
    assert len(by_tool) == 1 and by_tool[0]["tool_name"] == "Read"
    assert by_tool[0]["calls"] == 1
    assert by_tool[0]["errors"] == 0

    stats = body.get("stats") or {}
    assert stats.get("total_calls") == 1
    assert stats.get("paired_calls") == 1
    assert stats.get("distinct_tools") == 1
    assert stats.get("first_start_ms", 0) > 0
    assert stats.get("last_end_ms", 0) >= stats["first_start_ms"]
