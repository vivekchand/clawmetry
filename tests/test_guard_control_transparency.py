"""Pause / Stop / Kill must not be a black box.

These buttons send real signals to a real process tree and Kill cannot be
undone, yet the whole interaction was one ``confirm("Kill this agent?")`` and
one ``alert()`` carrying a single token. The operator could not see which pid
was about to be signalled, how many processes were in the tree, whether the
pid-reuse guard had agreed, or — afterwards — which step had failed.

Two halves, pinned here:

* ``process_control.control_preflight`` computes what a press WOULD do and
  sends nothing.
* ``guard_actuator.guard_actuate`` records what it DID, step by step, and the
  route returns that record.
"""
import json

import clawmetry.guard_actuator as ga
import clawmetry.process_control as pc
import pytest
from flask import Flask

import routes.guard as guard


# ── preflight: a plan, and no signals ─────────────────────────────────────
@pytest.fixture
def live_session(monkeypatch):
    monkeypatch.setattr(pc, "platform_support",
                        lambda: {"controllable": True, "reason": "", "note": ""})
    monkeypatch.setattr(pc, "resolve_session",
                        lambda *a, **k: {"ok": True, "pid": 4242,
                                         "cwd": "/w/one",
                                         "recorded_start": "x"})
    monkeypatch.setattr(pc, "is_alive", lambda pid: True)
    monkeypatch.setattr(pc, "verify_pid",
                        lambda pid, start=None: (True, "verified_start_token"))
    monkeypatch.setattr(pc, "process_set", lambda pid: [4243, 4244, 4242])
    monkeypatch.setattr(pc, "_proc_cmdline",
                        lambda pid: ["claude", "--resume", "abc"])


def test_preflight_sends_no_signal(live_session, monkeypatch):
    """The whole point: this is a preview. If it signalled anything, the
    confirmation dialog would itself be the destructive act."""
    sent = []
    monkeypatch.setattr(pc, "_signal_pid",
                        lambda pid, sig: sent.append((pid, sig)) or True)
    pc.control_preflight("claude_code", "claude_code:x", "/w/one", "kill")
    assert sent == []


def test_preflight_names_the_pid_the_tree_and_the_guard(live_session):
    plan = pc.control_preflight("claude_code", "claude_code:x", "/w/one", "kill")
    assert plan["ok"] is True
    assert plan["pid"] == 4242
    # Kill ending three processes instead of one is exactly the surprise this
    # dialog exists to remove, so the tree is enumerated, not counted.
    assert plan["tree"] == [4243, 4244, 4242]
    assert [p["pid"] for p in plan["processes"]] == [4243, 4244, 4242]
    assert [p for p in plan["processes"] if p["main"]][0]["pid"] == 4242
    assert plan["guard"] == "verified_start_token"
    assert plan["command"] == "claude --resume abc"


@pytest.mark.skipif(pc._IS_WINDOWS, reason="POSIX signal plan")
def test_the_kill_plan_spells_out_the_escalation(live_session):
    plan = pc.control_preflight("claude_code", "claude_code:x", "/w/one", "kill")
    steps = " | ".join(plan["steps"])
    assert "SIGTERM pid 4242" in steps
    assert "SIGKILL all 3 processes" in steps
    assert plan["destructive"] is True
    assert plan["reversible"] is False


@pytest.mark.skipif(pc._IS_WINDOWS, reason="POSIX signal plan")
def test_stop_says_the_children_are_left_alone(live_session):
    """stop_turn deliberately signals the main pid only. An operator who
    expects Stop to tear down a runaway tool shell must learn that here, not by
    watching it keep running."""
    plan = pc.control_preflight("claude_code", "claude_code:x", "/w/one", "stop")
    steps = " | ".join(plan["steps"])
    assert "SIGINT pid 4242 only" in steps
    assert "2 child processes running" in steps
    assert plan["destructive"] is False


def test_pause_is_declared_reversible(live_session):
    plan = pc.control_preflight("claude_code", "claude_code:x", "/w/one", "pause")
    assert plan["reversible"] is True
    assert plan["destructive"] is False


def test_a_refused_pid_guard_is_reported_before_the_press(monkeypatch,
                                                          live_session):
    """The pid-reuse guard is what stops a recycled pid being killed in place
    of the agent that used to own it. Its refusal belongs in the preview."""
    monkeypatch.setattr(pc, "verify_pid",
                        lambda pid, start=None: (False, "start_mismatch"))
    plan = pc.control_preflight("claude_code", "claude_code:x", "/w/one", "kill")
    assert plan["ok"] is False
    assert plan["blocked_reason"] == "pid_guard_refused:start_mismatch"


def test_a_dead_session_is_blocked_with_its_reason(monkeypatch):
    monkeypatch.setattr(pc, "platform_support",
                        lambda: {"controllable": True, "reason": "", "note": ""})
    monkeypatch.setattr(pc, "resolve_session",
                        lambda *a, **k: {"ok": False,
                                         "reason": "session_not_in_claude_map"})
    plan = pc.control_preflight("claude_code", "claude_code:x", "", "kill")
    assert plan["ok"] is False
    assert plan["state"] == "exited"
    assert plan["blocked_reason"]


def test_openclaw_does_not_describe_signals_it_never_sends(monkeypatch):
    """OpenClaw stop/kill is a gateway task cancel and pause is an advisory
    flag file. "SIGTERM pid N" here would describe a mechanism never used."""
    monkeypatch.setattr(pc, "platform_support",
                        lambda: {"controllable": True, "reason": "", "note": ""})
    plan = pc.control_preflight("openclaw", "s1", "", "kill")
    assert plan["mechanism"] == "openclaw_gateway_task_cancel"
    assert "No signal is sent" in plan["plan"]


def test_preflight_never_raises_on_a_junk_action():
    plan = pc.control_preflight("claude_code", "x", "", "detonate")
    assert plan["ok"] is False
    assert plan["blocked_reason"] == "unknown action"


# ── the actuator records what it did ──────────────────────────────────────
def test_the_trace_records_the_pid_the_guard_and_the_outcome(monkeypatch):
    monkeypatch.setattr(ga, "_log_token", lambda v, limit=128: str(v or "")[:limit])
    import clawmetry.sync as sync
    monkeypatch.setattr(sync, "_hitl_set_pause", lambda sid, on: None)
    monkeypatch.setattr(pc, "kill_session",
                        lambda rt, sid, cwd, mode="kill": {
                            "ok": True, "detail": "killed",
                            "resolved_pid": 4242, "resolved_cwd": "/w/one",
                            "guard": "verified_start_token",
                            "tree": [4243, 4242], "escalated": True,
                            "sigkilled": [4243, 4242],
                            "mechanism": "posix_sigterm_then_sigkill"})

    steps = []
    res = ga.guard_actuate("claude_code", "claude_code:x", "", "kill",
                           trace=steps)
    assert res["ok"] is True
    labels = " | ".join(s["step"] for s in steps)
    assert "End the session" in labels
    assert "Resolve the session to a process" in labels
    assert "pid-reuse guard" in labels
    assert "Snapshot the process tree" in labels
    assert "escalate to SIGKILL" in labels
    assert steps[-1]["step"] == "Outcome"
    assert steps[-1]["ok"] is True
    # The pid and the tree are IN the record, not just implied by it.
    joined = " ".join(s["detail"] for s in steps)
    assert "pid 4242" in joined
    assert "4243" in joined


def test_a_failed_step_is_recorded_as_failed(monkeypatch):
    import clawmetry.sync as sync
    monkeypatch.setattr(sync, "_hitl_set_pause", lambda sid, on: None)
    monkeypatch.setattr(pc, "kill_session",
                        lambda rt, sid, cwd, mode="kill": {
                            "ok": False, "detail": "pid_guard_refused:start_mismatch",
                            "guard": "refused_start_mismatch"})
    steps = []
    ga.guard_actuate("claude_code", "claude_code:x", "", "kill", trace=steps)
    assert steps[-1] == {"step": "Outcome", "ok": False,
                         "detail": steps[-1]["detail"], "at": steps[-1]["at"]}
    assert not steps[-1]["ok"]


def test_an_advisory_openclaw_pause_says_so_in_the_trace(monkeypatch):
    """A pause that changed nothing must not look like one that worked."""
    import clawmetry.sync as sync
    monkeypatch.setattr(sync, "_hitl_set_pause", lambda sid, on: None)
    monkeypatch.setattr(pc, "openclaw_pause_capability",
                        lambda: {"effective": False, "mechanism": "none",
                                 "detail": "no proxy; the agent keeps running"})
    steps = []
    res = ga.guard_actuate("openclaw", "s1", "", "pause", trace=steps)
    assert res["advisory_only"] is True
    proxy_step = [s for s in steps if "enforcement proxy" in s["step"]][0]
    assert proxy_step["ok"] is False


def test_the_trace_is_optional(monkeypatch):
    """The daemon's policy pass calls this with no trace; it must not change
    behaviour or cost anything."""
    import clawmetry.sync as sync
    monkeypatch.setattr(sync, "_hitl_set_pause", lambda sid, on: None)
    monkeypatch.setattr(pc, "kill_session",
                        lambda rt, sid, cwd, mode="kill": {"ok": True,
                                                           "detail": "killed"})
    res = ga.guard_actuate("claude_code", "claude_code:x", "", "kill")
    assert res["ok"] is True


# ── the route hands both to the browser ───────────────────────────────────
@pytest.fixture
def client(monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(guard.bp_guard)
    monkeypatch.setattr(guard, "_same_origin_ok", lambda: True)
    monkeypatch.setattr(
        guard, "_ls_call",
        lambda method, **kw: ({"session_id": kw.get("session_id"), "cwd": "/w/one"}
                              if method == "get_session_location" else None))
    return app.test_client()


def _post(client, path, **body):
    body.setdefault("session_id", "claude_code:x")
    body.setdefault("runtime", "claude_code")
    body.setdefault("action", "kill")
    return client.post(path, data=json.dumps(body),
                       content_type="application/json")


def test_the_preflight_route_returns_the_plan(client, live_session):
    resp = _post(client, "/api/guard/control/preflight")
    assert resp.status_code == 200
    d = json.loads(resp.data)
    assert d["ok"] is True
    assert d["pid"] == 4242
    assert d["tree_size"] == 3
    assert d["destructive"] is True
    assert d["steps"]


def test_the_preflight_route_refuses_cross_origin(client, monkeypatch):
    """It discloses local pids and command lines; a cross-site page must not
    be able to ask for them."""
    monkeypatch.setattr(guard, "_same_origin_ok", lambda: False)
    assert _post(client, "/api/guard/control/preflight").status_code == 403


def test_the_preflight_route_validates_the_action(client):
    resp = _post(client, "/api/guard/control/preflight", action="detonate")
    assert resp.status_code == 400


def test_the_control_route_returns_the_trace(client, monkeypatch):
    def fake(runtime, session_id, cwd, action, trace=None):
        if trace is not None:
            trace.append({"step": "SIGTERM pid 4242", "ok": True,
                          "detail": "sent", "at": 0})
            trace.append({"step": "Outcome", "ok": True, "detail": "killed",
                          "at": 0})
        return {"ok": True, "detail": "killed"}

    monkeypatch.setattr(ga, "guard_actuate", fake)
    d = json.loads(_post(client, "/api/guard/control").data)
    assert d["ok"] is True
    assert [s["step"] for s in d["trace"]] == ["SIGTERM pid 4242", "Outcome"]
    # ``at`` is a wall-clock float the page has no use for; it is dropped
    # rather than shipped.
    assert "at" not in d["trace"][0]


# ── the copy has to survive the sanitiser it is sent through ─────────────
#
# ``routes.guard._detail_safe`` is a CodeQL-credited sanitiser with a narrow
# allowlist, and it runs over every plan, step and trace line on the way to the
# page. A sentence written with a character outside that alphabet does not
# error — it silently loses the character. The em dash in the Stop plan welded
# two clauses into "the main pid only the same thing as pressing Ctrl-C", and
# ``runtime=claude_code`` reached the browser as ``runtimeclaude_code``. So the
# copy is pinned to the alphabet rather than the alphabet widened for the copy.
def _round_trips(s) -> bool:
    return guard._detail_safe(s) == s


@pytest.mark.parametrize("action", ["pause", "resume", "stop", "kill"])
def test_every_plan_and_step_survives_the_sanitiser(action, live_session):
    plan = pc.control_preflight("claude_code", "claude_code:x", "/w/one", action)
    assert _round_trips(plan["plan"]), plan["plan"]
    for s in plan["steps"]:
        assert _round_trips(s), s


def test_the_openclaw_plan_survives_the_sanitiser(monkeypatch):
    monkeypatch.setattr(pc, "platform_support",
                        lambda: {"controllable": True, "reason": "", "note": ""})
    plan = pc.control_preflight("openclaw", "s1", "", "kill")
    assert _round_trips(plan["plan"]), plan["plan"]
    for s in plan["steps"]:
        assert _round_trips(s), s


@pytest.mark.parametrize("action", ["pause", "resume", "stop", "kill"])
def test_trace_lines_survive_the_sanitiser(action, monkeypatch):
    import clawmetry.sync as sync
    monkeypatch.setattr(sync, "_hitl_set_pause", lambda sid, on: None)
    done = {"ok": True, "detail": "done", "resolved_pid": 4242,
            "resolved_cwd": "/w/one", "guard": "verified_start_token",
            "tree": [4243, 4242], "pgids": [4242], "shared_pgids": [7],
            "escalated": True, "sigkilled": [4243],
            "mechanism": "posix_sigterm_then_sigkill"}
    for name in ("pause_session", "resume_session"):
        monkeypatch.setattr(pc, name, lambda rt, sid, cwd: dict(done))
    monkeypatch.setattr(pc, "kill_session",
                        lambda rt, sid, cwd, mode="kill": dict(done))
    steps = []
    ga.guard_actuate("claude_code", "claude_code:x", "", action, trace=steps)
    assert steps
    for s in steps:
        assert _round_trips(s["step"]), s
        assert _round_trips(s["detail"]), s


def test_a_partial_trace_survives_an_actuator_crash(client, monkeypatch):
    """The failing case is exactly when the record matters most."""
    def boom(runtime, session_id, cwd, action, trace=None):
        if trace is not None:
            trace.append({"step": "Write the HITL pause flag", "ok": True,
                          "detail": "", "at": 0})
        raise RuntimeError("signal helper exploded")

    monkeypatch.setattr(ga, "guard_actuate", boom)
    resp = _post(client, "/api/guard/control")
    assert resp.status_code == 500
    d = json.loads(resp.data)
    assert d["trace"][0]["step"] == "Write the HITL pause flag"
    # The exception text stays in the server log.
    assert "exploded" not in json.dumps(d)
