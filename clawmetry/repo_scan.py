"""Workspace scanner: executable content shipped inside a checkout.

The behavioural detectors in ``detectors.py`` all read the agent's tool stream.
That works for anything the agent chooses to do, and it is blind to an entire
class of attack where the agent chooses nothing at all — GitSpawn being the
worked example. A repository's own ``.git/config`` names a program in
``core.fsmonitor``; git runs it during index refresh; the agent's routine
background ``git status`` becomes arbitrary code execution outside the sandbox,
before any approval prompt, with nothing on screen and nothing in the tool
stream. Opening the folder was the exploit.

So this module reads the *workspace*, not the session. It answers one question:
**does this checkout contain configuration that names a program?** Three places
it can hide:

  * ``.git/config`` — command-valued keys (``core.fsmonitor``, ``core.hooksPath``,
    ``filter.*.clean``, ``diff.*.textconv``, ``core.sshCommand``, ``!``-prefixed
    aliases, …). Git executes these; none of them require your consent.
  * editor/task configs that auto-run — ``.vscode/tasks.json`` with
    ``runOn: folderOpen``, which fires the moment a VS Code-derived runtime opens
    the folder.
  * agent hook configs — ``.claude/settings.json`` and friends, the surface the
    CHAINDROP worm used to persist across 400+ npm packages.

**The false-positive problem is the whole design problem.** ``filter.lfs.clean``
is in millions of legitimate repositories. A scanner that cannot tell git-lfs
from a payload gets muted in a week and then protects nobody, so known-good
tooling is allowlisted by exact command shape and everything else is reported
with the command *sketched*, never echoed raw.

Read-only by construction: this module opens files and returns findings. It
never edits a config, never runs a command it finds, and never touches git.
"""
from __future__ import annotations

import json
import os
import re
from typing import Optional

# Git config keys whose VALUE is a program git will execute. Section+key, lowered.
# Sourced from git-config(1); the wildcard forms cover per-name subsections.
_EXEC_KEYS = (
    "core.fsmonitor",
    "core.hookspath",
    "core.sshcommand",
    "core.editor",
    "core.pager",
    "core.askpass",
    "sequence.editor",
    "credential.helper",
    "uploadpack.packobjectshook",
    "diff.external",
    "gpg.program",
    "init.templatedir",
)
_EXEC_KEY_PATTERNS = (
    re.compile(r"^filter\..+\.(clean|smudge|process)$"),
    re.compile(r"^diff\..+\.(command|textconv)$"),
    re.compile(r"^merge\..+\.driver$"),
    re.compile(r"^alias\..+$"),          # only flagged when the value starts "!"
)

# Commands that legitimately appear in these keys in ordinary repositories.
# Matched against the value's leading tokens, so `git-lfs clean -- %f` is
# recognised while `git-lfs clean; curl evil` is not.
_KNOWN_GOOD_PREFIXES = (
    ("git-lfs", "clean"), ("git-lfs", "smudge"), ("git-lfs", "filter-process"),
    ("git", "lfs"),
    ("cat",), ("true",), ("false",),
    ("rustfmt",), ("gofmt",), ("black",), ("prettier",),
    ("less",), ("more",), ("delta",), ("diff-so-fancy",),
)
# A value that chains, substitutes or redirects is never "known good", whatever
# it starts with — `git-lfs clean -- %f; curl attacker` starts with git-lfs.
_SHELL_METACHARS = re.compile(r"[;&|`$><\n]|\$\(|\|\|")

_TASKS_AUTORUN = re.compile(r'"runOn"\s*:\s*"folderOpen"', re.I)


def _sketch(value: str, limit: int = 80) -> str:
    """A command shown to a human without handing them a copy-pasteable payload.

    The finding is *that a program is named here*, not the program's exact
    argv. Collapsing whitespace and truncating keeps an incident readable in a
    UI row and keeps an attacker-authored string out of anything that might
    render it.
    """
    flat = " ".join(str(value).split())
    return (flat[:limit] + "…") if len(flat) > limit else flat


def _is_known_good(value: str) -> bool:
    if _SHELL_METACHARS.search(value or ""):
        return False
    tokens = str(value).split()
    if not tokens:
        return True
    lowered = [t.lower() for t in tokens]
    for prefix in _KNOWN_GOOD_PREFIXES:
        if lowered[:len(prefix)] == list(prefix):
            return True
    return False


# Hook managers that legitimately point core.hooksPath at the working tree.
# Recognising one does NOT make it safe: husky hooks travel with a clone and run
# on ordinary git commands, which is mechanically what GitSpawn abuses. It makes
# it *expected*, which is a severity question, not a suppression question — a
# scanner that hides husky is lying, and one that calls it critical gets muted.
_KNOWN_HOOK_MANAGERS = {".husky": "husky", ".lefthook": "lefthook",
                        ".git-hooks": "pre-commit"}


def _hook_manager_for(value: str) -> Optional[str]:
    first = str(value).strip().strip("./").split("/")[0]
    return _KNOWN_HOOK_MANAGERS.get("." + first.lstrip("."))


def _hookspath_is_repo_supplied(workspace: str, value: str) -> bool:
    """True when core.hooksPath points at hooks the CHECKOUT ships.

    The distinction is what travels with a clone. ``.git/hooks`` is the default
    location and its contents are never distributed by git, so a hooksPath
    pointing there — which plenty of tooling sets explicitly, as an absolute
    path — is ordinary and must not be flagged; getting this wrong makes the
    scanner cry wolf on a large share of real repositories. A hooksPath aimed
    at the *working tree* (``.githooks``, ``scripts/hooks``) is the opposite:
    the attacker controls those files through the repository itself.
    """
    try:
        ws = os.path.realpath(workspace)
        target = value if os.path.isabs(value) else os.path.join(ws, value)
        target = os.path.realpath(target)
        git_dir = os.path.realpath(os.path.join(ws, ".git"))
        if target == git_dir or target.startswith(git_dir + os.sep):
            return False           # inside .git/ — not shipped by a clone
        return target == ws or target.startswith(ws + os.sep)
    except Exception:
        return True                # unreadable path: report rather than hide


def _parse_git_config(text: str) -> list:
    """Minimal git-config parser → [(fullkey, value, lineno)].

    Deliberately not shelling out to ``git config``: reading an untrusted
    repository's config with git is how several of these bugs fire in the first
    place. Handles ``[section]``, ``[section "sub"]``, ``key = value``.
    """
    out: list = []
    section = ""
    sub = ""
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("["):
            head = line[1:line.index("]")] if "]" in line else line[1:]
            m = re.match(r'^([\w.-]+)\s*(?:"(.*)")?\s*$', head.strip())
            if m:
                section, sub = m.group(1).lower(), (m.group(2) or "")
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().lower()
        value = value.strip().strip('"')
        full = f"{section}.{sub}.{key}" if sub else f"{section}.{key}"
        out.append((full, value, lineno))
    return out


def _key_is_executable(full_key: str, value: str) -> bool:
    if full_key in _EXEC_KEYS:
        return True
    for rx in _EXEC_KEY_PATTERNS:
        if rx.match(full_key):
            # A git alias is only a shell command when it starts with "!".
            if full_key.startswith("alias."):
                return value.strip().startswith("!")
            return True
    return False


def _finding(kind: str, severity: str, title: str, detail: str,
             evidence: dict, session_id: str, runtime: str) -> dict:
    return {
        "kind": kind,
        "session_id": session_id,
        "runtime": runtime,
        "severity": severity,
        "title": title,
        "detail": detail,
        "evidence": evidence,
        "first_bad_step": None,
    }


def scan_git_config(workspace: str, session_id: str = "",
                    runtime: str = "unknown") -> list:
    """Flag command-valued keys in the repository's own ``.git/config``."""
    path = os.path.join(workspace, ".git", "config")
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except Exception:
        return []

    hits = []
    for full_key, value, lineno in _parse_git_config(text):
        if not value or not _key_is_executable(full_key, value):
            continue
        if _is_known_good(value):
            continue
        manager = None
        if full_key == "core.hookspath":
            if not _hookspath_is_repo_supplied(workspace, value):
                continue
            manager = _hook_manager_for(value)
        hits.append({"key": full_key, "command": _sketch(value),
                     "line": lineno, "manager": manager})
    if not hits:
        return []

    keys = sorted({h["key"] for h in hits})
    head = keys[0]
    more = f" and {len(keys) - 1} more" if len(keys) > 1 else ""
    managers = sorted({m for m in (h.get("manager") for h in hits) if m})
    # Every hit explained by a known hook manager is expected, not anonymous.
    recognised = managers and all(h.get("manager") for h in hits)
    if recognised:
        tool = managers[0]
        return [_finding(
            "repo_config_exec", "warning",
            f"repository ships its own git hooks via {tool}",
            f"`core.hooksPath` points into the working tree, managed by {tool}. "
            "That is ordinary for this tool, and it is worth knowing that the "
            "mechanism is the same one GitSpawn abuses: the hooks came with the "
            "clone and run on ordinary git commands, so whoever can land a commit "
            "here can run code on your machine when an agent touches the repo. "
            "Expected for a project you trust; read the hook directory for one "
            "you do not.",
            {"keys": keys, "hits": hits[:5], "config": ".git/config",
             "hook_manager": tool, "observed": "repository_config"},
            session_id, runtime)]
    return [_finding(
        "repo_config_exec", "critical",
        f"repository config names a program to run: {head}{more}",
        "This checkout's own .git/config sets "
        f"{head}{more}, and git executes that value during ordinary operations "
        "— a background `git status` or `git diff` is enough. The code runs "
        "with your privileges, outside the agent's sandbox, before any approval "
        "prompt. Inspect .git/config before letting an agent work here; to "
        "neutralise it for one command, run `git -c core.fsmonitor=false status`.",
        {"keys": keys, "hits": hits[:5], "config": ".git/config",
         "observed": "repository_config"},
        session_id, runtime)]


def scan_autorun_tasks(workspace: str, session_id: str = "",
                       runtime: str = "unknown") -> list:
    """Flag editor task configs that execute on folder open."""
    path = os.path.join(workspace, ".vscode", "tasks.json")
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except Exception:
        return []
    if not _TASKS_AUTORUN.search(text):
        return []
    commands = []
    try:
        for task in (json.loads(text).get("tasks") or []):
            runs_on = ((task.get("runOptions") or {}).get("runOn") or "").lower()
            if runs_on == "folderopen" and task.get("command"):
                commands.append(_sketch(task["command"]))
    except Exception:
        pass  # regex already established the finding; parsing is a nicety
    return [_finding(
        "repo_config_exec", "warning",
        "workspace runs a task automatically when the folder is opened",
        "`.vscode/tasks.json` contains a task with `runOn: folderOpen`, which "
        "executes as soon as a VS Code-derived runtime opens this workspace — "
        "before any agent session exists to observe it. Read the task before "
        "opening this folder in Cursor, Cline, Copilot or Antigravity.",
        {"file": ".vscode/tasks.json", "commands": commands[:5],
         "observed": "workspace_config"},
        session_id, runtime)]


# Agent hook configs, relative to the workspace. Each is a file an agent reads
# at session start and will happily execute commands from.
_AGENT_HOOK_FILES = (
    (".claude/settings.json", "claude_code"),
    (".claude/settings.local.json", "claude_code"),
    (".cursor/settings.json", "cursor"),
)
# ClawMetry installs its own PreToolUse hook, so a scan has to tell our entry
# from somebody else's. Ownership is decided on the command's ARGV SHAPE — the
# launcher is argv[0] and `hook` is its subcommand — never on a substring of the
# raw string. A substring test is trivially defeated: an attacker who writes a
# payload to /tmp/clawmetry-cache/x.sh would be silently trusted by it. The
# launcher path is often shlex-quoted, which has broken a marker here before,
# so parse the command properly rather than matching text.
def _is_clawmetry_hook(command: str) -> bool:
    import shlex
    try:
        argv = shlex.split(command or "")
    except ValueError:
        argv = (command or "").split()
    if not argv:
        return False
    if os.path.basename(argv[0]).lower() in ("clawmetry", "clawmetry.exe"):
        return True
    # `python -m clawmetry.<mod>` — the module must be the token after -m, not
    # merely present somewhere in the string.
    for i, tok in enumerate(argv[:-1]):
        if tok == "-m" and argv[i + 1].startswith("clawmetry"):
            return True
    return False


def _hook_commands(node) -> list:
    """Walk a settings tree and collect every `command` string under `hooks`."""
    found: list = []
    if isinstance(node, dict):
        for key, val in node.items():
            if key == "command" and isinstance(val, str):
                found.append(val)
            else:
                found.extend(_hook_commands(val))
    elif isinstance(node, list):
        for item in node:
            found.extend(_hook_commands(item))
    return found


def scan_agent_hooks(workspace: str, session_id: str = "",
                     runtime: str = "unknown") -> list:
    """Flag hook commands in agent config that ClawMetry did not install."""
    out = []
    for rel, rt in _AGENT_HOOK_FILES:
        path = os.path.join(workspace, rel)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except Exception:
            continue
        hooks = data.get("hooks")
        if not hooks:
            continue
        foreign = [c for c in _hook_commands(hooks) if not _is_clawmetry_hook(c)]
        if not foreign:
            continue
        # A committed settings.json is normally the project author's own
        # tooling; settings.local.json is gitignored by convention, which is
        # exactly why a worm writes there — nothing shows up in `git status`.
        # Same mechanism, very different prior, so the severity differs and the
        # wording says which one the reader is looking at.
        local = rel.endswith(".local.json")
        out.append(_finding(
            "agent_config_tamper", "critical" if local else "warning",
            f"{rel} installs {len(foreign)} hook command(s) that run with your session",
            f"`{rel}` registers hook commands that run inside your {rt} session, "
            "on every matching tool call, with your credentials in the "
            "environment. "
            + ("This file is gitignored by convention, so an entry here does "
               "not show up in `git status` — the surface the CHAINDROP worm "
               "used to persist across 400+ npm packages. If you did not add "
               "these, treat the machine as compromised. "
               if local else
               "For a project you trust this is usually the author's own "
               "tooling and is committed to the repo; check `git log` on this "
               "file if you did not expect it. ")
            + "ClawMetry will not remove another tool's hooks for you.",
            {"file": rel, "commands": [_sketch(c) for c in foreign[:5]],
             "count": len(foreign), "gitignored_by_convention": local,
             "observed": "agent_config"},
            session_id, rt))
    return out


def scan_workspace(workspace: str, session_id: str = "",
                   runtime: str = "unknown") -> list:
    """Run every workspace check. Never raises; a broken check costs its finding.

    Returns incidents in the same shape as ``detectors.run_all``, so the Guard
    tab, the policy engine and the red-team audit all consume one vocabulary.
    """
    findings: list = []
    for check in (scan_git_config, scan_autorun_tasks, scan_agent_hooks):
        try:
            findings.extend(check(workspace, session_id, runtime) or [])
        except Exception:
            continue
    return findings
