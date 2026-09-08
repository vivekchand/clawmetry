"""Windows control path — dispatch, ordering and honesty.

The Win32 calls themselves can only be exercised on Windows, but everything
around them (which branch runs, in what order, what the result says) is
platform-independent and is what actually regressed before: the actuators
returned ``unsupported_platform`` on every Windows node, so every Guard button
was inert there.

These tests fake the platform flags rather than skipping off-Windows, so the
Windows path is covered by the macOS and Linux CI legs too — a suite that only
runs on the Windows leg is how the no-op survived in the first place.
"""
import clawmetry.process_control as pc
import pytest


@pytest.fixture
def win(monkeypatch):
    """Pretend we are on Windows, with every Win32 primitive stubbed."""
    monkeypatch.setattr(pc, "_IS_WINDOWS", True)
    monkeypatch.setattr(pc, "_IS_MACOS", False)
    monkeypatch.setattr(pc, "_IS_LINUX", False)
    monkeypatch.setattr(pc, "_POSIX", False)
    monkeypatch.setattr(pc, "_CONTROLLABLE_PLATFORM", True)

    calls = []
    monkeypatch.setattr(pc, "is_alive", lambda p: True)
    # A three-deep tree: process_set is children-first, parent last.
    monkeypatch.setattr(pc, "process_set", lambda p: [300, 200, int(p)])
    monkeypatch.setattr(pc, "_win_suspend",
                        lambda p: calls.append(("suspend", p)) or True)
    monkeypatch.setattr(pc, "_win_resume",
                        lambda p: calls.append(("resume", p)) or True)
    monkeypatch.setattr(pc, "_win_terminate",
                        lambda p: calls.append(("terminate", p)) or True)
    monkeypatch.setattr(pc, "_win_taskkill",
                        lambda p, force=False, timeout=10.0:
                        calls.append(("taskkill", p, force)) or True)
    monkeypatch.setattr(pc, "_win_ctrl_c",
                        lambda p, timeout=10.0:
                        (calls.append(("ctrl_c", p)), (True, "ctrl_c_sent_to_console"))[1])
    return calls


# ── the gap itself: these four used to be unconditional no-ops ────────────
@pytest.mark.parametrize("fn,action", [
    (lambda: pc.pause(100), "pause"),
    (lambda: pc.resume(100), "resume"),
    (lambda: pc.stop_turn(100), "stop_turn"),
    (lambda: pc.graceful_kill(100, grace_secs=0), "graceful_kill"),
])
def test_actuators_are_not_unsupported_on_windows(win, fn, action):
    res = fn()
    assert res["detail"] != "unsupported_platform"
    assert res["ok"] is True, res


def test_pause_suspends_children_before_parent(win):
    res = pc.pause(100, "claude_code")
    assert res["ok"] and res["detail"] == "paused"
    assert win == [("suspend", 300), ("suspend", 200), ("suspend", 100)]
    assert res["mechanism"] == "win32_nt_suspend_process"


def test_resume_wakes_parent_before_children(win):
    pc.resume(100, "claude_code")
    assert win == [("resume", 100), ("resume", 200), ("resume", 300)]


def test_partial_pause_is_reported_not_hidden(win, monkeypatch):
    """A child we could not freeze keeps spending. Say so."""
    monkeypatch.setattr(pc, "_win_suspend", lambda p: p != 300)
    res = pc.pause(100)
    assert res["ok"] is True
    assert res["failed"] == [300]
    assert "could not be suspended" in res["detail"]


def test_stop_turn_declares_its_console_blast_radius(win):
    res = pc.stop_turn(100, "codex")
    assert res["ok"] and res["scope"] == "console"
    assert res["mechanism"] == "win32_console_ctrl_c"


def test_stop_turn_reports_ctrl_c_failure_honestly(win, monkeypatch):
    monkeypatch.setattr(pc, "_win_ctrl_c",
                        lambda p, timeout=10.0: (False, "attach_console_failed"))
    res = pc.stop_turn(100)
    assert res["ok"] is False and res["detail"] == "attach_console_failed"


def test_graceful_kill_resumes_before_the_graceful_pass(win):
    """A suspended process cannot handle taskkill's close, so 'pause then
    kill' (an escalation ladder) would otherwise always burn the full grace
    window. Resume must come first."""
    pc.graceful_kill(100, grace_secs=0)
    kinds = [c[0] for c in win]
    assert kinds.index("resume") < kinds.index("taskkill")


def test_graceful_kill_escalates_to_terminate_when_still_alive(win):
    res = pc.graceful_kill(100, grace_secs=0)
    assert ("taskkill", 100, False) in win          # graceful pass first
    assert ("terminate", 300) in win                # then the tree, leaves first
    assert res["mechanism"] == "win32_terminate_process"


def test_graceful_kill_forces_taskkill_when_terminate_is_refused(win, monkeypatch):
    """TerminateProcess can be refused for an elevated target; /F is the last
    honest attempt rather than reporting a kill that did not happen."""
    monkeypatch.setattr(pc, "_win_terminate", lambda p: False)
    pc.graceful_kill(100, grace_secs=0)
    assert ("taskkill", 100, True) in win


def test_guarded_no_longer_refuses_the_platform(win, monkeypatch):
    monkeypatch.setattr(pc, "resolve_session",
                        lambda rt, sid="", cwd="": {"ok": True, "pid": 100,
                                                    "runtime": rt, "cwd": cwd,
                                                    "recorded_start": None})
    monkeypatch.setattr(pc, "verify_pid", lambda pid, rec=None: (True, "verified"))
    res = pc.pause_session("claude_code", "sess-1")
    assert res["detail"] != "unsupported_platform"
    assert res["ok"] is True


def test_dead_pid_still_refused_on_windows(win, monkeypatch):
    monkeypatch.setattr(pc, "is_alive", lambda p: False)
    assert pc.pause(100)["detail"] == "pid_not_alive"
    assert pc.stop_turn(100)["detail"] == "pid_not_alive"


# ── honesty for platforms we genuinely do not support ─────────────────────
def test_unknown_platform_still_refuses(monkeypatch):
    monkeypatch.setattr(pc, "_IS_WINDOWS", False)
    monkeypatch.setattr(pc, "_POSIX", False)
    monkeypatch.setattr(pc, "_CONTROLLABLE_PLATFORM", False)
    for res in (pc.pause(1), pc.resume(1), pc.stop_turn(1), pc.graceful_kill(1)):
        assert res["ok"] is False
        assert res["detail"] == "unsupported_platform"


def test_platform_support_states_the_mechanism(monkeypatch):
    monkeypatch.setattr(pc, "_POSIX", False)
    monkeypatch.setattr(pc, "_IS_WINDOWS", True)
    sup = pc.platform_support()
    assert sup["controllable"] is True
    assert sup["mechanism"] == "win32_native"
    assert set(sup["actions"]) == {"pause", "resume", "stop", "kill"}
    # The Ctrl+C caveat is a real behavioural difference; it must be surfaced.
    assert "Ctrl+C" in sup["note"]


def test_platform_support_is_honest_about_an_unsupported_os(monkeypatch):
    monkeypatch.setattr(pc, "_POSIX", False)
    monkeypatch.setattr(pc, "_IS_WINDOWS", False)
    sup = pc.platform_support()
    assert sup["controllable"] is False and sup["actions"] == []
    assert sup["reason"]


# ── the primitives are inert, never raising, off Windows ──────────────────
def test_win_primitives_are_inert_off_windows():
    assert pc._win_kernel32() is None
    assert pc._win_all_procs() == []
    assert pc._win_proc_start_epoch(1) is None
    assert pc._win_ctrl_c(1) == (False, "not_windows")
    assert pc._win_ntdll_call("NtSuspendProcess", 1) is False
