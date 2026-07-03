"""
ClawMetry provider detection and pricing table.

Prices are per 1M tokens (USD), sourced from provider pricing pages.
Updated: 2026-03-28. These are approximate — actual costs from API responses
take precedence when available.
"""
from __future__ import annotations

import re

# hostname fragment -> {name, input_price_per_1m, output_price_per_1m}
PROVIDER_MAP: dict[str, dict] = {
    "api.anthropic.com": {
        "name": "anthropic",
        # claude-sonnet-4 as baseline; real cost read from response
        "input_per_1m": 3.00,
        "output_per_1m": 15.00,
    },
    "api.openai.com": {
        "name": "openai",
        # gpt-4o as baseline
        "input_per_1m": 2.50,
        "output_per_1m": 10.00,
    },
    "generativelanguage.googleapis.com": {
        "name": "gemini",
        # gemini-2.0-flash as baseline
        "input_per_1m": 0.10,
        "output_per_1m": 0.40,
    },
    "aiplatform.googleapis.com": {
        "name": "gemini-vertex",
        "input_per_1m": 0.10,
        "output_per_1m": 0.40,
    },
    "api.mistral.ai": {
        "name": "mistral",
        # mistral-large as baseline
        "input_per_1m": 2.00,
        "output_per_1m": 6.00,
    },
    "api.groq.com": {
        "name": "groq",
        # llama-3.3-70b as baseline
        "input_per_1m": 0.59,
        "output_per_1m": 0.79,
    },
    "api.together.xyz": {
        "name": "together",
        # llama-3.3-70b as baseline
        "input_per_1m": 0.90,
        "output_per_1m": 0.90,
    },
    "openrouter.ai": {
        "name": "openrouter",
        # varies widely; use a median
        "input_per_1m": 1.00,
        "output_per_1m": 3.00,
    },
    "api.cohere.com": {
        "name": "cohere",
        "input_per_1m": 0.50,
        "output_per_1m": 1.50,
    },
    "bedrock-runtime": {
        "name": "aws-bedrock",
        "input_per_1m": 3.00,
        "output_per_1m": 15.00,
    },
    "inference.ai.azure.com": {
        "name": "azure-ai",
        "input_per_1m": 2.50,
        "output_per_1m": 10.00,
    },
}

# Model-specific overrides (provider, model_prefix) -> (input_per_1m, output_per_1m)
MODEL_OVERRIDES: dict[tuple[str, str], tuple[float, float]] = {
    ("anthropic", "claude-3-5-haiku"): (0.80, 4.00),
    ("anthropic", "claude-3-haiku"): (0.25, 1.25),
    ("anthropic", "claude-3-5-sonnet"): (3.00, 15.00),
    ("anthropic", "claude-3-opus"): (15.00, 75.00),
    ("anthropic", "claude-sonnet-4"): (3.00, 15.00),
    ("anthropic", "claude-opus-4"): (15.00, 75.00),
    # Current-generation Anthropic models (verified against LiteLLM
    # model_prices_and_context_window.json, the source ccusage uses, 2026-06-08).
    # Opus 4.5+ DROPPED to 1/3 of Opus 4/4.1 ($5/$25 vs $15/$75); without these
    # entries opus-4-5/6/7/8 matched the bare ``claude-opus-4`` prefix and were
    # priced 3x too high (the founder's Claude Code showed $103k vs ccusage's
    # $16k). opus-4-1 stays old-priced — _get_rates picks the LONGEST matching
    # prefix so "claude-opus-4-8" wins "claude-opus-4-8" over "claude-opus-4".
    # Cache read/write fall out correctly from the 0.1x/1.25x multipliers
    # (opus new: read $0.50 = 0.1x$5, write $6.25 = 1.25x$5 — matches LiteLLM).
    ("anthropic", "claude-opus-4-1"): (15.00, 75.00),
    ("anthropic", "claude-opus-4-5"): (5.00, 25.00),
    ("anthropic", "claude-opus-4-6"): (5.00, 25.00),
    ("anthropic", "claude-opus-4-7"): (5.00, 25.00),
    ("anthropic", "claude-opus-4-8"): (5.00, 25.00),
    ("anthropic", "claude-haiku-4"): (1.00, 5.00),
    # sonnet-4 / 4-5 / 4-6 are all $3/$15 — the bare claude-sonnet-4 prefix
    # already covers them; listed for clarity/future-proofing.
    ("anthropic", "claude-sonnet-4-5"): (3.00, 15.00),
    ("anthropic", "claude-sonnet-4-6"): (3.00, 15.00),
    ("openai", "gpt-4o-mini"): (0.15, 0.60),
    ("openai", "gpt-4o"): (2.50, 10.00),
    ("openai", "gpt-4-turbo"): (10.00, 30.00),
    ("openai", "gpt-3.5"): (0.50, 1.50),
    ("openai", "o1-mini"): (3.00, 12.00),
    ("openai", "o1"): (15.00, 60.00),
    ("openai", "o3-mini"): (1.10, 4.40),
    # GPT-5 family (gpt-5.4, gpt-5.6, …). Official prices not yet published —
    # $10/$40 per 1M is a best-effort estimate; update once OpenAI confirms.
    # gpt-5.6 entry beats the broad prefix via longest-prefix matching in _get_rates.
    ("openai", "gpt-5"): (10.00, 40.00),
    ("openai", "gpt-5.6"): (10.00, 40.00),
    ("gemini", "gemini-2.0-flash"): (0.10, 0.40),
    ("gemini", "gemini-1.5-pro"): (1.25, 5.00),
    ("gemini", "gemini-1.5-flash"): (0.075, 0.30),
    ("mistral", "mistral-small"): (0.20, 0.60),
    ("mistral", "mistral-medium"): (0.70, 2.10),
    ("mistral", "mistral-large"): (2.00, 6.00),
    ("mistral", "codestral"): (0.20, 0.60),
}


def estimate_cost_usd(
    provider: str,
    tokens_in: int,
    tokens_out: int,
    model: str = "",
) -> float:
    """
    Return estimated cost in USD for a single LLM API call.

    If model is known, uses model-specific rates. Falls back to provider
    baseline rates. Never raises.
    """
    try:
        input_rate, output_rate = _get_rates(provider, model)
        cost = (tokens_in / 1_000_000) * input_rate + (tokens_out / 1_000_000) * output_rate
        return round(cost, 8)
    except Exception:
        return 0.0


# Local / self-hosted inference: the user pays for hardware + power, not
# per-token, so the per-token API cost is genuinely zero. Listed explicitly so
# that local-model traffic (e.g. PicoClaw on Ollama, "ollama/llama3.2:3b")
# resolves to 0.0 intentionally rather than falling through to the conservative
# unknown-provider default below, which would over-charge it. Matched against
# the provider name and any "<provider>/..." model prefix.
_LOCAL_PROVIDERS = frozenset({"ollama", "llamacpp", "llama.cpp", "lmstudio", "local", "vllm"})


def _get_rates(provider: str, model: str) -> tuple[float, float]:
    """Return (input_per_1m, output_per_1m) for a provider+model combo."""
    prov_lower = (provider or "").lower()
    model_lower = (model or "").lower()

    # Local / self-hosted models cost nothing per token.
    if prov_lower in _LOCAL_PROVIDERS or any(
        model_lower.startswith(p + "/") for p in _LOCAL_PROVIDERS
    ):
        return 0.0, 0.0

    # `provider_for_model` returns "google" for Gemini, but the pricing tables
    # key on "gemini" — without this alias every Gemini call fell through to the
    # conservative unknown default (a ~10x over-charge on flash). Normalise so
    # the lookup matches. Compare case-insensitively too (callers vary).
    if prov_lower == "google":
        prov_lower = "gemini"

    if model:
        # Strip a leading provider namespace so OpenRouter ids
        # ("anthropic/claude-opus-4-1") and Bedrock ids
        # ("us.anthropic.claude-opus-4-1") match the bare-name overrides instead
        # of falling to the provider baseline (a ~5x undercount on namespaced
        # Claude/GPT, the bulk of real spend).
        match_model = model_lower
        if "/" in match_model:
            match_model = match_model.split("/", 1)[1]
        for _vendor in ("anthropic.", "amazon.", "meta.", "mistral.", "cohere.", "google."):
            _idx = match_model.find(_vendor)
            if _idx != -1:
                match_model = match_model[_idx + len(_vendor):]
                break
        # Longest matching prefix wins, so a specific current-gen key
        # ("claude-opus-4-8") beats the shorter family key ("claude-opus-4")
        # regardless of dict order. Plain first-match silently mispriced every
        # model whose family prefix was inserted first (the opus 4.5+ 3x bug).
        best_rates = None
        best_len = -1
        for (prov, prefix), rates in MODEL_OVERRIDES.items():
            if prov == prov_lower and match_model.startswith(prefix.lower()):
                if len(prefix) > best_len:
                    best_len = len(prefix)
                    best_rates = rates
        if best_rates is not None:
            return best_rates

    # Fall back to provider baseline
    for info in PROVIDER_MAP.values():
        if info["name"] == prov_lower:
            return info["input_per_1m"], info["output_per_1m"]

    return 1.0, 3.0  # unknown provider — conservative default


# #2049: self-hosted / local model name hints. Routed to the "local" provider
# so _get_rates returns 0 (the user pays for hardware, not per token) instead
# of the conservative unknown-provider default.
# Self-hosted model name hints -> "local" provider (zero per-token cost). Only
# families that are overwhelmingly run locally (via ollama/lmstudio/etc.). NOT
# mistral/mixtral/qwen/deepseek: those have hosted paid APIs, so a bare name is
# routed to its provider (mistral) or the conservative non-zero default
# (qwen/deepseek) rather than silently priced at $0. A genuinely local instance
# should carry an explicit local prefix (e.g. "ollama/qwen2.5") to be free.
_LOCAL_MODEL_HINTS = (
    "llama", "phi", "gemma", "codellama",
)

# Anthropic prompt-cache multipliers, relative to the input rate:
# cache reads are ~0.1x input; 5-minute cache writes are ~1.25x input.
_CACHE_READ_MULT = 0.1
_CACHE_WRITE_MULT = 1.25


def provider_for_model(model: str) -> str:
    """Best-effort provider id for pricing from a model name (self-contained,
    daemon-safe — no dashboard import). Mirrors dashboard._provider_from_model
    and additionally routes self-hosted models to "local" (zero cost).

    Returns "" when nothing matches so callers can decide whether to fall back.
    """
    m = (model or "").lower()
    if not m:
        return ""
    for prov in ("openai", "anthropic", "google", "openrouter", "xai"):
        if m.startswith(prov + "/"):
            return prov
    if any(m.startswith(p + "/") for p in _LOCAL_PROVIDERS) or any(
        h in m for h in _LOCAL_MODEL_HINTS
    ):
        return "local"
    if "gpt" in m or "codex" in m or m.startswith(("o1", "o3", "o4")):
        return "openai"
    if "claude" in m:
        return "anthropic"
    if "gemini" in m:
        return "google"
    if "grok" in m:
        return "xai"
    # Mistral's hosted family (mistral-large/small/medium, mixtral, codestral)
    # has real per-token rates in the pricing table; route it instead of
    # treating it as free/local.
    if "mistral" in m or "mixtral" in m or "codestral" in m:
        return "mistral"
    return ""


# #2816 Auto smart routing: default SAME-PROVIDER cheap-task downgrade map.
# Keyed by a substring found in the source model name -> the cheaper family
# name to substitute in (kept as a family token so the auto-router can splice it
# into the original model string, preserving date suffixes where possible). Only
# downgrades WITHIN a provider (opus->haiku is anthropic-internal; gpt-4o->
# gpt-4o-mini is openai-internal). Used as the default for AutoRoutingConfig.
_AUTO_DOWNGRADE_MAP: dict[str, str] = {
    # Anthropic: heavy reasoning families -> haiku
    "opus": "haiku",
    "sonnet": "haiku",
    "claude-opus-4": "claude-3-5-haiku-latest",
    "claude-sonnet-4": "claude-3-5-haiku-latest",
    "claude-3-opus": "claude-3-5-haiku-latest",
    "claude-3-5-sonnet": "claude-3-5-haiku-latest",
    # OpenAI: gpt-4o -> gpt-4o-mini, o1 -> o1-mini
    "gpt-4o": "gpt-4o-mini",
    "gpt-4-turbo": "gpt-4o-mini",
    "gpt-4": "gpt-4o-mini",
    "o1": "o1-mini",
    # Gemini: pro -> flash
    "gemini-1.5-pro": "gemini-1.5-flash",
}


def default_auto_downgrade_map() -> dict[str, str]:
    """Return a copy of the default cheap-task downgrade map (#2816).

    Per-family same-provider substitution table derived from the pricing tables
    above (heavy families -> their cheap sibling). Callers may override per
    install via ``AutoRoutingConfig.downgrade_map``.
    """
    return dict(_AUTO_DOWNGRADE_MAP)


# Real, cheap model ids an auto-downgrade is allowed to resolve TO. A computed
# candidate (a full-id map target OR a family-spliced name) is only returned if
# it's in here. This is the safety backstop that prevents two hazards the review
# flagged: (a) a loose substring key (e.g. "o1") matching a different provider's
# model and substituting cross-provider; (b) a bare-family splice (the spec's own
# {"opus":"haiku"} example) synthesizing a NON-EXISTENT id like
# "claude-haiku-4-X" that the upstream would reject. A user map that targets a
# model not in this set simply no-ops (safe) rather than forwarding a bad id.
_KNOWN_DOWNGRADE_TARGETS: frozenset[str] = frozenset({
    # Anthropic
    "claude-3-5-haiku-latest", "claude-3-5-haiku-20241022", "claude-3-haiku-20240307",
    # OpenAI
    "gpt-4o-mini", "o1-mini", "o3-mini", "gpt-3.5-turbo",
    # Google
    "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-2.0-flash",
})


def downgrade_model_name(model: str, downgrade_map: dict[str, str] | None = None) -> str:
    """Return a cheaper SAME-PROVIDER model for ``model`` or '' if none applies.

    Picks the MOST SPECIFIC (longest) matching key in ``downgrade_map`` whose
    substring is present in the (lower-cased) model name, resolves a candidate
    (full-id target as-is, or a family token spliced into the source id), then
    only returns it if it is (1) the SAME provider as the source AND (2) a
    recognised real model id (``_KNOWN_DOWNGRADE_TARGETS``). Those two guards stop
    a loose substring key downgrading cross-provider, and a splice synthesizing a
    non-existent id. Never raises; '' when nothing safe matches.
    """
    try:
        if not model:
            return ""
        dmap = downgrade_map if downgrade_map is not None else _AUTO_DOWNGRADE_MAP
        m = model.lower()
        src_provider = provider_for_model(m)
        # Longest key first so "claude-3-5-sonnet" wins over bare "sonnet".
        for key in sorted(dmap.keys(), key=len, reverse=True):
            if key not in m:
                continue
            target = dmap[key]
            if not target or target.lower() in m:
                # Already the cheap target (or empty) — keep looking.
                continue
            # Resolve a candidate model id: a full-looking id is used directly;
            # a bare family token is spliced in place of the matched key.
            if "-" in target or target.lower().startswith(("gpt", "claude", "gemini", "o1-", "o3-")):
                candidate = target
            else:
                candidate = re.sub(re.escape(key), target, m)
            cand_l = candidate.lower()
            if cand_l == m:
                continue
            # SAFETY GUARDS: same provider + recognised real model id.
            if src_provider and provider_for_model(cand_l) != src_provider:
                continue
            if cand_l not in _KNOWN_DOWNGRADE_TARGETS:
                continue
            return candidate
        return ""
    except Exception:
        return ""


def estimate_event_cost_usd(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
    provider: str = "",
) -> float:
    """Cache-aware per-event cost in USD (#2049).

    Infers the provider from the model when not supplied — important because
    ``_get_rates`` needs the right provider (an empty provider falls through to
    the conservative unknown default and mis-prices). Prices prompt-cache read
    and write on top of input+output using Anthropic's documented multipliers
    (only applied for the anthropic provider, where the split is well-defined).
    Local / self-hosted models resolve to 0. Never raises.
    """
    try:
        prov = provider or provider_for_model(model)
        input_rate, output_rate = _get_rates(prov, model)
        if input_rate == 0 and output_rate == 0:
            return 0.0
        cost = (
            (max(0, int(input_tokens)) / 1_000_000) * input_rate
            + (max(0, int(output_tokens)) / 1_000_000) * output_rate
        )
        if prov == "anthropic":
            cost += (max(0, int(cache_read_tokens)) / 1_000_000) * input_rate * _CACHE_READ_MULT
            cost += (max(0, int(cache_write_tokens)) / 1_000_000) * input_rate * _CACHE_WRITE_MULT
        return round(cost, 8)
    except Exception:
        return 0.0
