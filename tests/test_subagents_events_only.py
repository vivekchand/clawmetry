"""Regression tests for issue #1755 / MOAT epic #1743.

``LocalStore.query_subagents`` MUST derive ``cost_usd`` + ``token_count``
from the ``events`` table rather than reading the cached aggregate
columns on ``subagents``. The cache drifts low whenever the daemon
ingests an event but is SIGKILLed before the matching
``record_subagent()`` aggregate-update lands. Events are the source of
truth (#1725).

The bridge follows PR #1754:

    GREATEST(
        COALESCE(s.<aggregate>, 0),
        COALESCE(SUM(events.<field>), 0)
    )

so the stored column remains a fallback for sub-agents whose events
have not arrived yet (or whose events live in a different DuckDB),
while guaranteeing we never under-report once events ingest.

Join key: events for a sub-agent are written with
``events.session_id = subagents.subagent_id`` — verified by
``clawmetry/sync.py::_local_ingest_session_batch`` (line ~2540) and by
``tests/test_subagent_attribution_v3.py``.
"""

from __future__ import annotations

import importlib
import time
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
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if s.health()["ring_depth"] == 0:
            return
        time.sleep(0.01)
    raise AssertionError("flusher did not drain")


def _ingest_token_event(
    s, sid, *, tokens, cost, ts, event_type="model.completed",
    agent_type="openclaw",
):
    """Mimic the daemon's v3-projected events shape (#1565 pattern)."""
    s.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test",
        "agent_id": "main",
        "agent_type": agent_type,
        "session_id": sid,
        "event_type": event_type,
        "ts": ts,
        "token_count": int(tokens),
        "cost_usd": float(cost),
        "data": {"type": event_type, "data": {"text": "x"}},
    })


def _get_subagent(store, sid):
    rows = store.query_subagents(limit=200)
    matches = [r for r in rows if r.get("subagent_id") == sid]
    assert matches, f"sub-agent {sid!r} missing from query_subagents() result"
    return matches[0]


# ──────────────────────────────────────────────────────────────────────
# Issue #1755 — happy path: events outvote a stale cached column
# ──────────────────────────────────────────────────────────────────────

def test_query_subagents_cost_and_tokens_from_events_outvote_stale_cache(store):
    """3 events sum to $0.42 / 4250 tokens. The cached
    ``subagents.{cost_usd,token_count}`` are simulated stale ($0.05 /
    100). ``query_subagents`` MUST return the events-derived figures
    (the truth), not the stale cache."""
    parent_sid = "parent-1755"
    child_sid  = "child-1755"

    # 1. Register the sub-agent link. ingest_subagent() writes the cache
    # columns with the values we pass — start with the "drifted" $0.05/100.
    store.ingest_subagent({
        "subagent_id":       child_sid,
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-19T09:00:00Z",
        "task":              "events-only proof",
        "status":            "completed",
        "cost_usd":          0.05,   # ← stale / partial-ingest cache
        "token_count":       100,    # ← stale / partial-ingest cache
    })

    # 2. Three events for the child. SUM = $0.42 / 4250 tokens.
    _ingest_token_event(store, child_sid, tokens=1000, cost=0.10,
                        ts="2026-05-19T09:00:01Z")
    _ingest_token_event(store, child_sid, tokens=1250, cost=0.12,
                        ts="2026-05-19T09:00:02Z")
    _ingest_token_event(store, child_sid, tokens=2000, cost=0.20,
                        ts="2026-05-19T09:00:03Z")
    _wait(store)

    row = _get_subagent(store, child_sid)

    # Events-derived totals must win.
    assert row["cost_usd"] == pytest.approx(0.42, abs=1e-6), (
        f"expected events-derived $0.42, got {row['cost_usd']!r} "
        f"(stale cache was $0.05 — looks like the read is still hitting "
        f"the stored column instead of SUM(events))"
    )
    assert row["token_count"] == 4250, (
        f"expected events-derived 4250, got {row['token_count']!r} "
        f"(stale cache was 100)"
    )


# ──────────────────────────────────────────────────────────────────────
# Issue #1755 — fallback: no events yet, stored column wins
# ──────────────────────────────────────────────────────────────────────

def test_query_subagents_falls_back_to_stored_when_no_events(store):
    """If the sub-agent's events haven't ingested yet (or live in a
    different DuckDB), the cached column is still surfaced. This guards
    fresh installs and the cloud-relay path where the cache is the only
    source available."""
    parent_sid = "parent-cache-only"
    child_sid  = "child-cache-only"
    store.ingest_subagent({
        "subagent_id":       child_sid,
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-19T09:10:00Z",
        "status":            "active",
        "cost_usd":          0.077,
        "token_count":       1234,
    })
    _wait(store)

    row = _get_subagent(store, child_sid)
    assert row["cost_usd"] == pytest.approx(0.077, abs=1e-6)
    assert row["token_count"] == 1234


# ──────────────────────────────────────────────────────────────────────
# Issue #1755 — v3 sibling-pair dedupe (assistant + model.completed)
# ──────────────────────────────────────────────────────────────────────

def test_query_subagents_dedupes_v3_assistant_model_completed_sibling_pair(store):
    """On real v3 OpenClaw installs each LLM turn emits BOTH an
    ``assistant`` row AND a sibling ``model.completed`` row in the same
    second, both stamped with identical token/cost. A naive
    ``SUM(events.cost_usd)`` would double the billable turn.

    Seed one turn worth $0.10 / 1000 tokens as a sibling PAIR (same
    ``ts_sec``) and assert the result is $0.10 / 1000 — NOT $0.20 / 2000.
    Mirrors the dedupe contract proven on ``query_sessions`` (#1460) and
    ``query_aggregates``.
    """
    parent_sid = "parent-sibling"
    child_sid  = "child-sibling"

    # Stale cache so we can prove the events path is what's running.
    store.ingest_subagent({
        "subagent_id":       child_sid,
        "agent_type":        "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-19T09:20:00Z",
        "status":            "active",
        "cost_usd":          0.0,
        "token_count":       0,
    })

    # Sibling pair: identical ts_sec, both rows stamp the same usage.
    # Per query_sessions dedupe: ``assistant`` rank=2 outranks
    # ``model.completed`` rank=1 → the model.completed sibling is
    # dropped from the SUM.
    _ingest_token_event(store, child_sid, tokens=1000, cost=0.10,
                        ts="2026-05-19T09:20:05Z",
                        event_type="assistant")
    _ingest_token_event(store, child_sid, tokens=1000, cost=0.10,
                        ts="2026-05-19T09:20:05Z",  # ← same ts_sec
                        event_type="model.completed")

    # Plus one more distinct turn so we know we aren't returning 0.
    _ingest_token_event(store, child_sid, tokens=500, cost=0.05,
                        ts="2026-05-19T09:20:07Z",
                        event_type="assistant")
    _wait(store)

    row = _get_subagent(store, child_sid)
    # 1 deduped turn ($0.10) + 1 standalone turn ($0.05) = $0.15.
    # Without dedupe we'd see $0.25 ($0.10+$0.10+$0.05).
    assert row["cost_usd"] == pytest.approx(0.15, abs=1e-6), (
        f"sibling-pair dedupe broken: expected $0.15, got {row['cost_usd']!r}. "
        f"If you see $0.25 the ``model.completed`` sibling is being "
        f"counted alongside its ``assistant`` twin."
    )
    assert row["token_count"] == 1500, (
        f"sibling-pair dedupe broken on tokens: expected 1500, "
        f"got {row['token_count']!r}"
    )


# ──────────────────────────────────────────────────────────────────────
# Issue #1755 — isolation: events for sub-agent A don't bleed into B
# ──────────────────────────────────────────────────────────────────────

def test_query_subagents_does_not_cross_pollinate_between_subagents(store):
    """Two children of the same parent, each with their own events. The
    SUMs must be scoped to each child's ``subagent_id``."""
    parent_sid = "parent-isolated"
    sid_a = "child-A"
    sid_b = "child-B"
    store.ingest_subagent({
        "subagent_id":       sid_a, "agent_type": "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-19T09:30:00Z",
        "status":            "completed",
        "cost_usd": 0.0, "token_count": 0,
    })
    store.ingest_subagent({
        "subagent_id":       sid_b, "agent_type": "openclaw",
        "parent_session_id": parent_sid,
        "spawned_at":        "2026-05-19T09:30:01Z",
        "status":            "completed",
        "cost_usd": 0.0, "token_count": 0,
    })
    _ingest_token_event(store, sid_a, tokens=999, cost=0.11,
                        ts="2026-05-19T09:30:02Z")
    _ingest_token_event(store, sid_b, tokens=222, cost=0.04,
                        ts="2026-05-19T09:30:03Z")
    _wait(store)

    row_a = _get_subagent(store, sid_a)
    row_b = _get_subagent(store, sid_b)
    assert row_a["cost_usd"] == pytest.approx(0.11, abs=1e-6)
    assert row_a["token_count"] == 999
    assert row_b["cost_usd"] == pytest.approx(0.04, abs=1e-6)
    assert row_b["token_count"] == 222
