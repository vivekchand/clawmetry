"""Tests for the bundle-shaped batch-path pair:
:func:`clawmetry.entitlements.has_all_bundle_at_path_batch` /
:func:`clawmetry.entitlements.missing_all_bundle_at_path_batch` and
their paired POST
``/api/entitlement/has-all-bundle-at-path-batch`` /
``/api/entitlement/missing-all-bundle-at-path-batch`` endpoints.

Destination-batch siblings of :func:`has_all_bundle_at_path` /
:func:`missing_all_bundle_at_path` (singular destination) and bundle-
shaped counterparts of :func:`has_all_at_path_batch` /
:func:`missing_all_at_path_batch` (kwargs-shaped batch-path). Fills the
``_at_path_batch`` slot on the aggregate bundle boolean-fold and row-
detail families.

Pins:

1. Per-destination row shape byte-parity with
   :func:`has_all_at_path_batch` / :func:`missing_all_at_path_batch`.
2. Per-rung ``path`` byte-parity with the singular
   :func:`has_all_bundle_at_path` / :func:`missing_all_bundle_at_path`
   for the same ``(from, to, bundle)`` triple.
3. Complement invariant with the paired boolean-fold call per
   destination per rung.
4. Grace-independence: same answer under grace-on vs enforce for the
   same ``(from, to_tiers, bundle)`` triple.
5. Unknown-from short-circuit returns ``None`` (scalar) / envelope
   with ``tiers=[]`` (endpoint); never 4xxs on endpoint validity.
6. Partial-unknown-``to`` posture: valid ids fill ``tiers[]`` while
   unknown ids echo in ``unknown[]`` / ``unknown_tiers[]``.
7. Direction detection per destination: ``upgrade`` / ``downgrade`` /
   ``lateral`` / ``identity``.
8. Bundle normalisation semantics inherited from the singular
   ``_bundle_at_path`` seat (non-dict collapses, runtime alias
   canonicalisation, unknown runtime drop, unknown feature typo
   collapse on has-side).
9. Envelope-level rollup fields (``allowed_count`` / ``all_allowed`` /
   ``any_allowed`` for has; ``denied_count`` / ``all_denied`` /
   ``any_denied`` for missing).
10. Never-5xxs on delegate blowup: endpoint returns the fallback
    envelope with ``tiers=[]``.
11. Envelope shape (fixed key set) byte-stable across every input
    branch on both endpoints.
12. POST body wrapped form + bare-dict shorthand both accepted; 400 on
    missing / non-object bundle.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask

# -- Fixtures ---------------------------------------------------------


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


# -- Envelope + row shape constants -----------------------------------

_ENVELOPE_KEYS = {
    "from",
    "from_label",
    "from_rank",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown_tiers",
    "tiers",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}

_TIER_KEYS_HAS = {
    "to",
    "to_label",
    "to_rank",
    "direction",
    "path",
    "path_length",
    "allowed_count",
    "all_allowed",
    "any_allowed",
}

_TIER_KEYS_MISSING = {
    "to",
    "to_label",
    "to_rank",
    "direction",
    "path",
    "path_length",
    "denied_count",
    "all_denied",
    "any_denied",
}

_HAS_ROW_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "has_all_at",
}

_MISSING_ROW_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "missing",
}


def _post_json(client, url, body):
    resp = client.post(url, json=body)
    assert resp.status_code == 200, (
        url,
        resp.status_code,
        resp.get_data(as_text=True),
    )
    return resp.get_json()


# -- Scalar: unknown-from short-circuit -------------------------------


@pytest.mark.parametrize("bad", ["bogus", "", None])
def test_has_scalar_unknown_from_returns_none(ent, bad):
    assert (
        ent.has_all_bundle_at_path_batch(
            bad, ["cloud_pro"], {"features": ["fleet"]}
        )
        is None
    )


@pytest.mark.parametrize("bad", ["bogus", "", None])
def test_missing_scalar_unknown_from_returns_none(ent, bad):
    assert (
        ent.missing_all_bundle_at_path_batch(
            bad, ["cloud_pro"], {"features": ["fleet"]}
        )
        is None
    )


# -- Scalar: shape + parity with the singular -------------------------


def test_has_scalar_shape(ent):
    r = ent.has_all_bundle_at_path_batch(
        "oss",
        ["cloud_starter", "cloud_pro", "enterprise"],
        {"features": ["fleet"], "runtimes": ["claude_code"]},
    )
    assert set(r.keys()) == {"tiers", "unknown"}
    assert r["unknown"] == []
    for row in r["tiers"]:
        assert set(row.keys()) == {
            "to",
            "to_label",
            "to_rank",
            "direction",
            "path",
        }
        assert isinstance(row["path"], list)


def test_has_scalar_per_destination_path_parity_with_singular(ent):
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 5,
    }
    tos = ["cloud_starter", "cloud_pro", "enterprise", "trial"]
    r = ent.has_all_bundle_at_path_batch("oss", tos, bundle)
    for row in r["tiers"]:
        singular = ent.has_all_bundle_at_path("oss", row["to"], bundle)
        assert row["path"] == singular, row["to"]


def test_missing_scalar_per_destination_path_parity_with_singular(ent):
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 500,
    }
    tos = ["cloud_starter", "cloud_pro", "enterprise", "trial"]
    r = ent.missing_all_bundle_at_path_batch("oss", tos, bundle)
    for row in r["tiers"]:
        singular = ent.missing_all_bundle_at_path("oss", row["to"], bundle)
        assert row["path"] == singular, row["to"]


# -- Scalar: direction detection --------------------------------------


def test_has_scalar_direction_detection(ent):
    r = ent.has_all_bundle_at_path_batch(
        "cloud_pro",
        ["oss", "cloud_starter", "cloud_pro", "pro", "enterprise"],
        {"features": ["fleet"]},
    )
    by_to = {row["to"]: row for row in r["tiers"]}
    assert by_to["oss"]["direction"] == "downgrade"
    assert by_to["cloud_starter"]["direction"] == "downgrade"
    assert by_to["cloud_pro"]["direction"] == "identity"
    # cloud_pro and pro share rank 2.
    assert ent._TIER_RANK["cloud_pro"] == ent._TIER_RANK["pro"]
    assert by_to["pro"]["direction"] == "lateral"
    assert by_to["enterprise"]["direction"] == "upgrade"


def test_has_scalar_identity_row_has_empty_path(ent):
    r = ent.has_all_bundle_at_path_batch(
        "oss", ["oss"], {"features": ["fleet"]}
    )
    assert r["tiers"][0]["direction"] == "identity"
    assert r["tiers"][0]["path"] == []


# -- Scalar: partial-unknown-``to`` posture ---------------------------


def test_has_scalar_partial_unknown_to_echoes_in_unknown(ent):
    r = ent.has_all_bundle_at_path_batch(
        "oss",
        ["cloud_pro", "bogus", "enterprise", "totally_fake"],
        {"features": ["fleet"]},
    )
    assert [row["to"] for row in r["tiers"]] == ["cloud_pro", "enterprise"]
    assert r["unknown"] == ["bogus", "totally_fake"]


def test_missing_scalar_partial_unknown_to_echoes_in_unknown(ent):
    r = ent.missing_all_bundle_at_path_batch(
        "oss",
        ["cloud_pro", "bogus", "enterprise"],
        {"features": ["fleet"]},
    )
    assert [row["to"] for row in r["tiers"]] == ["cloud_pro", "enterprise"]
    assert r["unknown"] == ["bogus"]


def test_has_scalar_all_unknown_to_returns_empty_tiers(ent):
    r = ent.has_all_bundle_at_path_batch(
        "oss", ["bogus", "totally_fake"], {"features": ["fleet"]}
    )
    assert r == {
        "tiers": [],
        "unknown": ["bogus", "totally_fake"],
    }


def test_has_scalar_empty_to_returns_empty_tiers(ent):
    assert ent.has_all_bundle_at_path_batch(
        "oss", [], {"features": ["fleet"]}
    ) == {"tiers": [], "unknown": []}


def test_has_scalar_none_to_returns_empty_tiers(ent):
    assert ent.has_all_bundle_at_path_batch(
        "oss", None, {"features": ["fleet"]}
    ) == {"tiers": [], "unknown": []}


# -- Scalar: complement invariant -------------------------------------


def test_complement_invariant_per_rung_per_destination(ent):
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 500,
        "retention_days": 365,
        "nodes": 99,
    }
    tos = ["cloud_starter", "cloud_pro", "enterprise", "trial"]
    h = ent.has_all_bundle_at_path_batch("oss", tos, bundle)
    m = ent.missing_all_bundle_at_path_batch("oss", tos, bundle)
    assert [row["to"] for row in h["tiers"]] == [
        row["to"] for row in m["tiers"]
    ]
    for hrow, mrow in zip(h["tiers"], m["tiers"]):
        assert len(hrow["path"]) == len(mrow["path"])
        for hp, mp in zip(hrow["path"], mrow["path"]):
            assert hp["tier"] == mp["tier"]
            any_missing = any(
                v for v in mp["missing"].values() if v not in (None, [])
            )
            assert bool(any_missing) == (not hp["has_all_at"]), (
                hrow["to"],
                hp["tier"],
                hp["has_all_at"],
                mp["missing"],
            )


# -- Scalar: grace-independence ---------------------------------------


def test_has_scalar_grace_independence(ent, enforced):
    bundle = {"features": ["fleet"], "runtimes": ["claude_code"]}
    tos = ["cloud_starter", "cloud_pro", "enterprise"]
    assert ent.has_all_bundle_at_path_batch(
        "oss", tos, bundle
    ) == enforced.has_all_bundle_at_path_batch("oss", tos, bundle)


def test_missing_scalar_grace_independence(ent, enforced):
    bundle = {"features": ["fleet"], "runtimes": ["claude_code"]}
    tos = ["cloud_starter", "cloud_pro", "enterprise"]
    assert ent.missing_all_bundle_at_path_batch(
        "oss", tos, bundle
    ) == enforced.missing_all_bundle_at_path_batch("oss", tos, bundle)


# -- Scalar: bundle normalisation -------------------------------------


@pytest.mark.parametrize("bad_bundle", [None, "not-a-dict", 42, []])
def test_has_scalar_non_dict_bundle_collapses_fold_on_every_rung(
    ent, bad_bundle
):
    r = ent.has_all_bundle_at_path_batch("oss", ["enterprise"], bad_bundle)
    assert r["tiers"]
    for row in r["tiers"]:
        for prow in row["path"]:
            assert prow["has_all_at"] is False
            assert prow["features"] == []
            assert prow["runtimes"] == []


def test_has_scalar_runtime_alias_canonicalised_per_rung(ent):
    r = ent.has_all_bundle_at_path_batch(
        "oss", ["enterprise"], {"runtimes": ["claude-code"]}
    )
    for row in r["tiers"]:
        for prow in row["path"]:
            assert prow["runtimes"] == ["claude_code"]


def test_has_scalar_unknown_feature_collapses_fold_on_every_rung(ent):
    r = ent.has_all_bundle_at_path_batch(
        "oss", ["enterprise"], {"features": ["totally_bogus"]}
    )
    for row in r["tiers"]:
        for prow in row["path"]:
            assert prow["has_all_at"] is False


# -- Scalar: per-destination blowup posture ---------------------------


def test_has_scalar_delegate_blowup_short_circuits_only_that_row(
    monkeypatch, ent
):
    """A per-destination :func:`has_all_bundle_at_path` blowup logs a
    warning and short-circuits that id into ``unknown[]`` while the rest
    of the batch keeps building."""
    real = ent.has_all_bundle_at_path

    def _boom(from_tier, to_tier, bundle):
        if to_tier == "cloud_pro":
            raise RuntimeError("intentional")
        return real(from_tier, to_tier, bundle)

    monkeypatch.setattr(ent, "has_all_bundle_at_path", _boom)
    r = ent.has_all_bundle_at_path_batch(
        "oss",
        ["cloud_starter", "cloud_pro", "enterprise"],
        {"features": ["fleet"]},
    )
    assert [row["to"] for row in r["tiers"]] == [
        "cloud_starter",
        "enterprise",
    ]
    assert r["unknown"] == ["cloud_pro"]


# -- Endpoint: happy path ---------------------------------------------


def test_has_endpoint_upgrade_envelope_shape(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path-batch"
        "?from=oss&to=cloud_starter,cloud_pro,enterprise",
        {"bundle": {"features": ["fleet"], "runtimes": ["claude_code"]}},
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["from"] == "oss"
    assert body["unknown_tiers"] == []
    assert [row["to"] for row in body["tiers"]] == [
        "cloud_starter",
        "cloud_pro",
        "enterprise",
    ]
    for row in body["tiers"]:
        assert set(row.keys()) == _TIER_KEYS_HAS
        assert row["direction"] == "upgrade"
        assert row["path_length"] == len(row["path"])
        assert row["allowed_count"] == sum(
            1 for p in row["path"] if p["has_all_at"]
        )
        for prow in row["path"]:
            assert set(prow.keys()) == _HAS_ROW_KEYS


def test_missing_endpoint_upgrade_envelope_shape(client):
    body = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-at-path-batch"
        "?from=oss&to=cloud_starter,cloud_pro,enterprise",
        {"bundle": {"features": ["fleet"], "runtimes": ["claude_code"]}},
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    for row in body["tiers"]:
        assert set(row.keys()) == _TIER_KEYS_MISSING
        assert row["direction"] == "upgrade"
        assert row["path_length"] == len(row["path"])
        for prow in row["path"]:
            assert set(prow.keys()) == _MISSING_ROW_KEYS
            assert set(prow["missing"].keys()) == {
                "features",
                "runtimes",
                "channels",
                "retention_days",
                "nodes",
            }


def test_has_endpoint_axis_echo_matches_bundle(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path-batch?from=oss&to=enterprise",
        {
            "bundle": {
                "features": ["fleet"],
                "runtimes": ["claude-code"],
                "channels": 5,
            }
        },
    )
    assert body["features"] == ["fleet"]
    assert body["runtimes"] == ["claude_code"]
    assert body["channels"] == 5


def test_missing_endpoint_axis_echo_matches_bundle(client):
    body = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-at-path-batch?from=oss&to=enterprise",
        {"bundle": {"features": ["fleet"], "channels": 500}},
    )
    assert body["features"] == ["fleet"]
    assert body["channels"] == 500


def test_has_endpoint_bare_dict_shorthand_body(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path-batch?from=oss&to=cloud_pro,enterprise",
        {"features": ["fleet"]},
    )
    assert body["features"] == ["fleet"]
    assert len(body["tiers"]) == 2


def test_missing_endpoint_bare_dict_shorthand_body(client):
    body = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-at-path-batch"
        "?from=oss&to=cloud_pro,enterprise",
        {"features": ["fleet"]},
    )
    assert body["features"] == ["fleet"]
    assert len(body["tiers"]) == 2


# -- Endpoint: fold rollup ---------------------------------------------


def test_has_endpoint_all_allowed_true_when_every_rung_grants(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path-batch"
        "?from=cloud_pro&to=enterprise",
        {"bundle": {"features": ["fleet"]}},
    )
    assert body["tiers"]
    for row in body["tiers"]:
        assert row["all_allowed"] is True
        assert row["any_allowed"] is True
        assert row["allowed_count"] == row["path_length"]


def test_missing_endpoint_denied_flags_on_ungranted_bundle(client):
    """A bundle that requires enterprise-only capacity denies every
    rung short of enterprise."""
    body = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-at-path-batch"
        "?from=oss&to=enterprise",
        {"bundle": {"channels": 999999}},
    )
    tiers = body["tiers"]
    assert tiers
    for row in tiers:
        assert row["denied_count"] >= 0
        assert row["all_denied"] == all(
            any(v for v in p["missing"].values() if v not in (None, []))
            for p in row["path"]
        )
        assert row["any_denied"] == any(
            any(v for v in p["missing"].values() if v not in (None, []))
            for p in row["path"]
        )


# -- Endpoint: never-4xxs on endpoint validity ------------------------


def test_has_endpoint_unknown_from_returns_empty_tiers_200(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path-batch?from=bogus&to=cloud_pro",
        {"bundle": {"features": ["fleet"]}},
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tiers"] == []
    assert body["unknown_tiers"] == ["cloud_pro"]


def test_has_endpoint_missing_from_returns_empty_tiers_200(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path-batch?to=cloud_pro",
        {"bundle": {"features": ["fleet"]}},
    )
    assert body["tiers"] == []
    assert body["unknown_tiers"] == ["cloud_pro"]


def test_has_endpoint_empty_to_returns_empty_tiers_200(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path-batch?from=oss&to=",
        {"bundle": {"features": ["fleet"]}},
    )
    assert body["tiers"] == []
    assert body["unknown_tiers"] == []


def test_has_endpoint_partial_unknown_to_partitions_correctly(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path-batch"
        "?from=oss&to=cloud_pro,bogus,enterprise",
        {"bundle": {"features": ["fleet"]}},
    )
    assert [row["to"] for row in body["tiers"]] == [
        "cloud_pro",
        "enterprise",
    ]
    assert body["unknown_tiers"] == ["bogus"]


# -- Endpoint: 400 branches -------------------------------------------


def test_has_endpoint_missing_bundle_is_400(client):
    resp = client.post(
        "/api/entitlement/has-all-bundle-at-path-batch?from=oss&to=cloud_pro",
        json={},
    )
    assert resp.status_code == 400


def test_missing_endpoint_missing_bundle_is_400(client):
    resp = client.post(
        "/api/entitlement/missing-all-bundle-at-path-batch"
        "?from=oss&to=cloud_pro",
        json={},
    )
    assert resp.status_code == 400


def test_has_endpoint_non_object_bundle_is_400(client):
    resp = client.post(
        "/api/entitlement/has-all-bundle-at-path-batch?from=oss&to=cloud_pro",
        json={"bundle": "not-a-dict"},
    )
    assert resp.status_code == 400


def test_missing_endpoint_non_object_bundle_is_400(client):
    resp = client.post(
        "/api/entitlement/missing-all-bundle-at-path-batch"
        "?from=oss&to=cloud_pro",
        json={"bundle": ["not-a-dict"]},
    )
    assert resp.status_code == 400


# -- Endpoint: per-rung parity with singular /has-all-bundle-at-path --


def test_has_endpoint_per_rung_parity_with_singular_endpoint(client):
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 5,
    }
    tos = ["cloud_starter", "cloud_pro", "enterprise"]
    batch = _post_json(
        client,
        f"/api/entitlement/has-all-bundle-at-path-batch"
        f"?from=oss&to={','.join(tos)}",
        {"bundle": bundle},
    )
    for row in batch["tiers"]:
        singular = _post_json(
            client,
            f"/api/entitlement/has-all-bundle-at-path?from=oss&to={row['to']}",
            {"bundle": bundle},
        )
        assert len(row["path"]) == singular["path_length"]
        for bp, sp in zip(row["path"], singular["path"]):
            assert bp == sp, (row["to"], bp["tier"])


def test_missing_endpoint_per_rung_parity_with_singular_endpoint(client):
    bundle = {
        "features": ["fleet"],
        "runtimes": ["claude_code"],
        "channels": 500,
    }
    tos = ["cloud_starter", "cloud_pro", "enterprise"]
    batch = _post_json(
        client,
        f"/api/entitlement/missing-all-bundle-at-path-batch"
        f"?from=oss&to={','.join(tos)}",
        {"bundle": bundle},
    )
    for row in batch["tiers"]:
        singular = _post_json(
            client,
            f"/api/entitlement/missing-all-bundle-at-path?from=oss&to={row['to']}",
            {"bundle": bundle},
        )
        assert len(row["path"]) == singular["path_length"]
        for bp, sp in zip(row["path"], singular["path"]):
            assert bp == sp, (row["to"], bp["tier"])


# -- Endpoint: never-5xxs on body-builder blowup ----------------------


def test_has_endpoint_never_5xxs_on_body_builder_blowup(
    monkeypatch, client
):
    """A scalar blowup collapses to the fallback envelope with
    ``tiers=[]`` -- envelope key set stays byte-stable across the
    happy/fallback branches."""
    from clawmetry import entitlements as _e

    def _boom(*a, **k):
        raise RuntimeError("intentional")

    monkeypatch.setattr(_e, "has_all_bundle_at_path_batch", _boom)
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path-batch?from=oss&to=cloud_pro",
        {"bundle": {"features": ["fleet"]}},
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tiers"] == []


def test_missing_endpoint_never_5xxs_on_body_builder_blowup(
    monkeypatch, client
):
    from clawmetry import entitlements as _e

    def _boom(*a, **k):
        raise RuntimeError("intentional")

    monkeypatch.setattr(_e, "missing_all_bundle_at_path_batch", _boom)
    body = _post_json(
        client,
        "/api/entitlement/missing-all-bundle-at-path-batch"
        "?from=oss&to=cloud_pro",
        {"bundle": {"features": ["fleet"]}},
    )
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tiers"] == []


# -- Endpoint: identity + lateral edge branches -----------------------


def test_has_endpoint_identity_row_has_empty_path_but_axis_echo(client):
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path-batch?from=oss&to=oss",
        {"bundle": {"features": ["fleet"]}},
    )
    assert body["tiers"] == [
        {
            "to": "oss",
            "to_label": body["tiers"][0]["to_label"],
            "to_rank": body["tiers"][0]["to_rank"],
            "direction": "identity",
            "path": [],
            "path_length": 0,
            "allowed_count": 0,
            "all_allowed": False,
            "any_allowed": False,
        }
    ]
    # Axis echo still reflects the caller-supplied bundle even when no
    # rungs were walked (identity / cross-rung-empty branch).
    assert body["features"] == ["fleet"]


def test_has_endpoint_lateral_direction_single_rung(client):
    from clawmetry import entitlements as _e

    assert _e._TIER_RANK["cloud_pro"] == _e._TIER_RANK["pro"]
    body = _post_json(
        client,
        "/api/entitlement/has-all-bundle-at-path-batch"
        "?from=cloud_pro&to=pro",
        {"bundle": {"features": ["fleet"]}},
    )
    assert body["tiers"][0]["direction"] == "lateral"
    assert body["tiers"][0]["path_length"] == 1
    assert body["tiers"][0]["path"][0]["tier"] == "pro"
