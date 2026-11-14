"""The CLI restarts and stops only the daemon owning this user's store."""
from __future__ import annotations

import types

from clawmetry import cli


def test_sync_daemon_pid_uses_current_home_lock(monkeypatch, tmp_path):
    from clawmetry import sync

    pid_file = tmp_path / "sync.pid"
    monkeypatch.setattr(sync, "_pid_file", lambda: pid_file)
    monkeypatch.setattr(sync, "_read_lock_record", lambda path: {"pid": 1234, "start": "same-process"})
    monkeypatch.setattr(sync, "_lock_holder_verdict", lambda record, path: ("held", "daemon_running"))

    assert cli._sync_daemon_pid() == 1234
    assert cli._is_sync_running() is True
    assert cli._count_sync_daemons() == 1


def test_sync_daemon_pid_ignores_unrelated_processes(monkeypatch):
    from clawmetry import sync

    monkeypatch.setattr(sync, "_pid_file", lambda: "/current-user/sync.pid")
    monkeypatch.setattr(sync, "_read_lock_record", lambda path: None)
    monkeypatch.setattr(sync, "_lock_holder_verdict", lambda *args: (_ for _ in ()).throw(AssertionError()))

    assert cli._sync_daemon_pid() is None
    assert cli._is_sync_running() is False
    assert cli._count_sync_daemons() == 0


def test_kill_sync_daemon_terminates_only_verified_lock_holder(monkeypatch):
    from clawmetry import sync

    signals = []
    alive_checks = iter([True])
    monkeypatch.setattr(cli, "_sync_daemon_pid", lambda: 1234)
    monkeypatch.setattr(cli.os, "kill", lambda pid, sig: signals.append((pid, sig)))
    monkeypatch.setattr(sync, "_process_is_gone", lambda pid: next(alive_checks))
    monkeypatch.setattr("time.sleep", lambda seconds: None)

    assert cli._kill_sync_daemon(timeout=1) is True
    assert len(signals) == 1 and signals[0][0] == 1234


def test_linux_restart_stops_old_daemon_before_starting_fallback(monkeypatch):
    calls = []
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(cli, "_register_systemd", lambda config, restart=False: False)
    monkeypatch.setattr(cli, "_kill_sync_daemon", lambda: calls.append("stop") or True)
    monkeypatch.setattr(cli, "_start_subprocess", lambda: calls.append("start"))
    monkeypatch.setattr(cli, "_wait_for_sync_daemon", lambda: calls.append("wait") or True)

    assert cli._start_daemon({}, types.SimpleNamespace(restart=True, foreground=False)) is True
    assert calls == ["stop", "start", "wait"]


def test_linux_restart_fails_if_old_daemon_does_not_stop(monkeypatch):
    calls = []
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(cli, "_register_systemd", lambda config, restart=False: False)
    monkeypatch.setattr(cli, "_kill_sync_daemon", lambda: False)
    monkeypatch.setattr(cli, "_start_subprocess", lambda: calls.append("start"))

    assert cli._start_daemon({}, types.SimpleNamespace(restart=True, foreground=False)) is False
    assert calls == []
