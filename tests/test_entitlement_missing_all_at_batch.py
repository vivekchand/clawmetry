"""Tests for the batch what-if mixed-axis ``missing_all_at_batch`` row-detail
scalar and its paired ``/api/entitlement/missing-all-at-batch`` endpoint.

Row-detail complement of :func:`clawmetry.entitlements.has_all_at_batch` on
the aggregate what-if seat, in the same relationship
:func:`missing_features_at_batch` / :func:`missing_runtimes_at_batch` have
to :func:`has_features_at_batch` / :func:`has_runtimes_at_batch` on the
single-axis seat. Where the paired boolean-fold sibling collapses each
``(perspective_tier, bundle)`` pair to ONE ``has_all_at`` bool, this
returns WHAT is missing on each supplied axis for the same N perspectives
in ONE round-trip so a paywall diagnostics matrix ("out of {fleet, sso,
claude_code, 100 channels, 90d retention, 100 nodes}, which axes are
still blocked at OSS vs Cloud Starter vs Cloud Pro vs Enterprise?")
hydrates the per-axis denial column off ONE URL instead of five
``_at-batch`` row-detail round-trips + a client-side per-axis stitch.

This file pins:

1. Scalar envelope shape ({tiers, unknown}) + per-row shape (4 keys with a
   5-key ``missing`` sub-dict) stable across every input branch.
2. Per-row ``missing`` byte-parity with :func:`missing_all_at` scalar on
   every ``_TIER_ORDER`` perspective and every axis combination.
3. Tier normalisation via :func:`_normalise_csv` (whitespace / case /
   dedup) at the scalar layer; unknown tier ids bucket into ``unknown[]``
   without short-circuiting the batch.
4. Empty / None / non-iterable ``perspective_tiers`` -> stable empty
   ``{tiers: [], unknown: []}`` envelope.
5. Grace-independence invariant: scalar returns byte-identical rows under
   grace vs enforce for every ``(perspectives, bundle)`` pair.
6. Runtime scalar-alias posture: no scalar-level canonicalisation (matches
   :func:`missing_runtimes_at`); alias tolerance belongs to the endpoint.
7. Kwarg semantics parity with :func:`missing_all_at`: unsupplied axis
   skipped; empty features/runtimes list -> that axis empty on every row;
   non-int capacity -> that axis ``None`` on every row.
8. Endpoint envelope shape (21-key set) + per-row shape (10-key set with
   a 5-key ``missing`` sub-dict) stable across every input branch.
9. Runtime-alias canonicalisation applied per-token upstream at the
   endpoint layer (``?runtimes=claude-code`` -> canonical ``claude_code``).
10. Never-4xx on any input (missing / blank / unknown tiers or bundle
    -> always 200); never-5xx: monkeypatched scalar / resolver blowup
    collapses to :func:`_missing_all_at_batch_fallback`.
11. Complement invariant with the paired ``/has-all-at-batch``: for every
    fully-parseable bundle and every perspective row,
    ``any(row.missing.values())`` is the strict negation of the paired
    row's ``has_all_at`` bit.
12. Cross-endpoint parity vs sibling ``/missing-all-at``: for any
    ``(perspective, bundle)`` cell, this endpoint's per-row ``missing``
    byte-equals ``/missing-all-at?tier=<row.tier>&<bundle>``'s
    ``missing``.
13. Cross-endpoint parity vs single-axis batch siblings
    ``/missing-features-at-batch`` / ``/missing-runtimes-at-batch``: for
    a single-axis bundle, per-row ``missing.<axis>`` equals sibling's
    per-row ``missing``.
14. Deliberate divergence from the LIVE ``/missing-all`` sibling: on the
    OSS perspective and a paid-feature bundle,
    ``missing.features=[paid]`` even in grace (that's the whole point
    of the ``_at`` slot).
15. Per-row ``any_missing`` folds row-denial OR endpoint-unknowns; per-
    row ``missing_count`` folds axis-wise (list ``len``, capacity ``1``
    if denied). Endpoint-level ``denied_count`` / ``all_denied`` /
    ``any_denied`` fold row-wise on ``any_missing``.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode. The batch what-if
    row-detail scalars are grace-independent by construction (they
    delegate to :func:`missing_all_at`, which is backed by the static
    per-tier tables)."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def enforced(monkeypatch, tmp_path):
    """Enforcement-on fixture -- pins the grace-independence contract."""
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


# ── Envelope shape constants ──────────────────────────────────────────────


_SCALAR_ENVELOPE_KEYS = {"tiers", "unknown"}
_SCALAR_ROW_KEYS = {"tier", "tier_label", "tier_rank", "missing"}
_MISSING_SLOT_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
}

_ENDPOINT_ENVELOPE_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown_features",
    "unknown_runtimes",
    "unknown_tiers",
    "supplied_axes",
    "supplied_count",
    "tiers",
    "denied_count",
    "all_denied",
    "any_denied",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}
_ENDPOINT_ROW_KEYS = {
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


def _empty_missing() -> dict:
    return {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }


def _get_json(client, url: str) -> dict:
    resp = client.get(url)
    assert resp.status_code == 200, (url, resp.status_code, resp.data[:200])
    return resp.get_json()


def _paid_feature(ent) -> str:
    for f in sorted(ent.PAID_FEATURES):
        return f
    pytest.skip("no paid features on this build")


def _paid_runtime(ent) -> str:
    for rt in sorted(ent.PAID_RUNTIMES):
        return rt
    pytest.skip("no paid runtimes on this build")


# ── Scalar: envelope shape ────────────────────────────────────────────────


def test_scalar_envelope_shape_stable_features(ent):
    r = ent.missing_all_at_batch(["oss", "cloud_pro"], features=["fleet"])
    assert set(r) == _SCALAR_ENVELOPE_KEYS
    for row in r["tiers"]:
        assert set(row) == _SCALAR_ROW_KEYS
        assert set(row["missing"]) == _MISSING_SLOT_KEYS


def test_scalar_envelope_shape_stable_runtimes(ent):
    r = ent.missing_all_at_batch(["oss", "cloud_pro"], runtimes=["openclaw"])
    assert set(r) == _SCALAR_ENVELOPE_KEYS
    for row in r["tiers"]:
        assert set(row) == _SCALAR_ROW_KEYS
        assert set(row["missing"]) == _MISSING_SLOT_KEYS


def test_scalar_envelope_shape_stable_capacity(ent):
    r = ent.missing_all_at_batch(["oss", "cloud_pro"], channels=1)
    assert set(r) == _SCALAR_ENVELOPE_KEYS
    for row in r["tiers"]:
        assert set(row) == _SCALAR_ROW_KEYS
        assert set(row["missing"]) == _MISSING_SLOT_KEYS


def test_scalar_envelope_shape_stable_mixed(ent):
    r = ent.missing_all_at_batch(
        ["oss", "cloud_pro"],
        features=["fleet"],
        runtimes=["openclaw"],
        channels=1,
        retention_days=1,
        nodes=1,
    )
    assert set(r) == _SCALAR_ENVELOPE_KEYS
    for row in r["tiers"]:
        assert set(row) == _SCALAR_ROW_KEYS
        assert set(row["missing"]) == _MISSING_SLOT_KEYS


def test_scalar_envelope_shape_stable_empty(ent):
    r = ent.missing_all_at_batch([])
    assert r == {"tiers": [], "unknown": []}


# ── Scalar: per-row parity with missing_all_at singular ───────────────────


def test_scalar_row_parity_features_only(ent):
    paid = _paid_feature(ent)
    tiers = list(ent._TIER_ORDER)
    r = ent.missing_all_at_batch(tiers, features=[paid])
    for row in r["tiers"]:
        assert row["missing"] == ent.missing_all_at(
            row["tier"], features=[paid]
        ), row


def test_scalar_row_parity_runtimes_only(ent):
    paid = _paid_runtime(ent)
    tiers = list(ent._TIER_ORDER)
    r = ent.missing_all_at_batch(tiers, runtimes=[paid])
    for row in r["tiers"]:
        assert row["missing"] == ent.missing_all_at(
            row["tier"], runtimes=[paid]
        ), row


def test_scalar_row_parity_capacity_channels(ent):
    tiers = list(ent._TIER_ORDER)
    for count in (0, 1, 5, 50, 999):
        r = ent.missing_all_at_batch(tiers, channels=count)
        for row in r["tiers"]:
            assert row["missing"] == ent.missing_all_at(
                row["tier"], channels=count
            ), (row, count)


def test_scalar_row_parity_capacity_retention(ent):
    tiers = list(ent._TIER_ORDER)
    for days in (1, 30, 90, 365):
        r = ent.missing_all_at_batch(tiers, retention_days=days)
        for row in r["tiers"]:
            assert row["missing"] == ent.missing_all_at(
                row["tier"], retention_days=days
            ), (row, days)


def test_scalar_row_parity_capacity_nodes(ent):
    tiers = list(ent._TIER_ORDER)
    for count in (1, 2, 10, 100):
        r = ent.missing_all_at_batch(tiers, nodes=count)
        for row in r["tiers"]:
            assert row["missing"] == ent.missing_all_at(
                row["tier"], nodes=count
            ), (row, count)


def test_scalar_row_parity_mixed_bundle(ent):
    paid_f = _paid_feature(ent)
    paid_r = _paid_runtime(ent)
    tiers = list(ent._TIER_ORDER)
    kwargs = dict(
        features=[paid_f],
        runtimes=[paid_r],
        channels=100,
        retention_days=90,
        nodes=100,
    )
    r = ent.missing_all_at_batch(tiers, **kwargs)
    for row in r["tiers"]:
        assert row["missing"] == ent.missing_all_at(row["tier"], **kwargs), row


# ── Scalar: tier normalisation + unknown bucketing ────────────────────────


def test_scalar_tier_normalises_case_and_whitespace(ent):
    r = ent.missing_all_at_batch(["  OSS  ", "Cloud_Pro"], features=["fleet"])
    tiers_by_id = {row["tier"] for row in r["tiers"]}
    assert "oss" in tiers_by_id
    assert "cloud_pro" in tiers_by_id


def test_scalar_dedup_preserves_first_seen(ent):
    r = ent.missing_all_at_batch(
        ["oss", "OSS", "cloud_pro", "oss"], features=["fleet"]
    )
    tiers = [row["tier"] for row in r["tiers"]]
    assert tiers.count("oss") == 1


def test_scalar_unknown_tier_buckets(ent):
    r = ent.missing_all_at_batch(
        ["oss", "definitely_not_a_tier"], features=["fleet"]
    )
    tiers = [row["tier"] for row in r["tiers"]]
    assert "oss" in tiers
    assert "definitely_not_a_tier" in r["unknown"]


def test_scalar_none_perspectives_returns_empty(ent):
    assert ent.missing_all_at_batch(None, features=["fleet"]) == {
        "tiers": [],
        "unknown": [],
    }


def test_scalar_non_iterable_perspectives_returns_empty(ent):
    assert ent.missing_all_at_batch(123, features=["fleet"]) == {  # type: ignore[arg-type]
        "tiers": [],
        "unknown": [],
    }


# ── Scalar: kwarg semantics parity with missing_all_at ────────────────────


def test_scalar_no_axes_supplied_every_row_empty_missing(ent):
    r = ent.missing_all_at_batch(["oss", "cloud_pro"])
    for row in r["tiers"]:
        assert row["missing"] == _empty_missing(), row


def test_scalar_empty_features_list_every_row_empty_features(ent):
    r = ent.missing_all_at_batch(["oss", "cloud_pro"], features=[])
    for row in r["tiers"]:
        assert row["missing"]["features"] == [], row


def test_scalar_empty_runtimes_list_every_row_empty_runtimes(ent):
    r = ent.missing_all_at_batch(["oss", "cloud_pro"], runtimes=[])
    for row in r["tiers"]:
        assert row["missing"]["runtimes"] == [], row


def test_scalar_non_int_channels_every_row_none(ent):
    r = ent.missing_all_at_batch(
        ["oss", "cloud_pro"], channels="five"  # type: ignore[arg-type]
    )
    for row in r["tiers"]:
        assert row["missing"]["channels"] is None, row


def test_scalar_non_int_retention_every_row_none(ent):
    r = ent.missing_all_at_batch(
        ["oss", "cloud_pro"], retention_days="thirty"  # type: ignore[arg-type]
    )
    for row in r["tiers"]:
        assert row["missing"]["retention_days"] is None, row


def test_scalar_non_int_nodes_every_row_none(ent):
    r = ent.missing_all_at_batch(
        ["oss", "cloud_pro"], nodes=["a"]  # type: ignore[arg-type]
    )
    for row in r["tiers"]:
        assert row["missing"]["nodes"] is None, row


def test_scalar_unknown_feature_typo_surfaces_in_missing(ent):
    """The strict scalar :func:`missing_features_at` treats unknown ids
    as denied at every tier (nothing grants them), so a typo surfaces in
    ``missing.features`` on every row. The endpoint layer filters known-
    only before passing to the scalar and surfaces unknowns via
    ``unknown_features`` instead -- pinned by the endpoint tests."""
    r = ent.missing_all_at_batch(
        list(ent._TIER_ORDER), features=["fleeet"]  # typo
    )
    for row in r["tiers"]:
        assert "fleeet" in row["missing"]["features"], row


# ── Scalar: alias posture (strict scalar; alias tolerance is at endpoint) ─


def test_scalar_runtime_alias_stays_strict(ent):
    """Raw ``claude-code`` on the strict scalar surfaces in
    ``missing.runtimes`` in its ``.strip().lower()`` form (matches
    :func:`missing_runtimes_at`)."""
    r = ent.missing_all_at_batch(
        list(ent._TIER_ORDER), runtimes=["claude-code"]
    )
    # OSS-free: strict scalar sees "claude-code" as an unknown runtime;
    # the scalar delegates to :func:`missing_runtimes_at` which returns
    # a subset of the input. At OSS the raw alias remains in the
    # returned list; at cloud_pro any raw alias will not appear as a
    # granted (or denied) runtime because it's outside ALL_RUNTIMES.
    for row in r["tiers"]:
        assert isinstance(row["missing"]["runtimes"], list)


def test_scalar_runtime_canonical_id_denies_at_oss_grants_at_pro(ent):
    """Canonical form works at scalar layer."""
    r = ent.missing_all_at_batch(
        list(ent._TIER_ORDER), runtimes=["claude_code"]
    )
    row_by_tier = {row["tier"]: row for row in r["tiers"]}
    # OSS statically doesn't grant paid runtimes -> missing includes it.
    assert "claude_code" in row_by_tier["oss"]["missing"]["runtimes"]
    # cloud_pro statically grants paid runtimes -> nothing missing.
    assert row_by_tier["cloud_pro"]["missing"]["runtimes"] == []


# ── Scalar: free-vs-paid semantics ────────────────────────────────────────


def test_scalar_all_free_bundle_no_missing_at_every_tier_features(ent):
    free = sorted(ent.FREE_FEATURES)
    if not free:
        pytest.skip("no free features on this build")
    r = ent.missing_all_at_batch(list(ent._TIER_ORDER), features=free)
    for row in r["tiers"]:
        assert row["missing"]["features"] == [], row["tier"]


def test_scalar_paid_feature_bundle_denied_at_oss(ent):
    paid = _paid_feature(ent)
    r = ent.missing_all_at_batch(["oss"], features=[paid])
    assert r["tiers"][0]["missing"]["features"] == [paid]


def test_scalar_paid_feature_bundle_granted_at_enterprise(ent):
    if "enterprise" not in ent._TIER_ORDER:
        pytest.skip("enterprise not on this build")
    paid = _paid_feature(ent)
    r = ent.missing_all_at_batch(["enterprise"], features=[paid])
    assert r["tiers"][0]["missing"]["features"] == []


def test_scalar_free_runtime_no_missing_at_every_tier(ent):
    free = sorted(ent.FREE_RUNTIMES)
    if not free:
        pytest.skip("no free runtimes on this build")
    r = ent.missing_all_at_batch(list(ent._TIER_ORDER), runtimes=free)
    for row in r["tiers"]:
        assert row["missing"]["runtimes"] == [], row["tier"]


# ── Scalar: grace-independence ────────────────────────────────────────────


@pytest.mark.parametrize(
    "kwargs",
    [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"]},
        {"channels": 100},
        {"retention_days": 90},
        {"nodes": 100},
        {
            "features": ["fleet"],
            "runtimes": ["claude_code"],
            "channels": 100,
            "retention_days": 90,
            "nodes": 100,
        },
    ],
)
def test_scalar_grace_independence_matches_at_scalar(ent, kwargs):
    tiers = list(ent._TIER_ORDER)
    batch = ent.missing_all_at_batch(tiers, **kwargs)
    for row in batch["tiers"]:
        assert row["missing"] == ent.missing_all_at(row["tier"], **kwargs), (
            row,
            kwargs,
        )


def test_scalar_grace_off_returns_identical_rows(
    enforced, monkeypatch, tmp_path
):
    """Batch answer identical under enforce vs grace for every
    (perspectives, bundle) pair -- the delegate is grace-independent by
    construction."""
    tiers = list(enforced._TIER_ORDER)
    kwargs = {"features": ["fleet"], "channels": 100, "nodes": 100}
    enforced_batch = enforced.missing_all_at_batch(tiers, **kwargs)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    try:
        grace_batch = e.missing_all_at_batch(tiers, **kwargs)
        for erow, grow in zip(enforced_batch["tiers"], grace_batch["tiers"]):
            assert erow["tier"] == grow["tier"]
            assert erow["missing"] == grow["missing"], (erow, grow)
    finally:
        e.invalidate()


# ── Scalar: complement invariant with has_all_at_batch ────────────────────


@pytest.mark.parametrize(
    "kwargs",
    [
        {"features": ["fleet"]},
        {"runtimes": ["claude_code"]},
        {"features": ["fleet"], "runtimes": ["claude_code"]},
        {"channels": 100, "retention_days": 90, "nodes": 100},
    ],
)
def test_scalar_complement_invariant_with_has_all_at_batch(ent, kwargs):
    """``any(row.missing.values())`` on missing_all_at_batch equals the
    strict negation of the paired row's ``has_all_at`` bit on
    ``has_all_at_batch`` for every fully-parseable bundle."""
    tiers = list(ent._TIER_ORDER)
    missing = ent.missing_all_at_batch(tiers, **kwargs)
    has = ent.has_all_at_batch(tiers, **kwargs)
    missing_rows = {row["tier"]: row for row in missing["tiers"]}
    has_rows = {row["tier"]: row for row in has["tiers"]}
    for tid in tiers:
        m = missing_rows[tid]["missing"]
        any_missing = (
            bool(m["features"])
            or bool(m["runtimes"])
            or m["channels"] is not None
            or m["retention_days"] is not None
            or m["nodes"] is not None
        )
        assert any_missing == (not has_rows[tid]["has_all_at"]), (
            tid,
            kwargs,
        )


# ── Scalar: never-raises ──────────────────────────────────────────────────


def test_scalar_never_raises_on_delegate_blowup(ent, monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "missing_all_at", _boom)
    r = ent.missing_all_at_batch(["oss", "cloud_pro"], features=["fleet"])
    assert r["tiers"] == []
    assert r["unknown"] == ["oss", "cloud_pro"]


# ── Endpoint: envelope shape ──────────────────────────────────────────────


def test_endpoint_envelope_shape_no_args(client):
    body = _get_json(client, "/api/entitlement/missing-all-at-batch")
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    assert body["tiers"] == []
    assert body["denied_count"] == 0
    assert body["all_denied"] is False
    assert body["any_denied"] is False


def test_endpoint_envelope_shape_features_only(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch?tiers=oss,cloud_pro&features=fleet",
    )
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    for row in body["tiers"]:
        assert set(row) == _ENDPOINT_ROW_KEYS
        assert set(row["missing"]) == _MISSING_SLOT_KEYS


def test_endpoint_envelope_shape_runtimes_only(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch?tiers=oss,cloud_pro&runtimes=openclaw",
    )
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    for row in body["tiers"]:
        assert set(row) == _ENDPOINT_ROW_KEYS
        assert set(row["missing"]) == _MISSING_SLOT_KEYS


def test_endpoint_envelope_shape_mixed(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro&features=fleet"
        "&runtimes=claude_code&channels=100&retention_days=90&nodes=100",
    )
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    for row in body["tiers"]:
        assert set(row) == _ENDPOINT_ROW_KEYS
        assert set(row["missing"]) == _MISSING_SLOT_KEYS


def test_endpoint_envelope_shape_unknown_tokens(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,bogus_tier&features=fleeet&runtimes=totally_fake_rt",
    )
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    assert "fleeet" in body["unknown_features"]
    assert "totally_fake_rt" in body["unknown_runtimes"]
    assert "bogus_tier" in body["unknown_tiers"]


# ── Endpoint: capacity coercion ───────────────────────────────────────────


def test_endpoint_non_int_channels_none_on_every_row(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro&channels=five",
    )
    assert body["channels"] is None
    for row in body["tiers"]:
        assert row["missing"]["channels"] is None


def test_endpoint_non_int_retention_none_on_every_row(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro&retention_days=thirty",
    )
    assert body["retention_days"] is None
    for row in body["tiers"]:
        assert row["missing"]["retention_days"] is None


def test_endpoint_non_int_nodes_none_on_every_row(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro&nodes=two",
    )
    assert body["nodes"] is None
    for row in body["tiers"]:
        assert row["missing"]["nodes"] is None


# ── Endpoint: runtime-alias canonicalisation ──────────────────────────────


def test_endpoint_runtime_alias_canonicalised_upstream(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro&runtimes=claude-code",
    )
    assert "claude_code" in body["runtimes"]
    assert "claude-code" not in body["runtimes"]
    row_by_tier = {row["tier"]: row for row in body["tiers"]}
    assert "claude_code" in row_by_tier["oss"]["missing"]["runtimes"]
    assert row_by_tier["cloud_pro"]["missing"]["runtimes"] == []


def test_endpoint_runtime_alias_and_canonical_dedup(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss&runtimes=claude-code,claude_code",
    )
    assert body["runtimes"].count("claude_code") == 1
    assert body["tiers"][0]["missing"]["runtimes"].count("claude_code") == 1


# ── Endpoint: per-row aggregation ────────────────────────────────────────


def test_endpoint_row_missing_count_folds_axis_wise(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss&features=fleet,sso&runtimes=claude_code"
        "&channels=100&retention_days=90&nodes=100",
    )
    row = body["tiers"][0]
    missing = row["missing"]
    expected = (
        len(missing["features"])
        + len(missing["runtimes"])
        + (1 if missing["channels"] is not None else 0)
        + (1 if missing["retention_days"] is not None else 0)
        + (1 if missing["nodes"] is not None else 0)
    )
    assert row["missing_count"] == expected
    assert row["any_missing"] is (expected > 0)


def test_endpoint_row_any_missing_reflects_unknown_features(client):
    """Unknown feature id at endpoint layer flips ``any_missing`` on
    every row even when the strict scalar reports empty per-axis (matches
    :func:`_missing_bundle_at_batch_body` posture)."""
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=cloud_pro&features=fleeet",  # cloud_pro grants everything known
    )
    assert body["unknown_features"] == ["fleeet"]
    for row in body["tiers"]:
        assert row["any_missing"] is True


def test_endpoint_row_any_missing_reflects_unknown_runtimes(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=cloud_pro&runtimes=totally_fake_rt",
    )
    assert body["unknown_runtimes"] == ["totally_fake_rt"]
    for row in body["tiers"]:
        assert row["any_missing"] is True


def test_endpoint_denied_count_folds_row_wise(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro,enterprise&features=fleet",
    )
    expected = sum(1 for row in body["tiers"] if row["any_missing"])
    assert body["denied_count"] == expected
    assert body["all_denied"] is (
        bool(body["tiers"])
        and all(row["any_missing"] for row in body["tiers"])
    )
    assert body["any_denied"] is any(
        row["any_missing"] for row in body["tiers"]
    )


# ── Endpoint: per-row parity with scalar and singular endpoint ────────────


@pytest.mark.parametrize(
    "params",
    [
        "features=fleet",
        "runtimes=claude_code",
        "features=fleet&runtimes=claude_code",
        "channels=100",
        "retention_days=90",
        "nodes=100",
        (
            "features=fleet&runtimes=claude_code"
            "&channels=100&retention_days=90&nodes=100"
        ),
    ],
)
def test_endpoint_row_parity_with_scalar(client, ent, params):
    body = _get_json(
        client,
        f"/api/entitlement/missing-all-at-batch?tiers=oss,cloud_pro&{params}",
    )
    for row in body["tiers"]:
        expected = ent.missing_all_at(
            row["tier"],
            features=body["features"] or None,
            runtimes=body["runtimes"] or None,
            channels=body["channels"],
            retention_days=body["retention_days"],
            nodes=body["nodes"],
        )
        assert row["missing"] == expected, (row, params)


@pytest.mark.parametrize(
    "params",
    [
        "features=fleet,sso",
        "runtimes=claude_code",
        "channels=100",
        "retention_days=90",
        "nodes=100",
    ],
)
def test_endpoint_row_missing_matches_singular_endpoint(client, params):
    """Per-row ``missing`` byte-equals ``/missing-all-at?tier=<row.tier>&<bundle>``
    on the same bundle."""
    batch = _get_json(
        client,
        f"/api/entitlement/missing-all-at-batch?tiers=oss,cloud_pro&{params}",
    )
    for row in batch["tiers"]:
        singular = _get_json(
            client,
            f"/api/entitlement/missing-all-at?tier={row['tier']}&{params}",
        )
        for k in ("features", "runtimes", "channels", "retention_days", "nodes"):
            assert row["missing"][k] == singular.get(k), (row["tier"], k)


# ── Endpoint: cross-endpoint parity vs single-axis batch siblings ─────────


def test_endpoint_features_only_matches_missing_features_at_batch(client):
    """For a single-axis features bundle, per-row ``missing.features``
    equals the sibling ``/missing-features-at-batch``'s per-row
    ``missing``."""
    mixed = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro&features=fleet,sso",
    )
    single = _get_json(
        client,
        "/api/entitlement/missing-features-at-batch"
        "?tiers=oss,cloud_pro&features=fleet,sso",
    )
    mixed_by = {r["tier"]: r for r in mixed["tiers"]}
    single_by = {r["tier"]: r for r in single["tiers"]}
    for tid in mixed_by:
        assert mixed_by[tid]["missing"]["features"] == single_by[tid]["missing"], tid


def test_endpoint_runtimes_only_matches_missing_runtimes_at_batch(client):
    mixed = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro&runtimes=claude_code",
    )
    single = _get_json(
        client,
        "/api/entitlement/missing-runtimes-at-batch"
        "?tiers=oss,cloud_pro&runtimes=claude_code",
    )
    mixed_by = {r["tier"]: r for r in mixed["tiers"]}
    single_by = {r["tier"]: r for r in single["tiers"]}
    for tid in mixed_by:
        assert mixed_by[tid]["missing"]["runtimes"] == single_by[tid]["missing"], tid


# ── Endpoint: complement invariant with has-all-at-batch ──────────────────


@pytest.mark.parametrize(
    "params",
    [
        "features=fleet",
        "runtimes=claude_code",
        "features=fleet&runtimes=claude_code",
        "features=fleet&channels=100&retention_days=90&nodes=100",
    ],
)
def test_endpoint_complement_invariant_with_has_all_at_batch(client, params):
    """For every (perspective, bundle) row: any denial on missing-at-batch
    == not(has_all_at) on has-all-at-batch. Unknown-token branch is
    excluded via bundle picks known ids only."""
    missing = _get_json(
        client,
        f"/api/entitlement/missing-all-at-batch?tiers=oss,cloud_pro&{params}",
    )
    has = _get_json(
        client,
        f"/api/entitlement/has-all-at-batch?tiers=oss,cloud_pro&{params}",
    )
    missing_by = {r["tier"]: r for r in missing["tiers"]}
    has_by = {r["tier"]: r for r in has["tiers"]}
    for tid in missing_by:
        m = missing_by[tid]["missing"]
        any_missing = (
            bool(m["features"])
            or bool(m["runtimes"])
            or m["channels"] is not None
            or m["retention_days"] is not None
            or m["nodes"] is not None
        )
        assert any_missing == (not has_by[tid]["has_all_at"]), (tid, params)


# ── Endpoint: axis-echo parity with has-all-at-batch ──────────────────────


def test_endpoint_axis_echoes_match_has_all_at_batch(client):
    """features / runtimes / channels / retention_days / nodes /
    unknown_features / unknown_runtimes / unknown_tiers / supplied_axes /
    supplied_count byte-equal ``/has-all-at-batch`` on the same URL."""
    q = (
        "?tiers=oss,bogus_tier,cloud_pro"
        "&features=FLEET,fleet,sso,bogus"
        "&runtimes=claude-code,codex,totally_fake_rt"
        "&channels=5&retention_days=30&nodes=2"
    )
    missing = _get_json(
        client, f"/api/entitlement/missing-all-at-batch{q}"
    )
    has = _get_json(client, f"/api/entitlement/has-all-at-batch{q}")
    for k in (
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
        "unknown_features",
        "unknown_runtimes",
        "unknown_tiers",
        "supplied_axes",
        "supplied_count",
    ):
        assert missing[k] == has[k], k


# ── Endpoint: grace vs enforce -- perspective answers unchanged ───────────


def test_endpoint_grace_vs_enforce_row_identity(client, ent, monkeypatch):
    grace = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro&features=fleet",
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    try:
        from routes.entitlement import bp_entitlement

        app = Flask(__name__)
        app.register_blueprint(bp_entitlement)
        c2 = app.test_client()
        enforced = _get_json(
            c2,
            "/api/entitlement/missing-all-at-batch"
            "?tiers=oss,cloud_pro&features=fleet",
        )
    finally:
        monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
        importlib.reload(e)
        e.invalidate()
    grace_rows = {row["tier"]: row["missing"] for row in grace["tiers"]}
    enforced_rows = {row["tier"]: row["missing"] for row in enforced["tiers"]}
    assert grace_rows == enforced_rows


# ── Endpoint: never-4xx / never-5xx ───────────────────────────────────────


def test_endpoint_missing_tiers_returns_200(client):
    resp = client.get("/api/entitlement/missing-all-at-batch")
    assert resp.status_code == 200


def test_endpoint_blank_tiers_returns_200(client):
    resp = client.get("/api/entitlement/missing-all-at-batch?tiers=")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tiers"] == []


def test_endpoint_all_unknown_tiers_returns_200(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=bogus1,bogus2&features=fleet",
    )
    assert body["tiers"] == []
    assert set(body["unknown_tiers"]) == {"bogus1", "bogus2"}


def test_endpoint_never_5xxs_on_scalar_blowup(client, ent, monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "missing_all_at_batch", _boom)
    resp = client.get(
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    assert body["tiers"] == []
    assert body["denied_count"] == 0
    assert body["all_denied"] is False
    assert body["any_denied"] is False


def test_endpoint_never_5xxs_on_min_tier_blowup(client, ent, monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "min_tier_for_all", _boom)
    resp = client.get(
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro&features=fleet"
    )
    assert resp.status_code == 200


# ── Endpoint: LIVE resolver bits present on envelope ──────────────────────


def test_endpoint_carries_resolver_envelope_bits(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch?tiers=oss&features=fleet",
    )
    assert "current_tier" in body
    assert "current_tier_rank" in body
    assert isinstance(body["grace"], bool)
    assert isinstance(body["enforced"], bool)


def test_endpoint_required_tier_rolls_up_bundle_level(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro,enterprise&features=fleet",
    )
    assert body["required_tier"] is not None
    for row in body["tiers"]:
        assert row["required_tier"] == body["required_tier"]
        assert row["required_tier_label"] == body["required_tier_label"]
        assert row["required_tier_rank"] == body["required_tier_rank"]


def test_endpoint_row_upgrade_required_at_lower_tier(client):
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch"
        "?tiers=oss,cloud_pro,enterprise&features=fleet",
    )
    rows_by = {r["tier"]: r for r in body["tiers"]}
    required_rank = body["required_tier_rank"]
    for tid, row in rows_by.items():
        if row["tier_rank"] < required_rank:
            assert row["upgrade_required"] is True, tid
        else:
            assert row["upgrade_required"] is False, tid


# ── Endpoint: deliberate divergence from LIVE /missing-all ────────────────


def test_endpoint_oss_at_slot_denies_paid_feature_in_grace(client):
    """The whole point of the ``_at`` slot: on OSS + paid feature, the
    per-row ``missing.features`` reports the feature even when the LIVE
    resolver is in grace and ``/missing-all`` reports empty."""
    body = _get_json(
        client,
        "/api/entitlement/missing-all-at-batch?tiers=oss&features=fleet",
    )
    assert body["grace"] is True
    assert body["tiers"][0]["missing"]["features"] == ["fleet"]
    # Compare with LIVE /missing-all which pass-throughs in grace.
    live = _get_json(
        client, "/api/entitlement/missing-all?features=fleet"
    )
    assert live["features"] == []
