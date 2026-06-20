"""Tests for ``min_tier_for_features`` / ``min_tier_for_runtimes`` plural
helpers and the ``/api/entitlement/required-tier-batch`` endpoint.

The dashboard's upgrade-CTA copy ("you're using fleet + otel_export + sso --
Available in Enterprise") needs a single canonical reverse lookup that folds
the per-item lookup + max-by-rank into one place. The plural helpers under
test are that canonical lookup; this file pins their semantics so a future
tier shuffle breaks loudly here instead of silently in the UI.
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


# ── min_tier_for_features ──────────────────────────────────────────────────


def test_features_empty_iterable_returns_none(ent):
    assert ent.min_tier_for_features([]) is None
    assert ent.min_tier_for_features(()) is None


def test_features_none_returns_none(ent):
    assert ent.min_tier_for_features(None) is None


def test_features_all_free_returns_oss(ent):
    assert ent.min_tier_for_features(["sessions", "usage", "brain"]) == ent.TIER_OSS


def test_features_single_paid_returns_its_min(ent):
    assert ent.min_tier_for_features(["fleet"]) == ent.TIER_CLOUD_STARTER
    assert ent.min_tier_for_features(["otel_export"]) == ent.TIER_CLOUD_PRO
    assert ent.min_tier_for_features(["sso"]) == ent.TIER_ENTERPRISE


def test_features_picks_highest_rank_min(ent):
    """Most-constraining feature wins -- the answer must be the highest-rank
    ``min_tier_for_feature`` across the set, never the cheapest one."""
    assert (
        ent.min_tier_for_features(["fleet", "otel_export"]) == ent.TIER_CLOUD_PRO
    )
    assert (
        ent.min_tier_for_features(["fleet", "otel_export", "sso"])
        == ent.TIER_ENTERPRISE
    )
    assert (
        ent.min_tier_for_features(["sessions", "fleet"]) == ent.TIER_CLOUD_STARTER
    )


def test_features_unknown_items_are_skipped(ent):
    """A typo in one item must not silently mis-route to Enterprise. The
    helper skips unknowns and resolves off the known subset."""
    assert (
        ent.min_tier_for_features(["fleet", "not_a_real_feature"])
        == ent.TIER_CLOUD_STARTER
    )


def test_features_all_unknown_returns_none(ent):
    """If *every* item is unknown, the helper has no constraint to resolve
    against and returns ``None`` (matches the singular helper's posture)."""
    assert ent.min_tier_for_features(["nope", "also_nope", ""]) is None


def test_features_case_insensitive(ent):
    assert ent.min_tier_for_features(["OTEL_EXPORT", "SSO"]) == ent.TIER_ENTERPRISE


def test_features_non_iterable_returns_none(ent):
    """Never raises -- non-iterable input collapses to ``None``."""
    assert ent.min_tier_for_features(42) is None


def test_features_excludes_trial(ent):
    """Trial is a promotional grant, not a plan a customer can pick from a
    price page. The plural helper inherits that exclusion from the singular."""
    for f in ent.PAID_FEATURES | ent.ENTERPRISE_FEATURES:
        assert ent.min_tier_for_features([f]) != ent.TIER_TRIAL, f


# ── min_tier_for_runtimes ──────────────────────────────────────────────────


def test_runtimes_empty_returns_none(ent):
    assert ent.min_tier_for_runtimes([]) is None
    assert ent.min_tier_for_runtimes(None) is None


def test_runtimes_all_free_returns_oss(ent):
    assert ent.min_tier_for_runtimes(["openclaw", "nemoclaw"]) == ent.TIER_OSS


def test_runtimes_any_paid_returns_starter(ent):
    """Today every paid runtime unlocks at Starter, so any set containing one
    paid runtime resolves to Starter regardless of the rest."""
    assert ent.min_tier_for_runtimes(["claude_code"]) == ent.TIER_CLOUD_STARTER
    assert (
        ent.min_tier_for_runtimes(["claude_code", "codex"])
        == ent.TIER_CLOUD_STARTER
    )
    assert (
        ent.min_tier_for_runtimes(["openclaw", "claude_code"])
        == ent.TIER_CLOUD_STARTER
    )


def test_runtimes_unknown_skipped(ent):
    assert (
        ent.min_tier_for_runtimes(["claude_code", "not_a_runtime"])
        == ent.TIER_CLOUD_STARTER
    )


def test_runtimes_all_unknown_returns_none(ent):
    assert ent.min_tier_for_runtimes(["nope", ""]) is None


def test_runtimes_non_iterable_returns_none(ent):
    assert ent.min_tier_for_runtimes(42) is None


# ── /api/entitlement/required-tier-batch ───────────────────────────────────


def test_batch_features_only(client, ent):
    rv = client.get(
        "/api/entitlement/required-tier-batch?features=fleet,otel_export"
    )
    assert rv.status_code == 200
    d = rv.get_json()
    assert d["features"] == ["fleet", "otel_export"]
    assert d["runtimes"] == []
    assert d["required_tier"] == ent.TIER_CLOUD_PRO
    assert d["required_tier_rank"] == ent.tier_rank(ent.TIER_CLOUD_PRO)
    assert d["current_tier"] == ent.TIER_OSS
    assert d["current_tier_rank"] == 0
    assert d["upgrade_required"] is True
    assert d["allowed"] is True  # grace mode


def test_batch_runtimes_only(client, ent):
    d = client.get(
        "/api/entitlement/required-tier-batch?runtimes=claude_code,codex"
    ).get_json()
    assert d["runtimes"] == ["claude_code", "codex"]
    assert d["features"] == []
    assert d["required_tier"] == ent.TIER_CLOUD_STARTER
    assert d["upgrade_required"] is True


def test_batch_features_and_runtimes_mix(client, ent):
    """The endpoint must take the max across both axes, not just one."""
    d = client.get(
        "/api/entitlement/required-tier-batch?features=sso&runtimes=claude_code"
    ).get_json()
    assert d["required_tier"] == ent.TIER_ENTERPRISE
    assert d["required_tier_rank"] == ent.tier_rank(ent.TIER_ENTERPRISE)


def test_batch_all_free_returns_oss(client, ent):
    d = client.get(
        "/api/entitlement/required-tier-batch?features=sessions,usage&runtimes=openclaw"
    ).get_json()
    assert d["required_tier"] == ent.TIER_OSS
    assert d["upgrade_required"] is False


def test_batch_normalises_csv(client, ent):
    """Whitespace, blank tokens, and duplicates must be normalised away so
    the response payload is stable across messy input."""
    d = client.get(
        "/api/entitlement/required-tier-batch?features=otel_export,,otel_export,%20fleet%20"
    ).get_json()
    assert d["features"] == ["otel_export", "fleet"]
    assert d["required_tier"] == ent.TIER_CLOUD_PRO


def test_batch_unknown_items_skipped(client, ent):
    d = client.get(
        "/api/entitlement/required-tier-batch?features=fleet,not_a_real_feature"
    ).get_json()
    assert d["required_tier"] == ent.TIER_CLOUD_STARTER


def test_batch_all_unknown_returns_null_tier(client, ent):
    """All-unknown collapses to ``required_tier=None`` (no upgrade target),
    not a 500. Matches the singular endpoint's unknown-key posture."""
    rv = client.get(
        "/api/entitlement/required-tier-batch?features=nope,also_nope"
    )
    assert rv.status_code == 200
    d = rv.get_json()
    assert d["required_tier"] is None
    assert d["upgrade_required"] is False


def test_batch_requires_at_least_one_axis(client):
    assert client.get("/api/entitlement/required-tier-batch").status_code == 400
    assert (
        client.get("/api/entitlement/required-tier-batch?features=").status_code == 400
    )
    assert (
        client.get(
            "/api/entitlement/required-tier-batch?features=&runtimes="
        ).status_code
        == 400
    )


def test_batch_swallows_resolver_failure(monkeypatch, client, ent):
    """A flaky entitlement resolver must never 5xx the batch paywall endpoint."""
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "get_entitlement", boom)
    rv = client.get(
        "/api/entitlement/required-tier-batch?features=otel_export"
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["allowed"] is True
    assert body["current_tier"] == "oss"
    assert body["upgrade_required"] is False
