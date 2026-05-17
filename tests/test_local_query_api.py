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

    # Issue #1538: isolate fixture from any running clawmetry daemon
    # on the contributor's machine. Without this, _dispatch tries
    # _proxy_dispatch first; that reads ~/.clawmetry/local_query.json
    # and POSTs to the daemon, which then queries ITS production DuckDB
    # (~/.clawmetry/clawmetry.duckdb) instead of this test's tmp_path
    # fixture. CI never had a daemon so CI passed; laptops with the
    # daemon running silently failed 11/16. Force direct-mode always.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    # Pre-#1448 events tests seed historical timestamps that fall outside
    # the OSS 24h retention cap. Default the fixture to Pro so those
    # assertions still pass; the cap tests below monkeypatch
    # ``_is_pro_user`` explicitly. Mirrors PR #1445's fixture pattern.
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

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


def test_aggregates_endpoint_dedupes_v3_sibling_pairs(client):
    """Same dedupe contract as ``test_sessions_endpoint_dedupes_v3_sibling_pairs``,
    one level up at the daily-aggregate layer. Issue: ``query_aggregates``
    used to SUM(cost_usd) + SUM(token_count) over the raw events table,
    doubling every billable turn on real v3 installs. The SQL CTE now
    drops the slim sibling ONLY when an assistant/message rank-2 row
    exists in the same (session_id, ts_sec) bucket.

    ``event_count`` stays RAW so debug surfaces see all the rows.
    """
    c, ls = client
    store = ls.get_store()
    ts = "2026-05-16T10:00:00Z"
    # Sibling pair = 1 deduped turn @ 150 tokens / $0.005
    store.ingest(_ev(id="agg-assist", session_id="sess-pair",
                     event_type="assistant", ts=ts,
                     cost_usd=0.005, token_count=150))
    store.ingest(_ev(id="agg-mc", session_id="sess-pair",
                     event_type="model.completed", ts=ts,
                     cost_usd=0.005, token_count=150))
    # Two tool_calls sharing ts_sec are NOT siblings - both count
    store.ingest(_ev(id="agg-t1", session_id="sess-tools",
                     event_type="tool_call", ts=ts,
                     cost_usd=0.10, token_count=12))
    store.ingest(_ev(id="agg-t2", session_id="sess-tools",
                     event_type="tool_call", ts=ts,
                     cost_usd=0.20, token_count=33))
    _wait(store)
    r = c.get("/api/local/aggregates")
    body = r.get_json()
    by_day = {row["day"]: row for row in body["rows"]}
    row = by_day["2026-05-16"]
    assert row["event_count"] == 4, "raw event_count should report all 4 rows"
    assert row["token_count"] == 195, (
        f"dedupe wrong: expected 150 (deduped sibling) + 12 + 33 = 195 tokens, "
        f"got {row['token_count']}"
    )
    assert round(row["cost_usd"], 4) == 0.305, (
        f"dedupe wrong: expected $0.005 (deduped sibling) + $0.10 + $0.20 = $0.305, "
        f"got {round(row['cost_usd'], 4)}"
    )


def test_sessions_endpoint_dedupes_v3_sibling_pairs(client):
    """Issue #1460: on real OpenClaw v3 installs each LLM turn emits BOTH
    an ``assistant`` row AND a sibling ``model.completed`` row ~100 ms
    apart, both stamped with the same ``token_count`` + ``cost_usd``.
    The SQL fix in ``query_sessions`` must dedupe at the SQL layer so all
    consumers (cluster aggregator, anomaly detector, this endpoint, etc.)
    return the single billable turn — not 2× of it.

    ``event_count`` stays RAW (it is the row-count, not the turn-count) so
    debug surfaces can still tell you both rows did arrive.
    """
    c, ls = client
    store = ls.get_store()
    store.ingest(_ev(
        id="assist-1", session_id="sess-pair",
        event_type="assistant",
        ts="2026-05-16T10:00:00Z",
        cost_usd=0.005, token_count=150,
    ))
    store.ingest(_ev(
        id="mc-1", session_id="sess-pair",
        event_type="model.completed",
        ts="2026-05-16T10:00:00Z",
        cost_usd=0.005, token_count=150,
    ))
    _wait(store)
    r = c.get("/api/local/sessions")
    body = r.get_json()
    by_sid = {s["session_id"]: s for s in body["rows"]}
    row = by_sid["sess-pair"]
    assert row["event_count"] == 2, "raw event_count should still report both rows"
    assert row["token_count"] == 150, (
        f"sibling pair must dedupe to 1 turn = 150 tokens, got "
        f"{row['token_count']} (regression: SQL layer not deduping)"
    )
    assert round(row["cost_usd"], 4) == 0.005, (
        f"sibling pair must dedupe to 1 turn = $0.005, got "
        f"{round(row['cost_usd'], 4)}"
    )


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


# ── Retention cap (issue #1448 surface 4) ──────────────────────────────────
#
# OSS / Cloud-Free users get clamped to the last 24h of raw events on
# /api/local/events. Cloud-Pro users (gated by ``dashboard._is_pro_user``)
# bypass the cap. The response always carries ``capped_at_24h`` so the UI
# can surface an upgrade CTA when the cap kicks in. Mirrors PR #1445's
# pattern for /api/flow/runs.


def _seed_old_and_recent(store):
    """One ancient event (8 days old) + one fresh event (now)."""
    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc)
    old_ts = (now - _dt.timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_ts = (now - _dt.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    store.ingest(_ev(id="cap-old", session_id="sess-cap", ts=old_ts))
    store.ingest(_ev(id="cap-new", session_id="sess-cap", ts=new_ts))
    _wait(store)


def test_api_local_events_caps_24h_for_free(client, monkeypatch):
    c, ls = client
    _seed_old_and_recent(ls.get_store())
    # Force OSS (non-Pro) path.
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: False)

    r = c.get("/api/local/events?session_id=sess-cap&limit=10")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body["capped_at_24h"] is True
    ids = {row["id"] for row in body["rows"]}
    # The 8-day-old event must be excluded; only the fresh one shows.
    assert ids == {"cap-new"}


def test_api_local_events_no_cap_for_pro(client, monkeypatch):
    c, ls = client
    _seed_old_and_recent(ls.get_store())
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

    r = c.get("/api/local/events?session_id=sess-cap&limit=10")
    body = r.get_json()
    assert body["capped_at_24h"] is False
    ids = {row["id"] for row in body["rows"]}
    # Pro users see the full history including the 8-day-old event.
    assert ids == {"cap-old", "cap-new"}
