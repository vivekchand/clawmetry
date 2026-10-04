"""Unit tests for the daemon-side wake long-poll (fast relay, 2026-08-29).

The independent delivery worker owns ``GET /ingest/wake``. It forwards work
and viewer hints to the main loop without a second HTTP poll; collection and
generic queries remain on the main loop.

These tests cover the pure decision helper, the sleep/wake orchestration
(with the network call stubbed), and the 404 mute — no network, no daemon.
"""

from __future__ import annotations

import io
import json
import time
import urllib.error

import pytest

from clawmetry import sync


CONFIG = {"node_id": "node-wake-test", "api_key": "cm_wake_test"}


@pytest.fixture(autouse=True)
def _reset_wake_state(monkeypatch):
    monkeypatch.setattr(sync, "_WAKE_POLL_MUTED_UNTIL", 0.0)
    monkeypatch.delenv("CLAWMETRY_WAKE_POLL", raising=False)


# ── _wake_says_heartbeat: pure decision ────────────────────────────────────


@pytest.mark.parametrize("resp,expected", [
    ({"ok": True, "work": True, "viewer_active": False}, True),
    ({"ok": True, "work": False, "viewer_active": True}, True),
    ({"ok": True, "work": True, "viewer_active": True}, True),
    ({"ok": True, "work": False, "viewer_active": False}, False),
    ({}, False),
    (None, False),
    ("not-a-dict", False),
])
def test_wake_says_heartbeat(resp, expected):
    assert sync._wake_says_heartbeat(resp) is expected


# ── _idle_sleep_or_wake: orchestration ─────────────────────────────────────


def test_idle_sleep_without_wake_just_sleeps(monkeypatch):
    slept = []
    monkeypatch.setattr(sync.time, "sleep", lambda s: slept.append(s))
    called = []
    monkeypatch.setattr(sync, "_wake_wait", lambda *a: called.append(a))
    assert sync._idle_sleep_or_wake(CONFIG, 15, allow_wake=False) is False
    assert slept == [15.0]
    assert called == []  # FAST cadence / failing heartbeats never long-poll


def test_wake_with_work_forces_heartbeat_and_skips_sleep(monkeypatch):
    from clawmetry import assistant_relay as relay
    slept = []
    monkeypatch.setattr(sync.time, "sleep", lambda s: slept.append(s))
    monkeypatch.setattr(sync, "_wake_wait", lambda *a, **kw: pytest.fail("duplicate HTTP poll"))
    relay._wake_hint.set()
    assert sync._idle_sleep_or_wake(CONFIG, 15, allow_wake=True) is True
    assert not relay._wake_hint.is_set()
    assert slept == []  # woken: get to the heartbeat, don't finish the nap


def test_wake_error_sleeps_out_the_remainder(monkeypatch):
    """Absent hints wait on the event; no main-thread network or busy loop."""
    from clawmetry import assistant_relay as relay
    waited = []
    relay._wake_hint.clear()
    monkeypatch.setattr(relay._wake_hint, 'wait', lambda timeout: waited.append(timeout) or False)
    monkeypatch.setattr(sync, "_wake_wait", lambda *a, **kw: pytest.fail("duplicate HTTP poll"))
    assert sync._idle_sleep_or_wake(CONFIG, 15, allow_wake=True) is False
    assert waited == [15.0]


# ── _wake_wait: gates and mute ─────────────────────────────────────────────


def test_wake_wait_disabled_by_env(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_WAKE_POLL", "0")
    monkeypatch.setattr(
        sync.urllib.request, "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network hit")))
    assert sync._wake_wait(CONFIG, 10) is None


def test_wake_wait_requires_identity(monkeypatch):
    monkeypatch.setattr(
        sync.urllib.request, "urlopen",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("network hit")))
    assert sync._wake_wait({}, 10) is None
    assert sync._wake_wait({"node_id": "n"}, 10) is None


def test_wake_wait_parses_response(monkeypatch):
    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    payload = {"ok": True, "work": True, "viewer_active": False, "pending": 1}

    def _fake_urlopen(req, timeout=0):
        assert "/ingest/wake?node_id=node-wake-test&wait=" in req.full_url
        assert req.headers.get("X-api-key") == "cm_wake_test"
        return _Resp(json.dumps(payload).encode())

    monkeypatch.setattr(sync.urllib.request, "urlopen", _fake_urlopen)
    assert sync._wake_wait(CONFIG, 10) == payload


def test_wake_wait_404_mutes_further_polls(monkeypatch):
    calls = []

    def _fake_urlopen(req, timeout=0):
        calls.append(req.full_url)
        raise urllib.error.HTTPError(req.full_url, 404, "nf", {}, io.BytesIO())

    monkeypatch.setattr(sync.urllib.request, "urlopen", _fake_urlopen)
    assert sync._wake_wait(CONFIG, 10) is None
    assert sync._WAKE_POLL_MUTED_UNTIL > time.time()
    # Muted: the second call never reaches the network.
    assert sync._wake_wait(CONFIG, 10) is None
    assert len(calls) == 1
