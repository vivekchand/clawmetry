"""CCR codec + safety eval (#2843, #2844): reversible, auto-detecting, lossless,
never larger, and a no-op on uncompressed/foreign blobs so every reader is safe."""
import json
import os
import importlib

import clawmetry.ccr as ccr


def test_roundtrip_lossless():
    payload = json.dumps([{"path": "/x/%d" % i, "ok": True} for i in range(500)]).encode()
    packed = ccr.compress(payload, force=True)
    assert packed.startswith(b"\x1fCCR1")
    assert ccr.maybe_decompress(packed) == payload     # byte-identical
    # large repetitive content actually shrinks
    assert len(packed) < len(payload)


def test_decoder_is_a_noop_on_plain_blobs():
    plain = b'{"hello":"world"}'
    assert ccr.maybe_decompress(plain) == plain         # plain JSON untouched
    assert ccr.maybe_decompress("a string") == "a string"
    assert ccr.maybe_decompress(None) is None
    # decoding random non-magic bytes returns them unchanged (reader then decides)
    assert ccr.maybe_decompress(b"\x00\x01\x02") == b"\x00\x01\x02"


def test_small_payloads_not_compressed():
    tiny = b'{"a":1}'
    assert ccr.compress(tiny) == tiny                   # below threshold, unchanged
    assert not ccr.compress(tiny).startswith(b"\x1fCCR1")


def test_compress_is_idempotent_and_never_grows():
    p = ("x" * 5000).encode()
    once = ccr.compress(p, force=True)
    assert ccr.compress(once, force=True) == once       # idempotent
    # incompressible-but-small magic guard: never returns something bigger
    assert len(ccr.compress(p, force=True)) <= len(p) + len(b"\x1fCCR1")


def test_enabled_reads_env(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_CCR", raising=False)
    assert ccr.enabled() is False
    monkeypatch.setenv("CLAWMETRY_CCR", "1")
    assert ccr.enabled() is True


def test_event_row_seam_roundtrip_byte_identical(monkeypatch):
    """The real write->read seam: with CCR ON a large event compresses on write
    (_event_to_row) and inflates byte-identical on read (_row_to_event)."""
    monkeypatch.setenv("CLAWMETRY_CCR", "1")
    import clawmetry.local_store as ls
    big = {"tool": "Grep", "results": [{"path": "/p/%d" % i, "line": "x" * 40} for i in range(300)]}
    ev = {"id": "ev1", "agent_type": "openclaw", "node_id": "n", "agent_id": "main",
          "session_id": "s1", "event_type": "tool_result", "ts": "2026-06-08T00:00:00Z",
          "data": big}
    row = ls._event_to_row(ev)
    # the stored data BLOB is actually compressed (carries the CCR magic)
    data_idx = ls._EVENT_COLS.index("data")
    assert row[data_idx].startswith(b"\x1fCCR1"), "large event was not compressed with CCR on"
    back = ls._row_to_event(row, ls._EVENT_COLS)
    assert back["data"] == big, "CCR seam changed the payload"


def test_event_row_seam_default_off_is_unchanged(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_CCR", raising=False)
    import clawmetry.local_store as ls
    big = {"results": [{"k": "v" * 50} for i in range(300)]}
    row = ls._event_to_row({"id": "e", "agent_type": "openclaw", "node_id": "n",
                            "agent_id": "main", "session_id": "s", "event_type": "t",
                            "ts": "x", "data": big})
    data_idx = ls._EVENT_COLS.index("data")
    assert not row[data_idx].startswith(b"\x1fCCR1"), "default path must NOT compress"
    assert ls._row_to_event(row, ls._EVENT_COLS)["data"] == big
