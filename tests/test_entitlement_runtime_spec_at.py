"""Tests for ``runtime_spec_at(tier, runtime)`` + ``GET
/api/entitlement/runtime-spec-at``.

Scalar what-if sibling of :func:`runtime_catalog_at`: one catalogue row
for ``runtime`` with ``allowed`` / ``locked`` / ``entitled`` computed
as if the install were on ``tier``. Lets a pricing-comparison tooltip
hydrate against ONE runtime at a hypothetical tier in one round-trip
without fetching the full ``runtime_catalog_at`` payload.

Pins:

* the row shape matches a row from ``runtime_catalog_at(tier)``
  EXACTLY (so the scalar and bulk what-if accessors cannot drift) -- a
  parity test enumerates every (tier, runtime) pair
* every (tier, runtime) pair in ``_TIER_ORDER`` x ``ALL_RUNTIMES``
  round-trips
* aliases (``claude-code``) canonicalise to ``claude_code``
* unknown / empty / ``None`` / non-string tier ids return ``None``
* unknown / empty / ``None`` ids for ``runtime`` return ``None``
* both args are trimmed + lowercased before resolution
* free runtimes are always ``allowed=True`` / ``locked=False``
  regardless of the requested tier
* the helper is independent of the live resolver: switching
  enforcement or pointing HOME at a license cache does not change the
  rows the what-if surface returns
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
    "free",
    "tier",
    "tiers",
    "allowed",
    "locked",
    "entitled",
}


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir
    so no real ~/.clawmetry/license.key or cloud_plan.json leaks in.
    Enforcement off by default (grace mode) -- ``runtime_spec_at`` is
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
    rt = next(iter(ent.FREE_RUNTIMES))
    spec = ent.runtime_spec_at(ent.TIER_CLOUD_PRO, rt)
    assert spec is not None
    assert set(spec.keys()) == _ROW_KEYS


def test_parity_with_every_catalog_at_row(ent):
    """For every (tier, runtime) pair, the scalar what-if accessor
    returns the same dict as the bulk what-if accessor. Pins the
    scalar/bulk no-drift contract -- this is THE invariant the helper
    exists to make hydratable in one round-trip."""
    for tier in ent._TIER_ORDER:
        bulk_by_id = {row["id"]: row for row in ent.runtime_catalog_at(tier)}
        for rt, row in bulk_by_id.items():
            assert ent.runtime_spec_at(tier, rt) == row, (tier, rt)


# ── round-trip ────────────────────────────────────────────────────────────────


def test_every_pair_in_order_resolves(ent):
    for tier in ent._TIER_ORDER:
        for rt in ent.ALL_RUNTIMES:
            spec = ent.runtime_spec_at(tier, rt)
            assert spec is not None, (tier, rt)
            assert spec["id"] == rt


# ── invalid tier ──────────────────────────────────────────────────────────────


def test_unknown_tier_returns_none(ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    assert ent.runtime_spec_at("not_a_real_tier", rt) is None


def test_empty_tier_returns_none(ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    assert ent.runtime_spec_at("", rt) is None


def test_none_tier_returns_none(ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    assert ent.runtime_spec_at(None, rt) is None


def test_non_string_tier_returns_none(ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    assert ent.runtime_spec_at(123, rt) is None
    assert ent.runtime_spec_at(object(), rt) is None


# ── invalid runtime ───────────────────────────────────────────────────────────


def test_unknown_runtime_returns_none(ent):
    assert ent.runtime_spec_at(ent.TIER_CLOUD_PRO, "not_a_real_runtime") is None


def test_empty_runtime_returns_none(ent):
    assert ent.runtime_spec_at(ent.TIER_CLOUD_PRO, "") is None


def test_none_runtime_returns_none(ent):
    assert ent.runtime_spec_at(ent.TIER_CLOUD_PRO, None) is None


# ── normalisation ─────────────────────────────────────────────────────────────


def test_inputs_are_lowercased_and_trimmed(ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    a = ent.runtime_spec_at(ent.TIER_CLOUD_PRO, rt)
    b = ent.runtime_spec_at(ent.TIER_CLOUD_PRO.upper(), rt.upper())
    c = ent.runtime_spec_at(f"  {ent.TIER_CLOUD_PRO}  ", f"  {rt}  ")
    assert a == b == c


def test_alias_canonicalisation_matches_catalog_at(ent):
    """``claude-code`` (with a hyphen) is the alias surface; the
    canonical id is ``claude_code`` -- the scalar what-if accessor
    must canonicalise the same way as :func:`runtime_spec`."""
    if "claude_code" not in ent.ALL_RUNTIMES:
        pytest.skip("claude_code not in this build's ALL_RUNTIMES")
    a = ent.runtime_spec_at(ent.TIER_CLOUD_PRO, "claude-code")
    b = ent.runtime_spec_at(ent.TIER_CLOUD_PRO, "claude_code")
    assert a == b
    assert a["id"] == "claude_code"


# ── per-tier lock state ───────────────────────────────────────────────────────


def test_free_runtime_unlocked_at_every_tier(ent):
    """Free runtimes are part of the OSS grant and must be
    ``allowed=True`` / ``locked=False`` at every tier (the open-core
    floor)."""
    rt = next(iter(ent.FREE_RUNTIMES))
    for tier in ent._TIER_ORDER:
        row = ent.runtime_spec_at(tier, rt)
        assert row["allowed"] is True, (tier, rt)
        assert row["locked"] is False, (tier, rt)
        assert row["entitled"] is True, (tier, rt)


def test_oss_tier_locks_a_paid_runtime(ent):
    if not ent.PAID_RUNTIMES:
        pytest.skip("no paid runtimes defined")
    rt = next(iter(ent.PAID_RUNTIMES))
    row = ent.runtime_spec_at(ent.TIER_OSS, rt)
    assert row["locked"] is True
    assert row["allowed"] is False


def test_enterprise_unlocks_every_runtime(ent):
    for rt in ent.ALL_RUNTIMES:
        row = ent.runtime_spec_at(ent.TIER_ENTERPRISE, rt)
        assert row["allowed"] is True, rt
        assert row["locked"] is False, rt


# ── independent of live resolver ──────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    if not ent.PAID_RUNTIMES:
        pytest.skip("no paid runtimes defined")
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    rt = next(iter(ent.PAID_RUNTIMES))
    row = ent.runtime_spec_at(ent.TIER_OSS, rt)
    assert row["locked"] is True
    assert row["allowed"] is False


def test_helper_ignores_cloud_plan_cache(ent, monkeypatch, tmp_path):
    if not ent.PAID_RUNTIMES:
        pytest.skip("no paid runtimes defined")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro"}))
    ent.invalidate()
    rt = next(iter(ent.PAID_RUNTIMES))
    row = ent.runtime_spec_at(ent.TIER_OSS, rt)
    assert row["locked"] is True
    assert row["allowed"] is False


# ── never-raise ───────────────────────────────────────────────────────────────


def test_never_raises_when_get_entitlement_crashes(ent, monkeypatch):
    """The helper builds its own hypothetical Entitlement and does not
    consult :func:`get_entitlement`, so a blown resolver must not
    affect the result. Pins the never-raise contract anyway."""

    def boom(*_a, **_kw):
        raise RuntimeError("simulated resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rt = next(iter(ent.FREE_RUNTIMES))
    row = ent.runtime_spec_at(ent.TIER_CLOUD_PRO, rt)
    assert row is not None
    assert row["id"] == rt


# ── HTTP endpoint ─────────────────────────────────────────────────────────────


def test_endpoint_known_pair_returns_row(client, ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    resp = client.get(
        f"/api/entitlement/runtime-spec-at?tier={ent.TIER_CLOUD_PRO}&runtime={rt}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["runtime"] == rt
    assert body["spec"] == ent.runtime_spec_at(ent.TIER_CLOUD_PRO, rt)


def test_endpoint_lowercases_and_trims(client, ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    resp = client.get(
        f"/api/entitlement/runtime-spec-at?tier=%20%20{ent.TIER_CLOUD_PRO.upper()}%20%20"
        f"&runtime=%20%20{rt.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["runtime"] == rt


def test_endpoint_alias_canonicalises(client, ent):
    if "claude_code" not in ent.ALL_RUNTIMES:
        pytest.skip("claude_code not in this build's ALL_RUNTIMES")
    resp = client.get(
        f"/api/entitlement/runtime-spec-at?tier={ent.TIER_CLOUD_PRO}"
        "&runtime=claude-code"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["runtime"] == "claude_code"
    assert body["spec"]["id"] == "claude_code"


def test_endpoint_missing_tier_returns_400(client, ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    resp = client.get(f"/api/entitlement/runtime-spec-at?runtime={rt}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_tier_returns_400(client, ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    resp = client.get(
        f"/api/entitlement/runtime-spec-at?tier=%20%20&runtime={rt}"
    )
    assert resp.status_code == 400


def test_endpoint_missing_runtime_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/runtime-spec-at?tier={ent.TIER_CLOUD_PRO}"
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_runtime_returns_400(client, ent):
    resp = client.get(
        f"/api/entitlement/runtime-spec-at?tier={ent.TIER_CLOUD_PRO}&runtime=%20%20"
    )
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client, ent):
    rt = next(iter(ent.FREE_RUNTIMES))
    resp = client.get(
        f"/api/entitlement/runtime-spec-at?tier=nonsense_xyz&runtime={rt}"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["tier"] == "nonsense_xyz"
    assert body["which"] == "tier"
    assert "error" in body


def test_endpoint_unknown_runtime_returns_404(client, ent):
    resp = client.get(
        f"/api/entitlement/runtime-spec-at?tier={ent.TIER_CLOUD_PRO}"
        "&runtime=not_a_real_runtime"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["runtime"] == "not_a_real_runtime"
    assert body["which"] == "runtime"
    assert "error" in body


def test_endpoint_every_pair_in_order_round_trips(client, ent):
    for tier in ent._TIER_ORDER:
        for rt in ent.ALL_RUNTIMES:
            resp = client.get(
                f"/api/entitlement/runtime-spec-at?tier={tier}&runtime={rt}"
            )
            assert resp.status_code == 200, (tier, rt)
            body = resp.get_json()
            assert body["tier"] == tier, (tier, rt)
            assert body["runtime"] == rt, (tier, rt)
            assert body["spec"]["id"] == rt, (tier, rt)
