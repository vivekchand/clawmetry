"""clawmetry/tool_risk.py — deterministic call-level risk classification.

Classifies every tool CALL (not the tool definition) into
``low / medium / high / critical`` from the tool name + arguments, the way
a security reviewer would triage it: what does THIS invocation touch?

Why call-level: definition-level risk (Matimo-style "POST = medium") can't
tell ``ls`` from ``rm -rf /`` — both arrive through the same shell tool on
every harness. ClawMetry sees the arguments for all 27+ runtimes at the
same normalisation point the approvals watcher uses, so the classifier
runs on (canonical category, extracted command, raw args) and the SAME
verdict applies to a Claude Code ``Bash``, a Codex ``shell``, a Cursor
``run_terminal_cmd`` or an OpenClaw ``exec`` call.

Design rules (non-negotiable):
  * **Pure + deterministic.** Same input → same output. No I/O, no config,
    no network, no clock. Unit-testable in isolation, safe in the daemon,
    the dashboard, and replay.
  * **Never crash.** Malformed args, list-valued commands, None — anything
    degrades to a conservative verdict with an explanation, never a raise.
    The Brain feed classifies thousands of rows per page-load.
  * **Worst signal wins.** Every matching rule contributes a reason; the
    final level is the maximum. Reasons are plain copy (no em-dashes, no
    jargon) because they surface verbatim in approval prompts.
  * **This module imports nothing from the rest of clawmetry.** It is the
    leaf that ``approvals.py`` (and routes) import, so the canonical tool
    map lives HERE now and ``approvals`` re-exports it (single source of
    truth, no drift between watcher / replay / hook gate).

Public API:
  classify_tool_call(tool_name, args) -> {level, rank, category, reasons}
  risk_rank(level) -> int  (unknown level → 0)
  RISK_LEVELS, RISK_RANK
  canonical_tool(name), extract_command(tool_name, args)  (moved from
  approvals.py; the ``_``-prefixed aliases keep old import sites working)
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Canonical tool categories (moved verbatim from approvals.py) ──────────
# Harness-agnostic tool categories. Approval policies are authored against
# OpenClaw's tool names (``exec``, ``read``, …), but other harnesses emit the
# SAME semantic tool under a different name — claude-cli/Claude Code calls
# the shell ``Bash``, Codex ``shell``, etc. Map both sides to a canonical
# category before comparing.
_TOOL_CANON: dict[str, str] = {}
for _canon, _aliases in {
    "exec": ["exec", "bash", "sh", "shell", "zsh", "fish", "powershell", "pwsh",
             "cmd", "command", "run", "run_command", "run_terminal_cmd",
             "terminal", "execute", "shell_command", "bashtool"],
    "read": ["read", "cat", "view", "open", "read_file", "get_file", "fs_read",
             "view_file", "view_file_outline", "list_dir", "read_agent",
             # Kimi CLI ships PascalCase tool names (ReadFile, WriteFile,
             # StrReplaceFile, SearchWeb, FetchURL); canonical_tool()
             # lowercases before lookup, so the aliases are the lowered form.
             "readfile", "readmediafile"],
    "write": ["write", "edit", "multiedit", "str_replace", "str_replace_editor",
              "create", "apply_patch", "write_file", "fs_write",
              "write_to_file", "replace_file_content", "edit_file",
              "writefile", "strreplacefile"],
    "web": ["web_fetch", "webfetch", "fetch", "curl", "wget", "http",
            "web_search", "websearch", "browser", "browse", "search_web",
            "read_url_content", "searchweb", "fetchurl"],
    "search": ["grep", "rg", "glob", "ls", "find", "search", "memory_search",
               "grep_search", "find_by_name", "codebase_search"],
}.items():
    for _a in _aliases:
        _TOOL_CANON[_a] = _canon


def canonical_tool(name: str) -> str:
    """Map a harness-specific tool name to its canonical category (or itself)."""
    return _TOOL_CANON.get((name or "").strip().lower(), (name or "").strip().lower())


def extract_command(tool_name: str, args: Any) -> str:
    """Best-effort: derive the human-readable 'command' string from toolCall
    args. Different harness tools name the field differently (``command``,
    ``cmd``, ``script``, ``query``, ``path``, …); some (Codex ``shell``) pass
    a LIST like ``["bash", "-lc", "…"]`` — join those.
    """
    if isinstance(args, str) and args.strip().startswith("{"):
        # Codex / PicoClaw / Hermes persist OpenAI ``arguments`` as a JSON
        # string; parse so the REAL command classifies, not "".
        try:
            parsed = json.loads(args)
            args = parsed if isinstance(parsed, dict) else args
        except Exception:
            pass
    if not isinstance(args, dict):
        return ""
    for k in ("command", "cmd", "script", "query", "url", "path", "file_path",
              "task", "message", "content", "action"):
        v = args.get(k)
        if isinstance(v, str) and v:
            return v
        if isinstance(v, (list, tuple)) and v:
            try:
                return " ".join(str(x) for x in v)
            except Exception:
                continue
    # Fallback: stringify args
    try:
        return json.dumps(args)[:500]
    except Exception:
        return ""


# Backward-compat aliases: existing import sites use the underscored names
# (routes/hooks.py, claude_code_gate.py go through ``approvals`` which
# re-exports these).
_canonical_tool = canonical_tool
_extract_command = extract_command


# ── Risk vocabulary ───────────────────────────────────────────────────────

RISK_LEVELS = ("low", "medium", "high", "critical")
RISK_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def risk_rank(level: str) -> int:
    """Rank of a risk level; unknown strings rank as 0 (low)."""
    return RISK_RANK.get(str(level or "").strip().lower(), 0)


# ── Rule tables ───────────────────────────────────────────────────────────
# Each entry: (compiled regex over the lowercased command string, level,
# reason). Order does not matter — worst match wins. Keep every pattern
# anchored on word-ish boundaries so ``platform`` doesn't match ``rm``.

def _rx(p: str) -> "re.Pattern[str]":
    return re.compile(p, re.IGNORECASE)


# rm with -r and -f in either order / combined (-rf, -fr, -r -f …),
# targeting root, home, or a bare glob of either.
_RM_RECURSIVE_FORCE = _rx(
    r"\brm\s+(?=[^|;&]*\s-\w*r)(?=[^|;&]*\s-\w*f)")
_RM_ROOT_TARGET = _rx(
    r"\brm\s+[^|;&]*\s+(?:--?\w+\s+)*(?:/|/\*|~|~/|\$home\b|\$\{home\}|"
    r"%userprofile%|c:\\\\?\s*$|c:\\\\?\*)\s*(?:$|[|;&])")

_CMD_RULES: list[tuple["re.Pattern[str]", str, str]] = [
    # ── critical: irreversible machine or data destruction ──
    (_rx(r"\bdd\b[^|;&]*\bof=/dev/(?:r?disk|sd[a-z]|hd[a-z]|nvme)"),
     "critical", "writes raw bytes to a disk device"),
    (_rx(r"\bmkfs(?:\.\w+)?\b"), "critical", "formats a filesystem"),
    (_rx(r"\bdiskutil\s+(?:erase|reformat|partition)"), "critical",
     "erases or repartitions a disk"),
    (_rx(r"(?:^|[\s;|&])format\s+[a-z]:"), "critical",
     "formats a Windows drive"),
    (_rx(r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"), "critical",
     "fork bomb pattern"),
    (_rx(r"\b(?:curl|wget)\b[^|;&]*(?:169\.254\.169\.254|"
         r"metadata\.google\.internal|metadata/computeMetadata)"),
     "critical", "queries a cloud metadata endpoint, a credential theft vector"),
    (_rx(r"\b(?:curl|wget)\b[^|]*\|\s*sudo\s+(?:sh|bash|zsh)\b"), "critical",
     "pipes a remote script into a root shell"),
    (_rx(r"\b(?:nc|ncat|netcat)\b[^|;&]*\s-\w*e\b|/dev/tcp/|"
         r"\bsocat\b[^|;&]*\bexec\b|\bmkfifo\b[^|;&]*\|\s*(?:nc|sh|bash)\b"),
     "critical", "reverse shell pattern"),

    # ── high: destructive, privileged, secret-touching, or persistent ──
    (_rx(r"\brm\b[^|;&]*\s-\w*r"), "high",
     "recursive delete"),
    (_rx(r"\b(?:rmdir|rd)\s+/s\b"), "high", "recursive directory delete"),
    (_rx(r"\bdel\s+(?:/\w+\s+)*/s\b"), "high", "recursive file delete"),
    (_rx(r"\bremove-item\b[^|;&]*-recurse"), "high", "recursive delete"),
    (_rx(r"\bgit\s+push\b[^|;&]*(?:\s--force\b|\s-f\b|\s--force-with-lease\b)"),
     "high", "force-push rewrites remote history"),
    (_rx(r"\bgit\s+reset\s+--hard\b"), "high",
     "hard reset discards local changes"),
    (_rx(r"\bgit\s+clean\b[^|;&]*-\w*[fdx]"), "high",
     "git clean deletes untracked files"),
    # Anchored to a command position so prose mentioning "sudo" inside a
    # commit message or echo string does not classify as privileged.
    (_rx(r"(?:^|[|;&]\s*|\$\(\s*)sudo\s"), "high",
     "runs with elevated privileges"),
    (_rx(r"\bchmod\s+(?:-\w+\s+)*(?:-r\s+)?0?777\b"), "high",
     "makes files world-writable"),
    (_rx(r"\bchown\b[^|;&]*\s-\w*r"), "high", "recursive ownership change"),
    (_rx(r"(?:^|[|;&]\s*)(?:sudo\s+)?(?:shutdown|reboot|halt|poweroff)\b"),
     "high", "shuts down or reboots the machine"),
    (_rx(r"(?:^|[|;&]\s*)(?:kill|pkill|killall)\s+(?:-9|-kill)\b"), "high",
     "force-kills processes"),
    (_rx(r"\b(?:curl|wget)\b[^|]*\|\s*(?:sh|bash|zsh|python\d?)\b"), "high",
     "pipes a remote script into an interpreter"),
    (_rx(r"\b(?:crontab\s+-|schtasks\s+/create|launchctl\s+(?:load|bootstrap)|"
         r"systemctl\s+enable)"), "high",
     "installs a persistent scheduled task or service"),
    (_rx(r"(?:~|\$home|%userprofile%)?/?\.(?:aws|ssh|gnupg)/"), "high",
     "touches credential or key material"),
    (_rx(r"\.(?:netrc|npmrc|pypirc)\b"), "high",
     "touches a credentials file"),
    (_rx(r"/etc/(?:shadow|passwd|sudoers)\b"), "high",
     "touches system account files"),
    (_rx(r"(?:^|/)\.kube/|\bkubeconfig\b"), "high",
     "touches Kubernetes credentials"),
    (_rx(r"\bchmod\s+(?:-\w+\s+)*(?:u\+s|[24][0-7]{3})\b"), "high",
     "sets a setuid or setgid bit"),
    (_rx(r"\b(?:env|printenv|set)\b\s*(?:$|[|;&])[^|;&]*"
         r"\b(?:curl|wget|nc)\b"), "high",
     "dumps environment variables toward the network"),
    (_rx(r"\b\w*(?:api[_-]?key|secret|token|passwd|password|credential)\w*\s*="),
     "high", "references secret-looking values"),
    (_rx(r"\breg\s+add\s+hklm\b"), "high",
     "writes to the Windows machine registry"),
    (_rx(r"\b(?:ifconfig|iptables|pfctl|netsh)\b[^|;&]*"
         r"\b(?:down|flush|-f|delete)\b"), "high",
     "alters network configuration"),
    (_rx(r"\bdrop\s+(?:table|database|schema)\b"), "high",
     "drops a database object"),
    (_rx(r"\btruncate\s+table\b"), "high", "truncates a table"),

    # ── medium: state-changing but recoverable / routine ──
    (_rx(r"\bgit\s+push\b"), "medium", "pushes to a remote"),
    (_rx(r"\b(?:pip3?|pipx|npm|pnpm|yarn|brew|apt(?:-get)?|dnf|yum|cargo|gem)\s+"
         r"(?:install|add|upgrade|update)\b"), "medium",
     "installs or upgrades packages"),
    (_rx(r"\bdocker\s+(?:run|rm|rmi|compose\s+up)\b"), "medium",
     "manages containers"),
    (_rx(r"\b(?:mv|cp)\b[^|;&]*\s-\w*[rf]"), "medium",
     "bulk file move or copy"),
    (_rx(r"(?:^|[|;&]\s*)(?:tee|>>?)\s*/(?:etc|usr|bin|sbin|lib|system|"
         r"library|var)\b"), "high",
     "writes to a system directory"),
    (_rx(r"(?:^|[|;&]\s*)(?:kill|pkill|killall)\s"), "medium",
     "signals a process"),
]

# Benign exec commands: read-only inspectors that keep a shell call at low.
_BENIGN_EXEC = _rx(
    r"^\s*(?:ls|ll|cat|head|tail|less|more|pwd|whoami|which|type|file|stat|"
    r"wc|du|df|ps|top|env|printenv|echo|date|uname|hostname|id|uptime|"
    r"grep|rg|ag|find|fd|locate|tree|basename|dirname|readlink|"
    r"git\s+(?:status|log|diff|show|branch|remote|ls-files|blame|describe|"
    r"rev-parse|stash\s+list)|"
    r"npm\s+(?:ls|list|view|outdated)|pip3?\s+(?:list|show|freeze)|"
    r"docker\s+(?:ps|images|logs)|make\s+-n|"
    r"python\d?\s+(?:--version|-v)\b|node\s+(?:--version|-v)\b)\b")

# Sensitive path fragments for write-category tools (file_path / path args).
_SYSTEM_PATH = _rx(
    r"^(?:/etc/|/usr/|/bin/|/sbin/|/lib/|/system/|/library/|/var/(?!tmp)|"
    r"c:\\windows\\|c:\\program files)")
_DOTFILE_CRED_PATH = _rx(
    r"(?:^|/)\.(?:aws|ssh|gnupg|kube)(?:/|$)|\.(?:netrc|npmrc|pypirc)$|"
    r"(?:^|/)(?:credentials|secrets?)(?:\.\w+)?$|\.env(?:\.\w+)?$|"
    r"/etc/(?:shadow|passwd|sudoers)$|\bkubeconfig\b")

_METADATA_HOSTS = ("169.254.169.254", "metadata.google.internal")
_DESTRUCTIVE_HTTP = ("delete",)
_WRITE_HTTP = ("post", "put", "patch")


def _classify_exec(cmd: str, hits: list[tuple[str, str]]) -> None:
    low = cmd.lower()
    for rx_, level, reason in _CMD_RULES:
        if rx_.search(low):
            hits.append((level, reason))
    # rm -rf aimed at root or home escalates to critical.
    if _RM_RECURSIVE_FORCE.search(low) or _rx(r"\brm\s+-\w*r\w*\s").search(low):
        if _RM_ROOT_TARGET.search(low):
            hits.append(("critical",
                         "recursive delete targets the filesystem root or home"))
    if not hits:
        if _BENIGN_EXEC.search(low):
            hits.append(("low", "read-only shell command"))
        else:
            hits.append(("medium", "shell command with side effects unknown"))


def _classify_web(args: dict, cmd: str, hits: list[tuple[str, str]]) -> None:
    url = ""
    for k in ("url", "uri", "endpoint"):
        v = args.get(k)
        if isinstance(v, str):
            url = v
            break
    url = url or cmd
    lower_url = (url or "").lower()
    for host in _METADATA_HOSTS:
        if host in lower_url:
            hits.append(("critical",
                         "requests a cloud metadata endpoint, a credential "
                         "theft vector"))
    import re as _re2
    if _re2.search(r"(?:^|//)(?:localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|"
                   r"10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|"
                   r"172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+|\[?::1\]?)"
                   r"(?::|/|$)", lower_url):
        hits.append(("medium",
                     "requests a private or local network address"))
    method = str(args.get("method") or "get").strip().lower()
    if method in _DESTRUCTIVE_HTTP:
        hits.append(("high", "HTTP DELETE request"))
    elif method in _WRITE_HTTP:
        hits.append(("medium", f"HTTP {method.upper()} sends data"))
    if not hits:
        hits.append(("low", "web fetch or search"))


def _classify_write(args: dict, cmd: str, hits: list[tuple[str, str]]) -> None:
    path = ""
    for k in ("file_path", "path", "filename", "file", "target_file"):
        v = args.get(k)
        if isinstance(v, str) and v:
            path = v
            break
    path = path or cmd
    lower_path = (path or "").strip().lower().replace("\\", "/")
    if _SYSTEM_PATH.search(lower_path.replace("/", "\\", 0) or lower_path):
        hits.append(("high", "writes to a system directory"))
    if _DOTFILE_CRED_PATH.search(lower_path):
        hits.append(("high", "writes to a credentials or key file"))
    if not hits:
        hits.append(("medium", "writes or edits a file"))


def classify_tool_call(tool_name: str, args: Any) -> dict:
    """Classify one tool call. Returns
    ``{"level", "rank", "category", "reasons"}`` and NEVER raises.

    ``args`` may be any shape; non-dict degrades to command-string analysis
    of its stringification. Unknown tools with no signals are ``low`` with
    an "insufficient signal" reason (the honest floor: we will not invent
    risk we cannot see).
    """
    try:
        category = canonical_tool(tool_name)
        safe_args = args if isinstance(args, dict) else {}
        cmd = extract_command(tool_name, args)
        hits: list[tuple[str, str]] = []

        if category == "exec":
            _classify_exec(cmd, hits)
        elif category == "web":
            _classify_web(safe_args, cmd, hits)
        elif category == "write":
            _classify_write(safe_args, cmd, hits)
        elif category in ("read", "search"):
            # Reads can still touch secrets (cat ~/.aws/credentials via the
            # read TOOL, not the shell).
            probe = (cmd or "").lower().replace("\\", "/")
            if _DOTFILE_CRED_PATH.search(probe):
                hits.append(("high", "reads credential or key material"))
            else:
                hits.append(("low", "read-only operation"))
        else:
            # Unknown tool: scan whatever command-ish string we extracted
            # with the exec rules (many MCP tools wrap shell-like actions),
            # but do not apply the "unknown shell command" medium floor.
            low = (cmd or "").lower()
            for rx_, level, reason in _CMD_RULES:
                if rx_.search(low):
                    hits.append((level, reason))
            if not hits:
                hits.append(("low", "no risk signals for this tool call"))

        best = max(hits, key=lambda h: risk_rank(h[0]))
        level = best[0]
        # Dedup reasons, keep insertion order, cap for UI sanity.
        seen: set[str] = set()
        reasons: list[str] = []
        for _lvl, r in sorted(hits, key=lambda h: -risk_rank(h[0])):
            if r not in seen:
                seen.add(r)
                reasons.append(r)
            if len(reasons) >= 4:
                break
        return {"level": level, "rank": risk_rank(level),
                "category": category, "reasons": reasons}
    except Exception:
        # Fail CLOSED: a classifier bug must not silently disable a
        # declared min_risk policy. "high" makes the failure loud (calls
        # start pausing, the reason names the bug) instead of invisible.
        try:
            cat = canonical_tool(tool_name)
        except Exception:
            cat = ""
        return {"level": "high", "rank": RISK_RANK["high"],
                "category": cat,
                "reasons": ["risk classifier error, treated as high risk"]}
