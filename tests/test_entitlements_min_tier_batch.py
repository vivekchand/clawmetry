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


# ── min_tier_for_all (aggregate across all 5 axes) ────────────────────────


def test_all_no_constraints_returns_none(ent):
    assert ent.min_tier_for_all() is None


def test_all_features_only_matches_plural(ent):
    """Single-axis use of the aggregate must agree with the plural helper."""
    assert ent.min_tier_for_all(features=["fleet", "otel_export"]) == (
        ent.min_tier_for_features(["fleet", "otel_export"])
    )
    assert ent.min_tier_for_all(features=["sso"]) == ent.TIER_ENTERPRISE


def test_all_runtimes_only_matches_plural(ent):
    assert ent.min_tier_for_all(runtimes=["claude_code"]) == (
        ent.min_tier_for_runtimes(["claude_code"])
    )


def test_all_capacity_axes_singularly(ent):
    """Each capacity axis must resolve identically when passed via the
    aggregate vs the underlying singular helper."""
    assert ent.min_tier_for_all(channels=5) == ent.min_tier_for_channel_count(5)
    assert ent.min_tier_for_all(retention_days=30) == (
        ent.min_tier_for_retention_window(30)
    )
    assert ent.min_tier_for_all(nodes=2) == ent.min_tier_for_node_count(2)


def test_all_mixes_features_and_capacity(ent):
    """The aggregate must take the max across feature *and* capacity axes,
    not just one. ``fleet`` is Starter; 30-day retention is also Starter;
    the answer is Starter, not Pro."""
    assert ent.min_tier_for_all(features=["fleet"], retention_days=30) == (
        ent.TIER_CLOUD_STARTER
    )


def test_all_most_constraining_axis_wins(ent):
    """``otel_export`` is Pro; 5 channels is Starter; ``sso`` is Enterprise.
    The aggregate must pick Enterprise (the highest-rank constraint)."""
    assert (
        ent.min_tier_for_all(
            features=["otel_export", "sso"],
            runtimes=["claude_code"],
            channels=5,
        )
        == ent.TIER_ENTERPRISE
    )


def test_all_skips_axes_set_to_none(ent):
    """A capacity axis left at the default ``None`` must contribute
    nothing (NOT be interpreted as "unlimited retention" -> Enterprise).
    Same posture as the per-axis singular helpers being un-called."""
    assert ent.min_tier_for_all(features=["fleet"], retention_days=None) == (
        ent.TIER_CLOUD_STARTER
    )


def test_all_unknown_features_dont_misroute(ent):
    """A typo in features must not silently push the aggregate to a higher
    tier -- unknown ids contribute nothing."""
    assert ent.min_tier_for_all(features=["fleet", "not_a_real_feature"]) == (
        ent.TIER_CLOUD_STARTER
    )


def test_all_all_axes_collapse_to_none(ent):
    """Every axis going None (empty / unknown / non-int) collapses the
    aggregate to ``None`` -- never a 500."""
    assert ent.min_tier_for_all(
        features=[],
        runtimes=[],
        channels="not-a-number",  # type: ignore[arg-type]
    ) is None


# ── /api/entitlement/required-tier-batch -- capacity axes ─────────────────


def test_batch_channels_only(client, ent):
    """Channels axis alone must resolve like the singular endpoint."""
    d = client.get(
        "/api/entitlement/required-tier-batch?channels=5"
    ).get_json()
    assert d["channels"] == 5
    assert d["features"] == []
    assert d["runtimes"] == []
    assert d["required_tier"] == ent.min_tier_for_channel_count(5)
    assert d["upgrade_required"] is True
    assert d["allowed"] is True  # grace mode


def test_batch_retention_only(client, ent):
    d = client.get(
        "/api/entitlement/required-tier-batch?retention_days=30"
    ).get_json()
    assert d["retention_days"] == 30
    assert d["required_tier"] == ent.min_tier_for_retention_window(30)


def test_batch_nodes_only(client, ent):
    d = client.get(
        "/api/entitlement/required-tier-batch?nodes=3"
    ).get_json()
    assert d["nodes"] == 3
    assert d["required_tier"] == ent.min_tier_for_node_count(3)


def test_batch_mixes_all_five_axes(client, ent):
    """The whole point: a dashboard call mixing features + runtimes +
    capacity must resolve to the most-constraining tier in one round-trip."""
    d = client.get(
        "/api/entitlement/required-tier-batch"
        "?features=fleet&runtimes=claude_code&channels=5&retention_days=30&nodes=2"
    ).get_json()
    assert d["features"] == ["fleet"]
    assert d["runtimes"] == ["claude_code"]
    assert d["channels"] == 5
    assert d["retention_days"] == 30
    assert d["nodes"] == 2
    assert d["required_tier"] == ent.min_tier_for_all(
        features=["fleet"],
        runtimes=["claude_code"],
        channels=5,
        retention_days=30,
        nodes=2,
    )


def test_batch_capacity_alone_satisfies_at_least_one_axis(client):
    """Supplying only a capacity axis (no features/runtimes) must NOT 400
    -- the "at least one axis" rule now covers all five."""
    assert client.get(
        "/api/entitlement/required-tier-batch?channels=5"
    ).status_code == 200
    assert client.get(
        "/api/entitlement/required-tier-batch?retention_days=30"
    ).status_code == 200
    assert client.get(
        "/api/entitlement/required-tier-batch?nodes=3"
    ).status_code == 200


def test_batch_blank_capacity_treated_as_unsupplied(client):
    """A blank or non-int capacity value must be treated as "not supplied"
    (NOT mis-routed to Enterprise via the retention-None=unlimited
    sentinel). With ALL inputs blank, the endpoint must 400."""
    rv = client.get(
        "/api/entitlement/required-tier-batch?channels=&retention_days=&nodes="
    )
    assert rv.status_code == 400


def test_batch_non_int_capacity_silently_skipped(client, ent):
    """A non-int capacity is the never-crash path: that axis contributes
    nothing, the resolution uses the remaining axes."""
    d = client.get(
        "/api/entitlement/required-tier-batch?features=fleet&channels=abc"
    ).get_json()
    assert d["features"] == ["fleet"]
    assert d["channels"] is None
    assert d["required_tier"] == ent.TIER_CLOUD_STARTER
