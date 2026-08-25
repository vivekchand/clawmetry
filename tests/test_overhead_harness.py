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


# ── the hook gate: the path that can actually hold a tool call ───────────

def test_hook_gate_isolates_the_home_it_measures(tmp_path):
    """The gate resolves its config as ``expanduser("~/.clawmetry/config.json")``
    and ignores CLAWMETRY_HOME, so only a home override isolates a run. Getting
    this wrong reads the operator's real key and benchmarks a different branch
    than the one you meant, which is exactly what happened the first time."""
    from benchmarks.overhead import _hook_home
    import json as _json
    import os as _os

    home = _hook_home(str(tmp_path), api_key="cm_test", policies=[{"name": "p"}])
    cfg = _os.path.join(home, ".clawmetry", "config.json")
    cache = _os.path.join(home, ".clawmetry", "hooks_policy_cache.json")
    assert _os.path.isfile(cfg) and _os.path.isfile(cache)
    assert _json.load(open(cfg))["api_key"] == "cm_test"
    # A no-key condition must leave no config behind at all, or it silently
    # measures the keyed branch.
    bare = _hook_home(str(tmp_path), api_key=None, policies=None)
    assert not _os.path.exists(_os.path.join(bare, ".clawmetry", "config.json"))


def test_hook_gate_reports_every_condition_against_a_floor():
    """Most of a process-per-call hook is Python starting up, which belongs to
    the mechanism and not to us. Without the floor the headline number is
    dominated by a cost no change to ClawMetry could ever reduce."""
    from benchmarks.overhead import bench_hook_gate
    out = bench_hook_gate(n=4, warmup=1)
    assert out["floor_bare_interpreter"]["p50_us"] > 0
    for name in ("no_key", "warm_cache", "policy_miss", "cold_cache"):
        cond = out["conditions"][name]
        assert cond["n"] == 4
        assert "added_over_floor_p50_us" in cond
    # Only the refetch condition may be labelled network-dependent; mislabelling
    # would let a network figure be quoted as a per-call cost.
    assert out["conditions"]["cold_cache"]["network_dependent"] is True
    assert out["conditions"]["warm_cache"]["network_dependent"] is False


# ── a clock that cannot see the signal must say so ──────────────────────

def _cpu_resolvable(samples: list[float]) -> bool:
    """The harness's rule, restated independently of how it is factored:
    if most individual samples read exactly zero, the clock did not resolve a
    single call and no amount of averaging makes it so."""
    if not samples:
        return False
    return (sum(1 for v in samples if v <= 0.0) / len(samples)) < 0.5


def test_a_clock_too_coarse_to_see_one_call_is_not_resolvable():
    """Windows' process_time() advances only every ~15.6 ms against a
    sub-millisecond per-call cost, so nearly every sample reads exactly zero
    and the naive answer is a confident '+0.00 ms CPU'."""
    windows_like = [0.0] * 95 + [0.0156] * 5
    assert _cpu_resolvable(windows_like) is False


def test_a_fine_clock_is_resolvable():
    assert _cpu_resolvable([0.00035 + i * 1e-6 for i in range(100)]) is True


def test_advertised_resolution_is_not_the_test():
    """The first version of this guard trusted
    ``time.get_clock_info('process_time').resolution``, which reports 1e-07 on
    Windows because the counter is denominated in 100ns units even though its
    value only changes on a scheduler tick. That guard passed and published
    the zero anyway. The rule must be empirical."""
    import time
    advertised = time.get_clock_info("process_time").resolution
    windows_like = [0.0] * 99 + [0.0156]
    # A fine advertised resolution must not rescue a clock that plainly did
    # not move during the measurement.
    assert advertised < 1e-3
    assert _cpu_resolvable(windows_like) is False


def test_interceptor_reports_the_resolvability_verdict():
    from benchmarks.overhead import bench_interceptor
    out = bench_interceptor(n=80, warmup=20, rounds=2)
    if out.get("skipped"):
        pytest.skip(out["skipped"])
    cpu = out["cpu"]
    assert "resolvable" in cpu and "zero_sample_fraction" in cpu
    # When it is not resolvable the figure must be withheld, not zeroed.
    if not cpu["resolvable"]:
        assert cpu["added_p50_us"] is None
