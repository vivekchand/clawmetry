"""Tests for ``tier_unlocks_at(tier, target)`` +
``GET /api/entitlement/tier-unlocks-at``.

Scalar what-if sibling of :func:`tier_unlocks`: marginal unlocks for
``target`` computed against the caller-supplied ``tier`` rather than the
global next-lower-purchasable-tier anchor :func:`tier_unlocks` uses.
Single-hop view of :func:`tier_unlocks_path` for the cumulative
``tier -> target`` marginal grant, elides intermediate rungs.

Pins:

* the row shape matches :func:`tier_unlocks` exactly
* ``features`` / ``runtimes`` byte-equal ``tier_diff(tier, target)``'s
  ``added_features`` / ``added_runtimes`` for every pair -- the parity
  test that stops the scalar what-if drifting away from the cumulative
  diff (the same invariant ``_unlocks_row`` already enforces against
  :func:`tier_unlocks_path`'s rungs, lifted to the public scalar)
* ``previous_tier`` always echoes the caller-supplied ``tier``, NOT the
  global anchor :func:`tier_unlocks` substitutes
* downgrade and identity pairs collapse to empty grant lists -- you
  unlock nothing going down or staying put
* every ``(tier, target)`` pair in :data:`_TIER_ORDER` x :data:`_TIER_ORDER`
  round-trips (including ``trial`` on either side -- the ``_at`` family
  is lenient where :func:`tier_unlocks` rejects ``trial``)
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
    "previous_tier",
    "previous_tier_label",
    "previous_tier_rank",
    "features",
    "runtimes",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- ``tier_unlocks_at`` is
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


def test_row_shape_matches_tier_unlocks(ent):
    row = ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert row is not None
    assert set(row.keys()) == _ROW_KEYS


def test_tier_metadata_matches_target(ent):
    row = ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert row["tier"] == ent.TIER_CLOUD_PRO
    assert row["tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert row["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_previous_tier_echoes_caller_perspective(ent):
    """``previous_tier`` is the caller-supplied ``tier`` (the scalar
    what-if source), NOT the global next-lower-purchasable anchor
    :func:`tier_unlocks` substitutes."""
    row = ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert row["previous_tier"] == ent.TIER_OSS
    assert row["previous_tier_label"] == ent.tier_label(ent.TIER_OSS)
    assert row["previous_tier_rank"] == ent.tier_rank(ent.TIER_OSS)
    # Differs from tier_unlocks(ENTERPRISE), which anchors to CLOUD_PRO.
    live = ent.tier_unlocks(ent.TIER_ENTERPRISE)
    assert live["previous_tier"] == ent.TIER_CLOUD_PRO


def test_lists_are_sorted(ent):
    row = ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert row["features"] == sorted(row["features"])
    assert row["runtimes"] == sorted(row["runtimes"])


# ── parity with tier_diff (the cumulative invariant) ─────────────────────────


def test_features_match_tier_diff_added_features(ent):
    """The grant lists byte-equal ``tier_diff(tier, target)['added_*']``
    for every pair -- the parity that stops the scalar what-if drifting
    from the cumulative diff."""
    for tier in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            row = ent.tier_unlocks_at(tier, target)
            diff = ent.tier_diff(tier, target)
            assert row is not None and diff is not None, (tier, target)
            assert row["features"] == diff["added_features"], (tier, target)
            assert row["runtimes"] == diff["added_runtimes"], (tier, target)


# ── round-trip across every pair ─────────────────────────────────────────────


def test_every_pair_resolves(ent):
    for tier in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            row = ent.tier_unlocks_at(tier, target)
            assert row is not None, (tier, target)
            assert row["tier"] == target, (tier, target)
            assert row["previous_tier"] == tier, (tier, target)


# ── direction semantics ──────────────────────────────────────────────────────


def test_upgrade_unlocks_starter_features_from_oss(ent):
    row = ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_CLOUD_STARTER)
    assert set(row["features"]) == set(ent.STARTER_FEATURES)
    assert set(row["runtimes"]) == set(ent.PAID_RUNTIMES)


def test_oss_to_enterprise_unlocks_full_paid_grant(ent):
    row = ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert set(row["features"]) == set(ent.PAID_FEATURES) | set(
        ent.ENTERPRISE_FEATURES
    )
    assert set(row["runtimes"]) == set(ent.PAID_RUNTIMES)


def test_starter_to_cloud_pro_unlocks_pro_only_features(ent):
    row = ent.tier_unlocks_at(ent.TIER_CLOUD_STARTER, ent.TIER_CLOUD_PRO)
    assert set(row["features"]) == set(ent.PRO_ONLY_FEATURES)
    # Paid runtimes already unlocked at Starter -- no marginal here.
    assert row["runtimes"] == []


def test_downgrade_unlocks_nothing(ent):
    """Going down a tier unlocks no new features / runtimes."""
    row = ent.tier_unlocks_at(ent.TIER_ENTERPRISE, ent.TIER_OSS)
    assert row["features"] == []
    assert row["runtimes"] == []


def test_identity_unlocks_nothing(ent):
    """Staying at the same tier unlocks no new features / runtimes."""
    for tier in ent._TIER_ORDER:
        row = ent.tier_unlocks_at(tier, tier)
        assert row["features"] == [], tier
        assert row["runtimes"] == [], tier


def test_lateral_same_rank_unlocks_grant_diff(ent):
    """Same-rank sibling tiers (cloud_pro vs pro) share a grant set, so a
    lateral hop unlocks nothing."""
    row = ent.tier_unlocks_at(ent.TIER_PRO, ent.TIER_CLOUD_PRO)
    assert row["features"] == []
    assert row["runtimes"] == []


# ── trial is accepted on either side (lenient _at family) ────────────────────


def test_trial_accepted_as_perspective(ent):
    """The live :func:`tier_unlocks` rejects ``trial`` (not purchasable),
    but the ``_at`` family is lenient -- it must answer hypothetical
    questions like "what does Pro unlock vs a Trial install?" too."""
    row = ent.tier_unlocks_at(ent.TIER_TRIAL, ent.TIER_CLOUD_PRO)
    assert row is not None
    assert row["previous_tier"] == ent.TIER_TRIAL


def test_trial_accepted_as_target(ent):
    row = ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_TRIAL)
    assert row is not None
    assert row["tier"] == ent.TIER_TRIAL


# ── invalid tier (perspective) ───────────────────────────────────────────────


def test_unknown_tier_returns_none(ent):
    assert ent.tier_unlocks_at("not_a_real_tier", ent.TIER_CLOUD_PRO) is None


def test_empty_tier_returns_none(ent):
    assert ent.tier_unlocks_at("", ent.TIER_CLOUD_PRO) is None


def test_none_tier_returns_none(ent):
    assert ent.tier_unlocks_at(None, ent.TIER_CLOUD_PRO) is None  # type: ignore[arg-type]


def test_non_string_tier_returns_none(ent):
    assert ent.tier_unlocks_at(123, ent.TIER_CLOUD_PRO) is None  # type: ignore[arg-type]
    assert ent.tier_unlocks_at(object(), ent.TIER_CLOUD_PRO) is None  # type: ignore[arg-type]


# ── invalid target ───────────────────────────────────────────────────────────


def test_unknown_target_returns_none(ent):
    assert ent.tier_unlocks_at(ent.TIER_CLOUD_PRO, "not_a_real_tier") is None


def test_empty_target_returns_none(ent):
    assert ent.tier_unlocks_at(ent.TIER_CLOUD_PRO, "") is None


def test_none_target_returns_none(ent):
    assert ent.tier_unlocks_at(ent.TIER_CLOUD_PRO, None) is None  # type: ignore[arg-type]


def test_non_string_target_returns_none(ent):
    assert ent.tier_unlocks_at(ent.TIER_CLOUD_PRO, 123) is None  # type: ignore[arg-type]
    assert ent.tier_unlocks_at(ent.TIER_CLOUD_PRO, object()) is None  # type: ignore[arg-type]


# ── normalisation ────────────────────────────────────────────────────────────


def test_inputs_are_lowercased_and_trimmed(ent):
    a = ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    b = ent.tier_unlocks_at(ent.TIER_OSS.upper(), ent.TIER_CLOUD_PRO.upper())
    c = ent.tier_unlocks_at(
        f"  {ent.TIER_OSS}  ", f"  {ent.TIER_CLOUD_PRO}  "
    )
    assert a == b == c


# ── independent of live resolver ─────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    row_grace = ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    row_enforce = ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert row_grace == row_enforce


def test_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().to_dict()
    ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    after = ent.get_entitlement().to_dict()
    assert before == after


# ── never-raise ──────────────────────────────────────────────────────────────


def test_never_raises_when_builder_crashes(ent, monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("simulated builder failure")

    monkeypatch.setattr(ent, "_unlocks_row", boom)
    assert ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO) is None


# ── HTTP endpoint ────────────────────────────────────────────────────────────


def test_endpoint_known_pair_returns_row(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-unlocks-at?tier={ent.TIER_OSS}"
        f"&target={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] == ent.TIER_CLOUD_PRO
    assert body["row"] == ent.tier_unlocks_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)


def test_endpoint_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-unlocks-at?tier=%20%20{ent.TIER_OSS.upper()}%20%20"
        f"&target=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["target"] == ent.TIER_CLOUD_PRO


def test_endpoint_missing_tier_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-unlocks-at?target={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_tier_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-unlocks-at?tier=%20%20"
        f"&target={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400


def test_endpoint_missing_target_returns_400(client, ent):
    resp = client.get(f"/api/entitlement/tier-unlocks-at?tier={ent.TIER_OSS}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_target_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-unlocks-at?tier={ent.TIER_OSS}&target=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client, ent):
    resp = client.get(
        "/api/entitlement/tier-unlocks-at?tier=nonsense_xyz"
        f"&target={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_unknown_target_returns_404(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-unlocks-at?tier={ent.TIER_OSS}"
        "&target=not_a_real_tier"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["which"] == "target"
    assert body["target"] == "not_a_real_tier"
    assert "error" in body


def test_endpoint_trial_is_accepted(client, ent):
    """Unlike the live /tier-unlocks endpoint (which 404s on ``trial``),
    the ``_at`` family accepts ``trial`` on either side."""
    resp = client.get(
        f"/api/entitlement/tier-unlocks-at?tier={ent.TIER_OSS}"
        f"&target={ent.TIER_TRIAL}"
    )
    assert resp.status_code == 200
    assert resp.get_json()["row"]["tier"] == ent.TIER_TRIAL


def test_endpoint_every_pair_round_trips(client, ent):
    for tier in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            resp = client.get(
                "/api/entitlement/tier-unlocks-at"
                f"?tier={tier}&target={target}"
            )
            assert resp.status_code == 200, (tier, target)
            body = resp.get_json()
            assert body["tier"] == tier, (tier, target)
            assert body["target"] == target, (tier, target)
            assert body["row"]["tier"] == target, (tier, target)
            assert body["row"]["previous_tier"] == tier, (tier, target)
