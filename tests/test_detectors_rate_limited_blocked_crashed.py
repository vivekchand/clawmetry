"""Silent-failure detectors: rate_limited / blocked_on_user / crashed.

Pure unit tests over synthetic event sequences in the store's newest-first
``query_events`` shape. Each detector gets a positive case, a negative case
(a legitimate pattern it must not flag), and a contract check (severity,
threshold_source, honest ``observed``, spend annotation via ``run_all``).
"""
from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import detectors  # noqa: E402


def _ts(i: int) -> str:
    return f"2026-06-11T10:{i // 60:02d}:{i % 60:02d}"


def _ev(et: str, data: dict, i: int) -> dict:
    return {"event_type": et, "ts": _ts(i), "data": data}


def _newest_first(*evs):
    return list(reversed(list(evs)))


def _kinds(incidents):
    return [i["kind"] for i in incidents]


# ── rate_limited ─────────────────────────────────────────────────────────────

def test_rate_limited_fires_on_two_429_tool_results():
    evs = _newest_first(
        _ev("tool_call", {"tool": "web_fetch", "args": {"u": 1}}, 1),
        _ev("tool_result", {"is_error": True, "tool": "web_fetch",
                            "output": "HTTP 429 Too Many Requests"}, 2),
        _ev("tool_call", {"tool": "web_fetch", "args": {"u": 2}}, 3),
        _ev("tool_result", {"is_error": True, "tool": "web_fetch",
                            "output": "rate limit exceeded, retry later"}, 4),
    )
    inc = detectors.rate_limited(evs, "codex:s1", "codex")
    assert inc and inc["kind"] == "rate_limited"
    assert inc["severity"] == "warning"
    assert inc["evidence"]["refusals"] == 2
    assert inc["evidence"]["threshold_source"] == "static"
    assert "observed" in inc["evidence"]
    assert inc["first_bad_step"] == 1  # chronological index of the first 429


def test_rate_limited_reads_api_error_events_not_just_tool_results():
    """A model refusal is an error event, not a tool result."""
    evs = _newest_first(
        _ev("tool_call", {"tool": "Bash", "args": {}}, 1),
        _ev("api.error", {"error": {"type": "overloaded_error",
                                    "message": "Overloaded"}}, 2),
        _ev("error", {"status": 429, "message": "Too Many Requests"}, 3),
    )
    inc = detectors.rate_limited(evs, "claude_code:s2", "claude_code")
    assert inc and inc["evidence"]["refusals"] == 2


def test_rate_limited_ignores_a_single_refusal_and_incidental_429_text():
    evs = _newest_first(
        _ev("tool_call", {"tool": "Read", "args": {"f": "a"}}, 1),
        _ev("tool_result", {"is_error": False, "output": "file size 1429 bytes"}, 2),
        _ev("tool_call", {"tool": "web_fetch", "args": {}}, 3),
        _ev("tool_result", {"is_error": True, "output": "429 too many requests"}, 4),
    )
    assert detectors.rate_limited(evs, "codex:s3", "codex") is None


def test_rate_limited_threshold_is_env_overridable_per_runtime(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_RATE_LIMIT_MIN__CODEX", "1")
    evs = _newest_first(
        _ev("tool_call", {"tool": "web_fetch", "args": {}}, 1),
        _ev("tool_result", {"is_error": True, "output": "overloaded"}, 2),
    )
    inc = detectors.rate_limited(evs, "codex:s4", "codex")
    assert inc and inc["evidence"]["threshold"] == 1
    assert inc["evidence"]["threshold_source"] == "env_runtime"


# ── blocked_on_user ──────────────────────────────────────────────────────────

def test_blocked_on_user_fires_on_pending_approval_fact():
    evs = _newest_first(_ev("tool_call", {"tool": "Bash", "args": {}}, 1))
    inc = detectors.blocked_on_user(evs, "openclaw-1", "openclaw",
                                    facts={"pending_approvals": 2})
    assert inc and inc["kind"] == "blocked_on_user"
    assert inc["severity"] == "warning"
    assert inc["evidence"]["pending_approvals"] == 2
    assert "approvals table" in inc["evidence"]["observed"]


def test_blocked_on_user_fires_on_unanswered_question_after_idle():
    evs = _newest_first(
        _ev("tool_call", {"tool": "Bash", "args": {}}, 1),
        _ev("tool_call", {"tool": "AskUserQuestion",
                          "args": {"question": "Which branch?"}}, 2),
    )
    inc = detectors.blocked_on_user(evs, "claude_code:s5", "claude_code",
                                    facts={"idle_seconds": 600})
    assert inc and inc["evidence"]["asked_via"] == "AskUserQuestion"
    assert inc["evidence"]["threshold_source"] == "static"
    assert inc["first_bad_step"] == 1


def test_blocked_on_user_stays_quiet_when_the_question_was_answered():
    evs = _newest_first(
        _ev("tool_call", {"tool": "AskUserQuestion", "args": {"q": 1}}, 1),
        _ev("user", {"role": "user", "content": "main"}, 2),
        _ev("tool_call", {"tool": "Bash", "args": {}}, 3),
    )
    assert detectors.blocked_on_user(evs, "claude_code:s6", "claude_code",
                                     facts={"idle_seconds": 6000}) is None


def test_blocked_on_user_stays_quiet_on_a_fresh_prompt():
    """Two minutes of silence after a question is a conversation."""
    evs = _newest_first(
        _ev("tool_call", {"tool": "AskUserQuestion", "args": {"q": 1}}, 1),
    )
    assert detectors.blocked_on_user(evs, "claude_code:s7", "claude_code",
                                     facts={"idle_seconds": 30}) is None
    # No idle measurement at all: never guess.
    assert detectors.blocked_on_user(evs, "claude_code:s7", "claude_code") is None


def test_blocked_on_user_generalises_beyond_claude_code_event_names():
    evs = _newest_first(
        _ev("tool_call", {"tool": "shell", "args": {}}, 1),
        _ev("approval.requested", {"action": "rm -rf build"}, 2),
    )
    inc = detectors.blocked_on_user(evs, "codex:s8", "codex",
                                    facts={"idle_seconds": 900})
    assert inc and inc["evidence"]["asked_via"] == "approval.requested"


# ── crashed ──────────────────────────────────────────────────────────────────

def test_crashed_fires_on_two_starts_inside_the_window():
    evs = _newest_first(
        _ev("session.started", {}, 0),
        _ev("tool_call", {"tool": "Bash", "args": {}}, 30),
        _ev("session.started", {}, 400),
    )
    inc = detectors.crashed(evs, "claude_code:s9", "claude_code")
    assert inc and inc["kind"] == "crashed"
    assert inc["evidence"]["restarts"] == 2
    assert inc["evidence"]["threshold"] == 2  # matches the crash-loop impact tag
    assert inc["evidence"]["span_sec"] == 400
    assert inc["first_bad_step"] == 0


def test_crashed_ignores_restarts_far_apart():
    evs = _newest_first(
        _ev("session.started", {}, 0),
        _ev("tool_call", {"tool": "Bash", "args": {}}, 30),
        _ev("session.restarted", {}, 3000),  # 50 min later: a new day, not a loop
    )
    assert detectors.crashed(evs, "claude_code:s10", "claude_code") is None


def test_crashed_single_start_is_normal():
    evs = _newest_first(
        _ev("session.started", {}, 0),
        _ev("tool_call", {"tool": "Bash", "args": {}}, 1),
        _ev("tool_result", {"is_error": False, "output": "ok"}, 2),
    )
    assert detectors.crashed(evs, "codex:s11", "codex") is None


def test_crashed_without_timestamps_counts_the_window_and_says_so():
    evs = [{"event_type": "session.started", "data": {}},
           {"event_type": "session.started", "data": {}}]
    inc = detectors.crashed(evs, "codex:s12", "codex")
    assert inc and "event_window" in inc["evidence"]["observed"]


# ── contract via run_all ─────────────────────────────────────────────────────

def test_run_all_registers_the_three_and_annotates_spend():
    for k in ("rate_limited", "blocked_on_user", "crashed"):
        assert k in detectors.DETECTOR_KINDS
        assert getattr(detectors, k) in detectors._ALL_DETECTORS
    evs = _newest_first(
        _ev("session.started", {}, 0),
        _ev("tool_call", {"tool": "web", "args": {}}, 10),
        _ev("tool_result", {"is_error": True, "output": "429"}, 11),
        _ev("tool_result", {"is_error": True, "output": "rate limit"}, 12),
        _ev("session.started", {}, 200),
    )
    out = detectors.run_all(evs, "codex:s13", "codex",
                            facts={"cost_usd": 3.0, "bad_for_seconds": 120,
                                   "session_seconds": 600,
                                   "pending_approvals": 1})
    kinds = set(_kinds(out))
    assert {"rate_limited", "crashed", "blocked_on_user"} <= kinds
    for inc in out:
        assert inc["spend_basis"] in ("burn_rate", "window_fraction", "unknown")
        assert "spend_at_risk_usd" in inc
        assert inc["severity"] in ("info", "warning", "critical")


def test_healthy_session_triggers_none_of_the_three():
    evs = _newest_first(
        _ev("session.started", {}, 0),
        _ev("user", {"role": "user", "content": "fix the bug"}, 1),
        _ev("tool_call", {"tool": "Read", "args": {"f": "a.py"}}, 2),
        _ev("tool_result", {"is_error": False, "output": "def f(): ..."}, 3),
        _ev("tool_call", {"tool": "Edit", "args": {"f": "a.py"}}, 4),
        _ev("tool_result", {"is_error": False, "output": "ok"}, 5),
        _ev("assistant", {"role": "assistant", "content": "Done."}, 6),
    )
    out = detectors.run_all(evs, "claude_code:s14", "claude_code",
                            facts={"idle_seconds": 10_000})
    assert not ({"rate_limited", "blocked_on_user", "crashed"} & set(_kinds(out)))
