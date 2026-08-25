"""Context windows must be sized per provider, with visible provenance.

Before ``clawmetry/context_windows.py`` the resolver knew two numbers, both
Anthropic's (200K, and 1M for ``[1m]`` variants), and measured all 26
runtimes with that ruler. The consequences were symmetric and both silent:

  * a 300K-token GPT-5 turn rendered as ">100% blown" — GPT-5 is 400K, so it
    was at 75%;
  * a genuinely blown 130K DeepSeek turn (128K window) rendered as a
    comfortable 65%.

These tests pin the per-provider table, the provenance every answer carries,
and the family-aware ladder used when a measurement proves the table wrong.
"""

from __future__ import annotations

import pytest

from clawmetry.context_windows import (
    DEFAULT_CONTEXT_WINDOW,
    MODEL_CONTEXT_WINDOWS,
    context_window_for_model,
    resolve_context_window,
)


# ── the regression that motivated the module ─────────────────────────────

def test_gpt5_is_not_measured_with_anthropics_ruler():
    """A 300K GPT-5 prompt is at 75% of 400K, not 150% of 200K."""
    cw = resolve_context_window("gpt-5-codex", 300_000)
    assert cw.tokens == 400_000
    assert 100.0 * 300_000 / cw.tokens == pytest.approx(75.0)


def test_deepseek_overflow_is_not_hidden_by_a_200k_default():
    """128K is DeepSeek's real window; a 130K prompt is over it, and the
    resolver must not paper that over with Anthropic's 200K."""
    assert resolve_context_window("deepseek-chat").tokens == 128_000


@pytest.mark.parametrize("model,expected", [
    ("claude-opus-4-7", 200_000),
    ("claude-opus-4-8", 1_000_000),
    ("gpt-5-codex", 400_000),
    ("gpt-4o-mini", 128_000),
    ("gemini-2.5-pro", 1_000_000),
    ("gemini-1.5-pro", 2_000_000),
    ("grok-4-latest", 256_000),
    ("kimi-k2-0905", 256_000),
    ("qwen3-coder-480b", 256_000),
    ("deepseek-reasoner", 128_000),
    ("codestral-latest", 256_000),
    ("llama-3.3-70b", 128_000),
])
def test_per_provider_windows(model, expected):
    assert context_window_for_model(model) == expected


# ── provenance ───────────────────────────────────────────────────────────

def test_unknown_model_says_it_is_guessing():
    """The whole point: an unknown model must be flagged, not silently
    rendered with the same authority as a looked-up one."""
    cw = resolve_context_window("some-bespoke-local-model")
    assert cw.tokens == DEFAULT_CONTEXT_WINDOW
    assert cw.source == "default"
    assert cw.confidence == "fallback"
    assert cw.is_known is False


def test_table_hit_is_marked_inferred_and_names_its_match():
    cw = resolve_context_window("gpt-5-codex")
    assert (cw.source, cw.confidence) == ("model_table", "inferred")
    assert cw.matched == "GPT-5"
    assert cw.is_known is True


def test_explicit_marker_beats_the_table():
    cw = resolve_context_window("claude-opus-4-7[1m]")
    assert cw.tokens == 1_000_000
    assert (cw.source, cw.confidence) == ("explicit_marker", "exact")


def test_measurement_beats_everything():
    """A prompt the provider accepted cannot exceed the provider's window, so
    a measurement above the resolved window proves the resolution wrong."""
    cw = resolve_context_window("claude-opus-4-7", 323_485)
    assert cw.source == "observed_floor"
    assert cw.confidence == "exact"
    assert cw.tokens >= 323_485


# ── the family-aware ladder ──────────────────────────────────────────────

def test_anthropic_floor_snaps_to_1m_not_an_invented_400k_tier():
    """Anthropic ships 200K and 1M. Snapping a 323K Claude prompt to the
    generic ladder's 400K rung would fabricate a denominator from a tier that
    does not exist — the exact class of bug this module exists to prevent."""
    assert resolve_context_window("claude-opus-4-7", 323_485).tokens == 1_000_000


def test_openai_floor_uses_openais_rungs():
    """OpenAI does ship a 400K tier, so a 300K measurement on an unrecognised
    OpenAI model belongs there, not up at 1M."""
    assert resolve_context_window("gpt-4o", 300_000).tokens == 400_000


def test_floor_rounds_up_past_the_largest_known_tier():
    assert resolve_context_window("claude-opus-4-7", 1_300_000).tokens == 2_000_000


# ── operator override ────────────────────────────────────────────────────

def test_env_override_pins_the_window(monkeypatch):
    """The air-gapped / bespoke-model escape hatch: our table can never be
    right for a private model, so the operator gets the last word."""
    monkeypatch.setenv("CLAWMETRY_CONTEXT_WINDOW", "512000")
    cw = resolve_context_window("whatever-model")
    assert cw.tokens == 512_000
    assert cw.source == "explicit_marker"


def test_garbage_env_override_is_ignored_not_fatal(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_CONTEXT_WINDOW", "not-a-number")
    assert resolve_context_window("gpt-5").tokens == 400_000


# ── table hygiene ────────────────────────────────────────────────────────

def test_table_is_ordered_most_specific_first():
    """A broader pattern placed above a narrower one silently shadows it —
    ``gpt-4`` before ``gpt-4o`` would send every 4o model to the wrong
    window. Guard the ordering rather than the individual numbers."""
    seen: list[str] = []
    for pattern, _tokens, _label, _family in MODEL_CONTEXT_WINDOWS:
        for earlier in seen:
            assert earlier not in pattern, (
                f"'{pattern}' is shadowed by the earlier, broader '{earlier}'"
            )
        seen.append(pattern)


def test_never_raises_on_junk_input():
    for junk in (None, "", "   ", 12345, object()):
        assert resolve_context_window(junk).tokens > 0  # type: ignore[arg-type]


def test_observed_tokens_junk_is_survivable():
    assert resolve_context_window("gpt-5", None).tokens == 400_000  # type: ignore[arg-type]
    assert resolve_context_window("gpt-5", -5).tokens == 400_000


# ── the 1M marker must not fire on a coincidence ─────────────────────────

@pytest.mark.parametrize("model", [
    "some-model-21m-x",   # "21m" contains "1m" but is not a marker
    "model-1mb-variant",  # "1mb" likewise
    "a1m",                # no separator on the left
    "llama-31m-x",        # digit-run collision inside a real family
])
def test_1m_marker_does_not_fire_on_a_substring_coincidence(model):
    """The marker is matched inside a free-text model string, so it has to
    require a separator or a string edge on both sides. A naive ``"1m" in m``
    would size several of these at 1M and silently make every utilisation
    reading on them a fifth of the truth."""
    assert resolve_context_window(model).source != "explicit_marker"


@pytest.mark.parametrize("model", [
    "claude-opus-4-7[1m]",
    "claude-opus-4-7-1m",
    "claude_opus_4_7_1m",
    "ds-v3-1m",
    "qwen-1m-preview",
])
def test_1m_marker_fires_on_every_separator_style(model):
    cw = resolve_context_window(model)
    assert cw.source == "explicit_marker"
    assert cw.tokens == 1_000_000


def test_gpt_4_1_mini_is_not_shadowed_into_the_4o_window():
    """``gpt-4.1-mini`` normalises to ``gpt-4-1-mini`` and must match the
    1M GPT-4.1 entry, not fall through to a smaller one."""
    assert resolve_context_window("gpt-4.1-mini").tokens == 1_000_000
    # ...while 4o-mini keeps its own, genuinely smaller window.
    assert resolve_context_window("gpt-4o-mini").tokens == 128_000
