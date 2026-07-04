"""Regression tests for issue #3470.

`openclaw attach` (PR #96454) resumes an existing Gateway session via an
external harness.  The gateway stamps kind='attached' and/or an
externalHarness boolean on those session records.  Before this fix,
ClawMetry classified them identically to ordinary 'direct' sessions:
  - list_sessions() did not surface an externalHarness flag in extra
  - _infer_session_type() returned 'main' instead of 'attached'
"""

import clawmetry.adapters.openclaw as ocmod
from clawmetry.adapters.openclaw import OpenClawAdapter
from routes.sessions import _infer_session_type


class _FakeDash:
    def __init__(self, extra_fields=None):
        self._fields = extra_fields or {}

    def _get_sessions(self):
        record = {"sessionId": "sess-attach"}
        record.update(self._fields)
        return [record]


def test_list_sessions_sets_external_harness_when_kind_attached(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash({"kind": "attached"}))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert len(sessions) == 1
    assert sessions[0].extra.get("externalHarness") is True, (
        "list_sessions() must set extra['externalHarness']=True when kind='attached'"
    )


def test_list_sessions_sets_external_harness_when_field_present(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d", lambda: _FakeDash({"externalHarness": True})
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("externalHarness") is True, (
        "list_sessions() must set extra['externalHarness']=True when externalHarness field is set"
    )


def test_list_sessions_omits_external_harness_for_direct_session(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash({"kind": "direct"}))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert "externalHarness" not in sessions[0].extra, (
        "externalHarness must not appear in extra for normal direct sessions"
    )


def test_infer_session_type_returns_attached_for_attached_kind():
    session = {"sessionId": "sess-1", "kind": "attached"}
    assert _infer_session_type(session) == "attached", (
        "_infer_session_type() must return 'attached' when kind='attached'"
    )


def test_infer_session_type_returns_attached_for_external_kind():
    session = {"sessionId": "sess-2", "kind": "external"}
    assert _infer_session_type(session) == "attached", (
        "_infer_session_type() must return 'attached' when kind='external'"
    )


def test_infer_session_type_returns_main_for_direct_session():
    session = {"sessionId": "sess-3", "kind": "direct"}
    assert _infer_session_type(session) == "main", (
        "_infer_session_type() must still return 'main' for ordinary direct sessions"
    )


def test_infer_session_type_subagent_still_classified_correctly():
    session = {"sessionId": "sess-4", "kind": "subagent"}
    assert _infer_session_type(session) == "sub-agent", (
        "Adding the 'attached' branch must not break existing subagent classification"
    )
