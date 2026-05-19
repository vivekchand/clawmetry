"""Synthetic regression guard for /api/flow-events on v3 sessions.

Closes the Tier-1 audit checkbox for ``/api/flow-events`` in #1565: the
JSON envelope returned to non-SSE clients used to be a static
``{ok, type, streaming}`` blob — no DuckDB read, no snapshot of recent
flow events. Cloud-Pro / external scrapers / E2E health checks that
can't hold an SSE connection had to round-trip through `/api/transcript`
to reconstruct the flow timeline.

This file seeds DuckDB with the SAME daemon-normalised event shapes the
OSS sync daemon writes for real OpenClaw v3 sessions (see
``clawmetry/sync.py::_parse_v3_event`` + reference_openclaw_v3_event_types.md)
and asserts:

1. An empty local store falls through (caller fires legacy JSONL parser).
2. A populated store hydrates the envelope with ``events[]`` + ``_source: 'local_store'``.
3. Event ordering is chronological (matches SSE prefix).
4. The four flow lanes are populated correctly: msg_in (user / prompt.submitted),
   msg_out (assistant / model.completed), tool_call (toolMetas inside
   model.completed AND standalone tool.call rows), tool_result.
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
    import routes.infra as infra_mod
    importlib.reload(infra_mod)

    # Issue #1538 pattern: isolate fixture from a developer's locally-
    # running clawmetry daemon (otherwise ``_ls_call`` proxies through
    # ``~/.clawmetry/local_query.json`` and queries the daemon's production
    # DuckDB instead of our tmp_path fixture — seeded rows become invisible
    # to the fast path).
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(infra_mod.bp_logs)
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
    """Build a DuckDB events row matching what
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


def test_empty_local_store_returns_legacy_envelope(app):
    """When DuckDB has zero flow-relevant rows the helper returns None and
    the route falls back to the static envelope. Critical: this keeps the
    legacy SSE-only behaviour intact for fresh installs.

    The envelope still includes ``events: []`` so the on-the-wire shape is
    stable for non-SSE callers (refs #1763 — keystone E2E verifier expects
    ``.events`` / ``.ok`` keys regardless of local-store state)."""
    a, _ls = app
    r = a.test_client().get("/api/flow-events", headers={"Accept": "application/json"})
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("ok") is True
    assert body.get("type") == "flow-events"
    assert body.get("streaming") is True
    # No DuckDB rows → no _source tag, but events is always present (empty).
    assert "_source" not in body
    assert body.get("events") == []


def test_populated_local_store_hydrates_envelope(app):
    """A real v3 conversation must surface as a chronological list of
    msg_in / tool_call / msg_out / tool_result events tagged
    ``_source: 'local_store'``."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-flow-v3"
    tcid = "toolu_flow_abc"

    store.ingest(_row("e1", sid, "session.started", "2026-05-17T12:00:00Z",
                      {"_v3_type": "session", "type": "session.started",
                       "id": sid}))
    store.ingest(_row("e2", sid, "prompt.submitted", "2026-05-17T12:00:01Z",
                      {"_v3_type": "message", "type": "prompt.submitted",
                       "finalPromptText": "read /etc/hosts",
                       "channel": "telegram"}))
    store.ingest(_row(
        "e3", sid, "model.completed", "2026-05-17T12:00:02Z",
        {
            "_v3_type": "message", "type": "model.completed",
            "completionText": "I'll read that.",
            "modelId": "claude-opus-4-7",
            "provider": "anthropic",
            "channel": "telegram",
            "toolMetas": [
                {"id": tcid, "name": "Read", "input": {"path": "/etc/hosts"}},
            ],
        },
        model="claude-opus-4-7", cost_usd=0.0034,
    ))
    store.ingest(_row(
        "e4", sid, "tool.result", "2026-05-17T12:00:03Z",
        {
            "_v3_type": "tool_use_result", "type": "tool.result",
            "tool_use_id": tcid, "tool_name": "Read",
            "output": "127.0.0.1 localhost\n",
            "is_error": False,
        },
    ))
    _drain(store)

    r = a.test_client().get("/api/flow-events", headers={"Accept": "application/json"})
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("ok") is True, f"envelope shape regressed: {body!r}"
    assert body.get("type") == "flow-events"
    assert body.get("_source") == "local_store", (
        f"_source must be local_store on populated store; got {body.get('_source')!r}"
    )
    events = body.get("events") or []
    assert events, f"expected populated events list, got {events!r}"

    # Chronological order (msg_in must precede msg_out / tool_*).
    types = [e.get("type") for e in events]
    assert "msg_in" in types, f"missing msg_in lane: {types}"
    assert "msg_out" in types, f"missing msg_out lane: {types}"
    assert "tool_call" in types, f"missing tool_call lane: {types}"
    assert "tool_result" in types, f"missing tool_result lane: {types}"
    assert types.index("msg_in") < types.index("msg_out"), (
        f"events not chronological: {types}"
    )

    # Channel propagation — the prompt + completion both carry channel='telegram'.
    msg_in = next(e for e in events if e.get("type") == "msg_in")
    assert msg_in.get("channel") == "telegram", (
        f"msg_in channel lost: {msg_in!r}"
    )
    # Tool key mapping: 'Read' → 'exec'.
    tool_call = next(e for e in events if e.get("type") == "tool_call")
    assert tool_call.get("tool") == "exec", (
        f"tool key mapping broken: {tool_call!r}"
    )
    tool_result = next(e for e in events if e.get("type") == "tool_result")
    assert tool_result.get("tool") == "exec"

    # Every event must carry the session id + per-row source tag for
    # easy joining on the client.
    for ev in events:
        assert ev.get("session_id") == sid
        assert ev.get("_source") == "local_store"


def test_standalone_tool_call_event_is_surfaced(app):
    """Some adapters emit a standalone tool.call row instead of folding
    the tool_use into model.completed. Both shapes must populate the
    tool_call lane."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-flow-standalone"

    store.ingest(_row("e1", sid, "session.started", "2026-05-17T13:00:00Z",
                      {"_v3_type": "session", "type": "session.started"}))
    store.ingest(_row("e2", sid, "tool.call", "2026-05-17T13:00:01Z",
                      {"_v3_type": "tool_call", "type": "tool.call",
                       "tool_name": "web_search"}))
    _drain(store)

    r = a.test_client().get("/api/flow-events", headers={"Accept": "application/json"})
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store"
    events = body.get("events") or []
    tool_calls = [e for e in events if e.get("type") == "tool_call"]
    assert tool_calls, f"standalone tool.call dropped: {events!r}"
    # web_search → 'search' per _FLOW_TOOL_MAP.
    assert tool_calls[0].get("tool") == "search"


def test_flow_alias_route_preserves_envelope(app):
    """`/api/flow` is registered as an alias on the same handler. The
    live-E2E (`test_every_api_endpoint_returns_correct_data`) asserts
    the basic envelope on `/api/flow`; this guards that the fast path
    doesn't drop the `ok`/`type` keys."""
    a, ls = app
    store = ls.get_store()
    sid = "sess-flow-alias"
    store.ingest(_row("e1", sid, "prompt.submitted", "2026-05-17T14:00:00Z",
                      {"_v3_type": "message", "type": "prompt.submitted",
                       "finalPromptText": "hi"}))
    _drain(store)

    r = a.test_client().get("/api/flow", headers={"Accept": "application/json"})
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("ok") is True
    assert body.get("type") == "flow-events"
    # And fast-path is wired on this route too.
    assert body.get("_source") == "local_store"
