"""
clawmetry/token_confidence.py — Token Probability Visualizer (issue #563).

Per-LLM-call "How confident was the model in each word?" panel for the
Brain tab. Pure function: takes one event dict, returns a small payload the
frontend renders as an inline heatmap with hover-tooltip alternatives.

Phase 1 (this module): wire the data path end-to-end whenever upstream
already captured ``logprobs`` (OpenAI / Gemini compatible providers). When
no logprobs are present (every Anthropic call today, 2026-05-16) we return
``None`` so the frontend can paint a single-line "not available" hint
instead of an empty box.

Phase 2 (separate issue): land an OpenClaw adapter PR that requests
``logprobs=True`` from supporting providers and stores the per-token
distribution on the event row. ClawMetry only needs to read it.

Design notes
------------
* **Pure + total.** ``extract_token_confidence`` takes any event-shaped
  dict and returns either a payload dict or ``None``. Never raises.
* **No new dependencies.** Reads the same ``logprobs.content`` shape
  ``risk.py`` already understands (OpenAI chat-completions response):
  ``[{"token": str, "logprob": float, "top_logprobs": [{"token", "logprob"}]}]``.
* **Cap at 200 tokens.** Brain tab paints these inline; we don't want a
  5,000-token transcript to dominate the DOM. Tail tokens get summarised.
* **No-em-dash copy** in the explanation strings (memory:
  ``feedback_no_em_dashes_in_user_facing_copy.md``).
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Optional

# Hard cap so a multi-thousand-token completion does NOT blow up the Brain
# tab DOM. Matches the cap in ``risk._extract_logprob_summary`` for
# consistency. The frontend shows "… N more tokens" when truncated.
_MAX_TOKENS = 200

# How many alternative top-k tokens to surface in the hover tooltip. The
# OpenAI API caps top_logprobs at 20; 5 is a reasonable default for an
# inline tooltip (matches the issue spec).
_TOP_K = 5

# Probability bands → colour pill rendered by the frontend. Boundaries
# match the issue spec exactly.
#
#   p >= 0.9  → green   (high confidence)
#   p >= 0.5  → yellow  (medium)
#   p >= 0.2  → orange  (low)
#   p <  0.2  → red     (high-variance decision point)
#
# The frontend owns the colour mapping; we just stamp a band letter so the
# contract is forward-compatible (re-skinning is a CSS change).
_BANDS = [
    (0.9, "h"),  # high
    (0.5, "m"),  # medium
    (0.2, "l"),  # low
    (0.0, "v"),  # very-low (high variance)
]


def _band_for(prob: float) -> str:
    for threshold, label in _BANDS:
        if prob >= threshold:
            return label
    return "v"


def _logprob_to_prob(lp: float) -> float:
    """Convert a (typically negative) logprob to a probability in [0, 1]."""
    try:
        p = math.exp(float(lp))
    except (OverflowError, ValueError):
        return 0.0
    # Clamp to defend against floating-point > 1.0 from upstream.
    if p < 0.0:
        return 0.0
    if p > 1.0:
        return 1.0
    return p


def _find_logprobs_list(event_data: Mapping[str, Any]) -> Optional[list]:
    """Return the ``logprobs.content`` list from any common event shape."""
    if not isinstance(event_data, Mapping):
        return None
    candidates = [event_data]
    data = event_data.get("data") if isinstance(event_data.get("data"), Mapping) else None
    if data is not None:
        candidates.append(data)
        msg = data.get("message") if isinstance(data.get("message"), Mapping) else None
        if msg is not None:
            candidates.append(msg)
    for bucket in candidates:
        if not isinstance(bucket, Mapping):
            continue
        lp = bucket.get("logprobs")
        if isinstance(lp, Mapping):
            content = lp.get("content")
            if isinstance(content, list) and content:
                return content
        # Some adapters flatten to ``logprob_content`` directly.
        if isinstance(bucket.get("logprob_content"), list) and bucket["logprob_content"]:
            return bucket["logprob_content"]
    return None


def _token_row(entry: Mapping[str, Any]) -> Optional[dict]:
    """Project one OpenAI-shape token entry into the Brain payload row."""
    if not isinstance(entry, Mapping):
        return None
    token = entry.get("token")
    lp = entry.get("logprob")
    if not isinstance(token, str) or not isinstance(lp, (int, float)):
        return None
    prob = _logprob_to_prob(lp)

    # Top-k alternatives. We keep them sorted by descending probability and
    # capped at ``_TOP_K``. Each alt mirrors the {token, prob} shape so the
    # frontend doesn't have to do logprob math.
    alts_raw = entry.get("top_logprobs")
    alts: list[dict] = []
    if isinstance(alts_raw, list):
        for alt in alts_raw:
            if not isinstance(alt, Mapping):
                continue
            at = alt.get("token")
            alp = alt.get("logprob")
            if not isinstance(at, str) or not isinstance(alp, (int, float)):
                continue
            alts.append({"token": at, "prob": round(_logprob_to_prob(alp), 4)})
        alts.sort(key=lambda r: r["prob"], reverse=True)
        alts = alts[:_TOP_K]

    # Rank: how many alternatives outranked the chosen token? Rank 1 = the
    # model picked its top choice; rank >= 2 means decoding sampled a
    # lower-probability option (interesting for debugging).
    rank = 1
    for alt in alts:
        if alt["prob"] > prob and alt["token"] != token:
            rank += 1

    return {
        "token": token,
        "prob": round(prob, 4),
        "band": _band_for(prob),
        "top_k": alts,
        "rank": rank,
    }


def extract_token_confidence(event_data: Mapping[str, Any]) -> Optional[dict]:
    """Return a payload describing per-token confidence, or ``None``.

    Payload shape::

        {
          "tokens": [
            {"token": "Hello", "prob": 0.98, "band": "h",
             "top_k": [{"token": "Hi", "prob": 0.01}, ...], "rank": 1},
            ...
          ],
          "summary": {
            "token_count": 42,           # tokens included after capping
            "total_tokens": 42,          # raw count before capping
            "avg_prob": 0.83,            # mean across included tokens
            "min_prob": 0.18,            # the most "surprising" token
            "high_variance_count": 3,    # # tokens in red band (p < 0.2)
            "band": "h" | "m" | "l" | "v",
          },
          "truncated": false,
        }

    Returns ``None`` when no logprobs are available (the common case until
    OpenClaw wires logprobs collection in Phase 2). The frontend uses
    ``None`` as the signal to paint the "not available" hint instead.
    """
    content = _find_logprobs_list(event_data)
    if not content:
        return None

    rows: list[dict] = []
    for entry in content[:_MAX_TOKENS]:
        row = _token_row(entry)
        if row is not None:
            rows.append(row)
    if not rows:
        return None

    probs = [r["prob"] for r in rows]
    avg_prob = sum(probs) / len(probs)
    min_prob = min(probs)
    high_variance_count = sum(1 for p in probs if p < 0.2)
    summary = {
        "token_count": len(rows),
        "total_tokens": len(content),
        "avg_prob": round(avg_prob, 4),
        "min_prob": round(min_prob, 4),
        "high_variance_count": high_variance_count,
        "band": _band_for(avg_prob),
    }
    return {
        "tokens": rows,
        "summary": summary,
        "truncated": len(content) > _MAX_TOKENS,
    }


def annotate_events(events) -> None:
    """Stamp ``ev["token_confidence"]`` on every LLM-call event in place.

    Mirrors ``routes/brain._annotate_risk``. Silent fallback per event so
    one mis-shaped row never poisons the whole feed (CLAUDE.md "graceful
    fallbacks on bad input").
    """
    if not events:
        return
    # Lazy import to avoid pulling routes.brain into clawmetry.* at import
    # time (routes/* already imports clawmetry/*).
    try:
        from clawmetry.risk import is_llm_event
    except Exception:
        return
    for ev in events:
        try:
            if not is_llm_event(ev):
                continue
            payload = extract_token_confidence(ev)
            if payload is not None:
                ev["token_confidence"] = payload
        except Exception:
            # Never crash — Brain renders thousands per page-load.
            pass


# ── Alternatives-considered capture (issue #1616) ────────────────────────
#
# "What else did the agent reject?" Per OpenClaw blog Pillar #2 (Decision
# Auditing). For every tool.call event we walk the preceding model output
# and surface the alternatives the model evaluated. Two real sources:
#
#   1. OpenAI logprobs on the model.completed event that produced the
#      tool call — the top-k tokens at the first identifying position of
#      the tool name. (PR #1609 already plumbed these through.)
#   2. Extended-thinking text blocks (Claude / Gemini) that explicitly
#      narrate "I considered X but chose Y because Z". Common when the
#      model is run with thinking turned on.
#
# Anything else returns an empty alternatives list so the frontend can
# paint an honest "not available for this model" hint instead of made-up
# options. User trust > fake completeness (see PR-prompt critical note).

# Cap alts so the panel stays scannable. The OpenAI top_logprobs ceiling
# is 20; 4 is a reasonable signal-to-noise default for tool selection.
_TOOL_TOP_K = 4

# How many event rows backwards to look for the LLM completion that
# produced this tool call. Sub-agents can interleave a few EXEC/READ rows
# between the model output and the call; 8 covers the realistic worst
# case without scanning the whole 24h window.
_TOOL_LOOKBACK = 8

# Regex hits we accept inside extended-thinking text as a self-reported
# alternative narration. Order matters — first match wins so the most
# explicit pattern is tried first. Each group capture is (chosen, rejected).
#
# Memory respect: no em-dashes in user-facing copy. These patterns parse
# model output, not output we author, so dashes here are fine.
import re as _re

_ALT_NARRATION_PATTERNS = (
    # "Chose X over Y" / "Chose X over Y, Z"
    _re.compile(r"\bchose\s+`?([\w.\-]+)`?\s+over\s+([`\w.,\s\-]+?)(?:\s+because|\s*\.|$)", _re.IGNORECASE),
    # "Considered X but chose Y" / "Considered X, Z but chose Y"
    _re.compile(r"\bconsidered\s+([`\w.,\s\-]+?)\s+but\s+chose\s+`?([\w.\-]+)`?", _re.IGNORECASE),
    # "Picked X instead of Y"
    _re.compile(r"\bpicked\s+`?([\w.\-]+)`?\s+instead\s+of\s+([`\w.,\s\-]+?)(?:\s+because|\s*\.|$)", _re.IGNORECASE),
    # "Using X rather than Y"
    _re.compile(r"\busing\s+`?([\w.\-]+)`?\s+rather\s+than\s+([`\w.,\s\-]+?)(?:\s+because|\s*\.|$)", _re.IGNORECASE),
)


def _split_alt_list(raw: str) -> list[str]:
    """Split a "send_email, ask_clarification and foo" run into clean names."""
    if not raw:
        return []
    # Normalise " and " and " or " to commas, strip backticks/whitespace.
    norm = _re.sub(r"\s+(?:and|or)\s+", ",", raw, flags=_re.IGNORECASE)
    parts = [p.strip(" `.\t\n") for p in norm.split(",")]
    return [p for p in parts if p and _re.match(r"^[\w.\-]+$", p)]


def _tool_alts_from_logprobs(model_event: Mapping[str, Any], chosen: str) -> list[dict]:
    """Walk an LLM event's logprobs for tokens that look like alternative tool names.

    Strategy: the chosen tool name appears as one or more tokens in the
    model output. Find the first token whose text matches the start of
    ``chosen`` and read its ``top_logprobs`` — those are real alternative
    completions the sampler considered for the same decoding position.
    Filter to entries that look like identifiers (tool names) so we don't
    surface "_", " ", or unrelated wordpieces as "alternatives".
    """
    content = _find_logprobs_list(model_event)
    if not content or not chosen:
        return []
    chosen_lc = chosen.lower()
    for entry in content:
        if not isinstance(entry, Mapping):
            continue
        tok = entry.get("token")
        if not isinstance(tok, str):
            continue
        tok_clean = tok.strip().lower()
        if not tok_clean or not chosen_lc.startswith(tok_clean):
            continue
        alts_raw = entry.get("top_logprobs")
        if not isinstance(alts_raw, list):
            continue
        alts: list[dict] = []
        for alt in alts_raw:
            if not isinstance(alt, Mapping):
                continue
            at = alt.get("token")
            alp = alt.get("logprob")
            if not isinstance(at, str) or not isinstance(alp, (int, float)):
                continue
            at_clean = at.strip()
            # Skip whitespace/punctuation-only and the chosen token itself.
            if not at_clean or at_clean.lower() == tok_clean:
                continue
            # Only keep identifier-shaped tokens — real tool names look
            # like ``send_email`` / ``create.event`` / ``askUser``.
            if not _re.match(r"^[A-Za-z][\w.\-]*$", at_clean):
                continue
            alts.append({"name": at_clean, "score": round(_logprob_to_prob(alp), 4)})
        alts.sort(key=lambda r: r["score"], reverse=True)
        return alts[:_TOOL_TOP_K]
    return []


def _tool_alts_from_thinking(model_event: Mapping[str, Any], chosen: str) -> list[dict]:
    """Parse extended-thinking text blocks for a self-reported alternatives narration.

    Returns alternatives WITHOUT scores (the model just lists names; we
    don't fabricate numeric confidences). The frontend renders them as
    "Chose X over Y, Z (from extended-thinking)".
    """
    if not isinstance(model_event, Mapping) or not chosen:
        return []
    # Collect candidate text blobs the model wrote — extended-thinking
    # lives in various shapes depending on the adapter.
    blobs: list[str] = []
    for key in ("thinking", "reasoning", "extended_thinking", "thought"):
        v = model_event.get(key)
        if isinstance(v, str):
            blobs.append(v)
    data = model_event.get("data") if isinstance(model_event.get("data"), Mapping) else None
    if data:
        for key in ("thinking", "reasoning", "extended_thinking", "thought"):
            v = data.get(key)
            if isinstance(v, str):
                blobs.append(v)
        # Anthropic content[].type == "thinking" → text in content[].thinking
        msg = data.get("message") if isinstance(data.get("message"), Mapping) else None
        if msg and isinstance(msg.get("content"), list):
            for block in msg["content"]:
                if not isinstance(block, Mapping):
                    continue
                if block.get("type") in ("thinking", "reasoning"):
                    t = block.get("thinking") or block.get("text")
                    if isinstance(t, str):
                        blobs.append(t)
    if not blobs:
        return []
    chosen_lc = chosen.lower()
    text = "\n".join(blobs)
    for pat in _ALT_NARRATION_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        g1, g2 = m.group(1), m.group(2)
        # Two pattern shapes: (chosen, rejected_list) OR (rejected_list, chosen).
        # We disambiguate by checking which group equals the chosen tool.
        # Strip trailing punctuation (period, comma, backtick) before comparing.
        g1_clean = g1.strip("` .,\t\n").lower()
        g2_clean = g2.strip("` .,\t\n").lower()
        if g1_clean == chosen_lc:
            rejected = _split_alt_list(g2)
        elif g2_clean == chosen_lc:
            rejected = _split_alt_list(g1)
        else:
            # Narration doesn't match the actual chosen tool — could be
            # the model talking about a different decision. Skip rather
            # than show misleading data.
            continue
        # Drop the chosen name if it appears in the rejected list and
        # cap at _TOOL_TOP_K so the panel stays scannable.
        rejected = [n for n in rejected if n.lower() != chosen_lc][:_TOOL_TOP_K]
        if rejected:
            return [{"name": n, "score": None} for n in rejected]
    return []


def _is_tool_call_event(ev: Mapping[str, Any]) -> Optional[str]:
    """Return the chosen tool name if ``ev`` is a tool-call event, else ``None``."""
    if not isinstance(ev, Mapping):
        return None
    # v3 normalised: event_type == "tool.call"
    et = ev.get("event_type") or ev.get("type") or ""
    if isinstance(et, str) and et.lower() == "tool.call":
        name = ev.get("tool_name") or ev.get("name")
        if isinstance(name, str) and name:
            return name
        data = ev.get("data") if isinstance(ev.get("data"), Mapping) else None
        if data:
            n = data.get("tool_name") or data.get("name")
            if isinstance(n, str) and n:
                return n
    # Dashboard-projected tool rows carry the tool name in ``detail`` or
    # ``tool_name``. The projector sets ``type`` to the tool category
    # (EXEC, READ, WRITE, …) so we look for an explicit tool_name field.
    tn = ev.get("tool_name")
    if isinstance(tn, str) and tn:
        return tn
    return None


def extract_tool_alternatives(events: list) -> list[dict]:
    """For every tool.call event, return its chosen tool + rejected alternatives.

    Returns a list of payload dicts, one per tool call seen::

        [
          {
            "event_index": 17,
            "chosen": "create_event",
            "chosen_score": 0.89,     # None when source == "thinking"
            "alternatives": [
              {"name": "send_email", "score": 0.05},
              {"name": "ask_clarification", "score": 0.06},
            ],
            "source": "logprobs" | "thinking",
          },
          ...
        ]

    When neither source has real data the row's ``alternatives`` list is
    empty — callers MUST treat that as "not available" and never invent
    options (memory: PR-prompt critical note on user trust).

    ``events`` is expected ordered oldest-first or newest-first; we walk
    backwards from each tool call by up to ``_TOOL_LOOKBACK`` indices in
    both directions to find the producing LLM event.
    """
    if not events or not isinstance(events, list):
        return []
    try:
        from clawmetry.risk import is_llm_event
    except Exception:
        return []
    out: list[dict] = []
    for idx, ev in enumerate(events):
        chosen = _is_tool_call_event(ev)
        if not chosen:
            continue
        # Find the nearest LLM-call event in either direction (Brain
        # streams oldest-first; cache pushes can be newest-first).
        model_ev = None
        for offset in range(1, _TOOL_LOOKBACK + 1):
            for cand_idx in (idx - offset, idx + offset):
                if 0 <= cand_idx < len(events):
                    cand = events[cand_idx]
                    if isinstance(cand, Mapping) and is_llm_event(cand):
                        model_ev = cand
                        break
            if model_ev is not None:
                break
        if model_ev is None:
            out.append({
                "event_index": idx,
                "chosen": chosen,
                "chosen_score": None,
                "alternatives": [],
                "source": "none",
            })
            continue
        alts = _tool_alts_from_logprobs(model_ev, chosen)
        source = "logprobs" if alts else "none"
        chosen_score: Optional[float] = None
        if alts:
            # Locate the chosen token's own probability for display.
            content = _find_logprobs_list(model_ev) or []
            chosen_lc = chosen.lower()
            for entry in content:
                if not isinstance(entry, Mapping):
                    continue
                tok = entry.get("token")
                if isinstance(tok, str) and chosen_lc.startswith(tok.strip().lower()):
                    lp = entry.get("logprob")
                    if isinstance(lp, (int, float)):
                        chosen_score = round(_logprob_to_prob(lp), 4)
                    break
        if not alts:
            alts = _tool_alts_from_thinking(model_ev, chosen)
            if alts:
                source = "thinking"
        out.append({
            "event_index": idx,
            "chosen": chosen,
            "chosen_score": chosen_score,
            "alternatives": alts,
            "source": source,
        })
    return out


def annotate_tool_alternatives(events) -> None:
    """Stamp ``ev["tool_alternatives"]`` on every tool.call event in place.

    Companion to ``annotate_events`` for #1616. Silent per-event fallback
    so a single bad row never poisons the Brain feed.
    """
    if not events or not isinstance(events, list):
        return
    try:
        payloads = extract_tool_alternatives(events)
    except Exception:
        return
    for entry in payloads:
        try:
            i = entry.get("event_index")
            if not isinstance(i, int) or i < 0 or i >= len(events):
                continue
            target = events[i]
            if isinstance(target, dict):
                target["tool_alternatives"] = {
                    "chosen": entry["chosen"],
                    "chosen_score": entry.get("chosen_score"),
                    "alternatives": entry.get("alternatives", []),
                    "source": entry.get("source", "none"),
                }
        except Exception:
            pass
