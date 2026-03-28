"""
ClawMetry provider detection and pricing table.

Prices are per 1M tokens (USD), sourced from provider pricing pages.
Updated: 2026-03-28. These are approximate — actual costs from API responses
take precedence when available.
"""
from __future__ import annotations

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


def _get_rates(provider: str, model: str) -> tuple[float, float]:
    """Return (input_per_1m, output_per_1m) for a provider+model combo."""
    if model:
        model_lower = model.lower()
        for (prov, prefix), rates in MODEL_OVERRIDES.items():
            if prov == provider and model_lower.startswith(prefix.lower()):
                return rates

    # Fall back to provider baseline
    for info in PROVIDER_MAP.values():
        if info["name"] == provider:
            return info["input_per_1m"], info["output_per_1m"]

    return 1.0, 3.0  # unknown provider — conservative default
