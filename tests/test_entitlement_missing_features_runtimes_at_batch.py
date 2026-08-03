"""Tests for the batch what-if ``missing_features_at_batch`` /
``missing_runtimes_at_batch`` complement scalars and their paired
``/api/entitlement/missing-features-at-batch`` /
``/api/entitlement/missing-runtimes-at-batch`` endpoints.

Batch what-if siblings of :func:`missing_features_at` /
:func:`missing_runtimes_at` in the same relationship
:func:`feature_catalog_at_batch` has to :func:`feature_catalog_at`:
fixes ONE bundle and sweeps across N perspective tiers, returning one
row per tier with the per-item denial list so a pricing-matrix column
("out of {fleet, sso}, which are still locked at OSS vs Cloud Starter
vs Cloud Pro vs Enterprise?") hydrates off ONE call.

This file pins:

1. Per-tier row parity with the scalar ``_at`` sibling on every
   ``_TIER_ORDER`` perspective.
2. Envelope shape stability ({tiers, unknown} scalar; fixed endpoint
   key set) across empty / all-unknown / partially-unknown input.
3. Tier normalisation (``_normalise_csv``) at scalar layer -- whitespace
   stripped, lowered, dedup preserving first-seen.
4. Unknown tier ids bucket into ``unknown[]`` / ``unknown_tiers`` (batch
   never short-circuits on a single bad id).
5. Empty / None / non-iterable ``perspective_tiers`` -> stable empty
   ``{tiers: [], unknown: []}`` envelope.
6. Grace-independence: batch answer identical under grace on vs off for
   every ``(tiers, bundle)`` pair.
7. Runtime scalar alias posture: no scalar-level canonicalisation --
   a raw ``"claude-code"`` surfaces in each row's ``missing`` verbatim
   (matches :func:`missing_runtimes_at`). Endpoint canonicalises
   upstream so ``?runtimes=claude-code`` collapses to ``claude_code``.
8. Never-raises on delegate blowup: log-and-return the empty-row shape
   for the affected tier; unknown_tiers surfaces its id.
9. Endpoint envelope shape (fixed key set) across every input branch;
   per-row ``any_missing`` / ``missing_count`` roll-ups and per-row
   ``upgrade_required`` computed against the ROW's tier rank.
10. Never-5xx: monkeypatch scalar / delegate blowup collapses to the
    OSS-free ``_missing_bundle_at_batch_fallback`` shape.
11. Scalar-vs-endpoint parity: URL ``tiers[i].missing`` byte-equals
    scalar ``tiers[i].missing`` on the same ``(tiers, bundle)`` input.
12. Cross-endpoint consistency vs sibling ``/missing-features-at`` /
    ``/missing-runtimes-at``: per-row ``missing`` equals the sibling
    ``/missing-<axis>-at?tier=<row.tier>&<axis>=<bundle>`` ``missing``.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode. The batch what-if
    scalars are grace-independent by construction (they delegate to the
    scalar ``_at`` sibling backed by :func:`_hypothetical_entitlement`).
    """
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    """Enforcement-on fixture -- pins the grace-independence contract.
    Same shape as the sibling `test_entitlement_missing_features_runtimes_at`
    module."""
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


# ── Envelope shape ────────────────────────────────────────────────────────


_ENVELOPE_KEYS_FEATURES = {
    "features",
    "unknown",
    "unknown_tiers",
    "kind",
    "count",
    "tiers",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}
_ENVELOPE_KEYS_RUNTIMES = {
    "runtimes",
    "unknown",
    "unknown_tiers",
    "kind",
    "count",
    "tiers",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}
_ROW_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "missing",
    "missing_count",
    "any_missing",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "upgrade_required",
}


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, url
    return resp.get_json()


def _paid_feature(ent) -> str:
    """Pick a stable paid feature id for perspective sweeps."""
    for f in sorted(ent.PAID_FEATURES):
        return f
    pytest.skip("no paid features on this build")


def _paid_runtime(ent) -> str:
    for rt in sorted(ent.PAID_RUNTIMES):
        return rt
    pytest.skip("no paid runtimes on this build")


# ── Scalar: envelope shape ─────────────────────────────────────────────────


def test_scalar_features_envelope_shape_stable(ent):
    r = ent.missing_features_at_batch(["oss", "cloud_pro"], ["fleet"])
    assert set(r) == {"tiers", "unknown"}
    for row in r["tiers"]:
        assert set(row) == {"tier", "tier_label", "tier_rank", "missing"}


def test_scalar_runtimes_envelope_shape_stable(ent):
    r = ent.missing_runtimes_at_batch(["oss"], ["openclaw"])
    assert set(r) == {"tiers", "unknown"}
    for row in r["tiers"]:
        assert set(row) == {"tier", "tier_label", "tier_rank", "missing"}


# ── Scalar: parity with _at sibling ───────────────────────────────────────


def test_scalar_features_row_missing_equals_at_scalar(ent):
    """Per-row ``missing`` byte-equals :func:`missing_features_at` for
    the same ``(tier, features)`` pair, across every ``_TIER_ORDER``
    perspective and a mixed known-plus-paid bundle."""
    paid = _paid_feature(ent)
    bundle = sorted(ent.FREE_FEATURES) + [paid, "bogus_id"]
    tiers = list(ent._TIER_ORDER)
    r = ent.missing_features_at_batch(tiers, bundle)
    for row in r["tiers"]:
        assert row["missing"] == ent.missing_features_at(row["tier"], bundle)


def test_scalar_runtimes_row_missing_equals_at_scalar(ent):
    paid = _paid_runtime(ent)
    bundle = ["openclaw", paid, "bogus_id"]
    tiers = list(ent._TIER_ORDER)
    r = ent.missing_runtimes_at_batch(tiers, bundle)
    for row in r["tiers"]:
        assert row["missing"] == ent.missing_runtimes_at(row["tier"], bundle)


def test_scalar_features_row_tier_label_and_rank_match_helpers(ent):
    r = ent.missing_features_at_batch(list(ent._TIER_ORDER), ["fleet"])
    for row in r["tiers"]:
        assert row["tier_label"] == ent.tier_label(row["tier"])
        assert row["tier_rank"] == ent._TIER_RANK.get(row["tier"], -1)


def test_scalar_runtimes_row_tier_label_and_rank_match_helpers(ent):
    r = ent.missing_runtimes_at_batch(list(ent._TIER_ORDER), ["openclaw"])
    for row in r["tiers"]:
        assert row["tier_label"] == ent.tier_label(row["tier"])
        assert row["tier_rank"] == ent._TIER_RANK.get(row["tier"], -1)


# ── Scalar: tier normalisation and dedup ──────────────────────────────────


def test_scalar_features_normalises_and_dedups_tiers(ent):
    r = ent.missing_features_at_batch(
        ["  OSS  ", "oss", "Cloud_Pro"], ["fleet"]
    )
    seen = [row["tier"] for row in r["tiers"]]
    assert seen == ["oss", "cloud_pro"]
    assert r["unknown"] == []


def test_scalar_runtimes_normalises_and_dedups_tiers(ent):
    r = ent.missing_runtimes_at_batch(
        ["  OSS  ", "oss", " Cloud_Pro "], ["openclaw"]
    )
    seen = [row["tier"] for row in r["tiers"]]
    assert seen == ["oss", "cloud_pro"]


def test_scalar_features_unknown_tiers_bucket_not_shortcircuit(ent):
    r = ent.missing_features_at_batch(
        ["oss", "bogus_a", "cloud_pro", "bogus_b"], ["fleet"]
    )
    assert [row["tier"] for row in r["tiers"]] == ["oss", "cloud_pro"]
    assert r["unknown"] == ["bogus_a", "bogus_b"]


def test_scalar_runtimes_unknown_tiers_bucket_not_shortcircuit(ent):
    r = ent.missing_runtimes_at_batch(
        ["bogus_x", "pro", "bogus_y"], ["openclaw"]
    )
    assert [row["tier"] for row in r["tiers"]] == ["pro"]
    assert r["unknown"] == ["bogus_x", "bogus_y"]


# ── Scalar: empty / None / non-iterable input ──────────────────────────────


def test_scalar_features_empty_tiers_returns_empty_envelope(ent):
    assert ent.missing_features_at_batch([], ["fleet"]) == {
        "tiers": [],
        "unknown": [],
    }


def test_scalar_features_none_tiers_returns_empty_envelope(ent):
    assert ent.missing_features_at_batch(None, ["fleet"]) == {
        "tiers": [],
        "unknown": [],
    }


def test_scalar_features_non_iterable_tiers_returns_empty_envelope(ent):
    assert ent.missing_features_at_batch(123, ["fleet"]) == {  # type: ignore[arg-type]
        "tiers": [],
        "unknown": [],
    }


def test_scalar_features_empty_bundle_still_walks_tiers(ent):
    """Empty bundle: every valid tier still emits a row with missing=[]
    (parity with :func:`missing_features_at` on empty bundle)."""
    r = ent.missing_features_at_batch(["oss", "cloud_pro"], [])
    assert [row["tier"] for row in r["tiers"]] == ["oss", "cloud_pro"]
    assert all(row["missing"] == [] for row in r["tiers"])


def test_scalar_features_none_bundle_still_walks_tiers(ent):
    r = ent.missing_features_at_batch(["oss"], None)
    assert len(r["tiers"]) == 1
    assert r["tiers"][0]["missing"] == []


def test_scalar_runtimes_empty_bundle_still_walks_tiers(ent):
    r = ent.missing_runtimes_at_batch(["oss", "pro"], [])
    assert [row["tier"] for row in r["tiers"]] == ["oss", "pro"]
    assert all(row["missing"] == [] for row in r["tiers"])


# ── Scalar: all-tier sweep, free vs paid semantics ─────────────────────────


def test_scalar_features_all_free_bundle_empty_at_every_tier(ent):
    free = sorted(ent.FREE_FEATURES)
    r = ent.missing_features_at_batch(list(ent._TIER_ORDER), free)
    for row in r["tiers"]:
        assert row["missing"] == [], row["tier"]


def test_scalar_features_paid_bundle_at_oss_denies_every_id(ent):
    paid = sorted(ent.PAID_FEATURES)
    r = ent.missing_features_at_batch(["oss"], paid)
    assert set(r["tiers"][0]["missing"]) == set(paid)


def test_scalar_features_paid_bundle_at_enterprise_grants_all(ent):
    if "enterprise" not in ent._TIER_ORDER:
        pytest.skip("enterprise not on this build")
    paid = sorted(ent.PAID_FEATURES)
    r = ent.missing_features_at_batch(["enterprise"], paid)
    assert r["tiers"][0]["missing"] == []


def test_scalar_runtimes_all_free_bundle_empty_at_every_tier(ent):
    free = sorted(ent.FREE_RUNTIMES)
    r = ent.missing_runtimes_at_batch(list(ent._TIER_ORDER), free)
    for row in r["tiers"]:
        assert row["missing"] == [], row["tier"]


def test_scalar_runtimes_paid_bundle_at_oss_denies_every_id(ent):
    paid = sorted(ent.PAID_RUNTIMES)
    r = ent.missing_runtimes_at_batch(["oss"], paid)
    assert set(r["tiers"][0]["missing"]) == set(paid)


# ── Scalar: grace-independence ────────────────────────────────────────────


def test_scalar_features_grace_independence_all_tiers(ent, enforced):
    """The batch scalar delegates to :func:`missing_features_at` which is
    backed by :func:`_hypothetical_entitlement` (grace off) -- the answer
    is identical under grace vs enforce for the same input."""
    paid = sorted(ent.PAID_FEATURES)
    for tier in ent._TIER_ORDER:
        grace = ent.missing_features_at_batch([tier], paid)
        enf = enforced.missing_features_at_batch([tier], paid)
        assert grace == enf, tier


def test_scalar_runtimes_grace_independence_all_tiers(ent, enforced):
    paid = sorted(ent.PAID_RUNTIMES)
    for tier in ent._TIER_ORDER:
        assert ent.missing_runtimes_at_batch(
            [tier], paid
        ) == enforced.missing_runtimes_at_batch([tier], paid), tier


# ── Scalar: strict runtime alias posture ──────────────────────────────────


def test_scalar_runtimes_no_alias_canonicalisation_at_scalar_layer(ent):
    """A raw ``"claude-code"`` at the scalar layer surfaces in each
    row's ``missing`` verbatim (matches :func:`missing_runtimes_at`
    alias posture -- endpoint layer canonicalises)."""
    tier = "pro" if "pro" in ent._TIER_ORDER else "cloud_pro"
    r = ent.missing_runtimes_at_batch([tier], ["claude-code"])
    # Even though claude-code IS granted at Pro, the strict scalar sees
    # the alias as an unknown id and surfaces it in ``missing``.
    assert r["tiers"][0]["missing"] == ["claude-code"]


# ── Scalar: never raises on delegate blowup ────────────────────────────────


def test_scalar_features_row_delegate_blowup_buckets_tier_into_unknown(
    ent, monkeypatch
):
    """A per-tier delegate crash short-circuits that id into ``unknown[]``
    and the rest of the batch keeps building -- matches
    :func:`feature_catalog_at_batch` posture."""
    orig = ent.missing_features_at

    def boom(tier, features):
        if tier == "cloud_pro":
            raise RuntimeError("boom")
        return orig(tier, features)

    monkeypatch.setattr(ent, "missing_features_at", boom)
    r = ent.missing_features_at_batch(
        ["oss", "cloud_pro", "enterprise"], ["fleet"]
    )
    assert [row["tier"] for row in r["tiers"]] == ["oss", "enterprise"]
    assert "cloud_pro" in r["unknown"]


def test_scalar_runtimes_row_delegate_blowup_buckets_tier_into_unknown(
    ent, monkeypatch
):
    orig = ent.missing_runtimes_at

    def boom(tier, runtimes):
        if tier == "pro":
            raise RuntimeError("boom")
        return orig(tier, runtimes)

    monkeypatch.setattr(ent, "missing_runtimes_at", boom)
    r = ent.missing_runtimes_at_batch(["oss", "pro", "enterprise"], ["openclaw"])
    assert [row["tier"] for row in r["tiers"]] == ["oss", "enterprise"]
    assert "pro" in r["unknown"]


# ── Endpoint: happy-path envelope shape ───────────────────────────────────


def test_endpoint_features_envelope_key_set(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-batch"
        "?tiers=oss,cloud_pro&features=fleet,sso",
    )
    assert set(body) == _ENVELOPE_KEYS_FEATURES
    for row in body["tiers"]:
        assert set(row) == _ROW_KEYS


def test_endpoint_runtimes_envelope_key_set(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-batch"
        "?tiers=oss,pro&runtimes=openclaw,claude_code",
    )
    assert set(body) == _ENVELOPE_KEYS_RUNTIMES
    for row in body["tiers"]:
        assert set(row) == _ROW_KEYS


# ── Endpoint: never 4xxs ──────────────────────────────────────────────────


def test_endpoint_features_missing_tiers_returns_200(client):
    resp = client.get("/api/entitlement/missing-features-at-batch?features=fleet")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["unknown_tiers"] == []


def test_endpoint_features_missing_features_returns_200(client):
    resp = client.get("/api/entitlement/missing-features-at-batch?tiers=oss")
    assert resp.status_code == 200
    body = resp.get_json()
    # empty bundle: tier row emitted with missing=[]
    assert len(body["tiers"]) == 1
    assert body["tiers"][0]["missing"] == []


def test_endpoint_features_all_unknown_tiers_returns_200_with_empty_tiers(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-batch"
        "?tiers=bogus_a,bogus_b&features=fleet",
    )
    assert body["tiers"] == []
    assert body["unknown_tiers"] == ["bogus_a", "bogus_b"]


def test_endpoint_runtimes_missing_tiers_returns_200(client):
    resp = client.get(
        "/api/entitlement/missing-runtimes-at-batch?runtimes=openclaw"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []


def test_endpoint_runtimes_all_unknown_tiers_returns_200_with_empty_tiers(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-batch"
        "?tiers=bogus&runtimes=openclaw",
    )
    assert body["tiers"] == []
    assert body["unknown_tiers"] == ["bogus"]


# ── Endpoint: per-row rollups ─────────────────────────────────────────────


def test_endpoint_features_row_missing_count_matches_missing_len(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-batch"
        "?tiers=oss,cloud_pro&features=fleet,sso",
    )
    for row in body["tiers"]:
        assert row["missing_count"] == len(row["missing"])


def test_endpoint_features_row_any_missing_folds_missing_and_unknown(client, ent):
    """``any_missing`` is per-row and rolls up (row.missing != []) OR
    (top-level unknown != []) so an unknown feature token surfaces even
    on a tier that would otherwise grant everything."""
    if "enterprise" not in ent._TIER_ORDER:
        pytest.skip("enterprise not on this build")
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-batch"
        "?tiers=enterprise&features=fleet,bogus_id",
    )
    # unknown bucket has bogus_id -> any_missing True even at enterprise
    assert body["unknown"] == ["bogus_id"]
    row = body["tiers"][0]
    assert row["any_missing"] is True


def test_endpoint_features_row_upgrade_required_uses_row_rank(client, ent):
    """Per-row ``upgrade_required`` compares ``required_tier`` rank
    against the ROW's tier rank (not the live current rank), so a
    tier that already grants the whole bundle reads False."""
    paid = sorted(ent.PAID_FEATURES)
    bundle_csv = ",".join(paid[:2])
    tiers_csv = ",".join(list(ent._TIER_ORDER))
    body = _get_json(
        client,
        f"/api/entitlement/missing-features-at-batch"
        f"?tiers={tiers_csv}&features={bundle_csv}",
    )
    for row in body["tiers"]:
        req_rank = row["required_tier_rank"]
        row_rank = row["tier_rank"]
        if row["required_tier"] is None:
            assert row["upgrade_required"] is False
        else:
            assert row["upgrade_required"] == (req_rank > row_rank)


# ── Endpoint: known / unknown feature split ────────────────────────────────


def test_endpoint_features_known_unknown_split(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-batch"
        "?tiers=oss&features=fleet,sso,bogus_id",
    )
    assert body["features"] == ["fleet", "sso"]
    assert body["unknown"] == ["bogus_id"]
    assert body["count"] == 2


def test_endpoint_runtimes_known_unknown_split(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-batch"
        "?tiers=oss&runtimes=openclaw,claude_code,bogus_id",
    )
    assert body["runtimes"] == ["openclaw", "claude_code"]
    assert body["unknown"] == ["bogus_id"]
    assert body["count"] == 2


# ── Endpoint: runtime alias canonicalisation upstream of scalar ───────────


def test_endpoint_runtimes_endpoint_canonicalises_alias(client, ent):
    """``?runtimes=claude-code`` canonicalises to ``claude_code`` upstream
    of the strict batch scalar so it lands in the known list (not
    ``unknown``) and each row's ``missing`` reflects the granted status
    of the canonical id -- matches sibling ``/missing-runtimes-at``."""
    if "claude_code" not in ent.ALL_RUNTIMES:
        pytest.skip("claude_code not in ALL_RUNTIMES on this build")
    tier = "pro" if "pro" in ent._TIER_ORDER else "cloud_pro"
    body = _get_json(
        client,
        f"/api/entitlement/missing-runtimes-at-batch"
        f"?tiers={tier}&runtimes=claude-code",
    )
    # canonicalised to claude_code, listed as known
    assert body["runtimes"] == ["claude_code"]
    assert body["unknown"] == []
    row = body["tiers"][0]
    # Pro grants claude_code -> missing empty
    assert row["missing"] == []


def test_endpoint_runtimes_alias_and_canonical_dedup_to_one_row(client, ent):
    if "claude_code" not in ent.ALL_RUNTIMES:
        pytest.skip("claude_code not in ALL_RUNTIMES on this build")
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-batch"
        "?tiers=oss&runtimes=claude-code,claude_code",
    )
    assert body["runtimes"] == ["claude_code"]
    assert body["tiers"][0]["missing"] == ["claude_code"]


# ── Endpoint: scalar-vs-endpoint parity ────────────────────────────────────


def test_endpoint_features_row_missing_equals_scalar_missing(client, ent):
    """Per-row ``missing`` byte-equals the scalar
    :func:`missing_features_at_batch` for the same (tiers, features)."""
    paid = _paid_feature(ent)
    bundle = sorted(ent.FREE_FEATURES) + [paid, "bogus_id"]
    tiers = list(ent._TIER_ORDER)
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-batch"
        f"?tiers={','.join(tiers)}&features={','.join(bundle)}",
    )
    scalar = ent.missing_features_at_batch(tiers, bundle)
    endpoint_by_tier = {row["tier"]: row["missing"] for row in body["tiers"]}
    scalar_by_tier = {row["tier"]: row["missing"] for row in scalar["tiers"]}
    assert endpoint_by_tier == scalar_by_tier


def test_endpoint_runtimes_row_missing_equals_scalar_missing_canon_input(
    client, ent
):
    """Endpoint canonicalises aliases upstream; the equivalent scalar
    call must be given the canonical bundle for byte-identical parity."""
    paid = _paid_runtime(ent)
    bundle = ["openclaw", paid, "bogus_id"]
    tiers = list(ent._TIER_ORDER)
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-batch"
        f"?tiers={','.join(tiers)}&runtimes={','.join(bundle)}",
    )
    scalar = ent.missing_runtimes_at_batch(tiers, bundle)
    endpoint_by_tier = {row["tier"]: row["missing"] for row in body["tiers"]}
    scalar_by_tier = {row["tier"]: row["missing"] for row in scalar["tiers"]}
    assert endpoint_by_tier == scalar_by_tier


# ── Endpoint: cross-consistency with sibling _at endpoint ─────────────────


def test_endpoint_features_row_missing_equals_sibling_at_endpoint(client, ent):
    """Per-row ``missing`` on the batch endpoint byte-equals the
    ``/missing-features-at?tier=<row.tier>&features=<bundle>`` sibling
    ``missing`` on the same input -- pins the two endpoints as the same
    fold read at two granularities."""
    paid = _paid_feature(ent)
    bundle = sorted(ent.FREE_FEATURES) + [paid, "bogus_id"]
    bundle_csv = ",".join(bundle)
    tiers = list(ent._TIER_ORDER)
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-batch"
        f"?tiers={','.join(tiers)}&features={bundle_csv}",
    )
    for row in body["tiers"]:
        sib = _get_json(
            client,
            "/api/entitlement/missing-features-at"
            f"?tier={row['tier']}&features={bundle_csv}",
        )
        assert row["missing"] == sib["missing"], row["tier"]


def test_endpoint_runtimes_row_missing_equals_sibling_at_endpoint(client, ent):
    paid = _paid_runtime(ent)
    bundle = ["openclaw", paid, "bogus_id"]
    bundle_csv = ",".join(bundle)
    tiers = list(ent._TIER_ORDER)
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-batch"
        f"?tiers={','.join(tiers)}&runtimes={bundle_csv}",
    )
    for row in body["tiers"]:
        sib = _get_json(
            client,
            "/api/entitlement/missing-runtimes-at"
            f"?tier={row['tier']}&runtimes={bundle_csv}",
        )
        assert row["missing"] == sib["missing"], row["tier"]


# ── Endpoint: never 5xx on scalar / delegate blowup ───────────────────────


def test_endpoint_features_never_5xx_on_scalar_blowup(client, ent, monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "missing_features_at_batch", boom)
    resp = client.get(
        "/api/entitlement/missing-features-at-batch?tiers=oss&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    # fallback shape: tiers empty, tokens echoed, grace envelope
    assert body["tiers"] == []
    assert body["features"] == []
    assert body["unknown"] == ["fleet"]
    assert body["unknown_tiers"] == ["oss"]
    assert body["current_tier"] == "oss"


def test_endpoint_runtimes_never_5xx_on_scalar_blowup(client, ent, monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "missing_runtimes_at_batch", boom)
    resp = client.get(
        "/api/entitlement/missing-runtimes-at-batch?tiers=oss&runtimes=openclaw"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []
    assert body["runtimes"] == []
    assert body["unknown_tiers"] == ["oss"]


def test_endpoint_features_never_5xx_on_resolver_blowup(client, ent, monkeypatch):
    """A resolver crash inside :func:`_resolver_envelope` still returns 200
    with the fallback envelope."""
    def boom():
        raise RuntimeError("resolver down")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    resp = client.get(
        "/api/entitlement/missing-features-at-batch?tiers=oss&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) == _ENVELOPE_KEYS_FEATURES
    assert body["tiers"] == []


# ── Envelope kind and count sanity ────────────────────────────────────────


def test_endpoint_features_kind_and_count(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-batch"
        "?tiers=oss&features=fleet,sso",
    )
    assert body["kind"] == "features"
    assert body["count"] == 2


def test_endpoint_runtimes_kind_and_count(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-batch"
        "?tiers=oss&runtimes=openclaw,claude_code",
    )
    assert body["kind"] == "runtimes"
    assert body["count"] == 2


def test_endpoint_features_current_tier_echoes_resolver(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-batch?tiers=oss&features=fleet",
    )
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["grace"] == bool(live.grace)


# ── Preserved order + dedup at endpoint layer ─────────────────────────────


def test_endpoint_features_dedup_preserves_first_seen_order(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-features-at-batch"
        "?tiers=cloud_pro,oss,cloud_pro&features=fleet,sso,fleet",
    )
    assert [row["tier"] for row in body["tiers"]] == ["cloud_pro", "oss"]
    assert body["features"] == ["fleet", "sso"]


def test_endpoint_runtimes_dedup_preserves_first_seen_order(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-batch"
        "?tiers=pro,oss,pro&runtimes=openclaw,openclaw",
    )
    assert [row["tier"] for row in body["tiers"]] == ["pro", "oss"]
    assert body["runtimes"] == ["openclaw"]
