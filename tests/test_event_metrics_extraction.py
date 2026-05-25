"""Regression tests for ``_extract_event_metrics`` (#1129 bug 2).

The local DuckDB store used to read ``e["cost_usd"]`` / ``e["token_count"]``
/ ``e["model"]`` directly off the top-level event dict — but OpenClaw's
gateway emits these nested under ``data.modelId`` and
``data.promptCache.lastCallUsage.{input,output,total}``. Result: every
event landed in DuckDB with model="", tokens=0, cost=null, and every
read-side aggregate (brain history, sessions, usage charts) showed empty
values.

These tests pin down the four shape contracts the helper must honour:
OpenClaw nested, Anthropic SDK nested, already-extracted top-level
(interceptor / claude-cli adapter / sync), and totally-empty graceful.
"""

from __future__ import annotations

from clawmetry.local_store import _extract_event_metrics


def test_openclaw_shape_extracts_model_and_tokens():
    """OpenClaw gateway shape: data.modelId + data.provider +
    data.promptCache.lastCallUsage.{input,output,total}."""
    ev = {
        "id": "e1",
        "node_id": "agent+n",
        "event_type": "message",
        "ts": "2026-05-13T00:00:00Z",
        "data": {
            "modelId": "claude-opus-4-7",
            "provider": "anthropic",
            "promptCache": {
                "lastCallUsage": {
                    "input": 1000,
                    "output": 234,
                    "total": 1234,
                }
            },
        },
    }
    cost, tokens, model = _extract_event_metrics(ev)
    assert model == "claude-opus-4-7"
    assert tokens == 1234
    # Cost is derived from input/output split + provider + model via pricing
    # table. anthropic/claude-opus-4 → (15.00, 75.00) per 1M tokens.
    # = 1000/1M * 15 + 234/1M * 75 = 0.015 + 0.01755 = 0.03255
    assert cost is not None
    assert abs(cost - 0.03255) < 1e-6


def test_openclaw_total_only_leaves_cost_none():
    """When only data.promptCache.lastCallUsage.total is known (no
    input/output split), cost can't be priced correctly with asymmetric
    rates, so it must be left None — read-side computes on demand."""
    ev = {
        "id": "e1b",
        "node_id": "agent+n",
        "event_type": "message",
        "ts": "2026-05-13T00:00:00Z",
        "data": {
            "modelId": "claude-opus-4-7",
            "provider": "anthropic",
            "promptCache": {"lastCallUsage": {"total": 1234}},
        },
    }
    cost, tokens, model = _extract_event_metrics(ev)
    assert model == "claude-opus-4-7"
    assert tokens == 1234
    assert cost is None


def test_anthropic_shape_sums_input_and_output_tokens():
    """Anthropic SDK shape: data.usage.{input_tokens,output_tokens}.
    Without total_tokens we sum the two."""
    ev = {
        "id": "e2",
        "node_id": "agent+n",
        "event_type": "message",
        "ts": "2026-05-13T00:00:00Z",
        "data": {
            "model": "claude-3-5-sonnet-latest",
            "usage": {"input_tokens": 100, "output_tokens": 50},
        },
    }
    cost, tokens, model = _extract_event_metrics(ev)
    assert model == "claude-3-5-sonnet-latest"
    assert tokens == 150
    # Provider is now inferred from the model (no explicit provider needed) so
    # the split IS priced — previously this left cost None, which surfaced as
    # $0 for real spend. The provider-required gate was the bug, not a feature.
    from clawmetry.providers_pricing import estimate_event_cost_usd
    expect = estimate_event_cost_usd(
        "claude-3-5-sonnet-latest", input_tokens=100, output_tokens=50)
    assert expect > 0
    assert cost is not None and abs(cost - expect) < 1e-9


def test_claude_code_extra_split_derives_cost_with_inferred_provider():
    """Claude Code / Codex shape: ``token_count`` pre-set (the lumped total)
    with the input/output split under ``data.extra`` and NO provider. This
    used to leave cost NULL — the ``$0 for a 100k-token session`` bug — because
    the split-extraction blocks were gated on ``tokens is None`` and the cost
    derivation required an explicit provider. Now the split is recovered from
    ``data.extra`` and the provider is inferred from the model."""
    ev = {
        "id": "cc1",
        "node_id": "n",
        "event_type": "message",
        "ts": "2026-05-25T00:00:00Z",
        "model": "claude-opus-4-7",
        "token_count": 3212,
        "data": {"role": "assistant",
                 "extra": {"inputTokens": 3166, "outputTokens": 46}},
    }
    cost, tokens, model = _extract_event_metrics(ev)
    assert tokens == 3212
    assert model == "claude-opus-4-7"
    from clawmetry.providers_pricing import estimate_event_cost_usd
    expect = estimate_event_cost_usd(
        "claude-opus-4-7", input_tokens=3166, output_tokens=46)
    assert expect > 0, "pricing assumption broke"
    assert cost is not None and abs(cost - expect) < 1e-9


def test_claude_code_extra_cache_tokens_are_priced():
    """Prompt-cache tokens under ``data.extra`` are priced (Anthropic cache
    multipliers) so a cache-heavy Claude Code turn isn't undercounted — cache
    creation dominates cost on these turns."""
    base = {
        "id": "cc2", "node_id": "n", "event_type": "message",
        "ts": "2026-05-25T00:00:00Z",
        "model": "claude-opus-4-7", "token_count": 3212,
    }
    no_cache = dict(base, data={
        "role": "assistant",
        "extra": {"inputTokens": 3166, "outputTokens": 46}})
    with_cache = dict(base, data={
        "role": "assistant",
        "extra": {"inputTokens": 3166, "outputTokens": 46,
                  "cacheReadInputTokens": 10319,
                  "cacheCreationInputTokens": 12078}})
    c0, _, _ = _extract_event_metrics(no_cache)
    c1, _, _ = _extract_event_metrics(with_cache)
    assert c0 is not None and c1 is not None
    assert c1 > c0, "cache tokens must add cost"


def test_top_level_already_extracted_values_are_preserved():
    """interceptor / claude-cli adapter / sync push fully-extracted events
    with top-level cost_usd / token_count / model. The helper must not
    touch nested data when the top-level values are present."""
    ev = {
        "id": "e3",
        "node_id": "agent+n",
        "event_type": "message",
        "ts": "2026-05-13T00:00:00Z",
        "cost_usd": 0.05,
        "token_count": 99,
        "model": "gpt-4",
        # Conflicting nested values — must be ignored when top-level present.
        "data": {
            "modelId": "claude-opus-4-7",
            "promptCache": {"lastCallUsage": {"total": 999999}},
        },
    }
    cost, tokens, model = _extract_event_metrics(ev)
    assert cost == 0.05
    assert tokens == 99
    assert model == "gpt-4"


def test_event_with_no_metrics_returns_all_none():
    """Tool-call / heartbeat / log events have no token usage. Helper must
    return all-None without raising — the store is permissive on ingest."""
    ev = {
        "id": "e4",
        "node_id": "agent+n",
        "event_type": "tool_call",
        "ts": "2026-05-13T00:00:00Z",
        "data": {"tool": "Read", "args": {"path": "/tmp/x"}},
    }
    cost, tokens, model = _extract_event_metrics(ev)
    assert cost is None
    assert tokens is None
    assert model is None


def test_event_with_no_data_does_not_crash():
    """Missing ``data`` key is normal for skeleton events."""
    ev = {
        "id": "e5",
        "node_id": "agent+n",
        "event_type": "noop",
        "ts": "2026-05-13T00:00:00Z",
    }
    assert _extract_event_metrics(ev) == (None, None, None)


def test_openclaw_message_shape_with_priced_cost():
    """Message events expose data.message.usage with already-priced
    data.message.usage.cost.total — prefer the priced value over re-derivation
    so we match what the SDK billed."""
    ev = {
        "id": "e6",
        "node_id": "agent+n",
        "event_type": "message",
        "ts": "2026-05-13T00:00:00Z",
        "data": {
            "message": {
                "model": "claude-sonnet-4",
                "provider": "anthropic",
                "usage": {
                    "inputTokens": 200,
                    "outputTokens": 80,
                    "totalTokens": 280,
                    "cost": {"total": 0.0123},
                },
            }
        },
    }
    cost, tokens, model = _extract_event_metrics(ev)
    assert model == "claude-sonnet-4"
    assert tokens == 280
    # The pre-priced value wins, not the re-derivation.
    assert cost == 0.0123
