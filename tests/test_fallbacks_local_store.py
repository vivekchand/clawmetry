"""E2E tests for the model-fallbacks DuckDB fast path (#1364 Tier-1).

Covers the full ``synthetic ingest → DuckDB → /api/fallbacks`` loop:

  1. ``LocalStore.query_model_fallbacks`` walks per-session assistant turns
     in chronological order, emits one transition each time
     ``model``/``provider`` differs from the previous turn, and ranks
     pairs by count.
  2. ``GET /api/fallbacks`` returns the DuckDB rows in the same shape the
     legacy JSONL walker produced when ``CLAWMETRY_LOCAL_STORE_READ`` is
     enabled, gracefully degrading to the legacy path on miss.

Driver pattern: reload ``clawmetry.local_store`` against a tmp DuckDB,
ingest synthetic ``message`` events, then reload ``routes.sessions`` so
its module-level ``_ls_call`` points at the fresh store.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import uuid

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Reload ``clawmetry.local_store`` against a fresh DuckDB file."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "fallbacks.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)

    store = ls.get_store()
    yield ls, store

    try:
        store.stop(flush=False)
    except Exception:
        pass


def _ingest_assistant_turn(
    store, *, session_id: str, ts: str, model: str, provider: str = "anthropic"
):
    """Insert a synthetic assistant message into the events table."""
    store.ingest({
        "id":         str(uuid.uuid4()),
        "node_id":    "test-node",
        "agent_id":   "test-agent",
        "session_id": session_id,
        "event_type": "message",
        "ts":         ts,
        "data": json.dumps({
            "message": {
                "role":     "assistant",
                "model":    model,
                "provider": provider,
                "content":  [],
            },
        }),
        "model": model,
    })


# ── 1. Schema / aggregation ────────────────────────────────────────────────


def test_query_model_fallbacks_detects_single_session_transition(fresh_store):
    ls, store = fresh_store
    sid = "sess-001"
    _ingest_assistant_turn(store, session_id=sid, ts="2026-05-15T10:00:00",
                           model="claude-opus-4")
    _ingest_assistant_turn(store, session_id=sid, ts="2026-05-15T10:01:00",
                           model="claude-opus-4")
    # Transition: opus → sonnet
    _ingest_assistant_turn(store, session_id=sid, ts="2026-05-15T10:02:00",
                           model="claude-sonnet-4")
    store._flush_now()

    out = store.query_model_fallbacks(session_limit=10, top=10)
    assert out["scanned"] == 1
    assert out["sessions_affected"] == 1
    assert len(out["top_transitions"]) == 1
    t = out["top_transitions"][0]
    assert t["from_model"] == "claude-opus-4"
    assert t["to_model"] == "claude-sonnet-4"
    assert t["from_provider"] == "anthropic"
    assert t["to_provider"] == "anthropic"
    assert t["count"] == 1
    assert t["sessions"] == [sid]


def test_query_model_fallbacks_aggregates_pair_across_sessions(fresh_store):
    """Same (from_model, to_model) pair across two sessions → count=2,
    sessions list contains both."""
    ls, store = fresh_store
    for sid in ("sess-a", "sess-b"):
        _ingest_assistant_turn(store, session_id=sid,
                               ts=f"2026-05-15T10:00:00",
                               model="claude-opus-4")
        _ingest_assistant_turn(store, session_id=sid,
                               ts=f"2026-05-15T10:01:00",
                               model="claude-sonnet-4")
    store._flush_now()

    out = store.query_model_fallbacks(session_limit=10, top=10)
    assert out["scanned"] == 2
    assert out["sessions_affected"] == 2
    assert len(out["top_transitions"]) == 1
    t = out["top_transitions"][0]
    assert t["count"] == 2
    assert sorted(t["sessions"]) == ["sess-a", "sess-b"]


def test_query_model_fallbacks_ranks_pairs_by_count(fresh_store):
    """Two distinct transition pairs ranked by frequency, top=N truncates."""
    ls, store = fresh_store
    # Pair A (opus→sonnet) seen 3 times, pair B (sonnet→haiku) seen 1 time.
    for i in range(3):
        sid = f"a-{i}"
        _ingest_assistant_turn(store, session_id=sid,
                               ts="2026-05-15T10:00:00", model="claude-opus-4")
        _ingest_assistant_turn(store, session_id=sid,
                               ts="2026-05-15T10:01:00", model="claude-sonnet-4")
    sid = "b-0"
    _ingest_assistant_turn(store, session_id=sid,
                           ts="2026-05-15T10:00:00", model="claude-sonnet-4")
    _ingest_assistant_turn(store, session_id=sid,
                           ts="2026-05-15T10:01:00", model="claude-haiku-4")
    store._flush_now()

    out = store.query_model_fallbacks(session_limit=10, top=10)
    assert out["sessions_affected"] == 4
    assert len(out["top_transitions"]) == 2
    # First entry is the higher-count pair.
    assert out["top_transitions"][0]["from_model"] == "claude-opus-4"
    assert out["top_transitions"][0]["count"] == 3
    assert out["top_transitions"][1]["from_model"] == "claude-sonnet-4"
    assert out["top_transitions"][1]["count"] == 1

    # top=1 truncates to the most frequent pair only.
    truncated = store.query_model_fallbacks(session_limit=10, top=1)
    assert len(truncated["top_transitions"]) == 1
    assert truncated["top_transitions"][0]["from_model"] == "claude-opus-4"


def test_query_model_fallbacks_treats_provider_as_part_of_pair(fresh_store):
    """Same model name but different provider → still a transition."""
    ls, store = fresh_store
    sid = "router-sess"
    _ingest_assistant_turn(store, session_id=sid,
                           ts="2026-05-15T10:00:00",
                           model="gpt-4o", provider="openai")
    _ingest_assistant_turn(store, session_id=sid,
                           ts="2026-05-15T10:01:00",
                           model="gpt-4o", provider="openrouter")
    store._flush_now()

    out = store.query_model_fallbacks(session_limit=10, top=10)
    assert len(out["top_transitions"]) == 1
    t = out["top_transitions"][0]
    assert t["from_provider"] == "openai"
    assert t["to_provider"] == "openrouter"
    assert t["count"] == 1


def test_query_model_fallbacks_no_transitions_when_steady_model(fresh_store):
    """Steady model across the whole session → no transitions, no entries
    in sessions_affected."""
    ls, store = fresh_store
    sid = "steady"
    for i in range(4):
        _ingest_assistant_turn(store, session_id=sid,
                               ts=f"2026-05-15T10:0{i}:00",
                               model="claude-sonnet-4")
    store._flush_now()

    out = store.query_model_fallbacks(session_limit=10, top=10)
    assert out["scanned"] == 1
    assert out["sessions_affected"] == 0
    assert out["top_transitions"] == []


def test_query_model_fallbacks_session_limit_caps_scan(fresh_store):
    """``session_limit`` applies to the most-recent N sessions only —
    older sessions outside the window contribute nothing."""
    ls, store = fresh_store
    # 3 sessions, only 2 most-recent should be scanned with limit=2.
    for idx, day in enumerate(("13", "14", "15")):
        sid = f"sess-{day}"
        _ingest_assistant_turn(store, session_id=sid,
                               ts=f"2026-05-{day}T10:00:00",
                               model="claude-opus-4")
        _ingest_assistant_turn(store, session_id=sid,
                               ts=f"2026-05-{day}T10:01:00",
                               model="claude-sonnet-4")
    store._flush_now()

    out = store.query_model_fallbacks(session_limit=2, top=10)
    assert out["scanned"] == 2
    # Only the two most-recent sessions (14, 15) contributed transitions.
    sessions_in_pair = out["top_transitions"][0]["sessions"]
    assert "sess-13" not in sessions_in_pair
    assert sorted(sessions_in_pair) == ["sess-14", "sess-15"]


# ── 2. Route fast path ─────────────────────────────────────────────────────


def test_api_fallbacks_returns_rows_from_local_store(fresh_store, monkeypatch):
    """``GET /api/fallbacks`` reads the DuckDB rows when the read flag is
    on, and the response shape mirrors the legacy walker."""
    ls, store = fresh_store
    sid = "api-sess-1"
    _ingest_assistant_turn(store, session_id=sid,
                           ts="2026-05-15T10:00:00", model="claude-opus-4")
    _ingest_assistant_turn(store, session_id=sid,
                           ts="2026-05-15T10:01:00", model="claude-sonnet-4")
    store._flush_now()

    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    # Reload routes.sessions so its module-level _ls_call sees the fresh store.
    sys.modules.pop("routes.sessions", None)
    import routes.sessions as rs
    importlib.reload(rs)

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(rs.bp_sessions)
    client = app.test_client()

    resp = client.get("/api/fallbacks?limit=20&top=5")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["scanned"] == 1
    assert body["sessions_affected"] == 1
    assert body["_source"] == "local_store"
    assert len(body["top_transitions"]) == 1
    t = body["top_transitions"][0]
    assert t["from_model"] == "claude-opus-4"
    assert t["to_model"] == "claude-sonnet-4"
    assert t["count"] == 1


# ── v3 real-shape regression (issue #1385) ────────────────────────────────


def _ingest_v3_assistant(
    store, *, session_id: str, ts: str, model: str, provider: str = "anthropic"
):
    """Insert a real OpenClaw v3 ``event_type='assistant'`` row.
    Same Anthropic-SDK message envelope as legacy, just under a
    different event_type name. Fixture distilled from
    ``/Users/vivek/.clawmetry/clawmetry.duckdb`` on 2026-05-15."""
    store.ingest({
        "id":         str(uuid.uuid4()),
        "node_id":    "test-node",
        "agent_id":   "test-agent",
        "session_id": session_id,
        "event_type": "assistant",
        "ts":         ts,
        "data": json.dumps({
            "type":    "assistant",
            "version": 3,
            "message": {
                "role":     "assistant",
                "model":    model,
                "provider": provider,
                "usage":    {"input_tokens": 100, "output_tokens": 50},
                "content":  [],
            },
        }),
        "model": model,
    })


def _ingest_v3_model_completed(
    store, *, session_id: str, ts: str, model: str, provider: str = "claude-cli"
):
    """Insert a real OpenClaw v3 ``event_type='model.completed'`` row.
    No ``data.message`` envelope; carries ``modelId``/``provider`` at
    the data root and ``promptCache.lastCallUsage`` for tokens."""
    store.ingest({
        "id":         str(uuid.uuid4()),
        "node_id":    "test-node",
        "agent_id":   "test-agent",
        "session_id": session_id,
        "event_type": "model.completed",
        "ts":         ts,
        "data": json.dumps({
            "type":     "model.completed",
            "modelId":  model,
            "provider": provider,
            "promptCache": {
                "lastCallUsage": {"input": 100, "output": 50, "total": 150},
            },
            "stopReason": "stop",
        }),
        "model": model,
    })


def test_query_model_fallbacks_v3_assistant_event_shape(fresh_store):
    """v3 real-shape regression (#1385): real OpenClaw v3 emits
    ``event_type='assistant'`` (not ``'message'``). The previous
    predicate filtered ``= 'message'`` and silently returned
    ``scanned=0`` on every live install. Widened predicate must
    detect the v3 transition."""
    ls, store = fresh_store
    sid = "v3-sess-1"
    _ingest_v3_assistant(store, session_id=sid, ts="2026-05-15T10:00:00",
                         model="claude-opus-4-7")
    _ingest_v3_assistant(store, session_id=sid, ts="2026-05-15T10:01:00",
                         model="claude-opus-4-7")
    _ingest_v3_assistant(store, session_id=sid, ts="2026-05-15T10:02:00",
                         model="claude-sonnet-4-7")
    store._flush_now()

    out = store.query_model_fallbacks(session_limit=10, top=10)
    assert out["scanned"] == 1, f"v3 assistant rows ignored: {out}"
    assert out["sessions_affected"] == 1
    assert len(out["top_transitions"]) == 1
    t = out["top_transitions"][0]
    assert t["from_model"] == "claude-opus-4-7"
    assert t["to_model"] == "claude-sonnet-4-7"
    assert t["count"] == 1


def test_query_model_fallbacks_v3_model_completed_shape(fresh_store):
    """v3 real-shape regression (#1385): ``model.completed`` events
    don't carry a ``data.message`` envelope — model lives at
    ``data.modelId`` / ``data.provider``. Widened walker must read
    those fields, otherwise sessions where ONLY model.completed
    rows exist (no parallel ``assistant`` event) report no model
    information at all."""
    ls, store = fresh_store
    sid = "v3-mcp-sess"
    _ingest_v3_model_completed(store, session_id=sid,
                               ts="2026-05-15T10:00:00",
                               model="claude-opus-4-7",
                               provider="claude-cli")
    _ingest_v3_model_completed(store, session_id=sid,
                               ts="2026-05-15T10:01:00",
                               model="claude-haiku-4-7",
                               provider="claude-cli")
    store._flush_now()

    out = store.query_model_fallbacks(session_limit=10, top=10)
    assert out["scanned"] == 1
    assert out["sessions_affected"] == 1
    assert len(out["top_transitions"]) == 1
    t = out["top_transitions"][0]
    assert t["from_model"] == "claude-opus-4-7"
    assert t["to_model"] == "claude-haiku-4-7"
    assert t["from_provider"] == "claude-cli"


def test_query_model_fallbacks_excludes_subagent_assistant(fresh_store):
    """v3 real-shape regression (#1385): parent agent calling Task
    spawns a ``subagent:assistant`` row with a different model
    (often haiku from an opus parent). That's intentional — NOT a
    fallback. The widened predicate must exclude
    ``subagent:assistant`` so we don't fire false positives."""
    ls, store = fresh_store
    sid = "v3-mixed"
    _ingest_v3_assistant(store, session_id=sid, ts="2026-05-15T10:00:00",
                         model="claude-opus-4-7")
    # Subagent emission with a different model — must be IGNORED.
    store.ingest({
        "id":         str(uuid.uuid4()),
        "node_id":    "test-node",
        "agent_id":   "test-agent",
        "session_id": sid,
        "event_type": "subagent:assistant",
        "ts":         "2026-05-15T10:00:30",
        "data": json.dumps({
            "type":    "assistant",
            "version": 3,
            "message": {
                "role":     "assistant",
                "model":    "claude-haiku-4-5",
                "provider": "anthropic",
                "usage":    {"input_tokens": 100},
                "content":  [],
            },
        }),
        "model": "claude-haiku-4-5",
    })
    _ingest_v3_assistant(store, session_id=sid, ts="2026-05-15T10:01:00",
                         model="claude-opus-4-7")
    store._flush_now()

    out = store.query_model_fallbacks(session_limit=10, top=10)
    # Only opus→opus seen at the parent level; no transition.
    assert out["sessions_affected"] == 0, (
        f"subagent:assistant leaked into transitions: {out}"
    )
    assert out["top_transitions"] == []


def test_api_fallbacks_defers_to_legacy_when_store_empty(
    fresh_store, monkeypatch, tmp_path
):
    """Empty DuckDB → fast path returns None → legacy walker runs against
    a directory that doesn't exist → empty payload (no _source key).

    The "no _source" assertion is the contract: it proves we exercised
    the fallback rather than short-circuiting in the fast path."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    sys.modules.pop("routes.sessions", None)
    import routes.sessions as rs
    importlib.reload(rs)

    # Point dashboard.SESSIONS_DIR at an empty tmp dir so the legacy
    # walker has no files to scan.
    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(tmp_path / "no-sessions"))

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(rs.bp_sessions)
    client = app.test_client()

    resp = client.get("/api/fallbacks")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["scanned"] == 0
    assert body["sessions_affected"] == 0
    assert body["top_transitions"] == []
    # Fast path returned None, so the response was assembled by the legacy
    # walker — no _source marker.
    assert "_source" not in body
