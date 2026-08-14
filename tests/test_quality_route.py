"""Tests for the Quality tab endpoint (routes/quality.py, redesigned Evals
surface, 2026-08-14). Covers the shape the frontend depends on, the honest
empty envelope, the grade computation on a real-shape row set, and the
POST /api/quality/checks persistence hop."""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest
from flask import Flask


def _make_app():
    from routes.quality import bp_quality
    app = Flask(__name__)
    app.register_blueprint(bp_quality)
    return app


def _stub_store(monkeypatch, rows_by_agent_type):
    """Replace _store_via_daemon_or_direct with a fake that serves the
    given rows per agent_type. Rows are session dicts; missing agents
    return an empty list. query_recent_evals returns []."""
    from routes import quality as quality_module

    def _fake(method_name, **kwargs):
        if method_name == "query_outcomes":
            at = kwargs.get("agent_type")
            return list(rows_by_agent_type.get(at, []))
        if method_name == "query_recent_evals":
            # Not exercising judge-blend here; keep it empty so the score
            # comes purely from outcome (the deterministic path).
            return []
        return None

    monkeypatch.setattr(quality_module, "_store_via_daemon_or_direct", _fake)


def test_empty_envelope_on_no_rows(monkeypatch):
    _stub_store(monkeypatch, {})
    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/quality/report-card?window=7d")
        assert r.status_code == 200
        body = r.get_json()
        # Honest empty shape — every key the UI reads is present.
        for key in ("grade", "headline", "subline", "patterns",
                    "rough_runs", "week", "graded_runs", "total_runs",
                    "judge_key_set", "window_hours"):
            assert key in body, f"missing key {key!r}"
        assert body["grade"] == "—"
        assert body["graded_runs"] == 0
        assert body["patterns"] == []
        assert body["rough_runs"] == []
        assert "nothing to grade" in body["headline"].lower()


def test_grade_reflects_outcome_mix(monkeypatch):
    """A mix of successes + one failure yields a grade below A but not F,
    and the rough run surfaces with a plain-English story."""
    rows = [
        {"session_id": "s1", "agent_type": "claude_code",
         "title": "add unit tests", "outcome": "success",
         "cost_usd": 0.10, "started_at": "2026-08-14T09:00:00Z",
         "ended_at":   "2026-08-14T09:01:00Z"},
        {"session_id": "s2", "agent_type": "claude_code",
         "title": "refactor middleware", "outcome": "success",
         "cost_usd": 0.05, "started_at": "2026-08-14T09:02:00Z",
         "ended_at":   "2026-08-14T09:03:00Z"},
        {"session_id": "s3", "agent_type": "claude_code",
         "title": "debug the E2E", "outcome": "tool_call_stuck",
         "cost_usd": 0.90, "started_at": "2026-08-14T09:10:00Z",
         "ended_at":   "2026-08-14T09:20:00Z"},
    ]
    _stub_store(monkeypatch, {"claude_code": rows})
    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/quality/report-card").get_json()
    # 2/3 successes → grade should be B or C (score = ~0.67)
    assert body["grade"] in {"B", "C"}, body["grade"]
    assert body["success_runs"] == 2
    assert body["rough_runs_n"] == 1
    # The rough run row is human-scannable, no bare hash.
    assert body["rough_runs"], body
    rr = body["rough_runs"][0]
    assert rr["title"] == "debug the E2E"
    assert "stuck" in rr["story"].lower()
    # Patterns aggregate the failure and carry a $ cost.
    assert body["patterns"]
    top = body["patterns"][0]
    assert top["count"] == 1
    assert "stuck" in top["label"].lower()
    assert top["cost_display"].startswith("$")


def test_headline_matches_all_clean(monkeypatch):
    """When every run succeeds, the subline says 'No rough ones.'"""
    rows = [
        {"session_id": f"s{i}", "agent_type": "claude_code",
         "title": f"task {i}", "outcome": "success", "cost_usd": 0.01}
        for i in range(5)
    ]
    _stub_store(monkeypatch, {"claude_code": rows})
    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/quality/report-card").get_json()
    assert body["grade"] == "A"
    assert body["rough_runs_n"] == 0
    assert "no rough" in body["subline"].lower()


def test_week_bucket_shape(monkeypatch):
    """The `week` array is at most 7 items, each with grade + label + runs
    fields so the UI can render the day dots without a crash."""
    _stub_store(monkeypatch, {})
    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/quality/report-card?window=7d").get_json()
    assert isinstance(body["week"], list)
    assert 1 <= len(body["week"]) <= 7
    for day in body["week"]:
        assert "date" in day and "label" in day and "grade" in day and "runs" in day


def test_checks_post_requires_fail_when(monkeypatch):
    app = _make_app()
    with app.test_client() as c:
        r = c.post("/api/quality/checks", json={"name": "x"})
        assert r.status_code == 400
        assert "fail_when" in r.get_json()["error"]


def test_checks_post_persists_to_jsonl(monkeypatch, tmp_path):
    """A valid save appends a JSONL record to ~/.clawmetry/quality_checks.jsonl
    and returns {ok: true, id, deferred_enforcement: true}."""
    monkeypatch.setenv("HOME", str(tmp_path))
    app = _make_app()
    with app.test_client() as c:
        r = c.post("/api/quality/checks", json={
            "session_id": "claude_code:abc",
            "name":       "Tool loop guard",
            "fail_when":  "the same tool errors more than 3 times",
        })
        assert r.status_code == 200
        body = r.get_json()
        assert body["ok"] is True
        assert body["deferred_enforcement"] is True
        assert isinstance(body["id"], str) and len(body["id"]) >= 8

    saved = tmp_path / ".clawmetry" / "quality_checks.jsonl"
    assert saved.exists()
    line = saved.read_text().strip().splitlines()[0]
    rec = json.loads(line)
    assert rec["name"] == "Tool loop guard"
    assert rec["source_session_id"] == "claude_code:abc"
    assert rec["deferred_enforcement"] is True


def test_pattern_labels_have_no_ml_jargon():
    """Guard: the plain-English pattern labels never use ML jargon like
    'eval', 'rubric', 'judge', 'metric'. That was the vaporbox smell the
    2026-08-14 redesign fixed."""
    from clawmetry.quality import _PATTERN_LABEL
    banned = ("eval", "rubric", "judge", "metric", "score")
    for lbl in _PATTERN_LABEL.values():
        lo = lbl.lower()
        for word in banned:
            assert word not in lo, f"pattern label leaks ML jargon: {lbl!r}"


def test_story_never_blank():
    """Guard: story_for always returns a non-empty string, even on a row
    with no outcome + no judge reason. The rough-runs list can't render
    a blank story cell."""
    from clawmetry.quality import story_for
    assert story_for({}).strip()
    assert story_for({"outcome": "unknown"}).strip()
