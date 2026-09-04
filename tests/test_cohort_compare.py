"""Cohort compare and similar runs (WO-60; requirement "Cohort compare and
similar runs", REQ-COH-001..004).

Three layers, each hermetic (no live server, no gateway, no network):

1. the pure module ``clawmetry/cohort_compare.py`` driven with fixture rows:
   filter parsing, the shared delta rule and its favourable direction, the
   verdict (Better / Worse / Same / Not enough data / mixed), the
   comparability warning, suggestion derivation, n-gram shape similarity;
2. the routes in ``routes/cohort.py`` through a Flask test client with the
   store seam (``routes.cohort._ls_call``) monkeypatched, including the 402
   ``upgrade_required`` body for a runtime outside the tier;
3. an isolated DuckDB store (``LocalStore`` on a tmp path) for the two store
   reads the daemon proxy serves, including the coverage-none answer for a
   session with no tool stream;

plus a UI contract: the compare surface and the session view carry the ids
and functions the JS renders into, the new copy has no em dashes, and this
file is named in the CI job list (a test file CI never names is not a guard).
"""

from __future__ import annotations

import importlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from flask import Flask

REPO = Path(__file__).resolve().parents[1]


# ── fixtures ───────────────────────────────────────────────────────────────

def _view(sid, runtime="openclaw", model="m1", repo="repo-a", developer="node-1",
          cost=1.0, tokens=1000, steps=10, tool_results=10, tool_errors=0,
          outcome="success", started="2026-09-01T10:00:00", done=None,
          cache_read=None, input_tokens=None, signals=None, branch="main"):
    return {
        "session_id": sid, "title": sid, "runtime": runtime, "model": model,
        "runtime_version": None, "repo": repo, "developer": developer,
        "branch": branch, "started_at": started, "cost_usd": cost,
        "tokens": tokens, "steps": steps, "tool_results": tool_results,
        "tool_errors": tool_errors, "cache_read": cache_read,
        "input_tokens": input_tokens, "outcome": outcome,
        "done": (outcome == "success") if done is None else done,
        "done_basis": "outcome", "signals": signals, "instructions_hash": None,
    }


def _cohort(prefix, n, **kw):
    return [_view(f"{prefix}{i}", **kw) for i in range(n)]


@pytest.fixture()
def client(monkeypatch):
    from routes.cohort import bp_cohort
    app = Flask(__name__)
    app.register_blueprint(bp_cohort)
    return app.test_client()


def _patch(monkeypatch, handler):
    import routes.cohort as mod
    monkeypatch.setattr(mod, "_ls_call", handler)


def _store_row(sid, *, runtime="claude_code", model="m1", cost=1.0, outcome="success",
               started="2026-09-01T10:00:00", cwd="/home/dev/repo-a", node_id="node-1",
               tool_results=10, tool_errors=1, git_links=None, signals=None):
    row = {
        "session_id": sid, "node_id": node_id, "title": "t " + sid,
        "started_at": started, "last_active_at": started, "ended_at": started,
        "status": "ended", "cost_usd": cost, "total_tokens": 1200,
        "metadata": {"runtime": runtime, "model": model, "toolResults": tool_results,
                     "toolErrors": tool_errors,
                     "tokenSplit": {"input": 800, "cacheRead": 200}},
        "outcome": outcome, "cwd": cwd, "git_branch": "main",
        "agent_type": "openclaw", "tool_calls": tool_results,
        "git_commits_linked": git_links,
    }
    if signals is not None:
        row["signals"] = signals
    return row


# ── 1. pure module ─────────────────────────────────────────────────────────

class TestFilters:
    def test_parse_filter_accepts_json_and_dict_and_drops_unknown_keys(self):
        from clawmetry.cohort_compare import parse_filter
        f = parse_filter('{"runtime": "claude_code", "model": " opus ", "bogus": 1}')
        assert f == {"runtime": "claude_code", "model": "opus"}
        assert parse_filter({"repo": "x", "since": "2026-09-01"}) == {"repo": "x", "since": "2026-09-01"}
        assert parse_filter("not json") == {}
        assert parse_filter(None) == {}
        assert parse_filter("[1,2]") == {}

    def test_repeated_params_override_json(self):
        from clawmetry.cohort_compare import filter_from_params
        args = {"a": '{"runtime":"openclaw","model":"m1"}', "a.model": "m2", "a_branch": "dev"}
        assert filter_from_params(args, "a") == {"runtime": "openclaw", "model": "m2", "branch": "dev"}
        assert filter_from_params(args, "b") == {}

    def test_session_matches_every_dimension_and_date_range(self):
        from clawmetry.cohort_compare import session_matches
        v = _view("s", runtime="claude_code", model="opus", repo="r", developer="d",
                  branch="b", started="2026-09-02T00:00:00")
        assert session_matches(v, {"runtime": "claude_code", "model": "OPUS", "repo": "r",
                                   "developer": "d", "branch": "b"})
        assert not session_matches(v, {"model": "sonnet"})
        assert session_matches(v, {"since": "2026-09-01", "until": "2026-09-03"})
        assert not session_matches(v, {"since": "2026-09-03"})
        assert not session_matches(v, {"until": "2026-09-01"})


class TestDeltas:
    def test_signed_delta_and_favourable_direction(self):
        from clawmetry.cohort_compare import signed_deltas
        d = signed_deltas({"cost": 2.0, "hit": 0.5, "flag": True}, {"cost": 1.0, "hit": 0.75, "flag": False},
                          ("cost",), ("hit",))
        assert d["cost"] == {"a": 2.0, "b": 1.0, "abs": -1.0, "pct": -50.0,
                             "favorable": True, "favorable_lower": True}
        assert d["hit"]["favorable"] is True and d["hit"]["abs"] == 0.25
        assert "flag" not in d, "booleans are not metrics"

    def test_zero_baseline_has_no_percent_and_none_is_skipped(self):
        from clawmetry.cohort_compare import signed_deltas
        d = signed_deltas({"cost": 0.0, "steps": None}, {"cost": 3.0, "steps": 4}, ("cost", "steps"), ())
        assert d["cost"]["pct"] is None and d["cost"]["favorable"] is False
        assert "steps" not in d

    def test_run_compare_uses_the_same_rule(self):
        """/api/run-compare's deltas are the shared helper, so a green cell
        means the same thing on both surfaces."""
        import routes.sessions as rs
        from clawmetry.cohort_compare import signed_deltas
        a = {"cost_usd": 2.0, "cache_hit_rate": 0.5, "error_count": 3}
        b = {"cost_usd": 1.0, "cache_hit_rate": 0.7, "error_count": 5}
        assert rs._run_compare_deltas(a, b) == signed_deltas(
            a, b, rs._RUN_COMPARE_LOWER_BETTER, rs._RUN_COMPARE_HIGHER_BETTER)
        src = (REPO / "routes" / "sessions.py").read_text(encoding="utf-8")
        body = src.split("def _run_compare_deltas(a, b):", 1)[1].split("\n\n\n", 1)[0]
        assert "signed_deltas" in body, "run-compare must delegate, not re-implement"


class TestStats:
    def test_stats_report_rates_from_measured_denominators_only(self):
        from clawmetry.cohort_compare import cohort_stats
        views = [_view("a", tool_results=10, tool_errors=2, cache_read=300, input_tokens=100),
                 _view("b", tool_results=None, tool_errors=None, outcome="failed", cost=3.0),
                 _view("c", steps=None, tool_results=None, outcome="ongoing")]
        s = cohort_stats(views)
        assert s["session_count"] == 3
        assert s["tool_error_rate"] == 0.2
        assert s["cache_hit"] == 0.75
        assert s["failure_rate"] == 0.5  # 1 failed of 2 finished
        assert s["done"] == 1 and s["cost_per_done"] == 5.0
        assert s["outcome_mix"] == {"success": 1, "failed": 1, "ongoing": 1}
        assert s["signals"] == "not available"
        assert s["coverage"]["tool_health"] == 1

    def test_no_data_is_none_never_zero(self):
        from clawmetry.cohort_compare import cohort_stats
        s = cohort_stats([_view("a", tool_results=None, tool_errors=None, outcome="ongoing")])
        assert s["tool_error_rate"] is None
        assert s["failure_rate"] is None
        assert s["cache_hit"] is None
        assert s["cost_per_done"] is None

    def test_signal_rates_when_the_table_exists(self):
        from clawmetry.cohort_compare import cohort_stats
        s = cohort_stats([_view("a", signals=["frustration"]), _view("b", signals=[])],
                         signals_available=True)
        assert s["signals"] == {"frustration": 0.5}
        assert s["frustration_rate"] == 0.5


class TestVerdict:
    def _run(self, a, b, floor=5, **kw):
        from clawmetry.cohort_compare import compare
        return compare(a + b, {"model": "m1"}, {"model": "m2"}, floor=floor, **kw)

    def test_better_when_cost_per_done_and_failure_rate_improve(self):
        a = _cohort("a", 6, model="m1", cost=2.0, outcome="failed") + _cohort("a2", 6, model="m1", cost=2.0)
        b = _cohort("b", 12, model="m2", cost=1.0)
        r = self._run(a, b)
        assert r["verdict"]["verdict"] == "Better"
        assert r["verdict"]["mixed"] is False
        assert "cost_per_done" in r["verdict"]["drivers"]
        assert r["verdict"]["sample"] == {"a": 12, "b": 12}

    def test_worse_when_everything_regresses(self):
        a = _cohort("a", 8, model="m1", cost=1.0)
        b = _cohort("b", 8, model="m2", cost=3.0, tool_errors=5)
        r = self._run(a, b)
        assert r["verdict"]["verdict"] == "Worse"
        assert set(r["verdict"]["drivers"]) >= {"cost_per_done", "tool_error_rate"}

    def test_same_when_nothing_moved_materially(self):
        a = _cohort("a", 8, model="m1", cost=1.0)
        b = _cohort("b", 8, model="m2", cost=1.05)
        assert self._run(a, b)["verdict"]["verdict"] == "Same"

    def test_not_enough_data_below_floor(self):
        a = _cohort("a", 3, model="m1")
        b = _cohort("b", 8, model="m2", cost=0.1)
        v = self._run(a, b)["verdict"]
        assert v["verdict"] == "Not enough data"
        assert v["min_sessions"] == 5 and v["sample"] == {"a": 3, "b": 8}
        assert "3" in v["reason"]

    def test_floor_is_env_overridable(self, monkeypatch):
        from clawmetry.cohort_compare import MIN_SESSIONS_ENV, min_sessions
        monkeypatch.setenv(MIN_SESSIONS_ENV, "2")
        assert min_sessions() == 2
        monkeypatch.setenv(MIN_SESSIONS_ENV, "nope")
        assert min_sessions() == 5
        monkeypatch.setenv(MIN_SESSIONS_ENV, "0")
        assert min_sessions() == 1

    def test_mixed_names_the_metrics_that_moved_the_other_way(self):
        # Cheaper per finished job, but tool errors went up: Better, mixed.
        a = _cohort("a", 8, model="m1", cost=2.0, tool_errors=0)
        b = _cohort("b", 8, model="m2", cost=1.0, tool_errors=5)
        v = self._run(a, b)["verdict"]
        assert v["verdict"] in ("Same", "Better", "Worse")
        assert v["mixed"] is True
        assert set(v["drivers"]) | set(v["against"]) == {"cost_per_done", "tool_error_rate"}
        assert v["drivers"] and v["against"]

    def test_cost_per_done_falls_back_to_cost_per_session(self):
        a = _cohort("a", 6, model="m1", cost=2.0, outcome="ongoing")
        b = _cohort("b", 6, model="m2", cost=1.0, outcome="ongoing")
        v = self._run(a, b)["verdict"]
        assert "cost_per_session" in v["metrics_considered"]
        assert v["verdict"] == "Better"

    def test_frustration_rate_takes_part_only_with_signals(self):
        a = _cohort("a", 6, model="m1", signals=[])
        b = _cohort("b", 6, model="m2", signals=["frustration"])
        assert "frustration_rate" not in self._run(a, b)["deltas"]
        r = self._run(a, b, signals_available=True)
        assert r["deltas"]["frustration_rate"]["favorable"] is False
        assert r["verdict"]["verdict"] == "Worse"
        assert r["signals"] == "available"


class TestComparability:
    def test_warns_when_repo_or_developer_mix_differs(self):
        from clawmetry.cohort_compare import comparability
        a = _cohort("a", 6, repo="repo-a", developer="d1")
        b = _cohort("b", 6, repo="repo-b", developer="d1")
        c = comparability(a, b)
        assert c["comparable"] is False
        assert [w["dimension"] for w in c["warnings"]] == ["repo"]
        assert c["warnings"][0]["distance"] == 1.0
        assert "repositor" in c["warnings"][0]["note"]

    def test_no_warning_for_like_for_like_or_unrecorded_dimensions(self):
        from clawmetry.cohort_compare import comparability
        assert comparability(_cohort("a", 4), _cohort("b", 4))["comparable"] is True
        blank = _cohort("a", 4, repo="", developer="")
        assert comparability(blank, _cohort("b", 4, repo="", developer=""))["warnings"] == []


class TestSuggestions:
    def test_new_model_and_week_over_week(self):
        from clawmetry.cohort_compare import build_suggestions
        now = datetime(2026, 9, 4, 12, 0, 0)
        old = (now - timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%S")
        new = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S")
        views = (_cohort("old", 5, runtime="claude_code", model="sonnet-5", started=old)
                 + _cohort("new", 5, runtime="claude_code", model="opus-5", started=new)
                 + _cohort("oc", 3, runtime="openclaw", model="x", started=new))
        out = build_suggestions(views, now=now)
        kinds = [s["kind"] for s in out]
        assert "new_model" in kinds
        nm = next(s for s in out if s["kind"] == "new_model")
        assert nm["title"] == "opus-5 vs sonnet-5 on Claude Code, last 14 days"
        before = (now - timedelta(days=28)).strftime("%Y-%m-%dT%H:%M:%S")
        assert nm["a"] == {"runtime": "claude_code", "model": "sonnet-5", "since": before, "until": new}
        assert nm["b"] == {"runtime": "claude_code", "model": "opus-5", "since": new}
        wow = [s for s in out if s["kind"] == "week_over_week"]
        assert {s["a"]["runtime"] for s in wow} == {"claude_code", "openclaw"}
        assert all("until" in s["a"] and "since" in s["b"] for s in wow)
        assert not any(s["kind"] == "new_runtime_version" for s in out), "no versions recorded"

    def test_runtime_scope_and_instructions_only_when_context_exists(self):
        from clawmetry.cohort_compare import build_suggestions
        now = datetime(2026, 9, 4, 12, 0, 0)
        old = (now - timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%S")
        new = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
        views = _cohort("a", 3, runtime="claude_code", started=old) + _cohort("b", 3, runtime="claude_code", started=new)
        for v in views[:3]:
            v["instructions_hash"] = "aaa"
        for v in views[3:]:
            v["instructions_hash"] = "bbb"
        views += _cohort("oc", 2, runtime="openclaw", started=new)
        out = build_suggestions(views, now=now, runtime="claude_code")
        assert all(s["a"]["runtime"] == "claude_code" for s in out)
        assert not any(s["kind"] == "new_instructions" for s in out)
        out = build_suggestions(views, now=now, runtime="claude_code", context_available=True)
        ins = next(s for s in out if s["kind"] == "new_instructions")
        assert ins["a"]["until"] == new and ins["b"]["since"] == new

    def test_no_em_dashes_in_titles(self):
        from clawmetry.cohort_compare import build_suggestions
        now = datetime(2026, 9, 4)
        views = _cohort("a", 2, runtime="claude_code", started="2026-09-03T00:00:00")
        for s in build_suggestions(views, now=now):
            assert "—" not in s["title"] and " -- " not in s["title"]


class TestShape:
    def test_ngrams_and_weighted_jaccard(self):
        from clawmetry.cohort_compare import tool_shape, weighted_jaccard
        a = tool_shape(["Read", "Edit", "Bash"])
        assert a[("2", "read", "edit")] == 1 and a[("3", "read", "edit", "bash")] == 1
        assert weighted_jaccard(a, tool_shape(["Read", "Edit", "Bash"])) == 1.0
        assert weighted_jaccard(a, tool_shape(["Glob", "Grep"])) == 0.0
        assert 0.0 < weighted_jaccard(a, tool_shape(["Read", "Edit", "Grep"])) < 1.0
        assert tool_shape([]) == {}
        assert tool_shape(["Bash"])[("1", "bash")] == 1

    def test_ranking_skips_empty_and_honours_limit(self):
        from clawmetry.cohort_compare import similar_by_shape
        out = similar_by_shape(["Read", "Edit", "Bash", "Bash"], {
            "twin": ["Read", "Edit", "Bash", "Bash"],
            "close": ["Read", "Edit", "Bash"],
            "far": ["Grep", "Glob"],
            "none": [],
        }, limit=1)
        assert [r["session_id"] for r in out] == ["twin"]
        out = similar_by_shape(["Read", "Edit", "Bash", "Bash"], {"close": ["Read", "Edit", "Bash"], "far": ["Grep"]})
        assert [r["session_id"] for r in out] == ["close"]
        assert out[0]["score"] > 0 and out[0]["tool_calls"] == 3
        assert similar_by_shape([], {"x": ["Read"]}) == []


# ── 2. routes ──────────────────────────────────────────────────────────────

@pytest.fixture
def enforce(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e
    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


class TestCompareRoute:
    def test_missing_filters_is_400_with_the_key_list(self, client, monkeypatch):
        _patch(monkeypatch, lambda m, **kw: [])
        r = client.get("/api/cohort-compare")
        assert r.status_code == 400
        assert "runtime" in r.get_json()["filter_keys"]

    def test_store_unreachable_is_reported_not_blank(self, client, monkeypatch):
        _patch(monkeypatch, lambda m, **kw: None)
        r = client.get('/api/cohort-compare?a={"model":"m1"}&b={"model":"m2"}')
        assert r.status_code == 200
        body = r.get_json()
        assert body["store_available"] is False
        assert body["verdict"]["verdict"] == "Not enough data"
        assert body["signals"] == "not available"

    def test_full_payload_shape(self, client, monkeypatch):
        rows = ([_store_row(f"openclaw-a{i}", runtime="openclaw", model="m1", cost=2.0, tool_errors=3)
                 for i in range(6)]
                + [_store_row(f"openclaw-b{i}", runtime="openclaw", model="m2", cost=1.0, tool_errors=0)
                   for i in range(6)])
        calls = {}

        def fake(method, **kw):
            calls[method] = kw
            return rows
        _patch(monkeypatch, fake)
        r = client.get('/api/cohort-compare?a={"model":"m1"}&b={"model":"m2"}')
        assert r.status_code == 200
        body = r.get_json()
        assert calls["query_cohort_sessions"]["since"] <= datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S")
        assert body["a"]["stats"]["session_count"] == 6 and body["b"]["stats"]["session_count"] == 6
        assert body["a"]["stats"]["cache_hit"] == 0.2
        assert body["deltas"]["cost_per_done"]["favorable"] is True
        assert body["deltas"]["tool_error_rate"]["favorable"] is True
        assert body["verdict"]["verdict"] == "Better"
        assert body["comparability"]["comparable"] is True
        assert body["a"]["label"] == "model m1"
        assert len(body["a"]["sessions"]) == 6 and body["a"]["sessions"][0]["session_id"].startswith("openclaw-a")
        assert body["runtime_version_recorded"] is False
        assert body["signals"] == "not available"

    def test_runtime_switcher_scopes_both_sides(self, client, monkeypatch):
        rows = ([_store_row(f"openclaw-{i}", runtime="openclaw", model="m1") for i in range(6)]
                + [_store_row(f"goose:{i}", runtime="goose", model="m1") for i in range(6)])
        _patch(monkeypatch, lambda m, **kw: rows)
        r = client.get('/api/cohort-compare?a={"model":"m1"}&b={"model":"m1","runtime":"goose"}&runtime=openclaw')
        body = r.get_json()
        assert body["a"]["filter"]["runtime"] == "openclaw"
        assert body["b"]["filter"]["runtime"] == "goose"
        assert body["a"]["stats"]["session_count"] == 6
        assert body["b"]["stats"]["session_count"] == 6

    def test_signals_block_present_when_store_has_the_table(self, client, monkeypatch):
        rows = ([_store_row(f"a{i}", model="m1", signals=["frustration"]) for i in range(5)]
                + [_store_row(f"b{i}", model="m2", signals=[]) for i in range(5)])
        _patch(monkeypatch, lambda m, **kw: rows)
        body = client.get('/api/cohort-compare?a={"model":"m1"}&b={"model":"m2"}').get_json()
        assert body["signals"] == "available"
        assert body["a"]["stats"]["frustration_rate"] == 1.0
        assert body["deltas"]["frustration_rate"]["favorable"] is True

    def test_comparability_warning_when_repos_differ(self, client, monkeypatch):
        rows = ([_store_row(f"a{i}", model="m1", cwd="/x/repo-a") for i in range(5)]
                + [_store_row(f"b{i}", model="m2", cwd="/x/repo-b") for i in range(5)])
        _patch(monkeypatch, lambda m, **kw: rows)
        body = client.get('/api/cohort-compare?a={"model":"m1"}&b={"model":"m2"}').get_json()
        assert body["comparability"]["comparable"] is False
        assert body["comparability"]["warnings"][0]["dimension"] == "repo"


@pytest.fixture
def feature_ok_runtime_blocked(enforce, monkeypatch):
    """A tier that unlocks per_run_compare but only the free runtimes, so the
    runtime check inside the route (not the feature gate in front of it) is
    what produces the 402."""
    ent = enforce.Entitlement(
        tier=enforce.TIER_CLOUD_STARTER, source="license",
        features=frozenset({"per_run_compare"}), runtimes=enforce.FREE_RUNTIMES,
        grace=False,
    )
    monkeypatch.setattr(enforce, "get_entitlement", lambda force=False: ent)
    return ent


class TestEntitlement:
    def test_feature_gate_in_front_uses_the_shared_402_shape(self, client, monkeypatch, enforce):
        _patch(monkeypatch, lambda m, **kw: pytest.fail("store must not be read"))
        r = client.get('/api/cohort-compare?a={"model":"m1"}&b={"model":"m2"}')
        assert r.status_code == 402
        body = r.get_json()
        assert body["error"] == "upgrade_required" and body["feature"] == "per_run_compare"

    def test_named_paid_runtime_returns_the_upgrade_shape(self, client, monkeypatch, feature_ok_runtime_blocked):
        enforce = feature_ok_runtime_blocked and importlib.import_module("clawmetry.entitlements")
        _patch(monkeypatch, lambda m, **kw: pytest.fail("store must not be read"))
        r = client.get('/api/cohort-compare?a={"runtime":"claude_code","model":"m1"}&b={"runtime":"claude_code","model":"m2"}')
        assert r.status_code == 402
        body = r.get_json()
        assert body["error"] == "upgrade_required"
        assert body["runtime"] == "claude_code"
        assert body["required_tier"] == enforce.TIER_CLOUD_STARTER
        assert "a" not in body and "deltas" not in body, "never partial numbers"

    def test_unnamed_runtime_that_resolves_to_paid_sessions_is_refused(self, client, monkeypatch, feature_ok_runtime_blocked):
        rows = ([_store_row(f"claude_code:a{i}", runtime="claude_code", model="m1") for i in range(5)]
                + [_store_row(f"claude_code:b{i}", runtime="claude_code", model="m2") for i in range(5)])
        _patch(monkeypatch, lambda m, **kw: rows)
        r = client.get('/api/cohort-compare?a={"model":"m1"}&b={"model":"m2"}')
        assert r.status_code == 402
        assert r.get_json()["error"] == "upgrade_required"

    def test_free_runtime_passes_when_enforced(self, client, monkeypatch, feature_ok_runtime_blocked):
        rows = ([_store_row(f"openclaw-a{i}", runtime="openclaw", model="m1") for i in range(5)]
                + [_store_row(f"openclaw-b{i}", runtime="openclaw", model="m2") for i in range(5)])
        _patch(monkeypatch, lambda m, **kw: rows)
        r = client.get('/api/cohort-compare?a={"runtime":"openclaw","model":"m1"}&b={"runtime":"openclaw","model":"m2"}')
        assert r.status_code == 200

    def test_suggested_drops_paid_runtimes_and_similar_refuses_them(self, client, monkeypatch, feature_ok_runtime_blocked):
        rows = ([_store_row(f"claude_code:{i}", runtime="claude_code") for i in range(5)]
                + [_store_row(f"openclaw-{i}", runtime="openclaw") for i in range(5)])
        _patch(monkeypatch, lambda m, **kw: rows)
        body = client.get("/api/cohort-compare/suggested").get_json()
        assert all(s["a"]["runtime"] == "openclaw" for s in body["suggestions"])
        r = client.get("/api/sessions/claude_code:abc/similar")
        assert r.status_code == 402


class TestSuggestedRoute:
    def test_cards_carry_filters_titles_and_results(self, client, monkeypatch):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        old = (now - timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%S")
        new = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S")
        rows = ([_store_row(f"openclaw-o{i}", runtime="openclaw", model="sonnet-5", started=old, cost=2.0)
                 for i in range(6)]
                + [_store_row(f"openclaw-n{i}", runtime="openclaw", model="opus-5", started=new, cost=1.0)
                   for i in range(6)])
        _patch(monkeypatch, lambda m, **kw: rows)
        body = client.get("/api/cohort-compare/suggested").get_json()
        assert body["store_available"] is True and body["min_sessions"] == 5
        titles = [s["title"] for s in body["suggestions"]]
        assert "opus-5 vs sonnet-5 on OpenClaw, last 14 days" in titles
        nm = next(s for s in body["suggestions"] if s["kind"] == "new_model")
        assert nm["a"]["model"] == "sonnet-5" and nm["b"]["model"] == "opus-5"
        assert nm["result"]["verdict"]["verdict"] == "Better"
        assert nm["result"]["a"]["stats"]["session_count"] == 6
        assert len(body["suggestions"]) <= 5
        assert body["signals"] == "not available"

    def test_empty_store_is_an_honest_empty(self, client, monkeypatch):
        _patch(monkeypatch, lambda m, **kw: [])
        body = client.get("/api/cohort-compare/suggested").get_json()
        assert body["suggestions"] == [] and body["store_available"] is True
        _patch(monkeypatch, lambda m, **kw: None)
        body = client.get("/api/cohort-compare/suggested").get_json()
        assert body["suggestions"] == [] and body["store_available"] is False


class TestSimilarRoute:
    def test_proxies_to_the_daemon_and_parses_window(self, client, monkeypatch):
        calls = {}

        def fake(method, **kw):
            calls[method] = kw
            return {"session_id": kw["session_id"], "neighbours": [
                {"session_id": "openclaw-2", "score": 0.5, "runtime": "openclaw",
                 "model": "m", "cost_usd": 1.0, "outcome": "success"}],
                "coverage": "tool stream"}
        _patch(monkeypatch, fake)
        body = client.get("/api/sessions/openclaw-1/similar?window=2w&limit=3").get_json()
        assert calls["query_similar_sessions"] == {"session_id": "openclaw-1", "window_days": 14, "limit": 3}
        assert body["neighbours"][0]["score"] == 0.5 and body["store_available"] is True

    def test_store_unreachable(self, client, monkeypatch):
        _patch(monkeypatch, lambda m, **kw: None)
        body = client.get("/api/sessions/openclaw-1/similar").get_json()
        assert body["neighbours"] == [] and body["store_available"] is False
        assert body["coverage"] == "store unreachable"


# ── 3. isolated store ──────────────────────────────────────────────────────

@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    duckdb = pytest.importorskip("duckdb")  # noqa: F841
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "3600")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "100000")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "cohort.duckdb"))
    import clawmetry.local_store as ls
    ls = importlib.reload(ls)
    store = ls.LocalStore()
    try:
        yield ls, store
    finally:
        try:
            store.stop(flush=False)
        except Exception:
            pass


def _seed_sessions(store, rows):
    for r in rows:
        store.ingest_session(r)


def _tool_events(sid, names, day="2026-09-02"):
    out = []
    for i, name in enumerate(names):
        out.append({
            "id": f"{sid}-e{i}", "node_id": "n1", "agent_type": "openclaw",
            "session_id": sid, "event_type": "tool_call",
            "ts": f"{day}T10:{i:02d}:00", "data": {"tool": name, "args": {}},
        })
    return out


class TestStoreReads:
    def test_cohort_sessions_from_the_store(self, fresh_store):
        ls, store = fresh_store
        _seed_sessions(store, [
            {"session_id": "openclaw-1", "node_id": "n1", "started_at": "2026-09-02T10:00:00",
             "cost_usd": 2.0, "total_tokens": 100, "outcome": "success", "cwd": "/w/repo-a",
             "git_branch": "main", "metadata": {"runtime": "openclaw", "model": "m1", "toolResults": 4, "toolErrors": 1}},
            {"session_id": "openclaw-2", "node_id": "n1", "started_at": "2026-08-01T10:00:00",
             "cost_usd": 1.0, "outcome": "failed", "metadata": {"runtime": "openclaw", "model": "m2"}},
        ])
        store.flush()
        rows = store.query_cohort_sessions(since="2026-09-01T00:00:00")
        assert [r["session_id"] for r in rows] == ["openclaw-1"]
        r = rows[0]
        assert r["metadata"]["model"] == "m1" and r["cwd"] == "/w/repo-a"
        assert r["git_commits_linked"] is None
        # WO-58 ships the signal_matches table with the store (CREATE IF NOT
        # EXISTS), so the signals input is present on every store; a session
        # no tick has matched carries an empty list, never a missing key.
        assert r.get("signals") == [] and "instructions_hash" not in r
        from clawmetry.cohort_compare import session_view
        v = session_view(r)
        assert v["repo"] == "repo-a" and v["developer"] == "n1" and v["tool_errors"] == 1
        assert v["steps"] == 4 and v["runtime_version"] is None
        assert len(store.query_cohort_sessions()) == 2

    def test_suggested_derivation_from_the_store(self, fresh_store):
        ls, store = fresh_store
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        old = (now - timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%S")
        new = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
        rows = []
        for i in range(6):
            rows.append({"session_id": f"openclaw-o{i}", "node_id": "n1", "started_at": old,
                         "cost_usd": 2.0, "outcome": "success",
                         "metadata": {"runtime": "openclaw", "model": "sonnet-5"}})
            rows.append({"session_id": f"openclaw-n{i}", "node_id": "n1", "started_at": new,
                         "cost_usd": 1.0, "outcome": "success",
                         "metadata": {"runtime": "openclaw", "model": "opus-5"}})
        _seed_sessions(store, rows)
        store.flush()
        from clawmetry.cohort_compare import build_suggestions, session_view
        views = [session_view(r) for r in store.query_cohort_sessions()]
        out = build_suggestions(views)
        nm = next(s for s in out if s["kind"] == "new_model")
        assert nm["b"]["model"] == "opus-5" and nm["a"]["model"] == "sonnet-5"
        assert any(s["kind"] == "week_over_week" for s in out)

    def test_similar_sessions_from_the_store(self, fresh_store):
        ls, store = fresh_store
        day = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
        _seed_sessions(store, [
            {"session_id": s, "node_id": "n1", "started_at": f"{day}T09:00:00",
             "last_active_at": f"{day}T09:30:00", "cost_usd": 1.0, "outcome": "success",
             "title": "title " + s, "metadata": {"runtime": "openclaw", "model": "m1"}}
            for s in ("openclaw-target", "openclaw-twin", "openclaw-far", "openclaw-silent", "goose:cousin")
        ])
        events = (_tool_events("openclaw-target", ["Read", "Edit", "Bash", "Bash"], day)
                  + _tool_events("openclaw-twin", ["Read", "Edit", "Bash", "Bash"], day)
                  + _tool_events("openclaw-far", ["Grep", "Glob"], day)
                  + _tool_events("goose:cousin", ["Read", "Edit", "Bash"], day))
        store.ingest_many(events)
        store.flush()
        body = store.query_similar_sessions(session_id="openclaw-target", window_days=30, limit=10)
        assert body["tool_calls"] == 4 and body["coverage"] == "tool stream"
        ids = [n["session_id"] for n in body["neighbours"]]
        assert ids[0] == "openclaw-twin" and "goose:cousin" in ids
        assert "openclaw-far" not in ids and "openclaw-silent" not in ids
        twin = body["neighbours"][0]
        assert twin["score"] == 1.0 and twin["runtime"] == "openclaw" and twin["model"] == "m1"
        # ``outcome`` is written by the classifier, not by ingest_session, so a
        # freshly seeded row reads "unknown" here; the key is always present.
        assert twin["cost_usd"] == 1.0 and twin["outcome"] == "unknown" and twin["title"] == "title openclaw-twin"

    def test_similar_coverage_none_for_a_session_without_a_tool_stream(self, fresh_store):
        ls, store = fresh_store
        _seed_sessions(store, [{"session_id": "goose:quiet", "node_id": "n1",
                                "started_at": "2026-09-02T09:00:00", "metadata": {"runtime": "goose"}}])
        store.flush()
        body = store.query_similar_sessions(session_id="goose:quiet")
        assert body["neighbours"] == []
        assert body["coverage"] == "no tool stream exposed by goose"

    def test_daemon_dispatch_shape_and_allowlist(self):
        import routes.local_query as lq
        from clawmetry import query_contract as qc
        assert {"query_cohort_sessions", "query_similar_sessions"} <= set(lq._DAEMON_METHODS)
        assert lq._SHAPES["similar_sessions"] == "query_similar_sessions"
        assert qc.QUERY_CONTRACT["similar_sessions"]["trust"] == qc.TRUST_E2E
        args = lq._coerce_args("similar_sessions", {"session_id": "x", "window_days": "999", "limit": "0", "junk": 1})
        assert args == {"session_id": "x", "window_days": 365, "limit": 1}
        with pytest.raises(ValueError):
            lq._coerce_args("similar_sessions", {})


# ── 4. UI contract ─────────────────────────────────────────────────────────

class TestUiContract:
    def test_compare_surface_leads_with_suggestions_then_verdict_then_advanced(self):
        html = (REPO / "clawmetry" / "templates" / "tabs" / "overview.html").read_text(encoding="utf-8")
        card = html.split('id="compare-runs-card"', 1)[1].split("<!-- Error triage", 1)[0]
        order = [card.index('id="cohort-suggestions"'), card.index('id="cohort-result"'),
                 card.index('id="cohort-advanced"'), card.index('id="compare-input-a"'),
                 card.index('id="compare-runs-body"')]
        assert order == sorted(order), "suggestions, then verdict, then Advanced (two-run compare)"
        assert 'data-i18n="overview.compare_title"' in card
        assert "—" not in card and " -- " not in card and "&mdash;" not in card

    def test_session_view_offers_similar_runs_below_the_fold(self):
        html = (REPO / "clawmetry" / "templates" / "tabs" / "transcripts.html").read_text(encoding="utf-8")
        assert html.index('id="transcript-messages"') < html.index('id="similar-runs-card"')
        block = html.split('id="similar-runs-card"', 1)[1].split("</div>\n  </div>", 1)[0]
        assert 'id="similar-runs-body"' in block
        assert "—" not in block and " -- " not in block

    def test_app_js_wires_both_surfaces_with_honest_cloud_states(self):
        js = (REPO / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")
        for fn in ("loadCohortSuggested", "showCohortSuggestion", "renderCohortResult",
                   "runCohortCompare", "loadSimilarRuns", "openCohortSession"):
            assert re.search(r"function " + fn + r"\(", js), fn
        assert "/api/cohort-compare/suggested" in js
        assert "/similar?window=" in js
        assert "try { loadCohortSuggested(); } catch (e) {}" in js
        assert "try { loadSimilarRuns(sessionId); } catch (e) {}" in js
        block = js.split('Cohort compare: "did the change help?"', 1)[1].split("// ── Error triage", 1)[0]
        assert "window.CLOUD_MODE" in block and "compare_cloud_custom" in block
        assert "similar_runs_cloud" in block
        assert "_cmRuntimeFilter" in block, "respects the runtime switcher"
        assert "—" not in block and " -- " not in block

    def test_en_catalog_carries_the_new_copy(self):
        en = json.loads((REPO / "clawmetry" / "static" / "locales" / "en.json").read_text(encoding="utf-8"))
        for key in ("overview.compare_title", "overview.compare_hint", "overview.compare_advanced",
                    "overview.compare_none", "overview.compare_cloud_custom",
                    "transcripts.similar_runs_title", "transcripts.similar_runs_cloud",
                    "transcripts.similar_runs_none"):
            assert key in en, key
            assert "—" not in en[key] and " -- " not in en[key], key

    def test_snapshot_emits_cohort_suggested(self):
        src = (REPO / "clawmetry" / "sync.py").read_text(encoding="utf-8")
        assert '"cohortSuggested": cohort_slice' in src
        assert "def _build_cohort_suggested_slice(" in src

    def test_this_file_runs_in_ci(self):
        ci = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        mk = (REPO / "Makefile").read_text(encoding="utf-8")
        assert "tests/test_cohort_compare.py" in ci, "add to a ci.yml job list or it never runs"
        assert "tests/test_cohort_compare.py" in mk
