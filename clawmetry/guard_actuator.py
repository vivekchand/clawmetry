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
"""

from __future__ import annotations

import logging
import os
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


def guard_actuate(runtime: str, session_id: str, cwd: str,
                  action: str) -> Dict[str, Any]:
    """Send the signal for one policy decision, or one human button press.

    Deliberately mirrors ``sync._run_process_control`` (the cloud-relayed
    path) including its OpenClaw special-casing, so all three ways of
    reaching a process — cloud relay, local button, automatic policy — do
    exactly the same thing to it.

    Returns ``{ok, detail, ...}``. ``detail`` is one of a fixed set of
    tokens (``paused_via_proxy_hitl``, ``unsupported_no_primitive``,
    ``cwd_mismatch_rejected``, ``actuator_error``, ``no-op``, or the signal
    helper's own token) so it can be shown to an operator as-is.
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
                return {"ok": False, "detail": "cwd_mismatch_rejected"}
        except Exception:  # noqa: BLE001
            pass  # No recorded cwd — allow; the caller's own validation is enough

    try:
        if act == "pause":
            _s._hitl_set_pause(sid, True)
            if rt == "openclaw":
                # OpenClaw has no pause primitive. The HITL flag file is the
                # only lever, and the ONLY thing that enforces it is the
                # optional enforcement proxy. Claiming "the proxy refuses
                # further LLM calls" on a node with no proxy reported a
                # stopped agent that was still running — so ask first and
                # report what actually happened.
                cap = _pc.openclaw_pause_capability()
                return {"ok": bool(cap["effective"]),
                        "detail": ("paused_via_proxy_hitl" if cap["effective"]
                                   else "unsupported_no_primitive"),
                        "mechanism": cap["mechanism"],
                        "advisory_only": not cap["effective"],
                        "note": cap["detail"]}
            return _pc.pause_session(rt, sid, cwd)
        if act in ("stop", "kill"):
            _s._hitl_set_pause(sid, True)
            if rt == "openclaw":
                cr = _s._openclaw_cancel_task(sid)
                return {"ok": bool(cr.get("ok")), "action": "cancel",
                        "scope_pending": bool(cr.get("scope_pending")),
                        "detail": (cr.get("error") or "task cancel requested")}
            mode = "stop" if act == "stop" else "kill"
            return _pc.kill_session(rt, sid, cwd, mode=mode)
        if act == "resume":
            _s._hitl_set_pause(sid, False)
            if rt == "openclaw":
                cap = _pc.openclaw_pause_capability()
                return {"ok": bool(cap["effective"]),
                        "detail": ("resumed_via_proxy_hitl" if cap["effective"]
                                   else "nothing_was_holding_this_session"),
                        "mechanism": cap["mechanism"],
                        "advisory_only": not cap["effective"],
                        "note": cap["detail"]}
            return _pc.resume_session(rt, sid, cwd)
    except Exception:  # noqa: BLE001 — never raise into the daemon tick
        # The exception text stays in the log; the returned detail is a fixed
        # token because this dict is recorded and can reach an HTTP response.
        log.exception("guard actuator %s failed for %s",
                      _log_token(act, 32), _log_token(sid))
        return {"ok": False, "detail": "actuator_error"}
    return {"ok": False, "detail": "no-op"}
