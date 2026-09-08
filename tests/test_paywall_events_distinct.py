"""Store-level tests for the paywall-event distinct-values helper:

  ``clawmetry._paywall_events.distinct_values``
  ``clawmetry._paywall_events._PaywallEventStore.distinct_values``

Categorical dropdown-population sibling of ``summary`` / ``recent`` /
``count_matching`` -- returns the sorted set of distinct non-empty
values per categorical dimension currently in the ring (post-filter,
post-window). Anchored to the SAME filter + window semantics as the
rest of the store, and pinned against ``summary``'s ``by_*`` keys so
the two views cannot silently drift.

Store-level tests here pin:

* Envelope shape and always-present keys.
* Sorted, deduplicated, non-empty-only per-dimension lists.
* Categorical filters narrow BEFORE the distinct set is computed
  (drives "further narrow by:" dropdown UX).
* Time-window semantics (half-open ``[since, until)``, bad bounds
  collapse to unbounded).
* Parity with :meth:`summary` -- per-dimension keys match by_* keys
  byte-for-byte on identical filter + window inputs.
* Never-raises posture on a broken store.

HTTP shape tests live in ``test_paywall_events_distinct_api.py`` and
should stay independent so a route-only regression cannot silently
break the store contract.
"""
from __future__ import annotations

import pytest


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def store():
    """A fresh in-process store, isolated per test."""
    from clawmetry import _paywall_events as pe

    pe.reset()
    yield pe
    pe.reset()


@pytest.fixture
def clock(monkeypatch):
    """Deterministic clock so tests can pin exact ``since`` / ``until``
    boundaries."""
    from clawmetry import _paywall_events as pe

    box = {"now": 1_000_000.0}
    monkeypatch.setattr(pe.time, "time", lambda: box["now"])
    return box


def _rec(store, **fields):
    store.record_event(fields)


def _rec_at(store, clock, ts, **fields):
    clock["now"] = float(ts)
    store.record_event(fields)


# ── envelope shape ─────────────────────────────────────────────────────────


def test_distinct_empty_ring_returns_neutral_envelope(store):
    body = store.distinct_values()
    assert body == {
        "distinct": {
            "event": [],
            "feature": [],
            "harness": [],
            "source": [],
            "plan_chosen": [],
        },
        "in_window": 0,
        "matched": 0,
        "filters": {},
        "time_window": {"since": None, "until": None},
    }


def test_distinct_envelope_always_carries_top_level_keys(store):
    _rec(store, event="paywall_view", feature="fleet")
    body = store.distinct_values()
    assert set(body.keys()) == {
        "distinct", "in_window", "matched", "filters", "time_window",
    }
    assert set(body["distinct"].keys()) == {
        "event", "feature", "harness", "source", "plan_chosen",
    }


# ── unfiltered semantics ───────────────────────────────────────────────────


def test_distinct_unfiltered_returns_sorted_uniques(store):
    _rec(store, event="paywall_view", feature="fleet")
    _rec(store, event="paywall_cta_click", feature="anomaly_detection")
    _rec(store, event="paywall_view", feature="fleet")  # dup

    body = store.distinct_values()
    assert body["distinct"]["event"] == [
        "paywall_cta_click", "paywall_view",  # sorted ascending
    ]
    assert body["distinct"]["feature"] == ["anomaly_detection", "fleet"]
    assert body["in_window"] == 3
    assert body["matched"] == 3
    assert body["filters"] == {}


def test_distinct_excludes_empty_string_values(store):
    """A row that only carries ``event`` must NOT contribute an empty
    string to the other dimensions -- matches :meth:`summary`'s
    ``by_*`` posture (empty keys are excluded)."""
    _rec(store, event="paywall_view")  # every other field empty
    _rec(store, event="paywall_view", feature="fleet")

    body = store.distinct_values()
    assert body["distinct"]["event"] == ["paywall_view"]
    assert body["distinct"]["feature"] == ["fleet"]
    # No empty strings anywhere.
    for values in body["distinct"].values():
        assert "" not in values


def test_distinct_all_five_dimensions_populate(store):
    _rec(
        store,
        event="paywall_cta_click",
        feature="self_evolve",
        harness="claude_code",
        source="banner",
        plan_chosen="cloud_pro",
    )
    _rec(
        store,
        event="paywall_view",
        feature="fleet",
        harness="codex",
        source="tile",
        plan_chosen="cloud_starter",
    )
    body = store.distinct_values()
    assert body["distinct"] == {
        "event": ["paywall_cta_click", "paywall_view"],
        "feature": ["fleet", "self_evolve"],
        "harness": ["claude_code", "codex"],
        "source": ["banner", "tile"],
        "plan_chosen": ["cloud_pro", "cloud_starter"],
    }


def test_distinct_sort_is_case_sensitive_string_order(store):
    """Sort is Python's default string sort -- uppercase < lowercase.
    Pinned so a later locale-collation refactor cannot silently
    reorder dropdown options."""
    for name in ("banana", "Apple", "cherry"):
        _rec(store, event="paywall_view", feature=name)
    body = store.distinct_values()
    assert body["distinct"]["feature"] == ["Apple", "banana", "cherry"]


def test_distinct_unfiltered_matched_equals_in_window(store):
    for i in range(5):
        _rec(store, event="paywall_view", feature=f"f{i}")
    body = store.distinct_values()
    assert body["matched"] == body["in_window"] == 5


# ── categorical filters ────────────────────────────────────────────────────


def test_distinct_filter_narrows_before_distinct_set(store):
    """Filters run BEFORE the distinct set is computed, so the returned
    ``feature`` list is only those features that co-occur with the
    filter -- drives the "further narrow by:" dropdown UX."""
    _rec(store, event="paywall_view", feature="fleet")
    _rec(store, event="paywall_view", feature="anomaly")
    _rec(store, event="paywall_cta_click", feature="self_evolve")

    body = store.distinct_values(event="paywall_view")
    assert body["distinct"]["feature"] == ["anomaly", "fleet"]  # NOT self_evolve
    assert body["distinct"]["event"] == ["paywall_view"]
    assert body["matched"] == 2
    assert body["in_window"] == 3  # ring unaffected
    assert body["filters"] == {"event": "paywall_view"}


def test_distinct_filter_no_match_returns_empty_but_nonzero_in_window(store):
    _rec(store, event="paywall_view", feature="fleet")
    body = store.distinct_values(event="not_a_real_event")
    for values in body["distinct"].values():
        assert values == []
    assert body["matched"] == 0
    assert body["in_window"] == 1
    assert body["filters"] == {"event": "not_a_real_event"}


def test_distinct_blank_filter_is_not_supplied(store):
    _rec(store, event="paywall_view", feature="fleet")
    body = store.distinct_values(event="", feature="  ")
    assert body["filters"] == {}
    assert body["distinct"]["feature"] == ["fleet"]
    assert body["matched"] == 1


def test_distinct_combines_filters_with_and(store):
    _rec(store, event="paywall_view", feature="fleet", harness="claude_code")
    _rec(store, event="paywall_view", feature="fleet", harness="codex")
    _rec(store, event="paywall_cta_click", feature="fleet", harness="claude_code")

    body = store.distinct_values(event="paywall_view", feature="fleet")
    assert body["distinct"]["harness"] == ["claude_code", "codex"]
    assert body["matched"] == 2
    assert body["filters"] == {"event": "paywall_view", "feature": "fleet"}


# ── time-window semantics ──────────────────────────────────────────────────


def test_distinct_time_window_echoes_resolved_bounds(store, clock):
    _rec_at(store, clock, 100.0, event="paywall_view", feature="a")
    _rec_at(store, clock, 200.0, event="paywall_view", feature="b")

    body = store.distinct_values(since=150, until=250)
    assert body["distinct"]["feature"] == ["b"]
    assert body["matched"] == 1
    assert body["time_window"] == {"since": 150.0, "until": 250.0}


def test_distinct_since_is_inclusive_until_is_exclusive(store, clock):
    _rec_at(store, clock, 100.0, event="paywall_view", feature="a")
    _rec_at(store, clock, 101.0, event="paywall_view", feature="b")

    # since=100 includes ts=100.
    body = store.distinct_values(since=100)
    assert body["distinct"]["feature"] == ["a", "b"]

    # until=101 excludes ts=101.
    body = store.distinct_values(until=101)
    assert body["distinct"]["feature"] == ["a"]


def test_distinct_bad_bounds_collapse_to_unbounded(store, clock):
    _rec_at(store, clock, 100.0, event="paywall_view", feature="a")
    _rec_at(store, clock, 200.0, event="paywall_view", feature="b")

    body = store.distinct_values(since="junk", until="nan")
    assert body["distinct"]["feature"] == ["a", "b"]  # unbounded => full ring
    assert body["time_window"] == {"since": None, "until": None}


def test_distinct_empty_window_matches_nothing(store, clock):
    _rec_at(store, clock, 100.0, event="paywall_view", feature="f")
    body = store.distinct_values(since=200, until=200)
    for values in body["distinct"].values():
        assert values == []
    assert body["matched"] == 0
    assert body["in_window"] == 1
    assert body["time_window"] == {"since": 200.0, "until": 200.0}


def test_distinct_window_and_categorical_filter_combine(store, clock):
    _rec_at(store, clock, 100.0, event="paywall_view",      feature="fleet")
    _rec_at(store, clock, 200.0, event="paywall_cta_click", feature="fleet")
    _rec_at(store, clock, 300.0, event="paywall_cta_click", feature="anomaly")

    body = store.distinct_values(
        event="paywall_cta_click", since=150, until=250,
    )
    assert body["distinct"]["feature"] == ["fleet"]
    assert body["matched"] == 1
    assert body["filters"] == {"event": "paywall_cta_click"}
    assert body["time_window"] == {"since": 150.0, "until": 250.0}


# ── cross-view parity with summary() ───────────────────────────────────────


def test_distinct_matches_summary_by_star_keys_unfiltered(store):
    """The five per-dimension distinct lists byte-equal the sorted keys
    of :meth:`summary`'s ``by_*`` dicts for the same inputs -- pinned
    so a caller can trust the two views agree on which dropdown
    options are live."""
    _rec(
        store,
        event="paywall_view", feature="fleet",
        harness="claude_code", source="banner", plan_chosen="cloud_pro",
    )
    _rec(
        store,
        event="paywall_cta_click", feature="anomaly",
        harness="codex", source="tile", plan_chosen="cloud_starter",
    )
    _rec(
        store,
        event="paywall_view", feature="fleet",
        harness="claude_code", source="banner", plan_chosen="cloud_pro",
    )

    distinct = store.distinct_values()["distinct"]
    summary = store.summary()
    for dim, by_key in (
        ("event", "by_event"),
        ("feature", "by_feature"),
        ("harness", "by_harness"),
        ("source", "by_source"),
        ("plan_chosen", "by_plan_chosen"),
    ):
        assert distinct[dim] == sorted(summary[by_key].keys()), dim


def test_distinct_matches_summary_by_star_keys_with_filter(store):
    _rec(store, event="paywall_view", feature="fleet")
    _rec(store, event="paywall_view", feature="anomaly")
    _rec(store, event="paywall_cta_click", feature="self_evolve")

    distinct = store.distinct_values(event="paywall_view")["distinct"]
    summary = store.summary(event="paywall_view")
    assert distinct["feature"] == sorted(summary["by_feature"].keys())
    assert distinct["event"] == sorted(summary["by_event"].keys())


def test_distinct_matched_equals_summary_matched(store, clock):
    for ts, feature in (
        (100.0, "fleet"), (110.0, "fleet"),
        (120.0, "anomaly"), (200.0, "fleet"),
    ):
        _rec_at(store, clock, ts, event="paywall_view", feature=feature)

    distinct = store.distinct_values(feature="fleet", since=100, until=200)
    summary = store.summary(feature="fleet", since=100, until=200)
    assert distinct["matched"] == summary["matched"]


# ── never-raise ────────────────────────────────────────────────────────────


def test_distinct_never_raises_on_broken_ring(store, monkeypatch):
    """A store-internal explosion falls back to the neutral envelope,
    never propagating -- pins the never-raise posture that the
    ``/api/paywall/events/distinct`` route relies on to stay 200."""
    _rec(store, event="paywall_view", feature="fleet")

    # Force the lock acquisition inside distinct_values to blow up.
    class _BoomLock:
        def __enter__(self):
            raise RuntimeError("simulated lock outage")

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(store._STORE, "_lock", _BoomLock())
    body = store.distinct_values()
    assert body == {
        "distinct": {
            "event": [], "feature": [], "harness": [],
            "source": [], "plan_chosen": [],
        },
        "in_window": 0,
        "matched": 0,
        "filters": {},
        "time_window": {"since": None, "until": None},
    }
