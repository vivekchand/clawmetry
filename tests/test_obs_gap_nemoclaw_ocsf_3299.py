"""Tests for #3299 — _openshell_sandbox_logs retrieves OCSF JSON audit log
lines for a NemoClaw sandbox and the sync hook ingests them into DuckDB.
"""
import json
import shutil
import subprocess

import pytest

from clawmetry.adapters.openclaw import _openshell_sandbox_logs


# -- _openshell_sandbox_logs --------------------------------------------------

def test_logs_returns_empty_when_openshell_absent(monkeypatch):
    """No openshell binary -> [] with no exception."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)
    assert _openshell_sandbox_logs("alpha") == []


def test_logs_calls_settings_set_and_logs(monkeypatch):
    """Both 'settings set' and 'logs' commands are invoked for the sandbox."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    calls = []

    def fake_run(cmd, **kw):
        calls.append(" ".join(str(c) for c in cmd[1:]))
        return type("R", (), {"stdout": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)
    _openshell_sandbox_logs("deepagents-code")

    assert "settings set deepagents-code --key ocsf_json_enabled --value true" in calls
    assert "logs deepagents-code -n 20 --source all" in calls


def test_logs_parses_json_lines(monkeypatch):
    """Valid JSON lines are returned as parsed dicts."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    ev1 = {"uid": "abc", "time": 1700000001, "activity": "exec"}
    ev2 = {"uid": "def", "time": 1700000002, "activity": "net"}
    output = "\n".join([json.dumps(ev1), json.dumps(ev2)]) + "\n"

    def fake_run(cmd, **kw):
        if cmd[1] == "logs":
            return type("R", (), {"stdout": output})()
        return type("R", (), {"stdout": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = _openshell_sandbox_logs("alpha")
    assert result == [ev1, ev2]


def test_logs_drops_non_json_lines(monkeypatch):
    """Non-JSON lines are silently skipped; valid JSON lines still returned."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    ev = {"uid": "xyz", "time": 1700000001}
    output = "not-json\n" + json.dumps(ev) + "\nalso not json\n"

    def fake_run(cmd, **kw):
        if cmd[1] == "logs":
            return type("R", (), {"stdout": output})()
        return type("R", (), {"stdout": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = _openshell_sandbox_logs("beta")
    assert result == [ev]


def test_logs_empty_output_returns_empty(monkeypatch):
    """Empty openshell logs output -> []."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")

    def fake_run(cmd, **kw):
        return type("R", (), {"stdout": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert _openshell_sandbox_logs("gamma") == []


def test_logs_subprocess_error_returns_empty(monkeypatch):
    """subprocess.run failure -> [] never raises."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")

    def boom(*a, **kw):
        raise OSError("binary broken")

    monkeypatch.setattr(subprocess, "run", boom)
    assert _openshell_sandbox_logs("alpha") == []


def test_logs_respects_count_param(monkeypatch):
    """count parameter is forwarded to the -n flag."""
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/openshell")
    calls = []

    def fake_run(cmd, **kw):
        calls.append(list(cmd))
        return type("R", (), {"stdout": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)
    _openshell_sandbox_logs("alpha", count=42)

    logs_call = next(c for c in calls if "logs" in c)
    n_idx = logs_call.index("-n")
    assert logs_call[n_idx + 1] == "42"
