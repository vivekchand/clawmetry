"""routes/policy.py — tool-policy + sandbox + exec-approval audit (PRD P1-1).

This is the governance surface (our moat): "which tools can run, where they
run, and what got blocked/approved and why."

Two read-only endpoints, both backed by DuckDB through the daemon proxy
(the daemon owns the writer lock) with a single-process direct-read fallback
— the same ``_ls_call`` pattern as ``routes/agents.py`` / ``routes/scheduler.py``:

  GET /api/tool-policy      — per-agent effective sandbox mode + tool
                              allow/deny, mirrored from
                              ``openclaw sandbox explain --json``
                              (``clawmetry/sync.py:sync_tool_policy``).
  GET /api/approvals-audit  — exec-approval decisions (approved / denied /
                              pending) from the approvals table, summarised
                              into a decision rollup + recent decisions feed.

Neither endpoint ever 500s on empty data: a fresh sync, an OpenClaw build
without ``sandbox explain``, or a daemon mid-restart all return empty lists so
the tab paints an honest "nothing recorded yet" state.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from clawmetry._gate import gate

bp_policy = Blueprint("policy", __name__)


def _ls_call(method_name: str, **kwargs):
    """Cross-process LocalStore call with single-process fallback (issue #1088)."""
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


def _coerce_rows(rows) -> list[dict]:
    """``local_store_via_daemon`` returns the raw method result (a list) or a
    ``{"result": [...]}`` / ``{"rows": [...]}`` envelope depending on transport
    — normalise both to a plain list."""
    if isinstance(rows, dict):
        rows = rows.get("result") or rows.get("rows") or []
    return rows if isinstance(rows, list) else []


def _arg_preview(args) -> str:
    """Short single-line preview of tool-call arguments — never the full body."""
    if args is None:
        return ""
    if isinstance(args, dict):
        for k in ("command", "cmd", "tool", "path", "url"):
            v = args.get(k)
            if v:
                return str(v)[:160]
        try:
            import json as _json
            return _json.dumps(args, separators=(",", ":"))[:160]
        except Exception:
            return str(args)[:160]
    return str(args)[:160]


@bp_policy.route("/api/tool-policy")
@gate("tool_policy")
def api_tool_policy():
    """Per-agent effective sandbox mode + tool allow/deny.

    Returns ``{agents:[...], summary:{...}, _source}``. Each agent row carries
    the sandbox mode (``off`` / ``non-main`` / ``all``), scope, workspace
    access, and the effective tool ``allow`` / ``deny`` lists with their
    config provenance (``sources``). The summary rolls up how many agents are
    sandboxed and the most-restricted mode seen, so the UI can show a
    one-glance governance posture chip.

    Query params: ``agent_id`` (filter to one agent), ``limit`` (<=100).
    """
    try:
        limit = max(1, min(100, int(request.args.get("limit", 50))))
    except (TypeError, ValueError):
        limit = 50
    agent_id = (request.args.get("agent_id") or "").strip() or None

    agents = _coerce_rows(_ls_call("query_tool_policy", agent_id=agent_id, limit=limit))

    # Governance posture rollup. ``mode`` ordering: all > non-main > off
    # (most → least restrictive). We surface the most-restrictive mode in use
    # plus how many agents run with a non-off sandbox.
    _MODE_RANK = {"all": 3, "non-main": 2, "nonmain": 2, "off": 1}
    sandboxed = 0
    strongest = None
    strongest_rank = 0
    total_allow = 0
    total_deny = 0
    for a in agents:
        mode = (a.get("sandbox_mode") or "off")
        if mode and mode != "off":
            sandboxed += 1
        rank = _MODE_RANK.get(str(mode), 0)
        if rank > strongest_rank:
            strongest_rank = rank
            strongest = mode
        total_allow += int(a.get("allow_count") or 0)
        total_deny += int(a.get("deny_count") or 0)

    summary = {
        "agent_count": len(agents),
        "sandboxed_agents": sandboxed,
        "strongest_mode": strongest or ("off" if agents else None),
        "total_allowed_tools": total_allow,
        "total_denied_tools": total_deny,
    }
    return jsonify({"agents": agents, "summary": summary, "_source": "local_store"})


@bp_policy.route("/api/approvals-audit")
@gate("approval_queue")
def api_approvals_audit():
    """Exec-approval decision audit — what got approved / denied / is pending.

    Returns ``{decisions:[...], summary:{...}, _source}``. Each decision row is
    a normalised slice of an approvals-table row (the heavy ``args`` BLOB is
    reduced to a short preview so the audit feed can't bloat). The summary
    counts pending / approved / denied so the UI can render a posture bar.

    Query params: ``status`` (filter), ``limit`` (<=300).
    """
    try:
        limit = max(1, min(300, int(request.args.get("limit", 100))))
    except (TypeError, ValueError):
        limit = 100
    status = (request.args.get("status") or "").strip() or None

    return jsonify(_approvals_audit_payload(status=status, limit=limit))


@bp_policy.route("/api/approvals")
@gate("approval_queue")
def api_approvals_queue():
    """Pending approvals queue — compact format for mobile/remote clients.

    Returns {approvals:[...], count:int, _source}. Each entry carries
    action_token (the id a remote client uses to POST an approve/deny decision
    to the cloud) plus a short args_preview so mobile UI can show context.

    Query params: limit (<=100, default 50).
    """
    try:
        limit = max(1, min(100, int(request.args.get("limit", 50))))
    except (TypeError, ValueError):
        limit = 50
    rows = _coerce_rows(_ls_call("query_approvals", status="pending", limit=limit))
    approvals = [
        {
            "id":                   r.get("id"),
            "action_token":         r.get("id"),
            "action":               r.get("action"),
            "status":               r.get("status") or "pending",
            "created_at":           r.get("created_at"),
            "requestor_session_id": r.get("requestor_session_id"),
            "args_preview":         _arg_preview(r.get("args")),
        }
        for r in rows
    ]
    return jsonify({"approvals": approvals, "count": len(approvals), "_source": "local_store"})


def _approvals_audit_payload(status=None, limit=100):
    """Exec-approval decision audit payload, shared by the HTTP route and the
    cloud snapshot builder (trial-bug #22: the Policy tab audit was blank on the
    hosted dashboard). Returns {decisions, summary, _source}."""
    rows = _coerce_rows(_ls_call("query_approvals", status=status, limit=limit))

    decisions = []
    pending = approved = denied = simulated = 0
    for r in rows:
        st = (r.get("status") or "pending")
        dec = (r.get("decision") or "")
        if st == "simulated":
            # Monitor-mode (dry-run) policies record what WOULD have paused.
            simulated += 1
        elif st == "pending":
            pending += 1
        elif st in ("approved", "allow", "allowed") or dec in ("approve", "allow"):
            approved += 1
        elif st in ("denied", "deny", "blocked", "rejected") or dec in ("deny", "block"):
            denied += 1
        decisions.append({
            "id": r.get("id"),
            "action": r.get("action"),
            "args_preview": _arg_preview(r.get("args")),
            "status": st,
            "decision": dec or None,
            "decision_reason": (str(r.get("decision_reason"))[:300]
                                if r.get("decision_reason") else None),
            "resolver": r.get("resolver"),
            "requestor_session_id": r.get("requestor_session_id"),
            "created_at": r.get("created_at"),
            "resolved_at": r.get("resolved_at"),
        })

    summary = {
        "total": len(decisions),
        "pending": pending,
        "approved": approved,
        "denied": denied,
        "simulated": simulated,
    }
    return {"decisions": decisions, "summary": summary, "_source": "local_store"}


def _policy_summary(compiled: dict) -> dict:
    """JSON-safe summary of one compiled policy (regexes → pattern strings)."""
    def _pat(rx):
        return getattr(rx, "pattern", None)
    return {
        "name": compiled.get("name"),
        "tool": compiled.get("tool"),
        "runtime": compiled.get("runtime") or "",
        "action": compiled.get("action"),
        "timeout": compiled.get("timeout"),
        "on_timeout": compiled.get("on_timeout"),
        "command_regex": _pat(compiled.get("command_regex")),
        "command_not_regex": _pat(compiled.get("command_not_regex")),
        "args_regex": _pat(compiled.get("args_regex")),
    }


_VALID_ACTIONS = ("require_approval", "approve", "monitor")
_VALID_ON_TIMEOUT = ("deny", "kill", "approve", "allow", "ask")
# Keys we serialise back to policies.yml (whitelist keeps junk out of the
# file). ``match`` is handled separately (nested block).
_POLICY_SCALAR_KEYS = ("name", "tool", "runtime", "pattern_type", "pattern",
                       "action", "timeout", "on_timeout", "preset_key",
                       "enabled")
_MATCH_SCALAR_KEYS = ("tool", "command_regex", "command_not_regex",
                      "args_regex", "runtime")


def _yaml_quote(value):
    """Serialise one scalar for the policies.yml subset. Returns the string
    to write, or raises ValueError for values the subset can't round-trip
    (newlines, or strings containing BOTH quote kinds)."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    s = str(value)
    if "\n" in s or "\r" in s:
        raise ValueError("newlines are not allowed in policy values")
    if "'" not in s:
        return f"'{s}'"
    if '"' not in s:
        return f'"{s}"'
    raise ValueError("a policy value may not contain both ' and \" quotes")


def _serialize_policies_yaml(policies: list[dict]) -> str:
    """Emit the exact YAML subset ``approvals._load_yaml`` documents (flat
    keys + one optional nested ``match`` block), so the file round-trips
    through BOTH the pyyaml path and the hand-rolled fallback parser."""
    lines: list[str] = [
        "# ClawMetry approval policies — managed by the Approvals tab.",
        "# Docs: README 'Approval policies'. Hand edits are preserved on",
        "# the next dashboard save only if they use this same flat format.",
    ]
    for p in policies:
        first = True
        for k in _POLICY_SCALAR_KEYS:
            if k not in p or p[k] is None:
                continue
            prefix = "- " if first else "  "
            lines.append(f"{prefix}{k}: {_yaml_quote(p[k])}")
            first = False
        match = p.get("match")
        if isinstance(match, dict) and match:
            if first:
                lines.append("- match:")
                first = False
            else:
                lines.append("  match:")
            for mk in _MATCH_SCALAR_KEYS:
                if mk in match and match[mk] is not None:
                    lines.append(f"    {mk}: {_yaml_quote(match[mk])}")
        if first:
            # Nothing serialisable — shouldn't happen post-validation.
            raise ValueError("policy has no serialisable fields")
    return "\n".join(lines) + "\n"


def _validate_policies(policies) -> "tuple[list[dict], list[str]]":
    """Validate a candidate policy list. Returns (normalised, errors)."""
    from clawmetry import approvals as ap
    errors: list[str] = []
    normalised: list[dict] = []
    if not isinstance(policies, list):
        return [], ["'policies' must be a list"]
    for i, p in enumerate(policies):
        label = f"policies[{i}]"
        if not isinstance(p, dict):
            errors.append(f"{label}: must be an object")
            continue
        if p.get("name"):
            label = f"policy '{p['name']}'"
        action = str(p.get("action") or "require_approval").strip()
        if action not in _VALID_ACTIONS:
            errors.append(f"{label}: action must be one of "
                          f"{', '.join(_VALID_ACTIONS)} (got '{action}')")
        on_timeout = str(p.get("on_timeout") or "deny").strip()
        if on_timeout not in _VALID_ON_TIMEOUT:
            errors.append(f"{label}: on_timeout must be one of "
                          f"{', '.join(_VALID_ON_TIMEOUT)} "
                          f"(got '{on_timeout}')")
        if p.get("timeout") is not None:
            try:
                if int(p["timeout"]) <= 0:
                    errors.append(f"{label}: timeout must be > 0 seconds")
            except (TypeError, ValueError):
                errors.append(f"{label}: timeout must be an integer "
                              "(seconds)")
        compiled = None
        try:
            compiled = ap._compile_policy(p)
        except Exception as e:
            errors.append(f"{label}: {e}")
        if compiled is None:
            errors.append(f"{label}: invalid policy (bad regex or shape)")
        # Serialisability check (quotes/newlines) before we promise a write.
        try:
            _serialize_policies_yaml([p])
        except ValueError as e:
            errors.append(f"{label}: {e}")
        normalised.append(p)
    return normalised, errors


@bp_policy.route("/api/approvals/policies", methods=["GET"])
@gate("approval_queue")
def api_approvals_policies_get():
    """The local approval-policy list (``~/.clawmetry/policies.yml``) as the
    Approvals tab consumes it: the raw rows plus a compiled summary (regex
    patterns as strings, defaults resolved) so the UI can render toggles
    without re-implementing the engine's parsing rules.

    Returns ``{policies: [...], compiled: [...], path, exists}``. A missing
    or unreadable file is an empty list, never a 500 — the daemon treats it
    the same way."""
    from clawmetry import approvals as ap
    path = ap.POLICIES_PATH
    raw_list: list[dict] = []
    exists = False
    try:
        if path.exists():
            exists = True
            for p in ap._load_yaml(path.read_text(errors="replace")):
                if isinstance(p, dict):
                    raw_list.append(p)
    except Exception:
        raw_list = []
    compiled = []
    for p in raw_list:
        c = ap._compile_policy(p)
        if c:
            compiled.append(_policy_summary(c))
    return jsonify({"policies": raw_list, "compiled": compiled,
                    "path": str(path), "exists": exists})


@bp_policy.route("/api/approvals/policies", methods=["PUT"])
@gate("approval_queue")
def api_approvals_policies_put():
    """Replace the local policy file with the submitted list, atomically,
    after validating EVERY row (action/on_timeout/timeout/regexes and
    YAML-subset serialisability). Any error → 400 with per-policy messages
    and NO write, so a fat-fingered regex can't silently disable the file's
    other rules.

    Body: ``{"policies": [ {name, tool, pattern_type, pattern, action,
    timeout, on_timeout, runtime?, preset_key?, match?{...}}, ... ]}``.
    The daemon's watcher re-reads the file every iteration (~2 s), so a
    successful PUT is live within seconds — including pre-tool gate
    install/removal via ``approvals.sync_runtime_gates``.

    Returns ``{ok, count, compiled}`` (the same compiled summary shape as
    GET, post-write ground truth)."""
    from clawmetry import approvals as ap
    body = request.get_json(silent=True) or {}
    if "policies" not in body:
        return jsonify({"ok": False,
                        "error": "body must include 'policies' (list)"}), 400
    normalised, errors = _validate_policies(body.get("policies"))
    if errors:
        return jsonify({"ok": False, "error": "validation failed",
                        "errors": errors}), 400

    text = _serialize_policies_yaml(normalised) if normalised else (
        "# ClawMetry approval policies — none configured.\n")
    path = ap.POLICIES_PATH
    try:
        import os as _os
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text)
        _os.replace(tmp, path)
    except Exception as e:
        return jsonify({"ok": False, "error": f"write failed: {e}"}), 500

    # Post-write ground truth: parse + compile what actually landed.
    compiled = []
    try:
        for p in ap._load_yaml(path.read_text(errors="replace")):
            if isinstance(p, dict):
                c = ap._compile_policy(p)
                if c:
                    compiled.append(_policy_summary(c))
    except Exception:
        pass
    try:
        from clawmetry import audit as _audit
        _audit.audit_event("approvals.policies_updated", actor="local",
                           target=str(path), result="ok", source="dashboard",
                           metadata={"count": len(normalised)})
    except Exception:
        pass
    return jsonify({"ok": True, "count": len(normalised),
                    "compiled": compiled, "path": str(path)})


@bp_policy.route("/api/policy/replay", methods=["POST"])
def api_policy_replay():
    """Replay a CANDIDATE approval policy over recent tool-call history.

    The "eval before you enable" loop: before saving a rule, see what it
    would have paused over the last N days, across every runtime. Nothing is
    created, blocked, or sent to the cloud; this is a pure read.

    Body: ``{policy: {...}, days: int (default 14, max 30),
             limit: int (default 5000, max 10000)}``
    ``policy`` uses the same shape as ``~/.clawmetry/policies.yml`` rows or
    cloud-builder rows (``tool`` / ``match.command_regex`` / ...).

    Returns the ``clawmetry.approvals.replay_policy`` payload plus
    ``days`` + ``since``. Invalid input returns 400 with ``{ok: False}``;
    an empty store returns an honest all-zeros payload, never a 500.
    """
    body = request.get_json(silent=True) or {}
    policy = body.get("policy")
    if not isinstance(policy, dict) or not policy:
        return jsonify({"ok": False,
                        "error": "body must include a 'policy' object"}), 400
    try:
        days = max(1, min(30, int(body.get("days", 14))))
    except (TypeError, ValueError):
        days = 14
    try:
        limit = max(100, min(10000, int(body.get("limit", 5000))))
    except (TypeError, ValueError):
        limit = 5000

    import time as _time
    since = _time.strftime("%Y-%m-%dT%H:%M:%SZ",
                           _time.gmtime(_time.time() - days * 86400))
    # Same merged-event_type read as the live watcher: import the SHARED
    # list from approvals so replay and enforcement cannot drift (a replay
    # that scans different event types than the watcher would "predict"
    # pauses the watcher never fires, or miss ones it does).
    try:
        from clawmetry.approvals import replay_policy, _TOOL_EVENT_TYPES
    except Exception as e:
        return jsonify({"ok": False, "error": f"approvals engine unavailable: {e}"}), 500
    rows: list[dict] = []
    for et in _TOOL_EVENT_TYPES:
        rows.extend(_coerce_rows(
            _ls_call("query_events", event_type=et, since=since, limit=limit)))

    try:
        result = replay_policy(policy, rows)
    except Exception as e:
        result = {"ok": False, "error": f"replay failed: {e}"}
    result["days"] = days
    result["since"] = since
    return jsonify(result), (200 if result.get("ok") else 400)


@bp_policy.route("/api/approvals/<approval_id>/decide", methods=["POST"])
@gate("approval_queue")
def api_approval_decide(approval_id: str):
    """Local decision writer for the pending approvals queue.

    Body: ``{"decision": "approve"|"deny", "reason": "optional string"}``.
    Flips the row's ``status`` (approved / denied) via
    ``update_approval_decision`` and stamps ``resolver="local"``. Returns
    ``{"ok": True, "status": <new_status>}``. Unknown id → 404. Already-
    decided row → 200 with the existing status (idempotent — matches the
    store method's "first click wins" semantics so a double-click never
    overwrites the first decision).

    Wakes the LOCAL blocking watcher (``approvals._poll_decision_local``,
    3 s poll) so a denied session is killed within ~3 s of the click, not
    at the next policy timeout.

    No auth wall — dashboard routes here are cookie-gated at the reverse-
    proxy / bind-loopback layer, matching ``GET /api/approvals`` and
    ``GET /api/approvals-audit``. The ``@gate("approval_queue")`` decorator
    keeps unlicensed enforced OSS nodes from silently using a paid feature
    (grace mode preserves today's behaviour for free users)."""
    body = request.get_json(silent=True) or {}
    decision = str(body.get("decision") or "").strip().lower()
    if decision not in ("approve", "deny"):
        return jsonify({
            "ok":    False,
            "error": "decision must be 'approve' or 'deny'",
        }), 400
    reason = body.get("reason")
    if reason is not None:
        reason = str(reason)[:300]

    aid = (approval_id or "").strip()
    if not aid:
        return jsonify({"ok": False, "error": "missing approval id"}), 404

    # Read current status so we can 404 on unknown id (the store method
    # returns 0 both on "unknown" and "already decided" — those are
    # semantically different for a REST decide endpoint).
    rows = _coerce_rows(_ls_call("query_approvals", limit=500))
    row = next((r for r in rows if r.get("id") == aid), None)
    if row is None:
        return jsonify({"ok": False, "error": "unknown approval id"}), 404
    existing = str(row.get("status") or "pending").strip()
    if existing in ("approved", "denied", "timeout", "expired"):
        # Already decided — return the frozen status (idempotent). This is
        # the same "first click wins" the store method enforces.
        return jsonify({"ok": True, "status": existing, "already": True})

    # Flip the row. Prefer the daemon proxy (owns the DuckDB writer lock
    # — same pattern the cloud-relay decision path uses); fall back to a
    # direct writable open when the daemon isn't running (tests, dev
    # mode). ``_ls_call``'s read_only=True fallback is NOT usable here
    # because update_approval_decision needs the writer.
    wrote = None
    try:
        from routes.local_query import local_store_via_daemon
        wrote = local_store_via_daemon(
            "update_approval_decision",
            approval_id=aid, decision=decision,
            resolver="local", reason=reason,
        )
    except Exception:
        wrote = None
    if wrote is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store()
            store.update_approval_decision(aid, decision, "local", reason)
        except Exception as e:
            return jsonify({"ok": False,
                            "error": f"decision write failed: {e}"}), 500

    new_status = "approved" if decision == "approve" else "denied"
    return jsonify({"ok": True, "status": new_status})
