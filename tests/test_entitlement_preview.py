"""Tests for ``clawmetry.entitlements.preview`` +
``GET /api/entitlement/preview``.

Where :func:`upgrade_diff` answers "what changes", :func:`preview` answers
"what does the resulting Entitlement look like" -- the full denormalised
``to_dict()`` shape so the upgrade-CTA card can render concrete numbers
("Cloud Pro: 90-day retention, unlimited channels, claude_code unlocked")
without re-deriving per-tier capacity tables in JS. These tests pin the
shape and per-tier limits so a future reshuffle of those tables breaks
loudly here instead of silently in the UI.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def ent(monkeypatch, tmp_path):
    # preview() is grace-independent -- it always renders enforced limits --
    # but match every other entitlement fixture in the suite so the test env
    # stays identical.
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


# ── shape ─────────────────────────────────────────────────────────────────


def test_preview_returns_full_to_dict_shape(ent):
    body = ent.preview(ent.TIER_CLOUD_PRO)
    # The whole point is that the upgrade-CTA card reads the same shape as
    # /api/entitlement -- pin the contract.
    expected_keys = set(ent._build(ent.TIER_CLOUD_PRO, "preview").to_dict().keys())
    assert set(body.keys()) == expected_keys


def test_preview_tier_matches_target(ent):
    body = ent.preview(ent.TIER_CLOUD_PRO)
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["tier_label"] == ent.tier_label(ent.TIER_CLOUD_PRO)
    assert body["tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)


def test_preview_source_is_preview(ent):
    # The UI must be able to tell a preview from a live entitlement -- if a
    # preview ever leaked into the live state surface it would silently
    # over-grant. The "preview" source is the trip-wire.
    body = ent.preview(ent.TIER_CLOUD_PRO)
    assert body["source"] == "preview"


def test_preview_is_never_grace(ent, monkeypatch):
    # Grace zeroes out channel_limit / retention_days, which defeats the
    # purpose of a preview ("show concrete numbers"). Force grace ON in the
    # environment and verify preview still renders enforced limits.
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    body = ent.preview(ent.TIER_CLOUD_PRO)
    assert body["grace"] is False
    assert body["enforced"] is True


# ── per-tier limits ───────────────────────────────────────────────────────


def test_preview_oss_has_free_caps(ent):
    body = ent.preview(ent.TIER_OSS)
    assert body["retention_days"] == 7
    assert body["channel_limit"] == ent._FREE_CHANNEL_LIMIT
    # OSS doesn't unlock any paid runtimes.
    assert set(body["runtimes"]) == set(ent.FREE_RUNTIMES)


def test_preview_starter_unlocks_paid_runtimes(ent):
    body = ent.preview(ent.TIER_CLOUD_STARTER)
    assert body["retention_days"] == 30
    assert body["channel_limit"] is None  # unlimited
    assert set(body["runtimes"]) == set(ent.ALL_RUNTIMES)


def test_preview_cloud_pro_caps(ent):
    body = ent.preview(ent.TIER_CLOUD_PRO)
    assert body["retention_days"] == 90
    assert body["channel_limit"] is None
    assert set(body["features"]) == set(ent.FREE_FEATURES) | set(ent.PAID_FEATURES)


def test_preview_enterprise_includes_enterprise_features(ent):
    body = ent.preview(ent.TIER_ENTERPRISE)
    assert body["retention_days"] is None  # unlimited
    expected = (
        set(ent.FREE_FEATURES) | set(ent.PAID_FEATURES) | set(ent.ENTERPRISE_FEATURES)
    )
    assert set(body["features"]) == expected


# ── locked_* shows nothing in preview ─────────────────────────────────────


def test_preview_pro_has_no_locked_runtimes(ent):
    # In a Pro preview every paid runtime is unlocked -- locked_runtimes is
    # the inverse view and must therefore be empty so the CTA card doesn't
    # show ghost "still locked" rows.
    body = ent.preview(ent.TIER_CLOUD_PRO)
    assert body["locked_runtimes"] == []


def test_preview_enterprise_has_no_locked_features(ent):
    body = ent.preview(ent.TIER_ENTERPRISE)
    assert body["locked_features"] == []


# ── safety / fallback ─────────────────────────────────────────────────────


def test_preview_unknown_tier_returns_none(ent):
    assert ent.preview("nonsense_tier_xyz") is None


def test_preview_empty_returns_none(ent):
    assert ent.preview("") is None
    assert ent.preview(None) is None  # type: ignore[arg-type]


def test_preview_lowercases_input(ent):
    # Tier ids are case-insensitive everywhere else in the API; preview
    # mustn't be the one corner that breaks the symmetry.
    body = ent.preview("CLOUD_PRO")
    assert body is not None
    assert body["tier"] == ent.TIER_CLOUD_PRO


def test_preview_never_raises(monkeypatch, ent):
    # Force the inner build to blow up and confirm the helper swallows.
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "Entitlement", boom)
    assert ent.preview(ent.TIER_CLOUD_PRO) is None


def test_preview_does_not_mutate_live_entitlement(ent):
    # The whole module-level cache must be untouched by a preview call --
    # the rendered Entitlement is a throwaway, not a state change.
    live_before = ent.get_entitlement().to_dict()
    ent.preview(ent.TIER_ENTERPRISE)
    live_after = ent.get_entitlement().to_dict()
    assert live_before == live_after


# ── API surface ───────────────────────────────────────────────────────────


def test_api_preview_returns_shape_for_pro(client, ent):
    rv = client.get(f"/api/entitlement/preview?tier={ent.TIER_CLOUD_PRO}")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["tier"] == ent.TIER_CLOUD_PRO
    assert body["source"] == "preview"
    assert body["grace"] is False
    assert body["retention_days"] == 90


def test_api_preview_missing_tier_is_400(client):
    rv = client.get("/api/entitlement/preview")
    assert rv.status_code == 400
    assert "error" in rv.get_json()


def test_api_preview_unknown_tier_is_404(client):
    rv = client.get("/api/entitlement/preview?tier=nonsense_tier_xyz")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["tier"] == "nonsense_tier_xyz"


def test_api_preview_lowercases_query(client, ent):
    rv = client.get("/api/entitlement/preview?tier=CLOUD_STARTER")
    assert rv.status_code == 200
    assert rv.get_json()["tier"] == ent.TIER_CLOUD_STARTER
