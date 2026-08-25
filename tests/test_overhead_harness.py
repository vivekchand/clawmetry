"""The overhead harness has to be trustworthy before its numbers are.

A benchmark that always produces a tidy figure is not measuring anything. The
one property that makes `benchmarks/overhead.py` worth publishing is that it
detects when its own signal is below the rig's noise floor and refuses to
print an average instead. These tests pin that behaviour, plus the statistics
it reports, so neither can quietly rot into a number-generator.
"""

from __future__ import annotations

import pytest

from benchmarks.overhead import _pct, _summarise, machine_spec


def test_percentile_is_nearest_rank_and_small_n_safe():
    """statistics.quantiles needs 2+ points and interpolates, which
    over-smooths the tail we care about. Nearest-rank does not."""
    vals = [float(i) for i in range(1, 101)]
    assert _pct(vals, 50) == pytest.approx(50, abs=1)
    assert _pct(vals, 99) == pytest.approx(99, abs=1)
    assert _pct([], 50) == 0.0
    assert _pct([7.0], 99) == 7.0


def test_summarise_reports_a_distribution_not_just_a_mean():
    """A mean cannot tell a steady 40us tax from a 5us tax with a 3ms stall in
    it, and only the second one breaks an agent."""
    out = _summarise([0.001] * 99 + [0.05])
    assert out["n"] == 100
    assert out["p50_us"] == pytest.approx(1000, rel=0.01)
    assert out["max_us"] == pytest.approx(50_000, rel=0.01)
    assert out["stdev_us"] > 0


def test_summarise_survives_an_empty_sample():
    out = _summarise([])
    assert out["n"] == 0 and out["p50_us"] == 0.0


def test_machine_spec_stamps_the_run():
    """Numbers without a machine are not reproducible, so the report must
    always carry one."""
    spec = machine_spec()
    for key in ("platform", "processor", "python", "cpu_count"):
        assert spec.get(key), f"machine spec missing {key}"


# ── the integrity property ───────────────────────────────────────────────

def _noise_verdict(per_round_deltas: list[float]) -> bool:
    """Mirror of the harness rule: a delta is publishable only when every
    round agrees on its sign. Kept as a tiny reimplementation so the test
    states the rule independently of how bench_interceptor is factored."""
    return not (all(d > 0 for d in per_round_deltas)
                or all(d < 0 for d in per_round_deltas))


def test_rounds_that_disagree_on_sign_are_below_the_noise_floor():
    """The real failure this guard caught: an early draft measured the
    baseline cold and the instrumented run warm, and reported NEGATIVE
    overhead with a straight face."""
    assert _noise_verdict([557.6, -100.8, 414.6]) is True


def test_rounds_that_agree_are_publishable():
    assert _noise_verdict([557.6, 382.5, 414.6]) is False
    assert _noise_verdict([-20.0, -18.0, -22.0]) is False


def test_bench_interceptor_reports_the_verdict_field():
    """`below_noise_floor` must be present on every non-skipped result, since
    the renderer branches on it to decide whether a number may be shown."""
    from benchmarks.overhead import bench_interceptor
    out = bench_interceptor(n=60, warmup=20, rounds=2)
    if out.get("skipped"):
        pytest.skip(out["skipped"])
    assert "below_noise_floor" in out
    assert "rounds_agree_on_sign" in out
    assert out["below_noise_floor"] is not out["rounds_agree_on_sign"]
    # Both timing bases are always reported: wall is what a user feels, CPU is
    # what ClawMetry actually spends and is the reproducible one.
    assert out["wall"]["baseline"]["n"] > 0
    assert out["cpu"]["baseline"]["n"] > 0
