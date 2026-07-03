"""Tests for #3503 -- _sandbox_inference_configs discovers terminal/agent-execution
sandboxes from agents.yaml that have no entry in sandboxes.json.
"""
import json
import shutil
import subprocess

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


def _noop_openshell(*a, **kw):
    """subprocess.run stub: returns an empty stdout so openshell helpers no-op."""
    return type("R", (), {"stdout": ""})()


# ---------------------------------------------------------------------------
# 1. Terminal sandbox in agents.yaml but not in sandboxes.json → surfaced
# ---------------------------------------------------------------------------

def test_terminal_sandbox_from_agents_yaml_surfaces_in_output(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    # sandboxes.json has only an inference-routing sandbox
    _write_sandboxes_json(tmp_path, {
        "defaultSandbox": "inference-sb",
        "sandboxes": {
            "inference-sb": {"provider": "anthropic-prod", "model": "claude-opus-4-5"},
        },
    })
    # agents.yaml declares a terminal sandbox absent from sandboxes.json
    _write_agents_yaml(tmp_path, (
        "agents:\n"
        "  - name: deepagents-code\n"
        "    sandbox: deepagents-code\n"
        "    runtimeKind: terminal\n"
    ))
    # openshell absent — helpers no-op gracefully
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)

    result = _sandbox_inference_configs()
    sandboxes = {r["sandbox"]: r for r in result}

    assert "inference-sb" in sandboxes
    assert "deepagents-code" in sandboxes
    te = sandboxes["deepagents-code"]
    assert te["provider"] == "terminal"
    assert te["providerKey"] == "terminal"
    assert te["sandboxSource"] == "agents.yaml"
    assert te["primaryModelRef"] == ""


# ---------------------------------------------------------------------------
# 2. Sandbox already in sandboxes.json must not be duplicated
# ---------------------------------------------------------------------------

def test_sandbox_in_sandboxes_json_not_duplicated(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _write_sandboxes_json(tmp_path, {
        "sandboxes": {
            "shared-sb": {"provider": "openai-api", "model": "gpt-4o"},
        },
    })
    # agents.yaml also lists the same sandbox name
    _write_agents_yaml(tmp_path, (
        "agents:\n"
        "  - name: shared-sb\n"
        "    sandbox: shared-sb\n"
    ))
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)

    result = _sandbox_inference_configs()
    names = [r["sandbox"] for r in result]

    # Must appear exactly once; the sandboxes.json entry wins (providerKey != "terminal")
    assert names.count("shared-sb") == 1
    assert result[0]["providerKey"] != "terminal"


# ---------------------------------------------------------------------------
# 3. openshell is probed for the terminal sandbox; Phase/Runtime propagate
# ---------------------------------------------------------------------------

def test_terminal_sandbox_openshell_probed_for_phase_and_runtime(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _write_sandboxes_json(tmp_path, {"sandboxes": {}})
    _write_agents_yaml(tmp_path, (
        "agents:\n"
        "  - name: deepagents-code\n"
        "    sandbox: deepagents-code\n"
    ))

    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        if "get" in cmd:
            return type("R", (), {"stdout": "Phase: Ready\nRuntime: terminal\n"})()
        return type("R", (), {"stdout": ""})()

    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = _sandbox_inference_configs()
    te = next(r for r in result if r["sandbox"] == "deepagents-code")

    assert te["sandboxPhase"] == "Ready"
    assert te["sandboxRuntimeKind"] == "terminal"
    # openshell sandbox get was called with the right sandbox name
    assert any("deepagents-code" in c for c in calls)


# ---------------------------------------------------------------------------
# 4. No agents.yaml → no extra entries (graceful no-op)
# ---------------------------------------------------------------------------

def test_no_agents_yaml_no_extra_sandboxes(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _write_sandboxes_json(tmp_path, {
        "sandboxes": {
            "inference-sb": {"provider": "anthropic-prod", "model": "claude-3-5-sonnet"},
        },
    })
    # no agents.yaml written
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)

    result = _sandbox_inference_configs()
    assert len(result) == 1
    assert result[0]["sandbox"] == "inference-sb"
    assert result[0].get("sandboxSource") != "agents.yaml"
