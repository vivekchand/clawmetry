"""Tests for #3273 -- _openshell_sandbox_phase_policy and
_sandbox_inference_configs surface sandbox runtime.kind (terminal vs docker).
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

def test_phase_policy_parses_runtime_line(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "Name: alpha\nPhase: Ready\nRuntime: terminal\n"})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    result = _openshell_sandbox_phase_policy("alpha")
    assert result["sandboxRuntimeKind"] == "terminal"
    assert result["sandboxPhase"] == "Ready"


def test_phase_policy_runtime_docker(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "Name: b\nPhase: Ready\nRuntime: docker\n"})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    result = _openshell_sandbox_phase_policy("b")
    assert result["sandboxRuntimeKind"] == "docker"


def test_phase_policy_absent_runtime_line_returns_no_key(monkeypatch):
    """Backwards-compatible: when Runtime: is absent the key is not set."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "Name: alpha\nPhase: Ready\nPolicy: strict\n"})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    result = _openshell_sandbox_phase_policy("alpha")
    assert "sandboxRuntimeKind" not in result


def test_phase_policy_no_openshell_no_runtime(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)
    assert _openshell_sandbox_phase_policy("alpha") == {}


# -- _sandbox_inference_configs: openshell runtime surfacing ------------------

def test_sandbox_configs_surfaces_runtime_kind_from_openshell(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = {
        "defaultSandbox": "alpha",
        "sandboxes": {"alpha": {"provider": "anthropic-prod", "model": "claude-opus-4-5"}},
    }
    (tmp_path / ".nemoclaw").mkdir()
    (tmp_path / ".nemoclaw" / "sandboxes.json").write_text(json.dumps(cfg))

    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "Name: alpha\nPhase: Ready\nRuntime: terminal\n"})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)

    result = _sandbox_inference_configs()
    assert len(result) == 1
    assert result[0]["sandboxRuntimeKind"] == "terminal"
    assert result[0]["sandboxPhase"] == "Ready"


def test_sandbox_configs_surfaces_runtime_kind_from_json_field(tmp_path, monkeypatch):
    """runtimeKind in sandboxes.json is used when openshell is absent."""
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = {
        "sandboxes": {
            "dev": {
                "provider": "openai-api",
                "model": "gpt-4o",
                "runtimeKind": "docker",
            }
        }
    }
    (tmp_path / ".nemoclaw").mkdir()
    (tmp_path / ".nemoclaw" / "sandboxes.json").write_text(json.dumps(cfg))
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)

    result = _sandbox_inference_configs()
    assert len(result) == 1
    assert result[0]["sandboxRuntimeKind"] == "docker"


def test_sandbox_configs_surfaces_runtime_kind_from_nested_json(tmp_path, monkeypatch):
    """Nested runtime.kind in JSON entry is also read as a fallback."""
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = {
        "sandboxes": {
            "dev": {
                "provider": "openai-api",
                "model": "gpt-4o",
                "runtime": {"kind": "terminal"},
            }
        }
    }
    (tmp_path / ".nemoclaw").mkdir()
    (tmp_path / ".nemoclaw" / "sandboxes.json").write_text(json.dumps(cfg))
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)

    result = _sandbox_inference_configs()
    assert len(result) == 1
    assert result[0]["sandboxRuntimeKind"] == "terminal"


def test_openshell_runtime_takes_precedence_over_json(tmp_path, monkeypatch):
    """Live openshell value wins over stale JSON field."""
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = {
        "sandboxes": {
            "alpha": {
                "provider": "anthropic-prod",
                "model": "claude-haiku-4-5",
                "runtimeKind": "docker",  # stale value in JSON
            }
        }
    }
    (tmp_path / ".nemoclaw").mkdir()
    (tmp_path / ".nemoclaw" / "sandboxes.json").write_text(json.dumps(cfg))

    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "Name: alpha\nRuntime: terminal\n"})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)

    result = _sandbox_inference_configs()
    assert result[0]["sandboxRuntimeKind"] == "terminal"


def test_sandbox_configs_no_runtime_field_when_absent(tmp_path, monkeypatch):
    """When neither openshell nor JSON provides runtimeKind, the key is absent."""
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = {
        "sandboxes": {"dev": {"provider": "openai-api", "model": "gpt-4o"}}
    }
    (tmp_path / ".nemoclaw").mkdir()
    (tmp_path / ".nemoclaw" / "sandboxes.json").write_text(json.dumps(cfg))
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)

    result = _sandbox_inference_configs()
    assert len(result) == 1
    assert "sandboxRuntimeKind" not in result[0]


def test_sandbox_configs_ollama_surfaces_runtime_from_openshell(tmp_path, monkeypatch):
    """Ollama sandboxes also get sandboxRuntimeKind from openshell."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("OLLAMA_HOST_DOCKER_INTERNAL", raising=False)
    monkeypatch.delenv("OLLAMA_LOCALHOST", raising=False)
    cfg = {
        "sandboxes": {"local": {"provider": "ollama", "model": "llama3"}}
    }
    (tmp_path / ".nemoclaw").mkdir()
    (tmp_path / ".nemoclaw" / "sandboxes.json").write_text(json.dumps(cfg))

    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda *a, **kw: (_ for _ in ()).throw(OSError()))
    fake = type("R", (), {"stdout": "Name: local\nRuntime: terminal\n"})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)

    result = _sandbox_inference_configs()
    assert len(result) == 1
    assert result[0]["providerKey"] == "ollama"
    assert result[0]["sandboxRuntimeKind"] == "terminal"
