"""Claude Code hooks → ClawMetry: pre-execution approval gate + phone pushes.

The gap (claims-audit 2026-07-17, approvals.py:1337 admission): for family
runtimes we could only detect-and-kill AFTER a denied tool ran. Claude Code
exposes hooks that run BEFORE the tool executes, so the human approve/deny
loop becomes a genuine pre-execution block — no proxy, no agent changes,
just `clawmetry hooks install`.

Three hook events, one dispatcher (`clawmetry hooks run <event>`):

  PreToolUse   — the gate. Tool call JSON arrives on stdin; policies are
                 matched (disk-cached cloud policies + local YAML); on match
                 the approval round-trips the cloud (phone push → one tap)
                 while this process blocks. Approved → explicit "allow"
                 (skips Claude Code's own prompt — you already answered on
                 your phone). Denied → "deny" for THIS tool call only: the
                 session survives, unlike the watcher's kill path
                 (process_tool_call is called with kill_on_deny=False).
  Notification — phone push when Claude Code itself needs permission
                 (notification_type=permission_prompt) or is done and
                 waiting on you (idle_prompt). Fire-and-forget POST to
                 /api/cloud/push/notify; never blocks, never fails loud.
  Stop         — reserved; not installed by default (fires on every
                 assistant turn — a push per reply is noise; idle_prompt is
                 the real "finished, waiting on you" signal).

FAIL-OPEN by contract: any error, missing key, unparseable stdin, or
unmatched tool → exit 0 with no output, which per the hook contract means
"no opinion" — Claude Code's normal permission flow continues. A protection
hook that hard-failed on a transient blip would block the agent on every
call; degrading to today's posture is strictly better.

Hook stdout contract (code.claude.com/docs/en/hooks):
  exit 0, no output   → no decision; normal permission evaluation
  exit 0 + JSON       → hookSpecificOutput.permissionDecision allow|deny|ask
  exit 2              → universal block, stderr shown to the model
Deny emits BOTH the modern hookSpecificOutput JSON (stdout) and stderr +
exit 2 (honored by every Claude Code version). Allow emits the modern JSON
with exit 0.

TIMEOUT: the installer sets the PreToolUse hook timeout just above the
7-day max policy window (#4066) — process_tool_call answers within
policy.timeout + grace and then applies on_timeout, so the hook always
answers before Claude Code's hook timeout would block the call.
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid

_CONFIG_PATH = os.path.expanduser("~/.clawmetry/config.json")
_MARKER_PATH = os.path.expanduser("~/.clawmetry/hooks_installed.json")
_POLICY_CACHE_PATH = os.path.expanduser("~/.clawmetry/hooks_policy_cache.json")
_POLICY_CACHE_TTL_S = 60
_SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")

_HOOK_CMD_PRETOOL = "clawmetry hooks run pretooluse"
_HOOK_CMD_NOTIFICATION = "clawmetry hooks run notification"
_HOOK_CMD_STOP = "clawmetry hooks run stop"
# Any command containing this marker is ours (covers the stale-branch
# spelling `clawmetry hook claude-code` too, so uninstall cleans both).
_HOOK_CMD_MARKERS = ("clawmetry hooks run", "clawmetry hook claude-code")

# Must exceed the max policy window (7 days, #4066) + poll grace —
# Claude Code BLOCKS the call when a hook times out, which would
# override the policy's own on_timeout choice.
_PRETOOL_TIMEOUT_S = 605100
_NOTIFICATION_TIMEOUT_S = 10


# ── config (deliberately NOT sync.load_config — that import costs ~100ms
#    and this runs on every tool call) ────────────────────────────────────

def _load_api_key() -> str:
    k = os.environ.get("CLAWMETRY_API_KEY", "").strip()
    if k:
        return k
    try:
        cfg = json.load(open(_CONFIG_PATH))
        return (cfg.get("api_key") or "").strip()
    except Exception:
        return ""


def _node_id() -> str:
    nid = os.environ.get("CLAWMETRY_NODE_ID", "").strip()
    if nid:
        return nid
    try:
        cfg = json.load(open(_CONFIG_PATH))
        return (cfg.get("node_id") or "").strip()
    except Exception:
        return ""


def _ingest_url() -> str:
    # Same default as clawmetry.sync.INGEST_URL, read here without paying
    # the sync import.
    return os.environ.get("CLAWMETRY_INGEST_URL",
                          "https://ingest.clawmetry.com").rstrip("/")


# ── policies: disk-cached so a fresh hook process doesn't pay a cloud GET
#    per tool call (approvals' in-memory TTL cache dies with the process) ──

def _load_policies_fast(api_key: str) -> list:
    """Compiled policies from disk-cached cloud rows + local YAML.

    Cache freshness 60s; a failed cloud fetch falls back to the stale cache
    (policies changing mid-outage is the rarer failure than an outage).
    """
    from clawmetry import approvals

    raw_cloud: list = []
    fresh = False
    try:
        st = os.stat(_POLICY_CACHE_PATH)
        cached = json.load(open(_POLICY_CACHE_PATH))
        raw_cloud = cached.get("policies") or []
        fresh = (time.time() - st.st_mtime) < _POLICY_CACHE_TTL_S
    except Exception:
        pass
    if not fresh and api_key:
        try:
            raw_cloud = approvals._fetch_cloud_policies(api_key)
            tmp = _POLICY_CACHE_PATH + ".tmp"
            os.makedirs(os.path.dirname(_POLICY_CACHE_PATH), exist_ok=True)
            with open(tmp, "w") as f:
                json.dump({"policies": raw_cloud}, f)
            os.replace(tmp, _POLICY_CACHE_PATH)
        except Exception:
            pass  # stale raw_cloud (possibly []) is the fallback

    compiled = []
    for p in raw_cloud:
        if not isinstance(p, dict) or not p.get("enabled", True):
            continue
        c = approvals._compile_policy(p)
        if c:
            compiled.append(c)
    # Local YAML (power users) — same merge order as approvals.load_policies.
    try:
        if approvals.POLICIES_PATH.exists():
            for p in approvals._load_yaml(
                    approvals.POLICIES_PATH.read_text(errors="replace")):
                if isinstance(p, dict):
                    c = approvals._compile_policy(p)
                    if c:
                        compiled.append(c)
    except Exception:
        pass
    return compiled


# ── PreToolUse gate ───────────────────────────────────────────────────────

# Claude Code session modes where the user explicitly opted into autonomy:
# blanket "ask my phone" gates must not nag those sessions (user report
# 2026-07-26: auto-mode sessions were filling the approval inbox).
# `acceptEdits` is NOT here — it auto-accepts file edits only; shell still
# prompts natively, so the phone gate mirrors that.
_AUTONOMOUS_MODES = frozenset({"auto", "dontAsk", "bypassPermissions"})


def _is_blanket_ask(p: dict) -> bool:
    """A catch-all require_approval rule (pattern .* with no narrowing) —
    the interactive convenience gates, as opposed to targeted RISK gates
    (rm -rf, force push, sudo, …) which keep protecting even autonomous
    sessions: yolo mode is exactly when the safety net matters."""
    if (p.get("action") or "") != "require_approval":
        return False
    if p.get("args_regex") is not None or p.get("command_not_regex") is not None:
        return False
    pat = getattr(p.get("command_regex"), "pattern", None)
    return pat in (None, ".*", "^.*", ".+", "^.+")

def _deny_payload(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
        # legacy fallback honored by older builds
        "decision": "block",
        "reason": reason,
    }


def _allow_payload(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
        },
        "decision": "approve",
        "reason": reason,
    }


def evaluate(event: dict) -> "dict | None":
    """Map a PreToolUse event to an allow/deny payload, or None (no opinion).

    Never raises — returns None on any problem (fail-open). Split out so
    tests can drive it without stdin/exit plumbing.
    """
    try:
        if (event.get("hook_event_name") or "PreToolUse") != "PreToolUse":
            return None
        tool_name = event.get("tool_name") or ""
        tool_input = event.get("tool_input") or {}
        if not tool_name:
            return None
        api_key = _load_api_key()
        if not api_key:
            # OSS-local with no cloud approver wired: allow (today's posture)
            # rather than block every call.
            return None

        from clawmetry import approvals
        policies = _load_policies_fast(api_key)
        mode = (event.get("permission_mode") or "").strip()
        if mode in _AUTONOMOUS_MODES:
            policies = [p for p in policies if not _is_blanket_ask(p)]
        if not policies:
            return None
        if not approvals.match_policy(policies, tool_name, tool_input):
            return None  # cheap miss — no duckdb/local_store import paid

        result = approvals.process_tool_call(
            api_key=api_key,
            node_id=_node_id(),
            session_id=event.get("session_id"),
            tool_call_id=event.get("tool_use_id") or uuid.uuid4().hex,
            tool_name=tool_name,
            args=tool_input,
            policies=policies,
            kill_on_deny=False,   # the hook denies ONE call; session survives
        )
        decision = (result or {}).get("decision") or ""
        pol = (result or {}).get("policy") or "policy"
        # process_tool_call returns "denied"/"approved" for HUMAN decisions
        # but the raw on_timeout strings "deny"/"approve" when the window
        # lapsed — the distinction matters: telling the model (and the log)
        # "the human declined" when nobody answered erodes trust in the
        # whole gate (live confusion, 2026-07-26).
        if decision == "denied":
            return _deny_payload(
                f"Denied via ClawMetry approvals (policy '{pol}'). The human "
                "declined this specific call — pick a different approach or "
                "ask them what they'd prefer."
            )
        if decision == "deny":
            return _deny_payload(
                f"ClawMetry approval timed out with no decision (policy "
                f"'{pol}', on_timeout: deny). The human never saw or didn't "
                "reach it in time — worth asking them directly, or they can "
                "raise this policy's timeout in the Approvals tab."
            )
        if decision == "approved":
            if (result or {}).get("auto"):
                return _allow_payload(
                    f"Auto-approved by always-allow rule '{pol}' — no human "
                    "round-trip needed."
                )
            return _allow_payload(
                f"Approved by the human via ClawMetry approvals "
                f"(policy '{pol}')."
            )
        if decision == "approve":
            return _allow_payload(
                f"ClawMetry approval timed out (policy '{pol}', on_timeout: "
                "approve) — proceeding per the policy's timeout action."
            )
        # monitored / no_policy / error / anything unexpected → no opinion
        return None
    except Exception:
        return None  # fail-open: never block the agent on our own error


def main_pretooluse() -> int:
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # unparseable stdin → no opinion
    payload = evaluate(event)
    if payload is None:
        return 0
    try:
        sys.stdout.write(json.dumps(payload))
    except Exception:
        pass
    if payload.get("decision") == "block":
        # Belt and suspenders: exit 2 blocks on every Claude Code version,
        # even ones predating hookSpecificOutput.
        sys.stderr.write(payload.get("reason") or "Blocked by ClawMetry.")
        return 2
    return 0


# ── Notification → phone push ─────────────────────────────────────────────

def _push_notify(api_key: str, kind: str, title: str, body: str,
                 extra: "dict | None" = None) -> bool:
    """Fire-and-forget POST /api/cloud/push/notify. Never raises.

    ``extra`` carries session context (session_id, cwd, node_id) so the
    cloud can record WHICH terminal is waiting — the inbox's "Needs you
    at the desk" section (kind=input records, stop/clear clears)."""
    try:
        import urllib.request
        payload = {"kind": kind, "title": title, "body": body[:400],
                   "open_url": "/approvals"}
        payload.update(extra or {})
        req = urllib.request.Request(
            f"{_ingest_url()}/api/cloud/push/notify",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=4):
            return True
    except Exception:
        return False


def _session_extra(event: dict) -> dict:
    sid = (event.get("session_id") or "").strip()
    extra = {"node_id": _node_id()}
    if sid:
        # Cloud rows key on the runtime-prefixed form the daemon uses.
        extra["session_id"] = sid if ":" in sid else f"claude_code:{sid}"
    if event.get("cwd"):
        extra["cwd"] = str(event["cwd"])[:300]
    return extra


def main_notification() -> int:
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0
    api_key = _load_api_key()
    if not api_key:
        return 0
    ntype = event.get("notification_type") or ""
    message = (event.get("message") or "").strip()
    if ntype == "permission_prompt":
        # Only reached when the PreToolUse gate had no opinion (no policy
        # matched) and Claude Code raised its own prompt — the phone can't
        # answer it remotely, but the inbox shows WHICH terminal is waiting.
        _push_notify(api_key, "input", "Claude Code needs your permission",
                     message or "A tool call is waiting for your approval.",
                     _session_extra(event))
    elif ntype == "idle_prompt":
        _push_notify(api_key, "stop", "Claude Code is done — waiting on you",
                     message or "The agent finished and is waiting for input.",
                     _session_extra(event))
    return 0


def main_stop() -> int:
    """Stop hook: bookkeeping only. The turn ended, so whatever native
    prompt this session had is no longer waiting — clear its desk-attention
    row. kind=clear sends NO push (a push per assistant turn would be
    noise); observe-only exit 0 always."""
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0
    api_key = _load_api_key()
    if not api_key:
        return 0
    extra = _session_extra(event)
    if extra.get("session_id"):
        _push_notify(api_key, "clear", "", "", extra)
    return 0


# ── install / uninstall / status ──────────────────────────────────────────

def _read_settings(path: str) -> dict:
    if os.path.exists(path):
        with open(path) as f:
            txt = f.read().strip()
            return json.loads(txt) if txt else {}
    return {}


def _write_settings(path: str, settings: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(settings, f, indent=2)
    os.replace(tmp, path)


def _has_our_hook(entries: list) -> bool:
    for entry in entries or []:
        for h in (entry.get("hooks") or []):
            cmd = h.get("command") or ""
            if any(m in cmd for m in _HOOK_CMD_MARKERS):
                return True
    return False


def _write_marker(events: list) -> None:
    try:
        os.makedirs(os.path.dirname(_MARKER_PATH), exist_ok=True)
        data = {}
        try:
            data = json.load(open(_MARKER_PATH))
        except Exception:
            pass
        data["claude_code"] = {
            "events": events,
            "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        tmp = _MARKER_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, _MARKER_PATH)
    except Exception:
        pass


def install(settings_path: "str | None" = None, matcher: str = "*") -> dict:
    """Register the PreToolUse gate + Notification push in Claude Code's
    settings.json (idempotent per event; merges, never clobbers).

    Matcher default "*": policies cover write/web/secrets tools, not just
    Bash, and the no-match fast path costs ~40ms. The marker file written
    here is what tells the daemon's reactive watcher to stop double-gating
    claude_code sessions (approvals._hook_covered_runtimes).
    """
    path = settings_path or _SETTINGS_PATH
    try:
        settings = _read_settings(path)
        hooks = settings.setdefault("hooks", {})
        added = []

        pretool = hooks.setdefault("PreToolUse", [])
        if not _has_our_hook(pretool):
            pretool.append({
                "matcher": matcher,
                "hooks": [{"type": "command",
                           "command": _HOOK_CMD_PRETOOL,
                           "timeout": _PRETOOL_TIMEOUT_S}],
            })
            added.append("PreToolUse")

        notification = hooks.setdefault("Notification", [])
        if not _has_our_hook(notification):
            notification.append({
                "hooks": [{"type": "command",
                           "command": _HOOK_CMD_NOTIFICATION,
                           "timeout": _NOTIFICATION_TIMEOUT_S}],
            })
            added.append("Notification")

        # Stop = bookkeeping only (clears the "needs you at the desk" row
        # for the session; no push) — see main_stop.
        stop = hooks.setdefault("Stop", [])
        if not _has_our_hook(stop):
            stop.append({
                "hooks": [{"type": "command",
                           "command": _HOOK_CMD_STOP,
                           "timeout": _NOTIFICATION_TIMEOUT_S}],
            })
            added.append("Stop")

        if added:
            _write_settings(path, settings)
        _write_marker(["PreToolUse", "Notification", "Stop"])
        return {"status": "installed" if added else "already_present",
                "path": path, "added": added, "matcher": matcher,
                "timeout": _PRETOOL_TIMEOUT_S}
    except Exception as e:
        return {"status": "error", "path": path, "error": str(e)}


def uninstall(settings_path: "str | None" = None) -> dict:
    path = settings_path or _SETTINGS_PATH
    try:
        settings = _read_settings(path)
        hooks = settings.get("hooks") or {}
        removed = []
        for event, entries in list(hooks.items()):
            kept = []
            for entry in entries or []:
                cmds = [h.get("command") or "" for h in (entry.get("hooks") or [])]
                if any(any(m in c for m in _HOOK_CMD_MARKERS) for c in cmds):
                    removed.append(event)
                else:
                    kept.append(entry)
            if kept:
                hooks[event] = kept
            elif event in hooks:
                del hooks[event]
        if removed:
            _write_settings(path, settings)
        try:
            data = json.load(open(_MARKER_PATH))
            data.pop("claude_code", None)
            with open(_MARKER_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
        return {"status": "uninstalled" if removed else "not_installed",
                "path": path, "removed": removed}
    except Exception as e:
        return {"status": "error", "path": path, "error": str(e)}


def status(settings_path: "str | None" = None) -> dict:
    path = settings_path or _SETTINGS_PATH
    out = {"settings_path": path, "installed_events": [],
           "api_key_present": bool(_load_api_key()), "policies": 0}
    try:
        hooks = (_read_settings(path).get("hooks") or {})
        out["installed_events"] = [ev for ev, entries in hooks.items()
                                   if _has_our_hook(entries)]
    except Exception as e:
        out["settings_error"] = str(e)
    try:
        out["policies"] = len(_load_policies_fast(_load_api_key()))
    except Exception:
        pass
    return out


# ── CLI dispatcher (fast path from cli.main — no dashboard import) ────────

def cli_main(argv: "list | None" = None) -> int:
    argv = sys.argv[2:] if argv is None else argv
    cmd = argv[0] if argv else "status"
    if cmd == "run":
        event = argv[1] if len(argv) > 1 else ""
        if event == "pretooluse":
            return main_pretooluse()
        if event == "notification":
            return main_notification()
        if event == "stop":
            return main_stop()
        sys.stderr.write(f"unknown hook event: {event!r}\n")
        return 1
    if cmd == "install":
        matcher = "*"
        if "--matcher" in argv:
            try:
                matcher = argv[argv.index("--matcher") + 1]
            except IndexError:
                pass
        res = install(matcher=matcher)
        print(json.dumps(res, indent=2))
        if res.get("status") == "installed":
            print("\nDone. Claude Code tool calls matching your approval "
                  "policies now pause for a decision on your phone "
                  "(app.clawmetry.com/push to enable notifications).")
        return 0 if res.get("status") != "error" else 1
    if cmd == "uninstall":
        res = uninstall()
        print(json.dumps(res, indent=2))
        return 0 if res.get("status") != "error" else 1
    if cmd == "status":
        print(json.dumps(status(), indent=2))
        return 0
    sys.stderr.write(
        "usage: clawmetry hooks {install [--matcher RE] | uninstall | "
        "status | run {pretooluse|notification|stop}}\n")
    return 1
