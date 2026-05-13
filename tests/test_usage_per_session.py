"""Tests for issue #68 — per-session cost breakdown on /api/usage.

The Usage endpoint now returns a top-N ``sessions`` array sorted by
``total_cost_usd`` desc so the dashboard can show "which session burned
the budget". This test seeds three sessions with known token + cost
volumes via the DuckDB local store, hits ``/api/usage`` through the
local-store fast path, and asserts:

  * the ``sessions`` array is present and respects ordering
  * each row carries the contract fields specified in issue #68
  * totals per session match the seeded events

Pattern mirrors ``tests/test_usage_local_store.py``.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


def _wait_flush(store, t: float = 2.0) -> None:
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _seed_three_sessions(store):
    """Seed three sessions with deliberately distinct costs so we can
    assert ordering. Session A is the runaway loop ($5), Session B is
    the medium burner ($1.50), Session C is a quiet baseline ($0.10).
    Each session gets multiple events to exercise the per-session
    aggregation in ``query_sessions``."""
    now = time.time()
    seed = [
        # (session_id, n_events, per_event_cost, per_event_tokens, model)
        ("sess-runaway", 5, 1.0,  10000, "claude-opus-4"),    # $5.00, 50K tokens
        ("sess-medium",  3, 0.50, 3000,  "claude-sonnet-4"),  # $1.50, 9K  tokens
        ("sess-quiet",   2, 0.05, 500,   "gpt-4o-mini"),      # $0.10, 1K  tokens
    ]
    for sid, n, cost, tokens, model in seed:
        for i in range(n):
            store.ingest({
                "id":          f"ev-{sid}-{i}",
                "node_id":     "agent+test",
                "agent_id":    "main",
                "session_id":  sid,
                "event_type":  "tool_call",
                "ts":          _iso(now - (i * 60)),
                "data":        {"plugin": "bash"},
                "cost_usd":    cost,
                "token_count": tokens,
                "model":       model,
            })
    _wait_flush(store)
    return seed


@pytest.fixture
def fast_path_app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    # Isolate the daemon discovery file — if the dev machine has a real
    # daemon running, ``local_store_via_daemon`` would proxy our calls
    # to it and the test would read events from the wrong DuckDB.
    monkeypatch.setenv("HOME", str(tmp_path))

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    monkeypatch.setattr(lq, "_DISCOVERY_PATH", str(tmp_path / "no-daemon.json"))
    lq._invalidate_daemon_cache()
    import routes.usage as usage_mod
    importlib.reload(usage_mod)

    app = Flask(__name__)
    app.register_blueprint(usage_mod.bp_usage)
    yield app, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_usage_sessions_array_present(fast_path_app):
    """Smoke: /api/usage carries a ``sessions`` array under the fast path."""
    app, ls = fast_path_app
    _seed_three_sessions(ls.get_store())

    body = app.test_client().get("/api/usage").get_json()
    assert body["_source"] == "local_store"
    assert "sessions" in body, "missing top-level 'sessions' array"
    assert isinstance(body["sessions"], list)
    assert len(body["sessions"]) == 3


def test_usage_sessions_sorted_by_cost_desc(fast_path_app):
    """Sessions must be sorted by ``total_cost_usd`` DESC — the whole
    point of the breakdown is "who burned the budget"."""
    app, ls = fast_path_app
    _seed_three_sessions(ls.get_store())

    sessions = app.test_client().get("/api/usage").get_json()["sessions"]
    ids = [s["session_id"] for s in sessions]
    assert ids == ["sess-runaway", "sess-medium", "sess-quiet"], (
        f"unexpected ordering: {ids}"
    )
    costs = [s["total_cost_usd"] for s in sessions]
    assert costs == sorted(costs, reverse=True)


def test_usage_session_row_contract(fast_path_app):
    """Each row carries the issue-#68 contract fields."""
    app, ls = fast_path_app
    _seed_three_sessions(ls.get_store())

    sessions = app.test_client().get("/api/usage").get_json()["sessions"]
    expected_keys = {"session_id", "agent_id", "model", "total_tokens",
                     "total_cost_usd", "message_count", "started_at"}
    for row in sessions:
        assert expected_keys.issubset(row.keys()), (
            f"row missing keys: {expected_keys - set(row.keys())}"
        )


def test_usage_session_totals_match_seeded_data(fast_path_app):
    """Per-session totals match what we ingested. Costs use floating
    arithmetic, so allow a tiny epsilon."""
    app, ls = fast_path_app
    _seed_three_sessions(ls.get_store())

    sessions = app.test_client().get("/api/usage").get_json()["sessions"]
    by_id = {s["session_id"]: s for s in sessions}

    runaway = by_id["sess-runaway"]
    assert runaway["total_cost_usd"] == pytest.approx(5.0, abs=1e-6)
    assert runaway["total_tokens"] == 50000
    assert runaway["message_count"] == 5

    medium = by_id["sess-medium"]
    assert medium["total_cost_usd"] == pytest.approx(1.5, abs=1e-6)
    assert medium["total_tokens"] == 9000
    assert medium["message_count"] == 3

    quiet = by_id["sess-quiet"]
    assert quiet["total_cost_usd"] == pytest.approx(0.10, abs=1e-6)
    assert quiet["total_tokens"] == 1000
    assert quiet["message_count"] == 2


def test_usage_session_limit_respects_top_n(fast_path_app):
    """The helper caps at 20 sessions by default — feed it 25 and
    confirm only the top 20 (by cost) come back."""
    app, ls = fast_path_app
    store = ls.get_store()
    now = time.time()
    # 25 sessions, each one event, costs 0.01..0.25 so the cheapest 5
    # should be trimmed off.
    for i in range(25):
        sid = f"sess-{i:02d}"
        store.ingest({
            "id":          f"ev-{sid}",
            "node_id":     "agent+test",
            "agent_id":    "main",
            "session_id":  sid,
            "event_type":  "tool_call",
            "ts":          _iso(now - (i * 60)),
            "data":        {"plugin": "bash"},
            "cost_usd":    0.01 * (i + 1),
            "token_count": 100 * (i + 1),
            "model":       "claude-opus-4",
        })
    _wait_flush(store)

    sessions = app.test_client().get("/api/usage").get_json()["sessions"]
    assert len(sessions) == 20
    # The cheapest 5 (sess-00..sess-04) must NOT appear in the top-20.
    returned_ids = {s["session_id"] for s in sessions}
    for i in range(5):
        assert f"sess-{i:02d}" not in returned_ids
