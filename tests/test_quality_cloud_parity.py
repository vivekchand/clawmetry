"""Quality reaches the hosted dashboard, and never lies when it cannot.

Founder live-hit 2026-08-22: the hosted Quality tab said "Nothing to grade
yet" for a machine whose own dashboard showed an A over 119 graded runs, same
node, same runtime. Two faults, one screen:

  1. The grade never rode the encrypted snapshot, so the cloud had nothing to
     render — the cloud-parity gate every data card is supposed to pass.
  2. The hosted container answered anyway, from its OWN DuckDB. That file
     exists and is empty, so the query succeeded with zero rows and the tab
     reported a working machine as having produced nothing. "Nothing to
     grade" and "I cannot see your machine" look identical and mean opposite
     things.

These tests pin both: the daemon emits the slice (node-wide and per runtime),
and the hosted process refuses to answer from its own empty store.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _row(sid, runtime, cost=1.0, tool_err=0.0):
    return {
        "session_id": sid,
        "runtime": runtime,
        "cost_usd": cost,
        "message_count": 12,
        "toolErrorPct": tool_err,
        "maxIdleGapSec": 5,
        "status": "completed",
        "title": f"task {sid}",
        "started_at": "2026-08-20T10:00:00+00:00",
        "ended_at": "2026-08-20T10:20:00+00:00",
        "last_active_at": "2026-08-20T10:20:00+00:00",
        "metadata": {"quality": {"measurable": True, "rough": False,
                                 "signals": {}, "verdicts": []}},
    }


class _FakeStore:
    """Answers query_quality_sessions the way the daemon's own handle does."""

    def __init__(self, window_rows, hist_rows=None):
        self.window_rows = window_rows
        self.hist_rows = hist_rows if hist_rows is not None else window_rows
        self.calls = 0

    def query_quality_sessions(self, since=None, until=None, limit=None, runtime=None):
        self.calls += 1
        if until:                      # prior window
            return []
        if limit and limit > 1000:     # the 30-day calibration read
            return list(self.hist_rows)
        return list(self.window_rows)


@pytest.fixture
def daemon_store(monkeypatch):
    def _install(window_rows, hist_rows=None):
        from clawmetry import local_store as ls
        store = _FakeStore(window_rows, hist_rows)
        monkeypatch.setattr(ls, "get_store", lambda *a, **k: store)
        return store
    return _install


# ── the daemon emits it ────────────────────────────────────────────────

def test_snapshot_carries_node_wide_and_per_runtime_cards(daemon_store):
    from clawmetry import sync

    daemon_store([_row("s1", "claude_code"), _row("s2", "claude_code"),
                  _row("s3", "openclaw")])
    slice_ = sync._build_quality_snapshot()

    assert slice_["window_hours"] == 168
    assert slice_["all"]["total_runs"] == 3
    assert set(slice_["byRuntime"]) == {"claude_code", "openclaw"}
    assert slice_["byRuntime"]["claude_code"]["total_runs"] == 2
    assert slice_["byRuntime"]["openclaw"]["total_runs"] == 1


def test_per_runtime_card_never_carries_another_runtimes_runs(daemon_store):
    """The honesty rule for the runtime switcher: a grade shown under one
    runtime must be that runtime's, not the node's total wearing its name."""
    from clawmetry import sync

    daemon_store([_row("a", "claude_code"), _row("b", "codex"), _row("c", "codex")])
    cards = sync._build_quality_snapshot()["byRuntime"]
    assert cards["claude_code"]["total_runs"] == 1
    assert cards["codex"]["total_runs"] == 2
    assert cards["claude_code"]["runtime"] == "claude_code"


def test_runtime_quiet_this_week_still_gets_its_own_card(daemon_store):
    """Otherwise the hosted tab falls back to the node-wide card and shows
    another runtime's grade under this runtime's filter."""
    from clawmetry import sync

    daemon_store([_row("a", "claude_code")],
                 hist_rows=[_row("a", "claude_code"), _row("old", "cursor")])
    cards = sync._build_quality_snapshot()["byRuntime"]
    assert "cursor" in cards
    assert cards["cursor"]["total_runs"] == 0
    assert "nothing to grade" in cards["cursor"]["headline"].lower()


def test_calibration_is_carried_once_not_per_card(daemon_store):
    """It is identical in every card; inline it was a quarter of the slice."""
    from clawmetry import sync

    daemon_store([_row("a", "claude_code"), _row("b", "codex")])
    slice_ = sync._build_quality_snapshot()
    assert "thresholds" in slice_
    assert "thresholds" not in slice_["all"]
    for card in slice_["byRuntime"].values():
        assert "thresholds" not in card


def test_store_is_read_once_regardless_of_runtime_count(daemon_store):
    """Per-runtime cards must cost no extra queries — the daemon runs this
    every snapshot cycle and has a CPU budget."""
    from clawmetry import sync

    store = daemon_store([_row(f"s{i}", rt) for i, rt in
                          enumerate(["claude_code", "codex", "cursor",
                                     "goose", "openclaw", "pi"])])
    sync._build_quality_snapshot()
    assert store.calls == 3, (
        f"expected 3 reads (window, prior, history), got {store.calls}"
    )


def test_snapshot_slice_never_raises(monkeypatch):
    """A snapshot must not fail to build over one optional slice."""
    from clawmetry import local_store as ls
    from clawmetry import sync

    def boom(*a, **k):
        raise RuntimeError("store on fire")

    monkeypatch.setattr(ls, "get_store", boom)
    assert sync._build_quality_snapshot() == {}


# ── the hosted process refuses to answer from its own empty store ──────

def _app():
    from routes.quality import bp_quality
    app = Flask(__name__)
    app.register_blueprint(bp_quality)
    return app


def test_hosted_dashboard_says_where_the_grade_lives(monkeypatch):
    from routes import quality as qmod

    monkeypatch.setenv("CLAWMETRY_CLOUD", "1")
    # An empty-but-working store, exactly what the hosted container has.
    monkeypatch.setattr(qmod, "_store_via_daemon_or_direct", lambda *a, **k: [])
    with _app().test_client() as c:
        body = c.get("/api/quality/report-card?window=7d&runtime=claude_code").get_json()
    assert body["store_available"] is False
    assert "your own machine" in body["headline"].lower()
    assert "nothing to grade" not in body["headline"].lower(), (
        "the hosted tab must not report a working machine as having produced "
        "nothing — that is the bug this closes"
    )


def test_local_dashboard_still_reports_a_real_empty_week(monkeypatch):
    """Off the hosted dashboard, an empty store IS the answer: this machine
    genuinely has not run anything this week."""
    from routes import quality as qmod

    monkeypatch.delenv("CLAWMETRY_CLOUD", raising=False)
    monkeypatch.setattr(qmod, "_store_via_daemon_or_direct", lambda *a, **k: [])
    with _app().test_client() as c:
        body = c.get("/api/quality/report-card?window=7d").get_json()
    assert body["store_available"] is True
    assert "nothing to grade" in body["headline"].lower()


def test_unreachable_store_is_not_an_empty_grade(monkeypatch):
    from routes import quality as qmod

    monkeypatch.delenv("CLAWMETRY_CLOUD", raising=False)
    monkeypatch.setattr(qmod, "_store_via_daemon_or_direct", lambda *a, **k: None)
    with _app().test_client() as c:
        body = c.get("/api/quality/report-card").get_json()
    assert body["store_available"] is False
    assert "your own machine" in body["headline"].lower()


def test_precomputed_assessments_match_the_request_path(daemon_store):
    """The daemon reuses one assessment map across cards; that must not change
    the grade a card reports."""
    from routes.quality import _assess_rows, compose_report_card
    from clawmetry import quality_thresholds as qt

    rows = [_row("a", "claude_code", cost=3.0), _row("b", "claude_code")]
    thresholds = qt.calibrate_all({"claude_code": rows})
    shared = _assess_rows(rows, thresholds)

    fresh = compose_report_card(rows, [], rows, window_hours=168, runtime="claude_code")
    reused = compose_report_card(rows, [], rows, window_hours=168, runtime="claude_code",
                                 assessments=shared, prior_assessments={})
    assert fresh["grade"] == reused["grade"]
    assert fresh["total_runs"] == reused["total_runs"]
    assert fresh["graded_runs"] == reused["graded_runs"]
