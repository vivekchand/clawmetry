"""Route tests for the Harness Engineering tab (routes/bench.py).

The store seam is one module-level function (`routes.bench._ls_call`);
these tests monkeypatch it, matching the house pattern from
tests/test_quality_route.py. The distinction between store-unreachable
(None) and answered-but-empty ([]) is load-bearing and asserted here.
"""

import json

import pytest
from flask import Flask


def _make_app():
    from routes.bench import bp_bench
    app = Flask(__name__)
    app.register_blueprint(bp_bench)
    return app


@pytest.fixture()
def client():
    return _make_app().test_client()


def _session(runtime, cost=1.0, outcome="success", measurable=True, i=0):
    return {
        "session_id": "%s:s%d" % (runtime, i),
        "runtime": runtime,
        "cost_usd": cost,
        "total_tokens": 1000,
        "outcome": outcome,
        "metadata": {"quality": {"measurable": measurable, "verdicts": []}},
    }


def _patch(monkeypatch, handler):
    import routes.bench as bench_module
    monkeypatch.setattr(bench_module, "_ls_call", handler)


class TestApiBench:
    def test_store_unreachable_is_reported_not_blank(self, client, monkeypatch):
        _patch(monkeypatch, lambda method, **kw: None)
        data = client.get("/api/bench").get_json()
        assert data["store_available"] is False
        assert data["byRuntime"] == {}

    def test_empty_window_is_an_honest_empty(self, client, monkeypatch):
        def fake(method, **kw):
            return [] if method == "query_quality_sessions" else ([] if "rollup" in method else {})
        _patch(monkeypatch, fake)
        data = client.get("/api/bench").get_json()
        assert data["store_available"] is True
        assert data["byRuntime"] == {}

    def test_byruntime_payload_shape(self, client, monkeypatch):
        rows = ([_session("openclaw", i=i) for i in range(15)]
                + [_session("cursor", measurable=False, i=i) for i in range(5)])

        def fake(method, **kw):
            if method == "query_quality_sessions":
                return rows
            if method == "query_efficiency_rollup":
                return []
            if method == "query_subagent_stats_by_runtime":
                return {"openclaw": {"spawned": 3, "completed": 3, "failed": 0,
                                     "orphaned": 0, "deferred": 1,
                                     "cost_usd": 0.1, "tokens": 10}}
            return None
        _patch(monkeypatch, fake)
        data = client.get("/api/bench?days=30").get_json()
        assert set(data["byRuntime"]) == {"openclaw", "cursor"}
        assert "openclaw" in data["ranked"]
        assert "cursor" in data["unranked"]
        oc = data["byRuntime"]["openclaw"]
        assert oc["dollars_per_done"]["value"] is not None
        assert oc["marks"]["subagents"]["state"] == "observed"
        cursor = data["byRuntime"]["cursor"]
        assert cursor["stamp"] == "cant_see"
        # Recommendations ride the same payload: one set of store calls
        # per tab load, never a second quality-session scan.
        assert isinstance(data["recommendations"], list)
        assert data["profiles"] is not None

    def test_days_is_clamped(self, client, monkeypatch):
        seen = {}

        def fake(method, **kw):
            seen[method] = kw
            return [] if method != "query_subagent_stats_by_runtime" else {}
        _patch(monkeypatch, fake)
        client.get("/api/bench?days=9999")
        assert seen["query_efficiency_rollup"]["days"] == 90


class TestApiBenchFlow:
    def test_requires_session_and_reports_store_state(self, client, monkeypatch):
        _patch(monkeypatch, lambda method, **kw: None)
        data = client.get("/api/bench/flow/openclaw:abc").get_json()
        assert data["store_available"] is False

    def test_assembles_trace_from_events(self, client, monkeypatch):
        events = [
            {"session_id": "openclaw:abc", "event_type": "message", "ts": 1,
             "data": json.dumps({"role": "user", "content": "hi"})},
            {"session_id": "openclaw:abc", "event_type": "model.completed",
             "ts": 2, "model": "claude-opus-4-5", "cost_usd": 0.1,
             "token_count": 100, "data": "{}"},
        ]

        def fake(method, **kw):
            if method == "query_events":
                return events
            if method == "query_subagents_lite":
                return []
            return None
        _patch(monkeypatch, fake)
        data = client.get("/api/bench/flow/openclaw:abc").get_json()
        assert data["available"] is True
        assert data["runtime"] == "openclaw"
        assert any(s["type"] == "model" for s in data["stations"])


class TestApiBenchPublishedAndCurves:
    def test_published_pairs_have_provenance(self, client, monkeypatch):
        _patch(monkeypatch, lambda method, **kw: [])
        data = client.get("/api/bench/published").get_json()
        assert data["pairs"]
        for p in data["pairs"]:
            assert p["source_url"] and p["result_date"]

    def test_context_curves_group_by_runtime_prefix(self, client, monkeypatch):
        econ = {
            "utilization": [
                {"session_id": "codex:a", "ts": 1, "pct": 40},
                {"session_id": "codex:a", "ts": 2, "pct": 90},
                {"session_id": "bare-uuid", "ts": 1, "pct": 20},
            ],
            "compactions": [],
            "overflow_sessions": [],
        }
        _patch(monkeypatch, lambda method, **kw: econ
               if method == "query_context_economics" else None)
        data = client.get("/api/bench/context-curves").get_json()
        assert data["available"] is True
        assert set(data["byRuntime"]) == {"codex", "openclaw"}

    def test_curves_store_unreachable(self, client, monkeypatch):
        _patch(monkeypatch, lambda method, **kw: None)
        data = client.get("/api/bench/context-curves").get_json()
        assert data["store_available"] is False
