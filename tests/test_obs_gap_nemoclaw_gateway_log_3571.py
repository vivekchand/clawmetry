"""Tests for #3571 — NemoClaw: sandbox gateway log stream (/tmp/gateway.log)
merged for container-runtime sandboxes.

Verifies that _openshell_sandbox_logs() reads /tmp/gateway.log (env-overrideable
via OPENSHELL_GATEWAY_LOG) and appends its parsed JSON lines for non-terminal
sandboxes, matching the harness's showSandboxLogsWithDeps two-source merge.

Fingerprint: hgap-08cd94533a
"""
from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from clawmetry.adapters.openclaw import _openshell_sandbox_logs


def _fake_run_factory(*, ocsf_stdout="", runtime_kind="container"):
    """Return a fake subprocess.run that serves openshell mock responses."""
    def fake_run(cmd, **kw):
        cmd_words = [str(c) for c in cmd]
        if "sandbox" in cmd_words and "get" in cmd_words:
            return type("R", (), {"stdout": f"Runtime: {runtime_kind}\n"})()
        if "logs" in cmd_words and "--source" in cmd_words:
            return type("R", (), {"stdout": ocsf_stdout})()
        return type("R", (), {"stdout": ""})()
    return fake_run


def test_container_sandbox_includes_gateway_log(monkeypatch, tmp_path):
    """Container-runtime sandbox: gateway.log JSON lines appended to OCSF events."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")

    ocsf_event = {"uid": "ocsf-1", "activity": "exec"}
    gw_event = {"ts": 1700000001, "method": "tts.speak", "source": "gateway"}

    gw_log = tmp_path / "gateway.log"
    gw_log.write_text(json.dumps(gw_event) + "\n")
    monkeypatch.setenv("OPENSHELL_GATEWAY_LOG", str(gw_log))

    monkeypatch.setattr(
        subprocess, "run",
        _fake_run_factory(ocsf_stdout=json.dumps(ocsf_event) + "\n", runtime_kind="container"),
    )

    result = _openshell_sandbox_logs("my-sandbox")
    assert ocsf_event in result
    assert gw_event in result


def test_terminal_sandbox_excludes_gateway_log(monkeypatch, tmp_path):
    """Terminal-runtime sandbox: gateway.log is never read (harness parity)."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")

    gw_event = {"ts": 1700000001, "method": "tts.speak"}
    gw_log = tmp_path / "gateway.log"
    gw_log.write_text(json.dumps(gw_event) + "\n")
    monkeypatch.setenv("OPENSHELL_GATEWAY_LOG", str(gw_log))

    monkeypatch.setattr(
        subprocess, "run",
        _fake_run_factory(runtime_kind="terminal"),
    )

    result = _openshell_sandbox_logs("term-sandbox")
    assert gw_event not in result


def test_container_sandbox_missing_gateway_log_silently_ignored(monkeypatch):
    """Container sandbox with no gateway.log returns OCSF events only; no error."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")
    monkeypatch.setenv("OPENSHELL_GATEWAY_LOG", "/nonexistent/path/gateway.log")

    ocsf_event = {"uid": "ocsf-1", "activity": "exec"}
    monkeypatch.setattr(
        subprocess, "run",
        _fake_run_factory(ocsf_stdout=json.dumps(ocsf_event) + "\n", runtime_kind="docker"),
    )

    result = _openshell_sandbox_logs("docker-sandbox")
    assert result == [ocsf_event]


def test_container_sandbox_non_json_gateway_lines_dropped(monkeypatch, tmp_path):
    """Non-JSON gateway.log lines are silently skipped; valid events still returned."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")

    valid_gw = {"ts": 1700000002, "msg": "gateway ok"}
    gw_log = tmp_path / "gateway.log"
    gw_log.write_text(
        "not-json-line\n"
        "[INFO] gateway started\n"
        + json.dumps(valid_gw) + "\n"
    )
    monkeypatch.setenv("OPENSHELL_GATEWAY_LOG", str(gw_log))

    monkeypatch.setattr(
        subprocess, "run",
        _fake_run_factory(runtime_kind="container"),
    )

    result = _openshell_sandbox_logs("my-sandbox")
    assert valid_gw in result
    assert len(result) == 1


def test_gateway_log_count_limits_lines_read(monkeypatch, tmp_path):
    """Only the last `count` lines of gateway.log are read."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")

    lines = [{"i": i} for i in range(10)]
    gw_log = tmp_path / "gateway.log"
    gw_log.write_text("\n".join(json.dumps(e) for e in lines) + "\n")
    monkeypatch.setenv("OPENSHELL_GATEWAY_LOG", str(gw_log))

    monkeypatch.setattr(
        subprocess, "run",
        _fake_run_factory(runtime_kind="container"),
    )

    result = _openshell_sandbox_logs("my-sandbox", count=3)
    # Only the last 3 entries (i=7,8,9) should appear
    assert {"i": 9} in result
    assert {"i": 8} in result
    assert {"i": 7} in result
    assert {"i": 0} not in result


def test_no_openshell_gateway_log_never_read(monkeypatch, tmp_path):
    """When openshell is absent, gateway.log is never opened (early return)."""
    monkeypatch.setattr(shutil, "which", lambda _: None)

    opened = []

    real_open = open

    def patched_open(path, *a, **kw):
        opened.append(path)
        return real_open(path, *a, **kw)

    gw_log = tmp_path / "gateway.log"
    gw_log.write_text('{"ts": 123}\n')
    monkeypatch.setenv("OPENSHELL_GATEWAY_LOG", str(gw_log))

    result = _openshell_sandbox_logs("my-sandbox")
    assert result == []
    assert not any(str(gw_log) in str(p) for p in opened)


def test_unknown_runtime_kind_includes_gateway_log(monkeypatch, tmp_path):
    """Unknown/absent sandboxRuntimeKind defaults to non-terminal; gateway.log included."""
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/openshell")

    gw_event = {"ts": 1700000003, "msg": "startup"}
    gw_log = tmp_path / "gateway.log"
    gw_log.write_text(json.dumps(gw_event) + "\n")
    monkeypatch.setenv("OPENSHELL_GATEWAY_LOG", str(gw_log))

    def fake_run(cmd, **kw):
        cmd_words = [str(c) for c in cmd]
        if "sandbox" in cmd_words and "get" in cmd_words:
            # No "Runtime:" line in output → sandboxRuntimeKind absent → ""
            return type("R", (), {"stdout": "Phase: running\n"})()
        return type("R", (), {"stdout": ""})()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = _openshell_sandbox_logs("unknown-kind-sandbox")
    assert gw_event in result
