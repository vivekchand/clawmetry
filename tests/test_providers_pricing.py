"""Pricing-table correctness for providers_pricing — the canonical per-token
cost source used across the app (cost-intel, out-loop attribution, budgets)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry.providers_pricing import (
    _get_rates,
    estimate_event_cost_usd,
    provider_for_model,
)


def test_gemini_priced_under_google_provider_alias():
    # provider_for_model() returns "google" for Gemini, but the pricing tables
    # key on "gemini" — without the alias every Gemini call fell through to the
    # $1/$3 unknown default (a ~10x over-charge on flash). Regression guard.
    assert provider_for_model("gemini-2.0-flash") == "google"
    assert _get_rates("google", "gemini-2.0-flash") == (0.10, 0.40)
    assert _get_rates("google", "gemini-1.5-pro") == (1.25, 5.00)
    # the inferred-provider path (the common one) prices correctly now
    assert abs(estimate_event_cost_usd("gemini-2.0-flash", 1_000_000, 0) - 0.10) < 1e-9


def test_explicit_gemini_provider_still_works():
    assert _get_rates("gemini", "gemini-2.0-flash") == (0.10, 0.40)


def test_anthropic_openai_rates_unchanged():
    assert _get_rates("anthropic", "claude-opus-4-8") == (15.0, 75.0)
    assert _get_rates("anthropic", "claude-sonnet-4-6") == (3.0, 15.0)
    assert _get_rates("openai", "gpt-4o-mini") == (0.15, 0.60)
    assert _get_rates("openai", "gpt-4o") == (2.50, 10.00)


def test_unknown_provider_conservative_default():
    # Unknown model under a known provider → provider baseline (not free).
    assert _get_rates("openai", "totally-unknown-model") == (2.50, 10.00)
    # Fully unknown → conservative non-zero default.
    assert _get_rates("nobody", "nothing") == (1.0, 3.0)


def test_local_models_are_free():
    assert _get_rates("ollama", "llama3.2:3b") == (0.0, 0.0)
    assert _get_rates("", "ollama/llama3.2") == (0.0, 0.0)
