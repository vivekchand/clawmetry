"""Tests for ``tier_unlocks_at_batch(tier)`` +
``GET /api/entitlement/tier-unlocks-at-batch``.

What-if + batch sibling of :func:`tier_unlocks_batch`: marginal-unlocks
rows for every purchasable tier as a target, computed against the
caller-supplied ``tier`` rather than the global next-lower-purchasable-
tier anchor :func:`tier_unlocks_batch` uses. Composes
:func:`tier_unlocks_at` (scalar what-if) and :func:`tier_unlocks_batch`
(live batch).

Pins:

* one row per :data:`_PURCHASABLE_TIERS` entry, sorted by ``(rank, id)``
  ascending (byte-stable against :func:`tier_unlocks_batch`)
* row shape matches :func:`tier_unlocks_at` / :func:`tier_unlocks`
  exactly
* each row byte-equals ``tier_unlocks_at(tier, target)`` for the same
  pair -- the scalar-batch parity that stops the batch what-if drifting
  away from the scalar what-if (mirrors the parity ``feature_spec_at_batch``
  / ``runtime_spec_at_batch`` pin against their scalar siblings)
* ``previous_tier`` on every row echoes the caller-supplied source
  ``tier``, NOT the global anchor :func:`tier_unlocks_batch` uses
* the trial tier is excluded from the **target** axis (mirrors
  :func:`tier_unlocks_batch`), but accepted on the **source** ``tier``
  arg (the lenient ``_at`` posture)
* downgrade-direction rows collapse to empty grant lists; the source
  tier's identity row collapses too
* unknown / empty / ``None`` / non-string source returns ``None``
* the source ``tier`` is trimmed + lowercased before resolution
* the helper is independent of the live resolver (grace flips no field)
* the endpoint 400s on missing input, 404s on unknown source (with
  ``which=tier``), and never 5xxs
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
    Enforcement off by default (grace mode) -- the helper is independent
    of either knob, so the fixture only needs to keep the live resolver
    from surprising the test."""
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


def test_returns_list_for_known_tier(ent):
    rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    assert isinstance(rows, list)
    assert len(rows) > 0


def test_each_row_has_scalar_shape(ent):
    rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    for row in rows:
        assert set(row.keys()) == _ROW_KEYS


def test_excludes_trial_from_targets(ent):
    rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    ids = {row["tier"] for row in rows}
    assert ent.TIER_TRIAL not in ids


def test_includes_every_purchasable_tier_as_target(ent):
    rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    ids = {row["tier"] for row in rows}
    expected = {
        ent.TIER_OSS,
        ent.TIER_CLOUD_FREE,
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }
    assert ids == expected


def test_target_set_matches_purchasable_tiers(ent):
    """Hard-pin against ``_PURCHASABLE_TIERS`` so the target axis stays
    in lock-step with :func:`tier_unlocks_batch` even if the purchasable
    set ever changes."""
    rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    ids = {row["tier"] for row in rows}
    assert ids == set(ent._PURCHASABLE_TIERS)


# ── ordering ─────────────────────────────────────────────────────────────────


def test_sorted_by_rank_ascending(ent):
    rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    ranks = [row["tier_rank"] for row in rows]
    assert ranks == sorted(ranks)


def test_same_rank_sorted_by_tier_id(ent):
    rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    # Group rank -> [ids], confirm each group is sorted by id ascending.
    by_rank: dict[int, list[str]] = {}
    for row in rows:
        by_rank.setdefault(row["tier_rank"], []).append(row["tier"])
    for ids in by_rank.values():
        assert ids == sorted(ids)


def test_target_axis_matches_tier_unlocks_batch_ordering(ent):
    """The target axis is byte-stable against :func:`tier_unlocks_batch`'s
    ordering so a UI can swap the live anchor for a hypothetical one
    without re-sorting client-side."""
    at_rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    live_rows = ent.tier_unlocks_batch()
    assert [r["tier"] for r in at_rows] == [r["tier"] for r in live_rows]


# ── parity with scalar tier_unlocks_at ───────────────────────────────────────


def test_each_row_byte_equals_scalar_at(ent):
    """Every row byte-equals ``tier_unlocks_at(tier, target)`` for the
    same pair -- the parity that stops the batch what-if drifting from
    the scalar what-if."""
    for src in ent._TIER_ORDER:
        rows = ent.tier_unlocks_at_batch(src)
        assert rows is not None, src
        for row in rows:
            scalar = ent.tier_unlocks_at(src, row["tier"])
            assert row == scalar, (src, row["tier"])


def test_each_row_byte_equals_tier_diff_added(ent):
    """Composes the cumulative-diff parity ``tier_unlocks_at`` already
    pins, lifted to the batch (so a regression on either side of the
    pipeline trips here too)."""
    for src in ent._TIER_ORDER:
        rows = ent.tier_unlocks_at_batch(src)
        for row in rows:
            diff = ent.tier_diff(src, row["tier"])
            assert row["features"] == diff["added_features"], (src, row["tier"])
            assert row["runtimes"] == diff["added_runtimes"], (src, row["tier"])


def test_previous_tier_echoes_caller_perspective_on_every_row(ent):
    """``previous_tier`` on every row is the caller-supplied source
    ``tier``, NOT the global next-lower-purchasable anchor
    :func:`tier_unlocks_batch` uses."""
    rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    for row in rows:
        assert row["previous_tier"] == ent.TIER_OSS
        assert row["previous_tier_label"] == ent.tier_label(ent.TIER_OSS)
        assert row["previous_tier_rank"] == ent.tier_rank(ent.TIER_OSS)


def test_oss_source_perspective_differs_from_live_batch(ent):
    """The source-perspective batch must NOT match the live batch on
    the ``previous_tier`` axis (otherwise the helper is silently
    falling through to the live anchor)."""
    at_rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    live_rows = ent.tier_unlocks_batch()
    live_by_tier = {r["tier"]: r for r in live_rows}
    # Enterprise live row anchors to CLOUD_PRO (the next-lower-purchasable);
    # the OSS-perspective row must anchor to OSS instead.
    at_enterprise = next(r for r in at_rows if r["tier"] == ent.TIER_ENTERPRISE)
    live_enterprise = live_by_tier[ent.TIER_ENTERPRISE]
    assert at_enterprise["previous_tier"] == ent.TIER_OSS
    assert live_enterprise["previous_tier"] == ent.TIER_CLOUD_PRO


# ── direction semantics ──────────────────────────────────────────────────────


def test_oss_source_grants_full_paid_ladder_upward(ent):
    """From OSS, every upgrade target unlocks at least what OSS lacks
    (paid features/runtimes); the enterprise target unlocks the most."""
    rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    enterprise_row = next(r for r in rows if r["tier"] == ent.TIER_ENTERPRISE)
    assert set(enterprise_row["features"]) == set(ent.PAID_FEATURES) | set(
        ent.ENTERPRISE_FEATURES
    )
    assert set(enterprise_row["runtimes"]) == set(ent.PAID_RUNTIMES)


def test_identity_row_is_empty(ent):
    """The row whose target matches the source tier carries empty
    grant lists -- staying put unlocks nothing."""
    for src in ent._PURCHASABLE_TIERS:
        rows = ent.tier_unlocks_at_batch(src)
        identity = next(r for r in rows if r["tier"] == src)
        assert identity["features"] == [], src
        assert identity["runtimes"] == [], src


def test_enterprise_source_collapses_all_targets_to_empty(ent):
    """From the ceiling tier (ENTERPRISE), there is nothing to unlock
    going to any other tier -- every target row collapses to empty
    grant lists."""
    rows = ent.tier_unlocks_at_batch(ent.TIER_ENTERPRISE)
    for row in rows:
        assert row["features"] == [], row["tier"]
        assert row["runtimes"] == [], row["tier"]


# ── source-axis: trial accepted (lenient _at family) ─────────────────────────


def test_trial_accepted_as_source(ent):
    rows = ent.tier_unlocks_at_batch(ent.TIER_TRIAL)
    assert rows is not None
    assert len(rows) == len(ent._PURCHASABLE_TIERS)
    for row in rows:
        assert row["previous_tier"] == ent.TIER_TRIAL


# ── every source resolves ────────────────────────────────────────────────────


def test_every_source_round_trips(ent):
    """Every id in :data:`_TIER_ORDER` (including trial) is a valid
    source -- the helper must answer hypothetical comparisons against
    any rung in the catalog."""
    for src in ent._TIER_ORDER:
        rows = ent.tier_unlocks_at_batch(src)
        assert rows is not None, src
        assert len(rows) == len(ent._PURCHASABLE_TIERS), src


# ── invalid source ───────────────────────────────────────────────────────────


def test_unknown_source_returns_none(ent):
    assert ent.tier_unlocks_at_batch("not_a_real_tier") is None


def test_empty_source_returns_none(ent):
    assert ent.tier_unlocks_at_batch("") is None


def test_none_source_returns_none(ent):
    assert ent.tier_unlocks_at_batch(None) is None  # type: ignore[arg-type]


def test_non_string_source_returns_none(ent):
    assert ent.tier_unlocks_at_batch(123) is None  # type: ignore[arg-type]
    assert ent.tier_unlocks_at_batch(object()) is None  # type: ignore[arg-type]


# ── normalisation ────────────────────────────────────────────────────────────


def test_source_is_lowercased_and_trimmed(ent):
    a = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    b = ent.tier_unlocks_at_batch(ent.TIER_OSS.upper())
    c = ent.tier_unlocks_at_batch(f"  {ent.TIER_OSS}  ")
    assert a == b == c


# ── independent of live resolver ─────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    rows_grace = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    rows_enforce = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    assert rows_grace == rows_enforce


def test_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().to_dict()
    ent.tier_unlocks_at_batch(ent.TIER_OSS)
    after = ent.get_entitlement().to_dict()
    assert before == after


# ── never-raise ──────────────────────────────────────────────────────────────


def test_returns_empty_list_when_builder_crashes(ent, monkeypatch):
    """A builder failure short-circuits to ``[]`` so the matrix keeps
    rendering instead of breaking. Returns ``[]`` (not ``None``) so
    callers can iterate without a None-check -- ``None`` is reserved
    for the unknown-source 404 path."""
    def boom(*_a, **_kw):
        raise RuntimeError("simulated builder failure")

    monkeypatch.setattr(ent, "_unlocks_row", boom)
    assert ent.tier_unlocks_at_batch(ent.TIER_OSS) == []


# ── HTTP endpoint ────────────────────────────────────────────────────────────


def test_endpoint_known_source_returns_full_ladder(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-unlocks-at-batch?tier={ent.TIER_OSS}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["tiers"] == ent.tier_unlocks_at_batch(ent.TIER_OSS)
    assert "current_tier" in body
    assert "current_tier_rank" in body
    assert "grace" in body
    assert "enforced" in body


def test_endpoint_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-unlocks-at-batch?tier=%20%20{ent.TIER_OSS.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS


def test_endpoint_missing_tier_returns_400(client):
    resp = client.get("/api/entitlement/tier-unlocks-at-batch")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_tier_returns_400(client):
    resp = client.get("/api/entitlement/tier-unlocks-at-batch?tier=%20%20")
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client):
    resp = client.get(
        "/api/entitlement/tier-unlocks-at-batch?tier=nonsense_xyz"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_trial_is_accepted_as_source(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-unlocks-at-batch?tier={ent.TIER_TRIAL}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_TRIAL
    for row in body["tiers"]:
        assert row["previous_tier"] == ent.TIER_TRIAL


def test_endpoint_every_source_round_trips(client, ent):
    for src in ent._TIER_ORDER:
        resp = client.get(
            f"/api/entitlement/tier-unlocks-at-batch?tier={src}"
        )
        assert resp.status_code == 200, src
        body = resp.get_json()
        assert body["tier"] == src, src
        assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS), src


def test_endpoint_envelope_carries_resolver_state(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-unlocks-at-batch?tier={ent.TIER_OSS}"
    )
    body = resp.get_json()
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["current_tier_rank"] == ent.tier_rank(live.tier)
    assert body["grace"] == bool(live.grace)
    assert body["enforced"] == ent.is_enforced()
