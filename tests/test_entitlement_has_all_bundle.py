"""Tests for the singular row-detail
``/api/entitlement/has-all-bundle`` and
``/api/entitlement/has-all-bundle-at`` endpoints (plus their
:func:`clawmetry.entitlements.has_all_bundle` /
:func:`clawmetry.entitlements.has_all_bundle_at` helpers).

Fills the singular-row slot for the aggregate 5-axis bundle boolean-fold
family alongside the batch ``/has-all-bundle-batch`` /
``/has-all-bundle-batch-at`` endpoints so a paywall walkthrough tile
rendering one hypothetical whole-config cell at a time reads the row
without wrapping in a length-one list and unwrapping ``[0]`` from the
batch.

Distinct from the singular ``/api/entitlement/has-all`` GET endpoint
(whose 19-key diagnostic envelope carries unknown-token splits,
``required_tier`` resolution, and the ``upgrade_required`` rollup): the
singulars here return the stripped six-key batch-row shape so a UI
wiring the singular and the batch off the same helper sees byte-
identical rows across the two endpoints.

These tests pin:

* helper: row shape byte-parity with :func:`has_all_bundle_batch`
* helper: never-crash on ``None`` / non-dict / scalar bundle inputs
* helper: perspective-shaping of the ``_at`` variant (deliberate
  divergence from the LIVE helper at OSS in grace: paid feature -> False)
* helper: perspective-validation ``None`` posture on the ``_at`` variant
  (empty / blank / non-string / unknown perspective -> ``None``)
* API happy path: shape (batch row + resolver envelope), 200
* API error paths: 400 on missing / non-object ``bundle``
* API bare-dict shorthand (top-level body IS the bundle)
* API per-body byte-equals the batch's per-row body on the same bundle
* API ``_at`` perspective envelope keys + 400 on missing ``tier=``,
  404 on unknown ``tier=``, 400 on missing ``bundle``
* API never-5xxs on a delegate crash
* Grace vs enforce parity on the LIVE endpoint; grace-independence on
  the ``_at`` endpoint's ``has_all_at`` fold
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# -- Fixtures ------------------------------------------------------------------


@pytest.fixture
def ent(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
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


# -- Row shape constants -------------------------------------------------------


_LIVE_ROW_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "has_all",
}

_AT_ROW_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "has_all_at",
}

_LIVE_ENVELOPE_KEYS = _LIVE_ROW_KEYS | {
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}

_AT_ENVELOPE_KEYS = _AT_ROW_KEYS | {
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# -- helper: has_all_bundle -----------------------------------------------------


def test_helper_scalar_folds_across_all_five_axes(ent):
    row = ent.has_all_bundle(
        {
            "features": ["fleet"],
            "runtimes": ["claude_code"],
            "channels": 5,
            "retention_days": 30,
            "nodes": 2,
        }
    )
    assert set(row.keys()) == _LIVE_ROW_KEYS
    assert row["features"] == ["fleet"]
    assert row["runtimes"] == ["claude_code"]
    assert row["channels"] == 5
    assert row["retention_days"] == 30
    assert row["nodes"] == 2
    # Grace pass-through: LIVE fold reports True for every fully-known
    # bundle while ent.grace is on.
    assert row["has_all"] is True


def test_helper_scalar_row_byte_equals_batch_row(ent):
    """Row shape byte-parity contract: the singular row byte-equals
    the batch row for the same bundle, on every axis + fold + shape."""
    bundles = [
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 5},
        {"retention_days": 30, "nodes": 2},
        {"features": ["sso"]},
        {"features": ["FLEET", "fleet"], "runtimes": ["claude-code"]},
        {"channels": "abc", "retention_days": "", "nodes": None},
        {},
    ]
    for bundle in bundles:
        singular = ent.has_all_bundle(bundle)
        batch = ent.has_all_bundle_batch([bundle])[0]
        assert singular == batch


def test_helper_scalar_empty_bundle_is_stable_row(ent):
    row = ent.has_all_bundle({})
    assert set(row.keys()) == _LIVE_ROW_KEYS
    assert row["features"] == []
    assert row["runtimes"] == []
    assert row["channels"] is None
    assert row["retention_days"] is None
    assert row["nodes"] is None
    # Empty bundle: no axes supplied -> False (matches has_all).
    assert row["has_all"] is False


def test_helper_scalar_none_bundle_is_stable_row(ent):
    """Never-crash on ``None`` bundle: delegate returns a stable empty
    row shape (matches the batch's non-dict-row collapse)."""
    row = ent.has_all_bundle(None)
    assert set(row.keys()) == _LIVE_ROW_KEYS
    assert row["has_all"] is False


def test_helper_scalar_non_dict_bundle_is_stable_row(ent):
    """Non-dict input (scalar, list) collapses to the empty row shape."""
    for bad in ("not a dict", 42, [1, 2, 3]):
        row = ent.has_all_bundle(bad)
        assert set(row.keys()) == _LIVE_ROW_KEYS
        assert row["features"] == []
        assert row["has_all"] is False


def test_helper_scalar_paid_bundle_true_in_grace(ent):
    """Grace pass-through contract: paid bundle -> True in grace."""
    paid_f = next(iter(ent.PAID_FEATURES))
    paid_r = next(iter(ent.PAID_RUNTIMES))
    bundle = {"features": [paid_f], "runtimes": [paid_r], "channels": 999}
    assert ent.has_all_bundle(bundle)["has_all"] is True


def test_helper_scalar_paid_bundle_false_when_enforced(enforced):
    """Post-enforcement: paid bundle folds through the LIVE resolver's
    per-axis grants -- OSS-shaped install denies the paid feature."""
    paid_f = next(iter(enforced.PAID_FEATURES))
    row = enforced.has_all_bundle({"features": [paid_f]})
    assert row["has_all"] is False


# -- helper: has_all_bundle_at (perspective-shaped) ---------------------------


def test_helper_scalar_at_shapes_by_perspective(ent):
    """Whole point of the ``_at`` slot: at OSS a paid-feature bundle
    reports has_all_at=False even in grace (grace-independent by design)
    where the LIVE helper reports has_all=True via grace pass-through."""
    paid_f = next(iter(ent.PAID_FEATURES))
    bundle = {"features": [paid_f]}
    live = ent.has_all_bundle(bundle)
    at_oss = ent.has_all_bundle_at("oss", bundle)
    assert live["has_all"] is True  # grace pass-through
    assert at_oss["has_all_at"] is False  # static OSS grant table
    assert set(at_oss.keys()) == _AT_ROW_KEYS


def test_helper_scalar_at_enterprise_grants_everything(ent):
    """Enterprise perspective grants every axis in the catalog."""
    paid_f = next(iter(ent.PAID_FEATURES))
    paid_r = next(iter(ent.PAID_RUNTIMES))
    bundle = {
        "features": [paid_f],
        "runtimes": [paid_r],
        "channels": 100,
        "retention_days": 365,
        "nodes": 100,
    }
    row = ent.has_all_bundle_at("enterprise", bundle)
    assert row["has_all_at"] is True


def test_helper_scalar_at_row_byte_equals_batch_row_at(ent):
    """Row shape byte-parity contract for the ``_at`` variant: the
    singular row byte-equals the batch row on the same
    (perspective, bundle)."""
    paid_f = next(iter(ent.PAID_FEATURES))
    perspectives = ["oss", "cloud_starter", "cloud_pro", "enterprise"]
    bundles = [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"]},
        {"features": [paid_f]},
        {"channels": 5},
        {"retention_days": 30, "nodes": 2},
        {},
    ]
    for tier in perspectives:
        for bundle in bundles:
            singular = ent.has_all_bundle_at(tier, bundle)
            batch = ent.has_all_bundle_batch_at(tier, [bundle])[0]
            assert singular == batch


def test_helper_scalar_at_grace_independent(ent, enforced):
    """Grace-independence contract: has_all_bundle_at row body is
    byte-identical under grace vs enforce for the same
    (perspective, bundle)."""
    paid_f = next(iter(ent.PAID_FEATURES))
    for bundle in (
        {"features": ["fleet"]},
        {"features": [paid_f]},
        {"channels": 5},
        {},
    ):
        for tier in ("oss", "cloud_starter", "cloud_pro", "enterprise"):
            grace_row = ent.has_all_bundle_at(tier, bundle)
            enforce_row = enforced.has_all_bundle_at(tier, bundle)
            assert grace_row == enforce_row


def test_helper_scalar_at_unknown_perspective_returns_none(ent):
    for bad in ("bogus", "starter", "cloud-pro", "OSS_TYPO"):
        assert ent.has_all_bundle_at(bad, {"features": ["fleet"]}) is None


def test_helper_scalar_at_blank_perspective_returns_none(ent):
    for bad in ("", "   ", None, 42, [], {}):
        assert ent.has_all_bundle_at(bad, {"features": ["fleet"]}) is None


def test_helper_scalar_at_perspective_case_normalised(ent):
    """Perspective tier is ``.strip().lower()``-canonicalised so an
    upper-case perspective still resolves rather than falling through
    to ``None`` on the unknown-perspective branch."""
    ref = ent.has_all_bundle_at("oss", {"features": ["fleet"]})
    for variant in ("OSS", "  oss  ", "Oss"):
        assert ent.has_all_bundle_at(variant, {"features": ["fleet"]}) == ref


# -- API: /api/entitlement/has-all-bundle -------------------------------------


def test_api_happy_path_shape(client):
    r = client.post(
        "/api/entitlement/has-all-bundle",
        json={
            "bundle": {
                "features": ["fleet"],
                "runtimes": ["claude_code"],
                "channels": 5,
                "retention_days": 30,
                "nodes": 2,
            }
        },
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _LIVE_ENVELOPE_KEYS
    assert body["features"] == ["fleet"]
    assert body["runtimes"] == ["claude_code"]
    assert body["channels"] == 5
    assert body["retention_days"] == 30
    assert body["nodes"] == 2
    assert body["has_all"] is True  # grace pass-through
    assert body["grace"] is True
    assert body["enforced"] is False


def test_api_bare_dict_shorthand(client):
    """Top-level body IS the bundle (matches the shape a caller would
    hand to the ``/has-all`` GET endpoint as query args)."""
    r = client.post(
        "/api/entitlement/has-all-bundle",
        json={"features": ["fleet"], "channels": 5},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["features"] == ["fleet"]
    assert body["channels"] == 5


def test_api_wrapped_and_shorthand_equivalent(client):
    wrapped = client.post(
        "/api/entitlement/has-all-bundle",
        json={"bundle": {"features": ["fleet"]}},
    ).get_json()
    shorthand = client.post(
        "/api/entitlement/has-all-bundle",
        json={"features": ["fleet"]},
    ).get_json()
    assert wrapped == shorthand


def test_api_400_missing_bundle(client):
    r = client.post("/api/entitlement/has-all-bundle", json={})
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing bundle"}


def test_api_400_bundle_null(client):
    r = client.post("/api/entitlement/has-all-bundle", json={"bundle": None})
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing bundle"}


def test_api_400_bundle_not_object(client):
    r = client.post(
        "/api/entitlement/has-all-bundle", json={"bundle": [1, 2, 3]}
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "bundle must be an object"}


def test_api_row_byte_equals_batch_row(client):
    """Cross-endpoint per-row parity contract: the singular endpoint's
    row body byte-equals the batch endpoint's per-row body for the same
    bundle."""
    bundles = [
        {"features": ["fleet"]},
        {"channels": 5},
        {"features": ["FLEET"], "runtimes": ["claude-code"]},
        {},
    ]
    for bundle in bundles:
        s = client.post(
            "/api/entitlement/has-all-bundle", json={"bundle": bundle}
        ).get_json()
        b = client.post(
            "/api/entitlement/has-all-bundle-batch",
            json={"bundles": [bundle]},
        ).get_json()
        # Strip envelope keys before comparing per-row body.
        s_row = {k: v for k, v in s.items() if k in _LIVE_ROW_KEYS}
        b_row = b["bundles"][0]
        assert s_row == b_row


def test_api_empty_bundle_is_stable_row(client):
    r = client.post(
        "/api/entitlement/has-all-bundle", json={"bundle": {}}
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["features"] == []
    assert body["runtimes"] == []
    assert body["channels"] is None
    assert body["retention_days"] is None
    assert body["nodes"] is None
    assert body["has_all"] is False


def test_api_never_5xxs_on_delegate_crash(client, monkeypatch):
    from clawmetry import entitlements as _ent

    def boom(*a, **kw):
        raise RuntimeError("simulated resolver blowup")

    monkeypatch.setattr(_ent, "has_all_bundle", boom)
    r = client.post(
        "/api/entitlement/has-all-bundle",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _LIVE_ENVELOPE_KEYS
    assert body["has_all"] is False


# -- API: /api/entitlement/has-all-bundle-at ----------------------------------


def test_api_at_happy_path_shape(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-at?tier=enterprise",
        json={"bundle": {"features": ["fleet"], "channels": 100}},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _AT_ENVELOPE_KEYS
    assert body["perspective_tier"] == "enterprise"
    assert isinstance(body["perspective_tier_label"], str)
    assert isinstance(body["perspective_tier_rank"], int)
    assert body["has_all_at"] is True


def test_api_at_oss_perspective_denies_paid_feature_in_grace(client, ent):
    """Perspective divergence: at OSS in grace, a paid feature still
    reports has_all_at=false (grace-independent by design)."""
    paid_f = next(iter(ent.PAID_FEATURES))
    r = client.post(
        "/api/entitlement/has-all-bundle-at?tier=oss",
        json={"bundle": {"features": [paid_f]}},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["has_all_at"] is False
    assert body["grace"] is True  # LIVE resolver still in grace


def test_api_at_400_missing_tier(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-at",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing tier"}


def test_api_at_400_blank_tier(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-at?tier=%20%20",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing tier"}


def test_api_at_404_unknown_tier(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-at?tier=bogus",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_api_at_400_missing_bundle(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-at?tier=oss", json={}
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "missing bundle"}


def test_api_at_400_bundle_not_object(client):
    r = client.post(
        "/api/entitlement/has-all-bundle-at?tier=oss",
        json={"bundle": 42},
    )
    assert r.status_code == 400
    assert r.get_json() == {"error": "bundle must be an object"}


def test_api_at_row_byte_equals_batch_row_at(client):
    """Cross-endpoint per-row parity contract for the ``_at`` variant."""
    bundles = [
        {"features": ["fleet"]},
        {"channels": 5},
        {"features": ["FLEET"], "runtimes": ["claude-code"]},
        {},
    ]
    for tier in ("oss", "cloud_starter", "cloud_pro", "enterprise"):
        for bundle in bundles:
            s = client.post(
                f"/api/entitlement/has-all-bundle-at?tier={tier}",
                json={"bundle": bundle},
            ).get_json()
            b = client.post(
                f"/api/entitlement/has-all-bundle-batch-at?tier={tier}",
                json={"bundles": [bundle]},
            ).get_json()
            s_row = {k: v for k, v in s.items() if k in _AT_ROW_KEYS}
            b_row = b["bundles"][0]
            assert s_row == b_row


def test_api_at_never_5xxs_on_delegate_crash(client, monkeypatch):
    from clawmetry import entitlements as _ent

    def boom(*a, **kw):
        raise RuntimeError("simulated resolver blowup")

    monkeypatch.setattr(_ent, "has_all_bundle_at", boom)
    r = client.post(
        "/api/entitlement/has-all-bundle-at?tier=cloud_pro",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _AT_ENVELOPE_KEYS
    assert body["has_all_at"] is False
    assert body["perspective_tier"] == "cloud_pro"


def test_api_bare_dict_shorthand_at(client):
    """Bare-dict shorthand also works on the ``_at`` endpoint."""
    ref = client.post(
        "/api/entitlement/has-all-bundle-at?tier=oss",
        json={"bundle": {"features": ["fleet"]}},
    ).get_json()
    short = client.post(
        "/api/entitlement/has-all-bundle-at?tier=oss",
        json={"features": ["fleet"]},
    ).get_json()
    assert ref == short


# -- Cross-endpoint: LIVE / _at fold-slot divergence ---------------------------


def test_api_live_and_at_row_share_axis_echoes(client):
    """LIVE and _at endpoints emit byte-identical axis echoes on the
    same bundle -- only the fold slot name/value diverges
    (has_all vs has_all_at)."""
    bundle = {"features": ["fleet"], "channels": 5}
    live = client.post(
        "/api/entitlement/has-all-bundle", json={"bundle": bundle}
    ).get_json()
    at = client.post(
        "/api/entitlement/has-all-bundle-at?tier=cloud_pro",
        json={"bundle": bundle},
    ).get_json()
    for axis in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert live[axis] == at[axis]
