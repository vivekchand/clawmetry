"""Tests for the DuckDB coverage Phase-2 batch landed 2026-05-13.

Each test verifies the new ``_try_local_store_*`` fast path returns
``_source: "local_store"`` when DuckDB has the relevant rows. We only
assert the tag + a couple of structural keys — the legacy paths are
covered by their own existing tests.

Surfaces under test (6 of the 8 from issue #1088):
  - /api/transcript-events/<id>            routes/sessions.py
  - /api/sessions/<id>/export              routes/sessions.py
  - /api/cron-run-log                      routes/crons.py
  - /api/agents/<name>/sessions            routes/agents.py
  - /api/timeline                          routes/overview.py
  - /api/sessions/clusters                 routes/usage.py

/api/version-impact is intentionally excluded — its before/after stats
sit on a separate SQLite ``version_events`` table that DuckDB does not
mirror (Bypass-Medium per issue #1088 follow-up).

/api/clusters was removed in issue #1716 (Fleet Sonar deletion) — its
test (``test_clusters_fast_path``) went with it. The Trace Clusters
surface on the Usage tab is unrelated and still covered above by
``test_sessions_clusters_fast_path``.
"""

from __future__ import annotations

import importlib
import json
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


# ── /api/transcript-events/<id> ────────────────────────────────────────────


def test_transcript_events_fast_path(fresh_store):
    store = fresh_store.get_store()
    store.ingest({
        "id": "ev-te-1", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-te", "event_type": "message",
        "ts": "2026-05-12T12:00:00Z",
        "data": {
            "type": "message",
            "timestamp": "2026-05-12T12:00:00Z",
            "message": {"role": "user", "content": [{"type": "text", "text": "hi there"}]},
        },
    })
    _wait_flush(store)
    c = _client("routes.sessions", "bp_sessions")
    r = c.get("/api/transcript-events/sess-te")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["messageCount"] == 1
    assert any(e.get("type") == "user" and "hi there" in e.get("text", "")
               for e in body["events"])


# ── /api/sessions/<id>/export ──────────────────────────────────────────────


def test_session_export_fast_path(fresh_store):
    store = fresh_store.get_store()
    store.ingest({
        "id": "ev-ex-1", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-ex", "event_type": "message",
        "ts": "2026-05-12T12:00:00Z",
        "data": {
            "type": "message",
            "timestamp": "2026-05-12T12:00:00Z",
            "message": {
                "role": "assistant",
                "model": "claude-opus-4-7",
                "content": [{"type": "text", "text": "answer"}],
                "usage": {
                    "input": 10, "output": 20,
                    "cost": {"total": 0.001},
                },
            },
        },
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)
    c = _client("routes.sessions", "bp_sessions")
    r = c.get("/api/sessions/sess-ex/export?format=json")
    assert r.status_code == 200
    body = json.loads(r.data)
    assert body.get("_source") == "local_store"
    assert body["session_id"] == "sess-ex"
    assert body["metadata"]["message_count"] == 1
    assert body["cost_data"]["input_tokens"] == 10
    assert body["cost_data"]["total_cost_usd"] == pytest.approx(0.001)


# ── /api/cron-run-log ──────────────────────────────────────────────────────


def test_cron_run_log_fast_path(fresh_store):
    store = fresh_store.get_store()
    for i in range(2):
        store.ingest({
            "id": f"ev-cr-{i}", "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-cron", "event_type": "message",
            "ts": f"2026-05-12T12:0{i}:00Z",
            "data": {
                "type": "message",
                "timestamp": f"2026-05-12T12:0{i}:00Z",
                "message": {"role": "user", "content": "step"},
            },
        })
    _wait_flush(store)
    c = _client("routes.crons", "bp_crons")
    r = c.get("/api/cron-run-log?session_id=sess-cron")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["sessionId"] == "sess-cron"
    assert len(body["events"]) == 2


# ── /api/agents/<name>/sessions ────────────────────────────────────────────


def test_agent_sessions_fast_path(fresh_store):
    store = fresh_store.get_store()
    store.ingest_session({
        "agent_type": "openclaw",
        "session_id": "sess-ag-1",
        "agent_id": "main",
        "title": "demo run",
        "started_at": "2026-05-12T11:00:00Z",
        "last_active_at": "2026-05-12T12:00:00Z",
        "status": "active",
        "total_tokens": 1234,
        "cost_usd": 0.42,
        "message_count": 7,
        "metadata": {"model": "claude-opus-4-7", "source": "test"},
    })
    _wait_flush(store)
    c = _client("routes.agents", "bp_agents")
    r = c.get("/api/agents/openclaw/sessions?limit=10")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert len(body["sessions"]) == 1
    s = body["sessions"][0]
    assert s["id"] == "sess-ag-1"
    assert s["agent"] == "openclaw"
    assert s["totalTokens"] == 1234
    assert s["model"] == "claude-opus-4-7"


# ── /api/timeline ──────────────────────────────────────────────────────────


def test_timeline_fast_path(fresh_store):
    store = fresh_store.get_store()
    today = datetime.now()
    iso = today.replace(hour=15, minute=0, second=0, microsecond=0).isoformat()
    for i in range(3):
        store.ingest({
            "id": f"ev-tl-{i}", "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-tl", "event_type": "message",
            "ts": iso,
        })
    _wait_flush(store)
    c = _client("routes.overview", "bp_overview")
    r = c.get("/api/timeline")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert any(d.get("date") == today.strftime("%Y-%m-%d") and d.get("events", 0) >= 3
               for d in body["days"])


# ── /api/sessions/clusters ─────────────────────────────────────────────────


def test_sessions_clusters_fast_path(fresh_store):
    store = fresh_store.get_store()
    today_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    # One assistant turn with usage so the session has cost > 0 and one tool
    # call to drive the cluster_key.
    store.ingest({
        "id": "ev-cl-1", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-cl", "event_type": "message",
        "ts": today_iso,
        "model": "claude-opus-4-7",
        "cost_usd": 0.05, "token_count": 1500,
        "data": {
            "type": "message",
            "message": {
                "role": "assistant",
                "model": "claude-opus-4-7",
                "content": [
                    {"type": "text", "text": "running"},
                    {"type": "toolCall", "name": "exec", "arguments": {"command": "ls"}},
                ],
                "usage": {"input": 1000, "output": 500, "cost": {"total": 0.05}},
            },
        },
    })
    _wait_flush(store)
    c = _client("routes.usage", "bp_usage")
    r = c.get("/api/sessions/clusters?days=30")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["total_sessions"] == 1
    assert len(body["clusters"]) == 1
    cl = body["clusters"][0]
    assert cl["session_count"] == 1
    assert "sess-cl" in cl["session_ids"]


# /api/clusters test removed 2026-05-19 (issue #1716, Fleet Sonar deletion).
