"""Tests for #5293 — NemoClaw: gateway-log-probe-timeout diagnostic.

Verifies that _gateway_log_events_probe() respects NEMOCLAW_LOGS_PROBE_TIMEOUT_MS
and returns source_available=False on timeout, distinguishing 'gateway log
source unreachable' from 'gateway log source reachable but empty'. Mirrors the
NEMOCLAW_LOGS_PROBE_TIMEOUT_MS bounded-probe posture in the NemoClaw harness
(test/cli/logs.test.ts).
"""
import importlib
import time

import pytest


def _reload() -> object:
    import clawmetry.adapters.openclaw as oc
    return importlib.reload(oc)


def test_probe_returns_events_and_true_on_success(monkeypatch):
    """Reachable log with events -> (events, True)."""
    oc = _reload()
    events = [{"msg": "boot", "level": "info"}]
    monkeypatch.setattr(oc, "_gateway_log_events", lambda count=50: events)
    result, available = oc._gateway_log_events_probe()
    assert result == events
    assert available is True


def test_probe_returns_empty_and_true_when_log_is_empty(monkeypatch):
    """Reachable log that happens to be empty -> ([], True), not a timeout."""
    oc = _reload()
    monkeypatch.setattr(oc, "_gateway_log_events", lambda count=50: [])
    result, available = oc._gateway_log_events_probe()
    assert result == []
    assert available is True


def test_probe_returns_false_on_timeout(monkeypatch):
    """Slow probe exceeds NEMOCLAW_LOGS_PROBE_TIMEOUT_MS -> ([], False)."""
    oc = _reload()

    def _slow(count=50):
        time.sleep(10)
        return []

    monkeypatch.setenv("NEMOCLAW_LOGS_PROBE_TIMEOUT_MS", "50")
    monkeypatch.setattr(oc, "_gateway_log_events", _slow)
    result, available = oc._gateway_log_events_probe()
    assert result == []
    assert available is False


def test_probe_default_timeout_is_five_seconds(monkeypatch):
    """Without the env var, probe uses a 5-second budget (fast stub finishes)."""
    oc = _reload()
    monkeypatch.delenv("NEMOCLAW_LOGS_PROBE_TIMEOUT_MS", raising=False)
    monkeypatch.setattr(oc, "_gateway_log_events", lambda count=50: [{"msg": "ok"}])
    result, available = oc._gateway_log_events_probe()
    assert available is True
    assert result == [{"msg": "ok"}]
