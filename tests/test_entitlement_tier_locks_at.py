"""Tests for ``tier_locks_at(tier, target)`` +
``GET /api/entitlement/tier-locks-at``.

Marginal-loss mirror of :func:`tier_unlocks_at`. Scalar what-if sibling of
:func:`tier_locks`: marginal losses for ``target`` computed against the
caller-supplied ``tier`` rather than the global next-higher-purchasable-tier
anchor :func:`tier_locks` uses.

Pins:

* the row shape matches :func:`tier_locks` exactly
* ``lost_features`` / ``lost_runtimes`` byte-equal
  ``tier_diff(tier, target)``'s ``lost_features`` / ``lost_runtimes`` for
  every pair -- the parity test that stops the scalar what-if drifting
  from the cumulative diff
* ``next_tier`` always echoes the caller-supplied ``tier`` (the rung
  you're stepping FROM), NOT the global anchor :func:`tier_locks`
  substitutes
* upgrade and identity pairs collapse to empty loss lists -- you lose
  nothing going up or staying put
* every ``(tier, target)`` pair in :data:`_TIER_ORDER` x :data:`_TIER_ORDER`
  round-trips (including ``trial`` on either side -- the ``_at`` family
  is lenient where :func:`tier_locks` rejects ``trial``)
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


_ROW_KEYS = {
    "tier",
    "tier_label",
    "tier_rank",
    "next_tier",
    "next_tier_label",
    "next_tier_rank",
    "lost_features",
    "lost_runtimes",
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


# ── shape ─────────────────────────────────────────────────────────────────────


def test_row_shape_matches_tier_locks(ent):
    row = ent.tier_locks_at(ent.TIER_CLOUD_PRO, ent.TIER_OSS)
    assert row is not None
    assert set(row.keys()) == _ROW_KEYS


def test_tier_metadata_matches_target(ent):
    row = ent.tier_locks_at(ent.TIER_CLOUD_PRO, ent.TIER_OSS)
    assert row["tier"] == ent.TIER_OSS
    assert row["tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert row["tier_rank"] == ent.tier_rank(ent.TIER_OSS)


def test_next_tier_echoes_caller_perspective(ent):
    """``next_tier`` is the caller-supplied ``tier`` (the rung you're
    stepping FROM), NOT the global next-higher-purchasable anchor
    :func:`tier_locks` substitutes."""
    row = ent.tier_locks_at(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    assert row["next_tier"] == ent.TIER_ENTERPRISE
    assert row["next_tier_label"] == ent.tier_label(ent.TIER_ENTERPRISE)
    assert row["next_tier_rank"] == ent.tier_rank(ent.TIER_ENTERPRISE)
    # Differs from tier_locks(OSS), which anchors to CLOUD_STARTER (the
    # next-higher purchasable tier above OSS).
    live = ent.tier_locks(ent.TIER_OSS)
    assert live["next_tier"] == ent.TIER_CLOUD_STARTER


def test_lists_are_sorted(ent):
    row = ent.tier_locks_at(ent.TIER_CLOUD_PRO, ent.TIER_OSS)
    assert row["lost_features"] == sorted(row["lost_features"])
    assert row["lost_runtimes"] == sorted(row["lost_runtimes"])


# ── parity with tier_diff (the cumulative invariant) ─────────────────────────


def test_lost_features_match_tier_diff_lost_features(ent):
    """The loss lists byte-equal ``tier_diff(tier, target)['lost_*']``
    for every pair -- the parity that stops the scalar what-if drifting
    from the cumulative diff."""
    for tier in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            row = ent.tier_locks_at(tier, target)
            diff = ent.tier_diff(tier, target)
            assert row is not None and diff is not None, (tier, target)
            assert row["lost_features"] == diff["lost_features"], (tier, target)
            assert row["lost_runtimes"] == diff["lost_runtimes"], (tier, target)


# ── round-trip across every pair ─────────────────────────────────────────────


def test_every_pair_resolves(ent):
    for tier in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            row = ent.tier_locks_at(tier, target)
            assert row is not None, (tier, target)
            assert row["tier"] == target, (tier, target)
            assert row["next_tier"] == tier, (tier, target)


# ── direction semantics ──────────────────────────────────────────────────────


def test_downgrade_loses_full_paid_grant_to_oss(ent):
    row = ent.tier_locks_at(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    assert set(row["lost_features"]) == set(ent.PAID_FEATURES) | set(
        ent.ENTERPRISE_FEATURES
    )
    assert set(row["lost_runtimes"]) == set(ent.PAID_RUNTIMES)


def test_downgrade_cloud_pro_to_starter_loses_pro_only_features(ent):
    row = ent.tier_locks_at(ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER)
    assert set(row["lost_features"]) == set(ent.PRO_ONLY_FEATURES)
    # All paid runtimes still available at Starter -- no marginal loss.
    assert row["lost_runtimes"] == []


def test_downgrade_enterprise_to_cloud_pro_loses_enterprise_features(ent):
    row = ent.tier_locks_at(ent.TIER_ENTERPRISE, ent.TIER_CLOUD_PRO)
    assert set(row["lost_features"]) == set(ent.ENTERPRISE_FEATURES)
    assert row["lost_runtimes"] == []


def test_upgrade_loses_nothing(ent):
    """Going up a tier loses no features / runtimes."""
    row = ent.tier_locks_at(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert row["lost_features"] == []
    assert row["lost_runtimes"] == []


def test_identity_loses_nothing(ent):
    for tier in ent._TIER_ORDER:
        row = ent.tier_locks_at(tier, tier)
        assert row["lost_features"] == [], tier
        assert row["lost_runtimes"] == [], tier


def test_lateral_same_rank_loses_grant_diff(ent):
    """Same-rank sibling tiers (cloud_pro vs pro) share a grant set, so a
    lateral hop loses nothing."""
    row = ent.tier_locks_at(ent.TIER_CLOUD_PRO, ent.TIER_PRO)
    assert row["lost_features"] == []
    assert row["lost_runtimes"] == []


# ── mirror invariant with tier_unlocks_at ────────────────────────────────────


def test_swap_endpoints_mirrors_unlocks_at(ent):
    """``tier_locks_at(A, B)['lost_*']`` byte-equals
    ``tier_unlocks_at(B, A)['*']`` for every pair -- the swap-the-
    endpoints invariant ``tier_diff`` already pins, lifted to the scalar
    what-if pair."""
    for a in ent._TIER_ORDER:
        for b in ent._TIER_ORDER:
            locks = ent.tier_locks_at(a, b)
            unlocks = ent.tier_unlocks_at(b, a)
            assert locks["lost_features"] == unlocks["features"], (a, b)
            assert locks["lost_runtimes"] == unlocks["runtimes"], (a, b)


# ── trial is accepted on either side (lenient _at family) ────────────────────


def test_trial_accepted_as_perspective(ent):
    row = ent.tier_locks_at(ent.TIER_TRIAL, ent.TIER_OSS)
    assert row is not None
    assert row["next_tier"] == ent.TIER_TRIAL


def test_trial_accepted_as_target(ent):
    row = ent.tier_locks_at(ent.TIER_CLOUD_PRO, ent.TIER_TRIAL)
    assert row is not None
    assert row["tier"] == ent.TIER_TRIAL


# ── invalid tier (perspective) ───────────────────────────────────────────────


def test_unknown_tier_returns_none(ent):
    assert ent.tier_locks_at("not_a_real_tier", ent.TIER_OSS) is None


def test_empty_tier_returns_none(ent):
    assert ent.tier_locks_at("", ent.TIER_OSS) is None


def test_none_tier_returns_none(ent):
    assert ent.tier_locks_at(None, ent.TIER_OSS) is None  # type: ignore[arg-type]


def test_non_string_tier_returns_none(ent):
    assert ent.tier_locks_at(123, ent.TIER_OSS) is None  # type: ignore[arg-type]
    assert ent.tier_locks_at(object(), ent.TIER_OSS) is None  # type: ignore[arg-type]


# ── invalid target ───────────────────────────────────────────────────────────


def test_unknown_target_returns_none(ent):
    assert ent.tier_locks_at(ent.TIER_CLOUD_PRO, "not_a_real_tier") is None


def test_empty_target_returns_none(ent):
    assert ent.tier_locks_at(ent.TIER_CLOUD_PRO, "") is None


def test_none_target_returns_none(ent):
    assert ent.tier_locks_at(ent.TIER_CLOUD_PRO, None) is None  # type: ignore[arg-type]


def test_non_string_target_returns_none(ent):
    assert ent.tier_locks_at(ent.TIER_CLOUD_PRO, 123) is None  # type: ignore[arg-type]
    assert ent.tier_locks_at(ent.TIER_CLOUD_PRO, object()) is None  # type: ignore[arg-type]


# ── normalisation ────────────────────────────────────────────────────────────


def test_inputs_are_lowercased_and_trimmed(ent):
    a = ent.tier_locks_at(ent.TIER_CLOUD_PRO, ent.TIER_OSS)
    b = ent.tier_locks_at(ent.TIER_CLOUD_PRO.upper(), ent.TIER_OSS.upper())
    c = ent.tier_locks_at(
        f"  {ent.TIER_CLOUD_PRO}  ", f"  {ent.TIER_OSS}  "
    )
    assert a == b == c


# ── independent of live resolver ─────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    row_grace = ent.tier_locks_at(ent.TIER_CLOUD_PRO, ent.TIER_OSS)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    row_enforce = ent.tier_locks_at(ent.TIER_CLOUD_PRO, ent.TIER_OSS)
    assert row_grace == row_enforce


def test_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().to_dict()
    ent.tier_locks_at(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    after = ent.get_entitlement().to_dict()
    assert before == after


# ── never-raise ──────────────────────────────────────────────────────────────


def test_never_raises_when_builder_crashes(ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated builder failure")

    monkeypatch.setattr(ent, "_locks_row", boom)
    assert ent.tier_locks_at(ent.TIER_CLOUD_PRO, ent.TIER_OSS) is None


# ── HTTP endpoint ────────────────────────────────────────────────────────────


def test_endpoint_known_pair_returns_row(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-locks-at?tier={ent.TIER_CLOUD_PRO}"
        f"&target={ent.TIER_OSS}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["target"] == ent.TIER_OSS
    assert body["row"] == ent.tier_locks_at(ent.TIER_CLOUD_PRO, ent.TIER_OSS)


def test_endpoint_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-locks-at?tier=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
        f"&target=%20%20{ent.TIER_OSS.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["target"] == ent.TIER_OSS


def test_endpoint_missing_tier_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-locks-at?target={ent.TIER_OSS}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_tier_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-locks-at?tier=%20%20&target={ent.TIER_OSS}"
    )
    assert resp.status_code == 400


def test_endpoint_missing_target_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-locks-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_target_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-locks-at?tier={ent.TIER_CLOUD_PRO}&target=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client, ent):
    resp = client.get(
        "/api/entitlement/tier-locks-at?tier=nonsense_xyz"
        f"&target={ent.TIER_OSS}"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_unknown_target_returns_404(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-locks-at?tier={ent.TIER_CLOUD_PRO}"
        "&target=not_a_real_tier"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["which"] == "target"
    assert body["target"] == "not_a_real_tier"
    assert "error" in body


def test_endpoint_trial_is_accepted(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-locks-at?tier={ent.TIER_CLOUD_PRO}"
        f"&target={ent.TIER_TRIAL}"
    )
    assert resp.status_code == 200
    assert resp.get_json()["row"]["tier"] == ent.TIER_TRIAL


def test_endpoint_every_pair_round_trips(client, ent):
    for tier in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            resp = client.get(
                "/api/entitlement/tier-locks-at"
                f"?tier={tier}&target={target}"
            )
            assert resp.status_code == 200, (tier, target)
            body = resp.get_json()
            assert body["tier"] == tier, (tier, target)
            assert body["target"] == target, (tier, target)
            assert body["row"]["tier"] == target, (tier, target)
            assert body["row"]["next_tier"] == tier, (tier, target)
