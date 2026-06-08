"""Tests for the compression-potential meter (#2838) and the fleet waste
aggregation that surfaces it (#2839 cache-risk roll-up).

Measurement only: we assert the heuristics classify content correctly, the
detector estimates recoverable token share, persists ONLY aggregates (never raw
content), and the waste summary rolls per-session metrics into fleet figures.
"""
import clawmetry.sync as S
from routes.sessions import _derive_waste_summary


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
