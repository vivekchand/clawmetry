"""Tests for ``clawmetry.eval_runner`` — Phase 1 LLM-as-judge (refs #1619).

Six scenarios per the PRD:
  1. Score parsing (SCORE: 4 / REASON: ...)
  2. Rubric YAML loading (default + custom)
  3. Rate-limit guard (100/hour cap)
  4. Skip trivial sessions (<10 tokens)
  5. Judge LLM failure (graceful — NULL score + warning)
  6. Aggregate summary returns correct avg

Plus a smoke test of the canonical event-shape union (bug-class gate per
``feedback_synthetic_tests_missed_real_event_shape.md``): scoring exercises
real OpenClaw v3 ``prompt.submitted`` + ``model.completed`` shapes alongside
the legacy ``message`` shape.

All tests use mocked judge calls. The live-API smoke is gated on
``CI_ANTHROPIC_API_KEY`` so CI doesn't burn credits on every push.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


from clawmetry import eval_runner  # noqa: E402
from clawmetry.eval_runner import (  # noqa: E402
    EvalRunner,
    DEFAULT_RUBRIC,
    DEFAULT_RUBRIC_YAML,
    _RateLimiter,
    load_rubric,
    parse_score,
    save_rubric_yaml,
)


# ── Fakes ────────────────────────────────────────────────────────────────────


class _FakeStore:
    """In-memory stand-in for ``LocalStore`` that records persisted scores
    and serves a canned event timeline. Lets us exercise the full runner
    without DuckDB or the daemon proxy."""

    def __init__(self, events):
        # ``events`` is iterable of dicts; mirror DuckDB's DESC ordering.
        self._events = list(events)
        self.persisted: list[dict] = []

    def query_events(self, *, session_id, limit=200):
        rows = [e for e in self._events if e.get("session_id") == session_id]
        rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
        return rows[:limit]

    def persist_eval_score(self, **kwargs):
        self.persisted.append(kwargs)


def _events_v3_shape(session_id="s-1"):
    """Realistic OpenClaw v3 event shapes — the bug-class gate per
    ``feedback_synthetic_tests_missed_real_event_shape.md`` requires real
    event_type strings (``prompt.submitted`` + ``model.completed``), not
    synthetic ``message``."""
    return [
        {
            "session_id":  session_id,
            "event_type":  "prompt.submitted",
            "ts":          "2026-05-17T19:00:00+00:00",
            "data":        {"finalPromptText": "Write me a haiku about Rust."},
            "token_count": 18,
        },
        {
            "session_id":  session_id,
            "event_type":  "model.completed",
            "ts":          "2026-05-17T19:00:02+00:00",
            "data":        {
                "modelId":  "claude-haiku-4-5",
                "provider": "anthropic",
                "output":   "Borrow checker hums\nLifetimes weave through every scope\nMemory rests safe",
            },
            "token_count": 42,
        },
    ]


# ── 1. Score parsing ─────────────────────────────────────────────────────────


def test_parse_score_extracts_score_and_reason():
    s, r = parse_score("SCORE: 4\nREASON: Mostly correct but missed the closing tag.")
    assert s == 4.0
    assert r == "Mostly correct but missed the closing tag."


def test_parse_score_tolerates_extra_prose_and_case():
    s, r = parse_score("Sure! score: 5\nreason: Great answer.\n\n--end--")
    assert s == 5.0
    assert r and "Great answer" in r


def test_parse_score_handles_float_score():
    s, _ = parse_score("SCORE: 3.5\nREASON: Close.")
    assert s == 3.5


def test_parse_score_returns_none_when_garbage():
    s, r = parse_score("I cannot help with this request.")
    assert s is None and r is None


def test_parse_score_rejects_out_of_band_value():
    s, _ = parse_score("SCORE: 11\nREASON: Off scale.")
    assert s is None  # 11 isn't in 0-5; bail rather than persist


# ── 2. Rubric loading ────────────────────────────────────────────────────────


def test_load_rubric_defaults_when_no_file(tmp_path, monkeypatch):
    missing = tmp_path / "missing.yaml"
    monkeypatch.setattr(eval_runner, "RUBRIC_PATH", missing)
    r = load_rubric()
    assert r["judge_model"] == DEFAULT_RUBRIC["judge_model"]
    assert "SCORE:" in r["prompt"]


def test_load_rubric_custom_overrides_default(tmp_path, monkeypatch):
    p = tmp_path / "evals.yaml"
    p.write_text(
        "default:\n"
        "  judge_model: claude-sonnet-4-5\n"
        "  prompt: |\n"
        "    Custom rubric:\n"
        "    SCORE: <0-5>\n"
        "    REASON: <why>\n"
    )
    monkeypatch.setattr(eval_runner, "RUBRIC_PATH", p)
    r = load_rubric("default")
    assert r["judge_model"] == "claude-sonnet-4-5"
    assert "Custom rubric:" in r["prompt"]


def test_load_rubric_partial_override_keeps_default_prompt(tmp_path, monkeypatch):
    p = tmp_path / "evals.yaml"
    p.write_text("default:\n  judge_model: claude-opus-4-5\n")
    monkeypatch.setattr(eval_runner, "RUBRIC_PATH", p)
    r = load_rubric("default")
    assert r["judge_model"] == "claude-opus-4-5"
    # Default prompt is still wired in.
    assert r["prompt"] == DEFAULT_RUBRIC["prompt"]


def test_save_rubric_round_trips(tmp_path, monkeypatch):
    p = tmp_path / "evals.yaml"
    monkeypatch.setattr(eval_runner, "RUBRIC_PATH", p)
    save_rubric_yaml(DEFAULT_RUBRIC_YAML)
    assert p.exists()
    r = load_rubric("default")
    assert r["judge_model"] == DEFAULT_RUBRIC["judge_model"]


# ── 3. Rate-limit guard ─────────────────────────────────────────────────────


def test_rate_limiter_allows_up_to_cap_then_blocks_in_window():
    rl = _RateLimiter(cap=100)
    fixed_now = 1_700_000_000.0
    for _ in range(100):
        assert rl.allow(now=fixed_now) is True
    # 101st call within the hour bucket must be denied.
    assert rl.allow(now=fixed_now + 30) is False


def test_rate_limiter_recovers_after_window():
    rl = _RateLimiter(cap=2)
    base = 1_700_000_000.0
    assert rl.allow(now=base) is True
    assert rl.allow(now=base + 10) is True
    assert rl.allow(now=base + 20) is False
    # Past the 1-hour window — old hits dropped.
    assert rl.allow(now=base + 3601) is True


def test_runner_skips_when_rate_limit_exhausted():
    """End-to-end: a runner with an exhausted limiter returns a skip
    (not a failure) so the scheduler retries on the next tick."""
    rl = _RateLimiter(cap=1)
    rl.allow()  # burn the single slot
    store = _FakeStore(_events_v3_shape())
    runner = EvalRunner(rate_limiter=rl, store=store)
    res = runner.score_session("s-1", judge_call=lambda *a, **kw: "SCORE: 5\nREASON: ok")
    assert res is not None
    assert res.skipped is True
    assert "rate limit" in (res.skip_reason or "")
    assert res.score is None
    # Nothing persisted — the row stays NULL for the next pass.
    assert store.persisted == []


# ── 4. Skip trivial sessions ────────────────────────────────────────────────


def test_skip_trivial_session_under_min_tokens():
    """Sessions with <10 tokens are heartbeat/smoke pings — score them and
    you skew the rubric average."""
    tiny = [{
        "session_id":  "s-tiny",
        "event_type":  "prompt.submitted",
        "ts":          "2026-05-17T19:00:00+00:00",
        "data":        {"finalPromptText": "hi"},
        "token_count": 2,
    }]
    store = _FakeStore(tiny)
    called = {"n": 0}
    def _fake_judge(*a, **kw):
        called["n"] += 1
        return "SCORE: 5\nREASON: x"
    runner = EvalRunner(store=store)
    res = runner.score_session("s-tiny", judge_call=_fake_judge)
    assert res is not None
    assert res.skipped is True
    assert "trivial" in (res.skip_reason or "")
    # No judge call → no spend.
    assert called["n"] == 0
    assert store.persisted == []


# ── 5. Judge LLM failure ────────────────────────────────────────────────────


def test_judge_failure_returns_null_score_and_logs(caplog):
    store = _FakeStore(_events_v3_shape())
    runner = EvalRunner(store=store)
    def _exploding_judge(model, prompt, *, timeout):
        raise RuntimeError("judge offline")
    with caplog.at_level("WARNING", logger="clawmetry.eval_runner"):
        res = runner.score_session("s-1", judge_call=_exploding_judge)
    assert res is not None
    assert res.score is None
    assert res.skipped is False  # not a skip — a failure we want to retry
    assert "RuntimeError" in (res.skip_reason or "")
    # No DuckDB write on failure — the row stays NULL.
    assert store.persisted == []
    # Warning was logged so ops can see the judge outage.
    assert any("judge call failed" in r.message for r in caplog.records)


def test_score_persists_when_judge_succeeds():
    store = _FakeStore(_events_v3_shape())
    runner = EvalRunner(store=store)
    res = runner.score_session(
        "s-1",
        judge_call=lambda *a, **kw: "SCORE: 4\nREASON: Solid haiku.",
    )
    assert res is not None
    assert res.score == 4.0
    assert res.reason == "Solid haiku."
    assert len(store.persisted) == 1
    p = store.persisted[0]
    assert p["session_id"] == "s-1"
    assert p["score"] == 4.0
    assert p["judge_model"] == DEFAULT_RUBRIC["judge_model"]


# ── 6. Aggregate summary ────────────────────────────────────────────────────
#
# Exercises ``LocalStore.query_eval_summary`` end-to-end against a real
# DuckDB file so we catch quantile/AVG regressions. Uses a tmp DB so
# nothing touches the user's clawmetry.duckdb.


def test_eval_summary_avg_matches_persisted_scores(tmp_path, monkeypatch):
    db_path = tmp_path / "clawmetry.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    # Force module-level singletons to re-init against the tmp path.
    from clawmetry import local_store
    monkeypatch.setattr(local_store, "DB_PATH", db_path)
    monkeypatch.setattr(local_store, "_STORE", None, raising=False)
    store = local_store.LocalStore()
    # Seed three completed sessions with known scores.
    now_iso = "2026-05-17T19:00:00+00:00"
    with store._write_lock:
        for sid, tok in [("a", 50), ("b", 60), ("c", 70)]:
            store._conn.execute(
                """
                INSERT INTO sessions
                  (agent_type, session_id, node_id, agent_id, started_at,
                   last_active_at, ended_at, status, total_tokens, updated_at)
                VALUES ('openclaw', ?, 'node-x', 'main', ?, ?, ?, 'completed', ?, ?)
                """,
                [sid, now_iso, now_iso, now_iso, tok, int(time.time() * 1000)],
            )
    store.persist_eval_score(session_id="a", score=5.0, reason="r", judge_model="m", scored_at=1, rubric="default")
    store.persist_eval_score(session_id="b", score=3.0, reason="r", judge_model="m", scored_at=2, rubric="default")
    store.persist_eval_score(session_id="c", score=4.0, reason="r", judge_model="m", scored_at=3, rubric="default")
    summary = store.query_eval_summary(window_hours=24 * 365)
    assert summary["scored"] == 3
    assert summary["total"] == 3
    assert summary["avg_score"] == pytest.approx(4.0)
    # quantiles depend on duckdb's continuous interpolation; just sanity-check bounds.
    assert 3.0 <= summary["p50"] <= 5.0
    assert 3.0 <= summary["p10"] <= 5.0


# ── Bug-class gate: real v3 event shape extraction ─────────────────────────


def test_runner_extracts_v3_prompt_submitted_and_model_completed():
    """Bug-class gate per ``feedback_synthetic_tests_missed_real_event_shape``.
    Runner MUST handle ``prompt.submitted`` (v3) and ``model.completed``
    (v3) shapes — earlier ClawMetry fast-paths silently returned zeros
    because they only knew the synthetic ``message`` shape.
    """
    store = _FakeStore(_events_v3_shape())
    runner = EvalRunner(store=store)
    captured = {}
    def _capturing_judge(model, prompt, *, timeout):
        captured["prompt"] = prompt
        return "SCORE: 5\nREASON: ok"
    res = runner.score_session("s-1", judge_call=_capturing_judge)
    assert res is not None and res.score == 5.0
    # The judge prompt must include BOTH the user input (from
    # prompt.submitted.finalPromptText) and the model output (from
    # model.completed.output) — proving the v3 extractor works.
    assert "haiku about Rust" in captured["prompt"]
    assert "Borrow checker" in captured["prompt"]


# ── Env-switch disable ──────────────────────────────────────────────────────


def test_disabled_env_var_short_circuits(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_EVALS_ENABLED", "0")
    store = _FakeStore(_events_v3_shape())
    runner = EvalRunner(store=store)
    res = runner.score_session(
        "s-1",
        judge_call=lambda *a, **kw: "SCORE: 5\nREASON: x",
    )
    assert res is None
    assert store.persisted == []
    assert eval_runner.is_enabled() is False


def test_enabled_by_default_when_env_unset(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_EVALS_ENABLED", raising=False)
    assert eval_runner.is_enabled() is True


# ── Live-API smoke (gated on CI_ANTHROPIC_API_KEY) ─────────────────────────


@pytest.mark.skipif(
    not os.environ.get("CI_ANTHROPIC_API_KEY"),
    reason="CI_ANTHROPIC_API_KEY not set — skipping live judge call",
)
def test_live_haiku_judge_round_trip(monkeypatch):
    """End-to-end test against the real Anthropic Haiku endpoint. Gated
    behind CI_ANTHROPIC_API_KEY so push-CI doesn't burn credits."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", os.environ["CI_ANTHROPIC_API_KEY"])
    store = _FakeStore(_events_v3_shape())
    runner = EvalRunner(store=store)
    res = runner.score_session("s-1")
    assert res is not None
    # A live Haiku run on the canned haiku above should produce a numeric
    # score; tolerate any value in band rather than asserting equality.
    if res.score is not None:
        assert 0.0 <= res.score <= 5.0
