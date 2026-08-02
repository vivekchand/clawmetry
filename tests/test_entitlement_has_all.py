"""Tests for the aggregate mixed-axis ``has_all(...)`` boolean-gate scalar and
its paired ``/api/entitlement/has-all`` endpoint.

Aggregate boolean sibling of :func:`clawmetry.entitlements.min_tier_for_all`
(which folds the same five kwargs to ONE tier id): a paywall diagnostics tile
that gates on the FULL subscription state ("fleet + claude_code + 5 channels
+ 30-day retention + 2 nodes -- does the resolved entitlement grant
everything?") binds ONE boolean off ONE call instead of five singular
``has_*`` round-trips + a client-side AND-chain.

This file pins:

1. Scalar fold under grace vs enforce for every combination of the five
   axes (features / runtimes / channels / retention_days / nodes),
   including per-axis empty / None / unknown / non-int inputs.
2. The "no axes supplied" strict-``False`` posture (matches the singular
   ``has_features([])`` empty-``False`` scalar; distinct from
   :func:`min_tier_for_all` which returns ``None`` on the same input).
3. Endpoint envelope shape parity (fixed 19-key set) across every input
   branch so a frontend can bind fields off the URL without a branch on
   the underlying resolver state.
4. Never-4xx / never-5xx guarantees on the endpoint.
5. Cross-consistency with ``/api/entitlement/required-tier-batch``: same
   ``required_tier`` for the same fully-parseable bundle, so a UI wiring
   both URLs into the same paywall tile can't see inconsistent tier
   state (documented posture divergence on unparseable-capacity is a
   separate assertion).
6. Scalar-vs-endpoint parity: the URL ``has_all`` value equals the
   module-level scalar byte-for-byte on the same (parseable) input.
7. Grace invariant: fully-known mixed bundles report ``True`` while
   ``ent.grace`` is on -- wiring this into a gate today changes NO
   current behavior.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# -- Fixtures ------------------------------------------------------------------


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode -- the same fixture
    the sibling ``test_entitlement_has_features_has_runtimes.py`` uses so the
    aggregate-fold assertions here reproduce the same install state the
    per-axis ones are pinned against."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    """Enforcement-on fixture: ``CLAWMETRY_ENFORCE=1`` flips ``ent.grace``
    off so the grace pass-through collapses and paid axes report their
    post-enforce answers."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    importlib.reload(e)
    e.invalidate()


@pytest.fixture
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# -- Envelope shape ------------------------------------------------------------

_HAS_ALL_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown_features",
    "unknown_runtimes",
    "supplied_axes",
    "supplied_count",
    "has_all",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
    "upgrade_required",
}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


# -- Scalar: no axes supplied --------------------------------------------------


def test_has_all_no_axes_supplied_is_false(ent):
    """Nothing supplied collapses to False."""
    assert ent.has_all() is False


def test_has_all_no_axes_supplied_is_false_after_enforcement(enforced):
    assert enforced.has_all() is False


# -- Scalar: single axis -------------------------------------------------------


def test_has_all_features_only_free_is_true(ent):
    free = sorted(ent.FREE_FEATURES)
    assert ent.has_all(features=free) is True


def test_has_all_features_only_paid_true_in_grace(ent):
    paid = sorted(ent.PAID_FEATURES)
    assert ent.has_all(features=paid) is True


def test_has_all_features_only_paid_false_after_enforcement(enforced):
    paid = sorted(enforced.PAID_FEATURES)
    assert enforced.has_all(features=paid) is False


def test_has_all_runtimes_only_free_is_true(ent):
    free = sorted(ent.FREE_RUNTIMES)
    assert ent.has_all(runtimes=free) is True


def test_has_all_runtimes_only_paid_true_in_grace(ent):
    paid = sorted(ent.PAID_RUNTIMES)
    assert ent.has_all(runtimes=paid) is True


def test_has_all_runtimes_only_paid_false_after_enforcement(enforced):
    paid = sorted(enforced.PAID_RUNTIMES)
    assert enforced.has_all(runtimes=paid) is False


def test_has_all_channels_only_one_is_true(ent):
    assert ent.has_all(channels=1) is True


def test_has_all_channels_only_big_true_in_grace(ent):
    assert ent.has_all(channels=999) is True


def test_has_all_channels_only_big_false_after_enforcement(enforced):
    assert enforced.has_all(channels=999) is False


def test_has_all_nodes_only_one_is_true(ent):
    assert ent.has_all(nodes=1) is True


def test_has_all_nodes_only_big_true_in_grace(ent):
    assert ent.has_all(nodes=42) is True


def test_has_all_nodes_only_big_false_after_enforcement(enforced):
    assert enforced.has_all(nodes=42) is False


def test_has_all_retention_days_only_short_is_true(ent):
    assert ent.has_all(retention_days=1) is True


def test_has_all_retention_days_only_long_true_in_grace(ent):
    assert ent.has_all(retention_days=999) is True


def test_has_all_retention_days_only_long_false_after_enforcement(enforced):
    assert enforced.has_all(retention_days=999) is False


# -- Scalar: mixed axes --------------------------------------------------------


def test_has_all_mixed_free_bundle_is_true(ent):
    free_f = next(iter(ent.FREE_FEATURES))
    free_r = next(iter(ent.FREE_RUNTIMES))
    assert (
        ent.has_all(
            features=[free_f],
            runtimes=[free_r],
            channels=1,
            retention_days=1,
            nodes=1,
        )
        is True
    )


def test_has_all_mixed_free_bundle_still_true_after_enforcement(enforced):
    free_f = next(iter(enforced.FREE_FEATURES))
    free_r = next(iter(enforced.FREE_RUNTIMES))
    assert (
        enforced.has_all(
            features=[free_f],
            runtimes=[free_r],
            channels=1,
            retention_days=1,
            nodes=1,
        )
        is True
    )


def test_has_all_mixed_paid_bundle_true_in_grace(ent):
    paid_f = next(iter(ent.PAID_FEATURES))
    paid_r = next(iter(ent.PAID_RUNTIMES))
    assert (
        ent.has_all(
            features=[paid_f],
            runtimes=[paid_r],
            channels=5,
            retention_days=30,
            nodes=2,
        )
        is True
    )


def test_has_all_mixed_paid_bundle_false_after_enforcement(enforced):
    paid_f = next(iter(enforced.PAID_FEATURES))
    paid_r = next(iter(enforced.PAID_RUNTIMES))
    assert (
        enforced.has_all(
            features=[paid_f],
            runtimes=[paid_r],
            channels=5,
            retention_days=30,
            nodes=2,
        )
        is False
    )


def test_has_all_mixed_free_features_but_paid_runtime_false_after_enforcement(
    enforced,
):
    free_f = next(iter(enforced.FREE_FEATURES))
    paid_r = next(iter(enforced.PAID_RUNTIMES))
    assert (
        enforced.has_all(features=[free_f], runtimes=[paid_r], channels=1)
        is False
    )


# -- Scalar: empty inputs on supplied axes -------------------------------------


def test_has_all_features_empty_iterable_is_false(ent):
    assert ent.has_all(features=[]) is False
    assert ent.has_all(features=()) is False


def test_has_all_runtimes_empty_iterable_is_false(ent):
    assert ent.has_all(runtimes=[]) is False


def test_has_all_empty_features_supplied_denies_even_with_other_axes(ent):
    assert ent.has_all(features=[], channels=1) is False


# -- Scalar: unknown / typo'd inputs -------------------------------------------


def test_has_all_unknown_feature_collapses_fold(ent):
    assert ent.has_all(features=["fleet", "totally_fake_xyz"]) is False


def test_has_all_unknown_runtime_collapses_fold(ent):
    assert ent.has_all(runtimes=["openclaw", "totally_fake_rt"]) is False


def test_has_all_unknown_feature_wins_over_other_axes(ent):
    assert (
        ent.has_all(features=["bogus_xyz"], runtimes=["openclaw"], channels=1)
        is False
    )


# -- Scalar: non-int capacity --------------------------------------------------


def test_has_all_non_int_channels_is_false(ent):
    assert ent.has_all(channels="five") is False  # type: ignore[arg-type]


def test_has_all_non_int_nodes_is_false(ent):
    assert ent.has_all(nodes="two") is False  # type: ignore[arg-type]


def test_has_all_non_int_retention_is_false(ent):
    assert ent.has_all(retention_days="seven") is False  # type: ignore[arg-type]


# -- Scalar: retention_days=None means unsupplied ------------------------------


def test_has_all_retention_none_is_unsupplied_not_unlimited(ent):
    assert ent.has_all(channels=1, retention_days=None) is True
    assert ent.has_all(channels=1) is True


# -- Scalar: never raises ------------------------------------------------------


def test_has_all_never_raises_on_resolver_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("resolver blowup")

    monkeypatch.setattr(ent, "has_features", _boom)
    assert ent.has_all(features=["fleet"]) is False


def test_has_all_never_raises_on_capacity_delegate_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("blowup")

    monkeypatch.setattr(ent, "has_channel_count", _boom)
    assert ent.has_all(channels=1) is False


# -- Endpoint: envelope shape --------------------------------------------------


def test_endpoint_no_params_shape(client):
    body = _get_json(client, "/api/entitlement/has-all")
    assert set(body.keys()) == _HAS_ALL_KEYS
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["channels"] is None
    assert body["retention_days"] is None
    assert body["nodes"] is None
    assert body["unknown_features"] == []
    assert body["unknown_runtimes"] == []
    assert body["supplied_axes"] == []
    assert body["supplied_count"] == 0
    assert body["has_all"] is False
    assert body["allowed"] is False


def test_endpoint_all_free_axes_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all?"
        "features=nemo_governance&runtimes=openclaw"
        "&channels=1&retention_days=1&nodes=1",
    )
    assert set(body.keys()) == _HAS_ALL_KEYS
    assert body["features"] == ["nemo_governance"]
    assert body["runtimes"] == ["openclaw"]
    assert body["channels"] == 1
    assert body["retention_days"] == 1
    assert body["nodes"] == 1
    assert body["supplied_axes"] == [
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
    ]
    assert body["supplied_count"] == 5
    assert body["has_all"] is True
    assert body["allowed"] is True
    assert body["required_tier"] == "oss"
    assert body["required_tier_rank"] == 0
    assert body["upgrade_required"] is False


def test_endpoint_paid_bundle_grace_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all?features=fleet&runtimes=claude_code"
        "&channels=5&retention_days=30&nodes=2",
    )
    assert set(body.keys()) == _HAS_ALL_KEYS
    assert body["has_all"] is True
    assert body["allowed"] is True
    assert body["required_tier"] is not None
    assert body["required_tier"] != "oss"
    assert body["required_tier_rank"] > 0
    assert body["upgrade_required"] is True


def test_endpoint_features_only_shape(client):
    body = _get_json(client, "/api/entitlement/has-all?features=fleet")
    assert body["supplied_axes"] == ["features"]
    assert body["supplied_count"] == 1
    assert body["features"] == ["fleet"]
    assert body["runtimes"] == []
    assert body["channels"] is None
    assert body["has_all"] is True  # grace


def test_endpoint_runtimes_only_shape(client):
    body = _get_json(client, "/api/entitlement/has-all?runtimes=claude_code")
    assert body["supplied_axes"] == ["runtimes"]
    assert body["runtimes"] == ["claude_code"]
    assert body["has_all"] is True  # grace


def test_endpoint_channels_only_shape(client):
    body = _get_json(client, "/api/entitlement/has-all?channels=5")
    assert body["supplied_axes"] == ["channels"]
    assert body["channels"] == 5
    assert body["has_all"] is True  # grace


# -- Endpoint: unknown tokens --------------------------------------------------


def test_endpoint_unknown_feature_collapses_bundle(client):
    body = _get_json(
        client, "/api/entitlement/has-all?features=fleet,totally_fake_xyz"
    )
    assert body["features"] == ["fleet"]
    assert body["unknown_features"] == ["totally_fake_xyz"]
    assert body["has_all"] is False
    assert body["allowed"] is False


def test_endpoint_unknown_runtime_collapses_bundle(client):
    body = _get_json(
        client, "/api/entitlement/has-all?runtimes=openclaw,totally_fake_rt"
    )
    assert body["runtimes"] == ["openclaw"]
    assert body["unknown_runtimes"] == ["totally_fake_rt"]
    assert body["has_all"] is False


def test_endpoint_runtime_alias_canonicalises(client):
    body = _get_json(
        client, "/api/entitlement/has-all?runtimes=claude-code,claude_code"
    )
    assert body["runtimes"] == ["claude_code"]
    assert body["unknown_runtimes"] == []
    assert body["has_all"] is True  # grace


# -- Endpoint: capacity axes ---------------------------------------------------


def test_endpoint_non_int_channels_collapses_bundle(client):
    body = _get_json(client, "/api/entitlement/has-all?channels=five")
    assert body["supplied_axes"] == ["channels"]
    assert body["channels"] is None
    assert body["has_all"] is False


def test_endpoint_blank_channels_collapses_bundle(client):
    body = _get_json(client, "/api/entitlement/has-all?channels=")
    assert body["supplied_axes"] == ["channels"]
    assert body["channels"] is None
    assert body["has_all"] is False


def test_endpoint_zero_channels_is_true(client):
    body = _get_json(client, "/api/entitlement/has-all?channels=0")
    assert body["supplied_axes"] == ["channels"]
    assert body["channels"] == 0
    assert body["has_all"] is True


# -- Endpoint: enforce mode ----------------------------------------------------


def test_endpoint_paid_bundle_denied_after_enforcement(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    try:
        from routes.entitlement import bp_entitlement

        app = Flask(__name__)
        app.register_blueprint(bp_entitlement)
        client = app.test_client()
        resp = client.get(
            "/api/entitlement/has-all?features=fleet&runtimes=claude_code"
            "&channels=5&retention_days=30&nodes=2"
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["grace"] is False
        assert body["enforced"] is True
        assert body["has_all"] is False
        assert body["allowed"] is False
    finally:
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(e)
        e.invalidate()


# -- Endpoint: never 5xx -------------------------------------------------------


def test_endpoint_never_5xx_on_body_blowup(monkeypatch, client):
    def _boom(*a, **kw):
        raise RuntimeError("blowup in body builder")

    monkeypatch.setattr("routes.entitlement._has_all_body", _boom)
    resp = client.get(
        "/api/entitlement/has-all?features=fleet&channels=5"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _HAS_ALL_KEYS
    assert body["has_all"] is False
    assert body["allowed"] is False


def test_endpoint_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("boom in scalar")

    monkeypatch.setattr(_ent, "has_all", _boom)
    resp = client.get("/api/entitlement/has-all?features=fleet")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _HAS_ALL_KEYS
    assert body["has_all"] is False


# -- Endpoint: never 4xx -------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-all",
        "/api/entitlement/has-all?features=",
        "/api/entitlement/has-all?runtimes=",
        "/api/entitlement/has-all?channels=",
        "/api/entitlement/has-all?features=fleet&channels=notanint",
        "/api/entitlement/has-all?features=bogus_only",
        "/api/entitlement/has-all?features=fleet,,,",
    ],
)
def test_endpoint_never_4xx(client, url):
    resp = client.get(url)
    assert resp.status_code == 200, url
    body = resp.get_json()
    assert set(body.keys()) == _HAS_ALL_KEYS


# -- Endpoint: scalar-vs-endpoint parity ---------------------------------------


@pytest.mark.parametrize(
    "url,features,runtimes,channels,retention_days,nodes",
    [
        ("/api/entitlement/has-all?features=fleet", ["fleet"], None, None, None, None),
        (
            "/api/entitlement/has-all?features=fleet&runtimes=claude_code",
            ["fleet"],
            ["claude_code"],
            None,
            None,
            None,
        ),
        (
            "/api/entitlement/has-all?channels=5&nodes=2",
            None,
            None,
            5,
            None,
            2,
        ),
        (
            "/api/entitlement/has-all?features=nemo_governance"
            "&runtimes=openclaw&channels=1&retention_days=1&nodes=1",
            ["nemo_governance"],
            ["openclaw"],
            1,
            1,
            1,
        ),
        (
            "/api/entitlement/has-all?features=fleet,bogus_xyz",
            ["fleet", "bogus_xyz"],
            None,
            None,
            None,
            None,
        ),
    ],
)
def test_endpoint_matches_scalar(
    client, ent, url, features, runtimes, channels, retention_days, nodes
):
    body = _get_json(client, url)
    expected = ent.has_all(
        features=features,
        runtimes=runtimes,
        channels=channels,
        retention_days=retention_days,
        nodes=nodes,
    )
    assert body["has_all"] is expected
    assert body["allowed"] is expected


# -- Cross-consistency with /required-tier-batch --------------------------------


@pytest.mark.parametrize(
    "query,expect_required",
    [
        ("features=nemo_governance", True),
        ("features=fleet", True),
        ("runtimes=claude_code", True),
        ("features=fleet&runtimes=claude_code", True),
        ("channels=5&nodes=2", True),
    ],
)
def test_cross_consistent_with_required_tier_batch(
    client, query, expect_required
):
    has = _get_json(client, f"/api/entitlement/has-all?{query}")
    rtb = _get_json(client, f"/api/entitlement/required-tier-batch?{query}")
    assert has["required_tier"] == rtb["required_tier"]
    assert has["required_tier_label"] == rtb["required_tier_label"]
    assert has["required_tier_rank"] == rtb["required_tier_rank"]
    assert has["current_tier"] == rtb["current_tier"]
    assert has["current_tier_rank"] == rtb["current_tier_rank"]
    if expect_required:
        assert has["required_tier"] is not None


def test_documented_divergence_from_required_tier_batch_on_no_axes(client):
    has_resp = client.get("/api/entitlement/has-all")
    assert has_resp.status_code == 200
    rtb_resp = client.get("/api/entitlement/required-tier-batch")
    assert rtb_resp.status_code == 400


# -- Grace / enforce invariants ------------------------------------------------


def test_grace_invariant_full_known_paid_bundle_reports_true(ent):
    paid_f = next(iter(ent.PAID_FEATURES))
    paid_r = next(iter(ent.PAID_RUNTIMES))
    assert (
        ent.has_all(
            features=[paid_f],
            runtimes=[paid_r],
            channels=999,
            retention_days=999,
            nodes=999,
        )
        is True
    )


def test_enforce_full_known_paid_bundle_locked_on_oss(enforced):
    paid_f = next(iter(enforced.PAID_FEATURES))
    paid_r = next(iter(enforced.PAID_RUNTIMES))
    assert (
        enforced.has_all(
            features=[paid_f],
            runtimes=[paid_r],
            channels=999,
            retention_days=999,
            nodes=999,
        )
        is False
    )


def test_enforce_free_bundle_still_true(enforced):
    free_f = next(iter(enforced.FREE_FEATURES))
    free_r = next(iter(enforced.FREE_RUNTIMES))
    assert (
        enforced.has_all(
            features=[free_f],
            runtimes=[free_r],
            channels=1,
            retention_days=1,
            nodes=1,
        )
        is True
    )
