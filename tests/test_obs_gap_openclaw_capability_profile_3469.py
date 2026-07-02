"""Regression tests for issue #3469.

OpenClaw PR #98536 (harness 2026.7.1, "Safer scoped conversations") added
per-conversation capability profiles.  ClawMetry was not reading them:
``list_sessions()`` never placed ``capabilityProfile`` in ``Session.extra``
and ``list_events()`` did not extract it from the event data blob.
"""

import json

from clawmetry.adapters.openclaw import OpenClawAdapter
import clawmetry.adapters.openclaw as ocmod


class _FakeDash:
    def __init__(self, key="capabilityProfile", val="restricted"):
        self._key = key
        self._val = val

    def _get_sessions(self):
        return [{"sessionId": "sess-cap-1", self._key: self._val}]


def test_list_sessions_surfaces_capability_profile(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash("capabilityProfile", "restricted"))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert len(sessions) == 1
    assert sessions[0].extra.get("capabilityProfile") == "restricted", (
        "list_sessions() must propagate 'capabilityProfile' into Session.extra"
    )


def test_list_sessions_surfaces_conversation_capability_alias(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d", lambda: _FakeDash("conversationCapability", "scoped-read-only")
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("capabilityProfile") == "scoped-read-only", (
        "list_sessions() must also handle the 'conversationCapability' alias"
    )


def test_list_sessions_omits_capability_profile_when_absent(monkeypatch):
    class _NoDash:
        def _get_sessions(self):
            return [{"sessionId": "sess-cap-2"}]

    monkeypatch.setattr(ocmod, "_d", lambda: _NoDash())
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert "capabilityProfile" not in sessions[0].extra, (
        "capabilityProfile must not appear in extra when the upstream record omits it"
    )


def test_list_events_surfaces_capability_profile(monkeypatch):
    data = json.dumps({"capabilityProfile": "restricted"})

    class _FakeStore:
        def _fetch(self, sql, params):
            # id, event_type, ts, model, token_count, data, agent_id, node_id
            return [("e-cap-1", "message", "0", None, 0, data, "main", None)]

    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _FakeStore())

    events = OpenClawAdapter().list_events("sess-cap-1", limit=10)
    assert len(events) == 1
    assert events[0].extra.get("capabilityProfile") == "restricted", (
        "list_events() must extract 'capabilityProfile' from the data blob into extra"
    )


def test_list_events_surfaces_conversation_capability_alias(monkeypatch):
    data = json.dumps({"conversationCapability": "scoped-read-only"})

    class _FakeStore:
        def _fetch(self, sql, params):
            return [("e-cap-2", "message", "0", None, 0, data, "main", None)]

    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _FakeStore())

    events = OpenClawAdapter().list_events("sess-cap-2", limit=10)
    assert events[0].extra.get("capabilityProfile") == "scoped-read-only", (
        "list_events() must also handle the 'conversationCapability' alias in the blob"
    )
