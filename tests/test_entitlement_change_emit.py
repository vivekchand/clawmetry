"""Tests for the ``entitlement.changed`` extension-bus emit.

``clawmetry/entitlements.py`` fires ``entitlement.changed`` through
``clawmetry/extensions.py`` on every tier transition so the closed-source
``clawmetry-pro`` plugin (and any other listener) can react when
``clawmetry license activate`` / ``deactivate`` or the daemon's cloud-plan
cache writes a new tier.

Headline invariants pinned here:

* First fresh resolution emits exactly once with ``previous_tier=None``.
* Cache hits and resolutions that land on the same tier do NOT re-emit
  (so the every-minute cache refresh never spams the bus).
* A genuine tier transition (OSS -> cloud_pro via a cloud_plan cache write)
  fires a second emit with the right ``previous_tier`` / ``tier`` pair.
* Concurrent fresh resolves never double-emit the initial tier.
* A listener raising never propagates out of ``get_entitlement``.
* An ``ImportError`` on ``clawmetry.extensions`` (defensive) never crashes
  resolution.
"""
from __future__ import annotations

import importlib
import json
import threading

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Fresh entitlements module rooted at an empty HOME, enforcement off,
    listener registry snapshotted/restored, and the emit memo reset."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    import clawmetry.extensions as ext_mod
    import clawmetry.entitlements as e

    importlib.reload(e)  # re-expand ~ against the patched HOME
    e.invalidate()
    e._last_emitted_tier = None

    # Snapshot the event registry so listeners registered by a test can't
    # leak into the next one.
    saved_registry = {k: list(v) for k, v in ext_mod._registry.items()}
    ext_mod._registry.clear()

    try:
        yield e
    finally:
        e.invalidate()
        e._last_emitted_tier = None
        ext_mod._registry.clear()
        ext_mod._registry.update({k: list(v) for k, v in saved_registry.items()})


def _listen(ext_mod):
    """Register a list-collecting listener and return the list."""
    received: list[dict] = []
    ext_mod.register("entitlement.changed", lambda p: received.append(p))
    return received


def _write_cloud_plan(home, plan="cloud_pro", node_limit=5, expiry=None):
    """Drop a cloud_plan.json with ``plan`` so the resolver picks it up."""
    cm = home / ".clawmetry"
    cm.mkdir(parents=True, exist_ok=True)
    payload = {"plan": plan, "node_limit": node_limit}
    if expiry is not None:
        payload["expiry"] = expiry
    (cm / "cloud_plan.json").write_text(json.dumps(payload))


# ── first emit ───────────────────────────────────────────────────────────────


def test_first_resolution_emits_once(ent):
    import clawmetry.extensions as ext_mod
    received = _listen(ext_mod)

    ent.get_entitlement(force=True)
    assert len(received) == 1
    e0 = received[0]
    assert e0["tier"] == ent.TIER_OSS
    assert e0["previous_tier"] is None
    assert e0["source"] == "oss"
    assert e0["is_paid"] is False
    assert e0["grace"] is True


def test_listener_registered_after_resolution_misses_initial_emit(ent):
    """The bus is fire-and-forget; a listener that registers AFTER the first
    resolution does not retroactively hear the initial tier. Documenting the
    contract so the operator knows to call ``get_entitlement`` themselves
    when probing current state."""
    import clawmetry.extensions as ext_mod
    ent.get_entitlement(force=True)  # initial emit lands in the void
    received = _listen(ext_mod)
    ent.get_entitlement(force=True)
    assert received == []  # same tier -> silent


# ── steady-state silence ─────────────────────────────────────────────────────


def test_same_tier_resolution_does_not_re_emit(ent):
    import clawmetry.extensions as ext_mod
    received = _listen(ext_mod)
    ent.get_entitlement(force=True)
    ent.get_entitlement(force=True)
    ent.get_entitlement(force=True)
    assert len(received) == 1  # only the initial transition None -> oss


def test_cache_hit_does_not_emit(ent):
    """Within the 60s cache TTL, get_entitlement() returns the memoised
    Entitlement without re-running resolution or the emit hook."""
    import clawmetry.extensions as ext_mod
    ent.get_entitlement(force=True)  # primes cache + fires initial emit
    received = _listen(ext_mod)
    for _ in range(10):
        ent.get_entitlement()  # no force=True -> cache-hit path
    assert received == []


def test_invalidate_then_same_tier_still_quiet(ent):
    """``invalidate()`` busts the cache but NOT the emit memo, so a
    re-resolve that lands on the same tier stays silent. (The "did we
    actually transition?" question is independent of "is the cache hot?")."""
    import clawmetry.extensions as ext_mod
    ent.get_entitlement(force=True)
    received = _listen(ext_mod)
    ent.invalidate()
    ent.get_entitlement(force=True)
    assert received == []


# ── real tier transitions ───────────────────────────────────────────────────


def test_oss_to_cloud_pro_transition_emits(ent, tmp_path):
    import clawmetry.extensions as ext_mod
    received = _listen(ext_mod)

    ent.get_entitlement(force=True)
    assert received[-1]["tier"] == ent.TIER_OSS

    _write_cloud_plan(tmp_path, plan="cloud_pro", node_limit=11)
    ent.invalidate()
    ent.get_entitlement(force=True)

    assert len(received) == 2
    e1 = received[1]
    assert e1["previous_tier"] == ent.TIER_OSS
    assert e1["tier"] == ent.TIER_CLOUD_PRO
    assert e1["source"] == "cloud"
    assert e1["is_paid"] is True


def test_paid_to_oss_transition_emits(ent, tmp_path):
    """Activating then deactivating a license fires both transitions."""
    import clawmetry.extensions as ext_mod
    received = _listen(ext_mod)

    _write_cloud_plan(tmp_path, plan="cloud_starter", node_limit=3)
    ent.get_entitlement(force=True)
    # Remove the cache file so the next force-refresh resolves OSS.
    (tmp_path / ".clawmetry" / "cloud_plan.json").unlink()
    ent.invalidate()
    ent.get_entitlement(force=True)

    tiers = [(e["previous_tier"], e["tier"]) for e in received]
    assert tiers == [
        (None, ent.TIER_CLOUD_STARTER),
        (ent.TIER_CLOUD_STARTER, ent.TIER_OSS),
    ]


# ── never-raise contract ────────────────────────────────────────────────────


def test_misbehaving_listener_does_not_break_resolution(ent):
    import clawmetry.extensions as ext_mod

    def boom(_payload):
        raise RuntimeError("listener exploded")

    ext_mod.register("entitlement.changed", boom)
    # The exception must be swallowed by ext.emit and never bubble up.
    out = ent.get_entitlement(force=True)
    assert out.tier == ent.TIER_OSS


def test_missing_extensions_module_does_not_break_resolution(ent, monkeypatch):
    """If ``clawmetry.extensions`` is somehow unimportable (vendoring shenanigans,
    a broken install), resolution still returns the right tier."""
    import sys
    import clawmetry.extensions as ext_mod
    saved = sys.modules.pop("clawmetry.extensions", None)
    try:
        # Force the late ``from clawmetry import extensions`` inside
        # _maybe_emit_change to raise ImportError.
        monkeypatch.setitem(sys.modules, "clawmetry.extensions", None)
        out = ent.get_entitlement(force=True)
        assert out.tier == ent.TIER_OSS
    finally:
        if saved is not None:
            sys.modules["clawmetry.extensions"] = saved
        else:
            sys.modules.pop("clawmetry.extensions", None)
        # Restore the real module for the next test.
        importlib.reload(ext_mod)


# ── concurrency: no double-emit on the initial tier ─────────────────────────


def test_concurrent_first_resolves_emit_once(ent):
    """Two threads racing the very first ``get_entitlement(force=True)`` must
    produce exactly one emit (the lock-guarded memo prevents double-fire)."""
    import clawmetry.extensions as ext_mod
    received: list[dict] = []
    received_lock = threading.Lock()

    def listener(p):
        with received_lock:
            received.append(p)

    ext_mod.register("entitlement.changed", listener)

    barrier = threading.Barrier(8)
    errors: list[BaseException] = []

    def worker():
        try:
            barrier.wait(timeout=5)
            ent.get_entitlement(force=True)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert not errors
    assert len(received) == 1
    assert received[0]["previous_tier"] is None
    assert received[0]["tier"] == ent.TIER_OSS
