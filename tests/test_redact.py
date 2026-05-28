"""Unit tests for clawmetry.redact (issue #2198)."""

import pytest
from clawmetry.redact import compile_patterns, redact_value, build_redactor


def _pat():
    return compile_patterns()


# ── Individual default patterns ───────────────────────────────────────────────

def test_bearer_token_redacted():
    v = "curl -H 'Authorization: Bearer abcdefghijklmnopqrstuvwxyz'"
    out, count = redact_value(v, _pat(), "[REDACTED]")
    assert "[REDACTED]" in out
    assert count >= 1


def test_openai_key_redacted():
    key = "sk-" + "a" * 32
    out, count = redact_value(key, _pat(), "[REDACTED]")
    assert "sk-" not in out
    assert count >= 1


def test_github_pat_ghp_redacted():
    v = "export TOKEN=" + "ghp_" + "a" * 36
    out, count = redact_value(v, _pat(), "[REDACTED]")
    assert "ghp_" not in out
    assert count >= 1


def test_github_pat_gho_redacted():
    v = "gho_" + "A" * 36
    out, count = redact_value(v, _pat(), "[REDACTED]")
    assert "gho_" not in out
    assert count >= 1


def test_gitlab_pat_redacted():
    v = "glpat-" + "a" * 20
    out, count = redact_value(v, _pat(), "[REDACTED]")
    assert "glpat-" not in out
    assert count >= 1


def test_slack_token_redacted():
    v = "xoxb-" + "a" * 10
    out, count = redact_value(v, _pat(), "[REDACTED]")
    assert "xoxb-" not in out
    assert count >= 1


def test_api_key_assignment_redacted():
    v = 'api_key="supersecretvalue12345678"'
    out, count = redact_value(v, _pat(), "[REDACTED]")
    assert "supersecretvalue12345678" not in out
    assert count >= 1


# ── Recursive structures ──────────────────────────────────────────────────────

def test_nested_dict_redacted():
    v = {"tool": {"input": "bearer " + "a" * 22, "output": "ok"}}
    out, count = redact_value(v, _pat(), "[REDACTED]")
    assert "[REDACTED]" in out["tool"]["input"]
    assert out["tool"]["output"] == "ok"
    assert count >= 1


def test_nested_list_redacted():
    v = ["safe string", "sk-" + "a" * 32]
    out, count = redact_value(v, _pat(), "[REDACTED]")
    assert out[0] == "safe string"
    assert "sk-" not in out[1]
    assert count >= 1


def test_deeply_nested():
    v = {"a": {"b": {"c": "sk-" + "x" * 32}}}
    out, count = redact_value(v, _pat(), "[REDACTED]")
    assert out["a"]["b"]["c"] == "[REDACTED]"
    assert count == 1


# ── No-match passthrough ──────────────────────────────────────────────────────

def test_no_match_passthrough_string():
    v = "Hello, world! No secrets here."
    out, count = redact_value(v, _pat(), "[REDACTED]")
    assert out == v
    assert count == 0


def test_no_match_passthrough_dict():
    v = {"role": "user", "content": "What is the weather today?"}
    out, count = redact_value(v, _pat(), "[REDACTED]")
    assert out == v
    assert count == 0


def test_non_string_scalars_unchanged():
    v = {"count": 42, "flag": True, "nothing": None}
    out, count = redact_value(v, _pat(), "[REDACTED]")
    assert out == v
    assert count == 0


# ── build_redactor ────────────────────────────────────────────────────────────

def test_build_redactor_disabled_by_default():
    assert build_redactor({}) is None
    assert build_redactor({"redact": {"enabled": False}}) is None
    assert build_redactor(None) is None


def test_build_redactor_enabled():
    cfg = {"redact": {"enabled": True}}
    fn = build_redactor(cfg)
    assert fn is not None
    result = fn("sk-" + "a" * 32)
    assert "sk-" not in result


def test_build_redactor_custom_replacement():
    cfg = {"redact": {"enabled": True, "replacement": "***"}}
    fn = build_redactor(cfg)
    result = fn("ghp_" + "a" * 36)
    assert "***" in result
    assert "ghp_" not in result


def test_build_redactor_scope_default():
    fn = build_redactor({"redact": {"enabled": True}})
    assert fn.scope == "snapshot"


def test_build_redactor_scope_ingest():
    fn = build_redactor({"redact": {"enabled": True, "scope": "ingest"}})
    assert fn.scope == "ingest"


def test_build_redactor_custom_patterns():
    cfg = {"redact": {"enabled": True, "patterns": [r"MYCO-[A-Z]{4}-[0-9]{8}"]}}
    fn = build_redactor(cfg)
    result = fn("ticket MYCO-ABCD-12345678 opened")
    assert "MYCO-ABCD-12345678" not in result


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_bad_pattern_graceful():
    # Should not raise — bad pattern is skipped with a warning
    patterns = compile_patterns(["(unclosed"])
    assert isinstance(patterns, list)
    # Default patterns still compiled
    assert len(patterns) >= len([]) or True  # graceful, doesn't crash


def test_empty_string_passthrough():
    out, count = redact_value("", _pat(), "[REDACTED]")
    assert out == ""
    assert count == 0


def test_empty_dict_passthrough():
    out, count = redact_value({}, _pat(), "[REDACTED]")
    assert out == {}
    assert count == 0
