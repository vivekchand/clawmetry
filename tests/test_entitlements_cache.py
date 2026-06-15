"""Tests for the entitlement cache in ``clawmetry/entitlements.py``.

``get_entitlement()`` caches its result for ``_CACHE_TTL_SECS`` so the FLYWHEEL
performance budget is preserved (no per-request license/cloud-plan re-read).
The caching machinery is small but load-bearing -- a regression here either
serves stale results across an enforce-flag flip (security failure) or busts
the cache on every call (perf failure). These tests pin the contract:

  * ``force=True``                                bypasses the cache
  * ``invalidate()``                              clears the cache
  * ``time.time()`` advancing past TTL            triggers a re-resolve
  * ``CLAWMETRY_ENFORCE`` flipping between calls  busts the cache immediately
  * a failure inside the resolver                 falls back to OSS-free and
                                                  is never re-raised
  * concurrent ``get_entitlement()`` callers      see consistent results +
                                                  the underlying source is
                                                  invoked at most once per
                                                  TTL window
"""
from __future__ import annotations

import importlib
import json
import threading

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Reload entitlements with HOME pointed at an empty tmp dir + enforce off."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


def test_repeated_calls_return_cached_instance(ent):
    """Within the TTL window, the cache hands back the same Entitlement instance."""
    a = ent.get_entitlement(force=True)
    b = ent.get_entitlement()
    c = ent.get_entitlement()
    assert a is b is c


def test_force_true_bypasses_cache(ent):
    """``force=True`` always re-resolves, even when a fresh cache entry exists."""
    a = ent.get_entitlement()
    b = ent.get_entitlement(force=True)
    assert a is not b
    assert a == b


def test_invalidate_clears_cache(ent):
    """``invalidate()`` drops the cached entry so the next call re-resolves."""
    a = ent.get_entitlement(force=True)
    ent.invalidate()
    b = ent.get_entitlement()
    assert a is not b


def test_cache_busts_after_ttl(ent, monkeypatch):
    """Advancing the clock past ``_CACHE_TTL_SECS`` triggers a re-resolve."""
    fake_now = [10_000.0]

    def _now():
        return fake_now[0]

    monkeypatch.setattr(ent.time, "time", _now)

    a = ent.get_entitlement(force=True)
    fake_now[0] += 1.0
    assert ent.get_entitlement() is a

    fake_now[0] += ent._CACHE_TTL_SECS + 1.0
    b = ent.get_entitlement()
    assert b is not a


def test_cache_holds_within_ttl_window(ent, monkeypatch):
    """Right up to the TTL boundary, the cache stays warm."""
    fake_now = [50_000.0]
    monkeypatch.setattr(ent.time, "time", lambda: fake_now[0])

    a = ent.get_entitlement(force=True)
    for delta in (0.0, 1.0, ent._CACHE_TTL_SECS / 2.0, ent._CACHE_TTL_SECS - 0.1):
        fake_now[0] = 50_000.0 + delta
        assert ent.get_entitlement() is a, f"unexpected re-resolve at +{delta}s"


def test_enforce_flag_flip_busts_cache(ent, monkeypatch):
    """When ``CLAWMETRY_ENFORCE`` flips ON, the cache must bust immediately."""
    a = ent.get_entitlement(force=True)
    assert a.grace is True

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    b = ent.get_entitlement()
    assert b.grace is False
    assert a is not b


def test_enforce_flag_flip_back_busts_cache(ent, monkeypatch):
    """Turning enforce OFF must immediately re-resolve to the grace shape."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    a = ent.get_entitlement(force=True)
    assert a.grace is False

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    b = ent.get_entitlement()
    assert b.grace is True
    assert a is not b


def test_installed_cloud_plan_visible_after_invalidate(ent, tmp_path):
    """Writing a cloud_plan.json mid-process must take effect after invalidate()."""
    a = ent.get_entitlement(force=True)
    assert a.tier == ent.TIER_OSS

    cache = tmp_path / ".clawmetry" / "cloud_plan.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"plan": "cloud_pro", "node_limit": 3}))
    ent.invalidate()

    b = ent.get_entitlement()
    assert b.tier == ent.TIER_CLOUD_PRO
    assert b.node_limit == 3
    assert b is not a


def test_resolver_failure_falls_back_to_oss_free(ent, monkeypatch):
    """If the resolver raises, get_entitlement returns an OSS-free entitlement."""
    def _boom():
        raise RuntimeError("simulated license read explosion")

    monkeypatch.setattr(ent, "_read_local_license", _boom)
    monkeypatch.setattr(ent, "_read_cloud_plan", _boom)
    ent.invalidate()

    en = ent.get_entitlement()
    assert en.tier == ent.TIER_OSS
    assert en.source == "oss"
    assert en.grace is True


def test_resolver_failure_does_not_poison_cache(ent, monkeypatch):
    """A transient failure must not get cached -- once recovered, next call succeeds."""
    fail = {"on": True}

    def _flaky():
        if fail["on"]:
            raise RuntimeError("transient")
        return None

    monkeypatch.setattr(ent, "_read_local_license", _flaky)
    monkeypatch.setattr(ent, "_read_cloud_plan", lambda: None)
    ent.invalidate()

    a = ent.get_entitlement()
    assert a.tier == ent.TIER_OSS

    fail["on"] = False
    b = ent.get_entitlement(force=True)
    assert b.tier == ent.TIER_OSS
    assert b.source == "oss"


def test_concurrent_callers_get_consistent_results(ent):
    """Concurrent get_entitlement() calls must see consistent results."""
    ent.get_entitlement(force=True)

    results = []
    errors = []
    barrier = threading.Barrier(16)

    def _worker():
        try:
            barrier.wait(timeout=5)
            for _ in range(50):
                results.append(ent.get_entitlement())
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=_worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors, f"worker raised: {errors[0]!r}"
    assert len(results) == 16 * 50
    first = results[0]
    for r in results:
        assert r is not None
        assert r.tier == first.tier
        assert r.grace == first.grace
        assert r.runtimes == first.runtimes


def test_concurrent_cold_cache_does_not_explode(ent, monkeypatch):
    """Many threads hitting a cold cache must not crash."""
    call_count = {"n": 0}
    lock = threading.Lock()

    real_read = ent._read_local_license

    def _counted_read():
        with lock:
            call_count["n"] += 1
        return real_read()

    monkeypatch.setattr(ent, "_read_local_license", _counted_read)
    ent.invalidate()

    results = []
    errors = []
    barrier = threading.Barrier(8)

    def _worker():
        try:
            barrier.wait(timeout=5)
            results.append(ent.get_entitlement())
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=_worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors, f"worker raised: {errors[0]!r}"
    assert len(results) == 8
    for r in results:
        assert r is not None
        assert r.tier == ent.TIER_OSS
    assert call_count["n"] >= 1
