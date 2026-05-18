"""Tests for ``clawmetry.eval_suite_runner`` — Phase 2 evals (refs #1619).

Ten scenarios per the PRD:
  1. YAML loading (valid)
  2. YAML loading (missing required fields)
  3. YAML loading (invalid outcome enum)
  4. Suite execution: all tests pass
  5. Suite execution: one test fails (score below threshold)
  6. Suite execution: mixed (pass + missing-tools fail + judge-error)
  7. SuiteRun.exit_code matches outcomes
  8. CLI --list with no suites
  9. Persistence writes to a fake store with the right kwargs
 10. Watch mode re-runs on mtime change

These tests inject ``agent_call`` + ``judge_call`` callables so nothing
hits a network or a real subprocess. Mirrors the Phase 1 test pattern
(see tests/test_eval_runner.py) where the runner is exercised end-to-end
with a fake store and recorded judge replies.
"""
from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


from clawmetry import eval_suite_runner as esr  # noqa: E402
from clawmetry.eval_suite_runner import (  # noqa: E402
    AgentResponse,
    Suite,
    SuiteRun,
    TestCase,
    TestResult,
    format_table,
    load_suite,
    run_suite,
    watch_suite,
)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _write_suite(tmp_path: Path, body: str, name: str = "demo") -> Path:
    """Write ``body`` to ``tmp_path/<name>.yaml`` and return the path."""
    p = tmp_path / f"{name}.yaml"
    p.write_text(body, encoding="utf-8")
    return p


def _judge_score(score: float, reason: str = "ok"):
    """Build a fake judge_call that always returns the given score."""
    def _call(model, prompt, *, timeout=None):  # noqa: ARG001
        return f"SCORE: {score}\nREASON: {reason}"
    return _call


def _agent_ok(text: str = "done", tools=None, outcome: str = "success"):
    """Build a fake agent_call that always returns the same response."""
    def _call(_input: str):
        return AgentResponse(text=text, tools_used=list(tools or []), outcome=outcome)
    return _call


class _FakeStore:
    """In-memory stand-in for ``LocalStore.persist_eval_suite_run``."""
    def __init__(self):
        self.rows: list[dict] = []

    def persist_eval_suite_run(self, **kwargs):
        self.rows.append(kwargs)


_BASIC_SUITE = """\
suite: customer_support
judge_model: claude-haiku-4-5
tests:
  - name: refund
    input: "I need a refund"
    expected_tools: [lookup_order, refund]
    expected_outcome: success
    expected_min_score: 4
  - name: out_of_scope
    input: "Weather?"
    expected_tools: []
    expected_outcome: escalated
    expected_min_score: 3
"""


# ── 1. YAML loading — valid ──────────────────────────────────────────────────


def test_load_suite_parses_basic_yaml(tmp_path, monkeypatch):
    monkeypatch.setattr(esr, "SUITES_DIR", tmp_path)
    _write_suite(tmp_path, _BASIC_SUITE, name="customer_support")
    suite = load_suite("customer_support")
    assert suite.name == "customer_support"
    assert suite.judge_model == "claude-haiku-4-5"
    assert len(suite.tests) == 2
    assert suite.tests[0].name == "refund"
    assert suite.tests[0].expected_tools == ["lookup_order", "refund"]
    assert suite.tests[0].expected_outcome == "success"
    assert suite.tests[0].expected_min_score == 4.0
    assert suite.tests[1].expected_tools == []
    assert suite.tests[1].expected_outcome == "escalated"


# ── 2. YAML loading — missing required fields ─────────────────────────────────


def test_load_suite_rejects_missing_tests(tmp_path, monkeypatch):
    monkeypatch.setattr(esr, "SUITES_DIR", tmp_path)
    _write_suite(tmp_path, "suite: empty\njudge_model: claude-haiku-4-5\n", name="empty")
    with pytest.raises(ValueError, match="`tests:` list is required"):
        load_suite("empty")


def test_load_suite_rejects_test_without_name(tmp_path, monkeypatch):
    monkeypatch.setattr(esr, "SUITES_DIR", tmp_path)
    body = "suite: x\ntests:\n  - input: 'no name here'\n"
    _write_suite(tmp_path, body, name="noname")
    with pytest.raises(ValueError, match="missing required field `name`"):
        load_suite("noname")


def test_load_suite_rejects_missing_input(tmp_path, monkeypatch):
    monkeypatch.setattr(esr, "SUITES_DIR", tmp_path)
    body = "suite: x\ntests:\n  - name: only_name\n"
    _write_suite(tmp_path, body, name="noinput")
    with pytest.raises(ValueError, match="missing required field `input`"):
        load_suite("noinput")


def test_load_suite_missing_file_raises_helpful_error(tmp_path, monkeypatch):
    monkeypatch.setattr(esr, "SUITES_DIR", tmp_path)
    with pytest.raises(FileNotFoundError, match="no suite at"):
        load_suite("nonexistent")


# ── 3. YAML loading — invalid outcome enum ──────────────────────────────────


def test_load_suite_rejects_unknown_outcome(tmp_path, monkeypatch):
    monkeypatch.setattr(esr, "SUITES_DIR", tmp_path)
    body = (
        "suite: x\ntests:\n  - name: t1\n    input: 'hi'\n"
        "    expected_outcome: maybe_pass\n"
    )
    _write_suite(tmp_path, body, name="badoutcome")
    with pytest.raises(ValueError, match="expected_outcome"):
        load_suite("badoutcome")


# ── 4. Suite execution — all pass ─────────────────────────────────────────────


def test_run_suite_all_pass():
    suite = Suite(
        name="ok",
        judge_model="claude-haiku-4-5",
        tests=[
            TestCase(name="t1", input="hi", expected_tools=["search"],
                     expected_outcome="success", expected_min_score=4),
            TestCase(name="t2", input="hello", expected_tools=[],
                     expected_outcome="success", expected_min_score=3),
        ],
    )
    run = run_suite(
        suite,
        agent_call=_agent_ok(tools=["search"]),
        judge_call=_judge_score(5.0, "great"),
        persist=False,
    )
    assert run.passed == 2
    assert run.failed == 0
    assert run.exit_code == 0
    assert all(r.status == "pass" for r in run.results)


# ── 5. Suite execution — one fail (score below threshold) ─────────────────────


def test_run_suite_fail_score_below_threshold():
    suite = Suite(
        name="ok", judge_model="claude-haiku-4-5",
        tests=[TestCase(name="t1", input="hi", expected_tools=[],
                        expected_outcome="any", expected_min_score=4)],
    )
    run = run_suite(
        suite,
        agent_call=_agent_ok(),
        judge_call=_judge_score(2.0, "mediocre"),
        persist=False,
    )
    assert run.failed == 1
    assert run.results[0].status == "fail"
    assert "score 2.0" in run.results[0].reason
    assert run.exit_code == 1


# ── 6. Suite execution — mixed (pass + missing-tools + judge error) ──────────


def test_run_suite_mixed_outcomes():
    suite = Suite(
        name="mixed", judge_model="claude-haiku-4-5",
        tests=[
            TestCase(name="passes", input="a", expected_tools=["x"],
                     expected_outcome="any", expected_min_score=0),
            TestCase(name="missing_tool", input="b", expected_tools=["zzz"],
                     expected_outcome="any", expected_min_score=0),
            TestCase(name="judge_dead", input="c", expected_tools=[],
                     expected_outcome="any", expected_min_score=0),
        ],
    )

    def _agent(inp):
        return AgentResponse(text="done", tools_used=["x"], outcome="success")

    def _judge(model, prompt, *, timeout=None):
        if "ASSISTANT: done" in prompt and "USER: c" in prompt:
            raise RuntimeError("judge offline")
        return "SCORE: 5\nREASON: ok"

    run = run_suite(suite, agent_call=_agent, judge_call=_judge, persist=False)
    statuses = {r.name: r.status for r in run.results}
    assert statuses["passes"] == "pass"
    assert statuses["missing_tool"] == "fail"
    assert statuses["judge_dead"] == "error"
    # exit_code aggregates pass(0) + fail(1) + error(1) → 1
    assert run.exit_code == 1
    assert run.passed == 1
    assert run.failed == 2


# ── 7. SuiteRun.exit_code matches outcomes (regression guard for CI gate) ─────


def test_exit_code_zero_when_empty_passes_only():
    suite = Suite(
        name="s", judge_model="claude-haiku-4-5",
        tests=[TestCase(name="t", input="x", expected_tools=[],
                        expected_outcome="any", expected_min_score=0)],
    )
    run = run_suite(
        suite,
        agent_call=_agent_ok(),
        judge_call=_judge_score(3.0),
        persist=False,
    )
    assert run.exit_code == 0
    # Sanity: format_table doesn't raise and includes the summary line.
    out = format_table(run)
    assert "1 passed, 0 failed" in out


# ── 8. CLI --list with empty SUITES_DIR ──────────────────────────────────────


def test_list_suites_empty_when_dir_missing(tmp_path, monkeypatch):
    missing = tmp_path / "doesnotexist"
    monkeypatch.setattr(esr, "SUITES_DIR", missing)
    assert esr.list_suites() == []


def test_list_suites_returns_names(tmp_path, monkeypatch):
    monkeypatch.setattr(esr, "SUITES_DIR", tmp_path)
    _write_suite(tmp_path, _BASIC_SUITE, name="a_suite")
    _write_suite(tmp_path, _BASIC_SUITE, name="b_suite")
    names = esr.list_suites()
    assert names == ["a_suite", "b_suite"]


# ── 9. Persistence — fake store ──────────────────────────────────────────────


def test_persistence_writes_each_test_row():
    store = _FakeStore()
    suite = Suite(
        name="persist_check", judge_model="claude-haiku-4-5",
        tests=[
            TestCase(name="t1", input="a", expected_tools=[],
                     expected_outcome="any", expected_min_score=0),
            TestCase(name="t2", input="b", expected_tools=[],
                     expected_outcome="any", expected_min_score=0),
        ],
    )
    run = run_suite(
        suite,
        agent_call=_agent_ok(),
        judge_call=_judge_score(4.5, "fine"),
        store=store,
        persist=True,
    )
    assert len(store.rows) == 2
    for row, expected_name in zip(store.rows, ["t1", "t2"]):
        assert row["suite_name"] == "persist_check"
        assert row["test_name"] == expected_name
        assert row["status"] == "pass"
        assert row["score"] == 4.5
        assert row["reason"] == "fine"
        assert row["ran_at"] == run.ran_at
        # sha is best-effort — present (string) but may be empty in CI sandbox.
        assert isinstance(row["sha"], str)


# ── 10. Watch mode triggers on mtime change ──────────────────────────────────


def test_watch_mode_reruns_on_file_change(tmp_path, monkeypatch):
    monkeypatch.setattr(esr, "SUITES_DIR", tmp_path)
    path = _write_suite(tmp_path, _BASIC_SUITE, name="watched")

    fired: list[SuiteRun] = []

    def _on_run(run):
        fired.append(run)

    # First mutate the mtime BEFORE the second poll so the change is seen.
    def _mutate_in_background():
        time.sleep(0.05)
        # Re-write to bump mtime. Same body — we're testing change detection,
        # not parse correctness here.
        path.write_text(_BASIC_SUITE + "\n", encoding="utf-8")
        # Touch the future to guarantee a different mtime even on fast FS.
        future = time.time() + 1
        os.utime(path, (future, future))

    t = threading.Thread(target=_mutate_in_background, daemon=True)
    t.start()
    watch_suite(
        str(path),
        interval_secs=0.05,
        iterations=8,
        on_run=_on_run,
        agent_call=_agent_ok(),
        judge_call=_judge_score(5.0),
        persist=False,
    )
    t.join(timeout=2)
    # First poll always fires (new mtime vs sentinel None), then the
    # mutation triggers a second one.
    assert len(fired) >= 2, f"watch did not re-fire on mtime change, fired={len(fired)}"
    assert fired[0].suite_name == "customer_support"


# ── Bonus: DuckDB schema round-trip ──────────────────────────────────────────
# Verifies the eval_suite_runs table exists on a fresh local_store and that
# persist + query_recent_suite_runs round-trip correctly. Caught a missing
# DDL row early in dev; keeping it as a regression guard.


def test_local_store_eval_suite_runs_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "ls.duckdb"))
    try:
        from clawmetry import local_store
    except Exception as e:
        pytest.skip(f"local_store import failed: {e}")
    # Reset the singleton if the module is already loaded from a prior test.
    if hasattr(local_store, "_STORE"):
        local_store._STORE = None  # type: ignore[attr-defined]
    try:
        store = local_store.get_store()
    except Exception as e:
        pytest.skip(f"local_store.get_store failed: {e}")
    store.persist_eval_suite_run(
        suite_name="t",
        test_name="case1",
        status="pass",
        score=4.0,
        reason="great",
        ran_at=1700000000000,
        sha="abc123",
    )
    rows = store.query_recent_suite_runs(suite_name="t", limit=10)
    assert len(rows) == 1
    assert rows[0]["test_name"] == "case1"
    assert rows[0]["status"] == "pass"
    assert rows[0]["score"] == 4.0
    assert rows[0]["sha"] == "abc123"
