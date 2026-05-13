"""Tests for the DuckDB coverage batch landed 2026-05-13.

Each test verifies the new ``_try_local_store_*`` fast path returns
``_source: "local_store"`` when DuckDB has the relevant rows. We only
assert the tag + a couple of structural keys — the legacy paths are
covered by their own existing tests.

Surfaces under test (5):
  - /api/prompt-errors                       routes/overview.py
  - /api/transcripts                         routes/sessions.py
  - /api/sessions/cost-breakdown             routes/sessions.py
  - /api/sessions/<id>/cost-breakdown        routes/sessions.py
  - /api/heatmap                             routes/health.py
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


# ── shared fixtures ────────────────────────────────────────────────────────


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


# ── /api/prompt-errors ─────────────────────────────────────────────────────


def test_prompt_errors_fast_path(fresh_store):
    ls = fresh_store
    store = ls.get_store()
    store.ingest({
        "id": "ev-pe-1",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "sess-pe",
        "event_type": "openclaw:prompt-error",
        "ts": "2026-05-12T12:00:00Z",
        "data": {
            "runId": "run-1",
            "provider": "anthropic",
            "model": "claude-opus-4-7",
            "api": "messages.create",
            "error": "rate_limited",
        },
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    c = _client("routes.overview", "bp_overview")
    r = c.get("/api/prompt-errors")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["count"] == 1
    e = body["errors"][0]
    assert e["sessionId"] == "sess-pe"
    assert e["error"] == "rate_limited"


# ── /api/transcripts ───────────────────────────────────────────────────────


def test_transcripts_fast_path(fresh_store):
    ls = fresh_store
    store = ls.get_store()
    # Two sessions worth of events → two transcript rows.
    for sid in ("sess-tx-A", "sess-tx-B"):
        for i in range(3):
            store.ingest({
                "id": f"ev-{sid}-{i}",
                "node_id": "agent+test",
                "agent_id": "main",
                "session_id": sid,
                "event_type": "message",
                "ts": f"2026-05-12T1{i}:00:00Z",
                "data": {"message": {"role": "user", "content": "hi"}},
            })
    _wait_flush(store)

    c = _client("routes.sessions", "bp_sessions")
    r = c.get("/api/transcripts")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    ids = {t["id"] for t in body["transcripts"]}
    assert {"sess-tx-A", "sess-tx-B"}.issubset(ids)
    # Each transcript reports its event count (3 messages each).
    counts = {t["id"]: t["messages"] for t in body["transcripts"]}
    assert counts["sess-tx-A"] == 3
    assert counts["sess-tx-B"] == 3


# ── /api/sessions/cost-breakdown (top sessions) ────────────────────────────


def test_sessions_cost_breakdown_fast_path(fresh_store):
    ls = fresh_store
    store = ls.get_store()
    # Two sessions, different cost totals.
    store.ingest({
        "id": "ev-cb-1", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-cb-cheap", "event_type": "message",
        "ts": "2026-05-12T10:00:00Z", "cost_usd": 0.01, "token_count": 100,
    })
    store.ingest({
        "id": "ev-cb-2", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-cb-expensive", "event_type": "message",
        "ts": "2026-05-12T10:00:01Z", "cost_usd": 5.0, "token_count": 50000,
    })
    _wait_flush(store)

    c = _client("routes.sessions", "bp_sessions")
    r = c.get("/api/sessions/cost-breakdown")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    # Sorted by cost desc — expensive session first.
    assert body["top10"][0]["session_id"] == "sess-cb-expensive"
    assert body["top10"][0]["cost_usd"] == pytest.approx(5.0)
    assert body["total_cost_usd"] == pytest.approx(5.01)


# ── /api/sessions/<id>/cost-breakdown (per-turn) ──────────────────────────


def test_session_cost_breakdown_fast_path(fresh_store):
    ls = fresh_store
    store = ls.get_store()
    # Two assistant turns with usage blocks.
    for i in range(2):
        store.ingest({
            "id": f"ev-tcb-{i}",
            "node_id": "agent+test",
            "agent_id": "main",
            "session_id": "sess-tcb",
            "event_type": "message",
            "ts": f"2026-05-12T10:0{i}:00Z",
            "data": {
                "message": {
                    "role": "assistant",
                    "model": "claude-opus-4-7",
                    "usage": {
                        "input": 100,
                        "output": 50,
                        "cacheRead": 10,
                        "cacheWrite": 5,
                        "cost": {
                            "input": 0.001,
                            "output": 0.002,
                            "cacheRead": 0.0001,
                            "cacheWrite": 0.0005,
                            "total": 0.0036,
                        },
                    },
                },
            },
            "model": "claude-opus-4-7",
        })
    _wait_flush(store)

    c = _client("routes.sessions", "bp_sessions")
    r = c.get("/api/sessions/sess-tcb/cost-breakdown")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["turn_count"] == 2
    assert body["totals"]["input_tokens"] == 200
    assert body["totals"]["output_tokens"] == 100
    assert body["totals"]["total_cost_usd"] == pytest.approx(0.0072)


# ── /api/heatmap ───────────────────────────────────────────────────────────


def test_heatmap_fast_path(fresh_store):
    ls = fresh_store
    store = ls.get_store()
    # Stamp a few events at "today, 14:00 local" so they land on today's
    # row in the grid regardless of the test runner's tz.
    today = datetime.now()
    iso = today.replace(hour=14, minute=0, second=0, microsecond=0).isoformat()
    for i in range(3):
        store.ingest({
            "id": f"ev-hm-{i}",
            "node_id": "agent+test",
            "agent_id": "main",
            "session_id": "sess-hm",
            "event_type": "message",
            "ts": iso,
        })
    _wait_flush(store)

    c = _client("routes.health", "bp_health")
    r = c.get("/api/heatmap?days=1")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["n_days"] == 1
    today_hours = body["days"][0]["hours"]
    assert today_hours[14] == 3
