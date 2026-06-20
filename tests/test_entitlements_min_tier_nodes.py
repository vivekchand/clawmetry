"""Tests for :func:`clawmetry.entitlements.min_tier_for_node_count` -- the
fourth capacity-axis reverse-lookup helper, alongside
:func:`min_tier_for_channel_count` / :func:`min_tier_for_retention_window`.

The OSS free tier is a single-node grant; every paid tier carries an
unlimited per-tier ceiling (the actual cap is license-bound, surfaced through
``Entitlement.node_limit``). The helper therefore answers "what is the
cheapest *purchasable* tier whose static cap admits N registered nodes" so
the fleet page can render "you have 4 nodes -- Available in Starter" copy off
the same single source of truth the other three axes already use.

Companion to ``tests/test_entitlements_min_tier_capacity.py`` (the
channels= / retention= helper contract this file mirrors).
"""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ``~/.clawmetry/license.key`` or ``cloud_plan.json`` leaks in.
    Enforcement off by default -- matches the project rollout posture."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── happy path: within / over the free cap ─────────────────────────────────


def test_single_node_collapses_to_oss(ent):
    """1 node fits on OSS (free cap = 1). The free floor covers it."""
    assert ent.min_tier_for_node_count(1) == ent.TIER_OSS


def test_two_nodes_resolves_to_starter(ent):
    """2+ nodes need the cheapest paid tier (Starter) -- the first tier
    whose ``_TIER_NODE_LIMIT`` value is ``None`` (unlimited)."""
    assert ent.min_tier_for_node_count(2) == ent.TIER_CLOUD_STARTER


def test_large_count_still_resolves_to_starter(ent):
    """Every paid tier carries the unlimited sentinel, so even very high
    counts still resolve to the cheapest paid tier -- mirrors the channels
    axis where any count over the free cap also lands on Starter."""
    for n in (3, 10, 100, 10_000):
        assert ent.min_tier_for_node_count(n) == ent.TIER_CLOUD_STARTER, n


# ── zero / negative are trivially satisfied ────────────────────────────────


def test_zero_collapses_to_oss(ent):
    """``count == 0`` means "no nodes registered yet" -- trivially satisfied
    by the free floor. Mirrors :meth:`Entitlement.allows_node_count`'s
    zero-on-grace contract and the same posture on the channels axis."""
    assert ent.min_tier_for_node_count(0) == ent.TIER_OSS


def test_negative_collapses_to_oss(ent):
    """Stray negative values land on the free floor too -- defensive parity
    with :func:`min_tier_for_channel_count`."""
    assert ent.min_tier_for_node_count(-1) == ent.TIER_OSS
    assert ent.min_tier_for_node_count(-9999) == ent.TIER_OSS


# ── non-int / bad input ────────────────────────────────────────────────────


def test_non_int_returns_none(ent):
    """A non-int ``count`` returns ``None`` so a caller can distinguish
    "free covers it" from "couldn't parse" -- same contract the channels
    helper uses. Must never raise."""
    assert ent.min_tier_for_node_count("not-a-number") is None
    assert ent.min_tier_for_node_count(None) is None
    assert ent.min_tier_for_node_count(object()) is None


def test_numeric_string_is_accepted(ent):
    """A numeric string (``"3"``) coerces cleanly -- a fleet count read off
    a query string is already a str."""
    assert ent.min_tier_for_node_count("1") == ent.TIER_OSS
    assert ent.min_tier_for_node_count("4") == ent.TIER_CLOUD_STARTER


# ── never raises (defensive contract) ──────────────────────────────────────


def test_never_raises_on_weird_input(ent):
    """The helper is on a hot path (fleet route rendering); anything that
    would normally raise is swallowed to ``None``."""
    for bad in (object(), [], {}, b"bytes", float("nan")):
        try:
            ent.min_tier_for_node_count(bad)
        except Exception as exc:
            pytest.fail(f"min_tier_for_node_count raised on {bad!r}: {exc}")


# ── tier_catalog surface ───────────────────────────────────────────────────


def test_tier_catalog_surfaces_node_limit(ent):
    """``tier_catalog`` rows carry the static per-tier ``node_limit`` so the
    UI's plan-comparison table can render the same map the gate consumes
    (mirrors the ``channel_limit`` / ``retention_days`` columns already
    there)."""
    rows = {row["id"]: row for row in ent.tier_catalog()}
    assert rows[ent.TIER_OSS]["node_limit"] == 1
    assert rows[ent.TIER_CLOUD_FREE]["node_limit"] == 1
    for paid in (
        ent.TIER_CLOUD_STARTER,
        ent.TIER_CLOUD_PRO,
        ent.TIER_PRO,
        ent.TIER_ENTERPRISE,
    ):
        assert rows[paid]["node_limit"] is None, paid


# ── triad consistency with the other capacity helpers ──────────────────────


def test_axis_helpers_agree_on_free_floor(ent):
    """All four capacity axes collapse to OSS on zero / minimum counts --
    the canonical "free floor" invariant the dashboard relies on."""
    assert ent.min_tier_for_channel_count(0) == ent.TIER_OSS
    assert ent.min_tier_for_retention_window(0) == ent.TIER_OSS
    assert ent.min_tier_for_node_count(0) == ent.TIER_OSS
