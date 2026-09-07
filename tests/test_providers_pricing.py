"""Pricing-table correctness for providers_pricing — the canonical per-token
cost source used across the app (cost-intel, out-loop attribution, budgets)."""
import os
import sys
import pytest

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


def test_current_gen_anthropic_rates_match_litellm():
    # Opus 4.5+ is a NEW, cheaper generation: $5/$25, NOT the old opus-4 $15/$75.
    # (Verified against LiteLLM model_prices — the table ccusage uses — 2026-06-08.
    # The previous assertion here pinned $15/$75 and codified a 3x over-charge
    # that made the founder's Claude Code show $103k vs ccusage's $16k.)
    assert _get_rates("anthropic", "claude-opus-4-5") == (5.0, 25.0)
    assert _get_rates("anthropic", "claude-opus-4-6") == (5.0, 25.0)
    assert _get_rates("anthropic", "claude-opus-4-7") == (5.0, 25.0)
    assert _get_rates("anthropic", "claude-opus-4-8") == (5.0, 25.0)
    # Old-gen opus stays $15/$75 (longest-prefix must not let 4-8 win on 4/4-1).
    assert _get_rates("anthropic", "claude-opus-4-20250514") == (15.0, 75.0)
    assert _get_rates("anthropic", "claude-opus-4-1-20250805") == (15.0, 75.0)
    assert _get_rates("anthropic", "claude-sonnet-4-6") == (3.0, 15.0)
    assert _get_rates("anthropic", "claude-haiku-4-5") == (1.0, 5.0)
    assert _get_rates("openai", "gpt-4o-mini") == (0.15, 0.60)
    assert _get_rates("openai", "gpt-4o") == (2.50, 10.00)


def test_opus_4_8_full_cost_matches_ccusage():
    # End-to-end cache-aware cost for a real opus-4-8 token split must equal the
    # LiteLLM/ccusage number (input $5, output $25, cache_write $6.25, read $0.50/M).
    c = estimate_event_cost_usd(
        "claude-opus-4-8", input_tokens=5_619_327, output_tokens=18_967_474,
        cache_read_tokens=5_828_754_946, cache_write_tokens=113_278_937,
        provider="anthropic",
    )
    assert abs(c - 4124.65) < 1.0, f"opus-4-8 cost {c} != ccusage 4124.65"


def test_unknown_provider_conservative_default():
    # Unknown model under a known provider → provider baseline (not free).
    assert _get_rates("openai", "totally-unknown-model") == (2.50, 10.00)
    # Fully unknown → conservative non-zero default.
    assert _get_rates("nobody", "nothing") == (1.0, 3.0)


def test_local_models_are_free():
    assert _get_rates("ollama", "llama3.2:3b") == (0.0, 0.0)
    assert _get_rates("", "ollama/llama3.2") == (0.0, 0.0)


@pytest.mark.parametrize("model,rates", [
    ("gpt-4.1", (2.0, 8.0)),
    ("gpt-4.1-mini", (0.4, 1.6)),
    ("gpt-4.1-nano", (0.1, 0.4)),
    ("gpt-5", (1.25, 10.0)),
    ("gpt-5-mini", (0.25, 2.0)),
    ("gpt-5-nano", (0.05, 0.4)),
    ("gpt-5.1", (1.25, 10.0)),
    ("gpt-5.2", (1.75, 14.0)),
    ("gpt-5.3-codex", (1.75, 14.0)),
    ("gpt-5.4", (2.5, 15.0)),
    ("gpt-5.4-mini", (0.75, 4.5)),
    ("gpt-5.4-nano", (0.2, 1.25)),
    ("gpt-5.4-pro", (30.0, 180.0)),
    ("gpt-5.5", (5.0, 30.0)),
    ("gpt-5.6", (4.0, 20.0)),
    ("gpt-5.6-sol", (4.0, 20.0)),
    ("gpt-5.6-terra", (2.0, 12.0)),
    ("gpt-5.6-luna", (0.2, 1.2)),
])
def test_openai_standard_rates_match_published_model_pages(model, rates):
    # https://developers.openai.com/api/docs/models/<model>, 2026-09-07.
    assert _get_rates("openai", model) == rates
    assert _get_rates("openai", "openai/" + model) == rates


@pytest.mark.parametrize("model,expected", [
    ("gpt-4o", 1.375),
    ("gpt-4o-mini", 0.0825),
    ("gpt-4.1", 0.65),
    ("gpt-5", 0.2375),
    ("openai/gpt-5-2025-08-07", 0.2375),
    ("gpt-5.6-sol", 0.76),
])
def test_openai_cache_reads_are_a_discounted_subset_of_input(model, expected):
    # One million TOTAL input tokens, of which 900k were cache hits.
    assert estimate_event_cost_usd(
        model, input_tokens=1_000_000, cache_read_tokens=900_000,
    ) == pytest.approx(expected)


def test_openai_cache_writes_replace_ordinary_input_tokens():
    # GPT-5.6: input $4, read $0.40, write $5, output $20 per million.
    assert estimate_event_cost_usd(
        "gpt-5.6", input_tokens=1000, output_tokens=100,
        cache_read_tokens=600, cache_write_tokens=200,
    ) == pytest.approx(0.00404)


def test_openai_cache_counters_are_bounded_by_total_input():
    assert estimate_event_cost_usd(
        "gpt-4o", input_tokens=100, cache_read_tokens=1000,
    ) == pytest.approx(0.000125)
    assert estimate_event_cost_usd(
        "gpt-4o", input_tokens=100, cache_read_tokens=-50,
    ) == pytest.approx(0.00025)


def test_openai_unknown_variants_do_not_inherit_a_published_cache_discount():
    assert _get_rates("openai", "gpt-5.6-turbo") == (2.5, 10.0)
    assert estimate_event_cost_usd(
        "unknown-openai-model", input_tokens=100, cache_read_tokens=100,
        provider="OPENAI",
    ) == pytest.approx(0.00025)
    # This model's published pricing has no cached-input rate.
    assert estimate_event_cost_usd(
        "gpt-5.4-pro", input_tokens=100, cache_read_tokens=100,
    ) == pytest.approx(0.003)
