"""Context-window sizing across every runtime ClawMetry ingests.

Why this file exists
--------------------
"How full is the context?" is only meaningful against a denominator. Get the
denominator wrong and every downstream number is wrong in a way that *looks*
right: a 300K-token Codex turn rendered against Anthropic's 200K window reads
"150% — blown", when GPT-5 actually has 400K and the turn is at 75%. The
reverse is just as bad — a genuinely blown 130K DeepSeek turn reads "65%,
fine" against the same 200K default.

Until this module, ``context_window_for_model`` knew exactly two numbers,
both Anthropic's: 200K, and 1M for the ``[1m]`` variants. Every one of the
other runtimes was measured with Anthropic's ruler.

The contract
------------
Sizing is **resolved, not hard-coded**, and every answer carries where it
came from — the same convention Guard thresholds follow (``threshold_source``
in ``detectors.py``). A reader must always be able to tell a looked-up window
from a fallback, because a utilisation gauge built on a guess is worse than
no gauge at all.

Four signals, each overriding the last:

1. ``default``          — the documented fallback. Nothing matched.
2. ``model_table``      — an entry in ``MODEL_CONTEXT_WINDOWS`` below matched
                          the model string. This is the good case.
3. ``explicit_marker``  — the model string carries an explicit window marker
                          (``[1m]``, ``-1m``). The operator told us directly,
                          so it beats the table.
4. ``observed_floor``   — we measured a prompt LARGER than the resolved
                          window. A prompt can never exceed the window it was
                          accepted into, so the measurement is ground truth
                          and the table is wrong (or the model is a variant we
                          do not recognise). Round up to the next standard
                          tier so the gauge never reads >100%.

``confidence`` collapses that to three values for the UI: ``exact`` (the
operator or a measurement told us), ``inferred`` (table hit), ``fallback``
(we are guessing, say so).

Editing the table
-----------------
Entries are ``(pattern, tokens, label)``, matched as a substring against the
lower-cased, separator-normalised model string, **most specific first**. The
first match wins, so ``gpt-5`` must be listed before any broader ``gpt``
entry. Numbers are the vendor's published context window; when a vendor
ships several tiers under one family name we take the tier the agent
runtimes actually default to, and let ``observed_floor`` correct upward for
the larger variants rather than over-claiming here.

A model we have never seen falls back to ``DEFAULT_CONTEXT_WINDOW`` and is
reported as such. That is deliberate: an honest "we don't know this model"
is a bug report someone can fix with a one-line PR, whereas a confident
wrong number is a silent lie in a dashboard.
"""

from __future__ import annotations

import math
import os
from typing import NamedTuple

# The fallback when nothing matches. 200K is the modal agent context window
# in 2026 and is what the pre-table code assumed for everything; keeping it
# means an unknown model is no worse off than before, and now says so.
DEFAULT_CONTEXT_WINDOW = 200_000

# Tiers used when a measurement proves the resolved window too small. We snap
# up to a standard size rather than to the raw observation, so the gauge does
# not creep upward turn by turn.
#
# The ladder is per-vendor, because vendors do not ship the same rungs: a
# Claude prompt measured at 323K is on the 1M variant, NOT on some 400K tier
# Anthropic has never sold. Snapping it to a rung the vendor does not offer
# would be a fabricated denominator — the exact failure this module exists to
# stop. Families without a published ladder fall back to ``_TIERS_GENERIC``.
_TIERS_GENERIC = (128_000, 200_000, 256_000, 400_000, 1_000_000, 2_000_000)
_FAMILY_TIERS: dict[str, tuple[int, ...]] = {
    "anthropic": (200_000, 1_000_000),
    "openai":    (16_385, 128_000, 200_000, 400_000, 1_000_000),
    "google":    (1_000_000, 2_000_000),
}

MAX_CONTEXT_WINDOW = _TIERS_GENERIC[-1]


class ContextWindow(NamedTuple):
    """A resolved context window plus its provenance.

    ``tokens``     the denominator to use.
    ``source``     one of ``default`` / ``model_table`` / ``explicit_marker``
                   / ``observed_floor`` — see the module docstring.
    ``confidence`` ``exact`` | ``inferred`` | ``fallback``.
    ``matched``    the table pattern (or marker) that produced the answer;
                   empty when nothing matched. Lets a reader audit the hit.
    ``family``     the vendor family, which selects the observed-floor
                   ladder. Empty when unmatched.
    """

    tokens: int
    source: str
    confidence: str
    matched: str = ""
    family: str = ""

    @property
    def is_known(self) -> bool:
        """False when we are guessing. The UI should badge these."""
        return self.source != "default"


# ── the table ────────────────────────────────────────────────────────────
# (pattern, tokens, label). Most specific first — first substring match wins.
MODEL_CONTEXT_WINDOWS: tuple[tuple[str, int, str, str], ...] = (
    # ── Anthropic ────────────────────────────────────────────────────────
    # Opus 4.8 ships a 1M window by default, so a plain model string with no
    # [1m] marker must NOT be downgraded to 200K.
    ("claude-opus-4-8", 1_000_000, "Claude Opus 4.8", "anthropic"),
    ("claude-opus4-8", 1_000_000, "Claude Opus 4.8", "anthropic"),
    ("claude-instant", 100_000, "Claude Instant", "anthropic"),
    ("claude-2", 100_000, "Claude 2", "anthropic"),
    ("claude", 200_000, "Claude (default)", "anthropic"),

    # ── OpenAI ───────────────────────────────────────────────────────────
    # GPT-5 family is 400K — the single most consequential entry here, since
    # Codex defaults to it and was being measured with Anthropic's 200K ruler.
    ("gpt-5", 400_000, "GPT-5", "openai"),
    ("gpt-4-1", 1_000_000, "GPT-4.1", "openai"),
    ("gpt-4o", 128_000, "GPT-4o", "openai"),
    ("gpt-4-turbo", 128_000, "GPT-4 Turbo", "openai"),
    ("gpt-3-5", 16_385, "GPT-3.5 Turbo", "openai"),
    ("codex-mini", 200_000, "codex-mini", "openai"),
    ("o4-mini", 200_000, "o4-mini", "openai"),
    ("o3-mini", 200_000, "o3-mini", "openai"),
    ("o3", 200_000, "o3", "openai"),
    ("o1-mini", 128_000, "o1-mini", "openai"),
    ("o1", 200_000, "o1", "openai"),

    # ── Google ───────────────────────────────────────────────────────────
    ("gemini-1-5-pro", 2_000_000, "Gemini 1.5 Pro", "google"),
    ("gemini", 1_000_000, "Gemini (default)", "google"),

    # ── xAI ──────────────────────────────────────────────────────────────
    ("grok-4", 256_000, "Grok 4", "xai"),
    ("grok", 131_072, "Grok (default)", "xai"),

    # ── DeepSeek ─────────────────────────────────────────────────────────
    ("deepseek", 128_000, "DeepSeek", "deepseek"),

    # ── Moonshot / Kimi ──────────────────────────────────────────────────
    ("kimi-k2", 256_000, "Kimi K2", "moonshot"),
    ("kimi", 131_072, "Kimi (default)", "moonshot"),
    ("moonshot", 131_072, "Moonshot", "moonshot"),

    # ── Alibaba Qwen ─────────────────────────────────────────────────────
    ("qwen3-coder", 256_000, "Qwen3 Coder", "qwen"),
    ("qwen", 131_072, "Qwen (default)", "qwen"),

    # ── Mistral ──────────────────────────────────────────────────────────
    ("codestral", 256_000, "Codestral", "mistral"),
    ("devstral", 131_072, "Devstral", "mistral"),
    ("mistral", 131_072, "Mistral (default)", "mistral"),

    # ── Meta Llama ───────────────────────────────────────────────────────
    ("llama-3", 128_000, "Llama 3.x", "meta"),
    ("llama3", 128_000, "Llama 3.x", "meta"),

    # ── Z.ai GLM ─────────────────────────────────────────────────────────
    ("glm-4-6", 200_000, "GLM-4.6", "zai"),
    ("glm", 131_072, "GLM (default)", "zai"),
)


def _normalise(model: str) -> str:
    """Lower-case and unify separators so ``claude-opus-4.8``,
    ``claude_opus_4_8`` and ``claude-opus-4-8`` all match one pattern.

    Coerces non-strings rather than raising: this sits on a read path fed by
    whatever a runtime happened to put in its ``model`` field, and a
    dashboard query must never die because one adapter wrote an int there.
    """
    if not isinstance(model, str):
        model = "" if model is None else str(model)
    return model.lower().replace(".", "-").replace("_", "-")


def _has_1m_marker(m: str) -> bool:
    """True when the model string carries an explicit 1M-window marker.

    Matches ``[1m]``, ``-1m``, ``_1m`` and a bare ``1m`` token. Guarded
    against false hits inside longer words (a hypothetical ``...21m...``)
    by requiring a separator or string edge on the left.
    """
    if not m:
        return False
    for i in range(len(m) - 1):
        if m[i] == "1" and m[i + 1] == "m":
            left_ok = i == 0 or not m[i - 1].isalnum()
            right = m[i + 2] if i + 2 < len(m) else ""
            right_ok = not right.isalnum()
            if left_ok and right_ok:
                return True
    return False


def _env_override(model: str) -> int:
    """Operator escape hatch: ``CLAWMETRY_CONTEXT_WINDOW`` pins the window for
    every model, for the air-gapped / bespoke-model case where our table can
    never be right. Returns 0 when unset or unparseable — never raises."""
    raw = os.environ.get("CLAWMETRY_CONTEXT_WINDOW", "")
    if not raw:
        return 0
    try:
        val = int(str(raw).strip())
    except (TypeError, ValueError):
        return 0
    return val if 0 < val <= MAX_CONTEXT_WINDOW else 0


def _snap_to_tier(observed: int, family: str = "") -> int:
    """Smallest rung the vendor actually ships that still fits ``observed``.

    Falls back to the generic ladder for families we have no published rung
    list for, and to whole millions above the largest known rung.
    """
    ladder = _FAMILY_TIERS.get(family) or _TIERS_GENERIC
    for tier in ladder:
        if observed <= tier:
            return tier
    top = max(ladder[-1], _TIERS_GENERIC[-1])
    return int(math.ceil(observed / top) * top)


def resolve_context_window(
    model: str,
    observed_tokens: int = 0,
) -> ContextWindow:
    """Resolve the context window for ``model``, with provenance.

    ``observed_tokens`` is the live prompt size measured for the turn, when
    known. It acts as a hard floor: a prompt the provider accepted cannot
    exceed that provider's window, so a measurement above the resolved
    window proves the resolution wrong and wins.

    Never raises. An unknown model yields ``DEFAULT_CONTEXT_WINDOW`` with
    ``source='default'`` so callers can badge it as an estimate.
    """
    m = _normalise(model)
    obs = 0
    try:
        obs = max(0, int(observed_tokens or 0))
    except (TypeError, ValueError):
        obs = 0

    # Family is resolved independently of the window, so an explicit marker
    # or an env pin still snaps on the right vendor ladder.
    family = ""
    for pattern, _tokens, _label, fam in MODEL_CONTEXT_WINDOWS:
        if pattern in m:
            family = fam
            break

    pinned = _env_override(model)
    if pinned:
        base, source, confidence, matched = (
            pinned, "explicit_marker", "exact", "CLAWMETRY_CONTEXT_WINDOW",
        )
    elif _has_1m_marker(m):
        # The operator spelled the window out in the model string. Trust it
        # over the table — this is how the 1M betas are surfaced before the
        # model id itself changes.
        base, source, confidence, matched = (
            1_000_000, "explicit_marker", "exact", "1m",
        )
    else:
        base, source, confidence, matched = (
            DEFAULT_CONTEXT_WINDOW, "default", "fallback", "",
        )
        for pattern, tokens, label, _fam in MODEL_CONTEXT_WINDOWS:
            if pattern in m:
                base, source, confidence, matched = (
                    tokens, "model_table", "inferred", label,
                )
                break

    if obs > base:
        # Ground truth beats the table. Snap up to a rung the vendor ships,
        # rather than to the raw observation, so the denominator is stable
        # across turns instead of creeping upward with each measurement.
        return ContextWindow(
            _snap_to_tier(obs, family), "observed_floor", "exact", matched, family,
        )
    return ContextWindow(base, source, confidence, matched, family)


def context_window_for_model(model: str, observed_tokens: int = 0) -> int:
    """Back-compatible int accessor — the window only, no provenance.

    Prefer :func:`resolve_context_window` in new code so the caller can tell
    a looked-up window from a fallback.
    """
    return resolve_context_window(model, observed_tokens).tokens
