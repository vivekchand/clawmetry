"""Tests for routes/local_query.py — the local HTTP query API over the
DuckDB store (#960 phase A)."""

from __future__ import annotations

import importlib
import json
import time
import uuid

import pytest
from flask import Flask


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Flask test client wired to a fresh isolated local store."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)

    app = Flask(__name__)
    app.register_blueprint(lq.bp_local_query)
    # Trigger store init + flusher start.
    ls.get_store()
    yield app.test_client(), ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ev(**overrides):
    base = {
        "id": str(uuid.uuid4()),
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "sess-A",
        "event_type": "tool_call",
        "ts": "2026-05-11T10:00:00Z",
        "data": {"tool": "Bash"},
        "cost_usd": 0.001,
        "token_count": 12,
        "model": "claude-opus-4-7",
    }
    base.update(overrides)
    return base


def _wait(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def test_health_endpoint(client):
    c, _ = client
    r = c.get("/api/local/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["engine"] == "duckdb"
    assert body["_shape"] == "health"
    assert "size_bytes" in body
    assert "_elapsed_ms" in body


def test_events_endpoint_returns_inserted_rows(client):
    c, ls = client
    store = ls.get_store()
    for i in range(3):
        store.ingest(_ev(id=f"ev-{i}", ts=f"2026-05-11T10:00:0{i}Z"))
    _wait(store)
    r = c.get("/api/local/events?session_id=sess-A&limit=10")
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 3
    assert body["_shape"] == "events"
    assert {row["id"] for row in body["rows"]} == {"ev-0", "ev-1", "ev-2"}


def test_events_endpoint_filters_by_event_type(client):
    c, ls = client
    store = ls.get_store()
    store.ingest(_ev(id="t1", event_type="tool_call"))
    store.ingest(_ev(id="m1", event_type="message"))
    _wait(store)
    r = c.get("/api/local/events?event_type=message")
    body = r.get_json()
    assert [row["id"] for row in body["rows"]] == ["m1"]


def test_sessions_endpoint(client):
    c, ls = client
    store = ls.get_store()
    store.ingest(_ev(id="a", session_id="X", cost_usd=0.10))
    store.ingest(_ev(id="b", session_id="X", cost_usd=0.20))
    store.ingest(_ev(id="c", session_id="Y", cost_usd=0.05))
    _wait(store)
    r = c.get("/api/local/sessions")
    body = r.get_json()
    assert body["count"] == 2
    by_sid = {s["session_id"]: s for s in body["rows"]}
    assert by_sid["X"]["event_count"] == 2
    assert round(by_sid["X"]["cost_usd"], 4) == 0.30


def test_aggregates_endpoint(client):
    c, ls = client
    store = ls.get_store()
    store.ingest(_ev(id="a", ts="2026-05-10T10:00:00Z", cost_usd=0.50))
    store.ingest(_ev(id="b", ts="2026-05-11T10:00:00Z", cost_usd=0.30))
    _wait(store)
    r = c.get("/api/local/aggregates")
    body = r.get_json()
    by_day = {row["day"]: row for row in body["rows"]}
    assert round(by_day["2026-05-10"]["cost_usd"], 4) == 0.50
    assert round(by_day["2026-05-11"]["cost_usd"], 4) == 0.30


def test_transcript_endpoint(client):
    c, ls = client
    store = ls.get_store()
    store.ingest(_ev(id="t1", session_id="sess-T", ts="2026-05-11T10:00:00Z"))
    store.ingest(_ev(id="t2", session_id="sess-T", ts="2026-05-11T10:00:01Z"))
    store.ingest(_ev(id="x1", session_id="sess-OTHER"))
    _wait(store)
    r = c.get("/api/local/transcript/sess-T")
    body = r.get_json()
    assert body["count"] == 2
    assert all(row["session_id"] == "sess-T" for row in body["rows"])


def test_query_post_dispatches_by_shape(client):
    c, ls = client
    store = ls.get_store()
    store.ingest(_ev(id="q1", session_id="sess-Q"))
    _wait(store)
    r = c.post(
        "/api/local/query",
        data=json.dumps({"shape": "events", "args": {"session_id": "sess-Q"}}),
        content_type="application/json",
    )
    body = r.get_json()
    assert body["count"] == 1
    assert body["rows"][0]["id"] == "q1"


def test_query_post_rejects_unknown_shape(client):
    c, _ = client
    r = c.post(
        "/api/local/query",
        data=json.dumps({"shape": "drop_table_users"}),
        content_type="application/json",
    )
    assert r.status_code == 400
    body = r.get_json()
    assert "allowed_shapes" in body


def test_transcript_shape_requires_session_id(client):
    c, _ = client
    r = c.post(
        "/api/local/query",
        data=json.dumps({"shape": "transcript", "args": {}}),
        content_type="application/json",
    )
    assert r.status_code == 500
    assert "session_id" in r.get_json()["error"]


def test_limit_is_clamped(client):
    """A request asking for limit=999999 gets clamped, not an error."""
    c, ls = client
    store = ls.get_store()
    for i in range(20):
        store.ingest(_ev(id=f"clamp-{i}"))
    _wait(store)
    r = c.get("/api/local/events?limit=999999&session_id=sess-A")
    assert r.status_code == 200


def test_relay_dispatch_helper(client):
    """The relay_dispatch() entry point — used by the future WS relay —
    runs the same path as the HTTP endpoints. Same SQL, single source of
    truth."""
    c, ls = client
    store = ls.get_store()
    store.ingest(_ev(id="rd-1", session_id="sess-relay"))
    _wait(store)
    import routes.local_query as lq
    body = lq.relay_dispatch("events", {"session_id": "sess-relay"})
    assert body["count"] == 1
    assert body["rows"][0]["id"] == "rd-1"


def test_relay_dispatch_rejects_unknown_shape():
    import routes.local_query as lq
    body = lq.relay_dispatch("nope", {})
    assert "error" in body
