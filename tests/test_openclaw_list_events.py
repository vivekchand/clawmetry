"""Tests for OpenClawAdapter.list_events() — no longer a stub.

The unified Event-yielding API for the OpenClaw Free runtime used to
return ``[]`` with a "deferred to follow-up PR" comment. This test
pins the new DuckDB-backed implementation so the unified per-agent
session view + any caller of ``adapter.list_events(session_id)`` gets
real events back.
"""
from __future__ import annotations

import importlib
import time
import uuid

import pytest


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.local_store as _ls
    importlib.reload(_ls)
    s = _ls.LocalStore()
    s.start()
    monkeypatch.setattr(_ls, "get_store", lambda *a, **kw: s)
    yield s
    s.stop(flush=True)


def _seed(store, session_id, event_type, model=None, tokens=0):
    store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "openclaw",
        "session_id": session_id,
        "event_type": event_type,
        "ts": time.time(),
        "model": model or "",
        "data": {"x": 1},
        "token_count": tokens,
    })


def _wait_flush(s, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if s.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def test_list_events_returns_unified_shape(isolated_store):
    _seed(isolated_store, "sess-A", "session.started")
    _seed(isolated_store, "sess-A", "model.completed", model="claude-3.5", tokens=42)
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-A")
    assert len(events) == 2
    types = [e.type for e in events]
    assert "session.started" in types
    assert "model.completed" in types
    assert all(e.agent == "openclaw" for e in events)
    assert all(e.session_id == "sess-A" for e in events)
    # Model + tokens flow through into the unified shape.
    model_evt = next(e for e in events if e.type == "model.completed")
    assert model_evt.tokens == 42
    assert model_evt.extra.get("model") == "claude-3.5"


def test_list_events_filters_by_session_id(isolated_store):
    _seed(isolated_store, "sess-A", "model.completed")
    _seed(isolated_store, "sess-B", "model.completed")
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-A")
    assert len(events) == 1
    assert events[0].session_id == "sess-A"


def test_list_events_filters_by_agent_type(isolated_store):
    """A nemoclaw-tagged event in the same store must NOT leak into
    OpenClaw's list_events; agent_type is the discriminator."""
    _seed(isolated_store, "sess-C", "model.completed")
    isolated_store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "nemoclaw",
        "session_id": "sess-C",
        "event_type": "model.completed",
        "ts": time.time(),
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-C")
    assert len(events) == 1  # only the openclaw one


def test_list_events_respects_limit(isolated_store):
    for _ in range(5):
        _seed(isolated_store, "sess-D", "tool.call")
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-D", limit=3)
    assert len(events) == 3


def test_list_events_unknown_session_returns_empty(isolated_store):
    from clawmetry.adapters.openclaw import OpenClawAdapter
    assert OpenClawAdapter().list_events("no-such-session") == []


def test_list_events_surfaces_cache_token_split(isolated_store):
    """Per-type token fields from the data blob land in event.extra (#2603).

    Seed an assistant event whose data contains message.usage with input,
    output, and cache_read token counts; verify list_events() populates
    the corresponding extra keys so per-turn cache efficiency is measurable.
    """
    import uuid, time as _t
    isolated_store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "openclaw",
        "session_id": "sess-E",
        "event_type": "model.completed",
        "ts": _t.time(),
        "model": "claude-opus-4-7",
        "token_count": 150,
        "data": {
            "type": "assistant",
            "message": {
                "model": "claude-opus-4-7",
                "usage": {
                    "input_tokens": 30,
                    "output_tokens": 20,
                    "cache_read_input_tokens": 80,
                    "cache_creation_input_tokens": 10,
                },
            },
        },
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-E")
    assert len(events) == 1
    ex = events[0].extra
    assert ex.get("inputTokens") == 30
    assert ex.get("outputTokens") == 20
    assert ex.get("cacheReadTokens") == 80
    assert ex.get("cacheWriteTokens") == 10


def test_list_events_populates_content_from_log_message_text(isolated_store):
    """Log records with a string ``message`` populate Event.content (#2700).

    OpenClaw gateway log records (per docs/logging.md) put the flattened
    log text in a top-level string ``message`` field for full-text search.
    Previously list_events read obj["message"] only to choose a usage
    source (dict vs. string branch) and discarded the string, so log
    events came back with empty content. Pin the new behavior so the
    unified event stream stays searchable.
    """
    import uuid, time as _t
    isolated_store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "openclaw",
        "session_id": "sess-LOG",
        "event_type": "log",
        "ts": _t.time(),
        "data": {
            "channel": "gateway",
            "hostname": "Dhriti-1",
            "level": "info",
            "message": "tool dispatched: bash exit=0",
        },
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-LOG")
    assert len(events) == 1
    e = events[0]
    assert e.content == "tool dispatched: bash exit=0"
    # channel/hostname still come through extra.
    assert e.extra.get("channel") == "gateway"
    assert e.extra.get("hostname") == "Dhriti-1"


def test_list_events_dict_message_does_not_set_content(isolated_store):
    """Sanity guard: when ``message`` is a dict (assistant turn shape),
    Event.content stays empty — only string ``message`` values are
    treated as flattened log text. Keeps the dict branch — which is
    the usage source — unchanged.
    """
    import uuid, time as _t
    isolated_store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "openclaw",
        "session_id": "sess-DICT",
        "event_type": "model.completed",
        "ts": _t.time(),
        "data": {
            "type": "assistant",
            "message": {
                "model": "claude-opus-4-7",
                "usage": {"input_tokens": 1, "output_tokens": 2},
            },
        },
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-DICT")
    assert len(events) == 1
    assert events[0].content == ""


def test_list_events_surfaces_reasoning_tokens(isolated_store):
    """Extended-thinking / reasoning tokens land in event.extra (#2876).

    Anthropic extended-thinking sessions emit a reasoning-token share in
    the per-turn usage object that input+output alone omit. list_events()
    must surface it as ``reasoningTokens`` so per-turn cost is not
    under-reported for reasoning-capable models.
    """
    import uuid, time as _t
    isolated_store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "openclaw",
        "session_id": "sess-THINK",
        "event_type": "model.completed",
        "ts": _t.time(),
        "model": "claude-opus-4-7",
        "token_count": 150,
        "data": {
            "type": "assistant",
            "message": {
                "model": "claude-opus-4-7",
                "usage": {
                    "input_tokens": 30,
                    "output_tokens": 20,
                    "thinking_input_tokens": 64,
                },
            },
        },
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-THINK")
    assert len(events) == 1
    ex = events[0].extra
    assert ex.get("inputTokens") == 30
    assert ex.get("outputTokens") == 20
    assert ex.get("reasoningTokens") == 64


def test_reasoning_tokens_helper_key_variants():
    """_reasoning_tokens accepts the known key spellings and is robust to
    missing/garbage values (#2876)."""
    from clawmetry.adapters.openclaw import _reasoning_tokens
    assert _reasoning_tokens({"reasoning_tokens": 12}) == 12
    assert _reasoning_tokens({"reasoningTokens": 7}) == 7
    assert _reasoning_tokens({"thinking_tokens": 5}) == 5
    assert _reasoning_tokens({"thinking_input_tokens": 9}) == 9
    assert _reasoning_tokens({"reasoning_output_tokens": 3}) == 3
    # absent / non-dict / unparsable → 0
    assert _reasoning_tokens({"input_tokens": 10}) == 0
    assert _reasoning_tokens({}) == 0
    assert _reasoning_tokens(None) == 0  # type: ignore[arg-type]
    assert _reasoning_tokens({"reasoning_tokens": "nope"}) == 0
    # negative coerced to non-negative floor
    assert _reasoning_tokens({"reasoning_tokens": -4}) == 0


def test_list_events_surfaces_cache_token_split_sdk_keys(isolated_store):
    """SDK-normalized cacheRead/cacheWrite usage keys are read by list_events.

    The OpenClaw plugin SDK completeSimple() returns Usage with the
    normalized keys ``cacheRead`` / ``cacheWrite`` (instead of the raw
    Anthropic-style ``cache_read_input_tokens`` /
    ``cache_creation_input_tokens``). Sessions recorded via that SDK
    path should still surface the per-turn cache split through
    Event.extra. Regression for #2699.
    """
    import uuid, time as _t
    isolated_store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "openclaw",
        "session_id": "sess-SDK",
        "event_type": "model.completed",
        "ts": _t.time(),
        "model": "claude-opus-4-7",
        "token_count": 150,
        "data": {
            "type": "assistant",
            "message": {
                "model": "claude-opus-4-7",
                "usage": {
                    "input_tokens": 30,
                    "output_tokens": 20,
                    "cacheRead": 80,
                    "cacheWrite": 10,
                },
            },
        },
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-SDK")
    assert len(events) == 1
    ex = events[0].extra
    assert ex.get("inputTokens") == 30
    assert ex.get("outputTokens") == 20
    assert ex.get("cacheReadTokens") == 80
    assert ex.get("cacheWriteTokens") == 10


def test_list_events_surfaces_total_tokens_for_reasoning_model(isolated_store):
    """totalTokens from usage lands in event.extra so callers can derive the
    reasoning share (totalTokens - inputTokens - outputTokens). Fixes #2794."""
    import uuid, time as _t
    isolated_store.ingest({
        "id": str(uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "openclaw",
        "session_id": "sess-TOTAL",
        "event_type": "model.completed",
        "ts": _t.time(),
        "model": "claude-opus-4-7",
        "token_count": 162,
        "data": {
            "type": "assistant",
            "message": {
                "model": "claude-opus-4-7",
                "usage": {
                    "input_tokens": 30,
                    "output_tokens": 20,
                    "totalTokens": 162,
                },
            },
        },
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-TOTAL")
    assert len(events) == 1
    ex = events[0].extra
    assert ex.get("inputTokens") == 30
    assert ex.get("outputTokens") == 20
    assert ex.get("totalTokens") == 162, "totalTokens must appear in extra for reasoning-model events"


def test_build_spans_prefers_total_tokens_for_reasoning_model():
    """_build_spans_from_events must use totalTokens as token_count when it
    exceeds tok_in+tok_out — the extra comes from reasoning. Fixes #2794."""
    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = [
        {
            "type": "message",
            "timestamp": "1700000001",
            "message": {
                "role": "assistant",
                "model": "claude-opus-4-7",
                "usage": {
                    "input_tokens": 30,
                    "output_tokens": 20,
                    "totalTokens": 162,  # 112 reasoning tokens on top
                },
                "content": [],
            },
        },
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "sess-span-r")
    llm_spans = [s for s in spans if s.get("name", "").startswith("llm.call")]
    assert len(llm_spans) == 1
    assert llm_spans[0]["token_count"] == 162, (
        "token_count must equal totalTokens (162), not tok_in+tok_out (50)"
    )


def test_list_events_surfaces_talk_lifecycle_fields(isolated_store):
    """Talk/voice lifecycle fields (#2730) flow into Event.extra.

    ``local_store.ingest_talk_lifecycle`` writes a clean payload of
    ``{talkEventType, talkMode, talkTransport, talkBrain, talkProvider,
    talkFinal, talkDurationMs, talkByteLength}`` as the data BLOB on the
    ``talk.lifecycle`` event row. Pin the new behavior that those fields
    promote to ``Event.extra.{mode, transport, brain, provider, final,
    duration_ms, byte_length}`` so dashboards can render voice-session
    activity without re-decoding the raw daemon log.
    """
    isolated_store.ingest_talk_lifecycle(
        node_id="agent+test-node",
        session_id="sess-TALK",
        event_type="session.start",
        mode="voice",
        transport="webrtc",
        brain="gpt-realtime",
        provider="openai",
        final=True,
        duration_ms=1200,
        byte_length=4096,
        ts_iso="2026-06-06T22:00:00Z",
    )
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-TALK")
    assert len(events) == 1
    ev = events[0]
    assert ev.type == "talk.lifecycle"
    assert ev.extra.get("mode") == "voice"
    assert ev.extra.get("transport") == "webrtc"
    assert ev.extra.get("brain") == "gpt-realtime"
    assert ev.extra.get("provider") == "openai"
    assert ev.extra.get("duration_ms") == 1200
    assert ev.extra.get("byte_length") == 4096
    assert ev.extra.get("final") is True


def test_list_events_talk_lifecycle_omits_empty_fields(isolated_store):
    """Empty / unset Talk attrs (string "" or None) must NOT pollute Event.extra.

    Lifecycle events like ``session.end`` often only carry an event_type +
    duration_ms; mode/transport/provider may be blank. Pin that those blanks
    do not appear as empty strings in extra so downstream renderers can
    rely on key presence as a "field known" signal.
    """
    isolated_store.ingest_talk_lifecycle(
        node_id="agent+test-node",
        session_id="sess-TALK-MIN",
        event_type="session.end",
        duration_ms=850,
        ts_iso="2026-06-06T22:01:00Z",
    )
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-TALK-MIN")
    assert len(events) == 1
    ex = events[0].extra
    assert ex.get("duration_ms") == 850
    assert "mode" not in ex
    assert "transport" not in ex
    assert "brain" not in ex
    assert "provider" not in ex
    assert "final" not in ex


def test_list_events_talk_lifecycle_byte_length_zero_still_stamps(isolated_store):
    """``talkByteLength == 0`` is a real measurement, not "unset" -- stamp it.

    A zero-length audio chunk is a valid lifecycle observation (silent frame
    or empty turn). The isinstance-based stamping must include 0 so
    downstream avg/percentile math doesn't undercount empty turns.
    """
    isolated_store.ingest_talk_lifecycle(
        node_id="agent+test-node",
        session_id="sess-TALK-ZERO",
        event_type="audio.chunk",
        byte_length=0,
        duration_ms=0,
        ts_iso="2026-06-06T22:02:00Z",
    )
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-TALK-ZERO")
    assert len(events) == 1
    ex = events[0].extra
    assert ex.get("byte_length") == 0
    assert ex.get("duration_ms") == 0


def test_list_events_non_talk_events_unchanged_by_talk_extraction(isolated_store):
    """Non-Talk events keep their pre-existing extra shape (#2730 backwards-compat).

    Seeds a plain model.completed event with no Talk-shaped fields in its
    data blob and confirms none of the new talk.* keys leak in. Anchors
    backwards-compat at the test layer.
    """
    import uuid as _uuid, time as _t
    isolated_store.ingest({
        "id": str(_uuid.uuid4()),
        "node_id": "agent+test-node",
        "agent_id": "main",
        "agent_type": "openclaw",
        "session_id": "sess-NO-TALK",
        "event_type": "model.completed",
        "ts": _t.time(),
        "model": "claude-opus-4-7",
        "token_count": 5,
        "data": {"channel": "gateway", "hostname": "Dhriti-1"},
    })
    _wait_flush(isolated_store)

    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = OpenClawAdapter().list_events("sess-NO-TALK")
    assert len(events) == 1
    ex = events[0].extra
    assert ex.get("channel") == "gateway"
    assert ex.get("hostname") == "Dhriti-1"
    for k in ("mode", "transport", "brain", "provider",
              "duration_ms", "byte_length", "final"):
        assert k not in ex, f"unexpected talk.* key {k} leaked into non-talk event extra"
