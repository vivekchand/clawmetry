"""Tests for ``next_tier_feature_spec_at_batch`` /
``previous_tier_feature_spec_at_batch`` /
``next_tier_runtime_spec_at_batch`` /
``previous_tier_runtime_spec_at_batch`` and the four companion
``/api/entitlement/{next,previous}-tier-{feature,runtime}-spec-at-batch``
endpoints.

Batch siblings of the scalar
``{next,previous}_tier_{feature,runtime}_spec_at`` what-ifs.  Where each
scalar what-if projects the rung above / below the source onto ONE
feature / runtime id, the batch siblings project onto N ids in ONE
round-trip -- the feature / runtime axis analogue of
``{next,previous}_tier_spec_at_batch`` (which walks the full spec-row
descriptor at every purchasable source).

Pins covered here:

* each row in ``features[]`` / ``runtimes[]`` byte-equals the scalar
  ``feature_spec_at`` / ``runtime_spec_at`` row for the resolved
  ``target = _{next,previous}_purchasable_tier_after/before(tier)`` --
  the batch-vs-scalar parity that stops the batch what-if drifting from
  the scalar what-if
* each row byte-equals the row from
  ``feature_spec_at_batch(target, [id])`` /
  ``runtime_spec_at_batch(target, [id])`` for the same target -- pin
  against the perspective-tier batch helper
* the batch also byte-equals ``next_tier_feature_spec_at(tier, id)`` /
  ``next_tier_runtime_spec_at(tier, id)`` per row -- so the scalar
  ``next`` / ``previous`` what-if projections and the batch ``next`` /
  ``previous`` what-if projections cannot drift
* ``target`` echoes the resolved rung above / below the source; at the
  source-side ceiling / floor ``target`` collapses to ``None`` and
  ``features[]`` / ``runtimes[]`` is empty (surface stays populated
  instead of being dropped)
* supplied ids are normalised via ``_normalise_csv`` (trim / lowercase /
  duplicate drop / first-seen order); unknown ids echo into
  ``unknown[]`` instead of short-circuiting
* runtime aliases canonicalise (``claude-code`` -> ``claude_code``) and
  collapse against already-supplied canonical ids without emitting two
  rows
* unknown / blank ``tier`` returns ``None`` (helper) / 400 / 404 (HTTP)
* the helpers never raise: a top-level failure short-circuits to
  ``{"target": None, "features": [], "unknown": []}``
* grace vs enforce yields identical rows (the batch is catalogue-derived
  through the scalar sibling, not the gated resolver)
* the four HTTP endpoints 400 on missing / empty input, 404 on unknown
  tier, and never 5xx on a resolver crash
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_FEATURE_ROW_KEYS = {
    "id",
    "label",
    "tier",
    "tiers",
    "free",
    "allowed",
    "locked",
    "entitled",
    "alias",
}

_RUNTIME_ROW_KEYS = {
    "id",
    "label",
    "free",
    "tier",
    "tiers",
    "allowed",
    "locked",
    "entitled",
}

_ENVELOPE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "features",
    "unknown",
}

_RUNTIME_ENVELOPE_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "runtimes",
    "unknown",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode); the batch is catalogue-
    derived through the scalar sibling, so the fixture only needs to
    keep the live resolver from surprising the test."""
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


# ── next_tier_feature_spec_at_batch: tier + input handling ───────────────────


def test_next_feat_batch_unknown_tier_returns_none(ent):
    assert ent.next_tier_feature_spec_at_batch("bogus", ["sessions"]) is None


def test_next_feat_batch_blank_tier_returns_none(ent):
    assert ent.next_tier_feature_spec_at_batch("", ["sessions"]) is None
    assert ent.next_tier_feature_spec_at_batch("  ", ["sessions"]) is None


def test_next_feat_batch_none_tier_returns_none(ent):
    assert ent.next_tier_feature_spec_at_batch(None, ["sessions"]) is None


def test_next_feat_batch_int_tier_returns_none(ent):
    assert ent.next_tier_feature_spec_at_batch(42, ["sessions"]) is None


def test_next_feat_batch_trims_and_lowercases_tier(ent):
    # `_at` posture: any tier id in ``_TIER_ORDER`` accepted, including
    # trial.  Whitespace + case handled leniently.
    same = ent.next_tier_feature_spec_at_batch(
        "  OSS  ", list(ent.FREE_FEATURES)[:1]
    )
    canon = ent.next_tier_feature_spec_at_batch(
        ent.TIER_OSS, list(ent.FREE_FEATURES)[:1]
    )
    assert same == canon


# ── next_tier_feature_spec_at_batch: envelope shape + parity ─────────────────


def test_next_feat_batch_envelope_shape_from_oss(ent):
    body = ent.next_tier_feature_spec_at_batch(
        ent.TIER_OSS, list(ent.FREE_FEATURES)[:1]
    )
    assert body is not None
    assert set(body.keys()) == {"target", "features", "unknown"}
    assert body["target"] == ent._next_purchasable_tier_after(ent.TIER_OSS)


def test_next_feat_batch_row_shape_matches_feature_spec_at(ent):
    fid = next(iter(ent.FREE_FEATURES))
    body = ent.next_tier_feature_spec_at_batch(ent.TIER_OSS, [fid])
    assert body["features"], "expected at least one row above OSS"
    for row in body["features"]:
        assert set(row.keys()) == _FEATURE_ROW_KEYS


def test_next_feat_batch_parity_with_scalar_next_tier_feature_spec_at(ent):
    """Pin batch-vs-scalar no-drift on the ``next`` axis: every batch
    row equals ``next_tier_feature_spec_at(tier, id)`` for the same
    (source, feature) pair.
    """
    ids = sorted(ent.ALL_FEATURES)
    body = ent.next_tier_feature_spec_at_batch(ent.TIER_OSS, ids)
    rows_by_id = {row["id"]: row for row in body["features"]}
    for fid in ids:
        scalar = ent.next_tier_feature_spec_at(ent.TIER_OSS, fid)
        if scalar is None:
            continue
        assert rows_by_id.get(fid) == scalar, fid


def test_next_feat_batch_parity_with_feature_spec_at_batch_on_target(ent):
    """Pin the batch what-if against the perspective-tier batch: the
    rows must match ``feature_spec_at_batch(target, ids)`` for the
    resolved ``target = _next_purchasable_tier_after(tier)``.
    """
    ids = sorted(ent.ALL_FEATURES)
    body = ent.next_tier_feature_spec_at_batch(ent.TIER_OSS, ids)
    target = ent._next_purchasable_tier_after(ent.TIER_OSS)
    reference = ent.feature_spec_at_batch(target, ids)
    assert body["features"] == reference["features"]
    assert body["unknown"] == reference["unknown"]


def test_next_feat_batch_normalises_ids(ent):
    fid = next(iter(ent.FREE_FEATURES))
    body = ent.next_tier_feature_spec_at_batch(
        ent.TIER_OSS, [f"  {fid.upper()}  ", fid, fid]
    )
    # duplicates dropped, first-seen order preserved -> one row.
    assert len(body["features"]) == 1
    assert body["features"][0]["id"] == fid


def test_next_feat_batch_unknown_ids_echo_into_unknown(ent):
    fid = next(iter(ent.FREE_FEATURES))
    body = ent.next_tier_feature_spec_at_batch(
        ent.TIER_OSS, [fid, "totally_bogus_feature"]
    )
    assert "totally_bogus_feature" in body["unknown"]
    assert any(row["id"] == fid for row in body["features"])


def test_next_feat_batch_ceiling_collapses(ent):
    # Enterprise as source -> no rung strictly above.  target=None,
    # features=[] -- the envelope stays populated so callers can
    # render "you're at the top" without a status-code branch.
    body = ent.next_tier_feature_spec_at_batch(
        ent.TIER_ENTERPRISE, list(ent.FREE_FEATURES)[:1]
    )
    assert body == {"target": None, "features": [], "unknown": []}


def test_next_feat_batch_ceiling_still_reports_unknown_ids(ent):
    # Ceiling branch reports genuine unknown ids so a partially-bad
    # caller can still learn what would have been dropped one rung
    # earlier -- helps a UI debug the caller-supplied list even at the
    # top of the ladder.
    body = ent.next_tier_feature_spec_at_batch(
        ent.TIER_ENTERPRISE, ["totally_bogus_feature"]
    )
    assert body["target"] is None
    assert body["features"] == []
    assert "totally_bogus_feature" in body["unknown"]


def test_next_feat_batch_grace_matches_enforce(ent, monkeypatch):
    ids = sorted(ent.ALL_FEATURES)
    grace = ent.next_tier_feature_spec_at_batch(ent.TIER_OSS, ids)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    enforce = ent.next_tier_feature_spec_at_batch(ent.TIER_OSS, ids)
    assert enforce == grace


def test_next_feat_batch_swallows_resolver_exception(ent, monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "_next_purchasable_tier_after", boom)
    body = ent.next_tier_feature_spec_at_batch(
        ent.TIER_OSS, ["totally_bogus"]
    )
    # Resolver crash collapses to the "target=None" branch, envelope
    # keeps rendering, unknown ids still surface.
    assert body["target"] is None
    assert body["features"] == []
    assert "totally_bogus" in body["unknown"]


# ── previous_tier_feature_spec_at_batch ──────────────────────────────────────


def test_prev_feat_batch_floor_collapses(ent):
    body = ent.previous_tier_feature_spec_at_batch(
        ent.TIER_OSS, list(ent.FREE_FEATURES)[:1]
    )
    assert body == {"target": None, "features": [], "unknown": []}


def test_prev_feat_batch_parity_with_scalar(ent):
    ids = sorted(ent.ALL_FEATURES)
    body = ent.previous_tier_feature_spec_at_batch(ent.TIER_ENTERPRISE, ids)
    rows_by_id = {row["id"]: row for row in body["features"]}
    for fid in ids:
        scalar = ent.previous_tier_feature_spec_at(ent.TIER_ENTERPRISE, fid)
        if scalar is None:
            continue
        assert rows_by_id.get(fid) == scalar, fid


def test_prev_feat_batch_parity_with_feature_spec_at_batch_on_target(ent):
    ids = sorted(ent.ALL_FEATURES)
    body = ent.previous_tier_feature_spec_at_batch(ent.TIER_ENTERPRISE, ids)
    target = ent._previous_purchasable_tier_before(ent.TIER_ENTERPRISE)
    reference = ent.feature_spec_at_batch(target, ids)
    assert body["features"] == reference["features"]
    assert body["unknown"] == reference["unknown"]


# ── next_tier_runtime_spec_at_batch ──────────────────────────────────────────


def test_next_rt_batch_unknown_tier_returns_none(ent):
    assert ent.next_tier_runtime_spec_at_batch("bogus", ["openclaw"]) is None


def test_next_rt_batch_row_shape_matches_runtime_spec_at(ent):
    body = ent.next_tier_runtime_spec_at_batch(ent.TIER_OSS, ["openclaw"])
    assert body["runtimes"], "expected at least one row above OSS"
    for row in body["runtimes"]:
        assert set(row.keys()) == _RUNTIME_ROW_KEYS


def test_next_rt_batch_parity_with_scalar_next_tier_runtime_spec_at(ent):
    rts = sorted(ent.ALL_RUNTIMES)
    body = ent.next_tier_runtime_spec_at_batch(ent.TIER_OSS, rts)
    rows_by_id = {row["id"]: row for row in body["runtimes"]}
    for rt in rts:
        scalar = ent.next_tier_runtime_spec_at(ent.TIER_OSS, rt)
        if scalar is None:
            continue
        assert rows_by_id.get(rt) == scalar, rt


def test_next_rt_batch_parity_with_runtime_spec_at_batch_on_target(ent):
    rts = sorted(ent.ALL_RUNTIMES)
    body = ent.next_tier_runtime_spec_at_batch(ent.TIER_OSS, rts)
    target = ent._next_purchasable_tier_after(ent.TIER_OSS)
    reference = ent.runtime_spec_at_batch(target, rts)
    assert body["runtimes"] == reference["runtimes"]
    assert body["unknown"] == reference["unknown"]


def test_next_rt_batch_aliases_canonicalise_and_dedupe(ent):
    # ``claude-code`` (alias) + ``claude_code`` (canonical) collapse to
    # one row on the canonical id.
    rt_paid = next(iter(ent.PAID_RUNTIMES))  # e.g. "claude_code"
    aliased = rt_paid.replace("_", "-")
    body = ent.next_tier_runtime_spec_at_batch(
        ent.TIER_OSS, [aliased, rt_paid]
    )
    matching = [row for row in body["runtimes"] if row["id"] == rt_paid]
    assert len(matching) == 1


def test_next_rt_batch_ceiling_collapses(ent):
    body = ent.next_tier_runtime_spec_at_batch(
        ent.TIER_ENTERPRISE, ["openclaw"]
    )
    assert body == {"target": None, "runtimes": [], "unknown": []}


def test_next_rt_batch_unknown_alias_echoes_into_unknown_at_ceiling(ent):
    body = ent.next_tier_runtime_spec_at_batch(
        ent.TIER_ENTERPRISE, ["totally-bogus-runtime"]
    )
    assert body["target"] is None
    assert body["runtimes"] == []
    assert "totally-bogus-runtime" in body["unknown"]


# ── previous_tier_runtime_spec_at_batch ──────────────────────────────────────


def test_prev_rt_batch_floor_collapses(ent):
    body = ent.previous_tier_runtime_spec_at_batch(
        ent.TIER_OSS, ["openclaw"]
    )
    assert body == {"target": None, "runtimes": [], "unknown": []}


def test_prev_rt_batch_parity_with_scalar(ent):
    rts = sorted(ent.ALL_RUNTIMES)
    body = ent.previous_tier_runtime_spec_at_batch(ent.TIER_ENTERPRISE, rts)
    rows_by_id = {row["id"]: row for row in body["runtimes"]}
    for rt in rts:
        scalar = ent.previous_tier_runtime_spec_at(ent.TIER_ENTERPRISE, rt)
        if scalar is None:
            continue
        assert rows_by_id.get(rt) == scalar, rt


# ── HTTP: next-tier-feature-spec-at-batch ────────────────────────────────────


def test_http_next_feat_batch_missing_tier_400(client):
    resp = client.get("/api/entitlement/next-tier-feature-spec-at-batch")
    assert resp.status_code == 400


def test_http_next_feat_batch_blank_tier_400(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at-batch?tier=%20"
    )
    assert resp.status_code == 400


def test_http_next_feat_batch_missing_features_400(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at-batch?tier=oss"
    )
    assert resp.status_code == 400


def test_http_next_feat_batch_unknown_tier_404(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at-batch"
        "?tier=bogus&features=sessions"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["which"] == "tier"


def test_http_next_feat_batch_envelope_shape(ent, client):
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/next-tier-feature-spec-at-batch"
        f"?tier=oss&features={fid}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] == ent._next_purchasable_tier_after(ent.TIER_OSS)


def test_http_next_feat_batch_ceiling_200_with_null_target(client):
    resp = client.get(
        "/api/entitlement/next-tier-feature-spec-at-batch"
        "?tier=enterprise&features=sessions"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["features"] == []


def test_http_next_feat_batch_never_5xxs_on_helper_exception(
    ent, client, monkeypatch
):
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "next_tier_feature_spec_at_batch", boom)
    fid = next(iter(ent.FREE_FEATURES))
    resp = client.get(
        f"/api/entitlement/next-tier-feature-spec-at-batch"
        f"?tier=oss&features={fid}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["features"] == []
    assert body["unknown"] == []


# ── HTTP: previous-tier-feature-spec-at-batch ────────────────────────────────


def test_http_prev_feat_batch_missing_features_400(client):
    resp = client.get(
        "/api/entitlement/previous-tier-feature-spec-at-batch?tier=enterprise"
    )
    assert resp.status_code == 400


def test_http_prev_feat_batch_unknown_tier_404(client):
    resp = client.get(
        "/api/entitlement/previous-tier-feature-spec-at-batch"
        "?tier=bogus&features=sessions"
    )
    assert resp.status_code == 404


def test_http_prev_feat_batch_floor_200_with_null_target(client):
    resp = client.get(
        "/api/entitlement/previous-tier-feature-spec-at-batch"
        "?tier=oss&features=sessions"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert body["features"] == []


# ── HTTP: next-tier-runtime-spec-at-batch ────────────────────────────────────


def test_http_next_rt_batch_missing_runtimes_400(client):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-spec-at-batch?tier=oss"
    )
    assert resp.status_code == 400


def test_http_next_rt_batch_unknown_tier_404(client):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-spec-at-batch"
        "?tier=bogus&runtimes=openclaw"
    )
    assert resp.status_code == 404


def test_http_next_rt_batch_envelope_shape(ent, client):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-spec-at-batch"
        "?tier=oss&runtimes=openclaw"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body.keys()) == _RUNTIME_ENVELOPE_KEYS
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] == ent._next_purchasable_tier_after(ent.TIER_OSS)


def test_http_next_rt_batch_ceiling_200_with_null_target(client):
    resp = client.get(
        "/api/entitlement/next-tier-runtime-spec-at-batch"
        "?tier=enterprise&runtimes=openclaw"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert body["runtimes"] == []


# ── HTTP: previous-tier-runtime-spec-at-batch ────────────────────────────────


def test_http_prev_rt_batch_floor_200_with_null_target(client):
    resp = client.get(
        "/api/entitlement/previous-tier-runtime-spec-at-batch"
        "?tier=oss&runtimes=openclaw"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["target"] is None
    assert body["runtimes"] == []


def test_http_prev_rt_batch_unknown_tier_404(client):
    resp = client.get(
        "/api/entitlement/previous-tier-runtime-spec-at-batch"
        "?tier=bogus&runtimes=openclaw"
    )
    assert resp.status_code == 404
