"""clawmetry/daemon_registration.py — the shared "make the sync daemon
survive a reboot/logoff/crash" helper, and the two call sites that regressed
without it: cli.py's Windows branch of _start_daemon, and
routes/update_check.py's _daemon_supervised probe.

Windows previously had NO persistent-service equivalent of launchd
KeepAlive / systemd Restart=always -- _start_daemon fell through to a bare
detached subprocess with zero reboot/crash/logoff recovery, so a Windows
node silently stopped auto-updating (and ingesting) after any restart until
a human manually relaunched `clawmetry`. These tests pin the Task Scheduler
registration this fix adds, and its wiring into supervision detection.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import clawmetry.daemon_registration as dreg


class _Res:
    def __init__(self, rc=0, stdout=""):
        self.returncode = rc
        self.stdout = stdout


def test_register_windows_task_invokes_schtasks_with_restart_on_failure(monkeypatch):
    calls = []

    def _run(cmd, *a, **k):
        calls.append(cmd)
        return _Res(0)

    monkeypatch.setattr("subprocess.run", _run)
    written = {}

    def _fake_tempfile(mode, suffix, delete, encoding):
        import io

        class _FH:
            name = "/tmp/fake-task.xml"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def write(self, content):
                written["xml"] = content

        return _FH()

    monkeypatch.setattr("tempfile.NamedTemporaryFile", _fake_tempfile)
    monkeypatch.setattr(os, "remove", lambda p: None)

    ok = dreg.register_windows_task({})
    assert ok is True

    create_calls = [c for c in calls if "/create" in c]
    assert len(create_calls) == 1
    create_cmd = create_calls[0]
    assert "schtasks" in create_cmd[0]
    assert dreg.WINDOWS_TASK_NAME in create_cmd
    assert "/f" in create_cmd  # overwrite an existing registration idempotently

    # The task definition itself must restart on failure and run at logon,
    # matching launchd KeepAlive / systemd Restart=always semantics.
    assert "<RestartOnFailure>" in written["xml"]
    assert "<LogonTrigger>" in written["xml"]
    assert "-m clawmetry.sync" in written["xml"]

    # A successful /create must also /run the task immediately so THIS
    # session gets the daemon too, not just the next logon.
    run_calls = [c for c in calls if "/run" in c]
    assert len(run_calls) == 1


def test_register_windows_task_returns_false_on_schtasks_failure(monkeypatch):
    # tempfile creation raising is the simplest way to force the "something
    # went wrong" branch -> the function must fail closed (return False),
    # never raise, so callers can fall back safely.
    def _boom(**k):
        raise OSError("no temp dir")
    monkeypatch.setattr("tempfile.NamedTemporaryFile", _boom)
    assert dreg.register_windows_task({}) is False


def test_windows_task_registered_reflects_schtasks_query(monkeypatch):
    monkeypatch.setattr("subprocess.run", lambda cmd, *a, **k: _Res(0))
    assert dreg.windows_task_registered() is True

    monkeypatch.setattr("subprocess.run", lambda cmd, *a, **k: _Res(1))
    assert dreg.windows_task_registered() is False

    def _boom(*a, **k):
        raise FileNotFoundError("schtasks not on PATH")
    monkeypatch.setattr("subprocess.run", _boom)
    assert dreg.windows_task_registered() is False


def test_register_systemd_bounds_every_subprocess_call(monkeypatch, tmp_path):
    """2026-08-06 CI regression: these calls had no timeout, and this whole
    function runs synchronously inside the onboarding-complete HTTP handler.
    A runner with no user systemd/dbus session can make `systemctl --user
    enable --now` hang instead of failing fast -- visible live as the
    dashboard stuck forever on "Initializing ClawMetry" for mobile E2E
    screenshots. Every systemctl call here must be bounded."""
    monkeypatch.setattr(dreg, "_is_root", lambda: False)
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/systemctl")
    calls = []

    def _run(cmd, *a, **k):
        calls.append((cmd, k))
        return _Res(0, "active")

    monkeypatch.setattr("subprocess.run", _run)
    monkeypatch.setattr("time.sleep", lambda s: None)

    assert dreg.register_systemd({}) is True
    assert len(calls) == 3, "daemon-reload, enable --now, is-active"
    for cmd, kwargs in calls:
        assert kwargs.get("timeout") is not None, f"no timeout on {cmd}"


def test_register_launchd_bounds_every_subprocess_call(monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    calls = []

    def _run(cmd, *a, **k):
        calls.append((cmd, k))
        return _Res(1)  # force the fallback `launchctl load` branch too

    monkeypatch.setattr("subprocess.run", _run)
    monkeypatch.setattr(os, "getuid", lambda: 501, raising=False)

    dreg.register_launchd({})

    assert len(calls) == 2, "bootstrap + the load -w fallback"
    for cmd, kwargs in calls:
        assert kwargs.get("timeout") is not None, f"no timeout on {cmd}"


def test_ensure_persistent_daemon_dispatches_by_platform(monkeypatch):
    monkeypatch.setattr("clawmetry.sync.ensure_local_config", lambda: None, raising=False)

    monkeypatch.setattr("platform.system", lambda: "Darwin")
    calls = []
    monkeypatch.setattr(dreg, "register_launchd", lambda cfg: calls.append("launchd") or True)
    assert dreg.ensure_persistent_daemon({}) is True
    assert calls == ["launchd"]

    calls.clear()
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(dreg, "register_systemd", lambda cfg: calls.append("systemd") or True)
    assert dreg.ensure_persistent_daemon({}) is True
    assert calls == ["systemd"]

    calls.clear()
    monkeypatch.setattr("platform.system", lambda: "Windows")
    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setattr(dreg, "register_windows_task", lambda cfg: calls.append("winreg") or True)
    assert dreg.ensure_persistent_daemon({}) is True
    assert calls == ["winreg"]


def test_ensure_persistent_daemon_falls_back_to_background_subprocess(monkeypatch):
    monkeypatch.setattr("clawmetry.sync.ensure_local_config", lambda: None, raising=False)
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(dreg, "register_systemd", lambda cfg: False)
    calls = []
    monkeypatch.setattr(dreg, "start_background_subprocess", lambda: calls.append(1) or True)
    assert dreg.ensure_persistent_daemon({}) is True
    assert calls == [1]


def test_ensure_persistent_daemon_never_raises_on_bad_config(monkeypatch):
    monkeypatch.setattr("clawmetry.sync.ensure_local_config",
                         lambda: (_ for _ in ()).throw(RuntimeError("boom")),
                         raising=False)
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(dreg, "register_systemd", lambda cfg: True)
    assert dreg.ensure_persistent_daemon(None) is True


# ── Wiring: cli.py _start_daemon's Windows branch ──────────────────────────

def test_start_daemon_windows_branch_uses_task_scheduler(monkeypatch):
    import clawmetry.cli as cli

    monkeypatch.setattr("platform.system", lambda: "Windows")
    monkeypatch.setattr(cli.os, "name", "nt")
    calls = []
    monkeypatch.setattr("clawmetry.daemon_registration.register_windows_task",
                         lambda cfg: calls.append(cfg) or True)
    fallback_calls = []
    monkeypatch.setattr(cli, "_start_subprocess", lambda: fallback_calls.append(1))

    args = type("Args", (), {"foreground": False})()
    cli._start_daemon({"node_id": "n1"}, args)

    assert calls == [{"node_id": "n1"}]
    assert fallback_calls == [], "Task Scheduler succeeded, must not fall back"


def test_start_daemon_windows_branch_falls_back_when_schtasks_unavailable(monkeypatch):
    import clawmetry.cli as cli

    monkeypatch.setattr("platform.system", lambda: "Windows")
    monkeypatch.setattr(cli.os, "name", "nt")
    monkeypatch.setattr("clawmetry.daemon_registration.register_windows_task",
                         lambda cfg: False)
    fallback_calls = []
    monkeypatch.setattr(cli, "_start_subprocess", lambda: fallback_calls.append(1))

    args = type("Args", (), {"foreground": False})()
    cli._start_daemon({"node_id": "n1"}, args)

    assert fallback_calls == [1], "schtasks failed, must fall back to unsupervised subprocess"


# ── Wiring: routes/update_check.py's _daemon_supervised Windows detection ──

def test_daemon_supervised_detects_windows_task(monkeypatch):
    import routes.update_check as uc

    monkeypatch.setattr(uc.sys, "platform", "win32")
    monkeypatch.setattr(uc.os, "name", "nt")
    monkeypatch.setattr("clawmetry.daemon_registration.windows_task_registered",
                         lambda: True)
    assert uc._daemon_supervised() is True

    monkeypatch.setattr("clawmetry.daemon_registration.windows_task_registered",
                         lambda: False)
    assert uc._daemon_supervised() is False
