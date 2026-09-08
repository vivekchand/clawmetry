"""Shared cost-derivation helper for the bundled runtime adapters.

Single source of truth for "given tokens + a model, what did this cost?".
Wraps the cache-aware pricing path (``clawmetry.providers_pricing.
estimate_event_cost_usd``), which:
  * resolves the provider from the model name when provider is "" / None,
  * applies Anthropic prompt-cache multipliers (read 0.1x, write 1.25x input),
  * resolves local / self-hosted models (ollama/llama/qwen/...) to a real 0.0,
  * never raises (returns 0.0 on any internal error).

We layer one extra rule on top that the pricing function does NOT enforce:
return ``None`` (not 0.0) when there is genuinely nothing to price -- no
model, or no billable tokens at all. That preserves each adapter's honesty
contract (cost_usd=None == "unknown", distinct from a real 0.0 for a free
local model).

Leaf module (no intra-package imports) so every adapter can import it without
circular-import risk. Nothing here raises.

This lives in OSS because the Free runtime adapters bundled here need it.
``clawmetry_pro.lib.cost`` carries a byte-identical implementation for the
paid adapters; the two are kept in lockstep by
``tests/test_adapter_cost_helper.py``.
"""
from __future__ import annotations

from typing import Optional

try:
    from clawmetry.providers_pricing import estimate_event_cost_usd
except Exception:  # pragma: no cover - pricing always ships with clawmetry
    estimate_event_cost_usd = None  # type: ignore[assignment]


def _coerce_int(value) -> int:
    """Best-effort non-negative int; 0 for anything non-numeric/None."""
    try:
        if isinstance(value, bool):
            return 0
        n = int(value)
        return n if n > 0 else 0
    except (TypeError, ValueError):
        return 0


def derive_cost_usd(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read: int = 0,
    cache_write: int = 0,
    provider: Optional[str] = None,
) -> Optional[float]:
    """Derive per-session/-event cost in USD from a model + token split.

    Reuses the cache-aware pricing path. The provider is resolved from the
    model name automatically when ``provider`` is None/"" -- callers do NOT
    need to pre-resolve it.

    Returns:
        float: the derived cost (>= 0.0). A legitimate ``0.0`` is returned for
               local / self-hosted models (the user pays for hardware, not per
               token) -- a real, correct cost, not "unknown".
        None:  only when pricing is genuinely impossible -- the pricing path is
               unavailable, the model is empty/missing, or there are zero
               billable tokens (input + output + cache_read + cache_write all 0).

    Never raises.
    """
    if estimate_event_cost_usd is None:
        return None

    model = (model or "").strip()
    if not model:
        return None

    in_tok = _coerce_int(input_tokens)
    out_tok = _coerce_int(output_tokens)
    cr_tok = _coerce_int(cache_read)
    cw_tok = _coerce_int(cache_write)

    # Nothing to price -- keep the adapter's honest "unknown" (None); don't
    # fabricate a 0.0 that would read as "this turn was free".
    if not (in_tok or out_tok or cr_tok or cw_tok):
        return None

    try:
        cost = estimate_event_cost_usd(
            model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cache_read_tokens=cr_tok,
            cache_write_tokens=cw_tok,
            provider=provider or "",
        )
    except Exception:
        return None

    # estimate_event_cost_usd never raises and returns a float; 0.0 here is a
    # *real* cost (local model, or a known provider with a zero-rate model),
    # so return it as-is rather than collapsing it to None.
    try:
        return float(cost)
    except (TypeError, ValueError):
        return None
