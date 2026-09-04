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

Lifecycle events (WO-61) — seven more, all OBSERVE-ONLY and all installed
with Claude Code's ``"async": true`` so the runtime never waits on them:

  PostToolUseFailure  → tool.failed          (tool_name, tool_use_id, error)
  SubagentStart       → subagent.started     (agent_id, agent_type)
  SubagentStop        → subagent.stopped     (agent_id, agent_type)
  PermissionDenied    → permission.denied    (tool_name, reason; NO args)
  PostCompact         → context.compacted    (trigger)
  SessionStart        → session.started      (start_reason, model, cwd)
  InstructionsLoaded  → instructions.loaded  (path, type, reason, sha256)

Each handler maps the payload to one typed event with a DETERMINISTIC id
(session + event type + the fact's own key: tool_use_id, agent_id, path
and hash, ...) and POSTs it to the local dashboard's
``/api/hooks/claude-code/lifecycle`` intake with a 3s timeout. The intake
writes through the daemon (the only DuckDB writer); the store's
INSERT OR IGNORE on the id makes a second arrival of the same fact a
no-op. Unknown payload fields are accepted and their NAMES recorded, so a
Claude Code release that adds a field is visible without a code change.

InstructionsLoaded carries the PATH of the loaded file, not its contents
(verified against code.claude.com/docs/en/hooks). The handler reads the
file at that moment, caps it at ``INSTRUCTIONS_CAP_BYTES``, and sends it
with a sha256 of the FULL file so a changed instructions file is a
comparable property; the store redacts it (secrets + personal data) before
it rests. On a Claude Code build without InstructionsLoaded, SessionStart
falls back to the cwd's CLAUDE.md chain and says so in the event.

Which events a build offers is PROBED, not assumed from a version table:
the event name is a literal string in the resolved ``claude`` binary (or
its ``cli.js``), so the installer greps for it and skips, with a note,
any event the build does not name. An unlocatable binary installs all of
them (Claude Code ignores hook events it does not fire).

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

TIMEOUT: the installer wants the hook timeout just above the policy window
(#4066) so process_tool_call answers within policy.timeout + grace and
applies on_timeout, rather than Claude Code timing out and blocking the
call itself. That derivation alone produced a 7-day installed timeout, so
it is now clamped by hook_ownership.clamp_hook_timeout (default 8h,
CLAWMETRY_HOOK_TIMEOUT_MAX_S=0 to opt out). Past the ceiling the runtime
times out first and blocks that one call — a bounded block, deliberately
chosen over an unbounded wait on a wedged hook.

COEXISTENCE: this is not the only writer of ~/.claude/settings.json (see
clawmetry/hook_ownership.py). Install merges and uninstall removes at HOOK
granularity, so a co-installed writer sharing an entry with us keeps its
hook. Never delete a hook you did not write.
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid

from clawmetry import hook_ownership

_CONFIG_PATH = os.path.expanduser("~/.clawmetry/config.json")
_MARKER_PATH = os.path.expanduser("~/.clawmetry/hooks_installed.json")
_POLICY_CACHE_PATH = os.path.expanduser("~/.clawmetry/hooks_policy_cache.json")
_POLICY_CACHE_TTL_S = 60
_SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")

_HOOK_CMD_PRETOOL = "clawmetry hooks run pretooluse"
_HOOK_CMD_NOTIFICATION = "clawmetry hooks run notification"
_HOOK_CMD_STOP = "clawmetry hooks run stop"

# Lifecycle events (WO-61). Order = install order = the order the trail
# presents the facts. ``run`` names are the lower-cased event names.
LIFECYCLE_EVENTS: tuple = (
    "PostToolUseFailure", "SubagentStart", "SubagentStop",
    "PermissionDenied", "PostCompact", "SessionStart", "InstructionsLoaded",
)
LIFECYCLE_EVENT_TYPES: dict = {
    "PostToolUseFailure": "tool.failed",
    "SubagentStart": "subagent.started",
    "SubagentStop": "subagent.stopped",
    "PermissionDenied": "permission.denied",
    "PostCompact": "context.compacted",
    "SessionStart": "session.started",
    "InstructionsLoaded": "instructions.loaded",
}
_LIFECYCLE_RUN_NAMES: dict = {ev.lower(): ev for ev in LIFECYCLE_EVENTS}
_LIFECYCLE_TIMEOUT_S = 5          # not enforced on async hooks; documented cap
_LIFECYCLE_POST_TIMEOUT_S = 3.0   # the handler never waits longer than this
INSTRUCTIONS_CAP_BYTES = 32 * 1024
_ERROR_CAP_CHARS = 2000
_SERVER_INFO_PATH = os.path.expanduser("~/.clawmetry/server.json")
# Any command containing this marker is ours (covers the stale-branch
# spelling `clawmetry hook claude-code` too, so uninstall cleans both).
_HOOK_CMD_MARKERS = ("clawmetry hooks run", "clawmetry hook claude-code")

# Must exceed the max policy window (7 days, #4066) + poll grace —
# Claude Code BLOCKS the call when a hook times out, which would
# override the policy's own on_timeout choice.
_PRETOOL_TIMEOUT_S = hook_ownership.clamp_hook_timeout(605100)
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


# ── lifecycle events (WO-61) ──────────────────────────────────────────────

def _dashboard_base() -> str:
    """Where the local dashboard listens. ``routes/hooks.py`` writes
    ``~/.clawmetry/server.json`` with the bound port; 8900 otherwise."""
    base = os.environ.get("CLAWMETRY_URL", "").strip().rstrip("/")
    if base:
        return base
    port = 8900
    try:
        info = json.load(open(_SERVER_INFO_PATH))
        port = int(info.get("port") or 8900)
    except Exception:
        pass
    return f"http://127.0.0.1:{port}"


def lifecycle_event_id(session_id: str, event_type: str, key: str) -> str:
    """Deterministic id for one lifecycle fact. Same fact -> same id, so the
    store's INSERT OR IGNORE turns a second arrival into a no-op."""
    import hashlib
    raw = f"cc-hook:{session_id}:{event_type}:{key}"
    return hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:32]


# Fields every hook payload documents (code.claude.com/docs/en/hooks). Any
# other top-level key is "unknown" and its NAME is recorded on the event.
_KNOWN_PAYLOAD_FIELDS = frozenset({
    "session_id", "prompt_id", "transcript_path", "cwd", "permission_mode",
    "effort", "hook_event_name", "agent_id", "agent_type",
    "tool_name", "tool_input", "tool_use_id", "tool_response", "tool_error",
    "denial_reason", "agent_instructions", "last_assistant_message",
    "trigger", "start_reason", "model", "instruction_path",
    "instruction_type", "load_reason", "end_reason",
})


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + \
        f".{int((time.time() % 1) * 1000):03d}Z"


def read_instructions_file(path: str, cap: int = INSTRUCTIONS_CAP_BYTES) -> "dict | None":
    """Read an instructions file as the agent just saw it.

    Returns ``{content, sha256, bytes, truncated}`` or None when the path
    is unreadable. The hash covers the FULL file; the content is capped so
    a 4 MB CLAUDE.md cannot bloat the store. Redaction happens in the
    store, not here: this runs in a hook process and must stay cheap.
    """
    import hashlib
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except Exception:
        return None
    digest = hashlib.sha256(raw).hexdigest()
    truncated = len(raw) > cap
    body = raw[:cap] if truncated else raw
    return {
        "content": body.decode("utf-8", "replace"),
        "sha256": digest,
        "bytes": len(raw),
        "truncated": truncated,
    }


def _fallback_instruction_paths(cwd: str) -> list:
    """The CLAUDE.md chain a Claude Code build without InstructionsLoaded
    would have read: walk from cwd to the filesystem root, then the user
    file. Only existing files are returned."""
    out = []
    seen = set()
    try:
        cur = os.path.abspath(cwd or os.getcwd())
        while True:
            for rel in ("CLAUDE.md", os.path.join(".claude", "CLAUDE.md")):
                p = os.path.join(cur, rel)
                if p not in seen and os.path.isfile(p):
                    seen.add(p)
                    out.append(p)
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
        user = os.path.expanduser(os.path.join("~", ".claude", "CLAUDE.md"))
        if user not in seen and os.path.isfile(user):
            out.append(user)
    except Exception:
        pass
    return out


def _lifecycle_skipped_events() -> set:
    try:
        data = json.load(open(_MARKER_PATH))
        return set((data.get("claude_code") or {}).get("skipped") or [])
    except Exception:
        return set()


def map_lifecycle_event(event_name: str, payload: dict, ts: "str | None" = None,
                        read_file=read_instructions_file) -> list:
    """Pure mapping: one hook payload -> typed event dicts for the intake.

    Never raises on a strange payload; unknown fields are tolerated and
    their names recorded under ``unknown_fields``. Returns [] when the
    payload carries no session id (nothing to attach the fact to).
    """
    if not isinstance(payload, dict):
        return []
    sid = str(payload.get("session_id") or "").strip()
    if not sid:
        return []
    ts = ts or _now_iso()
    etype = LIFECYCLE_EVENT_TYPES.get(event_name)
    if not etype:
        return []
    unknown = sorted(k for k in payload if isinstance(k, str)
                     and k not in _KNOWN_PAYLOAD_FIELDS)
    common = {
        "source": "hook",
        "hook_event_name": event_name,
        "cwd": str(payload.get("cwd") or "")[:300],
        "permission_mode": str(payload.get("permission_mode") or "")[:32],
        "unknown_fields": unknown[:20],
    }
    if payload.get("agent_id"):
        common["agent_id"] = str(payload["agent_id"])[:120]
    if payload.get("agent_type"):
        common["agent_type"] = str(payload["agent_type"])[:120]

    def _evt(key: str, data: dict) -> dict:
        d = dict(common)
        d.update(data)
        return {
            "id": lifecycle_event_id(sid, etype, key),
            "session_id": sid,
            "event_type": etype,
            "ts": ts,
            "data": d,
        }

    out = []
    if event_name == "PostToolUseFailure":
        tuid = str(payload.get("tool_use_id") or "").strip()
        out.append(_evt(tuid or ts, {
            "tool_name": str(payload.get("tool_name") or "")[:120],
            "tool_use_id": tuid,
            "error": str(payload.get("tool_error") or "")[:_ERROR_CAP_CHARS],
        }))
    elif event_name in ("SubagentStart", "SubagentStop"):
        aid = str(payload.get("agent_id") or "").strip()
        data = {"agent_id": aid,
                "agent_type": str(payload.get("agent_type") or "")[:120]}
        if event_name == "SubagentStop":
            msg = payload.get("last_assistant_message")
            data["last_message_chars"] = len(msg) if isinstance(msg, str) else 0
        out.append(_evt(aid or ts, data))
    elif event_name == "PermissionDenied":
        tuid = str(payload.get("tool_use_id") or "").strip()
        # Deliberately no tool_input: the Behaviour Signals work counts
        # these, it does not need the arguments, and the arguments are
        # where a secret would be.
        out.append(_evt(tuid or ts, {
            "tool_name": str(payload.get("tool_name") or "")[:120],
            "tool_use_id": tuid,
            "reason": str(payload.get("denial_reason") or "")[:500],
        }))
    elif event_name == "PostCompact":
        trig = str(payload.get("trigger") or "")[:32]
        key = str(payload.get("prompt_id") or "") or ts
        out.append(_evt(f"{trig}:{key}", {"trigger": trig}))
    elif event_name == "SessionStart":
        reason = str(payload.get("start_reason") or "")[:32]
        out.append(_evt(f"{reason}:{ts[:16]}", {
            "start_reason": reason,
            "model": str(payload.get("model") or "")[:80],
            "transcript_path": str(payload.get("transcript_path") or "")[:400],
        }))
        if "InstructionsLoaded" in _lifecycle_skipped_events():
            for path in _fallback_instruction_paths(payload.get("cwd") or ""):
                info = read_file(path)
                if not info:
                    continue
                out.append({
                    "id": lifecycle_event_id(sid, "instructions.loaded",
                                             f"{path}:{info['sha256']}"),
                    "session_id": sid,
                    "event_type": "instructions.loaded",
                    "ts": ts,
                    "data": dict(common, instruction_path=path,
                                 instruction_type="claude_md",
                                 load_reason="session_start_fallback",
                                 sha256=info["sha256"], bytes=info["bytes"],
                                 truncated=info["truncated"]),
                    "instructions": info,
                })
    elif event_name == "InstructionsLoaded":
        path = str(payload.get("instruction_path") or "").strip()
        info = read_file(path) if path else None
        sha = info["sha256"] if info else ""
        evt = _evt(f"{path}:{sha}", {
            "instruction_path": path[:400],
            "instruction_type": str(payload.get("instruction_type") or "")[:32],
            "load_reason": str(payload.get("load_reason") or "")[:32],
            "sha256": sha,
            "bytes": info["bytes"] if info else None,
            "truncated": info["truncated"] if info else None,
            "readable": bool(info),
        })
        if info:
            evt["instructions"] = info
        out.append(evt)
    return out


def post_lifecycle(events: list, base: "str | None" = None,
                   timeout: float = _LIFECYCLE_POST_TIMEOUT_S) -> bool:
    """POST typed events to the local intake. Never raises, never blocks
    past ``timeout``: the hook is async on the runtime side, but a stuck
    process is still a process."""
    if not events:
        return False
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{base or _dashboard_base()}/api/hooks/claude-code/lifecycle",
            data=json.dumps({"events": events}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except Exception:
        return False


def main_lifecycle(event_name: str) -> int:
    """Handler for every lifecycle event: read stdin, map, post, exit 0."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0
    try:
        events = map_lifecycle_event(event_name, payload)
        post_lifecycle(events)
    except Exception:
        pass
    return 0


# ── which events does this Claude Code build fire? ────────────────────────

def _claude_binary_candidates() -> list:
    """Files that could carry Claude Code's hook-event string table."""
    import shutil
    cands = []
    found = shutil.which("claude")
    for p in (found,
              os.path.expanduser("~/.local/bin/claude"),
              os.path.expanduser("~/.claude/local/claude"),
              os.path.expanduser("~/.claude/local/node_modules/@anthropic-ai/claude-code/cli.js")):
        if not p:
            continue
        try:
            rp = os.path.realpath(p)
        except Exception:
            continue
        if os.path.isfile(rp) and rp not in cands:
            cands.append(rp)
        # npm shim: a small launcher next to a package dir holding cli.js.
        try:
            if os.path.getsize(rp) < 1_000_000:
                d = os.path.dirname(rp)
                for _ in range(4):
                    cli = os.path.join(d, "node_modules", "@anthropic-ai",
                                       "claude-code", "cli.js")
                    if os.path.isfile(cli) and cli not in cands:
                        cands.append(cli)
                        break
                    d = os.path.dirname(d)
        except Exception:
            pass
    return cands


def probe_claude_events(events=LIFECYCLE_EVENTS, binaries: "list | None" = None) -> dict:
    """``{event: True|False|None}`` -- None means "could not verify".

    A hook event name is a literal string in the build that fires it, so
    presence in the resolved binary (or cli.js) is a checkable fact. The
    scan is one pass per event over an mmap; ~200 MB in well under a
    second. A build we cannot locate answers None for everything.
    """
    import mmap
    cands = binaries if binaries is not None else _claude_binary_candidates()
    result = {ev: None for ev in events}
    for path in cands:
        try:
            with open(path, "rb") as f:
                try:
                    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                except (ValueError, OSError):
                    mm = f.read()  # empty file / platform without mmap
                try:
                    for ev in events:
                        hit = mm.find(ev.encode("ascii")) != -1
                        result[ev] = bool(result[ev]) or hit
                finally:
                    if hasattr(mm, "close"):
                        mm.close()
        except Exception:
            continue
    return result


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


def _cmd_binary_exists(cmd: str) -> bool:
    """Return True if the hook command's binary is runnable.

    Only validates absolute paths — bare command names depend on PATH at
    execution time and cannot be reliably pre-checked here.
    """
    if not cmd:
        return False
    first = cmd.split()[0]
    if os.path.isabs(first):
        return os.access(first, os.X_OK)
    return True


def _drop_stale_our_hooks(entries: list) -> bool:
    """Remove entries that carry our marker but whose binary is no longer
    executable.  Returns True if anything was pruned."""
    def _is_stale_ours(h: dict) -> bool:
        cmd = (h or {}).get("command") or ""
        return (hook_ownership.hook_is_ours(h, _HOOK_CMD_MARKERS)
                and not _cmd_binary_exists(cmd))

    kept, n = hook_ownership.prune_our_hooks(entries, _HOOK_CMD_MARKERS,
                                             ours_pred=_is_stale_ours)
    if n:
        entries[:] = kept
    return bool(n)


def _has_our_hook(entries: list) -> bool:
    for entry in entries or []:
        for h in (entry.get("hooks") or []):
            cmd = h.get("command") or ""
            if any(m in cmd for m in _HOOK_CMD_MARKERS):
                if _cmd_binary_exists(cmd):
                    return True
    return False


def _write_marker(events: list, skipped: "list | None" = None) -> None:
    try:
        os.makedirs(os.path.dirname(_MARKER_PATH), exist_ok=True)
        data = {}
        try:
            data = json.load(open(_MARKER_PATH))
        except Exception:
            pass
        data["claude_code"] = {
            "events": events,
            # Lifecycle events this Claude Code build does not fire (per the
            # binary probe). SessionStart reads this to decide whether to
            # fall back to the cwd's CLAUDE.md chain.
            "skipped": list(skipped or []),
            "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        tmp = _MARKER_PATH + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, _MARKER_PATH)
    except Exception:
        pass


def install(settings_path: "str | None" = None, matcher: str = "*",
            probe: "dict | None" = None) -> dict:
    """Register the PreToolUse gate + Notification push + the seven
    lifecycle events in Claude Code's settings.json (idempotent per event;
    merges, never clobbers). ``probe`` overrides the binary scan (tests).

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
        modified = False

        pretool = hooks.setdefault("PreToolUse", [])
        if _drop_stale_our_hooks(pretool):
            modified = True
        if not _has_our_hook(pretool):
            pretool.append({
                "matcher": matcher,
                "hooks": [{"type": "command",
                           "command": _HOOK_CMD_PRETOOL,
                           "timeout": _PRETOOL_TIMEOUT_S}],
            })
            added.append("PreToolUse")
            modified = True

        notification = hooks.setdefault("Notification", [])
        if _drop_stale_our_hooks(notification):
            modified = True
        if not _has_our_hook(notification):
            notification.append({
                "hooks": [{"type": "command",
                           "command": _HOOK_CMD_NOTIFICATION,
                           "timeout": _NOTIFICATION_TIMEOUT_S}],
            })
            added.append("Notification")
            modified = True

        # Stop = bookkeeping only (clears the "needs you at the desk" row
        # for the session; no push) — see main_stop.
        stop = hooks.setdefault("Stop", [])
        if _drop_stale_our_hooks(stop):
            modified = True
        if not _has_our_hook(stop):
            stop.append({
                "hooks": [{"type": "command",
                           "command": _HOOK_CMD_STOP,
                           "timeout": _NOTIFICATION_TIMEOUT_S}],
            })
            added.append("Stop")
            modified = True

        # Lifecycle events (WO-61): observe-only, async so the runtime never
        # waits on them, and only the ones this build actually fires.
        supported = probe_claude_events(LIFECYCLE_EVENTS) if probe is None else probe
        installed_lifecycle = []
        skipped = []
        for ev in LIFECYCLE_EVENTS:
            if supported.get(ev) is False:
                skipped.append(ev)
                continue
            entries = hooks.setdefault(ev, [])
            if _drop_stale_our_hooks(entries):
                modified = True
            if not _has_our_hook(entries):
                entries.append({
                    "hooks": [{"type": "command",
                               "command": f"clawmetry hooks run {ev.lower()}",
                               "timeout": _LIFECYCLE_TIMEOUT_S,
                               "async": True}],
                })
                added.append(ev)
                modified = True
            installed_lifecycle.append(ev)

        if modified:
            _write_settings(path, settings)
        _write_marker(["PreToolUse", "Notification", "Stop"] + installed_lifecycle,
                      skipped=skipped)
        notes = [f"{ev}: not offered by the installed Claude Code build, skipped"
                 for ev in skipped]
        if all(v is None for v in supported.values()):
            notes.append("Claude Code binary not found; every lifecycle event "
                         "was installed unverified (the runtime ignores events "
                         "it does not fire)")
        return {"status": "installed" if added else "already_present",
                "path": path, "added": added, "matcher": matcher,
                "timeout": _PRETOOL_TIMEOUT_S,
                "lifecycle": installed_lifecycle, "skipped": skipped,
                "notes": notes}
    except Exception as e:
        return {"status": "error", "path": path, "error": str(e)}


def uninstall(settings_path: "str | None" = None) -> dict:
    path = settings_path or _SETTINGS_PATH
    try:
        settings = _read_settings(path)
        hooks = settings.get("hooks") or {}
        removed = []
        for event, entries in list(hooks.items()):
            if not isinstance(entries, list):
                continue  # foreign/malformed shape — not ours to rewrite
            # Hook-level, never entry-level: a co-installed writer
            # (`gk ai hook install claude-code --force`, numbat, a
            # hand-written entry) may live in the SAME entry as ours, and
            # dropping the entry would take its hook with it.
            kept, n = hook_ownership.prune_our_hooks(entries, _HOOK_CMD_MARKERS)
            if n:
                removed.append(event)
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
        if event in _LIFECYCLE_RUN_NAMES:
            return main_lifecycle(_LIFECYCLE_RUN_NAMES[event])
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
        for note in res.get("notes") or []:
            print(f"note: {note}")
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
        "status | run {pretooluse|notification|stop|"
        + "|".join(sorted(_LIFECYCLE_RUN_NAMES)) + "}}\n")
    return 1
