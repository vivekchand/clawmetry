"""Claude Code pre-tool gate: policy-driven PreToolUse hook, local-first.

Two halves, one module (stdlib-only so the hook fast path stays cheap):

INSTALLER (daemon side) — ``gate_handler(want_gate, policies)`` is the
``GATE_HANDLERS['claude_code']`` entry driven by
``approvals.sync_runtime_gates`` every watcher iteration. When any active
``require_approval`` policy applies to claude_code (explicit ``runtime:
claude_code`` or runtime-unset), it installs a PreToolUse hook entry into
Claude Code's ``settings.json`` (``$CLAUDE_CONFIG_DIR/settings.json``,
default ``~/.claude/settings.json``):

    {"matcher": "<derived from policy tools>",
     "hooks": [{"type": "command",
                "command": "<python> -m clawmetry hook claude-code --base
                            http://127.0.0.1:<dashboard port>",
                "timeout": <max policy timeout + buffer>}]}

Merge rules (the ``_EXEC_POLICY_STATE`` pattern from approvals.py):
  * never clobbers foreign hook entries — ours is found/removed ONLY by the
    ``-m clawmetry hook claude-code`` command marker;
  * a state file (``~/.clawmetry/claude_code_gate.json``) records exactly
    what we installed; uninstall removes only that, and only when the state
    file says a prior run of ours installed it;
  * if the user already installed the cloud-path hook by hand
    (``clawmetry hooks install`` → command ``clawmetry hooks run
    pretooluse``), we DON'T stack a second gate on top — two PreToolUse
    gates would each pause the same call and double-file approvals.

HOOK CLIENT (Claude Code side) — ``hook_main(argv)`` backs the
``clawmetry hook claude-code --base <url>`` CLI fast path. It reads the
PreToolUse event JSON from stdin, POSTs it to the local dashboard's
``/api/hooks/claude-code/pretooluse`` receiver, and prints the returned
``hookSpecificOutput`` JSON to stdout. The receiver parks the approval in
the SAME local queue the Approvals tab reads, so the human decides in the
dashboard while this process blocks.

Long waits: the receiver answers each POST within a bounded slice (~20 s,
under waitress's 120 s channel_timeout) and returns
``{"status": "pending", "approval_id": …, "retry_after_ms": …}`` while the
human hasn't decided; the client loops, re-POSTing with ``approval_id`` so
no duplicate rows are created. FAIL-OPEN by contract: server down, bad
JSON, non-200, anything unexpected → exit 0 with NO output, which per the
Claude Code hook contract means "no opinion" (normal permission flow).
"""
from __future__ import annotations

import json
import os
import sys
import time

# ── paths / markers ────────────────────────────────────────────────────────

_STATE_PATH = os.path.expanduser("~/.clawmetry/claude_code_gate.json")
_SERVER_INFO_PATH = os.path.expanduser("~/.clawmetry/server.json")
# Shared with hooks_claude_code.py / approvals._hook_covered_runtimes: a
# "claude_code" entry whose events include PreToolUse tells the reactive
# watcher this runtime is pre-execution gated, so it must NOT double-file
# approvals (and kill sessions) for tool calls the hook already paused.
_MARKER_PATH = os.path.expanduser("~/.clawmetry/hooks_installed.json")

# Any hook command containing this is OURS (the local-first gate).
HOOK_CMD_MARKER = "-m clawmetry hook claude-code"
# Commands containing any of these belong to the CLOUD-path manual install
# (hooks_claude_code.py). Their presence means claude_code is already
# pre-tool gated — we must not stack a second gate.
_FOREIGN_CLAWMETRY_MARKERS = ("clawmetry hooks run",)

_DEFAULT_DASHBOARD_PORT = 8900

# Extra seconds on top of the max policy window so the receiver (which
# applies on_timeout itself) always answers before Claude Code's hook
# timeout would hard-block the call.
_HOOK_TIMEOUT_BUFFER_S = 60


# ── dashboard base-URL discovery ───────────────────────────────────────────

def dashboard_base() -> str:
    """Best-known base URL of the local dashboard, embedded into the hook
    command at install time.

    Order: CLAWMETRY_DASHBOARD_BASE env → ``~/.clawmetry/server.json``
    (written by routes/hooks.py when the dashboard boots / serves its first
    request) → the documented default port 8900. Always loopback — the
    receiver only trusts loopback callers anyway."""
    env = os.environ.get("CLAWMETRY_DASHBOARD_BASE", "").strip()
    if env:
        return env.rstrip("/")
    try:
        with open(_SERVER_INFO_PATH) as f:
            info = json.load(f)
        port = int(info.get("port") or 0)
        if 0 < port < 65536:
            return f"http://127.0.0.1:{port}"
    except Exception:
        pass
    return f"http://127.0.0.1:{_DEFAULT_DASHBOARD_PORT}"


# ── matcher / timeout derivation ───────────────────────────────────────────

# Canonical policy tool category → Claude Code tool-name matcher fragment.
# Policies use OpenClaw-ish names ('exec', 'write', …); Claude Code matchers
# are its own tool names. exec-ish (and the tool-agnostic '') map to Bash.
_CANON_TO_MATCHER = {
    "exec":   "Bash",
    "write":  "Write|Edit|MultiEdit|NotebookEdit",
    "read":   "Read",
    "web":    "WebFetch|WebSearch",
    "search": "Grep|Glob",
}


def _matcher_from_policies(policies) -> str:
    """Derive the PreToolUse matcher from the gate-wanting policies.

    bash/exec/shell/'' → "Bash"; known categories map to their Claude Code
    tool names; an unrecognised explicit tool name is used verbatim (the
    user may be naming an MCP tool). Union across policies, joined with
    '|'. Default "Bash"."""
    try:
        from clawmetry.approvals import _canonical_tool
    except Exception:
        def _canonical_tool(name):  # type: ignore
            return (name or "").strip().lower()
    parts: list[str] = []

    def _add(fragment: str) -> None:
        for piece in fragment.split("|"):
            if piece and piece not in parts:
                parts.append(piece)

    for p in policies or []:
        if not isinstance(p, dict):
            continue
        if (p.get("action") or "require_approval") != "require_approval":
            continue
        tool = str(p.get("tool") or "").strip()
        if tool == "":
            _add("Bash")
            continue
        canon = _canonical_tool(tool)
        _add(_CANON_TO_MATCHER.get(canon, tool))
    return "|".join(parts) if parts else "Bash"


def _timeout_from_policies(policies) -> int:
    """Hook timeout: the longest matching policy window + buffer, so the
    receiver's own on_timeout mapping always answers first."""
    longest = 0
    for p in policies or []:
        if not isinstance(p, dict):
            continue
        if (p.get("action") or "require_approval") != "require_approval":
            continue
        try:
            longest = max(longest, int(p.get("timeout") or 0))
        except (TypeError, ValueError):
            continue
    if longest <= 0:
        longest = 604800  # engine default: 7 days (#4066)
    return longest + _HOOK_TIMEOUT_BUFFER_S


# ── settings.json plumbing ─────────────────────────────────────────────────

def _settings_path() -> str:
    base = os.environ.get("CLAUDE_CONFIG_DIR", "").strip() \
        or os.path.expanduser("~/.claude")
    return os.path.join(base, "settings.json")


def _read_json(path: str) -> dict:
    try:
        with open(path) as f:
            txt = f.read().strip()
        return json.loads(txt) if txt else {}
    except FileNotFoundError:
        return {}


def _write_json_atomic(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def _entry_is_ours(entry: dict) -> bool:
    for h in (entry or {}).get("hooks") or []:
        if HOOK_CMD_MARKER in (h.get("command") or ""):
            return True
    return False


def _entry_is_foreign_clawmetry(entry: dict) -> bool:
    for h in (entry or {}).get("hooks") or []:
        cmd = h.get("command") or ""
        if any(m in cmd for m in _FOREIGN_CLAWMETRY_MARKERS):
            return True
    return False


def _read_state() -> dict:
    try:
        with open(_STATE_PATH) as f:
            return json.load(f) or {}
    except Exception:
        return {}


def _write_state(state: dict) -> None:
    try:
        _write_json_atomic(_STATE_PATH, state)
    except Exception:
        pass


def _clear_state() -> None:
    try:
        os.remove(_STATE_PATH)
    except FileNotFoundError:
        pass
    except Exception:
        pass


def _hook_command(base: str) -> str:
    py = sys.executable or "python3"
    return f"{py} -m clawmetry hook claude-code --base {base}"


def _ensure_marker() -> bool:
    """Mark claude_code as hook-covered in hooks_installed.json so the
    reactive watcher stops double-gating it (approvals._hook_covered_
    runtimes). Never overwrites a manual `clawmetry hooks install` entry
    (that one already covers PreToolUse and is owned by the user).
    Returns True when WE wrote/own the entry (tagged via='gate')."""
    data = _read_json(_MARKER_PATH)
    existing = data.get("claude_code")
    if isinstance(existing, dict) and existing.get("via") != "gate":
        return False  # manual install owns it — leave alone
    entry = {"events": ["PreToolUse"], "via": "gate",
             "installed_at": _utcnow()}
    if isinstance(existing, dict) and \
            existing.get("events") == entry["events"]:
        return True  # already ours, already correct
    data["claude_code"] = entry
    _write_json_atomic(_MARKER_PATH, data)
    return True


def _remove_marker_if_ours() -> None:
    data = _read_json(_MARKER_PATH)
    entry = data.get("claude_code")
    if isinstance(entry, dict) and entry.get("via") == "gate":
        data.pop("claude_code", None)
        _write_json_atomic(_MARKER_PATH, data)


# ── the gate handler ───────────────────────────────────────────────────────

def gate_handler(want_gate: bool, policies) -> None:
    """GATE_HANDLERS['claude_code'] entry — idempotent install/refresh/remove
    of OUR PreToolUse hook entry. Never raises (sync_runtime_gates would
    swallow it anyway, but a gate that half-writes settings.json is worse
    than one that skips a beat)."""
    try:
        if want_gate:
            _install(policies)
        else:
            _uninstall()
    except Exception:
        pass


def _install(policies) -> None:
    path = _settings_path()
    settings = _read_json(path)
    hooks = settings.setdefault("hooks", {})
    pretool = hooks.setdefault("PreToolUse", [])

    # A manual `clawmetry hooks install` (cloud path) already gates
    # claude_code — stacking our entry would double-pause every call.
    if any(_entry_is_foreign_clawmetry(e) for e in pretool
           if isinstance(e, dict)):
        st = _read_state()
        if not st.get("installed"):
            _write_state({"installed": False, "skipped": "manual-hook-present",
                          "checked_at": _utcnow()})
        return

    base = dashboard_base()
    command = _hook_command(base)
    matcher = _matcher_from_policies(policies)
    timeout = _timeout_from_policies(policies)
    desired = {
        "matcher": matcher,
        "hooks": [{"type": "command", "command": command,
                   "timeout": timeout}],
    }

    ours = [e for e in pretool if isinstance(e, dict) and _entry_is_ours(e)]
    if len(ours) == 1 and ours[0] == desired:
        _ensure_marker()  # cheap self-heal if the marker was deleted
        return  # already exactly in place — the common every-2s no-op
    # Replace ours (if any, or stale duplicates) with the single fresh entry.
    kept = [e for e in pretool
            if not (isinstance(e, dict) and _entry_is_ours(e))]
    kept.append(desired)
    hooks["PreToolUse"] = kept
    _write_json_atomic(path, settings)
    marker_written = _ensure_marker()
    _write_state({
        "installed": True,
        "settings_path": path,
        "command": command,
        "matcher": matcher,
        "timeout": timeout,
        "base": base,
        "marker_written": marker_written,
        "installed_at": _utcnow(),
    })


def _uninstall() -> None:
    st = _read_state()
    if not st.get("installed"):
        # We never installed (or already removed) — never touch a hook the
        # operator (or `clawmetry hooks install`) put there themselves.
        return
    path = st.get("settings_path") or _settings_path()
    settings = _read_json(path)
    hooks = settings.get("hooks") or {}
    pretool = hooks.get("PreToolUse")
    if isinstance(pretool, list):
        kept = [e for e in pretool
                if not (isinstance(e, dict) and _entry_is_ours(e))]
        if len(kept) != len(pretool):
            if kept:
                hooks["PreToolUse"] = kept
            else:
                hooks.pop("PreToolUse", None)
            if not hooks:
                settings.pop("hooks", None)
            _write_json_atomic(path, settings)
    if st.get("marker_written"):
        _remove_marker_if_ours()
    _clear_state()


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ── hook client (`clawmetry hook claude-code --base <url>`) ────────────────

_CONNECT_TIMEOUT_S = 3          # server must accept fast or we have no opinion
_REQUEST_TIMEOUT_S = 45         # per-POST ceiling (server slices at ~20 s)
_MAX_TRANSIENT_FAILURES = 3     # consecutive network errors before fail-open


def _post_json(url: str, payload: dict, timeout: float) -> "dict | None":
    """POST JSON, return parsed dict or None on any failure. stdlib-only."""
    import urllib.request
    try:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def hook_main(argv: "list | None" = None) -> int:
    """Entry point for the `clawmetry hook claude-code` fast path.

    ALWAYS returns 0. Output contract: on a decision, print the receiver's
    ``hookSpecificOutput`` envelope to stdout; on ANY failure print nothing
    (no opinion → Claude Code's normal permission flow)."""
    argv = list(argv or [])
    if not argv or argv[0] != "claude-code":
        return 0  # unknown subtarget → no opinion, never break the agent
    base = ""
    if "--base" in argv:
        try:
            base = argv[argv.index("--base") + 1].rstrip("/")
        except IndexError:
            base = ""
    if not base:
        base = dashboard_base()
    url = f"{base}/api/hooks/claude-code/pretooluse"

    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
        if not isinstance(event, dict):
            return 0
    except Exception:
        return 0

    payload = {
        "tool_name": event.get("tool_name") or "",
        "tool_input": event.get("tool_input") or {},
        "session_id": event.get("session_id") or "",
        "cwd": event.get("cwd") or "",
        "hook_event_name": event.get("hook_event_name") or "PreToolUse",
        "permission_mode": event.get("permission_mode") or "",
        "tool_use_id": event.get("tool_use_id") or "",
    }

    # First POST gets a short connect budget: a dashboard that isn't
    # running must cost ~nothing per tool call.
    resp = _post_json(url, payload, _CONNECT_TIMEOUT_S)
    failures = 0
    while True:
        if resp is None:
            failures += 1
            if failures >= _MAX_TRANSIENT_FAILURES:
                return 0  # fail-open
            time.sleep(1.0)
            resp = _post_json(url, payload, _REQUEST_TIMEOUT_S)
            continue
        failures = 0
        if not isinstance(resp, dict):
            return 0
        if resp.get("status") == "pending" and resp.get("approval_id"):
            # Parked in the local queue — poll without duplicating the row.
            payload["approval_id"] = resp["approval_id"]
            try:
                wait_s = max(0.2, float(resp.get("retry_after_ms") or 2000)
                             / 1000.0)
            except (TypeError, ValueError):
                wait_s = 2.0
            time.sleep(wait_s)
            resp = _post_json(url, payload, _REQUEST_TIMEOUT_S)
            continue
        hso = resp.get("hookSpecificOutput")
        if isinstance(hso, dict) and hso.get("permissionDecision"):
            try:
                sys.stdout.write(json.dumps({"hookSpecificOutput": hso}))
            except Exception:
                pass
            return 0
        return 0  # no decision in the response → no opinion
