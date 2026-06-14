"""Regression tests for issue #2794.

The OpenClaw adapter under-reported tokens for reasoning-capable models:
the per-turn ``token_count`` was derived as ``input + output`` and never
read the harness ``totalTokens`` field, and ``Session.reasoning_tokens``
was never populated by ``list_sessions()``. On extended-thinking models
``totalTokens`` carries a reasoning share the input/output split omits.
"""

import json

from clawmetry.adapters.openclaw import OpenClawAdapter
import clawmetry.adapters.openclaw as ocmod


def test_build_spans_token_count_uses_total_tokens_with_reasoning():
    # input+output = 300, but totalTokens = 500 -> 200 reasoning tokens that
    # the old (tok_in + tok_out) sum dropped on the floor.
    events = [{
        "type": "message",
        "timestamp": "2026-06-08T00:00:00Z",
        "message": {
            "role": "assistant",
            "model": "claude-opus-4-8",
            "usage": {"input_tokens": 100, "output_tokens": 200, "total_tokens": 500},
            "content": [],
        },
    }]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    llm = next(s for s in spans if s["name"].startswith("llm.call"))
    assert llm["token_count"] == 500, "token_count must reflect totalTokens (incl. reasoning)"
    assert llm["tokens_input"] == 100
    assert llm["tokens_output"] == 200


def test_build_spans_token_count_falls_back_to_sum_without_total():
    events = [{
        "type": "message",
        "timestamp": "2026-06-08T00:00:00Z",
        "message": {
            "role": "assistant",
            "model": "claude-sonnet-4-6",
            "usage": {"input_tokens": 40, "output_tokens": 60},
            "content": [],
        },
    }]
    spans = OpenClawAdapter._build_spans_from_events(events, "s2")
    llm = next(s for s in spans if s["name"].startswith("llm.call"))
    assert llm["token_count"] == 100


def test_list_sessions_populates_reasoning_tokens_from_residual(monkeypatch):
    class _FakeDash:
        def _get_sessions(self):
            # totalTokens outruns input+output+cache by 150 -> reasoning share.
            return [{
                "sessionId": "abc",
                "model": "claude-opus-4-8",
                "totalTokens": 1000,
                "inputTokens": 500,
                "outputTokens": 250,
                "cacheReadTokens": 100,
                "cacheWriteTokens": 0,
            }]

    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash())
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert len(sessions) == 1
    s = sessions[0]
    assert s.total_tokens == 1000
    assert s.reasoning_tokens == 150, "reasoning_tokens should recover the totalTokens residual"
    assert s.to_dict()["reasoningTokens"] == 150


def test_list_sessions_prefers_explicit_reasoning_field(monkeypatch):
    class _FakeDash:
        def _get_sessions(self):
            return [{
                "sessionId": "def",
                "totalTokens": 1000,
                "inputTokens": 500,
                "outputTokens": 250,
                "reasoningTokens": 222,
            }]

    monkeypatch.setattr(ocmod, "_d", lambda: _FakeDash())
    s = OpenClawAdapter().list_sessions(limit=10)[0]
    assert s.reasoning_tokens == 222, "an explicit reasoningTokens field wins over the residual"


def test_list_events_surfaces_total_and_reasoning_tokens(monkeypatch):
    data = json.dumps({
        "message": {
            "role": "assistant",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 200,
                "total_tokens": 500,
            },
        }
    })

    class _FakeStore:
        def _fetch(self, sql, params):
            # id, event_type, ts, model, token_count, data, agent_id, node_id
            return [("e1", "message", "1717800000", "claude-opus-4-8", 300, data, "main", None)]

    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda read_only=True: _FakeStore())

    events = OpenClawAdapter().list_events("abc", limit=10)
    assert len(events) == 1
    ev = events[0]
    # DB token_count was 300 (input+output); totalTokens 500 must win.
    assert ev.tokens == 500
    assert ev.extra["totalTokens"] == 500
    assert ev.extra["reasoningTokens"] == 200
