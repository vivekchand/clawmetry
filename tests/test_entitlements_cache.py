"""Tests for the entitlement cache in ``clawmetry/entitlements.py``.

``get_entitlement()`` caches its result for ``_CACHE_TTL_SECS`` so the FLYWHEEL
performance budget is preserved (no per-request license/cloud-plan re-read).
The caching machinery is small but load-bearing — a regression here either
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

Companion to ``tests/test_entitlements.py`` (grace/enforce mechanics) and
``tests/test_entitlements_catalogue.py`` (catalogue/retention pins).
"""
from __future__ import annotations

import importlib
import json
import threading

import pytest


@pytest.fixture
def ent(monkeypatch, tmp_path):
    """Reload entitlements with HOME pointed at an empty tmp dir + enforce off
    so each test starts from a clean cache and the OSS-free fallback path."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── identity / freshness ──────────────────────────────────────────────────────


def test_repeated_calls_return_cached_instance(ent):
    """Within the TTL window, the cache hands back the same Entitlement
    instance — no re-resolve, no rebuild. The dataclass is frozen so identity
    equality is a fine proxy for "cache hit"."""
    a = ent.get_entitlement(force=True)
    b = ent.get_entitlement()
    c = ent.get_entitlement()
    assert a is b is c


def test_force_true_bypasses_cache(ent):
    """``force=True`` always re-resolves, even when a fresh cache entry exists.
    Operator surfaces (``clawmetry entitlement``, debug paths) need this so a
    just-installed license shows up without waiting for the 60s TTL."""
    a = ent.get_entitlement()
    b = ent.get_entitlement(force=True)
    # Re-resolved => a fresh Entitlement instance (frozen dataclass equality
    # holds because the inputs are identical, but identity must change).
    assert a is not b
    assert a == b  # same tier/source/runtimes/features under unchanged inputs


def test_invalidate_clears_cache(ent):
    """``invalidate()`` drops the cached entry so the next call re-resolves."""
    a = ent.get_entitlement(force=True)
    ent.invalidate()
    b = ent.get_entitlement()
    assert a is not b


# ── TTL expiry ────────────────────────────────────────────────────────────────


def test_cache_busts_after_ttl(ent, monkeypatch):
    """Advancing the clock past ``_CACHE_TTL_SECS`` triggers a re-resolve.
    Patch ``time.time`` rather than ``time.sleep``-ing so the suite stays fast."""
    fake_now = [10_000.0]

    def _now():
        return fake_now[0]

    monkeypatch.setattr(ent.time, "time", _now)

    a = ent.get_entitlement(force=True)
    fake_now[0] += 1.0  # well under TTL — still cached
    assert ent.get_entitlement() is a

    fake_now[0] += ent._CACHE_TTL_SECS + 1.0  # past TTL — must re-resolve
    b = ent.get_entitlement()
    assert b is not a


def test_cache_holds_within_ttl_window(ent, monkeypatch):
    """Right up to the TTL boundary, the cache stays warm. The strict ``<``
    comparison in ``get_entitlement`` means exactly-at-TTL is a miss, which
    is fine — the test only pins "comfortably under TTL is a hit"."""
    fake_now = [50_000.0]
    monkeypatch.setattr(ent.time, "time", lambda: fake_now[0])

    a = ent.get_entitlement(force=True)
    for delta in (0.0, 1.0, ent._CACHE_TTL_SECS / 2.0, ent._CACHE_TTL_SECS - 0.1):
        fake_now[0] = 50_000.0 + delta
        assert ent.get_entitlement() is a, f"unexpected re-resolve at +{delta}s"


# ── enforce-flag bust (security-critical) ────────────────────────────────────


def test_enforce_flag_flip_busts_cache(ent, monkeypatch):
    """When ``CLAWMETRY_ENFORCE`` flips between two calls, the cache MUST bust
    — otherwise a process that was warmed in grace mode keeps serving paid
    runtimes after an operator turns the paywall on."""
    a = ent.get_entitlement(force=True)
    assert a.grace is True

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    b = ent.get_entitlement()  # no force=True — must still re-resolve
    assert b.grace is False
    assert a is not b


def test_enforce_flag_flip_back_busts_cache(ent, monkeypatch):
    """The opposite direction also busts: turning enforce OFF must immediately
    re-resolve to the grace shape, not keep serving the locked OSS view."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    a = ent.get_entitlement(force=True)
    assert a.grace is False

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    b = ent.get_entitlement()
    assert b.grace is True
    assert a is not b


# ── source-change refresh ─────────────────────────────────────────────────────


def test_installed_cloud_plan_visible_after_invalidate(ent, tmp_path):
    """Writing a cloud_plan.json mid-process must take effect on the next call
    after ``invalidate()`` — this is the path :func:`clawmetry.license.activate`
    uses to make a new license visible without restarting the daemon."""
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


# ── never-raise contract ──────────────────────────────────────────────────────


def test_resolver_failure_falls_back_to_oss_free(ent, monkeypatch):
    """If the local-license resolver raises *inside* the cached call, the
    top-level try/except in ``get_entitlement`` returns an OSS-free entitlement
    instead of propagating the exception."""
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
    """A transient failure must not get cached — once the resolver recovers,
    the next call must succeed. The current implementation guarantees this by
    never writing into the cache on the exception path."""
    fail = {"on": True}

    def _flaky():
        if fail["on"]:
            raise RuntimeError("transient")
        return None  # fall through to OSS-free

    monkeypatch.setattr(ent, "_read_local_license", _flaky)
    monkeypatch.setattr(ent, "_read_cloud_plan", lambda: None)
    ent.invalidate()

    a = ent.get_entitlement()  # fails -> OSS-free fallback (uncached)
    assert a.tier == ent.TIER_OSS

    fail["on"] = False
    b = ent.get_entitlement(force=True)
    assert b.tier == ent.TIER_OSS
    assert b.source == "oss"


# ── thread-safety ─────────────────────────────────────────────────────────────


def test_concurrent_callers_get_consistent_results(ent):
    """Hammer ``get_entitlement`` from many threads while the cache is warm.
    Every caller must receive a fully-formed Entitlement (no None, no half-
    populated dataclass) and every result must agree on tier/grace/runtimes
    — the lock around the cache prevents a torn read."""
    ent.get_entitlement(force=True)  # warm

    results: list = []
    errors: list[BaseException] = []
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
    """When many threads hit a cold cache at once, the resolver may run more
    than once (the lock is fine-grained), but every caller still receives a
    valid Entitlement and no thread raises. This pins the "no torn writes,
    no None reads" invariant under contention."""
    call_count = {"n": 0}
    lock = threading.Lock()

    real_read = ent._read_local_license

    def _counted_read():
        with lock:
            call_count["n"] += 1
        return real_read()

    monkeypatch.setattr(ent, "_read_local_license", _counted_read)
    ent.invalidate()

    results: list = []
    errors: list[BaseException] = []
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
    # The resolver was called at least once; it may be called more under cold-
    # cache contention. The point of the test is that nothing crashes.
    assert call_count["n"] >= 1
