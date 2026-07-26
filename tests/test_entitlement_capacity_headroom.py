"""Tests for ``Entitlement.capacity_headroom`` + the module-level helper.

``capacity_headroom`` is the resolver-pinned per-axis "how much room is
left" primitive. Companion to :func:`tiers_for_capacity_batch` (which is
decoupled from the resolver and returns the full pricing ladder). A quota
gauge or a "you're at 4/5 channels on Starter" badge reads off this single
primitive without re-deriving per-tier caps client-side.

Pins:
  * the per-axis row shape (``kind`` / ``used`` / ``cap`` / ``remaining`` /
    ``is_unlimited`` / ``at_limit`` / ``over_limit`` / ``pct_used``)
  * the ``None`` "axis not supplied" sentinel on the envelope
  * bad-input axis short-circuit (non-int / negative / blank / ``bool``)
    collapses per-axis to ``None`` so a stray query string cannot silently
    blank a gauge
  * grace-mode collapse: every axis renders unlimited while grace is open
  * the neutral envelope shape on a resolver failure (never raises)
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


# -- envelope shape --------------------------------------------------------


def test_envelope_shape(enforced):
    r = enforced._oss_free().capacity_headroom(
        channels=2, retention_days=5, nodes=1
    )
    assert set(r) == {"tier", "tier_label", "channels", "retention_days", "nodes"}
    assert r["tier"] == enforced.TIER_OSS
    assert r["tier_label"] == enforced.tier_label(enforced.TIER_OSS)


def test_row_shape(enforced):
    r = enforced._oss_free().capacity_headroom(channels=2)
    row = r["channels"]
    assert set(row) == {
        "kind", "used", "cap", "remaining", "is_unlimited",
        "at_limit", "over_limit", "pct_used",
    }
    assert row["kind"] == "channels"


# -- OSS caps concretely ---------------------------------------------------


def test_oss_channels_within_cap(enforced):
    r = enforced._oss_free().capacity_headroom(channels=2)
    row = r["channels"]
    assert row == {
        "kind": "channels",
        "used": 2,
        "cap": enforced._FREE_CHANNEL_LIMIT,
        "remaining": enforced._FREE_CHANNEL_LIMIT - 2,
        "is_unlimited": False,
        "at_limit": False,
        "over_limit": False,
        "pct_used": round(2 / enforced._FREE_CHANNEL_LIMIT * 100.0, 1),
    }


def test_oss_channels_at_limit(enforced):
    r = enforced._oss_free().capacity_headroom(
        channels=enforced._FREE_CHANNEL_LIMIT
    )
    row = r["channels"]
    assert row["at_limit"] is True
    assert row["over_limit"] is False
    assert row["remaining"] == 0
    assert row["pct_used"] == 100.0


def test_oss_channels_over_limit(enforced):
    r = enforced._oss_free().capacity_headroom(
        channels=enforced._FREE_CHANNEL_LIMIT + 5
    )
    row = r["channels"]
    assert row["over_limit"] is True
    assert row["at_limit"] is False
    assert row["remaining"] == -5
    assert row["pct_used"] > 100.0


def test_oss_retention_within(enforced):
    r = enforced._oss_free().capacity_headroom(retention_days=5)
    row = r["retention_days"]
    assert row["cap"] == 7
    assert row["used"] == 5
    assert row["remaining"] == 2
    assert row["is_unlimited"] is False
    assert row["over_limit"] is False


def test_oss_nodes_default_cap(enforced):
    r = enforced._oss_free().capacity_headroom(nodes=1)
    row = r["nodes"]
    # OSS carries the default license-bound node_limit=1.
    assert row["cap"] == 1
    assert row["at_limit"] is True
    assert row["remaining"] == 0


# -- unlimited (paid) tiers collapse row to unlimited shape ---------------


def test_starter_channels_unlimited(enforced):
    e = enforced._build(enforced.TIER_CLOUD_STARTER, "cloud", node_limit=None)
    r = e.capacity_headroom(channels=42)
    row = r["channels"]
    assert row["cap"] is None
    assert row["remaining"] is None
    assert row["is_unlimited"] is True
    assert row["at_limit"] is False
    assert row["over_limit"] is False
    assert row["pct_used"] is None


def test_pro_retention_within(enforced):
    e = enforced._build(enforced.TIER_CLOUD_PRO, "cloud", node_limit=None)
    r = e.capacity_headroom(retention_days=45)
    row = r["retention_days"]
    assert row["cap"] == 90
    assert row["is_unlimited"] is False
    assert row["remaining"] == 45


def test_enterprise_retention_unlimited(enforced):
    e = enforced._build(enforced.TIER_ENTERPRISE, "cloud", node_limit=None)
    r = e.capacity_headroom(retention_days=365)
    row = r["retention_days"]
    assert row["cap"] is None
    assert row["is_unlimited"] is True


# -- grace-mode collapse ---------------------------------------------------


def test_grace_collapses_every_axis_to_unlimited(ent):
    # Grace mode: channel_limit() returns None, nodes side is masked to
    # None by the method (grace hides the cap). Every axis should render
    # the unlimited-side shape so a gauge shows "unlimited / N used"
    # rather than a bogus percentage while grace is still open.
    r = ent._oss_free().capacity_headroom(channels=99, retention_days=1000, nodes=99)
    for kind in ("channels", "nodes"):
        row = r[kind]
        assert row["is_unlimited"] is True, kind
        assert row["cap"] is None, kind
        assert row["remaining"] is None, kind
        assert row["pct_used"] is None, kind


# -- per-axis opt-in: unsupplied axes stay None ---------------------------


def test_unsupplied_axis_is_none(enforced):
    r = enforced._oss_free().capacity_headroom(channels=2)
    assert r["channels"] is not None
    assert r["retention_days"] is None
    assert r["nodes"] is None


def test_nothing_supplied_neutral_envelope(enforced):
    r = enforced._oss_free().capacity_headroom()
    assert r["channels"] is None
    assert r["retention_days"] is None
    assert r["nodes"] is None


# -- bad-input axis short-circuit -----------------------------------------


@pytest.mark.parametrize(
    "bad_value",
    ["junk", "", None, -1, -5, True, False, [], {}],
)
def test_bad_axis_value_collapses_to_none(enforced, bad_value):
    # ``None`` for an axis means "not supplied" on the envelope so the row
    # collapses to None; every other bad value also collapses -- a stray
    # query string cannot silently blank the gauge with a 0/cap row.
    r = enforced._oss_free().capacity_headroom(channels=bad_value)
    assert r["channels"] is None


def test_bad_axis_does_not_affect_other_axes(enforced):
    r = enforced._oss_free().capacity_headroom(
        channels="junk", retention_days=5, nodes=None
    )
    assert r["channels"] is None
    assert r["retention_days"] is not None
    assert r["nodes"] is None


# -- module-level wrapper --------------------------------------------------


def test_module_level_wrapper_matches_method(enforced):
    method = enforced.get_entitlement().capacity_headroom(
        channels=2, retention_days=5, nodes=1
    )
    mod = enforced.capacity_headroom(channels=2, retention_days=5, nodes=1)
    assert method == mod


def test_module_level_never_raises_on_resolver_failure(enforced, monkeypatch):
    def _bang():
        raise RuntimeError("boom")

    monkeypatch.setattr(enforced, "get_entitlement", _bang)
    r = enforced.capacity_headroom(channels=1)
    # Neutral envelope shape -- caller keeps rendering.
    assert set(r) == {"tier", "tier_label", "channels", "retention_days", "nodes"}
    assert r["tier"] == enforced.TIER_OSS


# -- pct_used edge cases --------------------------------------------------


def test_pct_used_rounds_to_one_decimal(enforced):
    r = enforced._oss_free().capacity_headroom(channels=1)
    # 1/3 -> 33.333...% rounded to 33.3
    assert r["channels"]["pct_used"] == 33.3


def test_pct_used_zero_when_used_zero(enforced):
    r = enforced._oss_free().capacity_headroom(channels=0)
    row = r["channels"]
    assert row["used"] == 0
    assert row["pct_used"] == 0.0
    assert row["remaining"] == enforced._FREE_CHANNEL_LIMIT
