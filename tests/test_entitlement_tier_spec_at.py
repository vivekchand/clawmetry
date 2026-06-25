"""Tests for ``tier_spec_at(tier, target)`` + ``GET
/api/entitlement/tier-spec-at``.

Scalar what-if sibling of :func:`tier_catalog_at`: one descriptor row for
``target`` with ``is_current`` computed as if the install were on ``tier``.
Lets a pricing-comparison tooltip hydrate against ONE tier descriptor from
a hypothetical perspective in one round-trip without fetching the full
``tier_catalog_at`` payload.

Pins:

* the row shape matches a row from ``tier_catalog_at(tier)`` EXACTLY (so
  the scalar and bulk what-if accessors cannot drift) -- a parity test
  enumerates every (tier, target) pair
* every (tier, target) pair in ``_TIER_ORDER`` x ``_TIER_ORDER``
  round-trips
* ``is_current`` is True iff ``tier == target`` (the only field that
  shifts between perspectives) and False on every other row
* unknown / empty / ``None`` / non-string ids on either argument return
  ``None``
* both args are trimmed + lowercased before resolution
* the helper is independent of the live resolver: switching enforcement
  or pointing HOME at a license cache does not change the rows the
  what-if surface returns
* the endpoint 400s on missing input, 404s on unknown ids (with
  ``which`` so the caller can render the right "unknown ..." message),
  and never 5xxs
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


_ROW_KEYS = {
    "id",
    "label",
    "is_paid",
    "is_current",
    "rank",
    "unlocks_paid_runtimes",
    "retention_days",
    "channel_limit",
    "node_limit",
    "features",
    "runtimes",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- ``tier_spec_at`` is
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


def test_row_shape_matches_catalog_at_row(ent):
    spec = ent.tier_spec_at(ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER)
    assert spec is not None
    assert set(spec.keys()) == _ROW_KEYS


def test_parity_with_every_catalog_at_row(ent):
    """For every (tier, target) pair, the scalar what-if accessor returns
    the same dict as the matching row in the bulk what-if accessor. Pins
    the scalar/bulk no-drift contract -- this is THE invariant the helper
    exists to make hydratable in one round-trip."""
    for tier in ent._TIER_ORDER:
        bulk_by_id = {row["id"]: row for row in ent.tier_catalog_at(tier)}
        for tid, row in bulk_by_id.items():
            assert ent.tier_spec_at(tier, tid) == row, (tier, tid)


# ── round-trip ────────────────────────────────────────────────────────────────


def test_every_pair_in_order_resolves(ent):
    for tier in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            spec = ent.tier_spec_at(tier, target)
            assert spec is not None, (tier, target)
            assert spec["id"] == target


# ── is_current semantics ──────────────────────────────────────────────────────


def test_is_current_true_on_self_perspective(ent):
    for tier in ent._TIER_ORDER:
        spec = ent.tier_spec_at(tier, tier)
        assert spec["is_current"] is True, tier


def test_is_current_false_on_other_perspective(ent):
    for tier in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            if target == tier:
                continue
            spec = ent.tier_spec_at(tier, target)
            assert spec["is_current"] is False, (tier, target)


def test_only_is_current_field_shifts_between_perspectives(ent):
    """Every catalogue-derived field on the row stays identical regardless
    of perspective -- only ``is_current`` flips. Pins that the helper does
    not accidentally tie any other field to the (perspective) tier."""
    perspectives = list(ent._TIER_ORDER)
    for target in ent._TIER_ORDER:
        rows = [ent.tier_spec_at(t, target) for t in perspectives]
        baseline = {k: v for k, v in rows[0].items() if k != "is_current"}
        for r in rows[1:]:
            other = {k: v for k, v in r.items() if k != "is_current"}
            assert other == baseline, (target, r["id"])


# ── invalid tier (perspective) ────────────────────────────────────────────────


def test_unknown_tier_returns_none(ent):
    assert ent.tier_spec_at("not_a_real_tier", ent.TIER_CLOUD_PRO) is None


def test_empty_tier_returns_none(ent):
    assert ent.tier_spec_at("", ent.TIER_CLOUD_PRO) is None


def test_none_tier_returns_none(ent):
    assert ent.tier_spec_at(None, ent.TIER_CLOUD_PRO) is None


def test_non_string_tier_returns_none(ent):
    assert ent.tier_spec_at(123, ent.TIER_CLOUD_PRO) is None
    assert ent.tier_spec_at(object(), ent.TIER_CLOUD_PRO) is None


# ── invalid target ────────────────────────────────────────────────────────────


def test_unknown_target_returns_none(ent):
    assert ent.tier_spec_at(ent.TIER_CLOUD_PRO, "not_a_real_tier") is None


def test_empty_target_returns_none(ent):
    assert ent.tier_spec_at(ent.TIER_CLOUD_PRO, "") is None


def test_none_target_returns_none(ent):
    assert ent.tier_spec_at(ent.TIER_CLOUD_PRO, None) is None


def test_non_string_target_returns_none(ent):
    assert ent.tier_spec_at(ent.TIER_CLOUD_PRO, 123) is None
    assert ent.tier_spec_at(ent.TIER_CLOUD_PRO, object()) is None


# ── normalisation ─────────────────────────────────────────────────────────────


def test_inputs_are_lowercased_and_trimmed(ent):
    a = ent.tier_spec_at(ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER)
    b = ent.tier_spec_at(
        ent.TIER_CLOUD_PRO.upper(), ent.TIER_CLOUD_STARTER.upper()
    )
    c = ent.tier_spec_at(
        f"  {ent.TIER_CLOUD_PRO}  ", f"  {ent.TIER_CLOUD_STARTER}  "
    )
    assert a == b == c


# ── catalogue values for known tiers ──────────────────────────────────────────


def test_oss_target_row_is_free_floor(ent):
    row = ent.tier_spec_at(ent.TIER_CLOUD_PRO, ent.TIER_OSS)
    assert row["id"] == ent.TIER_OSS
    assert row["is_paid"] is False
    assert row["unlocks_paid_runtimes"] is False
    assert row["features"] == []
    assert row["runtimes"] == []


def test_cloud_pro_target_unlocks_paid_runtimes(ent):
    row = ent.tier_spec_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert row["is_paid"] is True
    assert row["unlocks_paid_runtimes"] is True
    assert sorted(row["runtimes"]) == sorted(ent.PAID_RUNTIMES)


def test_enterprise_target_has_unlimited_retention(ent):
    row = ent.tier_spec_at(ent.TIER_OSS, ent.TIER_ENTERPRISE)
    assert row["retention_days"] is None


def test_rank_matches_tier_order(ent):
    for tier in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            row = ent.tier_spec_at(tier, target)
            assert row["rank"] == ent._TIER_ORDER.index(target), (tier, target)


# ── independent of live resolver ──────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    """tier_spec_at is decoupled from the resolved entitlement: grace
    mode flips no field on the returned row."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    row_grace = ent.tier_spec_at(ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    row_enforce = ent.tier_spec_at(ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER)
    assert row_grace == row_enforce


def test_helper_ignores_cloud_plan_cache(ent, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    row = ent.tier_spec_at(ent.TIER_OSS, ent.TIER_CLOUD_PRO)
    assert row["is_current"] is False
    assert row["id"] == ent.TIER_CLOUD_PRO


# ── never-raise ───────────────────────────────────────────────────────────────


def test_never_raises_when_get_entitlement_crashes(ent, monkeypatch):
    """The helper builds its row off the static per-tier maps and does
    not consult :func:`get_entitlement`, so a blown resolver must not
    affect the result. Pins the never-raise contract anyway."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    row = ent.tier_spec_at(ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER)
    assert row is not None
    assert row["id"] == ent.TIER_CLOUD_STARTER


# ── HTTP endpoint ─────────────────────────────────────────────────────────────


def test_endpoint_known_pair_returns_row(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at?tier={ent.TIER_CLOUD_PRO}"
        f"&target={ent.TIER_CLOUD_STARTER}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["target"] == ent.TIER_CLOUD_STARTER
    assert body["spec"] == ent.tier_spec_at(
        ent.TIER_CLOUD_PRO, ent.TIER_CLOUD_STARTER
    )


def test_endpoint_self_perspective_is_current(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at?tier={ent.TIER_CLOUD_PRO}"
        f"&target={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 200
    assert resp.get_json()["spec"]["is_current"] is True


def test_endpoint_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at?tier=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
        f"&target=%20%20{ent.TIER_CLOUD_STARTER.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["target"] == ent.TIER_CLOUD_STARTER


def test_endpoint_missing_tier_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at?target={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_tier_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at?tier=%20%20&target={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400


def test_endpoint_missing_target_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_target_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at?tier={ent.TIER_CLOUD_PRO}&target=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at?tier=nonsense_xyz"
        f"&target={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["tier"] == "nonsense_xyz"
    assert body["which"] == "tier"
    assert "error" in body


def test_endpoint_unknown_target_returns_404(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-spec-at?tier={ent.TIER_CLOUD_PRO}"
        "&target=not_a_real_tier"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["target"] == "not_a_real_tier"
    assert body["which"] == "target"
    assert "error" in body


def test_endpoint_every_pair_in_order_round_trips(client, ent):
    for tier in ent._TIER_ORDER:
        for target in ent._TIER_ORDER:
            resp = client.get(
                f"/api/entitlement/tier-spec-at?tier={tier}&target={target}"
            )
            assert resp.status_code == 200, (tier, target)
            body = resp.get_json()
            assert body["tier"] == tier, (tier, target)
            assert body["target"] == target, (tier, target)
            assert body["spec"]["id"] == target, (tier, target)
            assert body["spec"]["is_current"] is (tier == target), (tier, target)
