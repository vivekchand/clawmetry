"""Tests for /api/brain-history reading from the local DuckDB store.

Companion to ``tests/test_brain_local_fastpath.py``. That file proves the
fast-path opt-in env var works; this file pins down two extra contracts that
the engineering plan calls out explicitly:

  1. **Latency** — the local-store read path should be dramatically faster
     than the JSONL parser. We assert <100ms end-to-end for 5 rows so a
     regression that re-introduces a synchronous JSONL scan in the fast
     path will trip the test.
  2. **Negative** — without ``CLAWMETRY_LOCAL_STORE_READ=1`` the route
     must NOT touch DuckDB. We patch ``query_events`` to blow up on call
     and assert the route still returns 200 (i.e. the legacy path runs).

Both tests use an isolated tmp DuckDB so they don't see (or pollute) any
real install's local store.
"""

from __future__ import annotations

import importlib
import time

import pytest
from flask import Flask


def _wait_flush(store, t=2.0):
    """Block until the in-memory ring buffer has drained to DuckDB."""
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _seed(store, n=5):
    for i in range(n):
        store.ingest({
            "id":          f"ev-store-{i}",
            "node_id":     "agent+test",
            "agent_id":    "main",
            "session_id":  "sess-store",
            "event_type":  "tool_call",
            "ts":          f"2026-05-11T12:00:0{i}Z",
            "data":        {"tool": "Bash", "input": f"echo hello-{i}"},
            "cost_usd":    0.001,
            "token_count": 10,
            "model":       "claude-opus-4-7",
        })
    _wait_flush(store)


def _build_app(tmp_path, monkeypatch, *, enable_fast_path: bool):
    """Build an isolated Flask app with the brain blueprint and a tmp DB.

    Reload-orders matter: ``local_store`` first (so its module-level
    DB_PATH picks up the env var), then ``routes.brain`` (which only
    imports the store inside the request handler, but reload is cheap
    and makes the test order-independent).
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    if enable_fast_path:
        monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    else:
        monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.brain as br
    importlib.reload(br)

    app = Flask(__name__)
    app.register_blueprint(br.bp_brain)
    return app, ls, br


@pytest.fixture
def fast_path_app(tmp_path, monkeypatch):
    app, ls, br = _build_app(tmp_path, monkeypatch, enable_fast_path=True)
    yield app, ls, br
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_brain_history_shape_matches_contract(fast_path_app):
    """The fast-path response shape is the documented contract:
    ``{events: [...], count: N, _source: 'local_store', _shape: 'brain_history'}``.
    Each event row must carry the keys the dashboard JS reads.
    """
    app, ls, _br = fast_path_app
    store = ls.get_store()
    _seed(store, n=5)

    body = app.test_client().get("/api/brain-history?limit=10").get_json()

    assert body["_source"] == "local_store"
    assert body["_shape"] == "brain_history"
    assert body["count"] == 5
    assert isinstance(body["events"], list) and len(body["events"]) == 5

    required_keys = {
        "time", "type", "detail", "src",
        "sessionId", "agentId", "tokens", "cost", "model",
    }
    for ev in body["events"]:
        missing = required_keys - ev.keys()
        assert not missing, f"event missing keys {missing}: {ev}"
        assert ev["sessionId"] == "sess-store"
        assert ev["type"] == "TOOL_CALL"
        assert ev["model"] == "claude-opus-4-7"
        assert ev["tokens"] == 10


def test_brain_history_latency_under_100ms(fast_path_app):
    """Five rows out of a warm DuckDB must complete in well under 100ms.

    This is a regression sentinel: if anyone re-introduces a JSONL scan
    or a synchronous network hop into the fast path the request will
    blow past this budget. We do one warm-up call so we measure steady
    state, not first-call DuckDB import + connection cost.
    """
    app, ls, _br = fast_path_app
    store = ls.get_store()
    _seed(store, n=5)

    client = app.test_client()
    # Warm-up: first call pays for module import + DuckDB connection open.
    client.get("/api/brain-history?limit=10")

    t0 = time.perf_counter()
    r = client.get("/api/brain-history?limit=10")
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert r.status_code == 200
    assert r.get_json()["_source"] == "local_store"
    assert elapsed_ms < 100.0, (
        f"local-store fast path took {elapsed_ms:.1f}ms (>100ms budget)"
    )


def test_brain_history_skips_duckdb_when_env_unset(tmp_path, monkeypatch):
    """Without ``CLAWMETRY_LOCAL_STORE_READ=1`` the handler must not call
    ``query_events`` at all — the legacy JSONL/log path runs instead.

    We prove this by monkey-patching ``LocalStore.query_events`` to raise
    on any call. If the env-var gate is wired correctly the route still
    returns 200 because the fast path is never invoked. If the gate
    leaks, the response would carry the ``_source: local_store`` tag (or
    crash, depending on how the regression looks).
    """
    app, ls, _br = _build_app(tmp_path, monkeypatch, enable_fast_path=False)

    # Even though the env flag is off, populate the store so we can prove
    # the route is genuinely *skipping* DuckDB rather than just finding
    # an empty table.
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")  # for the seed write
    store = ls.get_store()
    _seed(store, n=3)
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    # Now arm the trap. Any call to query_events from this point on
    # raises — the route MUST NOT touch it.
    def _boom(*_a, **_kw):
        raise AssertionError(
            "query_events called even though CLAWMETRY_LOCAL_STORE_READ is unset"
        )
    monkeypatch.setattr(store, "query_events", _boom)

    r = app.test_client().get("/api/brain-history?limit=10")
    assert r.status_code == 200
    body = r.get_json()
    # Legacy path's response shape lacks the fast-path tag.
    assert body.get("_source") != "local_store"

    try:
        store.stop(flush=True)
    except Exception:
        pass
