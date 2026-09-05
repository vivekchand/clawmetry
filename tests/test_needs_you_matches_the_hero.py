"""The needs-you strip and the Overview hero must give ONE answer.

Founder report 2026-09-05, one screenshot, two adjacent rows:

    Nothing needs you right now      No agents running
    3 sessions are working right now.
      - Father of India        Claude Code   just now
      - Clawmetry docs         Claude Code   19s ago
      - Session not in guard   Claude Code   1m ago

Both render on Overview, both answer "how many of my agents are running", and
they disagreed for two independent reasons:

  1. ``build_attention`` filtered rows on ``sessions.agent_type``, which the
     family ingest stamps ``openclaw`` for every runtime it writes. Under the
     Claude Code filter in the screenshot NOTHING matched, so ``working``
     was 0 -- and, far worse than a wrong count, a genuinely blocked Claude
     Code session would have been dropped from ``items`` too. The strip whose
     entire job is "tell me when an agent needs me" was silent for 25 of the
     26 runtimes whenever a runtime was selected.

  2. The two components defined "working" differently (15 minutes here, 2
     minutes there), so even node-wide they could print different numbers
     from the same rows.

These tests pin both halves against ``/api/live-sessions``, which is the
component that renders the sessions BY NAME and therefore the one that cannot
be wrong without it being obvious.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask

from clawmetry.entitlements import ALL_RUNTIMES

RUNTIMES = sorted(ALL_RUNTIMES)


def _iso(delta_secs: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=delta_secs)).isoformat()


def _family_row(runtime: str, name: str, age: float, status: str = "active") -> dict:
    """A row shaped the way the family ingest actually writes one.

    ``agent_type`` is "openclaw" for every runtime -- that is not a mistake in
    the fixture, it is the production shape this test exists to survive.
    """
    return {
        "session_id": "%s:%s" % (runtime, name),
        "agent_type": "openclaw",
        "title": "%s %s" % (runtime, name),
        "status": status,
        "last_active_at": _iso(age),
        "metadata": {"runtime": runtime},
        "attention_state": "",
    }


def _rows_for_every_runtime() -> list:
    """Per runtime: two working, one quiet, one long dead."""
    rows = []
    for rt in RUNTIMES:
        rows.append(_family_row(rt, "live-a", 5))
        rows.append(_family_row(rt, "live-b", 30))
        rows.append(_family_row(rt, "parked", 300, status="idle"))
        rows.append(_family_row(rt, "dead", 90000, status="ended"))
    return rows


@pytest.fixture
def wired(monkeypatch):
    """Both endpoints reading the SAME rows, so any difference is theirs."""
    rows = _rows_for_every_runtime()

    import routes.sessions as sessions_mod
    import routes.attention as attention_mod

    monkeypatch.setattr(sessions_mod, "_fetch_sessions_table_rows",
                        lambda limit=200: list(rows))
    monkeypatch.setattr(attention_mod, "_sessions", lambda: list(rows))
    monkeypatch.setattr(attention_mod, "_daemon_is_live", lambda: True)
    monkeypatch.setattr(attention_mod, "_daemon_age_seconds", lambda: 3)

    app = Flask(__name__)
    app.register_blueprint(sessions_mod.bp_sessions)
    return app.test_client()


def _live_counts(client, runtime: str = "") -> dict:
    q = ("?runtime=" + runtime) if runtime else ""
    return client.get("/api/live-sessions" + q).get_json()["counts"]


# ── 1. the count the two components print ───────────────────────────────────

@pytest.mark.parametrize("runtime", RUNTIMES)
def test_working_count_agrees_with_the_hero_per_runtime(wired, runtime):
    from routes.attention import build_attention

    hero = _live_counts(wired, runtime)
    strip = build_attention(runtime)
    assert strip["working"] == hero["working"], (
        "%s: the strip says %d working, the hero names %d. Same rows, same "
        "screen, two answers." % (runtime, strip["working"], hero["working"]))
    assert strip["quiet"] == hero["waiting"], (
        "%s: the strip's quiet bucket (%d) and the hero's (%d) disagree"
        % (runtime, strip["quiet"], hero["waiting"]))


def test_working_count_agrees_with_the_hero_node_wide(wired):
    from routes.attention import build_attention

    hero = _live_counts(wired)
    strip = build_attention("")
    assert strip["working"] == hero["working"]
    assert strip["quiet"] == hero["waiting"]


@pytest.mark.parametrize("runtime", RUNTIMES)
def test_a_runtime_with_live_sessions_is_never_reported_as_none(wired, runtime):
    """The literal screenshot: "No agents running" is what the strip renders
    when ``working`` and ``quiet`` are both zero."""
    from routes.attention import build_attention

    d = build_attention(runtime)
    assert d["working"] or d["quiet"], (
        "%s has live sessions but the strip would render 'No agents running'"
        % runtime)


# ── 2. the rows the strip is FOR ────────────────────────────────────────────

@pytest.mark.parametrize("runtime", RUNTIMES)
def test_a_blocked_session_survives_its_own_runtime_filter(monkeypatch, runtime):
    """The real cost of filtering on ``agent_type``: not a wrong number, a
    dropped row. A session asking for permission must reach the strip under
    the filter the user is actually looking at."""
    import routes.attention as attention_mod

    row = _family_row(runtime, "blocked", 20)
    row["attention_state"] = "waiting_approval"
    row["attention_signal"] = "hook"
    row["attention_tool"] = "Bash"
    monkeypatch.setattr(attention_mod, "_sessions", lambda: [row])
    monkeypatch.setattr(attention_mod, "_daemon_is_live", lambda: True)
    monkeypatch.setattr(attention_mod, "_daemon_age_seconds", lambda: 3)

    d = attention_mod.build_attention(runtime)
    assert len(d["items"]) == 1, (
        "%s: a hook-confirmed prompt vanished under its own runtime filter"
        % runtime)
    assert d["items"][0]["runtime"] == runtime, (
        "the row reached the strip labelled %r, so it renders under the wrong "
        "runtime name" % d["items"][0]["runtime"])


def test_runtimes_without_approval_is_reported_by_real_runtime(monkeypatch):
    """The "Pi never asks for permission" branch reads the same field. With
    ``agent_type`` it could only ever see "openclaw", so the branch was
    unreachable for the one runtime it was written for."""
    import routes.attention as attention_mod

    monkeypatch.setattr(attention_mod, "_sessions",
                        lambda: [_family_row("pi", "live", 10)])
    monkeypatch.setattr(attention_mod, "_daemon_is_live", lambda: True)
    monkeypatch.setattr(attention_mod, "_daemon_age_seconds", lambda: 3)
    assert attention_mod.build_attention("pi")["runtimes_without_approval"] == ["pi"]


# ── 3. the helper both sides now share ──────────────────────────────────────

def test_session_runtime_prefers_metadata_over_agent_type():
    from routes.sessions import session_runtime

    assert session_runtime(_family_row("codex", "x", 1)) == "codex"


def test_session_runtime_falls_back_to_the_id_namespace():
    """A metadata blob that failed to decode must not silently relabel every
    family session as OpenClaw."""
    from routes.sessions import session_runtime

    assert session_runtime({"session_id": "cursor:abc", "agent_type": "openclaw",
                            "metadata": None}) == "cursor"


def test_session_runtime_keeps_openclaw_rows_openclaw():
    from routes.sessions import session_runtime

    assert session_runtime({"session_id": "abc", "agent_type": "openclaw",
                            "metadata": {}}) == "openclaw"


def test_session_runtime_ignores_a_colon_that_is_not_a_runtime():
    """An id containing a colon is not a namespace unless the head names a
    runtime we actually ship."""
    from routes.sessions import session_runtime

    assert session_runtime({"session_id": "urn:uuid:1234", "agent_type": "hermes",
                            "metadata": {}}) == "hermes"


def test_counts_exclude_subagents_and_clawmetrys_own_sessions(monkeypatch):
    """Both components exclude these; a count that included them could not
    match the list printed beside it."""
    import routes.attention as attention_mod

    child = _family_row("claude_code", "subagent-1", 5)
    monkeypatch.setattr(attention_mod, "_sessions", lambda: [child])
    monkeypatch.setattr(attention_mod, "_daemon_is_live", lambda: True)
    monkeypatch.setattr(attention_mod, "_daemon_age_seconds", lambda: 3)
    # Node-wide, so the runtime filter is not what does the excluding.
    assert attention_mod.build_attention("")["working"] == 0
    assert attention_mod.build_attention("claude_code")["working"] == 0
