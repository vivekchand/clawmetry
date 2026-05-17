"""Tests for the NeMo free-tier daily ingest cap (issue #1170).

PR #1154 shipped the NeMo adapter that mirrors NVIDIA NeMo Agent Toolkit
telemetry into the local DuckDB. NeMo users are our highest-value paid-
conversion segment, so the OSS adapter caps free ingest at
``NEMO_FREE_DAILY_CAP`` events per UTC day. Pro users bypass the cap.

These tests use a fake in-memory store (no DuckDB) so they run fast and
deterministically — the adapter's contract with the store is just
``store.ingest(row)``.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _RecordingStore:
    """Minimal stand-in for clawmetry.local_store.LocalStore."""

    def __init__(self) -> None:
        self.rows: list[dict] = []

    def ingest(self, row: dict) -> None:
        self.rows.append(row)


def _make_event(i: int) -> dict:
    return {
        "event_type": "LLM_END",
        "trace_id": f"trace-{i}",
        "span_id": f"span-{i}",
        "attributes": {
            "model": "claude-3.5-sonnet",
            "completion": "x",
            "input_tokens": 1,
            "output_tokens": 1,
        },
    }


@pytest.fixture
def fresh_adapter(monkeypatch):
    """Adapter + store with cap state reset; Pro=False by default."""
    from clawmetry.adapters import nemo as nemo_mod

    nemo_mod._reset_cap_state_for_tests()
    monkeypatch.setattr(nemo_mod, "_is_pro", lambda: False)

    store = _RecordingStore()
    adapter = nemo_mod.NeMoAdapter(store, node_id="t", agent_id="t")
    return adapter, store, nemo_mod


# ---------------------------------------------------------------------------
# Cap-state contract
# ---------------------------------------------------------------------------


def test_cap_constant_is_1000():
    from clawmetry.adapters.nemo import NEMO_FREE_DAILY_CAP
    assert NEMO_FREE_DAILY_CAP == 1000


def test_cap_state_shape(fresh_adapter):
    _adapter, _store, nemo_mod = fresh_adapter
    snap = nemo_mod.get_nemo_cap_state()
    assert set(snap.keys()) >= {"cap", "used", "dropped", "is_pro", "cap_hit", "date"}
    assert snap["cap"] == 1000
    assert snap["used"] == 0
    assert snap["dropped"] == 0
    assert snap["is_pro"] is False
    assert snap["cap_hit"] is False


# ---------------------------------------------------------------------------
# Free-tier cap behaviour
# ---------------------------------------------------------------------------


def test_free_user_capped_at_1000(fresh_adapter, caplog):
    """Free user fires 5000 events -> first 1000 ingested, 4000 dropped."""
    adapter, store, nemo_mod = fresh_adapter
    caplog.set_level("WARNING", logger="clawmetry.adapters.nemo")

    rows_returned = 0
    for i in range(5000):
        r = adapter.on_event(_make_event(i))
        if r is not None:
            rows_returned += 1

    assert rows_returned == 1000, "exactly 1000 events should be accepted"
    assert len(store.rows) == 1000, "store should hold exactly 1000 ingested rows"

    snap = nemo_mod.get_nemo_cap_state()
    assert snap["used"] == 1000
    assert snap["dropped"] == 4000
    assert snap["cap_hit"] is True
    assert snap["is_pro"] is False

    # Warning logged ONCE per day, not 4000 times.
    cap_warnings = [r for r in caplog.records if "daily cap reached" in r.message]
    assert len(cap_warnings) == 1, f"expected one cap warning, got {len(cap_warnings)}"


def test_pro_user_unlimited(fresh_adapter, monkeypatch):
    """Pro user fires 5000 events -> all 5000 ingested."""
    adapter, store, nemo_mod = fresh_adapter
    monkeypatch.setattr(nemo_mod, "_is_pro", lambda: True)

    for i in range(5000):
        adapter.on_event(_make_event(i))

    assert len(store.rows) == 5000

    snap = nemo_mod.get_nemo_cap_state()
    assert snap["used"] == 5000
    assert snap["dropped"] == 0
    assert snap["is_pro"] is True
    # cap_hit is Pro-aware: never true for a Pro caller, even at 5000>>1000.
    assert snap["cap_hit"] is False


def test_counter_resets_at_day_boundary(fresh_adapter):
    """Cap counter resets when the UTC date changes."""
    adapter, store, nemo_mod = fresh_adapter

    # Manually shove yesterday's state into place and trip the cap.
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    nemo_mod._CAP_STATE["date"] = yesterday
    nemo_mod._CAP_STATE["count"] = 1000
    nemo_mod._CAP_STATE["dropped"] = 500
    nemo_mod._CAP_STATE["warned"] = True

    # First call on the new day rolls the bucket over and ingests.
    r = adapter.on_event(_make_event(0))
    assert r is not None, "first event on a new day should be accepted"
    assert len(store.rows) == 1

    snap = nemo_mod.get_nemo_cap_state()
    assert snap["date"] == date.today().isoformat()
    assert snap["used"] == 1
    assert snap["dropped"] == 0
    assert snap["cap_hit"] is False


def test_dropped_events_do_not_reach_store(fresh_adapter):
    """The cap check sits BEFORE store.ingest — dropped rows never land."""
    adapter, store, _nemo_mod = fresh_adapter

    for i in range(1500):
        adapter.on_event(_make_event(i))

    # 1500 free attempts -> 1000 ingested, 500 silently dropped.
    assert len(store.rows) == 1000
