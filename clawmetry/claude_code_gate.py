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

from clawmetry import hook_ownership

# ── paths / markers ────────────────────────────────────────────────────────

_STATE_PATH = os.path.expanduser("~/.clawmetry/claude_code_gate.json")
_MIRROR_STATE_PATH = os.path.expanduser("~/.clawmetry/claude_code_mirror.json")
_SERVER_INFO_PATH = os.path.expanduser("~/.clawmetry/server.json")
# Shared with hooks_claude_code.py / approvals._hook_covered_runtimes: a
# "claude_code" entry whose events include PreToolUse tells the reactive
# watcher this runtime is pre-execution gated, so it must NOT double-file
# approvals (and kill sessions) for tool calls the hook already paused.
_MARKER_PATH = os.path.expanduser("~/.clawmetry/hooks_installed.json")

# Any hook command containing this is OURS (the local-first gate).
# Form-agnostic: matches BOTH the legacy "<py> -m clawmetry hook claude-code"
# written by older releases and the console-script form written now, so an
# existing entry is replaced rather than stacked beside a second gate.
HOOK_CMD_MARKER = "clawmetry hook claude-code"
# …and this one is the MIRROR hook (PermissionRequest). Distinct marker so
# each installer only ever removes its own entry. NOTE the ordering trap:
# this string CONTAINS HOOK_CMD_MARKER, so any "is it ours?" test for the
# PreToolUse gate must exclude mirror commands explicitly (_entry_is_ours).
MIRROR_CMD_MARKER = "clawmetry hook claude-code-permission"
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
            if p.get("min_risk") or (
                    isinstance(p.get("match"), dict)
                    and p["match"].get("min_risk")):
                # Risk-gated tool-agnostic policy ("pause anything high
                # risk"): the risk classifier scores exec, write, web AND
                # read calls, so the hook must see all of them — a
                # Bash-only matcher would silently skip a critical
                # ``Write /etc/hosts`` while promising risk coverage.
                for frag in _CANON_TO_MATCHER.values():
                    _add(frag)
            else:
                _add("Bash")
            continue
        canon = _canonical_tool(tool)
        _add(_CANON_TO_MATCHER.get(canon, tool))
    return "|".join(parts) if parts else "Bash"


def _question_gate_enabled() -> bool:
    """Question-set approvals (WO-52): on by default, one env var off."""
    return os.environ.get("CLAWMETRY_QUESTION_GATE", "1").strip() != "0"


def _question_window_s() -> int:
    """Mirror of routes.hooks._question_window_s (stdlib-only fast path
    must not import Flask modules): env override → mirror window → 180 s."""
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
    # Bounded: a wedged hook must not sit on the user's tool call for a
    # week. See hook_ownership.clamp_hook_timeout for the trade-off.
    return hook_ownership.clamp_hook_timeout(longest + _HOOK_TIMEOUT_BUFFER_S)


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


def _hook_is_ours(hook: dict) -> bool:
    """Hook-level twin of :func:`_entry_is_ours` — same mirror carve-out.

    The mirror hook carries its own marker and is owned by
    ``_install_mirror``; the gate must not prune it.

    Both tests run against ``hook_ownership.normalize_command``, never the
    raw string: the launcher is shell-quoted whenever its path contains a
    space, which puts a quote exactly where the marker expects a space.
    See that function for what a raw-string test cost us.
    """
    cmd = hook_ownership.normalize_command((hook or {}).get("command") or "")
    if MIRROR_CMD_MARKER in cmd:
        return False
    return HOOK_CMD_MARKER in cmd


def _entry_is_ours(entry: dict) -> bool:
    for h in (entry or {}).get("hooks") or []:
        cmd = hook_ownership.normalize_command(h.get("command") or "")
        if MIRROR_CMD_MARKER in cmd:
            continue  # the mirror hook is owned by _install_mirror
        if HOOK_CMD_MARKER in cmd:
            return True
    return False


def _entry_is_mirror(entry: dict) -> bool:
    for h in (entry or {}).get("hooks") or []:
        cmd = hook_ownership.normalize_command(h.get("command") or "")
        if MIRROR_CMD_MARKER in cmd:
            return True
    return False


def _cmd_binary_exists(cmd: str) -> bool:
    """Return True if the hook command's binary is runnable.

    Only validates absolute paths — bare command names depend on PATH at
    execution time and cannot be reliably pre-checked here.
    """
    if not cmd:
        return False
    return hook_ownership.command_binary_exists(cmd)


def _hook_is_stale_ours(hook: dict) -> bool:
    """One of ours whose launcher is gone from disk.

    This is the wreckage a broken uninstall leaves: an entry naming a binary
    that no longer exists, so the runtime reports a hook error on every
    single tool call. Whoever installs next is the only process still
    running that can recognise it, so the installer clears it.
    """
    return _hook_is_ours(hook) and not _cmd_binary_exists(
        (hook or {}).get("command") or "")


def _entry_is_foreign_clawmetry(entry: dict) -> bool:
    for h in (entry or {}).get("hooks") or []:
        cmd = hook_ownership.normalize_command(h.get("command") or "")
        if any(m in cmd for m in _FOREIGN_CLAWMETRY_MARKERS):
            if _cmd_binary_exists(h.get("command") or ""):
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


def _windowless_python(py: str, is_windows: bool, exists=os.path.exists) -> str:
    """python.exe is a console executable: when Claude Code runs under a
    windowless parent (the desktop app), every hook invocation makes Windows
    allocate a VISIBLE console — and a gated call keeps it on screen until
    the human decides. pythonw.exe (same dir, GUI subsystem) never allocates
    one; the hook still talks over the pipes Claude Code attaches, and
    hook_main tolerates absent std streams (fail-open). Pure function so the
    swap is testable on any OS."""
    if is_windows and py.lower().endswith("python.exe"):
        pyw = os.path.join(os.path.dirname(py), "pythonw.exe")
        if exists(pyw):
            return pyw
    return py


def _console_script() -> "str | None":
    """Absolute path of the installed ``clawmetry`` console script, if any.

    Preferred over ``python -m clawmetry`` because Claude Code spawns the
    hook with the AGENT'S working directory, which ``-m`` puts first on
    ``sys.path``: any project containing a ``clawmetry/`` folder shadows the
    installed package, the subcommand is rejected, and the hook errors. Claude
    Code treats that as a non-blocking error, so the call proceeds ungated —
    the gate silently does nothing, which is exactly the failure mode this
    module's logging rule exists to prevent. A console script sets
    ``sys.path[0]`` to its own bin directory, so the working directory can
    never shadow the package. (The same defect DENIED calls on Copilot, where
    a hook error is a refusal; see clawmetry/runtime_gates.py.)

    None when no script sits next to the running interpreter (pipx / unusual
    layouts), in which case the caller falls back to ``-m``.
    """
    exe = sys.executable or ""
    if not exe:
        return None
    name = "clawmetry.exe" if os.name == "nt" else "clawmetry"
    cand = os.path.join(os.path.dirname(exe), name)
    try:
        if os.path.isfile(cand) and (os.name == "nt" or os.access(cand, os.X_OK)):
            return cand
    except Exception:  # noqa: BLE001
        return None
    return None


def _launcher_prefix() -> str:
    """Quoted launcher + any ``-m`` suffix, shared by both hook commands.

    The path is quoted because ``sys.executable`` routinely contains a space
    (``/Users/First Last/venv/bin/python``) and Claude Code shell-splits the
    command."""
    script = _console_script()
    launcher = script or _windowless_python(
        sys.executable or "python3", os.name == "nt")
    if os.name == "nt":
        import subprocess as _sp
        quoted = _sp.list2cmdline([launcher])
    else:
        import shlex as _shlex
        quoted = _shlex.quote(launcher)
    return quoted if script else f"{quoted} -m clawmetry"


def _hook_command(base: str) -> str:
    return f"{_launcher_prefix()} hook claude-code --base {base}"


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
    than one that skips a beat).

    Also drives the MIRROR hook (PermissionRequest), which is independent
    of the policy set: mirroring is on when the operator turned it on for
    claude_code in the approval routing config, whether or not they wrote
    a single protection rule."""
    try:
        if want_gate:
            _install(policies)
        else:
            _uninstall()
    except Exception:
        pass
    try:
        _sync_mirror()
    except Exception:
        pass


# ── mirror mode: Claude Code's OWN permission prompts ──────────────────────
# PreToolUse only fires for tools our policies name. The thing that actually
# stalls a session is Claude Code deciding, on its own, that it needs the
# user's permission — you find out by looking at the terminal, and unblock
# it by ticking a box in /permissions.
#
# PermissionRequest fires at exactly that moment and accepts a decision, so
# mirroring turns "walk back to the laptop" into "tap Approve on your
# phone". The fallback is the important part: our receiver answers "ask"
# once the mirror window elapses, which is Claude Code's own prompt — so
# the worst case is today's behaviour, never a call that silently hangs.

def _mirror_wanted() -> bool:
    """Ask the delivery layer whether to arm the mirror.

    Answered through the ``clawmetry.approval_events`` seam, so this module
    never imports the paid delivery package directly. Nothing registered
    (an OSS install with no paid package) answers False, and the mirror
    hook is simply never installed — the node keeps Claude Code's own
    terminal prompt, exactly as before the mirror existed.
    """
    try:
        from clawmetry import approval_events as _ae
        return _ae.mirror_wanted("claude_code")
    except Exception:
        return False


def _mirror_command(base: str) -> str:
    return f"{_launcher_prefix()} hook claude-code-permission --base {base}"


def mirror_timeout_s() -> int:
    """How long the phone gets before the terminal prompt takes over."""
    try:
        from clawmetry import approval_events as _ae
        return _ae.mirror_window_s("claude_code")
    except Exception:
        return 180


def _sync_mirror() -> None:
    if _mirror_wanted():
        _install_mirror()
    else:
        _uninstall_mirror()


def _install_mirror() -> None:
    path = _settings_path()
    settings = _read_json(path)
    hooks = settings.setdefault("hooks", {})
    entries = hooks.setdefault("PermissionRequest", [])
    base = dashboard_base()
    command = _mirror_command(base)
    # +15 s so OUR receiver's "ask" fallback always lands before Claude
    # Code's hook timeout would cancel us (a cancelled hook renders no
    # decision, which is the same outcome — but then the approval row is
    # left pending with nobody waiting on it).
    timeout = mirror_timeout_s() + 15
    desired = {"hooks": [{"type": "command", "command": command,
                          "timeout": timeout}]}
    ours = [e for e in entries if isinstance(e, dict) and _entry_is_mirror(e)]
    if len(ours) == 1 and ours[0] == desired:
        return
    kept = [e for e in entries
            if not (isinstance(e, dict) and _entry_is_mirror(e))]
    kept.append(desired)
    hooks["PermissionRequest"] = kept
    _write_json_atomic(path, settings)
    try:
        _write_json_atomic(_MIRROR_STATE_PATH, {
            "installed": True, "settings_path": path, "command": command,
            "timeout": timeout, "base": base, "installed_at": _utcnow()})
    except Exception:
        pass


def _mirror_hook_is_ours(hook: dict) -> bool:
    cmd = hook_ownership.normalize_command((hook or {}).get("command") or "")
    return MIRROR_CMD_MARKER in cmd


def _uninstall_mirror() -> None:
    st = _read_json(_MIRROR_STATE_PATH)
    path = st.get("settings_path") or _settings_path()
    if not st.get("installed"):
        # No record of installing, so a LIVE mirror entry is not ours to
        # remove. A dead one is — same reasoning as _uninstall's stale
        # sweep: our state dir can be purged out from under an entry that
        # then errors on every permission prompt with nobody to clean it.
        settings = _read_json(path)
        hooks = settings.get("hooks") or {}
        entries = hooks.get("PermissionRequest")
        if isinstance(entries, list):
            kept, n = hook_ownership.prune_our_hooks(
                entries, (MIRROR_CMD_MARKER,),
                ours_pred=lambda h: (_mirror_hook_is_ours(h)
                                     and not _cmd_binary_exists(
                                         (h or {}).get("command") or "")))
            if n:
                if kept:
                    hooks["PermissionRequest"] = kept
                else:
                    hooks.pop("PermissionRequest", None)
                if not hooks:
                    settings.pop("hooks", None)
                _write_json_atomic(path, settings)
        return
    settings = _read_json(path)
    hooks = settings.get("hooks") or {}
    entries = hooks.get("PermissionRequest")
    if isinstance(entries, list):
        kept = [e for e in entries
                if not (isinstance(e, dict) and _entry_is_mirror(e))]
        if len(kept) != len(entries):
            if kept:
                hooks["PermissionRequest"] = kept
            else:
                hooks.pop("PermissionRequest", None)
            if not hooks:
                settings.pop("hooks", None)
            _write_json_atomic(path, settings)
    try:
        os.remove(_MIRROR_STATE_PATH)
    except Exception:
        pass


def mirror_status() -> dict:
    """What the Approvals tab shows next to the mirror toggle."""
    st = _read_json(_MIRROR_STATE_PATH)
    return {
        "wanted": _mirror_wanted(),
        "installed": bool(st.get("installed")),
        "timeout_s": mirror_timeout_s(),
        "settings_path": st.get("settings_path") or _settings_path(),
        "installed_at": st.get("installed_at"),
    }


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
    # Question-set approvals (WO-52 phase 1): whenever the gate is armed,
    # also watch AskUserQuestion so the receiver can mirror the runtime's
    # structured questions to the dashboard, which answers with the actual
    # option labels (hookSpecificOutput.updatedInput). No answer inside the
    # question window → the receiver replies "ask" and the terminal prompt
    # takes over, exactly today's flow. CLAWMETRY_QUESTION_GATE=0 opts out.
    if _question_gate_enabled():
        if "AskUserQuestion" not in matcher.split("|"):
            matcher = f"{matcher}|AskUserQuestion"
        # The hook timeout must outlive the question window, or Claude Code
        # cancels the hook before our own "ask" fallback lands and the
        # parked row is left pending with nobody waiting on it.
        timeout = max(timeout, hook_ownership.clamp_hook_timeout(
            _question_window_s() + _HOOK_TIMEOUT_BUFFER_S))
    desired = {
        "matcher": matcher,
        "hooks": [{"type": "command", "command": command,
                   "timeout": timeout}],
    }

    ours = [e for e in pretool if isinstance(e, dict) and _entry_is_ours(e)]
    if len(ours) == 1 and ours[0] == desired:
        _ensure_marker()  # cheap self-heal if the marker was deleted
        return  # already exactly in place — the common every-2s no-op
    # Replace OUR HOOKS (or stale duplicates) with the single fresh entry.
    # Hook-level, never entry-level: a co-installed writer may have merged
    # its command into the same entry as ours (`gk ai hook install
    # claude-code --force`), and this path runs every ~2s — an entry-level
    # drop would delete that writer's hook within seconds of it landing.
    kept, _ = hook_ownership.prune_our_hooks(pretool, (HOOK_CMD_MARKER,),
                                             ours_pred=_hook_is_ours)
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


def _prune_pretool(path: str, ours_pred) -> int:
    """Remove the hooks *ours_pred* claims from ``PreToolUse`` in *path*.

    Returns how many hooks were removed. Hook-level throughout, so an entry
    shared with a co-installed writer keeps that writer's command.
    """
    settings = _read_json(path)
    hooks = settings.get("hooks") or {}
    pretool = hooks.get("PreToolUse")
    if not isinstance(pretool, list):
        return 0
    kept, n_removed = hook_ownership.prune_our_hooks(
        pretool, (HOOK_CMD_MARKER,), ours_pred=ours_pred)
    if not n_removed:
        return 0
    if kept:
        hooks["PreToolUse"] = kept
    else:
        hooks.pop("PreToolUse", None)
    if not hooks:
        settings.pop("hooks", None)
    _write_json_atomic(path, settings)
    return n_removed


def _uninstall() -> None:
    st = _read_state()
    path = st.get("settings_path") or _settings_path()
    if st.get("installed"):
        _prune_pretool(path, _hook_is_ours)
    else:
        # We have no record of installing — so we do NOT remove a live hook
        # the operator (or `clawmetry hooks install`) put there themselves.
        #
        # A DEAD one is a different matter. Our state lives in
        # ``~/.clawmetry``, which an uninstall purges, and the desktop app's
        # runtime venv goes with the .app: delete either and the state that
        # proves ownership is gone while the entry naming the vanished
        # binary stays behind, erroring on every tool call with nothing left
        # that will ever clean it up. An entry carrying our marker AND
        # pointing at a launcher that no longer exists can only be ours, and
        # it cannot do anything but fail, so it goes.
        _prune_pretool(path, _hook_is_stale_ours)
    if st.get("marker_written"):
        _remove_marker_if_ours()
    _clear_state()


def uninstall_all_hooks() -> dict:
    """Remove every Claude Code settings.json hook this module installs.

    ``clawmetry uninstall`` drains the ``clawmetry.hooks`` registry, but the
    gate and the mirror are installed by this module and were never in that
    registry — so a full uninstall left both behind pointing at the binary
    it had just deleted. Called from the uninstall path; safe to call when
    nothing is installed.
    """
    out = {"gate": False, "mirror": False, "errors": []}
    for key, fn in (("gate", _uninstall), ("mirror", _uninstall_mirror)):
        try:
            fn()
            out[key] = True
        except Exception as exc:  # noqa: BLE001 — one failure must not
            # strand the other hook; the caller prints what could not go.
            out["errors"].append(f"{key}: {exc}")
    return out


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
    if not argv or argv[0] not in ("claude-code", "claude-code-permission"):
        return 0  # unknown subtarget → no opinion, never break the agent
    mirror = argv[0] == "claude-code-permission"
    base = ""
    if "--base" in argv:
        try:
            base = argv[argv.index("--base") + 1].rstrip("/")
        except IndexError:
            base = ""
    if not base:
        base = dashboard_base()
    url = (f"{base}/api/hooks/claude-code/permissionrequest" if mirror
           else f"{base}/api/hooks/claude-code/pretooluse")

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
        "hook_event_name": event.get("hook_event_name")
                           or ("PermissionRequest" if mirror else "PreToolUse"),
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
        if isinstance(hso, dict) and (hso.get("permissionDecision")
                                      or hso.get("decision")):
            # PermissionRequest speaks `decision`, PreToolUse speaks
            # `permissionDecision`. The receiver already emits the right
            # shape for its own event; print it verbatim. "ask" from the
            # mirror hook is the deliberate no-answer fallback — Claude
            # Code shows its normal prompt, exactly as it would have.
            try:
                sys.stdout.write(json.dumps({"hookSpecificOutput": hso}))
            except Exception:
                pass
            return 0
        return 0  # no decision in the response → no opinion
