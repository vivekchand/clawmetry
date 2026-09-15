"""OpenClaw detection must not wait for ``openclaw doctor`` (#5935).

``OpenClawAdapter.detect()`` runs inside page requests (``/api/agents``,
``/api/inventory``). It used to run ``openclaw doctor --json`` synchronously on
every call: 9.4 s cold and 5.0 s warm on a real install. Two such requests at
dashboard startup held two of the browser's six connections for 12-15 s and
starved the rest of the page into client timeouts.

The findings are now served stale-while-revalidate. These tests pin the
contract (Factory requirement 08aff8e1-2a68-41c2-8052-da53bbbdd749, AC 4):

* a read never waits for the diagnostic;
* concurrent readers share one background run;
* the findings appear on reads after that run finishes, and are ABSENT (not
  "no findings") before it does;
* ``CLAWMETRY_OPENCLAW_DOCTOR_TTL=0`` restores a synchronous run per read;
* ``detect()`` itself goes through the cached path.
"""

from __future__ import annotations

import threading
import time

import pytest

from clawmetry.adapters import openclaw as oc

_FINDINGS = [{"id": "auth-profile", "severity": "warn"}]
_SLOW_S = 0.6


@pytest.fixture
def slow_doctor(monkeypatch):
    calls = {"n": 0}
    lock = threading.Lock()

    def _slow():
        with lock:
            calls["n"] += 1
        time.sleep(_SLOW_S)
        return list(_FINDINGS)

    monkeypatch.setattr(oc, "_openclaw_doctor_findings", _slow)
    monkeypatch.setattr(oc.shutil if hasattr(oc, "shutil") else __import__("shutil"),
                        "which", lambda name: "/usr/local/bin/openclaw")
    monkeypatch.delenv("CLAWMETRY_OPENCLAW_DOCTOR_TTL", raising=False)
    oc._DOCTOR_CACHE.update(at=0.0, value=None, refreshing=False)
    yield calls
    # Let any background refresh finish before the next test resets the cache.
    deadline = time.monotonic() + 5
    while oc._DOCTOR_CACHE["refreshing"] and time.monotonic() < deadline:
        time.sleep(0.02)
    oc._DOCTOR_CACHE.update(at=0.0, value=None, refreshing=False)


def _wait_refreshed(timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if oc._DOCTOR_CACHE["value"] is not None and not oc._DOCTOR_CACHE["refreshing"]:
            return
        time.sleep(0.02)
    raise AssertionError("background doctor refresh never finished")


def test_a_read_never_waits_for_the_diagnostic(slow_doctor):
    t0 = time.monotonic()
    first = oc._openclaw_doctor_findings_cached()
    elapsed = time.monotonic() - t0
    assert elapsed < _SLOW_S / 2, f"read blocked on the subprocess for {elapsed:.2f}s"
    # Unknown before the first run: absent, never a fabricated finding.
    assert first == []
    _wait_refreshed()
    assert oc._openclaw_doctor_findings_cached() == _FINDINGS
    assert slow_doctor["n"] == 1


def test_concurrent_readers_share_one_run(slow_doctor):
    barrier = threading.Barrier(8)

    def _read():
        barrier.wait()
        oc._openclaw_doctor_findings_cached()

    threads = [threading.Thread(target=_read) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    _wait_refreshed()
    for _ in range(5):
        assert oc._openclaw_doctor_findings_cached() == _FINDINGS
    assert slow_doctor["n"] == 1, "concurrent readers each ran openclaw doctor"


def test_ttl_zero_restores_a_synchronous_run(slow_doctor, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DOCTOR_TTL", "0")
    assert oc._openclaw_doctor_findings_cached() == _FINDINGS
    assert oc._openclaw_doctor_findings_cached() == _FINDINGS
    assert slow_doctor["n"] == 2


def test_no_openclaw_on_path_reports_nothing_and_spawns_nothing(slow_doctor, monkeypatch):
    import shutil

    monkeypatch.setattr(shutil, "which", lambda name: None)
    assert oc._openclaw_doctor_findings_cached() == []
    assert not oc._DOCTOR_CACHE["refreshing"]
    assert slow_doctor["n"] == 0


def test_detect_goes_through_the_cached_path(monkeypatch):
    """The regression itself: detect() must not call the blocking runner."""

    def _blocking():
        raise AssertionError("detect() ran openclaw doctor synchronously")

    monkeypatch.setattr(oc, "_openclaw_doctor_findings", _blocking)
    # raising=False: against the pre-#5935 adapter this attribute does not
    # exist, and the test must fail on BEHAVIOUR (detect() calling the
    # blocking runner, so no findings reach meta), not on a missing name.
    monkeypatch.setattr(oc, "_openclaw_doctor_findings_cached",
                        lambda: list(_FINDINGS), raising=False)
    result = oc.OpenClawAdapter().detect()
    assert result.meta.get("doctorFindings") == _FINDINGS
