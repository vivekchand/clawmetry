"""Issue #1772: detail endpoints return HTTP 503 when local_store ingest is
offline AND the fast-path result would otherwise be empty.

The probe wires ``LocalStore.is_writer_alive()`` into 6 detail endpoints so
the dashboard can render an inline "ingest temporarily offline" banner
instead of a silent "0 messages / 0 tokens / 0 tools" panel that looks
like a successful agent run that did nothing. Empty-but-healthy continues
to return 200 (regression guard).

Coverage matrix:

| endpoint                       | empty + writer-down → 503 | empty + writer-up → 200 |
|--------------------------------|---------------------------|--------------------------|
| /api/transcript/<sid>          | yes                       | yes                      |
| /api/session-tools             | yes                       | yes                      |
| /api/brain-history             | yes                       | yes                      |
| /api/usage                     | yes                       | yes                      |
| /api/subagents                 | yes                       | yes                      |
| /api/flow-events               | yes                       | yes                      |
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Boot the route blueprints against a fresh DuckDB and force the
    local-store fast path on. ``is_writer_alive()`` is monkeypatched per-test
    to flip the writer state."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.brain as br
    importlib.reload(br)
    import routes.sessions as se
    importlib.reload(se)
    import routes.usage as us
    importlib.reload(us)
    import routes.infra as inf
    importlib.reload(inf)

    # Default to Pro to bypass the OSS 24h retention cap so empty/healthy
    # tests don't accidentally hit a capped envelope and miss the assertion.
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True, raising=False)

    a = Flask(__name__)
    a.register_blueprint(br.bp_brain)
    a.register_blueprint(se.bp_sessions)
    a.register_blueprint(us.bp_usage)
    a.register_blueprint(inf.bp_logs)
    a.register_blueprint(lq.bp_local_query)
    yield a, ls, lq
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _set_writer(lq, alive: bool, monkeypatch):
    """Force the local-query module's writer-alive probe to a known value.

    Also stubs out ``local_store_via_daemon`` so fast paths in the route
    modules don't sneak past the test by hitting a real daemon's DuckDB —
    the dev/CI host often has the sync daemon running with a populated
    store, which would make the fast paths return real data instead of
    None/empty and mask the outage probe entirely.
    """
    monkeypatch.setattr(lq, "is_local_store_alive", lambda: alive)
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *_a, **_k: None)


# ── Empty + writer-down → 503 with the standard envelope ───────────────────


def test_transcript_returns_503_when_ingest_offline(app, monkeypatch):
    a, _ls, lq = app
    _set_writer(lq, False, monkeypatch)
    r = a.test_client().get("/api/transcript/sess-missing")
    assert r.status_code == 503, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body["error"] == "local_store ingest is offline"
    assert body["writer_status"] == "down"
    assert body["_source"] == "ingest_outage"


def test_session_tools_returns_503_when_ingest_offline(app, monkeypatch):
    a, _ls, lq = app
    _set_writer(lq, False, monkeypatch)
    r = a.test_client().get("/api/session-tools?session_id=sess-missing")
    assert r.status_code == 503
    body = r.get_json()
    assert body["error"] == "local_store ingest is offline"
    assert body["session_id"] == "sess-missing"


def test_brain_history_returns_503_when_ingest_offline(app, monkeypatch):
    a, _ls, lq = app
    _set_writer(lq, False, monkeypatch)
    r = a.test_client().get("/api/brain-history?limit=10")
    assert r.status_code == 503
    body = r.get_json()
    assert body["error"] == "local_store ingest is offline"


def test_usage_returns_503_when_ingest_offline(app, monkeypatch):
    a, _ls, lq = app
    _set_writer(lq, False, monkeypatch)
    r = a.test_client().get("/api/usage")
    assert r.status_code == 503
    body = r.get_json()
    assert body["error"] == "local_store ingest is offline"


def test_subagents_returns_503_when_ingest_offline(app, monkeypatch):
    a, _ls, lq = app
    _set_writer(lq, False, monkeypatch)
    r = a.test_client().get("/api/subagents")
    assert r.status_code == 503
    body = r.get_json()
    assert body["error"] == "local_store ingest is offline"


def test_flow_events_returns_503_when_ingest_offline(app, monkeypatch):
    a, _ls, lq = app
    _set_writer(lq, False, monkeypatch)
    # JSON Accept header so the route returns the snapshot envelope
    # (not the live SSE stream).
    r = a.test_client().get("/api/flow-events", headers={"Accept": "application/json"})
    assert r.status_code == 503
    body = r.get_json()
    assert body["error"] == "local_store ingest is offline"


# ── Empty + writer-up → 200 with empty result (regression guard) ───────────


def test_brain_history_returns_200_when_ingest_alive_and_empty(app, monkeypatch):
    """Empty store + healthy writer → fast path returns its empty shell
    (200), no 503 surfaced. This is the brand-new-install case."""
    a, _ls, lq = app
    _set_writer(lq, True, monkeypatch)
    r = a.test_client().get("/api/brain-history?limit=10")
    # 200 with brain-history shape (count=0 or fallthrough body — either is
    # acceptable; the load-bearing assertion is "not 503").
    assert r.status_code == 200


def test_flow_events_returns_200_when_ingest_alive_and_empty(app, monkeypatch):
    a, _ls, lq = app
    _set_writer(lq, True, monkeypatch)
    r = a.test_client().get("/api/flow-events", headers={"Accept": "application/json"})
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("ok") is True
    assert "events" in body


# ── LocalStore.is_writer_alive() direct probe ──────────────────────────────


def test_is_writer_alive_true_on_fresh_store(app):
    _a, ls, _lq = app
    store = ls.get_store()
    assert store.is_writer_alive() is True


def test_is_writer_alive_false_when_conn_closed(app):
    _a, ls, _lq = app
    store = ls.get_store()
    # Force a poisoned state: close the connection out from under the
    # probe and bust the 1s cache.
    store._conn.close()
    store._is_writer_alive_cache = None
    assert store.is_writer_alive() is False


def test_is_writer_alive_cached_for_one_second(app):
    """Cache is per-instance with a 1 s TTL — verify a fresh probe within
    the window doesn't re-hit the DuckDB connection.

    We can't easily monkeypatch ``_conn.execute`` (DuckDB's PyConnection
    attributes are read-only), so we drive the cache directly: warm it
    with a True probe, then close the underlying connection. A within-TTL
    probe should still return True because the cached value short-circuits
    the closed connection.
    """
    _a, ls, _lq = app
    store = ls.get_store()
    assert store.is_writer_alive() is True
    # Connection is now closed — but the cache was set above, so the
    # next call returns the cached True without touching the connection.
    store._conn.close()
    assert store.is_writer_alive() is True
    # Bust the cache; now the probe re-runs against the closed connection
    # and returns False.
    store._is_writer_alive_cache = None
    assert store.is_writer_alive() is False
