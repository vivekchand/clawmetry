"""Tests for clawmetry/efficiency.py (efficiency grade + measured savings)
and the GET /api/efficiency endpoint (routes/usage.py).

Pure-math unit tests with synthetic rows (acceptable for unit tests per
FLYWHEEL — these don't claim a user-facing feature works E2E). All expected
dollar values are recomputed IN the tests from clawmetry.providers_pricing
(``_get_rates`` / the cache multipliers / ``default_auto_downgrade_map``) so
the tests can't drift from the pricing table.
"""
from __future__ import annotations

import pytest
from flask import Flask

from clawmetry.efficiency import _grade_for_score, build_efficiency_slice
from clawmetry.providers_pricing import (
    _CACHE_READ_MULT,
    _CACHE_WRITE_MULT,
    _get_rates,
    default_auto_downgrade_map,
    downgrade_model_name,
    provider_for_model,
)


def _rates(model: str) -> tuple[float, float]:
    return _get_rates(provider_for_model(model), model)


def _row(**kw) -> dict:
    base = {
        "runtime": "openclaw",
        "model": "claude-sonnet-4",
        "tokens_in": 0,
        "tokens_out": 0,
        "cache_read": 0,
        "cache_write": 0,
        "cost_usd": 0.0,
        "calls": 0,
        "days_with_data": 30,
    }
    base.update(kw)
    return base


# ── grade boundaries ────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (100, "A"), (90, "A"),
    (89, "B"), (75, "B"),
    (74, "C"), (60, "C"),
    (59, "D"), (45, "D"),
    (44, "F"), (0, "F"),
])
def test_grade_boundaries(score, expected):
    assert _grade_for_score(score) == expected


def test_grade_none_passthrough():
    assert _grade_for_score(None) is None


def test_perfect_scope_grades_a():
    # hit rate 70% (40 pts) + roi 3.5 (30 pts) + avg ctx 12k (30 pts) = 100.
    rows = [_row(tokens_in=30_000, cache_read=70_000, cache_write=20_000,
                 tokens_out=1_000, cost_usd=1.0, calls=10)]
    out = build_efficiency_slice(rows)
    assert out["score"] == 100
    assert out["grade"] == "A"
    assert out["insufficient_data"] is False
    assert out["metrics"]["cache_hit_rate_pct"] == 70.0
    assert out["metrics"]["cache_roi"] == 3.5
    assert out["metrics"]["avg_context_tokens"] == 12_000.0


def test_no_cache_write_is_neutral_not_punished():
    # hit 0 (0) + no cache writes (18 neutral) + avg ctx 20k (30) = 48 -> D.
    rows = [_row(tokens_in=400_000, tokens_out=5_000, cost_usd=2.0, calls=20)]
    out = build_efficiency_slice(rows)
    assert out["score"] == 48
    assert out["grade"] == "D"


# ── insufficient data: never a fake grade ───────────────────────────────────

def test_insufficient_data_under_10_calls():
    rows = [_row(tokens_in=100_000, tokens_out=500, cost_usd=1.0, calls=9)]
    out = build_efficiency_slice(rows)
    assert out["insufficient_data"] is True
    assert out["score"] is None
    assert out["grade"] is None


def test_empty_rows_yield_honest_empty_shape():
    out = build_efficiency_slice([])
    assert out["schema"] == 1
    assert out["insufficient_data"] is True
    assert out["score"] is None
    assert out["grade"] is None
    assert out["actions"] == []
    assert out["byRuntime"] == {}
    assert out["projected_monthly_cost_usd"] == 0.0
    assert out["cache_saved_monthly_usd"] == 0.0


# ── model_downgrade action ──────────────────────────────────────────────────

def test_model_downgrade_savings_exact():
    model = "claude-opus-4-5"
    target = downgrade_model_name(model, default_auto_downgrade_map())
    assert target, "downgrade map must yield a target for the test model"
    src_in, src_out = _rates(model)
    tgt_in, tgt_out = _rates(target)
    assert (tgt_in, tgt_out) != (src_in, src_out)

    tokens_in, tokens_out, calls = 400_000, 5_000, 20  # avg out 250 < 300
    actual_cost = (tokens_in * src_in + tokens_out * src_out) / 1e6
    assert actual_cost >= 1.0  # meets the min window-cost gate
    target_cost = (tokens_in * tgt_in + tokens_out * tgt_out) / 1e6
    expected = actual_cost - target_cost  # days_with_data=30 -> factor 1

    rows = [_row(model=model, tokens_in=tokens_in, tokens_out=tokens_out,
                 cost_usd=actual_cost, calls=calls)]
    out = build_efficiency_slice(rows)
    acts = [a for a in out["actions"] if a["id"] == "model_downgrade"]
    assert len(acts) == 1
    act = acts[0]
    assert act["model"] == model
    assert act["estimate"] is False
    assert act["data"]["target_model"] == target
    assert act["savings_monthly_usd"] == pytest.approx(expected, rel=1e-6)
    # No other action fires for this row (ctx 20k, no cache writes).
    assert len(out["actions"]) == 1


def test_model_downgrade_gates():
    model = "claude-opus-4-5"
    # calls < 20 -> no action.
    out = build_efficiency_slice(
        [_row(model=model, tokens_in=400_000, tokens_out=2_000,
              cost_usd=2.5, calls=19)])
    assert not [a for a in out["actions"] if a["id"] == "model_downgrade"]
    # avg tokens_out/call >= 300 -> no action.
    out = build_efficiency_slice(
        [_row(model=model, tokens_in=400_000, tokens_out=6_000,
              cost_usd=2.5, calls=20)])
    assert not [a for a in out["actions"] if a["id"] == "model_downgrade"]
    # window cost < $1 -> no action.
    out = build_efficiency_slice(
        [_row(model=model, tokens_in=400_000, tokens_out=2_000,
              cost_usd=0.5, calls=20)])
    assert not [a for a in out["actions"] if a["id"] == "model_downgrade"]


# ── context_trim action ─────────────────────────────────────────────────────

def test_context_trim_math():
    model = "claude-sonnet-4"
    in_rate, _ = _rates(model)
    tokens_in, calls, dwd = 500_000, 10, 15  # avg ctx 50k > 40k; factor 2
    rows = [_row(model=model, tokens_in=tokens_in, tokens_out=1_000,
                 cost_usd=5.0, calls=calls, days_with_data=dwd)]
    out = build_efficiency_slice(rows)
    acts = [a for a in out["actions"] if a["id"] == "context_trim"]
    assert len(acts) == 1
    input_side = tokens_in * in_rate / 1e6
    expected = input_side * 0.4 * (30 / dwd)
    assert acts[0]["savings_monthly_usd"] == pytest.approx(expected, rel=1e-6)
    assert acts[0]["estimate"] is True
    assert out["projected_monthly_cost_usd"] == pytest.approx(5.0 * 30 / dwd)


def test_context_trim_not_emitted_below_threshold():
    rows = [_row(tokens_in=300_000, tokens_out=1_000, cost_usd=5.0, calls=10)]
    out = build_efficiency_slice(rows)  # avg ctx 30k <= 40k
    assert not [a for a in out["actions"] if a["id"] == "context_trim"]


# ── cache_warm action (re-read tax) ─────────────────────────────────────────

def test_cache_warm_math():
    model = "claude-sonnet-4"
    in_rate, _ = _rates(model)
    cache_write, cache_read = 200_000, 100_000  # roi 0.5 < 1
    rows = [_row(model=model, cache_read=cache_read, cache_write=cache_write,
                 tokens_out=500, cost_usd=10.0, calls=10)]
    out = build_efficiency_slice(rows)
    acts = [a for a in out["actions"] if a["id"] == "cache_warm"]
    assert len(acts) == 1
    roi = cache_read / cache_write
    expected = (cache_write * in_rate * _CACHE_WRITE_MULT / 1e6) * (1 - roi)
    assert acts[0]["savings_monthly_usd"] == pytest.approx(expected, rel=1e-6)
    assert acts[0]["estimate"] is True
    assert acts[0]["data"]["models"][0]["model"] == model


def test_cache_warm_not_emitted_with_healthy_roi():
    rows = [_row(cache_read=300_000, cache_write=100_000,
                 cost_usd=10.0, calls=10)]
    out = build_efficiency_slice(rows)  # roi 3 >= 1
    assert not [a for a in out["actions"] if a["id"] == "cache_warm"]


# ── cache_saved_monthly_usd + monthly scaling ───────────────────────────────

def test_cache_saved_monthly_and_scaling():
    model = "claude-sonnet-4"
    in_rate, _ = _rates(model)
    dwd = 10  # factor 3
    rows = [_row(model=model, tokens_in=50_000, cache_read=1_000_000,
                 cache_write=200_000, tokens_out=500, cost_usd=4.0,
                 calls=10, days_with_data=dwd)]
    out = build_efficiency_slice(rows)
    expected = (1_000_000 * in_rate * (1 - _CACHE_READ_MULT) / 1e6) * (30 / dwd)
    assert out["cache_saved_monthly_usd"] == pytest.approx(expected, rel=1e-6)
    assert out["projected_monthly_cost_usd"] == pytest.approx(4.0 * 3)


# ── the 0.9 savings cap (proportional scaling) ──────────────────────────────

def test_savings_capped_at_90pct_of_projected_proportionally():
    model = "claude-sonnet-4"
    in_rate, _ = _rates(model)
    # Big token volumes but a tiny stored window cost -> raw estimated
    # savings vastly exceed 0.9 * projected monthly cost.
    rows = [_row(model=model, tokens_in=10_000_000, tokens_out=1_000,
                 cache_read=100_000, cache_write=2_000_000,
                 cost_usd=1.0, calls=100)]
    out = build_efficiency_slice(rows)
    cap = 0.9 * out["projected_monthly_cost_usd"]
    total = sum(a["savings_monthly_usd"] for a in out["actions"])
    assert total == pytest.approx(cap, rel=1e-6)
    # Proportional: ratios match the uncapped window math.
    trim = next(a for a in out["actions"] if a["id"] == "context_trim")
    warm = next(a for a in out["actions"] if a["id"] == "cache_warm")
    raw_trim = (10_000_000 * in_rate
                + 100_000 * in_rate * _CACHE_READ_MULT
                + 2_000_000 * in_rate * _CACHE_WRITE_MULT) / 1e6 * 0.4
    roi = 100_000 / 2_000_000
    raw_warm = (2_000_000 * in_rate * _CACHE_WRITE_MULT / 1e6) * (1 - roi)
    # rel=1e-4: savings are rounded to 6dp after scaling, which perturbs the
    # ratio of two sub-dollar values by a few 1e-6.
    assert (trim["savings_monthly_usd"] / warm["savings_monthly_usd"]
            == pytest.approx(raw_trim / raw_warm, rel=1e-4))
    # Ranked largest-first.
    savings = [a["savings_monthly_usd"] for a in out["actions"]]
    assert savings == sorted(savings, reverse=True)


# ── byRuntime scoping ───────────────────────────────────────────────────────

def test_by_runtime_scopes_each_runtime_to_its_own_rows():
    rows = [
        # claude_code: perfect (A).
        _row(runtime="claude_code", tokens_in=30_000, cache_read=70_000,
             cache_write=20_000, tokens_out=1_000, cost_usd=2.0, calls=10),
        # openclaw: thin window (insufficient).
        _row(runtime="openclaw", tokens_in=100_000, tokens_out=500,
             cost_usd=1.0, calls=5),
    ]
    out = build_efficiency_slice(rows)
    assert set(out["byRuntime"].keys()) == {"claude_code", "openclaw"}
    cc = out["byRuntime"]["claude_code"]
    oc = out["byRuntime"]["openclaw"]
    assert cc["grade"] == "A"
    assert cc["metrics"]["calls"] == 10
    assert cc["metrics"]["window_cost_usd"] == pytest.approx(2.0)
    assert oc["insufficient_data"] is True
    assert oc["grade"] is None
    assert oc["metrics"]["calls"] == 5
    # Per-runtime entries don't nest byRuntime; node-wide sums both.
    assert "byRuntime" not in cc
    assert out["metrics"]["calls"] == 15
    assert out["metrics"]["window_cost_usd"] == pytest.approx(3.0)


# ── never raise on garbage ──────────────────────────────────────────────────

def test_never_raises_on_garbage_rows():
    rows = [
        None,
        42,
        "not-a-row",
        {"runtime": None, "model": None, "tokens_in": "abc",
         "tokens_out": -50, "cache_read": float("nan"),
         "cache_write": float("inf"), "cost_usd": "zzz",
         "calls": "7", "days_with_data": "bad"},
    ]
    out = build_efficiency_slice(rows, days="banana")
    assert out["schema"] == 1
    assert out["window_days"] == 30  # bad days falls back
    # Strings/negatives/NaN coerced to 0; "7" parses -> 7 calls < 10.
    assert out["insufficient_data"] is True
    assert out["metrics"]["calls"] == 7
    assert out["metrics"]["tokens_in"] == 0
    assert out["metrics"]["cache_read"] == 0


def test_garbage_only_rows_equal_empty():
    out = build_efficiency_slice([None, "x", 3.14])
    assert out["insufficient_data"] is True
    assert out["byRuntime"] == {}


# ── GET /api/efficiency endpoint ────────────────────────────────────────────

@pytest.fixture
def efficiency_app(monkeypatch):
    """Bare Flask app + bp_usage with the store call monkeypatched (pattern
    from tests/test_usage_local_store.py, minus the DuckDB seeding — the
    endpoint's store read is a single _ls_call, stubbed here)."""
    import routes.usage as usage_mod

    rows = [
        _row(runtime="claude_code", tokens_in=30_000, cache_read=70_000,
             cache_write=20_000, tokens_out=1_000, cost_usd=2.0, calls=10),
        _row(runtime="openclaw", tokens_in=100_000, tokens_out=500,
             cost_usd=1.0, calls=5),
    ]
    calls = []

    def fake_ls_call(method_name, **kwargs):
        calls.append((method_name, kwargs))
        if method_name == "query_efficiency_rollup":
            return rows
        return None

    monkeypatch.setattr(usage_mod, "_ls_call", fake_ls_call)
    app = Flask(__name__)
    app.register_blueprint(usage_mod.bp_usage)
    return app, calls


def test_endpoint_node_wide(efficiency_app):
    app, calls = efficiency_app
    resp = app.test_client().get("/api/efficiency")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["schema"] == 1
    assert body["window_days"] == 30
    assert set(body["byRuntime"].keys()) == {"claude_code", "openclaw"}
    assert calls and calls[0][0] == "query_efficiency_rollup"
    assert calls[0][1] == {"days": 30}


def test_endpoint_runtime_scoped(efficiency_app):
    app, _ = efficiency_app
    resp = app.test_client().get("/api/efficiency?runtime=claude_code")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["runtime"] == "claude_code"
    assert body["grade"] == "A"
    assert body["metrics"]["calls"] == 10  # ONLY claude_code's rows
    assert "byRuntime" not in body


def test_endpoint_unknown_runtime_is_honest_empty(efficiency_app):
    app, _ = efficiency_app
    resp = app.test_client().get("/api/efficiency?runtime=goose")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["runtime"] == "goose"
    assert body["insufficient_data"] is True
    assert body["grade"] is None
    # Never the node-wide numbers relabelled.
    assert body["metrics"]["calls"] == 0
    assert body["projected_monthly_cost_usd"] == 0.0


def test_endpoint_days_clamped(efficiency_app):
    app, calls = efficiency_app
    client = app.test_client()
    assert client.get("/api/efficiency?days=500").get_json()["window_days"] == 90
    assert client.get("/api/efficiency?days=1").get_json()["window_days"] == 7
    assert client.get("/api/efficiency?days=abc").get_json()["window_days"] == 30
    assert {c[1]["days"] for c in calls} == {90, 7, 30}


def test_endpoint_never_500s_on_store_failure(monkeypatch):
    import routes.usage as usage_mod

    def boom(method_name, **kwargs):
        raise RuntimeError("store exploded")

    monkeypatch.setattr(usage_mod, "_ls_call", boom)
    app = Flask(__name__)
    app.register_blueprint(usage_mod.bp_usage)
    resp = app.test_client().get("/api/efficiency")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["insufficient_data"] is True
    assert body["grade"] is None
