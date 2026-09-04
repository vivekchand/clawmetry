"""Non-determinism replay is OPT-IN and never runs without the env flag.

A replay re-runs the user's agent for real money, so the scheduler must be
inert by default, bounded by a per-day budget and a per-tick cap when on, and
must turn N replays of one session into an honest agreement number
(``session_replay_stats``) that the free session API exposes as
``nondeterminism`` (null when never measured).
"""
from __future__ import annotations

import importlib
import os
import sys
import time

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import sync as _sync  # noqa: E402
from clawmetry import eval_regression_replay as rr  # noqa: E402


class _Run:
    def __init__(self, sids):
        self.results = [type("R", (), {"session_id": s})() for s in sids]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for k in (_sync.REPLAY_ENABLE_ENV, _sync.REPLAY_DAILY_BUDGET_ENV,
              _sync.REPLAY_MAX_PER_TICK_ENV, _sync.REPLAY_RUNS_PER_SESSION_ENV):
        monkeypatch.delenv(k, raising=False)


# ── the flag ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("value", [None, "", "0", "false", "no", "off", "2"])
def test_nothing_runs_without_the_flag(monkeypatch, value):
    if value is None:
        monkeypatch.delenv(_sync.REPLAY_ENABLE_ENV, raising=False)
    else:
        monkeypatch.setenv(_sync.REPLAY_ENABLE_ENV, value)
    calls = []
    n = _sync._maybe_run_regression_replay(
        object(), {}, replay_fn=lambda **kw: calls.append(kw) or _Run(["s1"]))
    assert n == 0 and calls == []
    assert _sync._regression_replay_enabled() is False


def test_the_older_evals_flag_does_not_turn_the_scheduler_on(monkeypatch):
    """``CLAWMETRY_EVALS_REGRESSION_ENABLED`` gates the manual CLI; it must
    not schedule anything by itself."""
    monkeypatch.setenv("CLAWMETRY_EVALS_REGRESSION_ENABLED", "1")
    calls = []
    assert _sync._maybe_run_regression_replay(
        object(), {}, replay_fn=lambda **kw: calls.append(kw) or _Run(["s1"])) == 0
    assert calls == []


# ── budget + cap when on ───────────────────────────────────────────────────

def test_flag_on_runs_each_session_n_times_within_budget(monkeypatch):
    monkeypatch.setenv(_sync.REPLAY_ENABLE_ENV, "1")
    monkeypatch.setenv(_sync.REPLAY_RUNS_PER_SESSION_ENV, "3")
    monkeypatch.setenv(_sync.REPLAY_DAILY_BUDGET_ENV, "10")
    monkeypatch.setattr(rr, "update_agreement_stats", lambda store, sid: None)
    calls = []
    state = {}
    n = _sync._maybe_run_regression_replay(
        object(), state, replay_fn=lambda **kw: calls.append(kw) or _Run(["s1"]))
    assert n == 3 and len(calls) == 3
    assert all(c["limit"] == 1 for c in calls)  # per-tick cap default 1
    assert state["replay_budget"]["used"] == 3


def test_daily_budget_is_enforced_and_persisted_in_state(monkeypatch):
    monkeypatch.setenv(_sync.REPLAY_ENABLE_ENV, "1")
    monkeypatch.setenv(_sync.REPLAY_RUNS_PER_SESSION_ENV, "1")
    monkeypatch.setenv(_sync.REPLAY_DAILY_BUDGET_ENV, "2")
    monkeypatch.setattr(rr, "update_agreement_stats", lambda store, sid: None)
    state = {}
    fn = lambda **kw: _Run(["s1"])  # noqa: E731
    assert _sync._maybe_run_regression_replay(object(), state, replay_fn=fn) == 1
    assert _sync._maybe_run_regression_replay(object(), state, replay_fn=fn) == 1
    assert _sync._maybe_run_regression_replay(object(), state, replay_fn=fn) == 0
    assert state["replay_budget"]["used"] == 2
    # Next UTC day: the counter resets.
    tomorrow = time.time() + 86400
    assert _sync._maybe_run_regression_replay(object(), state, now=tomorrow, replay_fn=fn) == 1


def test_budget_smaller_than_runs_per_session_means_no_replay(monkeypatch):
    monkeypatch.setenv(_sync.REPLAY_ENABLE_ENV, "1")
    monkeypatch.setenv(_sync.REPLAY_RUNS_PER_SESSION_ENV, "3")
    monkeypatch.setenv(_sync.REPLAY_DAILY_BUDGET_ENV, "2")
    calls = []
    assert _sync._maybe_run_regression_replay(
        object(), {}, replay_fn=lambda **kw: calls.append(1) or _Run(["s1"])) == 0
    assert calls == []


# ── agreement metric ───────────────────────────────────────────────────────

def test_compute_agreement():
    assert rr.compute_agreement([]) == (None, None)
    assert rr.compute_agreement(["failed"]) == (100.0, "failed")
    assert rr.compute_agreement(["failed", "failed", "success"]) == (66.7, "failed")
    assert rr.compute_agreement(["a", "b", "c"]) == (33.3, "a")
    assert rr.compute_agreement(["a", "b", "b", "a"])[0] == 50.0


@pytest.fixture
def store(tmp_path, monkeypatch):
    pytest.importorskip("duckdb")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "t.duckdb"))
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    from pathlib import Path
    monkeypatch.setattr(ls, "DB_PATH", Path(str(tmp_path / "t.duckdb")))
    st = ls.get_store()
    yield st
    try:
        st.stop(flush=False)
    except Exception:
        pass


def _persist(store, sid, outcome, i):
    store.persist_eval_regression_run(
        session_id=sid, status="same", original_outcome="failed",
        new_outcome=outcome, original_score=1.0, new_score=1.0,
        reason="t", replayed_at=1_700_000_000_000 + i)


def test_agreement_persists_to_session_replay_stats(store):
    for i, o in enumerate(["failed", "success", "failed"]):
        _persist(store, "codex:s1", o, i)
    row = rr.update_agreement_stats(store, "codex:s1")
    assert row["runs"] == 3 and row["agreement_pct"] == 66.7
    rows = store.query_session_replay_stats(session_ids=["codex:s1"])
    assert rows[0]["runs"] == 3 and rows[0]["agreement_pct"] == 66.7
    assert rows[0]["outcomes"] == ["failed", "success", "failed"]
    assert rr.update_agreement_stats(store, "never-replayed") is None


def test_session_rows_expose_nondeterminism_null_until_measured(store):
    from routes import local_query as lq
    lq._ND_CACHE.update({"ts": 0.0, "rows": {}})
    body = {"rows": [{"session_id": "codex:s1"}, {"session_id": "codex:s2"}]}
    lq._attach_nondeterminism(body, store=store)
    assert body["rows"][0]["nondeterminism"] is None
    assert body["rows"][1]["nondeterminism"] is None
    for i, o in enumerate(["ok", "ok"]):
        _persist(store, "codex:s1", o, i)
    rr.update_agreement_stats(store, "codex:s1")
    lq._ND_CACHE.update({"ts": 0.0, "rows": {}})
    lq._attach_nondeterminism(body, store=store)
    assert body["rows"][0]["nondeterminism"] == {
        "runs": 2, "agreement_pct": 100.0,
        "measured_at": body["rows"][0]["nondeterminism"]["measured_at"]}
    assert body["rows"][1]["nondeterminism"] is None


def test_replay_stats_method_is_daemon_allowlisted():
    from routes.local_query import _DAEMON_METHODS
    assert "query_session_replay_stats" in _DAEMON_METHODS
    assert "query_incident_alerts" in _DAEMON_METHODS


def test_guard_status_copy_is_honest_when_off(monkeypatch):
    """The endpoint's note must say it is not measured and why it is opt-in."""
    import dashboard  # noqa: F401  (registers blueprints)
    from routes.guard import api_guard_nondeterminism
    monkeypatch.setattr("routes.guard._ls_call", lambda *a, **k: [])
    app = dashboard.app
    with app.test_request_context("/api/guard/nondeterminism"):
        payload = api_guard_nondeterminism().get_json()
    assert payload["enabled"] is False and payload["measured_sessions"] == 0
    assert "Not measured" in payload["note"] and "costs money" in payload["note"]
    assert _sync.REPLAY_ENABLE_ENV in payload["note"]
