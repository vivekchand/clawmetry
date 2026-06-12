"""CCR — reversible event-payload compression for the DuckDB store (#2843).

Headroom-inspired (chopratejas/headroom): tool outputs (search results, logs,
diffs, big JSON) dominate transcript size. We optionally gzip the event ``data``
BLOB at ingest and transparently inflate it on read, cutting local DuckDB +
the E2E cloud snapshot by a large margin with ZERO loss.

Design for safety:
- The decoder is AUTO-DETECTING: a compressed blob carries a 5-byte magic
  prefix; ``maybe_decompress`` inflates only when it sees the magic and returns
  everything else untouched. So old (uncompressed) rows and new (compressed)
  rows both read correctly regardless of the write flag, and turning the flag
  off later never strands already-compressed rows.
- Compression on WRITE is OFF by default (``CLAWMETRY_CCR=1`` to enable), so the
  default path is byte-for-byte unchanged. Self-hosters opt in.
- zlib only (stdlib) — no new dependency, per the minimal-deps rule.
"""
from __future__ import annotations

import os
import zlib

# 5-byte magic. \x1f is never the first byte of our UTF-8 JSON payloads
# ({, [, ", digit, whitespace), so detection is unambiguous.
_MAGIC = b"\x1fCCR1"
# Only compress payloads above this size; tiny blobs do not benefit and the
# magic prefix would be pure overhead.
_MIN_BYTES = 2048


def enabled() -> bool:
    """True when CCR compression-on-write is opted in via env. Read path is
    always on (auto-detecting), so this only gates whether we compress."""
    return str(os.environ.get("CLAWMETRY_CCR", "")).strip().lower() in ("1", "true", "yes", "on")


def compress(raw: bytes, *, force: bool = False) -> bytes:
    """Compress ``raw`` (utf-8 JSON bytes) to ``_MAGIC + zlib`` IF it is large
    enough; otherwise return it unchanged. Never raises — on any error the
    original bytes pass through so ingest can never break."""
    if not isinstance(raw, (bytes, bytearray)):
        return raw
    raw = bytes(raw)
    if not force and len(raw) < _MIN_BYTES:
        return raw
    if raw.startswith(_MAGIC):  # already compressed — idempotent
        return raw
    try:
        packed = _MAGIC + zlib.compress(raw, 6)
        # Never let the "compressed" form be bigger than the original.
        return packed if len(packed) < len(raw) else raw
    except Exception:
        return raw


def maybe_decompress(raw):
    """Inflate a CCR blob; pass anything else through untouched. Accepts bytes
    or str (str is returned as-is — it cannot carry the binary magic). Never
    raises; on a corrupt blob returns the raw bytes so the caller's own decode
    path decides what to do."""
    if not isinstance(raw, (bytes, bytearray)):
        return raw
    raw = bytes(raw)
    if not raw.startswith(_MAGIC):
        return raw
    try:
        return zlib.decompress(raw[len(_MAGIC):])
    except Exception:
        return raw
