"""Regression tests for MOAT epic #1743 — events-derived aggregates.

The principle (per @vivekchand on #1725):

    shouldn't all info / events be just pushed to DuckDB & then run
    queries on them to find total token usage per session, per agent,
    overall etc?

Yes. The ``sessions`` table has denormalized aggregate columns
(``total_tokens``, ``cost_usd``, ``message_count``) that drift when an
ingest path is partial. This fire migrates the EASY read surfaces to use

    GREATEST(stored, SUM(events.<field>))

so any session whose events ARE in the local DuckDB events table reports
correct figures even when the stored column drifted to 0.

Companion to ``tests/test_query_sessions_message_count.py`` (#1129 bug 4)
which pins the same pattern for ``message_count``.
"""

from __future__ import annotations

import importlib
import uuid

import pytest


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.02")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=True)


def _wait(s, timeout=2.0):
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if s.health()["ring_depth"] == 0:
            return
        time.sleep(0.01)
    raise AssertionError("flusher did not drain")


def _ingest_token_event(
    s, sid, *, tokens, cost, ts="2026-05-19T10:00:00Z", agent_type="openclaw"
):
    """Ingest a model-completion event with stamped tokens + cost.

    Per ``_coerce_event_metrics`` in local_store.py the daemon picks up
    top-level ``token_count`` + ``cost_usd`` first — pass them directly
    so the test doesn't depend on the pricing-table side of the
    extractor.
    """
    s.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test",
        "agent_id": "main",
        "agent_type": agent_type,
        "session_id": sid,
        "event_type": "brain",
        "ts": ts,
        "token_count": int(tokens),
        "cost_usd": float(cost),
        "data": {"type": "model.completed", "data": {"text": "x"}},
    })


# ──────────────────────────────────────────────────────────────────────
# query_sessions_table — total_tokens (#1725 / PR #1738) + cost_usd (#1743)
# ──────────────────────────────────────────────────────────────────────


def test_total_tokens_computed_from_events_when_stored_is_zero(store):
    """Gateway-ingested sessions (e.g. Telegram) arrive with
    total_tokens=0. The events table is the source of truth — the read
    must sum it."""
    sid = "tg-sess-1"
    store.ingest_session({
        "session_id": sid,
        "agent_type": "openclaw",
        "title": "Telegram session — gateway-ingested",
        "started_at":     "2026-05-19T10:00:00Z",
        "last_active_at": "2026-05-19T10:05:00Z",
        "status": "active",
        # bug class: gateway path never populates these
        # total_tokens defaulted to 0; cost_usd defaulted to 0
    })
    _ingest_token_event(store, sid, tokens=1500, cost=0.012,
                        ts="2026-05-19T10:00:01Z")
    _ingest_token_event(store, sid, tokens=2750, cost=0.022,
                        ts="2026-05-19T10:00:02Z")
    _wait(store)

    rows = store.query_sessions_table(agent_type="openclaw")
    assert len(rows) == 1
    assert rows[0]["session_id"] == sid
    assert rows[0]["total_tokens"] == 4250
    assert abs(rows[0]["cost_usd"] - 0.034) < 1e-9


def test_cost_usd_computed_from_events_when_stored_is_zero(store):
    """Same bridge for ``cost_usd`` (#1743). The stored column defaults
    to 0; events-derived sum wins."""
    sid = "cost-sess-1"
    store.ingest_session({
        "session_id": sid,
        "agent_type": "openclaw",
        "started_at":     "2026-05-19T10:00:00Z",
        "last_active_at": "2026-05-19T10:00:30Z",
        # cost_usd defaults to 0
    })
    for i in range(5):
        _ingest_token_event(store, sid, tokens=200, cost=0.005,
                            ts=f"2026-05-19T10:00:{i:02d}Z")
    _wait(store)

    rows = store.query_sessions_table(agent_type="openclaw")
    assert len(rows) == 1
    assert abs(rows[0]["cost_usd"] - 0.025) < 1e-9


def test_aggregates_fall_back_to_stored_when_no_events(store):
    """sync.py path stuffs aggregates into the typed row without
    necessarily writing events. Stored value must win in that case."""
    sid = "synced-sess"
    store.ingest_session({
        "session_id": sid,
        "agent_type": "claude_code",
        "started_at":     "2026-05-19T10:00:00Z",
        "last_active_at": "2026-05-19T10:00:00Z",
        "total_tokens": 9999,
        "cost_usd":     1.23,
        "message_count": 42,
    })
    _wait(store)

    rows = store.query_sessions_table(agent_type="claude_code")
    assert len(rows) == 1
    assert rows[0]["total_tokens"] == 9999
    assert rows[0]["cost_usd"] == 1.23
    assert rows[0]["message_count"] == 42


def test_aggregates_use_max_when_both_set(store):
    """If both sides have data, the larger wins — we never UNDER-count
    when the stored value is stale (events kept arriving after
    ingest_session). Mirrors the message_count test in #1129."""
    sid = "drift-sess"
    store.ingest_session({
        "session_id": sid,
        "agent_type": "openclaw",
        "started_at":     "2026-05-19T10:00:00Z",
        "last_active_at": "2026-05-19T10:01:00Z",
        "total_tokens": 100,   # stale
        "cost_usd":     0.001, # stale
    })
    for i in range(4):
        _ingest_token_event(store, sid, tokens=500, cost=0.01,
                            ts=f"2026-05-19T10:00:{i:02d}Z")
    _wait(store)

    rows = store.query_sessions_table(agent_type="openclaw")
    assert len(rows) == 1
    # events: 2000 tokens / $0.04 > stale 100 tokens / $0.001
    assert rows[0]["total_tokens"] == 2000
    assert abs(rows[0]["cost_usd"] - 0.04) < 1e-9


def test_aggregates_isolated_per_session(store):
    """Correlated subqueries must filter by session_id — events for
    OTHER sessions must not pollute the totals."""
    store.ingest_session({
        "session_id": "iso-A",
        "agent_type": "openclaw",
        "started_at":     "2026-05-19T10:00:00Z",
        "last_active_at": "2026-05-19T10:00:00Z",
    })
    store.ingest_session({
        "session_id": "iso-B",
        "agent_type": "openclaw",
        "started_at":     "2026-05-19T10:00:00Z",
        "last_active_at": "2026-05-19T10:00:01Z",
    })
    _ingest_token_event(store, "iso-A", tokens=100, cost=0.001)
    for i in range(3):
        _ingest_token_event(store, "iso-B", tokens=1000, cost=0.01,
                            ts=f"2026-05-19T10:01:{i:02d}Z")
    _wait(store)

    rows = {r["session_id"]: r for r in
            store.query_sessions_table(agent_type="openclaw")}
    assert rows["iso-A"]["total_tokens"] == 100
    assert abs(rows["iso-A"]["cost_usd"] - 0.001) < 1e-9
    assert rows["iso-B"]["total_tokens"] == 3000
    assert abs(rows["iso-B"]["cost_usd"] - 0.03) < 1e-9


# ──────────────────────────────────────────────────────────────────────
# query_recent_evals — same bridge (#1743)
# ──────────────────────────────────────────────────────────────────────


def test_recent_evals_aggregates_from_events_when_stored_is_zero(store):
    """``/api/evals/recent`` must not show $0 / 0 tokens for sessions
    whose stored aggregates drifted."""
    sid = "eval-sess-1"
    store.ingest_session({
        "session_id": sid,
        "agent_type": "openclaw",
        "title": "scored session",
        "started_at":     "2026-05-19T10:00:00Z",
        "last_active_at": "2026-05-19T10:05:00Z",
        "status": "completed",
        # bug class: gateway path leaves these 0
    })
    # Score the session so it shows up in query_recent_evals.
    store.persist_eval_score(
        session_id=sid,
        score=4.5,
        reason="good",
        judge_model="claude-3-5-sonnet",
        scored_at=1716112800000,
        rubric="openclaw_v1",
    )
    _ingest_token_event(store, sid, tokens=3000, cost=0.045,
                        ts="2026-05-19T10:00:01Z")
    _wait(store)

    rows = store.query_recent_evals(limit=10)
    assert len(rows) == 1
    assert rows[0]["session_id"] == sid
    assert rows[0]["total_tokens"] == 3000
    assert abs(rows[0]["cost_usd"] - 0.045) < 1e-9


def test_recent_evals_falls_back_to_stored_when_no_events(store):
    """sync.py / cloud-pulled scored sessions: stored value must win."""
    sid = "eval-stored-only"
    store.ingest_session({
        "session_id": sid,
        "agent_type": "claude_code",
        "started_at":     "2026-05-19T10:00:00Z",
        "last_active_at": "2026-05-19T10:00:00Z",
        "total_tokens": 5000,
        "cost_usd":     0.25,
    })
    store.persist_eval_score(
        session_id=sid,
        score=3.0,
        reason="ok",
        judge_model="claude-3-5-sonnet",
        scored_at=1716112800000,
        rubric="v1",
    )
    _wait(store)

    rows = store.query_recent_evals(limit=10)
    assert len(rows) == 1
    assert rows[0]["total_tokens"] == 5000
    assert rows[0]["cost_usd"] == 0.25


# ──────────────────────────────────────────────────────────────────────
# query_subagents — events bridge (#1743 / #1755)
# ──────────────────────────────────────────────────────────────────────


def _ingest_subagent_event(
    s, subagent_id, *, tokens, cost, ts="2026-05-19T10:00:00Z",
    agent_type="openclaw",
):
    """Ingest a brain event scoped to a subagent (session_id=subagent_id)."""
    s.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test",
        "agent_id": "main",
        "agent_type": agent_type,
        "session_id": subagent_id,
        "event_type": "brain",
        "ts": ts,
        "token_count": int(tokens),
        "cost_usd": float(cost),
        "data": {"type": "model.completed", "data": {"text": "x"}},
    })


def test_subagent_cost_computed_from_events_when_stored_is_zero(store):
    """Daemon SIGKILL between event ingest and aggregate update leaves
    subagents.cost_usd=0. Events are the source of truth (#1743/#1755)."""
    sa_id = "sa-test-1"
    store.ingest_subagent({
        "subagent_id": sa_id,
        "agent_type": "openclaw",
        "parent_session_id": "parent-1",
        "spawned_at": "2026-05-19T10:00:00Z",
        "status": "completed",
        "cost_usd": 0.0,
        "token_count": 0,
    })
    _ingest_subagent_event(store, sa_id, tokens=1200, cost=0.009,
                           ts="2026-05-19T10:00:01Z")
    _ingest_subagent_event(store, sa_id, tokens=800, cost=0.006,
                           ts="2026-05-19T10:00:02Z")
    _wait(store)

    rows = store.query_subagents()
    assert len(rows) == 1
    assert rows[0]["subagent_id"] == sa_id
    assert rows[0]["token_count"] == 2000
    assert abs(rows[0]["cost_usd"] - 0.015) < 1e-9


def test_subagent_aggregates_fall_back_to_stored_when_no_events(store):
    """Cloud-sync path writes stored aggregates without events — stored
    value must win when no events exist for that subagent."""
    sa_id = "sa-stored-only"
    store.ingest_subagent({
        "subagent_id": sa_id,
        "agent_type": "openclaw",
        "parent_session_id": "parent-2",
        "spawned_at": "2026-05-19T11:00:00Z",
        "status": "completed",
        "cost_usd": 0.05,
        "token_count": 3500,
    })
    _wait(store)

    rows = store.query_subagents()
    assert len(rows) == 1
    assert rows[0]["token_count"] == 3500
    assert abs(rows[0]["cost_usd"] - 0.05) < 1e-9


def test_subagent_events_dont_cross_pollinate(store):
    """Events scoped to subagent-A must not inflate subagent-B's totals."""
    store.ingest_subagent({
        "subagent_id": "sa-A",
        "agent_type": "openclaw",
        "parent_session_id": "parent-x",
        "spawned_at": "2026-05-19T10:00:00Z",
        "status": "completed",
        "cost_usd": 0.0, "token_count": 0,
    })
    store.ingest_subagent({
        "subagent_id": "sa-B",
        "agent_type": "openclaw",
        "parent_session_id": "parent-x",
        "spawned_at": "2026-05-19T10:00:01Z",
        "status": "completed",
        "cost_usd": 0.0, "token_count": 0,
    })
    _ingest_subagent_event(store, "sa-A", tokens=500, cost=0.004,
                           ts="2026-05-19T10:00:10Z")
    _wait(store)

    rows = {r["subagent_id"]: r for r in store.query_subagents()}
    assert rows["sa-A"]["token_count"] == 500
    assert rows["sa-B"]["token_count"] == 0
    assert rows["sa-B"]["cost_usd"] == 0.0


# ──────────────────────────────────────────────────────────────────────
# query_cron_runs — events bridge (#1743 / #1756)
# ──────────────────────────────────────────────────────────────────────


def _ingest_cron_event(
    s, job_id, *, tokens, cost, ts, agent_type="openclaw",
):
    """Ingest a cron_run event (event_type='cron_run', agent_id=job_id)."""
    s.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test",
        "agent_id": job_id,
        "agent_type": agent_type,
        "session_id": str(uuid.uuid4()),
        "event_type": "cron_run",
        "ts": ts,
        "token_count": int(tokens),
        "cost_usd": float(cost),
        "data": {},
    })


def test_cron_run_cost_computed_from_events_when_stored_is_zero(store):
    """Older gateway versions emit cron-run JSONL without a usage field,
    leaving token_count=0. Events have the correct totals (#1743/#1756)."""
    run_id = "cr-test-1"
    job_id = "daily-report"
    store.ingest_cron_run({
        "id": run_id,
        "job_id": job_id,
        "agent_type": "openclaw",
        "started_at": "2026-05-19T06:00:00Z",
        "ended_at":   "2026-05-19T06:01:00Z",
        "status": "success",
        "token_count": 0,
        "cost_usd": 0.0,
    })
    _ingest_cron_event(store, job_id, tokens=900, cost=0.007,
                       ts="2026-05-19T06:00:15Z")
    _ingest_cron_event(store, job_id, tokens=600, cost=0.004,
                       ts="2026-05-19T06:00:45Z")
    _wait(store)

    rows = store.query_cron_runs(job_id=job_id)
    assert len(rows) == 1
    assert rows[0]["token_count"] == 1500
    assert abs(rows[0]["cost_usd"] - 0.011) < 1e-9


def test_cron_run_aggregates_fall_back_to_stored_when_no_events(store):
    """When a cron run has stored aggregates and no matching events,
    the stored values must be returned."""
    run_id = "cr-stored-only"
    job_id = "weekly-summary"
    store.ingest_cron_run({
        "id": run_id,
        "job_id": job_id,
        "agent_type": "openclaw",
        "started_at": "2026-05-19T08:00:00Z",
        "ended_at":   "2026-05-19T08:02:00Z",
        "status": "success",
        "token_count": 4200,
        "cost_usd": 0.033,
    })
    _wait(store)

    rows = store.query_cron_runs(job_id=job_id)
    assert len(rows) == 1
    assert rows[0]["token_count"] == 4200
    assert abs(rows[0]["cost_usd"] - 0.033) < 1e-9


def test_cron_run_time_window_isolates_consecutive_runs(store):
    """Two consecutive runs of the same job must not cross-pollinate.
    The time-window filter [started_at, ended_at] is the disambiguator."""
    job_id = "hourly-ping"
    # First run: 09:00–09:01
    store.ingest_cron_run({
        "id": "cr-run1",
        "job_id": job_id,
        "agent_type": "openclaw",
        "started_at": "2026-05-19T09:00:00Z",
        "ended_at":   "2026-05-19T09:01:00Z",
        "status": "success",
        "token_count": 0, "cost_usd": 0.0,
    })
    # Second run: 10:00–10:01
    store.ingest_cron_run({
        "id": "cr-run2",
        "job_id": job_id,
        "agent_type": "openclaw",
        "started_at": "2026-05-19T10:00:00Z",
        "ended_at":   "2026-05-19T10:01:00Z",
        "status": "success",
        "token_count": 0, "cost_usd": 0.0,
    })
    # Event inside run1's window only
    _ingest_cron_event(store, job_id, tokens=300, cost=0.002,
                       ts="2026-05-19T09:00:30Z")
    # Event inside run2's window only
    _ingest_cron_event(store, job_id, tokens=700, cost=0.005,
                       ts="2026-05-19T10:00:30Z")
    _wait(store)

    rows = {r["id"]: r for r in store.query_cron_runs(job_id=job_id)}
    assert rows["cr-run1"]["token_count"] == 300
    assert rows["cr-run2"]["token_count"] == 700
    assert abs(rows["cr-run1"]["cost_usd"] - 0.002) < 1e-9
    assert abs(rows["cr-run2"]["cost_usd"] - 0.005) < 1e-9
