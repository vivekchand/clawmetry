"""Regression tests for portable pid liveness (#windows-liveness).

os.kill(pid, 0) is NOT a liveness probe on Windows: signal 0 is
CTRL_C_EVENT there, and the call returns without error even for
long-dead pids (verified empirically on Windows 11 / CPython 3.12 —
dead pid, detached process, and group-leader all "succeed"). Every raw
os.kill(pid, 0) probe therefore reported stale pid files as live
processes on Windows:

- the sync daemon refused to start after a crash (stale sync.pid read
  as "another instance is running")
- gateway/dashboard/proxy status stuck on "running" after the process
  died
- the MCP server and /__local_query__ kept dispatching to a dead daemon

The portable probe is clawmetry.process_control.is_alive() (Win32
OpenProcess + GetExitCodeProcess on Windows, the POSIX idiom
elsewhere). These tests pin its semantics, prove the stale-lock
recovery, and guard against raw-probe reintroduction.
"""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from clawmetry.process_control import is_alive


def _spawn_sleeper():
    return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])


def _spawn_dead():
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    return child


def test_is_alive_true_for_live_child():
    child = _spawn_sleeper()
    try:
        assert is_alive(child.pid) is True
        # The probe must OBSERVE, never signal: the child stays alive.
        time.sleep(0.2)
        assert child.poll() is None
    finally:
        child.kill()
        child.wait()


def test_is_alive_false_for_exited_child():
    child = _spawn_dead()
    deadline = time.time() + 5
    while is_alive(child.pid) and time.time() < deadline:
        time.sleep(0.1)
    # Red on the old code (Windows): os.kill(pid, 0) never raises, so the
    # dead child was reported alive forever.
    assert is_alive(child.pid) is False


def test_is_alive_rejects_garbage():
    assert is_alive(None) is False
    assert is_alive(0) is False
    assert is_alive(-1) is False


def test_acquire_pid_lock_reclaims_stale_lock(monkeypatch, tmp_path):
    """A crashed daemon leaves sync.pid behind; the next start must reclaim it.

    Red on the old code (Windows): the stale pid probed as alive, so
    _acquire_pid_lock returned False and the daemon could never start
    again until the file was deleted by hand.
    """
    import clawmetry.sync as sync

    dead = _spawn_dead()
    pid_file = tmp_path / "sync.pid"
    pid_file.write_text(str(dead.pid))
    monkeypatch.setattr(sync, "_pid_file", lambda: pid_file)

    assert sync._acquire_pid_lock() is True
    assert pid_file.read_text().strip() == str(os.getpid())
    pid_file.unlink()


def test_acquire_pid_lock_respects_live_lock(monkeypatch, tmp_path):
    """A genuinely running instance must still win the lock."""
    import clawmetry.sync as sync

    live = _spawn_sleeper()
    try:
        pid_file = tmp_path / "sync.pid"
        pid_file.write_text(str(live.pid))
        monkeypatch.setattr(sync, "_pid_file", lambda: pid_file)

        assert sync._acquire_pid_lock() is False
        assert pid_file.read_text().strip() == str(live.pid)
    finally:
        live.kill()
        live.wait()


@pytest.mark.skipif(os.name != "nt", reason="Windows ACL branch of check 7")
def test_security_posture_no_false_world_readable_on_windows(monkeypatch, tmp_path):
    """POSIX mode bits read as 0o777 for every Windows dir; check 7 must not
    emit its false 'world-readable' warn + un-runnable chmod remediation."""
    import dashboard

    (tmp_path / ".openclaw").mkdir()
    (tmp_path / ".openclaw" / "openclaw.json").write_text("{}")
    real_expanduser = os.path.expanduser
    monkeypatch.setattr(
        os.path,
        "expanduser",
        lambda p: p.replace("~", str(tmp_path), 1) if p.startswith("~") else real_expanduser(p),
    )

    result = dashboard._scan_security_posture()
    checks = result if isinstance(result, list) else result.get("checks", [])
    workspace = [c for c in checks if c.get("id") == "workspace_perms"]
    assert workspace, "workspace_perms check missing from posture scan"
    assert workspace[0]["status"] == "pass"
    assert "chmod" not in (workspace[0].get("remediation") or "")


# ── Class guard: no raw os.kill(pid, 0) probes may come back ──────────────

_REPO = Path(__file__).resolve().parents[1]
_RAW_PROBE = re.compile(r"\b_?os\.kill\(\s*[^,()]+,\s*0\s*\)")


def test_no_raw_pid0_probes_outside_process_control():
    """Auto-discovering guard: the portable probe lives in process_control;
    any raw os.kill(pid, 0) elsewhere silently breaks Windows again."""
    offenders = []
    targets = [_REPO / "dashboard.py"]
    targets += sorted((_REPO / "clawmetry").rglob("*.py"))
    targets += sorted((_REPO / "routes").rglob("*.py"))
    for path in targets:
        if path.name == "process_control.py":
            continue
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            code = line.split("#", 1)[0]  # the fixes reference the idiom in comments
            if _RAW_PROBE.search(code):
                offenders.append(f"{path.relative_to(_REPO)}:{lineno}")
    assert offenders == [], (
        "raw os.kill(pid, 0) probes found — use "
        "clawmetry.process_control.is_alive() instead (os.kill(pid, 0) "
        f"never raises on Windows): {offenders}"
    )
