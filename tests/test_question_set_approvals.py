"""Question-set approvals — decisions beyond yes/no (WO-52, phase 1).

Approvals were strictly binary. Claude Code's ``AskUserQuestion`` tool is
the first non-binary source: its PreToolUse hook payload carries 1-4
structured questions, and the hook may answer with
``hookSpecificOutput.updatedInput`` = tool_input + ``answers`` so the
session resumes with the human's actual choices.

Pins, in order:

  1. ``clawmetry.question_sets`` — sanitize + strict answer validation
     (unknown label → error, unknown question → error, multiSelect arrays,
     free text only when the set says so).
  2. The local decision wall (``POST /api/approvals/<id>/decide``) —
     ``decision='answer'`` round-trip, 400s, first-click-wins, and the
     binary approve/deny regression.
  3. The HITL wall (``POST /api/hitl/decide``) — same ``answer`` decision,
     plus the binary reject regression.
  4. The gate receiver (``POST /api/hooks/claude-code/pretooluse``) —
     an AskUserQuestion call parks a question-set row; an answered row
     yields allow + updatedInput; expiry yields "ask" (the terminal
     prompt), NEVER the binary deny default, NEVER a fabricated answer.

Fixture shape follows ``tests/test_mirror_gate.py``: real tmp HOME +
isolated CLAWMETRY_LOCAL_STORE_PATH, ``clawmetry.local_store`` popped and
reloaded FIRST so every late import in the routes resolves against the
fresh module (the reload-stales-your-import trap), daemon proxy pinned
offline, one-second wait slices.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time

import pytest
from flask import Flask

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import question_sets as qsets  # noqa: E402


# ── fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH",
                       str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    yield ls
    try:
        ls.get_store().stop(flush=False)
    except Exception:
        pass


def _pin_entitlement(monkeypatch):
    import clawmetry.entitlements as ent
    e = ent.Entitlement(tier="pro", source="test", grace=False,
                        features=frozenset(("approval_queue",
                                            "approval_routing",
                                            "approval_mirror")),
                        runtimes=frozenset())
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)


@pytest.fixture
def app(fresh_store, monkeypatch, tmp_path):
    """One Flask app carrying all three surfaces under test: the hook
    receiver, the local decide wall, and the HITL wall."""
    _pin_entitlement(monkeypatch)
    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    import routes.hooks as rh
    monkeypatch.setattr(rh, "_WAIT_SLICE_S", 1.0)
    # _HITL_DIR is bound at import time from Path.home(); repin it to THIS
    # test's HOME so flag files land (and are asserted) in the right place.
    import routes.hitl as rhitl
    from pathlib import Path
    monkeypatch.setattr(rhitl, "_HITL_DIR",
                        Path(str(tmp_path)) / ".clawmetry" / "hitl")
    from routes.hooks import bp_hooks
    from routes.policy import bp_policy
    from routes.hitl import bp_hitl
    flask_app = Flask(__name__)
    flask_app.register_blueprint(bp_hooks)
    flask_app.register_blueprint(bp_policy)
    flask_app.register_blueprint(bp_hitl)
    return flask_app.test_client(), fresh_store


_QUESTIONS_INPUT = {
    "questions": [
        {"question": "Which database should the cache use?",
         "header": "Cache",
         "options": [{"label": "Redis", "description": "in-memory"},
                     {"label": "DuckDB", "description": "embedded"}],
         "multiSelect": False},
        {"question": "Which environments should this ship to?",
         "header": "Envs",
         "options": [{"label": "staging", "description": ""},
                     {"label": "prod", "description": ""},
                     {"label": "dev", "description": ""}],
         "multiSelect": True},
    ],
}

_GOOD_ANSWERS = {
    "Which database should the cache use?": "DuckDB",
    "Which environments should this ship to?": ["staging", "dev"],
}


def _seed_question_row(ls, row_id="q-row-1", session="claude_code:s1",
                       deadline_offset_ms=60_000):
    """Park a question-set row exactly the way the receiver does."""
    store = ls.get_store()
    questions = qsets.sanitize_question_set(_QUESTIONS_INPUT)
    store.ingest_approval({
        "id": row_id,
        "requestor_session_id": session,
        "action": f"AskUserQuestion: {qsets.question_summary(questions)}",
        "args": {
            "source": "pretooluse-hook",
            "runtime": "claude_code",
            "kind": "question_set",
            "tool_name": "AskUserQuestion",
            "tool_input": _QUESTIONS_INPUT,
            "policy": "AskUserQuestion",
            "on_timeout": "ask",
            "deadline_ms": int(time.time() * 1000) + deadline_offset_ms,
            "_cm_questions": questions,
        },
        "status": "pending",
        "created_at": "2026-08-30T00:00:00Z",
    })
    return store


def _row(store, row_id):
    return next((r for r in store.query_approvals(limit=50)
                 if r["id"] == row_id), None)


# ── 1. question_sets: sanitize + validation ────────────────────────────────


def test_sanitize_normalises_and_caps():
    qs = qsets.sanitize_question_set(_QUESTIONS_INPUT)
    assert len(qs) == 2
    assert qs[0]["question"] == "Which database should the cache use?"
    assert qs[0]["multiSelect"] is False
    assert [o["label"] for o in qs[1]["options"]] == ["staging", "prod",
                                                      "dev"]
    # Garbage shapes come back None (the receiver answers "ask").
    assert qsets.sanitize_question_set({}) is None
    assert qsets.sanitize_question_set({"questions": []}) is None
    assert qsets.sanitize_question_set({"questions": "nope"}) is None
    assert qsets.sanitize_question_set(None) is None
    # Question without text is skipped; options without labels dropped.
    qs2 = qsets.sanitize_question_set({"questions": [
        {"question": "", "options": [{"label": "x"}]},
        {"question": "ok?", "options": [{"label": ""}, {"label": "yes"},
                                        7]},
    ]})
    assert len(qs2) == 1
    assert qs2[0]["options"] == [{"label": "yes", "description": ""}]


def test_validate_answers_strictness():
    qs = qsets.sanitize_question_set(_QUESTIONS_INPUT)
    assert qsets.validate_answers(qs, _GOOD_ANSWERS) is None
    # Unknown option label → error.
    err = qsets.validate_answers(qs, {
        "Which database should the cache use?": "Postgres"})
    assert err and "unknown option" in err
    # Unknown question → error.
    err = qsets.validate_answers(qs, {"Wat?": "Redis"})
    assert err and "unknown question" in err
    # A list against a single-choice question → error.
    err = qsets.validate_answers(qs, {
        "Which database should the cache use?": ["Redis", "DuckDB"]})
    assert err and "single-choice" in err
    # Unknown label inside a multiSelect array → error.
    err = qsets.validate_answers(qs, {
        "Which environments should this ship to?": ["staging", "moon"]})
    assert err and "unknown option" in err
    # Empty / wrong-shape answer maps → error.
    assert qsets.validate_answers(qs, {}) is not None
    assert qsets.validate_answers(qs, "Redis") is not None
    assert qsets.validate_answers(qs, {
        "Which database should the cache use?": ""}) is not None


def test_free_text_only_when_the_set_says_so():
    with_free = qsets.sanitize_question_set({"questions": [
        {"question": "Name the branch?", "header": "Branch",
         "options": [{"label": "main"}, {"label": "dev"}],
         "allowFreeText": True},
    ]})
    assert with_free[0]["allow_free_text"] is True
    assert qsets.validate_answers(with_free,
                                  {"Name the branch?": "my-feature"}) is None
    without = qsets.sanitize_question_set({"questions": [
        {"question": "Name the branch?",
         "options": [{"label": "main"}, {"label": "dev"}]},
    ]})
    err = qsets.validate_answers(without, {"Name the branch?": "my-feature"})
    assert err and "unknown option" in err


def test_merge_answers_into_input_shape():
    updated = qsets.merge_answers_into_input(_QUESTIONS_INPUT, _GOOD_ANSWERS)
    assert updated["questions"] == _QUESTIONS_INPUT["questions"]
    assert updated["answers"] == _GOOD_ANSWERS
    # A fresh dict — the stored tool_input is never mutated.
    assert "answers" not in _QUESTIONS_INPUT


# ── 2. local decide wall: /api/approvals/<id>/decide ───────────────────────


def test_wall_answer_round_trip_multiselect(app):
    client, ls = app
    store = _seed_question_row(ls)
    r = client.post("/api/approvals/q-row-1/decide",
                    json={"decision": "answer", "answers": _GOOD_ANSWERS})
    assert r.status_code == 200
    assert r.get_json() == {"ok": True, "status": "answered"}
    row = _row(store, "q-row-1")
    assert row["status"] == "answered"
    assert row["decision"] == "answered"
    # Structured answers ride in args (multiSelect array round-trips).
    assert row["args"]["_cm_answers"] == _GOOD_ANSWERS
    # decision_reason carries the human-readable summary for the audit feed.
    assert "answered" in row["decision_reason"]


def test_wall_answer_unknown_label_is_400(app):
    client, ls = app
    store = _seed_question_row(ls)
    r = client.post("/api/approvals/q-row-1/decide",
                    json={"decision": "answer", "answers": {
                        "Which database should the cache use?": "Postgres"}})
    assert r.status_code == 400
    assert "unknown option" in r.get_json()["error"]
    # The row is untouched — a rejected answer decides nothing.
    assert _row(store, "q-row-1")["status"] == "pending"


def test_wall_answer_unknown_question_is_400(app):
    client, ls = app
    _seed_question_row(ls)
    r = client.post("/api/approvals/q-row-1/decide",
                    json={"decision": "answer",
                          "answers": {"Not a question": "Redis"}})
    assert r.status_code == 400
    assert "unknown question" in r.get_json()["error"]


def test_wall_answer_on_binary_row_is_400(app):
    client, ls = app
    ls.get_store().ingest_approval({
        "id": "bin-1", "requestor_session_id": "claude_code:s1",
        "action": "Bash: rm -rf /tmp/x",
        "args": {"source": "pretooluse-hook", "tool_name": "Bash",
                 "tool_input": {"command": "rm -rf /tmp/x"}},
        "status": "pending", "created_at": "2026-08-30T00:00:00Z"})
    r = client.post("/api/approvals/bin-1/decide",
                    json={"decision": "answer",
                          "answers": {"q": "a"}})
    assert r.status_code == 400
    assert "question-set" in r.get_json()["error"]


def test_wall_first_click_wins_on_structured_answers(app):
    client, ls = app
    store = _seed_question_row(ls)
    first = client.post("/api/approvals/q-row-1/decide",
                        json={"decision": "answer",
                              "answers": _GOOD_ANSWERS})
    assert first.get_json() == {"ok": True, "status": "answered"}
    # Second structured answer: idempotent, the first one stands.
    second = client.post("/api/approvals/q-row-1/decide",
                         json={"decision": "answer", "answers": {
                             "Which database should the cache use?":
                                 "Redis"}})
    assert second.status_code == 200
    assert second.get_json() == {"ok": True, "status": "answered",
                                 "already": True}
    assert _row(store, "q-row-1")["args"]["_cm_answers"] == _GOOD_ANSWERS
    # A late binary click doesn't overwrite the answers either.
    late = client.post("/api/approvals/q-row-1/decide",
                       json={"decision": "deny"})
    assert late.get_json() == {"ok": True, "status": "answered",
                               "already": True}


def test_wall_deny_beats_a_late_answer(app):
    client, ls = app
    _seed_question_row(ls)
    assert client.post("/api/approvals/q-row-1/decide",
                       json={"decision": "deny"}).status_code == 200
    late = client.post("/api/approvals/q-row-1/decide",
                       json={"decision": "answer",
                             "answers": _GOOD_ANSWERS})
    assert late.status_code == 200
    assert late.get_json() == {"ok": True, "status": "denied",
                               "already": True}


def test_wall_binary_regression(app):
    """Plain approve/deny rows behave exactly as before."""
    client, ls = app
    store = ls.get_store()
    for rid, decision, status in (("b-appr", "approve", "approved"),
                                  ("b-deny", "deny", "denied")):
        store.ingest_approval({
            "id": rid, "requestor_session_id": "claude_code:s1",
            "action": "Bash: ls",
            "args": {"source": "pretooluse-hook", "tool_name": "Bash",
                     "tool_input": {"command": "ls"}},
            "status": "pending", "created_at": "2026-08-30T00:00:00Z"})
        r = client.post(f"/api/approvals/{rid}/decide",
                        json={"decision": decision, "reason": "because"})
        assert r.status_code == 200
        assert r.get_json()["status"] == status
        assert _row(store, rid)["status"] == status
    # Unknown decision word still rejected.
    r = client.post("/api/approvals/b-appr/decide",
                    json={"decision": "maybe"})
    assert r.status_code == 400


def test_queue_payload_carries_the_question_set(app):
    client, ls = app
    _seed_question_row(ls)
    d = client.get("/api/approvals").get_json()
    row = next(a for a in d["approvals"] if a["id"] == "q-row-1")
    assert row["kind"] == "question_set"
    assert [q["question"] for q in row["questions"]] == [
        "Which database should the cache use?",
        "Which environments should this ship to?"]
    assert [o["label"] for o in row["questions"][0]["options"]] == [
        "Redis", "DuckDB"]


# ── 3. HITL wall: /api/hitl/decide ─────────────────────────────────────────


def _flag_session(client, sid="hitl-s1"):
    r = client.post("/api/hitl/flag", json={"session_id": sid,
                                            "reason": "loop suspected",
                                            "operator": "op"})
    assert r.status_code == 200
    return sid


def _attach_questions(ls, sid):
    store = ls.get_store()
    questions = qsets.sanitize_question_set(_QUESTIONS_INPUT)
    store.ingest_approval({
        "id": f"hitl_{sid}",
        "args": {"tool_input": _QUESTIONS_INPUT,
                 "_cm_questions": questions},
        "status": "pending",
    })
    return store


def test_hitl_answer_round_trip(app, tmp_path):
    client, ls = app
    sid = _flag_session(client)
    store = _attach_questions(ls, sid)
    r = client.post("/api/hitl/decide",
                    json={"session_id": sid, "decision": "answer",
                          "operator": "op", "answers": _GOOD_ANSWERS})
    assert r.status_code == 200
    assert r.get_json()["decision"] == "answer"
    row = _row(store, f"hitl_{sid}")
    assert row["status"] == "answered"
    assert row["args"]["_cm_answers"] == _GOOD_ANSWERS
    # The pause flag is lifted — an answer unblocks like an approve.
    assert not (tmp_path / ".clawmetry" / "hitl" / f"pause_{sid}").exists()


def test_hitl_answer_unknown_label_is_400_and_keeps_the_flag(app, tmp_path):
    client, ls = app
    sid = _flag_session(client, "hitl-s2")
    _attach_questions(ls, sid)
    r = client.post("/api/hitl/decide",
                    json={"session_id": sid, "decision": "answer",
                          "operator": "op", "answers": {
                              "Which database should the cache use?":
                                  "Postgres"}})
    assert r.status_code == 400
    assert (tmp_path / ".clawmetry" / "hitl" / f"pause_{sid}").exists()


def test_hitl_binary_regression(app, tmp_path):
    client, _ls = app
    sid = _flag_session(client, "hitl-s3")
    r = client.post("/api/hitl/decide",
                    json={"session_id": sid, "decision": "reject",
                          "operator": "op", "reason": "no"})
    assert r.status_code == 200
    assert r.get_json()["decision"] == "reject"
    assert not (tmp_path / ".clawmetry" / "hitl" / f"pause_{sid}").exists()
    # Unknown decision word still rejected.
    _flag_session(client, "hitl-s4")
    r = client.post("/api/hitl/decide",
                    json={"session_id": "hitl-s4", "decision": "maybe"})
    assert r.status_code == 400


# ── 4. the gate receiver ───────────────────────────────────────────────────


def _ask_event(**over):
    return {"tool_name": "AskUserQuestion",
            "tool_input": _QUESTIONS_INPUT,
            "session_id": "s1", "cwd": "/tmp", "tool_use_id": "tu-q1",
            **over}


def test_gate_parks_a_question_row_and_answer_yields_updated_input(app):
    """The end-to-end loop: park → pending → wall answers → allow +
    updatedInput carrying the structured answers."""
    client, ls = app
    first = client.post("/api/hooks/claude-code/pretooluse",
                        json=_ask_event()).get_json()
    assert first["status"] == "pending"
    aid = first["approval_id"]
    row = _row(ls.get_store(), aid)
    assert row["args"]["kind"] == "question_set"
    assert row["args"]["on_timeout"] == "ask"
    assert len(row["args"]["_cm_questions"]) == 2

    # The human answers through the real decision wall.
    r = client.post(f"/api/approvals/{aid}/decide",
                    json={"decision": "answer", "answers": _GOOD_ANSWERS})
    assert r.status_code == 200

    # The hook client re-POSTs with approval_id, like the real fast path.
    done = client.post("/api/hooks/claude-code/pretooluse",
                       json=_ask_event(approval_id=aid)).get_json()
    hso = done["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    assert hso["updatedInput"]["answers"] == _GOOD_ANSWERS
    assert hso["updatedInput"]["questions"] == _QUESTIONS_INPUT["questions"]


def test_gate_dedups_on_tool_use_id(app):
    client, ls = app
    client.post("/api/hooks/claude-code/pretooluse", json=_ask_event())
    client.post("/api/hooks/claude-code/pretooluse", json=_ask_event())
    rows = [r for r in ls.get_store().query_approvals(limit=50)
            if (r.get("args") or {}).get("kind") == "question_set"]
    assert len(rows) == 1


def test_gate_plain_approve_allows_without_updated_input(app):
    """Approve ('answer in the terminal') → allow with the input UNCHANGED,
    so Claude Code renders its own question UI."""
    client, ls = app
    first = client.post("/api/hooks/claude-code/pretooluse",
                        json=_ask_event()).get_json()
    aid = first["approval_id"]
    client.post(f"/api/approvals/{aid}/decide", json={"decision": "approve"})
    done = client.post("/api/hooks/claude-code/pretooluse",
                       json=_ask_event(approval_id=aid)).get_json()
    hso = done["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    assert "updatedInput" not in hso


def test_gate_deny_denies_with_reason(app):
    client, ls = app
    first = client.post("/api/hooks/claude-code/pretooluse",
                        json=_ask_event()).get_json()
    aid = first["approval_id"]
    client.post(f"/api/approvals/{aid}/decide",
                json={"decision": "deny", "reason": "not now"})
    done = client.post("/api/hooks/claude-code/pretooluse",
                       json=_ask_event(approval_id=aid)).get_json()
    assert done["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_gate_expiry_falls_back_to_ask_never_deny(app):
    """THE safety pin: an expired question-set approval answers "ask" (the
    terminal prompt takes over) — never the binary on_timeout=deny default,
    never a fabricated answer."""
    client, ls = app
    _seed_question_row(ls, row_id="q-exp", deadline_offset_ms=-1000)
    done = client.post("/api/hooks/claude-code/pretooluse",
                       json=_ask_event(approval_id="q-exp")).get_json()
    assert done["hookSpecificOutput"]["permissionDecision"] == "ask"
    # …and the row records the timeout, closing the loop for the queue.
    assert _row(ls.get_store(), "q-exp")["status"] == "timeout"


def test_gate_expired_status_falls_back_to_ask(app):
    """A question row someone else already marked 'expired' must also come
    back as "ask" — the binary path maps expired to deny."""
    client, ls = app
    store = _seed_question_row(ls, row_id="q-expired")
    store.ingest_approval({"id": "q-expired", "status": "expired"})
    done = client.post("/api/hooks/claude-code/pretooluse",
                       json=_ask_event(approval_id="q-expired")).get_json()
    assert done["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_gate_malformed_question_payload_asks(app):
    client, _ls = app
    done = client.post("/api/hooks/claude-code/pretooluse",
                       json=_ask_event(tool_input={"nope": 1})).get_json()
    assert done["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_gate_question_gate_env_kill_switch(app, monkeypatch):
    """CLAWMETRY_QUESTION_GATE=0 restores the pre-WO-52 behaviour: no
    policies match AskUserQuestion, so the receiver has no opinion."""
    client, _ls = app
    monkeypatch.setenv("CLAWMETRY_QUESTION_GATE", "0")
    done = client.post("/api/hooks/claude-code/pretooluse",
                       json=_ask_event()).get_json()
    assert done["hookSpecificOutput"]["permissionDecision"] == "allow"
    assert "updatedInput" not in done["hookSpecificOutput"]
