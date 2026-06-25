"""Regression tests for issue #3323.

OpenClaw PR #95030 added an identity ``target`` field to session and event
transcript records so consumers can identify which agent/session context a
transcript belongs to.  ClawMetry was not reading it: ``list_sessions()``
never placed it in ``Session.extra`` and the ``list_events()`` blob parser
did not extract it from the event data.
"""

import json

from clawmetry.adapters.openclaw import OpenClawAdapter
import clawmetry.adapters.openclaw as ocmod


class _FakeDash:
    def __init__(self, target_key="target", target_val="agent/main"):
        self._key = target_key
        self._val = target_val

    def _get_sessions(self):
        return [{"sessionId": "sess-1", self._key: self._val}]


def test_list_sessions_surfaces_identity_target(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash("target", "agent/main"))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert len(sessions) == 1
    assert sessions[0].extra.get("identityTarget") == "agent/main", (
        "list_sessions() must propagate the 'target' field into extra['identityTarget']"
    )


def test_list_sessions_surfaces_identity_target_camelcase(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d", lambda: _FakeDash("identityTarget", "workspace/abc")
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("identityTarget") == "workspace/abc", (
        "list_sessions() must also handle the 'identityTarget' camelCase spelling"
    )


def test_list_sessions_omits_identity_target_when_absent(monkeypatch):
    class _NoDash:
        def _get_sessions(self):
            return [{"sessionId": "sess-2"}]

    monkeypatch.setattr(ocmod, "_d", lambda: _NoDash())
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert "identityTarget" not in sessions[0].extra, (
        "identityTarget must not appear in extra when the upstream record has no target field"
    )


def test_list_events_surfaces_identity_target(monkeypatch):
    data = json.dumps({"target": "agent/main"})

    class _FakeStore:
        def _fetch(self, sql, params):
            # id, event_type, ts, model, token_count, data, agent_id, node_id
            return [("e1", "message", "0", None, 0, data, "main", None)]

    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _FakeStore())

    events = OpenClawAdapter().list_events("sess-1", limit=10)
    assert len(events) == 1
    assert events[0].extra.get("identityTarget") == "agent/main", (
        "list_events() must extract 'target' from the data blob into extra['identityTarget']"
    )


def test_list_events_surfaces_identity_target_camelcase(monkeypatch):
    data = json.dumps({"identityTarget": "workspace/xyz"})

    class _FakeStore:
        def _fetch(self, sql, params):
            return [("e2", "message", "0", None, 0, data, "main", None)]

    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _FakeStore())

    events = OpenClawAdapter().list_events("sess-2", limit=10)
    assert events[0].extra.get("identityTarget") == "workspace/xyz"
