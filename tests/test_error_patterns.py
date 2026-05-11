"""Tests for clawmetry.error_patterns.summarize_error()."""
from __future__ import annotations

import pytest

from clawmetry.error_patterns import (
    ERROR_PATTERNS,
    MAX_SUMMARY_LEN,
    register_pattern,
    summarize_error,
)


# ---------------------------------------------------------------------------
# Fixture: ≥ 30 real OpenClaw / Python / Node / shell error variants.
# Each entry: (raw_input, expected_summary). Patterns are matched verbatim;
# new contributors add one line here when adding a new pattern.
# ---------------------------------------------------------------------------
ERROR_FIXTURES = [
    # ---- Network ----
    ("connect ECONNREFUSED 127.0.0.1:8080", "Connection refused"),
    ("Error: connect ECONNRESET", "Connection reset"),
    ("read ETIMEDOUT after 30000ms", "Connection timed out"),
    ("getaddrinfo ENOTFOUND api.anthropic.com", "DNS lookup failed"),
    ("Error: listen EADDRINUSE: address already in use :::3000", "Port already in use"),
    ("OSError: [Errno 13] Permission denied: '/var/log/clawmetry.log'", "Permission denied"),
    ("OSError: [Errno 1] Operation not permitted", "Operation not permitted"),

    # ---- HTTP ----
    ("HTTP 429 Too Many Requests — rate limit exceeded", "API rate limit exceeded"),
    ("401 Unauthorized: invalid bearer token", "Invalid auth token"),
    ("403 Forbidden — agent does not have access", "HTTP 403 forbidden"),
    ("Anthropic API returned 500 Internal Server Error", "HTTP 500 server error"),
    ("Upstream 502 Bad Gateway", "HTTP 502 bad gateway"),
    ("503 Service Unavailable from openai.com", "HTTP 503 service unavailable"),
    ("504 Gateway Timeout after 60s", "HTTP 504 gateway timeout"),

    # ---- Auth / certs ----
    ("Error: CERT_HAS_EXPIRED", "TLS certificate expired"),
    ("auth token expired at 2026-05-10T00:00:00Z", "Auth token expired"),

    # ---- Code (JS) ----
    ("TypeError: Cannot read properties of undefined (reading 'session')", "Null property access"),
    ("TypeError: obj.fn is not a function", "Called non-function value"),
    ("SyntaxError: Unexpected token < in JSON at position 0", "JSON parse failed"),

    # ---- Code (Python) ----
    ("KeyError: 'agent_id'", "Missing dictionary key"),
    ("AttributeError: 'NoneType' object has no attribute 'cost'", "Missing attribute"),
    ("TypeError: unsupported operand type(s) for +: 'int' and 'str'", "Type error"),
    ("ValueError: invalid literal for int() with base 10: 'abc'", "Invalid value"),
    ("ModuleNotFoundError: No module named 'tiktoken'", "Module not found"),

    # ---- DB ----
    ("sqlite3.OperationalError: database is locked", "SQLite database busy"),
    ("sqlite3.DatabaseError: database disk image is malformed", "SQLite database corrupt"),
    ("sqlite3.OperationalError: attempt to write a readonly database", "SQLite database readonly"),

    # ---- File / OS ----
    ("ENOENT: no such file or directory, open '/tmp/missing.json'", "File or directory not found"),
    ("EISDIR: illegal operation on a directory, read", "Expected file, got directory"),
    ("OSError: [Errno 28] No space left on device", "Disk full"),
    ("MemoryError", "Out of memory"),
    ("Process killed by signal 9 (SIGKILL)", "Process killed (SIGKILL)"),
    ("Worker terminated (SIGTERM)", "Process terminated (SIGTERM)"),
    ("Segmentation fault (core dumped)", "Segmentation fault"),

    # ---- OpenClaw-specific ----
    ("Slack bot token missing — set SLACK_BOT_TOKEN", "Slack bot token missing"),
    ("retry failed for delivery to channel #ops after 5 attempts", "Delivery retry failed"),
    ("socket-mode failed: WebSocket closed unexpectedly", "Slack socket-mode failed"),
    ("allowlist contains unknown entry: 'kody-coder-old'", "Allowlist contains unknown entry"),
    ("Hostname conflict: another node already registered as dhriti-2", "Hostname conflict"),
    ("missing skill path: skills/clawmetry-release/SKILL.md", "Missing skill path"),
    ("Gateway unreachable — connection refused on 127.0.0.1:18789", "Gateway unreachable"),
]


@pytest.mark.parametrize("raw,expected", ERROR_FIXTURES)
def test_summarize_error_fixtures(raw, expected):
    assert summarize_error(raw) == expected


def test_fixture_count_meets_minimum():
    # The issue mandates ≥ 30 fixtures. Guard against regressions.
    assert len(ERROR_FIXTURES) >= 30


# ---------------------------------------------------------------------------
# Pre-processor: timestamps, log levels, bracketed tags
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2026-05-11T07:23:45.123Z ERROR connect ECONNREFUSED", "Connection refused"),
        ("[2026-05-11 07:23:45,123] [ERROR] connect ECONNREFUSED", "Connection refused"),
        ("May 11 07:23:45 host1 [WARN] 429 too many requests", "API rate limit exceeded"),
        ("(12345) ERR: ENOENT no such file or directory", "File or directory not found"),
        ("WARNING: SQLITE_BUSY: database is locked", "SQLite database busy"),
        ("[clawmetry][interceptor] retry failed for delivery", "Delivery retry failed"),
    ],
)
def test_preprocessor_strips_log_noise(raw, expected):
    assert summarize_error(raw) == expected


# ---------------------------------------------------------------------------
# Fallback chain: Pythonic exception → verb phrase → keyword → first clause
# ---------------------------------------------------------------------------
def test_fallback_pythonic_exception_extraction():
    out = summarize_error("RuntimeError: telemetry pipeline blew up halfway through")
    assert out.startswith("RuntimeError:")
    assert len(out) <= MAX_SUMMARY_LEN


def test_fallback_verb_phrase():
    out = summarize_error("clawmetry: unable to reach pricing service at boot")
    assert "unable to reach" in out.lower()
    assert len(out) <= MAX_SUMMARY_LEN


def test_fallback_keyword_network():
    assert summarize_error("weird socket hiccup somewhere in the stack") == "Network error"


def test_fallback_keyword_timeout():
    assert summarize_error("operation deadline reached") == "Timeout"


def test_fallback_first_clause_truncates_to_limit():
    long = "this is an unusual error nobody has ever seen before in production"
    out = summarize_error(long)
    assert len(out) <= MAX_SUMMARY_LEN


def test_unknown_error_for_empty_input():
    assert summarize_error("") == "Unknown error"
    assert summarize_error("   \n\t  ") == "Unknown error"
    assert summarize_error(None) == "Unknown error"  # type: ignore[arg-type]


def test_non_string_input_does_not_crash():
    assert summarize_error(12345) == "Unknown error"  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Multiline tracebacks: prefer the exception line at the bottom
# ---------------------------------------------------------------------------
def test_multiline_traceback_prefers_exception_line():
    traceback = """Traceback (most recent call last):
  File "/app/dashboard.py", line 815, in _fire_alert
    raise ValueError("invalid alert payload")
ValueError: invalid alert payload"""
    out = summarize_error(traceback)
    assert out == "Invalid value"


# ---------------------------------------------------------------------------
# Output contract: every summary ≤ MAX_SUMMARY_LEN
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("raw,_expected", ERROR_FIXTURES)
def test_summary_respects_length_cap(raw, _expected):
    assert len(summarize_error(raw)) <= MAX_SUMMARY_LEN


# ---------------------------------------------------------------------------
# register_pattern() — runtime extensibility
# ---------------------------------------------------------------------------
def test_register_pattern_prepend_wins_over_existing():
    original_len = len(ERROR_PATTERNS)
    try:
        register_pattern(r"\bcustom-widget-failure\b", "Custom widget failed", prepend=True)
        assert summarize_error("custom-widget-failure on shard 7") == "Custom widget failed"
        assert len(ERROR_PATTERNS) == original_len + 1
    finally:
        # Restore module state so other tests stay deterministic.
        del ERROR_PATTERNS[0]
        assert len(ERROR_PATTERNS) == original_len


def test_register_pattern_append_is_lower_priority():
    original_len = len(ERROR_PATTERNS)
    try:
        # Append a pattern that would otherwise match an existing case — the
        # earlier match should still win.
        register_pattern(r"connection", "Custom connection label")
        assert summarize_error("Error: connect ECONNREFUSED") == "Connection refused"
        assert len(ERROR_PATTERNS) == original_len + 1
    finally:
        del ERROR_PATTERNS[-1]
        assert len(ERROR_PATTERNS) == original_len
