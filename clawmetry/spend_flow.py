"""
clawmetry/spend_flow.py — node-wide AI spend flow (pure math).

Turns a window of raw session events into an Opik-style "where does the
money go" flow: input-side spend categories (user prompts, prior assistant
context, tool results, and the derived system/skills/MCP overhead) ->
runtime/harness -> output-side categories (thinking, assistant text,
built-in vs MCP tool calls), each with tokens + USD.

Honesty contract (mirrors :mod:`clawmetry.efficiency`):

  * **Totals are exact.** Every dollar comes from the event's stored
    ``cost_usd`` (the cost-of-record) or, when absent, the shared pricing
    table — never invented. Per-call category dollars always sum to the
    call's cost, so the flow reconciles with the Usage tab by construction.
  * **Shares are measured, then reconciled.** Category token shares are
    measured from real event content (chars/4, same heuristic as the
    compression meter in ``sync.py``) and scaled to fit the model-reported
    prompt volume. What content can't explain becomes the ``overhead``
    residual (system prompt + skills + MCP tool definitions) — a *derived*
    bucket, flagged ``basis: "residual"``, never a hardcoded fraction.
  * ``insufficient_data`` (with empty categories) below ``_MIN_CALLS``
    model calls — never a fake chart.

Handles both event worlds we ingest:

  * OpenClaw v3 — ``assistant`` / ``model.completed`` rows with Anthropic
    SDK usage envelopes (``data.message.usage`` etc.) and block-list
    content; the ``model.completed`` sibling ~100ms after ``assistant`` is
    deduped per (session, second) exactly like ``query_aggregates``.
  * Family adapters (Claude Code, Codex, Cursor, …) — per-block event rows
    (``message`` / ``thinking`` / ``tool_call`` / ``tool_result``) where
    the API-call usage lands in ``data.extra`` with camelCase keys
    (``inputTokens`` / ``cacheReadInputTokens`` / …) on whichever event
    closed the call.

Pure + unit-testable: no I/O, no store access, importable without duckdb.
NEVER raises — any unexpected failure yields the honest empty shape.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from clawmetry.providers_pricing import estimate_event_cost_usd

log = logging.getLogger("clawmetry.spend_flow")

# Below this many model calls in the window we return insufficient_data
# instead of a chart built on noise.
_MIN_CALLS = 5
# Same rough chars->tokens heuristic as sync._session_compression_potential.
_CHARS_PER_TOKEN = 4

INPUT_CATEGORIES = ("user_prompts", "prior_assistant", "tool_results", "overhead")
OUTPUT_CATEGORIES = ("thinking", "assistant_text", "builtin_tool_calls", "mcp_tool_calls")

# Every vendor spelling of the four usage counters we have to swallow
# (superset of local_store._USAGE_KEYS_* plus the family-adapter camelCase
# names that land under ``data.extra``).
_KEYS_INPUT = ("input_tokens", "inputTokens", "input")
_KEYS_OUTPUT = ("output_tokens", "outputTokens", "output")
_KEYS_CACHE_READ = (
    "cache_read_input_tokens", "cacheReadInputTokens",
    "cacheRead", "cache_read", "cache_read_tokens",
)
_KEYS_CACHE_WRITE = (
    "cache_creation_input_tokens", "cacheCreationInputTokens",
    "cacheWrite", "cache_write", "cache_write_tokens", "cache_creation_tokens",
)


def _read_int(d: Any, keys: tuple) -> int:
    """First parseable non-negative int across ``keys``; 0 on every failure."""
    if not isinstance(d, dict):
        return 0
    for k in keys:
        v = d.get(k)
        if v is None:
            continue
        try:
            iv = int(v)
        except (TypeError, ValueError):
            continue
        if iv > 0:
            return iv
    return 0


def _usage_from(data: Any) -> dict[str, int] | None:
    """Extract ``{input, output, cache_read, cache_write}`` from an event
    data blob, walking every envelope shape we ingest. ``None`` when the
    event carries no usage (i.e. it is not a model-call boundary)."""
    if not isinstance(data, dict):
        return None
    candidates: list[Any] = []
    msg = data.get("message")
    if isinstance(msg, dict):
        candidates.append(msg.get("usage"))
    candidates.append(data.get("usage"))
    pc = data.get("promptCache")
    if isinstance(pc, dict):
        candidates.append(pc.get("lastCallUsage"))
    am = data.get("assistantMessage")
    if isinstance(am, dict):
        candidates.append(am.get("usage"))
    # Family adapters (claude_code / codex / …) stash the call usage flat
    # inside ``extra`` — the "data.extra $0" class of bug lives exactly here.
    candidates.append(data.get("extra"))
    for u in candidates:
        if not isinstance(u, dict):
            continue
        inp = _read_int(u, _KEYS_INPUT)
        out = _read_int(u, _KEYS_OUTPUT)
        if inp <= 0 and out <= 0:
            continue
        return {
            "input": inp,
            "output": out,
            "cache_read": _read_int(u, _KEYS_CACHE_READ),
            "cache_write": _read_int(u, _KEYS_CACHE_WRITE),
        }
    return None


def _est_tokens(text: Any) -> int:
    """chars/4 token estimate; 0 for empty / non-string."""
    if not isinstance(text, str) or not text:
        return 0
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _is_mcp_tool(name: Any) -> bool:
    """Name-shape rule from routes/tool_catalog._classify: any ``a__b``
    name is MCP-namespaced; everything else counts as built-in."""
    return isinstance(name, str) and "__" in name


def _json_len_tokens(obj: Any) -> int:
    """Token estimate of a structure's JSON serialization (tool-call args)."""
    if obj is None:
        return 0
    if isinstance(obj, str):
        return _est_tokens(obj)
    try:
        return _est_tokens(json.dumps(obj, default=str))
    except Exception:
        return 0


def _measure_blocks(content: Any, m: dict[str, int]) -> None:
    """Accumulate an Anthropic-style block list (or plain string) into the
    per-event measure dict ``m`` (assistant-side keys)."""
    if isinstance(content, str):
        m["asst_text"] += _est_tokens(content)
        return
    if not isinstance(content, list):
        return
    for block in content:
        if not isinstance(block, dict):
            m["asst_text"] += _est_tokens(str(block)) if block else 0
            continue
        btype = block.get("type") or ""
        if btype == "text":
            m["asst_text"] += _est_tokens(block.get("text"))
        elif btype in ("thinking", "redacted_thinking"):
            m["thinking"] += _est_tokens(block.get("thinking") or block.get("text"))
        elif btype in ("tool_use", "tool_call"):
            tok = _json_len_tokens(block.get("input") or block.get("arguments"))
            if _is_mcp_tool(block.get("name")):
                m["tool_call_mcp"] += tok
            else:
                m["tool_call_builtin"] += tok
        elif btype == "tool_result":
            m["tool_result"] += _json_len_tokens(block.get("content"))


def _measure_event(event_type: str, data: Any) -> dict[str, int]:
    """Measure one event's content into token-estimate buckets.

    Returns ``{user, asst_text, thinking, tool_call_builtin,
    tool_call_mcp, tool_result}`` (all >= 0, zeros for irrelevant events).
    """
    m = {
        "user": 0, "asst_text": 0, "thinking": 0,
        "tool_call_builtin": 0, "tool_call_mcp": 0, "tool_result": 0,
    }
    if not isinstance(data, dict):
        return m
    et = (event_type or "").lower()
    role = str(data.get("role") or "").lower()
    content = data.get("content")
    if content is None and isinstance(data.get("message"), dict):
        content = data["message"].get("content")

    if "result" in et or role == "tool":
        m["tool_result"] += _json_len_tokens(content)
        return m
    if et in ("tool_call", "tool_use", "tool.call", "toolcall"):
        tok = _json_len_tokens(data.get("tool_calls")) or _json_len_tokens(content)
        if _is_mcp_tool(data.get("tool_name")):
            m["tool_call_mcp"] += tok
        else:
            m["tool_call_builtin"] += tok
        return m
    if et == "thinking":
        m["thinking"] += _est_tokens(content if isinstance(content, str) else None) \
            or _json_len_tokens(content)
        return m
    if role == "user" or et in ("user", "prompt.submitted"):
        if isinstance(content, str):
            m["user"] += _est_tokens(content)
        elif isinstance(content, list):
            # Claude Code style: user turns can carry tool_result blocks.
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    m["tool_result"] += _json_len_tokens(block.get("content"))
                elif isinstance(block, dict) and block.get("type") == "text":
                    m["user"] += _est_tokens(block.get("text"))
                else:
                    m["user"] += _json_len_tokens(block)
        else:
            m["user"] += _json_len_tokens(content)
        return m
    if role == "assistant" or et in ("assistant", "message", "model.completed"):
        _measure_blocks(content, m)
        return m
    return m


def _ts_second(ts: Any) -> str:
    """Coarse per-second bucket key for the assistant/model.completed dedupe
    (same shape as query_aggregates' EPOCH-seconds bucketing)."""
    s = str(ts or "")
    return s[:19]


def _envelope_rank(event_type: str) -> int:
    et = (event_type or "").lower()
    if et in ("assistant", "message"):
        return 2
    if et == "model.completed":
        return 1
    return 0


def _num(v: Any) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    if f != f or f in (float("inf"), float("-inf")) or f < 0:
        return 0.0
    return f


def _new_agg() -> dict[str, Any]:
    return {
        "calls": 0,
        "cost_usd": 0.0,
        "input_cost_usd": 0.0,
        "output_cost_usd": 0.0,
        "prompt_tokens": 0,
        "output_tokens": 0,
        "input": {c: {"tokens": 0.0, "cost_usd": 0.0} for c in INPUT_CATEGORIES},
        "output": {c: {"tokens": 0.0, "cost_usd": 0.0} for c in OUTPUT_CATEGORIES},
    }


def _merge_agg(dst: dict[str, Any], src: dict[str, Any]) -> None:
    for k in ("calls", "cost_usd", "input_cost_usd", "output_cost_usd",
              "prompt_tokens", "output_tokens"):
        dst[k] += src[k]
    for side in ("input", "output"):
        for cat, v in src[side].items():
            dst[side][cat]["tokens"] += v["tokens"]
            dst[side][cat]["cost_usd"] += v["cost_usd"]


def _categories_out(side: dict[str, Any], side_cost: float, basis_map: dict[str, str]) -> list[dict]:
    out = []
    for cat, v in side.items():
        tokens = int(round(v["tokens"]))
        cost = round(v["cost_usd"], 6)
        if tokens <= 0 and cost <= 0:
            continue
        out.append({
            "id": cat,
            "tokens": tokens,
            "cost_usd": cost,
            "pct_of_side_cost": round(v["cost_usd"] / side_cost * 100.0, 1) if side_cost > 0 else 0.0,
            "basis": basis_map.get(cat, "measured"),
        })
    out.sort(key=lambda c: -c["cost_usd"])
    return out


_BASIS_INPUT = {
    "user_prompts": "measured",
    "prior_assistant": "measured",
    "tool_results": "measured",
    # Residual between the model-reported prompt volume and what event
    # content explains: system prompt, skill + MCP tool definitions, and
    # content the ingest truncated (large tool results).
    "overhead": "residual",
}
# ``thinking`` can be measured (OpenClaw v3 keeps the block text) or a
# per-call residual (family adapters strip thinking text at ingest; when a
# call demonstrably contained a thinking block, thinking = output_tokens
# minus the measured text/tool-arg components). The engine reports which
# basis actually contributed via the category's ``basis`` field.
_BASIS_OUTPUT = {c: "measured" for c in OUTPUT_CATEGORIES}


def _scope_payload(agg: dict[str, Any], days: int,
                   basis_output: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "schema": 1,
        "window_days": days,
        "insufficient_data": agg["calls"] < _MIN_CALLS,
        "totals": {
            "calls": int(agg["calls"]),
            "cost_usd": round(agg["cost_usd"], 6),
            "input_cost_usd": round(agg["input_cost_usd"], 6),
            "output_cost_usd": round(agg["output_cost_usd"], 6),
            "prompt_tokens": int(round(agg["prompt_tokens"])),
            "output_tokens": int(round(agg["output_tokens"])),
        },
        "input_categories": _categories_out(agg["input"], agg["input_cost_usd"], _BASIS_INPUT),
        "output_categories": _categories_out(
            agg["output"], agg["output_cost_usd"], basis_output or _BASIS_OUTPUT),
    }


def _empty_slice(days: int) -> dict[str, Any]:
    out = _scope_payload(_new_agg(), days)
    out["runtimes"] = []
    out["links"] = []
    out["byRuntime"] = {}
    return out


# ── Spend-derived savings actions (efficiency.actions shape) ────────────────
# thinking_trim emission gates: thinking must dominate output spend and be
# real money before we suggest touching it. The 0.5 trim fraction is the
# hypothesis (routine sessions on a lower thinking setting), flagged
# estimate=True exactly like efficiency's context_trim.
_THINKING_SHARE_MIN = 0.40
_THINKING_MIN_WINDOW_COST_USD = 1.0
_THINKING_TRIM_FRACTION = 0.5
_MONTH_DAYS = 30.0


def spend_actions(slice_: Any) -> list[dict]:
    """Savings actions derived from a spend-flow scope, in the shape of
    :mod:`clawmetry.efficiency` ``actions`` (id / savings_monthly_usd /
    estimate / data — numbers only, the frontend owns the copy).

    Emits ``thinking_trim`` when thinking is at least
    ``_THINKING_SHARE_MIN`` of the scope's output spend and above the
    window-cost floor. The MCP-definition prune Opik ships is deliberately
    NOT emitted: MCP tool-definition token cost is not measurable from our
    stored events (it hides inside the input residual) and inventing a
    dollar figure would break the no-fabrication contract.

    Pure; never raises; ``[]`` on anything unexpected.
    """
    try:
        if not isinstance(slice_, dict) or slice_.get("insufficient_data"):
            return []
        try:
            days = max(1, int(slice_.get("window_days") or 7))
        except (TypeError, ValueError):
            days = 7
        totals = slice_.get("totals") or {}
        out_cost = _num(totals.get("output_cost_usd"))
        think = next(
            (c for c in (slice_.get("output_categories") or [])
             if isinstance(c, dict) and c.get("id") == "thinking"),
            None,
        )
        if think is None or out_cost <= 0:
            return []
        think_cost = _num(think.get("cost_usd"))
        if think_cost < _THINKING_MIN_WINDOW_COST_USD:
            return []
        share = think_cost / out_cost
        if share < _THINKING_SHARE_MIN:
            return []
        factor = _MONTH_DAYS / days
        return [{
            "id": "thinking_trim",
            "savings_monthly_usd": round(
                think_cost * _THINKING_TRIM_FRACTION * factor, 6),
            "estimate": True,
            "data": {
                "thinking_window_cost_usd": round(think_cost, 6),
                "thinking_pct_of_output_cost": round(share * 100.0, 1),
                "trim_fraction": _THINKING_TRIM_FRACTION,
                "window_days": days,
                "basis": str(think.get("basis") or "measured"),
            },
        }]
    except Exception:  # pragma: no cover - defensive, never-crash rule
        return []


def merge_spend_actions(eff: Any, spend_slice: Any) -> Any:
    """Append spend-derived actions to an efficiency slice, node-wide AND
    per-runtime (per-runtime honesty: each byRuntime entry only ever gets
    actions computed from its OWN spend scope). Mutates and returns ``eff``;
    a bad input returns ``eff`` unchanged. Never raises."""
    try:
        if not isinstance(eff, dict) or not isinstance(spend_slice, dict):
            return eff
        def _extend(scope_eff: dict, acts: list[dict]) -> None:
            if not acts:
                return
            existing = scope_eff.setdefault("actions", [])
            have = {a.get("id") for a in existing if isinstance(a, dict)}
            existing.extend(a for a in acts if a["id"] not in have)
            existing.sort(key=lambda a: -_num(a.get("savings_monthly_usd")))
        _extend(eff, spend_actions(spend_slice))
        by_rt = spend_slice.get("byRuntime") or {}
        for rt, scope in by_rt.items():
            entry = (eff.get("byRuntime") or {}).get(rt)
            if isinstance(entry, dict):
                _extend(entry, spend_actions(scope))
        return eff
    except Exception:  # pragma: no cover - defensive, never-crash rule
        return eff


def build_spend_flow_slice(events: list[dict], days: int = 7) -> dict:
    """Spend-flow slice for a node from a window of raw events.

    ``events``: lightweight event dicts (any order) with keys
    ``session_id, ts, event_type, model, data`` and optionally
    ``id, runtime, cost_usd``. ``runtime`` defaults to ``data._runtime``
    then ``"openclaw"`` — the caller (LocalStore) attaches the
    session-id-prefix runtime so this module never copies the prefix list.

    Returns the node-wide scope plus ``runtimes`` / ``links`` (Sankey
    edges: category -> ``runtime:<rt>`` -> category) and a ``byRuntime``
    map of per-runtime scopes. Node totals == sum of byRuntime totals ==
    sum of per-call costs, by construction.

    Pure; never raises. Bad events are skipped; empty input returns the
    honest ``insufficient_data`` shape.
    """
    try:
        days_i = int(days)
    except (TypeError, ValueError):
        days_i = 7
    if days_i <= 0:
        days_i = 7
    try:
        return _build(events or [], days_i)
    except Exception as exc:  # pragma: no cover - defensive, never-crash rule
        log.warning("spend_flow: slice build failed (%s); returning empty", exc)
        return _empty_slice(days_i)


def _build(events: list[dict], days: int) -> dict[str, Any]:
    # ── group by session, order by (ts, id) ──────────────────────────────
    sessions: dict[str, list[dict]] = {}
    for ev in events:
        if not isinstance(ev, dict):
            continue
        sid = str(ev.get("session_id") or "")
        if not sid:
            continue
        sessions.setdefault(sid, []).append(ev)
    for rows in sessions.values():
        rows.sort(key=lambda e: (str(e.get("ts") or ""), str(e.get("id") or "")))

    per_runtime: dict[str, dict[str, Any]] = {}
    thinking_bases: set[str] = set()

    def _finalize_call(agg: dict[str, Any], call: dict[str, Any]) -> None:
        """Allocate one call's output tokens/dollars across the output
        categories from the content measured for that call (the usage
        event's own assistant content plus its sibling events up to the
        next call). Family adapters strip thinking text at ingest, so when
        the call demonstrably contained a thinking block but no thinking
        was measured, thinking gets the RESIDUAL (output_tokens minus the
        measured text/tool-arg components) — never a hardcoded fraction.
        """
        o_tok = call["o_tok"]
        output_cost = call["output_cost"]
        if o_tok <= 0:
            return
        acc = call["acc"]
        others = acc["asst_text"] + acc["tool_call_builtin"] + acc["tool_call_mcp"]
        think = acc["thinking"]
        if think > 0:
            thinking_bases.add("measured")
        elif call["has_thinking"]:
            think = max(0.0, o_tok - others)
            if think > 0:
                thinking_bases.add("residual")
        total_m = think + others
        if total_m <= 0:
            agg["output"]["assistant_text"]["tokens"] += o_tok
            agg["output"]["assistant_text"]["cost_usd"] += output_cost
            return
        for tok, cat in (
            (think, "thinking"),
            (acc["asst_text"], "assistant_text"),
            (acc["tool_call_builtin"], "builtin_tool_calls"),
            (acc["tool_call_mcp"], "mcp_tool_calls"),
        ):
            share = tok / total_m
            if share <= 0:
                continue
            agg["output"][cat]["tokens"] += o_tok * share
            agg["output"][cat]["cost_usd"] += output_cost * share

    def _new_call_acc() -> dict[str, float]:
        return {"thinking": 0.0, "asst_text": 0.0,
                "tool_call_builtin": 0.0, "tool_call_mcp": 0.0}

    for sid, rows in sessions.items():
        # v3 dedupe: drop the slim model.completed sibling when an
        # assistant/message row shares its (session, second) bucket.
        rank2_seconds = {
            _ts_second(e.get("ts")) for e in rows
            if _envelope_rank(str(e.get("event_type") or "")) == 2
            and _usage_from(e.get("data")) is not None
        }

        run_user = run_asst = run_tool = 0.0
        rt = ""
        cur_call: dict[str, Any] | None = None
        cur_agg: dict[str, Any] | None = None

        for ev in rows:
            et = str(ev.get("event_type") or "")
            data = ev.get("data")
            if not rt:
                rt = str(
                    ev.get("runtime")
                    or (data.get("_runtime") if isinstance(data, dict) else "")
                    or "openclaw"
                )

            m = _measure_event(et, data)
            # Prompt-side content precedes the next call by definition.
            run_user += m["user"]
            run_tool += m["tool_result"]

            usage = _usage_from(data)
            if usage is not None and not (
                _envelope_rank(et) == 1
                and _ts_second(ev.get("ts")) in rank2_seconds
            ):
                # ── a model-call boundary ───────────────────────────────
                if cur_call is not None and cur_agg is not None:
                    _finalize_call(cur_agg, cur_call)
                model = str(ev.get("model") or "")
                p_tok = usage["input"] + usage["cache_read"] + usage["cache_write"]
                o_tok = usage["output"]
                in_price = estimate_event_cost_usd(
                    model,
                    input_tokens=usage["input"],
                    cache_read_tokens=usage["cache_read"],
                    cache_write_tokens=usage["cache_write"],
                )
                out_price = estimate_event_cost_usd(model, output_tokens=o_tok)
                call_cost = _num(ev.get("cost_usd"))
                if call_cost <= 0:
                    call_cost = in_price + out_price
                denom = in_price + out_price
                if denom > 0:
                    input_cost = call_cost * (in_price / denom)
                elif (p_tok + o_tok) > 0:
                    input_cost = call_cost * (p_tok / (p_tok + o_tok))
                else:
                    input_cost = 0.0
                output_cost = call_cost - input_cost

                agg = per_runtime.setdefault(rt or "openclaw", _new_agg())
                agg["calls"] += 1
                agg["cost_usd"] += call_cost
                agg["input_cost_usd"] += input_cost
                agg["output_cost_usd"] += output_cost
                agg["prompt_tokens"] += p_tok
                agg["output_tokens"] += o_tok

                # ── input-side attribution (context replayed so far;
                # excludes this call's own response, which is added to the
                # running totals below) ─────────────────────────────────
                measured = run_user + run_asst + run_tool
                if p_tok > 0:
                    if measured <= p_tok:
                        shares = {
                            "user_prompts": run_user,
                            "prior_assistant": run_asst,
                            "tool_results": run_tool,
                            "overhead": p_tok - measured,
                        }
                    else:
                        k = p_tok / measured
                        shares = {
                            "user_prompts": run_user * k,
                            "prior_assistant": run_asst * k,
                            "tool_results": run_tool * k,
                            "overhead": 0.0,
                        }
                    for cat, tok in shares.items():
                        if tok <= 0:
                            continue
                        agg["input"][cat]["tokens"] += tok
                        agg["input"][cat]["cost_usd"] += input_cost * (tok / p_tok)

                # This call's output accumulator starts with the usage
                # event's own assistant content (v3 puts the whole block
                # list here; family usage events are usually an empty
                # thinking block whose siblings follow).
                cur_call = {
                    "o_tok": o_tok,
                    "output_cost": output_cost,
                    "has_thinking": et == "thinking" or m["thinking"] > 0,
                    "acc": _new_call_acc(),
                }
                cur_agg = agg
            elif cur_call is not None:
                # Sibling assistant events belong to the current call's
                # response (family adapters emit one event per block).
                if et == "thinking" and m["thinking"] <= 0:
                    cur_call["has_thinking"] = True

            if cur_call is not None:
                cur_call["acc"]["thinking"] += m["thinking"]
                cur_call["acc"]["asst_text"] += m["asst_text"]
                cur_call["acc"]["tool_call_builtin"] += m["tool_call_builtin"]
                cur_call["acc"]["tool_call_mcp"] += m["tool_call_mcp"]

            # Assistant text + tool-call args are replayed as context on
            # later calls; thinking is stripped from replay (Anthropic).
            run_asst += m["asst_text"] + m["tool_call_builtin"] + m["tool_call_mcp"]

        if cur_call is not None and cur_agg is not None:
            _finalize_call(cur_agg, cur_call)

    # ── node scope + per-runtime scopes + links ─────────────────────────
    node = _new_agg()
    for agg in per_runtime.values():
        _merge_agg(node, agg)

    basis_out = dict(_BASIS_OUTPUT)
    if thinking_bases == {"residual"}:
        basis_out["thinking"] = "residual"
    elif len(thinking_bases) > 1:
        basis_out["thinking"] = "mixed"

    out = _scope_payload(node, days, basis_out)
    out["runtimes"] = sorted(
        (
            {
                "runtime": rt,
                "calls": int(a["calls"]),
                "cost_usd": round(a["cost_usd"], 6),
                "input_cost_usd": round(a["input_cost_usd"], 6),
                "output_cost_usd": round(a["output_cost_usd"], 6),
                "prompt_tokens": int(round(a["prompt_tokens"])),
                "output_tokens": int(round(a["output_tokens"])),
            }
            for rt, a in per_runtime.items()
        ),
        key=lambda r: -r["cost_usd"],
    )
    links: list[dict[str, Any]] = []
    for rt, a in per_runtime.items():
        for cat, v in a["input"].items():
            if v["cost_usd"] > 0 or v["tokens"] > 0:
                links.append({
                    "source": cat, "target": f"runtime:{rt}",
                    "cost_usd": round(v["cost_usd"], 6),
                    "tokens": int(round(v["tokens"])),
                })
        for cat, v in a["output"].items():
            if v["cost_usd"] > 0 or v["tokens"] > 0:
                links.append({
                    "source": f"runtime:{rt}", "target": cat,
                    "cost_usd": round(v["cost_usd"], 6),
                    "tokens": int(round(v["tokens"])),
                })
    out["links"] = links
    out["byRuntime"] = {
        rt: _scope_payload(a, days, basis_out) for rt, a in per_runtime.items()
    }
    return out
