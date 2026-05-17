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
