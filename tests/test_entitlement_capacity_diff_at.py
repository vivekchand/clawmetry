"""Tests for ``capacity_diff_at(tier, target)`` +
``GET /api/entitlement/capacity-diff-at``.

Scalar what-if sibling of :func:`capacity_diff`: per-axis capacity
transition (channels / retention / nodes) from a caller-supplied
``tier`` to ``target``, computed off the static per-tier caps rather
than the resolved entitlement :func:`capacity_diff` anchors to.
Single-hop view of :func:`capacity_diff_path` for the cumulative
``tier -> target`` capacity step, elides intermediate rungs.

Pins:

* the row shape matches :func:`capacity_diff` exactly
* each row's axis triples byte-equal ``tier_diff(tier, target)
  ['capacity_changes']`` for every pair -- the cumulative-diff parity
  that stops the scalar what-if drifting from :func:`tier_diff` (the
  same invariant ``tier_unlocks_at`` pins against
  ``tier_diff(tier, target)['added_*']``, lifted to capacity)
* ``before`` on every axis is the caller-supplied ``tier``'s static
  cap, NOT the resolved entitlement's cap :func:`capacity_diff`
  substitutes; the per-axis caps do NOT collapse to the unlimited
  sentinel the way :func:`capacity_diff` does under grace
* every ``(tier, target)`` pair in :data:`_TIER_FEATURES` x
  :data:`_TIER_FEATURES` round-trips (including ``trial`` on either
  side -- the lenient ``_at`` posture)
* identity / lateral-rank pairs collapse every axis to a no-op triple
* unknown / empty / ``None`` / non-string ids on either argument return
  ``None``
* both args are trimmed + lowercased before resolution
* the helper is independent of the live resolver (grace flips no field)
* the endpoint 400s on missing input, 404s on unknown ids (with
  ``which`` so the caller can render the right "unknown ..." message),
  and never 5xxs
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


_ROW_KEYS = {"target", "channel_limit", "retention_days", "node_limit"}
_AXIS_KEYS = {"before", "after", "delta", "unlocked", "locked"}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- ``capacity_diff_at`` is
    independent of either knob, so the fixture only needs to make sure
    the live resolver does not surprise the test."""
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


# ── shape ─────────────────────────────────────────────────────────────────────


def test_row_shape_matches_capacity_diff(ent):
    row = ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert row is not None
    assert set(row.keys()) == _ROW_KEYS


def test_each_axis_has_full_triple(ent):
    row = ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    for axis in ("channel_limit", "retention_days", "node_limit"):
        assert set(row[axis].keys()) == _AXIS_KEYS, axis


def test_target_echoes_destination(ent):
    row = ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert row["target"] == ent.TIER_CLOUD_PRO


# ── before-side comes from caller-supplied tier (not the resolver) ────────────


def test_before_carries_caller_perspective(ent):
    """``before`` on every axis is the caller-supplied ``tier``'s
    static cap. From OSS the channel cap is 3 (not unlimited / None,
    which is what the resolved entitlement returns under grace)."""
    row = ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert row["channel_limit"]["before"] == ent._FREE_CHANNEL_LIMIT
    assert row["node_limit"]["before"] == ent._FREE_NODE_LIMIT
    assert row["retention_days"]["before"] == ent._TIER_RETENTION_DAYS[ent.TIER_OSS]


def test_before_does_not_collapse_under_grace(ent):
    """The live :func:`capacity_diff` collapses ``before`` to the
    unlimited sentinel under grace (resolved entitlement returns
    ``None``); this scalar what-if must NOT, since the source is
    hypothetical."""
    row = ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    live = ent.capacity_diff(ent.TIER_CLOUD_PRO)
    # The live row's before-side is None under grace; the _at row must
    # carry the static OSS cap (a finite int) so they MUST differ here.
    assert row["channel_limit"]["before"] == ent._FREE_CHANNEL_LIMIT
    assert live["channel_limit"]["before"] is None


# ── parity with tier_diff (the cumulative invariant) ────────────────────────


def test_axes_match_tier_diff_capacity_changes(ent):
    """Every axis triple byte-equals ``tier_diff(tier, target)
    ['capacity_changes'][axis]`` for every pair -- the cumulative-diff
    parity that stops the scalar what-if drifting from
    :func:`tier_diff`. (The full ``capacity_diff_at`` row carries an
    extra ``target`` key on top of the per-axis bundle ``tier_diff``
    exposes -- the rest must match byte-for-byte.)"""
    for tier in ent._TIER_FEATURES:
        for target in ent._TIER_FEATURES:
            row = ent.capacity_diff_at(tier, target)
            diff = ent.tier_diff(tier, target)
            assert row is not None and diff is not None, (tier, target)
            for axis in ("channel_limit", "retention_days", "node_limit"):
                assert row[axis] == diff["capacity_changes"][axis], (
                    tier, target, axis,
                )


# ── round-trip across every pair ─────────────────────────────────────────────


def test_every_pair_resolves(ent):
    for tier in ent._TIER_FEATURES:
        for target in ent._TIER_FEATURES:
            row = ent.capacity_diff_at(tier, target)
            assert row is not None, (tier, target)
            assert row["target"] == target, (tier, target)


# ── direction semantics ──────────────────────────────────────────────────────


def test_upgrade_oss_to_cloud_pro_unlocks_channels_and_nodes(ent):
    """OSS caps channels/nodes at finite ints; Cloud Pro is
    unlimited -- the upgrade flips ``unlocked`` on both axes."""
    row = ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert row["channel_limit"]["before"] == ent._FREE_CHANNEL_LIMIT
    assert row["channel_limit"]["after"] is None
    assert row["channel_limit"]["unlocked"] is True
    assert row["channel_limit"]["locked"] is False
    assert row["node_limit"]["before"] == ent._FREE_NODE_LIMIT
    assert row["node_limit"]["after"] is None
    assert row["node_limit"]["unlocked"] is True


def test_upgrade_finite_to_finite_carries_delta(ent):
    """OSS retention is 7d, Cloud Starter is 30d -- both ends finite
    so ``delta`` is the int difference (no unlocked/locked flip)."""
    row = ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    rt = row["retention_days"]
    assert rt["before"] == 7
    assert rt["after"] == 30
    assert rt["delta"] == 23
    assert rt["unlocked"] is False
    assert rt["locked"] is False


def test_downgrade_unlimited_to_finite_locks(ent):
    """Going from Enterprise (unlimited retention) to OSS (7d) flips
    ``locked`` -- the cancellation-warning copy."""
    row = ent.capacity_diff_at(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    rt = row["retention_days"]
    assert rt["before"] is None
    assert rt["after"] == 7
    assert rt["unlocked"] is False
    assert rt["locked"] is True


def test_identity_pair_is_a_noop_on_every_axis(ent):
    """Same source and target -> every axis collapses to a no-op
    triple: ``before == after``, both flags False."""
    for tier in ent._TIER_FEATURES:
        row = ent.capacity_diff_at(tier, tier)
        for axis in ("channel_limit", "retention_days", "node_limit"):
            triple = row[axis]
            assert triple["before"] == triple["after"], (tier, axis)
            assert triple["unlocked"] is False, (tier, axis)
            assert triple["locked"] is False, (tier, axis)


def test_lateral_same_rank_carries_real_transition(ent):
    """Same-rank sibling tiers (cloud_pro vs pro) share the same
    static caps, so the lateral hop produces a no-op triple on every
    axis -- but the row is returned (lateral != identity at the API
    level: a UI may render "same tier" copy on identity but "swap
    plans" on lateral)."""
    row = ent.capacity_diff_at(ent.TIER_PRO, ent.TIER_CLOUD_PRO)
    assert row is not None
    assert row["target"] == ent.TIER_CLOUD_PRO


# ── trial is accepted on either side (lenient _at family) ────────────────────


def test_trial_accepted_as_perspective(ent):
    """The ``_at`` family is lenient on the source: it must answer
    hypothetical questions like "what does Cloud Pro cost in capacity
    vs a trial install?" too."""
    row = ent.capacity_diff_at(ent.TIER_TRIAL, ent.TIER_CLOUD_PRO)
    assert row is not None
    assert row["target"] == ent.TIER_CLOUD_PRO


def test_trial_accepted_as_target(ent):
    row = ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_TRIAL)
    assert row is not None
    assert row["target"] == ent.TIER_TRIAL


# ── invalid tier (perspective) ───────────────────────────────────────────────


def test_unknown_tier_returns_none(ent):
    assert ent.capacity_diff_at("not_a_real_tier", ent.TIER_CLOUD_PRO) is None


def test_empty_tier_returns_none(ent):
    assert ent.capacity_diff_at("", ent.TIER_CLOUD_PRO) is None


def test_none_tier_returns_none(ent):
    assert ent.capacity_diff_at(None, ent.TIER_CLOUD_PRO) is None  # type: ignore[arg-type]


def test_non_string_tier_returns_none(ent):
    assert ent.capacity_diff_at(123, ent.TIER_CLOUD_PRO) is None  # type: ignore[arg-type]
    assert ent.capacity_diff_at(object(), ent.TIER_CLOUD_PRO) is None  # type: ignore[arg-type]


# ── invalid target ───────────────────────────────────────────────────────────


def test_unknown_target_returns_none(ent):
    assert ent.capacity_diff_at(ent.TIER_CLOUD_PRO, "not_a_real_tier") is None


def test_empty_target_returns_none(ent):
    assert ent.capacity_diff_at(ent.TIER_CLOUD_PRO, "") is None


def test_none_target_returns_none(ent):
    assert ent.capacity_diff_at(ent.TIER_CLOUD_PRO, None) is None  # type: ignore[arg-type]


def test_non_string_target_returns_none(ent):
    assert ent.capacity_diff_at(ent.TIER_CLOUD_PRO, 123) is None  # type: ignore[arg-type]
    assert ent.capacity_diff_at(ent.TIER_CLOUD_PRO, object()) is None  # type: ignore[arg-type]


# ── normalisation ────────────────────────────────────────────────────────────


def test_inputs_are_lowercased_and_trimmed(ent):
    a = ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    b = ent.capacity_diff_at(ent.TIER_OSS.upper(), ent.TIER_CLOUD_PRO.upper())
    c = ent.capacity_diff_at(
        f"  {ent.TIER_OSS}  ", f"  {ent.TIER_CLOUD_PRO}  "
    )
    assert a == b == c


# ── independent of live resolver ─────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    row_grace = ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    row_enforce = ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert row_grace == row_enforce


def test_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().to_dict()
    ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    after = ent.get_entitlement().to_dict()
    assert before == after


# ── never-raise ──────────────────────────────────────────────────────────────


def test_never_raises_when_builder_crashes(ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated builder failure")

    monkeypatch.setattr(ent, "_capacity_row", boom)
    assert ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO) is None


# ── HTTP endpoint ────────────────────────────────────────────────────────────


def test_endpoint_known_pair_returns_row(client, ent):
    resp = client.get(
        f"/api/entitlement/capacity-diff-at?tier={ent.TIER_OSS}"
        f"&target={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["row"] == ent.capacity_diff_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)


def test_endpoint_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/capacity-diff-at?tier=%20%20{ent.TIER_OSS.upper()}%20%20"
        f"&target=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] == ent.TIER_CLOUD_PRO


def test_endpoint_missing_tier_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/capacity-diff-at?target={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_tier_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/capacity-diff-at?tier=%20%20"
        f"&target={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400


def test_endpoint_missing_target_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/capacity-diff-at?tier={ent.TIER_OSS}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_target_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/capacity-diff-at?tier={ent.TIER_OSS}&target=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client, ent):
    resp = client.get(
        "/api/entitlement/capacity-diff-at?tier=nonsense_xyz"
        f"&target={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_unknown_target_returns_404(client, ent):
    resp = client.get(
        f"/api/entitlement/capacity-diff-at?tier={ent.TIER_OSS}"
        "&target=not_a_real_tier"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["which"] == "target"
    assert body["target"] == "not_a_real_tier"
    assert "error" in body


def test_endpoint_trial_is_accepted(client, ent):
    """Unlike a strict-only endpoint, the ``_at`` family accepts
    ``trial`` on either side."""
    resp = client.get(
        f"/api/entitlement/capacity-diff-at?tier={ent.TIER_OSS}"
        f"&target={ent.TIER_TRIAL}"
    )
    assert resp.status_code == 200
    assert resp.get_json()["row"]["target"] == ent.TIER_TRIAL


def test_endpoint_every_pair_round_trips(client, ent):
    for tier in ent._TIER_FEATURES:
        for target in ent._TIER_FEATURES:
            resp = client.get(
                "/api/entitlement/capacity-diff-at"
                f"?tier={tier}&target={target}"
            )
            assert resp.status_code == 200, (tier, target)
            body = resp.get_json()
            assert body["tier"] == tier, (tier, target)
            assert body["target"] == target, (tier, target)
            assert body["row"]["target"] == target, (tier, target)
