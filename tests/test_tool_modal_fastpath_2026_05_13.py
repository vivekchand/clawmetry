"""Audit P0 #4 — tool-modal DuckDB fast path matches the actual event_type.

Before: ``routes/components.py:_try_local_store_component_tool`` queried
``event_type='tool_call'`` rows that the daemon never writes —
``clawmetry/sync.py:1375`` writes ``event_type=obj.get('type')`` which is
the raw OpenClaw type (``message`` / ``assistant`` / ``user`` / …). The
fast path returned ``None`` for every tool, all 10 component-tool
endpoints fell through to legacy JSONL parsing, and the audit's
``_source: 'local_store'`` marker never appeared.

After: the helper queries ``message`` / ``assistant`` rows, walks
``data.message.content[]`` for ``toolCall`` / ``tool_use`` blocks, and
filters by tool family. These tests ingest one synthetic event per tool
name, hit ``/api/component/tool/<name>``, and assert the response carries
``_source == 'local_store'`` plus the event we just ingested.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Reload local_store + components blueprint against a per-test DuckDB."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.components as comp
    importlib.reload(comp)

    a = Flask(__name__)
    a.register_blueprint(comp.bp_components)
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


def _now_iso() -> str:
    """Today-stamped timestamp so the helper's ``ts.startswith(today)``
    filter accepts it. UTC because that's what OpenClaw emits."""
    return datetime.now(tz=timezone.utc).isoformat()


def _ingest_message_with_tool_block(
    store, *, tool_name: str, args: dict, ev_id: str = "ev-1"
) -> str:
    """Insert one OpenClaw-shaped ``message`` event whose
    ``data.message.content[]`` contains a single ``toolCall`` block for
    ``tool_name`` with ``args``."""
    ts = _now_iso()
    store.ingest({
        "id": ev_id,
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "sess-fast",
        "event_type": "message",  # the raw OpenClaw type, per sync.py:1375
        "ts": ts,
        "data": {
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "toolCall", "name": tool_name, "arguments": args},
                ],
            },
        },
        "cost_usd": 0.0,
        "token_count": 0,
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)
    return ts


# ─────────────────────────────────────────────────────────────────────────────
# One test per tool family (10 total — matches audit Section A's table).
# ─────────────────────────────────────────────────────────────────────────────


# (modal_name, tool_name_in_block, args, expected_action_substring)
TOOL_CASES = [
    ("exec",       "exec",            {"command": "ls -la /tmp"},          "exec"),
    ("browser",    "browser",         {"action": "navigate",
                                       "targetUrl": "https://example.com"}, "navigate"),
    ("search",     "web_search",      {"query": "duckdb upsert"},           "search"),
    ("cron",       "cron",            {"expr": "*/5 * * * *",
                                       "action": "schedule"},                "cron"),
    ("tts",        "tts",             {"text": "hello world",
                                       "voice": "alloy"},                    "tts"),
    ("memory",     "Read",            {"file_path": "/tmp/notes.md"},       "read"),
    ("session",    "sessions_spawn",  {"sessionId": "child-1",
                                       "name": "child"},                    "sessions_spawn"),
    # Unmapped families fall through to the literal name in _TOOL_MAP.get
    # (so the block must use the modal name itself) — covers the audit's
    # last three rows that the legacy parser also matches verbatim.
    ("storage",    "storage",         {"path": "/var/log/x"},               "storage"),
    ("network",    "network",         {"host": "1.1.1.1"},                  "network"),
    ("automation", "automation",      {"flow": "deploy"},                   "automation"),
]


@pytest.mark.parametrize("modal,tool_block_name,args,expected_action", TOOL_CASES,
                         ids=[c[0] for c in TOOL_CASES])
def test_tool_modal_serves_from_local_store(
    app, modal, tool_block_name, args, expected_action
):
    """For each of the 10 tool modals: ingest one matching tool_use block
    and confirm the endpoint returns ``_source: 'local_store'`` + event."""
    a, ls = app
    store = ls.get_store()
    _ingest_message_with_tool_block(
        store, tool_name=tool_block_name, args=args, ev_id=f"ev-{modal}"
    )

    r = a.test_client().get(f"/api/component/tool/{modal}")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"{modal} fast path bypassed — body={body}"
    )
    assert body["total"] >= 1, body
    assert body["events"], body
    # The first event is the most-recent (we sort desc by ts).
    evt = body["events"][0]
    assert evt["tool"] == tool_block_name
    assert evt["status"] == "ok"
    # Every tool branch sets `action`; check that something matching the
    # tool is present (loose match so per-tool detail formatting is free
    # to change without breaking us).
    assert expected_action in (evt.get("action") or "") + " " + (evt.get("tool") or "")


def test_fast_path_falls_through_when_no_tool_blocks(app):
    """A ``message`` row that only has plain text blocks (no toolCall)
    must NOT be served by the fast path — let the legacy parser try."""
    a, ls = app
    store = ls.get_store()
    store.ingest({
        "id": "ev-no-tool",
        "node_id": "agent+test", "agent_id": "main", "session_id": "sess-x",
        "event_type": "message", "ts": _now_iso(),
        "data": {
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "no tools here"}],
            },
        },
        "cost_usd": 0.0, "token_count": 0, "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    r = a.test_client().get("/api/component/tool/exec")
    body = r.get_json()
    assert body.get("_source") != "local_store"


def test_fast_path_handles_anthropic_tool_use_alias(app):
    """Older / Anthropic-direct transcripts use ``type='tool_use'`` and
    ``input`` instead of ``toolCall`` / ``arguments``. Must still match."""
    a, ls = app
    store = ls.get_store()
    store.ingest({
        "id": "ev-tool-use",
        "node_id": "agent+test", "agent_id": "main", "session_id": "sess-y",
        "event_type": "assistant", "ts": _now_iso(),
        "data": {
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "name": "exec",
                     "input": {"command": "uname -a"}},
                ],
            },
        },
        "cost_usd": 0.0, "token_count": 0, "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    r = a.test_client().get("/api/component/tool/exec")
    body = r.get_json()
    assert body.get("_source") == "local_store", body
    assert body["total"] >= 1
    assert body["events"][0]["tool"] == "exec"
    assert "uname" in (body["events"][0].get("detail") or "")
