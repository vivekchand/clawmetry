"""Tests for the /api/transcript/<sid> local-store fast path.

Closes the explicit MOAT gap surfaced in the real-OpenClaw E2E pipeline:
the transcript endpoint used to read JSONL directly, bypassing DuckDB.

Pattern matches test_sessions_local_fastpath.py:
- CLAWMETRY_LOCAL_STORE_READ=1 + populated events → returns from DuckDB
- Flag unset → falls through to legacy JSONL path
- No events for the session → falls through (so the JSONL path can still serve)
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
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)

    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ev(event_id, sid, role, content, ts, **extra):
    obj = {"role": role, "content": content, "timestamp": ts, **extra}
    return {
        "id": event_id,
        "node_id": "node-test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": "message" if role in ("user", "assistant") else role,
        "ts": ts,
        "data": json.dumps(obj),
    }


def _drain(store):
    """Force the ring buffer to flush so the events table is populated."""
    store._flush_now()
    # Allow the background flusher one tick.
    for _ in range(10):
        if not store._ring:
            break
        time.sleep(0.05)


def test_transcript_fast_path_returns_local_rows(app):
    a, ls = app
    store = ls.get_store()
    sid = "sess-transcript-A"
    store.ingest(_ev("e1", sid, "user", "hello", "2026-05-12T10:00:00Z"))
    store.ingest(_ev("e2", sid, "assistant", "hi there",
                     "2026-05-12T10:00:05Z", model="claude-opus-4-7",
                     usage={"input_tokens": 12, "output_tokens": 5}))
    store.ingest(_ev("e3", sid, "user", "what is 2+2?", "2026-05-12T10:00:10Z"))
    store.ingest(_ev("e4", sid, "assistant", "4",
                     "2026-05-12T10:00:15Z",
                     usage={"input_tokens": 8, "output_tokens": 1}))
    _drain(store)

    c = a.test_client()
    r = c.get(f"/api/transcript/{sid}")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["messageCount"] == 4
    assert body["model"] == "claude-opus-4-7"
    assert body["totalTokens"] == 26
    # Ascending timeline preserved.
    roles = [m["role"] for m in body["messages"]]
    assert roles == ["user", "assistant", "user", "assistant"]
    contents = [m["content"] for m in body["messages"]]
    assert contents == ["hello", "hi there", "what is 2+2?", "4"]
    # Duration: 15s between first and last.
    assert body["duration"] == "15s"


def test_transcript_fast_path_emits_tool_call_messages(app):
    a, ls = app
    store = ls.get_store()
    sid = "sess-transcript-tool"
    store.ingest(_ev("t1", sid, "assistant", "let me check",
                     "2026-05-12T10:00:00Z",
                     tool_calls=[{"name": "Bash", "input": {"cmd": "ls"}}]))
    _drain(store)

    c = a.test_client()
    r = c.get(f"/api/transcript/{sid}")
    body = r.get_json()
    assert body.get("_source") == "local_store"
    # tool message inserted before the assistant message
    tool_msgs = [m for m in body["messages"] if m["role"] == "tool"]
    assert len(tool_msgs) == 1
    assert "[Tool Call: Bash]" in tool_msgs[0]["content"]
    assert "ls" in tool_msgs[0]["content"]


def test_transcript_fast_path_falls_back_when_session_empty(app, tmp_path, monkeypatch):
    """Unknown session → fast path returns None → legacy path runs and 404s
    because no JSONL exists."""
    a, _ = app
    # Point dashboard.SESSIONS_DIR at an empty directory so the legacy
    # path's existence check fails and we get a 404 (not a crash).
    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(tmp_path / "no-such-dir"), raising=False)
    c = a.test_client()
    r = c.get("/api/transcript/sess-doesnt-exist")
    assert r.status_code == 404


def test_transcript_fast_path_off_when_flag_unset(app, monkeypatch):
    a, ls = app
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_READ", raising=False)
    store = ls.get_store()
    sid = "sess-off"
    store.ingest(_ev("o1", sid, "user", "should not be served from duckdb",
                     "2026-05-12T11:00:00Z"))
    _drain(store)

    # Without the flag, the route falls through to the JSONL path which
    # 404s because no file exists. Verify the response is NOT tagged with
    # _source=local_store.
    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", "/tmp/no-such-dir-here", raising=False)
    c = a.test_client()
    r = c.get(f"/api/transcript/{sid}")
    assert r.status_code == 404
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"
