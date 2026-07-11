"""Regression tests for issue #3649.

OpenClaw CHANGELOG #98021 ("GPT-5.6 Ultra and runtime switching") introduced
a distinct runtime (engine) dimension — Sol, Terra, Luna — that changes
atomically alongside model and thinking-mode during fallback.  ClawMetry was
not reading it: ``list_sessions()`` never placed ``fallbackRuntime`` in
``Session.extra`` and ``list_events()`` did not extract it from the event blob.
"""

import json

from clawmetry.adapters.openclaw import OpenClawAdapter
import clawmetry.adapters.openclaw as ocmod


class _FakeDash:
    def __init__(self, key="fallbackRuntime", val="codex"):
        self._key = key
        self._val = val

    def _get_sessions(self):
        return [{"sessionId": "sess-fbr-1", self._key: self._val}]


def test_list_sessions_surfaces_fallback_runtime(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash("fallbackRuntime", "codex"))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert len(sessions) == 1
    assert sessions[0].extra.get("fallbackRuntime") == "codex", (
        "list_sessions() must propagate 'fallbackRuntime' into Session.extra"
    )


def test_list_sessions_surfaces_fallback_runtime_engine_alias(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d", lambda: _FakeDash("fallbackRuntimeEngine", "openclaw")
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("fallbackRuntime") == "openclaw", (
        "list_sessions() must also handle the 'fallbackRuntimeEngine' alias"
    )


def test_list_sessions_surfaces_runtime_engine_alias(monkeypatch):
    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash("runtimeEngine", "sol"))
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("fallbackRuntime") == "sol", (
        "list_sessions() must also handle the 'runtimeEngine' alias"
    )


def test_list_sessions_omits_fallback_runtime_when_absent(monkeypatch):
    class _NoDash:
        def _get_sessions(self):
            return [{"sessionId": "sess-fbr-2"}]

    monkeypatch.setattr(ocmod, "_d", lambda: _NoDash())
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert "fallbackRuntime" not in sessions[0].extra, (
        "fallbackRuntime must not appear in extra when the upstream record omits it"
    )


def test_list_events_surfaces_fallback_runtime(monkeypatch):
    data = json.dumps({"fallbackRuntime": "codex"})

    class _FakeStore:
        def _fetch(self, sql, params):
            # id, event_type, ts, model, token_count, data, agent_id, node_id
            return [("e-fbr-1", "message", "0", None, 0, data, "main", None)]

    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _FakeStore())

    events = OpenClawAdapter().list_events("sess-fbr-1", limit=10)
    assert len(events) == 1
    assert events[0].extra.get("fallbackRuntime") == "codex", (
        "list_events() must extract 'fallbackRuntime' from the data blob into extra"
    )


def test_list_events_surfaces_runtime_engine_alias(monkeypatch):
    data = json.dumps({"runtimeEngine": "luna"})

    class _FakeStore:
        def _fetch(self, sql, params):
            return [("e-fbr-2", "message", "0", None, 0, data, "main", None)]

    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _FakeStore())

    events = OpenClawAdapter().list_events("sess-fbr-2", limit=10)
    assert events[0].extra.get("fallbackRuntime") == "luna", (
        "list_events() must also handle the 'runtimeEngine' alias in the blob"
    )
