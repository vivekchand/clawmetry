"""
ClawMetry provider detection and pricing table.

Prices are per 1M tokens (USD), sourced from provider pricing pages.
Updated: 2026-03-28. These are approximate — actual costs from API responses
take precedence when available.
"""
from __future__ import annotations

from typing import Optional

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
    ("openai", "gpt-4o-mini"): (0.15, 0.60),
    ("openai", "gpt-4o"): (2.50, 10.00),
    ("openai", "gpt-4-turbo"): (10.00, 30.00),
    ("openai", "gpt-4"): (30.00, 60.00),
    ("openai", "gpt-3.5"): (0.50, 1.50),
    ("openai", "o1-mini"): (3.00, 12.00),
    ("openai", "o1"): (15.00, 60.00),
    ("openai", "o3-mini"): (1.10, 4.40),
    ("gemini", "gemini-2.0-flash"): (0.10, 0.40),
    ("gemini", "gemini-1.5-pro"): (1.25, 5.00),
    ("gemini", "gemini-1.5-flash"): (0.075, 0.30),
    ("mistral", "mistral-small"): (0.20, 0.60),
    ("mistral", "mistral-medium"): (0.70, 2.10),
    ("mistral", "mistral-large"): (2.00, 6.00),
    ("mistral", "codestral"): (0.20, 0.60),
}

# Default same-provider downgrades used by the enforcement proxy's opt-in
# auto-router. Keys are model prefixes; values are cheaper models from the
# same provider. The resolver below still verifies provider parity and pricing
# before returning a target, so custom config cannot accidentally jump providers.
DEFAULT_MODEL_DOWNGRADE_MAP: dict[str, str] = {
    "claude-opus-4": "claude-3-5-haiku",
    "claude-3-opus": "claude-3-haiku",
    "claude-sonnet-4": "claude-3-5-haiku",
    "claude-3-5-sonnet": "claude-3-5-haiku",
    "gpt-4o": "gpt-4o-mini",
    "gpt-4-turbo": "gpt-4o-mini",
    "gpt-4": "gpt-4o-mini",
    "o1": "o1-mini",
}


def _strip_provider_prefix(model: str) -> str:
    """Return the model id without a leading provider prefix."""
    model_lower = (model or "").lower()
    if "/" not in model_lower:
        return model_lower
    return model_lower.split("/", 1)[1]


def resolve_same_provider_downgrade(
    model: str,
    downgrade_map: Optional[dict[str, str]] = None,
    provider: str = "",
) -> str:
    """Return a cheaper same-provider target for ``model`` if one is safe.

    This is intentionally conservative: the configured target must resolve to
    the same provider as the source model, the optional request provider must
    agree with the model's provider when both are known, and the target's rates
    must be strictly cheaper than the source rates.
    """
    model_lower = (model or "").lower()
    if not model_lower:
        return ""

    source_provider = provider_for_model(model_lower)
    request_provider = (provider or "").lower()
    if request_provider == "gemini":
        request_provider = "google"
    if source_provider and request_provider and source_provider != request_provider:
        return ""
    if not source_provider:
        source_provider = request_provider
    if not source_provider:
        return ""

    candidates = downgrade_map or DEFAULT_MODEL_DOWNGRADE_MAP
    unprefixed_model = _strip_provider_prefix(model_lower)

    for source_prefix, target_model in candidates.items():
        source_prefix_lower = (source_prefix or "").lower()
        target_model = target_model or ""
        target_lower = target_model.lower()
        if not source_prefix_lower or not target_lower:
            continue
        if not (
            model_lower.startswith(source_prefix_lower)
            or unprefixed_model.startswith(source_prefix_lower)
        ):
            continue

        target_provider = provider_for_model(target_lower)
        if target_provider == "gemini":
            target_provider = "google"
        if target_provider != source_provider:
            continue

        original_rates = _get_rates(source_provider, model_lower)
        target_rates = _get_rates(target_provider, target_lower)
        if sum(target_rates) >= sum(original_rates):
            continue
        return target_model

    return ""


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
        for (prov, prefix), rates in MODEL_OVERRIDES.items():
            if prov == prov_lower and model_lower.startswith(prefix.lower()):
                return rates

    # Fall back to provider baseline
    for info in PROVIDER_MAP.values():
        if info["name"] == prov_lower:
            return info["input_per_1m"], info["output_per_1m"]

    return 1.0, 3.0  # unknown provider — conservative default


# #2049: self-hosted / local model name hints. Routed to the "local" provider
# so _get_rates returns 0 (the user pays for hardware, not per token) instead
# of the conservative unknown-provider default.
_LOCAL_MODEL_HINTS = (
    "llama", "qwen", "mistral", "mixtral", "deepseek", "phi", "gemma", "codellama",
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
