"""Tests for the aggregate bundle-batch row-detail perspective-shaped
``/api/entitlement/missing-all-bundle-batch-at`` endpoint (plus the
:func:`clawmetry.entitlements.missing_all_bundle_batch_at` helper).

Perspective-shaped row-detail sibling of the boolean-fold
``/api/entitlement/has-all-bundle-batch-at`` on the same
``(perspective_tier, bundles)`` input. Where the paired boolean-fold
answers "would tier <perspective> grant this whole 5-axis bundle?" for
N caller-supplied aggregate bundles, this answers "which axes of THIS
bundle would tier <perspective> STILL not grant?" for the same N
bundles in ONE round-trip. Grace-independent by construction: delegates
per-row to :func:`missing_all_at` (backed by the static per-tier
tables), so grace vs enforce yields byte-identical row bodies.

Distinct from the LIVE ``/missing-all-bundle-batch`` endpoint (which
reads the live per-install grant with grace pass-through). Whole point
of the ``_at`` slot: at ``tier=oss`` a paid-feature bundle reports
``missing.features=["fleet"]`` even in grace, whereas the LIVE endpoint
reports ``missing.features=[]`` for the same bundle.

These tests pin:

* helper: per-bundle normalisation (feature/runtime CSV, runtime alias
  canonicalisation, capacity int coercion, blank / non-int axes collapse
  to ``None``, empty bundle surfaces as a stable row)
* helper: perspective-shaping -- OSS denies paid feature/runtime/capacity
  even in grace; Enterprise grants everything even after enforce
* helper: per-row parity with the singular :func:`missing_all_at` scalar
* helper: complement invariant with :func:`has_all_bundle_batch_at`
  (``any(row["missing"].values())`` == ``not row["has_all_at"]``)
* helper: never-crash contract on ``None`` / non-iterable / non-dict
  bundle inputs
* helper: perspective-validation ``None`` posture
* helper: grace-independence of the fold (same row body under enforce)
* API happy path: 9-key envelope, 6-key row (5-key ``missing`` sub-dict)
* API single-bundle shorthand (bare-dict posture)
* API error paths: 400 on missing / non-list-non-dict / empty ``bundles``;
  400 on missing ``tier=``; 404 on unknown ``tier=``
* API cross-endpoint axis-echo parity with ``/has-all-bundle-batch-at``
* API per-row ``missing`` byte-equals the singular ``/missing-all-at``
  endpoint on the same known bundle
* API grace-independence: same row body across grace vs enforce
* API never-5xxs on a monkeypatched delegate crash
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
    "bundles",
    "count",
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
    rows = ent.missing_all_bundle_batch_at(
        "cloud_pro",
        [
            {
                "features": ["fleet"],
                "runtimes": ["claude_code"],
                "channels": 5,
                "retention_days": 30,
                "nodes": 2,
            }
        ],
    )
    assert len(rows) == 1
    r = rows[0]
    assert set(r.keys()) == _ROW_KEYS
    assert r["features"] == ["fleet"]
    assert r["runtimes"] == ["claude_code"]
    assert r["channels"] == 5
    assert r["retention_days"] == 30
    assert r["nodes"] == 2
    assert set(r["missing"].keys()) == _MISSING_SLOT_KEYS
    # Cloud Pro grants fleet + claude_code + 5 channels + 30d + 2 nodes
    # under the static per-tier tables -- nothing missing.
    assert r["missing"] == _empty_missing()


def test_helper_normalises_feature_csv(ent):
    rows = ent.missing_all_bundle_batch_at(
        "cloud_pro", [{"features": ["FLEET", "fleet", "", "sso"]}]
    )
    assert rows[0]["features"] == ["fleet", "sso"]


def test_helper_normalises_runtime_alias(ent):
    rows = ent.missing_all_bundle_batch_at(
        "cloud_pro", [{"runtimes": ["claude-code", "claude_code", "codex"]}]
    )
    assert rows[0]["runtimes"] == ["claude_code", "codex"]


def test_helper_coerces_capacity_axes(ent):
    rows = ent.missing_all_bundle_batch_at(
        "cloud_pro",
        [{"channels": "5", "retention_days": "30", "nodes": "2"}],
    )
    r = rows[0]
    assert r["channels"] == 5
    assert r["retention_days"] == 30
    assert r["nodes"] == 2


def test_helper_blank_capacity_collapses_to_none(ent):
    rows = ent.missing_all_bundle_batch_at(
        "cloud_pro",
        [{"channels": "", "retention_days": "notanint", "nodes": None}],
    )
    r = rows[0]
    assert r["channels"] is None
    assert r["retention_days"] is None
    assert r["nodes"] is None
    # A blank capacity drops from the fold entirely; nothing missing.
    assert r["missing"] == _empty_missing()


def test_helper_empty_bundle_stable_row(ent):
    rows = ent.missing_all_bundle_batch_at("cloud_pro", [{}])
    r = rows[0]
    assert r["features"] == []
    assert r["runtimes"] == []
    assert r["channels"] is None
    assert r["retention_days"] is None
    assert r["nodes"] is None
    assert r["missing"] == _empty_missing()


def test_helper_none_bundles_returns_empty_list(ent):
    """Perspective valid + ``bundles=None`` -> ``[]`` (nothing to fold),
    NOT ``None`` -- matches :func:`has_all_bundle_batch_at`."""
    assert ent.missing_all_bundle_batch_at("cloud_pro", None) == []


def test_helper_non_iterable_bundles_returns_empty_list(ent):
    assert ent.missing_all_bundle_batch_at("cloud_pro", 42) == []


def test_helper_empty_bundles_list_returns_empty_list(ent):
    assert ent.missing_all_bundle_batch_at("cloud_pro", []) == []


def test_helper_none_bundle_row_stable(ent):
    rows = ent.missing_all_bundle_batch_at(
        "oss", [None, {"features": ["fleet"]}]
    )
    assert rows[0] == {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "missing": _empty_missing(),
    }
    assert rows[1]["features"] == ["fleet"]


def test_helper_non_dict_row_stable(ent):
    rows = ent.missing_all_bundle_batch_at(
        "oss", [42, ["fleet"], {"features": ["fleet"]}]
    )
    assert rows[0]["features"] == []
    assert rows[0]["missing"] == _empty_missing()
    assert rows[1]["features"] == []
    assert rows[1]["missing"] == _empty_missing()
    assert rows[2]["features"] == ["fleet"]


# -- helper: perspective validation -------------------------------------------


def test_helper_unknown_perspective_returns_none(ent):
    assert ent.missing_all_bundle_batch_at("bogus", [{}]) is None


def test_helper_blank_perspective_returns_none(ent):
    assert ent.missing_all_bundle_batch_at("", [{}]) is None
    assert ent.missing_all_bundle_batch_at("   ", [{}]) is None


def test_helper_none_perspective_returns_none(ent):
    assert ent.missing_all_bundle_batch_at(None, [{}]) is None


def test_helper_non_string_perspective_returns_none(ent):
    assert ent.missing_all_bundle_batch_at(42, [{}]) is None


def test_helper_perspective_case_and_whitespace_normalised(ent):
    rows = ent.missing_all_bundle_batch_at(
        "  Cloud_Pro  ", [{"features": ["fleet"]}]
    )
    assert rows is not None
    assert rows[0]["missing"]["features"] == []


# -- helper: perspective shaping (the whole point of _at) ---------------------


def test_helper_oss_denies_paid_feature_even_in_grace(ent):
    """The ``_at`` fold reads static per-tier tables, so OSS still
    reports fleet as missing even while the LIVE resolver would grant
    it via grace pass-through."""
    rows = ent.missing_all_bundle_batch_at("oss", [{"features": ["fleet"]}])
    assert rows[0]["missing"]["features"] == ["fleet"]


def test_helper_oss_denies_paid_runtime_even_in_grace(ent):
    rows = ent.missing_all_bundle_batch_at(
        "oss", [{"runtimes": ["claude_code"]}]
    )
    assert rows[0]["missing"]["runtimes"] == ["claude_code"]


def test_helper_oss_denies_paid_capacity_even_in_grace(ent):
    rows = ent.missing_all_bundle_batch_at(
        "oss", [{"channels": 100, "retention_days": 365, "nodes": 100}]
    )
    r = rows[0]
    assert r["missing"]["channels"] == 100
    assert r["missing"]["retention_days"] == 365
    assert r["missing"]["nodes"] == 100


@pytest.mark.parametrize(
    "perspective", ["oss", "cloud_free", "cloud_starter", "cloud_pro", "enterprise"]
)
def test_helper_free_runtime_never_missing_at_any_tier(ent, perspective):
    """openclaw is FREE_RUNTIMES; missing.runtimes empty at every tier."""
    rows = ent.missing_all_bundle_batch_at(
        perspective, [{"runtimes": ["openclaw"]}]
    )
    assert rows[0]["missing"]["runtimes"] == []


def test_helper_enterprise_grants_paid_bundle(ent):
    rows = ent.missing_all_bundle_batch_at(
        "enterprise",
        [
            {
                "features": ["fleet", "sso"],
                "runtimes": ["claude_code"],
                "channels": 100,
                "retention_days": 365,
                "nodes": 100,
            }
        ],
    )
    assert rows[0]["missing"] == _empty_missing()


def test_helper_cloud_starter_partial_grant(ent):
    """cloud_starter grants fleet (in STARTER_FEATURES) but not sso
    (Enterprise-only) and not otel_export (Pro-only)."""
    rows = ent.missing_all_bundle_batch_at(
        "cloud_starter",
        [{"features": ["fleet", "sso", "otel_export"]}],
    )
    missing_feats = set(rows[0]["missing"]["features"])
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
    grace_rows = ent.missing_all_bundle_batch_at("oss", [bundle])
    enforce_rows = enforced.missing_all_bundle_batch_at("oss", [bundle])
    assert grace_rows == enforce_rows


# -- helper: per-row parity with the singular missing_all_at scalar -----------


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
def test_helper_per_row_parity_with_singular_missing_all_at(
    ent, perspective, bundle
):
    """Per-bundle ``missing`` byte-equals :func:`missing_all_at` on the
    same normalised inputs."""
    row = ent.missing_all_bundle_batch_at(perspective, [bundle])[0]
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


# -- helper: complement invariant with has_all_bundle_batch_at ---------------


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
def test_helper_complement_with_has_all_bundle_batch_at(
    ent, perspective, bundle
):
    """For every fully-parseable NON-EMPTY bundle,
    ``any(row["missing"].values())`` byte-equals ``not row["has_all_at"]``
    on the paired boolean-fold row. The empty ``{}`` case is a
    deliberate divergence -- the boolean-fold sibling collapses to
    ``has_all_at=False`` under its typo posture while the row-detail
    seat reports nothing missing (nothing supplied to check)."""
    miss_row = ent.missing_all_bundle_batch_at(perspective, [bundle])[0]
    has_row = ent.has_all_bundle_batch_at(perspective, [bundle])[0]
    any_missing = (
        bool(miss_row["missing"]["features"])
        or bool(miss_row["missing"]["runtimes"])
        or miss_row["missing"]["channels"] is not None
        or miss_row["missing"]["retention_days"] is not None
        or miss_row["missing"]["nodes"] is not None
    )
    assert any_missing == (not has_row["has_all_at"])


# -- helper: axis-echo parity with has_all_bundle_batch_at -------------------


def test_helper_axis_echoes_match_has_all_bundle_batch_at(ent):
    """features / runtimes / channels / retention_days / nodes echoes
    byte-equal the paired :func:`has_all_bundle_batch_at` row on the
    same input (only the fold slot differs)."""
    bundle = {
        "features": ["FLEET", "sso"],
        "runtimes": ["claude-code", "codex"],
        "channels": "5",
        "retention_days": "30",
        "nodes": "2",
    }
    miss = ent.missing_all_bundle_batch_at("cloud_pro", [bundle])[0]
    has = ent.has_all_bundle_batch_at("cloud_pro", [bundle])[0]
    for k in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert miss[k] == has[k]


# -- helper: never-raise contract ---------------------------------------------


def test_helper_never_raises_on_bad_bundles(ent):
    rows = ent.missing_all_bundle_batch_at(
        "cloud_pro",
        [None, 42, "not a dict", [], {"features": ["fleet"]}],
    )
    assert len(rows) == 5


def test_helper_never_raises_on_bad_axis_types(ent):
    rows = ent.missing_all_bundle_batch_at(
        "cloud_pro",
        [
            {
                "features": 42,
                "runtimes": None,
                "channels": [],
                "retention_days": {"nope": True},
                "nodes": object(),
            }
        ],
    )
    r = rows[0]
    assert r["features"] == []
    assert r["runtimes"] == []
    assert r["channels"] is None
    assert r["retention_days"] is None
    assert r["nodes"] is None


# -- API: happy path ----------------------------------------------------------


def test_api_happy(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=cloud_pro",
        json={
            "bundles": [
                {"features": ["fleet"], "runtimes": ["claude_code"]},
                {"channels": 5, "retention_days": 30, "nodes": 2},
                {},
            ]
        },
    )
    assert r.status_code == 200
    j = r.get_json()
    assert set(j.keys()) == _AT_ENVELOPE_KEYS
    assert j["perspective_tier"] == "cloud_pro"
    assert isinstance(j["perspective_tier_label"], str)
    assert j["perspective_tier_label"] == ent.tier_label("cloud_pro")
    assert j["perspective_tier_rank"] == ent.tier_rank("cloud_pro")
    assert j["count"] == 3
    assert len(j["bundles"]) == 3
    for row in j["bundles"]:
        assert set(row.keys()) == _ROW_KEYS
        assert set(row["missing"].keys()) == _MISSING_SLOT_KEYS
        # cloud_pro grants the paid bundle -- nothing missing.
        assert row["missing"] == _empty_missing()


def test_api_oss_denies_paid_feature_even_in_grace(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 200
    j = r.get_json()
    row = j["bundles"][0]
    assert row["features"] == ["fleet"]
    # Grace-independent -- the _at fold reads the static per-tier
    # tables, so OSS denies fleet even in grace.
    assert row["missing"]["features"] == ["fleet"]


def test_api_single_bundle_shorthand(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss",
        json={"bundles": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 1
    assert j["bundles"][0]["features"] == ["fleet"]


def test_api_alias_canonicalised(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss",
        json={"bundles": [{"runtimes": ["claude-code", "claude_code"]}]},
    )
    row = r.get_json()["bundles"][0]
    assert row["runtimes"] == ["claude_code"]
    assert row["missing"]["runtimes"] == ["claude_code"]


def test_api_capacity_coercion(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss",
        json={"bundles": [{"channels": "5", "retention_days": "notanint"}]},
    )
    row = r.get_json()["bundles"][0]
    assert row["channels"] == 5
    assert row["retention_days"] is None


def test_api_tier_case_and_whitespace_normalised(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=%20Cloud_Pro%20",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "cloud_pro"


# -- API: error paths ---------------------------------------------------------


def test_api_missing_tier_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_api_blank_tier_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=%20%20%20",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing tier"


def test_api_unknown_tier_404(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=bogus",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["error"] == "unknown tier"
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_api_missing_bundles_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss", json={}
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


def test_api_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss",
        json={"bundles": []},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "empty bundles"


def test_api_non_list_bundles_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss",
        json={"bundles": 42},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "bundles must be a list"


def test_api_no_body_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss"
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


# -- API: cross-endpoint axis-echo parity -------------------------------------


def test_api_axis_echo_parity_with_has_all_bundle_batch_at(client):
    body = {
        "bundles": [
            {
                "features": ["FLEET", "fleet", "sso"],
                "runtimes": ["claude-code", "codex"],
                "channels": "5",
                "retention_days": "30",
                "nodes": "2",
            },
            {"features": ["otel_export"]},
            {},
        ]
    }
    miss = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=cloud_pro",
        json=body,
    ).get_json()
    has = client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=cloud_pro",
        json=body,
    ).get_json()
    axes = ("features", "runtimes", "channels", "retention_days", "nodes")
    for m, h in zip(miss["bundles"], has["bundles"]):
        for k in axes:
            assert m[k] == h[k]


def test_api_perspective_envelope_parity_with_has_all_bundle_batch_at(client):
    body = {"bundles": [{"features": ["fleet"]}]}
    miss = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=cloud_starter",
        json=body,
    ).get_json()
    has = client.post(
        "/api/entitlement/has-all-bundle-batch-at?tier=cloud_starter",
        json=body,
    ).get_json()
    for k in (
        "perspective_tier",
        "perspective_tier_label",
        "perspective_tier_rank",
    ):
        assert miss[k] == has[k]


# -- API: row-shape parity with the singular missing-all-at endpoint ----------


def test_api_row_missing_matches_singular_endpoint(client):
    """Per-bundle ``missing`` byte-equals the singular
    ``/missing-all-at?tier=oss`` endpoint's body on the same known
    bundle."""
    bundle = {"features": ["fleet", "sso"], "runtimes": ["claude_code"]}
    batch = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss",
        json={"bundles": [bundle]},
    ).get_json()
    singular = client.get(
        "/api/entitlement/missing-all-at"
        "?tier=oss&features=fleet,sso&runtimes=claude_code"
    ).get_json()
    row_missing = batch["bundles"][0]["missing"]
    for k in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert row_missing[k] == singular.get(k)


# -- API: grace-independence (whole point of the _at slot) --------------------


def test_api_row_body_grace_independent(client, enforced_client):
    """Row body byte-equals across grace vs enforce fixtures."""
    body = {
        "bundles": [
            {"features": ["fleet", "sso"], "runtimes": ["claude_code"]},
            {"channels": 100, "retention_days": 365, "nodes": 100},
            {},
        ]
    }
    g = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss", json=body
    ).get_json()
    e = enforced_client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss", json=body
    ).get_json()
    assert g["bundles"] == e["bundles"]


# -- API: never-5xxs on delegate crash ----------------------------------------


def test_api_never_5xxs_on_delegate_crash(client, ent, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "missing_all_bundle_batch_at", _boom)
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=cloud_pro",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["bundles"] == []
    assert j["count"] == 0
    assert j["perspective_tier"] == "cloud_pro"


# -- envelope resolver-slot stability -----------------------------------------


def test_api_envelope_grace_flags(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    j = r.get_json()
    assert j["grace"] is True
    assert j["enforced"] is False


def test_api_envelope_enforce_flags(enforced_client):
    r = enforced_client.post(
        "/api/entitlement/missing-all-bundle-batch-at?tier=oss",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    j = r.get_json()
    assert j["grace"] is False
    assert j["enforced"] is True
