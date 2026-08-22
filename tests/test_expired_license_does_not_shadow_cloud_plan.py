"""An EXPIRED local licence must not shadow a LIVE paid cloud plan.

`clawmetry connect` writes a 7-day signup-trial key to
``~/.clawmetry/license.key`` for every account, so a customer who then buys a
cloud plan has BOTH a licence file and a cloud plan cache on disk. Resolution
was ``_read_local_license() or _read_cloud_plan() or _oss_free()`` and
``_read_local_license`` returns an Entitlement even after its expiry passed
(``Entitlement.expired`` existed but nothing read it). So the dead trial key
kept winning, and once it lapsed the default-ON trial hard block paywalled an
account that had already paid.

Related: tests/test_trial_hard_block.py (the block itself).
"""
from __future__ import annotations

import importlib
import json
import time

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    return e, tmp_path


def _lic(e, *, tier=None, expiry=None):
    return e._build(tier or e.TIER_PRO, "license", node_limit=1, expiry=expiry)


def _cloud(e, *, tier=None, expiry=None):
    return e._build(tier or e.TIER_CLOUD_PRO, "cloud", node_limit=1, expiry=expiry)


def _readers(monkeypatch, e, lic, cloud):
    monkeypatch.setattr(e, "_read_local_license", lambda: lic)
    monkeypatch.setattr(e, "_read_cloud_plan", lambda: cloud)


def test_expired_license_yields_to_a_live_paid_cloud_plan(ent, monkeypatch):
    """The incident: a lapsed signup-trial key next to a paid cloud plan."""
    e, _ = ent
    _readers(monkeypatch, e,
             _lic(e, expiry=time.time() - 86400),
             _cloud(e, expiry=time.time() + 300 * 86400))
    got = e._resolve_best_entitlement()
    assert got.source == "cloud", "the live paid plan is the real entitlement"
    assert got.tier == e.TIER_CLOUD_PRO
    assert not got.expired


def test_live_license_still_wins_over_a_cloud_plan(ent, monkeypatch):
    """Unchanged precedence: the signed key is the strongest claim."""
    e, _ = ent
    _readers(monkeypatch, e,
             _lic(e, expiry=time.time() + 30 * 86400),
             _cloud(e, expiry=time.time() + 300 * 86400))
    assert e._resolve_best_entitlement().source == "license"


def test_license_with_no_expiry_still_wins(ent, monkeypatch):
    """A perpetual key has expiry None, which is not expired."""
    e, _ = ent
    _readers(monkeypatch, e, _lic(e, expiry=None), _cloud(e))
    assert e._resolve_best_entitlement().source == "license"


def test_expired_license_is_kept_when_the_cloud_plan_is_free(ent, monkeypatch):
    """Nothing live to promote: keep the old fallback so the paywall copy for
    a genuinely lapsed install does not change."""
    e, _ = ent
    _readers(monkeypatch, e,
             _lic(e, expiry=time.time() - 86400),
             _cloud(e, tier=e.TIER_CLOUD_FREE))
    got = e._resolve_best_entitlement()
    assert got.source == "license" and got.expired


def test_expired_license_alone_is_unchanged(ent, monkeypatch):
    e, _ = ent
    _readers(monkeypatch, e, _lic(e, expiry=time.time() - 86400), None)
    got = e._resolve_best_entitlement()
    assert got.source == "license" and got.expired


def test_no_license_no_cloud_plan_is_oss_free(ent, monkeypatch):
    e, _ = ent
    _readers(monkeypatch, e, None, None)
    assert e._resolve_best_entitlement().source == "oss"


def test_hard_block_lifts_for_a_payer_carrying_a_lapsed_trial_key(ent, monkeypatch):
    """End to end through the real cloud-plan cache file: an expired licence
    plus a paid cloud plan on disk must NOT be hard blocked."""
    e, home = ent
    (home / ".clawmetry").mkdir(parents=True, exist_ok=True)
    (home / ".clawmetry" / "cloud_plan.json").write_text(json.dumps({
        "plan": e.TIER_CLOUD_PRO,
        "node_limit": 1,
        "expiry": time.time() + 300 * 86400,
    }))
    monkeypatch.setattr(e, "_read_local_license",
                        lambda: _lic(e, expiry=time.time() - 86400))
    e.invalidate()

    resolved = e.get_entitlement(force=True)
    assert resolved.tier == e.TIER_CLOUD_PRO and resolved.source == "cloud"

    import clawmetry.trial_enforcement as te

    importlib.reload(te)
    assert te.hard_block_enabled() is True, "default-ON is the premise here"
    assert te.is_hard_blocked(resolved) is False, (
        "a paying cloud customer must never be paywalled by the lapsed "
        "signup-trial key that `clawmetry connect` left on disk"
    )
