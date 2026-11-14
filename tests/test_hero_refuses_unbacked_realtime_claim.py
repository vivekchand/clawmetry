"""The hero must not say "right now" from evidence that cannot support it.

Founder instruction, 2026-10-07:

    "Let's better not show that It's xyz right now if we cannot be realtime &
    accurate - this can lead to loss of customer trust"

What prompted it, measured on the node:

    process_control.live_sessions()  ->  7 live Claude Code processes
    newest last_active_at in store   ->  22,100s  (6.1 hours)

Liveness was inferred purely from how recently a transcript was WRITTEN. That
is a proxy for "is it working", and it fails in both directions that matter:
an agent mid-tool-call writes nothing for the length of the call, and the
store only ever knows what the daemon has ingested. With every row past the
600s window, all seven classified ``ended``, were hidden, and the hero said
**"It's idle right now."** over a working machine.

The daemon reported itself healthy throughout (``daemon_age_seconds: 51``,
``fresh: true``). "The daemon is alive" was being used to justify asserting
"the data is current", and those are different claims.

So the route now asks the OS, which is pid-backed and costs ~3ms cold. When
the process table shows agents the store has not caught up with, the answer
is "we cannot tell", never "idle".
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_JS = os.path.join(REPO, "clawmetry", "static", "js", "app.js")


def _iso(delta_secs: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=delta_secs)).isoformat()


def _client():
    import routes.sessions as sessions_mod
    app = Flask(__name__)
    app.register_blueprint(sessions_mod.bp_sessions)
    return app.test_client()


@pytest.fixture()
def rows(monkeypatch):
    """One Claude Code session, quiet for seven hours: the reported shape."""
    import routes.sessions as sessions_mod
    data = [{"session_id": "claude_code:aaa", "title": "Long build",
             "last_active_at": _iso(25200), "status": "active",
             "cost_usd": 1.0, "message_count": 40,
             "metadata": {"runtime": "claude_code"}}]
    monkeypatch.setattr(sessions_mod, "_fetch_sessions_table_rows",
                        lambda limit=200: data)
    return data


def _procs(monkeypatch, items):
    from clawmetry import process_control as pc
    monkeypatch.setattr(pc, "live_sessions", lambda: items)


# ---------------------------------------------------------------------------
# The refusal
# ---------------------------------------------------------------------------

def test_a_live_process_the_store_missed_blocks_the_idle_claim(rows, monkeypatch):
    """The exact founder state: nothing live in the store, agents on the box."""
    _procs(monkeypatch, [{"pid": 1, "runtime": "claude_code", "session_id": "aaa"},
                         {"pid": 2, "runtime": "claude_code", "session_id": "bbb"}])
    d = _client().get("/api/live-sessions").get_json()
    assert d["counts"]["working"] == 0
    assert d["available"] is False, "available:true is the hero's licence to say idle"
    assert d["realtime"] is False
    assert d["reason"] == "evidence_behind_processes"
    assert d["processes_live"] == 2


def test_an_idle_machine_still_gets_a_straight_answer(rows, monkeypatch):
    """No agent processes: "idle" is backed, so do not go vague."""
    _procs(monkeypatch, [])
    d = _client().get("/api/live-sessions").get_json()
    assert d["available"] is True and d["realtime"] is True
    assert d["processes_live"] == 0
    assert "reason" not in d


def test_agreement_is_not_disturbed(monkeypatch):
    """Store and OS agree that something is working: answer normally."""
    import routes.sessions as sessions_mod
    monkeypatch.setattr(sessions_mod, "_fetch_sessions_table_rows",
                        lambda limit=200: [
                            {"session_id": "claude_code:aaa", "title": "Working",
                             "last_active_at": _iso(5), "status": "active",
                             "metadata": {"runtime": "claude_code"}}])
    _procs(monkeypatch, [{"pid": 1, "runtime": "claude_code", "session_id": "aaa"}])
    d = _client().get("/api/live-sessions").get_json()
    assert d["counts"]["working"] == 1
    assert d["available"] is True and d["realtime"] is True


def test_the_cross_check_scopes_to_the_runtime(rows, monkeypatch):
    """Codex processes say nothing about a Claude Code question."""
    _procs(monkeypatch, [{"pid": 1, "runtime": "codex", "session_id": "zzz"}])
    cc = _client().get("/api/live-sessions?runtime=claude_code").get_json()
    assert cc["processes_live"] == 0
    assert cc["available"] is True, "another runtime's process must not block this one"
    cx = _client().get("/api/live-sessions?runtime=codex").get_json()
    assert cx["processes_live"] == 1
    assert cx["available"] is False, "codex has a live process and nothing live in the store"


def test_an_unreadable_process_table_is_unknown_not_zero(rows, monkeypatch):
    """Never manufacture a refusal, and never manufacture confidence."""
    from clawmetry import process_control as pc

    def boom():
        raise OSError("cannot read the process table")
    monkeypatch.setattr(pc, "live_sessions", boom)
    d = _client().get("/api/live-sessions").get_json()
    assert d["processes_live"] is None
    assert d["available"] is True, "an unreadable table must not block the answer"


def test_the_evidence_age_is_reported(monkeypatch):
    import routes.sessions as sessions_mod
    monkeypatch.setattr(sessions_mod, "_fetch_sessions_table_rows",
                        lambda limit=200: [
                            {"session_id": "claude_code:aaa", "title": "Quiet",
                             "last_active_at": _iso(300), "status": "active",
                             "metadata": {"runtime": "claude_code"}}])
    _procs(monkeypatch, [])
    d = _client().get("/api/live-sessions").get_json()
    assert 290 <= d["evidence_age_seconds"] <= 310


# ---------------------------------------------------------------------------
# The hero must honour the refusal, including via its fallback
# ---------------------------------------------------------------------------

def test_the_hero_does_not_assert_working_from_the_recency_fallback():
    """`!_liveKnown && busy` would otherwise re-assert "working" from the very
    runtime-recency data the endpoint just disowned."""
    js = open(APP_JS, encoding="utf-8").read()
    assert "_evidenceBehind" in js
    i_stale = js.index("} else if (_evidenceBehind) {")
    i_busy = js.index("} else if (!_liveKnown && busy) {")
    assert i_stale < i_busy, (
        "the stale branch must be tested BEFORE the recency fallback, or the "
        "hero reasserts 'working' on evidence it has refused")


def test_the_hero_says_what_the_os_can_prove():
    js = open(APP_JS, encoding="utf-8").read()
    assert "agents are open on this machine" in js
    assert "cannot say whether they are working right now" in js


def test_the_loader_forwards_the_refusal():
    js = open(APP_JS, encoding="utf-8").read()
    for marker in ("processes_live", "evidence_age_seconds", "staleReason"):
        assert marker in js, "the loader drops %s, so the hero never sees it" % marker
