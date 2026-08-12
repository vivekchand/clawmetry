"""Tests for the aggregate bundle-batch row-detail
``/api/entitlement/missing-all-bundle-batch`` endpoint (plus the
:func:`clawmetry.entitlements.missing_all_bundle_batch` helper).

Row-detail complement of the sibling boolean-fold
``/api/entitlement/has-all-bundle-batch`` on the LIVE per-install slot:
where the boolean-fold answers "does the CURRENT install grant this whole
5-axis bundle?" for N caller-supplied aggregate bundles, this answers
"which axes of THIS bundle are still denied?" for the same N bundles in
ONE round-trip. Symmetric to ``/required-tier-bundle-batch`` on the
reverse-lookup slot and to ``/has-all-bundle-batch`` on the boolean-fold
slot: same POST body, same per-row axis echoes, only the fold slot
diverges (``missing`` dict vs ``has_all`` bool vs ``required_tier`` id).

Distinct from ``/missing-all-at`` (which fixes ONE bundle and reads
ONE hypothetical perspective tier): this fixes N bundles and reads the
LIVE per-install grant.

These tests pin:

* helper: per-bundle normalisation (feature/runtime CSV, runtime alias
  canonicalisation, capacity int coercion, blank / non-int axes collapse
  to ``None``, empty bundle surfaces as a stable row)
* helper: grace pass-through (paid feature / runtime / capacity in
  grace -> ``missing`` shape empty)
* helper: post-enforce paid feature / runtime / capacity surfaces on
  the corresponding ``missing`` slot
* helper: :data:`FREE_RUNTIMES` (``openclaw``) reports
  ``missing.runtimes=[]`` on the LIVE install regardless of rollout
* helper: per-row parity with the singular :func:`missing_all` scalar
* helper: never-crash on ``None`` / non-iterable / non-dict bundle input
* API happy path: 6-key envelope, 6-key row (with 5-key ``missing`` sub-
  dict), ``count``
* API single-bundle shorthand (bare-dict posture)
* API error paths: 400 on missing / non-list-non-dict / empty ``bundles``
* API cross-endpoint axis-echo parity with ``/has-all-bundle-batch`` and
  ``/required-tier-bundle-batch``
* API row ``missing`` byte-equals the singular ``/missing-all`` endpoint
  on the same known bundle
* API never-5xxs on a monkeypatched delegate crash
* grace vs enforce fold divergence on a paid bundle
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
    ``ent.grace`` off so the grace pass-through collapses and paid
    axes report their post-enforce denial in ``missing``."""
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

_ENVELOPE_KEYS = {
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


def test_helper_batch_folds_across_all_five_axes(ent):
    rows = ent.missing_all_bundle_batch(
        [
            {
                "features": ["fleet"],
                "runtimes": ["claude_code"],
                "channels": 5,
                "retention_days": 30,
                "nodes": 2,
            }
        ]
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
    # Grace pass-through: every axis empty for a fully-known bundle.
    assert r["missing"] == _empty_missing()


def test_helper_normalises_feature_csv(ent):
    rows = ent.missing_all_bundle_batch(
        [{"features": ["FLEET", "fleet", "", "sso"]}]
    )
    assert rows[0]["features"] == ["fleet", "sso"]


def test_helper_normalises_runtime_alias(ent):
    rows = ent.missing_all_bundle_batch(
        [{"runtimes": ["claude-code", "claude_code", "codex"]}]
    )
    assert rows[0]["runtimes"] == ["claude_code", "codex"]


def test_helper_coerces_capacity_axes(ent):
    rows = ent.missing_all_bundle_batch(
        [{"channels": "5", "retention_days": "30", "nodes": "2"}]
    )
    r = rows[0]
    assert r["channels"] == 5
    assert r["retention_days"] == 30
    assert r["nodes"] == 2


def test_helper_blank_capacity_collapses_to_none(ent):
    rows = ent.missing_all_bundle_batch(
        [{"channels": "", "retention_days": "notanint", "nodes": None}]
    )
    r = rows[0]
    assert r["channels"] is None
    assert r["retention_days"] is None
    assert r["nodes"] is None
    # A blank capacity drops from the fold entirely; grace pass-through
    # keeps the missing shape empty regardless.
    assert r["missing"] == _empty_missing()


def test_helper_empty_bundle_stable_row(ent):
    rows = ent.missing_all_bundle_batch([{}])
    r = rows[0]
    assert r["features"] == []
    assert r["runtimes"] == []
    assert r["channels"] is None
    assert r["retention_days"] is None
    assert r["nodes"] is None
    assert r["missing"] == _empty_missing()


def test_helper_none_returns_empty(ent):
    assert ent.missing_all_bundle_batch(None) == []


def test_helper_non_iterable_returns_empty(ent):
    assert ent.missing_all_bundle_batch(42) == []


def test_helper_none_bundle_row_stable(ent):
    rows = ent.missing_all_bundle_batch([None, {"features": ["fleet"]}])
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
    rows = ent.missing_all_bundle_batch([42, ["fleet"], {"features": ["fleet"]}])
    assert rows[0]["features"] == []
    assert rows[0]["missing"] == _empty_missing()
    assert rows[1]["features"] == []
    assert rows[1]["missing"] == _empty_missing()
    assert rows[2]["features"] == ["fleet"]


# -- helper: grace pass-through vs post-enforce fold --------------------------


def test_helper_grace_pass_through_paid_feature(ent):
    """Paid feature (``fleet``) is granted in grace; missing.features=[]."""
    rows = ent.missing_all_bundle_batch([{"features": ["fleet", "sso"]}])
    assert rows[0]["features"] == ["fleet", "sso"]
    assert rows[0]["missing"] == _empty_missing()


def test_helper_enforce_reports_paid_feature_missing(enforced):
    rows = enforced.missing_all_bundle_batch([{"features": ["fleet", "sso"]}])
    r = rows[0]
    assert set(r["missing"]["features"]) == {"fleet", "sso"}
    assert r["missing"]["runtimes"] == []
    assert r["missing"]["channels"] is None


def test_helper_grace_pass_through_paid_runtime(ent):
    rows = ent.missing_all_bundle_batch(
        [{"runtimes": ["claude_code", "codex"]}]
    )
    assert rows[0]["runtimes"] == ["claude_code", "codex"]
    assert rows[0]["missing"] == _empty_missing()


def test_helper_enforce_reports_paid_runtime_missing(enforced):
    rows = enforced.missing_all_bundle_batch(
        [{"runtimes": ["claude_code", "codex"]}]
    )
    r = rows[0]
    assert set(r["missing"]["runtimes"]) == {"claude_code", "codex"}
    assert r["missing"]["features"] == []


def test_helper_free_runtime_never_missing_in_grace(ent):
    """openclaw is FREE_RUNTIMES; missing.runtimes is empty regardless."""
    rows = ent.missing_all_bundle_batch([{"runtimes": ["openclaw"]}])
    assert rows[0]["runtimes"] == ["openclaw"]
    assert rows[0]["missing"]["runtimes"] == []


def test_helper_free_runtime_never_missing_after_enforce(enforced):
    rows = enforced.missing_all_bundle_batch([{"runtimes": ["openclaw"]}])
    assert rows[0]["missing"]["runtimes"] == []


def test_helper_enforce_reports_paid_capacity_missing(enforced):
    """Post-enforce, the free tier caps kick in and each supplied
    capacity int is surfaced on the ``missing`` slot if denied."""
    rows = enforced.missing_all_bundle_batch(
        [{"channels": 100, "retention_days": 365, "nodes": 100}]
    )
    r = rows[0]
    # The requested int is surfaced iff the resolved tier's cap denies
    # it -- exact ints echo through when denied.
    assert r["missing"]["channels"] == 100
    assert r["missing"]["retention_days"] == 365
    assert r["missing"]["nodes"] == 100


def test_helper_multiple_bundles_grace(ent):
    rows = ent.missing_all_bundle_batch(
        [
            {"features": ["fleet"]},
            {"runtimes": ["claude_code"]},
            {"channels": 5},
            {},
        ]
    )
    assert len(rows) == 4
    for r in rows:
        assert r["missing"] == _empty_missing()


def test_helper_multiple_bundles_enforce(enforced):
    rows = enforced.missing_all_bundle_batch(
        [
            {"features": ["fleet"]},
            {"runtimes": ["claude_code"]},
            {},
        ]
    )
    assert rows[0]["missing"]["features"] == ["fleet"]
    assert rows[0]["missing"]["runtimes"] == []
    assert rows[1]["missing"]["features"] == []
    assert rows[1]["missing"]["runtimes"] == ["claude_code"]
    assert rows[2]["missing"] == _empty_missing()


# -- helper: per-row parity with the singular scalar --------------------------


@pytest.mark.parametrize(
    "bundle",
    [
        {"features": ["fleet", "sso"]},
        {"runtimes": ["claude_code"]},
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 5, "retention_days": 30, "nodes": 2},
        {},
    ],
)
def test_helper_per_row_parity_with_singular_grace(ent, bundle):
    """Per-bundle ``missing`` byte-equals :func:`missing_all` on the
    same normalised inputs."""
    row = ent.missing_all_bundle_batch([bundle])[0]
    singular = ent.missing_all(
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


@pytest.mark.parametrize(
    "bundle",
    [
        {"features": ["fleet", "sso"]},
        {"runtimes": ["claude_code"]},
        {"features": ["fleet"], "runtimes": ["claude_code"]},
    ],
)
def test_helper_per_row_parity_with_singular_enforce(enforced, bundle):
    row = enforced.missing_all_bundle_batch([bundle])[0]
    singular = enforced.missing_all(
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


# -- helper: never-raise contract ---------------------------------------------


def test_helper_never_raises_on_bad_bundle(ent):
    rows = ent.missing_all_bundle_batch(
        [None, 42, "not a dict", [], {"features": ["fleet"]}]
    )
    assert len(rows) == 5


def test_helper_never_raises_on_bad_axis_types(ent):
    """Non-list features / runtimes and non-int capacity axes should
    not crash the row."""
    rows = ent.missing_all_bundle_batch(
        [
            {
                "features": 42,
                "runtimes": None,
                "channels": [],
                "retention_days": {"nope": True},
                "nodes": object(),
            }
        ]
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
        "/api/entitlement/missing-all-bundle-batch",
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
    assert set(j.keys()) == _ENVELOPE_KEYS
    assert j["count"] == 3
    assert len(j["bundles"]) == 3
    for row in j["bundles"]:
        assert set(row.keys()) == _ROW_KEYS
        assert set(row["missing"].keys()) == _MISSING_SLOT_KEYS
    # Grace pass-through per-row.
    for row in j["bundles"]:
        assert row["missing"] == _empty_missing()


def test_api_single_bundle_shorthand(client, ent):
    """Bare dict is treated as ONE bundle (matches ``/has-all-bundle-batch``
    posture)."""
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch",
        json={"bundles": {"features": ["fleet"]}},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["count"] == 1
    assert j["bundles"][0]["features"] == ["fleet"]


def test_api_alias_canonicalised(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch",
        json={"bundles": [{"runtimes": ["claude-code", "claude_code"]}]},
    )
    row = r.get_json()["bundles"][0]
    assert row["runtimes"] == ["claude_code"]


def test_api_capacity_coercion(client, ent):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch",
        json={"bundles": [{"channels": "5", "retention_days": "notanint"}]},
    )
    row = r.get_json()["bundles"][0]
    assert row["channels"] == 5
    assert row["retention_days"] is None


# -- API: error paths ---------------------------------------------------------


def test_api_missing_bundles_400(client):
    r = client.post("/api/entitlement/missing-all-bundle-batch", json={})
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


def test_api_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch",
        json={"bundles": []},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "empty bundles"


def test_api_non_list_bundles_400(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch",
        json={"bundles": 42},
    )
    assert r.status_code == 400
    assert r.get_json()["error"] == "bundles must be a list"


def test_api_no_body_400(client):
    r = client.post("/api/entitlement/missing-all-bundle-batch")
    assert r.status_code == 400
    assert r.get_json()["error"] == "missing bundles"


# -- API: cross-endpoint axis-echo parity -------------------------------------


def test_api_axis_echo_parity_with_has_all_bundle_batch(client):
    """features / runtimes / channels / retention_days / nodes echoes
    byte-equal ``/has-all-bundle-batch`` on the same body."""
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
    missing_bat = client.post(
        "/api/entitlement/missing-all-bundle-batch", json=body
    ).get_json()
    has_bat = client.post(
        "/api/entitlement/has-all-bundle-batch", json=body
    ).get_json()
    axes = ("features", "runtimes", "channels", "retention_days", "nodes")
    for m, h in zip(missing_bat["bundles"], has_bat["bundles"]):
        for k in axes:
            assert m[k] == h[k]


def test_api_axis_echo_parity_with_required_tier_bundle_batch(client):
    body = {
        "bundles": [
            {"features": ["fleet"], "runtimes": ["claude_code"]},
            {"channels": 5, "retention_days": 30, "nodes": 2},
        ]
    }
    missing_bat = client.post(
        "/api/entitlement/missing-all-bundle-batch", json=body
    ).get_json()
    req_bat = client.post(
        "/api/entitlement/required-tier-bundle-batch", json=body
    ).get_json()
    axes = ("features", "runtimes", "channels", "retention_days", "nodes")
    for m, r in zip(missing_bat["bundles"], req_bat["bundles"]):
        for k in axes:
            assert m[k] == r[k]


# -- API: row-shape parity with the singular missing-all endpoint -------------


def test_api_row_missing_matches_singular_endpoint(client):
    """Per-bundle ``missing`` byte-equals the singular ``/missing-all``
    endpoint's body on the same known bundle."""
    bundle = {"features": ["fleet", "sso"], "runtimes": ["claude_code"]}
    batch = client.post(
        "/api/entitlement/missing-all-bundle-batch",
        json={"bundles": [bundle]},
    ).get_json()
    singular = client.get(
        "/api/entitlement/missing-all"
        "?features=fleet,sso&runtimes=claude_code"
    ).get_json()
    row_missing = batch["bundles"][0]["missing"]
    for k in ("features", "runtimes", "channels", "retention_days", "nodes"):
        assert row_missing[k] == singular.get(k)


# -- API: never-5xxs on delegate crash ----------------------------------------


def test_api_never_5xxs_on_delegate_crash(client, ent, monkeypatch):
    def _boom(*_a, **_kw):
        raise RuntimeError("delegate boom")

    monkeypatch.setattr(ent, "missing_all_bundle_batch", _boom)
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    assert r.status_code == 200
    j = r.get_json()
    assert j["bundles"] == []
    assert j["count"] == 0


# -- grace vs enforce fold divergence -----------------------------------------


def test_api_grace_fold_pass_through(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    j = r.get_json()
    assert j["bundles"][0]["features"] == ["fleet"]
    assert j["bundles"][0]["missing"] == _empty_missing()


def test_api_enforce_fold_denies_paid_feature(enforced_client):
    r = enforced_client.post(
        "/api/entitlement/missing-all-bundle-batch",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    j = r.get_json()
    row = j["bundles"][0]
    assert row["features"] == ["fleet"]
    assert row["missing"]["features"] == ["fleet"]


def test_api_enforce_fold_denies_paid_runtime(enforced_client):
    r = enforced_client.post(
        "/api/entitlement/missing-all-bundle-batch",
        json={"bundles": [{"runtimes": ["claude_code"]}]},
    )
    j = r.get_json()
    row = j["bundles"][0]
    assert row["runtimes"] == ["claude_code"]
    assert row["missing"]["runtimes"] == ["claude_code"]


# -- envelope resolver-slot stability -----------------------------------------


def test_api_envelope_grace_flags(client):
    r = client.post(
        "/api/entitlement/missing-all-bundle-batch",
        json={"bundles": [{"features": ["fleet"]}]},
    )
    j = r.get_json()
    assert j["grace"] is True
    assert j["enforced"] is False
