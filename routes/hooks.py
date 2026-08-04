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
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
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

def _hso(decision: str, reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        },
    }


def _decided(decision: str, reason: str, approval_id: "str | None" = None):
    body = _hso(decision, reason)
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


# ── the receiver ───────────────────────────────────────────────────────────

@bp_hooks.route("/api/hooks/claude-code/pretooluse", methods=["POST"])
def api_hook_claude_code_pretooluse():
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

    # ── fresh call: policy match ─────────────────────────────────────────
    try:
        from clawmetry import approvals as ap
        policies = ap.load_policies()
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
            "requestor_session_id": f"claude_code:{session_id}" if session_id
                                    else None,
            "action": f"{tool_name}: "
                      f"{ap._extract_command(tool_name, tool_input)[:140]}",
            "args": {"source": "pretooluse-hook", "runtime": "claude_code",
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

    # ── park a pending row in the local queue ────────────────────────────
    # Dedup: a client whose first POST timed out client-side retries without
    # approval_id.  Primary key: tool_use_id.  Fallback (tool_use_id absent):
    # (session_id, tool_name, md5(tool_input)) within a 30 s window.
    if tool_use_id:
        for r in _rows(_ls_read("query_approvals", status="pending",
                                limit=100)):
            if _args_meta(r).get("tool_use_id") == tool_use_id:
                return _wait_on_row(str(r.get("id")), r, tool_name)
    elif session_id:
        ih = _input_hash(tool_input)
        req_sid = f"claude_code:{session_id}"
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
                    return _wait_on_row(str(r.get("id")), r, tool_name)

    approval_id = uuid.uuid4().hex
    now_ms = int(time.time() * 1000)
    timeout_s = int(policy.get("timeout") or 604800)
    cmd_preview = ""
    try:
        cmd_preview = ap._extract_command(tool_name, tool_input)[:140]
    except Exception:
        pass
    ok = _ls_write("ingest_approval", approval={
        "id": approval_id,
        "requestor_session_id": f"claude_code:{session_id}" if session_id
                                else None,
        "action": f"{tool_name}: {cmd_preview}",
        # Meta rides in the args blob so resume requests are stateless:
        # the row itself knows its policy window and timeout action.
        "args": {
            "source": "pretooluse-hook",
            "runtime": "claude_code",
            "tool_name": tool_name,
            "tool_input": tool_input,
            "cwd": cwd,
            "tool_use_id": tool_use_id or None,
            "input_hash": None if tool_use_id else _input_hash(tool_input),
            "policy": policy.get("name"),
            "timeout": timeout_s,
            "on_timeout": policy.get("on_timeout") or "deny",
            "deadline_ms": now_ms + timeout_s * 1000,
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
    row = _find_approval(approval_id) or {"status": "pending", "args": {
        "on_timeout": policy.get("on_timeout") or "deny",
        "deadline_ms": now_ms + timeout_s * 1000,
        "policy": policy.get("name"),
    }}
    return _wait_on_row(approval_id, row, tool_name)


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
    while True:
        if status in ("approved", "auto_approved"):
            _audit("approved", tool_name, {"approval_id": approval_id,
                                           "policy": policy_name})
            return _decided(
                "allow",
                f"Approved by the human via ClawMetry approvals "
                f"(policy '{policy_name}')."
                + (f" Reason: {reason}" if reason else ""),
                approval_id)
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


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
