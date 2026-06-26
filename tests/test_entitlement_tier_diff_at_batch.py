"""Tests for ``tier_diff_at_batch(tier)`` +
``GET /api/entitlement/tier-diff-at-batch``.

What-if + batch sibling of :func:`tier_diff_batch`: full marginal
:func:`tier_diff` payload between the caller-supplied ``tier`` and
every purchasable tier as a target, in one pass. Composes
:func:`tier_diff` (arbitrary-endpoint diff) and :func:`tier_diff_batch`
(live walking batch).

Pins:

* one row per :data:`_PURCHASABLE_TIERS` entry, sorted by ``(rank, id)``
  ascending (byte-stable against :func:`tier_diff_batch` /
  :func:`tier_unlocks_at_batch` / :func:`tier_locks_at_batch` /
  :func:`capacity_diff_at_batch` for the same source tier)
* row shape matches :func:`tier_diff` exactly -- ``from``, ``from_label``,
  ``from_rank``, ``to``, ``to_label``, ``to_rank``, ``direction``,
  ``added_features``, ``lost_features``, ``added_runtimes``,
  ``lost_runtimes``, ``capacity_changes``
* each row byte-equals ``tier_diff(tier, target)`` for the same pair --
  the scalar-batch parity that stops the batch what-if drifting from
  the scalar tier_diff (mirrors the parity ``capacity_diff_at_batch``
  pins against ``capacity_diff_at``)
* per-slice parity with the other ``_at`` batches:
  - ``added_features`` / ``added_runtimes`` byte-equal
    :func:`tier_unlocks_at_batch`'s ``features`` / ``runtimes`` slot for
    the same target
  - ``lost_features`` / ``lost_runtimes`` byte-equal
    :func:`tier_locks_at_batch`'s ``lost_features`` / ``lost_runtimes``
    slot for the same target
  - ``capacity_changes`` byte-equal :func:`capacity_diff_at_batch`'s
    per-axis triples for the same target
* ``from`` on every row carries the caller-supplied source ``tier``
  (NOT the per-rung next-lower anchor :func:`tier_diff_batch` uses)
* the trial tier is excluded from the **target** axis (mirrors
  :func:`tier_diff_batch`), but accepted on the **source** ``tier``
  arg (the lenient ``_at`` posture)
* identity row collapses to ``tier_diff(t, t)`` with ``direction ==
  "identity"`` and empty marginal lists
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
    "from",
    "from_label",
    "from_rank",
    "to",
    "to_label",
    "to_rank",
    "direction",
    "added_features",
    "lost_features",
    "added_runtimes",
    "lost_runtimes",
    "capacity_changes",
}
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
    rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    assert isinstance(rows, list)
    assert len(rows) > 0


def test_each_row_has_scalar_shape(ent):
    rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    for row in rows:
        assert set(row.keys()) == _ROW_KEYS, row.get("to")


def test_capacity_changes_axes_have_full_triple(ent):
    rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    for row in rows:
        for axis in ("channel_limit", "retention_days", "node_limit"):
            assert set(row["capacity_changes"][axis].keys()) == _AXIS_KEYS, (
                row["to"],
                axis,
            )


def test_excludes_trial_from_targets(ent):
    rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    ids = {row["to"] for row in rows}
    assert ent.TIER_TRIAL not in ids


def test_includes_every_purchasable_tier_as_target(ent):
    rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    ids = {row["to"] for row in rows}
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
    in lock-step with :func:`tier_diff_batch` even if the purchasable
    set ever changes."""
    rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    ids = {row["to"] for row in rows}
    assert ids == set(ent._PURCHASABLE_TIERS)


# ── ordering ─────────────────────────────────────────────────────────────────


def test_sorted_by_rank_ascending(ent):
    rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    ranks = [ent.tier_rank(row["to"]) for row in rows]
    assert ranks == sorted(ranks)


def test_same_rank_sorted_by_tier_id(ent):
    rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    by_rank: dict[int, list[str]] = {}
    for row in rows:
        by_rank.setdefault(ent.tier_rank(row["to"]), []).append(row["to"])
    for ids in by_rank.values():
        assert ids == sorted(ids)


def test_target_axis_matches_tier_diff_batch_ordering(ent):
    """The target axis is byte-stable against :func:`tier_diff_batch`'s
    ordering so a UI can swap the per-rung walking anchor for a fixed
    hypothetical anchor without re-sorting client-side."""
    at_rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    live_rows = ent.tier_diff_batch()
    assert [r["to"] for r in at_rows] == [r["to"] for r in live_rows]


def test_target_axis_matches_tier_unlocks_at_batch_ordering(ent):
    """Byte-stable against :func:`tier_unlocks_at_batch` for the same
    source tier so a UI can fold the two responses into the same
    pricing-matrix table without re-sorting."""
    diff_rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    unlock_rows = ent.tier_unlocks_at_batch(ent.TIER_OSS)
    assert [r["to"] for r in diff_rows] == [r["tier"] for r in unlock_rows]


def test_target_axis_matches_capacity_diff_at_batch_ordering(ent):
    """Byte-stable against :func:`capacity_diff_at_batch` for the same
    source tier so the full ``_at`` batch family lines up rung-for-
    rung in any matrix UI."""
    diff_rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    cap_rows = ent.capacity_diff_at_batch(ent.TIER_OSS)
    assert [r["to"] for r in diff_rows] == [r["target"] for r in cap_rows]


# ── parity with scalar tier_diff ─────────────────────────────────────────────


def test_each_row_byte_equals_scalar_tier_diff(ent):
    """Every row byte-equals ``tier_diff(tier, target)`` for the same
    pair -- the parity that stops the batch what-if drifting from the
    scalar tier_diff."""
    for src in ent._TIER_FEATURES:
        rows = ent.tier_diff_at_batch(src)
        assert rows is not None, src
        for row in rows:
            scalar = ent.tier_diff(src, row["to"])
            assert row == scalar, (src, row["to"])


# ── per-slice parity with the other _at batches ──────────────────────────────


def test_added_features_match_tier_unlocks_at_batch(ent):
    for src in ent._TIER_FEATURES:
        rows = ent.tier_diff_at_batch(src)
        unlock_rows = ent.tier_unlocks_at_batch(src)
        assert rows is not None and unlock_rows is not None, src
        unlock_by_target = {r["tier"]: r for r in unlock_rows}
        for row in rows:
            unlock = unlock_by_target[row["to"]]
            assert row["added_features"] == unlock["features"], (src, row["to"])
            assert row["added_runtimes"] == unlock["runtimes"], (src, row["to"])


def test_lost_features_match_tier_locks_at_batch(ent):
    for src in ent._TIER_FEATURES:
        rows = ent.tier_diff_at_batch(src)
        lock_rows = ent.tier_locks_at_batch(src)
        assert rows is not None and lock_rows is not None, src
        lock_by_target = {r["tier"]: r for r in lock_rows}
        for row in rows:
            lock = lock_by_target[row["to"]]
            assert row["lost_features"] == lock["lost_features"], (src, row["to"])
            assert row["lost_runtimes"] == lock["lost_runtimes"], (src, row["to"])


def test_capacity_changes_match_capacity_diff_at_batch(ent):
    for src in ent._TIER_FEATURES:
        rows = ent.tier_diff_at_batch(src)
        cap_rows = ent.capacity_diff_at_batch(src)
        assert rows is not None and cap_rows is not None, src
        cap_by_target = {r["target"]: r for r in cap_rows}
        for row in rows:
            cap = cap_by_target[row["to"]]
            for axis in ("channel_limit", "retention_days", "node_limit"):
                assert row["capacity_changes"][axis] == cap[axis], (
                    src, row["to"], axis,
                )


# ── from-side carries caller perspective (not the live walker) ───────────────


def test_from_carries_caller_perspective_on_every_row(ent):
    """``from`` on every row carries the caller-supplied source tier,
    NOT the per-rung next-lower-purchasable anchor :func:`tier_diff_batch`
    uses."""
    for src in ent._TIER_FEATURES:
        rows = ent.tier_diff_at_batch(src)
        assert rows is not None, src
        for row in rows:
            assert row["from"] == src, (src, row["to"])
            assert row["from_label"] == ent.tier_label(src), (src, row["to"])
            assert row["from_rank"] == ent.tier_rank(src), (src, row["to"])


def test_oss_source_perspective_differs_from_live_batch(ent):
    """The source-perspective batch must NOT match the live batch on
    the ``from`` axis (otherwise the helper is silently falling
    through to the live walking anchor)."""
    at_rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    live_rows = ent.tier_diff_batch()
    at_by_target = {r["to"]: r for r in at_rows}
    live_by_target = {r["to"]: r for r in live_rows}
    # Cloud-Pro's live walker anchors against starter (not OSS), so the
    # `from` axis must differ here.
    at_pro = at_by_target[ent.TIER_CLOUD_PRO]
    live_pro = live_by_target[ent.TIER_CLOUD_PRO]
    assert at_pro["from"] == ent.TIER_OSS
    assert live_pro["from"] != ent.TIER_OSS


# ── direction semantics ──────────────────────────────────────────────────────


def test_identity_row_is_identity_direction(ent):
    """The row whose target matches the source tier carries
    ``direction == 'identity'`` and empty marginal lists -- staying put
    grants and loses nothing."""
    for src in ent._PURCHASABLE_TIERS:
        rows = ent.tier_diff_at_batch(src)
        identity = next(r for r in rows if r["to"] == src)
        assert identity["direction"] == "identity", src
        assert identity["added_features"] == [], src
        assert identity["lost_features"] == [], src
        assert identity["added_runtimes"] == [], src
        assert identity["lost_runtimes"] == [], src


def test_oss_source_upgrades_have_upgrade_direction(ent):
    """From OSS, every higher-rank target carries ``direction ==
    'upgrade'``."""
    rows = ent.tier_diff_at_batch(ent.TIER_OSS)
    oss_rank = ent.tier_rank(ent.TIER_OSS)
    for row in rows:
        target_rank = ent.tier_rank(row["to"])
        if target_rank > oss_rank:
            assert row["direction"] == "upgrade", row["to"]


def test_enterprise_source_downgrades_have_downgrade_direction(ent):
    """From the ceiling tier, every lower-rank target carries
    ``direction == 'downgrade'``."""
    rows = ent.tier_diff_at_batch(ent.TIER_ENTERPRISE)
    ent_rank = ent.tier_rank(ent.TIER_ENTERPRISE)
    for row in rows:
        target_rank = ent.tier_rank(row["to"])
        if target_rank < ent_rank:
            assert row["direction"] == "downgrade", row["to"]


# ── source-axis: trial accepted (lenient _at family) ─────────────────────────


def test_trial_accepted_as_source(ent):
    rows = ent.tier_diff_at_batch(ent.TIER_TRIAL)
    assert rows is not None
    assert len(rows) == len(ent._PURCHASABLE_TIERS)
    for row in rows:
        assert row["from"] == ent.TIER_TRIAL, row["to"]


# ── every source resolves ────────────────────────────────────────────────────


def test_every_source_round_trips(ent):
    """Every id in :data:`_TIER_FEATURES` (including trial) is a valid
    source -- the helper must answer hypothetical comparisons against
    any rung in the catalog."""
    for src in ent._TIER_FEATURES:
        rows = ent.tier_diff_at_batch(src)
        assert rows is not None, src
        assert len(rows) == len(ent._PURCHASABLE_TIERS), src


# ── invalid source ───────────────────────────────────────────────────────────


def test_unknown_source_returns_none(ent):
    assert ent.tier_diff_at_batch("not_a_real_tier") is None


def test_empty_source_returns_none(ent):
    assert ent.tier_diff_at_batch("") is None


def test_none_source_returns_none(ent):
    assert ent.tier_diff_at_batch(None) is None  # type: ignore[arg-type]


def test_non_string_source_returns_none(ent):
    assert ent.tier_diff_at_batch(123) is None  # type: ignore[arg-type]
    assert ent.tier_diff_at_batch(object()) is None  # type: ignore[arg-type]


# ── normalisation ────────────────────────────────────────────────────────────


def test_source_is_lowercased_and_trimmed(ent):
    a = ent.tier_diff_at_batch(ent.TIER_OSS)
    b = ent.tier_diff_at_batch(ent.TIER_OSS.upper())
    c = ent.tier_diff_at_batch(f"  {ent.TIER_OSS}  ")
    assert a == b == c


# ── independent of live resolver ─────────────────────────────────────────────


def test_helper_ignores_grace_mode(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    ent.invalidate()
    rows_grace = ent.tier_diff_at_batch(ent.TIER_OSS)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    rows_enforce = ent.tier_diff_at_batch(ent.TIER_OSS)
    assert rows_grace == rows_enforce


def test_does_not_mutate_live_entitlement(ent):
    before = ent.get_entitlement().to_dict()
    ent.tier_diff_at_batch(ent.TIER_OSS)
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

    monkeypatch.setattr(ent, "tier_diff", boom)
    assert ent.tier_diff_at_batch(ent.TIER_OSS) == []


# ── HTTP endpoint ────────────────────────────────────────────────────────────


def test_endpoint_known_source_returns_full_ladder(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-diff-at-batch?tier={ent.TIER_OSS}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS
    assert body["tiers"] == ent.tier_diff_at_batch(ent.TIER_OSS)
    assert "current_tier" in body
    assert "current_tier_rank" in body
    assert "grace" in body
    assert "enforced" in body


def test_endpoint_lowercases_and_trims(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-diff-at-batch?tier=%20%20{ent.TIER_OSS.upper()}%20%20"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_OSS


def test_endpoint_missing_tier_returns_400(client):
    resp = client.get("/api/entitlement/tier-diff-at-batch")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_endpoint_blank_tier_returns_400(client):
    resp = client.get("/api/entitlement/tier-diff-at-batch?tier=%20%20")
    assert resp.status_code == 400


def test_endpoint_unknown_tier_returns_404(client):
    resp = client.get(
        "/api/entitlement/tier-diff-at-batch?tier=nonsense_xyz"
    )
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["which"] == "tier"
    assert body["tier"] == "nonsense_xyz"
    assert "error" in body


def test_endpoint_trial_is_accepted_as_source(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-diff-at-batch?tier={ent.TIER_TRIAL}"
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tier"] == ent.TIER_TRIAL
    assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS)


def test_endpoint_every_source_round_trips(client, ent):
    for src in ent._TIER_FEATURES:
        resp = client.get(
            f"/api/entitlement/tier-diff-at-batch?tier={src}"
        )
        assert resp.status_code == 200, src
        body = resp.get_json()
        assert body["tier"] == src, src
        assert len(body["tiers"]) == len(ent._PURCHASABLE_TIERS), src


def test_endpoint_envelope_carries_resolver_state(client, ent):
    resp = client.get(
        f"/api/entitlement/tier-diff-at-batch?tier={ent.TIER_OSS}"
    )
    body = resp.get_json()
    live = ent.get_entitlement()
    assert body["current_tier"] == live.tier
    assert body["current_tier_rank"] == ent.tier_rank(live.tier)
    assert body["grace"] == bool(live.grace)
    assert body["enforced"] == ent.is_enforced()
