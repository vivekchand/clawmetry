"""Tests for clawmetry/entitlements.py — open-core entitlement resolution.

Validates the grace-vs-enforce behaviour, the free/paid runtime split,
graceful fallback on bad input, and the /api/entitlement JSON shape.

The headline invariant: with no license + no cloud plan + no CLAWMETRY_ENFORCE,
the resolver returns OSS-free in GRACE mode where every allows_* check passes,
so wiring the gate in changes no behaviour.
"""
from __future__ import annotations

import importlib
import json
import time

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so no
    real ~/.clawmetry/license.key or cloud_plan.json leaks in. Enforcement off
    by default."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)  # re-expand ~ against the patched HOME
    e.invalidate()
    yield e
    e.invalidate()


# ── grace mode (default) ──────────────────────────────────────────────────────


def test_default_is_oss_free_in_grace(ent):
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_OSS
    assert en.source == "oss"
    assert en.grace is True
    assert en.is_paid is False
    assert en.expired is False


def test_grace_allows_everything(ent):
    en = ent.get_entitlement(force=True)
    # Paid runtimes + paid features all pass while in grace.
    assert en.allows_runtime("claude_code") is True
    assert en.allows_runtime("openclaw") is True
    assert en.allows_feature("otel_export") is True
    assert en.allows_feature("custom_alerts") is True


def test_available_runtimes_grace_shows_all(ent):
    assert set(ent.available_runtimes()) == set(ent.ALL_RUNTIMES)


# ── enforce mode ───────────────────────────────────────────────────────────────


def test_enforce_blocks_paid_runtime(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.grace is False
    assert en.tier == ent.TIER_OSS
    assert en.allows_runtime("openclaw") is True          # free stays free
    assert en.allows_runtime("claude_code") is False      # paid is blocked
    assert en.allows_feature("custom_alerts") is False
    # core features are always free even when enforced
    assert en.allows_feature("sessions") is True


def test_available_runtimes_enforced_oss_is_free_only(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    assert ent.available_runtimes() == sorted(ent.FREE_RUNTIMES)


def test_is_enforced_env_parsing(ent, monkeypatch):
    for v in ("1", "true", "YES", "On"):
        monkeypatch.setenv("CLAWMETRY_ENFORCE", v)
        assert ent.is_enforced() is True
    for v in ("0", "false", "", "no"):
        monkeypatch.setenv("CLAWMETRY_ENFORCE", v)
        assert ent.is_enforced() is False


# ── catalogue invariants ────────────────────────────────────────────────────────


def test_free_runtimes_is_openclaw_and_nemoclaw(ent):
    # NVIDIA NemoClaw is a free-tier agent runtime alongside OpenClaw
    # (issue #2289). NeMo *governance* is a separate free feature.
    assert ent.FREE_RUNTIMES == frozenset({"openclaw", "nemoclaw"})
    assert "claude_code" in ent.PAID_RUNTIMES
    assert "nemoclaw" not in ent.PAID_RUNTIMES
    assert ent.FREE_RUNTIMES.isdisjoint(ent.PAID_RUNTIMES)


def test_nemo_governance_is_a_free_feature(ent):
    assert "nemo_governance" in ent.FREE_FEATURES


# ── cloud plan cache (stub source) ───────────────────────────────────────────────


def test_cloud_plan_cache_grants_tier(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro", "node_limit": 10, "expiry": None}))
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_CLOUD_PRO
    assert en.source == "cloud"
    assert en.node_limit == 10
    assert en.is_paid is True


def test_expired_cloud_plan_blocks_when_enforced(ent, tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro", "node_limit": 5, "expiry": time.time() - 60}))
    en = ent.get_entitlement(force=True)
    assert en.expired is True
    assert en.allows_runtime("claude_code") is False  # expired => no paid runtime


# ── robustness ────────────────────────────────────────────────────────────────


def test_corrupt_cloud_plan_falls_back_to_oss(ent, tmp_path):
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("{not valid json")
    en = ent.get_entitlement(force=True)
    assert en.tier == ent.TIER_OSS  # never raises, falls through


def test_to_dict_shape(ent):
    d = ent.get_entitlement(force=True).to_dict()
    for key in ("tier", "source", "grace", "enforced", "retention_days",
                "runtimes", "features", "all_runtimes"):
        assert key in d
    assert d["enforced"] == (not d["grace"])
    assert isinstance(d["runtimes"], list)


def test_to_dict_retention_days_oss_is_seven(ent):
    """OSS-free surfaces the 7-day retention cap so the UI can render it."""
    d = ent.get_entitlement(force=True).to_dict()
    assert d["retention_days"] == 7


@pytest.mark.parametrize(
    "plan,expected",
    [
        ("cloud_free", 7),
        ("cloud_starter", 30),
        ("trial", 30),
        ("cloud_pro", 90),
        ("pro", 90),
        ("enterprise", None),
    ],
)
def test_to_dict_retention_days_matches_tier(ent, monkeypatch, tmp_path, plan, expected):
    """Every tier surfaces its retention cap through ``to_dict()`` — and
    Enterprise's "unlimited / custom" reads as ``None`` (JSON ``null``) so the
    UI can render the special-case copy instead of a number.

    Mirrors the per-tier values in ``_TIER_RETENTION_DAYS`` (see also
    ``tests/test_entitlements_catalogue.py``). Pinning this here means a
    silent retention-cap change in the table now breaks the API contract too,
    not just the method.
    """
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": plan, "node_limit": 1, "expiry": None}))
    d = ent.get_entitlement(force=True).to_dict()
    assert d["tier"] == plan
    assert d["retention_days"] == expected


# ── runtime_catalog (Phase 5: locked-but-visible foundation) ────────────────


def test_runtime_catalog_grace_locks_nothing(ent):
    cat = ent.runtime_catalog()
    # Every known runtime is present exactly once.
    ids = [r["id"] for r in cat]
    assert set(ids) == set(ent.ALL_RUNTIMES)
    assert len(ids) == len(set(ids))
    # Free runtimes first, paid runtimes after — stable ordering.
    free_count = len(ent.FREE_RUNTIMES)
    assert set(ids[:free_count]) == set(ent.FREE_RUNTIMES)
    assert set(ids[free_count:]) == set(ent.PAID_RUNTIMES)
    # Grace mode: nothing is locked, everything is allowed.
    for row in cat:
        assert row["allowed"] is True
        assert row["locked"] is False
        assert isinstance(row["label"], str) and row["label"]
        # `free` matches FREE_RUNTIMES membership.
        assert row["free"] == (row["id"] in ent.FREE_RUNTIMES)


def test_runtime_catalog_enforced_oss_locks_paid(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cat = {r["id"]: r for r in ent.runtime_catalog()}
    # Free stays free + allowed.
    for rt in ent.FREE_RUNTIMES:
        assert cat[rt]["allowed"] is True
        assert cat[rt]["locked"] is False
    # Every paid runtime is locked when enforced + no entitlement.
    for rt in ent.PAID_RUNTIMES:
        assert cat[rt]["allowed"] is False, rt
        assert cat[rt]["locked"] is True, rt


def test_runtime_catalog_labels_match_paid_runtimes(ent):
    # Every paid runtime has a human-readable label (not just the id) so the
    # UI never has to guess. Catches "added a runtime but forgot the label".
    for rt in ent.PAID_RUNTIMES | ent.FREE_RUNTIMES:
        assert rt in ent.RUNTIME_LABELS, rt
        assert ent.RUNTIME_LABELS[rt], rt


def test_runtime_label_falls_back_to_id(ent):
    assert ent.runtime_label("openclaw") == "OpenClaw"
    # Unknown runtime → graceful fallback to the id so plugin runtimes still
    # render with *something* in the UI.
    assert ent.runtime_label("brand_new_plugin_runtime") == "brand_new_plugin_runtime"
    assert ent.runtime_label("") == ""
    assert ent.runtime_label(None) == ""


# ── paid-tier coverage (issue #2293) ─────────────────────────────────────────


def test_paid_runtimes_exact_membership(ent):
    # Asserts the exact 10-entry PAID_RUNTIMES set so any accidental add/remove
    # breaks loudly instead of silently skipping gate coverage.
    expected = frozenset(
        {
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
        }
    )
    assert ent.PAID_RUNTIMES == expected
    assert len(ent.PAID_RUNTIMES) == 10


def test_all_paid_runtimes_blocked_on_oss_enforced(ent, monkeypatch):
    """Every entry in PAID_RUNTIMES is denied for an OSS install once enforced."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    en = ent.get_entitlement(force=True)
    assert en.grace is False
    for rt in ent.PAID_RUNTIMES:
        assert en.allows_runtime(rt) is False, rt
    # Free runtimes are never blocked regardless of enforcement.
    for rt in ent.FREE_RUNTIMES:
        assert en.allows_runtime(rt) is True, rt


def test_paid_runtimes_allowed_on_paid_tiers_enforced(ent, monkeypatch, tmp_path):
    """Every paid runtime is allowed on trial / pro / cloud_pro even with
    CLAWMETRY_ENFORCE=1 — the gate must pass for legitimate subscribers."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    for tier in (ent.TIER_TRIAL, ent.TIER_PRO, ent.TIER_CLOUD_PRO):
        cache.write_text(json.dumps({"plan": tier, "node_limit": 1, "expiry": None}))
        en = ent.get_entitlement(force=True)
        assert en.tier == tier, tier
        assert en.grace is False, tier
        for rt in ent.PAID_RUNTIMES:
            assert en.allows_runtime(rt) is True, f"{tier}/{rt}"
        for rt in ent.FREE_RUNTIMES:
            assert en.allows_runtime(rt) is True, f"{tier}/{rt}"


# ── grace teaser (#1532: entitled is grace-INDEPENDENT) ─────────────────────


def test_entitled_runtime_is_grace_independent(ent):
    """REGRESSION GUARD for the dead conversion surface: in grace mode
    allows_runtime says True for everything, which the UI read as 'working'
    so the upgrade affordance never rendered (12 paywall views in 30 days
    fleet-wide). `entitled_runtime` must report the PLAN fact regardless of
    grace."""
    en = ent.get_entitlement(force=True)
    assert en.grace is True
    # Grace allows...
    assert en.allows_runtime("claude_code") is True
    # ...but the OSS-free plan does NOT entitle paid runtimes.
    for rt in ent.PAID_RUNTIMES:
        assert en.entitled_runtime(rt) is False, rt
    for rt in ent.FREE_RUNTIMES:
        assert en.entitled_runtime(rt) is True, rt


def test_runtime_catalog_carries_entitled_in_grace(ent):
    cat = {r["id"]: r for r in ent.runtime_catalog()}
    for rt in ent.PAID_RUNTIMES:
        assert cat[rt]["entitled"] is False, rt
        # Enforcement semantics unchanged: grace still does not LOCK.
        assert cat[rt]["locked"] is False, rt
        assert cat[rt]["allowed"] is True, rt
    for rt in ent.FREE_RUNTIMES:
        assert cat[rt]["entitled"] is True, rt


def test_entitled_tier_entitles_its_runtimes(ent):
    en = ent.Entitlement(tier="pro", runtimes=set(ent.ALL_RUNTIMES),
                         features=set(), grace=True, source="test")
    assert en.entitled_runtime("claude_code") is True
    assert en.entitled_runtime("cursor") is True


# -- CLAWMETRY_ENFORCE_AT (grace countdown) -------------------------


def test_enforce_at_unset_is_none(ent, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ENFORCE_AT", raising=False)
    assert ent.enforce_at_epoch() is None
    en = ent.get_entitlement(force=True)
    assert en.grace_remaining_days() is None
    d = en.to_dict()
    assert d["enforce_at"] is None
    assert d["enforce_at_iso"] is None
    assert d["days_until_enforce"] is None


def test_enforce_at_iso_date_future(ent, monkeypatch):
    # ~30 days out
    future = time.time() + 30 * 86400
    from datetime import datetime, timezone
    iso = datetime.fromtimestamp(future, tz=timezone.utc).date().isoformat()
    monkeypatch.setenv("CLAWMETRY_ENFORCE_AT", iso)
    at = ent.enforce_at_epoch()
    assert at is not None
    en = ent.get_entitlement(force=True)
    days = en.grace_remaining_days()
    assert days is not None and 25 <= days <= 31  # tolerate UTC midnight rounding
    d = en.to_dict()
    assert d["enforce_at"] == pytest.approx(at)
    assert d["enforce_at_iso"] is not None and d["enforce_at_iso"].endswith("Z")
    assert d["days_until_enforce"] == days


def test_enforce_at_epoch_seconds_accepted(ent, monkeypatch):
    future = time.time() + 7 * 86400
    monkeypatch.setenv("CLAWMETRY_ENFORCE_AT", str(int(future)))
    en = ent.get_entitlement(force=True)
    assert en.grace_remaining_days() in (6, 7)
    assert en.to_dict()["enforce_at"] == pytest.approx(float(int(future)))


def test_enforce_at_iso_datetime_z_suffix(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE_AT", "2099-01-01T00:00:00Z")
    en = ent.get_entitlement(force=True)
    d = en.to_dict()
    assert d["enforce_at"] is not None
    assert d["enforce_at_iso"] == "2099-01-01T00:00:00Z"
    assert d["days_until_enforce"] is not None and d["days_until_enforce"] > 0


def test_enforce_at_past_clamps_to_zero(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE_AT", "2000-01-01")
    en = ent.get_entitlement(force=True)
    # Past moment: countdown is 0, never negative.
    assert en.grace_remaining_days() == 0
    d = en.to_dict()
    assert d["days_until_enforce"] == 0
    assert d["enforce_at"] is not None


def test_enforce_at_malformed_is_graceful(ent, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE_AT", "not-a-date")
    assert ent.enforce_at_epoch() is None
    en = ent.get_entitlement(force=True)
    d = en.to_dict()
    assert d["enforce_at"] is None
    assert d["enforce_at_iso"] is None
    assert d["days_until_enforce"] is None


def test_enforce_at_independent_of_enforce_flag(ent, monkeypatch):
    """Setting the countdown env var must NOT flip grace -> enforce. Only
    CLAWMETRY_ENFORCE does that."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE_AT", "2099-01-01")
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    en = ent.get_entitlement(force=True)
    assert en.grace is True
    assert en.allows_runtime("claude_code") is True


# ── canonical_runtime + RUNTIME_ALIASES ─────────────────────────────────────


def test_canonical_runtime_passthrough_for_known_ids(ent):
    for rt in ent.ALL_RUNTIMES:
        assert ent.canonical_runtime(rt) == rt


def test_canonical_runtime_resolves_aliases(ent):
    cases = {
        "claude-code": "claude_code",
        "claudecode": "claude_code",
        "qwen-code": "qwen_code",
        "qwencode": "qwen_code",
        "open-code": "opencode",
        "open_code": "opencode",
        "open-claw": "openclaw",
        "open_claw": "openclaw",
        "nemo-claw": "nemoclaw",
        "nemo_claw": "nemoclaw",
        "pico-claw": "picoclaw",
        "pico_claw": "picoclaw",
        "nano-claw": "nanoclaw",
        "nano_claw": "nanoclaw",
    }
    for alias, canonical in cases.items():
        assert ent.canonical_runtime(alias) == canonical, alias


def test_canonical_runtime_is_case_insensitive(ent):
    assert ent.canonical_runtime("CLAUDE-CODE") == "claude_code"
    assert ent.canonical_runtime("  Claude-Code  ") == "claude_code"
    assert ent.canonical_runtime("OpenClaw") == "openclaw"


def test_canonical_runtime_unknown_passes_through_lowercased(ent):
    assert ent.canonical_runtime("brand_new_plugin_runtime") == "brand_new_plugin_runtime"
    assert ent.canonical_runtime("BRAND_NEW") == "brand_new"


def test_canonical_runtime_empty_and_none_safe(ent):
    assert ent.canonical_runtime("") == ""
    assert ent.canonical_runtime(None) == ""
    assert ent.canonical_runtime("   ") == ""


def test_runtime_label_resolves_via_aliases(ent):
    # Aliases now hit the same label as the canonical id, so UI strings stay
    # consistent regardless of which form the caller passed in.
    assert ent.runtime_label("claude-code") == "Claude Code"
    assert ent.runtime_label("CLAUDECODE") == "Claude Code"
    assert ent.runtime_label("qwen-code") == "Qwen Code"
    assert ent.runtime_label("open-claw") == "OpenClaw"


def test_runtime_aliases_all_resolve_to_known_runtimes(ent):
    # Every alias value must be a canonical runtime — otherwise the alias is
    # mapping to nothing the gate or label lookup understands.
    for alias, canonical in ent.RUNTIME_ALIASES.items():
        assert canonical in ent.ALL_RUNTIMES, alias
        # The alias key itself must NOT already be a canonical id (an alias
        # for itself is dead weight).
        assert alias not in ent.ALL_RUNTIMES, alias


def test_appjs_teaser_wiring():
    """The catalog loader must use `entitled` (grace teaser) and must NOT
    early-return when enforcement is off, while guarding hosted paying/trial
    accounts via CLOUD_PLAN/_account. Mirrors the two-renderer-mirror rule:
    server flag + JS consumer must move together."""
    import os
    appjs = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "clawmetry", "static", "js", "app.js")
    src = open(appjs).read()
    i = src.find("async function _cmLoadRuntimeCatalog")
    assert i != -1
    block = src[i:i + 2500]
    assert "entitled === false" in block, "loader must consume the entitled flag"
    assert "!cat.enforced" not in block, "loader must not bail out in grace mode"
    assert "CLOUD_PLAN" in block and "_account" in block, (
        "hosted paying/trial guard missing"
    )
