"""Regression tests for issue #3014.

OpenClaw's Talk/realtime-voice/managed-room subsystem writes structured JSONL
lifecycle records that the sync daemon ingests via ``ingest_talk_lifecycle()``.
That call stores data blobs with camelCase keys (``talkMode``, ``talkTransport``,
``talkProvider``, ``talkBrain``, ``talkDurationMs``, ``talkByteLength``,
``talkFinal``) — the exact keys the adapter must parse in ``list_events()``.

The extraction loop at ``clawmetry/adapters/openclaw.py:1828–1841`` handles
these keys, but the test at ``test_openclaw_list_events.py:242`` only exercises
the top-level snake_case variant.  These tests pin the camelCase path.
"""

import json

import clawmetry.local_store as ls
from clawmetry.adapters.openclaw import OpenClawAdapter


def _fake_store(data_blob: str):
    """Return a _FakeStore whose _fetch yields one event with the given blob."""

    class _FakeStore:
        def _fetch(self, sql, params):
            # id, event_type, ts, model, token_count, data, agent_id, node_id
            return [("e-tl-1", "talk.lifecycle", "0", None, 0, data_blob, "main", None)]

    return _FakeStore()


def test_list_events_surfaces_talk_mode_transport_provider(monkeypatch):
    """talkMode/talkTransport/talkProvider land as mode/transport/provider in extra."""
    blob = json.dumps({
        "talkMode": "realtime",
        "talkTransport": "webrtc",
        "talkProvider": "openai",
    })
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _fake_store(blob))

    events = OpenClawAdapter().list_events("sess-tl-1", limit=10)
    assert len(events) == 1
    extra = events[0].extra
    assert extra.get("mode") == "realtime", "talkMode must surface as extra['mode']"
    assert extra.get("transport") == "webrtc", "talkTransport must surface as extra['transport']"
    assert extra.get("provider") == "openai", "talkProvider must surface as extra['provider']"


def test_list_events_surfaces_talk_brain(monkeypatch):
    """talkBrain surfaces as extra['brain']."""
    blob = json.dumps({"talkBrain": "gpt-5-realtime"})
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _fake_store(blob))

    events = OpenClawAdapter().list_events("sess-tl-2", limit=10)
    assert events[0].extra.get("brain") == "gpt-5-realtime", (
        "talkBrain must surface as extra['brain']"
    )


def test_list_events_surfaces_talk_duration_and_byte_length(monkeypatch):
    """talkDurationMs/talkByteLength surface as duration_ms/byte_length in extra."""
    blob = json.dumps({"talkDurationMs": 3500, "talkByteLength": 8192})
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _fake_store(blob))

    events = OpenClawAdapter().list_events("sess-tl-3", limit=10)
    extra = events[0].extra
    assert extra.get("duration_ms") == 3500, "talkDurationMs must surface as extra['duration_ms']"
    assert extra.get("byte_length") == 8192, "talkByteLength must surface as extra['byte_length']"


def test_list_events_preserves_talk_final_false(monkeypatch):
    """talkFinal=False must not be silently dropped by a falsy guard (#3115)."""
    blob = json.dumps({"talkFinal": False})
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _fake_store(blob))

    events = OpenClawAdapter().list_events("sess-tl-4", limit=10)
    assert events[0].extra.get("final") is False, (
        "talkFinal=False must surface as extra['final']=False (is-not-None guard required)"
    )


def test_list_events_preserves_talk_final_true(monkeypatch):
    """talkFinal=True surfaces as extra['final']=True."""
    blob = json.dumps({"talkFinal": True})
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _fake_store(blob))

    events = OpenClawAdapter().list_events("sess-tl-5", limit=10)
    assert events[0].extra.get("final") is True, (
        "talkFinal=True must surface as extra['final']=True"
    )


def test_list_events_no_talk_fields_leaves_extra_clean(monkeypatch):
    """An event with no talk fields must not inject mode/transport/provider into extra."""
    blob = json.dumps({"channel": "main", "hostname": "box-1"})
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _fake_store(blob))

    events = OpenClawAdapter().list_events("sess-tl-6", limit=10)
    extra = events[0].extra
    for key in ("mode", "transport", "provider", "brain", "duration_ms", "byte_length", "final"):
        assert key not in extra, f"extra must not contain '{key}' when talk fields are absent"
