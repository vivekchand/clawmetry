"""Unit tests for :func:`clawmetry._paywall_events.first_matching` and
:func:`clawmetry._paywall_events.last_matching` -- the scalar (dict-or-
``None``) siblings of :func:`clawmetry._paywall_events.recent`.

Both are thin filtered walks over the ring. The store-level invariants
they inherit (thread-safe snapshot, filter parsing, never-raise, copy-
on-return) live in ``test_paywall_events_store.py``; the tests here
pin the return-shape and short-circuit contract that a paywall
dashboard tile binding "last CTA click for feature X" depends on.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _fresh_store():
    from clawmetry import _paywall_events as pe

    pe.reset()
    yield
    pe.reset()


def test_last_matching_empty_ring_returns_none():
    from clawmetry import _paywall_events as pe

    assert pe.last_matching() is None
    assert pe.last_matching(event="paywall_view") is None


def test_first_matching_empty_ring_returns_none():
    from clawmetry import _paywall_events as pe

    assert pe.first_matching() is None
    assert pe.first_matching(feature="fleet") is None


def test_last_matching_with_no_filters_returns_newest_row():
    from clawmetry import _paywall_events as pe

    for i in range(3):
        pe.record_event({"event": f"e{i}", "feature": "fleet"})
    row = pe.last_matching()
    assert row is not None
    assert row["event"] == "e2"
    assert row["feature"] == "fleet"


def test_first_matching_with_no_filters_returns_oldest_row():
    from clawmetry import _paywall_events as pe

    for i in range(3):
        pe.record_event({"event": f"e{i}", "feature": "fleet"})
    row = pe.first_matching()
    assert row is not None
    assert row["event"] == "e0"


def test_last_matching_respects_categorical_filter():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    pe.record_event({"event": "paywall_cta_click", "feature": "fleet"})
    pe.record_event({"event": "paywall_view", "feature": "self_evolve"})

    row = pe.last_matching(event="paywall_view")
    assert row is not None
    assert row["event"] == "paywall_view"
    assert row["feature"] == "self_evolve"  # newest paywall_view


def test_first_matching_respects_categorical_filter():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    pe.record_event({"event": "paywall_cta_click", "feature": "fleet"})
    pe.record_event({"event": "paywall_view", "feature": "self_evolve"})

    row = pe.first_matching(event="paywall_view")
    assert row is not None
    assert row["event"] == "paywall_view"
    assert row["feature"] == "fleet"  # oldest paywall_view


def test_last_matching_combines_filters_with_and():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    pe.record_event({"event": "paywall_view", "feature": "self_evolve"})
    pe.record_event({"event": "paywall_cta_click", "feature": "fleet"})

    row = pe.last_matching(event="paywall_view", feature="fleet")
    assert row is not None
    assert row["event"] == "paywall_view"
    assert row["feature"] == "fleet"


def test_first_matching_combines_filters_with_and():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    pe.record_event({"event": "paywall_view", "feature": "self_evolve"})
    pe.record_event({"event": "paywall_view", "feature": "fleet"})

    row = pe.first_matching(event="paywall_view", feature="fleet")
    assert row is not None
    assert row["feature"] == "fleet"


def test_last_matching_no_match_returns_none():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    assert pe.last_matching(feature="nonexistent") is None
    assert pe.last_matching(event="not_a_real_event") is None


def test_first_matching_no_match_returns_none():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    assert pe.first_matching(feature="nonexistent") is None


def test_last_matching_returns_all_fields():
    from clawmetry import _paywall_events as pe

    pe.record_event(
        {
            "event": "paywall_cta_click",
            "feature": "self_evolve",
            "harness": "claude_code",
            "source": "runtime-switcher",
            "plan_chosen": "pro",
        }
    )
    row = pe.last_matching()
    assert row is not None
    for key in ("event", "feature", "harness", "source", "plan_chosen", "ts"):
        assert key in row
    assert row["plan_chosen"] == "pro"
    assert isinstance(row["ts"], float)


def test_first_matching_returns_all_fields():
    from clawmetry import _paywall_events as pe

    pe.record_event(
        {
            "event": "paywall_view",
            "feature": "fleet",
            "harness": "openclaw",
            "source": "empty-state",
            "plan_chosen": "",
        }
    )
    row = pe.first_matching()
    assert row is not None
    for key in ("event", "feature", "harness", "source", "plan_chosen", "ts"):
        assert key in row


def test_last_matching_hands_back_a_copy():
    """Callers mutating the returned dict must not corrupt the ring --
    parity with ``recent`` / ``count_matching``.
    """
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    row = pe.last_matching()
    assert row is not None
    row["feature"] = "TAMPERED"
    row2 = pe.last_matching()
    assert row2 is not None
    assert row2["feature"] == "fleet"


def test_first_matching_hands_back_a_copy():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    row = pe.first_matching()
    assert row is not None
    row["feature"] = "TAMPERED"
    row2 = pe.first_matching()
    assert row2 is not None
    assert row2["feature"] == "fleet"


def test_last_matching_ignores_blank_and_none_filters():
    """A blank / ``None`` filter is "not supplied" -- same as
    :func:`recent` / :func:`count_matching`."""
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    # Empty string and None both mean "unfiltered on that axis".
    row1 = pe.last_matching(event="", feature=None)
    row2 = pe.last_matching()
    assert row1 == row2
    assert row1 is not None


def test_first_matching_ignores_blank_and_none_filters():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    row1 = pe.first_matching(event="", feature=None)
    row2 = pe.first_matching()
    assert row1 == row2
    assert row1 is not None


def test_last_matching_reflects_ring_eviction():
    """After the ring evicts the newest oldest row, ``last_matching``
    still points at the newest resident row -- not something evicted.
    """
    from clawmetry import _paywall_events as pe

    pe._set_capacity(3)
    try:
        for i in range(6):
            pe.record_event({"event": "paywall_view", "feature": f"f{i}"})
        row = pe.last_matching()
        assert row is not None
        assert row["feature"] == "f5"
    finally:
        pe._set_capacity(200)


def test_first_matching_reflects_ring_eviction():
    """After eviction ``first_matching`` returns the oldest RESIDENT
    row, not the all-time first (which has been evicted)."""
    from clawmetry import _paywall_events as pe

    pe._set_capacity(3)
    try:
        for i in range(6):
            pe.record_event({"event": "paywall_view", "feature": f"f{i}"})
        row = pe.first_matching()
        assert row is not None
        # After 6 records with capacity 3, oldest resident is f3.
        assert row["feature"] == "f3"
    finally:
        pe._set_capacity(200)


def test_last_and_first_match_when_ring_has_one_row():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    assert pe.last_matching() == pe.first_matching()


def test_last_matching_agrees_with_recent_limit_one():
    """``last_matching`` is the scalar unwrap of ``recent(1)`` --
    same row, same fields, minus the list wrapper.
    """
    from clawmetry import _paywall_events as pe

    for i in range(5):
        pe.record_event({"event": f"e{i}", "feature": "fleet"})
    listed = pe.recent(1)
    scalar = pe.last_matching()
    assert scalar == listed[0]


def test_last_matching_filter_agrees_with_recent_filter():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    pe.record_event({"event": "paywall_cta_click", "feature": "fleet"})
    pe.record_event({"event": "paywall_view", "feature": "self_evolve"})
    listed = pe.recent(1, event="paywall_view")
    scalar = pe.last_matching(event="paywall_view")
    assert scalar == listed[0]
