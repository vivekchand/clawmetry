"""What a tool call SENT, and what it CARRIED.

Split out of :mod:`clawmetry.detector_surface`, which says what a call touched
(paths, command, hosts). This module holds the two capabilities the Hugging
Face swarm scorecard showed were missing (REQ-OBS-RSO-034), kept short so the
whole of them is readable in one place:

* **Direction.** ``_write_hosts`` / ``_segment_write_hosts`` classify each
  shell segment as a read or a write, so ``network_egress`` can tell a mirror an
  agent reads from apart from one it writes to. ``detectors.normalize_events``
  stamps the result on every tool-call step as ``write_hosts``.
* **Credential values.** ``_secret_value_categories`` matches token shapes in
  raw arguments and in tool output; ``detectors.normalize_events`` stamps the
  categories on each step as ``secret_values``. ``SECRET_VALUE_OWNERS`` and
  ``host_owned_by`` say which hosts a kind of token legitimately goes to, which
  is how ``credential_access`` tells a token used from a token leaked. Only the
  CATEGORY ever leaves this module.
"""
from __future__ import annotations

import re

from clawmetry.detector_surface import _MAX_CMD_CHARS, _MAX_SURFACE_ITEMS, _hosts_from_text


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
