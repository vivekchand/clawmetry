"""Tests for clawmetry/spend_flow.py (node-wide spend flow, pure math)
and the GET /api/spend-flow endpoint (routes/spend_flow.py).

Pure-math unit tests with synthetic events (acceptable for unit tests per
FLYWHEEL — these don't claim the user-facing feature works E2E). Dollar
expectations are recomputed IN the tests from clawmetry.providers_pricing
so they can't drift from the pricing table. The reconciliation invariants
(category sums == call totals == node totals) are the point of the module,
so most tests assert them directly.
"""
from __future__ import annotations

import pytest

from clawmetry.spend_flow import (
    INPUT_CATEGORIES,
    OUTPUT_CATEGORIES,
    _usage_from,
    build_spend_flow_slice,
)

MODEL = "claude-sonnet-4"


# ── event builders ──────────────────────────────────────────────────────────

def _ev(sid, ts, etype, data, model=MODEL, cost=0.0, eid=None, runtime=None):
    ev = {
        "id": eid or f"{sid}-{ts}-{etype}",
        "session_id": sid,
        "ts": ts,
        "event_type": etype,
        "model": model,
        "data": data,
        "cost_usd": cost,
    }
    if runtime:
        ev["runtime"] = runtime
    return ev


def _family_user(sid, ts, text, runtime="claude_code"):
    return _ev(sid, ts, "message", {"role": "user", "content": text}, runtime=runtime)


def _family_call(sid, ts, *, inp, out, cr=0, cw=0, cost=0.0, text="",
                 runtime="claude_code"):
    """Family-adapter shape: usage lands flat in data.extra (camelCase)."""
    data = {
        "role": "assistant",
        "content": text,
        "extra": {
            "inputTokens": inp,
            "outputTokens": out,
            "cacheReadInputTokens": cr,
            "cacheCreationInputTokens": cw,
        },
    }
    return _ev(sid, ts, "message", data, cost=cost, runtime=runtime)


def _cat_map(payload, side):
    return {c["id"]: c for c in payload[f"{side}_categories"]}


# ── usage extraction ────────────────────────────────────────────────────────

def test_usage_from_sdk_envelope():
    u = _usage_from({"message": {"usage": {
        "input_tokens": 100, "output_tokens": 20,
        "cache_read_input_tokens": 300, "cache_creation_input_tokens": 40,
    }}})
    assert u == {"input": 100, "output": 20, "cache_read": 300, "cache_write": 40}


def test_usage_from_family_extra_camelcase():
    """The data.extra camelCase shape (Claude Code / Codex family ingest) —
    the '$0 cost' class of bug is exactly this envelope being missed."""
    u = _usage_from({"role": "assistant", "extra": {
        "inputTokens": 7, "outputTokens": 9,
        "cacheReadInputTokens": 11, "cacheCreationInputTokens": 13,
    }})
    assert u == {"input": 7, "output": 9, "cache_read": 11, "cache_write": 13}


def test_usage_from_non_usage_event_is_none():
    assert _usage_from({"role": "user", "content": "hi"}) is None
    assert _usage_from("not a dict") is None
    assert _usage_from({"extra": {"isError": True}}) is None


# ── empty / insufficient / garbage input ────────────────────────────────────

def test_empty_events_honest_shape():
    out = build_spend_flow_slice([], days=7)
    assert out["insufficient_data"] is True
    assert out["totals"]["cost_usd"] == 0.0
    assert out["totals"]["calls"] == 0
    assert out["input_categories"] == []
    assert out["output_categories"] == []
    assert out["runtimes"] == []
    assert out["links"] == []
    assert out["byRuntime"] == {}


def test_garbage_events_never_raise():
    out = build_spend_flow_slice(
        [None, 42, "x", {}, {"session_id": ""}, {"session_id": "s", "data": b"\xff"}],
        days="not-a-number",
    )
    assert out["window_days"] == 7
    assert out["insufficient_data"] is True


def test_insufficient_below_min_calls():
    evs = [_family_call("claude_code:s1", "2026-08-01T00:00:01", inp=100, out=10)]
    out = build_spend_flow_slice(evs, days=7)
    assert out["totals"]["calls"] == 1
    assert out["insufficient_data"] is True
    # Data is still returned (the UI decides how to render thin windows).
    assert out["totals"]["prompt_tokens"] == 100


# ── reconciliation invariants (the point of the module) ─────────────────────

def _mixed_window():
    """Two sessions on two runtimes with prompts, tool results, and calls."""
    evs = []
    sid_a = "claude_code:aaaa"
    evs.append(_family_user(sid_a, "2026-08-01T10:00:00", "x" * 400))
    for i in range(3):
        ts = f"2026-08-01T10:00:{10 + i * 10:02d}"
        evs.append(_family_call(
            sid_a, ts, inp=1000 + i * 500, out=200, cr=2000, cw=100,
            cost=0.05, text="y" * 800, runtime="claude_code"))
        evs.append(_ev(sid_a, ts + ".500", "tool_result",
                       {"role": "tool", "content": "z" * 2000},
                       runtime="claude_code"))
    sid_b = "11111111-2222-3333-4444-555555555555"  # bare UUID -> openclaw
    evs.append(_ev(sid_b, "2026-08-01T11:00:00", "prompt.submitted",
                   {"role": "user", "content": "w" * 600, "_runtime": "openclaw"}))
    for i in range(3):
        ts = f"2026-08-01T11:00:{10 + i * 10:02d}"
        evs.append(_ev(sid_b, ts, "assistant", {
            "role": "assistant",
            "message": {
                "usage": {"input_tokens": 800, "output_tokens": 150,
                          "cache_read_input_tokens": 1000},
                "content": [
                    {"type": "thinking", "thinking": "t" * 400},
                    {"type": "text", "text": "a" * 400},
                    {"type": "tool_use", "name": "mcp__srv__go", "input": {"q": "b" * 100}},
                ],
            },
            "_runtime": "openclaw",
        }, cost=0.03))
    return evs


def test_category_dollars_reconcile_to_call_totals():
    out = build_spend_flow_slice(_mixed_window(), days=7)
    t = out["totals"]
    assert t["calls"] == 6
    assert out["insufficient_data"] is False
    # cost-of-record: 3 * 0.05 + 3 * 0.03
    assert t["cost_usd"] == pytest.approx(0.24, abs=1e-6)
    assert t["input_cost_usd"] + t["output_cost_usd"] == pytest.approx(t["cost_usd"], abs=1e-6)
    in_cats = sum(c["cost_usd"] for c in out["input_categories"])
    out_cats = sum(c["cost_usd"] for c in out["output_categories"])
    assert in_cats == pytest.approx(t["input_cost_usd"], abs=1e-4)
    assert out_cats == pytest.approx(t["output_cost_usd"], abs=1e-4)


def test_category_tokens_reconcile_to_prompt_volume():
    out = build_spend_flow_slice(_mixed_window(), days=7)
    t = out["totals"]
    in_tok = sum(c["tokens"] for c in out["input_categories"])
    out_tok = sum(c["tokens"] for c in out["output_categories"])
    # Per-call shares are scaled to exactly the reported prompt volume.
    assert in_tok == pytest.approx(t["prompt_tokens"], abs=len(out["input_categories"]) + 2)
    assert out_tok == pytest.approx(t["output_tokens"], abs=len(out["output_categories"]) + 2)


def test_by_runtime_sums_to_node():
    out = build_spend_flow_slice(_mixed_window(), days=7)
    assert set(out["byRuntime"]) == {"claude_code", "openclaw"}
    node_cost = sum(s["totals"]["cost_usd"] for s in out["byRuntime"].values())
    assert node_cost == pytest.approx(out["totals"]["cost_usd"], abs=1e-6)
    node_calls = sum(s["totals"]["calls"] for s in out["byRuntime"].values())
    assert node_calls == out["totals"]["calls"]


def test_links_reconcile_per_runtime():
    out = build_spend_flow_slice(_mixed_window(), days=7)
    for rt, scope in out["byRuntime"].items():
        into_rt = sum(l["cost_usd"] for l in out["links"]
                      if l["target"] == f"runtime:{rt}")
        outof_rt = sum(l["cost_usd"] for l in out["links"]
                       if l["source"] == f"runtime:{rt}")
        assert into_rt == pytest.approx(scope["totals"]["input_cost_usd"], abs=1e-4)
        assert outof_rt == pytest.approx(scope["totals"]["output_cost_usd"], abs=1e-4)


# ── attribution behaviour ───────────────────────────────────────────────────

def test_overhead_is_residual_never_negative():
    # First call: tiny measured content, huge reported prompt -> overhead.
    evs = [
        _family_user("claude_code:s", "2026-08-01T00:00:00", "hi"),
        _family_call("claude_code:s", "2026-08-01T00:00:01",
                     inp=10_000, out=10, cost=0.01),
    ]
    out = build_spend_flow_slice(evs, days=7)
    cats = _cat_map(out, "input")
    assert cats["overhead"]["basis"] == "residual"
    assert cats["overhead"]["tokens"] > 9000
    # Overestimated content (more measured chars than reported prompt)
    # scales down instead of going negative.
    evs2 = [
        _family_user("claude_code:s2", "2026-08-01T00:00:00", "x" * 100_000),
        _family_call("claude_code:s2", "2026-08-01T00:00:01",
                     inp=100, out=10, cost=0.01),
    ]
    out2 = build_spend_flow_slice(evs2, days=7)
    cats2 = _cat_map(out2, "input")
    assert "overhead" not in cats2
    assert cats2["user_prompts"]["tokens"] == pytest.approx(100, abs=2)


def test_tool_results_accumulate_as_prior_context():
    """A tool result should be attributed on the NEXT call's prompt."""
    sid = "claude_code:s3"
    evs = [
        _family_user(sid, "2026-08-01T00:00:00", "q" * 400),
        _family_call(sid, "2026-08-01T00:00:01", inp=200, out=10, cost=0.01),
        _ev(sid, "2026-08-01T00:00:02", "tool_result",
            {"role": "tool", "content": "r" * 8000}, runtime="claude_code"),
        _family_call(sid, "2026-08-01T00:00:03", inp=2400, out=10, cost=0.01),
    ]
    out = build_spend_flow_slice(evs, days=7)
    cats = _cat_map(out, "input")
    assert cats["tool_results"]["tokens"] > 1500


def test_output_split_thinking_vs_text_vs_tools():
    sid = "s4"
    evs = [_ev(sid, "2026-08-01T00:00:01", "assistant", {
        "role": "assistant",
        "message": {
            "usage": {"input_tokens": 100, "output_tokens": 1000},
            "content": [
                {"type": "thinking", "thinking": "t" * 2400},   # 600 tok
                {"type": "text", "text": "a" * 1200},           # 300 tok
                {"type": "tool_use", "name": "Read", "input": {"f": "x" * 200}},
                {"type": "tool_use", "name": "mcp__gh__pr", "input": {"n": "y" * 200}},
            ],
        },
    }, cost=0.02)]
    out = build_spend_flow_slice(evs, days=7)
    cats = _cat_map(out, "output")
    assert set(cats) == set(OUTPUT_CATEGORIES)
    assert cats["thinking"]["tokens"] > cats["assistant_text"]["tokens"]
    assert cats["builtin_tool_calls"]["tokens"] > 0
    assert cats["mcp_tool_calls"]["tokens"] > 0
    total = sum(c["tokens"] for c in cats.values())
    assert total == pytest.approx(1000, abs=4)


def test_family_thinking_residual():
    """Family adapters strip thinking text at ingest: the call's usage rides
    on an EMPTY 'thinking' event, and the response text follows as sibling
    events. Thinking must get the residual output (o_tok - measured text),
    flagged basis='residual' — and the siblings must be attributed to THIS
    call, not the next one (the off-by-one the live data exposed)."""
    sid = "claude_code:s8"
    call = _ev(sid, "2026-08-01T00:00:01", "thinking", {
        "role": "assistant", "content": "",
        "extra": {"inputTokens": 500, "outputTokens": 1000},
    }, cost=0.02, runtime="claude_code")
    sibling_text = _ev(sid, "2026-08-01T00:00:02", "message",
                       {"role": "assistant", "content": "a" * 1600},  # ~400 tok
                       runtime="claude_code")
    sibling_tool = _ev(sid, "2026-08-01T00:00:03", "tool_call",
                       {"role": "assistant", "content": "",
                        "tool_name": "Bash", "tool_calls": [{"name": "Bash", "arguments": {"command": "x" * 380}}]},
                       runtime="claude_code")
    out = build_spend_flow_slice([call, sibling_text, sibling_tool], days=7)
    cats = _cat_map(out, "output")
    assert cats["thinking"]["basis"] == "residual"
    # residual ~ 1000 - 400 - ~100 = ~500; allocation is proportional so
    # thinking ends up the largest single output category.
    assert cats["thinking"]["tokens"] > cats["assistant_text"]["tokens"] > 0
    assert cats["builtin_tool_calls"]["tokens"] > 0
    total = sum(c["tokens"] for c in cats.values())
    assert total == pytest.approx(1000, abs=4)


def test_output_fallback_to_assistant_text():
    """model.completed with usage but no content: output lands honestly in
    assistant_text rather than being dropped."""
    evs = [_ev("s5", "2026-08-01T00:00:01", "model.completed",
               {"promptCache": {"lastCallUsage": {"input": 500, "output": 80}}},
               cost=0.01)]
    out = build_spend_flow_slice(evs, days=7)
    cats = _cat_map(out, "output")
    assert cats["assistant_text"]["tokens"] == 80


def test_v3_sibling_dedupe():
    """assistant + model.completed in the same (session, second) bucket must
    count ONCE (query_aggregates' dedupe rule) or every turn double-bills."""
    sid = "s6"
    usage = {"input_tokens": 1000, "output_tokens": 100}
    evs = [
        _ev(sid, "2026-08-01T00:00:01.100", "assistant",
            {"role": "assistant",
             "message": {"usage": dict(usage), "content": "hello"}}, cost=0.02),
        _ev(sid, "2026-08-01T00:00:01.200", "model.completed",
            {"promptCache": {"lastCallUsage": {"input": 1000, "output": 100}}},
            cost=0.02),
    ]
    out = build_spend_flow_slice(evs, days=7)
    assert out["totals"]["calls"] == 1
    assert out["totals"]["cost_usd"] == pytest.approx(0.02, abs=1e-9)
    assert out["totals"]["prompt_tokens"] == 1000


def test_priced_fallback_when_cost_missing():
    """No stored cost_usd -> dollars come from the shared pricing table."""
    from clawmetry.providers_pricing import estimate_event_cost_usd
    evs = [_family_call("claude_code:s7", "2026-08-01T00:00:01",
                        inp=10_000, out=2_000, cr=5_000, cw=1_000, cost=0.0)]
    out = build_spend_flow_slice(evs, days=7)
    expect = (
        estimate_event_cost_usd(MODEL, input_tokens=10_000,
                                cache_read_tokens=5_000, cache_write_tokens=1_000)
        + estimate_event_cost_usd(MODEL, output_tokens=2_000)
    )
    assert out["totals"]["cost_usd"] == pytest.approx(expect, abs=1e-6)


def test_category_ids_are_stable_contract():
    assert INPUT_CATEGORIES == ("user_prompts", "prior_assistant",
                                "tool_results", "overhead")
    assert OUTPUT_CATEGORIES == ("thinking", "assistant_text",
                                 "builtin_tool_calls", "mcp_tool_calls")


# ── spend-derived savings actions (feat/spend-actions) ──────────────────────

def _slice_with_thinking(think_cost, out_cost, days=7, insufficient=False):
    return {
        "schema": 1,
        "window_days": days,
        "insufficient_data": insufficient,
        "totals": {"calls": 50, "cost_usd": out_cost * 3,
                   "input_cost_usd": out_cost * 2, "output_cost_usd": out_cost,
                   "prompt_tokens": 1, "output_tokens": 1},
        "input_categories": [],
        "output_categories": [
            {"id": "thinking", "tokens": 1000, "cost_usd": think_cost,
             "pct_of_side_cost": 0, "basis": "residual"},
            {"id": "assistant_text", "tokens": 1000,
             "cost_usd": out_cost - think_cost, "pct_of_side_cost": 0,
             "basis": "measured"},
        ],
    }


def test_thinking_trim_emitted_when_dominant():
    from clawmetry.spend_flow import spend_actions
    acts = spend_actions(_slice_with_thinking(think_cost=6.0, out_cost=10.0))
    assert len(acts) == 1
    a = acts[0]
    assert a["id"] == "thinking_trim"
    assert a["estimate"] is True
    # 6.0 window cost * 0.5 trim * (30/7) monthly scaling
    assert a["savings_monthly_usd"] == pytest.approx(6.0 * 0.5 * 30 / 7, abs=1e-4)
    assert a["data"]["thinking_pct_of_output_cost"] == 60.0
    assert a["data"]["basis"] == "residual"


def test_thinking_trim_silent_below_gates():
    from clawmetry.spend_flow import spend_actions
    # below the 40% share gate
    assert spend_actions(_slice_with_thinking(3.0, 10.0)) == []
    # below the $1 window floor
    assert spend_actions(_slice_with_thinking(0.5, 1.0)) == []
    # insufficient window never emits
    assert spend_actions(_slice_with_thinking(6.0, 10.0, insufficient=True)) == []
    # garbage never raises
    assert spend_actions(None) == []
    assert spend_actions({"totals": "x"}) == []


def test_merge_spend_actions_node_and_per_runtime():
    from clawmetry.spend_flow import merge_spend_actions
    eff = {
        "actions": [{"id": "context_trim", "savings_monthly_usd": 1.0}],
        "byRuntime": {
            "claude_code": {"actions": []},
            "openclaw": {"actions": []},
        },
    }
    sf = _slice_with_thinking(6.0, 10.0)
    sf["byRuntime"] = {
        "claude_code": _slice_with_thinking(6.0, 10.0),
        "openclaw": _slice_with_thinking(0.0, 1.0),  # below gates
    }
    out = merge_spend_actions(eff, sf)
    ids = [a["id"] for a in out["actions"]]
    assert "thinking_trim" in ids and "context_trim" in ids
    # sorted by savings desc: thinking_trim (12.86) before context_trim (1.0)
    assert ids[0] == "thinking_trim"
    assert [a["id"] for a in out["byRuntime"]["claude_code"]["actions"]] == ["thinking_trim"]
    # per-runtime honesty: a runtime below the gates gets NO action
    assert out["byRuntime"]["openclaw"]["actions"] == []
    # idempotent-ish: merging again never duplicates the action id
    out2 = merge_spend_actions(out, sf)
    assert [a["id"] for a in out2["actions"]].count("thinking_trim") == 1


def test_merge_spend_actions_bad_input_returns_eff():
    from clawmetry.spend_flow import merge_spend_actions
    eff = {"actions": []}
    assert merge_spend_actions(eff, None) is eff
    assert merge_spend_actions(None, {}) is None


# ── endpoint ────────────────────────────────────────────────────────────────

def _make_app(monkeypatch, payload):
    from flask import Flask
    import routes.spend_flow as sf_route
    monkeypatch.setattr(sf_route, "_ls_call", lambda method, **kw: payload)
    app = Flask(__name__)
    app.register_blueprint(sf_route.bp_spend_flow)
    return app


def test_endpoint_returns_slice(monkeypatch):
    payload = build_spend_flow_slice(_mixed_window(), days=7)
    app = _make_app(monkeypatch, payload)
    resp = app.test_client().get("/api/spend-flow?days=7")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["schema"] == 1
    assert body["totals"]["calls"] == 6
    assert body["_source"] in ("local_store", "empty")


def test_endpoint_empty_store_never_500s(monkeypatch):
    app = _make_app(monkeypatch, None)
    resp = app.test_client().get("/api/spend-flow")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["insufficient_data"] is True
    assert body["_source"] == "empty"


def test_endpoint_clamps_days(monkeypatch):
    seen = {}

    def fake(method, **kw):
        seen.update(kw)
        return build_spend_flow_slice([], days=kw.get("days", 7))

    from flask import Flask
    import routes.spend_flow as sf_route
    monkeypatch.setattr(sf_route, "_ls_call", fake)
    app = Flask(__name__)
    app.register_blueprint(sf_route.bp_spend_flow)
    app.test_client().get("/api/spend-flow?days=9999")
    assert seen["days"] <= 90
    app.test_client().get("/api/spend-flow?days=-3")
    assert seen["days"] >= 1
