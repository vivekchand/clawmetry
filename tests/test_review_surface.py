"""The review queue gets a surface, and can say why it is empty.

Since issue #1615 the sync daemon has picked a few sessions at random every
night, written them to a review queue, and tracked how often the operator
agreed with the agent. On a real install 2026-08-25 that queue held rows and
the accuracy was zero for every agent, because the endpoints shipped without
any screen: ``routes/review.py`` even documents a "Sample now button on an
empty Review tab" that never existed. Nobody could answer, so nothing was
ever answered.

These tests pin the two halves of making that reachable:

1. ``store_available`` on the queue and accuracy payloads. Without it an
   unreadable store (the hosted dashboard has no local DuckDB; the daemon
   proxy can also be briefly down) is indistinguishable from an empty queue,
   and the surface tells a cloud user "nothing waiting" when the truth is
   "cannot see". FLYWHEEL §0a.1 forbids exactly that.
2. The Spot-check panel exists in the LIVE template (§0a.4: dashboard.py
   defines DASHBOARD_HTML twice and only the second one renders).
"""
from __future__ import annotations

import pytest
from flask import Flask


def _app():
    from routes.review import bp_review

    app = Flask(__name__)
    app.register_blueprint(bp_review)
    return app


@pytest.fixture
def store(monkeypatch):
    """Swap the DuckDB hop. ``None`` means the store could not be read."""
    holder = {"queue": [], "accuracy": {}, "sessions": []}

    def _fake(method_name, **kwargs):
        if method_name == "query_review_queue":
            return holder["queue"]
        if method_name == "query_review_accuracy":
            return holder["accuracy"]
        if method_name == "query_sessions_table":
            return holder["sessions"]
        return None

    monkeypatch.setattr("routes.review._store_call", _fake)
    return holder


# ── empty vs unreadable ─────────────────────────────────────────────────────


def test_empty_queue_is_available(store):
    store["queue"] = []
    with _app().test_client() as c:
        body = c.get("/api/review/queue").get_json()
    assert body["count"] == 0
    assert body["store_available"] is True


def test_unreadable_store_is_not_an_empty_queue(store):
    """The distinction the whole surface depends on. Both answer 200 with
    zero rows; only ``store_available`` separates "nothing waiting" from
    "cannot see from here"."""
    store["queue"] = None
    with _app().test_client() as c:
        r = c.get("/api/review/queue")
        assert r.status_code == 200
        body = r.get_json()
    assert body["count"] == 0
    assert body["store_available"] is False


def test_accuracy_reports_an_unreadable_store_too(store):
    """A clean record and an unreadable one both look like zero decisions."""
    store["accuracy"] = None
    with _app().test_client() as c:
        body = c.get("/api/review/accuracy?window=30").get_json()
    assert body["store_available"] is False
    assert body["global"]["accuracy"] is None


def test_accuracy_available_when_the_store_answers(store):
    store["accuracy"] = {
        "window_days": 30,
        "global": {"correct": 9, "wrong": 2, "borderline": 1, "accuracy": 0.75},
        "per_agent": [],
    }
    with _app().test_client() as c:
        body = c.get("/api/review/accuracy").get_json()
    assert body["store_available"] is True
    assert body["global"]["correct"] == 9


def test_rows_are_decorated_with_the_session_summary(store):
    """One self-contained card per row, so the panel needs no second fetch."""
    store["queue"] = [{"session_id": "claude_code:s1", "status": "pending"}]
    store["sessions"] = [{"session_id": "claude_code:s1", "title": "Fix the build",
                          "cost_usd": 0.42, "total_tokens": 900,
                          "message_count": 12, "started_at": "2026-08-24T10:00:00Z"}]
    with _app().test_client() as c:
        body = c.get("/api/review/queue").get_json()
    summary = body["rows"][0]["session_summary"]
    assert summary["title"] == "Fix the build"
    assert summary["cost_usd"] == 0.42


# ── recording a verdict ─────────────────────────────────────────────────────


def test_a_verdict_is_recorded(store, monkeypatch):
    seen = {}

    def _fake(method_name, **kwargs):
        if method_name == "update_review_decision":
            seen.update(kwargs)
            return True
        return []

    monkeypatch.setattr("routes.review._store_call", _fake)
    with _app().test_client() as c:
        r = c.post("/api/review/claude_code:s1",
                   json={"status": "reviewed_correct"})
    assert r.status_code == 200
    assert seen["session_id"] == "claude_code:s1"
    assert seen["status"] == "reviewed_correct"


def test_an_unknown_verdict_is_rejected(store):
    """The three buttons are the whole vocabulary; anything else is a bug in
    the caller, not a new outcome to record."""
    with _app().test_client() as c:
        r = c.post("/api/review/s1", json={"status": "lgtm"})
    assert r.status_code == 400
    assert "reviewed_correct" in r.get_json()["allowed"]


# ── the live template ───────────────────────────────────────────────────────


def _render_evals_tab():
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader("clawmetry/templates"))
    return env.get_template("tabs/evals.html").render()


def test_spot_check_panel_is_in_the_rendered_tab():
    html = _render_evals_tab()
    for marker in ('id="q-spot"', 'id="q-spot-list"', 'id="q-spot-score"'):
        assert marker in html, f"{marker} missing from the live Quality tab"


def test_spot_check_starts_hidden():
    """It reveals itself only once the store answers, so a hosted user does
    not get told their queue is empty when we simply cannot read it."""
    html = _render_evals_tab()
    section = html[html.index('id="q-spot"'):]
    assert "hidden" in section[: section.index(">")]


def test_the_loader_branches_on_store_available():
    """Guards the regression this whole field exists to prevent."""
    src = open("clawmetry/static/js/app.js", encoding="utf-8").read()
    assert "_qLoadSpotCheck" in src
    assert "store_available === false" in src
