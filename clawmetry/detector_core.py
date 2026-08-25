"""The shared floor every detector stands on: parse, normalize, redact.

Split out of :mod:`clawmetry.detectors`. Three jobs, none of which is detection:

* **Normalize.** ``normalize_events`` flattens the heterogeneous on-the-wire
  event shapes (top-level tool_call, OpenClaw v3 toolMetas, Claude-Code content
  blocks, family ``data.tool_calls`` arrays) into one ordered list of steps.
  Done ONCE per session per tick and shared by all eight detectors.
* **Extract the action surface.** What a tool call actually touched: paths, the
  command, the hosts. Heredoc bodies are stripped here, because a document an
  agent WROTE is not a command it RAN.
* **Redact.** What an incident is allowed to publish. Incident evidence travels
  to ``loop_signals``, into the plaintext heartbeat, and on to the cloud, so a
  path is truncated and a command is reduced to its program and first flag.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable, Optional

from clawmetry.detector_calibration import (
    DETECT_EVENT_WINDOW,
    WRITE_TOOL_SUBSTRINGS,
    resolve_thresholds,
)


# Substrings in tool-result text that, on their own, mark a failure even when no
# structured ``is_error`` flag is present (TRAIL System-Execution signals).
_FAILURE_TEXT_MARKERS = (
    "command not found", "no such file", "no such file or directory",
    "permission denied", "fatal:", "traceback (most recent call last)",
    "exit code 1", "exit status 1", "non-zero exit", "errno",
    "exception:", "segmentation fault", "connection refused", "timed out",
)

# ── Normalized event shape ───────────────────────────────────────────────────
# A detector never reasons over raw store rows directly. ``normalize_events``
# flattens the heterogenous on-the-wire shapes (top-level tool_call, OpenClaw v3
# model.completed+toolMetas, Claude-Code assistant+content blocks, family
# data.tool_calls arrays, tool_result/tool.result rows) into a flat, ordered
# list of NormStep dicts the heuristics scan:
#
#   {"i": int,              # index into the *original* event list (localization)
#    "kind": "tool_call" | "tool_result" | "text" | "user" | "end" | "other",
#    "tool": str,           # tool name (tool_call/tool_result), else ""
#    "args_hash": str,      # stable hash of normalized args (tool_call), else ""
#    "is_error": bool,      # tool_result only
#    "result_text": str,    # tool_result only (lower-cased, truncated)
#    "has_text": bool,      # text turn carrying a real reply (progress marker)
#   }

_TOPLEVEL_TOOL_CALL_TYPES = frozenset(
    {"tool_call", "tool_use", "toolcall", "tool.call", "tool.invoked"}
)
_TOOL_RESULT_TYPES = frozenset(
    {"tool_result", "tool-result", "tool.result", "tool.completed",
     "tool_use_result"}
)
_ASSISTANT_TYPES = frozenset(
    {"assistant", "message", "model.completed", "subagent:assistant"}
)
_USER_TYPES = frozenset({"user", "prompt.submitted", "subagent:user"})
_END_TYPES = frozenset(
    {"session.ended", "session.end", "session.completed",
     "session.stopped", "compaction"}
)


def _coerce_dict(data: Any) -> dict:
    """Best-effort dict from an event ``data`` field (dict, JSON string, junk).
    Never raises; returns ``{}`` when nothing usable."""
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _args_hash(args: Any) -> str:
    """Stable short hash of a tool call's arguments. Order-insensitive for
    dicts (sorted keys) so logically-identical calls hash the same. Never
    raises — falls back to ``str`` then to an empty hash."""
    try:
        norm = json.dumps(args, sort_keys=True, separators=(",", ":"),
                          default=str)
    except Exception:
        try:
            norm = str(args)
        except Exception:
            return ""
    return hashlib.sha1(norm.encode("utf-8", "replace")).hexdigest()[:16]


def _iter_tool_calls_from_data(et: str, data: dict) -> list[dict]:
    """Yield ``{"tool": name, "args": value}`` for every tool invocation a
    single event describes. Covers all real shapes (top-level tool_call,
    OpenClaw v3 toolMetas, Claude-Code content tool_use blocks, family
    ``data.tool_calls`` arrays). Never raises."""
    out: list[dict] = []
    try:
        # Shape 1: top-level tool call event — name + args live on data.
        if et in _TOPLEVEL_TOOL_CALL_TYPES:
            name = data.get("tool") or data.get("tool_name") or data.get("name")
            args = (data.get("args") if data.get("args") is not None
                    else data.get("arguments") if data.get("arguments") is not None
                    else data.get("input"))
            if isinstance(name, str) and name:
                out.append({"tool": name, "args": args})
            # Some top-level rows still carry a tool_calls array; fall through.

        # Shape 2: family ``data.tool_calls`` array (claude_code/codex/cursor
        # event_type='tool_call' w/ data.tool_calls — the gap fixed in #2984).
        tcs = data.get("tool_calls")
        if isinstance(tcs, list):
            for tc in tcs:
                if not isinstance(tc, dict):
                    continue
                fn = tc.get("function") if isinstance(tc.get("function"), dict) else {}
                name = (tc.get("name") or tc.get("tool")
                        or fn.get("name"))
                args = (tc.get("args") if tc.get("args") is not None
                        else tc.get("arguments") if tc.get("arguments") is not None
                        else tc.get("input") if tc.get("input") is not None
                        else fn.get("arguments"))
                if isinstance(name, str) and name:
                    out.append({"tool": name, "args": args})

        # Shape 3: OpenClaw v3 ``toolMetas`` projection.
        metas = data.get("toolMetas")
        if isinstance(metas, list):
            for m in metas:
                if not isinstance(m, dict):
                    continue
                name = m.get("name") or m.get("tool")
                args = (m.get("args") if m.get("args") is not None
                        else m.get("arguments") if m.get("arguments") is not None
                        else m.get("input"))
                if isinstance(name, str) and name:
                    out.append({"tool": name, "args": args})

        # Shape 4: assistant ``message.content`` tool_use / toolCall blocks.
        msg = data.get("message") if isinstance(data.get("message"), dict) else None
        container = msg or data
        content = container.get("content")
        if isinstance(content, list):
            for blk in content:
                if not isinstance(blk, dict):
                    continue
                if str(blk.get("type") or "").lower() not in ("tool_use", "toolcall"):
                    continue
                name = blk.get("name") or blk.get("tool")
                args = (blk.get("input") if blk.get("input") is not None
                        else blk.get("arguments") if blk.get("arguments") is not None
                        else blk.get("args"))
                if isinstance(name, str) and name:
                    out.append({"tool": name, "args": args})
    except Exception:
        return out
    return out


def _result_text(data: dict) -> str:
    """Best-effort lower-cased text of a tool result for failure-marker
    matching. Walks ``output``/``result``/``content``/``details``/``stderr``.
    Truncated. Never raises."""
    try:
        for k in ("stderr", "error", "output", "result", "details"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                return v[:2000].lower()
        content = data.get("content")
        if isinstance(content, str) and content.strip():
            return content[:2000].lower()
        if isinstance(content, list):
            parts = []
            for blk in content:
                if isinstance(blk, dict) and isinstance(blk.get("text"), str):
                    parts.append(blk["text"])
                elif isinstance(blk, str):
                    parts.append(blk)
            if parts:
                return (" ".join(parts))[:2000].lower()
        msg = data.get("message")
        if isinstance(msg, dict):
            return _result_text(msg)
    except Exception:
        pass
    return ""


def _structured_is_error(data: dict) -> Optional[bool]:
    """Return the structured error flag if the event carries one, else None.
    Covers ``is_error``/``isError``/``error``/non-zero exit codes."""
    for k in ("is_error", "isError"):
        if k in data:
            return bool(data.get(k))
    msg = data.get("message")
    if isinstance(msg, dict):
        for k in ("is_error", "isError"):
            if k in msg:
                return bool(msg.get(k))
    err = data.get("error")
    if err not in (None, "", False):
        return True
    for k in ("exit_code", "exitCode", "returncode", "exit_status"):
        if k in data:
            try:
                return int(data.get(k)) != 0
            except (TypeError, ValueError):
                continue
    return None


def _assistant_has_text(data: dict) -> bool:
    """True if an assistant/model turn carries a real text reply (progress
    marker, not a tool-only turn). Mirrors the stuck detector's logic."""
    msg = data.get("message") if isinstance(data.get("message"), dict) else data
    content = msg.get("content")
    if isinstance(content, str) and content.strip():
        return True
    if isinstance(content, list):
        for blk in content:
            if isinstance(blk, str) and blk.strip():
                return True
            if isinstance(blk, dict):
                bt = str(blk.get("type") or "").lower()
                if bt in ("text", "output_text") and str(blk.get("text") or "").strip():
                    return True
                if not bt and str(blk.get("text") or "").strip():
                    return True
    if isinstance(msg.get("text"), str) and msg["text"].strip():
        return True
    for k in ("completionText", "completion"):
        if isinstance(data.get(k), str) and data[k].strip():
            return True
    at = data.get("assistantTexts")
    if isinstance(at, list) and any(isinstance(t, str) and t.strip() for t in at):
        return True
    return False


def _event_role(data: dict) -> str:
    role = data.get("role")
    if not role and isinstance(data.get("message"), dict):
        role = data["message"].get("role")
    return str(role or "").strip().lower()


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

_MAX_SURFACE_ITEMS = 24          # per step; bounds CPU and evidence size
_MAX_CMD_CHARS = 2000


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


def normalize_events(events: Iterable[dict]) -> list[dict]:
    """Flatten heterogenous store events (newest-first OR oldest-first) into a
    flat, CHRONOLOGICAL (oldest-first) list of NormStep dicts. A single event
    can expand into multiple tool_call steps (multi-tool turns). Never raises;
    skips malformed events. Bounded by ``DETECT_EVENT_WINDOW``.

    Accepts the store's newest-first ``query_events`` output and reverses it so
    detectors reason forward in time. ``i`` on each step is the index into the
    chronological-ordered original event list (for first_bad_step localization).
    """
    evlist = [e for e in events if isinstance(e, dict)]
    # Cap to the newest window, then present oldest-first. query_events is
    # newest-first; if a caller already passes oldest-first that's fine too —
    # we sort by ts when available, else keep input order.
    evlist = evlist[:DETECT_EVENT_WINDOW]
    evlist = list(reversed(evlist))  # store gives newest-first -> chronological

    steps: list[dict] = []
    for i, ev in enumerate(evlist):
        et = str(ev.get("event_type") or "").strip().lower()
        data = _coerce_dict(ev.get("data"))
        role = _event_role(data)

        if et in _END_TYPES:
            steps.append({"i": i, "kind": "end", "tool": "", "args_hash": "",
                          "is_error": False, "result_text": "", "has_text": False})
            continue
        if et in _USER_TYPES or role == "user":
            steps.append({"i": i, "kind": "user", "tool": "", "args_hash": "",
                          "is_error": False, "result_text": "", "has_text": False})
            continue
        if et in _TOOL_RESULT_TYPES:
            txt = _result_text(data)
            sflag = _structured_is_error(data)
            # A structured True wins; otherwise (False or absent) fall back to
            # failure-text markers — adapters that set is_error=False but emit a
            # "command not found"/non-zero stderr are still real failures.
            is_err = bool(sflag) or _text_looks_failed(txt)
            tool = (data.get("tool") or data.get("tool_name") or data.get("name")
                    or "")
            steps.append({"i": i, "kind": "tool_result",
                          "tool": str(tool or ""), "args_hash": "",
                          "is_error": is_err, "result_text": txt,
                          "has_text": False})
            continue

        # Tool CALLS (top-level or hosted inside an assistant/model envelope).
        calls = _iter_tool_calls_from_data(et, data)
        if calls:
            for c in calls:
                tool = str(c.get("tool") or "")
                paths, cmd, hosts = _action_surface(tool, c.get("args"))
                steps.append({
                    "i": i, "kind": "tool_call",
                    "tool": tool,
                    "args_hash": _args_hash(c.get("args")),
                    "is_error": False, "result_text": "", "has_text": False,
                    # Action surface (behavioural detectors read these).
                    "paths": paths, "cmd": cmd, "hosts": hosts,
                })
            continue

        # Assistant/model text turn with a real reply = a progress marker.
        if et in _ASSISTANT_TYPES or role == "assistant":
            if _assistant_has_text(data):
                steps.append({"i": i, "kind": "text", "tool": "", "args_hash": "",
                              "is_error": False, "result_text": "", "has_text": True})
                continue

        steps.append({"i": i, "kind": "other", "tool": "", "args_hash": "",
                      "is_error": False, "result_text": "", "has_text": False})
    return steps


def _text_looks_failed(text: str) -> bool:
    if not text:
        return False
    return any(m in text for m in _FAILURE_TEXT_MARKERS)


def _is_write_tool(tool: str, write_tools=None) -> bool:
    """Does this tool NAME mean a file mutation?

    ``write_tools`` is the resolved per-runtime vocabulary (the global default
    plus the runtime profile's additions). Passing None keeps the old global
    behaviour so existing callers are unaffected.
    """
    t = (tool or "").lower()
    vocab = write_tools if write_tools else WRITE_TOOL_SUBSTRINGS
    return any(sub in t for sub in vocab)


def _step_mutates(step: dict, write_tools=None) -> bool:
    """Did this step change a file — by tool name OR by shell command?

    The second half is what makes ``no_progress`` correct for shell-first
    runtimes (codex, picoclaw, nanoclaw and anything else whose edits happen
    inside ``shell``/``exec``). Before this, a codex session that wrote code
    through a heredoc looked identical to one that spun for an hour, because
    neither produced a tool call whose NAME matched a write verb.
    """
    if step.get("kind") != "tool_call":
        return False
    if _is_write_tool(step.get("tool") or "", write_tools):
        return True
    cmd = step.get("cmd") or ""
    if not cmd:
        return False
    return bool(_MUTATING_CMD_RE.search(cmd) or _REDIRECT_WRITE_RE.search(cmd))


def session_profile(steps: list, write_tools=None) -> dict:
    """Summarize one session for the cohort baseline it feeds.

    Takes already-normalized steps (the daemon has them; re-parsing 200 events
    to count them would double the tick cost for nothing) and returns the four
    numbers ``record_guard_observation`` stores: how many tool calls, how many
    distinct files mutated, whether it wrote at all, and which external hosts
    it reached.

    This is the loop that closes gap 03: today's sessions decide what counts as
    unusual tomorrow. Never raises — an empty profile just means this session
    teaches the baseline nothing.
    """
    out = {"tool_calls": 0, "write_files": 0, "wrote": False, "hosts": []}
    try:
        files = set()
        hosts = set()
        calls = 0
        for st in steps or []:
            if not isinstance(st, dict):
                continue
            for h in st.get("hosts") or ():
                hosts.add(h)
            if st.get("kind") != "tool_call" or not st.get("tool"):
                continue
            calls += 1
            if _step_mutates(st, write_tools):
                out["wrote"] = True
                for p in st.get("paths") or ():
                    files.add(p)
        out["tool_calls"] = calls
        out["write_files"] = len(files)
        out["hosts"] = sorted(hosts)[:64]
    except Exception:
        return out
    return out


def _prepare(events, steps, thresholds, runtime, session_id):
    """Shared detector preamble: resolve the runtime, its thresholds, and the
    normalized steps exactly once when the caller has already done the work."""
    rt = runtime or _runtime_of(session_id)
    th = thresholds if isinstance(thresholds, dict) else resolve_thresholds(rt)
    st = steps if steps is not None else normalize_events(events)
    return rt, th, st


def _runtime_of(session_id: str) -> str:
    try:
        from clawmetry import waste_flags as _wf
        return _wf.runtime_from_session_id(session_id) or "openclaw"
    except Exception:
        return "openclaw"


def _stop_hint() -> str:
    return "You can Stop or Pause this agent from the ClawMetry dashboard or device."


def _incident(kind: str, session_id: str, runtime: str, severity: str,
              title: str, detail: str, evidence: dict,
              first_bad_step: Optional[int]) -> dict:
    return {
        "kind": kind,
        "session_id": session_id,
        "runtime": runtime,
        "severity": severity,
        "title": title,
        "detail": detail,
        "evidence": evidence,
        "first_bad_step": first_bad_step,
    }
