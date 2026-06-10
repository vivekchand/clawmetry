"""Unit tests for clawmetry/process_control.py + the sync.py kill/pause/resume
dispatch wiring.

These tests spawn REAL throwaway child processes (``sleep`` subprocesses) and
assert the actual OS state transitions:

  * pause  -> the process enters the STOPPED state (T) and resume -> running (R)
  * graceful_kill terminates it
  * the pid-reuse GUARD refuses to signal when the recorded procStart mismatches
  * a claude_code session-json map resolves a sessionId to a controlled pid and
    signaling it works

All spawned processes are cleaned up in teardown. Signal tests are skipped on
platforms that don't support POSIX job-control signals (Windows).
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import clawmetry.process_control as pc  # noqa: E402

_POSIX = pc._POSIX
posix_only = pytest.mark.skipif(not _POSIX, reason="POSIX signals required")


# ──────────────────────────────────────────────────────────────────────────
# spawn helper + cleanup
# ──────────────────────────────────────────────────────────────────────────
@pytest.fixture
def spawned():
    procs = []

    def _spawn(cmd=None):
        # A child that ignores SIGINT would defeat stop_turn tests; a plain
        # sleep is fine for pause/resume/kill.
        cmd = cmd or [sys.executable, "-c", "import time; time.sleep(120)"]
        # start_new_session=True puts the child in its OWN session + process
        # group. Critical for the pause tests: pause() signals the process
        # GROUP, and if the child shared pytest's pgid we'd SIGSTOP the test
        # runner itself. Real agent CLIs (claude/codex/goose) are launched as
        # their own session leaders too, so this also mirrors production.
        p = subprocess.Popen(cmd, start_new_session=True)
        procs.append(p)
        # give it a moment to actually be running
        time.sleep(0.2)
        return p

    yield _spawn

    for p in procs:
        # A SIGSTOP'd process must be continued before SIGKILL can reap it
        # cleanly; SIGCONT first so wait() never blocks on a stopped child.
        try:
            os.kill(p.pid, signal.SIGCONT)
        except Exception:
            pass
        try:
            p.kill()
        except Exception:
            pass
        try:
            p.wait(timeout=5)
        except Exception:
            pass


def _proc_state(pid: int) -> str:
    """Single-char process state from ps (R/S/T/Z...). '' if gone."""
    try:
        out = subprocess.run(
            ["ps", "-o", "state=", "-p", str(pid)],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        # macOS prints e.g. 'T+', 'R+', 'S' — first char is the state.
        return out[:1] if out else ""
    except Exception:
        return ""


def _reaped(p, timeout: float = 4.0) -> bool:
    """True once the Popen child has actually exited (and is reaped).

    NOTE: ``os.kill(pid, 0)`` succeeds on a ZOMBIE (exited-but-unreaped) child,
    so ``pc.is_alive`` reports True until the parent (pytest) calls wait(). In
    production the daemon kills a process whose REAL parent reaps it, so it
    vanishes — there is no zombie. In-test, pytest is the parent, so we must
    reap with wait() to observe the exit. This asymmetry is a test artifact,
    not a module bug.
    """
    try:
        p.wait(timeout=timeout)
        return True
    except Exception:
        return False


def _wait_state(pid: int, want: str, timeout: float = 3.0) -> str:
    deadline = time.monotonic() + timeout
    last = ""
    while time.monotonic() < deadline:
        last = _proc_state(pid)
        if last == want:
            return last
        time.sleep(0.05)
    return last


# ──────────────────────────────────────────────────────────────────────────
# pid-reuse guard
# ──────────────────────────────────────────────────────────────────────────
def test_is_alive_and_dead(spawned):
    p = spawned()
    assert pc.is_alive(p.pid) is True
    p.kill()
    p.wait(timeout=5)
    assert pc.is_alive(p.pid) is False
    assert pc.is_alive(-1) is False
    assert pc.is_alive(0) is False


def test_verify_pid_alive_no_start_check(spawned):
    p = spawned()
    ok, reason = pc.verify_pid(p.pid, recorded_start=None)
    assert ok is True
    assert reason == "alive_no_start_check"


def test_verify_pid_matches_real_start(spawned):
    p = spawned()
    tok = pc._proc_start_token(p.pid)
    if tok is None:
        pytest.skip("could not read process start time on this platform")
    # Feed the live token back as the recorded value -> must verify.
    ok, reason = pc.verify_pid(p.pid, recorded_start=tok)
    assert ok is True, reason
    assert reason == "verified"


def test_pid_reuse_guard_refuses_on_start_mismatch(spawned):
    """The core safety guard: a fabricated/stale procStart must REFUSE."""
    p = spawned()
    assert pc.is_alive(p.pid)
    # A clearly-wrong recorded start (epoch far in the past).
    ok, reason = pc.verify_pid(p.pid, recorded_start="epoch:1")
    assert ok is False
    assert reason.startswith("start_mismatch"), reason


def test_pid_reuse_guard_refuses_dead_pid(spawned):
    p = spawned()
    p.kill()
    p.wait(timeout=5)
    ok, reason = pc.verify_pid(p.pid, recorded_start="epoch:1")
    assert ok is False
    assert reason == "pid_not_alive"


# ──────────────────────────────────────────────────────────────────────────
# signal helpers: pause / resume / graceful_kill
# ──────────────────────────────────────────────────────────────────────────
@posix_only
def test_pause_then_resume_real_state_transition(spawned):
    p = spawned()
    assert _proc_state(p.pid) in ("R", "S")  # running or sleeping

    res = pc.pause(p.pid, runtime="claude_code")
    assert res["ok"] is True, res
    assert res["action"] == "pause"
    state = _wait_state(p.pid, "T", timeout=3.0)
    assert state == "T", f"expected stopped (T), got {state!r}"

    res2 = pc.resume(p.pid, runtime="claude_code")
    assert res2["ok"] is True, res2
    # back to running/sleeping (not T)
    deadline = time.monotonic() + 3.0
    state2 = "T"
    while time.monotonic() < deadline:
        state2 = _proc_state(p.pid)
        if state2 and state2 != "T":
            break
        time.sleep(0.05)
    assert state2 in ("R", "S"), f"expected resumed, got {state2!r}"


@posix_only
def test_graceful_kill_terminates(spawned):
    p = spawned()
    assert pc.is_alive(p.pid)
    res = pc.graceful_kill(p.pid, runtime="codex", grace_secs=2.0)
    assert res["ok"] is True, res
    # SIGTERM on a plain python sleep exits promptly. Reap to observe the exit.
    assert _reaped(p), res
    assert p.returncode is not None


@posix_only
def test_graceful_kill_escalates_to_sigkill(spawned):
    # A child that ignores SIGTERM must still be killed via the SIGKILL escalation.
    code = (
        "import signal, time\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "time.sleep(120)\n"
    )
    p = spawned([sys.executable, "-c", code])
    assert pc.is_alive(p.pid)
    res = pc.graceful_kill(p.pid, runtime="goose", grace_secs=1.0)
    # SIGTERM is ignored, so only the SIGKILL escalation can end it. Reap.
    assert _reaped(p), res
    assert p.returncode is not None


@posix_only
def test_descendant_set_includes_child():
    # parent spawns a child; descendant_pids must find the child.
    code = (
        "import subprocess, sys, time\n"
        "c = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
        "time.sleep(120)\n"
    )
    parent = subprocess.Popen([sys.executable, "-c", code], start_new_session=True)
    try:
        time.sleep(0.6)
        desc = pc.descendant_pids(parent.pid)
        assert len(desc) >= 1, f"expected at least one descendant, got {desc}"
        pset = pc.process_set(parent.pid)
        assert parent.pid in pset
        assert pset[-1] == parent.pid  # parent last (children first)
    finally:
        parent.kill()
        try:
            parent.wait(timeout=5)
        except Exception:
            pass
        # reap any orphaned grandchild
        for d in pc.descendant_pids(parent.pid):
            try:
                os.kill(d, signal.SIGKILL)
            except Exception:
                pass


# ──────────────────────────────────────────────────────────────────────────
# claude_code session-json discovery
# ──────────────────────────────────────────────────────────────────────────
@posix_only
def test_claude_code_session_map_and_signal(spawned, tmp_path, monkeypatch):
    import json

    p = spawned()
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    sid = "test-session-abc123"
    start_tok = pc._proc_start_token(p.pid)
    if start_tok is None:
        pytest.skip("no start token on this platform")
    # claude_code writes <pid>.json with {pid, sessionId, cwd, procStart, status}
    (sessions_dir / f"{p.pid}.json").write_text(json.dumps({
        "pid": p.pid,
        "sessionId": sid,
        "cwd": os.getcwd(),
        "procStart": start_tok,   # use the live token so the guard verifies
        "status": "running",
        "version": "1.0.0",
    }))
    # CLAUDE_CONFIG_DIR override -> <dir>/sessions/
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))

    m = pc.claude_code_session_map()
    assert sid in m
    assert m[sid]["pid"] == p.pid

    info = pc.resolve_claude_code(sid)
    assert info["ok"] is True
    assert info["pid"] == p.pid

    # End-to-end: pause via the high-level guarded path, assert it stops.
    res = pc.pause_session("claude_code", sid)
    assert res["ok"] is True, res
    assert _wait_state(p.pid, "T", timeout=3.0) == "T"
    pc.resume_session("claude_code", sid)


def test_claude_code_unknown_session_returns_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    info = pc.resolve_claude_code("does-not-exist")
    assert info["ok"] is False
    assert info["reason"] == "session_not_in_claude_map"


def test_cursor_is_unsupported():
    info = pc.resolve_session("cursor", "sid")
    assert info["ok"] is False
    assert info["unsupported"] is True
    res = pc.kill_session("cursor", "sid")
    assert res["ok"] is False
    assert res.get("unsupported") is True


def test_kill_session_refuses_stale_claude_record(spawned, tmp_path, monkeypatch):
    """The reuse guard, exercised through the high-level kill path: a stale
    procStart must REFUSE to signal (the process must survive)."""
    import json

    p = spawned()
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    sid = "stale-session"
    (sessions_dir / f"{p.pid}.json").write_text(json.dumps({
        "pid": p.pid,
        "sessionId": sid,
        "cwd": os.getcwd(),
        "procStart": "epoch:1",   # deliberately wrong
        "status": "running",
    }))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))

    res = pc.kill_session("claude_code", sid)
    assert res["ok"] is False
    assert "pid_guard_refused" in res["detail"], res
    # process must still be alive — we refused to signal a possibly-reused pid.
    assert pc.is_alive(p.pid) is True


@posix_only
def test_stop_turn_sends_sigint(spawned):
    # A python child that exits on SIGINT (default) — stop_turn should end it.
    p = spawned([sys.executable, "-c", "import time; time.sleep(120)"])
    res = pc.stop_turn(p.pid, runtime="claude_code")
    assert res["ok"] is True, res
    # Default SIGINT handler raises KeyboardInterrupt -> the child exits. Reap.
    assert _reaped(p), res
    assert p.returncode is not None
