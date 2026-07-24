"""Filter-aware ``summary`` tests for :mod:`clawmetry._paywall_events`
and the ``GET /api/paywall/events/summary`` HTTP endpoint.

Pairs with ``test_paywall_events_recent_filters.py`` -- the store's
``summary(...)`` filter kwargs are the natural mirror of
``recent(...)`` / ``count_matching(...)``, and both endpoints must accept
the same filter contract so a dashboard tile can bind one filter set to
both surfaces without translation.

Invariants pinned:

* Filter kwargs restrict the ``by_*`` aggregate to matching rows only.
* Process-lifetime counters (``total`` / ``dropped`` / ``first_ts`` /
  ``last_ts`` / ``capacity``) and unfiltered ``in_window`` are NEVER
  sliced by the filters -- they describe the ring itself, not the
  caller's subset, so a filtered tile can still see churn / evictions.
* ``matched`` is byte-equal to ``in_window`` on an unfiltered call and
  reflects the pre-aggregation subset size when filters are applied.
* ``filters`` echoes the applied filter set (empty dict when none) so a
  caller distinguishes "asked for nothing, got 0" from "asked for X, got 0".
* Blank / whitespace-only filter values collapse to "not supplied"
  matching the ``recent`` endpoint's contract.
* Filters are ``AND`` combined, case-sensitive, and per-dimension
  independent.
* HTTP endpoint never 5xxs and always emits the two new fields.
"""
from __future__ import annotations

import pytest
from flask import Flask


# ── store-level ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _fresh_store():
    from clawmetry import _paywall_events as pe

    pe.reset()
    yield
    pe.reset()


def _seed(pe, rows):
    for r in rows:
        pe.record_event(r)


def test_summary_no_filter_emits_filters_and_matched_fields():
    """Backwards-compat + new-field contract: an unfiltered call still
    matches the pre-filter shape AND now always includes ``filters={}``
    and ``matched == in_window`` so callers can rely on the mirror."""
    from clawmetry import _paywall_events as pe

    _seed(pe, [
        {"event": "paywall_view", "feature": "fleet"},
        {"event": "paywall_cta_click", "feature": "fleet", "plan_chosen": "pro"},
    ])
    s = pe.summary()
    assert s["filters"] == {}
    assert s["matched"] == s["in_window"] == 2
    assert s["by_event"] == {"paywall_view": 1, "paywall_cta_click": 1}


def test_summary_filter_by_event_restricts_by_star_aggregates():
    from clawmetry import _paywall_events as pe

    _seed(pe, [
        {"event": "paywall_view", "feature": "fleet"},
        {"event": "paywall_view", "feature": "anomaly"},
        {"event": "paywall_cta_click", "feature": "fleet", "plan_chosen": "pro"},
    ])
    s = pe.summary(event="paywall_view")
    assert s["filters"] == {"event": "paywall_view"}
    assert s["matched"] == 2
    assert s["by_event"] == {"paywall_view": 2}
    assert s["by_feature"] == {"fleet": 1, "anomaly": 1}
    # No CTA rows in the subset -- plan_chosen bucket must not leak.
    assert s["by_plan_chosen"] == {}
    # in_window reflects the FULL ring, not the filtered subset.
    assert s["in_window"] == 3


def test_summary_filter_by_feature_isolates_plan_chosen_slice():
    """The motivating use case: a dashboard tile filtered to feature=fleet
    asks 'which plans did fleet CTA clicks convert to?' and must see only
    fleet-scoped plan_chosen counts."""
    from clawmetry import _paywall_events as pe

    _seed(pe, [
        {"event": "paywall_cta_click", "feature": "fleet",   "plan_chosen": "pro"},
        {"event": "paywall_cta_click", "feature": "fleet",   "plan_chosen": "pro"},
        {"event": "paywall_cta_click", "feature": "fleet",   "plan_chosen": "starter"},
        {"event": "paywall_cta_click", "feature": "anomaly", "plan_chosen": "pro"},
        {"event": "paywall_cta_click", "feature": "anomaly", "plan_chosen": "starter"},
    ])
    s = pe.summary(feature="fleet")
    assert s["matched"] == 3
    assert s["by_feature"] == {"fleet": 3}
    assert s["by_plan_chosen"] == {"pro": 2, "starter": 1}
    # anomaly-scoped rows must not leak in.
    assert "anomaly" not in s["by_feature"]


def test_summary_and_combines_filters():
    from clawmetry import _paywall_events as pe

    _seed(pe, [
        {"event": "paywall_view",       "feature": "fleet"},
        {"event": "paywall_cta_click",  "feature": "fleet", "plan_chosen": "pro"},
        {"event": "paywall_cta_click",  "feature": "anomaly", "plan_chosen": "pro"},
    ])
    s = pe.summary(event="paywall_cta_click", feature="fleet")
    assert s["filters"] == {"event": "paywall_cta_click", "feature": "fleet"}
    assert s["matched"] == 1
    assert s["by_plan_chosen"] == {"pro": 1}


def test_summary_filter_mismatch_returns_empty_by_star_but_keeps_ring_stats():
    from clawmetry import _paywall_events as pe

    _seed(pe, [
        {"event": "paywall_view", "feature": "fleet"},
    ])
    s = pe.summary(feature="does_not_exist")
    assert s["matched"] == 0
    assert s["filters"] == {"feature": "does_not_exist"}
    assert s["by_event"] == {}
    assert s["by_feature"] == {}
    assert s["by_plan_chosen"] == {}
    # Process-lifetime + unfiltered ring stats survive.
    assert s["total"] == 1
    assert s["in_window"] == 1
    assert s["first_ts"] is not None
    assert s["last_ts"] is not None


def test_summary_blank_and_whitespace_filters_treated_as_not_supplied():
    """Matches the recent-endpoint contract: an empty or whitespace-only
    value collapses to "not supplied" so ``?feature=`` on the URL does
    not accidentally match rows with no feature."""
    from clawmetry import _paywall_events as pe

    _seed(pe, [
        {"event": "paywall_view", "feature": "fleet"},
    ])
    for blank in ("", "   ", "\t", None):
        s = pe.summary(feature=blank)
        assert s["filters"] == {}, f"blank {blank!r} leaked into filters"
        assert s["matched"] == 1


def test_summary_filter_is_case_sensitive():
    from clawmetry import _paywall_events as pe

    _seed(pe, [
        {"event": "paywall_view", "feature": "Fleet"},
    ])
    assert pe.summary(feature="Fleet")["matched"] == 1
    assert pe.summary(feature="fleet")["matched"] == 0


def test_summary_process_lifetime_counters_survive_filter():
    """Filters must never scale down ``total`` / ``dropped`` /
    ``capacity`` / ``in_window`` -- those describe the ring itself, not
    the caller's subset. A filtered dashboard tile must still see churn."""
    from clawmetry import _paywall_events as pe

    _seed(pe, [
        {"event": "paywall_view", "feature": "fleet"},
        {"event": "paywall_view", "feature": "anomaly"},
        {"event": "paywall_view", "feature": "anomaly"},
    ])
    filtered = pe.summary(feature="fleet")
    unfiltered = pe.summary()
    assert filtered["total"] == unfiltered["total"] == 3
    assert filtered["in_window"] == unfiltered["in_window"] == 3
    assert filtered["dropped"] == unfiltered["dropped"] == 0
    assert filtered["capacity"] == unfiltered["capacity"]
    # But the by_* aggregate IS scaled.
    assert filtered["matched"] == 1
    assert filtered["by_feature"] == {"fleet": 1}


def test_summary_shim_accepts_all_five_filter_dimensions():
    """The public :func:`summary` shim must expose the same kwargs as
    the store method so ``recent`` / ``count_matching`` / ``summary``
    stay a coherent surface."""
    from clawmetry import _paywall_events as pe

    _seed(pe, [
        {"event": "paywall_view",       "feature": "fleet",   "harness": "claude_code",
         "source": "runtime-switcher",  "plan_chosen": ""},
        {"event": "paywall_cta_click",  "feature": "fleet",   "harness": "codex",
         "source": "sidebar",           "plan_chosen": "pro"},
        {"event": "paywall_view",       "feature": "anomaly", "harness": "claude_code",
         "source": "runtime-switcher",  "plan_chosen": ""},
    ])
    for kwarg, value, expected in (
        ("event",       "paywall_view",      2),
        ("feature",     "fleet",             2),
        ("harness",     "claude_code",       2),
        ("source",      "runtime-switcher",  2),
        ("plan_chosen", "pro",               1),
    ):
        s = pe.summary(**{kwarg: value})
        assert s["matched"] == expected, f"{kwarg}={value!r} matched {s['matched']}, want {expected}"
        assert s["filters"] == {kwarg: value}


def test_summary_empty_store_with_filter_returns_zero_matched_and_echo():
    from clawmetry import _paywall_events as pe

    s = pe.summary(event="paywall_view")
    assert s["matched"] == 0
    assert s["in_window"] == 0
    assert s["total"] == 0
    assert s["filters"] == {"event": "paywall_view"}
    assert s["by_event"] == {}


# ── HTTP endpoint ───────────────────────────────────────────────────────────


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


def _post(client, payload):
    return client.post("/api/paywall/event", json=payload)


def test_http_summary_no_filter_backwards_compatible(client):
    """An unfiltered GET still returns every pre-filter key the
    dashboard tile binds to, PLUS the new ``filters`` / ``matched`` mirror."""
    _post(client, {"event": "paywall_view", "feature": "fleet"})
    body = client.get("/api/paywall/events/summary").get_json()
    assert body["total"] == 1
    assert body["in_window"] == 1
    assert body["by_event"] == {"paywall_view": 1}
    assert body["by_feature"] == {"fleet": 1}
    assert body["filters"] == {}
    assert body["matched"] == body["in_window"]


def test_http_summary_filter_by_feature(client):
    _post(client, {"event": "paywall_cta_click", "feature": "fleet",   "plan_chosen": "pro"})
    _post(client, {"event": "paywall_cta_click", "feature": "fleet",   "plan_chosen": "starter"})
    _post(client, {"event": "paywall_cta_click", "feature": "anomaly", "plan_chosen": "pro"})
    body = client.get("/api/paywall/events/summary?feature=fleet").get_json()
    assert body["filters"] == {"feature": "fleet"}
    assert body["matched"] == 2
    assert body["in_window"] == 3
    assert body["by_plan_chosen"] == {"pro": 1, "starter": 1}
    # Ring stats unfiltered.
    assert body["total"] == 3


def test_http_summary_and_combines_multiple_query_params(client):
    _post(client, {"event": "paywall_view",      "feature": "fleet"})
    _post(client, {"event": "paywall_cta_click", "feature": "fleet",   "plan_chosen": "pro"})
    _post(client, {"event": "paywall_cta_click", "feature": "anomaly", "plan_chosen": "pro"})
    body = client.get(
        "/api/paywall/events/summary?event=paywall_cta_click&feature=fleet"
    ).get_json()
    assert body["matched"] == 1
    assert body["filters"] == {"event": "paywall_cta_click", "feature": "fleet"}
    assert body["by_plan_chosen"] == {"pro": 1}


def test_http_summary_blank_query_param_treated_as_not_supplied(client):
    """?feature= (empty value) must NOT restrict on that dimension --
    matching how ``/api/paywall/events/recent`` handles it."""
    _post(client, {"event": "paywall_view", "feature": "fleet"})
    body = client.get("/api/paywall/events/summary?feature=").get_json()
    assert body["filters"] == {}
    assert body["matched"] == 1


def test_http_summary_filter_mismatch_returns_empty_aggregate_not_5xx(client):
    _post(client, {"event": "paywall_view", "feature": "fleet"})
    resp = client.get("/api/paywall/events/summary?feature=does_not_exist")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["matched"] == 0
    assert body["by_feature"] == {}
    assert body["filters"] == {"feature": "does_not_exist"}
    # Ring stats survive the filter.
    assert body["total"] == 1
    assert body["in_window"] == 1


def test_http_summary_fallback_shape_includes_new_fields(client, monkeypatch):
    """Even the error-path neutral shape must carry ``filters`` +
    ``matched`` so a caller can trust the top-level key set is stable."""
    from clawmetry import _paywall_events as pe

    def _boom(**kwargs):
        raise RuntimeError("simulated store failure")

    monkeypatch.setattr(pe, "summary", _boom)
    resp = client.get("/api/paywall/events/summary?feature=fleet")
    assert resp.status_code == 200
    body = resp.get_json()
    for key in (
        "total", "in_window", "dropped", "capacity", "first_ts", "last_ts",
        "by_event", "by_feature", "by_harness", "by_source", "by_plan_chosen",
        "filters", "matched",
    ):
        assert key in body, f"error-path fallback missing {key!r}"
    assert body["matched"] == 0
    assert body["filters"] == {}


def test_http_summary_matches_recent_filter_names(client):
    """Both endpoints must accept the same query-param names so a tile
    can bind one filter set to both surfaces. Iterate every dimension
    and confirm ``summary?<k>=v`` produces the same slice count as
    ``recent?limit=200&<k>=v``."""
    rows = [
        {"event": "paywall_view",      "feature": "fleet",   "harness": "claude_code",
         "source": "runtime-switcher"},
        {"event": "paywall_cta_click", "feature": "fleet",   "harness": "codex",
         "source": "sidebar",          "plan_chosen": "pro"},
        {"event": "paywall_view",      "feature": "anomaly", "harness": "claude_code",
         "source": "runtime-switcher"},
    ]
    for r in rows:
        _post(client, r)

    for kv in (
        "event=paywall_view",
        "feature=fleet",
        "harness=claude_code",
        "source=runtime-switcher",
        "plan_chosen=pro",
    ):
        summary_matched = client.get(
            f"/api/paywall/events/summary?{kv}"
        ).get_json()["matched"]
        recent_matched = client.get(
            f"/api/paywall/events/recent?limit=200&{kv}"
        ).get_json()["matched"]
        assert summary_matched == recent_matched, (
            f"{kv}: summary.matched={summary_matched} "
            f"differs from recent.matched={recent_matched}"
        )
