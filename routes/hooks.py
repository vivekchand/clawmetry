"""routes/hooks.py — local receiver for runtime pre-tool hooks.

POST /api/hooks/claude-code/pretooluse is the server half of the Claude
Code PreToolUse gate (client half: ``clawmetry hook claude-code`` →
clawmetry/claude_code_gate.hook_main; installer:
claude_code_gate.gate_handler driven by approvals.sync_runtime_gates).

Flow per call:
  1. Match the {tool_name, tool_input} against the active local policies
     (the SAME load_policies/match_policy the reactive watcher uses).
  2. No require_approval match → immediate "allow" (no opinion recorded).
  3. Match → park a *pending* row in the local approvals queue (the exact
     queue GET /api/approvals serves and the Approvals tab renders), then
     wait for the human's POST /api/approvals/<id>/decide.
  4. approved → allow; denied → deny (with the decision reason);
     policy window elapsed → the policy's on_timeout, mapped
     kill/deny → deny, allow/approve → allow, anything else → ask.

LONG WAITS: the hook client may need to block for the policy's full window
(up to 7 days), but one HTTP request must NOT (waitress's channel_timeout
is 120 s and reverse proxies are worse). So each POST waits at most
``_WAIT_SLICE_S`` and then answers ``{"status": "pending", "approval_id"}``;
the client re-POSTs with that ``approval_id`` and we resume — resume
requests never create a second row. The row itself carries the policy
timeout / on_timeout / deadline in its args blob, so resumes are stateless
on the server side and safe under concurrency (all state lives in the
DuckDB row; decisions go through update_approval_decision's
first-click-wins transition).

AUTH: none beyond loopback. This endpoint is called by a hook process on
the SAME machine as the dashboard; the installer always embeds a
http://127.0.0.1:<port> base. We reject non-loopback callers outright —
a dashboard bound to 0.0.0.0 must not accept pre-tool verdicts from the
network. Entitlement: rather than @gate's 402 (which the fail-open client
would surface as "no opinion" anyway), an unentitled node gets an explicit
"allow" so the behaviour is identical but observable.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import uuid

from flask import Blueprint, jsonify, request

bp_hooks = Blueprint("hooks", __name__)

# How long one POST may hold the connection while waiting for a human
# decision. Keep well under waitress's 120 s channel_timeout.
_WAIT_SLICE_S = float(os.environ.get("CLAWMETRY_HOOK_WAIT_SLICE_S", "20"))
_POLL_INTERVAL_S = 1.0

_SERVER_INFO_PATH = os.path.expanduser("~/.clawmetry/server.json")


# ── dashboard port discovery (~/.clawmetry/server.json) ────────────────────
# The claude_code gate installer (which runs in the sync DAEMON, a different
# process) needs this dashboard's base URL to embed into the hook command.
# No existing mechanism records the dashboard's port (~/.clawmetry/
# local_query.json is the daemon's own query server, not us), so this
# blueprint writes it: once at registration (port parsed from this process's
# argv, default 8900) and refined on the first real request with the port
# the WSGI server actually bound.

def _write_server_info(port: int) -> None:
    try:
        payload = {"port": int(port), "pid": os.getpid(),
                   "written_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                               time.gmtime())}
        os.makedirs(os.path.dirname(_SERVER_INFO_PATH), exist_ok=True)
        tmp = _SERVER_INFO_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(payload, f)
        os.replace(tmp, _SERVER_INFO_PATH)
    except Exception:
        pass  # discovery degrades to the 8900 default — never break boot


def _argv_port() -> int:
    argv = sys.argv or []
    for flag in ("--port", "-p"):
        if flag in argv:
            try:
                return int(argv[argv.index(flag) + 1])
            except (IndexError, TypeError, ValueError):
                pass
    return 8900


@bp_hooks.record_once
def _record_dashboard_port(state) -> None:
    # Skip under pytest — test apps register this blueprint too and must
    # not clobber the developer's real server.json.
    if "pytest" in sys.modules:
        return
    _write_server_info(_argv_port())


_port_refined = False


@bp_hooks.before_app_request
def _refine_dashboard_port():
    # One-shot: the first request tells us the port the server REALLY bound
    # (argv parsing can miss exotic launch paths). Cheap guard first — this
    # runs on every request app-wide.
    global _port_refined
    if _port_refined:
        return None
    _port_refined = True
    if "pytest" in sys.modules:
        return None
    try:
        port = int(request.environ.get("SERVER_PORT") or 0)
        if 0 < port < 65536 and port != _argv_port():
            _write_server_info(port)
    except Exception:
        pass
    return None


# ── store plumbing (same daemon-proxy-first ladder as routes/policy.py) ────

def _ls_read(method_name: str, **kwargs):
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


def _input_hash(tool_input: dict) -> str:
    return hashlib.md5(
        json.dumps(tool_input, sort_keys=True, default=str).encode()
    ).hexdigest()


def _ls_write(method_name: str, **kwargs) -> bool:
    """Writer call: daemon proxy first (it owns the DuckDB writer lock),
    direct writable store as the single-process fallback."""
    try:
        from routes.local_query import (
            local_store_call_via_daemon, PROXY_UNAVAILABLE,
        )
        # Every writer here (ingest_approval, ...) returns None on SUCCESS.
        # The old ``result is not None`` test therefore read a completed
        # write as a failure and fell through to a store that cannot write,
        # so the call reported False despite the row having landed.
        if local_store_call_via_daemon(method_name, **kwargs) is not PROXY_UNAVAILABLE:
            return True
    except Exception:
        pass
    try:
        from clawmetry import local_store
        store = local_store.get_store()
        if getattr(store, "_read_only", False):
            # _ProxyStore (daemon registered but its write no-ops) or an
            # explicit read-only LocalStore — nothing will persist.
            return False
        getattr(store, method_name)(**kwargs)
        return True
    except Exception:
        return False


def _rows(result) -> list:
    if isinstance(result, dict):
        result = result.get("result") or result.get("rows") or []
    return result if isinstance(result, list) else []


def _find_approval(approval_id: str):
    for r in _rows(_ls_read("query_approvals", limit=500)):
        if r.get("id") == approval_id:
            return r
    return None


# ── response helpers ───────────────────────────────────────────────────────

def _hso(decision: str, reason: str,
         updated_input: "dict | None" = None) -> dict:
    out = {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }
    if updated_input is not None:
        # Question-set answers (WO-52): allow + updatedInput = the original
        # tool_input plus the human's structured answers — the session
        # resumes as if they had been picked in the terminal.
        out["updatedInput"] = updated_input
    return {"hookSpecificOutput": out}


def _decided(decision: str, reason: str, approval_id: "str | None" = None,
             updated_input: "dict | None" = None):
    body = _hso(decision, reason, updated_input)
    body["status"] = "decided"
    if approval_id:
        body["approval_id"] = approval_id
    return jsonify(body)


def _audit(result: str, tool_name: str, meta: dict) -> None:
    try:
        from clawmetry import audit as _a
        _a.audit_event("approval.decision", actor="local", target=tool_name,
                       result=result, source="pretooluse-hook", metadata=meta)
    except Exception:
        pass


def _page_human(approval: dict) -> None:
    """Fan the parked approval out to this runtime's channels.

    Non-blocking (the delivering handler fans out on its own thread) and
    never raises: the human notification is an enhancement on top of a row
    that is already parked, so a broken webhook must not turn into a
    stalled agent. Nothing registered (no paid package) is not an error —
    the row is still in the queue and the Approvals tab still renders it.
    """
    try:
        from clawmetry import approval_events as _ae
        _ae.notify_pending(approval)
    except Exception:
        pass


def _map_on_timeout(on_timeout: str) -> str:
    ot = (on_timeout or "deny").strip().lower()
    if ot in ("deny", "kill", "denied", "block"):
        return "deny"
    if ot in ("allow", "approve", "approved"):
        return "allow"
    return "ask"


def _args_meta(row) -> dict:
    args = row.get("args")
    return args if isinstance(args, dict) else {}


# ── question-set approvals (WO-52 phase 1) ─────────────────────────────────
# Claude Code's AskUserQuestion tool is a question addressed to the human,
# so it never needs a protection rule to be worth mirroring: when the gate
# hook sees it, the question set is parked as an approval row the dashboard
# renders full-fidelity, and an "answer" decision resumes the session with
# the picked labels (hookSpecificOutput.updatedInput). Every failure mode —
# window elapsed, malformed payload, unreadable answers, store down — falls
# back to "ask" (the runtime's own terminal prompt). NEVER "deny" and NEVER
# a fabricated answer: the worst case must be exactly today's behaviour.

def _question_gate_enabled() -> bool:
    return os.environ.get("CLAWMETRY_QUESTION_GATE", "1").strip() != "0"


def _question_window_s() -> int:
    """How long the dashboard/phone gets before the terminal prompt takes
    over. Env override first, then the mirror window (same concept: a
    bounded head start for the remote surface), then 180 s."""
    raw = os.environ.get("CLAWMETRY_QUESTION_WINDOW_S", "").strip()
    if raw:
        try:
            return max(10, int(raw))
        except ValueError:
            pass
    try:
        from clawmetry import approval_events as _ae
        return int(_ae.mirror_window_s("claude_code"))
    except Exception:
        return 180


# ── the receiver ───────────────────────────────────────────────────────────

# URL slug -> the runtime name stamped on approval rows. Each gated runtime
# gets its OWN receiver URL so a Cursor pause is never filed as a
# claude_code approval (2026-08-19 matrix-gap sprint: cursor + copilot
# gates in clawmetry/runtime_gates.py reuse this whole engine).
_HOOK_RUNTIME_SLUGS = {
    "claude-code": "claude_code",
    "cursor": "cursor",
    "copilot": "copilot",
}


@bp_hooks.route("/api/hooks/claude-code/pretooluse", methods=["POST"])
def api_hook_claude_code_pretooluse():
    return _pretooluse_impl("claude_code")


@bp_hooks.route("/api/hooks/<slug>/pretooluse", methods=["POST"])
def api_hook_runtime_pretooluse(slug):
    runtime = _HOOK_RUNTIME_SLUGS.get(str(slug or "").lower())
    if not runtime:
        return jsonify({"error": "unknown hook runtime"}), 404
    return _pretooluse_impl(runtime)


def _pretooluse_impl(runtime: str):
    # Loopback-only: the hook always runs on this machine (the installer
    # embeds 127.0.0.1). A 0.0.0.0-bound dashboard must not take pre-tool
    # verdict requests off the wire.
    if request.remote_addr not in ("127.0.0.1", "::1", None):
        return jsonify({"error": "loopback only"}), 403

    body = request.get_json(silent=True) or {}
    tool_name = str(body.get("tool_name") or "").strip()
    tool_input = body.get("tool_input")
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    session_id = str(body.get("session_id") or "").strip()
    cwd = str(body.get("cwd") or "")[:300]
    tool_use_id = str(body.get("tool_use_id") or "").strip()
    resume_id = str(body.get("approval_id") or "").strip()

    # Entitlement: explicit allow (observable fail-open) instead of a 402
    # the fail-open client would render identically as "no opinion".
    try:
        from clawmetry import entitlements as _ent
        entitled = _ent.get_entitlement().allows_feature("approval_queue")
    except Exception:
        entitled = True
    if not entitled:
        return _decided("allow", "approval queue not entitled on this node "
                                 "— pre-tool gate inactive")

    # ── resume path: the row exists, just wait on it ─────────────────────
    if resume_id:
        row = _find_approval(resume_id)
        if row is None:
            # Row vanished (store reset?) — never block the agent on our
            # own bookkeeping.
            return _decided("allow", "approval row not found — proceeding "
                                     "(fail-open)", resume_id)
        return _wait_on_row(resume_id, row, tool_name)

    if not tool_name:
        return _decided("allow", "no tool_name in hook payload")

    # ── AskUserQuestion: question-set approval (WO-52 phase 1) ───────────
    # Intercepted BEFORE policy matching: the runtime is already asking its
    # human a structured question, so no protection rule is required for
    # the dashboard to be allowed to answer it.
    if tool_name == "AskUserQuestion" and _question_gate_enabled():
        return _park_question_set(runtime, session_id, cwd, tool_use_id,
                                  tool_input)

    # ── fresh call: policy match ─────────────────────────────────────────
    try:
        from clawmetry import approvals as ap
        # Runtime-scoped: a policy pinned to another runtime must not gate
        # this one (mirrors sync_runtime_gates, which installs each gate
        # from the same filtered set).
        policies = ap._policies_for_runtime(ap.load_policies(), runtime)
        policy = ap.match_policy(policies, tool_name, tool_input) \
            if policies else None
    except Exception as e:
        return _decided("allow", f"policy engine unavailable ({e}) — "
                                 "fail-open")
    if policy is None:
        return _decided("allow", "no matching policy")

    action = (policy.get("action") or "require_approval").strip()
    if action == "approve":
        return _decided("allow", f"always-allow rule '{policy['name']}' "
                                 "matched — no human round-trip needed")
    if action == "monitor":
        # Dry-run: record what WOULD have paused, never block.
        _ls_write("ingest_approval", approval={
            "id": uuid.uuid4().hex,
            "requestor_session_id": f"{runtime}:{session_id}" if session_id
                                    else None,
            "action": f"{tool_name}: "
                      f"{ap._extract_command(tool_name, tool_input)[:140]}",
            "args": {"source": "pretooluse-hook", "runtime": runtime,
                     "tool_input": tool_input},
            "status": "simulated",
            "decision_reason": f"monitor mode: policy '{policy['name']}' "
                               "would have paused this",
            "created_at": _utcnow(),
        })
        return _decided("allow", f"monitor-mode policy '{policy['name']}' "
                                 "matched (dry run — not blocked)")
    if action != "require_approval":
        return _decided("allow", f"policy action '{action}' does not gate")

    # Approve-and-remember: an earlier "approve for this session" decision
    # for this exact (session, tool, command) skips the human round-trip.
    try:
        if session_id and ap.check_session_allow(
                f"{runtime}:{session_id}", tool_name, tool_input):
            _audit("approved", tool_name, {"policy": policy.get("name"),
                                           "session_id": session_id,
                                           "session_allow": True})
            return _decided("allow", "approved earlier this session "
                                     "(remember-my-choice)")
    except Exception:
        pass

    # ── park a pending row in the local queue ────────────────────────────
    dupe = _find_pending_dupe(runtime, session_id, tool_name, tool_input,
                              tool_use_id)
    if dupe is not None:
        return _wait_on_row(str(dupe.get("id")), dupe, tool_name)

    approval_id = uuid.uuid4().hex
    now_ms = int(time.time() * 1000)
    timeout_s = int(policy.get("timeout") or 604800)
    cmd_preview = ""
    try:
        cmd_preview = ap._extract_command(tool_name, tool_input)[:140]
    except Exception:
        pass
    try:
        from clawmetry.tool_risk import classify_tool_call
        _risk = classify_tool_call(tool_name, tool_input)
        risk_meta = {"level": _risk["level"], "reasons": _risk["reasons"]}
    except Exception:
        risk_meta = None
    ok = _ls_write("ingest_approval", approval={
        "id": approval_id,
        "requestor_session_id": f"{runtime}:{session_id}" if session_id
                                else None,
        "action": f"{tool_name}: {cmd_preview}",
        # Meta rides in the args blob so resume requests are stateless:
        # the row itself knows its policy window and timeout action.
        "args": {
            "source": "pretooluse-hook",
            "runtime": runtime,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "cwd": cwd,
            "tool_use_id": tool_use_id or None,
            "input_hash": None if tool_use_id else _input_hash(tool_input),
            "policy": policy.get("name"),
            "timeout": timeout_s,
            "on_timeout": policy.get("on_timeout") or "deny",
            "deadline_ms": now_ms + timeout_s * 1000,
            "_cm_risk": risk_meta,
        },
        "status": "pending",
        "created_at": _utcnow(),
    })
    if not ok:
        return _decided("allow", "approval store unavailable — fail-open")
    _audit("pending", tool_name, {"approval_id": approval_id,
                                  "policy": policy.get("name"),
                                  "session_id": session_id,
                                  "command": cmd_preview})
    _page_human({"id": approval_id, "runtime": runtime,
                 "kind": "policy", "tool_name": tool_name,
                 "command": cmd_preview, "cwd": cwd,
                 "policy": policy.get("name"),
                 "requestor_session_id": session_id})
    row = _find_approval(approval_id) or {"status": "pending", "args": {
        "on_timeout": policy.get("on_timeout") or "deny",
        "deadline_ms": now_ms + timeout_s * 1000,
        "policy": policy.get("name"),
    }}
    return _wait_on_row(approval_id, row, tool_name)


def _find_pending_dupe(runtime: str, session_id: str, tool_name: str,
                       tool_input: dict, tool_use_id: str):
    """Existing pending row for this exact call, or None.

    Dedup: a client whose first POST timed out client-side retries without
    approval_id.  Primary key: tool_use_id.  Fallback (tool_use_id absent):
    (session_id, tool_name, md5(tool_input)) within a 30 s window.
    """
    if tool_use_id:
        for r in _rows(_ls_read("query_approvals", status="pending",
                                limit=100)):
            if _args_meta(r).get("tool_use_id") == tool_use_id:
                return r
        return None
    if session_id:
        ih = _input_hash(tool_input)
        req_sid = f"{runtime}:{session_id}"
        cutoff_ms = int(time.time() * 1000) - 30_000
        for r in _rows(_ls_read("query_approvals", status="pending",
                                limit=100)):
            m = _args_meta(r)
            if (m.get("tool_use_id") is None
                    and m.get("input_hash") == ih
                    and m.get("tool_name") == tool_name
                    and r.get("requestor_session_id") == req_sid):
                try:
                    import datetime as _dt
                    row_ms = int(_dt.datetime.fromisoformat(
                        (r.get("created_at") or "").replace("Z", "+00:00")
                    ).timestamp() * 1000)
                except Exception:
                    row_ms = 0
                if row_ms >= cutoff_ms:
                    return r
    return None


def _park_question_set(runtime: str, session_id: str, cwd: str,
                       tool_use_id: str, tool_input: dict):
    """Park an AskUserQuestion call as a question-set approval row and wait.

    The row carries the sanitized set in ``args["_cm_questions"]`` and
    ``on_timeout="ask"`` — a question that nobody answers in the window
    falls back to the runtime's own terminal prompt, NEVER the binary
    deny default, and NEVER a fabricated answer.
    """
    from clawmetry import question_sets as qsets
    questions = qsets.sanitize_question_set(tool_input)
    if questions is None:
        return _decided("ask", "AskUserQuestion payload not understood — "
                               "falling back to the terminal prompt")

    dupe = _find_pending_dupe(runtime, session_id, "AskUserQuestion",
                              tool_input, tool_use_id)
    if dupe is not None:
        return _wait_on_row(str(dupe.get("id")), dupe, "AskUserQuestion")

    approval_id = uuid.uuid4().hex
    now_ms = int(time.time() * 1000)
    window_s = _question_window_s()
    summary = qsets.question_summary(questions)
    ok = _ls_write("ingest_approval", approval={
        "id": approval_id,
        "requestor_session_id": f"{runtime}:{session_id}" if session_id
                                else None,
        "action": f"AskUserQuestion: {summary[:140]}",
        "args": {
            "source": "pretooluse-hook",
            "runtime": runtime,
            "kind": "question_set",
            "tool_name": "AskUserQuestion",
            "tool_input": tool_input,
            "cwd": cwd,
            "tool_use_id": tool_use_id or None,
            "input_hash": None if tool_use_id else _input_hash(tool_input),
            "policy": "AskUserQuestion",
            "timeout": window_s,
            "on_timeout": "ask",
            "deadline_ms": now_ms + window_s * 1000,
            "_cm_questions": questions,
        },
        "status": "pending",
        "created_at": _utcnow(),
    })
    if not ok:
        return _decided("ask", "approval store unavailable — falling back "
                               "to the terminal prompt")
    _audit("pending", "AskUserQuestion", {"approval_id": approval_id,
                                          "kind": "question_set",
                                          "session_id": session_id,
                                          "questions": len(questions)})
    _page_human({"id": approval_id, "runtime": runtime,
                 "kind": "question_set", "tool_name": "AskUserQuestion",
                 "command": summary[:140], "cwd": cwd,
                 "policy": "AskUserQuestion",
                 "requestor_session_id": session_id})
    row = _find_approval(approval_id) or {"status": "pending", "args": {
        "on_timeout": "ask",
        "deadline_ms": now_ms + window_s * 1000,
        "policy": "AskUserQuestion",
        "tool_input": tool_input,
        "_cm_questions": questions,
    }}
    return _wait_on_row(approval_id, row, "AskUserQuestion")


def _answered_reply(approval_id: str, row: dict, tool_name: str):
    """Turn an ``answered`` row into allow + updatedInput.

    Re-validates the stored answers against the stored set before replying;
    anything unreadable degrades to "ask" (the terminal prompt) — a broken
    answer must never become a fabricated one.
    """
    meta = _args_meta(row)
    try:
        from clawmetry import question_sets as qsets
        questions = meta.get("_cm_questions")
        answers = meta.get("_cm_answers")
        err = qsets.validate_answers(questions, answers)
        if err:
            raise ValueError(err)
        updated = qsets.merge_answers_into_input(
            meta.get("tool_input") or {}, answers)
    except Exception as e:
        _audit("answered:unreadable", tool_name,
               {"approval_id": approval_id, "error": str(e)[:200]})
        return _decided("ask", f"answers recorded but unreadable ({e}) — "
                               "falling back to the terminal prompt",
                        approval_id)
    _audit("answered", tool_name, {"approval_id": approval_id})
    return _decided(
        "allow",
        "Answered by the human via ClawMetry approvals — resuming with "
        "their answers.",
        approval_id, updated_input=updated)


def _wait_on_row(approval_id: str, row: dict, tool_name: str):
    """Poll the approvals row for up to one wait slice; final answer or
    ``pending``. All state is in the row — safe under concurrent calls
    (update_approval_decision only ever transitions pending → decided
    once)."""
    meta = _args_meta(row)
    on_timeout = str(meta.get("on_timeout") or "deny")
    policy_name = str(meta.get("policy") or "policy")
    try:
        deadline_ms = int(meta.get("deadline_ms") or 0)
    except (TypeError, ValueError):
        deadline_ms = 0
    if deadline_ms <= 0:
        # No recorded deadline (foreign row?) — one slice, then on_timeout.
        deadline_ms = int(time.time() * 1000) + int(_WAIT_SLICE_S * 1000)

    slice_end = time.time() + _WAIT_SLICE_S
    status = str(row.get("status") or "pending").strip()
    reason = row.get("decision_reason")
    is_question = bool(meta.get("_cm_questions"))
    while True:
        if status == "answered":
            # Question-set decision (WO-52): allow + updatedInput carrying
            # the human's structured answers.
            return _answered_reply(approval_id, row, tool_name)
        if status in ("approved", "auto_approved"):
            _audit("approved", tool_name, {"approval_id": approval_id,
                                           "policy": policy_name})
            return _decided(
                "allow",
                f"Approved by the human via ClawMetry approvals "
                f"(policy '{policy_name}')."
                + (f" Reason: {reason}" if reason else ""),
                approval_id)
        if status == "expired" and is_question:
            # A question that expired is NOT a refusal: hand the decision
            # back to the runtime's own prompt (never the binary deny).
            _audit("expired:ask", tool_name, {"approval_id": approval_id})
            return _decided("ask", "question-set approval expired with no "
                                   "answer — falling back to the terminal "
                                   "prompt", approval_id)
        if status in ("denied", "expired"):
            _audit("denied", tool_name, {"approval_id": approval_id,
                                         "policy": policy_name})
            return _decided(
                "deny",
                f"Denied via ClawMetry approvals (policy '{policy_name}'). "
                "The human declined this specific call — pick a different "
                "approach or ask them what they'd prefer."
                + (f" Reason: {reason}" if reason else ""),
                approval_id)
        if status == "timeout":
            break  # someone else already timed it out — map below

        now_ms = int(time.time() * 1000)
        if now_ms >= deadline_ms:
            # Policy window elapsed with no decision: apply on_timeout.
            # update_approval_decision is first-click-wins, so a racing
            # human click landing this instant keeps its result.
            decision_word = {"deny": "deny", "allow": "approve",
                             "ask": "timeout"}[_map_on_timeout(on_timeout)]
            _ls_write("update_approval_decision", approval_id=approval_id,
                      decision=decision_word, resolver="timeout",
                      reason=f"policy window elapsed; on_timeout="
                             f"{on_timeout}")
            break

        if time.time() >= slice_end:
            return jsonify({
                "status": "pending",
                "approval_id": approval_id,
                "retry_after_ms": 2000,
                "deadline_ms": deadline_ms,
            })

        time.sleep(min(_POLL_INTERVAL_S, max(0.05, slice_end - time.time())))
        fresh = _find_approval(approval_id)
        if fresh is not None:
            row = fresh
            status = str(row.get("status") or "pending").strip()
            reason = row.get("decision_reason")

    # timeout path — re-read in case the racing human click won the
    # first-click-wins transition (resolver != "timeout" means it did;
    # resolver == "timeout" is our own on_timeout write above).
    fresh = _find_approval(approval_id)
    final = str((fresh or {}).get("status") or "timeout").strip()
    if final == "answered" and (fresh or {}).get("resolver") != "timeout":
        return _answered_reply(approval_id, fresh or row, tool_name)
    if final in ("approved", "auto_approved") \
            and (fresh or {}).get("resolver") != "timeout":
        _audit("approved", tool_name, {"approval_id": approval_id,
                                       "policy": policy_name})
        return _decided("allow", f"Approved by the human via ClawMetry "
                                 f"approvals (policy '{policy_name}').",
                        approval_id)
    if final == "denied" and (fresh or {}).get("resolver") != "timeout":
        _audit("denied", tool_name, {"approval_id": approval_id,
                                     "policy": policy_name})
        return _decided("deny", f"Denied via ClawMetry approvals "
                                f"(policy '{policy_name}').", approval_id)
    mapped = _map_on_timeout(on_timeout)
    _audit(f"timeout:{mapped}", tool_name, {"approval_id": approval_id,
                                            "policy": policy_name,
                                            "on_timeout": on_timeout})
    if mapped == "deny":
        return _decided(
            "deny",
            f"ClawMetry approval timed out with no decision (policy "
            f"'{policy_name}', on_timeout: {on_timeout}). The human never "
            "saw or didn't reach it in time — worth asking them directly.",
            approval_id)
    if mapped == "allow":
        return _decided(
            "allow",
            f"ClawMetry approval timed out (policy '{policy_name}', "
            f"on_timeout: {on_timeout}) — proceeding per the policy's "
            "timeout action.", approval_id)
    return _decided(
        "ask",
        f"ClawMetry approval timed out (policy '{policy_name}') — falling "
        "back to Claude Code's own permission prompt.", approval_id)


# ── mirror receiver: Claude Code's OWN permission prompts ──────────────────
# PreToolUse gates the tools YOUR rules name. This one fires when Claude
# Code itself decides it needs the user — the case that actually stalls a
# session, because unblocking it means walking to the terminal (or ticking
# a box in /permissions). We park it like any other approval, page the
# phone, and answer with the human's tap.
#
# Answering "ask" is the safety valve, used whenever we can't do better
# (mirroring off, no answer in time, store unavailable): Claude Code then
# shows its normal prompt, i.e. exactly today's behaviour. Nothing this
# endpoint does can make a session MORE stuck than it already was.
#
# No double-parking with the PreToolUse gate: if that hook answered
# "allow"/"deny", Claude Code never reaches the permission stage, so this
# event doesn't fire. If it answered "ask" (or wasn't installed), this is
# the only gate in play.

def _hso_mirror(decision: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PermissionRequest",
                                   "decision": decision}}


def _attention_write_async(**kwargs) -> None:
    """Write attention state on a daemon thread, off the request path.

    NOT merely defensive. ``_ls_write`` goes through the daemon proxy, whose
    per-attempt timeouts are 5s then 9s — so a contended DuckDB could add up
    to fourteen seconds before this handler even reaches its first gate. On a
    permission hook that is fourteen seconds of an agent sitting still,
    waiting on a cosmetic badge. Nothing about showing a badge justifies
    delaying the decision the badge is describing.

    Fire and forget: the caller never waits, and a failure is invisible to
    the runtime by design.
    """
    import threading

    def _run():
        try:
            _ls_write(**kwargs)
        except Exception:
            pass

    try:
        threading.Thread(target=_run, daemon=True,
                         name="clawmetry-attention-write").start()
    except Exception:
        pass


def _mark_waiting(session_id: str, tool_name: str) -> None:
    """Flag a session as waiting on a human, with ``signal='hook'``.

    Ground truth: the runtime fired its permission hook, so we are not
    inferring. That matters downstream — the daemon's inference pass cannot
    see a permission dialog (it leaves no transcript event), and deliberately
    refuses to clear hook rows for that reason.

    Off-thread and silent on failure. This sits on the agent's critical path;
    a badge is never worth stalling a turn over.
    """
    if not session_id:
        return
    _attention_write_async(
        method_name="set_session_attention",
        session_id=f"claude_code:{session_id}",
        agent_type="claude_code",
        state="waiting_approval", signal="hook",
        tool=(tool_name or "")[:80])


def _clear_waiting(full_session_id: str) -> None:
    """The human answered — drop the badge. ``full_session_id`` is the
    already-prefixed id as stored (``claude_code:<uuid>``).

    Whatever sets a hook row owns clearing it; the daemon's inference pass
    deliberately will not. NOT called when we answer ``ask``: that hands the
    decision back to Claude Code's own prompt, so the human is still being
    asked and the badge is still true.
    """
    if not full_session_id:
        return
    _attention_write_async(method_name="clear_session_attention",
                           session_id=str(full_session_id),
                           agent_type="claude_code")


def _mirror_answer(decision: str, approval_id: "str | None" = None,
                   note: str = ""):
    body = _hso_mirror(decision)
    body["status"] = "decided"
    if approval_id:
        body["approval_id"] = approval_id
    if note:
        body["note"] = note
    return jsonify(body)


@bp_hooks.route("/api/hooks/claude-code/permissionrequest", methods=["POST"])
def api_hook_claude_code_permissionrequest():
    if request.remote_addr not in ("127.0.0.1", "::1", None):
        return jsonify({"error": "loopback only"}), 403

    body = request.get_json(silent=True) or {}
    tool_name = str(body.get("tool_name") or "").strip()
    tool_input = body.get("tool_input")
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    session_id = str(body.get("session_id") or "").strip()
    cwd = str(body.get("cwd") or "")[:300]
    tool_use_id = str(body.get("tool_use_id") or "").strip()
    resume_id = str(body.get("approval_id") or "").strip()

    # Stamp the "needs you" badge FIRST, before every gate below.
    #
    # The fact that this hook fired IS the ground truth that Claude Code has a
    # prompt open — true whether or not the operator turned mirroring on, and
    # whether or not this node is entitled to ANSWER the prompt. Being TOLD an
    # approval is waiting is the free half; answering it remotely is the paid
    # half (see the entitlement note below). Gating the badge on the paid
    # feature would hide the problem from exactly the users most likely to be
    # surprised by it.
    #
    # Deliberately best-effort and never in the request's failure path: an
    # agent must never stall because a badge could not be written.
    _mark_waiting(session_id, tool_name)

    # Answering a runtime's own permission prompt remotely is the Pro half
    # of approvals (Starter is TOLD an approval is waiting; Pro answers it
    # without walking back to the terminal). Unentitled → "ask", which is
    # that terminal prompt: the downgrade path is the pre-mirror behaviour,
    # never a call left hanging.
    try:
        from clawmetry import entitlements as _ent
        entitled = _ent.get_entitlement().allows_feature("approval_mirror")
    except Exception:
        entitled = True
    if not entitled:
        return _mirror_answer("ask", note="phone approvals not entitled")

    try:
        from clawmetry import approval_events as _ae
        if not _ae.mirror_wanted("claude_code"):
            # Also the answer with no paid package installed: nothing
            # registered → False → the runtime's own prompt, unchanged.
            return _mirror_answer("ask", note="mirroring is off")
        window_s = _ae.mirror_window_s("claude_code")
    except Exception:
        return _mirror_answer("ask", note="routing config unavailable")

    if resume_id:
        row = _find_approval(resume_id)
        if row is None:
            return _mirror_answer("ask", resume_id, "approval row vanished")
        return _wait_mirror(resume_id, row, tool_name)

    if not tool_name:
        return _mirror_answer("ask", note="no tool_name in hook payload")

    if tool_use_id:
        for r in _rows(_ls_read("query_approvals", status="pending",
                                limit=100)):
            if _args_meta(r).get("tool_use_id") == tool_use_id:
                return _wait_mirror(str(r.get("id")), r, tool_name)

    # Approve-and-remember: an earlier "approve for this session" decision
    # for this exact (session, tool, command) answers the runtime's own
    # prompt without paging the human again.
    try:
        from clawmetry import approvals as _ap_sa
        if session_id and _ap_sa.check_session_allow(
                f"claude_code:{session_id}", tool_name, tool_input):
            _audit("approved", tool_name, {"kind": "permission_prompt",
                                           "session_id": session_id,
                                           "session_allow": True})
            return _mirror_answer("allow",
                                  note="approved earlier this session "
                                       "(remember-my-choice)")
    except Exception:
        pass

    approval_id = uuid.uuid4().hex
    now_ms = int(time.time() * 1000)
    try:
        from clawmetry import approvals as ap
        cmd_preview = ap._extract_command(tool_name, tool_input)[:140]
    except Exception:
        cmd_preview = ""
    try:
        from clawmetry.tool_risk import classify_tool_call as _ctc
        _mr = _ctc(tool_name, tool_input)
        mirror_risk = {"level": _mr["level"], "reasons": _mr["reasons"]}
    except Exception:
        mirror_risk = None
    ok = _ls_write("ingest_approval", approval={
        "id": approval_id,
        "requestor_session_id": f"claude_code:{session_id}" if session_id
                                else None,
        "action": f"{tool_name}: {cmd_preview}",
        "args": {
            "_cm_risk": mirror_risk,
            "source": "permissionrequest-hook",
            "runtime": "claude_code",
            "kind": "permission_prompt",
            "tool_name": tool_name,
            "tool_input": tool_input,
            "cwd": cwd,
            "tool_use_id": tool_use_id or None,
            "policy": "Claude Code permission prompt",
            "timeout": window_s,
            "on_timeout": "ask",
            "deadline_ms": now_ms + window_s * 1000,
        },
        "status": "pending",
        "created_at": _utcnow(),
    })
    if not ok:
        return _mirror_answer("ask", note="approval store unavailable")
    _audit("pending", tool_name, {"approval_id": approval_id,
                                  "kind": "permission_prompt",
                                  "session_id": session_id,
                                  "command": cmd_preview})
    _page_human({"id": approval_id, "runtime": "claude_code",
                 "kind": "permission_prompt", "tool_name": tool_name,
                 "command": cmd_preview, "cwd": cwd,
                 "policy": "Claude Code permission prompt",
                 "requestor_session_id": session_id})
    row = _find_approval(approval_id) or {"status": "pending", "args": {
        "on_timeout": "ask", "deadline_ms": now_ms + window_s * 1000}}
    return _wait_mirror(approval_id, row, tool_name)


def _wait_mirror(approval_id: str, row: dict, tool_name: str):
    """One wait slice on a mirrored permission prompt.

    Same sliced-wait shape as _wait_on_row (one HTTP request never holds
    longer than _WAIT_SLICE_S), but the verdicts are PermissionRequest's:
    approve → allow, deny → deny, no answer in the window → ask, which
    hands the decision back to Claude Code's own prompt.
    """
    meta = _args_meta(row)
    try:
        deadline_ms = int(meta.get("deadline_ms") or 0)
    except (TypeError, ValueError):
        deadline_ms = 0
    if deadline_ms <= 0:
        deadline_ms = int(time.time() * 1000) + int(_WAIT_SLICE_S * 1000)

    slice_end = time.time() + _WAIT_SLICE_S
    status = str(row.get("status") or "pending").strip()
    while True:
        if status in ("approved", "auto_approved"):
            _audit("approved", tool_name, {"approval_id": approval_id,
                                           "kind": "permission_prompt"})
            # Decided — the prompt is closed, so the badge is no longer true.
            _clear_waiting(row.get("requestor_session_id") or "")
            return _mirror_answer("allow", approval_id)
        if status in ("denied", "expired"):
            _audit("denied", tool_name, {"approval_id": approval_id,
                                         "kind": "permission_prompt"})
            _clear_waiting(row.get("requestor_session_id") or "")
            return _mirror_answer("deny", approval_id)
        if status == "timeout":
            break

        if int(time.time() * 1000) >= deadline_ms:
            _ls_write("update_approval_decision", approval_id=approval_id,
                      decision="timeout", resolver="timeout",
                      reason="mirror window elapsed — handed back to Claude "
                             "Code's own permission prompt")
            break

        if time.time() >= slice_end:
            return jsonify({"status": "pending", "approval_id": approval_id,
                            "retry_after_ms": 2000,
                            "deadline_ms": deadline_ms})

        time.sleep(min(_POLL_INTERVAL_S, max(0.05, slice_end - time.time())))
        fresh = _find_approval(approval_id)
        if fresh is not None:
            row = fresh
            status = str(row.get("status") or "pending").strip()

    fresh = _find_approval(approval_id)
    final = str((fresh or {}).get("status") or "timeout").strip()
    if final in ("approved", "auto_approved") \
            and (fresh or {}).get("resolver") != "timeout":
        return _mirror_answer("allow", approval_id)
    if final == "denied" and (fresh or {}).get("resolver") != "timeout":
        return _mirror_answer("deny", approval_id)
    _audit("timeout:ask", tool_name, {"approval_id": approval_id,
                                      "kind": "permission_prompt"})
    return _mirror_answer("ask", approval_id,
                          "no answer in the mirror window")


# ── lifecycle intake (WO-61) ───────────────────────────────────────────────
#
# The seven observe-only Claude Code hooks (tool failures, subagent start
# and stop, permission denials, compactions, session start, instructions
# loaded) each map their payload to a typed event in the hook process
# (clawmetry/hooks_claude_code.py::map_lifecycle_event) and POST it here.
# This handler validates the shape, forwards the rows to the daemon (the
# only DuckDB writer) and answers 200 whatever happened: the hook is async
# on the runtime side, and a failed badge is never worth an agent's turn.
# Dedupe is the store's INSERT OR IGNORE on the deterministic event id.

_LIFECYCLE_TYPES = frozenset({
    "tool.failed", "subagent.started", "subagent.stopped",
    "permission.denied", "context.compacted", "session.started",
    "instructions.loaded",
})
_LIFECYCLE_MAX_EVENTS = 50


def _lifecycle_node_id() -> str:
    try:
        from clawmetry.hooks_claude_code import _node_id
        nid = _node_id()
        if nid:
            return nid
    except Exception:
        pass
    import socket
    return socket.gethostname() or "unknown"


def _clean_lifecycle_event(raw: dict) -> "dict | None":
    if not isinstance(raw, dict):
        return None
    etype = str(raw.get("event_type") or "").strip()
    sid = str(raw.get("session_id") or "").strip()
    eid = str(raw.get("id") or "").strip()
    if etype not in _LIFECYCLE_TYPES or not sid or not eid:
        return None
    data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    out = {
        "id": eid[:64],
        "session_id": sid[:200],
        "event_type": etype,
        "ts": str(raw.get("ts") or _utcnow())[:40],
        "data": data,
    }
    instr = raw.get("instructions")
    if etype == "instructions.loaded" and isinstance(instr, dict):
        content = instr.get("content")
        if isinstance(content, str):
            out["instructions"] = {
                "content": content,
                "sha256": str(instr.get("sha256") or "")[:64],
                "bytes": instr.get("bytes"),
                "truncated": bool(instr.get("truncated")),
            }
    return out


@bp_hooks.route("/api/hooks/claude-code/lifecycle", methods=["POST"])
def api_hook_claude_code_lifecycle():
    """Intake for the seven lifecycle hooks. Body: ``{"events": [...]}``.

    Loopback-only like every hook receiver. Always 200 with
    ``{ok, accepted, stored}``; ``stored`` reports whether the daemon write
    went through, because a hook wired against an older daemon whose proxy
    allowlist lacks the method would otherwise fail silently.
    """
    if request.remote_addr not in ("127.0.0.1", "::1", None):
        return jsonify({"ok": False, "error": "loopback only"}), 403
    try:
        body = request.get_json(silent=True) or {}
        raw_events = body.get("events") if isinstance(body, dict) else None
        if not isinstance(raw_events, list):
            return jsonify({"ok": False, "error": "events must be a list",
                            "accepted": 0, "stored": False}), 200
        events = []
        for raw in raw_events[:_LIFECYCLE_MAX_EVENTS]:
            ev = _clean_lifecycle_event(raw)
            if ev:
                events.append(ev)
        if not events:
            return jsonify({"ok": True, "accepted": 0, "stored": False}), 200
        node_id = _lifecycle_node_id()
        stored = _ls_write("ingest_lifecycle_events", events=events,
                           node_id=node_id, agent_type="claude_code")
        instr_ok = True
        for ev in events:
            info = ev.get("instructions")
            if not info:
                continue
            ok = _ls_write("upsert_session_instructions", row={
                "session_id": ev["session_id"],
                "instruction_path": str(ev["data"].get("instruction_path") or ""),
                "instruction_type": str(ev["data"].get("instruction_type") or ""),
                "load_reason": str(ev["data"].get("load_reason") or ""),
                "sha256": info.get("sha256") or "",
                "bytes": info.get("bytes"),
                "truncated": bool(info.get("truncated")),
                "content": info.get("content") or "",
                "loaded_at": ev["ts"],
            }, agent_type="claude_code")
            instr_ok = instr_ok and bool(ok)
        return jsonify({"ok": True, "accepted": len(events),
                        "stored": bool(stored) and instr_ok}), 200
    except Exception as e:  # noqa: BLE001
        log_warn = getattr(sys.stderr, "write", None)
        if log_warn:
            try:
                log_warn(f"lifecycle intake failed: {str(e)[:200]}\n")
            except Exception:
                pass
        return jsonify({"ok": False, "accepted": 0, "stored": False}), 200


@bp_hooks.route("/api/sessions/<session_id>/instructions", methods=["GET"])
def api_session_instructions(session_id):
    """The instructions files a session ran under, as the agent saw them:
    redacted, capped, and hashed. ``{session_id, instructions: [...]}``."""
    sid = str(session_id or "").strip()
    if not sid:
        return jsonify({"session_id": "", "instructions": []})
    rows = _ls_read("get_session_instructions", session_id=sid)
    rows = rows if isinstance(rows, list) else []
    return jsonify({"session_id": sid, "instructions": rows,
                    "cap_bytes": 32 * 1024})


@bp_hooks.route("/api/lifecycle/coverage", methods=["GET"])
def api_lifecycle_coverage():
    """Which lifecycle facts each runtime can put on the trail.

    ``?runtime=<id>`` narrows to one runtime and adds the ready-to-render
    ``lines``; without it every runtime is returned. The declaration lives
    in ``clawmetry/lifecycle_coverage.py`` and is the single source the
    local and hosted dashboards read.
    """
    from clawmetry import lifecycle_coverage as _lc
    rt = (request.args.get("runtime") or "").strip().lower()
    if rt:
        return jsonify(_lc.summarise(rt))
    return jsonify({"facts": list(_lc.FACTS), "labels": _lc.FACT_LABELS,
                    "event_types": _lc.EVENT_TYPES,
                    "runtimes": _lc.coverage_table()})


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
