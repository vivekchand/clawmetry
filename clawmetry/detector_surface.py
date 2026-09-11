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


# ── Direction: did the call SEND something, or only fetch? ───────────────────
# A host set cannot tell a package mirror an agent reads from apart from one it
# writes to. The July 2026 Hugging Face swarm used exactly that gap: WebDAV
# MKCOL/PUT to an Artifactory host every session was allowed to reach, then
# uploads to huggingface.co. So each shell segment is classified, and the hosts
# a WRITING segment reaches ride on the step as ``write_hosts``.
_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE", "MKCOL", "MOVE",
                            "COPY", "PROPPATCH", "LOCK"})
_WRITE_METHOD_ALT = "|".join(sorted(_WRITE_METHODS))
_SEGMENT_SPLIT_RE = re.compile(r"\|\||&&|[;|\n]")
# curl's flags are case-sensitive: ``-x`` is a proxy and ``-f`` is --fail, so
# only the method itself is matched case-insensitively.
_CURL_METHOD_RE = re.compile(
    r"(?:^|\s)(?:-(?!-)[A-Za-z]*X\s*|--request[=\s]+)['\"]?(?i:"
    + _WRITE_METHOD_ALT + r")\b")
_CURL_BODY_RE = re.compile(
    r"(?:^|\s)-(?!-)[A-Za-z]*[dFT](?![A-Za-z])"
    r"|(?:^|\s)--(?:data(?:-binary|-raw|-urlencode|-ascii)?|form|form-string|"
    r"json|upload-file)(?:[=\s]|$)")
# ``curl -G -d q=1`` sends the body as a query string: still a GET.
_CURL_GET_RE = re.compile(r"(?:^|\s)(?:-(?!-)[A-Za-z]*G(?![A-Za-z])|--get\b)")
_WGET_WRITE_RE = re.compile(
    r"--(?:post-data|post-file|body-data|body-file)\b|--method[=\s]+['\"]?(?i:"
    + _WRITE_METHOD_ALT + r")\b")
_HTTPIE_WRITE_RE = re.compile(
    r"^(?:https?|xh|xhs)\s+(?:-\S+\s+)*(?i:" + _WRITE_METHOD_ALT + r")\s")
_LIB_WRITE_RE = re.compile(r"\b(?:requests|httpx)\.(?:post|put|patch|delete)\s*\(", re.I)
# Publishing commands. Where the command names no URL the destination is the
# registry's public host; ``""`` means "only when a URL or remote is named".
_PUBLISH_CMDS = (
    (re.compile(r"\btwine\s+upload\b|\b(?:uv|poetry|flit|hatch)\s+publish\b", re.I),
     "upload.pypi.org"),
    (re.compile(r"\b(?:npm|pnpm)\s+publish\b|\byarn\s+(?:npm\s+)?publish\b", re.I),
     "registry.npmjs.org"),
    (re.compile(r"\b(?:huggingface-cli|hf)\s+upload\b", re.I), "huggingface.co"),
    (re.compile(r"\bcargo\s+publish\b", re.I), "crates.io"),
    (re.compile(r"\bgem\s+push\b", re.I), "rubygems.org"),
    (re.compile(r"\bgit\s+push\b", re.I), ""),
)
# Copies whose DESTINATION (the last argument) decides the direction.
_REMOTE_COPY_RE = re.compile(
    r"\b(?:gsutil\s+(?:-\S+\s+)*(?:cp|mv|rsync)|gcloud\s+storage\s+(?:cp|mv|rsync)|"
    r"aws\s+s3\s+(?:cp|mv|sync)|scp|rsync|sftp)\b", re.I)
_WRAPPER_PROGRAMS = frozenset({"sudo", "env", "time", "nohup", "command", "exec",
                               "nice", "doas"})


def _program(segment: str) -> str:
    """The program a shell segment runs, past ``sudo``/``env``/``VAR=1``."""
    for tok in segment.split()[:8]:
        if tok in _WRAPPER_PROGRAMS or (("=" in tok) and not tok.startswith("-")):
            continue
        if tok.startswith("-"):
            continue
        return tok.rsplit("/", 1)[-1].lower()
    return ""


def _segment_write_hosts(segment: str) -> list:
    """Hosts one shell segment SENDS data to. ``[]`` for a read. Never raises."""
    try:
        seg = segment.strip()
        if not seg:
            return []
        prog = _program(seg)
        if prog == "curl":
            if _CURL_METHOD_RE.search(seg) or (
                    _CURL_BODY_RE.search(seg) and not _CURL_GET_RE.search(seg)):
                return _hosts_from_text(seg)
            return []
        if prog == "wget":
            return _hosts_from_text(seg) if _WGET_WRITE_RE.search(seg) else []
        if prog in ("http", "https", "xh", "xhs"):
            return _hosts_from_text(seg) if _HTTPIE_WRITE_RE.search(seg) else []
        if _REMOTE_COPY_RE.search(seg):
            last = seg.split()[-1].strip("'\"")
            if "://" in last or re.search(r"^[\w.\-]+@[\w.\-]+:", last):
                return _hosts_from_text(last)
            return []
        for rx, implied in _PUBLISH_CMDS:
            if rx.search(seg):
                named = _hosts_from_text(seg)
                return named or ([implied] if implied else [])
        if _LIB_WRITE_RE.search(seg):
            return _hosts_from_text(seg)
    except Exception:
        return []
    return []


def _write_hosts(tool: str, args, cmd: str) -> tuple:
    """Hosts a tool call sent data to, from its shell segments and, for HTTP
    tools that take a ``method`` argument, from the method it named."""
    out: list = []
    try:
        if isinstance(args, dict):
            method = args.get("method") or args.get("http_method") or ""
            if isinstance(method, str) and method.strip().upper() in _WRITE_METHODS:
                for val in list(args.values())[:40]:
                    if isinstance(val, str) and val.startswith(("http://", "https://")):
                        out.extend(_hosts_from_text(val))
        for seg in _SEGMENT_SPLIT_RE.split((cmd or "")[:_MAX_CMD_CHARS])[:40]:
            out.extend(_segment_write_hosts(seg))
    except Exception:
        pass
    return tuple(dict.fromkeys(h for h in out if h))[:_MAX_SURFACE_ITEMS]


# ── Secret VALUES: a token in the agent's hand, not a file it opened ─────────
# ``credential_access`` used to match locations only (``~/.ssh``, ``.env``), so
# a live token pasted into a command was invisible: 0 of 45 in the vendored
# corpus. The swarm read Hugging Face write tokens out of tool output and posted
# them to a shared board. Each entry is (category, regex, owner hosts): the
# hosts the token legitimately goes to. ``None`` means "no claim" (a JWT goes
# to whatever API issued it); ``()`` means "no host should ever receive this".
# Only the CATEGORY ever leaves this module. Every regex is case-insensitive
# because tool-result text is lower-cased before it reaches the detectors.
_NO_OWNER: tuple = ()
_SECRET_VALUE_PATTERNS = (
    ("Hugging Face token", r"(?<![a-z0-9])hf_[a-z0-9]{30,}",
     ("huggingface.co", "hf.co")),
    ("GitHub token", r"(?<![a-z0-9_])(?:gh[pousr]_[a-z0-9]{36,}|github_pat_[a-z0-9_]{50,})",
     ("github.com", "githubusercontent.com")),
    ("AWS access key", r"(?<![a-z0-9])(?:akia|asia)[a-z0-9]{16}(?![a-z0-9])",
     ("amazonaws.com",)),
    ("Google API key", r"(?<![a-z0-9_-])aiza[0-9a-z_-]{35}(?![a-z0-9_-])",
     ("googleapis.com",)),
    # A digit AND an unbroken run of 20+ alphanumerics: every real key has one
    # (``sk-proj-…``, ``sk-ant-api03-…``); a kebab-case branch name such as
    # ``sk-2024-release-notes-draft-final`` never does.
    ("OpenAI or Anthropic API key",
     r"(?<![a-z0-9_-])sk-(?=[a-z0-9_-]{0,200}\d)[a-z0-9_-]{0,40}?[a-z0-9]{20,}",
     ("openai.com", "anthropic.com")),
    ("Slack token", r"(?<![a-z0-9])xox[abprs]-[a-z0-9-]{10,}", ("slack.com",)),
    ("Stripe secret key", r"(?<![a-z0-9])[rs]k_live_[a-z0-9]{16,}", ("stripe.com",)),
    ("JSON web token",
     r"(?<![a-z0-9_-])eyj[a-z0-9_-]{8,}\.eyj[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}", None),
    ("private key block", r"-----begin (?:[a-z]+ )*private key-----", _NO_OWNER),
    # Ported from the Apache-2.0 pipelock-community DLP bundle (vendored with
    # its licence under tests/fixtures/pipelock_rules; see PROVENANCE.md).
    # One deliberate change: a left boundary. Upstream scans HTTP bodies; we
    # scan shell text, where ``views-dashboardcomponent`` would otherwise
    # match the Modal ``ws-`` rule.
    ("1Password service account token", r"(?<![a-z0-9])ops_[a-z0-9]{20,}", ("1password.com",)),
    ("Buildkite token", r"(?<![a-z0-9])bkua_[a-z0-9]{20,}", ("buildkite.com",)),
    ("Doppler token", r"(?<![a-z0-9])dp\.[a-z]{2}\.[a-z0-9_-]+\.[a-z0-9_-]{20,}", ("doppler.com",)),
    ("Modal token", r"(?<![a-z0-9])w[ks]-[a-z0-9]{16,}", ("modal.com",)),
    ("Perplexity API key", r"(?<![a-z0-9])pplx-[a-z0-9]{16,}", ("perplexity.ai",)),
    ("Pulumi token", r"(?<![a-z0-9])pul-[a-z0-9]{20,}", ("pulumi.com",)),
    ("Shopify token", r"(?<![a-z0-9])shp(?:at|pa|ca|ua|ss)_[a-f0-9]{16,}",
     ("myshopify.com", "shopify.com")),
    ("Vercel token", r"(?<![a-z0-9])vc[kip]_[a-z0-9._-]{16,}", ("vercel.com",)),
)
_SECRET_VALUE_RX = tuple((label, re.compile(rx, re.I), owners)
                         for label, rx, owners in _SECRET_VALUE_PATTERNS)
SECRET_VALUE_OWNERS = {label: owners for label, _rx, owners in _SECRET_VALUE_RX}
_MAX_VALUE_SCAN_CHARS = 8000


def _looks_placeholder(value: str) -> bool:
    """Documentation tokens: ``AKIAIOSFODNN7EXAMPLE``, ``ghp_XXXX…``. Real
    tokens are high-entropy; a body with few distinct characters is not one."""
    body = value.lower()
    body = body.split("_", 1)[-1] if "_" in body[:12] else body
    return ("example" in body or "xxxx" in body or "your" in body[:8]
            or len(set(body)) < 8)


def _secret_value_categories(text: str) -> tuple:
    """Categories of secret-shaped values in ``text``. Never the values."""
    if not text:
        return ()
    try:
        window = str(text)[:_MAX_VALUE_SCAN_CHARS]
        out = []
        for label, rx, _o in _SECRET_VALUE_RX:
            for m in rx.finditer(window):
                if not _looks_placeholder(m.group(0)):
                    out.append(label)
                    break
        return tuple(out)
    except Exception:
        return ()


def _args_text(args) -> str:
    """The raw argument text a value scan reads. Heredoc bodies are KEPT here,
    unlike the command surface: a token written into a file the agent is about
    to send is still a token in the agent's hand."""
    try:
        if isinstance(args, str):
            return args[:_MAX_VALUE_SCAN_CHARS]
        import json as _json
        return _json.dumps(args, default=str)[:_MAX_VALUE_SCAN_CHARS]
    except Exception:
        return ""


def host_owned_by(host: str, owners) -> bool:
    """True when ``host`` is one of ``owners`` or a subdomain of one."""
    h = str(host or "").lower().rstrip(".")
    return any(h == o or h.endswith("." + o) for o in (owners or ()))


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
