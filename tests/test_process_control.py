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


# ──────────────────────────────────────────────────────────────────────────
# TZ-safe start-time guard (macOS-without-psutil bug, found in mobile E2E)
# ──────────────────────────────────────────────────────────────────────────
@pytest.fixture
def berlin_tz():
    """Run the test in a non-UTC timezone (Europe/Berlin) so the UTC-vs-local
    ctime rendering skew actually manifests, then restore the original TZ."""
    if not hasattr(time, "tzset"):
        pytest.skip("time.tzset required (POSIX only)")
    old = os.environ.get("TZ")
    os.environ["TZ"] = "Europe/Berlin"
    time.tzset()
    yield
    if old is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = old
    time.tzset()


def test_verify_pid_tz_normalized_ctime(berlin_tz, monkeypatch):
    """THE regression: claude_code records procStart as a UTC ctime string,
    while macOS `ps -o lstart=` (the no-psutil fallback) prints LOCAL time.
    On any non-UTC Mac the raw tokens can never be equal, so the pid-reuse
    guard refused every pause/kill/resume. Same instant must now verify."""
    epoch = 1751430415  # fixed instant (2026-07-02, DST active in Berlin)
    recorded = time.asctime(time.gmtime(epoch))            # what claude_code writes
    live = "lstart:" + time.asctime(time.localtime(epoch))  # what ps prints
    assert recorded not in live  # sanity: the strings really do differ in Berlin
    monkeypatch.setattr(pc, "_proc_start_token", lambda _pid: live)
    ok, reason = pc.verify_pid(os.getpid(), recorded_start=recorded)
    assert ok is True, reason
    assert reason == "verified_tz_normalized"


def test_verify_pid_tz_guard_still_refuses_different_start(berlin_tz, monkeypatch):
    """A genuinely different process start (offset that is NOT a whole timezone
    offset) must still REFUSE — the TZ bridge must not weaken the reuse guard."""
    epoch = 1751430415
    recorded = time.asctime(time.gmtime(epoch))
    live = "lstart:" + time.asctime(time.localtime(epoch - 12345))
    monkeypatch.setattr(pc, "_proc_start_token", lambda _pid: live)
    ok, reason = pc.verify_pid(os.getpid(), recorded_start=recorded)
    assert ok is False
    assert reason.startswith("start_mismatch"), reason


def test_start_tokens_unparseable_fail_closed():
    # Garbage on either side yields no epoch candidates -> never equivalent.
    assert pc._start_tokens_equivalent("raw:garbage", "lstart:also garbage") is False
    assert pc._start_tokens_equivalent("", "") is False
    assert pc._start_tokens_equivalent("epoch:notanumber", "epoch:123") is False
    # Plain epoch tokens still compare within tolerance.
    assert pc._start_tokens_equivalent("epoch:1000", "epoch:1002") is True
    assert pc._start_tokens_equivalent("epoch:1000", "epoch:1010") is False


def test_claude_session_map_prefers_started_at_epoch(tmp_path, monkeypatch):
    """When claude_code provides startedAt (epoch ms, timezone-unambiguous) the
    map must prefer it over the ambiguous procStart ctime string."""
    import json

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    (sessions_dir / "12345.json").write_text(json.dumps({
        "pid": 12345,
        "sessionId": "sid-startedat",
        "startedAt": 1751430415123,  # ms
        "procStart": "Thu Jul  2 04:26:55 2026",
        "status": "running",
    }))
    (sessions_dir / "12346.json").write_text(json.dumps({
        "pid": 12346,
        "sessionId": "sid-ctime-only",
        "procStart": "Thu Jul  2 04:26:55 2026",
        "status": "running",
    }))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    m = pc.claude_code_session_map()
    assert m["sid-startedat"]["procStart"] == pytest.approx(1751430415.123)
    # Without startedAt the ctime string still flows through (TZ bridge handles it).
    assert m["sid-ctime-only"]["procStart"] == "Thu Jul  2 04:26:55 2026"


# ──────────────────────────────────────────────────────────────────────────
# pause must not freeze a process group shared with the caller
# ──────────────────────────────────────────────────────────────────────────
def _read_until(proc, marker: str, timeout: float) -> str:
    """Accumulate proc.stdout (non-blocking) until ``marker`` appears or the
    deadline passes. Bounded; never hangs the test runner."""
    import select

    fd = proc.stdout.fileno()
    buf = ""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if marker in buf:
            return buf
        r, _, _ = select.select([fd], [], [], 0.1)
        if r:
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            buf += chunk.decode("utf-8", "replace")
    return buf


@posix_only
def test_pause_does_not_freeze_group_sharing_orchestrator():
    """Second mobile-E2E finding: pause() SIGSTOP'd the target's whole process
    GROUP, freezing a parent orchestrator that shared the group. An orchestrator
    that spawns the agent WITHOUT a new session (same pgid) must survive its own
    pause() call; the child must still stop."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = (
        "import os, subprocess, sys, time\n"
        f"sys.path.insert(0, {repo_root!r})\n"
        "import clawmetry.process_control as pc\n"
        "# child shares OUR pgid (no start_new_session) — the E2E topology\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
        "time.sleep(0.3)\n"
        "print('CHILD', child.pid, flush=True)\n"
        "res = pc.pause(child.pid)\n"
        "print('SURVIVED', res.get('ok'), flush=True)\n"
        "time.sleep(120)\n"
    )
    orch = subprocess.Popen(
        [sys.executable, "-c", script],
        start_new_session=True,  # isolate from pytest's own group
        stdout=subprocess.PIPE,
    )
    try:
        out = _read_until(orch, "SURVIVED", timeout=15.0)
        assert "CHILD " in out, f"orchestrator never spawned a child: {out!r}"
        child_pid = int(out.split("CHILD", 1)[1].split()[0])
        # Un-fixed code SIGSTOPs the shared group, freezing the orchestrator
        # mid-call, so SURVIVED never prints and its state goes to T.
        assert "SURVIVED" in out, (
            f"orchestrator froze during its own pause() call "
            f"(state={_proc_state(orch.pid)!r}, out={out!r})"
        )
        assert _proc_state(orch.pid) != "T", "orchestrator was SIGSTOP'd"
        # The actual target must still be frozen.
        assert _wait_state(child_pid, "T", timeout=3.0) == "T"
    finally:
        # Wake + tear down the whole orchestrator group (covers the child too).
        for sig_ in (signal.SIGCONT, signal.SIGKILL):
            try:
                os.killpg(os.getpgid(orch.pid), sig_)
            except Exception:
                pass
        try:
            orch.wait(timeout=5)
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────────
# locale-independent ps start-time reading (non-English macOS, no psutil)
# ──────────────────────────────────────────────────────────────────────────
_EN_LSTART = "Thu Jul  2 04:26:55 2026"       # C-locale `ps -o lstart=`
_DE_LSTART = "Do  2. Jul 04:26:55 2026"       # German-locale `ps -o lstart=`


def _is_c_locale_env(env) -> bool:
    """True when the subprocess env forces the C locale the way _run must."""
    if not env or env.get("LC_ALL") != "C":
        return False
    if "LANG" in env or "LANGUAGE" in env:
        return False
    return not any(k.startswith("LC_") and k != "LC_ALL" for k in env)


def _fake_localized_ps(cmd, **kwargs):
    """Simulate `ps -o lstart=` on a German-locale host: localized month/day
    names UNLESS the caller forces the C locale via the subprocess env."""
    assert "lstart=" in cmd, f"unexpected subprocess call in test: {cmd}"
    out = _EN_LSTART if _is_c_locale_env(kwargs.get("env")) else _DE_LSTART
    return subprocess.CompletedProcess(cmd, 0, stdout=out + "\n", stderr="")


def test_guard_verifies_on_non_english_locale_host(monkeypatch):
    """THE regression (follow-up to the TZ fix): on a non-English-locale Mac
    without psutil, `ps -o lstart=` prints localized month/day names, the
    ctime parse (%a %b) failed, and the guard failed CLOSED, so kill/pause/
    resume refused for those users. _run now forces LC_ALL=C on the ps
    subprocess, so lstart is always English and the guard verifies.

    Revert-proof: without the _run env fix the fake ps below returns the
    German rendering, _ctime_epoch_candidates yields no candidates, and
    verify_pid refuses (RED); with the fix it sees English and verifies."""
    monkeypatch.setattr(pc, "_psutil", None)
    monkeypatch.setattr(pc, "_IS_MACOS", True)
    monkeypatch.setattr(pc, "_IS_LINUX", False)
    # The host is a German-locale machine.
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    monkeypatch.setenv("LC_TIME", "de_DE.UTF-8")
    monkeypatch.setattr(pc.subprocess, "run", _fake_localized_ps)
    # claude_code records procStart as an English ctime regardless of locale.
    ok, reason = pc.verify_pid(os.getpid(), recorded_start=_EN_LSTART)
    assert ok is True, reason
    assert reason in ("verified", "verified_tz_normalized")


def test_run_forces_c_locale_on_subprocess(monkeypatch):
    """_run must pass an env that forces the C locale and strips every other
    locale variable, while preserving the rest of the environment (PATH)."""
    captured = {}

    def spy(cmd, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(cmd, 0, stdout="x\n", stderr="")

    monkeypatch.setenv("LANG", "fr_FR.UTF-8")
    monkeypatch.setenv("LC_TIME", "fr_FR.UTF-8")
    monkeypatch.setenv("LANGUAGE", "fr")
    monkeypatch.setattr(pc.subprocess, "run", spy)
    assert pc._run(["ps", "-o", "lstart=", "-p", "1"]) == "x\n"
    env = captured.get("env")
    assert _is_c_locale_env(env), f"subprocess env does not force C locale: {env}"
    assert "PATH" in env  # non-locale environment is preserved


def test_guard_still_fails_closed_on_unparseable_ps_output(monkeypatch):
    """Fail-closed semantics survive the locale fix: if ps emits something
    genuinely unparseable even under the C locale, the guard must refuse."""
    monkeypatch.setattr(pc, "_psutil", None)
    monkeypatch.setattr(pc, "_IS_MACOS", True)
    monkeypatch.setattr(pc, "_IS_LINUX", False)

    def broken_ps(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="not a date\n", stderr="")

    monkeypatch.setattr(pc.subprocess, "run", broken_ps)
    ok, reason = pc.verify_pid(os.getpid(), recorded_start=_EN_LSTART)
    assert ok is False
    assert reason.startswith("start_mismatch"), reason


# ──────────────────────────────────────────────────────────────────────────
# copilot: log-filename pid map (2026-08-19 matrix-gap sprint)
# ──────────────────────────────────────────────────────────────────────────
def _write_copilot_log(home, sid, pid, epoch_ms=1787175091173):
    d = home / "logs"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"process-{epoch_ms}-{pid}.log"
    p.write_text(
        "2026-08-19T00:00:00.000Z [INFO] Session indexing debug\n"
        f"2026-08-19T00:00:00.100Z [INFO] Workspace initialized: {sid} (checkpoints: 0)\n"
        "2026-08-19T00:00:00.200Z [INFO] Starting Copilot CLI: 1.0.80\n"
    )
    return p


def test_resolve_copilot_maps_sid_to_pid_from_log_filename(spawned, tmp_path,
                                                           monkeypatch):
    monkeypatch.setenv("COPILOT_HOME", str(tmp_path))
    sid = "1035fc8f-aaaa-bbbb-cccc-333333333333"
    p = spawned()  # must be a LIVE pid: stale logs are skipped by design
    _write_copilot_log(tmp_path, sid, p.pid)
    info = pc.resolve_copilot(sid)
    assert info["ok"] is True
    assert info["pid"] == p.pid
    assert info["runtime"] == "copilot"
    # epoch_ms from the FILENAME becomes the recorded start (seconds).
    assert abs(info["recorded_start"] - 1787175091.173) < 0.01


def test_resolve_copilot_skips_stale_log_for_dead_pid(tmp_path, monkeypatch):
    """The per-process log is not removed on exit, so a stale entry is
    normal. It must be skipped, not returned — otherwise it masks a live
    session and suppresses the argv+cwd fallback."""
    monkeypatch.setenv("COPILOT_HOME", str(tmp_path))
    sid = "dead-session"
    _write_copilot_log(tmp_path, sid, 999999)
    info = pc.resolve_copilot(sid)
    assert info["ok"] is False
    assert info["reason"] == "session_not_in_copilot_logs"


def test_resolve_copilot_requires_exact_session_id(spawned, tmp_path,
                                                   monkeypatch):
    """A truncated id must NOT resolve to the full session's pid: the
    recorded start comes from the same filename, so the pid-reuse guard
    would pass and we would signal the wrong session."""
    monkeypatch.setenv("COPILOT_HOME", str(tmp_path))
    p = spawned()
    _write_copilot_log(tmp_path, "1035fc8f-full-uuid-here", p.pid)
    assert pc.resolve_copilot("1035fc8f")["ok"] is False
    assert pc.resolve_copilot("1035fc8f-full-uuid-here")["ok"] is True


def test_resolve_copilot_unknown_sid(tmp_path, monkeypatch):
    monkeypatch.setenv("COPILOT_HOME", str(tmp_path))
    _write_copilot_log(tmp_path, "some-other-session", 1234)
    info = pc.resolve_copilot("not-there")
    assert info["ok"] is False
    assert info["reason"] == "session_not_in_copilot_logs"


def test_resolve_copilot_no_logs_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("COPILOT_HOME", str(tmp_path / "absent"))
    info = pc.resolve_copilot("x")
    assert info["ok"] is False
    assert info["reason"] == "no_copilot_logs_dir"


@posix_only
def test_copilot_kill_session_end_to_end(spawned, tmp_path, monkeypatch):
    """A copilot session resolved from the log map is actually killable, and
    the pid-reuse guard still refuses a mismatched start."""
    monkeypatch.setenv("COPILOT_HOME", str(tmp_path))
    p = spawned()
    sid = "e2e-copilot-session"
    # recorded epoch_ms far in the past -> start mismatch -> guard refuses
    _write_copilot_log(tmp_path, sid, p.pid, epoch_ms=1000000000000)
    res = pc.kill_session("copilot", sid)
    assert res["ok"] is False
    assert "pid_guard_refused" in (res.get("detail") or "")
    # rewrite with the true start time -> kill succeeds
    for f in (tmp_path / "logs").iterdir():
        f.unlink()
    start = pc._proc_start_epoch(p.pid)
    if start is None:
        start = time.time()
    _write_copilot_log(tmp_path, sid, p.pid, epoch_ms=int(start * 1000))
    res = pc.kill_session("copilot", sid)
    assert res["ok"] is True, res
    # SIGTERM on a plain python sleep exits promptly. Reap to observe the
    # exit (an unreaped child is a zombie and still passes is_alive).
    assert _reaped(p), res
    assert p.returncode is not None


# ──────────────────────────────────────────────────────────────────────────
# qwen_code: pid sidecar
# ──────────────────────────────────────────────────────────────────────────
def _write_qwen_sidecar(root, sid, pid, work_dir):
    d = root / "projects" / "abc123" / "chats"
    d.mkdir(parents=True, exist_ok=True)
    import json as _json
    (d / f"{sid}.runtime.json").write_text(_json.dumps({
        "schema_version": 1, "pid": pid, "session_id": sid,
        "work_dir": str(work_dir), "started_at": "2026-08-19T00:00:00Z",
    }))


def test_resolve_qwen_code_sidecar_dead_pid_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("QWEN_CODE_HOME", str(tmp_path))
    _write_qwen_sidecar(tmp_path, "sid-1", 99999999, tmp_path)
    info = pc.resolve_qwen_code("sid-1")
    assert info["ok"] is False
    assert info["reason"] == "sidecar_pid_not_alive"


def test_resolve_qwen_code_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("QWEN_CODE_HOME", str(tmp_path))
    info = pc.resolve_qwen_code("nope")
    assert info["ok"] is False
    assert info["reason"] in ("no_qwen_projects_dir", "session_not_in_qwen_sidecars")


@posix_only
def test_resolve_qwen_code_live_pid_identity_check(spawned, tmp_path, monkeypatch):
    """A live sidecar pid that is NOT a qwen process is refused (identity
    guard replaces the unreliable sidecar start time)."""
    monkeypatch.setenv("QWEN_CODE_HOME", str(tmp_path))
    p = spawned()  # a python sleep, argv has no 'qwen'
    _write_qwen_sidecar(tmp_path, "sid-2", p.pid, os.getcwd())
    info = pc.resolve_qwen_code("sid-2")
    assert info["ok"] is False
    assert info["reason"] == "sidecar_pid_not_qwen"


# ──────────────────────────────────────────────────────────────────────────
# exact-basename argv hints ("pi" must not match pip/python)
# ──────────────────────────────────────────────────────────────────────────
def test_hint_matches_exact_for_pi():
    assert pc._hint_matches(("pi",), "pi", "pi") is True
    assert pc._hint_matches(("pi",), "/usr/local/bin/pi", "/usr/local/bin/pi") is True
    assert pc._hint_matches(("pi",), "pip", "pip install x") is False
    assert pc._hint_matches(("pi",), "python3", "python3 -m pip") is False


def test_hint_matches_substring_for_others():
    # copilot is EXACT-basename: the platform binary (the real agent) is
    # `.../@github/copilot-darwin-arm64/copilot`, while the npm loader runs
    # as `node`. Matching the loader is unnecessary (we want the child) and
    # matching on the cmdline would also hit the editor's language server.
    assert pc._hint_matches(("copilot",), "copilot",
                            "/opt/homebrew/bin/copilot -p hi") is True
    assert pc._hint_matches(("copilot",), "node",
                            "node /opt/homebrew/bin/copilot -p hi") is False
    assert pc._hint_matches(("qwen",), "node",
                            "node /x/qwen-code/bundle/gemini.js") is True


def test_hint_matches_excludes_language_servers():
    """An editor language server shares the runtime's name and runs in the
    workspace root — signaling it would kill the user's editor tooling."""
    assert pc._hint_matches(
        ("copilot",), "node",
        "node /u/.vscode/extensions/github.copilot/dist/"
        "copilot-language-server --stdio") is False
    assert pc._hint_matches(("cursor-agent",), "node",
                            "node /x/cursor/worker-server") is False
    assert pc._hint_matches(("dsh",), "bash", "bash /tmp/dshboard.sh") is False
    assert pc._hint_matches(("dsh",), "dsh", "dsh --resume x") is True


def test_new_runtimes_are_supported():
    for rt in ("copilot", "qwen_code", "pi", "grok", "deepseek_harness", "kimi"):
        assert rt in pc.SUPPORTED_RUNTIMES, rt
        assert rt in pc._RUNTIME_ARGV_HINTS, rt


def test_cursor_cli_resolves_ide_refuses():
    # No cursor-agent process running in the test env and no cwd ->
    # the honest single-IDE-process refusal.
    info = pc.resolve_session("cursor", session_id="x", cwd="")
    assert info["ok"] is False
    assert info.get("unsupported") is True


# ──────────────────────────────────────────────────────────────────────────
# Safety guards added after adversarial review (2026-08-21)
# ──────────────────────────────────────────────────────────────────────────
def test_cursor_ide_session_never_resolves_to_a_pid(tmp_path, monkeypatch):
    """An IDE conversation must never resolve to a CLI agent's pid just
    because they share a directory — that would stop an unrelated terminal
    session and report success."""
    monkeypatch.setenv("CLAWMETRY_CURSOR_CHATS_ROOT", str(tmp_path / "chats"))
    info = pc.resolve_session("cursor", session_id="ide-conversation-1",
                              cwd=os.getcwd())
    assert info["ok"] is False
    assert info.get("unsupported") is True
    assert info["reason"] == "cursor_single_ide_process_no_per_session_signal"


def test_cursor_cli_session_is_recognised(tmp_path, monkeypatch):
    """A session present in Cursor's CLI chat store IS a CLI session, so it
    gets a real resolution attempt (here: no process, honest not-found)."""
    chats = tmp_path / "chats" / "d10a1c600d91eeb605acc62dd97e0ff8" / "sid-1"
    chats.mkdir(parents=True)
    (chats / "meta.json").write_text('{"cwd": "/proj"}')
    monkeypatch.setenv("CLAWMETRY_CURSOR_CHATS_ROOT", str(tmp_path / "chats"))
    info = pc.resolve_session("cursor", session_id="sid-1", cwd="/proj")
    assert info["ok"] is False
    assert info.get("unsupported") is not True
    assert info["reason"] in ("cursor_cli_session_process_not_found",
                              "no_matching_process", "ambiguous_candidates")


def test_cursor_path_traversal_session_id_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_CURSOR_CHATS_ROOT", str(tmp_path / "chats"))
    assert pc._cursor_cli_session_exists("../../etc") is False
    assert pc._cursor_cli_session_exists("") is False


@posix_only
def test_ambiguous_cwd_candidates_are_refused(spawned):
    """Two sibling sessions of the same runtime in one directory: refuse
    rather than silently stopping the lowest pid (somebody else's session)."""
    a, b = spawned(), spawned()
    assert pc._pick_session_pid([a.pid, b.pid]) is None
    assert pc._pick_session_pid([a.pid]) == a.pid


@posix_only
def test_parent_with_children_is_not_ambiguous(spawned):
    """A top-level CLI plus its own children is NOT ambiguous — the ancestor
    is the session process."""
    code = ("import subprocess, sys, time\n"
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
            "time.sleep(60)\n")
    parent = spawned([sys.executable, "-c", code])
    time.sleep(0.6)
    kids = pc.descendant_pids(parent.pid)
    assert kids, "expected a child process"
    assert pc._pick_session_pid([parent.pid] + kids) == parent.pid


def test_qwen_sidecar_unverifiable_pid_fails_closed(tmp_path, monkeypatch):
    """The sidecar is not deleted on exit. A live pid whose identity cannot
    be read must be REFUSED, not signaled on liveness alone."""
    monkeypatch.setenv("QWEN_CODE_HOME", str(tmp_path))
    _write_qwen_sidecar(tmp_path, "sid-x", os.getpid(), tmp_path)
    monkeypatch.setattr(pc, "_proc_cmdline", lambda pid: [])
    info = pc.resolve_qwen_code("sid-x")
    assert info["ok"] is False
    assert info["reason"] == "sidecar_pid_unverifiable"
