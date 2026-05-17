"""Tests for the decision-sampling review surface (issue #1615).

Covers:
  * DDL — review_queue table is created at schema v8.
  * ingest_review_sample is idempotent on duplicate session_id.
  * update_review_decision flips the row + rejects invalid statuses.
  * query_review_accuracy excludes borderline + pending rows from the
    denominator, returns accuracy=None on an empty queue (no div-by-zero).
  * sample_yesterday_for_review picks N per agent deterministically with
    a seeded RNG.
  * /api/review/queue + /api/review/<sid> + /api/review/accuracy round-trip.
"""

from __future__ import annotations

import importlib
import os
import random
import sys
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── fixtures ───────────────────────────────────────────────────────────────


def _fresh_store(tmp_path, monkeypatch):
    """Reload local_store against an isolated DuckDB file. Also redirects
    ~/.clawmetry to ``tmp_path`` so the daemon-discovery file from a real
    live install can't hijack ``_store_call`` (would otherwise route our
    test fixture's queries to the user's real DuckDB)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Force the daemon-proxy discovery to re-read against the new HOME.
    import routes.local_query as lq
    importlib.reload(lq)
    return ls


def _seed_sessions(store, *, day: str, agent_sessions: dict[str, int]) -> None:
    """Seed N sessions per agent_id with started_at on ``day``.

    Writes through the typed ``sessions`` table the way sync.py does so
    sample_yesterday_for_review's query_sessions_table call finds them.
    """
    started_iso = f"{day}T12:00:00+00:00"
    for agent_id, n in agent_sessions.items():
        for i in range(n):
            sid = f"sess-{agent_id}-{i}"
            store.ingest_session({
                "session_id":     sid,
                "agent_id":       agent_id,
                "agent_type":     "openclaw",
                "title":          f"Session {sid}",
                "started_at":     started_iso,
                "last_active_at": started_iso,
                "total_tokens":   100 * (i + 1),
            })


# ── unit tests ─────────────────────────────────────────────────────────────


def test_schema_creates_review_queue(tmp_path, monkeypatch):
    ls = _fresh_store(tmp_path, monkeypatch)
    store = ls.get_store()
    try:
        rows = store._fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='main' AND table_name='review_queue'",
            [],
        )
        assert len(rows) == 1
    finally:
        store.stop(flush=False)


def test_ingest_review_sample_is_idempotent(tmp_path, monkeypatch):
    ls = _fresh_store(tmp_path, monkeypatch)
    store = ls.get_store()
    try:
        first = store.ingest_review_sample({
            "session_id": "sess-1",
            "agent_id":   "main",
        })
        second = store.ingest_review_sample({
            "session_id": "sess-1",
            "agent_id":   "main",
        })
        assert first == 1
        assert second == 0
        rows = store.query_review_queue()
        assert len(rows) == 1
        assert rows[0]["session_id"] == "sess-1"
        assert rows[0]["status"] == "pending"
    finally:
        store.stop(flush=False)


def test_update_review_decision_flips_row(tmp_path, monkeypatch):
    ls = _fresh_store(tmp_path, monkeypatch)
    store = ls.get_store()
    try:
        store.ingest_review_sample({"session_id": "sess-1", "agent_id": "main"})
        n = store.update_review_decision(
            "sess-1", "reviewed_correct", notes="Looks fine"
        )
        assert n == 1
        rows = store.query_review_queue()
        assert rows[0]["status"] == "reviewed_correct"
        assert rows[0]["reviewer_notes"] == "Looks fine"
        assert rows[0]["reviewed_at"] is not None

        # Re-decision is allowed (reviewer changing their mind).
        n2 = store.update_review_decision("sess-1", "reviewed_wrong")
        assert n2 == 1
        rows = store.query_review_queue()
        assert rows[0]["status"] == "reviewed_wrong"
    finally:
        store.stop(flush=False)


def test_update_review_rejects_invalid_status(tmp_path, monkeypatch):
    ls = _fresh_store(tmp_path, monkeypatch)
    store = ls.get_store()
    try:
        store.ingest_review_sample({"session_id": "sess-1", "agent_id": "main"})
        with pytest.raises(ValueError):
            store.update_review_decision("sess-1", "approve")
        # Missing rows are a graceful 0, not an exception.
        assert store.update_review_decision("missing", "reviewed_correct") == 0
    finally:
        store.stop(flush=False)


def test_query_review_accuracy_empty_returns_none(tmp_path, monkeypatch):
    """Empty queue must not divide by zero — UI relies on accuracy=None."""
    ls = _fresh_store(tmp_path, monkeypatch)
    store = ls.get_store()
    try:
        out = store.query_review_accuracy(window_days=30)
        assert out["global"]["accuracy"] is None
        assert out["per_agent"] == []
        assert out["window_days"] == 30
    finally:
        store.stop(flush=False)


def test_query_review_accuracy_excludes_borderline(tmp_path, monkeypatch):
    """Borderline rows should not move the accuracy needle.

    Seed: 3 correct, 1 wrong, 2 borderline → 75% (3 / (3 + 1)).
    """
    ls = _fresh_store(tmp_path, monkeypatch)
    store = ls.get_store()
    try:
        for i in range(3):
            sid = f"sess-correct-{i}"
            store.ingest_review_sample({"session_id": sid, "agent_id": "main"})
            store.update_review_decision(sid, "reviewed_correct")
        store.ingest_review_sample({"session_id": "sess-wrong-0", "agent_id": "main"})
        store.update_review_decision("sess-wrong-0", "reviewed_wrong")
        for i in range(2):
            sid = f"sess-bdr-{i}"
            store.ingest_review_sample({"session_id": sid, "agent_id": "main"})
            store.update_review_decision(sid, "reviewed_borderline")
        # And a pending row, which must also be excluded.
        store.ingest_review_sample({"session_id": "sess-pending", "agent_id": "main"})

        out = store.query_review_accuracy(window_days=30)
        assert out["global"]["correct"] == 3
        assert out["global"]["wrong"] == 1
        assert out["global"]["borderline"] == 2
        assert out["global"]["accuracy"] == pytest.approx(0.75)
        assert len(out["per_agent"]) == 1
        assert out["per_agent"][0]["agent_id"] == "main"
        assert out["per_agent"][0]["accuracy"] == pytest.approx(0.75)
    finally:
        store.stop(flush=False)


def test_query_review_accuracy_per_agent_split(tmp_path, monkeypatch):
    """Two agents → two per_agent buckets, each with its own accuracy."""
    ls = _fresh_store(tmp_path, monkeypatch)
    store = ls.get_store()
    try:
        # agent-A: 2 correct, 0 wrong → 100%
        for i in range(2):
            sid = f"a-{i}"
            store.ingest_review_sample({"session_id": sid, "agent_id": "agent-A"})
            store.update_review_decision(sid, "reviewed_correct")
        # agent-B: 1 correct, 1 wrong → 50%
        store.ingest_review_sample({"session_id": "b-0", "agent_id": "agent-B"})
        store.update_review_decision("b-0", "reviewed_correct")
        store.ingest_review_sample({"session_id": "b-1", "agent_id": "agent-B"})
        store.update_review_decision("b-1", "reviewed_wrong")

        out = store.query_review_accuracy(window_days=30)
        by_agent = {r["agent_id"]: r for r in out["per_agent"]}
        assert by_agent["agent-A"]["accuracy"] == pytest.approx(1.0)
        assert by_agent["agent-B"]["accuracy"] == pytest.approx(0.5)
        assert out["global"]["accuracy"] == pytest.approx(0.75)
    finally:
        store.stop(flush=False)


def test_sample_yesterday_picks_n_per_agent_deterministic(tmp_path, monkeypatch):
    """Seeded RNG → identical samples on repeated runs (same store wipe).

    Seed 20 sessions for agent-A + 5 for agent-B on yesterday's date.
    Ask for 10 random per agent. agent-A returns 10 (sampled), agent-B
    returns all 5 (no oversample). Same seed → same sids on a fresh
    store.
    """
    ls = _fresh_store(tmp_path, monkeypatch)
    store = ls.get_store()
    try:
        now = datetime.now(timezone.utc)
        yesterday = (now - timedelta(days=1)).date().isoformat()
        _seed_sessions(store, day=yesterday, agent_sessions={"agent-A": 20, "agent-B": 5})

        # Import after store is up so routes/review.py picks up our env.
        import routes.review as rv
        importlib.reload(rv)

        rng1 = random.Random(42)
        out1 = rv.sample_yesterday_for_review(sample_size=10, now=now, rng=rng1)
        assert out1["sampled"] == 15  # 10 from agent-A + 5 from agent-B
        assert out1["agents"] == 2

        queued1 = sorted(r["session_id"] for r in store.query_review_queue())
        assert len(queued1) == 15

        # Second invocation with the same now/seed is idempotent — all 15
        # already in the queue, no new inserts.
        rng2 = random.Random(42)
        out2 = rv.sample_yesterday_for_review(sample_size=10, now=now, rng=rng2)
        assert out2["sampled"] == 0
        assert out2["skipped"] >= 15
    finally:
        store.stop(flush=False)


# ── HTTP surface tests ────────────────────────────────────────────────────


def _build_review_app(tmp_path, monkeypatch):
    ls = _fresh_store(tmp_path, monkeypatch)
    import routes.review as rv
    importlib.reload(rv)
    app = Flask(__name__)
    app.register_blueprint(rv.bp_review)
    return app, ls, rv


def test_api_review_queue_and_post(tmp_path, monkeypatch):
    app, ls, rv = _build_review_app(tmp_path, monkeypatch)
    store = ls.get_store()
    try:
        store.ingest_review_sample({"session_id": "sess-1", "agent_id": "main"})
        client = app.test_client()

        r = client.get("/api/review/queue")
        assert r.status_code == 200
        body = r.get_json()
        assert body["count"] == 1
        assert body["rows"][0]["status"] == "pending"

        r = client.post(
            "/api/review/sess-1",
            json={"status": "reviewed_correct", "notes": "ok"},
        )
        assert r.status_code == 200
        assert r.get_json()["ok"] is True

        # Invalid status returns 400.
        r = client.post(
            "/api/review/sess-1",
            json={"status": "looks_good"},
        )
        assert r.status_code == 400

        # Missing row returns 404.
        r = client.post(
            "/api/review/missing-sess",
            json={"status": "reviewed_correct"},
        )
        assert r.status_code == 404
    finally:
        store.stop(flush=False)


def test_api_review_accuracy_empty(tmp_path, monkeypatch):
    """Endpoint returns 200 + accuracy=None on an empty store."""
    app, ls, rv = _build_review_app(tmp_path, monkeypatch)
    store = ls.get_store()
    try:
        client = app.test_client()
        r = client.get("/api/review/accuracy?window=30")
        assert r.status_code == 200
        body = r.get_json()
        assert body["global"]["accuracy"] is None
        assert body["per_agent"] == []
    finally:
        store.stop(flush=False)
