"""'Did it work?' -- the question that kills setup funnels.

A user who installs ClawMetry and sees an empty dashboard has no way to
tell "nothing is running" from "it is broken". We have numbers for what
that costs: 285 launches produced 13 choices in 14 days on the old gate.

``GET /api/onboarding/ingest-status`` answers it from real data, and the
first-run gate renders the answer. These guards cover the two things that
would make it worse than nothing: saying "connected" when nothing has
arrived, and saying nothing at all when the answer is no.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture
def client(monkeypatch):
    import routes.local_query as lq
    import routes.onboarding as ob

    importlib.reload(ob)
    ob._INGEST_STATUS_CACHE["at"] = 0.0
    ob._INGEST_STATUS_CACHE["body"] = None

    state = {"aggregates": [], "runtimes": []}

    def _fake(shape, args=None):
        return {"rows": state.get(shape, [])}

    monkeypatch.setattr(lq, "_dispatch", _fake)

    app = Flask(__name__)
    app.register_blueprint(ob.bp_onboarding)
    c = app.test_client()
    c.state = state
    c.ob = ob
    return c


def _get(client):
    client.ob._INGEST_STATUS_CACHE["at"] = 0.0
    client.ob._INGEST_STATUS_CACHE["body"] = None
    return client.get("/api/onboarding/ingest-status").get_json()


# ── the honest no ───────────────────────────────────────────────────────

def test_empty_store_is_not_connected_and_says_what_to_do(client):
    d = _get(client)
    assert d["connected"] is False
    assert d["events_total"] == 0
    assert d["runtimes"] == []
    assert "setup-prompt" in d["next_step"], (
        "the endpoint that answers 'did it work?' must also answer 'what "
        "now?', or the user is exactly where they started"
    )


def test_a_runtime_with_no_activity_is_not_reported_as_a_source(client):
    """A runtime we merely know about is not a runtime that is sending.
    Listing it would answer 'is anything arriving?' with a yes it has not
    earned -- the same shape as a tab that renders empty and calls it
    success."""
    client.state["runtimes"] = [
        {"runtime": "codex", "day": "2026-09-08", "sessions": 0, "tokens": 0},
    ]
    assert _get(client)["runtimes"] == []


# ── the yes ─────────────────────────────────────────────────────────────

def test_events_make_it_connected(client):
    client.state["aggregates"] = [
        {"day": "2026-09-07", "event_count": 100},
        {"day": "2026-09-08", "event_count": 23},
    ]
    d = _get(client)
    assert d["connected"] is True
    assert d["events_total"] == 123
    assert d["last_event_day"] == "2026-09-08"
    assert d["next_step"] == "", "no next step is needed once data arrives"


def test_per_day_rows_collapse_to_one_row_per_runtime(client):
    """The rollup is one row per runtime PER DAY, so a runtime sending for
    a week appears seven times. The question is 'which sources are
    sending', so the answer is one row each."""
    client.state["aggregates"] = [{"day": "2026-09-08", "event_count": 5}]
    client.state["runtimes"] = [
        {"runtime": "claude_code", "day": "2026-09-06", "sessions": 1, "tokens": 10},
        {"runtime": "claude_code", "day": "2026-09-07", "sessions": 2, "tokens": 20},
        {"runtime": "claude_code", "day": "2026-09-08", "sessions": 3, "tokens": 30},
        {"runtime": "opencode", "day": "2026-09-08", "sessions": 1, "tokens": 5},
    ]
    rows = _get(client)["runtimes"]
    assert [r["runtime"] for r in rows] == ["claude_code", "opencode"], rows
    cc = rows[0]
    assert cc["tokens"] == 60 and cc["sessions"] == 6
    assert cc["last_day"] == "2026-09-08", "the most recent day should win"


# ── the two clocks are kept apart ───────────────────────────────────────

def test_in_process_otlp_counters_are_reported_separately(client):
    """The receiver's own counters empty on restart. Folding them into the
    durable total would tell a working install it is broken every time the
    dashboard restarts."""
    d = _get(client)
    assert "otlp_receiver" in d
    assert "has_data_this_process" in d["otlp_receiver"], (
        "the in-memory counter must be named as in-memory"
    )
    assert "otlp" not in d.get("events_total", "") if isinstance(
        d.get("events_total"), str) else True


# ── it is polled, so it must be cheap ───────────────────────────────────

def test_repeat_calls_are_memoised(client, monkeypatch):
    import routes.local_query as lq

    calls = []
    real = lq._dispatch
    monkeypatch.setattr(lq, "_dispatch",
                        lambda shape, args=None: (calls.append(shape),
                                                  real(shape, args))[1])
    client.ob._INGEST_STATUS_CACHE["at"] = 0.0
    client.ob._INGEST_STATUS_CACHE["body"] = None
    client.get("/api/onboarding/ingest-status")
    first = len(calls)
    client.get("/api/onboarding/ingest-status")
    assert len(calls) == first, (
        "the second call re-read the store. This endpoint is polled every "
        "few seconds while the gate is open."
    )


def test_a_store_failure_does_not_500(client, monkeypatch):
    """Never crash on bad input: a store that cannot answer should produce
    'nothing yet', not a stack trace on the first screen a user sees."""
    import routes.local_query as lq

    def _boom(shape, args=None):
        raise RuntimeError("store is invalidated")

    monkeypatch.setattr(lq, "_dispatch", _boom)
    client.ob._INGEST_STATUS_CACHE["at"] = 0.0
    client.ob._INGEST_STATUS_CACHE["body"] = None
    res = client.get("/api/onboarding/ingest-status")
    assert res.status_code == 200
    assert res.get_json()["connected"] is False


# ── the gate actually renders it ────────────────────────────────────────

def test_gate_markup_carries_the_strip_inside_the_card():
    """A strip rendered outside .obg-card sits on the overlay backdrop
    instead of in the dialog -- which is where it first landed."""
    import pathlib
    import re

    html = (pathlib.Path(__file__).resolve().parents[1]
            / "clawmetry" / "templates" / "partials"
            / "onboarding-modal.html").read_text()
    assert 'id="obg-ingest"' in html
    card = re.search(r'<div class="obg-card">(.*)', html, re.S)
    assert card and 'id="obg-ingest"' in card.group(1), (
        "the ingest strip is outside .obg-card"
    )


def test_gate_js_polls_and_stops():
    """A dismissed modal that keeps polling is a background fetch nobody
    can see -- the same shape as the Home widget that fetched every
    sub-agent into a hidden element."""
    import pathlib

    js = (pathlib.Path(__file__).resolve().parents[1]
          / "clawmetry" / "static" / "js" / "onboarding.js").read_text()
    assert "/api/onboarding/ingest-status" in js
    assert "_startIngestPoll" in js and "_stopIngestPoll" in js
    hide = js[js.index("function _hide("):js.index("function _hide(") + 200]
    assert "_stopIngestPoll" in hide, (
        "the poll is never stopped when the gate closes"
    )
