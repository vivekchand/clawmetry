"""Insights improve loop: templates that read ``sessions.outcome`` and the
judge's ``eval_score`` / ``eval_reason`` (they never did before).

Runs the three new templates against a real temp DuckDB with seeded sessions
so the SQL is proven, not just validated.
"""
from __future__ import annotations

import datetime
import importlib
import json
import os
import sys
import time

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

NEW_KEYS = ("top_failure_reasons", "intent_unmet", "eval_score_trend")


@pytest.fixture
def fresh(tmp_path, monkeypatch):
    pytest.importorskip("duckdb")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "t.duckdb"))
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path))
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    from pathlib import Path
    monkeypatch.setattr(ls, "DB_PATH", Path(str(tmp_path / "t.duckdb")))
    monkeypatch.setattr(ls, "_writer_owner", True)
    store = ls.get_store()
    sys.modules.pop("clawmetry.insights", None)
    import clawmetry.insights as ins
    importlib.reload(ins)
    yield store, ins
    try:
        store.stop(flush=False)
    except Exception:
        pass


def _seed(store):
    now = datetime.datetime.utcnow()
    now_ms = int(time.time() * 1000)
    rows = [
        # runtime, outcome, eval_score, eval_reason, days_ago
        ("claude_code:a1", "failed", 1.0, "Ignored the second half of the ask", 1),
        ("claude_code:a2", "failed", 2.0, "Wrong file edited", 2),
        ("claude_code:a3", "tool_call_stuck", None, None, 3),
        ("codex:b1", "cognitive_loop", 4.5, "Good", 1),
        ("codex:b2", "success", 5.0, "Great", 1),
        ("oc-legacy", "failed", None, None, 20),  # outside the 7d window
    ]
    with store._write_lock:
        for sid, outcome, score, reason, days in rows:
            la = (now - datetime.timedelta(days=days)).isoformat()
            scored_at = now_ms - days * 86400 * 1000 if score is not None else None
            store._conn.execute(
                "INSERT INTO sessions (agent_type, session_id, title, started_at, "
                "last_active_at, cost_usd, updated_at, outcome, eval_score, "
                "eval_reason, eval_scored_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                ["openclaw", sid, f"task {sid}", la, la, 1.5, now_ms, outcome,
                 score, reason, scored_at])


def test_new_templates_exist_and_pass_sql_safety(fresh):
    _, ins = fresh
    keys = [k for k, *_ in ins._INSIGHT_TEMPLATES]
    for k in NEW_KEYS:
        assert k in keys
    from clawmetry.dives_sql_safety import validate_sql
    for key, _t, sql, _h in ins._INSIGHT_TEMPLATES:
        if key not in NEW_KEYS:
            continue
        sanitized = (sql.replace("$since_ms", "1700000000000")
                        .replace("$trend_since_ms", "1700000000000")
                        .replace("$since", "'2026-01-01T00:00:00Z'"))
        ok, reason = validate_sql(sanitized)
        assert ok, f"{key}: {reason}"


def test_titles_speak_to_a_newcomer(fresh):
    _, ins = fresh
    titles = {k: t for k, t, *_ in ins._INSIGHT_TEMPLATES}
    assert titles["top_failure_reasons"] == "Why sessions failed this week"
    for k in NEW_KEYS:
        assert "—" not in titles[k] and "--" not in titles[k]
        assert "eval_score" not in titles[k].lower()


def test_top_failure_reasons_groups_by_runtime_and_outcome(fresh):
    store, ins = fresh
    _seed(store)
    digest = ins.WeeklyDigestGenerator({"enabled": True, "anthropic_api_key": ""}).generate()
    by_key = {i.key: i for i in digest.insights}
    rows = by_key["top_failure_reasons"].rows
    got = {(r["runtime"], r["outcome"]): r["sessions"] for r in rows}
    assert got[("claude_code", "failed")] == 2
    assert got[("claude_code", "tool_call_stuck")] == 1
    assert got[("codex", "cognitive_loop")] == 1
    assert ("codex", "success") not in got
    assert ("openclaw", "failed") not in got  # 20 days old: outside the week


def test_intent_unmet_lists_low_scores_with_reasons(fresh):
    store, ins = fresh
    _seed(store)
    digest = ins.WeeklyDigestGenerator({"enabled": True, "anthropic_api_key": ""}).generate()
    rows = {i.key: i.rows for i in digest.insights}["intent_unmet"]
    assert [r["session_id"] for r in rows] == ["claude_code:a1", "claude_code:a2"]
    assert rows[0]["why"] == "Ignored the second half of the ask"
    assert rows[0]["score"] == 1.0 and rows[0]["asked"] == "task claude_code:a1"


def test_eval_score_trend_is_a_weekly_mean(fresh):
    store, ins = fresh
    _seed(store)
    digest = ins.WeeklyDigestGenerator({"enabled": True, "anthropic_api_key": ""}).generate()
    rows = {i.key: i.rows for i in digest.insights}["eval_score_trend"]
    assert rows, "scored sessions this week must produce at least one week bucket"
    total = sum(r["scored_sessions"] for r in rows)
    assert total == 4
    weighted = sum(r["mean_score"] * r["scored_sessions"] for r in rows) / total
    assert abs(weighted - (1.0 + 2.0 + 4.5 + 5.0) / 4) < 0.05
    for r in rows:
        datetime.date.fromisoformat(r["week"])  # ISO week start, renderable


def test_empty_store_yields_empty_rows_not_errors(fresh):
    _, ins = fresh
    digest = ins.WeeklyDigestGenerator({"enabled": True, "anthropic_api_key": ""}).generate()
    for i in digest.insights:
        if i.key in NEW_KEYS:
            assert i.rows == [] and i.error is None
    json.dumps(digest.to_dict())
