"""Guard — live session control and enforcement policies.

Two surfaces, one feature:

* **Control** (``/api/guard/sessions``, ``/api/guard/control``) — what is
  running right now, whether a detector thinks it has gone off track, and a
  Pause / Stop / Kill button per session. This is the human path.
* **Policies** (``/api/guard/policies``) — rules that let the DAEMON take the
  same action with no human present. Authored here, evaluated in
  ``sync.py::_emit_detector_incidents`` via ``clawmetry.policy_engine``.

Both paths end in the SAME actuator (``sync._guard_actuate``) so an automatic
pause and a hand-pressed pause do exactly the same thing to the process.

Naming note: ``/api/guard/policies`` is deliberately distinct from
``/api/tool-policy`` in ``routes/policy.py`` — that one is the pre-tool
sandbox/permission surface, this one is mid-run enforcement. Different axis,
different table, no shared state.
"""
import logging
import os
import re
import time
import uuid

from flask import Blueprint, jsonify, request

log = logging.getLogger("clawmetry.guard")


def _log_safe(v) -> str:
    """One log token from a request-supplied value: no line breaks, bounded."""
    return str(v or "").replace("\r", " ").replace("\n", " ")[:128]


_DETAIL_OK = re.compile(r"[^A-Za-z0-9 _.,:;()'/-]")

# Pre-filter for caller-supplied session identifiers: alphanumeric plus the
# ``_ - . :`` a stored id can legitimately carry (family rows are namespaced
# ``<runtime>:<id>``). Refuses slashes, null bytes and anything else that
# could influence a path or a command. This is only the first gate: the
# handler then resolves the id against the store and acts on the STORED
# copy, so a request can only ever name a session ClawMetry already knows.
_SID_SAFE_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:\-]{0,127}$')
_POLICY_ID_RE = re.compile(r'^[A-Za-z0-9_\-]{1,128}$')


def _detail_safe(v) -> str:
    """Reduce an actuator string to plain words before it reaches a response.

    Actuator dicts can carry stderr fragments or (historically) exception
    text; stripping to a conservative character set breaks that path while
    keeping every legitimate token (``unsupported_no_primitive``,
    ``paused_via_proxy_hitl``, capability notes) readable.
    """
    return _DETAIL_OK.sub("", str(v or ""))[:300]

bp_guard = Blueprint("guard", __name__)

# Actions a caller may ask for. `resume` is control-only (there is no policy
# that resumes; a human decides that). Anything not in here is refused rather
# than passed through to a signal helper.
_CONTROL_ACTIONS = ("pause", "resume", "stop", "kill")

# Runtime ids are snake_case adapter names (``claude_code``, ``qwen_code``).
_RUNTIME_SAFE_RE = re.compile(r'^[a-z0-9_]{1,40}$')


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback.

    Mirror of ``routes/health.py::_ls_call``. The daemon owns DuckDB's writer
    lock, so a direct open from the dashboard raises on the standard install;
    we go through the daemon proxy first and only fall back to a direct open
    for single-process boots (tests + dev mode).
    """
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


def _ls_write(method_name, **kwargs):
    """Route a WRITE at whichever process owns the DuckDB writer lock.

    Reads can fall back to a read-only open; writes cannot. On the standard
    install the daemon holds the writer lock, so the proxy is the only path
    that works; in single-process dev/test boots the direct open is. We try
    both — every write here is idempotent (PK upsert / PK delete), so a
    double-apply is harmless and one of the two landing is what matters.

    Returns nothing meaningful on purpose: ``local_store_via_daemon``
    returns ``None`` both for "method missing" and for a write that
    succeeded (writes return None), so the return value cannot be trusted
    (memory: feedback_dashboard_writes_noop_through_proxy). Callers MUST
    verify by reading back.
    """
    try:
        from routes.local_query import local_store_via_daemon
        local_store_via_daemon(method_name, **kwargs)
    except Exception:
        pass
    try:
        from clawmetry import local_store
        getattr(local_store.get_store(), method_name)(**kwargs)
    except Exception:
        pass


def _same_origin_ok() -> bool:
    """Reject cross-site POSTs to the mutating endpoints.

    These routes can SIGKILL a user's agent, so a drive-by form post from any
    open browser tab to ``localhost:8900`` must not reach the actuator. A
    request with no Origin/Referer at all (curl, the CLI, tests) is allowed —
    browsers always send one for a cross-site POST, so absence is not the
    attack we are blocking here.
    """
    origin = request.headers.get("Origin") or ""
    if not origin:
        referer = request.headers.get("Referer") or ""
        if not referer:
            return True
        origin = referer
    try:
        from urllib.parse import urlparse
        host = urlparse(origin).netloc.lower()
    except Exception:
        return False
    if not host:
        return False
    req_host = (request.host or "").lower()
    if host == req_host:
        return True
    # Same port on an equivalent loopback name (localhost vs 127.0.0.1).
    loopback = ("localhost", "127.0.0.1", "[::1]", "::1")
    def _split(h):
        if h.startswith("["):
            close = h.find("]")
            return h[:close + 1], h[close + 2:] if close + 1 < len(h) else ""
        parts = h.rsplit(":", 1)
        return (parts[0], parts[1]) if len(parts) == 2 else (h, "")
    o_host, o_port = _split(host)
    r_host, r_port = _split(req_host)
    return o_host in loopback and r_host in loopback and o_port == r_port


def _runtime_supports_signals(runtime: str, session_id: str = "",
                              cwd: str = "") -> dict:
    """Can we actually control this SESSION, on this platform, right now?

    Answering honestly at LIST time is the point: a Stop button that silently
    does nothing is worse than a disabled one with a reason next to it.

    The verdict comes from ``process_control.runtime_control_support`` so the
    UI, the daemon and the actuator all read the same answer. It is per
    session, not per runtime, because three things vary independently:

    * the OS — POSIX signals, the Windows native equivalents, or neither;
    * the session's execution model — a Cursor CLI session is a real process
      tree and IS controllable, while a Cursor editor conversation is not;
    * for OpenClaw, whether the enforcement proxy is running, which decides
      whether Pause does anything at all.
    """
    try:
        from clawmetry import process_control as _pc
    except Exception:
        return {"controllable": False, "reason": "process_control unavailable",
                "actions": []}
    try:
        return _pc.runtime_control_support(runtime, session_id, cwd)
    except Exception:  # noqa: BLE001 — never break the list render
        log.exception("guard capability check failed for %s",
                      _log_safe(session_id))
        return {"controllable": False, "actions": [],
                "reason": "capability check failed; see the server log"}


def _session_runtime(session_id: str, agent_type: str) -> str:
    """Which runtime is this session, really? Mirrors ``sync._detector_runtime``:
    the session-id prefix wins, ``agent_type`` is only the fallback, because on
    a real install the column reads ``openclaw`` for nearly every row."""
    try:
        from clawmetry import waste_flags as _wf
        rt = str(_wf.runtime_from_session_id(session_id) or "").strip().lower()
    except Exception:
        rt = ""
    return rt or str(agent_type or "").strip().lower()


# Severity ladder shared with ``clawmetry.detectors`` (higher is louder).
_SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}


def _incident_rank(inc) -> tuple:
    """Sort key for one incident: money, then severity, then size.

    Kept in sync with ``detectors.incident_rank``. It is duplicated rather
    than imported because this route must render on a cloud instance where
    ``clawmetry.detectors`` may be absent, and a missing import must not take
    the Guard tab down with it.
    """
    if not isinstance(inc, dict):
        return (0.0, 0, 0)
    try:
        spend = float(inc.get("spend_at_risk_usd") or 0)
    except (TypeError, ValueError):
        spend = 0.0
    sev = _SEVERITY_RANK.get(str(inc.get("severity") or "").lower(), 0)
    try:
        count = int(inc.get("count") or 0)
    except (TypeError, ValueError):
        count = 0
    return (spend, sev, count)


@bp_guard.route("/api/guard/sessions")
def api_guard_sessions():
    """Live sessions with their current Guard status.

    One row per active session: identity, spend, whether a detector currently
    flags it, and whether this node can actually signal it. Returns an empty
    list (HTTP 200) on any store error so the tab renders an honest empty
    state instead of an error page.
    """
    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 200))
    except (TypeError, ValueError):
        limit = 50

    sessions = _ls_call("query_sessions_table", limit=limit) or []
    signals = _ls_call("query_recent_loop_signals", limit=200,
                       since_minutes=30) or []

    # Newest incident per session wins; a session can trip several detectors.
    incident_by_session = {}
    for sig in signals:
        if not isinstance(sig, dict):
            continue
        sid = str(sig.get("session_id") or "")
        if not sid:
            continue
        details = sig.get("details")
        if isinstance(details, str):
            try:
                import json as _json
                details = _json.loads(details)
            except Exception:
                details = {}
        details = details if isinstance(details, dict) else {}
        prev = incident_by_session.get(sid)
        count = int(sig.get("repeat_count") or 0)
        try:
            at_risk = round(float(details.get("spend_at_risk_usd") or 0), 4)
        except (TypeError, ValueError):
            at_risk = 0.0
        candidate = {
            "kind": str(details.get("kind") or ""),
            "title": str(details.get("message") or ""),
            "detail": str(details.get("detail") or ""),
            "severity": str(sig.get("severity") or "warning"),
            "count": count,
            "since": sig.get("first_seen"),
            # What ignoring this stretch is estimated to cost, and on what
            # basis. ``basis`` travels with the number on purpose: a reader
            # must be able to tell a measured burn rate from a guess.
            "spend_at_risk_usd": at_risk,
            "spend_basis": str(details.get("spend_basis") or "unknown"),
            "evidence": details.get("evidence")
            if isinstance(details.get("evidence"), dict) else {},
        }
        # A session can trip several detectors at once. The one that gets the
        # row is the one that costs the most to ignore, falling back to
        # severity and then to count when no cost is known — the same order
        # ``detectors.incident_rank`` uses, so the tab and the daemon agree on
        # which finding is the loudest.
        if prev is None or _incident_rank(candidate) > _incident_rank(prev):
            incident_by_session[sid] = candidate

    out = []
    for s in sessions:
        if not isinstance(s, dict):
            continue
        if s.get("ended_at"):
            continue
        status = str(s.get("status") or "").lower()
        if status in ("ended", "completed", "stopped", "failed"):
            continue
        sid = str(s.get("session_id") or "")
        if not sid:
            continue
        # The ``sessions`` table's ``agent_type`` reads ``openclaw`` for
        # nearly every row on a real install; the session-id prefix is the
        # identity the rest of the product uses (same derivation as
        # ``sync._detector_runtime``). Trusting the column here would hand
        # ``runtime_control_support`` the wrong runtime for every family
        # session and disable controls that work.
        runtime = _session_runtime(sid, s.get("agent_type") or "")
        meta = s.get("metadata")
        meta = meta if isinstance(meta, dict) else {}
        cwd = ""
        for key in ("cwd", "workspace", "project_dir", "working_dir", "path"):
            val = meta.get(key)
            if isinstance(val, str) and val.strip():
                cwd = val.strip()
                break
        try:
            cost = round(float(s.get("cost_usd") or 0), 4)
        except (TypeError, ValueError):
            cost = 0.0
        support = _runtime_supports_signals(runtime, sid, cwd)
        out.append({
            "session_id": sid,
            "runtime": runtime,
            "agent_id": str(s.get("agent_id") or ""),
            "title": str(s.get("title") or "")[:160],
            "status": status,
            "started_at": s.get("started_at"),
            "last_active_at": s.get("last_active_at"),
            "cost_usd": cost,
            "total_tokens": int(s.get("total_tokens") or 0),
            "message_count": int(s.get("message_count") or 0),
            "cwd": cwd,
            "incident": incident_by_session.get(sid),
            "controllable": support["controllable"],
            "control_reason": support.get("reason", ""),
            "no_pause": support.get("no_pause", False),
            # Which buttons may be enabled for THIS session. Empty means none.
            "control_actions": support.get("actions", []),
            # Why a control behaves differently here (OpenClaw's proxy-backed
            # pause, the Windows Ctrl+C blast radius). Rendered as a hint.
            "control_note": support.get("note", "")
                            or support.get("platform", {}).get("note", ""),
        })

    # Flagged sessions first, most expensive to ignore at the top; unflagged
    # sessions keep their recency order below. Sorting by severity alone put a
    # $0.02 "continued after a failed command" above a $170 loop, which is the
    # ranking the money model exists to fix.
    out.sort(key=lambda r: (
        1 if r.get("incident") else 0,
        _incident_rank(r.get("incident")),
    ), reverse=True)

    flagged = [r for r in out if r.get("incident")]
    return jsonify({
        "sessions": out,
        "count": len(out),
        "flagged": len(flagged),
        # The headline number for the tab: what the flagged stretches are
        # estimated to be burning right now.
        "spend_at_risk_usd": round(sum(
            float((r.get("incident") or {}).get("spend_at_risk_usd") or 0)
            for r in flagged), 2),
    })


@bp_guard.route("/api/guard/control", methods=["POST"])
def api_guard_control():
    """Pause / resume / stop / kill one session, on the user's explicit click.

    Not entitlement-gated: the user pressed the button, exactly as the manual
    budget pause bypasses ``_auto_pause_allowed``. What IS gated is the daemon
    deciding to do this on its own (see ``sync._guard_enforcement_allowed``).
    """
    if not _same_origin_ok():
        return jsonify({"ok": False, "error": "cross-origin request refused"}), 403

    data = request.get_json(silent=True) or {}
    action = str(data.get("action") or "").strip().lower()
    session_id = str(data.get("session_id") or "").strip()
    runtime = str(data.get("runtime") or "").strip().lower()
    cwd = str(data.get("cwd") or "").strip()

    # Literal tuple on purpose: a comparison against constants is the one
    # sanitizer static analysis credits, and ``action`` is echoed into the
    # audit trail and the log.
    if action not in ("pause", "resume", "stop", "kill"):
        return jsonify({"ok": False,
                        "error": f"action must be one of {list(_CONTROL_ACTIONS)}"}), 400
    if not session_id:
        return jsonify({"ok": False, "error": "session_id is required"}), 400
    if not _SID_SAFE_RE.match(session_id) or ".." in session_id:
        return jsonify({"ok": False, "error": "invalid session_id"}), 400
    if runtime and not _RUNTIME_SAFE_RE.match(runtime):
        return jsonify({"ok": False, "error": "invalid runtime"}), 400
    if cwd:
        try:
            cwd = os.path.realpath(cwd)
        except Exception:
            return jsonify({"ok": False, "error": "invalid cwd"}), 400

    # Act on the STORED session, not the request. The store's own copy of the
    # id and working directory are what reach the signal helpers, so a
    # request can name a session but never supply the strings a process is
    # located or signalled with. A session the store does not know cannot be
    # controlled from here — it is not on any list this dashboard renders.
    recorded = _ls_call("get_session_location", session_id=session_id)
    if not isinstance(recorded, dict) or not recorded.get("session_id"):
        return jsonify({"ok": False, "error": "unknown session",
                        "detail": "session_not_in_store"}), 404
    stored_sid = str(recorded.get("session_id") or "")
    stored_cwd = str(recorded.get("cwd") or "")
    if cwd and stored_cwd and os.path.realpath(stored_cwd) != cwd:
        # A crafted request cannot redirect signals to an arbitrary
        # working directory.
        return jsonify({"ok": False,
                        "error": "cwd does not match session record"}), 400

    try:
        # Every control action — resume included — goes through the actuator
        # the daemon's policies use, so a manual pause and an automatic one
        # are indistinguishable to the agent process.
        from clawmetry.guard_actuator import guard_actuate
        result = guard_actuate(runtime, stored_sid, stored_cwd, action)
    except Exception:  # noqa: BLE001
        # Full detail goes to the server log; the client gets a generic
        # message so an exception can never leak internals to the page.
        # Request-supplied values are stripped of line breaks before logging
        # so a crafted id cannot forge extra log lines.
        log.exception("guard control %s failed for %s",
                      _log_safe(action), _log_safe(session_id))
        return jsonify({"ok": False,
                        "error": "control action failed; see the server log",
                        "session_id": session_id, "action": action}), 500

    result = result if isinstance(result, dict) else {"ok": False}
    ok = bool(result.get("ok"))

    # Manual actions belong in the same audit trail as automatic ones.
    try:
        from clawmetry import audit as _a
        _a.audit_event(
            f"guard.{action}",
            actor="dashboard",
            target=stored_sid,
            result="ok" if ok else "failed",
            source="dashboard",
            metadata={"runtime": runtime,
                      "detail": str(result.get("detail") or "")[:200]},
        )
    except Exception:
        pass

    # A curated result, not the raw actuator dict: an actuator error string
    # can carry an exception message, and the client only needs the fields
    # the UI renders. ``detail`` is reduced to a plain-word token set so no
    # exception text or control characters can reach the page.
    return jsonify({
        "ok": ok,
        "action": action,
        "session_id": stored_sid,
        "runtime": runtime,
        "detail": _detail_safe(result.get("detail") or result.get("reason")
                               or result.get("error") or ""),
        "advisory_only": bool(result.get("advisory_only")),
        "mechanism": _detail_safe(result.get("mechanism"))[:80],
        "note": _detail_safe(result.get("note")),
        "unsupported": (None if result.get("unsupported") is None
                        else _detail_safe(result.get("unsupported"))[:80]),
    })


@bp_guard.route("/api/guard/policies", methods=["GET", "POST"])
def api_guard_policies():
    """List Guard policies, or create/update one.

    A new policy defaults to ``action="monitor"`` — it records what it WOULD
    have done and changes nothing — so authoring a rule can never surprise
    anyone. Escalating to pause/stop/kill is a deliberate second step, and
    still needs ``CLAWMETRY_POLICY_ENFORCE=1`` on the node to bite.

    A policy may also carry an escalation ladder as ``steps``::

        "steps": [{"action": "pause", "after_secs": 0},
                  {"action": "kill",  "after_secs": 300}]

    Each rung passes through the same three locks as a plain action, and only
    fires if the session is still matching when its delay elapses. Rungs are
    normalized (and malformed ones dropped) by
    ``policy_engine.normalize_steps`` before storage, so what comes back from
    a read is exactly what will be evaluated.
    """
    if request.method == "GET":
        rows = _ls_call("query_session_policies") or []
        import os as _os
        from clawmetry.policy_engine import (ACTIONS, MAX_LADDER_STEPS,
                                             MAX_STEP_DELAY_SECS)
        # Show the ladder the ENGINE will run, not the raw column: a policy
        # stored before ladders existed reads back as its single action, and
        # the UI should render one shape for both.
        try:
            from clawmetry.policy_engine import normalize_steps as _norm
            for r in rows:
                if isinstance(r, dict):
                    r["steps"] = _norm(r)
        except Exception:
            pass
        return jsonify({
            "policies": rows,
            "count": len(rows),
            "actions": list(ACTIONS),
            "max_ladder_steps": MAX_LADDER_STEPS,
            "max_step_delay_secs": MAX_STEP_DELAY_SECS,
            # The UI must be able to say "these rules are not enforcing".
            "enforcement_enabled": _os.environ.get(
                "CLAWMETRY_POLICY_ENFORCE", "0") == "1",
            "evaluation_enabled": _os.environ.get(
                "CLAWMETRY_GUARD_POLICIES", "1") != "0",
        })

    if not _same_origin_ok():
        return jsonify({"ok": False, "error": "cross-origin request refused"}), 403

    data = request.get_json(silent=True) or {}
    from clawmetry.policy_engine import ACTIONS, MAX_LADDER_STEPS, normalize_steps
    action = str(data.get("action") or "monitor").strip().lower()
    if action not in ACTIONS:
        return jsonify({"ok": False,
                        "error": f"action must be one of {list(ACTIONS)}"}), 400

    # Reject a bad ladder loudly instead of silently storing a shorter one.
    # normalize_steps DROPS unusable rungs by design (never coerces them into
    # some other action), which is right for the engine reading old rows but
    # wrong for a fresh author request: an operator who typed "terminate"
    # must be told, not handed a ladder quietly missing a rung.
    raw_steps = data.get("steps")
    if raw_steps not in (None, "", []):
        if not isinstance(raw_steps, list):
            return jsonify({"ok": False,
                            "error": "steps must be a list of "
                                     "{action, after_secs} objects"}), 400
        if len(raw_steps) > MAX_LADDER_STEPS:
            return jsonify({"ok": False,
                            "error": f"a ladder may have at most "
                                     f"{MAX_LADDER_STEPS} steps"}), 400
        for i, entry in enumerate(raw_steps):
            if not isinstance(entry, dict):
                return jsonify({"ok": False,
                                "error": f"step {i + 1} must be an object"}), 400
            act = str(entry.get("action") or "").strip().lower()
            if act not in ACTIONS:
                return jsonify({"ok": False,
                                "error": f"step {i + 1}: action must be one "
                                         f"of {list(ACTIONS)}"}), 400
            delay = entry.get("after_secs", 0)
            try:
                if int(delay or 0) < 0:
                    raise ValueError
            except (TypeError, ValueError):
                return jsonify({"ok": False,
                                "error": f"step {i + 1}: after_secs must be a "
                                         f"non-negative number of seconds"}), 400

    policy_id = str(data.get("policy_id") or "").strip() or f"gp-{uuid.uuid4().hex[:12]}"
    policy = {
        "policy_id": policy_id,
        "name": str(data.get("name") or "")[:200],
        "enabled": bool(data.get("enabled", True)),
        "scope_runtime": str(data.get("scope_runtime") or "").strip(),
        "scope_agent_id": str(data.get("scope_agent_id") or "").strip(),
        "trigger_kind": str(data.get("trigger_kind") or "").strip(),
        "min_severity": str(data.get("min_severity") or "info").strip(),
        "min_repeat": data.get("min_repeat") or 0,
        "min_duration_s": data.get("min_duration_s") or 0,
        "min_spend_usd": data.get("min_spend_usd") or 0,
        "min_spend_at_risk_usd": data.get("min_spend_at_risk_usd") or 0,
        "action": action,
        "steps": raw_steps or [],
    }
    # Echo back the ladder the engine will actually run (step 0's delay is
    # forced to 0, delays are clamped), so the UI never shows the operator a
    # ladder that differs from the stored one.
    policy["steps"] = normalize_steps(policy)
    _ls_write("upsert_session_policy", policy=policy)
    # Verify by reading back: a write through the daemon proxy returns None
    # whether it landed or not, so "no exception" is not evidence of success.
    rows = _ls_call("query_session_policies") or []
    if not any(r.get("policy_id") == policy_id for r in rows):
        return jsonify({"ok": False, "error": "policy store unavailable"}), 503
    return jsonify({"ok": True, "policy_id": policy_id, "policy": policy})


@bp_guard.route("/api/guard/policies/<policy_id>", methods=["DELETE"])
def api_guard_policy_delete(policy_id):
    """Delete one Guard policy."""
    if not _same_origin_ok():
        return jsonify({"ok": False, "error": "cross-origin request refused"}), 403
    if not _POLICY_ID_RE.match(policy_id or ""):
        return jsonify({"ok": False, "error": "invalid policy_id"}), 400
    _ls_write("delete_session_policy", policy_id=policy_id)
    rows = _ls_call("query_session_policies") or []
    still_there = any(r.get("policy_id") == policy_id for r in rows)
    return jsonify({"ok": not still_there, "policy_id": policy_id})


@bp_guard.route("/api/guard/actions")
def api_guard_actions():
    """Recent policy decisions — what fired, what it did, and why.

    Includes dry-run (``monitor``) decisions, which is the point: before
    turning enforcement on you can read exactly what would have happened.
    """
    try:
        limit = max(1, min(int(request.args.get("limit", 50)), 500))
    except (TypeError, ValueError):
        limit = 50
    rows = _ls_call("query_policy_actions", limit=limit) or []
    return jsonify({"actions": rows, "count": len(rows),
                    "server_time": int(time.time())})
