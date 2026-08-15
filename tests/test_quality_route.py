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


def _stub_store(monkeypatch, rows_by_agent_type, events_by_session=None):
    """Replace _store_via_daemon_or_direct with a fake store.

    The endpoint no longer sweeps agent_type (that column is hardcoded to
    "openclaw" for every row, which is what made the old surface report the
    wrong runtime for everyone). It reads query_quality_sessions, scoped by
    the real runtime, so the stub is keyed by runtime and each row carries a
    metadata blob the way the daemon writes it.
    """
    from routes import quality as quality_module

    events_by_session = events_by_session or {}

    def _fake(method_name, **kwargs):
        if method_name == "query_quality_sessions":
            want = kwargs.get("runtime")
            out = []
            for rt, rows in rows_by_agent_type.items():
                if want and want != rt:
                    continue
                for r in rows:
                    r = dict(r)
                    r.setdefault("runtime", rt)
                    r.setdefault("metadata", {})
                    out.append(r)
            # until= marks the "prior window" read; keep it empty so vs_prior
            # stays None rather than comparing a window against itself.
            return [] if kwargs.get("until") else out
        if method_name == "query_events":
            return list(events_by_session.get(kwargs.get("session_id"), []))
        if method_name == "query_recent_evals":
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


def _tool_call(ts, tool, inp):
    return {"event_type": "tool_call", "ts": ts,
            "data": {"role": "assistant", "content": "", "_runtime": "claude_code",
                     "tool_calls": [{"name": tool, "input": inp}], "tool_name": tool}}


def _tool_result(ts, err=False, text="ok"):
    return {"event_type": "tool_result", "ts": ts,
            "data": {"role": "user", "content": text, "_runtime": "claude_code",
                     "extra": {"isError": bool(err)}}}


def _clean_events(n=14):
    """A session doing varied, successful work."""
    out, t = [], 1_780_000_000
    for i in range(n):
        out.append(_tool_call(t, ["Bash", "Read", "Edit", "Grep"][i % 4],
                              {"file_path": "/repo/f%d.py" % i}))
        out.append(_tool_result(t + 1))
        t += 20
    return out


def _failing_events(n=14):
    """A session whose tools keep really failing."""
    out, t = [], 1_780_000_000
    for _ in range(n):
        out.append(_tool_call(t, "Bash", {"command": "flaky"}))
        out.append(_tool_result(t + 1, err=True, text="boom"))
        t += 20
    return out


def test_grade_reflects_evidence_mix(monkeypatch):
    """Two clean sessions plus one that really failed lands below A, and the
    rough run surfaces with plain-English copy AND inspectable evidence.

    Rewritten 2026-08-15: the old version drove this from a hand-set
    ``outcome`` enum. Grading is now derived from the session's real events,
    so the fixture supplies events and the verdict has to earn itself.
    """
    rows = [
        {"session_id": "s1", "title": "add unit tests", "cost_usd": 0.10,
         "started_at": "2026-08-14T09:00:00Z", "ended_at": "2026-08-14T09:01:00Z"},
        {"session_id": "s2", "title": "refactor middleware", "cost_usd": 0.05,
         "started_at": "2026-08-14T09:02:00Z", "ended_at": "2026-08-14T09:03:00Z"},
        {"session_id": "s3", "title": "debug the E2E", "cost_usd": 0.90,
         "started_at": "2026-08-14T09:10:00Z", "ended_at": "2026-08-14T09:20:00Z"},
    ]
    _stub_store(monkeypatch, {"claude_code": rows}, events_by_session={
        "s1": _clean_events(), "s2": _clean_events(), "s3": _failing_events(),
    })
    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/quality/report-card").get_json()

    assert body["success_runs"] == 2, body
    assert body["rough_runs_n"] == 1, body
    assert body["grade"] in {"B", "C", "D", "F"}, body["grade"]

    rr = body["rough_runs"][0]
    assert rr["title"] == "debug the E2E"
    assert rr["story"].strip()
    # The runtime is the session's real runtime, never a loop variable.
    assert rr["runtime"] == "claude_code", rr

    # THE contract: the claim ships with the evidence for it.
    assert rr["verdicts"], "a rough run must carry at least one verdict"
    ev = rr["verdicts"][0]["evidence"]
    assert ev["exhibits"], "a verdict without exhibits must never render"
    assert ev["observed"] and ev["threshold"]
    assert 0.0 < rr["verdicts"][0]["confidence"] <= 1.0

    assert body["patterns"] and body["patterns"][0]["cost_display"].startswith("$")


def test_headline_matches_all_clean(monkeypatch):
    """When nothing is flagged, the subline says so plainly."""
    rows = [{"session_id": "s%d" % i, "title": "task %d" % i, "cost_usd": 0.01}
            for i in range(5)]
    _stub_store(monkeypatch, {"claude_code": rows},
                events_by_session={"s%d" % i: _clean_events() for i in range(5)})
    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/quality/report-card").get_json()
    assert body["grade"] == "A", body
    assert body["rough_runs_n"] == 0
    assert "nothing rough" in body["subline"].lower(), body["subline"]


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
    """Guard: user-facing copy never leaks ML jargon or internal signal ids.

    Widened 2026-08-15 to cover the per-session stories too, since the rough
    run list renders them straight to the user.
    """
    from clawmetry.quality import _VERDICT_COPY
    banned = ("eval", "rubric", "judge", "metric", "score", "_")
    for name, copy in _VERDICT_COPY.items():
        for field in ("label", "story"):
            lo = copy[field].lower()
            for word in banned:
                assert word not in lo, (
                    "%s.%s leaks jargon (%r): %r" % (name, field, word, copy[field])
                )


def test_story_never_blank():
    """Guard: story_for always returns a non-empty string, even on a row
    with no outcome + no judge reason. The rough-runs list can't render
    a blank story cell."""
    from clawmetry.quality import story_for
    assert story_for({}).strip()
    assert story_for({"outcome": "unknown"}).strip()


def test_store_unreachable_says_so_instead_of_nothing_to_grade(monkeypatch):
    """A store that cannot be reached must NOT read as "nothing to grade".

    FLYWHEEL cloud-parity gate: the hosted dashboard has no local DuckDB, so
    this path is what a trial user sees. Reporting an empty week for a machine
    that is working fine is a wrong answer dressed as an empty state.
    """
    from routes import quality as quality_module
    monkeypatch.setattr(quality_module, "_store_via_daemon_or_direct",
                        lambda *a, **k: None)
    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/quality/report-card").get_json()
    assert body["store_available"] is False
    assert "nothing to grade" not in body["headline"].lower()
    assert "your own machine" in body["headline"].lower()
    assert body["rough_runs"] == []


def test_empty_store_still_reads_as_nothing_to_grade(monkeypatch):
    """The other half of the distinction: a store that answers with no rows
    genuinely has nothing to grade, and must say that."""
    _stub_store(monkeypatch, {})
    app = _make_app()
    with app.test_client() as c:
        body = c.get("/api/quality/report-card").get_json()
    assert body["store_available"] is True
    assert "nothing to grade" in body["headline"].lower()


def test_excluded_sessions_report_the_right_reason(monkeypatch):
    """"Not graded yet" must not be reported as "too little activity".

    The first is a fact about us, the second a fact about the session.
    Collapsing them tells the user their work was too thin when the truth is
    the collector hasn't caught up — wrong, and reassuring in the wrong
    direction, which is the species of copy this rebuild exists to remove.
    """
    from clawmetry.quality import compute_report_card

    rows = [{"session_id": "s%d" % i, "title": "t%d" % i, "cost_usd": 1.0}
            for i in range(6)]

    def unmeasured(reason):
        return {"measurable": False, "reason": reason, "verdicts": []}

    assessments = {
        "s0": {"measurable": True, "verdicts": []},
        "s1": {"measurable": True, "verdicts": []},
        "s2": unmeasured("Too little activity to judge — 3 events, 0 tool results."),
        "s3": unmeasured("Too little activity to judge — 2 events, 0 tool results."),
        "s4": unmeasured("Not graded yet — the collector will pick this up."),
        "s5": unmeasured("Not graded yet — the collector will pick this up."),
    }
    sub = compute_report_card(rows, assessments)["subline"]
    assert "2 more had too little activity" in sub, sub
    assert "2 are still being graded" in sub, sub

    # All-thin must not invent a "still being graded" clause.
    all_thin = dict(assessments)
    for k in ("s4", "s5"):
        all_thin[k] = unmeasured("Too little activity to judge — 1 events, 0 tool results.")
    sub2 = compute_report_card(rows, all_thin)["subline"]
    assert "still being graded" not in sub2, sub2
    assert "4 more had too little activity" in sub2, sub2
