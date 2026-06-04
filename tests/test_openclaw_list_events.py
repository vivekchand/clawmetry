"""Tests for OpenClawAdapter.list_events() — no longer a stub.

The unified Event-yielding API for the OpenClaw Free runtime used to
return ``[]`` with a "deferred to follow-up PR" comment. This test
pins the new DuckDB-backed implementation so the unified per-agent
session view + any caller of ``adapter.list_events(session_id)`` gets
real events back.
"""
from __future__ import annotations

import importlib
import time
import uuid

import pytest


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.local_store as _ls
    importlib.reload(_ls)
    s = _ls.LocalStore()
    s.start()
    monkeypatch.setattr(_ls, "get_store", lambda *a, **kw: s)
    yield s
    s.stop(flush=True)


def _seed(store, session_id, event_type, model=None, tokens=0):
    store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "openclaw",
        "session_id": session_id,
        "event_type": event_type,
        "ts": time.time(),
        "model": model or "",
        "data": {"x": 1},
        "token_count": tokens,
    })


def _wait_flush(s, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if s.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def test_list_events_returns_unified_shape(isolated_store):
    _seed(isolated_store, "sess-A", "session.started")
    _seed(isolated_store, "sess-A", "model.completed", model="claude-3.5", tokens=42)
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-A")
    assert len(events) == 2
    types = [e.type for e in events]
    assert "session.started" in types
    assert "model.completed" in types
    assert all(e.agent == "openclaw" for e in events)
    assert all(e.session_id == "sess-A" for e in events)
    # Model + tokens flow through into the unified shape.
    model_evt = next(e for e in events if e.type == "model.completed")
    assert model_evt.tokens == 42
    assert model_evt.extra.get("model") == "claude-3.5"


def test_list_events_filters_by_session_id(isolated_store):
    _seed(isolated_store, "sess-A", "model.completed")
    _seed(isolated_store, "sess-B", "model.completed")
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-A")
    assert len(events) == 1
    assert events[0].session_id == "sess-A"


def test_list_events_filters_by_agent_type(isolated_store):
    """A nemoclaw-tagged event in the same store must NOT leak into
    OpenClaw's list_events; agent_type is the discriminator."""
    _seed(isolated_store, "sess-C", "model.completed")
    isolated_store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "nemoclaw",
        "session_id": "sess-C",
        "event_type": "model.completed",
        "ts": time.time(),
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-C")
    assert len(events) == 1  # only the openclaw one


def test_list_events_respects_limit(isolated_store):
    for _ in range(5):
        _seed(isolated_store, "sess-D", "tool.call")
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-D", limit=3)
    assert len(events) == 3


def test_list_events_unknown_session_returns_empty(isolated_store):
    from clawmetry.adapters.openclaw import OpenClawAdapter
    assert OpenClawAdapter().list_events("no-such-session") == []


def test_list_events_surfaces_cache_token_split(isolated_store):
    """Per-type token fields from the data blob land in event.extra (#2603).

    Seed an assistant event whose data contains message.usage with input,
    output, and cache_read token counts; verify list_events() populates
    the corresponding extra keys so per-turn cache efficiency is measurable.
    """
    import uuid, time as _t
    isolated_store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "openclaw",
        "session_id": "sess-E",
        "event_type": "model.completed",
        "ts": _t.time(),
        "model": "claude-opus-4-7",
        "token_count": 150,
        "data": {
            "type": "assistant",
            "message": {
                "model": "claude-opus-4-7",
                "usage": {
                    "input_tokens": 30,
                    "output_tokens": 20,
                    "cache_read_input_tokens": 80,
                    "cache_creation_input_tokens": 10,
                },
            },
        },
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-E")
    assert len(events) == 1
    ex = events[0].extra
    assert ex.get("inputTokens") == 30
    assert ex.get("outputTokens") == 20
    assert ex.get("cacheReadTokens") == 80
    assert ex.get("cacheWriteTokens") == 10
