"""Tests for ``clawmetry.entitlements.runtime_tier`` and the ``tier`` field
on ``runtime_catalog()`` rows.

Runtime side of the catalogue's tier vocabulary — mirrors the in-flight
``feature_tier()`` so the dashboard renders Runtime and Feature rows against
a single tier identifier (``"free"`` / ``"starter"`` / ``"pro"`` / ``"enterprise"``).

All paid runtimes unlock together via the Starter ``multi_runtime`` grant, so
the runtime vocabulary is intentionally smaller than the feature one:
``{"free", "starter"}``.
"""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module with a clean HOME — mirrors the fixture used
    in tests/test_entitlements_catalogue.py and tests/test_routes_runtimes.py."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── runtime_tier() helper ──────────────────────────────────────────────────────


def test_free_runtimes_tier_is_free(ent):
    assert ent.runtime_tier("openclaw") == "free"
    assert ent.runtime_tier("nemoclaw") == "free"


def test_every_free_runtime_resolves_to_free(ent):
    for rt in ent.FREE_RUNTIMES:
        assert ent.runtime_tier(rt) == "free", rt


def test_every_paid_runtime_resolves_to_starter(ent):
    for rt in ent.PAID_RUNTIMES:
        assert ent.runtime_tier(rt) == "starter", rt


def test_unknown_runtime_defaults_to_starter(ent):
    """Unknown ids err on the locked side rather than silently grant access —
    same policy ``feature_tier()`` uses for unknown feature keys."""
    assert ent.runtime_tier("totally_made_up_runtime") == "starter"
    assert ent.runtime_tier("some.other.runtime") == "starter"


def test_empty_and_none_safely_default(ent):
    assert ent.runtime_tier("") == "starter"
    assert ent.runtime_tier(None) == "starter"  # type: ignore[arg-type]


def test_case_insensitive(ent):
    assert ent.runtime_tier("OpenClaw") == "free"
    assert ent.runtime_tier("CLAUDE_CODE") == "starter"


def test_whitespace_is_stripped(ent):
    assert ent.runtime_tier("  openclaw  ") == "free"
    assert ent.runtime_tier("\tclaude_code\n") == "starter"


def test_never_raises_on_non_string_input(ent):
    """CLAUDE.md rule: never crash on bad input. Non-string ids fall back to
    the safe-default ``"starter"`` so a buggy caller can't take the gate down."""
    for weird in (123, 0, [], {}, object()):
        try:
            result = ent.runtime_tier(weird)  # type: ignore[arg-type]
        except Exception as exc:
            pytest.fail(f"runtime_tier({weird!r}) raised: {exc}")
        assert result == "starter"


# ── runtime_catalog() carries the tier field ───────────────────────────────────


def test_catalog_rows_carry_tier_field(ent):
    for row in ent.runtime_catalog():
        assert "tier" in row, row
        assert isinstance(row["tier"], str)


def test_catalog_free_rows_are_tier_free(ent):
    rows = {r["id"]: r for r in ent.runtime_catalog()}
    for rt in ent.FREE_RUNTIMES:
        assert rows[rt]["tier"] == "free", rt


def test_catalog_paid_rows_are_tier_starter(ent):
    rows = {r["id"]: r for r in ent.runtime_catalog()}
    for rt in ent.PAID_RUNTIMES:
        assert rows[rt]["tier"] == "starter", rt


def test_catalog_tier_vocabulary_is_only_free_or_starter(ent):
    """Runtime tier vocabulary is intentionally narrower than feature_tier():
    all paid runtimes unlock together via the Starter ``multi_runtime`` grant,
    so no row reports ``pro`` or ``enterprise`` tier."""
    tiers = {r["tier"] for r in ent.runtime_catalog()}
    assert tiers == {"free", "starter"}


def test_catalog_tier_matches_free_bit(ent):
    """Invariant: every ``free=True`` row is ``tier="free"`` and every
    ``free=False`` row is ``tier="starter"``."""
    for row in ent.runtime_catalog():
        if row["free"]:
            assert row["tier"] == "free", row
        else:
            assert row["tier"] == "starter", row


def test_catalog_tier_matches_runtime_tier_helper(ent):
    """``runtime_catalog()`` and ``runtime_tier()`` agree row-by-row — the
    helper is the single source of truth that the catalog reads from."""
    for row in ent.runtime_catalog():
        assert row["tier"] == ent.runtime_tier(row["id"]), row


def test_tier_is_static_across_grace_and_enforce(monkeypatch, tmp_path):
    """``tier`` is a catalogue fact (which tier *could* unlock this row), not
    an entitlement check (does THIS install have that tier). It must not
    change between grace and enforce."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    grace_tiers = {r["id"]: r["tier"] for r in e.runtime_catalog()}

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    importlib.reload(e)
    e.invalidate()
    enforce_tiers = {r["id"]: r["tier"] for r in e.runtime_catalog()}

    assert grace_tiers == enforce_tiers


def test_tier_unchanged_by_resolution_failure(ent, monkeypatch):
    """Even when ``get_entitlement()`` blows up, the catalogue still reports
    the same per-row tier (grace fallback path) — never silently drops the
    field on the error branch."""
    def _boom():
        raise RuntimeError("simulated resolution failure")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    rows = ent.runtime_catalog()
    assert rows, "fallback catalog should still be non-empty"
    for row in rows:
        assert "tier" in row, row
        assert row["tier"] in ("free", "starter"), row
