"""Tests for #3675 — dcodeSupervisionFeasible flag on deepagents-code sandboxes.

The dcode session-supervisor requires Linux + an OpenShell sandbox; it exits
immediately with a fail-closed diagnostic otherwise.  ClawMetry now surfaces
``dcodeSupervisionFeasible`` so users can distinguish healthy supervised
sessions from silently unsupervised ones.
"""
import json
import shutil
import subprocess
import sys

import pytest

from clawmetry.adapters.openclaw import _sandbox_inference_configs


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_sandboxes_json(tmp_path, data):
    nemo = tmp_path / ".nemoclaw"
    nemo.mkdir(exist_ok=True)
    (nemo / "sandboxes.json").write_text(json.dumps(data))


def _write_agents_yaml(tmp_path, content):
    nemo = tmp_path / ".nemoclaw"
    nemo.mkdir(exist_ok=True)
    (nemo / "agents.yaml").write_text(content)


def _fake_run_with_phase(cmd, **kw):
    """subprocess.run stub: openshell sandbox get returns a Phase line."""
    if "get" in cmd:
        return type("R", (), {"stdout": "Phase: Ready\nRuntime: terminal\n"})()
    return type("R", (), {"stdout": ""})()


def _fake_run_no_phase(cmd, **kw):
    """subprocess.run stub: openshell returns empty output."""
    return type("R", (), {"stdout": ""})()


# ---------------------------------------------------------------------------
# 1. Linux + openshell with phase data → dcodeSupervisionFeasible=True
# ---------------------------------------------------------------------------

def test_dcode_supervision_feasible_on_linux_with_openshell(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _write_sandboxes_json(tmp_path, {"sandboxes": {}})
    _write_agents_yaml(tmp_path, (
        "agents:\n"
        "  - name: deepagents-code\n"
        "    sandbox: deepagents-code\n"
    ))
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    monkeypatch.setattr(subprocess, "run", _fake_run_with_phase)
    monkeypatch.setattr(sys, "platform", "linux")

    result = _sandbox_inference_configs()
    te = next((r for r in result if r["sandbox"] == "deepagents-code"), None)
    assert te is not None, "deepagents-code sandbox not found in output"
    assert te.get("dcodeSupervisionFeasible") is True, (
        f"expected True on Linux+openshell; got {te.get('dcodeSupervisionFeasible')!r}"
    )


# ---------------------------------------------------------------------------
# 2. Non-Linux platform → dcodeSupervisionFeasible=False (fail-closed)
# ---------------------------------------------------------------------------

def test_dcode_supervision_fail_closed_non_linux(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _write_sandboxes_json(tmp_path, {"sandboxes": {}})
    _write_agents_yaml(tmp_path, (
        "agents:\n"
        "  - name: deepagents-code\n"
        "    sandbox: deepagents-code\n"
    ))
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    monkeypatch.setattr(subprocess, "run", _fake_run_with_phase)
    monkeypatch.setattr(sys, "platform", "darwin")

    result = _sandbox_inference_configs()
    te = next((r for r in result if r["sandbox"] == "deepagents-code"), None)
    assert te is not None
    assert te.get("dcodeSupervisionFeasible") is False, (
        f"expected False on non-Linux; got {te.get('dcodeSupervisionFeasible')!r}"
    )


# ---------------------------------------------------------------------------
# 3. Linux + no openshell (phase absent) → dcodeSupervisionFeasible=False
# ---------------------------------------------------------------------------

def test_dcode_supervision_fail_closed_no_openshell(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _write_sandboxes_json(tmp_path, {"sandboxes": {}})
    _write_agents_yaml(tmp_path, (
        "agents:\n"
        "  - name: deepagents-code\n"
        "    sandbox: deepagents-code\n"
    ))
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)  # openshell absent
    monkeypatch.setattr(sys, "platform", "linux")

    result = _sandbox_inference_configs()
    te = next((r for r in result if r["sandbox"] == "deepagents-code"), None)
    assert te is not None
    assert te.get("dcodeSupervisionFeasible") is False, (
        f"expected False when openshell absent; got {te.get('dcodeSupervisionFeasible')!r}"
    )


# ---------------------------------------------------------------------------
# 4. Non-dcode sandbox must not gain the flag
# ---------------------------------------------------------------------------

def test_non_dcode_sandbox_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _write_sandboxes_json(tmp_path, {"sandboxes": {}})
    _write_agents_yaml(tmp_path, (
        "agents:\n"
        "  - name: inference-only\n"
        "    sandbox: inference-only\n"
    ))
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    monkeypatch.setattr(subprocess, "run", _fake_run_with_phase)
    monkeypatch.setattr(sys, "platform", "linux")

    result = _sandbox_inference_configs()
    te = next((r for r in result if r["sandbox"] == "inference-only"), None)
    assert te is not None
    assert "dcodeSupervisionFeasible" not in te, (
        f"unexpected dcodeSupervisionFeasible on non-dcode sandbox: {te}"
    )
