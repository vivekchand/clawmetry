"""`clawmetry uninstall` must remove EVERY com.clawmetry.* LaunchAgent.

Regression (2026-07-15): uninstall only handled com.clawmetry.sync.plist,
leaving com.clawmetry.dashboard.plist registered. That agent has KeepAlive,
so launchd kept the dashboard serving on localhost:8900 from the already
deleted ~/.clawmetry venv (open file handles survive the rmtree) — and
respawned it on every login.
"""

import subprocess
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import clawmetry.cli as cli_mod
import clawmetry.sync as sync_mod


def _setup_fake_darwin(tmp_path, monkeypatch, recorded):
    home = tmp_path / "home"
    la_dir = home / "Library" / "LaunchAgents"
    la_dir.mkdir(parents=True)

    for label in (
        "com.clawmetry.dashboard",
        "com.clawmetry.sync",
        "com.clawmetry.sandbox.nemoclaw-sandbox",
    ):
        (la_dir / f"{label}.plist").write_text("<plist/>")
    (la_dir / "com.other.app.plist").write_text("<plist/>")

    clawmetry_dir = home / ".clawmetry"
    (clawmetry_dir / "bin").mkdir(parents=True)
    (clawmetry_dir / "bin" / "clawmetry").write_text("#!/usr/bin/env python3\n")

    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr("platform.system", lambda: "Darwin")

    def fake_run(cmd, *a, **kw):
        recorded.append(list(cmd))
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.input", lambda *_: "uninstall")
    monkeypatch.setattr(cli_mod, "_get_nemoclaw_sandboxes", lambda: [])
    monkeypatch.setattr(cli_mod, "_count_sync_daemons", lambda: 0)
    monkeypatch.setattr(cli_mod, "_kill_sync_daemon", lambda: None)
    for name in ("CONFIG_FILE", "STATE_FILE", "LOG_FILE"):
        monkeypatch.setattr(sync_mod, name, home / f".fake_{name.lower()}")
    return home, la_dir


def test_uninstall_removes_all_clawmetry_launchagents(tmp_path, monkeypatch):
    recorded = []
    home, la_dir = _setup_fake_darwin(tmp_path, monkeypatch, recorded)
    dash_kills = []
    monkeypatch.setattr(
        cli_mod, "_kill_dashboard_processes", lambda: dash_kills.append(1) or 0
    )

    cli_mod._cmd_uninstall()

    leftovers = sorted(p.name for p in la_dir.glob("com.clawmetry.*.plist"))
    assert leftovers == [], f"launchd plists survived uninstall: {leftovers}"
    # Unrelated agents must be untouched.
    assert (la_dir / "com.other.app.plist").exists()
    assert not (home / ".clawmetry").exists()

    booted = {c[2].rsplit("/", 1)[-1] for c in recorded if c[:2] == ["launchctl", "bootout"]}
    assert booted == {
        "com.clawmetry.dashboard",
        "com.clawmetry.sync",
        "com.clawmetry.sandbox.nemoclaw-sandbox",
    }
    assert dash_kills, "_kill_dashboard_processes was not invoked"


def test_uninstall_falls_back_to_unload_without_bootout(tmp_path, monkeypatch):
    recorded = []
    _, la_dir = _setup_fake_darwin(tmp_path, monkeypatch, recorded)
    monkeypatch.setattr(cli_mod, "_kill_dashboard_processes", lambda: 0)

    def fake_run(cmd, *a, **kw):
        recorded.append(list(cmd))
        rc = 1 if cmd[:2] == ["launchctl", "bootout"] else 0
        return types.SimpleNamespace(returncode=rc, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    cli_mod._cmd_uninstall()

    unloaded = [c for c in recorded if c[:2] == ["launchctl", "unload"]]
    assert len(unloaded) == 3
    assert not list(la_dir.glob("com.clawmetry.*.plist"))


def test_kill_dashboard_processes_skips_self(monkeypatch):
    import os

    own = os.getpid()
    ps_out = (
        f"  {own} /Users/x/.clawmetry/bin/python3 /Users/x/.clawmetry/bin/clawmetry uninstall\n"
        f"  424242 /Users/x/.clawmetry/bin/python3 /Users/x/.clawmetry/bin/clawmetry --no-debug --port 8900\n"
        f"  424243 /usr/bin/some-unrelated-daemon --port 8900\n"
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **kw: types.SimpleNamespace(returncode=0, stdout=ps_out, stderr=""),
    )
    killed = []
    monkeypatch.setattr(os, "kill", lambda pid, sig: killed.append(pid))

    assert cli_mod._kill_dashboard_processes() == 1
    assert killed == [424242]
