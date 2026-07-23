"""Unit + API tests for the ``event`` / ``feature`` / ``harness`` /
``source`` / ``plan_chosen`` query-param filters on
``GET /api/paywall/events/recent`` (and the mirror kwargs on
:func:`clawmetry._paywall_events.recent`).

Store-level invariants for the underlying ring / summary / raw ``recent``
live in ``test_paywall_events_store.py``; envelope invariants for the
unfiltered endpoint live in ``test_paywall_events_api.py``. This file
pins the filter contract:

* A blank / missing filter is "not supplied" and does not restrict on
  that dimension.
* Case-sensitive exact match on the stored (post-``_coerce_str``) value.
* Filters ``AND``-combine across dimensions.
* Filter mismatches never fail the request -- they return an empty
  ``events`` list and ``matched=0``.
* On the API envelope: ``matched`` is the pre-limit total; ``count`` is
  the post-limit returned length; ``filters`` echoes the applied
  filters (blank ones omitted).
* Never 5xxs on a store failure, whether or not filters are supplied.
"""
from __future__ import annotations

import json
import threading

import pytest
from flask import Flask


# ── store-level filter contract ────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _fresh_store():
    from clawmetry import _paywall_events as pe

    pe.reset()
    yield
    pe.reset()


def _seed(events):
    from clawmetry import _paywall_events as pe

    for e in events:
        pe.record_event(e)


def test_recent_no_filter_matches_previous_behaviour():
    from clawmetry import _paywall_events as pe

    _seed([{"event": "paywall_view", "feature": "fleet"} for _ in range(3)])
    # Unfiltered call must be byte-equal to the legacy signature.
    got = pe.recent(10)
    assert len(got) == 3
    assert all(e["event"] == "paywall_view" for e in got)


def test_recent_filter_event_matches_exactly():
    from clawmetry import _paywall_events as pe

    _seed(
        [
            {"event": "paywall_view", "feature": "fleet"},
            {"event": "paywall_cta_click", "feature": "fleet", "plan_chosen": "pro"},
            {"event": "paywall_view", "feature": "self_evolve"},
        ]
    )
    got = pe.recent(10, event="paywall_cta_click")
    assert len(got) == 1
    assert got[0]["event"] == "paywall_cta_click"
    assert got[0]["plan_chosen"] == "pro"


def test_recent_filter_feature_matches_exactly():
    from clawmetry import _paywall_events as pe

    _seed(
        [
            {"event": "paywall_view", "feature": "fleet"},
            {"event": "paywall_view", "feature": "self_evolve"},
            {"event": "paywall_view", "feature": "fleet"},
        ]
    )
    got = pe.recent(10, feature="fleet")
    assert len(got) == 2
    assert {row["feature"] for row in got} == {"fleet"}


def test_recent_filter_harness_and_source_and_plan():
    from clawmetry import _paywall_events as pe

    _seed(
        [
            {
                "event": "paywall_cta_click",
                "feature": "fleet",
                "harness": "claude_code",
                "source": "runtime-switcher",
                "plan_chosen": "pro",
            },
            {
                "event": "paywall_cta_click",
                "feature": "fleet",
                "harness": "codex",
                "source": "runtime-switcher",
                "plan_chosen": "starter",
            },
        ]
    )
    got = pe.recent(10, harness="claude_code")
    assert len(got) == 1
    assert got[0]["harness"] == "claude_code"

    got = pe.recent(10, source="runtime-switcher")
    assert len(got) == 2

    got = pe.recent(10, plan_chosen="pro")
    assert len(got) == 1
    assert got[0]["plan_chosen"] == "pro"


def test_recent_filters_are_and_combined():
    from clawmetry import _paywall_events as pe

    _seed(
        [
            {"event": "paywall_view", "feature": "fleet"},
            {"event": "paywall_cta_click", "feature": "fleet", "plan_chosen": "pro"},
            {"event": "paywall_cta_click", "feature": "self_evolve", "plan_chosen": "pro"},
        ]
    )
    got = pe.recent(10, event="paywall_cta_click", feature="fleet")
    assert len(got) == 1
    assert got[0]["feature"] == "fleet"
    assert got[0]["event"] == "paywall_cta_click"


def test_recent_filter_case_sensitive():
    """The store keeps values verbatim (only truncates); a filter mismatch
    on case must return no rows so the operator sees "no matches" rather
    than a silently loose match."""
    from clawmetry import _paywall_events as pe

    _seed([{"event": "paywall_view", "feature": "Fleet"}])
    assert pe.recent(10, feature="fleet") == []
    assert len(pe.recent(10, feature="Fleet")) == 1


def test_recent_filter_no_matches_returns_empty_list():
    from clawmetry import _paywall_events as pe

    _seed([{"event": "paywall_view", "feature": "fleet"}])
    assert pe.recent(10, feature="does_not_exist") == []


def test_recent_filter_blank_or_none_is_not_supplied():
    from clawmetry import _paywall_events as pe

    _seed(
        [
            {"event": "paywall_view", "feature": "fleet"},
            {"event": "paywall_cta_click", "feature": "self_evolve"},
        ]
    )
    # Both should behave the same as the unfiltered call.
    assert len(pe.recent(10)) == 2
    assert len(pe.recent(10, feature=None)) == 2
    assert len(pe.recent(10, feature="")) == 2
    assert len(pe.recent(10, feature="   ")) == 2


def test_recent_filter_missing_row_field_never_matches():
    """A filter on ``plan_chosen`` should only match rows that actually
    carry a matching plan; a paywall_view without a plan must not
    silently match a ``plan_chosen=`` filter."""
    from clawmetry import _paywall_events as pe

    _seed(
        [
            {"event": "paywall_view", "feature": "fleet"},
            {"event": "paywall_cta_click", "feature": "fleet", "plan_chosen": "pro"},
        ]
    )
    got = pe.recent(10, plan_chosen="pro")
    assert len(got) == 1
    assert got[0]["plan_chosen"] == "pro"


def test_recent_filter_respects_limit_after_filter():
    """The limit clamps the FILTERED list, not the raw ring."""
    from clawmetry import _paywall_events as pe

    for i in range(6):
        pe.record_event({"event": "paywall_view", "feature": "fleet"})
    for _ in range(2):
        pe.record_event({"event": "paywall_cta_click", "feature": "fleet"})
    # 8 total; filter to views -> 6; limit=3 -> 3 rows (newest views).
    got = pe.recent(3, event="paywall_view")
    assert len(got) == 3
    assert all(e["event"] == "paywall_view" for e in got)


def test_recent_filter_preserves_newest_first_ordering():
    from clawmetry import _paywall_events as pe

    for i in range(4):
        pe.record_event({"event": "paywall_view", "feature": f"f{i}"})
        pe.record_event({"event": "paywall_cta_click", "feature": f"f{i}"})
    got = pe.recent(10, event="paywall_view")
    assert [row["feature"] for row in got] == ["f3", "f2", "f1", "f0"]


def test_recent_filter_returns_copies_not_ring_refs():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    got = pe.recent(10, feature="fleet")
    got[0]["feature"] = "TAMPERED"
    again = pe.recent(10, feature="fleet")
    assert again[0]["feature"] == "fleet"


def test_recent_filter_zero_limit_returns_empty():
    from clawmetry import _paywall_events as pe

    pe.record_event({"event": "paywall_view", "feature": "fleet"})
    assert pe.recent(0, feature="fleet") == []


def test_recent_filter_bad_limit_falls_back_to_default_then_still_filters():
    from clawmetry import _paywall_events as pe

    for _ in range(3):
        pe.record_event({"event": "paywall_view", "feature": "fleet"})
    for _ in range(2):
        pe.record_event({"event": "paywall_cta_click", "feature": "fleet"})
    # A garbage limit still resolves to the default (>= 5) so all 3 views land.
    got = pe.recent("garbage", event="paywall_view")
    assert len(got) == 3


# ── count_matching ──────────────────────────────────────────────────────────


def test_count_matching_unfiltered_equals_ring_size():
    from clawmetry import _paywall_events as pe

    for _ in range(5):
        pe.record_event({"event": "paywall_view", "feature": "fleet"})
    assert pe.count_matching() == 5


def test_count_matching_narrows_by_dimension():
    from clawmetry import _paywall_events as pe

    _seed(
        [
            {"event": "paywall_view", "feature": "fleet"},
            {"event": "paywall_cta_click", "feature": "fleet", "plan_chosen": "pro"},
            {"event": "paywall_view", "feature": "self_evolve"},
        ]
    )
    assert pe.count_matching(event="paywall_view") == 2
    assert pe.count_matching(feature="fleet") == 2
    assert pe.count_matching(feature="fleet", event="paywall_cta_click") == 1
    assert pe.count_matching(plan_chosen="pro") == 1
    assert pe.count_matching(feature="nope") == 0


def test_count_matching_and_recent_agree_pre_limit():
    """The number of matches ``count_matching`` reports must equal the
    number of rows :func:`recent` returns at a limit large enough to
    admit all matches."""
    from clawmetry import _paywall_events as pe

    for _ in range(6):
        pe.record_event({"event": "paywall_view", "feature": "fleet"})
    for _ in range(2):
        pe.record_event({"event": "paywall_cta_click", "feature": "fleet"})
    matched = pe.count_matching(event="paywall_view")
    got = pe.recent(pe.RECENT_MAX_LIMIT, event="paywall_view")
    assert matched == len(got) == 6


def test_count_matching_never_raises():
    """The store must swallow filter-time errors and return 0 rather than
    propagate them into the API layer."""
    from clawmetry import _paywall_events as pe

    # An unhashable / weird filter value should just miss, not raise.
    pe.record_event({"event": "paywall_view"})
    assert pe.count_matching(event=object()) == 0


# ── API endpoint filter contract ───────────────────────────────────────────


@pytest.fixture
def client():
    from routes.entitlement import bp_entitlement
    from clawmetry import _paywall_events as pe

    pe.reset()
    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    app.config["TESTING"] = True
    try:
        yield app.test_client()
    finally:
        pe.reset()


def _post_beacon(client, payload):
    return client.post(
        "/api/paywall/event",
        data=json.dumps(payload),
        content_type="application/json",
    )


def test_api_recent_unfiltered_still_carries_new_envelope_keys(client):
    _post_beacon(client, {"event": "paywall_view", "feature": "fleet"})
    body = client.get("/api/paywall/events/recent").get_json()
    # Legacy keys still present.
    assert body["count"] == 1
    assert body["in_window"] == 1
    assert body["limit"] == 50
    # New keys.
    assert body["matched"] == 1
    assert body["filters"] == {}


def test_api_recent_envelope_shape_is_stable(client):
    """Pin the full envelope key set so a paywall dashboard tile that binds
    to these keys cannot silently blank when the endpoint drops one."""
    body = client.get("/api/paywall/events/recent").get_json()
    assert set(body.keys()) == {
        "events", "count", "matched", "limit", "in_window", "filters",
    }


def test_api_recent_filter_narrows_events(client):
    _post_beacon(client, {"event": "paywall_view", "feature": "fleet"})
    _post_beacon(
        client,
        {"event": "paywall_cta_click", "feature": "fleet", "plan_chosen": "pro"},
    )
    _post_beacon(client, {"event": "paywall_view", "feature": "self_evolve"})

    body = client.get("/api/paywall/events/recent?event=paywall_cta_click").get_json()
    assert body["count"] == 1
    assert body["matched"] == 1
    assert body["events"][0]["event"] == "paywall_cta_click"
    assert body["filters"] == {"event": "paywall_cta_click"}


def test_api_recent_filter_and_combined(client):
    _post_beacon(client, {"event": "paywall_view", "feature": "fleet"})
    _post_beacon(client, {"event": "paywall_cta_click", "feature": "fleet"})
    _post_beacon(client, {"event": "paywall_cta_click", "feature": "self_evolve"})

    body = client.get(
        "/api/paywall/events/recent?event=paywall_cta_click&feature=fleet"
    ).get_json()
    assert body["count"] == 1
    assert body["matched"] == 1
    assert body["filters"] == {"event": "paywall_cta_click", "feature": "fleet"}


def test_api_recent_matched_reports_pre_limit_total(client):
    for _ in range(6):
        _post_beacon(client, {"event": "paywall_view", "feature": "fleet"})
    body = client.get(
        "/api/paywall/events/recent?event=paywall_view&limit=2"
    ).get_json()
    assert body["count"] == 2                # post-limit
    assert body["matched"] == 6              # pre-limit total
    assert body["limit"] == 2
    assert body["in_window"] == 6


def test_api_recent_matched_equals_in_window_when_unfiltered(client):
    for _ in range(4):
        _post_beacon(client, {"event": "paywall_view"})
    body = client.get("/api/paywall/events/recent").get_json()
    assert body["matched"] == body["in_window"] == 4


def test_api_recent_no_match_returns_empty_events_and_matched_zero(client):
    _post_beacon(client, {"event": "paywall_view", "feature": "fleet"})
    body = client.get(
        "/api/paywall/events/recent?feature=does_not_exist"
    ).get_json()
    assert body["events"] == []
    assert body["count"] == 0
    assert body["matched"] == 0
    assert body["in_window"] == 1
    assert body["filters"] == {"feature": "does_not_exist"}


def test_api_recent_blank_filter_is_not_supplied(client):
    _post_beacon(client, {"event": "paywall_view", "feature": "fleet"})
    _post_beacon(client, {"event": "paywall_cta_click", "feature": "self_evolve"})
    body = client.get(
        "/api/paywall/events/recent?feature=&harness="
    ).get_json()
    assert body["count"] == 2
    assert body["matched"] == 2
    assert body["filters"] == {}


def test_api_recent_filter_case_sensitive(client):
    _post_beacon(client, {"event": "paywall_view", "feature": "Fleet"})
    lower = client.get("/api/paywall/events/recent?feature=fleet").get_json()
    assert lower["count"] == 0
    assert lower["matched"] == 0
    upper = client.get("/api/paywall/events/recent?feature=Fleet").get_json()
    assert upper["count"] == 1
    assert upper["matched"] == 1


def test_api_recent_filter_survives_limit_clamp(client):
    """A ``?limit=`` bogus + ``?event=`` filter combination must still
    apply the filter after the limit falls back to default."""
    for _ in range(3):
        _post_beacon(client, {"event": "paywall_view"})
    for _ in range(2):
        _post_beacon(client, {"event": "paywall_cta_click"})
    body = client.get(
        "/api/paywall/events/recent?event=paywall_view&limit=nope"
    ).get_json()
    assert body["count"] == 3
    assert body["matched"] == 3
    assert body["limit"] == 50


def test_api_recent_filter_all_five_dimensions_echoes_them(client):
    _post_beacon(
        client,
        {
            "event": "paywall_cta_click",
            "feature": "fleet",
            "harness": "claude_code",
            "source": "runtime-switcher",
            "plan_chosen": "pro",
        },
    )
    body = client.get(
        "/api/paywall/events/recent"
        "?event=paywall_cta_click"
        "&feature=fleet"
        "&harness=claude_code"
        "&source=runtime-switcher"
        "&plan_chosen=pro"
    ).get_json()
    assert body["count"] == 1
    assert body["matched"] == 1
    assert body["filters"] == {
        "event": "paywall_cta_click",
        "feature": "fleet",
        "harness": "claude_code",
        "source": "runtime-switcher",
        "plan_chosen": "pro",
    }


def test_api_recent_filter_does_not_change_in_window(client):
    """A filtered request must NOT collapse ``in_window`` -- that field
    reports the ring's total, filter-independent."""
    for _ in range(3):
        _post_beacon(client, {"event": "paywall_view", "feature": "fleet"})
    for _ in range(2):
        _post_beacon(client, {"event": "paywall_cta_click", "feature": "self_evolve"})
    filtered = client.get(
        "/api/paywall/events/recent?event=paywall_view"
    ).get_json()
    assert filtered["in_window"] == 5
    assert filtered["matched"] == 3
    assert filtered["count"] == 3


def test_api_recent_filter_never_5xxs_on_store_failure(client, monkeypatch):
    """The neutral empty envelope (including the new ``matched`` /
    ``filters`` keys) must render even when the store raises under a
    filtered call."""
    from clawmetry import _paywall_events as pe

    def _boom(*_a, **_kw):
        raise RuntimeError("simulated store failure")

    monkeypatch.setattr(pe, "recent", _boom)
    resp = client.get("/api/paywall/events/recent?event=paywall_view")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {
        "events": [],
        "count": 0,
        "matched": 0,
        "limit": 0,
        "in_window": 0,
        "filters": {},
    }


def test_api_recent_filter_never_5xxs_when_count_matching_raises(client, monkeypatch):
    from clawmetry import _paywall_events as pe

    def _boom(**_kw):
        raise RuntimeError("simulated count_matching failure")

    monkeypatch.setattr(pe, "count_matching", _boom)
    resp = client.get("/api/paywall/events/recent?event=paywall_view")
    assert resp.status_code == 200
    body = resp.get_json()
    # Falls through to the neutral empty envelope.
    assert body["events"] == []
    assert body["matched"] == 0
    assert body["filters"] == {}


def test_api_recent_filter_does_not_consult_entitlement(client, monkeypatch):
    import clawmetry.entitlements as ent

    monkeypatch.setattr(
        ent, "get_entitlement",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("nope")),
    )
    resp = client.get("/api/paywall/events/recent?event=paywall_view")
    assert resp.status_code == 200


def test_api_recent_ignores_unknown_query_params(client):
    """A caller passing an unrelated ``?foo=bar`` must not affect the
    response -- only the five documented filter dimensions matter."""
    _post_beacon(client, {"event": "paywall_view", "feature": "fleet"})
    body = client.get(
        "/api/paywall/events/recent?foo=bar&nonsense=value"
    ).get_json()
    assert body["count"] == 1
    assert body["matched"] == 1
    assert body["filters"] == {}


# ── thread-safety smoke: filter reads race with writes ────────────────────


def test_concurrent_filtered_reads_do_not_raise(client):
    """A filtered ``recent`` call must be safe against concurrent
    ``record_event`` writes -- the ring lock covers the snapshot."""
    from clawmetry import _paywall_events as pe

    stop = threading.Event()

    def _writer():
        while not stop.is_set():
            pe.record_event({"event": "paywall_view", "feature": "fleet"})

    thread = threading.Thread(target=_writer, daemon=True)
    thread.start()
    try:
        for _ in range(200):
            got = pe.recent(50, feature="fleet")
            assert all(row["feature"] == "fleet" for row in got)
    finally:
        stop.set()
        thread.join(timeout=2.0)
