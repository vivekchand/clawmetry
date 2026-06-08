"""Proxy cache-bust detection + SSE token-counting tests (#2839/#2840/#2841/#2842)."""
from clawmetry.proxy import (
    normalize_tools, raw_tools_fp, scan_volatile_content, stable_prefix_hash,
    detect_cache_risk, parse_anthropic_sse_chunk, StreamUsage,
)


def test_normalize_tools_is_order_and_key_stable():
    a = [{"name": "b", "input_schema": {"y": 1, "x": 2}}, {"name": "a", "x": 1}]
    b = [{"name": "a", "x": 1}, {"name": "b", "input_schema": {"x": 2, "y": 1}}]
    assert normalize_tools(a) == normalize_tools(b)        # reorder + key-order = same
    assert normalize_tools(a) != normalize_tools([{"name": "a"}])
    assert normalize_tools("nope") == ""


def test_scan_volatile_counts_only_no_values():
    txt = ("now is 2026-06-08T12:00:00 id 550e8400-e29b-41d4-a716-446655440000 "
           "build 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08")
    v = scan_volatile_content(txt)
    assert v.get("iso_timestamp", 0) >= 1
    assert v.get("uuid", 0) == 1
    assert v.get("long_hex", 0) == 1
    # values themselves are never returned, only counts
    assert all(isinstance(n, int) for n in v.values())
    assert scan_volatile_content("") == {}


def test_stable_prefix_hash_ignores_tool_order_but_catches_system_drift():
    base = {"model": "claude-sonnet-4-5", "tools": [{"name": "a"}, {"name": "b"}],
            "system": "You are helpful."}
    reordered = {"model": "claude-sonnet-4-5", "tools": [{"name": "b"}, {"name": "a"}],
                 "system": "You are helpful."}
    drifted = dict(base); drifted["system"] = "You are helpful. Now: 2026-06-08T00:00:00"
    assert stable_prefix_hash(base) == stable_prefix_hash(reordered)   # reorder != drift
    assert stable_prefix_hash(base) != stable_prefix_hash(drifted)     # system change = drift


def test_detect_cache_risk_scores_volatile():
    body = {"model": "m", "system": "ts 2026-06-08T12:00:00 ts 2026-06-08T13:00:00",
            "tools": [{"name": "x"}]}
    r = detect_cache_risk(body)
    assert r["cache_risk_score"] >= 2
    assert r["prefix_hash"]
    assert "content" not in r  # no raw text


def test_tool_order_churn_detection():
    tools_ab = [{"name": "a", "input_schema": {"type": "object"}}, {"name": "b"}]
    tools_ba = [{"name": "b"}, {"name": "a", "input_schema": {"type": "object"}}]
    tools_diff = [{"name": "a"}, {"name": "c"}]
    # raw fp differs on reorder; normalize_tools doesn't — this combination
    # is the signal for order-only churn
    assert raw_tools_fp(tools_ab) != raw_tools_fp(tools_ba)
    assert normalize_tools(tools_ab) == normalize_tools(tools_ba)
    # a genuine tool change shows up in both fingerprints
    assert raw_tools_fp(tools_ab) != raw_tools_fp(tools_diff)
    assert normalize_tools(tools_ab) != normalize_tools(tools_diff)
    # edge cases never raise
    assert isinstance(raw_tools_fp([]), str)  # empty list still hashes cleanly
    assert raw_tools_fp("bad") == ""  # type: ignore[arg-type]  # non-list → empty


def test_sse_message_delta_takes_max_output_tokens():
    u = StreamUsage()
    parse_anthropic_sse_chunk('data: {"type":"message_start","message":{"usage":{"input_tokens":100,"cache_read_input_tokens":50},"model":"m"}}', u)
    parse_anthropic_sse_chunk('data: {"type":"message_delta","usage":{"output_tokens":40}}', u)
    parse_anthropic_sse_chunk('data: {"type":"message_delta","usage":{"output_tokens":120}}', u)
    # a stray lower delta must not lower the count
    parse_anthropic_sse_chunk('data: {"type":"message_delta","usage":{"output_tokens":5}}', u)
    assert u.output_tokens == 120
    assert u.input_tokens == 100
    assert u.cache_read_tokens == 50


def test_sse_extended_thinking_reasoning_tokens_extracted():
    """Streamed extended-thinking session: reasoning_tokens read from message_delta.usage."""
    u = StreamUsage()
    # 1. Message start — input tokens only
    parse_anthropic_sse_chunk(
        'data: {"type":"message_start","message":{"usage":{"input_tokens":200},"model":"claude-opus-4-8"}}', u
    )
    # 2. Thinking block starts
    parse_anthropic_sse_chunk(
        'data: {"type":"content_block_start","index":0,"content_block":{"type":"thinking","thinking":""}}', u
    )
    # 3. Thinking delta — text only, no token count here
    parse_anthropic_sse_chunk(
        'data: {"type":"content_block_delta","index":0,"delta":{"type":"thinking_delta","thinking":"Let me think..."}}', u
    )
    # 4. Signature delta marks end of thinking block
    parse_anthropic_sse_chunk(
        'data: {"type":"content_block_delta","index":0,"delta":{"type":"signature_delta","signature":"abc123"}}', u
    )
    # 5. Thinking block stops
    parse_anthropic_sse_chunk('data: {"type":"content_block_stop","index":0}', u)
    # 6. Final message_delta carries reconciled usage including thinking_tokens
    parse_anthropic_sse_chunk(
        'data: {"type":"message_delta","usage":{"output_tokens":350,"thinking_tokens":300},"delta":{"stop_reason":"end_turn"}}', u
    )
    assert u.output_tokens == 350
    assert u.reasoning_tokens == 300
    assert u.input_tokens == 200
    assert u.stop_reason == "end_turn"


def test_sse_thinking_tokens_alternate_key_names():
    """reasoning_tokens is read regardless of which key name the API uses."""
    for key in ("thinking_tokens", "reasoning_tokens", "thinking_input_tokens"):
        u = StreamUsage()
        parse_anthropic_sse_chunk(
            f'data: {{"type":"message_delta","usage":{{"output_tokens":100,"{key}":75}}}}', u
        )
        assert u.reasoning_tokens == 75, f"key {key!r} not read"


def test_sse_thinking_tokens_max_across_deltas():
    """Like output_tokens, reasoning_tokens takes the max over multiple message_delta events."""
    u = StreamUsage()
    parse_anthropic_sse_chunk('data: {"type":"message_delta","usage":{"output_tokens":50,"thinking_tokens":40}}', u)
    parse_anthropic_sse_chunk('data: {"type":"message_delta","usage":{"output_tokens":150,"thinking_tokens":120}}', u)
    parse_anthropic_sse_chunk('data: {"type":"message_delta","usage":{"output_tokens":10,"thinking_tokens":5}}', u)
    assert u.output_tokens == 150
    assert u.reasoning_tokens == 120


def test_sse_no_thinking_tokens_leaves_zero():
    """Non-thinking sessions must not populate reasoning_tokens."""
    u = StreamUsage()
    parse_anthropic_sse_chunk('data: {"type":"message_start","message":{"usage":{"input_tokens":50},"model":"claude-haiku-4-5"}}', u)
    parse_anthropic_sse_chunk('data: {"type":"message_delta","usage":{"output_tokens":80},"delta":{"stop_reason":"end_turn"}}', u)
    assert u.reasoning_tokens == 0
    assert u.output_tokens == 80
