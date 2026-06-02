"""Unit tests for the cost-intelligence foundation (_session_cost_intel).

Verifies the per-session token split + derived reasoning-tax $ and cache-hit %
that the family ingest stashes on the session metadata.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry.sync import _session_cost_intel


class _FakeSession:
    def __init__(self, **k):
        self.input_tokens = k.get("input", 0)
        self.output_tokens = k.get("output", 0)
        self.cache_read_tokens = k.get("cache_read", 0)
        self.cache_write_tokens = k.get("cache_write", 0)
        self.reasoning_tokens = k.get("reasoning", 0)
        self.model = k.get("model", "")


def test_cloud_model_reasoning_and_cache():
    intel = _session_cost_intel(
        _FakeSession(input=100000, output=20000, cache_read=80000, reasoning=5000, model="gpt-5.4")
    )
    assert intel["tokenSplit"]["reasoning"] == 5000
    assert intel["reasoningCostUsd"] > 0  # reasoning billed at the output rate
    assert intel["cacheHitPct"] == round(80000 / 180000 * 100, 1)


def test_local_model_reasoning_is_real_zero():
    intel = _session_cost_intel(
        _FakeSession(input=1000, output=500, reasoning=200, model="qwen3:8b")
    )
    # Local model: reasoning is real $0.00 (not "unknown").
    assert intel["reasoningCostUsd"] == 0.0


def test_no_model_omits_reasoning_keeps_cache():
    intel = _session_cost_intel(_FakeSession(input=1000, cache_read=1000))
    assert "reasoningCostUsd" not in intel  # honest "unknown" -> omitted
    assert intel["cacheHitPct"] == 50.0


def test_no_tokens_omits_cache():
    intel = _session_cost_intel(_FakeSession(model="gpt-5.4"))
    assert "cacheHitPct" not in intel  # nothing to ratio against
    assert "reasoningCostUsd" not in intel
    assert intel["tokenSplit"]["input"] == 0


def test_never_raises_on_garbage():
    class Bad:
        input_tokens = "x"
        model = None
    # Must not raise; returns at worst an empty-ish dict.
    assert isinstance(_session_cost_intel(Bad()), dict)


from clawmetry.sync import _session_tool_health


class _FakeEvent:
    def __init__(self, type="", tool_name="", content="", extra=None):
        self.type = type
        self.tool_name = tool_name
        self.content = content
        self.extra = extra or {}


def test_tool_health_counts_real_errors():
    evs = [
        _FakeEvent(type="tool.result", tool_name="browser", extra={"isError": True}, content="Connection refused: fatal"),
        _FakeEvent(type="tool.result", tool_name="browser"),
        _FakeEvent(type="tool.result", tool_name="bash"),
        _FakeEvent(type="message", content="hi"),  # not a tool result -> ignored
    ]
    h = _session_tool_health(evs)
    assert h["toolResults"] == 3
    assert h["toolErrors"] >= 1
    assert 0 < h["toolErrorPct"] <= 100


def test_tool_health_empty_when_no_tools():
    assert _session_tool_health([_FakeEvent(type="message")]) == {}


def test_tool_health_clean_session_zero_errors():
    evs = [_FakeEvent(type="tool.result", tool_name="read"), _FakeEvent(type="tool.result", tool_name="bash")]
    h = _session_tool_health(evs)
    assert h["toolResults"] == 2 and h["toolErrors"] == 0 and h["toolErrorPct"] == 0.0
