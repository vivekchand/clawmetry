"""Tests for the /api/flow/runs historical flow-runs endpoint (issue #611).

A "flow run" = one session_id's worth of events from the DuckDB ``events``
table. The endpoint aggregates per-session: duration, distinct models,
tool-call count, total cost, status, and a left-joined channel.

These tests seed events for three sessions across two channels and two
models, then assert the grouping + aggregation invariants. The endpoint
must never crash on missing data and must order most-recent-first.
"""

from __future__ import annotations

import importlib
import time

import pytest
from flask import Flask


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.infra as infra_mod
    importlib.reload(infra_mod)

    a = Flask(__name__)
    a.register_blueprint(infra_mod.bp_logs)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed_three_sessions(store):
    """Seed events across 3 sessions / 2 channels / 2 models.

    Session A (telegram, claude-opus-4-7):
      - 2 messages, 1 tool_call, cost $0.30 total, ~10 min duration.
    Session B (slack, gpt-4o):
      - 1 message, 2 tool_calls, cost $0.20 total, ~5 min duration.
    Session C (telegram, claude-opus-4-7 + gpt-4o):
      - 1 error event → status=failed, cost $0.05, ~2 min duration.
    """
    # Session A — telegram, two assistant turns + one tool_call
    store.ingest_channel({"session_id": "sess-A", "channel": "telegram"})
    store.ingest({
        "id": "A-1", "node_id": "n1", "agent_id": "main",
        "session_id": "sess-A", "event_type": "message",
        "ts": "2026-05-13T10:00:00Z",
        "data": {"role": "user"},
        "cost_usd": 0.10, "token_count": 100, "model": "claude-opus-4-7",
    })
    store.ingest({
        "id": "A-2", "node_id": "n1", "agent_id": "main",
        "session_id": "sess-A", "event_type": "tool_call",
        "ts": "2026-05-13T10:05:00Z",
        "data": {"tool": "Bash"},
        "cost_usd": 0.10, "token_count": 50, "model": "claude-opus-4-7",
    })
    store.ingest({
        "id": "A-3", "node_id": "n1", "agent_id": "main",
        "session_id": "sess-A", "event_type": "message",
        "ts": "2026-05-13T10:10:00Z",
        "data": {"role": "assistant"},
        "cost_usd": 0.10, "token_count": 80, "model": "claude-opus-4-7",
    })

    # Session B — slack, two tool_calls, different model
    store.ingest_channel({"session_id": "sess-B", "channel": "slack"})
    store.ingest({
        "id": "B-1", "node_id": "n1", "agent_id": "main",
        "session_id": "sess-B", "event_type": "message",
        "ts": "2026-05-13T11:00:00Z",
        "data": {"role": "user"},
        "cost_usd": 0.05, "token_count": 50, "model": "gpt-4o",
    })
    store.ingest({
        "id": "B-2", "node_id": "n1", "agent_id": "main",
        "session_id": "sess-B", "event_type": "tool_call",
        "ts": "2026-05-13T11:02:00Z",
        "data": {"tool": "Bash"},
        "cost_usd": 0.08, "token_count": 40, "model": "gpt-4o",
    })
    store.ingest({
        "id": "B-3", "node_id": "n1", "agent_id": "main",
        "session_id": "sess-B", "event_type": "tool_call",
        "ts": "2026-05-13T11:05:00Z",
        "data": {"tool": "Read"},
        "cost_usd": 0.07, "token_count": 30, "model": "gpt-4o",
    })

    # Session C — telegram, FAILED (has an error event), two models
    store.ingest_channel({"session_id": "sess-C", "channel": "telegram"})
    store.ingest({
        "id": "C-1", "node_id": "n1", "agent_id": "main",
        "session_id": "sess-C", "event_type": "message",
        "ts": "2026-05-13T12:00:00Z",
        "data": {"role": "user"},
        "cost_usd": 0.03, "token_count": 30, "model": "claude-opus-4-7",
    })
    store.ingest({
        "id": "C-2", "node_id": "n1", "agent_id": "main",
        "session_id": "sess-C", "event_type": "tool_error",
        "ts": "2026-05-13T12:02:00Z",
        "data": {"error": "boom"},
        "cost_usd": 0.02, "token_count": 10, "model": "gpt-4o",
    })

    _wait_flush(store)


def test_flow_runs_returns_one_row_per_session(app):
    a, ls = app
    _seed_three_sessions(ls.get_store())
    r = a.test_client().get("/api/flow/runs?limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body["_source"] == "local_store"
    assert body["count"] == 3
    sids = {row["session_id"] for row in body["runs"]}
    assert sids == {"sess-A", "sess-B", "sess-C"}


def test_flow_runs_aggregates_cost_tools_models(app):
    a, ls = app
    _seed_three_sessions(ls.get_store())
    r = a.test_client().get("/api/flow/runs?limit=10")
    runs = {row["session_id"]: row for row in r.get_json()["runs"]}

    a_row = runs["sess-A"]
    # 3 events, 1 tool_call, 1 distinct model, cost $0.30 (±float dust).
    assert a_row["event_count"] == 3
    assert a_row["tools_called"] == 1
    assert a_row["models_invoked"] == 1
    assert a_row["models"] == ["claude-opus-4-7"]
    assert abs(a_row["total_cost"] - 0.30) < 1e-6
    assert a_row["channel"] == "telegram"
    assert a_row["channels_touched"] == 1
    assert a_row["status"] == "completed"
    # 10 min duration (10:00 → 10:10).
    assert abs(a_row["duration_seconds"] - 600.0) < 1.0

    b_row = runs["sess-B"]
    assert b_row["event_count"] == 3
    assert b_row["tools_called"] == 2
    assert b_row["models_invoked"] == 1
    assert b_row["models"] == ["gpt-4o"]
    assert abs(b_row["total_cost"] - 0.20) < 1e-6
    assert b_row["channel"] == "slack"
    assert b_row["status"] == "completed"
    # 5 min duration (11:00 → 11:05).
    assert abs(b_row["duration_seconds"] - 300.0) < 1.0


def test_flow_runs_marks_error_sessions_failed(app):
    a, ls = app
    _seed_three_sessions(ls.get_store())
    r = a.test_client().get("/api/flow/runs?limit=10")
    runs = {row["session_id"]: row for row in r.get_json()["runs"]}
    c_row = runs["sess-C"]
    # Has a `tool_error` event → status flips to failed.
    assert c_row["status"] == "failed"
    # Two distinct models seen in sess-C.
    assert c_row["models_invoked"] == 2
    assert set(c_row["models"]) == {"claude-opus-4-7", "gpt-4o"}


def test_flow_runs_ordered_most_recent_first(app):
    a, ls = app
    _seed_three_sessions(ls.get_store())
    r = a.test_client().get("/api/flow/runs?limit=10")
    ids = [row["session_id"] for row in r.get_json()["runs"]]
    # C (12:02 last) before B (11:05) before A (10:10).
    assert ids == ["sess-C", "sess-B", "sess-A"]


def test_flow_runs_limit_param_caps_rows(app):
    a, ls = app
    _seed_three_sessions(ls.get_store())
    r = a.test_client().get("/api/flow/runs?limit=2")
    body = r.get_json()
    assert body["count"] == 2
    # Most-recent-first slicing — A (oldest) is the one dropped.
    sids = [row["session_id"] for row in body["runs"]]
    assert "sess-A" not in sids
    assert "sess-C" in sids


def test_flow_runs_empty_store_returns_empty_list(app):
    a, _ls = app
    r = a.test_client().get("/api/flow/runs")
    assert r.status_code == 200
    body = r.get_json()
    assert body["runs"] == []
    assert body["count"] == 0
    assert body["_source"] == "empty"
