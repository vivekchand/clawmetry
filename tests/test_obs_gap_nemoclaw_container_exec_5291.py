"""Tests for #5291 — NemoClaw: container-backed sandbox gateway log read via
sandbox exec when no host-side log is available.

For container-backed (non-terminal) sandboxes the gateway writes its log to
/tmp/gateway.log *inside* the container.  Host-side globs (_gateway_log_files)
return nothing, so _openshell_sandbox_logs must fall back to
`openshell sandbox exec -n <name> -- tail -n N /tmp/gateway.log`, matching the
harness's showSandboxLogsWithDeps approach.

Fingerprint: hgap-f28fbe6633
"""
from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from clawmetry.adapters.openclaw import _openshell_sandbox_logs


def _fake_run_factory(*, ocsf_stdout="", runtime_kind="container", exec_stdout=""):
    """Return a fake subprocess.run serving openshell mock responses."""
    def fake_run(cmd, **kw):
        words = [str(c) for c in cmd]
        if "sandbox" in words and "get" in words:
            return type("R", (), {"stdout": f"Runtime: {runtime_kind}\n"})()
        if "sandbox" in words and "exec" in words:
            return type("R", (), {"stdout": exec_stdout})()
        if "logs" in words and "--source" in words:
            return type("R", (), {"stdout": ocsf_stdout})()
        return type("R", (), {"stdout": ""})()
    return fake_run


def test_container_no_host_log_uses_sandbox_exec(monkeypatch):
    """Container sandbox + no host log → sandbox exec output ingested."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    monkeypatch.delenv("OPENSHELL_GATEWAY_LOG", raising=False)

    from clawmetry.adapters import openclaw as _oc
    monkeypatch.setattr(_oc, "_gateway_log_files", lambda: [])

    gw_event = {"ts": 1700000010, "msg": "container-gateway startup"}
    exec_out = json.dumps(gw_event) + "\n"

    monkeypatch.setattr(subprocess, "run", _fake_run_factory(exec_stdout=exec_out))

    result = _openshell_sandbox_logs("container-sandbox")
    assert gw_event in result


def test_container_exec_non_json_lines_dropped(monkeypatch):
    """sandbox exec output with non-JSON lines is silently skipped."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    monkeypatch.delenv("OPENSHELL_GATEWAY_LOG", raising=False)

    from clawmetry.adapters import openclaw as _oc
    monkeypatch.setattr(_oc, "_gateway_log_files", lambda: [])

    valid = {"ts": 1700000011, "msg": "ok"}
    exec_out = "not-json\n[INFO] gateway\n" + json.dumps(valid) + "\n"

    monkeypatch.setattr(subprocess, "run", _fake_run_factory(exec_stdout=exec_out))

    result = _openshell_sandbox_logs("container-sandbox")
    assert valid in result
    assert len(result) == 1


def test_host_log_present_sandbox_exec_not_called(monkeypatch, tmp_path):
    """When a host-side log IS found, sandbox exec is never invoked."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    monkeypatch.delenv("OPENSHELL_GATEWAY_LOG", raising=False)

    gw_log = tmp_path / "openclaw-2026-01-01.log"
    host_event = {"ts": 1700000020, "msg": "host-gateway"}
    gw_log.write_text(json.dumps(host_event) + "\n")

    from clawmetry.adapters import openclaw as _oc
    monkeypatch.setattr(_oc, "_gateway_log_files", lambda: [str(gw_log)])

    exec_called = []

    def fake_run(cmd, **kw):
        words = [str(c) for c in cmd]
        if "exec" in words:
            exec_called.append(True)
        if "sandbox" in words and "get" in words:
            return type("R", (), {"stdout": "Runtime: container\n"})()
        return type("R", (), {"stdout": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = _openshell_sandbox_logs("container-sandbox")
    assert host_event in result
    assert not exec_called, "sandbox exec must not be called when host log is present"


def test_openshell_gateway_log_set_sandbox_exec_not_called(monkeypatch, tmp_path):
    """OPENSHELL_GATEWAY_LOG override set (even if missing) → exec not called."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    monkeypatch.setenv("OPENSHELL_GATEWAY_LOG", "/nonexistent/gateway.log")

    from clawmetry.adapters import openclaw as _oc
    monkeypatch.setattr(_oc, "_gateway_log_files", lambda: [])

    exec_called = []

    def fake_run(cmd, **kw):
        words = [str(c) for c in cmd]
        if "exec" in words:
            exec_called.append(True)
        if "sandbox" in words and "get" in words:
            return type("R", (), {"stdout": "Runtime: container\n"})()
        return type("R", (), {"stdout": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = _openshell_sandbox_logs("container-sandbox")
    assert not exec_called, "sandbox exec must not be called when OPENSHELL_GATEWAY_LOG is set"


def test_terminal_sandbox_exec_not_called(monkeypatch):
    """Terminal sandboxes never trigger sandbox exec (gateway block skipped)."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    monkeypatch.delenv("OPENSHELL_GATEWAY_LOG", raising=False)

    from clawmetry.adapters import openclaw as _oc
    monkeypatch.setattr(_oc, "_gateway_log_files", lambda: [])

    exec_called = []

    def fake_run(cmd, **kw):
        words = [str(c) for c in cmd]
        if "exec" in words:
            exec_called.append(True)
        if "sandbox" in words and "get" in words:
            return type("R", (), {"stdout": "Runtime: terminal\n"})()
        return type("R", (), {"stdout": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)

    _openshell_sandbox_logs("term-sandbox")
    assert not exec_called
