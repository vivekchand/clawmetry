"""clawmetry/event_shape.py: ONE normalizer for every stored event shape.

Every reader used to carry its own ladder for "who spoke, was it a tool,
which tool, did it fail" (routes/sessions.py, routes/tracing.py,
routes/reasoning.py, routes/turn_anatomy.py), and the four drifted apart:
a Claude Code ``tool_use`` block was a tool span in Tracing, a "model" step
in Turn Anatomy and invisible to Reasoning. This module is the single
answer, used both at ingest (to fill the typed ``events.role`` /
``block_kind`` / ``tool_name`` / ``is_error`` columns) and at read time.

``block_kind`` is deliberately aligned with :mod:`clawmetry.replay_schema`
kinds so a typed event column and a replay event agree on vocabulary:

    replay ``thinking``     -> block_kind ``thinking``
    replay ``tool.call``    -> block_kind ``tool_use``
    replay ``tool.result``  -> block_kind ``tool_result``
    replay ``llm.response`` -> block_kind ``text`` (role assistant)
    replay ``llm.call``     -> block_kind ``text`` (role user)

The remaining kinds are ``system`` (harness context, compaction, errors
the runtime reported about itself) and ``other`` (plumbing: session
markers, heartbeats, model changes).

Shapes covered (each has a test in tests/test_event_shape.py):

* OpenClaw v3 as normalised by ``sync._parse_v3_event`` and the legacy
  trajectory parser: ``prompt.submitted`` (``finalPromptText``),
  ``model.completed`` / ``trace.artifacts`` (``completionText`` /
  ``assistantTexts`` + ``toolMetas``), ``tool.call`` / ``tool.invoked``
  (``name`` / ``input``), ``tool.result`` / ``tool.completed``
  (``output`` / ``result`` / ``is_error``), ``context.compiled``,
  ``compaction``, ``workspace.conflict``, the ``session.*`` markers. The
  content keys may sit on ``data`` directly or under a nested ``data.data``
  (the trajectory envelope); both are read.
* Raw Claude Code transcript rows (``type`` user/assistant with the
  Anthropic message under ``data.message``: ``content`` is a string or a
  list of ``text`` / ``thinking`` / ``tool_use`` / ``tool_result`` blocks).
* The family-adapter row every pro adapter (Codex, Cursor, Gemini CLI,
  Copilot, Goose, ...) writes through ``sync.py``: ``event_type`` in
  {message, tool_call, tool_result, thinking, compaction, error, ...} with
  ``data.role`` / ``data.content`` / ``data.tool_name`` / ``data.tool_calls``
  and the error flag under ``data.extra.isError``.
* Flat Anthropic-style messages (``role`` + ``content`` + ``tool_calls``),
  and the Claude Code native-OTel intake rows (``user_prompt``,
  ``llm_call``, ``api_error``, ``waiting_on_user``).

``classify`` never raises and never fabricates: a shape it cannot place
comes back as ``role ""`` / ``block_kind "other"`` with empty text.
"""
from __future__ import annotations

from typing import Any, Iterable
from clawmetry.event_shape_classify import (  # noqa: E402
    _classify,
    _empty,
    _s,
    split_blocks,
)

__all__ = [
    "typed_columns",
    "BLOCK_KINDS",
    "ROLES",
    "classify",
    "split_blocks",
    "first_user_prompt",
    "clean_prompt_text",
    "INTENT_MAX_CHARS",
]

BLOCK_KINDS = ("text", "thinking", "tool_use", "tool_result", "system", "other")
ROLES = ("user", "assistant", "system", "tool", "")

#: ``sessions.intent`` is the FULL first user prompt, but bounded: a pasted
#: log file is not an intent, and the column rides the encrypted cloud slice.
INTENT_MAX_CHARS = 4000


# ── Public API (the three entry points other modules call) ─────────────────

def typed_columns(event_type: Any, data: Any) -> tuple:
    """The four typed ``events`` columns for one row, in insert order:
    ``(role, block_kind, tool_name, is_error)``.

    Called by the store's row builder for EVERY new event row, so a row
    written after schema v15 carries its classification from the moment it
    is inserted; the daemon's bounded back-fill only exists for rows that
    predate v15. ``block_kind`` is never NULL on a stamped row (``other``
    when nothing fits), which is also the marker the back-fill uses to skip
    rows it has already visited.
    """
    shape = classify(event_type, data)
    return (
        shape["role"] or None,
        shape["block_kind"] or "other",
        shape["tool_name"] or None,
        bool(shape["is_error"]),
    )


def first_user_prompt(rows: Iterable[Any], max_chars: int = INTENT_MAX_CHARS) -> str:
    """The full text of the first real user prompt in ``rows``.

    ``rows`` are stored event dicts (``event_type`` + ``data``, oldest first
    or not; the earliest by ``ts`` wins), the raw dicts a transcript batch
    hands the ingester, or adapter ``Event`` objects (``type`` / ``role`` /
    ``content``). Capped at ``max_chars`` with an ellipsis marker. "" when
    no qualifying prompt exists. Never raises."""
    best_ts: Any = None
    best = ""
    try:
        for r in rows:
            et, data, ts = _row_parts(r)
            shape = classify(et, data)
            if shape["role"] != "user" or shape["block_kind"] != "text":
                continue
            text = clean_prompt_text(shape["text"])
            if not text:
                continue
            key = _s(ts)
            if best and best_ts is not None and key and key >= best_ts:
                continue
            best, best_ts = text, key
            if not key:
                break  # unordered input: first hit wins
    except Exception:  # noqa: BLE001
        return best[:max_chars]
    if len(best) > max_chars:
        best = best[: max_chars - 3].rstrip() + "..."
    return best


def clean_prompt_text(text: Any) -> str:
    """Whitespace-normalised prompt text, or "" when it cannot be a human
    prompt (harness wrappers such as ``<system-reminder>``, the resumed-
    session ``Caveat:`` preamble). Same rule ``session_titles`` applies, so
    the 80-char title and the full intent always come from the same turn."""
    if not isinstance(text, str):
        return ""
    stripped = text.strip()
    if not stripped or stripped.startswith(_PROMPT_SKIP_PREFIXES):
        return ""
    return "\n".join(" ".join(line.split()) for line in stripped.splitlines()).strip()


# Harness-injected wrappers that can never be a human prompt: the
# "<system-reminder>" / "<command-name>" frames and the resume preamble.
_PROMPT_SKIP_PREFIXES = ("<", "Caveat:")


# ── the classifier ─────────────────────────────────────────────────────────

def classify(event_type: Any, data: Any) -> dict[str, Any]:
    """Normalise one stored event into ``{role, block_kind, tool_name,
    is_error, text, thinking, ...}``.

    ``event_type`` is the stored ``events.event_type`` column; ``data`` is
    the decoded ``events.data`` payload (dict, JSON string or bytes are all
    accepted). Extra keys ``thinking_blocks``, ``tool_uses`` and
    ``tool_results`` carry the structured parts for readers that render each
    block separately (the transcript, the trace).

    Precedence when one event carries several block types (a Claude Code
    assistant turn that thinks, speaks and calls a tool): ``tool_result`` >
    ``tool_use`` > ``text`` > ``thinking``. The typed column records the
    event's most action-like part; the structured lists carry the rest.
    """
    try:
        return _classify(event_type, data)
    except Exception:  # noqa: BLE001 - a classifier bug must never drop a row
        return _empty(_s(event_type))


# ── intent (first user prompt) ────────────────────────────────────────────

def _row_parts(r: Any) -> tuple:
    if isinstance(r, dict):
        if "event_type" in r and "data" in r:
            # A stored event row (or the dict the ingester queues).
            return r.get("event_type") or "", r.get("data"), r.get("ts") or ""
        # A raw transcript line: the whole object is the payload.
        return (r.get("type") or r.get("event_type") or ""), r, \
            (r.get("timestamp") or r.get("ts") or "")
    # adapter Event dataclass
    et = getattr(r, "type", "") or "message"
    data = {
        "role": getattr(r, "role", "") or "",
        "content": getattr(r, "content", "") or "",
        "tool_name": getattr(r, "tool_name", "") or "",
    }
    return et, data, getattr(r, "ts", "") or ""
