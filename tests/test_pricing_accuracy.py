"""Regression guard for pricing $0 / namespace drift (cloud #1576).

- Bare family names mistral/qwen/deepseek were routed to the "local" provider
  ($0) even for hosted API usage (qwen_code is a paid runtime that read $0).
- MODEL_OVERRIDES matched startswith-only, so namespaced ids
  (anthropic/claude-opus-4-1 via OpenRouter, us.anthropic.claude-... via Bedrock)
  missed every override and fell to the $3/$15 baseline (a ~5x undercount).
"""
import importlib

pp = importlib.import_module("clawmetry.providers_pricing")


def _rates(prov, model):
    return pp._get_rates(prov, model)


def test_mistral_routes_to_provider_not_local():
    assert pp.provider_for_model("mistral-large-latest") == "mistral"
    assert _rates("mistral", "mistral-large-latest")[0] > 0


def test_namespaced_claude_matches_bare_override():
    bare = _rates("anthropic", "claude-opus-4-1")
    openrouter = _rates("anthropic", "anthropic/claude-opus-4-1")
    bedrock = _rates("anthropic", "us.anthropic.claude-opus-4-1-20250805-v1:0")
    assert bare == openrouter == bedrock, (bare, openrouter, bedrock)
    # and it is the real opus rate, not the $3/$15 anthropic baseline
    assert bare[0] > 3.0, bare


def test_hosted_qwen_deepseek_not_zero():
    for name in ("qwen-max", "deepseek-chat"):
        assert pp.provider_for_model(name) != "local", name
        prov = pp.provider_for_model(name) or ""
        inp, out = _rates(prov, name)
        assert inp > 0 and out > 0, (name, inp, out)


def test_genuine_local_still_free():
    assert pp.provider_for_model("ollama/llama3.1") == "local"
    assert pp.provider_for_model("llama3.1") == "local"
    assert _rates("local", "llama3.1") == (0.0, 0.0)
