"""Tests for #3202 -- _openshell_sandbox_phase_policy surfaces live Phase /
Policy per NemoClaw sandbox in DetectResult.meta.sandboxInferenceConfigs.
"""
import json
import shutil
import subprocess

import pytest

from clawmetry.adapters.openclaw import (
    _openshell_sandbox_phase_policy,
    _sandbox_inference_configs,
)


# -- _openshell_sandbox_phase_policy ------------------------------------------

def test_phase_policy_returns_empty_when_openshell_absent(monkeypatch):
    """No openshell binary -> {} with no exception."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)
    assert _openshell_sandbox_phase_policy("alpha") == {}


def test_phase_policy_parses_phase_and_policy(monkeypatch):
    """Both Phase and Policy lines are parsed from openshell output."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "Name: alpha\nPhase: Ready\nPolicy: strict\n"})() 
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    result = _openshell_sandbox_phase_policy("alpha")
    assert result == {"sandboxPhase": "Ready", "sandboxPolicy": "strict"}


def test_phase_policy_empty_policy_value(monkeypatch):
    """Policy field present but empty -> sandboxPolicy = '' (default policy)."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "Name: alpha\nPhase: Ready\nPolicy:\n"})() 
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    result = _openshell_sandbox_phase_policy("alpha")
    assert result.get("sandboxPhase") == "Ready"
    assert result.get("sandboxPolicy") == ""


def test_phase_policy_only_phase_when_no_policy_line(monkeypatch):
    """If Policy line is absent only sandboxPhase is set."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "Name: alpha\nPhase: Pending\n"})() 
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    result = _openshell_sandbox_phase_policy("alpha")
    assert result == {"sandboxPhase": "Pending"}


def test_phase_policy_subprocess_error_returns_empty(monkeypatch):
    """Subprocess failure -> {} never raises."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    def boom(*a, **kw):
        raise OSError("binary broken")
    monkeypatch.setattr(subprocess, "run", boom)
    assert _openshell_sandbox_phase_policy("alpha") == {}


def test_phase_policy_empty_stdout(monkeypatch):
    """Empty stdout -> {} with no exception (openshell returned nothing)."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": ""})() 
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    assert _openshell_sandbox_phase_policy("beta") == {}


# -- integration: _sandbox_inference_configs merges phase fields --------------

def test_sandbox_inference_configs_includes_phase_and_policy(tmp_path, monkeypatch):
    """sandboxInferenceConfigs entries gain sandboxPhase / sandboxPolicy
    when openshell is available and returns status for the sandbox."""
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = {
        "defaultSandbox": "alpha",
        "sandboxes": {
            "alpha": {"provider": "anthropic-prod", "model": "claude-opus-4-5"},
        },
    }
    (tmp_path / ".nemoclaw").mkdir()
    (tmp_path / ".nemoclaw" / "sandboxes.json").write_text(json.dumps(cfg))

    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "Name: alpha\nPhase: Ready\nPolicy:\n"})() 
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)

    result = _sandbox_inference_configs()
    assert len(result) == 1
    r = result[0]
    assert r["sandboxPhase"] == "Ready"
    assert r.get("sandboxPolicy") == ""
    # existing fields must still be intact
    assert r["providerKey"] == "anthropic"
    assert r["isDefault"] is True


def test_sandbox_inference_configs_no_phase_when_openshell_absent(tmp_path, monkeypatch):
    """When openshell is absent, inference config entries are returned without
    sandboxPhase / sandboxPolicy (backwards-compatible)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = {
        "defaultSandbox": None,
        "sandboxes": {
            "dev": {"provider": "openai-api", "model": "gpt-4o"},
        },
    }
    (tmp_path / ".nemoclaw").mkdir()
    (tmp_path / ".nemoclaw" / "sandboxes.json").write_text(json.dumps(cfg))

    monkeypatch.setattr(shutil, "which", lambda _cmd: None)

    result = _sandbox_inference_configs()
    assert len(result) == 1
    r = result[0]
    assert "sandboxPhase" not in r
    assert "sandboxPolicy" not in r
    assert r["providerKey"] == "openai"


def test_sandbox_inference_configs_multiple_sandboxes_each_queried(tmp_path, monkeypatch):
    """Each sandbox is queried independently; phases can differ."""
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = {
        "defaultSandbox": "prod",
        "sandboxes": {
            "prod": {"provider": "anthropic-prod", "model": "claude-opus-4-5"},
            "dev": {"provider": "openai-api", "model": "gpt-4o"},
        },
    }
    (tmp_path / ".nemoclaw").mkdir()
    (tmp_path / ".nemoclaw" / "sandboxes.json").write_text(json.dumps(cfg))

    phases = {"prod": "Ready", "dev": "Pending"}
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")

    def fake_run(cmd, **kw):
        sandbox_name = cmd[-1]
        stdout = f"Name: {sandbox_name}\nPhase: {phases[sandbox_name]}\nPolicy:\n"
        return type("R", (), {"stdout": stdout})()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = _sandbox_inference_configs()
    assert len(result) == 2
    by_name = {r["sandbox"]: r for r in result}
    assert by_name["prod"]["sandboxPhase"] == "Ready"
    assert by_name["dev"]["sandboxPhase"] == "Pending"
