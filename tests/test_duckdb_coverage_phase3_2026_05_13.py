"""Tests for the DuckDB coverage Phase-3 batch landed 2026-05-13.

Each test verifies the new ``_try_local_store_*`` fast path returns
``_source: "local_store"`` when DuckDB has the relevant rows. We only
assert the tag + a couple of structural keys — the legacy paths are
covered by their own existing tests.

Surfaces under test (5 of the Bypass-Medium follow-up to issue #1088):
  - /api/compactions                    routes/sessions.py
  - /api/session-tools                  routes/sessions.py
  - /api/cost-split                     routes/sessions.py
  - /api/session-model-journey/<id>     routes/sessions.py
  - /api/agent-intentions               routes/crons.py
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


def _wait_flush(store, t: float = 2.0) -> None:
    """Wait for the ring buffer to drain so SELECTs see the rows."""
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Reload local_store against a fresh DuckDB file with the read flag on."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    yield ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _client(blueprint_module_name: str, blueprint_attr: str):
    """Reload `routes/<module>` so its late-bound store handle picks up the
    freshly-reloaded local_store, then return a Flask test client."""
    import importlib as _il
    mod = _il.import_module(blueprint_module_name)
    _il.reload(mod)
    a = Flask(__name__)
    a.register_blueprint(getattr(mod, blueprint_attr))
    return a.test_client()


# ── /api/compactions ───────────────────────────────────────────────────────


def test_compactions_fast_path(fresh_store):
    store = fresh_store.get_store()
    store.ingest({
        "id": "ev-cmp-1", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-cmp", "event_type": "compaction",
        "ts": "2026-05-12T12:00:00Z",
        "data": {
            "type": "compaction",
            "timestamp": "2026-05-12T12:00:00Z",
            "summary": "Compacted earlier turns into a 2K summary.",
            "tokensBefore": 9000,
            "firstKeptEntryId": "ent-7",
            "fromHook": False,
        },
    })
    _wait_flush(store)
    c = _client("routes.sessions", "bp_sessions")
    r = c.get("/api/compactions")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["total_compactions"] == 1
    assert body["total_tokens_compacted"] == 9000
    only = body["compactions"][0]
    assert only["session_id"] == "sess-cmp"
    assert only["tokens_before"] == 9000
    assert "Compacted earlier" in only["summary"]


# ── /api/session-tools ─────────────────────────────────────────────────────


def test_session_tools_fast_path(fresh_store):
    store = fresh_store.get_store()
    # Assistant turn with one toolCall, then a paired toolResult.
    store.ingest({
        "id": "ev-st-call", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-st", "event_type": "message",
        "ts": "2026-05-12T12:00:00Z",
        "data": {
            "type": "message",
            "timestamp": "2026-05-12T12:00:00Z",
            "message": {
                "role": "assistant",
                "model": "claude-opus-4-7",
                "content": [{
                    "type": "toolCall",
                    "id": "tc-1",
                    "name": "Read",
                    "arguments": {"path": "/tmp/x"},
                }],
                "usage": {"cost": {"total": 0.001}},
            },
        },
    })
    store.ingest({
        "id": "ev-st-res", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-st", "event_type": "message",
        "ts": "2026-05-12T12:00:01Z",
        "data": {
            "type": "message",
            "timestamp": "2026-05-12T12:00:01Z",
            "message": {
                "role": "toolResult",
                "toolCallId": "tc-1",
                "details": {"contents": "hello world"},
                "isError": False,
            },
        },
    })
    _wait_flush(store)
    c = _client("routes.sessions", "bp_sessions")
    r = c.get("/api/session-tools?session_id=sess-st")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["session_id"] == "sess-st"
    assert body["stats"]["total_calls"] == 1
    assert body["stats"]["paired_calls"] == 1
    assert body["tools"][0]["tool_name"] == "Read"
    assert body["tools"][0]["paired"] is True
    assert any(bt["tool_name"] == "Read" for bt in body["by_tool"])


# ── /api/cost-split ────────────────────────────────────────────────────────


def test_cost_split_fast_path(fresh_store):
    store = fresh_store.get_store()
    store.ingest({
        "id": "ev-csp-1", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-csp", "event_type": "message",
        "ts": "2026-05-12T12:00:00Z",
        "model": "claude-opus-4-7",
        "data": {
            "type": "message",
            "message": {
                "role": "assistant",
                "model": "claude-opus-4-7",
                "content": [{"type": "text", "text": "ok"}],
                "usage": {
                    "input": 1000, "output": 500,
                    "cacheRead": 2000, "cacheWrite": 100,
                    "totalTokens": 3600,
                    "cost": {"input": 0.01, "output": 0.02,
                             "cacheRead": 0.001, "cacheWrite": 0.0005,
                             "total": 0.0315},
                },
            },
        },
    })
    _wait_flush(store)
    c = _client("routes.sessions", "bp_sessions")
    r = c.get("/api/cost-split")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert len(body["sessions"]) == 1
    s = body["sessions"][0]
    assert s["session_id"] == "sess-csp"
    assert s["primary_model"] == "claude-opus-4-7"
    assert s["input_tokens"] == 1000
    assert s["cache_read_tokens"] == 2000
    assert s["total_cost_usd"] == pytest.approx(0.0315, abs=1e-6)
    assert body["totals"]["session_count"] == 1
    assert body["totals"]["cache_read_tokens"] == 2000


# ── /api/session-model-journey/<id> ────────────────────────────────────────


def test_session_model_journey_fast_path(fresh_store):
    store = fresh_store.get_store()
    store.ingest({
        "id": "ev-mj-mc-1", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-mj", "event_type": "model_change",
        "ts": "2026-05-12T12:00:00Z",
        "data": {"modelId": "claude-sonnet-4-5", "provider": "anthropic"},
    })
    store.ingest({
        "id": "ev-mj-msg-1", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-mj", "event_type": "message",
        "ts": "2026-05-12T12:00:30Z",
        "model": "claude-sonnet-4-5",
        "data": {
            "type": "message",
            "message": {
                "role": "assistant", "model": "claude-sonnet-4-5",
                "content": [{"type": "text", "text": "x"}],
                "usage": {"totalTokens": 250, "cost": {"total": 0.005}},
            },
        },
    })
    store.ingest({
        "id": "ev-mj-mc-2", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-mj", "event_type": "model_change",
        "ts": "2026-05-12T12:01:00Z",
        "data": {"modelId": "claude-opus-4-7", "provider": "anthropic"},
    })
    _wait_flush(store)
    c = _client("routes.sessions", "bp_sessions")
    r = c.get("/api/session-model-journey/sess-mj")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["session_id"] == "sess-mj"
    assert body["stats"]["total_segments"] >= 1
    assert body["stats"]["total_models_used"] >= 1
    # First segment is the sonnet stretch with the assistant message tokens.
    seg0 = body["segments"][0]
    assert seg0["modelId"] == "claude-sonnet-4-5"
    assert seg0["tokens"] == 250
    assert seg0["cost_usd"] == pytest.approx(0.005, abs=1e-6)


# ── /api/agent-intentions ──────────────────────────────────────────────────


def test_agent_intentions_fast_path(fresh_store):
    store = fresh_store.get_store()
    # Schedule firing 1 hour from now so it falls inside the 7-day window.
    next_run_ms = int(time.time() * 1000) + 3600 * 1000
    next_run_iso = datetime.fromtimestamp(next_run_ms / 1000, tz=timezone.utc).isoformat()
    store.ingest_cron({
        "cron_id":     "cron-ai-1",
        "agent_type":  "openclaw",
        "name":        "Hourly heartbeat",
        "schedule":    {"kind": "every", "everyMs": 3600 * 1000},
        "enabled":     True,
        "last_run_at": "2026-05-12T11:00:00Z",
        "last_status": "ok",
        "next_run_at": next_run_iso,
    })
    _wait_flush(store)
    c = _client("routes.crons", "bp_crons")
    r = c.get("/api/agent-intentions?days=7")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["window"]["days"] == 7
    # At least the immediate next firing should appear in the timeline.
    assert body["stats"]["total_intentions"] >= 1
    first = body["intentions"][0]
    assert first["jobId"] == "cron-ai-1"
    assert first["name"] == "Hourly heartbeat"
    assert first["scheduleKind"] in ("every", "interval")
