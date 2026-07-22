"""Unit tests for :mod:`clawmetry._paywall_events` -- the in-process
rolling store for ``POST /api/paywall/event`` client beacons.

The store is the ONLY place that persists paywall pings between requests.
The two HTTP endpoints (``/api/paywall/events/summary`` +
``/api/paywall/events/recent``) are thin JSON wrappers around it, so its
invariants -- boundedness, truncation, never-raise, thread-safety,
monotonic totals -- are what actually protect the operator surface.
Nail them here so a future refactor of the module cannot silently
regress the wrapping endpoints.
"""
from __future__ import annotations

import threading

import pytest


@pytest.fixture(autouse=True)
def _fresh_store():
    """Reset the module-level singleton before each test so per-test writes
    can't leak into each other -- the store is process-scoped so pytest
    would otherwise carry state across the file."""
    from clawmetry import _paywall_events as pe

    pe.reset()
    yield
    pe.reset()


# ── record + summary happy path ─────────────────────────────────────────────


def test_summary_starts_empty():
    from clawmetry import _paywall_events as pe

    s = pe.summary()
    assert s["total"] == 0
    assert s["in_window"] == 0
    assert s["dropped"] == 0
    assert s["capacity"] >= 1
    assert s["first_ts"] is None
    assert s["last_ts"] is None
    assert s["by_event"] == {}
    assert s["by_feature"] == {}
    assert s["by_harness"] == {}
    assert s["by_source"] == {}
    assert s["by_plan_chosen"] == {}


def test_record_single_event_appears_in_summary_aggregations():
    from clawmetry import _paywall_events as pe

    pe.record_event(
        {
            "event": "paywall_view",
            "feature": "self_evolve",
            "harness": "claude_code",
            "source": "runtime-switcher",
        }
    )
    s = pe.summary()
    assert s["total"] == 1
    assert s["in_window"] == 1
    assert s["dropped"] == 0
    assert s["by_event"] == {"paywall_view": 1}
    assert s["by_feature"] == {"self_evolve": 1}
    assert s["by_harness"] == {"claude_code": 1}
    assert s["by_source"] == {"runtime-switcher": 1}
    assert s["by_plan_chosen"] == {}  # no plan on a view
    assert s["first_ts"] is not None
    assert s["last_ts"] is not None
    assert s["first_ts"] <= s["last_ts"]


def test_record_cta_click_captures_plan_chosen():
    from clawmetry import _paywall_events as pe

    pe.record_event(
        {
            "event": "paywall_cta_click",
            "harness": "codex",
            "source": "runtime-switcher",
            "plan_chosen": "pro",
        }
    )
    s = pe.summary()
    assert s["by_event"] == {"paywall_cta_click": 1}
    assert s["by_plan_chosen"] == {"pro": 1}


def test_summary_aggregates_per_dimension_across_events():
    from clawmetry import _paywall_events as pe

    for _ in range(3):
        pe.record_event({"event": "paywall_view", "feature": "fleet"})
    for _ in range(2):
        pe.record_event({"event": "paywall_view", "feature": "self_evolve"})
    pe.record_event({"event": "paywall_cta_click", "plan_chosen": "pro"})

    s = pe.summary()
    assert s["total"] == 6
    assert s["in_window"] == 6
    assert s["by_event"] == {"paywall_view": 5, "paywall_cta_click": 1}
    assert s["by_feature"] == {"fleet": 3, "self_evolve": 2}
    assert s["by_plan_chosen"] == {"pro": 1}


def test_empty_dimension_values_are_not_bucketed():
    """A payload with an empty string on one axis (e.g. no ``feature`` on
    a paywall_view) must NOT bucket into ``by_feature[""]`` -- else every
    field's tally would be dominated by an empty bucket the operator
    cannot act on."""
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "harness": "claude_code"})
    s = pe.summary()
    assert s["by_event"] == {"paywall_view": 1}
    assert s["by_harness"] == {"claude_code": 1}
    assert s["by_feature"] == {}
    assert s["by_source"] == {}
    assert s["by_plan_chosen"] == {}


# ── truncation parity with the route ────────────────────────────────────────


def test_event_field_truncated_to_64_chars():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "e" * 200})
    s = pe.summary()
    key = next(iter(s["by_event"]))
    assert len(key) == 64
    assert key == "e" * 64


def test_feature_field_truncated_to_128_chars():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "f" * 300})
    s = pe.summary()
    key = next(iter(s["by_feature"]))
    assert len(key) == 128


def test_harness_source_plan_truncated_to_64_chars():
    from clawmetry import _paywall_events as pe

    pe.record_event(
        {
            "event": "paywall_view",
            "harness": "h" * 200,
            "source": "s" * 200,
            "plan_chosen": "p" * 200,
        }
    )
    s = pe.summary()
    assert len(next(iter(s["by_harness"]))) == 64
    assert len(next(iter(s["by_source"]))) == 64
    assert len(next(iter(s["by_plan_chosen"]))) == 64


# ── never-raise contract ────────────────────────────────────────────────────


def test_non_dict_payload_still_records_a_beat():
    """A list / string / None body must not raise and must still bump the
    total so the operator can see "beacons are firing but the client
    is malformed"."""
    from clawmetry import _paywall_events as pe

    pe.record_event(["not", "a", "dict"])
    pe.record_event("scalar")
    pe.record_event(None)
    s = pe.summary()
    assert s["total"] == 3
    # No fields to bucket, so per-key dicts are empty.
    assert s["by_event"] == {}
    assert s["by_feature"] == {}


def test_non_string_field_values_do_not_raise():
    """The route already ``str(body.get(k, ""))`` -- the store must do the
    same so an int / list / dict field coerces without raising."""
    from clawmetry import _paywall_events as pe

    pe.record_event(
        {
            "event": 42,
            "feature": ["self_evolve"],
            "harness": {"name": "claude_code"},
            "source": None,
            "plan_chosen": 3.14,
        }
    )
    s = pe.summary()
    assert s["total"] == 1
    assert s["in_window"] == 1


# ── ring boundedness + monotonic counters ───────────────────────────────────


def test_ring_capacity_is_bounded_and_evicts_oldest():
    from clawmetry import _paywall_events as pe

    pe._set_capacity(5)
    try:
        for i in range(8):
            pe.record_event({"event": f"e{i}"})
        s = pe.summary()
        assert s["capacity"] == 5
        assert s["in_window"] == 5
        assert s["total"] == 8
        assert s["dropped"] == 3
        # Only the last 5 events survive the ring.
        assert set(s["by_event"].keys()) == {"e3", "e4", "e5", "e6", "e7"}
    finally:
        pe._set_capacity(200)


def test_total_and_dropped_are_monotonic_across_many_writes():
    from clawmetry import _paywall_events as pe

    pe._set_capacity(3)
    try:
        for i in range(10):
            pe.record_event({"event": f"e{i}"})
        s = pe.summary()
        assert s["total"] == 10
        assert s["dropped"] == 7
        assert s["in_window"] == 3
    finally:
        pe._set_capacity(200)


def test_reset_clears_ring_and_counters():
    from clawmetry import _paywall_events as pe

    for _ in range(4):
        pe.record_event({"event": "paywall_view"})
    pe.reset()
    s = pe.summary()
    assert s["total"] == 0
    assert s["dropped"] == 0
    assert s["in_window"] == 0
    assert s["first_ts"] is None
    assert s["last_ts"] is None
    assert s["by_event"] == {}


def test_resize_shrinks_and_records_dropped():
    from clawmetry import _paywall_events as pe

    for i in range(10):
        pe.record_event({"event": f"e{i}"})
    pe._set_capacity(3)
    try:
        s = pe.summary()
        assert s["capacity"] == 3
        assert s["in_window"] == 3
        # 10 recorded, 3 remain -> 7 evicted overall.
        assert s["dropped"] == 7
        assert set(s["by_event"].keys()) == {"e7", "e8", "e9"}
    finally:
        pe._set_capacity(200)


def test_resize_clamps_to_bounds():
    from clawmetry import _paywall_events as pe

    pe._set_capacity(999_999_999)
    try:
        assert pe.capacity() == 5000
    finally:
        pe._set_capacity(200)

    pe._set_capacity(-42)
    try:
        assert pe.capacity() == 1
    finally:
        pe._set_capacity(200)


# ── recent() ordering + clamping ────────────────────────────────────────────


def test_recent_returns_newest_first():
    from clawmetry import _paywall_events as pe

    for i in range(4):
        pe.record_event({"event": f"e{i}"})
    got = pe.recent(10)
    assert [e["event"] for e in got] == ["e3", "e2", "e1", "e0"]


def test_recent_respects_limit():
    from clawmetry import _paywall_events as pe

    for i in range(4):
        pe.record_event({"event": f"e{i}"})
    got = pe.recent(2)
    assert [e["event"] for e in got] == ["e3", "e2"]


def test_recent_clamps_bad_limits_to_default():
    from clawmetry import _paywall_events as pe

    for i in range(3):
        pe.record_event({"event": f"e{i}"})
    # Negative -> default; non-int -> default; huge -> hard cap.
    assert len(pe.recent(-5)) == 3
    assert len(pe.recent("garbage")) == 3
    assert len(pe.recent(10_000_000)) == 3


def test_recent_zero_returns_empty():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view"})
    assert pe.recent(0) == []


def test_recent_returns_dicts_with_all_fields_and_ts():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    got = pe.recent(1)
    assert len(got) == 1
    row = got[0]
    for key in ("event", "feature", "harness", "source", "plan_chosen", "ts"):
        assert key in row
    assert row["event"] == "paywall_view"
    assert row["feature"] == "fleet"
    assert isinstance(row["ts"], float)


def test_recent_never_leaks_internal_state():
    """The store hands back COPIES of its rows so a caller mutating the
    returned list can't corrupt the ring."""
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    got = pe.recent(1)
    got[0]["feature"] = "TAMPERED"
    got2 = pe.recent(1)
    assert got2[0]["feature"] == "fleet"


# ── thread-safety smoke test ────────────────────────────────────────────────


def test_concurrent_record_writes_all_counted():
    """The store must not drop writes under N threads all appending
    simultaneously -- ``total`` is the ground truth. ``in_window`` is
    capped by ring capacity so we don't check it here.
    """
    from clawmetry import _paywall_events as pe

    n_threads = 16
    per_thread = 250

    def _writer():
        for _ in range(per_thread):
            pe.record_event({"event": "paywall_view", "feature": "fleet"})

    threads = [threading.Thread(target=_writer) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    s = pe.summary()
    assert s["total"] == n_threads * per_thread
    # Everything past capacity should be in dropped.
    assert s["in_window"] <= s["capacity"]
    assert s["total"] == s["in_window"] + s["dropped"]


# ── capacity env resolution ─────────────────────────────────────────────────


def test_resolve_capacity_default_when_env_missing(monkeypatch):
    from clawmetry import _paywall_events as pe

    monkeypatch.delenv("CLAWMETRY_PAYWALL_EVENT_CAPACITY", raising=False)
    assert pe._resolve_capacity() == 200


def test_resolve_capacity_reads_env(monkeypatch):
    from clawmetry import _paywall_events as pe

    monkeypatch.setenv("CLAWMETRY_PAYWALL_EVENT_CAPACITY", "42")
    assert pe._resolve_capacity() == 42


def test_resolve_capacity_clamps_low(monkeypatch):
    from clawmetry import _paywall_events as pe

    monkeypatch.setenv("CLAWMETRY_PAYWALL_EVENT_CAPACITY", "0")
    assert pe._resolve_capacity() == 1


def test_resolve_capacity_clamps_high(monkeypatch):
    from clawmetry import _paywall_events as pe

    monkeypatch.setenv("CLAWMETRY_PAYWALL_EVENT_CAPACITY", "1000000")
    assert pe._resolve_capacity() == 5000


def test_resolve_capacity_falls_back_on_bad_value(monkeypatch):
    from clawmetry import _paywall_events as pe

    monkeypatch.setenv("CLAWMETRY_PAYWALL_EVENT_CAPACITY", "not-a-number")
    assert pe._resolve_capacity() == 200
