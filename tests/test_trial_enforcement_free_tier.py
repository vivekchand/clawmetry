"""Regression: the trial-end hard-block gate must never wall off a plain
OSS/free install.

`clawmetry/trial_enforcement.py` is default-on (2026-08-06 founder policy:
trial ends -> non-dismissable modal -> payment is not opt-in). Its
`_resolver_says_unpaid_or_expired()` originally fell through to `return True`
(blocked) for ANY entitlement that wasn't `source=="license"` and wasn't
`is_paid` -- which is exactly the plain OSS / cloud_free free tier documented
in docs/ENTITLEMENTS.md, not a lapsed trial. A fresh `pip install clawmetry`
with no license and no cloud account was hard-blocked (402) on every
non-allowlisted route, confirmed live: `/api/sessions` and `/api/overview`
both returned `hard_blocked: true, source: "oss"`.

The fix: only block when there is POSITIVE evidence of a lapsed paid/trial
state (a license or cloud-plan source that WAS on a paid tier and has now
passed its expiry). Never had one -> never blocked.
"""
from __future__ import annotations

import time

import pytest


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    # hard_block_enabled() defaults True; make sure no stray env from a
    # prior test / the developer's shell flips the escape hatches and
    # silently makes every assertion here vacuously pass.
    monkeypatch.delenv("CLAWMETRY_HARD_BLOCK", raising=False)
    monkeypatch.delenv("CLAWMETRY_HARD_BLOCK_ESCAPE", raising=False)


def _ent(**kwargs):
    from clawmetry.entitlements import Entitlement
    return Entitlement(**kwargs)


def test_plain_oss_free_tier_is_never_blocked():
    from clawmetry.entitlements import TIER_OSS
    from clawmetry.trial_enforcement import is_hard_blocked

    ent = _ent(tier=TIER_OSS, source="oss", node_limit=1, expiry=None, grace=True)
    assert is_hard_blocked(ent) is False


def test_plain_cloud_free_tier_is_never_blocked():
    from clawmetry.entitlements import TIER_CLOUD_FREE
    from clawmetry.trial_enforcement import is_hard_blocked

    ent = _ent(tier=TIER_CLOUD_FREE, source="cloud", node_limit=1, expiry=None, grace=True)
    assert is_hard_blocked(ent) is False


def test_expired_trial_license_is_blocked():
    from clawmetry.entitlements import TIER_TRIAL
    from clawmetry.trial_enforcement import is_hard_blocked

    ent = _ent(
        tier=TIER_TRIAL, source="license", node_limit=1,
        expiry=time.time() - 86400, grace=True,
    )
    assert is_hard_blocked(ent) is True


def test_expired_paid_cloud_subscription_is_blocked():
    from clawmetry.entitlements import TIER_CLOUD_PRO
    from clawmetry.trial_enforcement import is_hard_blocked

    ent = _ent(
        tier=TIER_CLOUD_PRO, source="cloud", node_limit=5,
        expiry=time.time() - 3600, grace=True,
    )
    assert is_hard_blocked(ent) is True


def test_active_trial_is_not_blocked():
    from clawmetry.entitlements import TIER_TRIAL
    from clawmetry.trial_enforcement import is_hard_blocked

    ent = _ent(
        tier=TIER_TRIAL, source="license", node_limit=1,
        expiry=time.time() + 86400, grace=True,
    )
    assert is_hard_blocked(ent) is False


def test_active_paid_license_with_no_expiry_is_not_blocked():
    from clawmetry.entitlements import TIER_PRO
    from clawmetry.trial_enforcement import is_hard_blocked

    ent = _ent(tier=TIER_PRO, source="license", node_limit=10, expiry=None, grace=True)
    assert is_hard_blocked(ent) is False


def test_unreadable_entitlement_fails_closed():
    # `_resolver_says_unpaid_or_expired(None)` is the genuinely-unreadable
    # case (an entitlement object that couldn't be built at all) and must
    # fail closed. `is_hard_blocked(None)` is a DIFFERENT thing -- passing no
    # entitlement there means "resolve one live via get_entitlement()", which
    # never returns None (it falls back to a real OSS entitlement), so it is
    # covered by test_plain_oss_free_tier_is_never_blocked instead.
    from clawmetry.trial_enforcement import _resolver_says_unpaid_or_expired

    assert _resolver_says_unpaid_or_expired(None) is True


def test_hard_block_escape_hatch_bypasses_everything(monkeypatch):
    from clawmetry.entitlements import TIER_TRIAL
    from clawmetry.trial_enforcement import is_hard_blocked

    monkeypatch.setenv("CLAWMETRY_HARD_BLOCK_ESCAPE", "1")
    ent = _ent(
        tier=TIER_TRIAL, source="license", node_limit=1,
        expiry=time.time() - 86400, grace=True,
    )
    assert is_hard_blocked(ent) is False


def test_hard_block_disabled_bypasses_everything(monkeypatch):
    from clawmetry.entitlements import TIER_TRIAL
    from clawmetry.trial_enforcement import is_hard_blocked

    monkeypatch.setenv("CLAWMETRY_HARD_BLOCK", "0")
    ent = _ent(
        tier=TIER_TRIAL, source="license", node_limit=1,
        expiry=time.time() - 86400, grace=True,
    )
    assert is_hard_blocked(ent) is False
