"""Pre-tool gates for Cursor and GitHub Copilot CLI — "block before it runs".

Same two-halves pattern as ``clawmetry/claude_code_gate.py`` (read that
module's docstring first — the merge rules, state files, and fail-open
contract all carry over), generalised across runtimes whose native hook
systems can DENY a tool call before it executes:

* **Cursor** (IDE + `cursor-agent` CLI): Cursor Hooks, ``~/.cursor/hooks.json``
  (`{"version": 1, "hooks": {"beforeShellExecution": [entry, …], …}}`).
  Blocking events used: ``beforeShellExecution`` (payload carries the shell
  ``command`` + ``cwd``) and ``beforeMCPExecution`` (``tool_name`` +
  ``tool_input``), plus ``beforeReadFile`` when a policy gates reads or is
  risk-gated. The hook prints ``{"permission": "allow"|"deny"|"ask",
  "user_message": …, "agent_message": …}``. Fail-open: a hook that exits 0
  with no output renders no opinion; we deliberately do NOT set Cursor's
  ``failClosed`` flag — same never-break-the-agent contract as claude_code.
  (Verified live 2026-08-19 on Cursor 3.16 / CLI 2026.08.11: a deny surfaces
  to the model as a blocked call with our reason.)

* **GitHub Copilot CLI**: hook config files under ``$COPILOT_HOME/hooks/``
  (default ``~/.copilot/hooks/``). We own a whole file
  (``clawmetry.json``) instead of merging into a shared one — Copilot loads
  every ``hooks/*.json``, so install/uninstall is write/delete of our file
  and can never clobber a foreign entry. Event ``preToolUse`` (camelCase =
  native payload: ``{sessionId, timestamp, cwd, toolName, toolArgs}`` where
  ``toolArgs`` is frequently a JSON *string*). The hook prints
  ``{"permissionDecision": "allow"|"deny"|"ask",
  "permissionDecisionReason": …}`` (reason required on deny). Copilot
  command preToolUse hooks are fail-closed on CRASH but treat empty output
  as "no opinion" — our client always exits 0, so failures stay fail-open.
  (Verified live 2026-08-19 on Copilot CLI 1.0.80.)

Both clients POST to the runtime's own receiver
(``/api/hooks/<runtime>/pretooluse`` in routes/hooks.py) so approvals are
attributed to the RIGHT runtime — reusing the claude-code receiver would
file every Cursor/Copilot pause as a claude_code approval.

Stdlib-only: the hook fast path runs on every gated tool call.
"""
from __future__ import annotations

import json
import logging
import os
import shlex
import sys
import time

from clawmetry import hook_ownership

from clawmetry.claude_code_gate import (
    _post_json,
    _read_json,
    _windowless_python,
    _write_json_atomic,
    dashboard_base,
)

_MARKER_PATH = os.path.expanduser("~/.clawmetry/hooks_installed.json")
_HOOK_TIMEOUT_BUFFER_S = 60

_CONNECT_TIMEOUT_S = 3
_REQUEST_TIMEOUT_S = 45
_MAX_TRANSIENT_FAILURES = 3


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


log = logging.getLogger("clawmetry.runtime_gates")


def _hook_command(runtime_slug: str, base: str) -> str:
    r"""The hook command line each runtime will execute.

    The interpreter path is QUOTED: ``sys.executable`` routinely contains a
    space (``/Users/First Last/venv/bin/python``, ``C:\Program Files\...``)
    and these runtimes shell-split the command. An unquoted path split at the
    space into a "command not found", and a Copilot ``preToolUse`` command
    hook that exits non-zero is fail-CLOSED — every gated tool call would be
    denied. Found in review before this ever shipped."""
    launcher = _console_script() or _windowless_python(
        sys.executable or "python3", os.name == "nt")
    if os.name == "nt":
        import subprocess as _sp
        quoted = _sp.list2cmdline([launcher])
    else:
        quoted = shlex.quote(launcher)
    suffix = "" if _console_script() else " -m clawmetry"
    return f"{quoted}{suffix} hook {runtime_slug} --base {base}"


def _console_script() -> "str | None":
    """Absolute path of the installed ``clawmetry`` console script, if any.

    Preferred over ``python -m clawmetry`` because the runtimes spawn the
    hook with the AGENT'S working directory. For ``-m``, Python puts that
    directory first on ``sys.path``, so any project containing a
    ``clawmetry/`` folder shadows the installed package: the import resolves
    to the user's own directory, argparse rejects the ``hook`` subcommand,
    and the process exits non-zero. On Copilot a non-zero command hook is
    fail-CLOSED, so that would deny EVERY tool call for anyone whose repo has
    a directory of that name (this repo included). A console script sets
    ``sys.path[0]`` to its own bin directory instead, so the working
    directory can never shadow the package.

    Returns None when no script sits next to the running interpreter (pipx /
    unusual layouts), in which case the caller falls back to ``-m``.
    """
    exe = sys.executable or ""
    if not exe:
        return None
    bindir = os.path.dirname(exe)
    name = "clawmetry.exe" if os.name == "nt" else "clawmetry"
    cand = os.path.join(bindir, name)
    try:
        if os.path.isfile(cand) and (os.name == "nt" or os.access(cand, os.X_OK)):
            return cand
    except Exception:  # noqa: BLE001
        return None
    return None


def _timeout_from_policies(policies) -> int:
    """Longest matching require_approval window + buffer (mirrors
    claude_code_gate._timeout_from_policies)."""
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
        longest = 604800
    # Bounded — this one lands on Copilot, whose preToolUse gate is
    # FAIL-CLOSED on crash/non-zero exit. See hook_ownership.
    return hook_ownership.clamp_hook_timeout(longest + _HOOK_TIMEOUT_BUFFER_S)


def _policies_gate_reads(policies) -> bool:
    """True when some require_approval policy covers reads — either an
    explicit read tool or a risk-gated tool-agnostic rule (the risk
    classifier scores read calls too, so the hook must see them)."""
    try:
        from clawmetry.approvals import _canonical_tool
    except Exception:
        def _canonical_tool(name):  # type: ignore
            return (name or "").strip().lower()
    for p in policies or []:
        if not isinstance(p, dict):
            continue
        if (p.get("action") or "require_approval") != "require_approval":
            continue
        tool = str(p.get("tool") or "").strip()
        if tool == "":
            if p.get("min_risk") or (isinstance(p.get("match"), dict)
                                     and p["match"].get("min_risk")):
                return True
            continue
        if _canonical_tool(tool) == "read":
            return True
    return False


def _policies_gate_uncovered_tools(policies, covered: "set") -> bool:
    """True when some require_approval policy targets a tool category our
    installed hook events do NOT see.

    This decides whether we may claim hook coverage. Cursor's blocking events
    cover exec (shell), MCP tools and (optionally) reads — but NOT file
    writes. Claiming blanket coverage for a write-only policy told the
    reactive watcher to skip the runtime entirely, so the policy would have
    been enforced by nobody (found in review). When anything is uncovered we
    leave the marker off and the after-the-fact watcher keeps working."""
    try:
        from clawmetry.approvals import _canonical_tool
    except Exception:
        def _canonical_tool(name):  # type: ignore
            return (name or "").strip().lower()
    for p in policies or []:
        if not isinstance(p, dict):
            continue
        if (p.get("action") or "require_approval") != "require_approval":
            continue
        tool = str(p.get("tool") or "").strip()
        if tool == "":
            # Tool-agnostic (incl. risk-gated): spans every category.
            return True
        if _canonical_tool(tool) not in covered:
            return True
    return False


def _ensure_marker(runtime: str) -> bool:
    """Mark ``runtime`` as pre-execution hook-covered (see
    approvals._hook_covered_runtimes) so the reactive watcher doesn't
    double-file approvals for calls the hook already paused."""
    data = _read_json(_MARKER_PATH)
    existing = data.get(runtime)
    if isinstance(existing, dict) and existing.get("via") != "gate":
        return False
    entry = {"events": ["PreToolUse"], "via": "gate",
             "installed_at": _utcnow()}
    if isinstance(existing, dict) and existing.get("events") == entry["events"]:
        return True
    data[runtime] = entry
    _write_json_atomic(_MARKER_PATH, data)
    return True


def _remove_marker_if_ours(runtime: str) -> None:
    data = _read_json(_MARKER_PATH)
    entry = data.get(runtime)
    if isinstance(entry, dict) and entry.get("via") == "gate":
        data.pop(runtime, None)
        _write_json_atomic(_MARKER_PATH, data)


# ═══════════════════════════════════════════════════════════════════════════
# Cursor
# ═══════════════════════════════════════════════════════════════════════════

_CURSOR_STATE_PATH = os.path.expanduser("~/.clawmetry/cursor_gate.json")
# Deliberately form-agnostic: matches BOTH "<py> -m clawmetry hook cursor"
# (how we used to write it, still present in older installs) and
# "<prefix>/bin/clawmetry hook cursor" (what we write now). An entry is ours
# if it carries this substring, whichever launcher form it uses.
CURSOR_CMD_MARKER = "clawmetry hook cursor"

# Blocking Cursor hook events we install on. beforeShellExecution +
# beforeMCPExecution are always gated (exec is what policies overwhelmingly
# target); beforeReadFile joins when a policy actually covers reads.
_CURSOR_BASE_EVENTS = ("beforeShellExecution", "beforeMCPExecution")
_CURSOR_READ_EVENT = "beforeReadFile"


def _cursor_hooks_path() -> str:
    override = os.environ.get("CLAWMETRY_CURSOR_HOOKS_PATH", "").strip()
    if override:
        return os.path.expanduser(override)
    return os.path.expanduser("~/.cursor/hooks.json")


def _cursor_entry_is_ours(entry: dict) -> bool:
    return CURSOR_CMD_MARKER in str((entry or {}).get("command") or "")


def cursor_gate_handler(want_gate: bool, policies) -> None:
    """GATE_HANDLERS['cursor'] — idempotent install/refresh/remove of OUR
    entries in ~/.cursor/hooks.json. Never raises."""
    try:
        if want_gate:
            _cursor_install(policies)
        else:
            _cursor_uninstall()
    except Exception as e:  # noqa: BLE001 - a gate must never kill the watcher
        # Logged, not swallowed silently: a gate that never installed is
        # otherwise indistinguishable from one that did.
        log.warning("cursor gate sync failed (%s): %s", type(e).__name__, e)


def _cursor_install(policies) -> None:
    path = _cursor_hooks_path()
    config = _read_json(path)
    if not isinstance(config, dict):
        config = {}
    config.setdefault("version", 1)
    hooks = config.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        return  # unrecognisable foreign shape — never guess-rewrite it

    base = dashboard_base()
    command = _hook_command("cursor", base)
    timeout = _timeout_from_policies(policies)
    desired_entry = {"type": "command", "command": command, "timeout": timeout}

    events = list(_CURSOR_BASE_EVENTS)
    covered = {"exec", "web", "search"}  # shell + MCP tool calls
    if _policies_gate_reads(policies):
        events.append(_CURSOR_READ_EVENT)
        covered.add("read")

    changed = False
    for ev in events:
        entries = hooks.setdefault(ev, [])
        if not isinstance(entries, list):
            continue
        ours = [e for e in entries
                if isinstance(e, dict) and _cursor_entry_is_ours(e)]
        if len(ours) == 1 and ours[0] == desired_entry:
            continue
        kept = [e for e in entries
                if not (isinstance(e, dict) and _cursor_entry_is_ours(e))]
        kept.append(dict(desired_entry))
        hooks[ev] = kept
        changed = True
    # An event we previously installed but no longer want (e.g. the read
    # gate was removed) — strip our entry from every OTHER event list.
    for ev, entries in list(hooks.items()):
        if ev in events or not isinstance(entries, list):
            continue
        kept = [e for e in entries
                if not (isinstance(e, dict) and _cursor_entry_is_ours(e))]
        if len(kept) != len(entries):
            if kept:
                hooks[ev] = kept
            else:
                hooks.pop(ev, None)
            changed = True

    if changed:
        _write_json_atomic(path, config)
    # Only claim coverage when our events see every gated category; otherwise
    # the reactive watcher must keep covering this runtime (see
    # _policies_gate_uncovered_tools).
    if _policies_gate_uncovered_tools(policies, covered):
        _remove_marker_if_ours("cursor")
        marker_written = False
    else:
        marker_written = _ensure_marker("cursor")
    st = _read_json(_CURSOR_STATE_PATH)
    if changed or not st.get("installed"):
        _write_json_atomic(_CURSOR_STATE_PATH, {
            "installed": True, "hooks_path": path, "command": command,
            "events": events, "timeout": timeout, "base": base,
            "marker_written": marker_written, "installed_at": _utcnow()})


def _cursor_uninstall() -> None:
    st = _read_json(_CURSOR_STATE_PATH)
    if not st.get("installed"):
        return  # never installed by us — never touch a foreign hook
    path = st.get("hooks_path") or _cursor_hooks_path()
    config = _read_json(path)
    hooks = config.get("hooks") if isinstance(config, dict) else None
    if isinstance(hooks, dict):
        changed = False
        for ev, entries in list(hooks.items()):
            if not isinstance(entries, list):
                continue
            kept = [e for e in entries
                    if not (isinstance(e, dict) and _cursor_entry_is_ours(e))]
            if len(kept) != len(entries):
                if kept:
                    hooks[ev] = kept
                else:
                    hooks.pop(ev, None)
                changed = True
        if changed:
            if not hooks:
                config.pop("hooks", None)
            _write_json_atomic(path, config)
    if st.get("marker_written"):
        _remove_marker_if_ours("cursor")
    try:
        os.remove(_CURSOR_STATE_PATH)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# GitHub Copilot CLI
# ═══════════════════════════════════════════════════════════════════════════

_COPILOT_STATE_PATH = os.path.expanduser("~/.clawmetry/copilot_gate.json")
COPILOT_CMD_MARKER = "clawmetry hook copilot"  # form-agnostic, see CURSOR_CMD_MARKER
_COPILOT_GATE_BASENAME = "clawmetry.json"


def _copilot_hooks_dir() -> str:
    base = os.environ.get("COPILOT_HOME", "").strip() \
        or os.path.expanduser("~/.copilot")
    return os.path.join(os.path.expanduser(base), "hooks")


def copilot_gate_handler(want_gate: bool, policies) -> None:
    """GATE_HANDLERS['copilot'] — we own the whole hooks/clawmetry.json
    file, so install is an atomic write and uninstall a delete. Never
    raises."""
    try:
        if want_gate:
            _copilot_install(policies)
        else:
            _copilot_uninstall()
    except Exception as e:  # noqa: BLE001 - a gate must never kill the watcher
        log.warning("copilot gate sync failed (%s): %s", type(e).__name__, e)


def _copilot_install(policies) -> None:
    path = os.path.join(_copilot_hooks_dir(), _COPILOT_GATE_BASENAME)
    base = dashboard_base()
    command = _hook_command("copilot", base)
    timeout = _timeout_from_policies(policies)
    desired = {
        "version": 1,
        "hooks": {
            "preToolUse": [{
                # `command` is Copilot's cross-platform field (copied to both
                # bash and powershell when those are absent).
                "type": "command",
                "command": command,
                "timeoutSec": timeout,
            }],
        },
    }
    current = _read_json(path)
    marker_written = _ensure_marker("copilot")
    st = _read_json(_COPILOT_STATE_PATH)
    if current == desired and st.get("installed"):
        return
    if current != desired:
        _write_json_atomic(path, desired)
    # Self-heal the state file even when the hook file was already correct:
    # without this, a deleted state file made uninstall a permanent no-op and
    # our hook stayed installed forever (found in review).
    _write_json_atomic(_COPILOT_STATE_PATH, {
        "installed": True, "hooks_path": path, "command": command,
        "timeout": timeout, "base": base,
        "marker_written": marker_written, "installed_at": _utcnow()})


def _copilot_uninstall() -> None:
    st = _read_json(_COPILOT_STATE_PATH)
    if not st.get("installed"):
        return
    path = st.get("hooks_path") \
        or os.path.join(_copilot_hooks_dir(), _COPILOT_GATE_BASENAME)
    # Only delete a file that is still OURS (marker in the command).
    current = _read_json(path)
    blob = json.dumps(current) if current else ""
    if COPILOT_CMD_MARKER in blob:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        except Exception:
            pass
    if st.get("marker_written"):
        _remove_marker_if_ours("copilot")
    try:
        os.remove(_COPILOT_STATE_PATH)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# Hook clients (`clawmetry hook cursor|copilot --base <url>`)
# ═══════════════════════════════════════════════════════════════════════════

def _read_stdin_event() -> dict:
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
        return event if isinstance(event, dict) else {}
    except Exception:
        return {}


def _first_workspace_root(event: dict) -> str:
    """First entry of Cursor's ``workspace_roots``, defensively.

    The field is documented as a list of folder paths, but a hook client must
    never assume a payload shape: a dict/int/None here previously raised
    (KeyError/TypeError) out of the client, which for Copilot means a denied
    tool call. Anything unexpected yields ''."""
    roots = event.get("workspace_roots")
    if isinstance(roots, (list, tuple)) and roots:
        first = roots[0]
        return first if isinstance(first, str) else ""
    return ""


def _cursor_payload(event: dict) -> dict:
    """Map a Cursor hook stdin event onto the receiver's neutral shape.

    beforeShellExecution has no tool_name — synthesize Bash so policies
    authored as 'exec'/'Bash' match; beforeMCPExecution/preToolUse carry
    their own tool_name/tool_input."""
    hook_event = str(event.get("hook_event_name") or "")
    tool_name = str(event.get("tool_name") or "").strip()
    tool_input = event.get("tool_input")
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    if not tool_name and event.get("command") is not None:
        tool_name = "Bash"
        tool_input = {"command": str(event.get("command") or "")}
    elif not tool_name and hook_event == "beforeReadFile":
        tool_name = "Read"
        tool_input = {"file_path": str(event.get("file_path") or "")}
    return {
        "tool_name": tool_name,
        "tool_input": tool_input,
        # conversation_id is Cursor's stable per-conversation handle; the
        # per-run session_id changes every generation.
        "session_id": str(event.get("conversation_id")
                          or event.get("session_id") or ""),
        "cwd": str(event.get("cwd") or _first_workspace_root(event) or ""),
        "hook_event_name": hook_event or "beforeShellExecution",
        "tool_use_id": str(event.get("generation_id") or ""),
    }


def _copilot_payload(event: dict) -> dict:
    """Map a Copilot CLI camelCase preToolUse stdin event. ``toolArgs`` is
    frequently a JSON string — parse it when possible."""
    args = event.get("toolArgs")
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
            args = parsed if isinstance(parsed, dict) else {"raw": args}
        except Exception:
            args = {"raw": args}
    if not isinstance(args, dict):
        args = {}
    return {
        "tool_name": str(event.get("toolName") or event.get("tool_name") or ""),
        "tool_input": args,
        "session_id": str(event.get("sessionId")
                          or event.get("session_id") or ""),
        "cwd": str(event.get("cwd") or ""),
        "hook_event_name": "preToolUse",
        "tool_use_id": "",
    }


def _emit_cursor(decision: str, reason: str) -> None:
    out: dict = {"permission": decision}
    if reason and decision in ("deny", "ask"):
        out["user_message"] = reason
        out["agent_message"] = reason
    sys.stdout.write(json.dumps(out))


def _emit_copilot(decision: str, reason: str) -> None:
    out: dict = {"permissionDecision": decision}
    if decision == "deny":
        out["permissionDecisionReason"] = reason or "Denied by ClawMetry policy"
    elif reason:
        out["permissionDecisionReason"] = reason
    sys.stdout.write(json.dumps(out))


_RUNTIME_CLIENTS = {
    "cursor": (_cursor_payload, _emit_cursor),
    "copilot": (_copilot_payload, _emit_copilot),
}


def hook_main(argv: "list | None" = None) -> int:
    """`clawmetry hook cursor|copilot --base <url>` — ALWAYS returns 0.

    Total fail-open wrapper. A Copilot ``preToolUse`` COMMAND hook that
    crashes or exits non-zero is fail-CLOSED (it denies the tool), so an
    unhandled exception here would block every gated call on the user's
    machine. BaseException is caught deliberately: even an unexpected
    SystemExit/MemoryError must degrade to "no opinion", never to a denied
    agent."""
    try:
        return _hook_main_inner(argv)
    except BaseException:  # noqa: BLE001 - see docstring; must never propagate
        return 0


def _hook_main_inner(argv: "list | None" = None) -> int:
    argv = list(argv or [])
    if not argv or argv[0] not in _RUNTIME_CLIENTS:
        return 0
    runtime_slug = argv[0]
    to_payload, emit = _RUNTIME_CLIENTS[runtime_slug]
    base = ""
    if "--base" in argv:
        try:
            base = argv[argv.index("--base") + 1].rstrip("/")
        except IndexError:
            base = ""
    if not base:
        base = dashboard_base()
    url = f"{base}/api/hooks/{runtime_slug}/pretooluse"

    payload = to_payload(_read_stdin_event())

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
            decision = str(hso.get("permissionDecision"))
            reason = str(hso.get("permissionDecisionReason") or "")
            if decision not in ("allow", "deny", "ask"):
                return 0
            try:
                emit(decision, reason)
            except Exception:
                pass
            return 0
        return 0  # no decision in the response → no opinion
