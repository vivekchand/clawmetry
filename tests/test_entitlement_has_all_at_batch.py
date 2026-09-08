"""Tests for the batch what-if mixed-axis ``has_all_at_batch`` boolean-fold
scalar and its paired ``/api/entitlement/has-all-at-batch`` endpoint.

Batch what-if sibling of :func:`has_all_at` (single perspective, mixed-axis
fold) in the same relationship :func:`has_features_at_batch` /
:func:`has_runtimes_at_batch` have to :func:`has_features_at` /
:func:`has_runtimes_at`: fixes ONE mixed-axis bundle and sweeps across N
perspective tiers, returning one row per tier with the aggregate mixed-
axis fold boolean so a pricing-matrix column ("does OSS admit fleet +
claude_code + 100 channels + 90d retention + 100 nodes? Starter? Cloud
Pro? Enterprise?") hydrates off ONE call instead of five ``_at-batch``
round-trips + a client-side AND-chain.

This file pins:

1. Scalar envelope shape ({tiers, unknown}) + per-row shape (4 keys) stable
   across every input branch.
2. Per-row ``has_all_at`` byte-parity with :func:`has_all_at` scalar on
   every ``_TIER_ORDER`` perspective and every axis combination.
3. Tier normalisation via :func:`_normalise_csv` (whitespace / case /
   dedup) at the scalar layer; unknown tier ids bucket into ``unknown[]``
   without short-circuiting the batch.
4. Empty / None / non-iterable ``perspective_tiers`` -> stable empty
   ``{tiers: [], unknown: []}`` envelope.
5. Grace-independence invariant: scalar returns byte-identical rows under
   grace vs enforce for every ``(perspectives, bundle)`` pair.
6. Runtime scalar-alias posture: no scalar-level canonicalisation (matches
   :func:`has_runtimes_at`); alias tolerance belongs to the endpoint.
7. Kwarg semantics mirror :func:`has_all_at`: unsupplied axis skipped;
   empty features/runtimes list -> every row False; non-int capacity ->
   every row False; no axes supplied -> every row False.
8. Endpoint envelope shape (fixed 21-key set) + per-row shape (9-key set)
   stable across every input branch.
9. Runtime-alias canonicalisation applied per-token upstream at the
   endpoint layer (``?runtimes=claude-code`` -> canonical ``claude_code``).
10. Never-4xx on any input (missing / blank / unknown tiers or bundle -
    always 200); never-5xx: monkeypatch scalar / resolver blowup collapses
    to :func:`_has_all_at_batch_fallback`.
11. Scalar-vs-endpoint parity: per-row endpoint ``has_all_at`` byte-equals
    the scalar's ``has_all_at`` on the same ``(tier, bundle)`` pair
    (modulo the endpoint's unknown-collapse fold, which is documented).
12. Cross-endpoint parity vs sibling ``/has-all-at``: for any
    ``(perspective, bundle)`` cell, this endpoint's per-row ``has_all_at``
    equals ``/has-all-at?tier=<row.tier>&<bundle>``'s ``has_all_at``.
13. Cross-endpoint parity vs the single-axis batch siblings
    ``/has-features-at-batch`` / ``/has-runtimes-at-batch``: for a
    single-axis bundle, per-row ``has_all_at`` equals sibling's per-row
    ``has_features_at`` / ``has_runtimes_at``.
14. Deliberate divergence from the LIVE ``/has-all`` sibling: on the OSS
    perspective and a paid-feature bundle, ``has_all_at=false`` even in
    grace (that's the whole point of the ``_at`` slot).
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module in OSS-free-grace mode. The batch what-if
    scalars are grace-independent by construction (they delegate to
    :func:`has_all_at`, which is backed by the static per-tier tables)."""
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
_SCALAR_ROW_KEYS = {"tier", "tier_label", "tier_rank", "has_all_at"}

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
    "allowed_count",
    "all_allowed",
    "any_allowed",
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
    "has_all_at",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "upgrade_required",
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
    r = ent.has_all_at_batch(["oss", "cloud_pro"], features=["fleet"])
    assert set(r) == _SCALAR_ENVELOPE_KEYS
    for row in r["tiers"]:
        assert set(row) == _SCALAR_ROW_KEYS


def test_scalar_envelope_shape_stable_runtimes(ent):
    r = ent.has_all_at_batch(["oss", "cloud_pro"], runtimes=["openclaw"])
    assert set(r) == _SCALAR_ENVELOPE_KEYS
    for row in r["tiers"]:
        assert set(row) == _SCALAR_ROW_KEYS


def test_scalar_envelope_shape_stable_capacity(ent):
    r = ent.has_all_at_batch(["oss", "cloud_pro"], channels=1)
    assert set(r) == _SCALAR_ENVELOPE_KEYS
    for row in r["tiers"]:
        assert set(row) == _SCALAR_ROW_KEYS


def test_scalar_envelope_shape_stable_mixed(ent):
    r = ent.has_all_at_batch(
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


def test_scalar_envelope_shape_stable_empty(ent):
    r = ent.has_all_at_batch([])
    assert r == {"tiers": [], "unknown": []}


# ── Scalar: per-row parity with has_all_at singular ───────────────────────


def test_scalar_row_parity_features_only(ent):
    paid = _paid_feature(ent)
    tiers = list(ent._TIER_ORDER)
    r = ent.has_all_at_batch(tiers, features=[paid])
    for row in r["tiers"]:
        assert row["has_all_at"] == ent.has_all_at(
            row["tier"], features=[paid]
        ), row


def test_scalar_row_parity_runtimes_only(ent):
    paid = _paid_runtime(ent)
    tiers = list(ent._TIER_ORDER)
    r = ent.has_all_at_batch(tiers, runtimes=[paid])
    for row in r["tiers"]:
        assert row["has_all_at"] == ent.has_all_at(
            row["tier"], runtimes=[paid]
        ), row


def test_scalar_row_parity_capacity_channels(ent):
    tiers = list(ent._TIER_ORDER)
    for count in (0, 1, 5, 50, 999):
        r = ent.has_all_at_batch(tiers, channels=count)
        for row in r["tiers"]:
            assert row["has_all_at"] == ent.has_all_at(
                row["tier"], channels=count
            ), (row, count)


def test_scalar_row_parity_capacity_retention(ent):
    tiers = list(ent._TIER_ORDER)
    for days in (1, 30, 90, 365):
        r = ent.has_all_at_batch(tiers, retention_days=days)
        for row in r["tiers"]:
            assert row["has_all_at"] == ent.has_all_at(
                row["tier"], retention_days=days
            ), (row, days)


def test_scalar_row_parity_capacity_nodes(ent):
    tiers = list(ent._TIER_ORDER)
    for count in (1, 2, 10, 100):
        r = ent.has_all_at_batch(tiers, nodes=count)
        for row in r["tiers"]:
            assert row["has_all_at"] == ent.has_all_at(
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
    r = ent.has_all_at_batch(tiers, **kwargs)
    for row in r["tiers"]:
        assert row["has_all_at"] == ent.has_all_at(row["tier"], **kwargs), row


def test_scalar_row_label_and_rank_match_helpers(ent):
    r = ent.has_all_at_batch(list(ent._TIER_ORDER), features=["fleet"])
    for row in r["tiers"]:
        assert row["tier_label"] == ent.tier_label(row["tier"])
        assert row["tier_rank"] == ent._TIER_RANK.get(row["tier"], -1)


# ── Scalar: tier normalisation ────────────────────────────────────────────


def test_scalar_normalises_and_dedups_tiers(ent):
    r = ent.has_all_at_batch(
        ["  OSS  ", "oss", "Cloud_Pro"], features=["fleet"]
    )
    assert [row["tier"] for row in r["tiers"]] == ["oss", "cloud_pro"]
    assert r["unknown"] == []


def test_scalar_unknown_tiers_bucket_not_shortcircuit(ent):
    r = ent.has_all_at_batch(
        ["oss", "bogus_a", "cloud_pro", "bogus_b"], features=["fleet"]
    )
    assert [row["tier"] for row in r["tiers"]] == ["oss", "cloud_pro"]
    assert r["unknown"] == ["bogus_a", "bogus_b"]


def test_scalar_none_perspectives_returns_empty(ent):
    assert ent.has_all_at_batch(None, features=["fleet"]) == {
        "tiers": [],
        "unknown": [],
    }


def test_scalar_non_iterable_perspectives_returns_empty(ent):
    assert ent.has_all_at_batch(123, features=["fleet"]) == {  # type: ignore[arg-type]
        "tiers": [],
        "unknown": [],
    }


# ── Scalar: kwarg semantics parity with has_all_at ────────────────────────


def test_scalar_no_axes_supplied_every_row_false(ent):
    r = ent.has_all_at_batch(["oss", "cloud_pro"])
    assert all(row["has_all_at"] is False for row in r["tiers"])


def test_scalar_empty_features_list_every_row_false(ent):
    r = ent.has_all_at_batch(["oss", "cloud_pro"], features=[])
    assert all(row["has_all_at"] is False for row in r["tiers"])


def test_scalar_empty_runtimes_list_every_row_false(ent):
    r = ent.has_all_at_batch(["oss", "cloud_pro"], runtimes=[])
    assert all(row["has_all_at"] is False for row in r["tiers"])


def test_scalar_non_int_channels_every_row_false(ent):
    r = ent.has_all_at_batch(
        ["oss", "cloud_pro"], channels="five"  # type: ignore[arg-type]
    )
    assert all(row["has_all_at"] is False for row in r["tiers"])


def test_scalar_non_int_retention_every_row_false(ent):
    r = ent.has_all_at_batch(
        ["oss", "cloud_pro"], retention_days="thirty"  # type: ignore[arg-type]
    )
    assert all(row["has_all_at"] is False for row in r["tiers"])


def test_scalar_non_int_nodes_every_row_false(ent):
    r = ent.has_all_at_batch(
        ["oss", "cloud_pro"], nodes=["a"]  # type: ignore[arg-type]
    )
    assert all(row["has_all_at"] is False for row in r["tiers"])


def test_scalar_unknown_feature_typo_collapses_every_row(ent):
    r = ent.has_all_at_batch(
        list(ent._TIER_ORDER), features=["fleeet"]  # typo
    )
    assert all(row["has_all_at"] is False for row in r["tiers"])


def test_scalar_unknown_runtime_typo_collapses_every_row(ent):
    r = ent.has_all_at_batch(
        list(ent._TIER_ORDER), runtimes=["totally_fake_rt"]
    )
    assert all(row["has_all_at"] is False for row in r["tiers"])


# ── Scalar: alias posture (strict scalar; alias tolerance is at endpoint) ─


def test_scalar_runtime_alias_stays_strict(ent):
    """Raw ``claude-code`` on the strict scalar collapses to ``False`` on
    every row (matches :func:`has_runtimes_at`). Alias tolerance belongs
    to the endpoint upstream layer."""
    r = ent.has_all_at_batch(list(ent._TIER_ORDER), runtimes=["claude-code"])
    assert all(row["has_all_at"] is False for row in r["tiers"])


def test_scalar_runtime_canonical_id_grants_at_paid_tiers(ent):
    """Canonical form works at scalar layer."""
    r = ent.has_all_at_batch(list(ent._TIER_ORDER), runtimes=["claude_code"])
    row_by_tier = {row["tier"]: row for row in r["tiers"]}
    # OSS statically doesn't grant paid runtimes.
    assert row_by_tier["oss"]["has_all_at"] is False
    # cloud_pro statically grants paid runtimes.
    assert row_by_tier["cloud_pro"]["has_all_at"] is True


# ── Scalar: free-vs-paid semantics ────────────────────────────────────────


def test_scalar_all_free_bundle_true_at_every_tier_features(ent):
    free = sorted(ent.FREE_FEATURES)
    if not free:
        pytest.skip("no free features on this build")
    r = ent.has_all_at_batch(list(ent._TIER_ORDER), features=free)
    for row in r["tiers"]:
        assert row["has_all_at"] is True, row["tier"]


def test_scalar_paid_feature_bundle_denied_at_oss(ent):
    paid = _paid_feature(ent)
    r = ent.has_all_at_batch(["oss"], features=[paid])
    assert r["tiers"][0]["has_all_at"] is False


def test_scalar_paid_feature_bundle_granted_at_enterprise(ent):
    if "enterprise" not in ent._TIER_ORDER:
        pytest.skip("enterprise not on this build")
    paid = _paid_feature(ent)
    r = ent.has_all_at_batch(["enterprise"], features=[paid])
    assert r["tiers"][0]["has_all_at"] is True


def test_scalar_free_runtime_true_at_every_tier(ent):
    free = sorted(ent.FREE_RUNTIMES)
    if not free:
        pytest.skip("no free runtimes on this build")
    r = ent.has_all_at_batch(list(ent._TIER_ORDER), runtimes=free)
    for row in r["tiers"]:
        assert row["has_all_at"] is True, row["tier"]


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
    batch = ent.has_all_at_batch(tiers, **kwargs)
    for row in batch["tiers"]:
        assert row["has_all_at"] == ent.has_all_at(row["tier"], **kwargs), (
            row,
            kwargs,
        )


def test_scalar_grace_off_returns_identical_rows(enforced, monkeypatch, tmp_path):
    """Batch answer identical under enforce vs grace for every
    (perspectives, bundle) pair -- the delegate is grace-independent by
    construction."""
    tiers = list(enforced._TIER_ORDER)
    kwargs = {"features": ["fleet"], "channels": 100, "nodes": 100}
    enforced_batch = enforced.has_all_at_batch(tiers, **kwargs)
    # Flip back to grace and re-run: same answer.
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    try:
        grace_batch = e.has_all_at_batch(tiers, **kwargs)
        # Rows may differ only if tier ordering changed (they don't).
        for erow, grow in zip(enforced_batch["tiers"], grace_batch["tiers"]):
            assert erow["tier"] == grow["tier"]
            assert erow["has_all_at"] == grow["has_all_at"], (erow, grow)
    finally:
        e.invalidate()


# ── Scalar: never-raises ──────────────────────────────────────────────────


def test_scalar_never_raises_on_delegate_blowup(ent, monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "has_all_at", _boom)
    r = ent.has_all_at_batch(["oss", "cloud_pro"], features=["fleet"])
    # Both rows short-circuit into unknown[]; envelope stays stable.
    assert r["tiers"] == []
    assert r["unknown"] == ["oss", "cloud_pro"]


# ── Endpoint: envelope shape ──────────────────────────────────────────────


def test_endpoint_envelope_shape_no_args(client):
    body = _get_json(client, "/api/entitlement/has-all-at-batch")
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    assert body["tiers"] == []


def test_endpoint_envelope_shape_mixed_bundle(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss,cloud_pro"
        "&features=fleet&runtimes=claude_code"
        "&channels=100&retention_days=90&nodes=100",
    )
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    for row in body["tiers"]:
        assert set(row) == _ENDPOINT_ROW_KEYS


def test_endpoint_envelope_shape_only_tiers(client):
    body = _get_json(
        client, "/api/entitlement/has-all-at-batch?tiers=oss,cloud_pro"
    )
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    # Tiers still emitted; every row False (no axes supplied).
    assert [row["tier"] for row in body["tiers"]] == ["oss", "cloud_pro"]
    assert all(row["has_all_at"] is False for row in body["tiers"])


def test_endpoint_envelope_shape_bogus_tier(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss,bogus,cloud_pro&features=fleet",
    )
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    assert body["unknown_tiers"] == ["bogus"]
    assert [row["tier"] for row in body["tiers"]] == ["oss", "cloud_pro"]


def test_endpoint_envelope_shape_unknown_feature(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss,cloud_pro&features=fleet,totally_fake",
    )
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    assert body["unknown_features"] == ["totally_fake"]
    assert all(row["has_all_at"] is False for row in body["tiers"])


def test_endpoint_envelope_shape_unknown_runtime(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss,cloud_pro&runtimes=openclaw,totally_fake_rt",
    )
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    assert body["unknown_runtimes"] == ["totally_fake_rt"]
    assert all(row["has_all_at"] is False for row in body["tiers"])


def test_endpoint_envelope_shape_non_int_capacity(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss,cloud_pro&channels=five",
    )
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    assert body["channels"] is None
    assert all(row["has_all_at"] is False for row in body["tiers"])


# ── Endpoint: supplied_axes tracking ──────────────────────────────────────


def test_endpoint_supplied_axes_features_only(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss&features=fleet",
    )
    assert body["supplied_axes"] == ["features"]
    assert body["supplied_count"] == 1


def test_endpoint_supplied_axes_all_five(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss&features=fleet"
        "&runtimes=claude_code&channels=1&retention_days=1&nodes=1",
    )
    assert body["supplied_axes"] == [
        "features",
        "runtimes",
        "channels",
        "retention_days",
        "nodes",
    ]
    assert body["supplied_count"] == 5


def test_endpoint_supplied_axes_empty(client):
    body = _get_json(client, "/api/entitlement/has-all-at-batch?tiers=oss")
    assert body["supplied_axes"] == []
    assert body["supplied_count"] == 0


# ── Endpoint: runtime alias canonicalisation upstream ─────────────────────


def test_endpoint_runtime_alias_canonicalises(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=cloud_pro&runtimes=claude-code",
    )
    # The alias flips to canonical form; cloud_pro admits claude_code.
    assert body["runtimes"] == ["claude_code"]
    assert body["unknown_runtimes"] == []
    assert body["tiers"][0]["has_all_at"] is True


def test_endpoint_runtime_alias_dedups_pair(client):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=cloud_pro"
        "&runtimes=claude-code,claude_code",
    )
    # Alias + canonical collapse to one row before the scalar sees them.
    assert body["runtimes"] == ["claude_code"]


# ── Endpoint: rollups ─────────────────────────────────────────────────────


def test_endpoint_all_allowed_and_any_allowed_paid_feature(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss,cloud_pro&features=fleet",
    )
    # OSS false, cloud_pro true.
    assert body["all_allowed"] is False
    assert body["any_allowed"] is True
    assert body["allowed_count"] == 1


def test_endpoint_all_allowed_all_free(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss,cloud_pro"
        "&runtimes=openclaw",
    )
    # Free runtime -> every row True.
    assert body["all_allowed"] is True
    assert body["any_allowed"] is True
    assert body["allowed_count"] == 2


def test_endpoint_all_allowed_empty_tiers(client):
    body = _get_json(client, "/api/entitlement/has-all-at-batch?tiers=&features=fleet")
    assert body["all_allowed"] is False  # empty tiers -> False (fail-closed)
    assert body["any_allowed"] is False


# ── Endpoint: per-row upgrade_required ────────────────────────────────────


def test_endpoint_upgrade_required_flips_at_required_tier(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss,cloud_starter,cloud_pro,enterprise&features=fleet",
    )
    required_tier = body["required_tier"]
    required_rank = body["required_tier_rank"]
    assert required_tier is not None
    for row in body["tiers"]:
        expected_upgrade = row["tier_rank"] < required_rank
        assert row["upgrade_required"] is expected_upgrade, row


# ── Endpoint: never-4xx ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "/api/entitlement/has-all-at-batch",
        "/api/entitlement/has-all-at-batch?tiers=",
        "/api/entitlement/has-all-at-batch?tiers=bogus",
        "/api/entitlement/has-all-at-batch?tiers=oss",
        "/api/entitlement/has-all-at-batch?tiers=oss&features=",
        "/api/entitlement/has-all-at-batch?tiers=oss&channels=",
        "/api/entitlement/has-all-at-batch?tiers=oss&channels=five",
        "/api/entitlement/has-all-at-batch?tiers=oss&features=totally_fake",
        "/api/entitlement/has-all-at-batch?tiers=oss&runtimes=totally_fake_rt",
    ],
)
def test_endpoint_never_4xx(client, url):
    resp = client.get(url)
    assert resp.status_code == 200, (url, resp.status_code)


# ── Endpoint: never-5xx (monkeypatched blowup) ────────────────────────────


def test_endpoint_never_5xx_on_body_builder_blowup(client, ent, monkeypatch):
    from routes import entitlement as _routes

    def _boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(_routes, "_has_all_at_batch_body", _boom)
    resp = client.get(
        "/api/entitlement/has-all-at-batch?tiers=oss,bogus&features=fleet"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    # Fallback envelope shape stable.
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS
    assert body["tiers"] == []
    assert body["unknown_tiers"] == ["oss", "bogus"]
    assert body["unknown_features"] == ["fleet"]
    assert body["all_allowed"] is False
    assert body["any_allowed"] is False


def test_endpoint_never_5xx_on_scalar_blowup(client, ent, monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "has_all_at_batch", _boom)
    resp = client.get(
        "/api/entitlement/has-all-at-batch?tiers=oss,cloud_pro&features=fleet"
    )
    # The endpoint call site swallows the RuntimeError into the fallback
    # envelope because ``has_all_at_batch`` is imported inside the body
    # builder each request (via ``from clawmetry import entitlements``).
    # Either way: 200 with envelope stable.
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) == _ENDPOINT_ENVELOPE_KEYS


# ── Endpoint: scalar-vs-endpoint parity ───────────────────────────────────


def test_endpoint_row_parity_with_scalar(client, ent):
    body = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss,cloud_starter,cloud_pro,enterprise"
        "&features=fleet&channels=100",
    )
    # Reconstruct known values the endpoint would pass to the scalar.
    for row in body["tiers"]:
        assert row["has_all_at"] == ent.has_all_at(
            row["tier"], features=["fleet"], channels=100
        ), row


# ── Cross-endpoint: parity with /has-all-at ───────────────────────────────


def test_cross_endpoint_row_parity_with_has_all_at(client):
    for tier in ("oss", "cloud_starter", "cloud_pro", "enterprise"):
        one = _get_json(
            client,
            f"/api/entitlement/has-all-at?tier={tier}"
            "&features=fleet&channels=100",
        )
        batch = _get_json(
            client,
            f"/api/entitlement/has-all-at-batch?tiers={tier}"
            "&features=fleet&channels=100",
        )
        assert (
            batch["tiers"][0]["has_all_at"] == one["has_all_at"]
        ), (tier, batch["tiers"][0], one)


# ── Cross-endpoint: parity with /has-features-at-batch on single axis ─────


def test_cross_endpoint_features_axis_parity(client):
    body_all = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss,cloud_pro,enterprise&features=fleet",
    )
    body_features = _get_json(
        client,
        "/api/entitlement/has-features-at-batch?tiers=oss,cloud_pro,enterprise&features=fleet",
    )
    for row_all, row_feat in zip(body_all["tiers"], body_features["tiers"]):
        assert row_all["tier"] == row_feat["tier"]
        assert row_all["has_all_at"] == row_feat["has_features_at"], (
            row_all,
            row_feat,
        )


def test_cross_endpoint_runtimes_axis_parity(client):
    body_all = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss,cloud_pro,enterprise&runtimes=claude_code",
    )
    body_runtimes = _get_json(
        client,
        "/api/entitlement/has-runtimes-at-batch?tiers=oss,cloud_pro,enterprise&runtimes=claude_code",
    )
    for row_all, row_rt in zip(body_all["tiers"], body_runtimes["tiers"]):
        assert row_all["tier"] == row_rt["tier"]
        assert row_all["has_all_at"] == row_rt["has_runtimes_at"], (
            row_all,
            row_rt,
        )


# ── Deliberate divergence from LIVE /has-all in grace ─────────────────────


def test_endpoint_diverges_from_live_has_all_on_oss_paid_feature(client):
    """The LIVE ``/has-all`` grants any fully-known bundle in grace via
    the resolver pass-through, but ``/has-all-at-batch`` reads the
    static per-tier tables and reports ``has_all_at=false`` on the OSS
    row for a paid feature -- that's the whole point of the ``_at``
    slot."""
    body_at_batch = _get_json(
        client,
        "/api/entitlement/has-all-at-batch?tiers=oss&features=fleet",
    )
    body_live = _get_json(
        client, "/api/entitlement/has-all?features=fleet"
    )
    assert body_live["has_all"] is True  # grace grants it live
    assert body_at_batch["tiers"][0]["has_all_at"] is False  # static OSS denies


# ── Resolver envelope carried on the endpoint ─────────────────────────────


def test_endpoint_carries_resolver_envelope_in_grace(client):
    body = _get_json(
        client, "/api/entitlement/has-all-at-batch?tiers=oss&features=fleet"
    )
    assert body["grace"] is True
    assert body["enforced"] is False
    assert body["current_tier"] == "oss"
    assert body["current_tier_rank"] == 0


# ── Sanity: retention_days=None on kwarg semantics ───────────────────────


def test_scalar_retention_none_unset_not_unlimited(ent):
    # Passing retention_days=None means "unset" (skipped); doesn't
    # collapse the fold or route to Enterprise-only.
    r_none = ent.has_all_at_batch(["oss"], retention_days=None)
    r_zero = ent.has_all_at_batch(["oss"], retention_days=0)
    # None -> no axis supplied -> row False (empty-False posture).
    assert r_none["tiers"][0]["has_all_at"] is False
    # 0 -> supplied and trivially satisfied at OSS.
    assert r_zero["tiers"][0]["has_all_at"] is True
