"""Tests for `_extract_decoding_params` — issue #564.

Anthropic / OpenAI / OpenClaw events all carry sampling params in slightly
different nested shapes. The transcript modal renders a small "⚙ T=0.7 ·
top_p=1 · max=4096" pill next to each assistant turn, fed by this helper.
The pill's correctness depends on the helper handling every shape we've
seen in the wild without crashing on the weird ones.

The helper lives in ``routes.sessions`` — these tests import it directly
and never spin up a Flask app, so they stay fast (<200ms total).
"""

from __future__ import annotations

import pytest

from routes.sessions import _extract_decoding_params


# ── 1. data.params  (OpenClaw gateway model.completed) ─────────────────────
def test_extracts_from_data_params():
    """OpenClaw gateway emits the sampling config as a sibling of `content`
    on the model.completed event — under ``data.params``."""
    ev = {
        "type": "model.completed",
        "data": {
            "params": {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_tokens": 4096,
                "stop_sequences": ["</done>"],
            }
        },
    }
    out = _extract_decoding_params(ev)
    assert out == {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_tokens": 4096,
        "stop_sequences": ["</done>"],
    }


# ── 2. data.message.params  (Anthropic SDK request payload) ────────────────
def test_extracts_from_data_message_params():
    """The Anthropic-style adapter wraps the request as
    ``data.message.params`` — a literal copy of the API request kwargs."""
    ev = {
        "data": {
            "message": {
                "role": "assistant",
                "params": {
                    "temperature": 1.0,
                    "max_tokens": 8192,
                },
            }
        }
    }
    out = _extract_decoding_params(ev)
    assert out["temperature"] == 1.0
    assert out["max_tokens"] == 8192
    assert "top_p" not in out


# ── 3. data.config  (generic LLM-client wrapper) ───────────────────────────
def test_extracts_from_data_config():
    """Some adapters (our SDK wrapper, LiteLLM) write the sampling config
    under ``data.config`` instead of ``data.params``."""
    ev = {
        "data": {
            "config": {
                "temperature": 0.2,
                "top_p": 0.99,
            }
        }
    }
    out = _extract_decoding_params(ev)
    assert out == {"temperature": 0.2, "top_p": 0.99}


# ── 4. Mixed shapes — earlier bucket wins ──────────────────────────────────
def test_data_params_wins_over_data_config_for_same_key():
    """When the same key appears in multiple buckets we prefer the more
    specific path (``data.params``) over the generic fallback so a stale
    ``data.config`` value doesn't shadow the per-call override."""
    ev = {
        "data": {
            "params": {"temperature": 0.1},
            "config": {"temperature": 0.9, "max_tokens": 2048},
        }
    }
    out = _extract_decoding_params(ev)
    assert out["temperature"] == 0.1  # data.params wins
    assert out["max_tokens"] == 2048  # filled from data.config


# ── 5. Camel-case aliases — adapters that copy OpenClaw camelCase verbatim ─
def test_normalizes_camelcase_aliases():
    ev = {
        "data": {
            "params": {
                "maxTokens": 1024,
                "topP": 0.8,
                "topK": 20,
                "stopSequences": ["EOT"],
            }
        }
    }
    out = _extract_decoding_params(ev)
    assert out["max_tokens"] == 1024
    assert out["top_p"] == 0.8
    assert out["top_k"] == 20
    assert out["stop_sequences"] == ["EOT"]


def test_openai_max_completion_tokens_alias():
    """OpenAI's newer models use ``max_completion_tokens`` instead of
    ``max_tokens``. We map both to ``max_tokens`` so the UI stays uniform."""
    ev = {"data": {"params": {"max_completion_tokens": 512, "temperature": 0.5}}}
    out = _extract_decoding_params(ev)
    assert out["max_tokens"] == 512
    assert out["temperature"] == 0.5


# ── 6. stop_sequences shape coercion ───────────────────────────────────────
def test_stop_string_promotes_to_list():
    """OpenAI's ``stop`` parameter is sometimes a bare string. We wrap it
    in a list so the frontend can `.length`-check uniformly."""
    ev = {"data": {"params": {"stop": "END", "temperature": 0.3}}}
    out = _extract_decoding_params(ev)
    assert out["stop_sequences"] == ["END"]


def test_empty_stop_list_dropped():
    """An empty stop list isn't worth a pill segment."""
    ev = {"data": {"params": {"stop_sequences": [], "temperature": 0.0}}}
    out = _extract_decoding_params(ev)
    assert "stop_sequences" not in out
    assert out["temperature"] == 0.0  # zero is a valid temperature


# ── 7. Flat shape — message dict passed directly ───────────────────────────
def test_flat_params_on_root():
    """When the caller passes the unwrapped message dict the helper still
    finds params via the flat fallback path."""
    msg = {"role": "assistant", "params": {"temperature": 0.4}}
    out = _extract_decoding_params(msg)
    assert out["temperature"] == 0.4


# ── 8. Robustness — bad input never raises ────────────────────────────────
@pytest.mark.parametrize(
    "bad",
    [
        None,
        "string",
        123,
        [],
        {"data": "not a dict"},
        {"data": {"params": "not a dict"}},
        {"data": {"params": {"temperature": None}}},
        {"data": {"params": {"temperature": "0.7"}}},  # wrong type — dropped
        {"data": {"message": "not a dict"}},
        {"data": {"message": {"params": None}}},
    ],
)
def test_bad_input_returns_empty(bad):
    out = _extract_decoding_params(bad)
    assert out == {}


# ── 9. Missing fields — only present keys returned ────────────────────────
def test_only_temperature_present():
    ev = {"data": {"params": {"temperature": 0.6}}}
    out = _extract_decoding_params(ev)
    assert out == {"temperature": 0.6}


def test_no_decoding_keys_at_all():
    ev = {"data": {"params": {"unrelated": "value"}}}
    out = _extract_decoding_params(ev)
    assert out == {}


# ── 10. Zero / boundary values ─────────────────────────────────────────────
def test_temperature_zero_kept():
    ev = {"data": {"params": {"temperature": 0}}}
    out = _extract_decoding_params(ev)
    assert out["temperature"] == 0.0
    assert isinstance(out["temperature"], float)


def test_top_k_int_coercion():
    ev = {"data": {"params": {"top_k": 50.0}}}
    out = _extract_decoding_params(ev)
    assert out["top_k"] == 50
    assert isinstance(out["top_k"], int)
