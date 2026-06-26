"""Tests for ``capacity_diff_at_batch(tier)`` +
``GET /api/entitlement/capacity-diff-at-batch``.

What-if + batch sibling of :func:`capacity_diff_batch`: per-axis
capacity-transition rows for every purchasable tier as a target,
computed against the caller-supplied ``tier`` rather than the resolved
entitlement :func:`capacity_diff_batch` anchors to. Composes
:func:`capacity_diff_at` (scalar what-if) and :func:`capacity_diff_batch`
(live batch).

Pins:

* one row per :data:`_PURCHASABLE_TIERS` entry, sorted by ``(rank, id)``
  ascending (byte-stable against :func:`capacity_diff_batch` /
  :func:`tier_unlocks_at_batch` / :func:`tier_locks_at_batch` for the
  same source tier)
* row shape matches :func:`capacity_diff_at` / :func:`capacity_diff`
  exactly
* each row byte-equals ``capacity_diff_at(tier, target)`` for the same
  pair -- the scalar-batch parity that stops the batch what-if drifting
  away from the scalar what-if (mirrors the parity ``tier_unlocks_at_batch``
  / ``tier_locks_at_batch`` pin against their scalar siblings)
* ``before`` on every row's axes carries the caller-supplied source
  ``tier``'s static caps, NOT the resolved entitlement's caps
  :func:`capacity_diff_batch` uses; the per-axis ``before`` does NOT
  collapse to the unlimited sentinel the way :func:`capacity_diff_batch`
  does under grace
* the trial tier is excluded from the **target** axis (mirrors
  :func:`capacity_diff_batch`), but accepted on the **source** ``tier``
  arg (the lenient ``_at`` posture)
* identity row collapses every axis to a no-op triple
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


_ROW_KEYS = {"target", "channel_limit", "retention_days", "node_limit"}
_AXIS_KEYS = {"before", "after", "delta", "unlocked", "locked"}


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
    rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    assert isinstance(rows, list)
    assert len(rows) > 0


def test_each_row_has_scalar_shape(ent):
    rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    for row in rows:
        assert set(row.keys()) == _ROW_KEYS


def test_each_axis_has_full_triple(ent):
    rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    for row in rows:
        for axis in ("channel_limit", "retention_days", "node_limit"):
            assert set(row[axis].keys()) == _AXIS_KEYS, (row["target"], axis)


def test_excludes_trial_from_targets(ent):
    rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    ids = {row["target"] for row in rows}
    assert ent.TIER_TRIAL not in ids


def test_includes_every_purchasable_tier_as_target(ent):
    rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    ids = {row["target"] for row in rows}
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
    in lock-step with :func:`capacity_diff_batch` even if the purchasable
    set ever changes."""
    rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    ids = {row["target"] for row in rows}
    assert ids == set(ent._PURCHASABLE_TIERS)


# ── ordering ─────────────────────────────────────────────────────────────────


def test_sorted_by_rank_ascending(ent):
    rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    ranks = [ent.tier_rank(row["target"]) for row in rows]
    assert ranks == sorted(ranks)


def test_same_rank_sorted_by_tier_id(ent):
    rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    by_rank: dict[int, list[str]] = {}
    for row in rows:
        by_rank.setdefault(ent.tier_rank(row["target"]), []).append(row["target"])
    for ids in by_rank.values():
        assert ids == sorted(ids)


def test_target_axis_matches_capacity_diff_batch_ordering(ent):
    """The target axis is byte-stable against :func:`capacity_diff_batch`'s
    ordering so a UI can swap the live anchor for a hypothetical one
    without re-sorting client-side."""
    at_rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    live_rows = ent.capacity_diff_batch()
    assert [r["target"] for r in at_rows] == [r["target"] for r in live_rows]


def test_target_axis_matches_tier_unlocks_at_batch_ordering(ent):
    """Byte-stable against :func:`tier_unlocks_at_batch` for the same
    source tier so a UI can fold the two responses into the same
    pricing-matrix table without re-sorting."""
    cap_rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    unlock_rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    assert [r["target"] for r in cap_rows] == [r["tier"] for r in unlock_rows]


# ── parity with scalar capacity_diff_at ──────────────────────────────────────


def test_each_row_byte_equals_scalar_at(ent):
    """Every row byte-equals ``capacity_diff_at(tier, target)`` for the
    same pair -- the parity that stops the batch what-if drifting from
    the scalar what-if."""
    for src in ent._TIER_FEATURES:
        rows = ent.capacity_diff_at_batch(src)
        assert rows is not None, src
        for row in rows:
            scalar = ent.capacity_diff_at(src, row["target"])
            assert row == scalar, (src, row["target"])


def test_each_row_axes_match_tier_diff_capacity_changes(ent):
    """Composes the cumulative-diff parity ``capacity_diff_at`` pins
    against :func:`tier_diff`, lifted to the batch (so a regression on
    either side of the pipeline trips here too)."""
    for src in ent._TIER_FEATURES:
        rows = ent.capacity_diff_at_batch(src)
        if rows is None:
            continue
        for row in rows:
            diff = ent.tier_diff(src, row["target"])
            assert diff is not None, (src, row["target"])
            for axis in ("channel_limit", "retention_days", "node_limit"):
                assert row[axis] == diff["capacity_changes"][axis], (
                    src, row["target"], axis,
                )


# ── before-side carries caller perspective (not the resolver) ────────────────


def test_before_carries_caller_perspective_on_every_row(ent):
    """``before`` on every axis carries the caller-supplied source
    ``tier``'s static caps, NOT the resolved entitlement's caps the
    live batch uses."""
    rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    for row in rows:
        assert row["channel_limit"]["before"] == ent._FREE_CHANNEL_LIMIT, row["target"]
        assert row["node_limit"]["before"] == ent._FREE_NODE_LIMIT, row["target"]
        assert (
            row["retention_days"]["before"]
            == ent._TIER_RETENTION_DAYS[ent.TIER_OSS]
        ), row["target"]


def test_oss_source_perspective_differs_from_live_batch(ent):
    """The source-perspective batch must NOT match the live batch on
    the ``before`` axis (otherwise the helper is silently falling
    through to the live anchor). Under grace the live batch's
    ``before`` collapses to the unlimited sentinel; the OSS-perspective
    batch must carry the finite OSS cap."""
    at_rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    live_rows = ent.capacity_diff_batch()
    at_by_target = {r["target"]: r for r in at_rows}
    live_by_target = {r["target"]: r for r in live_rows}
    at_pro = at_by_target[ent.TIER_CLOUD_PRO]
    live_pro = live_by_target[ent.TIER_CLOUD_PRO]
    assert at_pro["channel_limit"]["before"] == ent._FREE_CHANNEL_LIMIT
    assert live_pro["channel_limit"]["before"] is None


# ── direction semantics ──────────────────────────────────────────────────────


def test_oss_source_upgrades_unlock_channels_on_paid_tiers(ent):
    """From OSS, every paid target flips ``unlocked`` on the channel
    axis (finite OSS cap -> unlimited paid cap)."""
    rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    paid_targets = {
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    }
    for row in rows:
        if row["target"] in paid_targets:
            assert row["channel_limit"]["unlocked"] is True, row["target"]
            assert row["channel_limit"]["after"] is None, row["target"]


def test_identity_row_is_a_noop(ent):
    """The row whose target matches the source tier carries no-op
    triples on every axis -- staying put changes no capacity."""
    for src in ent._PURCHASABLE_TIERS:
        rows = ent.capacity_diff_at_batch(src)
        identity = next(r for r in rows if r["target"] == src)
        for axis in ("channel_limit", "retention_days", "node_limit"):
            triple = identity[axis]
            assert triple["before"] == triple["after"], (src, axis)
            assert triple["unlocked"] is False, (src, axis)
            assert triple["locked"] is False, (src, axis)


def test_enterprise_source_locks_capacity_on_downgrades(ent):
    """From the ceiling tier (Enterprise, unlimited everywhere), every
    finite-capped target flips ``locked`` on the relevant axes -- the
    cancellation-warning copy."""
    rows = ent.capacity_diff_at_batch(ent.TIER_ENTERPRISE)
    by_target = {r["target"]: r for r in rows}
    oss_row = by_target[ent.TIER_OSS]
    assert oss_row["channel_limit"]["locked"] is True
    assert oss_row["node_limit"]["locked"] is True
    # Enterprise retention is None (unlimited), OSS is 7d -- so
    # retention also flips locked (the unlimited -> finite transition).
    assert oss_row["retention_days"]["before"] is None
    assert oss_row["retention_days"]["after"] == 7
    assert oss_row["retention_days"]["locked"] is True
    assert oss_row["retention_days"]["unlocked"] is False


# ── source-axis: trial accepted (lenient _at family) ─────────────────────────


def test_trial_accepted_as_source(ent):
    rows = ent.capacity_diff_at_batch(ent.TIER_TRIAL)
    assert rows is not None
    assert len(rows) == len(ent._PURCHASABLE_TIERS)
    for row in rows:
        # Trial channel/node caps are unlimited (None); paid targets
        # are also unlimited so the channel axis is a no-op there.
        assert row["channel_limit"]["before"] is None, row["target"]


# ── every source resolves ────────────────────────────────────────────────────


def test_every_source_round_trips(ent):
    """Every id in :data:`_TIER_FEATURES` (including trial) is a valid
    source -- the helper must answer hypothetical comparisons against
    any rung in the catalog."""
    for src in ent._TIER_FEATURES:
        rows = ent.capacity_diff_at_batch(src)
        assert rows is not None, src
        assert len(rows) == len(ent._PURCHASABLE_TIERS), src


# ── invalid source ───────────────────────────────────────────────────────────


def test_unknown_source_returns_none(ent):
    assert ent.capacity_diff_at_batch("not_a_real_tier") is None


def test_empty_source_returns_none(ent):
    assert ent.capacity_diff_at_batch("") is None


def test_none_source_returns_none(ent):
    assert ent.capacity_diff_at_batch(None) is None  # type: ignore[arg-type]


def test_non_string_source_returns_none(ent):
    assert ent.capacity_diff_at_batch(123) is None  # type: ignore[arg-type]
    assert ent.capacity_diff_at_batch(object()) is None  # type: ignore[arg-type]


# ── normalisation ────────────────────────────────────────────────────────────


def test_source_is_lowercased_and_trimmed(ent):
    a = ent.capacity_diff_at_batch(ent.TIER_OSS)
    b = ent.capacity_diff_at_batch(ent.TIER_OSS.upper())
    c = ent.capacity_diff_at_batch(f"  {ent.TIER_OSS}  ")
    assert a == b == c


# ── independent of live resolver ─────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    rows_grace = ent.capacity_diff_at_batch(ent.TIER_OSS)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    rows_enforce = ent.capacity_diff_at_batch(ent.TIER_OSS)
    assert rows_grace == rows_enforce


def test_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().to_dict()
    ent.capacity_diff_at_batch(ent.TIER_OSS)
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

    monkeypatch.setattr(ent, "_capacity_row", boom)
    assert ent.capacity_diff_at_batch(ent.TIER_OSS) == []


# ── HTTP endpoint ────────────────────────────────────────────────────────────


def test_endpoint_known_source_returns_full_ladder(client, ent):
    resp = client.get(
        f"/api/entitlement/capacity-diff-at-batch?tier={ent.TIER_OSS}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["tiers"] == ent.capacity_diff_at_batch(ent.TIER_OSS)
    assert "current_tier" in body
    assert "current_tier_rank" in body
    assert "grace" in body
    assert "enforced" in body


def test_endpoint_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/capacity-diff-at-batch?tier=%20%20{ent.TIER_OSS.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS


def test_endpoint_missing_tier_returns_400(client):
    resp = client.get("/api/entitlement/capacity-diff-at-batch")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_tier_returns_400(client):
    resp = client.get("/api/entitlement/capacity-diff-at-batch?tier=%20%20")
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client):
    resp = client.get(
        "/api/entitlement/capacity-diff-at-batch?tier=nonsense_xyz"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_trial_is_accepted_as_source(client, ent):
    resp = client.get(
        f"/api/entitlement/capacity-diff-at-batch?tier={ent.TIER_TRIAL}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_TRIAL
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)


def test_endpoint_every_source_round_trips(client, ent):
    for src in ent._TIER_FEATURES:
        resp = client.get(
            f"/api/entitlement/capacity-diff-at-batch?tier={src}"
        )
        assert resp.status_code == 200, src
        body = resp.get_json()
        assert body["tier"] == src, src
        assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS), src


def test_endpoint_envelope_carries_resolver_state(client, ent):
    resp = client.get(
        f"/api/entitlement/capacity-diff-at-batch?tier={ent.TIER_OSS}"
    )
    body = resp.get_json()
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["current_tier_rank"] == ent.tier_rank(live.tier)
    assert body["grace"] == bool(live.grace)
    assert body["enforced"] == ent.is_enforced()
