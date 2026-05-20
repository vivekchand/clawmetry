"""Regression tests for MOAT issue #1756 — ``query_cron_runs`` must derive
``cost_usd`` + ``token_count`` from the ``events`` table rather than reading
the (drift-prone) stored aggregate columns on the ``cron_runs`` row.

Per @vivekchand on #1725 ("shouldn't all info / events be just pushed to
DuckDB & then run queries on them to find total token usage per session,
per agent, overall etc?") the source of truth is the events table.
``cron_runs.{token_count, cost_usd}`` are stored at JSONL-ingest time and
can drift below the real cost when:

  * The gateway WS delivers the ``cron_run`` event rollup AFTER the JSONL
    line was synced (token_count/cost_usd were zero at ingest time).
  * An early gateway version's JSONL writer omitted the ``usage`` block
    entirely (stored aggregates land as zero).

This file pins the bridge: ``GREATEST(stored, SUM(events.field))`` scoped
to ``event_type='cron_run' AND agent_id = cr.job_id AND agent_type ==
cr.agent_type AND ts within [cr.started_at, cr.ended_at]``.

Sibling of ``tests/test_events_only_computation.py`` (PR #1754 for
``query_sessions_table``).
"""

from __future__ import annotations

import importlib
import uuid

import pytest


# ── fixture ────────────────────────────────────────────────────────────────


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh LocalStore against a tmp DuckDB, flusher tuned for speed."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH",
                       str(tmp_path / "cron_runs.duckdb"))
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


def _ingest_cron_run_event(
    s, *, job_id, ts, tokens, cost,
    agent_type="openclaw", session_id=None,
):
    """Ingest a single ``cron_run`` event with stamped tokens + cost.

    Mirrors the shape the gateway WS writer ships per
    ``routes/crons.py:_try_local_store_cron_runs`` — ``agent_id`` carries
    the cron's job_id, top-level ``token_count`` + ``cost_usd`` carry the
    rollup, and ``data`` holds the freeform payload.
    """
    s.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test",
        "agent_id": str(job_id),
        "agent_type": agent_type,
        "session_id": session_id or "",
        "event_type": "cron_run",
        "ts": ts,
        "token_count": int(tokens),
        "cost_usd": float(cost),
        "data": {"cron_id": job_id, "jobId": job_id, "status": "ok"},
    })


def _ingest_cron_runs_row(
    s, *, run_id, job_id, started_at, ended_at,
    stored_tokens=0, stored_cost=0.0, agent_type="openclaw",
):
    """Upsert one cron_runs row with the given stored aggregates."""
    s.ingest_cron_run({
        "id": str(run_id),
        "node_id": "agent+test",
        "agent_type": agent_type,
        "agent_id": "main",
        "job_id": str(job_id),
        "started_at": started_at,
        "ended_at":   ended_at,
        "duration_ms": 1000,
        "status": "ok",
        "token_count": int(stored_tokens),
        "cost_usd": float(stored_cost),
    })


# ── core regression — #1756 acceptance ─────────────────────────────────────


def test_cost_and_tokens_derived_from_events_when_stored_drifted(store):
    """The smoking-gun case from #1756.

    Stored aggregate on cron_runs row is ARTIFICIALLY HIGH ($0.99) to
    simulate a stale-but-stored value the JSONL writer recorded. Three
    ``cron_run`` events in the events table together sum to the TRUE
    values: tokens=2100, cost=$0.18.

    The bridge uses ``GREATEST(stored, computed)`` so it picks the
    LARGER of the two. To prove this test exercises the events path
    (and isn't just reading the cached column), we instead drift the
    stored DOWN to a value smaller than the events sum.

    Truth: tokens=2100, cost=$0.18 (from events).
    Stored: tokens=0, cost=$0.0 (simulates JSONL ingest before usage
    rollup landed via gateway WS).
    """
    job_id = "daily-backup"
    started, ended = "2026-05-19T10:00:00Z", "2026-05-19T10:00:05Z"

    _ingest_cron_runs_row(
        store, run_id=f"{job_id}:{started}", job_id=job_id,
        started_at=started, ended_at=ended,
        stored_tokens=0, stored_cost=0.0,  # drifted below truth
    )
    # Three events together = $0.18 + 2100 tokens.
    _ingest_cron_run_event(store, job_id=job_id,
                           ts="2026-05-19T10:00:01Z",
                           tokens=500, cost=0.05)
    _ingest_cron_run_event(store, job_id=job_id,
                           ts="2026-05-19T10:00:02Z",
                           tokens=700, cost=0.06)
    _ingest_cron_run_event(store, job_id=job_id,
                           ts="2026-05-19T10:00:03Z",
                           tokens=900, cost=0.07)
    _wait(store)

    rows = store.query_cron_runs(job_id=job_id)
    assert len(rows) == 1
    r = rows[0]
    assert r["token_count"] == 2100, \
        f"expected events-derived tokens=2100, got {r['token_count']}"
    assert abs(r["cost_usd"] - 0.18) < 1e-9, \
        f"expected events-derived cost=$0.18, got ${r['cost_usd']}"


def test_stored_aggregate_wins_when_higher_than_events(store):
    """The GREATEST envelope must never UNDER-count — if the stored
    aggregate is higher (e.g. cron events haven't landed yet but the
    JSONL writer's usage block is authoritative for this run), the
    stored value wins.

    This is the inverse case of the smoking-gun above. Stored is $0.99
    + 9999 tokens; the events table has a single low-cost rollup.
    Result must keep the stored value, not regress to events.
    """
    job_id = "deploy-bot"
    started, ended = "2026-05-19T11:00:00Z", "2026-05-19T11:00:03Z"
    _ingest_cron_runs_row(
        store, run_id=f"{job_id}:{started}", job_id=job_id,
        started_at=started, ended_at=ended,
        stored_tokens=9999, stored_cost=0.99,
    )
    _ingest_cron_run_event(store, job_id=job_id,
                           ts="2026-05-19T11:00:01Z",
                           tokens=100, cost=0.01)
    _wait(store)

    rows = store.query_cron_runs(job_id=job_id)
    assert len(rows) == 1
    r = rows[0]
    assert r["token_count"] == 9999, \
        f"expected stored-wins tokens=9999, got {r['token_count']}"
    assert abs(r["cost_usd"] - 0.99) < 1e-9, \
        f"expected stored-wins cost=$0.99, got ${r['cost_usd']}"


def test_two_runs_same_job_isolated_by_time_window(store):
    """``cron_runs`` is NOT 1:1 with ``job_id`` — the same cron can run
    hundreds of times in a day. The bridge MUST scope the events sum to
    a single run's ``[started_at, ended_at]`` window so consecutive
    runs of the same job don't pollute each other's totals.

    Two runs of ``hourly-poll``:
      * Run A (10:00:00 → 10:00:05): events sum to 500 tokens, $0.05
      * Run B (11:00:00 → 11:00:05): events sum to 900 tokens, $0.09

    Without time-window scoping, both rows would report the JOIN-sum
    1400 tokens / $0.14 — that's the bug class to pin.
    """
    job_id = "hourly-poll"
    _ingest_cron_runs_row(
        store, run_id="run-A", job_id=job_id,
        started_at="2026-05-19T10:00:00Z",
        ended_at  ="2026-05-19T10:00:05Z",
        stored_tokens=0, stored_cost=0.0,
    )
    _ingest_cron_runs_row(
        store, run_id="run-B", job_id=job_id,
        started_at="2026-05-19T11:00:00Z",
        ended_at  ="2026-05-19T11:00:05Z",
        stored_tokens=0, stored_cost=0.0,
    )
    _ingest_cron_run_event(store, job_id=job_id,
                           ts="2026-05-19T10:00:02Z",
                           tokens=500, cost=0.05)
    _ingest_cron_run_event(store, job_id=job_id,
                           ts="2026-05-19T11:00:02Z",
                           tokens=900, cost=0.09)
    _wait(store)

    rows = {r["id"]: r for r in store.query_cron_runs(job_id=job_id)}
    assert set(rows.keys()) == {"run-A", "run-B"}
    assert rows["run-A"]["token_count"] == 500
    assert abs(rows["run-A"]["cost_usd"] - 0.05) < 1e-9
    assert rows["run-B"]["token_count"] == 900
    assert abs(rows["run-B"]["cost_usd"] - 0.09) < 1e-9


def test_v3_sibling_pair_not_double_counted(store):
    """V3 sibling-pair guard (per ``feedback_usage_dedupe_pattern.md``).

    The OpenClaw v3 daemon normalises a model call into a (prompt.submitted,
    model.completed) sibling pair. Both events carry their own
    ``token_count`` / ``cost_usd`` — but for cron-run aggregation we only
    want the rolled-up ``event_type='cron_run'`` row, NOT the underlying
    model events. The bridge's ``WHERE event_type = 'cron_run'`` filter
    pins this: dropping the sibling pair into the events table alongside
    a cron_run event must not inflate the row's aggregates.

    Truth: cron-run event = 1500 tokens + $0.15.
    Noise: a model.completed sibling event = 1200 tokens + $0.12.
    Expected query_cron_runs result = 1500, NOT 2700.
    """
    job_id = "v3-cron"
    started, ended = "2026-05-19T12:00:00Z", "2026-05-19T12:00:05Z"
    _ingest_cron_runs_row(
        store, run_id=f"{job_id}:{started}", job_id=job_id,
        started_at=started, ended_at=ended,
        stored_tokens=0, stored_cost=0.0,
    )
    # The authoritative rollup.
    _ingest_cron_run_event(store, job_id=job_id,
                           ts="2026-05-19T12:00:02Z",
                           tokens=1500, cost=0.15)
    # A sibling-pair model.completed in the same time window with the
    # same agent_id — must NOT be summed in because event_type differs.
    store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test",
        "agent_id": job_id,
        "agent_type": "openclaw",
        "session_id": "model-sess-1",
        "event_type": "brain",  # v3 wraps model.completed under 'brain'
        "ts": "2026-05-19T12:00:03Z",
        "token_count": 1200,
        "cost_usd": 0.12,
        "data": {"type": "model.completed",
                 "data": {"text": "sibling pair"}},
    })
    _wait(store)

    rows = store.query_cron_runs(job_id=job_id)
    assert len(rows) == 1
    r = rows[0]
    assert r["token_count"] == 1500, \
        f"sibling-pair leaked into cron sum: got {r['token_count']}"
    assert abs(r["cost_usd"] - 0.15) < 1e-9, \
        f"sibling-pair leaked into cron cost: got ${r['cost_usd']}"


def test_no_events_falls_back_to_stored(store):
    """When the events table has nothing for this cron run (e.g. on a
    cold install before the gateway WS has emitted any cron_run rollups
    yet), reads must fall back gracefully to the stored aggregate
    rather than report zeros."""
    job_id = "weekly-report"
    started, ended = "2026-05-19T13:00:00Z", "2026-05-19T13:00:02Z"
    _ingest_cron_runs_row(
        store, run_id=f"{job_id}:{started}", job_id=job_id,
        started_at=started, ended_at=ended,
        stored_tokens=42, stored_cost=0.42,
    )
    _wait(store)

    rows = store.query_cron_runs(job_id=job_id)
    assert len(rows) == 1
    r = rows[0]
    assert r["token_count"] == 42
    assert abs(r["cost_usd"] - 0.42) < 1e-9


def test_cross_job_events_do_not_leak(store):
    """Events emitted for ``job_A`` must not be summed into ``job_B``'s
    cron_run row even when their time windows overlap. The
    ``agent_id = cr.job_id`` filter is the isolation."""
    _ingest_cron_runs_row(
        store, run_id="run-A", job_id="job_A",
        started_at="2026-05-19T14:00:00Z",
        ended_at  ="2026-05-19T14:00:05Z",
        stored_tokens=0, stored_cost=0.0,
    )
    _ingest_cron_runs_row(
        store, run_id="run-B", job_id="job_B",
        started_at="2026-05-19T14:00:00Z",
        ended_at  ="2026-05-19T14:00:05Z",
        stored_tokens=0, stored_cost=0.0,
    )
    _ingest_cron_run_event(store, job_id="job_A",
                           ts="2026-05-19T14:00:02Z",
                           tokens=111, cost=0.011)
    _ingest_cron_run_event(store, job_id="job_B",
                           ts="2026-05-19T14:00:02Z",
                           tokens=222, cost=0.022)
    _wait(store)

    rows_a = store.query_cron_runs(job_id="job_A")
    rows_b = store.query_cron_runs(job_id="job_B")
    assert rows_a[0]["token_count"] == 111
    assert rows_b[0]["token_count"] == 222
    assert abs(rows_a[0]["cost_usd"] - 0.011) < 1e-9
    assert abs(rows_b[0]["cost_usd"] - 0.022) < 1e-9
