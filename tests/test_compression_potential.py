"""Tests for the compression-potential meter (#2838) and the fleet waste
aggregation that surfaces it (#2839 cache-risk roll-up).

Measurement only: we assert the heuristics classify content correctly, the
detector estimates recoverable token share, persists ONLY aggregates (never raw
content), and the waste summary rolls per-session metrics into fleet figures.

Also covers _agg_compression (issue #2837 sub-task #1) — the Usage-tab
endpoint helper that rolls per-session fields into fleet totals.
"""
import clawmetry.sync as S
from routes.sessions import _derive_waste_summary
from routes.usage import _agg_compression


class _Ev:
    def __init__(self, etype="tool_result", content="", tool="", model=""):
        self.type = etype
        self.content = content
        self.tool_name = tool
        self.extra = {}
        self.model = model


def test_classify_compressible():
    assert S._classify_compressible('[{"a":1},{"a":2}]') == "json"
    assert S._classify_compressible('{"k": "v"}') == "json"
    assert S._classify_compressible("diff --git a/x b/x\n@@ -1 +1 @@") == "diff"
    log = "\n".join("2026-06-08 12:00:0%d INFO started worker" % (i % 9) for i in range(14))
    assert S._classify_compressible(log) == "log"
    assert S._classify_compressible("a short human sentence") == "text"
    assert S._classify_compressible("") == "text"


def test_detector_json_is_highly_compressible():
    big = "[" + ",".join('{"path":"/p/%d","size":%d,"ok":true}' % (i, i) for i in range(200)) + "]"
    out = S._session_compression_potential([_Ev(content=big, tool="Grep")], model="claude-sonnet-4-5")
    assert out["compressionPotentialPct"] >= 50
    assert out["compressibleToolTokens"] > 0
    assert "json" in out["compressionByType"]
    # privacy: only aggregates, never raw content
    assert "content" not in out
    assert all(isinstance(v, int) for v in out["compressionByType"].values())


def test_detector_skips_small_and_prose():
    assert S._session_compression_potential([_Ev(content="ok")]) == {}
    prose = "This is a normal prose answer. " * 30
    out = S._session_compression_potential([_Ev(content=prose, tool="Read")])
    # prose has 0 compressible ratio -> nothing recoverable -> empty
    assert out == {}


def test_detector_never_raises_on_garbage():
    assert S._session_compression_potential(None) == {}
    assert S._session_compression_potential([_Ev(content=None)]) == {}
    assert S._session_compression_potential([object()]) == {}


def test_waste_summary_rolls_up_compression_and_cache_expiry():
    sessions = [
        {"session_id": "a", "cost_usd": 1.0,
         "compression_potential_pct": 85.0, "compressible_tool_tokens": 5000,
         "compression_recoverable_usd": 0.02, "cache_expiry_count": 3},
        {"session_id": "b", "cost_usd": 1.0,
         "compression_potential_pct": 10.0, "compressible_tool_tokens": 100},  # below threshold
    ]
    w = _derive_waste_summary(sessions)
    assert w["compressible_sessions"] == 1
    assert w["compressible_tokens"] == 5000
    assert round(w["compressible_usd"], 2) == 0.02
    assert w["cache_expiry_sessions"] == 1
    assert w["cache_expiry_count"] == 3


# ---------------------------------------------------------------------------
# _agg_compression (issue #2837 sub-task #1)
# ---------------------------------------------------------------------------

def test_agg_compression_rolls_up_qualifying_sessions():
    rows = [
        {"compression_potential_pct": 85.0, "compressible_tool_tokens": 5000,
         "compression_recoverable_usd": 0.03, "dominant_compression_type": "json"},
        {"compression_potential_pct": 60.0, "compressible_tool_tokens": 3000,
         "compression_recoverable_usd": 0.01, "dominant_compression_type": "diff"},
        # below threshold: pct < 50
        {"compression_potential_pct": 30.0, "compressible_tool_tokens": 5000,
         "compression_recoverable_usd": 0.01},
        # below threshold: tokens < 2000
        {"compression_potential_pct": 80.0, "compressible_tool_tokens": 500,
         "compression_recoverable_usd": 0.01},
    ]
    out = _agg_compression(rows)
    assert out["compressible_sessions"] == 2
    assert out["total_sessions"] == 4
    assert out["compressible_tokens"] == 8000
    assert round(out["recoverable_usd"], 2) == 0.04
    assert out["by_type"]["json"] == 5000
    assert out["by_type"]["diff"] == 3000


def test_agg_compression_empty_input():
    assert _agg_compression([]) == {}
    assert _agg_compression(None) == {}


def test_agg_compression_all_below_threshold():
    rows = [
        {"compression_potential_pct": 40.0, "compressible_tool_tokens": 10000},
        {"compression_potential_pct": 90.0, "compressible_tool_tokens": 100},
    ]
    assert _agg_compression(rows) == {}
