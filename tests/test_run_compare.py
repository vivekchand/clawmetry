"""Per-run A/B compare with deltas (#2196 item #2)."""
from __future__ import annotations

import importlib
import time

import pytest


def _store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "ev.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "2")
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    return ls, ls.get_store()


def _wait_flush(store, t=3.0):
    end = time.monotonic() + t
    while time.monotonic() < end and store.health()["ring_depth"] > 0:
        time.sleep(0.02)


def _patch_daemon_proxy(monkeypatch, store):
    """Make routes.local_query.local_store_via_daemon read straight from the
    in-process store, so the route handler runs end-to-end without needing the
    real daemon HTTP server."""
    import routes.sessions as sessions_mod

    def fake_proxy(method, **kwargs):
        fn = getattr(store, method)
        return fn(**kwargs)

    # The route imports lazily inside the function — patch the module it pulls
    # from so both call sites resolve to our fake.
    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", fake_proxy, raising=False,
    )
    return sessions_mod


def test_run_compare_stats_basic(tmp_path, monkeypatch):
    ls, store = _store(tmp_path, monkeypatch)
    try:
        # Baseline run "a": 3 tool calls, no errors, no flags (clean).
        for i in range(3):
            store.ingest({
                "id": f"a:{i}", "node_id": "n", "agent_id": "main",
                "session_id": "claude_code:run-a",
                "event_type": "tool_call",
                "ts": f"2026-05-28T10:00:{i:02d}Z",
                "data": {"name": "Read"},
                "cost_usd": 0.10, "token_count": 100, "model": None,
            })
        # Candidate run "b": 35 tool calls (runaway) + a real error.
        for i in range(35):
            store.ingest({
                "id": f"b:{i}", "node_id": "n", "agent_id": "main",
                "session_id": "claude_code:run-b",
                "event_type": "tool_call",
                "ts": f"2026-05-28T11:00:{i:02d}Z",
                "data": {"name": "Bash"},
                "cost_usd": 0.10, "token_count": 100, "model": None,
            })
        store.ingest({
            "id": "b:result-err", "node_id": "n", "agent_id": "main",
            "session_id": "claude_code:run-b",
            "event_type": "tool_result",
            "ts": "2026-05-28T11:01:00Z",
            "data": {"role": "tool", "_runtime": "claude_code",
                     "content": "Exit code 1\nTraceback ...",
                     "extra": {"isError": True}},
            "cost_usd": 0.0, "token_count": 0, "model": None,
        })
        _wait_flush(store)

        sessions_mod = _patch_daemon_proxy(monkeypatch, store)
        a = sessions_mod._run_compare_stats("claude_code:run-a")
        b = sessions_mod._run_compare_stats("claude_code:run-b")

        # Baseline: clean (3 steps, no errors, no flags).
        assert a["runtime"] == "claude_code"
        assert a["step_count"] == 3
        assert a["error_count"] == 0
        assert a["flag_count"] == 0
        assert a["severity"] == "green"
        assert a["missing"] is False
        # Candidate: runaway flag + 1 real error.
        assert b["step_count"] == 35
        assert b["error_count"] == 1
        assert any(f["type"] == "runaway" for f in b["flags"])
        assert b["severity"] == "red"

        deltas = sessions_mod._run_compare_deltas(a, b)
        # Step count went up — that's a regression (favorable=False for
        # lower-is-better metrics).
        assert deltas["step_count"]["abs"] == 32
        assert deltas["step_count"]["favorable"] is False
        # Error count went up too.
        assert deltas["error_count"]["a"] == 0
        assert deltas["error_count"]["b"] == 1
        assert deltas["error_count"]["favorable"] is False
        # When A is zero, pct is None (no /0).
        assert deltas["error_count"]["pct"] is None
    finally:
        store.stop(flush=True)


def _client_with_route():
    """Mount bp_sessions on a fresh Flask app — dashboard.py only registers
    blueprints inside main(), so plain ``import dashboard`` leaves them off.
    This mirrors the pattern in tests/test_channels_local_store.py."""
    from flask import Flask
    import routes.sessions as sessions_mod
    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    return a.test_client()


def test_run_compare_route_missing_params():
    """The HTTP route returns a clean 400 when either id is missing or both
    refer to the same session — sanity test for the API contract."""
    client = _client_with_route()
    resp = client.get("/api/run-compare?a=x")
    assert resp.status_code == 400, resp.get_data(as_text=True)

    resp = client.get("/api/run-compare?a=same&b=same")
    assert resp.status_code == 400


def test_run_compare_route_end_to_end(tmp_path, monkeypatch):
    ls, store = _store(tmp_path, monkeypatch)
    try:
        # Two clean sessions, different cost.
        store.ingest({
            "id": "cheap:1", "node_id": "n", "agent_id": "main",
            "session_id": "openclaw-cheap", "event_type": "tool_call",
            "ts": "2026-05-28T08:00:00Z", "data": {"name": "Read"},
            "cost_usd": 0.05, "token_count": 100, "model": None,
        })
        store.ingest({
            "id": "spendy:1", "node_id": "n", "agent_id": "main",
            "session_id": "openclaw-spendy", "event_type": "tool_call",
            "ts": "2026-05-28T09:00:00Z", "data": {"name": "Read"},
            # cost up, but under the bloated-context token threshold so the
            # severity stays green — we're only asserting the cost delta here.
            "cost_usd": 5.00, "token_count": 1_000, "model": None,
        })
        _wait_flush(store)

        _patch_daemon_proxy(monkeypatch, store)
        client = _client_with_route()
        resp = client.get(
            "/api/run-compare?a=openclaw-cheap&b=openclaw-spendy"
        )
        assert resp.status_code == 200, resp.get_data(as_text=True)
        body = resp.get_json()
        assert body["a"]["session_id"] == "openclaw-cheap"
        assert body["b"]["session_id"] == "openclaw-spendy"
        # B is more expensive -> regression on cost.
        assert body["deltas"]["cost_usd"]["abs"] > 4.0
        assert body["deltas"]["cost_usd"]["favorable"] is False
        # Both clean -> green severity.
        assert body["a"]["severity"] == body["b"]["severity"] == "green"
    finally:
        store.stop(flush=True)


def _set_outcome(store, *, agent_type, session_id, outcome, confidence=0.9):
    """Test helper: stamp an outcome on a session row. There's no public
    'set outcome' method (only the classifier writes it); write directly under
    the store's writer lock the same way reclassify_session_outcome does."""
    with store._write_lock:
        store._conn.execute(
            "UPDATE sessions SET outcome=?, outcome_confidence=?, "
            "outcome_classified_at=? WHERE agent_type=? AND session_id=?",
            [outcome, float(confidence), int(time.time() * 1000),
             agent_type, session_id],
        )


def test_run_compare_quality_rows_end_to_end(tmp_path, monkeypatch):
    """Two scored + classified sessions -> /api/run-compare carries eval_score
    with a signed delta (favorable=higher), outcome per side, and an
    improved/regressed verdict."""
    ls, store = _store(tmp_path, monkeypatch)
    try:
        # One event per side so the sessions exist in the events-derived path.
        for sid in ("oc-base", "oc-cand"):
            store.ingest({
                "id": f"{sid}:1", "node_id": "n", "agent_id": "main",
                "session_id": sid, "event_type": "tool_call",
                "ts": "2026-05-28T08:00:00Z", "data": {"name": "Read"},
                "cost_usd": 0.05, "token_count": 100, "model": None,
            })
        # Typed session rows (eval/outcome columns live on the sessions table).
        store.ingest_session({"session_id": "oc-base", "agent_type": "openclaw"})
        store.ingest_session({"session_id": "oc-cand", "agent_type": "openclaw"})
        now_ms = int(time.time() * 1000)
        store.persist_eval_score(session_id="oc-base", score=2.0,
                                 reason="weak", judge_model="m", scored_at=now_ms)
        store.persist_eval_score(session_id="oc-cand", score=4.5,
                                 reason="strong", judge_model="m", scored_at=now_ms)
        _set_outcome(store, agent_type="openclaw", session_id="oc-base",
                     outcome="failed")
        _set_outcome(store, agent_type="openclaw", session_id="oc-cand",
                     outcome="success")
        _wait_flush(store)

        _patch_daemon_proxy(monkeypatch, store)
        client = _client_with_route()
        resp = client.get("/api/run-compare?a=oc-base&b=oc-cand")
        assert resp.status_code == 200, resp.get_data(as_text=True)
        body = resp.get_json()

        # Per-side quality fields.
        assert body["a"]["eval_score"] == 2.0
        assert body["b"]["eval_score"] == 4.5
        assert body["a"]["eval_reason"] == "weak"
        assert body["a"]["outcome"] == "failed"
        assert body["b"]["outcome"] == "success"

        # eval_score delta: higher is better, B improved -> favorable.
        ed = body["deltas"]["eval_score"]
        assert ed["a"] == 2.0 and ed["b"] == 4.5
        assert abs(ed["abs"] - 2.5) < 1e-9
        assert ed["favorable"] is True
        assert ed["favorable_lower"] is False

        # Textual outcome verdict: failed -> success is an improvement.
        assert body["outcome_verdict"] == "improved"
    finally:
        store.stop(flush=True)


def test_run_compare_quality_null_safe_when_one_side_unscored(tmp_path, monkeypatch):
    """A session without an eval score / outcome comes back null and the
    eval_score delta is omitted (additive, backward-compatible)."""
    ls, store = _store(tmp_path, monkeypatch)
    try:
        for sid in ("oc-scored", "oc-bare"):
            store.ingest({
                "id": f"{sid}:1", "node_id": "n", "agent_id": "main",
                "session_id": sid, "event_type": "tool_call",
                "ts": "2026-05-28T08:00:00Z", "data": {"name": "Read"},
                "cost_usd": 0.05, "token_count": 100, "model": None,
            })
        store.ingest_session({"session_id": "oc-scored", "agent_type": "openclaw"})
        # oc-bare: no ingest_session, no score, no outcome.
        store.persist_eval_score(session_id="oc-scored", score=3.5,
                                 reason="ok", judge_model="m",
                                 scored_at=int(time.time() * 1000))
        _wait_flush(store)

        _patch_daemon_proxy(monkeypatch, store)
        client = _client_with_route()
        resp = client.get("/api/run-compare?a=oc-scored&b=oc-bare")
        assert resp.status_code == 200, resp.get_data(as_text=True)
        body = resp.get_json()

        assert body["a"]["eval_score"] == 3.5
        assert body["b"]["eval_score"] is None
        assert body["b"]["outcome"] is None
        # Delta omitted when either side is null (no /0, no bogus arrow).
        assert "eval_score" not in body["deltas"]
        # Verdict null when an outcome is missing.
        assert body["outcome_verdict"] is None
        # Legacy keys still present + correct (backward compatible).
        assert "cost_usd" in body["deltas"]
    finally:
        store.stop(flush=True)


def test_query_session_quality_window_eval_and_outcome(tmp_path, monkeypatch):
    """Store-level: the quality window aggregates scored + classified sessions
    and excludes ongoing/old rows."""
    ls, store = _store(tmp_path, monkeypatch)
    try:
        now_ms = int(time.time() * 1000)
        old_ms = now_ms - 5 * 60 * 60 * 1000  # 5h ago, outside a 60m window.
        # Three in-window scored sessions: avg = (1 + 2 + 3) / 3 = 2.0
        for i, score in enumerate((1.0, 2.0, 3.0)):
            sid = f"s-{i}"
            store.ingest_session({"session_id": sid, "agent_type": "openclaw"})
            store.persist_eval_score(session_id=sid, score=score, reason="r",
                                     judge_model="m", scored_at=now_ms)
        # One out-of-window score (5h old) — must NOT count.
        store.ingest_session({"session_id": "s-old", "agent_type": "openclaw"})
        store.persist_eval_score(session_id="s-old", score=5.0, reason="r",
                                 judge_model="m", scored_at=old_ms)
        # Outcomes: 2 success, 1 failed, 1 tool_call_stuck, 1 ongoing (excluded).
        for sid, oc in (("o-1", "success"), ("o-2", "success"),
                        ("o-3", "failed"), ("o-4", "tool_call_stuck"),
                        ("o-5", "ongoing")):
            store.ingest_session({"session_id": sid, "agent_type": "openclaw"})
            _set_outcome(store, agent_type="openclaw", session_id=sid, outcome=oc)

        q = store.query_session_quality_window(window_minutes=60)
        assert q["eval_count"] == 3
        assert abs(q["eval_avg"] - 2.0) < 1e-9
        # 4 classified non-ongoing; 2 failure-ish.
        assert q["classified_total"] == 4
        assert q["failed_count"] == 2
        assert abs(q["failure_rate"] - 0.5) < 1e-9
        assert q["outcome_counts"].get("success") == 2
        assert "ongoing" not in q["outcome_counts"]
    finally:
        store.stop(flush=True)


def test_query_session_quality_window_empty_store(tmp_path, monkeypatch):
    """Empty store -> zero counts, None averages, no crash."""
    ls, store = _store(tmp_path, monkeypatch)
    try:
        q = store.query_session_quality_window(window_minutes=60)
        assert q["eval_count"] == 0
        assert q["eval_avg"] is None
        assert q["classified_total"] == 0
        assert q["failure_rate"] is None
    finally:
        store.stop(flush=True)


def test_query_session_quality_lookup(tmp_path, monkeypatch):
    """query_session_quality returns per-session eval/outcome, null for
    unscored, and {} for an empty id list."""
    ls, store = _store(tmp_path, monkeypatch)
    try:
        store.ingest_session({"session_id": "q-1", "agent_type": "openclaw"})
        store.persist_eval_score(session_id="q-1", score=4.0, reason="good",
                                 judge_model="m", scored_at=int(time.time() * 1000))
        _set_outcome(store, agent_type="openclaw", session_id="q-1",
                     outcome="success")
        store.ingest_session({"session_id": "q-2", "agent_type": "openclaw"})

        out = store.query_session_quality(session_ids=["q-1", "q-2", "missing"])
        assert out["q-1"]["eval_score"] == 4.0
        assert out["q-1"]["eval_reason"] == "good"
        assert out["q-1"]["outcome"] == "success"
        assert out["q-2"]["eval_score"] is None
        assert out["q-2"]["outcome"] is None
        assert "missing" not in out
        assert store.query_session_quality(session_ids=[]) == {}
    finally:
        store.stop(flush=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
