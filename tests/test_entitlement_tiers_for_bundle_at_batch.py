"""Tests for the perspective-scoped bundle-batch
``/api/entitlement/tiers-for-features-at-batch`` and
``/api/entitlement/tiers-for-runtimes-at-batch`` endpoints (plus their
:func:`clawmetry.entitlements.tiers_for_features_at_batch` /
:func:`clawmetry.entitlements.tiers_for_runtimes_at_batch` helpers).

Fills the ``_at_batch`` slot on the bundle-axis tiers-for family alongside
the existing ``/min-tier-for-features-at-batch`` /
``/min-tier-for-runtimes-at-batch`` (per-bundle cheapest tier what-if) and
``/affordable-tiers-at-batch`` (per-item plural what-if) so a pricing-
matrix / upgrade-walkthrough can call ``X_at(perspective, ...)`` uniformly
across every ``_at`` batch sibling.

These tests pin:

  * helper: perspective validation (empty / non-string / unknown -> None)
  * helper: per-row parity with the bare batch (rows are perspective-
    independent -- the ``_at`` prefix does NOT shape rows)
  * helper: bundle normalisation, unknown-id bucketing, runtime alias
    canonicalisation inherit from the bare batch delegate
  * helper: never raises on a delegate crash
  * API: happy path shape and envelope keys
  * API: per-row body byte-equals the bare batch endpoint body
  * API: 400 on missing ``tier=`` / missing / empty / non-list ``bundles``
  * API: 404 on unknown ``tier=``
  * API: never-5xxs on a delegate crash (returns fallback envelope)
  * grace vs enforce yields byte-identical per-row bodies
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


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
def client(ent):
    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    return app.test_client()


# ── helper: features_at_batch ────────────────────────────────────────────


def test_helper_features_at_batch_returns_list(ent):
    rows = ent.tiers_for_features_at_batch(
        ent.TIER_CLOUD_STARTER, [["fleet"], ["otel_export"]]
    )
    assert isinstance(rows, list)
    assert len(rows) == 2


def test_helper_features_at_batch_row_shape(ent):
    rows = ent.tiers_for_features_at_batch(
        ent.TIER_CLOUD_STARTER, [["fleet", "sso"]]
    )
    row = rows[0]
    assert set(row.keys()) == {
        "items",
        "unknown",
        "kind",
        "count",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert row["kind"] == "features"


def test_helper_features_at_batch_empty_perspective_is_none(ent):
    assert ent.tiers_for_features_at_batch("", [["fleet"]]) is None


def test_helper_features_at_batch_none_perspective_is_none(ent):
    assert ent.tiers_for_features_at_batch(None, [["fleet"]]) is None


def test_helper_features_at_batch_unknown_perspective_is_none(ent):
    assert (
        ent.tiers_for_features_at_batch("no-such-tier", [["fleet"]]) is None
    )


def test_helper_features_at_batch_non_string_perspective_is_none(ent):
    assert ent.tiers_for_features_at_batch(42, [["fleet"]]) is None


def test_helper_features_at_batch_row_equals_bare_batch(ent):
    """Rows are perspective-independent -- byte-equal to the bare-batch
    delegate. Pinned across every known tier including TIER_TRIAL."""
    bundles = [["fleet", "sso"], ["otel_export"], []]
    bare = ent.tiers_for_features_batch(bundles)
    for perspective in ent._TIER_ORDER:
        assert (
            ent.tiers_for_features_at_batch(perspective, bundles) == bare
        )


def test_helper_features_at_batch_row_equals_singular(ent):
    for bundle in (["fleet", "sso"], ["otel_export"], ["fleet", "bogus"], []):
        rows = ent.tiers_for_features_at_batch(
            ent.TIER_CLOUD_PRO, [bundle]
        )
        assert rows[0] == ent.tiers_for_features(bundle)


def test_helper_features_at_batch_none_bundles_delegates_to_empty(ent):
    # Delegate returns [] for None; the _at wrapper preserves that.
    assert ent.tiers_for_features_at_batch(ent.TIER_CLOUD_STARTER, None) == []


def test_helper_features_at_batch_non_iterable_bundles(ent):
    assert ent.tiers_for_features_at_batch(ent.TIER_CLOUD_STARTER, 123) == []


def test_helper_features_at_batch_never_raises(ent, monkeypatch):
    def _boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tiers_for_features_batch", _boom)
    assert (
        ent.tiers_for_features_at_batch(
            ent.TIER_CLOUD_STARTER, [["fleet"]]
        )
        is None
    )


# ── helper: runtimes_at_batch ────────────────────────────────────────────


def test_helper_runtimes_at_batch_row_shape(ent):
    rows = ent.tiers_for_runtimes_at_batch(
        ent.TIER_CLOUD_STARTER, [["openclaw"]]
    )
    assert set(rows[0].keys()) == {
        "items",
        "unknown",
        "kind",
        "count",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }
    assert rows[0]["kind"] == "runtimes"


def test_helper_runtimes_at_batch_canonicalises_alias(ent):
    rows = ent.tiers_for_runtimes_at_batch(
        ent.TIER_CLOUD_STARTER, [["claude-code"]]
    )
    assert rows[0]["items"] == ["claude_code"]
    assert rows[0]["unknown"] == []


def test_helper_runtimes_at_batch_row_equals_bare_batch(ent):
    bundles = [["claude_code", "codex"], ["openclaw"], []]
    bare = ent.tiers_for_runtimes_batch(bundles)
    for perspective in ent._TIER_ORDER:
        assert (
            ent.tiers_for_runtimes_at_batch(perspective, bundles) == bare
        )


def test_helper_runtimes_at_batch_empty_perspective_is_none(ent):
    assert ent.tiers_for_runtimes_at_batch("", [["openclaw"]]) is None


def test_helper_runtimes_at_batch_unknown_perspective_is_none(ent):
    assert (
        ent.tiers_for_runtimes_at_batch("no-such-tier", [["openclaw"]])
        is None
    )


def test_helper_runtimes_at_batch_never_raises(ent, monkeypatch):
    def _boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "tiers_for_runtimes_batch", _boom)
    assert (
        ent.tiers_for_runtimes_at_batch(
            ent.TIER_CLOUD_STARTER, [["openclaw"]]
        )
        is None
    )


# ── perspective independence ─────────────────────────────────────────────


def test_helper_features_at_batch_grace_vs_enforce_same_rows(
    monkeypatch, ent
):
    bundles = [["fleet", "sso"], ["otel_export"], []]
    grace_rows = ent.tiers_for_features_at_batch(
        ent.TIER_CLOUD_STARTER, bundles
    )
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    enforce_rows = ent.tiers_for_features_at_batch(
        ent.TIER_CLOUD_STARTER, bundles
    )
    assert grace_rows == enforce_rows


# ── API: features at batch ───────────────────────────────────────────────


def test_api_features_at_batch_happy_path(client, ent):
    r = client.post(
        "/api/entitlement/tiers-for-features-at-batch?tier=cloud_starter",
        json={"bundles": [["fleet", "sso"], ["otel_export"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert set(body.keys()) >= {
        "bundles",
        "count",
        "current_tier",
        "current_tier_rank",
        "grace",
        "enforced",
        "perspective_tier",
        "perspective_tier_label",
        "perspective_tier_rank",
    }
    assert body["count"] == 2
    assert body["perspective_tier"] == "cloud_starter"
    assert body["bundles"][0]["kind"] == "features"


def test_api_features_at_batch_row_shape(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-at-batch?tier=cloud_pro",
        json={"bundles": [["fleet", "sso"]]},
    )
    row = r.get_json()["bundles"][0]
    assert set(row.keys()) == {
        "items",
        "unknown",
        "kind",
        "count",
        "min_tier",
        "min_tier_label",
        "min_tier_rank",
        "tiers",
    }


def test_api_features_at_batch_row_byte_equals_bare_batch(client, ent):
    bundles = [["fleet", "sso"], ["otel_export"], []]
    r_at = client.post(
        "/api/entitlement/tiers-for-features-at-batch?tier=cloud_starter",
        json={"bundles": bundles},
    )
    r_bare = client.post(
        "/api/entitlement/tiers-for-features-batch",
        json={"bundles": bundles},
    )
    assert r_at.status_code == 200
    assert r_bare.status_code == 200
    at_body = r_at.get_json()
    bare_body = r_bare.get_json()
    assert at_body["bundles"] == bare_body["bundles"]


def test_api_features_at_batch_row_byte_equals_singular(client, ent):
    bundles = [["fleet", "sso"], ["otel_export"], []]
    r = client.post(
        "/api/entitlement/tiers-for-features-at-batch?tier=cloud_pro",
        json={"bundles": bundles},
    )
    body = r.get_json()
    for row, bundle in zip(body["bundles"], bundles):
        assert row == ent.tiers_for_features(bundle)


def test_api_features_at_batch_missing_tier_400(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-at-batch",
        json={"bundles": [["fleet"]]},
    )
    assert r.status_code == 400
    assert "tier" in r.get_json()["error"]


def test_api_features_at_batch_unknown_tier_404(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-at-batch?tier=no-such-tier",
        json={"bundles": [["fleet"]]},
    )
    assert r.status_code == 404
    body = r.get_json()
    assert "unknown" in body["error"]
    assert body["tier"] == "no-such-tier"


def test_api_features_at_batch_missing_bundles_400(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-at-batch?tier=cloud_starter",
        json={},
    )
    assert r.status_code == 400
    assert "bundles" in r.get_json()["error"]


def test_api_features_at_batch_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-at-batch?tier=cloud_starter",
        json={"bundles": []},
    )
    assert r.status_code == 400
    assert "empty" in r.get_json()["error"]


def test_api_features_at_batch_non_list_bundles_400(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-at-batch?tier=cloud_starter",
        json={"bundles": "fleet,sso"},
    )
    assert r.status_code == 400


def test_api_features_at_batch_bare_list_of_strings_is_one_bundle(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-at-batch?tier=cloud_starter",
        json={"bundles": ["fleet", "sso"]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 1
    assert body["bundles"][0]["items"] == ["fleet", "sso"]


def test_api_features_at_batch_never_5xxs_on_delegate_crash(
    client, monkeypatch, ent
):
    def _boom(*_a, **_k):
        raise RuntimeError("resolver on fire")

    monkeypatch.setattr(ent, "tiers_for_features_at_batch", _boom)
    r = client.post(
        "/api/entitlement/tiers-for-features-at-batch?tier=cloud_starter",
        json={"bundles": [["fleet"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["bundles"] == []
    assert body["count"] == 0
    assert body["perspective_tier"] == "cloud_starter"


def test_api_features_at_batch_all_unknown_row_still_populates(client):
    r = client.post(
        "/api/entitlement/tiers-for-features-at-batch?tier=cloud_starter",
        json={"bundles": [["bogus"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    row = body["bundles"][0]
    assert row["items"] == []
    assert row["unknown"] == ["bogus"]
    assert row["min_tier"] is None
    assert row["tiers"] == []


# ── API: runtimes at batch ───────────────────────────────────────────────


def test_api_runtimes_at_batch_happy_path(client):
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-at-batch?tier=cloud_starter",
        json={"bundles": [["claude_code", "codex"], ["openclaw"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 2
    assert body["bundles"][0]["kind"] == "runtimes"
    assert body["perspective_tier"] == "cloud_starter"


def test_api_runtimes_at_batch_row_byte_equals_bare_batch(client, ent):
    bundles = [["claude_code", "codex"], ["openclaw"], []]
    r_at = client.post(
        "/api/entitlement/tiers-for-runtimes-at-batch?tier=cloud_pro",
        json={"bundles": bundles},
    )
    r_bare = client.post(
        "/api/entitlement/tiers-for-runtimes-batch",
        json={"bundles": bundles},
    )
    assert r_at.status_code == 200
    assert r_bare.status_code == 200
    assert r_at.get_json()["bundles"] == r_bare.get_json()["bundles"]


def test_api_runtimes_at_batch_canonicalises_alias(client):
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-at-batch?tier=cloud_starter",
        json={"bundles": [["claude-code"]]},
    )
    body = r.get_json()
    assert body["bundles"][0]["items"] == ["claude_code"]


def test_api_runtimes_at_batch_missing_tier_400(client):
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-at-batch",
        json={"bundles": [["openclaw"]]},
    )
    assert r.status_code == 400


def test_api_runtimes_at_batch_unknown_tier_404(client):
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-at-batch?tier=no-such-tier",
        json={"bundles": [["openclaw"]]},
    )
    assert r.status_code == 404


def test_api_runtimes_at_batch_missing_bundles_400(client):
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-at-batch?tier=cloud_starter",
        json={},
    )
    assert r.status_code == 400


def test_api_runtimes_at_batch_empty_bundles_400(client):
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-at-batch?tier=cloud_starter",
        json={"bundles": []},
    )
    assert r.status_code == 400


def test_api_runtimes_at_batch_never_5xxs_on_delegate_crash(
    client, monkeypatch, ent
):
    def _boom(*_a, **_k):
        raise RuntimeError("resolver on fire")

    monkeypatch.setattr(ent, "tiers_for_runtimes_at_batch", _boom)
    r = client.post(
        "/api/entitlement/tiers-for-runtimes-at-batch?tier=cloud_starter",
        json={"bundles": [["openclaw"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["bundles"] == []
    assert body["count"] == 0
    assert body["perspective_tier"] == "cloud_starter"


# ── envelope parity ──────────────────────────────────────────────────────


def test_api_at_batch_envelope_carries_perspective(client, ent):
    r = client.post(
        "/api/entitlement/tiers-for-features-at-batch?tier=cloud_pro",
        json={"bundles": [["fleet"]]},
    )
    body = r.get_json()
    assert body["perspective_tier"] == "cloud_pro"
    assert body["perspective_tier_label"] == ent.tier_label("cloud_pro")
    assert body["perspective_tier_rank"] == ent.tier_rank("cloud_pro")
    ent_obj = ent.get_entitlement()
    assert body["current_tier"] == ent_obj.tier
    assert body["current_tier_rank"] == ent.tier_rank(ent_obj.tier)
    assert body["grace"] is bool(ent_obj.grace)
    assert body["enforced"] is ent.is_enforced()


def test_api_at_batch_perspective_trial_allowed(client, ent):
    """``TIER_TRIAL`` is a valid perspective (matches every other ``_at``
    sibling) even though it is not purchasable."""
    r = client.post(
        f"/api/entitlement/tiers-for-features-at-batch?tier={ent.TIER_TRIAL}",
        json={"bundles": [["fleet"]]},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["perspective_tier"] == ent.TIER_TRIAL
