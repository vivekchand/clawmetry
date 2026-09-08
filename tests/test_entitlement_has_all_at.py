"""Tests for the hypothetical-perspective mixed-axis ``has_all_at(...)``
boolean-gate scalar and its paired ``/api/entitlement/has-all-at`` endpoint.

Perspective-shaped sibling of :func:`clawmetry.entitlements.has_all` (which
folds the same five kwargs against the LIVE resolver): a pricing-matrix
walkthrough that gates on the full subscription state per hypothetical tier
("if I were on Cloud Pro, would this whole bundle be granted?") binds ONE
boolean per (perspective, bundle) cell off ONE call instead of five singular
``_at`` round-trips + a client-side AND-chain.

This file pins:

1. Scalar fold under grace vs enforce for every combination of the five
   axes (features / runtimes / channels / retention_days / nodes),
   including per-axis empty / None / unknown / non-int inputs.
2. Perspective validation (empty / non-string / unknown -> ``False`` at
   the scalar; 400 / 404 at the endpoint).
3. **Grace-independence invariant**: ``has_all_at(p, ...) ==
   has_all_at(p, ...)`` under both grace and enforce for every ``p`` and
   every input (delegates to the singular ``_at`` scalars, which are
   backed by the static per-tier tables via
   :func:`_hypothetical_entitlement`).
4. Endpoint envelope shape parity (fixed 21-key set) across every input
   branch so a frontend can bind fields off the URL without a branch on
   the underlying resolver state.
5. Never-4xx on axis-side inputs; 400 on missing / blank tier; 404 on
   unknown tier; never 5xx.
6. Cross-consistency with the singular ``/has-feature-at`` /
   ``/has-runtime-at`` / ``/has-channel-count-at`` /
   ``/has-retention-window-at`` / ``/has-node-count-at`` endpoints: for
   any (perspective, single-axis) query, this endpoint's ``has_all_at``
   equals the sibling scalar byte-for-byte.
7. Scalar-vs-endpoint parity: the URL ``has_all_at`` value equals the
   module-level scalar byte-for-byte on the same (parseable) input.
8. Deliberate divergence from the LIVE ``/has-all`` sibling: a bundle
   the resolver grants under grace can still report
   ``has_all_at=false`` on the OSS perspective (that's the whole point
   of the ``_at`` slot).
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# -- Fixtures ------------------------------------------------------------------


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode."""
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
    off so the grace pass-through collapses. Perspective-shaped answers
    are intentionally identical in grace and enforce; this fixture pins
    that invariant."""
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

_HAS_ALL_AT_KEYS = {
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown_features",
    "unknown_runtimes",
    "supplied_axes",
    "supplied_count",
    "has_all_at",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


# -- Scalar: perspective validation --------------------------------------------


def test_has_all_at_unknown_perspective_is_false(ent):
    assert ent.has_all_at("bogus", features=["fleet"]) is False


def test_has_all_at_empty_perspective_is_false(ent):
    assert ent.has_all_at("", features=["fleet"]) is False


def test_has_all_at_none_perspective_is_false(ent):
    assert ent.has_all_at(None, features=["fleet"]) is False  # type: ignore[arg-type]


def test_has_all_at_non_string_perspective_is_false(ent):
    assert ent.has_all_at(123, features=["fleet"]) is False  # type: ignore[arg-type]


def test_has_all_at_perspective_case_and_whitespace_normalised(ent):
    assert (
        ent.has_all_at("  CLOUD_PRO  ", features=["fleet"])
        == ent.has_all_at("cloud_pro", features=["fleet"])
    )


# -- Scalar: no axes supplied --------------------------------------------------


def test_has_all_at_no_axes_supplied_is_false(ent):
    """Nothing supplied collapses to False -- matches has_all."""
    for tier in ent._TIER_ORDER:
        assert ent.has_all_at(tier) is False, tier


def test_has_all_at_no_axes_supplied_is_false_after_enforcement(enforced):
    for tier in enforced._TIER_ORDER:
        assert enforced.has_all_at(tier) is False, tier


# -- Scalar: perspective-shaped semantics on free bundles ----------------------


def test_has_all_at_oss_free_bundle_is_true(ent):
    free_f = next(iter(ent.FREE_FEATURES))
    free_r = next(iter(ent.FREE_RUNTIMES))
    assert (
        ent.has_all_at(
            "oss",
            features=[free_f],
            runtimes=[free_r],
            channels=1,
            retention_days=1,
            nodes=1,
        )
        is True
    )


def test_has_all_at_every_tier_admits_free_bundle(ent):
    free_f = next(iter(ent.FREE_FEATURES))
    free_r = next(iter(ent.FREE_RUNTIMES))
    for tier in ent._TIER_ORDER:
        assert (
            ent.has_all_at(
                tier,
                features=[free_f],
                runtimes=[free_r],
                channels=1,
                retention_days=1,
                nodes=1,
            )
            is True
        ), tier


# -- Scalar: perspective-shaped semantics on paid bundles ----------------------


def test_has_all_at_oss_denies_paid_feature(ent):
    paid_f = next(iter(ent.PAID_FEATURES))
    assert ent.has_all_at("oss", features=[paid_f]) is False


def test_has_all_at_oss_denies_paid_runtime(ent):
    paid_r = next(iter(ent.PAID_RUNTIMES))
    assert ent.has_all_at("oss", runtimes=[paid_r]) is False


def test_has_all_at_cloud_pro_admits_paid_bundle(ent):
    paid_f = next(iter(ent.PAID_FEATURES))
    paid_r = next(iter(ent.PAID_RUNTIMES))
    assert (
        ent.has_all_at(
            "cloud_pro",
            features=[paid_f],
            runtimes=[paid_r],
            channels=100,
            retention_days=90,
            nodes=1000,
        )
        is True
    )


def test_has_all_at_enterprise_admits_paid_bundle(ent):
    paid_f = next(iter(ent.PAID_FEATURES))
    paid_r = next(iter(ent.PAID_RUNTIMES))
    assert (
        ent.has_all_at(
            "enterprise",
            features=[paid_f],
            runtimes=[paid_r],
            channels=999,
            retention_days=999,
            nodes=99999,
        )
        is True
    )


# -- Scalar: grace-independence invariant --------------------------------------


def test_has_all_at_grace_vs_enforce_byte_identical_on_oss(monkeypatch, tmp_path):
    """The whole point of the ``_at`` slot: perspective-shaped answers
    read the static per-tier tables and are grace-independent."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    paid_f = next(iter(e.PAID_FEATURES))
    paid_r = next(iter(e.PAID_RUNTIMES))
    grace = e.has_all_at(
        "oss",
        features=[paid_f],
        runtimes=[paid_r],
        channels=5,
        retention_days=30,
        nodes=2,
    )

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    enforce = e.has_all_at(
        "oss",
        features=[paid_f],
        runtimes=[paid_r],
        channels=5,
        retention_days=30,
        nodes=2,
    )
    assert grace == enforce
    assert grace is False


def test_has_all_at_grace_vs_enforce_byte_identical_on_cloud_pro(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    paid_f = next(iter(e.PAID_FEATURES))
    paid_r = next(iter(e.PAID_RUNTIMES))
    grace = e.has_all_at(
        "cloud_pro", features=[paid_f], runtimes=[paid_r], channels=5
    )

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    enforce = e.has_all_at(
        "cloud_pro", features=[paid_f], runtimes=[paid_r], channels=5
    )
    assert grace == enforce
    assert grace is True


# -- Scalar: divergence from live has_all in grace -----------------------------


def test_has_all_diverges_from_has_all_at_on_oss_paid_bundle(ent):
    """LIVE has_all reports True in grace; _at reports False from the
    OSS perspective (static per-tier tables). Whole point of the slot."""
    paid_f = next(iter(ent.PAID_FEATURES))
    live = ent.has_all(features=[paid_f])
    perspective = ent.has_all_at("oss", features=[paid_f])
    assert live is True
    assert perspective is False


# -- Scalar: empty inputs on supplied axes -------------------------------------


def test_has_all_at_features_empty_iterable_is_false(ent):
    assert ent.has_all_at("cloud_pro", features=[]) is False
    assert ent.has_all_at("cloud_pro", features=()) is False


def test_has_all_at_runtimes_empty_iterable_is_false(ent):
    assert ent.has_all_at("cloud_pro", runtimes=[]) is False


def test_has_all_at_empty_features_supplied_denies_even_with_other_axes(ent):
    assert ent.has_all_at("cloud_pro", features=[], channels=1) is False


# -- Scalar: unknown / typo'd inputs -------------------------------------------


def test_has_all_at_unknown_feature_collapses_fold(ent):
    assert ent.has_all_at("cloud_pro", features=["fleet", "bogus_xyz"]) is False


def test_has_all_at_unknown_runtime_collapses_fold(ent):
    assert (
        ent.has_all_at("cloud_pro", runtimes=["openclaw", "bogus_rt"]) is False
    )


def test_has_all_at_unknown_feature_wins_over_other_axes(ent):
    assert (
        ent.has_all_at(
            "cloud_pro",
            features=["bogus_xyz"],
            runtimes=["openclaw"],
            channels=1,
        )
        is False
    )


# -- Scalar: non-int capacity --------------------------------------------------


def test_has_all_at_non_int_channels_is_false(ent):
    assert ent.has_all_at("cloud_pro", channels="five") is False  # type: ignore[arg-type]


def test_has_all_at_non_int_nodes_is_false(ent):
    assert ent.has_all_at("cloud_pro", nodes="two") is False  # type: ignore[arg-type]


def test_has_all_at_non_int_retention_is_false(ent):
    assert ent.has_all_at("cloud_pro", retention_days="seven") is False  # type: ignore[arg-type]


# -- Scalar: retention_days=None means unsupplied ------------------------------


def test_has_all_at_retention_none_is_unsupplied_not_unlimited(ent):
    assert ent.has_all_at("cloud_pro", channels=1, retention_days=None) is True
    assert ent.has_all_at("cloud_pro", channels=1) is True


# -- Scalar: never raises ------------------------------------------------------


def test_has_all_at_never_raises_on_delegate_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("delegate blowup")

    monkeypatch.setattr(ent, "has_features_at", _boom)
    assert ent.has_all_at("cloud_pro", features=["fleet"]) is False


def test_has_all_at_never_raises_on_capacity_delegate_blowup(monkeypatch, ent):
    def _boom(*a, **kw):
        raise RuntimeError("blowup")

    monkeypatch.setattr(ent, "has_channel_count_at", _boom)
    assert ent.has_all_at("cloud_pro", channels=1) is False


# -- Endpoint: perspective validation ------------------------------------------


def test_endpoint_missing_tier_is_400(client):
    resp = client.get("/api/entitlement/has-all-at")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing tier"}


def test_endpoint_blank_tier_is_400(client):
    resp = client.get("/api/entitlement/has-all-at?tier=&features=fleet")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing tier"}


def test_endpoint_unknown_tier_is_404(client):
    resp = client.get(
        "/api/entitlement/has-all-at?tier=bogus_tier&features=fleet"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus_tier"


def test_endpoint_perspective_case_and_whitespace_normalised(client):
    lower = _get_json(client, "/api/entitlement/has-all-at?tier=cloud_pro&features=fleet")
    upper = _get_json(client, "/api/entitlement/has-all-at?tier=%20CLOUD_PRO%20&features=fleet")
    assert upper["has_all_at"] == lower["has_all_at"]
    assert upper["perspective_tier"] == "cloud_pro"


# -- Endpoint: envelope shape --------------------------------------------------


def test_endpoint_no_axes_shape(client):
    body = _get_json(client, "/api/entitlement/has-all-at?tier=cloud_pro")
    assert set(body.keys()) == _HAS_ALL_AT_KEYS
    assert body["perspective_tier"] == "cloud_pro"
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["channels"] is None
    assert body["retention_days"] is None
    assert body["nodes"] is None
    assert body["unknown_features"] == []
    assert body["unknown_runtimes"] == []
    assert body["supplied_axes"] == []
    assert body["supplied_count"] == 0
    assert body["has_all_at"] is False
    assert body["allowed"] is False


def test_endpoint_all_free_axes_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at?tier=oss"
        "&features=nemo_governance&runtimes=openclaw"
        "&channels=1&retention_days=1&nodes=1",
    )
    assert set(body.keys()) == _HAS_ALL_AT_KEYS
    assert body["perspective_tier"] == "oss"
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
    assert body["has_all_at"] is True
    assert body["allowed"] is True


def test_endpoint_paid_bundle_at_cloud_pro_is_true(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at?tier=cloud_pro"
        "&features=fleet&runtimes=claude_code",
    )
    assert body["has_all_at"] is True
    assert body["allowed"] is True


def test_endpoint_paid_bundle_at_oss_is_false_even_in_grace(client):
    body = _get_json(
        client, "/api/entitlement/has-all-at?tier=oss&features=fleet"
    )
    assert body["has_all_at"] is False
    assert body["allowed"] is False
    assert body["grace"] is True


def test_endpoint_supplied_axes_order_stable(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at?tier=cloud_pro&nodes=1&features=fleet"
        "&channels=1&retention_days=1&runtimes=claude_code",
    )
    assert body["supplied_axes"] == [
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
    ]


# -- Endpoint: unknown tokens --------------------------------------------------


def test_endpoint_unknown_feature_collapses_bundle(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at?tier=cloud_pro"
        "&features=fleet,totally_fake_xyz",
    )
    assert body["features"] == ["fleet"]
    assert body["unknown_features"] == ["totally_fake_xyz"]
    assert body["has_all_at"] is False
    assert body["allowed"] is False


def test_endpoint_unknown_runtime_collapses_bundle(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at?tier=cloud_pro"
        "&runtimes=openclaw,totally_fake_rt",
    )
    assert body["runtimes"] == ["openclaw"]
    assert body["unknown_runtimes"] == ["totally_fake_rt"]
    assert body["has_all_at"] is False


def test_endpoint_runtime_alias_canonicalises(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at?tier=cloud_pro"
        "&runtimes=claude-code,claude_code",
    )
    assert body["runtimes"] == ["claude_code"]
    assert body["unknown_runtimes"] == []
    assert body["has_all_at"] is True


# -- Endpoint: capacity axes ---------------------------------------------------


def test_endpoint_non_int_channels_collapses_bundle(client):
    body = _get_json(
        client, "/api/entitlement/has-all-at?tier=cloud_pro&channels=five"
    )
    assert body["supplied_axes"] == ["channels"]
    assert body["channels"] is None
    assert body["has_all_at"] is False


def test_endpoint_blank_channels_collapses_bundle(client):
    body = _get_json(
        client, "/api/entitlement/has-all-at?tier=cloud_pro&channels="
    )
    assert body["supplied_axes"] == ["channels"]
    assert body["channels"] is None
    assert body["has_all_at"] is False


def test_endpoint_zero_channels_is_true(client):
    body = _get_json(
        client, "/api/entitlement/has-all-at?tier=cloud_pro&channels=0"
    )
    assert body["supplied_axes"] == ["channels"]
    assert body["channels"] == 0
    assert body["has_all_at"] is True


def test_endpoint_oss_denies_five_nodes(client):
    body = _get_json(
        client, "/api/entitlement/has-all-at?tier=oss&nodes=5"
    )
    assert body["nodes"] == 5
    assert body["has_all_at"] is False


def test_endpoint_cloud_pro_admits_thousand_nodes(client):
    body = _get_json(
        client, "/api/entitlement/has-all-at?tier=cloud_pro&nodes=1000"
    )
    assert body["nodes"] == 1000
    assert body["has_all_at"] is True


# -- Endpoint: enforce mode has byte-stable rows -------------------------------


def test_endpoint_perspective_grace_and_enforce_byte_identical(
    monkeypatch, tmp_path
):
    """Perspective-shaped answers must be identical grace vs enforce
    for the same (perspective, bundle) input."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    grace_client = app.test_client()
    grace_body = grace_client.get(
        "/api/entitlement/has-all-at?tier=cloud_pro"
        "&features=fleet&runtimes=claude_code&channels=5"
    ).get_json()

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    enforce_app = Flask(__name__)
    enforce_app.register_blueprint(bp_entitlement)
    enforce_body = enforce_app.test_client().get(
        "/api/entitlement/has-all-at?tier=cloud_pro"
        "&features=fleet&runtimes=claude_code&channels=5"
    ).get_json()

    assert grace_body["has_all_at"] == enforce_body["has_all_at"]
    assert grace_body["perspective_tier"] == enforce_body["perspective_tier"]
    assert grace_body["features"] == enforce_body["features"]
    assert grace_body["runtimes"] == enforce_body["runtimes"]
    assert grace_body["channels"] == enforce_body["channels"]
    assert grace_body["required_tier"] == enforce_body["required_tier"]
    assert grace_body["grace"] != enforce_body["grace"]
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)


# -- Endpoint: never 5xx -------------------------------------------------------


def test_endpoint_never_5xx_on_body_blowup(monkeypatch, client):
    def _boom(*a, **kw):
        raise RuntimeError("blowup in body builder")

    monkeypatch.setattr("routes.entitlement._has_all_at_body", _boom)
    resp = client.get(
        "/api/entitlement/has-all-at?tier=cloud_pro&features=fleet&channels=5"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _HAS_ALL_AT_KEYS
    assert body["has_all_at"] is False
    assert body["allowed"] is False
    assert body["perspective_tier"] == "cloud_pro"


def test_endpoint_never_5xx_on_scalar_blowup(monkeypatch, client):
    from clawmetry import entitlements as _ent

    def _boom(*a, **kw):
        raise RuntimeError("boom in scalar")

    monkeypatch.setattr(_ent, "has_all_at", _boom)
    resp = client.get(
        "/api/entitlement/has-all-at?tier=cloud_pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _HAS_ALL_AT_KEYS
    assert body["has_all_at"] is False


# -- Endpoint: never 4xx on axis-side inputs (400 only on tier=) ---------------


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-all-at?tier=cloud_pro",
        "/api/entitlement/has-all-at?tier=cloud_pro&features=",
        "/api/entitlement/has-all-at?tier=cloud_pro&runtimes=",
        "/api/entitlement/has-all-at?tier=cloud_pro&channels=",
        "/api/entitlement/has-all-at?tier=cloud_pro&features=fleet&channels=notanint",
        "/api/entitlement/has-all-at?tier=cloud_pro&features=bogus_only",
        "/api/entitlement/has-all-at?tier=cloud_pro&features=fleet,,,",
        "/api/entitlement/has-all-at?tier=oss&nodes=100",
        "/api/entitlement/has-all-at?tier=trial&features=fleet",
    ],
)
def test_endpoint_never_4xx_on_axis_side(client, url):
    resp = client.get(url)
    assert resp.status_code == 200, url
    body = resp.get_json()
    assert set(body.keys()) == _HAS_ALL_AT_KEYS


# -- Endpoint: scalar-vs-endpoint parity ---------------------------------------


@pytest.mark.parametrize(
    "url,tier,features,runtimes,channels,retention_days,nodes",
    [
        (
            "/api/entitlement/has-all-at?tier=oss&features=fleet",
            "oss",
            ["fleet"],
            None,
            None,
            None,
            None,
        ),
        (
            "/api/entitlement/has-all-at?tier=cloud_pro&features=fleet&runtimes=claude_code",
            "cloud_pro",
            ["fleet"],
            ["claude_code"],
            None,
            None,
            None,
        ),
        (
            "/api/entitlement/has-all-at?tier=oss&channels=5&nodes=2",
            "oss",
            None,
            None,
            5,
            None,
            2,
        ),
        (
            "/api/entitlement/has-all-at?tier=oss&features=nemo_governance"
            "&runtimes=openclaw&channels=1&retention_days=1&nodes=1",
            "oss",
            ["nemo_governance"],
            ["openclaw"],
            1,
            1,
            1,
        ),
        (
            "/api/entitlement/has-all-at?tier=enterprise"
            "&features=fleet,bogus_xyz",
            "enterprise",
            ["fleet", "bogus_xyz"],
            None,
            None,
            None,
            None,
        ),
    ],
)
def test_endpoint_matches_scalar(
    client, ent, url, tier, features, runtimes, channels, retention_days, nodes
):
    body = _get_json(client, url)
    expected = ent.has_all_at(
        tier,
        features=features,
        runtimes=runtimes,
        channels=channels,
        retention_days=retention_days,
        nodes=nodes,
    )
    assert body["has_all_at"] is expected
    assert body["allowed"] is expected


# -- Cross-consistency with singular _at endpoints -----------------------------


@pytest.mark.parametrize(
    "tier,feature",
    [
        ("oss", "fleet"),
        ("cloud_pro", "fleet"),
        ("enterprise", "sso"),
    ],
)
def test_cross_consistent_with_has_feature_at(client, tier, feature):
    all_body = _get_json(
        client,
        f"/api/entitlement/has-all-at?tier={tier}&features={feature}",
    )
    single = _get_json(
        client,
        f"/api/entitlement/has-feature-at?tier={tier}&feature={feature}",
    )
    assert all_body["has_all_at"] is single["has_feature_at"]


@pytest.mark.parametrize(
    "tier,runtime",
    [
        ("oss", "claude_code"),
        ("cloud_pro", "claude_code"),
        ("cloud_pro", "codex"),
    ],
)
def test_cross_consistent_with_has_runtime_at(client, tier, runtime):
    all_body = _get_json(
        client,
        f"/api/entitlement/has-all-at?tier={tier}&runtimes={runtime}",
    )
    single = _get_json(
        client,
        f"/api/entitlement/has-runtime-at?tier={tier}&runtime={runtime}",
    )
    assert all_body["has_all_at"] is single["has_runtime_at"]


@pytest.mark.parametrize(
    "tier,count",
    [
        ("oss", 1),
        ("oss", 100),
        ("cloud_pro", 5),
        ("cloud_pro", 999),
    ],
)
def test_cross_consistent_with_has_channel_count_at(client, tier, count):
    all_body = _get_json(
        client,
        f"/api/entitlement/has-all-at?tier={tier}&channels={count}",
    )
    single = _get_json(
        client,
        f"/api/entitlement/has-channel-count-at?tier={tier}&count={count}",
    )
    assert all_body["has_all_at"] is single["has_channel_count_at"]


@pytest.mark.parametrize(
    "tier,count",
    [
        ("oss", 1),
        ("oss", 5),
        ("cloud_pro", 1000),
    ],
)
def test_cross_consistent_with_has_node_count_at(client, tier, count):
    all_body = _get_json(
        client,
        f"/api/entitlement/has-all-at?tier={tier}&nodes={count}",
    )
    single = _get_json(
        client,
        f"/api/entitlement/has-node-count-at?tier={tier}&count={count}",
    )
    assert all_body["has_all_at"] is single["has_node_count_at"]


# -- Divergence from LIVE /has-all --------------------------------------------


def test_divergence_from_live_has_all_on_oss_paid_feature(client):
    """LIVE /has-all reports True in grace for a paid feature; /has-all-at
    at OSS reports False (the whole point of the _at slot)."""
    live = _get_json(client, "/api/entitlement/has-all?features=fleet")
    perspective = _get_json(
        client, "/api/entitlement/has-all-at?tier=oss&features=fleet"
    )
    assert live["has_all"] is True
    assert perspective["has_all_at"] is False


def test_agreement_with_live_has_all_when_perspective_matches_current(client):
    """When perspective_tier == current_tier the boolean equals the LIVE
    /has-all rollup byte-for-byte for the same fully-known bundle."""
    live = _get_json(
        client,
        "/api/entitlement/has-all?features=nemo_governance&runtimes=openclaw",
    )
    cur = live["current_tier"]
    perspective = _get_json(
        client,
        f"/api/entitlement/has-all-at?tier={cur}"
        "&features=nemo_governance&runtimes=openclaw",
    )
    assert live["has_all"] is perspective["has_all_at"]


# -- Envelope key set stability across every input branch ----------------------


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-all-at?tier=oss",
        "/api/entitlement/has-all-at?tier=cloud_pro&features=fleet",
        "/api/entitlement/has-all-at?tier=enterprise&features=fleet&runtimes=claude_code&channels=5&retention_days=30&nodes=100",
        "/api/entitlement/has-all-at?tier=oss&features=bogus",
        "/api/entitlement/has-all-at?tier=oss&channels=notanint",
        "/api/entitlement/has-all-at?tier=trial&features=fleet",
    ],
)
def test_envelope_keyset_stable(client, url):
    body = _get_json(client, url)
    assert set(body.keys()) == _HAS_ALL_AT_KEYS


def test_envelope_omits_upgrade_required(client):
    """Perspective-shaped ``_at`` slots deliberately omit
    ``upgrade_required`` -- comparing against the LIVE current-tier
    rank would double-count the perspective (matches the singular
    ``/has-feature-at`` / ``/has-runtime-at`` siblings)."""
    body = _get_json(
        client, "/api/entitlement/has-all-at?tier=cloud_pro&features=fleet"
    )
    assert "upgrade_required" not in body
