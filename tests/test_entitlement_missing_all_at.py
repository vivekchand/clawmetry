"""Tests for the hypothetical-perspective mixed-axis ``missing_all_at(...)``
row-detail complement scalar and its paired ``/api/entitlement/missing-all-at``
endpoint.

Perspective-shaped row-detail sibling of :func:`clawmetry.entitlements.missing_all`
(which folds the same five kwargs against the LIVE resolver): a paywall
diagnostics tile that renders per-axis denial detail per hypothetical tier
("if I were on OSS, you'd still be missing fleet + claude_code + 100 channels")
binds every per-axis slot off ONE call per (perspective, bundle) cell instead
of five singular ``_at`` round-trips + a client-side per-axis stitch.

This file pins:

1. Scalar per-axis rules under grace vs enforce for every combination of the
   five axes (features / runtimes / channels / retention_days / nodes),
   including per-axis empty / None / unknown / non-int inputs.
2. Perspective validation (empty / non-string / unknown -> empty per-axis
   dict at the scalar; 400 / 404 at the endpoint).
3. **Grace-independence invariant**: ``missing_all_at(p, ...)`` returns the
   same per-axis dict under both grace and enforce for every ``p`` and every
   input (delegates to the singular ``_at`` scalars, which are backed by the
   static per-tier tables via :func:`_hypothetical_entitlement`).
4. Endpoint envelope shape parity (fixed 21-key set) across every input
   branch so a frontend can bind fields off the URL without a branch on
   the underlying resolver state.
5. Never-4xx on axis-side inputs; 400 on missing / blank tier; 404 on
   unknown tier; never 5xx.
6. Cross-consistency with the singular ``/missing-features-at`` /
   ``/missing-runtimes-at`` endpoints on the two grant axes.
7. Scalar-vs-endpoint parity on the known-only subsets (the endpoint's
   per-axis missing list is a strict superset of the scalar's -- unknown
   tokens are appended at endpoint layer for the diagnostics tooltip).
8. Symmetry with :func:`has_all_at`: ``any(missing_all_at(p, **b).values())``
   is the strict negation of ``has_all_at(p, **b)`` on every fully-parseable
   bundle.
9. Deliberate divergence from the LIVE ``/missing-all`` sibling: a bundle
   the resolver grants under grace can still report a non-empty per-axis
   missing list on the OSS perspective (that's the whole point of the
   ``_at`` slot).
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

_MISSING_ALL_AT_KEYS = {
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
    "missing_count",
    "any_missing",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}

_SCALAR_KEYS = {"features", "runtimes", "channels", "retention_days", "nodes"}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


# -- Scalar: perspective validation --------------------------------------------


def test_missing_all_at_unknown_perspective_is_empty(ent):
    out = ent.missing_all_at("bogus", features=["fleet"])
    assert set(out.keys()) == _SCALAR_KEYS
    assert out == {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


def test_missing_all_at_empty_perspective_is_empty(ent):
    out = ent.missing_all_at("", features=["fleet"])
    assert out["features"] == []


def test_missing_all_at_none_perspective_is_empty(ent):
    out = ent.missing_all_at(None, features=["fleet"])  # type: ignore[arg-type]
    assert out["features"] == []


def test_missing_all_at_non_string_perspective_is_empty(ent):
    out = ent.missing_all_at(123, features=["fleet"])  # type: ignore[arg-type]
    assert out["features"] == []


def test_missing_all_at_perspective_case_and_whitespace_normalised(ent):
    a = ent.missing_all_at("  CLOUD_PRO  ", features=["fleet"])
    b = ent.missing_all_at("cloud_pro", features=["fleet"])
    assert a == b


# -- Scalar: no axes supplied --------------------------------------------------


def test_missing_all_at_no_axes_supplied_is_empty(ent):
    """Nothing supplied -> every per-axis slot empty."""
    for tier in ent._TIER_ORDER:
        assert ent.missing_all_at(tier) == {
            "features": [],
            "runtimes": [],
            "channels": None,
            "retention_days": None,
            "nodes": None,
        }, tier


def test_missing_all_at_no_axes_supplied_is_empty_after_enforcement(enforced):
    for tier in enforced._TIER_ORDER:
        out = enforced.missing_all_at(tier)
        assert out["features"] == [] and out["runtimes"] == []
        assert (
            out["channels"] is None
            and out["retention_days"] is None
            and out["nodes"] is None
        )


# -- Scalar: shape stability ---------------------------------------------------


def test_missing_all_at_shape_stable_across_axis_combos(ent):
    combos = [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"]},
        {"channels": 100},
        {"retention_days": 90},
        {"nodes": 99},
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {
            "features": ["fleet"],
            "runtimes": ["claude_code"],
            "channels": 100,
            "retention_days": 90,
            "nodes": 99,
        },
    ]
    for kw in combos:
        out = ent.missing_all_at("oss", **kw)  # type: ignore[arg-type]
        assert set(out.keys()) == _SCALAR_KEYS, kw


# -- Scalar: perspective-shaped semantics on free bundles ----------------------


def test_missing_all_at_oss_free_bundle_is_empty(ent):
    free_f = next(iter(ent.FREE_FEATURES))
    free_r = next(iter(ent.FREE_RUNTIMES))
    out = ent.missing_all_at(
        "oss",
        features=[free_f],
        runtimes=[free_r],
        channels=1,
        retention_days=1,
        nodes=1,
    )
    assert out == {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


def test_missing_all_at_every_tier_admits_free_bundle(ent):
    free_f = next(iter(ent.FREE_FEATURES))
    free_r = next(iter(ent.FREE_RUNTIMES))
    for tier in ent._TIER_ORDER:
        out = ent.missing_all_at(
            tier,
            features=[free_f],
            runtimes=[free_r],
            channels=1,
            retention_days=1,
            nodes=1,
        )
        assert not any(
            [out["features"], out["runtimes"]]
        ), tier
        assert (
            out["channels"] is None
            and out["retention_days"] is None
            and out["nodes"] is None
        ), tier


# -- Scalar: perspective-shaped semantics on paid bundles ----------------------


def test_missing_all_at_oss_denies_paid_feature(ent):
    paid_f = next(iter(ent.PAID_FEATURES))
    out = ent.missing_all_at("oss", features=[paid_f])
    assert out["features"] == [paid_f]


def test_missing_all_at_oss_denies_paid_runtime(ent):
    paid_r = next(iter(ent.PAID_RUNTIMES))
    out = ent.missing_all_at("oss", runtimes=[paid_r])
    assert out["runtimes"] == [paid_r]


def test_missing_all_at_oss_denies_big_channels(ent):
    out = ent.missing_all_at("oss", channels=100)
    assert out["channels"] == 100


def test_missing_all_at_oss_denies_big_retention(ent):
    out = ent.missing_all_at("oss", retention_days=365)
    assert out["retention_days"] == 365


def test_missing_all_at_oss_denies_big_nodes(ent):
    out = ent.missing_all_at("oss", nodes=99)
    assert out["nodes"] == 99


def test_missing_all_at_cloud_pro_admits_paid_bundle(ent):
    paid_f = next(iter(ent.PAID_FEATURES))
    paid_r = next(iter(ent.PAID_RUNTIMES))
    out = ent.missing_all_at(
        "cloud_pro",
        features=[paid_f],
        runtimes=[paid_r],
        channels=100,
        retention_days=90,
        nodes=1000,
    )
    assert out["features"] == []
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


def test_missing_all_at_enterprise_admits_paid_bundle(ent):
    paid_f = next(iter(ent.PAID_FEATURES))
    paid_r = next(iter(ent.PAID_RUNTIMES))
    out = ent.missing_all_at(
        "enterprise",
        features=[paid_f],
        runtimes=[paid_r],
        channels=999,
        retention_days=999999,
        nodes=99999,
    )
    assert out["features"] == []
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


def test_missing_all_at_oss_denies_every_axis_on_full_paid_bundle(ent):
    paid_f = next(iter(ent.PAID_FEATURES))
    paid_r = next(iter(ent.PAID_RUNTIMES))
    out = ent.missing_all_at(
        "oss",
        features=[paid_f],
        runtimes=[paid_r],
        channels=100,
        retention_days=90,
        nodes=99,
    )
    assert out["features"] == [paid_f]
    assert out["runtimes"] == [paid_r]
    assert out["channels"] == 100
    assert out["retention_days"] == 90
    assert out["nodes"] == 99


# -- Scalar: grace-independence invariant --------------------------------------


def test_missing_all_at_grace_vs_enforce_byte_identical_on_oss(
    monkeypatch, tmp_path
):
    """The whole point of the ``_at`` slot: perspective-shaped answers
    read the static per-tier tables and are grace-independent."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    paid_f = next(iter(e.PAID_FEATURES))
    paid_r = next(iter(e.PAID_RUNTIMES))
    grace = e.missing_all_at(
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
    enforce = e.missing_all_at(
        "oss",
        features=[paid_f],
        runtimes=[paid_r],
        channels=5,
        retention_days=30,
        nodes=2,
    )
    assert grace == enforce
    assert grace["features"] == [paid_f]


def test_missing_all_at_grace_vs_enforce_byte_identical_on_cloud_pro(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    paid_f = next(iter(e.PAID_FEATURES))
    paid_r = next(iter(e.PAID_RUNTIMES))
    grace = e.missing_all_at(
        "cloud_pro", features=[paid_f], runtimes=[paid_r], channels=5
    )

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    enforce = e.missing_all_at(
        "cloud_pro", features=[paid_f], runtimes=[paid_r], channels=5
    )
    assert grace == enforce
    assert grace["features"] == []


# -- Scalar: divergence from live missing_all in grace -------------------------


def test_missing_all_at_diverges_from_missing_features_on_oss_paid_bundle(ent):
    """LIVE missing_features reports [] in grace; _at reports the paid
    feature from the OSS perspective (static per-tier tables). Whole
    point of the slot."""
    paid_f = next(iter(ent.PAID_FEATURES))
    live = ent.missing_features([paid_f])
    perspective = ent.missing_all_at("oss", features=[paid_f])
    assert live == []
    assert perspective["features"] == [paid_f]


# -- Scalar: empty inputs on supplied axes -------------------------------------


def test_missing_all_at_features_empty_iterable(ent):
    out = ent.missing_all_at("cloud_pro", features=[])
    assert out["features"] == []
    out = ent.missing_all_at("cloud_pro", features=())
    assert out["features"] == []


def test_missing_all_at_runtimes_empty_iterable(ent):
    out = ent.missing_all_at("cloud_pro", runtimes=[])
    assert out["runtimes"] == []


# -- Scalar: unknown / typo'd inputs -------------------------------------------


def test_missing_all_at_unknown_feature_included_in_missing(ent):
    """Unknown/typo'd feature surfaces IN the missing list (matches
    :func:`missing_features_at` typo posture)."""
    out = ent.missing_all_at("cloud_pro", features=["fleet", "bogus_xyz"])
    # Cloud Pro grants fleet -> only the typo surfaces.
    assert out["features"] == ["bogus_xyz"]


def test_missing_all_at_unknown_runtime_included_in_missing(ent):
    out = ent.missing_all_at("cloud_pro", runtimes=["openclaw", "bogus_rt"])
    assert out["runtimes"] == ["bogus_rt"]


# -- Scalar: non-int capacity --------------------------------------------------


def test_missing_all_at_non_int_channels_is_none(ent):
    """Non-int capacity swallows to None on the scalar (paired has_all_at
    reports False via strict singular scalar; a UI wanting the coherent
    'supplied but denied' story on this branch should call has_all_at)."""
    out = ent.missing_all_at("cloud_pro", channels="five")  # type: ignore[arg-type]
    assert out["channels"] is None


def test_missing_all_at_non_int_nodes_is_none(ent):
    out = ent.missing_all_at("cloud_pro", nodes="two")  # type: ignore[arg-type]
    assert out["nodes"] is None


def test_missing_all_at_non_int_retention_is_none(ent):
    out = ent.missing_all_at("cloud_pro", retention_days="seven")  # type: ignore[arg-type]
    assert out["retention_days"] is None


def test_missing_all_at_bool_channels_is_none(ent):
    """`True`/`False` on capacity axes should NOT be silently coerced to
    1/0 via the isinstance-int leak that bool inherits from int."""
    out = ent.missing_all_at("oss", channels=True)  # type: ignore[arg-type]
    assert out["channels"] is None


# -- Scalar: retention_days=None means unsupplied ------------------------------


def test_missing_all_at_retention_none_is_unsupplied_not_unlimited(ent):
    out = ent.missing_all_at("cloud_pro", channels=1, retention_days=None)
    assert out["retention_days"] is None
    assert out["channels"] is None


# -- Scalar: symmetry with has_all_at ------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"]},
        {"channels": 100},
        {"retention_days": 90},
        {"nodes": 99},
        {"features": ["fleet"], "channels": 5},
        {
            "features": ["fleet"],
            "runtimes": ["claude_code"],
            "channels": 100,
            "retention_days": 90,
            "nodes": 99,
        },
    ],
)
@pytest.mark.parametrize("tier", ["oss", "cloud_starter", "cloud_pro", "enterprise"])
def test_missing_all_at_negates_has_all_at_on_fully_parseable_bundles(
    ent, tier, kwargs
):
    """``any(missing_all_at(p, **b).values())`` is the strict negation of
    ``has_all_at(p, **b)`` on every fully-parseable bundle."""
    missing = ent.missing_all_at(tier, **kwargs)  # type: ignore[arg-type]
    has = ent.has_all_at(tier, **kwargs)
    any_missing = any(
        [
            missing["features"],
            missing["runtimes"],
            missing["channels"] is not None,
            missing["retention_days"] is not None,
            missing["nodes"] is not None,
        ]
    )
    assert any_missing == (not has), (tier, kwargs, missing, has)


# -- Scalar: cross-consistency with singular missing_*_at ----------------------


def test_missing_all_at_features_matches_singular(ent):
    for tier in ent._TIER_ORDER:
        for bundle in ([], ["fleet"], ["nemo_governance"], ["fleet", "sso"]):
            out = ent.missing_all_at(tier, features=bundle)
            assert out["features"] == list(
                ent.missing_features_at(tier, bundle)
            ), (tier, bundle)


def test_missing_all_at_runtimes_matches_singular(ent):
    for tier in ent._TIER_ORDER:
        for bundle in ([], ["openclaw"], ["claude_code"], ["openclaw", "claude_code"]):
            out = ent.missing_all_at(tier, runtimes=bundle)
            assert out["runtimes"] == list(
                ent.missing_runtimes_at(tier, bundle)
            ), (tier, bundle)


# -- Scalar: never raises ------------------------------------------------------


def test_missing_all_at_never_raises_on_features_delegate_blowup(
    monkeypatch, ent
):
    def _boom(*a, **kw):
        raise RuntimeError("delegate blowup")

    monkeypatch.setattr(ent, "missing_features_at", _boom)
    out = ent.missing_all_at("cloud_pro", features=["fleet"])
    assert out["features"] == []


def test_missing_all_at_never_raises_on_runtimes_delegate_blowup(
    monkeypatch, ent
):
    def _boom(*a, **kw):
        raise RuntimeError("delegate blowup")

    monkeypatch.setattr(ent, "missing_runtimes_at", _boom)
    out = ent.missing_all_at("cloud_pro", runtimes=["openclaw"])
    assert out["runtimes"] == []


def test_missing_all_at_never_raises_on_capacity_delegate_blowup(
    monkeypatch, ent
):
    def _boom(*a, **kw):
        raise RuntimeError("blowup")

    monkeypatch.setattr(ent, "has_channel_count_at", _boom)
    out = ent.missing_all_at("cloud_pro", channels=1)
    assert out["channels"] is None


# -- Endpoint: perspective validation ------------------------------------------


def test_endpoint_missing_tier_is_400(client):
    resp = client.get("/api/entitlement/missing-all-at")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing tier"}


def test_endpoint_blank_tier_is_400(client):
    resp = client.get("/api/entitlement/missing-all-at?tier=&features=fleet")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "missing tier"}


def test_endpoint_unknown_tier_is_404(client):
    resp = client.get(
        "/api/entitlement/missing-all-at?tier=bogus_tier&features=fleet"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus_tier"


def test_endpoint_perspective_case_and_whitespace_normalised(client):
    lower = _get_json(
        client, "/api/entitlement/missing-all-at?tier=cloud_pro&features=fleet"
    )
    upper = _get_json(
        client,
        "/api/entitlement/missing-all-at?tier=%20CLOUD_PRO%20&features=fleet",
    )
    assert upper["features"] == lower["features"]
    assert upper["perspective_tier"] == "cloud_pro"


# -- Endpoint: envelope shape --------------------------------------------------


def test_endpoint_no_axes_shape(client):
    body = _get_json(client, "/api/entitlement/missing-all-at?tier=cloud_pro")
    assert set(body.keys()) == _MISSING_ALL_AT_KEYS
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
    assert body["missing_count"] == 0
    assert body["any_missing"] is False


def test_endpoint_all_free_axes_shape(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at?tier=oss"
        "&features=nemo_governance&runtimes=openclaw"
        "&channels=1&retention_days=1&nodes=1",
    )
    assert set(body.keys()) == _MISSING_ALL_AT_KEYS
    assert body["perspective_tier"] == "oss"
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["channels"] is None
    assert body["retention_days"] is None
    assert body["nodes"] is None
    assert body["supplied_axes"] == [
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
    ]
    assert body["supplied_count"] == 5
    assert body["missing_count"] == 0
    assert body["any_missing"] is False


def test_endpoint_paid_bundle_at_oss_is_denied_even_in_grace(client):
    body = _get_json(
        client, "/api/entitlement/missing-all-at?tier=oss&features=fleet"
    )
    assert body["features"] == ["fleet"]
    assert body["missing_count"] == 1
    assert body["any_missing"] is True
    assert body["grace"] is True


def test_endpoint_paid_bundle_at_cloud_pro_is_admitted(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at?tier=cloud_pro"
        "&features=fleet&runtimes=claude_code",
    )
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["missing_count"] == 0
    assert body["any_missing"] is False


def test_endpoint_full_paid_bundle_at_oss_missing_count_five(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at?tier=oss"
        "&features=fleet&runtimes=claude_code"
        "&channels=100&retention_days=90&nodes=99",
    )
    assert body["features"] == ["fleet"]
    assert body["runtimes"] == ["claude_code"]
    assert body["channels"] == 100
    assert body["retention_days"] == 90
    assert body["nodes"] == 99
    assert body["missing_count"] == 5
    assert body["any_missing"] is True


# -- Endpoint: unknown / typo tokens -------------------------------------------


def test_endpoint_unknown_feature_surfaces_inside_missing_and_unknown_split(
    client,
):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at?tier=cloud_pro&features=fleet,totally_fake_xyz",
    )
    # Cloud Pro grants fleet -> only the typo surfaces in features.
    assert body["features"] == ["totally_fake_xyz"]
    assert body["unknown_features"] == ["totally_fake_xyz"]
    assert body["any_missing"] is True


def test_endpoint_unknown_runtime_surfaces_inside_missing_and_unknown_split(
    client,
):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at?tier=cloud_pro&runtimes=claude_code,totally_fake_rt",
    )
    assert body["runtimes"] == ["totally_fake_rt"]
    assert body["unknown_runtimes"] == ["totally_fake_rt"]


def test_endpoint_runtime_alias_canonicalisation(client):
    """`claude-code` (hyphen) canonicalises to `claude_code` (underscore)
    upstream of the strict scalar; a Cloud Pro perspective admits it so
    the missing list is empty."""
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at?tier=cloud_pro&runtimes=claude-code",
    )
    assert body["runtimes"] == []
    assert body["unknown_runtimes"] == []


# -- Endpoint: capacity typo posture ------------------------------------------


def test_endpoint_non_int_channels_surfaces_raw_string(client):
    body = _get_json(
        client, "/api/entitlement/missing-all-at?tier=cloud_pro&channels=five"
    )
    assert body["channels"] == "five"
    assert body["supplied_axes"] == ["channels"]
    assert body["any_missing"] is True


def test_endpoint_blank_capacity_surfaces_raw_string(client):
    body = _get_json(
        client, "/api/entitlement/missing-all-at?tier=cloud_pro&channels="
    )
    # Blank capacity: raw string echoed (matches the sibling has-all-at
    # posture where a supplied-but-unparseable axis collapses the fold).
    assert body["supplied_axes"] == ["channels"]
    assert body["channels"] == ""


def test_endpoint_zero_channels_admitted_by_free_floor(client):
    body = _get_json(
        client, "/api/entitlement/missing-all-at?tier=oss&channels=0"
    )
    assert body["channels"] is None
    assert body["missing_count"] == 0


# -- Endpoint: cross-consistency with singular missing-*-at --------------------


def test_endpoint_features_matches_singular_missing_features_at(client):
    for tier in ("oss", "cloud_starter", "cloud_pro", "enterprise"):
        url_all = (
            f"/api/entitlement/missing-all-at?tier={tier}&features=fleet,sso"
        )
        url_one = (
            f"/api/entitlement/missing-features-at?tier={tier}&features=fleet,sso"
        )
        body_all = _get_json(client, url_all)
        body_one = _get_json(client, url_one)
        assert body_all["features"] == body_one["missing"], tier


def test_endpoint_runtimes_matches_singular_missing_runtimes_at(client):
    for tier in ("oss", "cloud_starter", "cloud_pro", "enterprise"):
        url_all = (
            f"/api/entitlement/missing-all-at?tier={tier}"
            "&runtimes=openclaw,claude_code"
        )
        url_one = (
            f"/api/entitlement/missing-runtimes-at?tier={tier}"
            "&runtimes=openclaw,claude_code"
        )
        body_all = _get_json(client, url_all)
        body_one = _get_json(client, url_one)
        assert body_all["runtimes"] == body_one["missing"], tier


# -- Endpoint: scalar vs endpoint parity ---------------------------------------


@pytest.mark.parametrize(
    "url_kwargs, scalar_kwargs",
    [
        ("features=fleet", {"features": ["fleet"]}),
        ("runtimes=claude_code", {"runtimes": ["claude_code"]}),
        ("channels=100", {"channels": 100}),
        ("retention_days=90", {"retention_days": 90}),
        ("nodes=99", {"nodes": 99}),
        (
            "features=fleet&runtimes=claude_code&channels=100&retention_days=90&nodes=99",
            {
                "features": ["fleet"],
                "runtimes": ["claude_code"],
                "channels": 100,
                "retention_days": 90,
                "nodes": 99,
            },
        ),
    ],
)
def test_endpoint_scalar_vs_body_parity_on_known_only_bundles(
    client, ent, url_kwargs, scalar_kwargs
):
    for tier in ("oss", "cloud_starter", "cloud_pro", "enterprise"):
        body = _get_json(
            client, f"/api/entitlement/missing-all-at?tier={tier}&{url_kwargs}"
        )
        scalar = ent.missing_all_at(tier, **scalar_kwargs)  # type: ignore[arg-type]
        for axis in ("features", "runtimes", "channels", "retention_days", "nodes"):
            assert body[axis] == scalar[axis], (tier, axis, url_kwargs)


# -- Endpoint: never 4xx / never 5xx across every input branch -----------------


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/missing-all-at?tier=cloud_pro",
        "/api/entitlement/missing-all-at?tier=cloud_pro&features=",
        "/api/entitlement/missing-all-at?tier=cloud_pro&runtimes=",
        "/api/entitlement/missing-all-at?tier=cloud_pro&channels=",
        "/api/entitlement/missing-all-at?tier=cloud_pro&features=totally_fake",
        "/api/entitlement/missing-all-at?tier=cloud_pro&runtimes=totally_fake",
        "/api/entitlement/missing-all-at?tier=cloud_pro&channels=five",
    ],
)
def test_endpoint_never_4xx_on_axis_side_inputs(client, url):
    resp = client.get(url)
    assert resp.status_code == 200, url
    body = resp.get_json()
    assert set(body.keys()) == _MISSING_ALL_AT_KEYS


def test_endpoint_never_5xx_on_body_builder_blowup(monkeypatch, client):
    """A body-builder blowup collapses to the fallback envelope with
    stable 21-key shape."""
    import routes.entitlement as re_mod

    def _boom(*a, **kw):
        raise RuntimeError("body builder blowup")

    monkeypatch.setattr(re_mod, "_missing_all_at_body", _boom)
    resp = client.get("/api/entitlement/missing-all-at?tier=cloud_pro&features=fleet")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _MISSING_ALL_AT_KEYS
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["any_missing"] is False


# -- Endpoint: required_tier fold ----------------------------------------------


def test_endpoint_required_tier_folds_through_min_tier_for_all(client, ent):
    body = _get_json(
        client, "/api/entitlement/missing-all-at?tier=oss&features=fleet"
    )
    expected = ent.min_tier_for_all(features=["fleet"])
    assert body["required_tier"] == expected


def test_endpoint_required_tier_is_none_on_no_axes(client):
    body = _get_json(client, "/api/entitlement/missing-all-at?tier=cloud_pro")
    assert body["required_tier"] is None
    assert body["required_tier_label"] is None
    assert body["required_tier_rank"] == -1


# -- Endpoint: resolver envelope carried in grace ------------------------------


def test_endpoint_carries_resolver_envelope(client):
    body = _get_json(client, "/api/entitlement/missing-all-at?tier=cloud_pro")
    assert body["grace"] is True
    assert body["enforced"] is False
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0
