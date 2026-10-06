"""The hosted dashboard must never state a negative it cannot know.

Founder report 2026-10-06: app.clawmetry.com said **"It's idle right now."**
on the Overview hero while localhost:8900, reading the very same node, said
"It's working right now." over two Claude Code sessions mid-task. The
needs-you strip directly above it said "No agents running".

Mechanism — an empty success outranking a real signal:

  * ``/api/live-sessions`` is an OSS passthrough. The hosted container ships
    the same route module as a laptop, and
    ``local_store.get_store(read_only=True)`` SUCCEEDS there against a DuckDB
    no daemon ever wrote to. So ``_fetch_sessions_table_rows`` returned
    ``[]`` — not ``None`` — and the route answered
    ``{"available": true, "counts": {"working": 0}}``.
  * ``available: true`` is the hero's licence to state the negative as fact
    (``app.js``: ``if (_liveKnown) busy = _working > 0;``). The confident
    zero therefore also OVERRODE the hero's own fallback, which reads
    runtime recency from the snapshot and would have been right on its own.

This is the third time this exact shape has shipped (hosted Guard tab and
the Signals drill-down, both 2026-09-14). These tests pin the rule rather
than the symptom: **in cloud, a store-backed reader answers "unknown",
never "zero".**
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _iso(delta_secs: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=delta_secs)).isoformat()


@pytest.fixture
def cloud_env(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_CLOUD", "1")


@pytest.fixture
def node_env(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_CLOUD", raising=False)
    monkeypatch.delenv("CLOUD_MODE", raising=False)


# ---------------------------------------------------------------------------
# 1. The shared verdict
# ---------------------------------------------------------------------------

def test_store_is_not_authoritative_in_cloud(cloud_env):
    from helpers.node_store import running_in_cloud, store_is_authoritative
    assert running_in_cloud() is True
    assert store_is_authoritative() is False


def test_store_is_authoritative_on_a_node(node_env):
    from helpers.node_store import store_is_authoritative
    assert store_is_authoritative() is True


@pytest.mark.parametrize("value", ["1", "true", "YES", "on"])
def test_cloud_mode_spellings_all_count(monkeypatch, value):
    """Four modules probed this by hand with four different spellings; the
    hosted image sets CLAWMETRY_CLOUD=1 (Dockerfile) and CLOUD_MODE
    (config.py). Missing one is how a reader keeps its false authority."""
    from helpers.node_store import running_in_cloud
    monkeypatch.delenv("CLAWMETRY_CLOUD", raising=False)
    monkeypatch.setenv("CLOUD_MODE", value)
    assert running_in_cloud() is True


# ---------------------------------------------------------------------------
# 2. The reader cannot be tricked by a container's empty DuckDB
# ---------------------------------------------------------------------------

def test_fetch_sessions_defers_in_cloud_instead_of_returning_empty(cloud_env, monkeypatch):
    """The regression itself: the direct ``get_store`` fallback SUCCEEDS in
    the container. Even so the helper must answer "unknown"."""
    import routes.sessions as sessions_mod

    class _FakeStore:
        def query_sessions_table(self, limit=200):
            return []          # an empty container DuckDB, exactly as in prod

    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda **kw: _FakeStore(), raising=False)
    monkeypatch.setattr("routes.local_query.local_store_via_daemon",
                        lambda *a, **kw: None, raising=False)

    assert sessions_mod._fetch_sessions_table_rows(limit=5) is None, (
        "an empty cloud store must read as 'unknown', never as 'no sessions'")


# ---------------------------------------------------------------------------
# 3. The endpoint the hero reads
# ---------------------------------------------------------------------------

def _client():
    import routes.sessions as sessions_mod
    app = Flask(__name__)
    app.register_blueprint(sessions_mod.bp_sessions)
    return app.test_client()


def test_live_sessions_never_reports_available_zero_in_cloud(cloud_env, monkeypatch):
    """The exact wire response behind "It's idle right now."."""
    import clawmetry.local_store as ls

    class _FakeStore:
        def query_sessions_table(self, limit=200):
            return []

    monkeypatch.setattr(ls, "get_store", lambda **kw: _FakeStore(), raising=False)
    monkeypatch.setattr("routes.local_query.local_store_via_daemon",
                        lambda *a, **kw: None, raising=False)

    for url in ("/api/live-sessions", "/api/live-sessions?runtime=claude_code"):
        d = _client().get(url).get_json()
        assert d["available"] is False, (
            "%s claimed authority it does not have; the hero reads "
            "available:true as permission to say 'It's idle right now.'" % url)
        assert d["counts"] == {"working": 0, "waiting": 0}
        assert d["sessions"] == []


def test_live_sessions_still_answers_on_a_real_node(node_env, monkeypatch):
    """The cloud guard must not cost a laptop its own hero."""
    import routes.sessions as sessions_mod

    rows = [{"session_id": "claude_code:aaa", "title": "Fix the login redirect",
             "last_active_at": _iso(8), "status": "active", "cost_usd": 1.25,
             "message_count": 40,
             "metadata": {"runtime": "claude_code", "recent_model": "claude-opus-5"}}]
    monkeypatch.setattr(sessions_mod, "_fetch_sessions_table_rows",
                        lambda limit=200: rows)
    d = _client().get("/api/live-sessions").get_json()
    assert d["available"] is True
    assert d["counts"]["working"] == 1


# ---------------------------------------------------------------------------
# 4. The hero's contract, pinned in the JS
# ---------------------------------------------------------------------------

def test_hero_treats_unavailable_as_unknown_not_idle():
    """``available:false`` must reach the "Nothing to report yet." branch and
    leave the recency fallback free to answer. If this ever collapses back
    into a single boolean, the cloud hero lies again."""
    js = open(os.path.join(REPO, "clawmetry", "static", "js", "app.js"),
              encoding="utf-8").read()
    assert "available: !(d && d.available === false)" in js, (
        "the live-sessions loader no longer tracks knownness separately")
    assert "_liveKnown = !!(_live && _live.available)" in js
    assert "if (_liveKnown) busy = _working > 0;" in js, (
        "the hero no longer gates its verdict on knownness")
    assert "'Nothing to report yet.'" in js, (
        "the unknown branch is gone; unknown would read as idle again")
