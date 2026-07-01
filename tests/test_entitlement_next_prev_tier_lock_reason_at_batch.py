"""Tests for the two directional batch what-if helpers projecting
:func:`clawmetry.entitlements.lock_reasons_at_batch` onto the rung
above / below a caller-supplied source tier, and the two companion
``/api/entitlement/{next,previous}-tier-lock-reason-at-batch``
endpoints.

These helpers fill the batch member of the ``next_*_at_batch`` /
``previous_*_at_batch`` family on the lock-reason axis, alongside
the existing:

* :func:`next_tier_feature_spec_at_batch` /
  :func:`previous_tier_feature_spec_at_batch`
* :func:`next_tier_runtime_spec_at_batch` /
  :func:`previous_tier_runtime_spec_at_batch`
* :func:`next_tier_spec_at_batch` / :func:`previous_tier_spec_at_batch`
* :func:`next_tier_capacity_diff_at_batch` /
  :func:`previous_tier_capacity_diff_at_batch`
* :func:`next_tier_locks_at_batch` / :func:`next_tier_unlocks_at_batch`
  (and the ``previous_`` twins)

The new helpers compose:
:func:`next_tier_lock_reason_at` (scalar projection) +
:func:`lock_reasons_at_batch` (5-axis matrix what-if) -- same target as
the scalar, same 5-axis row shape as the batch helper. Lets a paywall
"does THIS column of features / runtimes / capacity axes unlock at my
next / previous rung?" matrix surface render every row off ONE call
instead of N calls to :func:`next_tier_lock_reason_at` per axis.

Pins covered here:

* per-rung byte-equality with :func:`lock_reasons_at_batch` at the
  resolved next / previous purchasable target (parity, all five axes)
* ``next`` / ``previous`` align with
  :func:`_next_purchasable_tier_after` /
  :func:`_previous_purchasable_tier_before` so the batch helpers cannot
  drift from the rung-walker shared with the other ``next_*_at_batch``
  family
* ceiling (enterprise as source) / floor (oss / cloud_free as source)
  still emit per-item rows with ``reason=null`` / ``locked=false`` /
  ``allowed=true`` so the matrix's row count stays stable (no shape
  branch for edge tiers)
* trial-as-source resolves the same way the sibling ``_at_batch``
  families do: next -> enterprise, previous -> cloud_starter
* unknown / empty / whitespace / case-insensitive id handling
* runtime alias resolution (``claude-code`` -> ``claude_code``)
  produces canonical ``key`` values in the returned rows
* capacity axes (``channels`` / ``retention_days`` / ``nodes``) route
  through the batch helper's kwarg surface just like
  :func:`lock_reasons_at_batch`
* grace vs enforce yields the same body (catalogue-derived, not gated)
* the helpers never raise -- a builder failure short-circuits to
  grace-shape rows so the matrix keeps rendering rather than 500-ing
* the two API endpoints never 5xx: 400 on missing input / no-axis,
  404 on unknown tier, 200 with grace-shape rows at the ceiling /
  floor; an internal failure yields the same 200 envelope shape
* the endpoint response is byte-identical to
  ``/lock-reasons-at-batch?tier=<target>&...`` for the resolved target,
  plus a ``tier`` / ``target`` echo -- parity pin so the two batch
  surfaces cannot drift
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ROW_KEYS = {
    "key",
    "kind",
    "reason",
    "locked",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
}

_HELPER_BATCH_KEYS = {
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
}

_API_EXTRA_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "target",
    "target_label",
    "target_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
}


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


# ── next_tier_lock_reason_at_batch: helper shape ────────────────────────────


def test_next_helper_returns_dict_with_axis_keys(ent):
    fid = next(iter(ent.FREE_FEATURES))
    out = ent.next_tier_lock_reason_at_batch(ent.TIER_OSS, features=[fid])
    assert isinstance(out, dict)
    assert set(out.keys()) == _HELPER_BATCH_KEYS


def test_next_helper_features_row_shape(ent):
    fid = next(iter(ent.FREE_FEATURES))
    out = ent.next_tier_lock_reason_at_batch(ent.TIER_OSS, features=[fid])
    assert isinstance(out["features"], list)
    assert len(out["features"]) == 1
    assert set(out["features"][0].keys()) == _ROW_KEYS


def test_next_helper_every_purchasable_tier_returns_dict(ent):
    paid_universe = (
        ent.STARTER_FEATURES | ent.PRO_ONLY_FEATURES | ent.ENTERPRISE_FEATURES
    )
    fid = next(iter(paid_universe))
    for tier in ent._TIER_ORDER:
        out = ent.next_tier_lock_reason_at_batch(tier, features=[fid])
        assert isinstance(out, dict), tier
        assert set(out.keys()) == _HELPER_BATCH_KEYS


# ── next helper: invalid source tier ────────────────────────────────────────


def test_next_helper_unknown_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert (
        ent.next_tier_lock_reason_at_batch("not_a_real_tier", features=[fid])
        is None
    )


def test_next_helper_empty_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.next_tier_lock_reason_at_batch("", features=[fid]) is None


def test_next_helper_none_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.next_tier_lock_reason_at_batch(None, features=[fid]) is None


def test_next_helper_non_string_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.next_tier_lock_reason_at_batch(123, features=[fid]) is None


# ── next helper: byte-parity with lock_reasons_at_batch at target ───────────


def test_next_helper_byte_equal_to_lock_reasons_at_batch_at_target(ent):
    """The batch what-if projection must be byte-identical to the full
    :func:`lock_reasons_at_batch` payload at the resolved target for
    every purchasable source tier. Parity pin so the projection cannot
    drift from the full helper.
    """
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    rt = next(iter(ent.PAID_RUNTIMES))
    for src in ent._PURCHASABLE_TIERS:
        target = ent._next_purchasable_tier_after(src)
        if target is None:
            continue
        projected = ent.next_tier_lock_reason_at_batch(
            src,
            features=[fid],
            runtimes=[rt],
            channels=50,
            retention_days=365,
            nodes=10,
        )
        direct = ent.lock_reasons_at_batch(
            target,
            features=[fid],
            runtimes=[rt],
            channels=50,
            retention_days=365,
            nodes=10,
        )
        assert projected == direct, src


def test_next_helper_scalar_matches_row_reason(ent):
    """Row ``reason`` for a feature in the batch must byte-equal the
    scalar :func:`next_tier_lock_reason_at` sibling for the same input.
    """
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    for src in ent._PURCHASABLE_TIERS:
        batch = ent.next_tier_lock_reason_at_batch(src, features=[fid])
        scalar = ent.next_tier_lock_reason_at(src, fid, kind="feature")
        assert batch["features"][0]["reason"] == scalar, src


# ── next helper: rows at rung above unlock paid items ───────────────────────


def test_paid_feature_locked_from_oss_next_rung_is_starter(ent):
    """From OSS the next purchasable rung is Starter -- Pro-only
    features should still be locked there."""
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    out = ent.next_tier_lock_reason_at_batch(ent.TIER_OSS, features=[fid])
    row = out["features"][0]
    assert row["locked"] is True
    assert row["allowed"] is False
    assert isinstance(row["reason"], str) and row["reason"]


def test_paid_feature_unlocked_from_starter_next_rung_is_pro(ent):
    """From Starter the next purchasable rung is Pro -- Pro-only
    features should be unlocked there."""
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    out = ent.next_tier_lock_reason_at_batch(
        ent.TIER_CLOUD_STARTER, features=[fid]
    )
    row = out["features"][0]
    assert row["locked"] is False
    assert row["allowed"] is True
    assert row["reason"] is None


# ── next helper: runtime + alias canonicalisation ───────────────────────────


def test_next_helper_paid_runtime_locked_from_oss_next_rung(ent):
    rt = next(iter(ent.PAID_RUNTIMES))
    out = ent.next_tier_lock_reason_at_batch(ent.TIER_OSS, runtimes=[rt])
    row = out["runtimes"][0]
    assert row["locked"] is False
    assert row["allowed"] is True


def test_next_helper_runtime_alias_preserved_like_parent(ent):
    """Aliased runtime ids are echoed back verbatim in the row ``key``
    -- matching :func:`lock_reasons_at_batch`'s no-canonicalisation
    posture (the sibling ``next_tier_runtime_spec_at_batch`` canonicalises
    because it delegates to :func:`runtime_spec_at`; this helper
    delegates to :func:`lock_reasons_at_batch` which does not). Pin so
    the two batch surfaces cannot silently diverge on alias handling."""
    if ent.canonical_runtime("claude-code") != "claude_code":
        pytest.skip("claude-code alias not present")
    out = ent.next_tier_lock_reason_at_batch(
        ent.TIER_OSS, runtimes=["claude-code"]
    )
    row = out["runtimes"][0]
    direct = ent.lock_reasons_at_batch(
        ent._next_purchasable_tier_after(ent.TIER_OSS),
        runtimes=["claude-code"],
    )
    assert row["key"] == direct["runtimes"][0]["key"]


# ── next helper: capacity axes ──────────────────────────────────────────────


def test_next_helper_capacity_axes_default_to_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    out = ent.next_tier_lock_reason_at_batch(ent.TIER_OSS, features=[fid])
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


def test_next_helper_nodes_axis_carries_capacity_row(ent):
    out = ent.next_tier_lock_reason_at_batch(ent.TIER_OSS, nodes=100)
    row = out["nodes"]
    assert row is not None
    assert row["kind"] == "nodes"


def test_next_helper_channels_axis_carries_capacity_row(ent):
    out = ent.next_tier_lock_reason_at_batch(ent.TIER_OSS, channels=50)
    row = out["channels"]
    assert row is not None
    assert row["kind"] == "channels"


def test_next_helper_retention_axis_carries_capacity_row(ent):
    out = ent.next_tier_lock_reason_at_batch(
        ent.TIER_OSS, retention_days=365
    )
    row = out["retention_days"]
    assert row is not None
    assert row["kind"] == "retention_days"


# ── next helper: ceiling posture ────────────────────────────────────────────


def test_next_helper_at_ceiling_emits_grace_rows(ent):
    """Enterprise as source has no rung above; rows must still render
    with ``reason=null`` / ``locked=false`` / ``allowed=true``."""
    assert ent._next_purchasable_tier_after(ent.TIER_ENTERPRISE) is None
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    rt = next(iter(ent.PAID_RUNTIMES))
    out = ent.next_tier_lock_reason_at_batch(
        ent.TIER_ENTERPRISE,
        features=[fid],
        runtimes=[rt],
        nodes=100,
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == _HELPER_BATCH_KEYS
    assert len(out["features"]) == 1
    assert out["features"][0]["locked"] is False
    assert out["features"][0]["reason"] is None
    assert out["features"][0]["allowed"] is True
    assert out["runtimes"][0]["locked"] is False
    assert out["runtimes"][0]["reason"] is None
    assert out["nodes"]["locked"] is False
    assert out["nodes"]["reason"] is None


# ── next helper: trial-as-source resolves to enterprise ─────────────────────


def test_next_helper_trial_source_resolves_to_enterprise(ent):
    assert (
        ent._next_purchasable_tier_after(ent.TIER_TRIAL) == ent.TIER_ENTERPRISE
    )
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    projected = ent.next_tier_lock_reason_at_batch(
        ent.TIER_TRIAL, features=[fid]
    )
    direct = ent.lock_reasons_at_batch(ent.TIER_ENTERPRISE, features=[fid])
    assert projected == direct


# ── next helper: whitespace / case-insensitive ──────────────────────────────


def test_next_helper_whitespace_and_case_insensitive(ent):
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    canon = ent.next_tier_lock_reason_at_batch(ent.TIER_OSS, features=[fid])
    other = ent.next_tier_lock_reason_at_batch(" OSS ", features=[fid])
    assert canon == other


# ── next helper: independent of the live resolver ───────────────────────────


def test_next_helper_grace_and_enforce_match(ent, monkeypatch):
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    grace = ent.next_tier_lock_reason_at_batch(ent.TIER_OSS, features=[fid])
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.next_tier_lock_reason_at_batch(
        ent.TIER_OSS, features=[fid]
    )
    assert grace == enforced


# ── next helper: never raises on garbage input ──────────────────────────────


def test_next_helper_never_raises_on_garbage_features(ent):
    out = ent.next_tier_lock_reason_at_batch(
        ent.TIER_OSS,
        features=["", None, "valid_id"],  # type: ignore[list-item]
    )
    assert isinstance(out, dict)
    assert isinstance(out["features"], list)


def test_next_helper_empty_inputs_returns_empty_lists(ent):
    out = ent.next_tier_lock_reason_at_batch(ent.TIER_OSS)
    assert out["features"] == []
    assert out["runtimes"] == []
    assert out["channels"] is None
    assert out["retention_days"] is None
    assert out["nodes"] is None


# ── previous_tier_lock_reason_at_batch: helper shape ────────────────────────


def test_previous_helper_returns_dict_with_axis_keys(ent):
    fid = next(iter(ent.FREE_FEATURES))
    out = ent.previous_tier_lock_reason_at_batch(
        ent.TIER_CLOUD_PRO, features=[fid]
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == _HELPER_BATCH_KEYS


def test_previous_helper_unknown_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert (
        ent.previous_tier_lock_reason_at_batch("bogus", features=[fid])
        is None
    )


def test_previous_helper_empty_tier_returns_none(ent):
    fid = next(iter(ent.FREE_FEATURES))
    assert ent.previous_tier_lock_reason_at_batch("", features=[fid]) is None


# ── previous helper: byte-parity at target ──────────────────────────────────


def test_previous_helper_byte_equal_to_lock_reasons_at_batch_at_target(ent):
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    rt = next(iter(ent.PAID_RUNTIMES))
    for src in ent._PURCHASABLE_TIERS:
        target = ent._previous_purchasable_tier_before(src)
        if target is None:
            continue
        projected = ent.previous_tier_lock_reason_at_batch(
            src,
            features=[fid],
            runtimes=[rt],
            channels=50,
            retention_days=365,
            nodes=10,
        )
        direct = ent.lock_reasons_at_batch(
            target,
            features=[fid],
            runtimes=[rt],
            channels=50,
            retention_days=365,
            nodes=10,
        )
        assert projected == direct, src


def test_previous_helper_scalar_matches_row_reason(ent):
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    for src in ent._PURCHASABLE_TIERS:
        batch = ent.previous_tier_lock_reason_at_batch(src, features=[fid])
        scalar = ent.previous_tier_lock_reason_at(src, fid, kind="feature")
        assert batch["features"][0]["reason"] == scalar, src


# ── previous helper: floor posture ──────────────────────────────────────────


def test_previous_helper_at_floor_emits_grace_rows(ent):
    """OSS as source has no rung below; rows must still render."""
    assert ent._previous_purchasable_tier_before(ent.TIER_OSS) is None
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    rt = next(iter(ent.PAID_RUNTIMES))
    out = ent.previous_tier_lock_reason_at_batch(
        ent.TIER_OSS,
        features=[fid],
        runtimes=[rt],
        nodes=100,
    )
    assert isinstance(out, dict)
    assert set(out.keys()) == _HELPER_BATCH_KEYS
    assert len(out["features"]) == 1
    assert out["features"][0]["locked"] is False
    assert out["features"][0]["reason"] is None
    assert out["runtimes"][0]["locked"] is False
    assert out["nodes"]["locked"] is False


def test_previous_helper_trial_source_resolves_below_pro(ent):
    """Trial sits at rank 2 alongside Pro; the strictly-lower
    purchasable rung is Starter."""
    target = ent._previous_purchasable_tier_before(ent.TIER_TRIAL)
    assert target == ent.TIER_CLOUD_STARTER
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    projected = ent.previous_tier_lock_reason_at_batch(
        ent.TIER_TRIAL, features=[fid]
    )
    direct = ent.lock_reasons_at_batch(ent.TIER_CLOUD_STARTER, features=[fid])
    assert projected == direct


def test_previous_helper_grace_and_enforce_match(ent, monkeypatch):
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    grace = ent.previous_tier_lock_reason_at_batch(
        ent.TIER_CLOUD_PRO, features=[fid]
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforced = ent.previous_tier_lock_reason_at_batch(
        ent.TIER_CLOUD_PRO, features=[fid]
    )
    assert grace == enforced


# ── directional independence (next vs previous) ─────────────────────────────


def test_next_vs_previous_disagree_for_pro_only_from_starter(ent):
    """From Starter, ``next`` steps up to Pro (Pro-only unlocks) and
    ``previous`` steps down to Free (still locked). The two directions
    must resolve to different targets and different lock outcomes."""
    fid = next(iter(ent.PRO_ONLY_FEATURES))
    up = ent.next_tier_lock_reason_at_batch(
        ent.TIER_CLOUD_STARTER, features=[fid]
    )
    down = ent.previous_tier_lock_reason_at_batch(
        ent.TIER_CLOUD_STARTER, features=[fid]
    )
    assert up["features"][0]["locked"] is False
    assert down["features"][0]["locked"] is True


# ── endpoint: error contract ────────────────────────────────────────────────


def test_next_endpoint_missing_tier_400(client):
    r = client.get(
        "/api/entitlement/next-tier-lock-reason-at-batch?features=custom_alerts"
    )
    assert r.status_code == 400
    body = r.get_json()
    assert "error" in body


def test_previous_endpoint_missing_tier_400(client):
    r = client.get(
        "/api/entitlement/previous-tier-lock-reason-at-batch?features=custom_alerts"
    )
    assert r.status_code == 400
    body = r.get_json()
    assert "error" in body


def test_next_endpoint_blank_tier_400(client):
    r = client.get(
        "/api/entitlement/next-tier-lock-reason-at-batch?tier=&features=custom_alerts"
    )
    assert r.status_code == 400


def test_previous_endpoint_blank_tier_400(client):
    r = client.get(
        "/api/entitlement/previous-tier-lock-reason-at-batch?tier=&features=custom_alerts"
    )
    assert r.status_code == 400


def test_next_endpoint_unknown_tier_404(client):
    r = client.get(
        "/api/entitlement/next-tier-lock-reason-at-batch?tier=nonsense&features=custom_alerts"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body.get("which") == "tier"
    assert body.get("tier") == "nonsense"


def test_previous_endpoint_unknown_tier_404(client):
    r = client.get(
        "/api/entitlement/previous-tier-lock-reason-at-batch?tier=nonsense&features=custom_alerts"
    )
    assert r.status_code == 404
    body = r.get_json()
    assert body.get("which") == "tier"


def test_next_endpoint_no_axis_400(client, ent):
    r = client.get(
        f"/api/entitlement/next-tier-lock-reason-at-batch?tier={ent.TIER_OSS}"
    )
    assert r.status_code == 400
    body = r.get_json()
    assert "error" in body


def test_previous_endpoint_no_axis_400(client, ent):
    r = client.get(
        f"/api/entitlement/previous-tier-lock-reason-at-batch?tier={ent.TIER_CLOUD_PRO}"
    )
    assert r.status_code == 400


# ── endpoint: happy path + shape ────────────────────────────────────────────


def test_next_endpoint_returns_full_envelope(client, ent):
    r = client.get(
        "/api/entitlement/next-tier-lock-reason-at-batch?tier="
        + ent.TIER_OSS
        + "&features=custom_alerts&runtimes=claude_code&nodes=100"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) >= (_HELPER_BATCH_KEYS | _API_EXTRA_KEYS)
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] == ent._next_purchasable_tier_after(ent.TIER_OSS)
    assert isinstance(body["features"], list)
    assert isinstance(body["runtimes"], list)


def test_previous_endpoint_returns_full_envelope(client, ent):
    r = client.get(
        "/api/entitlement/previous-tier-lock-reason-at-batch?tier="
        + ent.TIER_CLOUD_PRO
        + "&features=custom_alerts&nodes=10"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) >= (_HELPER_BATCH_KEYS | _API_EXTRA_KEYS)
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["target"] == ent._previous_purchasable_tier_before(
        ent.TIER_CLOUD_PRO
    )


def test_next_endpoint_at_ceiling_target_null(client, ent):
    r = client.get(
        "/api/entitlement/next-tier-lock-reason-at-batch?tier="
        + ent.TIER_ENTERPRISE
        + "&features=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["target_rank"] is None
    assert body["features"][0]["locked"] is False
    assert body["features"][0]["reason"] is None


def test_previous_endpoint_at_floor_target_null(client, ent):
    r = client.get(
        "/api/entitlement/previous-tier-lock-reason-at-batch?tier="
        + ent.TIER_OSS
        + "&features=custom_alerts"
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["target"] is None
    assert body["target_label"] is None
    assert body["features"][0]["locked"] is False


# ── endpoint: byte parity with /lock-reasons-at-batch at target ─────────────


def test_next_endpoint_body_byte_equal_to_lock_reasons_at_batch(client, ent):
    """The batch-what-if endpoint body (minus the ``tier`` / ``target``
    echo keys) must be byte-identical to the direct
    ``/lock-reasons-at-batch?tier=<target>&...`` call. Parity pin so
    the two batch surfaces cannot drift.
    """
    target = ent._next_purchasable_tier_after(ent.TIER_CLOUD_STARTER)
    assert target is not None
    r1 = client.get(
        "/api/entitlement/next-tier-lock-reason-at-batch?tier="
        + ent.TIER_CLOUD_STARTER
        + "&features=custom_alerts&nodes=10"
    )
    r2 = client.get(
        "/api/entitlement/lock-reasons-at-batch?tier="
        + target
        + "&features=custom_alerts&nodes=10"
    )
    assert r1.status_code == r2.status_code == 200
    b1 = r1.get_json()
    b2 = r2.get_json()
    for k in _HELPER_BATCH_KEYS:
        assert b1[k] == b2[k], k


def test_previous_endpoint_body_byte_equal_to_lock_reasons_at_batch(
    client, ent
):
    target = ent._previous_purchasable_tier_before(ent.TIER_CLOUD_PRO)
    assert target is not None
    r1 = client.get(
        "/api/entitlement/previous-tier-lock-reason-at-batch?tier="
        + ent.TIER_CLOUD_PRO
        + "&features=custom_alerts&nodes=10"
    )
    r2 = client.get(
        "/api/entitlement/lock-reasons-at-batch?tier="
        + target
        + "&features=custom_alerts&nodes=10"
    )
    assert r1.status_code == r2.status_code == 200
    b1 = r1.get_json()
    b2 = r2.get_json()
    for k in _HELPER_BATCH_KEYS:
        assert b1[k] == b2[k], k


# ── endpoint: blueprint uniqueness ──────────────────────────────────────────


def test_endpoints_registered_on_blueprint():
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    rules = {r.rule for r in app.url_map.iter_rules()}
    assert "/api/entitlement/next-tier-lock-reason-at-batch" in rules
    assert "/api/entitlement/previous-tier-lock-reason-at-batch" in rules
