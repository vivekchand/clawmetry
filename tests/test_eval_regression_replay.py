"""Tests for ``clawmetry.eval_regression_replay`` — Phase 3 evals (refs #1619).

Eight scenarios per the PRD:
  1. find_failed_sessions — picks outcome IN (failed, escalated) + low-score
  2. replay_session — improved (failed -> success with higher score)
  3. replay_session — regressed (success -> failed)
  4. replay_session — same (no meaningful delta)
  5. compare_outcomes — pure-function rules (outcome > score)
  6. persistence — run_regression writes rows to a fake store
  7. API — /api/evals/regression-summary returns the aggregate shape
  8. CLI — `clawmetry eval --regression` happy path + cost-guarded limit

Honours the bug-class gate from feedback_synthetic_tests_missed_real_
event_shape.md: real OpenClaw v3 event shapes (prompt.submitted with
finalPromptText) feed the replay path, NOT synthetic ``message`` rows.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


from clawmetry import eval_regression_replay as err  # noqa: E402
from clawmetry.eval_regression_replay import (  # noqa: E402
    FailedSession,
    ReplayResult,
    compare_outcomes,
    find_failed_sessions,
    regression_summary,
    replay_session,
    run_regression,
)
from clawmetry.eval_suite_runner import AgentResponse  # noqa: E402


# ── Fakes ────────────────────────────────────────────────────────────────────


class _FakeStore:
    """In-memory stand-in for ``LocalStore``. Serves canned ``sessions``
    rows + per-session events, records persisted regression rows."""

    def __init__(self, sessions=None, events=None):
        # sessions: list of (sid, title, outcome, eval_score, last_active)
        self._sessions = list(sessions or [])
        # events: dict[session_id -> list[event dict]]
        self._events = dict(events or {})
        self.persisted: list[dict] = []

    def _fetch(self, sql, params):
        sql_l = " ".join(sql.split()).lower()
        if "from sessions" in sql_l and "where" in sql_l and "outcome in" in sql_l:
            # find_failed_sessions filter
            low_thresh = float(params[0])
            cutoff = params[1]
            limit = int(params[-1])
            out = []
            for sid, title, outcome, score, last_active in self._sessions:
                fails_outcome = outcome in ("failed", "escalated")
                low_score = score is not None and score < low_thresh
                if not (fails_outcome or low_score):
                    continue
                if cutoff and last_active and last_active < cutoff:
                    continue
                out.append((sid, title, outcome, score, last_active))
            return out[:limit]
        if "from sessions where session_id" in sql_l:
            sid = params[0]
            for s_sid, _t, outcome, score, _la in self._sessions:
                if s_sid == sid:
                    return [(outcome, score)]
            return []
        if "from eval_regression_runs" in sql_l:
            cutoff_ms = int(params[0])
            counts: dict[str, int] = {}
            last_ms = 0
            for r in self.persisted:
                if r["replayed_at"] < cutoff_ms:
                    continue
                counts[r["status"]] = counts.get(r["status"], 0) + 1
                if r["replayed_at"] > last_ms:
                    last_ms = r["replayed_at"]
            return [(s, n, last_ms) for s, n in counts.items()]
        return []

    def query_events(self, *, session_id, limit=200):
        # Mirror DuckDB DESC ordering — newest ts first.
        evs = list(self._events.get(session_id, []))
        evs.sort(key=lambda e: e.get("ts", ""), reverse=True)
        return evs[:limit]

    def persist_eval_regression_run(self, **kwargs):
        self.persisted.append(kwargs)


def _v3_events(session_id, prompt_text="I need a refund"):
    """Real OpenClaw v3 event shapes — prompt.submitted carries finalPromptText.
    Honours the bug-class gate per feedback_synthetic_tests_missed_real_event_shape."""
    return [
        {
            "session_id": session_id,
            "event_type": "prompt.submitted",
            "ts": "2026-05-15T10:00:00+00:00",
            "data": {"finalPromptText": prompt_text},
            "token_count": 12,
        },
        {
            "session_id": session_id,
            "event_type": "model.completed",
            "ts": "2026-05-15T10:00:02+00:00",
            "data": {"output": "Sorry, I cannot help."},
            "token_count": 24,
        },
    ]


# ── 1. find_failed_sessions picks the right rows ─────────────────────────────


def test_find_failed_sessions_picks_failed_and_low_score():
    store = _FakeStore(
        sessions=[
            ("s-fail", "Refund issue", "failed", None, "2026-05-15T10:00:00+00:00"),
            ("s-esc", "Hand-off", "escalated", 4.0, "2026-05-15T11:00:00+00:00"),
            ("s-low", "Bad answer", "success", 2.0, "2026-05-15T12:00:00+00:00"),
            ("s-good", "Worked", "success", 5.0, "2026-05-15T13:00:00+00:00"),
            ("s-unscored", "Unscored", "success", None, "2026-05-15T14:00:00+00:00"),
        ],
        events={
            "s-fail": _v3_events("s-fail", "I need a refund"),
            "s-esc": _v3_events("s-esc", "Escalate this"),
            "s-low": _v3_events("s-low", "Help me"),
        },
    )
    failed = find_failed_sessions(window_days=30, limit=10, store=store)
    sids = {f.session_id for f in failed}
    assert sids == {"s-fail", "s-esc", "s-low"}
    by_id = {f.session_id: f for f in failed}
    # Verifies the real-event-shape extraction reaches finalPromptText.
    assert by_id["s-fail"].original_input == "I need a refund"
    assert by_id["s-fail"].original_outcome == "failed"


# ── 2. replay_session — improved (failed -> success with higher score) ───────


def test_replay_session_improved():
    fs = FailedSession(
        session_id="s-1",
        title="Refund failure",
        original_input="I need a refund",
        original_outcome="failed",
        original_score=1.5,
        last_active_at="2026-05-15T10:00:00+00:00",
    )
    agent = lambda inp: AgentResponse(text="Issued refund #1234.", tools_used=["refund"], outcome="success")
    judge = lambda model, prompt, *, timeout=None: "SCORE: 5\nREASON: clean refund flow"
    result = replay_session("s-1", failed_session=fs, agent_call=agent, judge_call=judge)
    assert result.status == "improved"
    assert result.original_outcome == "failed"
    assert result.new_outcome == "success"
    assert result.new_score == 5.0


# ── 3. replay_session — regressed (success -> failed) ────────────────────────


def test_replay_session_regressed():
    fs = FailedSession(
        session_id="s-2",
        title="Was good",
        original_input="What's the weather?",
        original_outcome="success",
        original_score=4.5,
        last_active_at="",
    )
    # Original outcome is "success" but the session is low-score-flagged; new
    # run produces an outright failure -> regression.
    agent = lambda inp: AgentResponse(text="error", tools_used=[], outcome="failed")
    judge = lambda model, prompt, *, timeout=None: "SCORE: 1\nREASON: broken"
    result = replay_session("s-2", failed_session=fs, agent_call=agent, judge_call=judge)
    assert result.status == "regressed"
    assert result.new_outcome == "failed"


# ── 4. replay_session — same (no meaningful delta) ───────────────────────────


def test_replay_session_same_when_no_delta():
    fs = FailedSession(
        session_id="s-3",
        title="Borderline",
        original_input="hello",
        original_outcome="failed",
        original_score=2.0,
        last_active_at="",
    )
    # Failed -> failed, score within dead band.
    agent = lambda inp: AgentResponse(text="still broken", tools_used=[], outcome="failed")
    judge = lambda model, prompt, *, timeout=None: "SCORE: 2.2\nREASON: same shape"
    result = replay_session("s-3", failed_session=fs, agent_call=agent, judge_call=judge)
    assert result.status == "same"


def test_replay_session_error_when_no_input():
    fs = FailedSession(
        session_id="s-4", title="Empty", original_input="",
        original_outcome="failed", original_score=None, last_active_at="",
    )
    agent = lambda inp: AgentResponse(text="x", tools_used=[], outcome="success")
    result = replay_session("s-4", failed_session=fs, agent_call=agent)
    assert result.status == "error"
    assert "no original input" in result.reason.lower()


# ── 5. compare_outcomes — pure rules ─────────────────────────────────────────


def test_compare_outcomes_outcome_transition_wins():
    assert compare_outcomes(
        old_outcome="failed", old_score=4.5,
        new_outcome="success", new_score=1.0,
    ) == "improved"
    assert compare_outcomes(
        old_outcome="success", old_score=1.0,
        new_outcome="failed", new_score=4.5,
    ) == "regressed"


def test_compare_outcomes_score_delta_in_dead_band():
    # Outcome unchanged, score moves by less than 0.5 -> same.
    assert compare_outcomes(
        old_outcome="success", old_score=3.0,
        new_outcome="success", new_score=3.3,
    ) == "same"
    # >= 0.5 delta crosses the dead band.
    assert compare_outcomes(
        old_outcome="success", old_score=3.0,
        new_outcome="success", new_score=3.5,
    ) == "improved"
    assert compare_outcomes(
        old_outcome="success", old_score=3.0,
        new_outcome="success", new_score=2.5,
    ) == "regressed"


# ── 6. Persistence — run_regression writes to the fake store ─────────────────


def test_run_regression_persists_to_store():
    store = _FakeStore(
        sessions=[
            ("s-a", "Refund", "failed", 1.0, "2026-05-15T10:00:00+00:00"),
            ("s-b", "Hand-off", "escalated", None, "2026-05-15T11:00:00+00:00"),
        ],
        events={
            "s-a": _v3_events("s-a", "refund please"),
            "s-b": _v3_events("s-b", "escalate"),
        },
    )
    agent = lambda inp: AgentResponse(text="fixed", tools_used=["refund"], outcome="success")
    judge = lambda model, prompt, *, timeout=None: "SCORE: 5\nREASON: ok"
    run = run_regression(
        window_days=30, limit=10, store=store,
        agent_call=agent, judge_call=judge, persist=True,
    )
    assert run.tested == 2
    assert run.improved == 2
    assert run.regressed == 0
    assert len(store.persisted) == 2
    # All rows carry the canonical column set the schema migration expects.
    for row in store.persisted:
        assert set(row.keys()) >= {
            "session_id", "status", "original_outcome", "new_outcome",
            "original_score", "new_score", "reason", "replayed_at",
        }
        assert row["status"] == "improved"


def test_regression_summary_aggregates_persisted_rows():
    store = _FakeStore()
    # Pre-populate the persisted log directly so we test the read path.
    import time as _t
    now_ms = int(_t.time() * 1000)
    store.persisted.extend([
        {"session_id": "x1", "status": "improved", "replayed_at": now_ms,
         "original_outcome": "failed", "new_outcome": "success",
         "original_score": 1.0, "new_score": 5.0, "reason": ""},
        {"session_id": "x2", "status": "improved", "replayed_at": now_ms - 1000,
         "original_outcome": "failed", "new_outcome": "success",
         "original_score": 1.0, "new_score": 5.0, "reason": ""},
        {"session_id": "x3", "status": "regressed", "replayed_at": now_ms - 2000,
         "original_outcome": "success", "new_outcome": "failed",
         "original_score": 4.5, "new_score": 1.0, "reason": ""},
        {"session_id": "x4", "status": "same", "replayed_at": now_ms - 3000,
         "original_outcome": "failed", "new_outcome": "failed",
         "original_score": 2.0, "new_score": 2.1, "reason": ""},
    ])
    out = regression_summary(window_days=7, store=store)
    assert out["tested"] == 4
    assert out["improved"] == 2
    assert out["regressed"] == 1
    assert out["same"] == 1
    assert out["window_days"] == 7
    assert out["last_run_at"] == now_ms


# ── 7. API — /api/evals/regression-summary returns the aggregate shape ───────


def test_api_regression_summary_endpoint_shape(monkeypatch):
    """Exercise the Flask route end-to-end via the test client. Patches the
    summary helper so the endpoint doesn't reach the live DuckDB."""
    sample = {
        "tested": 5, "improved": 3, "regressed": 1, "same": 1,
        "errored": 0, "window_days": 7, "last_run_at": 1234567890123,
    }
    monkeypatch.setattr(err, "regression_summary", lambda **kw: dict(sample))

    from flask import Flask
    from routes.evals import bp_evals

    app = Flask(__name__)
    app.register_blueprint(bp_evals)
    client = app.test_client()
    resp = client.get("/api/evals/regression-summary?window=7d")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tested"] == 5
    assert body["improved"] == 3
    assert body["regressed"] == 1
    assert body["window_days"] == 7
    assert body["last_run_at"] == 1234567890123


def test_api_regression_summary_handles_empty_store(monkeypatch):
    """A fresh install (no run yet) returns the empty payload, not an error."""
    monkeypatch.setattr(
        err, "regression_summary",
        lambda **kw: {
            "tested": 0, "improved": 0, "regressed": 0, "same": 0,
            "errored": 0, "window_days": 7, "last_run_at": None,
        },
    )
    from flask import Flask
    from routes.evals import bp_evals

    app = Flask(__name__)
    app.register_blueprint(bp_evals)
    client = app.test_client()
    resp = client.get("/api/evals/regression-summary")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tested"] == 0
    assert body["last_run_at"] is None


# ── 8. CLI — `clawmetry eval --regression` ──────────────────────────────────


def test_cli_regression_invokes_run_regression(monkeypatch, capsys):
    """Drive _cmd_eval through a synthetic argparse namespace; verify the
    cost-guarded limit is respected and the summary prints. We patch the
    runner module to avoid touching DuckDB or HTTP."""
    from clawmetry import cli, eval_regression_replay as err_mod

    captured = {}

    def fake_run_regression(*, window_days, limit, **kwargs):
        captured["window_days"] = window_days
        captured["limit"] = limit
        run = err_mod.RegressionRun(ran_at=1, window_days=window_days)
        run.results.append(err_mod.ReplayResult(
            session_id="abc", status="improved",
            original_outcome="failed", new_outcome="success",
            original_score=1.0, new_score=5.0,
            reason="fixed", replayed_at=2,
        ))
        return run

    monkeypatch.setattr(err_mod, "run_regression", fake_run_regression)
    monkeypatch.setattr(err_mod, "is_enabled", lambda: True)

    class _Args:
        regression = True
        window = "14d"
        limit = 3
        as_json = False

    with pytest.raises(SystemExit) as exc:
        cli._cmd_eval(_Args())
    # 0 because no regressed/errored rows.
    assert exc.value.code == 0
    assert captured["window_days"] == 14
    assert captured["limit"] == 3
    out = capsys.readouterr().out
    assert "1 improved" in out
    assert "0 regressed" in out


def test_cli_regression_exit_code_nonzero_on_regression(monkeypatch):
    """A regressed row in the run should make the CLI exit 1 — that's the
    CI-gate contract that mirrors --suite behavior."""
    from clawmetry import cli, eval_regression_replay as err_mod

    def fake_run(*, window_days, limit, **kwargs):
        run = err_mod.RegressionRun(ran_at=1, window_days=window_days)
        run.results.append(err_mod.ReplayResult(
            session_id="z", status="regressed",
            original_outcome="success", new_outcome="failed",
            original_score=4.5, new_score=1.0,
            reason="broke", replayed_at=2,
        ))
        return run

    monkeypatch.setattr(err_mod, "run_regression", fake_run)
    monkeypatch.setattr(err_mod, "is_enabled", lambda: True)

    class _Args:
        regression = True
        window = "7d"
        limit = None
        as_json = False

    with pytest.raises(SystemExit) as exc:
        cli._cmd_eval(_Args())
    assert exc.value.code == 1


# ── Smoke: DuckDB v10 migration creates the regression table ────────────────


def test_schema_v10_creates_eval_regression_runs_table(tmp_path, monkeypatch):
    """End-to-end: opening a fresh LocalStore at v10 must create the table
    and the persist + query methods must round-trip a row. Catches schema
    drift bugs that synthetic _FakeStore tests would miss."""
    db_file = tmp_path / "store.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_file))
    # Force fresh import so the env var is honoured + reset singletons.
    for mod in ("clawmetry.local_store",):
        if mod in sys.modules:
            del sys.modules[mod]
    from clawmetry import local_store as ls
    assert ls.SCHEMA_VERSION >= 10
    # Patch DB_PATH on the freshly-loaded module — env-var-via-Path() was
    # evaluated at import time so this belt+suspenders ensures the tmp file.
    monkeypatch.setattr(ls, "DB_PATH", db_file)
    store = ls.LocalStore()
    try:
        store.persist_eval_regression_run(
            session_id="sid-1",
            status="improved",
            original_outcome="failed",
            new_outcome="success",
            original_score=1.0,
            new_score=5.0,
            reason="r",
            replayed_at=10_000,
        )
        rows = store.query_recent_regression_runs(limit=10)
        assert len(rows) == 1
        assert rows[0]["session_id"] == "sid-1"
        assert rows[0]["status"] == "improved"
        assert rows[0]["new_score"] == 5.0
    finally:
        try:
            store.stop(flush=False)
        except Exception:
            pass
        ls._reset_singleton_for_tests()
