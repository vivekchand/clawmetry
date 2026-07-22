"""Regression tests for Windows uninstall (#3914).

`clawmetry uninstall` on Windows crashed mid-purge: no code path stopped
the running sync daemon (the Darwin/Linux branches don't run, and
_kill_dashboard_processes shells to POSIX `ps`), so the daemon kept
sync.log open and the purge died on WinError 32 AFTER pip uninstall had
already removed the package. The node was left with a zombie
Scripts\\clawmetry.exe (every later invocation: ModuleNotFoundError), a
half-deleted ~/.clawmetry, and a false "Removed" success message printed
over a directory that was still there.

Pinned here: processes are stopped BEFORE any file purge on Windows, a
locked file warns-and-continues instead of aborting, and the process
enumeration can never match the uninstall process itself.
"""

import builtins
import os
import sys
import types
from pathlib import Path

import pytest

import clawmetry.cli as cli


# ── _safe_unlink ──────────────────────────────────────────────────────────


def test_safe_unlink_removes_file(tmp_path):
    f = tmp_path / "gone.log"
    f.write_text("x")
    assert cli._safe_unlink(f) is True
    assert not f.exists()


def test_safe_unlink_missing_file_is_ok(tmp_path):
    assert cli._safe_unlink(tmp_path / "never-existed.log") is True


def test_safe_unlink_locked_file_warns_not_raises(tmp_path, monkeypatch, capsys):
    """The #3914 crash: one locked file must never abort the purge."""
    f = tmp_path / "sync.log"
    f.write_text("held open")
    if os.name == "nt":
        # Real lock: an open handle without FILE_SHARE_DELETE blocks unlink.
        handle = open(f, "r")
        try:
            result = cli._safe_unlink(f, retries=2, delay=0.05)
        finally:
            handle.close()
    else:
        monkeypatch.setattr(
            Path, "unlink", lambda self, missing_ok=False: (_ for _ in ()).throw(
                PermissionError(32, "in use", str(f))
            )
        )
        result = cli._safe_unlink(f, retries=2, delay=0.05)
    assert result is False
    assert "Remove it manually" in capsys.readouterr().out


# ── _windows_clawmetry_pids ───────────────────────────────────────────────


@pytest.mark.skipif(os.name != "nt", reason="Windows process enumeration")
def test_windows_pids_excludes_self_and_non_clawmetry(monkeypatch):
    import json

    fake_rows = [
        {"ProcessId": os.getpid(), "CommandLine": "clawmetry.exe uninstall"},
        {"ProcessId": os.getppid(), "CommandLine": "clawmetry.exe uninstall"},
        {"ProcessId": 4242, "CommandLine": "python.exe -m clawmetry.sync"},
        {"ProcessId": 4243, "CommandLine": "python.exe -m pytest tests"},
    ]

    def fake_run(cmd, **kwargs):
        return types.SimpleNamespace(returncode=0, stdout=json.dumps(fake_rows), stderr="")

    import subprocess
    monkeypatch.setattr(subprocess, "run", fake_run)
    pids = [pid for pid, _ in cli._windows_clawmetry_pids()]
    assert pids == [4242]  # daemon found; self, parent, and pytest excluded


# ── uninstall ordering: stop processes BEFORE purging files ───────────────


def test_uninstall_windows_stops_processes_before_purge(monkeypatch, tmp_path, capsys):
    """Red on the un-fixed code: no Windows stop branch existed at all, so
    the daemon lived through the purge and sync.log unlink crashed."""
    import shutil
    import subprocess
    import platform
    import clawmetry.sync as sync

    calls = []

    # Sandbox every filesystem root the command touches (both env vars —
    # Windows expanduser ignores HOME, see clawmetry#3850).
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    clawmetry_dir = tmp_path / ".clawmetry"
    clawmetry_dir.mkdir()
    log_file = clawmetry_dir / "sync.log"
    log_file.write_text("live")
    monkeypatch.setattr(sync, "CONFIG_FILE", clawmetry_dir / "config.json", raising=False)
    monkeypatch.setattr(sync, "STATE_FILE", clawmetry_dir / "sync-state.json", raising=False)
    monkeypatch.setattr(sync, "LOG_FILE", log_file, raising=False)

    monkeypatch.setattr(platform, "system", lambda: "Windows")
    monkeypatch.setattr(builtins, "input", lambda prompt="": "uninstall")
    monkeypatch.setattr(cli, "_get_nemoclaw_sandboxes", lambda: [], raising=False)

    monkeypatch.setattr(
        cli, "_stop_windows_processes", lambda: calls.append("stop") or 1
    )
    monkeypatch.setattr(
        cli, "_kill_dashboard_processes", lambda: calls.append("posix-dash-kill") or 0
    )
    monkeypatch.setattr(
        cli, "_safe_unlink", lambda p, **kw: calls.append("unlink") or True
    )
    real_rmtree = shutil.rmtree
    monkeypatch.setattr(
        shutil, "rmtree",
        lambda p, **kw: calls.append("rmtree") or real_rmtree(p, ignore_errors=True),
    )
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **kw: calls.append("pip") or types.SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        subprocess, "Popen",
        lambda *a, **kw: calls.append("popen") or types.SimpleNamespace(pid=0),
    )

    cli._cmd_uninstall()

    assert "stop" in calls, f"Windows process stop never ran: {calls}"
    first_purge = min(
        (calls.index(c) for c in ("rmtree", "unlink", "pip") if c in calls),
        default=len(calls),
    )
    assert calls.index("stop") < first_purge, f"purge before process stop: {calls}"
    # The POSIX ps-based dashboard sweep is a silent no-op on Windows and
    # must not be relied on there.
    assert "posix-dash-kill" not in calls
