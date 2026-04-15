"""
helpers/pricing.py — Pure helpers for mapping model names to providers.

Extracted from dashboard.py as Phase 6.1 of the incremental modularisation
(first move out of the module-level helper bag). These functions have no
module-level state and no cross-module dependencies — trivially safe to move.

Re-exported from dashboard.py so existing `_d._provider_from_model(...)`
calls in `routes/*.py` keep working without code changes there.
"""


def _provider_from_model(model_name):
    """Strict provider mapping — used for pricing table lookups.

    Prefix and substring match: `openai/`, `anthropic/`, `google/`,
    `openrouter/`, `xai/`; substring fallbacks for `gpt`, `codex`, `o1`,
    `claude`, `gemini`, `grok`.
    """
    m = str(model_name or "").lower()
    if m.startswith("openai/") or "gpt" in m or "codex" in m or m.startswith("o1"):
        return "openai"
    if m.startswith("anthropic/") or "claude" in m:
        return "anthropic"
    if m.startswith("google/") or "gemini" in m:
        return "google"
    if m.startswith("openrouter/"):
        return "openrouter"
    if m.startswith("xai/") or "grok" in m:
        return "xai"
    return "unknown"


def _infer_provider_from_model(model_name):
    """Best-effort provider inference for display only.

    Looser than `_provider_from_model` — matches substrings so
    `claude-3-5-sonnet` → anthropic without needing a prefix. Also
    recognises `local/other` for open-weights families (llama, mistral,
    qwen, deepseek).
    """
    m = (model_name or "").lower()
    if not m:
        return "unknown"
    if "claude" in m:
        return "anthropic"
    if "grok" in m or "x-ai" in m or m.startswith("xai"):
        return "xai"
    if "gpt" in m or "o1" in m or "o3" in m or "o4" in m:
        return "openai"
    if "gemini" in m:
        return "google"
    if "llama" in m or "mistral" in m or "qwen" in m or "deepseek" in m:
        return "local/other"
    return "unknown"
