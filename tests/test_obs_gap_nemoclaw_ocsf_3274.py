"""Tests for #3274 -- _openshell_sandbox_ocsf_enabled surfaces the
ocsf_json_enabled setting per NemoClaw sandbox in DetectResult.meta.sandboxInferenceConfigs.
"""
import json
import shutil
import subprocess

import pytest

from clawmetry.adapters.openclaw import (
    _openshell_sandbox_ocsf_enabled,
    _sandbox_inference_configs,
)


# -- _openshell_sandbox_ocsf_enabled ------------------------------------------

def test_ocsf_returns_empty_when_openshell_absent(monkeypatch):
    """No openshell binary -> {} with no exception."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)
    assert _openshell_sandbox_ocsf_enabled("alpha") == {}


def test_ocsf_enabled_true(monkeypatch):
    """ocsf_json_enabled: true -> {"sandboxOcsfJsonEnabled": True}."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "some_key: value\nocsf_json_enabled: true\n"})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    result = _openshell_sandbox_ocsf_enabled("alpha")
    assert result == {"sandboxOcsfJsonEnabled": True}


def test_ocsf_enabled_false(monkeypatch):
    """ocsf_json_enabled: false -> {"sandboxOcsfJsonEnabled": False}."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "ocsf_json_enabled: false\n"})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    result = _openshell_sandbox_ocsf_enabled("beta")
    assert result == {"sandboxOcsfJsonEnabled": False}


def test_ocsf_key_absent_returns_empty(monkeypatch):
    """Output without ocsf_json_enabled -> {}."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "some_key: value\nother_key: 123\n"})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    assert _openshell_sandbox_ocsf_enabled("gamma") == {}


def test_ocsf_subprocess_error_returns_empty(monkeypatch):
    """Subprocess failure -> {} never raises."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    def boom(*a, **kw):
        raise OSError("binary broken")
    monkeypatch.setattr(subprocess, "run", boom)
    assert _openshell_sandbox_ocsf_enabled("alpha") == {}


def test_ocsf_empty_stdout_returns_empty(monkeypatch):
    """Empty stdout -> {} with no exception."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": ""})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    assert _openshell_sandbox_ocsf_enabled("beta") == {}


def test_ocsf_case_insensitive_value(monkeypatch):
    """Value matching is case-insensitive (TRUE / True / true all work)."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    fake = type("R", (), {"stdout": "ocsf_json_enabled: TRUE\n"})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    result = _openshell_sandbox_ocsf_enabled("alpha")
    assert result == {"sandboxOcsfJsonEnabled": True}


# -- integration: _sandbox_inference_configs merges OCSF flag ----------------

def test_sandbox_inference_configs_includes_ocsf_flag(tmp_path, monkeypatch):
    """sandboxInferenceConfigs entries gain sandboxOcsfJsonEnabled when
    openshell settings reports the flag."""
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

    def fake_run(cmd, **kw):
        # cmd form: ["openshell", "settings", "get", <name>] or sandbox variant
        if cmd[1] == "settings":
            return type("R", (), {"stdout": "ocsf_json_enabled: true\n"})()
        return type("R", (), {"stdout": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = _sandbox_inference_configs()
    assert len(result) == 1
    r = result[0]
    assert r["sandboxOcsfJsonEnabled"] is True
    assert r["providerKey"] == "anthropic"
    assert r["isDefault"] is True


def test_sandbox_inference_configs_no_ocsf_when_openshell_absent(tmp_path, monkeypatch):
    """When openshell is absent, entries are returned without sandboxOcsfJsonEnabled
    (backwards-compatible)."""
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
    assert "sandboxOcsfJsonEnabled" not in result[0]
    assert result[0]["providerKey"] == "openai"


def test_sandbox_inference_configs_ocsf_per_sandbox(tmp_path, monkeypatch):
    """Each sandbox is queried independently; OCSF flag can differ per sandbox."""
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

    ocsf_states = {"prod": "true", "dev": "false"}
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")

    def fake_run(cmd, **kw):
        # cmd form: ["openshell", "settings", "get", <sandbox_name>]
        #       or: ["openshell", "sandbox",  "get", <sandbox_name>]
        if cmd[1] == "settings":
            sandbox_name = cmd[3]
            return type("R", (), {
                "stdout": f"ocsf_json_enabled: {ocsf_states[sandbox_name]}\n"
            })()
        return type("R", (), {"stdout": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = _sandbox_inference_configs()
    assert len(result) == 2
    by_name = {r["sandbox"]: r for r in result}
    assert by_name["prod"]["sandboxOcsfJsonEnabled"] is True
    assert by_name["dev"]["sandboxOcsfJsonEnabled"] is False
