"""Compression / cache-safety eval suite — Tier-1 deterministic gate (#2844, epic #2837).

Headroom (chopratejas/headroom) earns the right to claim "compression-safe" by
running needle-retention / UUID-retrieval / anomaly-preservation evals: prove the
pipeline never silently drops the one token that mattered. This suite ports that
rigor to ClawMetry's two cost-intelligence surfaces and hardens them against
regressions:

  * CCR reversible payload compression (``clawmetry/ccr.py``, #2843) — must be
    byte-for-byte lossless, so a critical needle buried in a 100 KB tool result
    survives compress -> store -> decompress exactly.
  * The cache-risk / compression-potential METRICS (``proxy.scan_volatile_content``
    / ``proxy.detect_cache_risk`` #2839, ``sync._session_compression_potential``
    #2838) — must persist ONLY aggregates and never echo a raw secret
    (UUID / JWT / timestamp) back into the metric, even though they scan content
    that may contain them.

Tiers (the CI gate is graduated, cheapest first):

  * Tier-1 (this file): pure-Python, deterministic, ZERO API spend. Runs on every
    PR as a required check — see ``.github/workflows/ci.yml``.
  * Tier-2/3 (LLM-judge needle retrieval over real transcripts): gated behind an
    API key and skipped without one, following the existing
    ``tests/test_eval_skip_without_key.py`` pattern. Out of scope for the cheap
    PR gate; tracked under epic #2837.
"""
import json

import clawmetry.ccr as ccr
import clawmetry.proxy as proxy
import clawmetry.sync as sync


# ── Fixtures: a known needle, UUID and anomaly buried in bulk content ─────────

NEEDLE = "NEEDLE-7f3a91-CRITICAL-this-line-must-survive-compression"
KNOWN_UUID = "550e8400-e29b-41d4-a716-446655440000"
KNOWN_JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"


def _bulk_json(n: int = 2000) -> str:
    """A large, highly-compressible tool-result-shaped JSON blob (well over CCR's
    2 KB floor) — the kind of payload that dominates transcript size."""
    return "[" + ",".join(
        '{"i":%d,"path":"/var/log/app/%d.log","msg":"routine padding entry %d","ok":true}' % (i, i, i)
        for i in range(n)
    ) + "]"


def _embed(haystack: str, needle: str, at: int = 1000) -> str:
    return haystack[:at] + needle + haystack[at:]


# ── Tier-1a: CCR is byte-for-byte lossless (the core "compression-safe" claim) ─

def test_needle_retention_survives_ccr_roundtrip():
    """A critical needle buried in a 100 KB payload must come back byte-identical."""
    raw = _embed(_bulk_json(), NEEDLE).encode()
    packed = ccr.compress(raw, force=True)

    assert packed[:5] == b"\x1fCCR1"          # actually compressed (magic present)
    assert len(packed) < len(raw)             # and it paid for itself
    restored = ccr.maybe_decompress(packed)
    assert restored == raw                    # byte-for-byte, no loss
    assert NEEDLE in restored.decode()        # the needle specifically survived


def test_uuid_retrieval_survives_ccr_roundtrip():
    """UUIDs / request-ids are exactly the tokens an LLM later needs to cite —
    a lossy codec that mangled one would be silent corruption."""
    raw = _embed(_bulk_json(), f'{{"request_id":"{KNOWN_UUID}"}}').encode()
    restored = ccr.maybe_decompress(ccr.compress(raw, force=True))
    assert restored == raw
    assert KNOWN_UUID in restored.decode()


def test_anomaly_preservation_survives_ccr_roundtrip():
    """A single anomalous line among thousands of uniform ones is the highest-value,
    lowest-redundancy content — verify it is preserved, not "smoothed away"."""
    lines = ["2026-06-09 12:00:%02d INFO worker heartbeat ok" % (i % 60) for i in range(4000)]
    anomaly = "2026-06-09 12:34:56 FATAL OOMKilled pid=9999 unrecoverable anomaly-marker-XYZ"
    lines[2718] = anomaly
    raw = ("\n".join(lines)).encode()
    restored = ccr.maybe_decompress(ccr.compress(raw, force=True))
    assert restored == raw
    assert anomaly in restored.decode()


def test_ccr_lossless_across_payload_shapes():
    """json / log / diff / unicode all round-trip identically — no shape is special-cased."""
    samples = [
        _bulk_json(),
        "\n".join("2026-06-09 12:00:00 INFO line %d" % i for i in range(3000)),
        "diff --git a/x b/x\n" + "\n".join("+added line %d" % i for i in range(3000)),
        ("café — naïve — 日本語 — emoji 🚀 — " * 500),
    ]
    for s in samples:
        raw = s.encode()
        assert ccr.maybe_decompress(ccr.compress(raw, force=True)) == raw


def test_ccr_passthrough_is_safe_for_uncompressed_and_corrupt_blobs():
    """The read path auto-detects, so plain rows and a truncated/corrupt CCR blob
    must NEVER raise and must return usable bytes — losing a row would lose data."""
    plain = b"plain uncompressed row " + NEEDLE.encode()
    assert ccr.maybe_decompress(plain) == plain          # no magic -> untouched
    corrupt = b"\x1fCCR1" + b"not-valid-zlib-stream"
    assert ccr.maybe_decompress(corrupt) == corrupt      # bad blob -> raw, no crash


# ── Tier-1b: the metrics never leak the secrets they scan (privacy-safe) ──────

def test_volatile_scan_emits_counts_only_never_raw_values():
    """scan_volatile_content reads content that may hold secrets but must persist
    only per-pattern COUNTS — never the matched UUID / JWT / timestamp itself."""
    text = f"You are an agent. session {KNOWN_UUID} built 2026-06-09T12:00:00 auth {KNOWN_JWT}"
    out = proxy.scan_volatile_content(text)

    assert out.get("uuid") == 1 and out.get("jwt") == 1   # detected...
    assert all(isinstance(v, int) for v in out.values())  # ...as integers only
    blob = repr(out)
    assert KNOWN_UUID not in blob and KNOWN_JWT not in blob  # raw values never echoed


def test_cache_risk_persists_score_not_secrets():
    """detect_cache_risk's persisted shape is score + counts + a hash — a request
    body full of secrets must not surface any raw secret in the result."""
    body = {
        "model": "claude-sonnet-4-5",
        "system": f"You are an agent. tenant {KNOWN_UUID}",
        "tools": [{"name": "auth", "description": f"bearer {KNOWN_JWT}"}],
    }
    cr = proxy.detect_cache_risk(body)

    assert cr["cache_risk_score"] >= 2                    # uuid + jwt counted
    assert isinstance(cr["cache_risk_score"], int)
    assert cr["volatile"] == {k: v for k, v in cr["volatile"].items() if isinstance(v, int)}
    blob = json.dumps(cr)
    assert KNOWN_UUID not in blob and KNOWN_JWT not in blob


def test_compression_potential_persists_aggregates_not_content():
    """The compression-potential detector estimates recoverable tokens from tool
    output but must persist ONLY aggregates — a needle in the content stays out."""
    class _Ev:
        def __init__(self, content):
            self.type = "tool_result"
            self.content = content
            self.tool_name = "Grep"
            self.extra = {}
            self.model = ""

    payload = _embed(_bulk_json(), NEEDLE)
    out = sync._session_compression_potential([_Ev(payload)], model="claude-sonnet-4-5")

    assert out and out["compressionPotentialPct"] > 0
    assert all(not isinstance(v, str) for v in out.values())  # numbers only, no content
    assert NEEDLE not in repr(out)
    assert "content" not in out


def test_metrics_never_raise_on_garbage():
    """Safety eval invariant: the cost-intelligence surfaces are best-effort and
    must degrade to empty/zero on malformed input rather than break ingest."""
    assert proxy.scan_volatile_content(None) == {}
    assert proxy.scan_volatile_content("") == {}
    assert proxy.detect_cache_risk({})["cache_risk_score"] == 0
    assert sync._session_compression_potential(None) == {}
    assert sync._session_compression_potential([object()]) == {}
