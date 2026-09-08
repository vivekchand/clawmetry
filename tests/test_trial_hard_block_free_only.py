"""Tests for the trial-end hard-block + "continue with free runtimes" fallback.

These tests pin the two headline invariants that back the founder-policy
paywall:

1. When a trial has expired AND the hard-block is enabled (the default),
   ``is_hard_blocked`` returns True — the request-time gate 402s every
   non-allowlisted API call.

2. When the operator has opted into free-only mode (via
   ``set_free_only_mode(True)``), the gate flips to runtime-scoped:
   ``openclaw`` / ``nemoclaw`` scoped requests are allowed through so basic
   observability keeps working, but every paid-runtime scoped request stays
   blocked. This is the ONLY escape from the paywall short of activating a
   license.

The marker file lives at ``~/.clawmetry/free_only.marker``; the fixture
scopes HOME to a tmp_path so tests do not touch the developer's real
install.
"""
from __future__ import annotations

import importlib
import os
import time

import pytest


@pytest.fixture
def te(monkeypatch, tmp_path):
    """Fresh trial_enforcement + entitlements modules against an empty HOME."""
    monkeypatch.setenv("HOME", str(tmp_path))
    # Force hard-block on (matches production default).
    monkeypatch.delenv("CLAWMETRY_HARD_BLOCK", raising=False)
    monkeypatch.delenv("CLAWMETRY_HARD_BLOCK_ESCAPE", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    import clawmetry.entitlements as e
    import clawmetry.trial_enforcement as t

    importlib.reload(e)
    importlib.reload(t)
    e.invalidate()
    yield t
    # Clean up any marker the test wrote.
    try:
        t.set_free_only_mode(False)
    except Exception:
        pass
    e.invalidate()


def _expired_trial_ent():
    from clawmetry.entitlements import Entitlement, TIER_TRIAL

    return Entitlement(
        tier=TIER_TRIAL,
        source="cloud",
        node_limit=1,
        expiry=time.time() - 3600.0,  # expired 1h ago
        features=frozenset(),
        runtimes=frozenset({"openclaw", "nemoclaw"}),
        grace=False,
    )


def _active_pro_ent():
    from clawmetry.entitlements import Entitlement, TIER_PRO

    return Entitlement(
        tier=TIER_PRO,
        source="license",
        node_limit=5,
        expiry=time.time() + 86400.0 * 30,
        features=frozenset(),
        runtimes=frozenset({"openclaw", "nemoclaw", "claude_code"}),
        grace=False,
    )


def test_expired_trial_is_blocked_by_default(te):
    """Baseline: hard-block ON + expired trial ⇒ blocked."""
    assert te.hard_block_enabled() is True
    assert te.is_hard_blocked(_expired_trial_ent()) is True


def test_active_paid_is_not_blocked(te):
    """A paying customer never trips the block."""
    assert te.is_hard_blocked(_active_pro_ent()) is False


def test_hard_block_env_off_disables_block(te, monkeypatch):
    """CLAWMETRY_HARD_BLOCK=0 is the support-only opt-out."""
    monkeypatch.setenv("CLAWMETRY_HARD_BLOCK", "0")
    assert te.hard_block_enabled() is False
    assert te.is_hard_blocked(_expired_trial_ent()) is False


def test_free_only_mode_marker_persists(te):
    """set_free_only_mode(True) writes a marker; (False) removes it."""
    assert te.free_only_mode_enabled() is False
    assert te.set_free_only_mode(True) is True
    assert te.free_only_mode_enabled() is True
    assert os.path.isfile(os.path.expanduser("~/.clawmetry/free_only.marker"))
    assert te.set_free_only_mode(False) is False
    assert te.free_only_mode_enabled() is False


def test_free_only_mode_lets_openclaw_through(te):
    """Free-only + expired trial + openclaw scope ⇒ NOT blocked."""
    te.set_free_only_mode(True)
    ent = _expired_trial_ent()
    assert te.is_hard_blocked(ent, runtime="openclaw") is False
    assert te.is_hard_blocked(ent, runtime="nemoclaw") is False


def test_free_only_mode_still_blocks_paid_runtimes(te):
    """Free-only mode is not an unlock for paid runtimes."""
    te.set_free_only_mode(True)
    ent = _expired_trial_ent()
    assert te.is_hard_blocked(ent, runtime="claude_code") is True
    assert te.is_hard_blocked(ent, runtime="codex") is True
    assert te.is_hard_blocked(ent, runtime="cursor") is True


def test_free_only_mode_unknown_scope_stays_blocked(te):
    """A request with no runtime hint on an expired trial ⇒ blocked, even in
    free-only mode. The fallback is deliberately conservative — if we cannot
    prove the request is scoped to a free runtime, we treat it as paid."""
    te.set_free_only_mode(True)
    ent = _expired_trial_ent()
    assert te.is_hard_blocked(ent) is True
    assert te.is_hard_blocked(ent, path="/api/sessions") is True


def test_classify_scope_url_prefix_wins(te):
    """URL prefix classification treats /api/<paid-runtime>/* as paid scope
    even when the caller did not pass ``runtime=`` — defense in depth for any
    per-runtime shard the app may grow."""
    ent = _expired_trial_ent()
    te.set_free_only_mode(True)
    # No runtime kwarg, but path is /api/claude_code/* → paid.
    assert te.is_hard_blocked(ent, path="/api/claude_code/sessions") is True


def test_block_payload_shape(te):
    """Payload includes the free-mode toggle so the overlay can render the
    Continue-free button + note."""
    body = te.block_payload(_expired_trial_ent())
    for key in (
        "hard_blocked",
        "upgrade_url",
        "activation_endpoint",
        "refresh_endpoint",
        "free_only_endpoint",
        "exit_free_endpoint",
        "free_only_mode",
        "free_runtimes",
    ):
        assert key in body, f"block_payload missing key: {key}"
    assert body["hard_blocked"] is True
    assert body["free_only_endpoint"] == "/api/trial/continue-free"
    assert body["exit_free_endpoint"] == "/api/trial/exit-free"
    assert "openclaw" in body["free_runtimes"]


def test_allowlist_covers_new_endpoints(te):
    """Both toggle endpoints are allowlisted so the overlay can hit them while
    the rest of the app is 402-locked."""
    assert te.allowlisted_path("/api/trial/status") is True
    assert te.allowlisted_path("/api/trial/continue-free") is True
    assert te.allowlisted_path("/api/trial/exit-free") is True
    assert te.allowlisted_path("/api/trial/refresh-license") is True
    # Non-trial paths still fall through to the block.
    assert te.allowlisted_path("/api/sessions") is False
    assert te.allowlisted_path("/api/brain-history") is False
