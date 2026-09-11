"""What a tool call actually touched, and what a finding may repeat back.

Every function here is new in this change, which is why it is its own file: the
existing detector module keeps its shape and a reader can see the whole of the
new capability in one place.

Two jobs:

* **The action surface.** Given a tool call's arguments, the paths it names,
  the command it ran, and the hosts it reached. Heredoc bodies are stripped
  first, because a document an agent WROTE is not a command it RAN, and
  reading one as the other reported scripts that merely contain the words
  ``csrutil disable`` as having disabled a system protection.
* **Redaction.** A finding travels to ``loop_signals``, into the plaintext
  heartbeat, and on to the cloud. So a path keeps at most its last two
  segments, and a command is reduced to its program and first flag, dropping
  any token that could carry a secret.
"""
from __future__ import annotations

import re

_MAX_SURFACE_ITEMS = 24          # per step; bounds CPU and evidence size
_MAX_CMD_CHARS = 2000

# ── Action surface: what a tool call actually touched ────────────────────────
# The loop detectors only need (tool, args_hash). The behavioural ones need the
# nouns: paths, commands, hosts. We extract them ONCE during normalization,
# bounded in size, so eight detectors do not each re-parse the same arguments.

# Argument keys that carry a filesystem path across the runtimes we ingest.
_PATH_ARG_KEYS = (
    "path", "file_path", "filepath", "file", "filename", "file_name",
    "notebook_path", "target_file", "old_path", "new_path", "dst",
    "destination", "src", "source", "dir", "directory", "cwd",
    "paths", "files", "file_paths", "edits",
)
# Argument keys that carry a shell command / script body.
_CMD_ARG_KEYS = (
    "command", "cmd", "commands", "script", "shell_command", "code",
    "bash_command", "input", "argv", "args",
)
# Tools whose single string argument IS a command rather than a path.
_SHELL_TOOL_SUBSTRINGS = ("bash", "shell", "exec", "terminal", "run_command",
                          "process", "console", "sh")

_URL_RE = re.compile(r"\b[a-z][a-z0-9+.\-]{1,15}://([^/\s'\"<>|)]+)", re.I)
# scp/ssh/rsync style ``user@host:path`` targets — egress without a URL.
_SSH_HOST_RE = re.compile(
    r"(?:^|\s)[\w.\-]+@([a-z0-9][a-z0-9.\-]*\.[a-z]{2,63})(?=[:\s]|$)", re.I)
# A redirect that writes a REAL file. ``2>/dev/null`` and ``>/dev/null`` are so
# common in normal work that counting them as progress would silence
# no_progress for every shell-first runtime, so they are excluded explicitly.
_REDIRECT_WRITE_RE = re.compile(r">>?\s*(?!/dev/null)([\w./~\-]+)")
# Commands that mutate the filesystem. Progress for no_progress, and the write
# side of the blast radius for shell-first runtimes.
_MUTATING_CMD_RE = re.compile(
    r"(?:^|[;&|]\s*|\s)(?:cp|mv|rm|mkdir|rmdir|touch|tee|patch|truncate|ln|"
    r"install|unzip|tar|dd)\s|"
    r"\bsed\s+-i|\bgit\s+(?:apply|commit|checkout|restore|stash|clean|reset)\b|"
    r"\bnpm\s+(?:install|i)\b|\bpip\s+install\b", re.I)
# Hosts that are not egress: the machine talking to itself.
_LOCAL_HOSTS = frozenset({
    "localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]", "host.docker.internal",
    "169.254.169.254",  # the metadata endpoint IS interesting -> see below
})
_IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")



def _looks_like_path(value: str) -> bool:
    v = value.strip()
    if not v or len(v) > 400 or "\n" in v:
        return False
    if "://" in v:
        return False   # a URL is egress, not a file the agent mutated
    if v.startswith(("/", "./", "../", "~/")) or "\\" in v[:3]:
        return True
    return "/" in v and " " not in v


def _iter_str_values(value, depth: int = 0):
    """Yield the string leaves of an argument value, one level of nesting deep.
    Bounded so a huge ``edits`` array cannot make normalization expensive."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, (list, tuple)) and depth < 2:
        for v in value[:_MAX_SURFACE_ITEMS]:
            for s in _iter_str_values(v, depth + 1):
                yield s
    elif isinstance(value, dict) and depth < 2:
        for k, v in list(value.items())[:_MAX_SURFACE_ITEMS]:
            if k in _PATH_ARG_KEYS or k in _CMD_ARG_KEYS:
                for s in _iter_str_values(v, depth + 1):
                    yield s


# ``cat > f <<'EOF' ... EOF`` writes a document. The document is not something
# the agent RAN, and reading it as one is how a script that merely contains the
# string "csrutil disable" gets reported as having disabled a system
# protection. Found on real sessions: the detectors flagged the very patch
# scripts that define their own patterns.
_HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def _strip_heredocs(cmd: str) -> str:
    """Drop heredoc BODIES, keep the command lines around them.

    ``cat > x.py <<'PY'`` keeps its redirect and target (the blast radius still
    sees the write); only the document between the marker and its terminator is
    removed. Never raises: on anything unexpected the original text is
    returned, which is the pre-existing behaviour."""
    try:
        out = []
        lines = cmd.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            m = _HEREDOC_RE.search(line)
            out.append(line)
            i += 1
            if not m:
                continue
            delim = m.group(2)
            # Skip to the terminator (a line that is just the delimiter).
            while i < len(lines) and lines[i].strip() != delim:
                i += 1
            i += 1  # drop the terminator line too
        return "\n".join(out)
    except Exception:
        return cmd


# Commands that INSPECT text rather than act on it. A privilege pattern found
# inside one of these is a mention, not an action: ``grep -r sudoers docs/``
# changes nothing. Credential access is deliberately NOT filtered this way,
# because for a secret file the reading IS the action.
_READONLY_CMD_RE = re.compile(
    r"^\s*(?:sudo\s+)?(?:grep|rg|ag|ack|find|locate|man|less|more|head|tail|"
    r"echo|printf|type|which|whereis|history|diff|comm|wc|awk|jq|"
    r"git\s+(?:log|show|diff|grep|blame|status))\b", re.I)


def _is_inspect_only(cmd: str) -> bool:
    """True when every segment of the command line only reads or prints."""
    try:
        segments = [seg.strip() for seg in re.split(r"[;&|]+", cmd) if seg.strip()]
        if not segments:
            return False
        return all(_READONLY_CMD_RE.match(seg) for seg in segments)
    except Exception:
        return False


def _is_shell_tool(tool: str) -> bool:
    t = (tool or "").lower()
    return any(sub in t for sub in _SHELL_TOOL_SUBSTRINGS)


def _hosts_from_text(text: str) -> list:
    """External hostnames a command or argument reaches out to. Local names are
    dropped — a request to 127.0.0.1 is not egress."""
    out = []
    if not text:
        return out
    try:
        for m in _URL_RE.finditer(text[:_MAX_CMD_CHARS]):
            netloc = m.group(1)
            host = netloc.rsplit("@", 1)[-1]          # strip user:pass@
            host = host.split("/", 1)[0]
            if host.startswith("["):                   # [::1]:8080
                host = host[:host.find("]") + 1]
            else:
                host = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
            host = host.strip().lower().rstrip(".")
            if host and host not in _LOCAL_HOSTS and not host.endswith(".local"):
                out.append(host)
        for m in _SSH_HOST_RE.finditer(text[:_MAX_CMD_CHARS]):
            host = m.group(1).strip().lower().rstrip(".")
            if host and host not in _LOCAL_HOSTS and "." in host:
                out.append(host)
    except Exception:
        return out
    return out[:_MAX_SURFACE_ITEMS]


def _paths_from_command(cmd: str) -> list:
    """Path-looking tokens inside a shell command (bounded)."""
    out = []
    try:
        for tok in cmd[:_MAX_CMD_CHARS].split()[:60]:
            tok = tok.strip("'\"();|&")
            if _looks_like_path(tok):
                out.append(tok)
        for m in _REDIRECT_WRITE_RE.finditer(cmd[:_MAX_CMD_CHARS]):
            out.append(m.group(1))
    except Exception:
        return out
    return out[:_MAX_SURFACE_ITEMS]


def _action_surface(tool: str, args) -> tuple:
    """``(paths, cmd, hosts)`` for one tool call. Never raises."""
    paths: list = []
    cmd_parts: list = []
    try:
        if isinstance(args, str):
            if _is_shell_tool(tool):
                cmd_parts.append(args)
            elif _looks_like_path(args):
                paths.append(args)
        elif isinstance(args, dict):
            for key, val in list(args.items())[:40]:
                k = str(key).lower()
                if k in _CMD_ARG_KEYS:
                    for s in _iter_str_values(val):
                        cmd_parts.append(s)
                elif k in _PATH_ARG_KEYS:
                    for s in _iter_str_values(val):
                        if _looks_like_path(s) or ("." in s and "/" not in s
                                                   and len(s) < 120):
                            paths.append(s)
                elif isinstance(val, str) and val.startswith(("http://", "https://")):
                    cmd_parts.append(val)
        elif isinstance(args, (list, tuple)):
            joined = " ".join(str(a) for a in args[:_MAX_SURFACE_ITEMS])
            if _is_shell_tool(tool):
                cmd_parts.append(joined)
    except Exception:
        pass
    cmd = _strip_heredocs(" ".join(cmd_parts))[:_MAX_CMD_CHARS]
    if cmd:
        paths.extend(_paths_from_command(cmd))
    hosts = _hosts_from_text(cmd)
    for p in list(paths):
        if "://" in p:
            hosts.extend(_hosts_from_text(p))
    # dedupe, preserve order, bound
    seen = set()
    uniq_paths = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            uniq_paths.append(p)
    seen = set()
    uniq_hosts = []
    for h in hosts:
        if h not in seen:
            seen.add(h)
            uniq_hosts.append(h)
    return (tuple(uniq_paths[:_MAX_SURFACE_ITEMS]), cmd,
            tuple(uniq_hosts[:_MAX_SURFACE_ITEMS]))


# ── Redaction: what an incident is allowed to publish ────────────────────────
# Incident evidence travels: loop_signals -> the heartbeat slice -> the cloud
# device summary. A full path usually names a customer or a project, and a raw
# command line can carry a bearer token, so neither goes in whole.

def _redact_path(path: str) -> str:
    """At most the last two segments, home collapsed. ``/Users/x/acme/api/db.py``
    becomes ``.../api/db.py``."""
    try:
        p = str(path or "").strip()
        if not p:
            return ""
        parts = [seg for seg in p.replace("\\", "/").split("/") if seg]
        tail = "/".join(parts[-2:])
        return (".../" + tail) if len(parts) > 2 else tail
    except Exception:
        return ""


_SECRETY = ("=", "@", "://", "sk-", "token", "key", "secret", "password", "pw=")


def _cmd_sketch(cmd: str) -> str:
    """The program and its first flag, nothing else. ``curl -sS -H
    "Authorization: Bearer sk-…" https://x`` becomes ``curl -sS``. Anything
    that could carry a value is dropped rather than truncated, because a
    truncated secret is still a leaked prefix."""
    try:
        out = []
        for tok in str(cmd or "").split()[:2]:
            low = tok.lower()
            if any(marker in low for marker in _SECRETY):
                break
            out.append(tok[:24])
        return " ".join(out)
    except Exception:
        return ""
