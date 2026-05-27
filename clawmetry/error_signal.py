"""Shared tool-result error classification.

A number of tool results carry an ``isError`` / ``is_error`` flag (or an
``error``-suffixed event type) for outcomes that are not real failures: a
runtime read-guard telling the agent to re-read a file, a transient gateway
timeout that succeeded on retry, and similar control-flow nudges. Counting
these as errors inflated error rates across the Tracing / Health / Self-Evolve
surfaces and the snapshot (measured live: two read-guard signatures alone were
~two thirds of all flagged tool errors).

This module is the single source of truth for "is this flagged error actually
benign?". It is a dependency-free leaf module so both the daemon ingest path
(``clawmetry.sync``) and the request handlers (``routes/*``) can import it
without circular-import risk. Nothing here raises.

The signatures are intentionally conservative and easy to tune: each entry is a
plain substring matched (case-insensitively) against the tool result's text.
"""

from __future__ import annotations

from typing import Any

# Substrings that mark a flagged tool result as benign (not a real failure).
# Matched case-insensitively against the result text. Keep this list tight and
# evidence-backed — every entry suppresses a real ``isError`` flag, so a
# too-broad signature would hide genuine failures.
BENIGN_TOOL_ERROR_SIGNATURES: tuple[str, ...] = (
    # Claude Code Edit/Write read-guards: the runtime asks the agent to read
    # (or re-read) the file first, the agent complies, and the turn proceeds.
    # Control-flow nudges, not task failures.
    "file has not been read yet",
    "file has been modified since read",
    # Transient gateway timeout that the runtime retries; surfaces as a flagged
    # result even when the retry succeeds.
    "gateway timeout after",
)


def is_benign_tool_error(text: Any) -> bool:
    """True if ``text`` (a tool result body) matches a known-benign signature.

    Defensive: non-string / empty input is treated as not-benign so we never
    suppress an error we couldn't actually read.
    """
    if not text:
        return False
    try:
        low = str(text).lower()
    except Exception:
        return False
    return any(sig in low for sig in BENIGN_TOOL_ERROR_SIGNATURES)


def extract_tool_result_text(data: Any) -> str:
    """Best-effort plain text of a tool result, across runtime shapes.

    Handles the OpenClaw v3 shape (``data.output`` / ``data.result`` strings)
    and the Claude Code family shape (``data.content`` as a string or a list of
    ``{type, text|content}`` blocks, including the ``<tool_use_error>`` wrapper).
    Returns ``""`` on anything unrecognised. Never raises.
    """
    if not isinstance(data, dict):
        return ""
    try:
        # v3 / flattened string fields first.
        for key in ("output", "result", "preview", "full", "detail"):
            v = data.get(key)
            if isinstance(v, str) and v:
                return v
        # Claude Code family: content is a string or a list of blocks.
        content = data.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for blk in content:
                if isinstance(blk, dict):
                    t = blk.get("text") or blk.get("content")
                    if isinstance(t, str):
                        parts.append(t)
                elif isinstance(blk, str):
                    parts.append(blk)
            return " ".join(parts)
    except Exception:
        return ""
    return ""


def corrected_is_error(raw_is_error: Any, result_text: Any) -> bool:
    """Return the error flag with benign results filtered out.

    ``raw_is_error and not is_benign_tool_error(result_text)``, coerced to a
    plain bool. Use at ingest so the stored flag (and therefore every reader and
    the snapshot) reflects the corrected value.
    """
    if not raw_is_error:
        return False
    return not is_benign_tool_error(result_text)
