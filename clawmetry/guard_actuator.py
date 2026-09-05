"""Guard actuator — the ONE path from a decision to a process.

Both ways ClawMetry can act on an agent end here: a human pressing
Pause / Resume / Stop / Kill in the Guard tab (``routes/guard.py``) and the
daemon's policy pass firing a rung of a policy (``sync._apply_guard_policies``).
Because they share this function, an automatic pause and a hand-pressed
pause are identical to the agent process — resume included, which used to
bypass the shared path and call the signal helper directly.

The module is deliberately small and free of module-level imports from the
daemon so it can be read on its own: the pieces it composes (the HITL pause
flag, the OpenClaw CLI task cancel, the per-platform signal helpers) are
looked up at call time. That also keeps the daemon's monkeypatch seams
(``sync._hitl_set_pause``, ``sync._openclaw_cancel_task``) working exactly
as before.

Never raises: every outcome is a structured result the caller records
verbatim, and the ``detail`` field is always a fixed token, never exception
text, because the dict can reach an HTTP response.

Every call also records a STEP TRACE — an ordered list of what it did, in
order, with the outcome of each step. Pause / Stop / Kill signal real
processes and Kill is irreversible; an operator pressing one is entitled to
see the mechanism rather than a spinner and a verdict. The trace is built
here, at the one place both callers pass through, so the daemon's policy
decisions and a human's button press produce the same record.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict

log = logging.getLogger("clawmetry.guard_actuator")

# Actions the actuator understands. ``resume`` is control-only: no policy
# can request it (it is not in ``policy_engine.ACTIONS``); a human decides
# that.
ACTIONS = ("pause", "resume", "stop", "kill")


def _log_token(value: Any, limit: int = 128) -> str:
    """One log-safe token from a caller-supplied value: line breaks removed
    so a crafted id cannot forge extra log lines, length bounded."""
    return str(value or "")[:limit].replace("\r", " ").replace("\n", " ")


def _step(trace, label: str, ok: bool = True, detail: str = "") -> None:
    """Append one step to the trace, if the caller asked for one.

    ``detail`` is caller-facing: it is bounded and stripped of line breaks for
    the same reason ``guard_actuate``'s ``detail`` is a fixed token — the trace
    is rendered in a browser and recorded in the audit trail.
    """
    if trace is None:
        return
    trace.append({"step": str(label)[:160],
                  "ok": bool(ok),
                  "detail": _log_token(detail, 200),
                  "at": time.time()})


# What each action's headline step is called, so the trace reads as prose
# rather than as function names.
_ACTION_STEP = {
    "pause": "Freeze the process tree (SIGSTOP)",
    "resume": "Unfreeze the process tree (SIGCONT)",
    "stop": "Cancel the current turn (SIGINT to the main pid)",
    "kill": "End the session (SIGTERM, then SIGKILL the tree)",
}


def guard_actuate(runtime: str, session_id: str, cwd: str,
                  action: str, trace=None) -> Dict[str, Any]:
    """Send the signal for one policy decision, or one human button press.

    Deliberately mirrors ``sync._run_process_control`` (the cloud-relayed
    path) including its OpenClaw special-casing, so all three ways of
    reaching a process — cloud relay, local button, automatic policy — do
    exactly the same thing to it.

    Returns ``{ok, detail, ...}``. ``detail`` is one of a fixed set of
    tokens (``paused_via_proxy_hitl``, ``unsupported_no_primitive``,
    ``cwd_mismatch_rejected``, ``actuator_error``, ``no-op``, or the signal
    helper's own token) so it can be shown to an operator as-is.

    Pass a list as ``trace`` to receive the ordered steps this call took —
    ``[{step, ok, detail, at}, ...]``. It is appended to as the work happens,
    so a caller still holds the partial record if a step fails.
    """
    import clawmetry.process_control as _pc
    import clawmetry.sync as _s

    rt = (runtime or "").strip().lower()
    act = (action or "").strip().lower()
    sid = str(session_id or "")

    # When an HTTP handler supplies cwd, validate it against the session's
    # recorded location before passing it to any signal helper. The daemon
    # supplies cwd from the session record itself, so this is a no-op for
    # automatic policy actions; it closes the injection path for the HTTP
    # handler (routes/guard.py also canonicalises, but defence-in-depth here).
    if cwd:
        try:
            import clawmetry.local_store as _ls
            rec = _ls.get_store().get_session_location(sid)
            recorded_cwd = (rec or {}).get("cwd") or ""
            if recorded_cwd and (
                os.path.realpath(cwd) != os.path.realpath(recorded_cwd)
            ):
                log.warning(
                    "guard actuate cwd mismatch for %s: supplied=%s recorded=%s",
                    _log_token(sid), _log_token(cwd, 200),
                    _log_token(recorded_cwd, 200),
                )
                _step(trace, "Check the working directory against the session "
                             "record", False,
                      "refused: supplied cwd does not match the recorded one")
                return {"ok": False, "detail": "cwd_mismatch_rejected",
                        "trace": trace}
            _step(trace, "Check the working directory against the session "
                         "record", True, recorded_cwd or cwd)
        except Exception:  # noqa: BLE001
            # No recorded cwd — allow; the caller's own validation is enough.
            _step(trace, "Check the working directory against the session "
                         "record", True, "no recorded cwd; caller-validated")

    _step(trace, _ACTION_STEP.get(act, act), True, f"runtime: {rt or 'unknown'}")

    try:
        if act == "pause":
            _s._hitl_set_pause(sid, True)
            _step(trace, "Write the HITL pause flag for this session", True,
                  "clawmetry home, hitl/pause_ plus the session id")
            if rt == "openclaw":
                # OpenClaw has no pause primitive. The HITL flag file is the
                # only lever, and the ONLY thing that enforces it is the
                # optional enforcement proxy. Claiming "the proxy refuses
                # further LLM calls" on a node with no proxy reported a
                # stopped agent that was still running — so ask first and
                # report what actually happened.
                cap = _pc.openclaw_pause_capability()
                _step(trace, "Check whether the enforcement proxy is running",
                      bool(cap["effective"]), cap["detail"])
                return {"ok": bool(cap["effective"]),
                        "detail": ("paused_via_proxy_hitl" if cap["effective"]
                                   else "unsupported_no_primitive"),
                        "mechanism": cap["mechanism"],
                        "advisory_only": not cap["effective"],
                        "note": cap["detail"], "trace": trace}
            return _traced(trace, _pc.pause_session(rt, sid, cwd))
        if act in ("stop", "kill"):
            _s._hitl_set_pause(sid, True)
            _step(trace, "Write the HITL pause flag for this session", True,
                  "held so the session cannot start a new turn mid-stop")
            if rt == "openclaw":
                cr = _s._openclaw_cancel_task(sid)
                _step(trace, "Ask the OpenClaw gateway to cancel this task",
                      bool(cr.get("ok")),
                      str(cr.get("error") or "task cancel requested"))
                return {"ok": bool(cr.get("ok")), "action": "cancel",
                        "scope_pending": bool(cr.get("scope_pending")),
                        "detail": (cr.get("error") or "task cancel requested"),
                        "trace": trace}
            mode = "stop" if act == "stop" else "kill"
            return _traced(trace, _pc.kill_session(rt, sid, cwd, mode=mode))
        if act == "resume":
            _s._hitl_set_pause(sid, False)
            _step(trace, "Clear the HITL pause flag for this session", True, "")
            if rt == "openclaw":
                cap = _pc.openclaw_pause_capability()
                return {"ok": bool(cap["effective"]),
                        "detail": ("resumed_via_proxy_hitl" if cap["effective"]
                                   else "nothing_was_holding_this_session"),
                        "mechanism": cap["mechanism"],
                        "advisory_only": not cap["effective"],
                        "note": cap["detail"], "trace": trace}
            return _traced(trace, _pc.resume_session(rt, sid, cwd))
    except Exception:  # noqa: BLE001 — never raise into the daemon tick
        # The exception text stays in the log; the returned detail is a fixed
        # token because this dict is recorded and can reach an HTTP response.
        log.exception("guard actuator %s failed for %s",
                      _log_token(act, 32), _log_token(sid))
        _step(trace, "Send the signal", False,
              "the actuator raised; see the server log")
        return {"ok": False, "detail": "actuator_error", "trace": trace}
    _step(trace, "Send the signal", False, "no-op: nothing matched this action")
    return {"ok": False, "detail": "no-op", "trace": trace}


# Which fields of a signal-helper result are worth a trace line, and what to
# call them. The helpers already return this detail; it simply never reached
# anyone (memory: the tab was a black box between click and alert box).
def _traced(trace, res: Dict[str, Any]) -> Dict[str, Any]:
    """Turn one signal-helper result into trace steps, then return it.

    Reads only fields the helpers document (``resolved_pid``, ``guard``,
    ``tree``, ``escalated``, ``pgids``, ``mechanism``, ``detail``), so a helper
    that grows a field does not silently change what an operator is shown.
    """
    if trace is None or not isinstance(res, dict):
        return res
    pid = res.get("resolved_pid") or res.get("pid")
    if pid:
        _step(trace, "Resolve the session to a process", True,
              f"pid {pid}" + (f" in {res['resolved_cwd']}"
                              if res.get("resolved_cwd") else ""))
    guard = str(res.get("guard") or "")
    if guard:
        # The pid-reuse guard is the check that stops a recycled pid being
        # signalled in place of the agent that used to own it. Naming its
        # verdict is the difference between "we killed something" and "we
        # killed the right thing".
        _step(trace, "Confirm the pid is still the same process (pid-reuse "
                     "guard)", not guard.startswith("refused"), guard)
    tree = res.get("tree")
    if isinstance(tree, list) and tree:
        _step(trace, "Snapshot the process tree", True,
              f"{len(tree)} process" + ("es" if len(tree) != 1 else "")
              + ": " + ", ".join(str(p) for p in tree[:12]))
    pgids = res.get("pgids")
    if isinstance(pgids, list) and pgids:
        _step(trace, "Signal the process groups owned by this session", True,
              "pgid " + ", ".join(str(g) for g in pgids[:12]))
    shared = res.get("shared_pgids")
    if isinstance(shared, list) and shared:
        _step(trace, "Skip process groups shared with something outside this "
                     "session, signal their members individually", True,
              "pgid " + ", ".join(str(g) for g in shared[:12]))
    mech = str(res.get("mechanism") or "")
    if res.get("escalated"):
        killed = res.get("sigkilled") or []
        _step(trace, "SIGTERM was not enough; escalate to SIGKILL", True,
              f"{len(killed)} process" + ("es" if len(killed) != 1 else "")
              + " SIGKILLed")
    _step(trace, "Outcome", bool(res.get("ok")),
          str(res.get("detail") or "") + (f" ({mech})" if mech else ""))
    res["trace"] = trace
    return res
