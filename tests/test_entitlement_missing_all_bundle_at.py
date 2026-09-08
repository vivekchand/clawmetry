"""Tests for the aggregate bundle singular row-detail perspective-shaped
``/api/entitlement/missing-all-bundle-at`` endpoint (plus the
:func:`clawmetry.entitlements.missing_all_bundle_at` helper).

Perspective-shaped row-detail scalar sibling of the batch
``/api/entitlement/missing-all-bundle-batch-at`` on the same
``(perspective_tier, bundle)`` input. Where the paired batch answers
"which axes of THIS bundle would tier <perspective> STILL not grant?"
for N caller-supplied aggregate bundles, this answers the same question
for ONE bundle in one round-trip -- fills the singular-row slot so a
paywall walkthrough tile rendering ONE bundle cell at a time reads the
perspective-scoped denial detail without wrapping in a length-one list
and unwrapping ``[0]`` from the batch.

Grace-independent by construction: delegates to
:func:`_missing_all_bundle_row_at`, which folds through
:func:`missing_all_at` (backed by the static per-tier tables), so grace
vs enforce yields byte-identical row bodies. Whole point of the ``_at``
slot: at ``tier=oss`` a paid-feature bundle reports
``missing.features=["fleet"]`` even in grace, whereas the LIVE
``/missing-all-bundle`` reports ``missing.features=[]`` for the same
bundle via grace pass-through.

These tests pin:

* helper: per-bundle normalisation (feature/runtime CSV, runtime alias
  canonicalisation, capacity int coercion, blank / non-int axes collapse
  to ``None``, empty bundle surfaces as a stable row)
* helper: perspective-shaping -- OSS denies paid feature/runtime/capacity
  even in grace; Enterprise grants everything even after enforce
* helper: row byte-parity with the batch's row on the same input
* helper: ``missing`` byte-parity with the singular :func:`missing_all_at`
* helper: complement invariant with :func:`has_all_bundle_at`
  (``any(row["missing"].values())`` == ``not row["has_all_at"]`` for
  every fully-parseable NON-EMPTY bundle)
* helper: axis-echo byte-parity with :func:`has_all_bundle_at`
* helper: never-crash contract on ``None`` / non-dict / scalar bundle
* helper: perspective-validation ``None`` posture
* helper: grace-independence of the fold (same row body under enforce)
* API happy path: 10-key envelope, 6-key row (5-key ``missing`` sub-dict)
* API bare-dict shorthand (matches :func:`_parse_single_bundle_body`)
* API error paths: 400 on missing / non-object ``bundle``; 400 on missing
  / blank ``tier=``; 404 on unknown ``tier=``
* API cross-endpoint axis-echo parity with ``/has-all-bundle-at``
* API row byte-parity with ``/missing-all-bundle-batch-at`` on the same
  ``(tier, bundle)``
* API per-row ``missing`` byte-equals the singular ``/missing-all-at``
  GET endpoint on the same known bundle
* API grace-independence: same row body across grace vs enforce
* API never-5xxs on a monkeypatched delegate crash
* API envelope grace / enforced flags surface the resolver state
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
    """Enforcement-on fixture: ``CLAWMETRY_ENFORCE=1`` flips
    ``ent.grace`` off. The perspective-shaped ``_at`` fold is
    grace-independent by construction, so every row body should
    byte-equal the grace fixture's row body on the same input."""
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


@pytest.fixture
def enforced_client(enforced):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# -- Row / envelope shape constants -------------------------------------------


_ROW_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "missing",
}

_MISSING_SLOT_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
}

_AT_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "missing",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


def _empty_missing() -> dict:
    return {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


# -- helper: bundle normalisation ---------------------------------------------


def test_helper_folds_across_all_five_axes(ent):
    r = ent.missing_all_bundle_at(
        "cloud_pro",
        {
            "features": ["fleet"],
            "runtimes": ["claude_code"],
            "channels": 5,
            "retention_days": 30,
            "nodes": 2,
        },
    )
    assert isinstance(r, dict)
    assert set(r.keys()) == _ROW_KEYS
    assert r["features"] == ["fleet"]
    assert r["runtimes"] == ["claude_code"]
    assert r["channels"] == 5
    assert r["retention_days"] == 30
    assert r["nodes"] == 2
    assert set(r["missing"].keys()) == _MISSING_SLOT_KEYS
    # Cloud Pro grants the paid bundle under the static per-tier tables
    # -- nothing missing.
    assert r["missing"] == _empty_missing()


def test_helper_normalises_feature_csv(ent):
    r = ent.missing_all_bundle_at(
        "cloud_pro", {"features": ["FLEET", "fleet", "", "sso"]}
    )
    assert r["features"] == ["fleet", "sso"]


def test_helper_normalises_runtime_alias(ent):
    r = ent.missing_all_bundle_at(
        "cloud_pro", {"runtimes": ["claude-code", "claude_code", "codex"]}
    )
    assert r["runtimes"] == ["claude_code", "codex"]


def test_helper_coerces_capacity_axes(ent):
    r = ent.missing_all_bundle_at(
        "cloud_pro",
        {"channels": "5", "retention_days": "30", "nodes": "2"},
    )
    assert r["channels"] == 5
    assert r["retention_days"] == 30
    assert r["nodes"] == 2


def test_helper_blank_capacity_collapses_to_none(ent):
    r = ent.missing_all_bundle_at(
        "cloud_pro",
        {"channels": "", "retention_days": "notanint", "nodes": None},
    )
    assert r["channels"] is None
    assert r["retention_days"] is None
    assert r["nodes"] is None
    # A blank capacity drops from the fold entirely; nothing missing.
    assert r["missing"] == _empty_missing()


def test_helper_empty_bundle_stable_row(ent):
    r = ent.missing_all_bundle_at("cloud_pro", {})
    assert r["features"] == []
    assert r["runtimes"] == []
    assert r["channels"] is None
    assert r["retention_days"] is None
    assert r["nodes"] is None
    assert r["missing"] == _empty_missing()


def test_helper_none_bundle_stable_row(ent):
    r = ent.missing_all_bundle_at("oss", None)
    assert r == {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "missing": _empty_missing(),
    }


def test_helper_non_dict_bundle_stable_row(ent):
    for bad in (42, "nope", ["fleet"], (1, 2, 3)):
        r = ent.missing_all_bundle_at("oss", bad)
        assert r["features"] == []
        assert r["runtimes"] == []
        assert r["missing"] == _empty_missing()


# -- helper: perspective validation -------------------------------------------


def test_helper_unknown_perspective_returns_none(ent):
    assert ent.missing_all_bundle_at("bogus", {}) is None


def test_helper_blank_perspective_returns_none(ent):
    assert ent.missing_all_bundle_at("", {}) is None
    assert ent.missing_all_bundle_at("   ", {}) is None


def test_helper_none_perspective_returns_none(ent):
    assert ent.missing_all_bundle_at(None, {}) is None


def test_helper_non_string_perspective_returns_none(ent):
    assert ent.missing_all_bundle_at(42, {}) is None


def test_helper_perspective_case_and_whitespace_normalised(ent):
    r = ent.missing_all_bundle_at("  Cloud_Pro  ", {"features": ["fleet"]})
    assert r is not None
    assert r["missing"]["features"] == []


# -- helper: perspective shaping (the whole point of _at) ---------------------


def test_helper_oss_denies_paid_feature_even_in_grace(ent):
    """The ``_at`` fold reads static per-tier tables, so OSS still
    reports fleet as missing even while the LIVE resolver would grant
    it via grace pass-through."""
    r = ent.missing_all_bundle_at("oss", {"features": ["fleet"]})
    assert r["missing"]["features"] == ["fleet"]


def test_helper_oss_denies_paid_runtime_even_in_grace(ent):
    r = ent.missing_all_bundle_at("oss", {"runtimes": ["claude_code"]})
    assert r["missing"]["runtimes"] == ["claude_code"]


def test_helper_oss_denies_paid_capacity_even_in_grace(ent):
    r = ent.missing_all_bundle_at(
        "oss", {"channels": 100, "retention_days": 365, "nodes": 100}
    )
    assert r["missing"]["channels"] == 100
    assert r["missing"]["retention_days"] == 365
    assert r["missing"]["nodes"] == 100


@pytest.mark.parametrize(
    "perspective",
    ["oss", "cloud_free", "cloud_starter", "cloud_pro", "enterprise"],
)
def test_helper_free_runtime_never_missing_at_any_tier(ent, perspective):
    """openclaw is FREE_RUNTIMES; missing.runtimes empty at every tier."""
    r = ent.missing_all_bundle_at(perspective, {"runtimes": ["openclaw"]})
    assert r["missing"]["runtimes"] == []


def test_helper_enterprise_grants_paid_bundle(ent):
    r = ent.missing_all_bundle_at(
        "enterprise",
        {
            "features": ["fleet", "sso"],
            "runtimes": ["claude_code"],
            "channels": 100,
            "retention_days": 365,
            "nodes": 100,
        },
    )
    assert r["missing"] == _empty_missing()


def test_helper_cloud_starter_partial_grant(ent):
    """cloud_starter grants fleet (in STARTER_FEATURES) but not sso
    (Enterprise-only) and not otel_export (Pro-only)."""
    r = ent.missing_all_bundle_at(
        "cloud_starter",
        {"features": ["fleet", "sso", "otel_export"]},
    )
    missing_feats = set(r["missing"]["features"])
    assert "fleet" not in missing_feats
    assert "sso" in missing_feats
    assert "otel_export" in missing_feats


# -- helper: grace-independence (whole point of the _at slot) -----------------


@pytest.mark.parametrize(
    "bundle",
    [
        {"features": ["fleet", "sso"]},
        {"runtimes": ["claude_code", "codex"]},
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 100, "retention_days": 365, "nodes": 100},
        {},
    ],
)
def test_helper_row_body_grace_independent(ent, enforced, bundle):
    """Same ``(perspective, bundle)`` yields byte-identical row body
    under grace vs enforce -- the whole point of the ``_at`` slot."""
    grace_row = ent.missing_all_bundle_at("oss", bundle)
    enforce_row = enforced.missing_all_bundle_at("oss", bundle)
    assert grace_row == enforce_row


# -- helper: row byte-parity with the batch ----------------------------------


@pytest.mark.parametrize(
    "perspective",
    ["oss", "cloud_free", "cloud_starter", "cloud_pro", "enterprise"],
)
@pytest.mark.parametrize(
    "bundle",
    [
        {"features": ["fleet", "sso"]},
        {"runtimes": ["claude_code", "codex"]},
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 5, "retention_days": 30, "nodes": 2},
        {"channels": 100, "retention_days": 365, "nodes": 100},
        {},
    ],
)
def test_helper_row_byte_parity_with_batch(ent, perspective, bundle):
    """Singular row byte-equals the batch's ``[0]`` row on the same
    ``(perspective, bundle)`` inputs -- same shared row helper."""
    single = ent.missing_all_bundle_at(perspective, bundle)
    batch = ent.missing_all_bundle_batch_at(perspective, [bundle])[0]
    assert single == batch


# -- helper: missing parity with the singular missing_all_at scalar -----------


@pytest.mark.parametrize(
    "perspective",
    ["oss", "cloud_free", "cloud_starter", "cloud_pro", "enterprise"],
)
@pytest.mark.parametrize(
    "bundle",
    [
        {"features": ["fleet", "sso"]},
        {"runtimes": ["claude_code", "codex"]},
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 5, "retention_days": 30, "nodes": 2},
        {},
    ],
)
def test_helper_missing_parity_with_singular_missing_all_at(
    ent, perspective, bundle
):
    """Per-row ``missing`` byte-equals :func:`missing_all_at` on the
    same normalised inputs."""
    row = ent.missing_all_bundle_at(perspective, bundle)
    singular = ent.missing_all_at(
        perspective,
        features=(row["features"] or None),
        runtimes=(row["runtimes"] or None),
        channels=row["channels"],
        retention_days=row["retention_days"],
        nodes=row["nodes"],
    )
    assert row["missing"]["features"] == list(singular.get("features") or [])
    assert row["missing"]["runtimes"] == list(singular.get("runtimes") or [])
    assert row["missing"]["channels"] == singular.get("channels")
    assert row["missing"]["retention_days"] == singular.get("retention_days")
    assert row["missing"]["nodes"] == singular.get("nodes")


# -- helper: complement invariant with has_all_bundle_at ---------------------


@pytest.mark.parametrize(
    "perspective",
    ["oss", "cloud_free", "cloud_starter", "cloud_pro", "enterprise"],
)
@pytest.mark.parametrize(
    "bundle",
    [
        {"features": ["fleet", "sso"]},
        {"runtimes": ["claude_code"]},
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 5},
    ],
)
def test_helper_complement_with_has_all_bundle_at(ent, perspective, bundle):
    """For every fully-parseable NON-EMPTY bundle,
    ``any(row["missing"].values())`` byte-equals ``not row["has_all_at"]``
    on the paired boolean-fold row. The empty ``{}`` case is a
    deliberate divergence -- the boolean-fold sibling collapses to
    ``has_all_at=False`` under its typo posture while the row-detail
    seat reports nothing missing."""
    miss_row = ent.missing_all_bundle_at(perspective, bundle)
    has_row = ent.has_all_bundle_at(perspective, bundle)
    any_missing = (
        bool(miss_row["missing"]["features"])
        or bool(miss_row["missing"]["runtimes"])
        or miss_row["missing"]["channels"] is not None
        or miss_row["missing"]["retention_days"] is not None
        or miss_row["missing"]["nodes"] is not None
    )
    assert any_missing == (not has_row["has_all_at"])


# -- helper: axis-echo parity with has_all_bundle_at -------------------------


def test_helper_axis_echoes_match_has_all_bundle_at(ent):
    """features / runtimes / channels / retention_days / nodes echoes
    byte-equal the paired :func:`has_all_bundle_at` row on the same
    input (only the fold slot differs)."""
    bundle = {
        "features": ["FLEET", "sso"],
        "runtimes": ["claude-code", "codex"],
        "channels": "5",
        "retention_days": "30",
        "nodes": "2",
    }
    miss = ent.missing_all_bundle_at("cloud_pro", bundle)
    has = ent.has_all_bundle_at("cloud_pro", bundle)
    for k in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert miss[k] == has[k]


# -- helper: never-raise contract ---------------------------------------------


def test_helper_never_raises_on_bad_axis_types(ent):
    r = ent.missing_all_bundle_at(
        "cloud_pro",
        {
            "features": 42,
            "runtimes": None,
            "channels": [],
            "retention_days": {"nope": True},
            "nodes": object(),
        },
    )
    assert r["features"] == []
    assert r["runtimes"] == []
    assert r["channels"] is None
    assert r["retention_days"] is None
    assert r["nodes"] is None


def test_helper_never_raises_on_delegate_crash(ent, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "_missing_all_bundle_row_at", _boom)
    r = ent.missing_all_bundle_at("cloud_pro", {"features": ["fleet"]})
    assert r == {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "missing": _empty_missing(),
    }


# -- API: happy path ----------------------------------------------------------


def test_api_happy(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=cloud_pro",
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
    j = r.get_json()
    assert set(j.keys()) == _AT_ENVELOPE_KEYS
    assert j["perspective_tier"] == "cloud_pro"
    assert isinstance(j["perspective_tier_label"], str)
    assert j["perspective_tier_label"] == ent.tier_label("cloud_pro")
    assert j["perspective_tier_rank"] == ent.tier_rank("cloud_pro")
    assert set(j["missing"].keys()) == _MISSING_SLOT_KEYS
    # cloud_pro grants the paid bundle -- nothing missing.
    assert j["missing"] == _empty_missing()


def test_api_oss_denies_paid_feature_even_in_grace(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["features"] == ["fleet"]
    # Grace-independent -- the _at fold reads the static per-tier
    # tables, so OSS denies fleet even in grace.
    assert j["missing"]["features"] == ["fleet"]


def test_api_bare_dict_shorthand(client, ent):
    """Bare-dict body (no ``bundle`` wrapper) is accepted for parity
    with the singular ``/has-all-bundle-at`` endpoint."""
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={"features": ["fleet"]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["features"] == ["fleet"]
    assert j["missing"]["features"] == ["fleet"]


def test_api_empty_bundle_accepted(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={"bundle": {}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["features"] == []
    assert j["missing"] == _empty_missing()


def test_api_alias_canonicalised(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={"bundle": {"runtimes": ["claude-code", "claude_code"]}},
    )
    j = r.get_json()
    assert j["runtimes"] == ["claude_code"]
    assert j["missing"]["runtimes"] == ["claude_code"]


def test_api_capacity_coercion(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={"bundle": {"channels": "5", "retention_days": "notanint"}},
    )
    j = r.get_json()
    assert j["channels"] == 5
    assert j["retention_days"] is None


def test_api_tier_case_and_whitespace_normalised(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=%20Cloud_Pro%20",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "cloud_pro"


# -- API: error paths ---------------------------------------------------------


def test_api_missing_tier_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_api_blank_tier_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=%20%20%20",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_api_unknown_tier_404(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=bogus",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_api_missing_bundle_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss", json={}
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundle"


def test_api_null_bundle_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={"bundle": None},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundle"


def test_api_non_object_bundle_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={"bundle": 5},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "bundle must be an object"


def test_api_no_body_400(client):
    r = client.post("/api/entitlement/missing-all-bundle-at?tier=oss")
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundle"


# -- API: cross-endpoint parity ----------------------------------------------


def test_api_axis_echo_parity_with_has_all_bundle_at(client):
    body = {
        "bundle": {
            "features": ["FLEET", "fleet", "sso"],
            "runtimes": ["claude-code", "codex"],
            "channels": "5",
            "retention_days": "30",
            "nodes": "2",
        }
    }
    miss = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=cloud_pro",
        json=body,
    ).get_json()
    has = client.post(
        "/api/entitlement/has-all-bundle-at?tier=cloud_pro",
        json=body,
    ).get_json()
    for k in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert miss[k] == has[k]


def test_api_perspective_envelope_parity_with_has_all_bundle_at(client):
    body = {"bundle": {"features": ["fleet"]}}
    miss = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=cloud_starter",
        json=body,
    ).get_json()
    has = client.post(
        "/api/entitlement/has-all-bundle-at?tier=cloud_starter",
        json=body,
    ).get_json()
    for k in (
        "perspective_tier",
        "perspective_tier_label",
        "perspective_tier_rank",
    ):
        assert miss[k] == has[k]


def test_api_row_byte_parity_with_batch_at(client):
    """The singular row body byte-equals the batch's ``bundles[0]`` on
    the same ``(tier, bundle)`` -- same shared row helper on both."""
    bundle = {
        "features": ["fleet", "sso"],
        "runtimes": ["claude_code"],
        "channels": 5,
        "retention_days": 30,
        "nodes": 2,
    }
    single = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={"bundle": bundle},
    ).get_json()
    batch = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss",
        json={"bundles": [bundle]},
    ).get_json()
    batch_row = batch["bundles"][0]
    for k in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert single[k] == batch_row[k]
    assert single["missing"] == batch_row["missing"]


def test_api_row_missing_matches_singular_missing_all_at_endpoint(client):
    """The row's ``missing`` byte-equals the singular
    ``/missing-all-at?tier=oss`` endpoint's body on the same known
    bundle (byte parity on the axis-echo -> denial slots)."""
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={
            "bundle": {
                "features": ["fleet", "sso"],
                "runtimes": ["claude_code"],
            }
        },
    ).get_json()
    singular = client.get(
        "/api/entitlement/missing-all-at"
        "?tier=oss&features=fleet,sso&runtimes=claude_code"
    ).get_json()
    for k in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert r["missing"][k] == singular.get(k)


# -- API: grace-independence (whole point of the _at slot) --------------------


@pytest.mark.parametrize(
    "bundle",
    [
        {"features": ["fleet", "sso"], "runtimes": ["claude_code"]},
        {"channels": 100, "retention_days": 365, "nodes": 100},
        {},
    ],
)
def test_api_row_body_grace_independent(client, enforced_client, bundle):
    """Row body byte-equals across grace vs enforce fixtures on every
    axis -- only the envelope's ``current_tier`` / ``grace`` /
    ``enforced`` slots differ."""
    g = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={"bundle": bundle},
    ).get_json()
    e = enforced_client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={"bundle": bundle},
    ).get_json()
    for k in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert g[k] == e[k]
    assert g["missing"] == e["missing"]


# -- API: never-5xxs on delegate crash ----------------------------------------


def test_api_never_5xxs_on_delegate_crash(client, ent, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "missing_all_bundle_at", _boom)
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=cloud_pro",
        json={"bundle": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["perspective_tier"] == "cloud_pro"
    assert j["features"] == []
    assert j["missing"] == _empty_missing()


# -- envelope resolver-slot stability -----------------------------------------


def test_api_envelope_grace_flags(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={"bundle": {"features": ["fleet"]}},
    )
    j = r.get_json()
    assert j["grace"] is True
    assert j["enforced"] is False


def test_api_envelope_enforce_flags(enforced_client):
    r = enforced_client.post(
        "/api/entitlement/missing-all-bundle-at?tier=oss",
        json={"bundle": {"features": ["fleet"]}},
    )
    j = r.get_json()
    assert j["grace"] is False
    assert j["enforced"] is True
