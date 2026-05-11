"""
clawmetry.error_patterns — translate raw error text into short human summaries.

Operators reading an alert on their phone need a glanceable label, not 4 KB of
stack trace. ``summarize_error()`` runs the input through:

1. A pre-processor that strips timestamps, log levels, and bracketed tags so the
   pattern library can match the actual message body.
2. A regex pattern library grouped by category (network, HTTP, code, DB, auth,
   file/OS, OpenClaw-specific). First match wins.
3. A smart fallback chain when no pattern matches: extract ``SomeError: body``,
   then a leading verb phrase, then a keyword category, then a hard-truncated
   first clause.

Every return value is capped at ``MAX_SUMMARY_LEN`` characters (default 50).

Adding a new pattern is a one-line append to ``ERROR_PATTERNS`` plus a fixture
in ``tests/test_error_patterns.py``.
"""
from __future__ import annotations

import re
from typing import Iterable, List, Pattern, Tuple

MAX_SUMMARY_LEN = 50

# Strip ISO timestamps, syslog timestamps, log levels, bracketed tags, leading
# pid/thread markers — anything that pads the front of a log line and would
# otherwise prevent the body from matching a pattern.
_TIMESTAMP_PATTERNS: Tuple[Pattern[str], ...] = (
    # 2026-05-11T07:23:45.123Z / 2026-05-11 07:23:45,123 / 2026-05-11T07:23:45+00:00
    re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?\s*"),
    # May 11 07:23:45 host
    re.compile(r"^[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\S+\s*"),
    # 07:23:45.123 / 07:23:45
    re.compile(r"^\d{2}:\d{2}:\d{2}(?:[.,]\d+)?\s*"),
)

_LEVEL_PATTERN = re.compile(
    r"^(?:\[?\s*)(?:TRACE|DEBUG|INFO|NOTICE|WARN(?:ING)?|ERR(?:OR)?|FATAL|CRITICAL)(?:\s*\])?[:\s-]*",
    re.IGNORECASE,
)

# [tag] or (tag) at the start, possibly multiple
_BRACKET_TAG_PATTERN = re.compile(r"^(?:\[[^\]\n]{1,40}\]|\([^)\n]{1,40}\))\s*")

# pid=123 / tid=abc / (12345) on its own
_PID_PATTERN = re.compile(r"^\(\d+\)\s*|^pid=\d+\s+|^tid=\S+\s+", re.IGNORECASE)


def _preprocess(text: str) -> str:
    """Strip log noise from the front of an error line."""
    if not text:
        return ""
    line = text.strip()
    # Some inputs are multiline tracebacks — collapse to first non-empty line
    # but keep the LAST line too because Python tracebacks put the exception
    # on the final line. We pick whichever line is most informative below.
    lines = [ln for ln in line.splitlines() if ln.strip()]
    if lines:
        # If the last line looks like "SomeError: ...", prefer it.
        last = lines[-1].strip()
        if re.match(r"^[A-Z][A-Za-z0-9_]*(?:Error|Exception|Warning)\b", last):
            line = last
        else:
            line = lines[0].strip()

    # Repeatedly strip prefixes until nothing changes.
    for _ in range(6):
        before = line
        for pat in _TIMESTAMP_PATTERNS:
            line = pat.sub("", line, count=1)
        line = _PID_PATTERN.sub("", line, count=1)
        line = _LEVEL_PATTERN.sub("", line, count=1)
        line = _BRACKET_TAG_PATTERN.sub("", line, count=1)
        line = line.lstrip()
        if line == before:
            break
    return line


# Pattern library. Order matters: earlier = higher priority. Each entry is a
# compiled regex paired with the canonical short summary. Patterns are matched
# against the preprocessed error body using ``re.search``.
_RAW_PATTERNS: Tuple[Tuple[str, str], ...] = (
    # ---- OpenClaw-specific (match first so they aren't shadowed by generic) ----
    (r"slack[_ ]bot[_ ]token[^a-z0-9]*(missing|not set|empty)", "Slack bot token missing"),
    (r"retry failed for delivery", "Delivery retry failed"),
    (r"socket[- ]mode (failed|disconnected|error)", "Slack socket-mode failed"),
    (r"allowlist contains unknown", "Allowlist contains unknown entry"),
    (r"hostname conflict", "Hostname conflict"),
    (r"missing skill path", "Missing skill path"),
    (r"gateway (unreachable|connection refused|not responding)", "Gateway unreachable"),
    # ---- Auth / certs ----
    (r"\bCERT_HAS_EXPIRED\b", "TLS certificate expired"),
    (r"\bCERT_NOT_YET_VALID\b", "TLS certificate not yet valid"),
    (r"\b(SELF_SIGNED_CERT|UNABLE_TO_VERIFY_LEAF_SIGNATURE|DEPTH_ZERO_SELF_SIGNED_CERT)\b", "TLS certificate untrusted"),
    (r"\btoken (?:has |is )?expired\b", "Auth token expired"),
    (r"\binvalid (?:\w+\s+){0,2}token\b", "Invalid auth token"),
    # ---- HTTP status ----
    (r"\b(?:rate[- ]?limit(?:ed)?|429\b|too many requests)\b", "API rate limit exceeded"),
    (r"\b401\b|\bunauthorized\b", "HTTP 401 unauthorized"),
    (r"\b403\b|\bforbidden\b", "HTTP 403 forbidden"),
    (r"\b404\b|\bnot found\b", "HTTP 404 not found"),
    (r"\b500\b|\binternal server error\b", "HTTP 500 server error"),
    (r"\b502\b|\bbad gateway\b", "HTTP 502 bad gateway"),
    (r"\b503\b|\bservice unavailable\b", "HTTP 503 service unavailable"),
    (r"\b504\b|\bgateway timeout\b", "HTTP 504 gateway timeout"),
    # ---- Network ----
    (r"\bECONNREFUSED\b|connection refused", "Connection refused"),
    (r"\bECONNRESET\b|connection reset", "Connection reset"),
    (r"\bETIMEDOUT\b|connection timed out|connect timeout", "Connection timed out"),
    (r"\bENOTFOUND\b|name (or service )?not (resolved|known)|getaddrinfo (failed|enotfound)", "DNS lookup failed"),
    (r"\bEADDRINUSE\b|address already in use", "Port already in use"),
    (r"\bEPERM\b|operation not permitted", "Operation not permitted"),
    (r"\bEACCES\b|permission denied", "Permission denied"),
    # ---- Code (JS-ish & Python) ----
    (r"cannot read propert(?:y|ies) of (?:undefined|null)", "Null property access"),
    (r"is not a function", "Called non-function value"),
    (r"\bJSON\.parse\b|JSONDecodeError|expecting value|invalid json|unexpected token\s.+\bin json\b", "JSON parse failed"),
    (r"\bKeyError: ", "Missing dictionary key"),
    (r"\bAttributeError: ", "Missing attribute"),
    (r"\bTypeError: ", "Type error"),
    (r"\bValueError: ", "Invalid value"),
    (r"\bImportError: |ModuleNotFoundError: ", "Module not found"),
    # ---- DB ----
    (r"\bSQLITE_BUSY\b|database is locked", "SQLite database busy"),
    (r"\bSQLITE_CORRUPT\b|database disk image is malformed", "SQLite database corrupt"),
    (r"\bSQLITE_READONLY\b|attempt to write a readonly database", "SQLite database readonly"),
    # ---- File / OS ----
    (r"\bENOENT\b|no such file or directory", "File or directory not found"),
    (r"\bEISDIR\b|is a directory", "Expected file, got directory"),
    (r"\bENOSPC\b|no space left on device", "Disk full"),
    (r"\b(out of memory|MemoryError|OOMKilled|cannot allocate memory)\b", "Out of memory"),
    (r"\bSIGKILL\b|killed( by signal 9)?", "Process killed (SIGKILL)"),
    (r"\bSIGTERM\b|terminated( by signal 15)?", "Process terminated (SIGTERM)"),
    (r"\bSIGSEGV\b|segmentation fault", "Segmentation fault"),
)

# Compile once. Case-insensitive so operators don't have to worry about logger casing.
ERROR_PATTERNS: List[Tuple[Pattern[str], str]] = [
    (re.compile(pat, re.IGNORECASE), summary) for pat, summary in _RAW_PATTERNS
]


_VERB_PHRASE_PATTERN = re.compile(
    r"\b(failed to|cannot|unable to|could not|can't|won't|refused to|did not)\b[^.;\n]{1,60}",
    re.IGNORECASE,
)

_PYTHONIC_EXCEPTION = re.compile(r"\b([A-Z][A-Za-z0-9_]*(?:Error|Exception|Warning))\s*:\s*(.+)")

_KEYWORD_CATEGORIES: Tuple[Tuple[Pattern[str], str], ...] = (
    (re.compile(r"\b(connect|socket|tcp|udp|network)\b", re.IGNORECASE), "Network error"),
    (re.compile(r"\b(permission|denied|forbidden|unauthorized)\b", re.IGNORECASE), "Permission error"),
    (re.compile(r"\b(invalid|unexpected|malformed|corrupt)\b", re.IGNORECASE), "Invalid input"),
    (re.compile(r"\b(missing|not found|absent|undefined)\b", re.IGNORECASE), "Missing resource"),
    (re.compile(r"\b(timeout|timed out|deadline)\b", re.IGNORECASE), "Timeout"),
)


def _truncate(text: str, limit: int = MAX_SUMMARY_LEN) -> str:
    text = " ".join(text.split())  # collapse whitespace
    if len(text) <= limit:
        return text
    # leave room for a trailing ellipsis
    return text[: max(1, limit - 1)].rstrip(" ,.;:-_") + "…"


def _humanize_pythonic(match: "re.Match[str]") -> str:
    name, body = match.group(1), match.group(2).strip()
    # Drop trailing tracebacks (next line). Body may include file paths — keep
    # the first clause.
    body = re.split(r"\s+at\s+|\sin\s+/", body, maxsplit=1)[0]
    short = f"{name}: {body}".strip(" :")
    return _truncate(short)


def _fallback_summary(line: str) -> str:
    """When no pattern matches, do progressively cheaper extraction."""
    if not line:
        return "Unknown error"

    pythonic = _PYTHONIC_EXCEPTION.search(line)
    if pythonic:
        return _humanize_pythonic(pythonic)

    verb = _VERB_PHRASE_PATTERN.search(line)
    if verb:
        return _truncate(verb.group(0))

    for pat, label in _KEYWORD_CATEGORIES:
        if pat.search(line):
            return label

    # Last resort: first clause, truncated. Strip a trailing colon/period that
    # would otherwise look ragged.
    first_clause = re.split(r"[.;\n]", line, maxsplit=1)[0]
    return _truncate(first_clause) or "Unknown error"


def summarize_error(text: str) -> str:
    """Return a short (≤ 50 char) human-readable summary of *text*.

    Never raises. Empty / whitespace-only input becomes ``"Unknown error"``.
    """
    if not isinstance(text, str):
        return "Unknown error"

    line = _preprocess(text)
    if not line:
        return "Unknown error"

    for pattern, summary in ERROR_PATTERNS:
        if pattern.search(line):
            return _truncate(summary)

    return _fallback_summary(line)


def register_pattern(regex: str, summary: str, *, prepend: bool = False) -> None:
    """Add a custom pattern at runtime.

    ``prepend=True`` puts the new pattern at the front so it wins over earlier
    matches — useful for product-specific overrides during local development.
    """
    compiled = re.compile(regex, re.IGNORECASE)
    entry = (compiled, summary)
    if prepend:
        ERROR_PATTERNS.insert(0, entry)
    else:
        ERROR_PATTERNS.append(entry)


def iter_patterns() -> Iterable[Tuple[Pattern[str], str]]:
    """Read-only iterator over the current pattern table (for introspection)."""
    return tuple(ERROR_PATTERNS)


__all__ = [
    "MAX_SUMMARY_LEN",
    "ERROR_PATTERNS",
    "summarize_error",
    "register_pattern",
    "iter_patterns",
]
