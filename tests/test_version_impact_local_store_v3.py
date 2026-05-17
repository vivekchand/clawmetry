"""Regression guard for /api/version-impact DuckDB fast path (Tier-1 #1565).

``routes/meta.py:_try_local_store_version_impact`` derives the
version timeline + per-version aggregates from ``session.started``
events in the local DuckDB store. Before the fast path, every request
re-walked every session JSONL on disk (`_compute_session_stats_in_range`
in ``dashboard.py``) AND read the per-process SQLite ``version_events``
table — both of which scale poorly once a user has hundreds of sessions
or has bounced between several OpenClaw releases.

This file seeds DuckDB with the SAME daemon-normalised event shapes the
OSS sync daemon writes for real OpenClaw v3 sessions (see
``clawmetry/sync.py::_parse_v3_event`` + reference_openclaw_v3_event_types.md)
and asserts:

1. An empty local store falls through to the legacy SQLite path.
2. A populated store with two distinct versions hydrates ``transitions``
   tagged with ``_source: 'local_store'`` and the per-version aggregates
   reflect the seeded rows.
3. Sessions are correctly partitioned into the version window they
   started in.
4. The env-gate is honoured — fast path stays dormant when
   CLAWMETRY_LOCAL_STORE_READ is off.
5. ``session.started`` rows missing the version field are skipped
   gracefully (older installs / partial data).
"""

from __future__ import annotations

import importlib
import json
import time
import uuid

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    # Point the legacy SQLite version_events table at the tmp dir so a
    # contributor's real ``~/.clawmetry/history.db`` doesn't leak version
    # rows into the test fixture.
    monkeypatch.setenv("HOME", str(tmp_path))

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.meta as meta_mod
    importlib.reload(meta_mod)

    # Issue #1538 pattern: isolate fixture from a developer's locally-
    # running clawmetry daemon (otherwise ``_ls_call`` proxies through
    # ``~/.clawmetry/local_query.json`` and queries the daemon's
    # production DuckDB instead of our tmp_path fixture — seeded rows
    # become invisible to the fast path).
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(meta_mod.bp_version_impact)
    yield a, ls, meta_mod
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


def _started_event(sid, ts, version):
    """A ``session.started`` row matching what
    ``clawmetry/sync.py::_parse_v3_event`` produces for v3 sessions."""
    return {
        "id":          str(uuid.uuid4()),
        "node_id":     "node-test",
        "agent_type":  "openclaw",
        "agent_id":    "main",
        "session_id":  sid,
        "workspace_id": None,
        "event_type":  "session.started",
        "ts":          ts,
        "data":        json.dumps({
            "_v3_type": "session",
            "type":     "session.started",
            "id":       sid,
            "version":  version,
            "cwd":      "/tmp/wks",
            "timestamp": ts,
        }),
    }


def _assistant_event(sid, ts, *, cost_usd=0.0, token_count=0):
    """An assistant turn — cost + token bookkeeping. ``query_sessions``
    SQL-side dedupe handles sibling-pair collapsing per issue #1460."""
    return {
        "id":          str(uuid.uuid4()),
        "node_id":     "node-test",
        "agent_type":  "openclaw",
        "agent_id":    "main",
        "session_id":  sid,
        "workspace_id": None,
        "event_type":  "assistant",
        "ts":          ts,
        "data":        json.dumps({
            "_v3_type": "message",
            "type":     "model.completed",
            "modelId":  "claude-opus-4-7",
        }),
        "cost_usd":    cost_usd,
        "token_count": token_count,
        "model":       "claude-opus-4-7",
    }


def _tool_call_event(sid, ts):
    return {
        "id":          str(uuid.uuid4()),
        "node_id":     "node-test",
        "agent_type":  "openclaw",
        "agent_id":    "main",
        "session_id":  sid,
        "workspace_id": None,
        "event_type":  "tool_call",
        "ts":          ts,
        "data":        json.dumps({"tool_name": "Read"}),
    }


def test_empty_store_falls_through_to_legacy_path(app, monkeypatch):
    """No session.started rows → fast path returns None → caller
    serves the legacy SQLite envelope (or the "no version history" stub
    when SQLite is empty too)."""
    a, _ls, meta_mod = app
    # Pin the legacy version probe so we don't shell out to ``openclaw``
    # during the test. Empty SQLite + empty DuckDB should produce the
    # canonical "no history yet" envelope WITHOUT the _source tag.
    import dashboard as _d
    monkeypatch.setattr(_d, "_get_openclaw_version", lambda: None)

    r = a.test_client().get("/api/version-impact")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    # Legacy path's signature: no _source tag.
    assert "_source" not in body, (
        f"empty store must not tag _source=local_store; got {body!r}"
    )
    assert body.get("current_version") == "unknown"
    assert body.get("transitions") == []


def test_populated_store_tags_local_store_source(app, monkeypatch):
    """Two distinct versions seeded → fast path returns ``_source='local_store'``
    with a transition between them, and per-version aggregates reflect
    the seeded cost + token totals."""
    a, ls, meta_mod = app
    import dashboard as _d
    monkeypatch.setattr(_d, "_get_openclaw_version", lambda: "2026.5.13")
    monkeypatch.setattr(_d, "_record_version_if_changed", lambda v: None)

    store = ls.get_store()
    # ── v1: 2026.5.12 — 2 sessions, modest spend.
    store.ingest(_started_event("sess-v1-a", "2026-05-15T10:00:00Z", "2026.5.12"))
    store.ingest(_assistant_event("sess-v1-a", "2026-05-15T10:00:05Z",
                                  cost_usd=0.010, token_count=1000))
    store.ingest(_tool_call_event("sess-v1-a", "2026-05-15T10:00:06Z"))
    store.ingest(_assistant_event("sess-v1-a", "2026-05-15T10:00:15Z",
                                  cost_usd=0.020, token_count=2000))

    store.ingest(_started_event("sess-v1-b", "2026-05-15T11:00:00Z", "2026.5.12"))
    store.ingest(_assistant_event("sess-v1-b", "2026-05-15T11:00:05Z",
                                  cost_usd=0.030, token_count=3000))

    # ── v2: 2026.5.13 — 1 session, lower per-session spend.
    store.ingest(_started_event("sess-v2-a", "2026-05-16T10:00:00Z", "2026.5.13"))
    store.ingest(_assistant_event("sess-v2-a", "2026-05-16T10:00:05Z",
                                  cost_usd=0.005, token_count=500))
    store.ingest(_tool_call_event("sess-v2-a", "2026-05-16T10:00:06Z"))
    store.ingest(_tool_call_event("sess-v2-a", "2026-05-16T10:00:07Z"))
    _drain(store)

    r = a.test_client().get("/api/version-impact")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"_source must be local_store on populated store; got {body.get('_source')!r}"
    )
    # Version history is ordered earliest-detected first.
    history = body.get("version_history") or []
    assert [h["version"] for h in history] == ["2026.5.12", "2026.5.13"], (
        f"version history mis-ordered: {history!r}"
    )
    # Exactly one transition (v1 → v2).
    transitions = body.get("transitions") or []
    assert len(transitions) == 1, (
        f"expected 1 transition, got {len(transitions)}: {transitions!r}"
    )
    t = transitions[0]
    assert t["from_version"] == "2026.5.12"
    assert t["to_version"] == "2026.5.13"
    # Before bucket = v1 = 2 sessions, $0.060 total.
    assert t["before"]["session_count"] == 2, t["before"]
    assert t["before"]["total_cost"] == pytest.approx(0.060, rel=1e-3), t["before"]
    # After bucket = v2 = 1 session, $0.005 total.
    assert t["after"]["session_count"] == 1, t["after"]
    assert t["after"]["total_cost"] == pytest.approx(0.005, rel=1e-3), t["after"]
    # Tool-call counts surface in avg_tool_calls.
    assert t["before"]["avg_tool_calls"] == pytest.approx(0.5, rel=1e-3), t["before"]
    assert t["after"]["avg_tool_calls"] == pytest.approx(2.0, rel=1e-3), t["after"]
    # Diff carries the percentage drop in avg_cost.
    diff = t.get("diff") or {}
    assert "avg_cost" in diff
    assert diff["avg_cost"]["before"] > 0
    assert diff["avg_cost"]["after"] > 0


def test_env_gate_skips_fast_path(app, monkeypatch):
    """With ``CLAWMETRY_LOCAL_STORE_READ`` off the fast path must NOT
    fire even when DuckDB has rows — preserves the opt-out for users
    who hit a regression."""
    a, ls, meta_mod = app
    import dashboard as _d
    monkeypatch.setattr(_d, "_get_openclaw_version", lambda: None)
    monkeypatch.setattr(_d, "_record_version_if_changed", lambda v: None)
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")

    store = ls.get_store()
    store.ingest(_started_event("sess-x", "2026-05-15T10:00:00Z", "2026.5.12"))
    _drain(store)

    r = a.test_client().get("/api/version-impact")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert "_source" not in body, (
        f"env-gate off must NOT tag _source; got {body!r}"
    )


def test_session_started_without_version_skipped(app, monkeypatch):
    """Some pre-v3 / partial-write rows lack ``data.version``. The fast
    path must skip them — never crash, never spawn an "unknown" bucket.
    If NO row carries a version the helper must return None so the
    legacy path serves the response."""
    a, ls, meta_mod = app
    import dashboard as _d
    monkeypatch.setattr(_d, "_get_openclaw_version", lambda: None)
    monkeypatch.setattr(_d, "_record_version_if_changed", lambda v: None)

    store = ls.get_store()
    # session.started without a version field — older installs.
    no_version = _started_event("sess-noversion", "2026-05-15T10:00:00Z", "")
    blob = json.loads(no_version["data"])
    blob.pop("version", None)
    no_version["data"] = json.dumps(blob)
    store.ingest(no_version)
    _drain(store)

    r = a.test_client().get("/api/version-impact")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    # All rows lacked version → fast path bailed → legacy envelope (no _source).
    assert "_source" not in body
    assert body.get("transitions") == []


def test_single_version_yields_no_transitions(app, monkeypatch):
    """Only one version observed → version_history populated but no
    transitions (consistent with the legacy SQLite path's first-version
    behaviour). _source must still be tagged so the dashboard knows the
    DuckDB pipeline served the response."""
    a, ls, meta_mod = app
    import dashboard as _d
    monkeypatch.setattr(_d, "_get_openclaw_version", lambda: "2026.5.12")
    monkeypatch.setattr(_d, "_record_version_if_changed", lambda v: None)

    store = ls.get_store()
    store.ingest(_started_event("sess-only", "2026-05-15T10:00:00Z", "2026.5.12"))
    store.ingest(_assistant_event("sess-only", "2026-05-15T10:00:05Z",
                                  cost_usd=0.01, token_count=100))
    _drain(store)

    r = a.test_client().get("/api/version-impact")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert len(body.get("version_history") or []) == 1
    assert body.get("transitions") == []
    assert body.get("current_version") == "2026.5.12"
