"""Tests for
``clawmetry.entitlements.feature_spec_at_path(perspective, from, to, feature)``
+ ``feature_spec_at_path_batch(perspective, from, to, features)`` + the
``GET /api/entitlement/feature-spec-at-path`` and ``GET
/api/entitlement/feature-spec-at-path-batch`` endpoints.

Perspective-validated what-if sibling of :func:`feature_spec_path` /
:func:`feature_spec_path_batch`: perspective is validated but does NOT
shape the ``path`` rows, so an upgrade-walkthrough surface can call
``X_at_path(perspective, from, to, ...)`` uniformly across the whole
``_at_path`` family (alongside ``preview_at_path`` and
``tier_catalog_at_path``).

Pins:

* body byte-parity with :func:`feature_spec_path` for every
  ``(perspective, from, to, feature)`` triple; perspective invariance
  (rows byte-identical across shifting perspective for the same
  ``(from, to, feature)``)
* per-rung path row byte-equals :func:`feature_spec_at(rung, feature)`
  after dropping the three ``rung*`` keys (delegated from
  :func:`feature_spec_path`, pinned by
  ``test_entitlement_feature_spec_path``)
* batch per-feature ``path`` byte-equals scalar
  :func:`feature_spec_at_path(perspective, from, to, feature)`
* unknown perspective / from / to / feature → ``None`` (scalar); batch
  short-circuits to ``None`` on unknown perspective / from / to and
  buckets unknown features into ``unknown[]``
* case + whitespace normalisation on all four ids
* trial accepted as perspective + endpoint (lateral / identity branch)
* grace vs enforce identical rows (delegates to
  :func:`feature_spec_path` which walks static per-tier maps)
* API surface: 400 on missing / blank / empty args, 404 with ``which``
  bucketing on unknown tier ids, unknown feature ids echoed into
  ``unknown[]`` on the batch endpoint (never 404), 200 envelope with
  ``perspective_tier`` echo + standard ``_at*`` resolver-context tail
  on the happy path
* endpoint never 5xxs on resolver crash
"""
from __future__ import annotations

import importlib
from itertools import product

import pytest
from flask import Flask


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
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


ALL_TIERS = (
    "oss",
    "cloud_free",
    "trial",
    "cloud_starter",
    "cloud_pro",
    "pro",
    "enterprise",
)

SAMPLE_FEATURES = (
    "sessions",
    "custom_alerts",
    "fleet",
    "sso",
    "anomaly_detection",
)

_RUNG_KEYS = {"rung", "rung_label", "rung_rank"}

_SCALAR_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "feature",
    "path",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}

_BATCH_ENVELOPE_KEYS = {
    "perspective_tier",
    "perspective_tier_rank",
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "features",
    "unknown",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# ── scalar helper: shape + invariants ────────────────────────────────────────


def test_scalar_returns_list(ent):
    path = ent.feature_spec_at_path(
        "cloud_pro", "oss", "enterprise", "custom_alerts"
    )
    assert isinstance(path, list)
    assert len(path) >= 1


def test_scalar_body_byte_parity_with_feature_spec_path(ent):
    """Perspective must NOT shape the rows -- delegation to
    :func:`feature_spec_path` is byte-identical for every perspective."""
    for perspective, f, t, feat in product(
        ALL_TIERS, ALL_TIERS, ALL_TIERS, SAMPLE_FEATURES
    ):
        at_path = ent.feature_spec_at_path(perspective, f, t, feat)
        direct = ent.feature_spec_path(f, t, feat)
        assert at_path == direct, (perspective, f, t, feat)


def test_scalar_perspective_invariance(ent):
    """Rows must be byte-identical across every perspective for the same
    ``(from, to, feature)`` triple."""
    for f, t, feat in product(("oss", "cloud_free"), ("enterprise", "pro"), SAMPLE_FEATURES):
        rows_by_perspective = [
            ent.feature_spec_at_path(p, f, t, feat) for p in ALL_TIERS
        ]
        first = rows_by_perspective[0]
        for other in rows_by_perspective[1:]:
            assert other == first


def test_scalar_per_rung_byte_equality_with_feature_spec_at(ent):
    """Dropping the three ``rung*`` keys from a path row yields exact
    byte-equality with :func:`feature_spec_at(rung, feature)` -- a
    property inherited from :func:`feature_spec_path`."""
    path = ent.feature_spec_at_path(
        "cloud_pro", "oss", "enterprise", "custom_alerts"
    )
    for row in path:
        body = {k: v for k, v in row.items() if k not in _RUNG_KEYS}
        direct = ent.feature_spec_at(row["rung"], "custom_alerts")
        assert body == direct


def test_scalar_identity_returns_empty_path(ent):
    path = ent.feature_spec_at_path("cloud_pro", "cloud_pro", "cloud_pro", "custom_alerts")
    assert path == []


def test_scalar_lateral_returns_single_row(ent):
    # cloud_pro and pro share a rank; lateral returns a single-row path.
    path = ent.feature_spec_at_path("oss", "cloud_pro", "pro", "custom_alerts")
    assert isinstance(path, list)
    assert len(path) == 1
    assert path[0]["rung"] == "pro"


def test_scalar_upgrade_ranks_monotonic(ent):
    path = ent.feature_spec_at_path("oss", "oss", "enterprise", "custom_alerts")
    ranks = [r["rung_rank"] for r in path]
    assert ranks == sorted(ranks)


def test_scalar_downgrade_ranks_monotonic(ent):
    path = ent.feature_spec_at_path("oss", "enterprise", "oss", "custom_alerts")
    ranks = [r["rung_rank"] for r in path]
    assert ranks == sorted(ranks, reverse=True)


def test_scalar_trial_accepted_as_perspective(ent):
    path = ent.feature_spec_at_path("trial", "oss", "enterprise", "custom_alerts")
    assert path == ent.feature_spec_path("oss", "enterprise", "custom_alerts")


def test_scalar_trial_accepted_as_endpoint(ent):
    # trial as `to` is a valid lateral / identity endpoint via feature_spec_path.
    lat = ent.feature_spec_at_path("cloud_pro", "cloud_free", "trial", "custom_alerts")
    assert lat == ent.feature_spec_path("cloud_free", "trial", "custom_alerts")


def test_scalar_unknown_perspective_returns_none(ent):
    assert (
        ent.feature_spec_at_path("bogus", "oss", "enterprise", "custom_alerts")
        is None
    )


def test_scalar_unknown_from_returns_none(ent):
    assert (
        ent.feature_spec_at_path("cloud_pro", "bogus", "enterprise", "custom_alerts")
        is None
    )


def test_scalar_unknown_to_returns_none(ent):
    assert (
        ent.feature_spec_at_path("cloud_pro", "oss", "bogus", "custom_alerts")
        is None
    )


def test_scalar_unknown_feature_returns_none(ent):
    assert (
        ent.feature_spec_at_path("cloud_pro", "oss", "enterprise", "no_such_feat")
        is None
    )


def test_scalar_none_inputs_return_none(ent):
    assert ent.feature_spec_at_path(None, "oss", "enterprise", "custom_alerts") is None
    assert ent.feature_spec_at_path("cloud_pro", None, "enterprise", "custom_alerts") is None
    assert ent.feature_spec_at_path("cloud_pro", "oss", None, "custom_alerts") is None
    assert ent.feature_spec_at_path("cloud_pro", "oss", "enterprise", None) is None


def test_scalar_case_and_whitespace_normalised(ent):
    a = ent.feature_spec_at_path(
        "  Cloud_PRO ", " oss ", " ENTERPRISE\t", " custom_alerts "
    )
    b = ent.feature_spec_at_path(
        "cloud_pro", "oss", "enterprise", "custom_alerts"
    )
    assert a == b


def test_scalar_never_raises_on_weird_types(ent):
    for weird in (b"bytes", 42, 3.14, [], {}):
        assert ent.feature_spec_at_path(weird, "oss", "enterprise", "custom_alerts") is None
        assert ent.feature_spec_at_path("cloud_pro", weird, "enterprise", "custom_alerts") is None
        assert ent.feature_spec_at_path("cloud_pro", "oss", weird, "custom_alerts") is None
        assert ent.feature_spec_at_path("cloud_pro", "oss", "enterprise", weird) is None


def test_scalar_grace_vs_enforce_identical(ent, monkeypatch):
    grace = ent.feature_spec_at_path(
        "cloud_pro", "oss", "enterprise", "custom_alerts"
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.feature_spec_at_path(
        "cloud_pro", "oss", "enterprise", "custom_alerts"
    )
    assert grace == enforced


# ── batch helper: shape + invariants ─────────────────────────────────────────


def test_batch_returns_dict_shape(ent):
    batch = ent.feature_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["custom_alerts", "sso"]
    )
    assert isinstance(batch, dict)
    assert set(batch.keys()) == {"features", "unknown"}
    assert isinstance(batch["features"], list)
    assert isinstance(batch["unknown"], list)


def test_batch_body_byte_parity_with_feature_spec_path_batch(ent):
    """Per-feature body must be byte-identical to
    :func:`feature_spec_path_batch` for every perspective."""
    features = ["custom_alerts", "sso", "fleet"]
    for perspective, f, t in product(ALL_TIERS, ("oss", "cloud_free"), ("enterprise", "pro")):
        at_batch = ent.feature_spec_at_path_batch(perspective, f, t, features)
        direct = ent.feature_spec_path_batch(f, t, features)
        assert at_batch == direct, (perspective, f, t)


def test_batch_perspective_invariance(ent):
    """Envelope byte-identical across every perspective for the same
    ``(from, to, features)`` triple."""
    features = ["custom_alerts", "sso"]
    envelopes = [
        ent.feature_spec_at_path_batch(p, "oss", "enterprise", features)
        for p in ALL_TIERS
    ]
    first = envelopes[0]
    for other in envelopes[1:]:
        assert other == first


def test_batch_row_path_equals_scalar_at_path(ent):
    """Each ``features[].path`` byte-equals scalar
    :func:`feature_spec_at_path(perspective, from, to, feature)`."""
    features = ["custom_alerts", "sso"]
    batch = ent.feature_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", features
    )
    for entry in batch["features"]:
        fid = entry["feature"]
        scalar = ent.feature_spec_at_path(
            "cloud_pro", "oss", "enterprise", fid
        )
        assert entry["path"] == scalar


def test_batch_unknown_features_bucketed(ent):
    batch = ent.feature_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["custom_alerts", "no_such_feat", "sso"]
    )
    assert [e["feature"] for e in batch["features"]] == ["custom_alerts", "sso"]
    assert batch["unknown"] == ["no_such_feat"]


def test_batch_all_unknown_features(ent):
    batch = ent.feature_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["nope1", "nope2"]
    )
    assert batch == {"features": [], "unknown": ["nope1", "nope2"]}


def test_batch_unknown_perspective_returns_none(ent):
    assert (
        ent.feature_spec_at_path_batch(
            "bogus", "oss", "enterprise", ["custom_alerts"]
        )
        is None
    )


def test_batch_unknown_from_returns_none(ent):
    assert (
        ent.feature_spec_at_path_batch(
            "cloud_pro", "bogus", "enterprise", ["custom_alerts"]
        )
        is None
    )


def test_batch_unknown_to_returns_none(ent):
    assert (
        ent.feature_spec_at_path_batch(
            "cloud_pro", "oss", "bogus", ["custom_alerts"]
        )
        is None
    )


def test_batch_trial_accepted_as_perspective(ent):
    batch = ent.feature_spec_at_path_batch(
        "trial", "oss", "enterprise", ["custom_alerts", "sso"]
    )
    assert batch == ent.feature_spec_path_batch("oss", "enterprise", ["custom_alerts", "sso"])


def test_batch_case_and_whitespace_normalised(ent):
    a = ent.feature_spec_at_path_batch(
        "  Cloud_PRO ", " oss ", " ENTERPRISE ", ["custom_alerts", "SSO"]
    )
    b = ent.feature_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["custom_alerts", "sso"]
    )
    assert a == b


def test_batch_grace_vs_enforce_identical(ent, monkeypatch):
    grace = ent.feature_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["custom_alerts", "sso"]
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.feature_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["custom_alerts", "sso"]
    )
    assert grace == enforced


def test_batch_per_feature_crash_shorts_into_unknown(ent, monkeypatch):
    """A per-feature delegation crash must short-circuit into
    ``unknown[]`` -- the rest of the batch keeps building."""

    real = ent.feature_spec_path

    def _boom(f, t, feat):
        if feat == "sso":
            raise RuntimeError("boom")
        return real(f, t, feat)

    monkeypatch.setattr(ent, "feature_spec_path", _boom)
    batch = ent.feature_spec_at_path_batch(
        "cloud_pro", "oss", "enterprise", ["custom_alerts", "sso", "fleet"]
    )
    assert [e["feature"] for e in batch["features"]] == ["custom_alerts", "fleet"]
    assert batch["unknown"] == ["sso"]


# ── HTTP scalar: /api/entitlement/feature-spec-at-path ────────────────────────


def test_http_scalar_envelope_shape(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&feature=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _SCALAR_ENVELOPE_KEYS
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"
    assert body["direction"] == "upgrade"
    assert body["feature"] == "custom_alerts"
    assert isinstance(body["path"], list) and body["path"]


def test_http_scalar_missing_tier(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path?from=oss&to=enterprise&feature=custom_alerts"
    )
    assert r.status_code == 400


def test_http_scalar_missing_from(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path?tier=cloud_pro&to=enterprise&feature=custom_alerts"
    )
    assert r.status_code == 400


def test_http_scalar_missing_to(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path?tier=cloud_pro&from=oss&feature=custom_alerts"
    )
    assert r.status_code == 400


def test_http_scalar_missing_feature(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path?tier=cloud_pro&from=oss&to=enterprise"
    )
    assert r.status_code == 400


def test_http_scalar_unknown_tier_404_which_tier(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path"
        "?tier=bogus&from=oss&to=enterprise&feature=custom_alerts"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_http_scalar_unknown_from_404_which_from(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path"
        "?tier=cloud_pro&from=bogus&to=enterprise&feature=custom_alerts"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "from"


def test_http_scalar_unknown_to_404_which_to(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path"
        "?tier=cloud_pro&from=oss&to=bogus&feature=custom_alerts"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "to"


def test_http_scalar_unknown_feature_404_which_feature(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&feature=no_such_feat"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "feature"
    assert body["feature"] == "no_such_feat"


def test_http_scalar_trial_accepted_as_perspective(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path"
        "?tier=trial&from=oss&to=enterprise&feature=custom_alerts"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "trial"


def test_http_scalar_identity_empty_path(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path"
        "?tier=cloud_pro&from=cloud_pro&to=cloud_pro&feature=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_http_scalar_downgrade_direction(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path"
        "?tier=cloud_pro&from=enterprise&to=oss&feature=custom_alerts"
    )
    assert r.status_code == 200
    assert r.get_json()["direction"] == "downgrade"


def test_http_scalar_case_whitespace_normalised(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path"
        "?tier=%20Cloud_PRO%20&from=%20OSS%20&to=%20ENTERPRISE%20&feature=%20custom_alerts%20"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"
    assert body["feature"] == "custom_alerts"


def test_http_scalar_path_parity_with_feature_spec_path(client):
    """``path`` in the ``_at_path`` envelope must byte-equal ``path`` in
    ``/feature-spec-path`` for the same ``(from, to, feature)``."""
    r_at = client.get(
        "/api/entitlement/feature-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&feature=custom_alerts"
    )
    r_base = client.get(
        "/api/entitlement/feature-spec-path"
        "?from=oss&to=enterprise&feature=custom_alerts"
    )
    assert r_at.get_json()["path"] == r_base.get_json()["path"]


def test_http_scalar_perspective_invariance(client):
    baseline = client.get(
        "/api/entitlement/feature-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&feature=custom_alerts"
    ).get_json()["path"]
    for p in ALL_TIERS:
        got = client.get(
            f"/api/entitlement/feature-spec-at-path?tier={p}&from=oss&to=enterprise&feature=custom_alerts"
        ).get_json()["path"]
        assert got == baseline, p


# ── HTTP batch: /api/entitlement/feature-spec-at-path-batch ──────────────────


def test_http_batch_envelope_shape(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&features=custom_alerts,sso,fleet"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _BATCH_ENVELOPE_KEYS
    assert body["perspective_tier"] == "cloud_pro"
    assert body["direction"] == "upgrade"
    assert [e["feature"] for e in body["features"]] == ["custom_alerts", "sso", "fleet"]
    assert body["unknown"] == []


def test_http_batch_missing_tier(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?from=oss&to=enterprise&features=custom_alerts"
    )
    assert r.status_code == 400


def test_http_batch_missing_from(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=cloud_pro&to=enterprise&features=custom_alerts"
    )
    assert r.status_code == 400


def test_http_batch_missing_to(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&features=custom_alerts"
    )
    assert r.status_code == 400


def test_http_batch_missing_features_400(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise"
    )
    assert r.status_code == 400


def test_http_batch_empty_features_400(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&features="
    )
    assert r.status_code == 400


def test_http_batch_unknown_tier_404_which_tier(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=bogus&from=oss&to=enterprise&features=custom_alerts"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "tier"


def test_http_batch_unknown_from_404_which_from(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=cloud_pro&from=bogus&to=enterprise&features=custom_alerts"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "from"


def test_http_batch_unknown_to_404_which_to(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=bogus&features=custom_alerts"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "to"


def test_http_batch_unknown_feature_bucketed_not_404(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&features=custom_alerts,no_such_feat,sso"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [e["feature"] for e in body["features"]] == ["custom_alerts", "sso"]
    assert body["unknown"] == ["no_such_feat"]


def test_http_batch_features_parity_with_feature_spec_path_batch(client):
    """``features[]`` in the ``_at_path_batch`` envelope must byte-equal
    ``features[]`` in ``/feature-spec-path-batch`` for the same
    ``(from, to, features)``."""
    r_at = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&features=custom_alerts,sso"
    )
    r_base = client.get(
        "/api/entitlement/feature-spec-path-batch"
        "?from=oss&to=enterprise&features=custom_alerts,sso"
    )
    assert r_at.get_json()["features"] == r_base.get_json()["features"]


def test_http_batch_perspective_invariance(client):
    baseline = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&features=custom_alerts,sso"
    ).get_json()["features"]
    for p in ALL_TIERS:
        got = client.get(
            f"/api/entitlement/feature-spec-at-path-batch?tier={p}&from=oss&to=enterprise&features=custom_alerts,sso"
        ).get_json()["features"]
        assert got == baseline, p


def test_http_batch_trial_accepted_as_perspective(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=trial&from=oss&to=enterprise&features=custom_alerts,sso"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "trial"


def test_http_batch_case_whitespace_normalised(client):
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=%20Cloud_PRO%20&from=%20OSS%20&to=%20ENTERPRISE%20"
        "&features=%20custom_alerts%20,%20SSO%20"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"
    assert [e["feature"] for e in body["features"]] == ["custom_alerts", "sso"]


def test_http_batch_never_5xxs_on_resolver_crash(client, monkeypatch, ent):
    monkeypatch.setattr(
        ent,
        "feature_spec_at_path_batch",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    r = client.get(
        "/api/entitlement/feature-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=enterprise&features=custom_alerts,sso"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["features"] == []
    assert body["unknown"] == []
    assert body["grace"] is True


def test_http_scalar_never_5xxs_on_resolver_crash(client, monkeypatch, ent):
    monkeypatch.setattr(
        ent,
        "feature_spec_at_path",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    r = client.get(
        "/api/entitlement/feature-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise&feature=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["path"] == []
    assert body["grace"] is True
