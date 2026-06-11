"""Crash-loop rollback guard (clawmetry/update_guard.py).

perform_self_update ARMS the guard; run_daemon CHECKS it each boot. Three
rapid boots on a freshly-installed version = boot loop -> pip-roll back to
the previous version and exit for the supervisor to respawn. A healthy run
confirms (clears) the guard. These tests drive the pure state machine with
the pip/exit side effects injected.
"""
from __future__ import annotations

import importlib
import json
import time


def _ug(tmp_path, monkeypatch):
    import clawmetry.update_guard as ug
    ug = importlib.reload(ug)
    monkeypatch.setattr(ug, "STATE_PATH", tmp_path / "update_state.json")
    monkeypatch.setattr(ug, "ROLLBACK_MARKER", tmp_path / "update_rollback.json")
    return ug


def test_idle_without_armed_guard(tmp_path, monkeypatch):
    ug = _ug(tmp_path, monkeypatch)
    assert ug.check_boot_and_maybe_rollback("0.12.2") == "idle"


def test_arm_noops_on_same_version(tmp_path, monkeypatch):
    ug = _ug(tmp_path, monkeypatch)
    ug.arm_rollback_guard("0.12.2", "0.12.2", "auto")
    assert not ug.STATE_PATH.exists(), "same-version 'upgrade' must not arm"


def test_third_rapid_boot_rolls_back(tmp_path, monkeypatch):
    ug = _ug(tmp_path, monkeypatch)
    ug.arm_rollback_guard("0.12.1", "0.12.2", "auto")

    installed, exited = [], []
    fake_install = lambda v: (installed.append(v), True)[1]
    fake_exit = lambda code: exited.append(code)

    # Boots 1 and 2: armed, counter increments, no rollback.
    assert ug.check_boot_and_maybe_rollback("0.12.2", fake_install, fake_exit) == "armed"
    assert ug.check_boot_and_maybe_rollback("0.12.2", fake_install, fake_exit) == "armed"
    assert installed == [] and exited == []

    # Boot 3: crash loop -> roll back to the previous version and exit.
    status = ug.check_boot_and_maybe_rollback("0.12.2", fake_install, fake_exit)
    assert status == "rolled_back"
    assert installed == ["0.12.1"], "must pip-install the PREVIOUS version"
    assert exited == [0], "must exit so the supervisor respawns on the old wheel"
    assert not ug.STATE_PATH.exists(), "guard must clear after rollback"
    marker = json.loads(ug.ROLLBACK_MARKER.read_text())
    assert marker["from"] == "0.12.2" and marker["to"] == "0.12.1" and marker["ok"]


def test_failed_rollback_does_not_exit(tmp_path, monkeypatch):
    ug = _ug(tmp_path, monkeypatch)
    ug.arm_rollback_guard("0.12.1", "0.12.2", "auto")
    exited = []
    for _ in range(2):
        ug.check_boot_and_maybe_rollback("0.12.2", lambda v: False, exited.append)
    status = ug.check_boot_and_maybe_rollback("0.12.2", lambda v: False, exited.append)
    assert status == "rollback_failed"
    assert exited == [], "a failed pip rollback must NOT exit (keep running)"


def test_version_mismatch_clears_guard(tmp_path, monkeypatch):
    """Booting a version other than the armed target (update never applied,
    or someone already fixed it by hand) must clear the guard, not count."""
    ug = _ug(tmp_path, monkeypatch)
    ug.arm_rollback_guard("0.12.1", "0.12.2", "auto")
    assert ug.check_boot_and_maybe_rollback("0.12.3") == "mismatch"
    assert not ug.STATE_PATH.exists()


def test_stale_guard_expires(tmp_path, monkeypatch):
    ug = _ug(tmp_path, monkeypatch)
    ug.arm_rollback_guard("0.12.1", "0.12.2", "auto")
    state = json.loads(ug.STATE_PATH.read_text())
    state["ts"] = time.time() - ug.WINDOW_S - 10
    ug.STATE_PATH.write_text(json.dumps(state))
    assert ug.check_boot_and_maybe_rollback("0.12.2") == "expired"
    assert not ug.STATE_PATH.exists()


def test_confirm_clears_guard(tmp_path, monkeypatch):
    ug = _ug(tmp_path, monkeypatch)
    ug.arm_rollback_guard("0.12.1", "0.12.2", "auto")
    ug.check_boot_and_maybe_rollback("0.12.2", lambda v: True, lambda c: None)
    ug.confirm_update_ok()
    assert not ug.STATE_PATH.exists(), "healthy-run confirmation must clear"
    # Next boot after confirmation is a clean slate.
    assert ug.check_boot_and_maybe_rollback("0.12.2") == "idle"


def test_perform_self_update_arms_guard(tmp_path, monkeypatch):
    """The vetted upgrade path must arm the guard after pip succeeds
    (integration seam: routes.meta.perform_self_update -> update_guard).
    pip + restart are stubbed; restart=False keeps the process alive."""
    ug = _ug(tmp_path, monkeypatch)

    import subprocess

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Proc())
    monkeypatch.setattr(
        subprocess, "check_output",
        lambda *a, **k: b"Name: clawmetry\nVersion: 9.9.9\n",
    )

    import routes.meta as meta
    payload, status = meta.perform_self_update(reason="auto", restart=False)
    assert status == 200 and payload.get("ok") is True
    assert payload.get("restart_deferred") is True
    state = json.loads(ug.STATE_PATH.read_text())
    assert state["target"] == "9.9.9", "guard must be armed for the new version"
    assert state["reason"] == "auto"
