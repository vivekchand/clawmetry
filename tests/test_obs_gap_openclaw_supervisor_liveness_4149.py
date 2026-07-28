"""Tests for issue #4149 — OPENCLAW_SUPERVISOR_MODE=external not reflected in gateway health.

Verifies that compute_gateway_health() returns status "externally_supervised"
when the gateway PID is absent but OPENCLAW_SUPERVISOR_MODE=external is set,
so the dashboard badge distinguishes a supervised pause from a crash.

Fingerprint: hgap-1e190bef38 (used to dedupe — keep it in the body).
"""
from __future__ import annotations

import sys
import types

import pytest


def _stub_dashboard():
    mod = types.ModuleType("dashboard")
    sys.modules.setdefault("dashboard", mod)
    return mod


def _get_compute_gateway_health():
    _stub_dashboard()
    import routes.health as health_mod
    return health_mod.compute_gateway_health


def test_externally_supervised_when_no_pid(monkeypatch):
    """No gateway PID + OPENCLAW_SUPERVISOR_MODE=external → status 'externally_supervised'."""
    monkeypatch.setenv("OPENCLAW_SUPERVISOR_MODE", "external")
    compute = _get_compute_gateway_health()
    result = compute(
        pid_path="/nonexistent/gateway.pid",
        _cmdline_pid=lambda: None,
    )
    assert result["status"] == "externally_supervised"
    assert result["pid"] is None


def test_not_running_when_no_pid_no_supervisor(monkeypatch):
    """No gateway PID + no supervisor env var → status 'not_running' (unchanged)."""
    monkeypatch.delenv("OPENCLAW_SUPERVISOR_MODE", raising=False)
    compute = _get_compute_gateway_health()
    result = compute(
        pid_path="/nonexistent/gateway.pid",
        _cmdline_pid=lambda: None,
    )
    assert result["status"] == "not_running"
    assert result["pid"] is None


def test_supervisor_env_ignored_when_gateway_running(monkeypatch):
    """OPENCLAW_SUPERVISOR_MODE=external has no effect when the gateway is up."""
    monkeypatch.setenv("OPENCLAW_SUPERVISOR_MODE", "external")
    compute = _get_compute_gateway_health()
    result = compute(
        pid_path="/nonexistent/gateway.pid",
        _cmdline_pid=lambda: 99999,
        _psutil_vitals=lambda pid: (120, 200.0, 1.5),
    )
    assert result["status"] in ("healthy", "warning", "critical")
    assert result["pid"] == 99999
