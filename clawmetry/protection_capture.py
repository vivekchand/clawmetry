"""Daemon-only, bounded observations of native hook configuration.

This reads configuration through the existing runtime path resolvers. It never
installs hooks, runs a command, contacts a service, or claims runtime execution.
"""
from __future__ import annotations

import json
import logging
import os
import time

log = logging.getLogger("clawmetry.protection_capture")
_MAX_CONFIG_BYTES = 1_048_576


def _read(path):
    try:
        with open(path, "rb") as stream:
            raw = stream.read(_MAX_CONFIG_BYTES + 1)
        if len(raw) > _MAX_CONFIG_BYTES:
            return "unknown", {}
        value = json.loads(raw)
        return ("ok", value) if isinstance(value, dict) else ("unknown", {})
    except FileNotFoundError:
        return "not_configured", {}
    except (OSError, ValueError, UnicodeError):
        return "unknown", {}


def _inspect(config, status, specs):
    from clawmetry import hook_ownership as ownership
    result = {"state": "not_configured" if status != "unknown" else "unknown",
              "source": "runtime_hook_configuration", "supported": True,
              "events": [], "matchers": []}
    if status != "ok":
        return result
    hooks = config.get("hooks")
    if not isinstance(hooks, dict):
        result["state"] = "unknown" if hooks is not None else "not_configured"
        return result
    matched = []
    usable = False
    complete = True
    for event, markers, nested, label in specs:
        entries = hooks.get(event, [])
        if not isinstance(entries, list):
            result["state"] = "unknown"
            complete = False
            continue
        complete = complete and len(entries) <= 100
        for entry in entries[:100]:
            if not isinstance(entry, dict):
                continue
            candidates = entry.get("hooks", []) if nested else [entry]
            if not isinstance(candidates, list):
                complete = False
                continue
            complete = complete and len(candidates) <= 100
            for candidate in candidates[:100]:
                if not ownership.hook_is_ours(candidate, markers):
                    continue
                # The permission mirror shares the local gate's prefix.
                command = ownership.normalize_command(candidate.get("command") or "")
                if "hook claude-code-permission" in command:
                    continue
                matched.append(event)
                usable = usable or ownership.command_binary_exists(candidate.get("command") or "")
                scope = ("All tools" if entry.get("matcher") == "*" else "Selected tools") if nested else label
                if scope not in result["matchers"]:
                    result["matchers"].append(scope)
    if matched:
        result["state"] = "configured" if usable else "broken"
        result["events"] = list(dict.fromkeys(matched))
    elif not complete:
        result["state"] = "unknown"
    result["inspection_complete"] = complete
    return result


def capture_hook_configuration(*, paths=None, now=None):
    """Capture settings, not enforcement proof. Path injection supports tests."""
    from clawmetry import claude_code_gate as cc, runtime_gates as rg
    paths = paths or {
        "claude_code": cc._settings_path(),
        "cursor": rg._cursor_hooks_path(),
        "copilot": os.path.join(rg._copilot_hooks_dir(), rg._COPILOT_GATE_BASENAME),
    }
    specs = {
        "claude_code": [("PreToolUse", (cc.HOOK_CMD_MARKER, "clawmetry hooks run pretooluse"), True, "Selected tools")],
        "cursor": [(event, (rg.CURSOR_CMD_MARKER,), False, label) for event, label in (
            ("beforeShellExecution", "Shell commands"),
            ("beforeMCPExecution", "MCP tools"), ("beforeReadFile", "File reads"))],
        "copilot": [("preToolUse", (rg.COPILOT_CMD_MARKER,), False, "Tool calls")],
    }
    runtimes = {}
    for runtime, items in specs.items():
        try:
            status, config = _read(paths.get(runtime, ""))
            runtimes[runtime] = _inspect(config, status, items)
        except Exception as exc:
            log.warning("Hook configuration observation failed for %s (%s)", runtime, type(exc).__name__)
            runtimes[runtime] = {"state": "unknown", "supported": True,
                                 "source": "runtime_hook_configuration", "events": [], "matchers": []}
    return {"schema_version": 1, "checked_at": int((time.time() if now is None else now) * 1000),
            "runtimes": runtimes}
