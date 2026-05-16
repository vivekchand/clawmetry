"""
clawmetry/risk.py — Hallucination Risk Indicator (issue #567).

Per-call risk score for LLM completions, surfaced as Low / Medium / High in
the Brain tab and as a session-level warning badge when any call in a
session scores High.

Why this exists
---------------
Chapter 6 of the agent observability plan: creativity and hallucination are
the same mechanism. Higher sampling temperature, low-confidence token
selection, and unusually long outputs all correlate with the model
extrapolating beyond its training distribution. ClawMetry already captures
the per-call sampling config (temperature, max_tokens) and per-call output
token counts, so we can compose a cheap, additive risk score with ZERO new
data collection and ZERO new dependencies.

Design notes
------------
* **Pure function.** ``compute_hallucination_risk`` takes a single event
  dict (the same shape ``routes/brain.py`` passes around) and returns a
  ``{"risk_level": ..., "risk_explanation": ...}`` dict. No I/O, no global
  state, fully unit-testable in isolation.

* **Three additive signals**, weighted equally and summed:

    1. *Temperature* (always available when the adapter recorded it):
         T < 0.3   → +0  (deterministic, low risk)
         T < 0.7   → +1  (balanced, medium contribution)
         T >= 0.7  → +2  (creative, high contribution)

    2. *Token entropy / logprobs* (when present): the mean negative
       logprob across sampled tokens — proxy for the model's confidence
       in its own output. Anthropic does NOT expose logprobs today, so we
       degrade GRACEFULLY when the field is absent: the signal simply
       contributes 0 and the explanation says so.

    3. *Response length* (always available):
         <  500 tokens   → +0
         500-2000        → +1
         > 2000          → +2

* **Score → label.** total in [0..6]. Threshold band:
         0-1 → low      (T<0.3 short responses or no signals)
         2-3 → medium   (one strong signal, e.g. T=0.7 + short response)
         >=4 → high     (compound risk — high T + long response, etc.)

* **Graceful degradation.** When no signals are available (e.g. a tool
  call event with no temperature and no token counts), we return
  ``risk_level="low"`` with an explanation that says "insufficient signal".
  Never crash on bad input — the dashboard renders thousands of these
  per page-load.

The plan calls this Phase 1 of the Hallucination Risk Indicator. A future
phase will add a fourth signal (model self-reported confidence via
constrained decoding) once OpenClaw exposes it.

Memory respects
---------------
* ``feedback_no_em_dashes_in_user_facing_copy.md`` — explanations are
  plain copy, no em-dashes / "X, Y, and Z — coda" patterns.
* ``feedback_simple_ui_for_nontechnical.md`` — Low / Medium / High labels
  are readable without ML training.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional


# ── Tunable thresholds ──────────────────────────────────────────────────
# Kept as module-level constants so tests can monkey-patch them when the
# Anthropic API surface eventually exposes logprobs and we want to add a
# fourth band without churning every assertion.
_TEMP_LOW_MAX = 0.3        # T < this → +0 (deterministic)
_TEMP_MED_MAX = 0.7        # T < this → +1 (balanced)
                           # T >= 0.7 → +2 (creative / high)

_TOKENS_SHORT_MAX = 500    # output < this → +0
_TOKENS_MED_MAX = 2000     # output < this → +1
                           # output >= 2000 → +2

# Score → label thresholds. Inclusive lower bound. Tuned so that a single
# moderate signal alone never trips "high" — that requires at least one
# strong signal + one moderate signal.
_LABEL_BANDS = [
    (0, "low"),
    (2, "medium"),
    (4, "high"),
]

# Event types that DO represent an LLM call. ``routes/brain.py`` projects
# many event flavours (USER, RESULT, EXEC, READ, …) into the same stream
# and the risk score only makes sense on the assistant-output events.
_LLM_EVENT_TYPES = frozenset({
    "AGENT",          # legacy JSONL assistant text turn
    "THINK",          # legacy JSONL extended-thinking block
    "MODEL.COMPLETED",  # v3 underscore mapper LLM completion event
})


def _band_label(score: int) -> str:
    """Map an integer score → ``low | medium | high`` using ``_LABEL_BANDS``."""
    label = "low"
    for thresh, name in _LABEL_BANDS:
        if score >= thresh:
            label = name
    return label


def is_llm_event(event_data: Mapping[str, Any]) -> bool:
    """Return ``True`` when ``event_data`` represents an assistant LLM call.

    Tolerant of three shapes the Brain pipeline emits:

    * Dashboard-projected events: ``ev["type"]`` is one of ``AGENT/THINK``.
    * Local-store rows: ``ev["event_type"]`` is ``model.completed`` (lower
      or upper case).
    * Raw JSONL turn objects: ``ev["role"] == "assistant"``.
    """
    if not isinstance(event_data, Mapping):
        return False
    t = (event_data.get("type") or event_data.get("event_type") or "")
    if isinstance(t, str) and t.upper() in _LLM_EVENT_TYPES:
        return True
    return event_data.get("role") == "assistant"


def _extract_temperature(event_data: Mapping[str, Any]) -> Optional[float]:
    """Pull temperature out of the event, no matter which adapter wrote it.

    Mirrors ``routes/sessions._extract_decoding_params`` but inlined here
    to avoid pulling a heavy import chain (sessions.py imports dashboard
    helpers) into the risk module. We only care about temperature, so the
    full alias table isn't needed.
    """
    if not isinstance(event_data, Mapping):
        return None
    # Flat: explicit projection (some tests pass it pre-extracted).
    for key in ("temperature",):
        v = event_data.get(key)
        if isinstance(v, (int, float)):
            return float(v)

    data = event_data.get("data") if isinstance(event_data.get("data"), Mapping) else None
    candidates = []
    if data is not None:
        for k in ("params", "config"):
            sub = data.get(k)
            if isinstance(sub, Mapping):
                candidates.append(sub)
        msg = data.get("message") if isinstance(data.get("message"), Mapping) else None
        if msg is not None:
            for k in ("params", "config"):
                sub = msg.get(k)
                if isinstance(sub, Mapping):
                    candidates.append(sub)
            md = msg.get("metadata") if isinstance(msg.get("metadata"), Mapping) else None
            if md is not None and isinstance(md.get("params"), Mapping):
                candidates.append(md["params"])
        # Some adapters inline the params on `data` itself.
        candidates.append(data)
    for k in ("params", "config"):
        sub = event_data.get(k)
        if isinstance(sub, Mapping):
            candidates.append(sub)

    for bucket in candidates:
        v = bucket.get("temperature")
        if isinstance(v, (int, float)):
            return float(v)
    return None


def _extract_output_tokens(event_data: Mapping[str, Any]) -> Optional[int]:
    """Pull output token count from the event. Returns ``None`` when absent."""
    if not isinstance(event_data, Mapping):
        return None
    # Flat projections used by the Brain stream renderer + local_store row.
    for key in ("output_tokens", "outputTokens"):
        v = event_data.get(key)
        if isinstance(v, (int, float)):
            return int(v)

    data = event_data.get("data") if isinstance(event_data.get("data"), Mapping) else None
    buckets: list[Mapping[str, Any]] = []
    if data is not None:
        for k in ("usage",):
            sub = data.get(k)
            if isinstance(sub, Mapping):
                buckets.append(sub)
        msg = data.get("message") if isinstance(data.get("message"), Mapping) else None
        if msg is not None and isinstance(msg.get("usage"), Mapping):
            buckets.append(msg["usage"])
        buckets.append(data)
    if isinstance(event_data.get("usage"), Mapping):
        buckets.append(event_data["usage"])

    for bucket in buckets:
        for k in ("output_tokens", "outputTokens", "completion_tokens"):
            v = bucket.get(k)
            if isinstance(v, (int, float)):
                return int(v)

    # token_count on the local_store row is total, but it's still a useful
    # length proxy for the response-length signal when nothing finer is
    # available. Only consult it as a last resort.
    v = event_data.get("token_count")
    if isinstance(v, (int, float)) and v > 0:
        return int(v)
    return None


def _extract_logprob_summary(event_data: Mapping[str, Any]) -> Optional[float]:
    """Return the MEAN negative logprob across sampled tokens, or ``None``.

    Anthropic does not expose logprobs today (2026-05-16); the field shows
    up only when the user has wired in an OpenAI-style adapter that
    captured ``logprobs.content[*].logprob``. We accept either:

    * a pre-computed ``mean_neg_logprob`` scalar (the cheap, common case
      once a future PR adds aggregation upstream), or
    * a list of token-level logprob entries (``logprobs.content`` shape).

    Returns ``None`` when neither is present so the temperature + length
    signals can still produce a useful score (graceful degradation).
    """
    if not isinstance(event_data, Mapping):
        return None
    # Pre-computed scalar — preferred.
    v = event_data.get("mean_neg_logprob")
    if isinstance(v, (int, float)):
        return float(v)
    data = event_data.get("data") if isinstance(event_data.get("data"), Mapping) else None
    if data is not None and isinstance(data.get("mean_neg_logprob"), (int, float)):
        return float(data["mean_neg_logprob"])

    # Token-level list — compute the mean here. Capped at 256 entries so a
    # multi-thousand-token completion doesn't dominate Brain rendering.
    def _from_list(arr):
        if not isinstance(arr, list) or not arr:
            return None
        vals = []
        for entry in arr[:256]:
            if isinstance(entry, Mapping):
                lp = entry.get("logprob")
                if isinstance(lp, (int, float)):
                    vals.append(-float(lp))
        if not vals:
            return None
        return sum(vals) / len(vals)

    for bucket in (event_data, data or {}):
        lp = bucket.get("logprobs")
        if isinstance(lp, Mapping):
            mean = _from_list(lp.get("content"))
            if mean is not None:
                return mean
        if isinstance(bucket.get("logprob_content"), list):
            mean = _from_list(bucket["logprob_content"])
            if mean is not None:
                return mean
    return None


def compute_hallucination_risk(event_data: Mapping[str, Any]) -> dict:
    """Score a single LLM-call event for hallucination risk.

    Returns a dict with two keys:

    * ``risk_level``      — one of ``"low" | "medium" | "high"``.
    * ``risk_explanation`` — short human-readable string for the tooltip.

    The function is total. Pass it anything and it returns a sensible
    default rather than raising. Non-LLM events are scored ``low`` with
    an explanation that says we have no signal to act on.
    """
    if not isinstance(event_data, Mapping):
        return {
            "risk_level":       "low",
            "risk_explanation": "No signal available for this event.",
        }
    # Non-LLM events (USER, EXEC, READ, …) get a stable low + explanation.
    # The Brain renderer filters on this and only shows the badge when the
    # event is an LLM call, but returning a value for everything keeps the
    # API contract simple.
    if not is_llm_event(event_data):
        return {
            "risk_level":       "low",
            "risk_explanation": "Not an LLM call; no risk score applied.",
        }

    score = 0
    reasons: list[str] = []

    # ── Signal 1: temperature ──────────────────────────────────────────
    temp = _extract_temperature(event_data)
    if temp is None:
        reasons.append("temperature unknown")
    elif temp < _TEMP_LOW_MAX:
        # +0; explicit reason still helps the tooltip
        reasons.append(f"temperature {temp:g} is low")
    elif temp < _TEMP_MED_MAX:
        score += 1
        reasons.append(f"temperature {temp:g} is moderate")
    else:
        score += 2
        reasons.append(f"temperature {temp:g} is high")

    # ── Signal 2: logprobs / entropy ───────────────────────────────────
    # Mean negative logprob: higher = less confident. Anthropic does not
    # expose logprobs today, so the typical install will hit the "not
    # available" branch.
    mean_neg_lp = _extract_logprob_summary(event_data)
    if mean_neg_lp is None:
        reasons.append("token confidence data not available")
    elif mean_neg_lp < 0.3:
        reasons.append("token confidence is high")
    elif mean_neg_lp < 1.0:
        score += 1
        reasons.append("token confidence is moderate")
    else:
        score += 2
        reasons.append("token confidence is low")

    # ── Signal 3: response length ──────────────────────────────────────
    out_tok = _extract_output_tokens(event_data)
    if out_tok is None:
        reasons.append("output length unknown")
    elif out_tok < _TOKENS_SHORT_MAX:
        reasons.append(f"output is short ({out_tok} tokens)")
    elif out_tok < _TOKENS_MED_MAX:
        score += 1
        reasons.append(f"output is medium length ({out_tok} tokens)")
    else:
        score += 2
        reasons.append(f"output is very long ({out_tok} tokens)")

    # If we got zero signals, downgrade to a stable low + clear message.
    if temp is None and mean_neg_lp is None and out_tok is None:
        return {
            "risk_level":       "low",
            "risk_explanation": "No risk signals available for this call.",
        }

    label = _band_label(score)
    return {
        "risk_level":       label,
        "risk_explanation": "; ".join(reasons),
    }


def session_has_high_risk(events: list) -> bool:
    """Return True if any LLM-call event in ``events`` scored ``high``.

    Convenience helper for the sessions-list renderer: it iterates the
    Brain history once per page-load and stamps a warning icon on any
    session whose call mix tripped the high-risk band.
    """
    if not events:
        return False
    for ev in events:
        if not isinstance(ev, Mapping):
            continue
        risk = ev.get("risk") if isinstance(ev.get("risk"), Mapping) else None
        if risk and risk.get("risk_level") == "high":
            return True
    return False
