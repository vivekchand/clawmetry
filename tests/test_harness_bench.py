"""Unit tests for the Harness Engineering bench engine (pure math).

Covers the honesty contracts of the Blueprint "Harness Benchmarks &
Comparison": $/done derivation, the minimum-sample floor, blindness never
ranking, stamp rules, mark coverage states, workload recommendations always
listing options, published pairs carrying dated provenance, and flow traces
drawing only observed stations.
"""

import time

from clawmetry.flow_trace import build_flow_trace
from clawmetry.harness_bench import (
    BENCH_MIN_SESSIONS,
    STAMP_BURNING,
    STAMP_CANT_SEE,
    STAMP_COASTING,
    STAMP_EARNING,
    build_bench,
    build_context_curves,
    build_runtime_scope,
)
from clawmetry.published_benchmarks import published_pairs
from clawmetry.workload_profiles import (
    build_recommendations,
    classify_session,
    profile_spend,
)


def _session(cost, outcome="success", measurable=True, rough=False, **extra):
    verdicts = [{"severity": "rough", "verdict": "tool_thrash",
                 "evidence": {"exhibits": ["x"]}}] if rough else []
    row = {
        "session_id": extra.pop("session_id", "claude_code:s1"),
        "cost_usd": cost,
        "total_tokens": extra.pop("tokens", 1000),
        "outcome": outcome,
        "metadata": {"quality": {"measurable": measurable, "verdicts": verdicts}},
    }
    row.update(extra)
    return row


def _cohort(n_success, n_failed, cost=1.0, unmeasured=0):
    rows = [_session(cost) for _ in range(n_success)]
    rows += [_session(cost * 4, outcome="failed") for _ in range(n_failed)]
    rows += [_session(cost, measurable=False) for _ in range(unmeasured)]
    return rows


class TestDollarsPerDone:
    def test_failed_spend_lands_in_the_numerator(self):
        # 10 successes at $1 + 4 failures at $4: $/done = 26/10, not 10/10.
        scope = build_runtime_scope(_cohort(10, 4), runtime="claude_code")
        assert scope["dollars_per_done"]["value"] == 2.6

    def test_unmeasurable_sessions_are_excluded_from_both_sides(self):
        with_blind = build_runtime_scope(_cohort(10, 4, unmeasured=20),
                                         runtime="claude_code")
        without = build_runtime_scope(_cohort(10, 4), runtime="claude_code")
        assert (with_blind["dollars_per_done"]["value"]
                == without["dollars_per_done"]["value"])
        assert with_blind["coverage"]["unmeasured_sessions"] == 20

    def test_below_minimum_sample_prints_no_number(self):
        scope = build_runtime_scope(_cohort(BENCH_MIN_SESSIONS - 2, 0),
                                    runtime="codex")
        assert scope["dollars_per_done"]["value"] is None
        assert scope["dollars_per_done"]["n_measurable"] == BENCH_MIN_SESSIONS - 2

    def test_band_is_deterministic(self):
        a = build_runtime_scope(_cohort(15, 5), runtime="codex")
        b = build_runtime_scope(_cohort(15, 5), runtime="codex")
        assert a["dollars_per_done"]["band"] == b["dollars_per_done"]["band"]
        assert a["dollars_per_done"]["band"] is not None


class TestStampsAndRanking:
    def test_blind_harness_is_cant_see_and_never_ranked(self):
        bench = build_bench({
            "cursor": [_session(2.0, measurable=False,
                                session_id="cursor:s%d" % i) for i in range(30)],
            "openclaw": _cohort(20, 2),
        })
        assert bench["byRuntime"]["cursor"]["stamp"] == STAMP_CANT_SEE
        assert "cursor" in bench["unranked"]
        assert "cursor" not in bench["ranked"]

    def test_high_failed_spend_share_stamps_burning(self):
        bench = build_bench({"codex": _cohort(12, 10)})
        assert bench["byRuntime"]["codex"]["stamp"] == STAMP_BURNING

    def test_small_sample_stamps_coasting_not_a_fake_price(self):
        bench = build_bench({"goose": _cohort(5, 1)})
        scope = bench["byRuntime"]["goose"]
        assert scope["stamp"] == STAMP_COASTING
        assert scope["dollars_per_done"]["value"] is None

    def test_healthy_harness_earns_and_ranked_sorts_by_price(self):
        bench = build_bench({
            "openclaw": _cohort(20, 1, cost=1.0),
            "claude_code": _cohort(20, 1, cost=1.5),
        })
        assert bench["byRuntime"]["openclaw"]["stamp"] == STAMP_EARNING
        assert bench["ranked"] == ["openclaw", "claude_code"]

    def test_engine_never_raises_on_garbage(self):
        bench = build_bench({"weird": [None, {}, {"metadata": "x"}, 42]})
        assert bench["byRuntime"]["weird"]["stamp"] == STAMP_CANT_SEE


class TestMarks:
    def test_marks_carry_state_and_source(self):
        scope = build_runtime_scope(_cohort(15, 2), runtime="claude_code")
        for mark in scope["marks"].values():
            assert mark["state"] in ("observed", "supported_none_seen",
                                     "unsupported")
            assert mark["source"]

    def test_no_subagent_records_reads_unsupported_not_zero(self):
        scope = build_runtime_scope(_cohort(15, 2), runtime="grok_bot",
                                    subagent_stats=None)
        assert scope["marks"]["subagents"]["verdict"] == "unseen"
        assert scope["marks"]["subagents"]["state"] == "unsupported"

    def test_observed_subagents_score(self):
        stats = {"spawned": 10, "completed": 9, "failed": 1, "orphaned": 0,
                 "deferred": 3}
        scope = build_runtime_scope(_cohort(15, 2), runtime="openclaw",
                                    subagent_stats=stats)
        assert scope["marks"]["subagents"]["verdict"] == "strong"
        assert scope["marks"]["delegation"]["state"] == "observed"


class TestContextCurves:
    def test_groups_points_and_attaches_compactions(self):
        econ = {
            "utilization": [
                {"session_id": "a", "ts": 1, "pct": 10},
                {"session_id": "a", "ts": 2, "pct": 50},
                {"session_id": "b", "ts": 1, "pct": 90},
            ],
            "compactions": [{"session_id": "a", "ts": 2, "trigger": "proactive",
                             "reclaimed": 38000}],
            "overflow_sessions": ["b"],
        }
        out = build_context_curves(econ)
        by_sid = {c["session_id"]: c for c in out["curves"]}
        assert by_sid["a"]["compactions"][0]["trigger"] == "proactive"
        assert by_sid["b"]["overflowed"] is True
        assert by_sid["a"]["peak_pct"] == 50

    def test_empty_input_is_an_empty_answer_not_an_error(self):
        assert build_context_curves(None) == {"curves": [], "session_count": 0}


class TestWorkloadProfiles:
    def test_channel_sessions_are_chat(self):
        assert classify_session({"metadata": {"channel": "telegram"}}) == "chat_automation"

    def test_repo_sessions_are_coding(self):
        assert classify_session({"git_branch": "main", "metadata": {}}) == "coding"

    def test_recommendations_list_options_and_never_one_winner(self):
        grouped = {
            "openclaw": [_session(2.0, session_id="openclaw:a",
                                  **{"metadata": {"channel": "telegram",
                                                  "quality": {"measurable": True}}})],
        }
        spend = profile_spend(grouped)
        cards = build_recommendations(spend, {}, published_pairs())
        assert cards, "a profile with spend must yield a card"
        for card in cards:
            assert len(card["candidates"]) >= 2
            assert card["qualities"]

    def test_insufficient_evidence_is_unranked(self):
        grouped = {"openclaw": [_session(1.0, session_id="openclaw:a")]}
        cards = build_recommendations(profile_spend(grouped), {}, [])
        assert all(c["ranked"] is False for c in cards)


class TestPublishedPairs:
    def test_every_pair_carries_dated_provenance(self):
        for p in published_pairs():
            assert p["source_url"].startswith("https://")
            assert p["result_date"]
            assert p["runner"] in ("third_party", "vendor")
            assert "historical" in p

    def test_old_results_are_marked_historical(self):
        pairs = published_pairs(now=time.time() + 10 * 365 * 86400)
        assert pairs and all(p["historical"] for p in pairs)

    def test_model_filter_scopes(self):
        pairs = published_pairs(models=["gpt-5.2"])
        assert pairs and all(p["model"] == "gpt-5.2" for p in pairs)


class TestFlowTrace:
    def _events(self):
        return [
            {"session_id": "openclaw:x", "event_type": "message", "ts": 1000,
             "data": {"role": "user", "content": "do the thing"}},
            {"session_id": "openclaw:x", "event_type": "model.completed",
             "ts": 1010, "model": "claude-opus-4-5", "cost_usd": 0.2,
             "token_count": 5000, "data": {}},
            {"session_id": "openclaw:x", "event_type": "tool.result", "ts": 1020,
             "data": {"tool_name": "Bash", "is_error": False}},
            {"session_id": "openclaw:x", "event_type": "message", "ts": 1030,
             "data": {"role": "assistant", "content": "done"}},
        ]

    def test_stations_come_only_from_recorded_events(self):
        trace = build_flow_trace({"session_id": "openclaw:x"}, self._events(),
                                 [], runtime="openclaw", now=2000)
        types = {s["type"] for s in trace["stations"]}
        assert "origin" in types and "model" in types and "reply" in types
        # No subagent rows were provided: no subagent station may be drawn,
        # and the gap is reported in coverage instead.
        assert "subagent" not in types
        assert any(u["type"] == "subagent" for u in trace["unobserved"])

    def test_every_hop_carries_a_receipt(self):
        trace = build_flow_trace({}, self._events(), [], runtime="openclaw")
        assert trace["hops"]
        assert all("receipt" in h for h in trace["hops"])

    def test_recent_activity_reads_live(self):
        trace = build_flow_trace({"session_id": "openclaw:x",
                                  "last_active_at": 1990},
                                 self._events(), [], runtime="openclaw",
                                 now=2000)
        assert trace["live"] is True

    def test_empty_input_never_raises(self):
        trace = build_flow_trace(None, None, None, runtime="")
        assert trace["stations"] and trace["hops"] == []


class TestOutcomeAvailability:
    """Regression: query_quality_sessions rows without an outcome column
    (a daemon wheel predating outcome reporting) must read as "outcomes
    unavailable", never as "nothing ever finished" or "too few runs"."""

    def test_missing_outcomes_have_their_own_basis(self):
        rows = [_session(1.0) for _ in range(20)]
        for r in rows:
            del r["outcome"]
        bench = build_bench({"claude_code": rows})
        scope = bench["byRuntime"]["claude_code"]
        assert scope["dollars_per_done"]["basis"] == "outcomes_unavailable"
        assert "daemon" in scope["stamp_reason"]

    def test_real_failures_are_not_conflated_with_missing_outcomes(self):
        rows = [_session(1.0, outcome="failed") for _ in range(20)]
        bench = build_bench({"codex": rows})
        scope = bench["byRuntime"]["codex"]
        assert scope["dollars_per_done"]["basis"] == "no_success_outcomes"
        assert scope["stamp_reason"] == "no completed jobs recorded in the window"


class TestFlowTraceOrdering:
    """Regression: the store returns events newest-first; a reversed input
    once produced a reply station with negative end-to-end latency."""

    def test_reversed_events_still_yield_positive_latency(self):
        events = [
            {"session_id": "s", "event_type": "message", "ts": 1030,
             "data": {"role": "assistant", "content": "done"}},
            {"session_id": "s", "event_type": "model.completed", "ts": 1010,
             "model": "claude-opus-4-5", "data": {}},
            {"session_id": "s", "event_type": "message", "ts": 1000,
             "data": {"role": "user", "content": "go"}},
        ]
        trace = build_flow_trace({}, events, [], runtime="claude_code")
        reply = next(s for s in trace["stations"] if s["type"] == "reply")
        assert reply["latency_secs"] == 30.0
