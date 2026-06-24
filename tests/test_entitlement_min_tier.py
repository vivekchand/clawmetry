"""Tests for the ``min_tier_for_feature`` / ``min_tier_for_runtime`` helpers,
the ``tier_label`` / ``tier_rank`` metadata accessors, the ``to_dict`` surface,
and the companion ``/api/entitlement/min-tier`` endpoint.

The dashboard's locked-row CTA (paid runtime / paid feature) needs a single,
canonical "cheapest tier that unlocks X" lookup so the JS doesn't re-derive
the ladder. These tests pin the per-feature / per-runtime answer so a future
catalogue shuffle (a feature moves from Starter to Pro, a runtime is renamed)
breaks loudly here rather than silently downgrading the CTA copy.

The headline invariants:

* Free features / free runtimes resolve to ``TIER_OSS`` so the CTA can short
  to "Already included" rather than a paid tier.
* Starter features resolve to ``TIER_CLOUD_STARTER`` and Pro-only features
  resolve to ``TIER_CLOUD_PRO`` (cloud upsell wins the same-rank tie against
  the self-hosted ``pro`` license).
* Enterprise-only features resolve to ``TIER_ENTERPRISE``.
* Trial is never the answer (it's promotional, not purchasable).
* Unknown inputs return ``None`` / a 404 envelope — no nonsense tier.
* Catalogue-derived: identical answer in grace and enforce mode.
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


# ── tier_label / tier_rank ──────────────────────────────────────────────────


def test_tier_label_known_tiers(ent):
    assert ent.tier_label(ent.TIER_OSS) == "OSS"
    assert ent.tier_label(ent.TIER_CLOUD_FREE) == "Free"
    assert ent.tier_label(ent.TIER_CLOUD_STARTER) == "Starter"
    assert ent.tier_label(ent.TIER_TRIAL) == "Trial"
    assert ent.tier_label(ent.TIER_CLOUD_PRO) == "Pro"
    assert ent.tier_label(ent.TIER_PRO) == "Pro (Self-hosted)"
    assert ent.tier_label(ent.TIER_ENTERPRISE) == "Enterprise"


def test_tier_label_unknown_falls_back_to_id(ent):
    # A misconfigured plan with an unknown tier id should still render with
    # *something* — the id itself — rather than crash the CTA copy.
    assert ent.tier_label("nonsense_tier_xyz") == "nonsense_tier_xyz"


def test_tier_label_empty_falls_back_to_unknown(ent):
    assert ent.tier_label("") == "Unknown"
    assert ent.tier_label(None) == "Unknown"


def test_tier_rank_orders_ladder(ent):
    # The ladder must be strictly monotonic in the canonical upgrade order:
    # OSS/Free (0) < Starter (1) < Pro (2) < Enterprise (3).
    assert ent.tier_rank(ent.TIER_OSS) == 0
    assert ent.tier_rank(ent.TIER_CLOUD_FREE) == 0
    assert ent.tier_rank(ent.TIER_CLOUD_STARTER) == 1
    assert ent.tier_rank(ent.TIER_TRIAL) == 2
    assert ent.tier_rank(ent.TIER_CLOUD_PRO) == 2
    assert ent.tier_rank(ent.TIER_PRO) == 2
    assert ent.tier_rank(ent.TIER_ENTERPRISE) == 3


def test_tier_rank_unknown_is_floor(ent):
    # An unknown tier id maps to floor rank, matching the OSS-free fallback
    # in get_entitlement (the resolver returns floor rather than crashing).
    assert ent.tier_rank("nonsense_tier_xyz") == 0
    assert ent.tier_rank("") == 0


def test_tier_rank_case_insensitive(ent):
    # Tier ids are normalised lowercase everywhere; the rank lookup must too.
    assert ent.tier_rank("CLOUD_STARTER") == 1
    assert ent.tier_rank("Enterprise") == 3


# ── min_tier_for_feature ────────────────────────────────────────────────────


def test_min_tier_free_feature_is_oss(ent):
    # Free features are always available; the CTA short-circuits to
    # "Already included" rather than recommending an upsell.
    for feat in ("sessions", "transcripts", "usage", "brain", "nemo_governance"):
        assert ent.min_tier_for_feature(feat) == ent.TIER_OSS


def test_min_tier_starter_feature_is_cloud_starter(ent):
    # Multi-runtime, fleet, cloud sync etc. unlock at Starter.
    for feat in (
        "multi_runtime",
        "fleet",
        "cloud_sync",
        "all_channels",
        "approval_queue",
        "budget_limits",
        "per_runtime_health_timeline",
    ):
        assert ent.min_tier_for_feature(feat) == ent.TIER_CLOUD_STARTER, feat


def test_min_tier_pro_only_feature_is_cloud_pro(ent):
    # Pro-only features tie at rank 2 between cloud_pro / pro / trial. Trial
    # is excluded (not purchasable); cloud_pro beats pro on the lexical
    # tiebreak so the standard cloud upsell wins.
    for feat in (
        "per_run_waste_flags",
        "self_evolve",
        "eval_suite",
        "tool_policy",
        "otel_export",
        "custom_alerts",
        "custom_webhooks",
        "custom_runtime_ingest",
        "anomaly_detection",
        "cost_optimizer",
    ):
        assert ent.min_tier_for_feature(feat) == ent.TIER_CLOUD_PRO, feat


def test_min_tier_enterprise_only_feature_is_enterprise(ent):
    for feat in (
        "siem_export",
        "sso",
        "audit_logs",
        "rbac",
        "air_gapped_license",
        "custom_data_residency",
    ):
        assert ent.min_tier_for_feature(feat) == ent.TIER_ENTERPRISE, feat


def test_min_tier_unknown_feature_is_none(ent):
    # A misconfigured paywall ping with an unknown feature id must not point
    # the operator at a nonsense tier — return None so the caller can render
    # a neutral "not available" hint.
    assert ent.min_tier_for_feature("nonsense_feature_xyz") is None
    assert ent.min_tier_for_feature("") is None
    assert ent.min_tier_for_feature(None) is None


def test_min_tier_never_returns_trial(ent):
    # Trial is granted, not sold; no feature should ever advertise it as the
    # cheapest unlock. Pins the _PURCHASABLE_TIERS exclusion against an
    # accidental future include.
    for feat in ent.ALL_FEATURES:
        assert ent.min_tier_for_feature(feat) != ent.TIER_TRIAL


def test_min_tier_grace_and_enforce_match(ent, monkeypatch):
    # The helper is catalogue-derived (it answers "where would this be
    # unlocked", not "is it unlocked right now") so flipping enforce must not
    # change the answer.
    grace = ent.min_tier_for_feature("custom_alerts")
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(ent)
    ent.invalidate()
    assert ent.min_tier_for_feature("custom_alerts") == grace


# ── min_tier_for_runtime ────────────────────────────────────────────────────


def test_min_tier_free_runtime_is_oss(ent):
    for rt in ("openclaw", "nemoclaw"):
        assert ent.min_tier_for_runtime(rt) == ent.TIER_OSS


def test_min_tier_paid_runtime_is_cloud_starter(ent):
    # Every paid runtime unlocks at the cheapest paid tier (Starter) — there
    # is no per-runtime tier carve-out.
    for rt in (
        "claude_code",
        "codex",
        "cursor",
        "aider",
        "goose",
        "opencode",
        "qwen_code",
        "hermes",
        "picoclaw",
        "nanoclaw",
    ):
        assert ent.min_tier_for_runtime(rt) == ent.TIER_CLOUD_STARTER, rt


def test_min_tier_unknown_runtime_is_none(ent):
    assert ent.min_tier_for_runtime("nonsense_runtime") is None
    assert ent.min_tier_for_runtime("") is None
    assert ent.min_tier_for_runtime(None) is None


def test_min_tier_runtime_case_insensitive(ent):
    # Runtime ids are normalised lowercase; uppercase input should still
    # resolve.
    assert ent.min_tier_for_runtime("CLAUDE_CODE") == ent.TIER_CLOUD_STARTER
    assert ent.min_tier_for_runtime("OpenClaw") == ent.TIER_OSS


# ── to_dict surface ─────────────────────────────────────────────────────────


def test_to_dict_carries_tier_label_and_rank(ent):
    body = ent._oss_free().to_dict()
    assert body["tier"] == ent.TIER_OSS
    assert body["tier_label"] == "OSS"
    assert body["tier_rank"] == 0


def test_to_dict_paid_tier_label_and_rank(ent):
    body = ent._build(ent.TIER_CLOUD_PRO, "cloud").to_dict()
    assert body["tier_label"] == "Pro"
    assert body["tier_rank"] == 2


# ── /api/entitlement/min-tier ───────────────────────────────────────────────


def test_endpoint_feature_free_returns_oss(client, ent):
    rv = client.get("/api/entitlement/min-tier?feature=sessions")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["key"] == "feature"
    assert body["value"] == "sessions"
    assert body["free"] is True
    assert body["min_tier"] == ent.TIER_OSS
    assert body["tier_label"] == "OSS"
    assert body["tier_rank"] == 0


def test_endpoint_feature_starter(client, ent):
    rv = client.get("/api/entitlement/min-tier?feature=multi_runtime")
    body = rv.get_json()
    assert rv.status_code == 200
    assert body["free"] is False
    assert body["min_tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == "Starter"
    assert body["tier_rank"] == 1


def test_endpoint_feature_pro(client, ent):
    rv = client.get("/api/entitlement/min-tier?feature=custom_alerts")
    body = rv.get_json()
    assert body["min_tier"] == ent.TIER_CLOUD_PRO
    assert body["tier_rank"] == 2


def test_endpoint_feature_enterprise(client, ent):
    rv = client.get("/api/entitlement/min-tier?feature=siem_export")
    body = rv.get_json()
    assert body["min_tier"] == ent.TIER_ENTERPRISE
    assert body["tier_rank"] == 3


def test_endpoint_runtime_free(client, ent):
    rv = client.get("/api/entitlement/min-tier?runtime=openclaw")
    body = rv.get_json()
    assert rv.status_code == 200
    assert body["key"] == "runtime"
    assert body["value"] == "openclaw"
    assert body["free"] is True
    assert body["min_tier"] == ent.TIER_OSS


def test_endpoint_runtime_paid(client, ent):
    rv = client.get("/api/entitlement/min-tier?runtime=claude_code")
    body = rv.get_json()
    assert body["min_tier"] == ent.TIER_CLOUD_STARTER
    assert body["tier_label"] == "Starter"


def test_endpoint_unknown_feature_404(client):
    rv = client.get("/api/entitlement/min-tier?feature=nonsense")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["min_tier"] is None
    assert body["tier_label"] is None
    assert body["error"] == "unknown"


def test_endpoint_unknown_runtime_404(client):
    rv = client.get("/api/entitlement/min-tier?runtime=nonsense")
    assert rv.status_code == 404
    body = rv.get_json()
    assert body["min_tier"] is None


def test_endpoint_requires_exactly_one_arg(client):
    # No args → 400.
    rv = client.get("/api/entitlement/min-tier")
    assert rv.status_code == 400
    # Both args → 400 (ambiguous: which one is being asked about?).
    rv = client.get(
        "/api/entitlement/min-tier?feature=sessions&runtime=openclaw"
    )
    assert rv.status_code == 400


def test_endpoint_never_5xx_on_resolver_failure(client, ent, monkeypatch):
    # Synthesise a resolver failure; the envelope must stay 200 with a
    # null-shaped body so the dashboard CTA keeps rendering instead of
    # disappearing.
    def boom(*_, **__):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(ent, "min_tier_for_feature", boom)
    rv = client.get("/api/entitlement/min-tier?feature=multi_runtime")
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["min_tier"] is None
    assert body["tier_label"] is None
    assert body["key"] == "feature"
    assert body["value"] == "multi_runtime"


def test_endpoint_envelope_keys(client):
    # Pin the envelope shape so a downstream consumer can rely on every key
    # being present regardless of free/paid/unknown branch.
    rv = client.get("/api/entitlement/min-tier?feature=sessions")
    body = rv.get_json()
    for key in ("key", "value", "free", "min_tier", "tier_label", "tier_rank"):
        assert key in body, key
