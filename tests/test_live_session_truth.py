"""Session liveness truthfulness (founder report 2026-08-15).

Every family runtime (Claude Code, Codex, Cursor, Antigravity, ...) used to be
ingested with ``status="ended"`` and a non-null ``ended_at`` hardcoded from its
very first turn. A node with six terminals mid-task therefore reported
``activeSessions: 0`` and the Overview hero read "It's idle right now."

These tests pin the whole chain:

  sync._session_liveness()            -> recency buckets, never a hardcode
  routes/sessions.py _live_state()    -> the same buckets, explicit end wins
  GET /api/live-sessions              -> named live sessions, runtime-scoped
  routes/overview.py activeSessions   -> counts the live vocabulary
  app.js                              -> 'running' is as live as 'active'

The JS hops are guarded mechanically so a frontend refactor cannot silently
drop them again.
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
    """ISO timestamp `delta_secs` in the past."""
    return (datetime.now(timezone.utc) - timedelta(seconds=delta_secs)).isoformat()


# ---------------------------------------------------------------------------
# 1. Ingest: liveness is derived, never hardcoded
# ---------------------------------------------------------------------------

def test_session_liveness_buckets():
    from clawmetry.sync import _session_liveness

    status, ended = _session_liveness(_iso(5))
    assert status == "active"
    assert ended is None, "a live session must carry NO end time"

    status, ended = _session_liveness(_iso(300))
    assert status == "idle"
    assert ended is None, "an idle-but-open session has not ended"

    last = _iso(4000)
    status, ended = _session_liveness(last)
    assert status == "ended"
    assert ended == last, "an ended session keeps its real end timestamp"


def test_session_liveness_never_resurrects_on_bad_input():
    """A missing or unparseable timestamp must fall back to 'ended'.

    Marking a dead session live is the worse failure: it is what puts a ghost
    row in front of the user and re-arms the stuck/loop detectors on it.
    """
    from clawmetry.sync import _session_liveness

    assert _session_liveness(None)[0] == "ended"
    assert _session_liveness("")[0] == "ended"
    assert _session_liveness("not-a-timestamp")[0] == "ended"


def test_session_liveness_tolerates_clock_skew():
    """A future timestamp is a skewed clock, not a live session — but it must
    not crash or be silently dropped either."""
    from clawmetry.sync import _session_liveness

    future = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
    status, ended = _session_liveness(future)
    assert status == "active"
    assert ended is None


def test_family_ingest_no_longer_hardcodes_ended():
    """Mechanical guard: the three family/vm ingest sites must not go back to
    stamping a literal status."""
    src = open(os.path.join(REPO, "clawmetry", "sync.py")).read()
    assert '"status": "ended"' not in src, (
        "a session ingest site is hardcoding status='ended' again — derive it "
        "from _session_liveness() instead"
    )
    assert "_session_liveness(" in src


def test_openclaw_end_reason_beats_recency():
    """OpenClaw emits a REAL end signal; it must win over the recency guess."""
    src = open(os.path.join(REPO, "clawmetry", "sync.py")).read()
    assert re.search(
        r"if end_reason:\s*\n\s*_oc_status, _oc_ended = \"completed\", updated_at",
        src,
    ), "OpenClaw's explicit end_reason is no longer honoured"


# ---------------------------------------------------------------------------
# 2. /api/live-sessions
# ---------------------------------------------------------------------------

def _rows():
    """Three sessions: one working, one waiting, one long dead."""
    return [
        {"session_id": "claude_code:aaa", "title": "Fix the login redirect",
         "last_active_at": _iso(8), "status": "active", "cost_usd": 1.25,
         "message_count": 40, "metadata": {"runtime": "claude_code",
                                           "recent_model": "claude-opus-5"}},
        {"session_id": "codex:bbb", "title": "Port the parser",
         "last_active_at": _iso(400), "status": "idle", "cost_usd": 0.5,
         "message_count": 12, "metadata": {"runtime": "codex"}},
        {"session_id": "claude_code:ccc", "title": "Ancient history",
         "last_active_at": _iso(90000), "status": "ended", "cost_usd": 9.0,
         "message_count": 3, "metadata": {"runtime": "claude_code"}},
    ]


@pytest.fixture
def client(monkeypatch):
    import routes.sessions as sessions_mod

    monkeypatch.setattr(sessions_mod, "_fetch_sessions_table_rows",
                        lambda limit=200: _rows())
    app = Flask(__name__)
    app.register_blueprint(sessions_mod.bp_sessions)
    return app.test_client()


def test_live_sessions_names_the_live_ones(client):
    d = client.get("/api/live-sessions").get_json()
    assert d["counts"] == {"working": 1, "waiting": 1}
    titles = [s["title"] for s in d["sessions"]]
    assert titles == ["Fix the login redirect", "Port the parser"], (
        "expected most-recently-active first, dead session excluded"
    )
    first = d["sessions"][0]
    assert first["state"] == "working"
    assert first["runtime"] == "claude_code"
    assert first["model"] == "claude-opus-5"
    assert first["age_seconds"] < 120


def test_live_sessions_scopes_to_runtime(client):
    """FLYWHEEL §1c: ?runtime= must actually filter, server-side."""
    d = client.get("/api/live-sessions?runtime=codex").get_json()
    assert [s["runtime"] for s in d["sessions"]] == ["codex"]
    assert d["counts"] == {"working": 0, "waiting": 1}

    d = client.get("/api/live-sessions?runtime=cursor").get_json()
    assert d["sessions"] == [], "an absent runtime returns nothing, not the node total"


def test_live_sessions_says_unknown_when_store_unreachable(monkeypatch):
    """The daemon being unreachable is 'we don't know', never 'nothing runs'."""
    import routes.sessions as sessions_mod

    monkeypatch.setattr(sessions_mod, "_fetch_sessions_table_rows",
                        lambda limit=200: None)
    app = Flask(__name__)
    app.register_blueprint(sessions_mod.bp_sessions)
    d = app.test_client().get("/api/live-sessions").get_json()
    assert d["available"] is False
    assert d["sessions"] == []


def test_live_sessions_hides_plumbing_and_subagents(monkeypatch):
    import routes.sessions as sessions_mod

    rows = _rows() + [
        {"session_id": "clawmetry-selfevolve-1", "title": "our own plumbing",
         "last_active_at": _iso(5), "status": "active", "metadata": {}},
        {"session_id": "claude_code:subagent:zzz", "title": "spawned child",
         "last_active_at": _iso(5), "status": "active", "metadata": {}},
    ]
    monkeypatch.setattr(sessions_mod, "_fetch_sessions_table_rows",
                        lambda limit=200: rows)
    app = Flask(__name__)
    app.register_blueprint(sessions_mod.bp_sessions)
    d = app.test_client().get("/api/live-sessions").get_json()
    ids = [s["session_id"] for s in d["sessions"]]
    assert "clawmetry-selfevolve-1" not in ids
    assert "claude_code:subagent:zzz" not in ids


def test_explicit_end_beats_recency():
    """A runtime that can assert 'this is over' must not be second-guessed by
    a fresh mtime."""
    from routes.sessions import _live_state

    assert _live_state(_iso(5), "completed")[0] == "ended"
    assert _live_state(_iso(5), "failed")[0] == "ended"
    assert _live_state(_iso(5), "active")[0] == "working"


# ---------------------------------------------------------------------------
# 3. The JS hops (mechanical guards)
# ---------------------------------------------------------------------------

def test_js_treats_running_as_live():
    js = open(APP_JS).read()
    assert "function _cmIsWorkingStatus" in js
    assert re.search(r"s === 'active' \|\| s === 'running'", js), (
        "the status helper stopped accepting 'running' — the API emits it"
    )
    assert "if (_cmIsWorkingStatus(a.status)) running.push(a);" in js, (
        "the hero busy gate went back to comparing the raw 'active' literal"
    )
    assert not re.search(r"status === 'active' \? 'running'", js), (
        "_ovRenderCard is labelling running sub-agents 'complete' again"
    )


def test_js_hero_reads_named_live_sessions():
    js = open(APP_JS).read()
    assert "/api/live-sessions" in js
    assert "_cmLiveRowsHtml" in js
    assert "cmOpenLiveSession" in js, "live rows must stay clickable"
    assert re.search(r"' sessions are working right now\.'", js), (
        "the hero lost the counted headline and is back to one boolean"
    )
    # Perf: the shared cache + in-flight dedup must survive refactors.
    assert "_cmLiveWait" in js and "_CM_LIVE_TTL_MS" in js


def test_js_names_the_waiting_group():
    """A dot colour alone does not teach a first-timer what amber means."""
    js = open(APP_JS).read()
    assert "cm-live-group" in js and "Waiting on you</div>" in js, (
        "the working/waiting boundary lost its written label"
    )
    css = open(os.path.join(REPO, "clawmetry", "static", "css",
                            "dashboard.css")).read()
    assert ".cm-live-group" in css


def test_js_live_rows_are_keyboard_reachable():
    js = open(APP_JS).read()
    assert re.search(r"<button type=\"button\" class=\"cm-live-row\"", js), (
        "live rows must be real buttons, not clickable divs"
    )
    css = open(os.path.join(REPO, "clawmetry", "static", "css",
                            "dashboard.css")).read()
    assert ".cm-live-row:focus-visible" in css, "focus ring lost"
    assert "prefers-reduced-motion" in css


# ---------------------------------------------------------------------------
# 4. activeSessions
# ---------------------------------------------------------------------------

def test_overview_active_count_matches_live_vocabulary():
    src = open(os.path.join(REPO, "routes", "overview.py")).read()
    assert re.search(
        r'active_count = sum\(\s*\n\s*1 for s in user_sessions', src
    ), "activeSessions no longer counts over user_sessions"
    assert '("active", "running")' in src, (
        "activeSessions is back to matching a single status literal — that is "
        "how it read 0 while six terminals were mid-task"
    )


# ---------------------------------------------------------------------------
# 5. The hero never claims "free" from a number it has not read
# ---------------------------------------------------------------------------

def test_hero_never_claims_free_from_a_placeholder():
    """The cost tile ships as a literal '$0.00' placeholder and only reaches
    its real value once loadMiniWidgets lands. Deriving "free on your plan"
    from that string announced free spend over a real $8.49 for the first
    ~15s of every page load (founder report 2026-08-15)."""
    js = open(APP_JS).read()
    assert "window._cmCostTodayRaw = Number(usage.todayCost || 0);" in js, (
        "the hero lost its record of the cost value actually rendered"
    )
    assert re.search(r"var free = _costKnown && \(", js), (
        "'free on your plan' is being derived from the string again, so a "
        "not-yet-loaded tile reads as genuinely free"
    )
    assert re.search(r"if \(_costKnown\) stats\.push\('💸", js), (
        "the cost chip renders before its value is known — an unlabelled "
        "$0.00 next to live sessions reads as a real reading"
    )
