"""Period-over-period outcome trend (``clawmetry.outcome_classifier``).

The Evaluate pillar's procurement question is "can I tell whether my agent is
improving over time?" A single-window success rate cannot answer it, so
``outcome_trend`` compares two equal windows of the same ``query_outcomes``
rows. These tests pin the parts that would silently lie if they drifted:

- ``cost_per_finished`` is ``None`` when nothing finished, never ``0.0`` —
  a real $0 has to stay distinguishable from missing data (memory
  ``reference_cost_windows_one_definition``: ``or`` treating 0.0 as absent
  turned a genuine $0 into "stale").
- a direction is only claimed once BOTH periods clear ``TREND_MIN_FINISHED``,
  so three sessions on a fresh install can't manufacture "improving".
- cost never flips the verdict. An agent that got cheaper by giving up
  earlier is regressing, not improving.
"""
from __future__ import annotations

from clawmetry.outcome_classifier import (
    TREND_MIN_FINISHED,
    TREND_RATE_EPSILON,
    aggregate_cost,
    outcome_trend,
    summarize_period,
)


def _rows(spec, cost=None):
    """``{"success": 8, "failed": 2}`` → 10 rows, optionally priced."""
    out = []
    for outcome, n in spec.items():
        for i in range(n):
            row = {"session_id": f"{outcome}-{i}", "outcome": outcome}
            if cost is not None:
                row["cost_usd"] = cost
                row["total_tokens"] = 1000
            out.append(row)
    return out


# ── cost roll-up ────────────────────────────────────────────────────────────


def test_cost_per_finished_is_none_when_nothing_finished():
    """Ongoing-only window: no denominator, so no per-task cost — and the
    answer is None, not a 0.0 that would render as "free"."""
    agg = aggregate_cost(_rows({"ongoing": 4}, cost=1.0))
    assert agg["cost_usd"] == 4.0
    assert agg["cost_per_finished"] is None


def test_cost_per_finished_keeps_a_real_zero():
    """A genuinely free window reports 0.0, distinct from the None above."""
    agg = aggregate_cost(_rows({"success": 4}, cost=0.0))
    assert agg["cost_per_finished"] == 0.0
    assert agg["priced_sessions"] == 4


def test_escalated_and_ongoing_stay_out_of_the_denominator():
    """Same denominator ``aggregate_outcomes`` uses for ``success_rate``:
    a human takeover is not the agent failing, and in-flight isn't done."""
    rows = _rows({"success": 2, "failed": 2, "escalated": 6, "ongoing": 10},
                 cost=1.0)
    agg = aggregate_cost(rows)
    assert agg["cost_usd"] == 20.0
    assert agg["cost_per_finished"] == 5.0  # 20.0 / 4 finished


def test_unpriced_rows_do_not_count_as_zero_dollars():
    """``cost_usd`` missing means unknown. Averaging it in as $0 would
    understate spend on runtimes whose adapter has no pricing yet."""
    rows = _rows({"success": 2}, cost=3.0) + _rows({"failed": 2})
    agg = aggregate_cost(rows)
    assert agg["cost_usd"] == 6.0
    assert agg["priced_sessions"] == 2


def test_summarize_period_carries_both_halves():
    period = summarize_period(_rows({"success": 3, "failed": 1}, cost=2.0))
    assert period["success"] == 3
    assert period["finished"] == 4
    assert period["success_rate"] == 0.75
    assert period["cost_usd"] == 8.0


# ── direction ───────────────────────────────────────────────────────────────


def test_improving_when_success_rate_climbs():
    t = outcome_trend(
        _rows({"success": 9, "failed": 1}),   # 90%
        _rows({"success": 7, "failed": 3}),   # 70%
    )
    assert t["direction"] == "improving"
    assert t["comparable"] is True
    assert t["delta"]["success_rate"] == 0.2


def test_regressing_when_success_rate_falls():
    t = outcome_trend(
        _rows({"success": 5, "failed": 5}),
        _rows({"success": 9, "failed": 1}),
    )
    assert t["direction"] == "regressing"
    assert t["delta"]["success_rate"] == -0.4


def test_a_move_inside_the_epsilon_reads_as_flat():
    """Noise is not a trend. 100/100 vs 99/100 is one session, not a signal."""
    t = outcome_trend(
        _rows({"success": 100}),
        _rows({"success": 99, "failed": 1}),
    )
    assert abs(t["delta"]["success_rate"]) <= TREND_RATE_EPSILON
    assert t["direction"] == "flat"


def test_too_few_finished_sessions_is_unknown_not_improving():
    """Below ``TREND_MIN_FINISHED`` we report the numbers and refuse the
    verdict, rather than dressing up a two-session swing as progress."""
    few = TREND_MIN_FINISHED - 1
    t = outcome_trend(_rows({"success": few}), _rows({"failed": few}))
    assert t["comparable"] is False
    assert t["direction"] == "unknown"
    # The counts are still reported — "unknown" means unproven, not hidden.
    assert t["current"]["success"] == few
    assert t["min_finished"] == TREND_MIN_FINISHED


def test_ongoing_sessions_do_not_make_a_period_comparable():
    """A window of in-flight sessions has nothing finished to compare."""
    t = outcome_trend(_rows({"ongoing": 50}), _rows({"success": 50}))
    assert t["direction"] == "unknown"
    assert t["current"]["finished"] == 0


def test_cheaper_but_worse_is_still_regressing():
    """Cost is reported beside the verdict, never allowed to set it."""
    t = outcome_trend(
        _rows({"success": 4, "failed": 6}, cost=0.10),   # 40%, cheap
        _rows({"success": 9, "failed": 1}, cost=1.00),   # 90%, pricey
    )
    assert t["direction"] == "regressing"
    assert t["delta"]["cost_per_finished"] == -0.9


def test_missing_cost_on_one_side_yields_a_null_delta():
    """No fabricated delta when one period has no priced sessions.

    Caught a real bug: the unpriced period summed to 0.0 and divided into a
    confident "$0.10 cheaper per task". Unknown cost has to stay unknown.
    """
    t = outcome_trend(
        _rows({"success": 5, "failed": 5}, cost=1.0),
        _rows({"success": 5, "failed": 5}),
    )
    assert t["delta"]["cost_per_finished"] is None


def test_empty_input_never_raises():
    t = outcome_trend([], [])
    assert t["direction"] == "unknown"
    assert t["current"]["total"] == 0
    assert t["delta"]["finished"] == 0
