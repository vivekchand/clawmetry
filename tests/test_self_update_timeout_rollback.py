"""perform_self_update must roll back to a known-good install when pip fails
OR is killed by its 180s timeout (ghost-install fix, 2026-07-30).

A pip KILLED mid-install (TimeoutExpired) lays down the new wheel's package
files but never generates the console scripts: site-packages then claims the
new version is installed while ``bin/clawmetry`` is gone, and every later
plain ``pip install --upgrade`` no-ops against that metadata. The node is
left with a dangling ``~/.local/bin/clawmetry`` symlink (seen live on the
founder's machine: dist-info with no INSTALLER file and no ``bin/`` entries
in RECORD, created the second the auto-updater fired).

Before this fix only the pip-exit-nonzero branch rolled back; the
TimeoutExpired branch returned without any repair — and the timeout kill is
exactly the failure mode that strands the ghost state. The rollback must use
``--force-reinstall`` so the entry points are regenerated regardless of what
the (lying) metadata claims.
"""

from __future__ import annotations

import subprocess
import types


def _fake_completed(returncode=0, stdout="", stderr=""):
    return types.SimpleNamespace(
        returncode=returncode, stdout=stdout, stderr=stderr,
    )


def _patched_run(calls, upgrade_behaviour):
    """A subprocess.run stand-in: records every command, applies
    ``upgrade_behaviour`` to the main ``pip install --upgrade`` call and
    succeeds everything else (ensurepip, the rollback install)."""

    def _run(cmd, *a, **k):
        cmd = list(cmd)
        calls.append(cmd)
        if "--upgrade" in cmd and "ensurepip" not in cmd:
            return upgrade_behaviour(cmd)
        return _fake_completed()

    return _run


def _rollback_calls(calls, old_version):
    return [
        c for c in calls
        if "--force-reinstall" in c and f"clawmetry=={old_version}" in c
    ]


def test_timeout_rolls_back_with_force_reinstall(monkeypatch):
    import dashboard
    from routes import meta

    calls = []

    def _timeout(cmd):
        raise subprocess.TimeoutExpired(cmd, 180)

    monkeypatch.setattr(subprocess, "run", _patched_run(calls, _timeout))
    payload, status = meta.perform_self_update(reason="test-timeout")

    assert payload["ok"] is False
    assert status == 500
    assert "timed out" in payload["error"]
    rollbacks = _rollback_calls(calls, dashboard.__version__)
    assert rollbacks, (
        "TimeoutExpired must trigger a pip rollback to the old version with "
        "--force-reinstall — a pip killed mid-install leaves a scriptless "
        f"half-install that a plain install can't repair. Calls seen: {calls}"
    )


def test_pip_failure_rolls_back_with_force_reinstall(monkeypatch):
    import dashboard
    from routes import meta

    calls = []

    def _fail(cmd):
        return _fake_completed(returncode=1, stderr="boom")

    monkeypatch.setattr(subprocess, "run", _patched_run(calls, _fail))
    payload, status = meta.perform_self_update(reason="test-pip-fail")

    assert payload["ok"] is False
    assert status == 500
    rollbacks = _rollback_calls(calls, dashboard.__version__)
    assert rollbacks, (
        "a nonzero pip exit must trigger a --force-reinstall rollback to the "
        f"old version. Calls seen: {calls}"
    )


def test_success_does_not_roll_back(monkeypatch):
    import dashboard
    from routes import meta

    calls = []
    monkeypatch.setattr(
        subprocess, "run",
        _patched_run(calls, lambda cmd: _fake_completed()),
    )
    # The pip-show version re-read uses check_output; stub it. Keep the
    # crash-loop rollback guard from touching real ~/.clawmetry state.
    monkeypatch.setattr(
        subprocess, "check_output",
        lambda *a, **k: b"Version: 0.0.0\n",
    )
    from clawmetry import update_guard
    monkeypatch.setattr(
        update_guard, "arm_rollback_guard", lambda *a, **k: None,
    )
    payload, status = meta.perform_self_update(
        reason="test-ok", restart=False,
    )
    assert payload["ok"] is True
    assert status == 200
    assert not _rollback_calls(calls, dashboard.__version__), (
        "a successful upgrade must not trigger a rollback"
    )
