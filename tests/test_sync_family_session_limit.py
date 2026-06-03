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
