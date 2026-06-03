"""Regression test for the configurable family-runtime session-ingest cap.

Family runtimes (Claude Code / Codex / Cursor / …) ingest the N most-recent
sessions per runtime. The default is 50 to bound storage + initial-sync payload
on machines with thousands of historical sessions; CLAWMETRY_FAMILY_SESSION_LIMIT
lets power users raise it. The parse must floor at 1 and never crash on a bad
value (the daemon must not die on a typo'd env var).
"""

import importlib

import clawmetry.sync as sync


def _limit(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("CLAWMETRY_FAMILY_SESSION_LIMIT", raising=False)
    else:
        monkeypatch.setenv("CLAWMETRY_FAMILY_SESSION_LIMIT", value)
    return sync._family_session_limit()


def test_default_is_50(monkeypatch):
    assert _limit(monkeypatch, None) == 50


def test_env_override(monkeypatch):
    assert _limit(monkeypatch, "300") == 300


def test_floored_at_one(monkeypatch):
    # 0 / negative would ingest nothing or break the adapter — floor at 1.
    assert _limit(monkeypatch, "0") == 1
    assert _limit(monkeypatch, "-5") == 1


def test_bad_value_falls_back_to_default(monkeypatch):
    assert _limit(monkeypatch, "abc") == 50
    assert _limit(monkeypatch, "") == 50


# ── on-demand backfill (founder: default 50, dig deeper on demand) ─────────────

def _reset_overrides():
    sync._RUNTIME_BACKFILL_OVERRIDES.clear()


def test_effective_limit_default_is_family_limit(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_FAMILY_SESSION_LIMIT", raising=False)
    _reset_overrides()
    assert sync._effective_family_limit("claude_code") == 50


def test_backfill_raises_one_runtime_only(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_FAMILY_SESSION_LIMIT", raising=False)
    _reset_overrides()
    sync._action_runtime_backfill({}, {"type": "runtime_backfill", "runtime": "claude_code", "limit": 500})
    assert sync._effective_family_limit("claude_code") == 500
    # other runtimes untouched
    assert sync._effective_family_limit("goose") == 50


def test_backfill_is_monotonic(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_FAMILY_SESSION_LIMIT", raising=False)
    _reset_overrides()
    sync._action_runtime_backfill({}, {"runtime": "claude_code", "limit": 500})
    sync._action_runtime_backfill({}, {"runtime": "claude_code", "limit": 200})  # lower — ignored
    assert sync._effective_family_limit("claude_code") == 500


def test_backfill_no_limit_steps_up_a_page(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_FAMILY_SESSION_LIMIT", raising=False)
    _reset_overrides()
    sync._action_runtime_backfill({}, {"runtime": "claude_code"})  # no limit -> +page
    assert sync._effective_family_limit("claude_code") == 100  # 50 + 50


def test_backfill_capped_and_never_below_default(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_FAMILY_SESSION_LIMIT", raising=False)
    _reset_overrides()
    sync._action_runtime_backfill({}, {"runtime": "claude_code", "limit": 10 ** 9})
    assert sync._effective_family_limit("claude_code") == sync._RUNTIME_BACKFILL_MAX
    # a raised default still wins if larger than a small override
    _reset_overrides()
    monkeypatch.setenv("CLAWMETRY_FAMILY_SESSION_LIMIT", "300")
    assert sync._effective_family_limit("codex") == 300


def test_backfill_in_pending_action_allowlist():
    assert "runtime_backfill" in sync._PENDING_ACTIONS


def test_backfill_bad_input_never_raises(monkeypatch):
    _reset_overrides()
    sync._action_runtime_backfill({}, {})  # no runtime
    sync._action_runtime_backfill({}, {"runtime": "x", "limit": "abc"})  # bad limit
    # no exception == pass
