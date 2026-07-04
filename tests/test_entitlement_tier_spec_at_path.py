"""Tests for
``clawmetry.entitlements.tier_spec_at_path(perspective, from, to)`` +
``tier_spec_at_path_batch(perspective, from, to_tiers)`` + the
``GET /api/entitlement/tier-spec-at-path`` and
``GET /api/entitlement/tier-spec-at-path-batch`` endpoints.

Tier-axis sibling of :func:`feature_spec_at_path` /
:func:`runtime_spec_at_path`: perspective is validated but does NOT
shape the ``path`` rows, so an upgrade-walkthrough surface can call
``X_at_path(perspective, from, to, ...)`` uniformly across the whole
``_at_path`` family (alongside ``preview_at_path`` and
``tier_catalog_at_path``).

Pins:

* body byte-parity with :func:`tier_spec_path` for every
  ``(perspective, from, to)`` triple; perspective invariance (rows
  byte-identical across shifting perspective for the same
  ``(from, to)``)
* per-rung path row byte-equals :func:`tier_spec_at(from, rung)`
  (delegated from :func:`tier_spec_path`, pinned by
  ``test_entitlement_tier_spec_path``)
* batch per-destination ``path`` byte-equals scalar
  :func:`tier_spec_at_path(perspective, from, to)`
* unknown perspective / from short-circuit to ``None`` (scalar and
  batch); scalar unknown ``to`` -> ``None``; batch unknown destinations
  bucketed into ``unknown[]``
* case + whitespace normalisation on all three ids
* trial accepted as perspective + endpoint (lateral / identity branch)
* grace vs enforce identical rows (delegates to :func:`tier_spec_path`
  which walks static per-tier maps)
* API surface: 400 on missing / blank / empty args, 404 with ``which``
  bucketing on unknown tier ids, unknown destination ids echoed into
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
    "tiers",
    "unknown",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


# ── scalar helper: shape + invariants ────────────────────────────────────────


def test_scalar_returns_list(ent):
    path = ent.tier_spec_at_path("cloud_pro", "oss", "enterprise")
    assert isinstance(path, list)
    assert len(path) >= 1


def test_scalar_body_byte_parity_with_tier_spec_path(ent):
    """Perspective must NOT shape the rows -- delegation to
    :func:`tier_spec_path` is byte-identical for every perspective."""
    for perspective, f, t in product(ALL_TIERS, ALL_TIERS, ALL_TIERS):
        at_path = ent.tier_spec_at_path(perspective, f, t)
        direct = ent.tier_spec_path(f, t)
        assert at_path == direct, (perspective, f, t)


def test_scalar_perspective_invariance(ent):
    """Rows must be byte-identical across every perspective for the same
    ``(from, to)`` pair."""
    for f, t in product(("oss", "cloud_free"), ("enterprise", "pro")):
        rows_by_perspective = [
            ent.tier_spec_at_path(p, f, t) for p in ALL_TIERS
        ]
        first = rows_by_perspective[0]
        for other in rows_by_perspective[1:]:
            assert other == first


def test_scalar_per_rung_byte_equality_with_tier_spec_at(ent):
    """Each path row byte-equals :func:`tier_spec_at(from, rung)` --
    property inherited from :func:`tier_spec_path`."""
    path = ent.tier_spec_at_path("cloud_pro", "oss", "enterprise")
    for row in path:
        direct = ent.tier_spec_at("oss", row["id"])
        assert row == direct


def test_scalar_identity_returns_empty_path(ent):
    assert ent.tier_spec_at_path("cloud_pro", "cloud_pro", "cloud_pro") == []


def test_scalar_lateral_returns_single_row(ent):
    # cloud_pro and pro share a rank; lateral returns a single-row path.
    path = ent.tier_spec_at_path("oss", "cloud_pro", "pro")
    assert isinstance(path, list)
    assert len(path) == 1
    assert path[0]["id"] == "pro"


def test_scalar_upgrade_ranks_non_decreasing(ent):
    """Upgrade walk is non-decreasing on the walk-order tier rank
    (same-rank siblings between the endpoints may appear together)."""
    path = ent.tier_spec_at_path("oss", "oss", "enterprise")
    ranks = [ent.tier_rank(r["id"]) for r in path]
    assert ranks == sorted(ranks)


def test_scalar_downgrade_ranks_non_increasing(ent):
    """Downgrade walk is non-increasing on the walk-order tier rank."""
    path = ent.tier_spec_at_path("oss", "enterprise", "oss")
    ranks = [ent.tier_rank(r["id"]) for r in path]
    assert ranks == sorted(ranks, reverse=True)


def test_scalar_trial_accepted_as_perspective(ent):
    path = ent.tier_spec_at_path("trial", "oss", "enterprise")
    assert path == ent.tier_spec_path("oss", "enterprise")


def test_scalar_trial_accepted_as_endpoint(ent):
    # trial as `to` is a valid lateral / identity endpoint via tier_spec_path.
    lat = ent.tier_spec_at_path("cloud_pro", "cloud_free", "trial")
    assert lat == ent.tier_spec_path("cloud_free", "trial")


def test_scalar_unknown_perspective_returns_none(ent):
    assert ent.tier_spec_at_path("bogus", "oss", "enterprise") is None


def test_scalar_unknown_from_returns_none(ent):
    # tier_spec_path itself short-circuits unknown ``from`` to ``None``.
    assert ent.tier_spec_at_path("cloud_pro", "bogus", "enterprise") is None


def test_scalar_unknown_to_returns_none(ent):
    assert ent.tier_spec_at_path("cloud_pro", "oss", "bogus") is None


def test_scalar_none_inputs_return_none(ent):
    assert ent.tier_spec_at_path(None, "oss", "enterprise") is None
    assert ent.tier_spec_at_path("cloud_pro", None, "enterprise") is None
    assert ent.tier_spec_at_path("cloud_pro", "oss", None) is None


def test_scalar_case_and_whitespace_normalised(ent):
    a = ent.tier_spec_at_path("  Cloud_PRO ", " oss ", " ENTERPRISE\t")
    b = ent.tier_spec_at_path("cloud_pro", "oss", "enterprise")
    assert a == b


def test_scalar_never_raises_on_weird_types(ent):
    for weird in (b"bytes", 42, 3.14, [], {}):
        assert ent.tier_spec_at_path(weird, "oss", "enterprise") is None
        assert ent.tier_spec_at_path("cloud_pro", weird, "enterprise") is None
        assert ent.tier_spec_at_path("cloud_pro", "oss", weird) is None


def test_scalar_grace_vs_enforce_identical(ent, monkeypatch):
    grace = ent.tier_spec_at_path("cloud_pro", "oss", "enterprise")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tier_spec_at_path("cloud_pro", "oss", "enterprise")
    assert grace == enforced


# ── batch helper: shape + invariants ─────────────────────────────────────────


def test_batch_returns_dict_shape(ent):
    batch = ent.tier_spec_at_path_batch(
        "cloud_pro", "oss", ["cloud_starter", "enterprise"]
    )
    assert isinstance(batch, dict)
    assert set(batch.keys()) == {"tiers", "unknown"}
    assert isinstance(batch["tiers"], list)
    assert isinstance(batch["unknown"], list)


def test_batch_body_byte_parity_with_tier_spec_path_batch(ent):
    """Per-destination body must be byte-identical to
    :func:`tier_spec_path_batch` for every perspective."""
    tos = ["cloud_starter", "cloud_pro", "enterprise"]
    for perspective, f in product(ALL_TIERS, ("oss", "cloud_free")):
        at_batch = ent.tier_spec_at_path_batch(perspective, f, tos)
        direct = ent.tier_spec_path_batch(f, tos)
        assert at_batch == direct, (perspective, f)


def test_batch_perspective_invariance(ent):
    """Envelope byte-identical across every perspective for the same
    ``(from, to_tiers)`` pair."""
    tos = ["cloud_starter", "enterprise"]
    envelopes = [
        ent.tier_spec_at_path_batch(p, "oss", tos) for p in ALL_TIERS
    ]
    first = envelopes[0]
    for other in envelopes[1:]:
        assert other == first


def test_batch_row_path_equals_scalar_at_path(ent):
    """Each ``tiers[].path`` byte-equals scalar
    :func:`tier_spec_at_path(perspective, from, to)`."""
    tos = ["cloud_starter", "enterprise"]
    batch = ent.tier_spec_at_path_batch("cloud_pro", "oss", tos)
    for row in batch["tiers"]:
        scalar = ent.tier_spec_at_path("cloud_pro", "oss", row["to"])
        assert row["path"] == scalar


def test_batch_unknown_destinations_bucketed(ent):
    batch = ent.tier_spec_at_path_batch(
        "cloud_pro", "oss", ["cloud_starter", "no_such_tier", "enterprise"]
    )
    assert [r["to"] for r in batch["tiers"]] == ["cloud_starter", "enterprise"]
    assert batch["unknown"] == ["no_such_tier"]


def test_batch_all_unknown_destinations(ent):
    batch = ent.tier_spec_at_path_batch(
        "cloud_pro", "oss", ["nope1", "nope2"]
    )
    assert batch == {"tiers": [], "unknown": ["nope1", "nope2"]}


def test_batch_unknown_perspective_returns_none(ent):
    assert (
        ent.tier_spec_at_path_batch("bogus", "oss", ["enterprise"]) is None
    )


def test_batch_unknown_from_returns_none(ent):
    assert (
        ent.tier_spec_at_path_batch("cloud_pro", "bogus", ["enterprise"])
        is None
    )


def test_batch_trial_accepted_as_perspective(ent):
    batch = ent.tier_spec_at_path_batch(
        "trial", "oss", ["cloud_starter", "enterprise"]
    )
    assert batch == ent.tier_spec_path_batch(
        "oss", ["cloud_starter", "enterprise"]
    )


def test_batch_case_and_whitespace_normalised(ent):
    a = ent.tier_spec_at_path_batch(
        "  Cloud_PRO ", " oss ", [" CLOUD_STARTER ", "enterprise "]
    )
    b = ent.tier_spec_at_path_batch(
        "cloud_pro", "oss", ["cloud_starter", "enterprise"]
    )
    assert a == b


def test_batch_grace_vs_enforce_identical(ent, monkeypatch):
    tos = ["cloud_starter", "enterprise"]
    grace = ent.tier_spec_at_path_batch("cloud_pro", "oss", tos)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.tier_spec_at_path_batch("cloud_pro", "oss", tos)
    assert grace == enforced


# ── HTTP scalar: /api/entitlement/tier-spec-at-path ──────────────────────────


def test_http_scalar_envelope_shape(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _SCALAR_ENVELOPE_KEYS
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"
    assert body["direction"] == "upgrade"
    assert isinstance(body["path"], list) and body["path"]


def test_http_scalar_missing_tier(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path?from=oss&to=enterprise"
    )
    assert r.status_code == 400


def test_http_scalar_missing_from(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path?tier=cloud_pro&to=enterprise"
    )
    assert r.status_code == 400


def test_http_scalar_missing_to(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path?tier=cloud_pro&from=oss"
    )
    assert r.status_code == 400


def test_http_scalar_unknown_tier_404_which_tier(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path"
        "?tier=bogus&from=oss&to=enterprise"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "bogus"


def test_http_scalar_unknown_from_404_which_from(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path"
        "?tier=cloud_pro&from=bogus&to=enterprise"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "from"


def test_http_scalar_unknown_to_404_which_to(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path"
        "?tier=cloud_pro&from=oss&to=bogus"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "to"


def test_http_scalar_trial_accepted_as_perspective(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path"
        "?tier=trial&from=oss&to=enterprise"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "trial"


def test_http_scalar_identity_empty_path(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path"
        "?tier=cloud_pro&from=cloud_pro&to=cloud_pro"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["direction"] == "identity"
    assert body["path"] == []


def test_http_scalar_downgrade_direction(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path"
        "?tier=cloud_pro&from=enterprise&to=oss"
    )
    assert r.status_code == 200
    assert r.get_json()["direction"] == "downgrade"


def test_http_scalar_case_whitespace_normalised(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path"
        "?tier=%20Cloud_PRO%20&from=%20OSS%20&to=%20ENTERPRISE%20"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert body["to"] == "enterprise"


def test_http_scalar_path_parity_with_tier_spec_path(client):
    """``path`` in the ``_at_path`` envelope must byte-equal ``path`` in
    ``/tier-spec-path`` for the same ``(from, to)``."""
    r_at = client.get(
        "/api/entitlement/tier-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise"
    )
    r_base = client.get(
        "/api/entitlement/tier-spec-path?from=oss&to=enterprise"
    )
    assert r_at.get_json()["path"] == r_base.get_json()["path"]


def test_http_scalar_perspective_invariance(client):
    baseline = client.get(
        "/api/entitlement/tier-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise"
    ).get_json()["path"]
    for p in ALL_TIERS:
        got = client.get(
            f"/api/entitlement/tier-spec-at-path?tier={p}&from=oss&to=enterprise"
        ).get_json()["path"]
        assert got == baseline, p


# ── HTTP batch: /api/entitlement/tier-spec-at-path-batch ─────────────────────


def test_http_batch_envelope_shape(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=cloud_starter,cloud_pro,enterprise"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) == _BATCH_ENVELOPE_KEYS
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert [r["to"] for r in body["tiers"]] == [
        "cloud_starter",
        "cloud_pro",
        "enterprise",
    ]
    assert body["unknown"] == []


def test_http_batch_missing_tier(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?from=oss&to=enterprise"
    )
    assert r.status_code == 400


def test_http_batch_missing_from(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?tier=cloud_pro&to=enterprise"
    )
    assert r.status_code == 400


def test_http_batch_missing_to_400(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?tier=cloud_pro&from=oss"
    )
    assert r.status_code == 400


def test_http_batch_empty_to_400(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to="
    )
    assert r.status_code == 400


def test_http_batch_unknown_tier_404_which_tier(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?tier=bogus&from=oss&to=enterprise"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "tier"


def test_http_batch_unknown_from_404_which_from(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?tier=cloud_pro&from=bogus&to=enterprise"
    )
    assert r.status_code == 404
    assert r.get_json()["which"] == "from"


def test_http_batch_unknown_destination_bucketed_not_404(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=cloud_starter,no_such_tier,enterprise"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert [row["to"] for row in body["tiers"]] == [
        "cloud_starter",
        "enterprise",
    ]
    assert body["unknown"] == ["no_such_tier"]


def test_http_batch_tiers_parity_with_tier_spec_path_batch(client):
    """``tiers[]`` in the ``_at_path_batch`` envelope must byte-equal
    ``tiers[]`` in ``/tier-spec-path-batch`` for the same
    ``(from, to)``."""
    r_at = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=cloud_starter,enterprise"
    )
    r_base = client.get(
        "/api/entitlement/tier-spec-path-batch"
        "?from=oss&to=cloud_starter,enterprise"
    )
    assert r_at.get_json()["tiers"] == r_base.get_json()["tiers"]


def test_http_batch_perspective_invariance(client):
    baseline = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=cloud_starter,enterprise"
    ).get_json()["tiers"]
    for p in ALL_TIERS:
        got = client.get(
            f"/api/entitlement/tier-spec-at-path-batch?tier={p}&from=oss&to=cloud_starter,enterprise"
        ).get_json()["tiers"]
        assert got == baseline, p


def test_http_batch_trial_accepted_as_perspective(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?tier=trial&from=oss&to=cloud_starter,enterprise"
    )
    assert r.status_code == 200
    assert r.get_json()["perspective_tier"] == "trial"


def test_http_batch_case_whitespace_normalised(client):
    r = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?tier=%20Cloud_PRO%20&from=%20OSS%20"
        "&to=%20CLOUD_STARTER%20,%20enterprise%20"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["from"] == "oss"
    assert [r["to"] for r in body["tiers"]] == [
        "cloud_starter",
        "enterprise",
    ]


def test_http_batch_never_5xxs_on_resolver_crash(client, monkeypatch, ent):
    monkeypatch.setattr(
        ent,
        "tier_spec_at_path_batch",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    r = client.get(
        "/api/entitlement/tier-spec-at-path-batch"
        "?tier=cloud_pro&from=oss&to=cloud_starter,enterprise"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["tiers"] == []
    assert body["unknown"] == []
    assert body["grace"] is True


def test_http_scalar_never_5xxs_on_resolver_crash(client, monkeypatch, ent):
    monkeypatch.setattr(
        ent,
        "tier_spec_at_path",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    r = client.get(
        "/api/entitlement/tier-spec-at-path"
        "?tier=cloud_pro&from=oss&to=enterprise"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["path"] == []
    assert body["grace"] is True
