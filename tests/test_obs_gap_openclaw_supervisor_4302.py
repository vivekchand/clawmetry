"""Tests for #4302 — gateway liveness misreports during externally-supervised
restart-handoff.

``_gateway_live()`` probes PID + TCP only; it has no awareness that
``OPENCLAW_SUPERVISOR_MODE=external`` means a gateway that appears down may
simply be mid-handoff under an external lifecycle owner (e.g. OCM).

Fixes:
- ``_gateway_is_in_restart_handoff()`` — pure helper that infers the handoff
  state from supervisor_mode + gateway_live.
- ``detect()`` now sets ``meta["gatewayInRestartHandoff"] = True`` when the
  helper returns True, so callers can surface "restarting (supervised)" rather
  than "gateway offline".
"""
from __future__ import annotations

import os


def _adapter():
    from clawmetry.adapters.openclaw import (
        _gateway_is_in_restart_handoff,
        _gateway_supervisor_mode_env,
    )
    return _gateway_is_in_restart_handoff, _gateway_supervisor_mode_env


# ---------------------------------------------------------------------------
# _gateway_supervisor_mode_env — env-var fallback already existed (#4023)
# ---------------------------------------------------------------------------

def test_supervisor_mode_env_unset(monkeypatch):
    """No OPENCLAW_SUPERVISOR_MODE → empty dict."""
    monkeypatch.delenv("OPENCLAW_SUPERVISOR_MODE", raising=False)
    monkeypatch.delenv("OPENCLAW_SUPERVISOR_MODE_VERSION", raising=False)
    _, _env = _adapter()
    assert _env() == {}


def test_supervisor_mode_env_external(monkeypatch):
    """OPENCLAW_SUPERVISOR_MODE=external → gatewaySupervisorMode key present."""
    monkeypatch.setenv("OPENCLAW_SUPERVISOR_MODE", "external")
    monkeypatch.delenv("OPENCLAW_SUPERVISOR_MODE_VERSION", raising=False)
    _, _env = _adapter()
    result = _env()
    assert result == {"gatewaySupervisorMode": "external"}


def test_supervisor_mode_env_with_version(monkeypatch):
    """Version env var is also surfaced when set."""
    monkeypatch.setenv("OPENCLAW_SUPERVISOR_MODE", "external")
    monkeypatch.setenv("OPENCLAW_SUPERVISOR_MODE_VERSION", "1.2")
    _, _env = _adapter()
    result = _env()
    assert result["gatewaySupervisorMode"] == "external"
    assert result["gatewaySupervisorModeVersion"] == "1.2"


def test_supervisor_mode_env_non_external(monkeypatch):
    """A supervisor mode value other than 'external' is still surfaced."""
    monkeypatch.setenv("OPENCLAW_SUPERVISOR_MODE", "internal")
    monkeypatch.delenv("OPENCLAW_SUPERVISOR_MODE_VERSION", raising=False)
    _, _env = _adapter()
    result = _env()
    assert result["gatewaySupervisorMode"] == "internal"


# ---------------------------------------------------------------------------
# _gateway_is_in_restart_handoff — the new helper (#4302)
# ---------------------------------------------------------------------------

def test_handoff_external_and_gateway_down():
    """external supervisor + gateway down → handoff in progress."""
    _in_handoff, _ = _adapter()
    assert _in_handoff("external", False) is True


def test_handoff_external_and_gateway_up():
    """external supervisor + gateway live → NOT in handoff (normal operation)."""
    _in_handoff, _ = _adapter()
    assert _in_handoff("external", True) is False


def test_handoff_no_supervisor_and_gateway_down():
    """No supervisor mode + gateway down → NOT a supervised handoff (real outage)."""
    _in_handoff, _ = _adapter()
    assert _in_handoff("", False) is False


def test_handoff_no_supervisor_and_gateway_up():
    """No supervisor mode + gateway up → not a handoff."""
    _in_handoff, _ = _adapter()
    assert _in_handoff("", True) is False


def test_handoff_non_external_supervisor_and_gateway_down():
    """Non-external supervisor mode + gateway down → not an external handoff."""
    _in_handoff, _ = _adapter()
    assert _in_handoff("internal", False) is False
