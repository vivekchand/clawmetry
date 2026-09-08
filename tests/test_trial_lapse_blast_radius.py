"""Who the trial paywall may and may not block.

Derived from the real prod population (2026-08-15, users table):

    plan       trial_used  trial_end   count
    free       f           null         3439   <- never trialed, MUST NOT block
    trial      t           past         2378   <- lapsed, MUST block
    trial      t           future        351   <- live trial, MUST NOT block
    free       t           past           40   <- lapsed, MUST block
    cloud_pro  f           null           21   <- paying, MUST NOT block
    cloud_pro  t           past            5   <- paying, once trialed, MUST NOT block

Two bugs this pins, both caught by checking that table before shipping:

1. Stamping trial_end as the entitlement expiry for a PAID tier hard-blocks a
   paying subscriber. Signup is trial-by-default, so every paying customer has
   trial_used=True and a trial_end in the past -- the 5 rows above today, and
   every future one.
2. plan='trial_expired' (what _effective_plan returns for the 2378 rows) was not
   in _HEARTBEAT_PLAN_TO_TIER, so the daemon DELETED cloud_plan.json and lost
   the trial verdict. The paywall would have armed for 40 accounts and missed
   the 2378 it exists for.
"""

import json
import os
import sys
import tempfile
import time

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

DAY = 86400.0


def _resolve(tmp_path, **plan_fields):
    """Write cloud_plan.json and resolve the entitlement + block verdict."""
    from clawmetry import entitlements as ent, trial_enforcement as te
    os.makedirs(os.path.dirname(ent._CLOUD_PLAN_CACHE), exist_ok=True)
    with open(ent._CLOUD_PLAN_CACHE, "w") as fh:
        json.dump(plan_fields, fh)
    ent.invalidate()
    e = ent.get_entitlement(force=True)
    return e, te.is_hard_blocked(e, path="/api/sessions")


def _isolate(monkeypatch, tmp_path):
    """Point the resolver's import-time cache path into a tmp dir."""
    from clawmetry import entitlements as ent
    monkeypatch.setattr(ent, "_CLOUD_PLAN_CACHE",
                        str(tmp_path / ".clawmetry" / "cloud_plan.json"))
    monkeypatch.setattr(ent, "_LICENSE_PATH", str(tmp_path / ".clawmetry" / "nope.key"))
    monkeypatch.delenv("CLAWMETRY_HARD_BLOCK", raising=False)
    monkeypatch.delenv("CLAWMETRY_HARD_BLOCK_ESCAPE", raising=False)


def test_paying_customer_who_once_trialed_is_never_blocked(monkeypatch, tmp_path):
    """The 5 cloud_pro rows with a past trial_end. Bricking a live subscriber is
    the worst failure this system can have.

    Asserts the state the daemon ACTUALLY writes for them: a paid plan whose
    expiry stays None even though trial_used/trial_end say the trial is long
    gone. (A paid plan with a genuinely past expiry -- a lapsed subscription --
    SHOULD still block; that is a different case and stays blocked.)"""
    _isolate(monkeypatch, tmp_path)
    past = time.time() - 30 * DAY
    e, blocked = _resolve(tmp_path, plan="cloud_pro", node_limit=5,
                          expiry=None, trial_end=past, trial_used=True)
    assert blocked is False, "a paying subscriber must never be hard-blocked"
    assert e.expired is False, "a paid tier must not inherit the trial's expiry"
    assert e.allows_runtime("claude_code") is True


def test_paid_starter_who_once_trialed_is_never_blocked(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    past = time.time() - 10 * DAY
    e, blocked = _resolve(tmp_path, plan="cloud_starter", node_limit=1,
                          expiry=None, trial_end=past, trial_used=True)
    assert blocked is False
    assert e.allows_runtime("claude_code") is True


def test_genuinely_lapsed_subscription_still_blocks(monkeypatch, tmp_path):
    """The paid-tier carve-out above is scoped to the TRIAL's date, not a free
    pass: a paid plan whose own expiry has passed must still block, or a
    cancelled subscription would keep working forever."""
    _isolate(monkeypatch, tmp_path)
    past = time.time() - 5 * DAY
    e, blocked = _resolve(tmp_path, plan="cloud_pro", node_limit=5,
                          expiry=past, trial_end=None, trial_used=True)
    assert blocked is True
    assert e.allows_runtime("claude_code") is False


def test_lapsed_trial_is_blocked(monkeypatch, tmp_path):
    """The 2378 + 40 rows."""
    _isolate(monkeypatch, tmp_path)
    past = time.time() - 2 * DAY
    e, blocked = _resolve(tmp_path, plan="cloud_free", node_limit=1,
                          expiry=past, trial_end=past, trial_used=True)
    assert blocked is True
    assert e.allows_runtime("claude_code") is False
    assert e.allows_runtime("openclaw") is True, "free runtimes always survive"


def test_live_trial_is_not_blocked(monkeypatch, tmp_path):
    """The 351 rows mid-trial."""
    _isolate(monkeypatch, tmp_path)
    future = time.time() + 3 * DAY
    e, blocked = _resolve(tmp_path, plan="cloud_free", node_limit=1,
                          expiry=future, trial_end=future, trial_used=True)
    assert blocked is False
    assert e.allows_runtime("claude_code") is True


def test_never_trialed_is_not_blocked(monkeypatch, tmp_path):
    """The 3439 rows. Blocking these bricks every fresh pip install."""
    _isolate(monkeypatch, tmp_path)
    e, blocked = _resolve(tmp_path, plan="cloud_free", node_limit=1, expiry=None)
    assert blocked is False
    assert e.allows_runtime("claude_code") is True


# ── the heartbeat plan mapping ──────────────────────────────────────────────

def test_trial_expired_maps_to_cloud_free_not_none():
    """_effective_plan returns 'trial_expired' for the 2378. If that is not in
    the map the daemon deletes cloud_plan.json, the trial verdict is lost, and
    the paywall silently misses the entire population it was built for."""
    import clawmetry.sync as s
    assert s._HEARTBEAT_PLAN_TO_TIER.get("trial_expired") == "cloud_free"


def test_persist_writes_lapse_verdict_for_trial_expired(monkeypatch, tmp_path):
    """End to end through the daemon's own writer: a trial_expired heartbeat
    must leave a cache that blocks, not an absent file."""
    import clawmetry.sync as s
    from clawmetry import entitlements as ent, trial_enforcement as te
    cache = str(tmp_path / ".clawmetry" / "cloud_plan.json")
    monkeypatch.setattr(s, "_CLOUD_PLAN_CACHE_PATH", cache)
    monkeypatch.setattr(ent, "_CLOUD_PLAN_CACHE", cache)
    monkeypatch.setattr(ent, "_LICENSE_PATH", str(tmp_path / "nope.key"))
    monkeypatch.delenv("CLAWMETRY_HARD_BLOCK", raising=False)

    past_iso = "2026-08-13T08:44:45.286492Z"
    s._persist_cloud_plan_to_disk("trial_expired", None,
                                  trial_end=past_iso, trial_used=True)
    assert os.path.isfile(cache), "cache must be written, not deleted"
    written = json.load(open(cache))
    assert written["plan"] == "cloud_free"
    assert written["trial_used"] is True
    assert written["expiry"] is not None

    ent.invalidate()
    e = ent.get_entitlement(force=True)
    assert te.is_hard_blocked(e, path="/api/sessions") is True
    assert e.allows_runtime("claude_code") is False


def test_persist_does_not_expire_a_paid_plan_from_trial_end(monkeypatch, tmp_path):
    """Same path, paid tier: the trial_end must not become the expiry."""
    import clawmetry.sync as s
    from clawmetry import entitlements as ent, trial_enforcement as te
    cache = str(tmp_path / ".clawmetry" / "cloud_plan.json")
    monkeypatch.setattr(s, "_CLOUD_PLAN_CACHE_PATH", cache)
    monkeypatch.setattr(ent, "_CLOUD_PLAN_CACHE", cache)
    monkeypatch.setattr(ent, "_LICENSE_PATH", str(tmp_path / "nope.key"))
    monkeypatch.delenv("CLAWMETRY_HARD_BLOCK", raising=False)

    s._persist_cloud_plan_to_disk("pro", None,
                                  trial_end="2026-08-13T08:44:45Z", trial_used=True)
    written = json.load(open(cache))
    assert written["plan"] == "cloud_pro"
    assert written["expiry"] is None, \
        "a paid plan must not inherit the trial_end as its expiry"

    ent.invalidate()
    e = ent.get_entitlement(force=True)
    assert te.is_hard_blocked(e, path="/api/sessions") is False
