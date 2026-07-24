"""Tests for :func:`clawmetry.entitlements.capacity_headroom_at`.

Hypothetical-perspective sibling of :func:`capacity_headroom`. Fills the
``_at`` slot on the capacity-headroom axis alongside
``tiers_for_channel_count_at`` / ``tiers_for_retention_window_at`` /
``tiers_for_node_count_at``.

Pins:
  * decoupled from the resolved entitlement (grace vs enforce yields
    byte-identical rows)
  * row shape matches :func:`capacity_headroom` byte-for-byte
  * unknown / empty ``perspective_tier`` -> ``None``
  * same bad-axis short-circuit as :func:`capacity_headroom`
"""
from __future__ import annotations

import importlib

import pytest


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
def enforced(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# -- envelope + row shape parity ------------------------------------------


def test_envelope_shape(enforced):
    r = enforced.capacity_headroom_at(
        enforced.TIER_OSS, channels=2, retention_days=5, nodes=1
    )
    assert set(r) == {"tier", "tier_label", "channels", "retention_days", "nodes"}
    assert r["tier"] == enforced.TIER_OSS


def test_row_shape_parity_with_singular(enforced):
    # OSS caps are the same as the singular capacity_headroom sees on
    # a freshly-built OSS entitlement -- the two should agree row-for-row.
    at_row = enforced.capacity_headroom_at(
        enforced.TIER_OSS, channels=2
    )["channels"]
    singular = enforced._oss_free().capacity_headroom(channels=2)["channels"]
    assert at_row == singular


# -- unknown tier ---------------------------------------------------------


@pytest.mark.parametrize("bad_tier", ["", "  ", "does-not-exist", "nonesuch"])
def test_unknown_tier_returns_none(enforced, bad_tier):
    assert enforced.capacity_headroom_at(bad_tier, channels=1) is None


def test_none_tier_returns_none(enforced):
    assert enforced.capacity_headroom_at(None, channels=1) is None  # type: ignore[arg-type]


# -- concrete per-tier caps -----------------------------------------------


def test_oss_channel_cap_is_free_limit(enforced):
    r = enforced.capacity_headroom_at(enforced.TIER_OSS, channels=2)
    assert r["channels"]["cap"] == enforced._FREE_CHANNEL_LIMIT
    assert r["channels"]["is_unlimited"] is False


def test_starter_channel_cap_is_unlimited(enforced):
    r = enforced.capacity_headroom_at(
        enforced.TIER_CLOUD_STARTER, channels=99
    )
    assert r["channels"]["cap"] is None
    assert r["channels"]["is_unlimited"] is True


def test_starter_retention_cap_30d(enforced):
    r = enforced.capacity_headroom_at(
        enforced.TIER_CLOUD_STARTER, retention_days=25
    )
    row = r["retention_days"]
    assert row["cap"] == 30
    assert row["remaining"] == 5
    assert row["over_limit"] is False


def test_starter_retention_over_limit(enforced):
    r = enforced.capacity_headroom_at(
        enforced.TIER_CLOUD_STARTER, retention_days=45
    )
    row = r["retention_days"]
    assert row["over_limit"] is True
    assert row["remaining"] == -15
    assert row["pct_used"] == 150.0


def test_pro_retention_cap_90d(enforced):
    r = enforced.capacity_headroom_at(
        enforced.TIER_CLOUD_PRO, retention_days=45
    )
    assert r["retention_days"]["cap"] == 90


def test_enterprise_retention_unlimited(enforced):
    r = enforced.capacity_headroom_at(
        enforced.TIER_ENTERPRISE, retention_days=365
    )
    assert r["retention_days"]["cap"] is None
    assert r["retention_days"]["is_unlimited"] is True


# -- decoupled from resolver ----------------------------------------------


def test_grace_vs_enforce_same_row(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e_grace

    importlib.reload(e_grace)
    e_grace.invalidate()
    grace_row = e_grace.capacity_headroom_at(
        e_grace.TIER_OSS, channels=2, retention_days=5, nodes=1
    )

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as e_enf

    importlib.reload(e_enf)
    e_enf.invalidate()
    enf_row = e_enf.capacity_headroom_at(
        e_enf.TIER_OSS, channels=2, retention_days=5, nodes=1
    )

    assert grace_row == enf_row


# -- bad-input axis short-circuit -----------------------------------------


@pytest.mark.parametrize("bad_value", ["junk", "", -1, True, [], {}])
def test_bad_axis_value_collapses_to_none(enforced, bad_value):
    r = enforced.capacity_headroom_at(enforced.TIER_OSS, channels=bad_value)
    assert r["channels"] is None


def test_unsupplied_axis_is_none(enforced):
    r = enforced.capacity_headroom_at(enforced.TIER_OSS, channels=2)
    assert r["channels"] is not None
    assert r["retention_days"] is None
    assert r["nodes"] is None


# -- nothing-supplied envelope --------------------------------------------


def test_nothing_supplied_returns_envelope_with_all_none(enforced):
    r = enforced.capacity_headroom_at(enforced.TIER_OSS)
    assert r["tier"] == enforced.TIER_OSS
    assert r["channels"] is None
    assert r["retention_days"] is None
    assert r["nodes"] is None
