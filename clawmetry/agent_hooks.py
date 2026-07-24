"""clawmetry/agent_hooks.py — pre-execution permission gate for coding agents.

Wires ClawMetry into Claude Code's hook system so risky tool calls are
checked BEFORE they run: safe steps auto-run, risky ones escalate to the
operator's phone/Slack (via clawmetry/questions.py), and the kill switch
denies everything until released. Close the laptop; the agent still
reaches you.

    clawmetry hooks setup     # wire PreToolUse / Notification / Stop hooks
    clawmetry hooks doctor    # verify the installation end to end
    clawmetry hooks clean     # remove everything setup added
    clawmetry hooks mode …    # push_only | push_first | terminal_only | notify_only
    clawmetry hooks wait 45   # blocking-wait ladder (seconds)
    clawmetry hooks stats     # approval moments by outcome

Fail-safe contract: if the gate cannot run (store down, config missing,
any exception) the decision falls back to the agent's own permission
prompt — never a silent allow. Secrets are redacted before anything is
sent to a phone or stored.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

_CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
_HOOK_MARKER = "clawmetry hook"  # identifies entries we own in settings.json

# ── Risky-command detection ──────────────────────────────────────────────
# Category → compiled patterns. A gated category escalates to the operator
# (per delivery mode); everything else passes through to the agent's own
# permission flow untouched.

RISKY_CATEGORIES: dict[str, list[re.Pattern]] = {
    "file_deletion": [
        re.compile(r"\brm\s+(-[a-zA-Z]*[rf][a-zA-Z]*\s+|-[a-zA-Z]*\s+-[a-zA-Z]*[rf])"),
        re.compile(r"\brm\s+-rf\b"),
        re.compile(r"\bshred\b|\bunlink\b"),
        re.compile(r"\bfind\b.*-delete\b"),
    ],
    "git_history": [
        re.compile(r"\bgit\s+push\s+.*(--force\b|-f\b|--force-with-lease)"),
        re.compile(r"\bgit\s+reset\s+--hard\b"),
        re.compile(r"\bgit\s+(rebase|filter-branch|filter-repo)\b"),
        re.compile(r"\bgit\s+branch\s+-[dD]\b"),
        re.compile(r"\bgit\s+clean\s+-[a-z]*f"),
    ],
    "database": [
        re.compile(r"(?i)\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX)\b"),
        re.compile(r"(?i)\bTRUNCATE\s+(TABLE\s+)?\w+"),
        re.compile(r"(?i)\bDELETE\s+FROM\b"),
        re.compile(r"(?i)\b(migrate|migration)s?\b.*\b(down|rollback|reset)\b"),
    ],
    "deployment": [
        re.compile(r"\b(deploy|kubectl\s+(apply|delete)|terraform\s+(apply|destroy)|helm\s+(install|upgrade|delete))\b"),
        re.compile(r"\b(npm|yarn|pnpm)\s+publish\b|\btwine\s+upload\b|\bgem\s+push\b|\bcargo\s+publish\b"),
        re.compile(r"\bgcloud\s+.*\bdeploy\b|\baws\s+.*\b(deploy|delete)\b|\bflyctl\s+deploy\b|\bvercel\s+(--prod|deploy)\b"),
    ],
    "system_admin": [
        re.compile(r"\b(systemctl|service)\s+(stop|restart|disable|mask)\b"),
        re.compile(r"\b(apt(-get)?|yum|dnf|brew)\s+(remove|purge|uninstall)\b"),
        re.compile(r"\blaunchctl\s+(unload|remove|bootout)\b"),
        re.compile(r"\bchmod\s+([0-7]*7[0-7]*\s+/|-R)\b|\bchown\s+-R\b.*\s/"),
        re.compile(r"\bmkfs\b|\bdd\s+.*of=/dev/"),
    ],
    "network_config": [
        re.compile(r"\b(iptables|ufw|firewall-cmd|pfctl)\b"),
        re.compile(r"\b(ifconfig|ip)\s+.*\b(down|del)\b"),
        re.compile(r"\bnetworksetup\b.*-set"),
    ],
    "spending": [
        re.compile(r"(?i)\bstripe\b.*\b(charge|payment|refund)\b"),
        re.compile(r"\baws\s+ec2\s+run-instances\b|\bgcloud\s+compute\s+instances\s+create\b"),
    ],
}

# Proven read-only commands: never worth an interruption, whatever the mode.
_READ_ONLY_RE = re.compile(
    r"^\s*(ls|cat|head|tail|pwd|whoami|date|echo|env|printenv|which|file|stat|wc|du|df"
    r"|git\s+(status|log|diff|show|branch\s*$|remote\s+-v)"
    r"|grep|rg|find(?!.*-delete)|fd|tree)\b[^|;&>]*$"
)

# Tools that never execute anything — pass straight through.
_SAFE_TOOLS = frozenset({
    "read", "glob", "grep", "ls", "websearch", "webfetch", "web_search",
    "web_fetch", "notebookread", "todoread", "todowrite", "taskget",
    "tasklist",
})


def classify_command(tool_name: str, tool_input: dict) -> Optional[str]:
    """Return the risky category for this tool call, or None if benign."""
    from clawmetry.approvals import _canonical_tool, _extract_command
    tname = (tool_name or "").strip().lower()
    if tname in _SAFE_TOOLS:
        return None
    cmd = _extract_command(tool_name, tool_input if isinstance(tool_input, dict) else {})
    if not cmd:
        return None
    if _canonical_tool(tool_name) == "exec" and _READ_ONLY_RE.match(cmd):
        return None
    for category, patterns in RISKY_CATEGORIES.items():
        for pat in patterns:
            if pat.search(cmd):
                return category
    return None


# ── Gate evaluation ──────────────────────────────────────────────────────


def evaluate_gate(
    tool_name: str,
    tool_input: dict,
    session_id: str = "",
    cwd: str = "",
) -> dict[str, Any]:
    """Decide what happens to one tool call.

    Returns ``{"decision": "allow"|"deny"|"ask"|"pass", "reason": str}``.
    ``pass`` means "no opinion — the agent's normal permission flow
    continues" (the fail-safe default: nothing is ever silently allowed).
    """
    from clawmetry import questions as _q
    from clawmetry.approvals import (
        _extract_command, load_policies, match_policy,
    )

    # 1. Kill switch — denies everything gated, even auto-approvables.
    if _q.killswitch_active(session_id):
        return {"decision": "deny",
                "reason": "ClawMetry kill switch is engaged — release it "
                          "from the Approvals tab or: clawmetry hooks killswitch off"}

    # 2. Explicit operator policies win over built-in risk detection.
    policy = None
    try:
        policy = match_policy(load_policies(), tool_name,
                              tool_input if isinstance(tool_input, dict) else {})
    except Exception:
        policy = None
    category = classify_command(tool_name, tool_input)
    action = (policy or {}).get("action") or ""
    if action in ("allow", "auto_approve"):
        return {"decision": "allow", "reason": f"policy '{policy['name']}' auto-approves"}
    if action in ("deny", "block"):
        return {"decision": "deny", "reason": f"policy '{policy['name']}' blocks this"}
    if action == "monitor":
        # Dry-run: record, notify, never block.
        _notify_risky(tool_name, tool_input, category or "policy_monitor",
                      session_id, blocking=False)
        return {"decision": "pass", "reason": "policy monitor (dry-run)"}
    escalate = bool(policy) or category is not None
    if not escalate:
        return {"decision": "pass", "reason": "not gated"}

    # 3. Escalation — route by delivery mode.
    mode = _q.load_mode()["mode"]
    cfg = _q.load_channels_config()
    label = category or f"policy '{(policy or {}).get('name', '')}'"
    if mode == "terminal_only":
        return {"decision": "ask",
                "reason": f"ClawMetry gate: {label} requires approval (terminal mode)"}
    if mode == "notify_only":
        _notify_risky(tool_name, tool_input, label, session_id, blocking=False)
        return {"decision": "pass", "reason": f"{label}: notified (notify-only mode)"}

    # push_only / push_first — ask the phone and block.
    cmd = _q.redact_secrets(
        _extract_command(tool_name, tool_input if isinstance(tool_input, dict) else {}))[:300]
    timeout_s = float((policy or {}).get("timeout") or cfg.get("wait_seconds") or 45)
    try:
        result = _q.ask_blocking(
            question=f"Approve {tool_name}: {cmd}?",
            qtype="confirm",
            context=f"Gated ({label})" + (f" in {cwd}" if cwd else ""),
            agent_name=_agent_label(cwd),
            session_id=session_id,
            source="hook",
            timeout_s=timeout_s,
        )
    except Exception as exc:
        # Fail safe: fall back to the agent's own prompt, never silent-allow.
        return {"decision": "ask",
                "reason": f"ClawMetry gate unavailable ({exc}) — approve in terminal"}
    if result.get("answered"):
        if result.get("value") == "yes":
            return {"decision": "allow", "reason": f"approved from phone ({label})"}
        return {"decision": "deny", "reason": f"denied from phone ({label})"}

    # Unanswered — per policy/config.
    on_timeout = (policy or {}).get("on_timeout") or ""
    unanswered = on_timeout if on_timeout in ("deny", "wait", "terminal") \
        else ("terminal" if mode == "push_first" else cfg.get("unanswered", "deny"))
    if unanswered == "wait":
        # Hold for the phone until the question itself expires.
        expiry = float(cfg.get("expiry_seconds") or 600)
        qid = result.get("correlationId") or ""
        if qid:
            late = _q.wait_for_answer(qid, timeout_s=max(0.0, expiry - timeout_s))
            if late.get("answered"):
                if late.get("value") == "yes":
                    return {"decision": "allow", "reason": f"approved from phone ({label})"}
                return {"decision": "deny", "reason": f"denied from phone ({label})"}
        unanswered = "deny"
    if unanswered == "terminal":
        return {"decision": "ask",
                "reason": f"no phone answer in {int(timeout_s)}s — approve in terminal"}
    return {"decision": "deny",
            "reason": f"no answer in {int(timeout_s)}s — denied by timeout "
                      f"(fail closed). Nothing runs unapproved."}


def _agent_label(cwd: str) -> str:
    project = Path(cwd).name if cwd else ""
    return f"Claude Code - {project}" if project else "Claude Code"


def _notify_risky(tool_name: str, tool_input: dict, label: str,
                  session_id: str, blocking: bool) -> None:
    try:
        from clawmetry import questions as _q
        from clawmetry.approvals import _extract_command
        cmd = _q.redact_secrets(_extract_command(
            tool_name, tool_input if isinstance(tool_input, dict) else {}))[:200]
        _q.notify_channels(
            f"Gated action ran ({label})",
            f"{tool_name}: {cmd}" + (f"\nsession {session_id[:8]}" if session_id else ""),
        )
    except Exception:
        pass


# ── Hook entry points (invoked by the agent, JSON on stdin/stdout) ───────


def run_pretooluse_hook() -> int:
    """Claude Code PreToolUse hook: gate one tool call.

    Reads the hook payload from stdin, writes a permissionDecision to
    stdout. Any internal failure emits no decision at all, which leaves
    Claude Code's native permission flow in charge (fail safe)."""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        return 0
    tool_name = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    session_id = payload.get("session_id") or ""
    cwd = payload.get("cwd") or ""
    try:
        verdict = evaluate_gate(tool_name, tool_input,
                                session_id=session_id, cwd=cwd)
    except Exception:
        return 0  # no output → agent's own permission flow decides
    if verdict["decision"] == "pass":
        return 0
    decision = verdict["decision"]
    if decision not in ("allow", "deny", "ask"):
        return 0
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": verdict.get("reason") or "",
        }
    }, sys.stdout)
    return 0


def run_notification_hook() -> int:
    """Claude Code Notification hook: forward the agent's own permission
    prompts / idle notices to the operator's channels."""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        return 0
    message = payload.get("message") or "Claude Code needs your attention"
    try:
        from clawmetry import questions as _q
        _q.notify_channels(_agent_label(payload.get("cwd") or ""), str(message)[:400])
    except Exception:
        pass
    return 0


def run_stop_hook() -> int:
    """Claude Code Stop hook: push 'agent finished' so the operator can
    walk away and still know when the work is done."""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        return 0
    if payload.get("stop_hook_active"):
        return 0  # avoid loops when a stop hook already continued the agent
    try:
        from clawmetry import questions as _q
        session = (payload.get("session_id") or "")[:8]
        _q.notify_channels(
            _agent_label(payload.get("cwd") or ""),
            f"Agent finished{' (session ' + session + ')' if session else ''}. "
            "Open ClawMetry for the full trace.",
        )
    except Exception:
        pass
    return 0


# ── Setup / doctor / clean ───────────────────────────────────────────────

_HOOK_EVENTS = {
    "PreToolUse": {"matcher": "*", "command": "clawmetry hook pretooluse", "timeout": 660},
    "Notification": {"matcher": "", "command": "clawmetry hook notification", "timeout": 30},
    "Stop": {"matcher": "", "command": "clawmetry hook stop", "timeout": 30},
}


def _load_settings() -> dict:
    try:
        return json.loads(_CLAUDE_SETTINGS.read_text())
    except (FileNotFoundError, OSError, ValueError):
        return {}


def _our_entry(event: str) -> dict:
    spec = _HOOK_EVENTS[event]
    entry: dict[str, Any] = {
        "hooks": [{"type": "command", "command": spec["command"],
                   "timeout": spec["timeout"]}],
    }
    if spec["matcher"]:
        entry["matcher"] = spec["matcher"]
    return entry


def setup_hooks(events: Optional[list[str]] = None, quiet: bool = False) -> dict:
    """Idempotently install our hook entries into ~/.claude/settings.json."""
    events = events or list(_HOOK_EVENTS)
    settings = _load_settings()
    hooks = settings.setdefault("hooks", {})
    added: list[str] = []
    for event in events:
        if event not in _HOOK_EVENTS:
            continue
        entries = hooks.setdefault(event, [])
        already = any(
            _HOOK_MARKER in json.dumps(e) for e in entries if isinstance(e, dict))
        if not already:
            entries.append(_our_entry(event))
            added.append(event)
    if added:
        _CLAUDE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        _CLAUDE_SETTINGS.write_text(json.dumps(settings, indent=2))
    if not quiet:
        for e in added:
            print(f"  ✓ {e} hook installed")
        for e in set(events) - set(added):
            if e in _HOOK_EVENTS:
                print(f"  ✓ {e} hook already installed")
    return {"added": added, "settings_path": str(_CLAUDE_SETTINGS)}


def clean_hooks(quiet: bool = False) -> dict:
    """Remove every hook entry setup added. Leaves other hooks untouched."""
    settings = _load_settings()
    hooks = settings.get("hooks") or {}
    removed = 0
    for event, entries in list(hooks.items()):
        if not isinstance(entries, list):
            continue
        kept = [e for e in entries
                if not (isinstance(e, dict) and _HOOK_MARKER in json.dumps(e))]
        removed += len(entries) - len(kept)
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event, None)
    if removed:
        _CLAUDE_SETTINGS.write_text(json.dumps(settings, indent=2))
    if not quiet:
        print(f"  removed {removed} ClawMetry hook entr{'y' if removed == 1 else 'ies'}")
    return {"removed": removed}


def doctor() -> int:
    """Verify the whole chain: hooks installed → channels configured →
    store reachable → test push delivered."""
    from clawmetry import questions as _q
    ok = True
    settings = _load_settings()
    hooks = settings.get("hooks") or {}
    for event in _HOOK_EVENTS:
        installed = any(
            _HOOK_MARKER in json.dumps(e)
            for e in (hooks.get(event) or []) if isinstance(e, dict))
        print(f"  {'✓' if installed else '✗'} {event} hook "
              f"{'installed' if installed else 'missing — run: clawmetry hooks setup'}")
        ok = ok and installed
    cfg = _q.load_channels_config()
    channels = [name for name, key in
                (("ntfy", "ntfy_topic"), ("pushover", "pushover_token"),
                 ("slack", "slack_webhook_url"), ("webhook", "webhook_url"))
                if cfg.get(key)]
    if channels:
        print(f"  ✓ channels configured: {', '.join(channels)}")
    else:
        print("  ✗ no delivery channels configured — set one in the "
              "Approvals tab or POST /api/questions/channels")
        ok = False
    mode = _q.load_mode()
    print(f"  ✓ delivery mode: {mode['mode']}"
          + (" (temporary override)" if mode.get("override") else ""))
    store_ok = _q._store_call("query_questions", limit=1) is not None
    print(f"  {'✓' if store_ok else '✗'} question store "
          f"{'reachable' if store_ok else 'unreachable — is the daemon running? (clawmetry sync)'}")
    ok = ok and store_ok
    if channels:
        sent = _q.notify_channels("ClawMetry doctor",
                                  "Hook installation verified — you will "
                                  "get agent questions here.")
        print(f"  {'✓' if sent else '✗'} test notification "
              f"{'delivered to ' + ', '.join(sent) if sent else 'failed on every channel'}")
        ok = ok and bool(sent)
    print("\n" + ("All good — close the laptop, the agent can still reach you."
                  if ok else "Fix the ✗ items above, then re-run: clawmetry hooks doctor"))
    return 0 if ok else 1


def stats() -> int:
    """Approval-moment counts by outcome (the audit-trail rollup)."""
    from clawmetry import questions as _q
    rows = _q.list_questions(limit=500)
    if not rows:
        print("  no agent questions recorded yet")
        return 0
    by_status: dict[str, int] = {}
    latencies: list[int] = []
    for r in rows:
        by_status[r.get("status") or "unknown"] = \
            by_status.get(r.get("status") or "unknown", 0) + 1
        if r.get("latency_ms") is not None:
            try:
                latencies.append(int(r["latency_ms"]))
            except (TypeError, ValueError):
                pass
    print(f"  questions: {len(rows)}")
    for status, n in sorted(by_status.items(), key=lambda kv: -kv[1]):
        print(f"    {status:<10} {n}")
    if latencies:
        latencies.sort()
        median = latencies[len(latencies) // 2]
        print(f"  median answer latency: {median / 1000.0:.1f}s")
    ks = _q.killswitch_state()
    if ks.get("engaged") or ks.get("sessions"):
        print(f"  kill switch: ENGAGED "
              f"({'global' if ks.get('engaged') else ''}"
              f"{', ' if ks.get('engaged') and ks.get('sessions') else ''}"
              f"{len(ks.get('sessions') or {})} session(s))")
    return 0


def parse_duration(text: str) -> Optional[int]:
    """'30m' → 1800, '2h' → 7200, '45' → 45 (seconds). None on bad input."""
    m = re.fullmatch(r"(\d+)([smhd]?)", (text or "").strip())
    if not m:
        return None
    n = int(m.group(1))
    return n * {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(2)]
