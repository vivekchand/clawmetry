"""A question the agent asks can be answered from anywhere, not just approved.

Claude Code's AskUserQuestion is parked by the gate hook as a question-set
approval (clawmetry/question_sets.py). Until now only the local Approvals tab
knew that: the snapshot's ``deviceSummary.approval`` carried no questions, so
the cloud strip and the desk device offered Approve/Deny, which cannot answer
a question at all. Burned 2026-09-11: "Was that intentional?" with three
options showed up on the cloud strip as Approve / Deny, 2h38m after the
terminal had already taken it over.

Covers:
  * the snapshot carries the question set and the window's end;
  * a request past its window is not offered (its waiter is gone);
  * ``expire_stale_approvals`` retires such rows, and only those;
  * a cloud-relayed ``answer`` (sealed with the node key) lands as an
    ``answered`` row the waiting hook turns into updatedInput; a wrong
    label or an unreadable seal leaves the row pending (the terminal takes
    over at the deadline, never a fabricated answer).
"""

from __future__ import annotations

import base64
import importlib
import json
import os
import time

import pytest

QUESTION = "PR #5869 was closed by your account. Was that intentional?"
QUESTIONS = [{
    "question": QUESTION,
    "header": "PR #5869",
    "multiSelect": False,
    "options": [
        {"label": "Reopen and ship it", "description": "Not intentional."},
        {"label": "Intentional: don't release", "description": "Leave it closed."},
        {"label": "Split it up", "description": "Separate PRs."},
    ],
}]


@pytest.fixture
def sync_with_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()

    import clawmetry.sync as sync
    importlib.reload(sync)
    yield sync, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _park(store, approval_id, *, deadline_ms, questions=QUESTIONS,
          created_at="2026-09-11T18:12:35Z"):
    args = {"tool_name": "AskUserQuestion", "deadline_ms": deadline_ms,
            "on_timeout": "ask", "tool_input": {"questions": questions}}
    if questions:
        args["_cm_questions"] = questions
    store.ingest_approval({
        "id": approval_id, "requestor_session_id": "claude_code:s1",
        "action": "AskUserQuestion: 1 question — PR #5869",
        "args": args, "status": "pending", "created_at": created_at,
    })


def _row(store, approval_id):
    return next(r for r in store.query_approvals(limit=50)
                if r.get("id") == approval_id)


def _now_ms():
    return int(time.time() * 1000)


# ── snapshot ────────────────────────────────────────────────────────────────

def test_snapshot_carries_the_questions_and_the_window(sync_with_store):
    sync, ls = sync_with_store
    store = ls.get_store()
    deadline = _now_ms() + 150_000
    _park(store, "q1", deadline_ms=deadline)
    ap = sync._build_device_summary({}, {})["approval"]
    assert ap["id"] == "q1"
    assert ap["kind"] == "question_set"
    assert ap["deadline_ms"] == deadline
    (q,) = ap["questions"]
    assert q["question"] == QUESTION and q["header"] == "PR #5869"
    assert [o["label"] for o in q["options"]] == [
        "Reopen and ship it", "Intentional: don't release", "Split it up"]
    assert q["multiSelect"] is False


def test_a_yes_no_approval_carries_no_questions(sync_with_store):
    sync, ls = sync_with_store
    store = ls.get_store()
    _park(store, "b1", deadline_ms=_now_ms() + 60_000, questions=None)
    ap = sync._build_device_summary({}, {})["approval"]
    assert ap["id"] == "b1"
    assert "questions" not in ap and "kind" not in ap


def test_a_request_past_its_window_is_not_offered(sync_with_store):
    sync, ls = sync_with_store
    store = ls.get_store()
    _park(store, "dead", deadline_ms=_now_ms() - 1000,
          created_at="2026-09-11T18:00:00Z")
    assert sync._build_device_summary({}, {})["approval"] is None
    # A live one behind it is still offered.
    _park(store, "live", deadline_ms=_now_ms() + 60_000,
          created_at="2026-09-11T18:05:00Z")
    assert sync._build_device_summary({}, {})["approval"]["id"] == "live"


# ── sweep ───────────────────────────────────────────────────────────────────

def test_sweep_expires_only_rows_whose_waiter_is_gone(sync_with_store):
    _sync, ls = sync_with_store
    store = ls.get_store()
    _park(store, "gone", deadline_ms=_now_ms() - 10 * 60_000)
    _park(store, "in_grace", deadline_ms=_now_ms() - 10_000)
    _park(store, "open", deadline_ms=_now_ms() + 60_000)
    store.ingest_approval({"id": "no_deadline", "action": "exec",
                           "args": {"command": "ls"}, "status": "pending"})
    assert store.expire_stale_approvals(grace_seconds=120) == 1
    assert _row(store, "gone")["status"] == "expired"
    assert _row(store, "gone")["resolver"] == "sweep"
    for aid in ("in_grace", "open", "no_deadline"):
        assert _row(store, aid)["status"] == "pending", aid


# ── relayed answers ─────────────────────────────────────────────────────────

def _key():
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


def _relay(sync, monkeypatch, key, answers=None, sealed=None):
    monkeypatch.setattr(sync, "load_config", lambda: {"encryption_key": key})
    if sealed is None:
        sealed = sync.encrypt_payload({"answers": answers}, key)
    sync._apply_approval_decision({
        "type": "approval_decision", "id": "q1", "decision": "answer",
        "sealed_answers": sealed, "resolver": "dashboard:abcd1234",
    })


def test_a_sealed_answer_lands_as_answered(sync_with_store, monkeypatch):
    sync, ls = sync_with_store
    store = ls.get_store()
    _park(store, "q1", deadline_ms=_now_ms() + 60_000)
    _relay(sync, monkeypatch, _key(), {QUESTION: "Reopen and ship it"})
    row = _row(store, "q1")
    assert row["status"] == "answered"
    assert row["resolver"] == "dashboard:abcd1234"
    assert row["args"]["_cm_answers"] == {QUESTION: "Reopen and ship it"}
    # The hook's reply is built from exactly this row.
    from clawmetry import question_sets as qsets
    assert qsets.validate_answers(row["args"]["_cm_questions"],
                                  row["args"]["_cm_answers"]) is None


def test_a_label_that_is_not_an_option_is_rejected(sync_with_store, monkeypatch):
    sync, ls = sync_with_store
    store = ls.get_store()
    _park(store, "q1", deadline_ms=_now_ms() + 60_000)
    _relay(sync, monkeypatch, _key(), {QUESTION: "Delete the repo"})
    assert _row(store, "q1")["status"] == "pending"


def test_an_answer_sealed_with_another_key_is_ignored(sync_with_store, monkeypatch):
    sync, ls = sync_with_store
    store = ls.get_store()
    _park(store, "q1", deadline_ms=_now_ms() + 60_000)
    wrong = sync.encrypt_payload({"answers": {QUESTION: "Split it up"}}, _key())
    _relay(sync, monkeypatch, _key(), sealed=wrong)
    row = _row(store, "q1")
    assert row["status"] == "pending"
    assert "_cm_answers" not in row["args"]


def test_browser_style_unpadded_seal_is_readable(sync_with_store, monkeypatch):
    """The cloud strip seals with WebCrypto and strips base64 padding."""
    sync, ls = sync_with_store
    store = ls.get_store()
    _park(store, "q1", deadline_ms=_now_ms() + 60_000)
    key = _key()
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    iv = os.urandom(12)
    ct = AESGCM(base64.urlsafe_b64decode(key)).encrypt(
        iv, json.dumps({"answers": {QUESTION: "Split it up"}}).encode(), None)
    sealed = base64.urlsafe_b64encode(iv + ct).decode().rstrip("=")
    _relay(sync, monkeypatch, key, sealed=sealed)
    assert _row(store, "q1")["status"] == "answered"


def test_an_answer_after_the_window_changes_nothing(sync_with_store, monkeypatch):
    sync, ls = sync_with_store
    store = ls.get_store()
    _park(store, "q1", deadline_ms=_now_ms() - 10 * 60_000)
    store.expire_stale_approvals(grace_seconds=120)
    _relay(sync, monkeypatch, _key(), {QUESTION: "Reopen and ship it"})
    assert _row(store, "q1")["status"] == "expired"
