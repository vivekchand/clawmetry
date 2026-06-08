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


def test_cache_reread_tax_quantified():
    # A churny Anthropic session: large cache WRITE, tiny cache READ → it keeps
    # rebuilding the cache (5-min TTL expired) instead of reusing it. The
    # re-read tax = what was paid to rebuild; savings = what little reuse gave.
    intel = _session_cost_intel(
        _FakeSession(input=2000, output=500, cache_read=200, cache_write=8000,
                     model="claude-opus-4-8")
    )
    # opus-4-8 is the new gen: input $5/1M; writes bill at 1.25x →
    # 8000*5*1.25/1e6 = 0.05 (was $0.15 under the old opus-4 $15/1M rate).
    assert abs(intel["cacheWriteCostUsd"] - 0.05) < 1e-6
    # savings on the 200 read tokens: 200*(5 - 0.5)/1e6 = 0.0009
    assert abs(intel["cacheSavedUsd"] - 0.0009) < 1e-6
    # rebuild cost dwarfs savings → the re-read tax is real here
    assert intel["cacheWriteCostUsd"] > intel["cacheSavedUsd"]


def test_cache_fields_omitted_without_cache_tokens():
    intel = _session_cost_intel(
        _FakeSession(input=1000, output=200, model="claude-opus-4-8")
    )
    assert "cacheWriteCostUsd" not in intel
    assert "cacheSavedUsd" not in intel


def test_reread_tax_waste_flag():
    from routes.sessions import _derive_session_insight, _WASTE_RECOMMENDATIONS
    churn = {"cost_usd": 1.0, "cache_hit_pct": 9.1,
             "cache_write_cost_usd": 0.15, "cache_saved_usd": 0.0027}
    assert "reread_tax" in _derive_session_insight(churn, [])["waste_flags"]
    assert "reread_tax" in _WASTE_RECOMMENDATIONS
    # healthy reuse (savings exceed rebuild) must NOT flag
    healthy = {"cost_usd": 1.0, "cache_hit_pct": 85,
               "cache_write_cost_usd": 0.01, "cache_saved_usd": 0.50}
    assert "reread_tax" not in _derive_session_insight(healthy, [])["waste_flags"]


def test_waste_summary_rolls_up_reread_tax():
    from routes.sessions import _derive_waste_summary
    sessions = [
        {"session_id": "a", "cost_usd": 1.0, "cache_write_cost_usd": 0.15,
         "cache_saved_usd": 0.0027, "cache_hit_pct": 9},   # churn → counted
        {"session_id": "b", "cost_usd": 2.0, "cache_write_cost_usd": 0.01,
         "cache_saved_usd": 0.50, "cache_hit_pct": 85},      # healthy → not
    ]
    w = _derive_waste_summary(sessions)
    assert w["reread_tax_sessions"] == 1
    assert abs(w["reread_tax_usd"] - 0.15) < 1e-9


def test_idle_gap_cache_expiry_count():
    from clawmetry.sync import _session_idle_gaps
    class _E:
        def __init__(self, ts): self.ts = ts
    # gaps: 100s (ok), 500s (>300 → expiry), 700s (expiry)
    evs = [_E(1000.0), _E(1100.0), _E(1600.0), _E(2300.0)]
    out = _session_idle_gaps(evs)
    assert out["cacheExpiryCount"] == 2
    assert out["maxIdleGapSec"] == 700.0
    # ISO timestamps also parse
    iso = [_E("2026-06-02T00:00:00Z"), _E("2026-06-02T00:10:00Z")]  # 600s gap
    assert _session_idle_gaps(iso)["cacheExpiryCount"] == 1
    # fewer than 2 events → empty
    assert _session_idle_gaps([_E(1.0)]) == {}


def test_reread_tax_flag_on_idle_evidence():
    from routes.sessions import _derive_session_insight
    # direct idle evidence (>=2 expiries) flags even without the cost heuristic
    out = _derive_session_insight({"cost_usd": 1.0, "cache_expiry_count": 2}, [])
    assert "reread_tax" in out["waste_flags"]
    assert out["cache_expiry_count"] == 2
    # a single brief idle does not
    assert "reread_tax" not in _derive_session_insight(
        {"cost_usd": 1.0, "cache_expiry_count": 1}, [])["waste_flags"]
