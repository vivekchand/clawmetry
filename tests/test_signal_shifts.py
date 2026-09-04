"""Signal shifts (WO-62): band math, issue lifecycle, breakdown, delivery,
routes, snapshot.

Requirement 0904463d-6472-4812-978c-86d541f1cca5 (REQ-SHIFT-001).

What is pinned here, and why each pin exists:

* Band math and clamps: a flat history cannot fire on noise (floor), a
  wildly noisy history cannot push the threshold out of reach (ceiling),
  and the ``threshold_source`` says which one applied.
* Minimum samples on BOTH sides. A solo developer with twenty turns never
  gets an issue invented from three of them.
* One open issue per (signal, runtime): a second tick over the same shift
  updates the row, never duplicates it.
* A resolved issue reopens (``reopen_count`` + 1) rather than duplicating,
  but only once the resolved window has aged out, so resolving a live shift
  does not reopen it on the next tick.
* An ignored issue stays silent: refreshed, never delivered.
* Breakdown ranks the value that got WORSE, not the one that got busier.
* The alert payload names signal / runtime / rates / samples / top line and
  never carries text (nothing here has any).
* Routes through the Flask test client against an isolated DuckDB file;
  the status route refuses a cross-origin POST.
* Snapshot slice key ``signalIssues`` and the daemon allowlist.
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from clawmetry import signal_shifts as ss  # noqa: E402

pytest.importorskip("duckdb")

_DAY = 86400 * 1000
_HOUR = 3600 * 1000


# ── band math ───────────────────────────────────────────────────────────────

def _hist(rate, days=28, turns=20, jitter=None):
    rows = []
    for d in range(days):
        r = rate + (jitter[d % len(jitter)] if jitter else 0.0)
        rows.append({"day": d, "turns": turns, "matches": int(round(max(0.0, r) * turns))})
    return rows


def test_flat_history_uses_the_floor():
    band = ss.learned_band(_hist(0.04), k=2.0, min_delta=0.02, ceil_ratio=5.0)
    assert band["spread"] == 0.0
    assert band["source"] == "floor"
    assert abs(band["threshold"] - (band["mean"] + 0.02)) < 1e-5


def test_noisy_history_learns_and_is_capped_by_the_ceiling():
    band = ss.learned_band(_hist(0.05, turns=100, jitter=[-0.02, 0.0, 0.02]), k=2.0,
                           min_delta=0.02, ceil_ratio=5.0)
    assert band["source"] == "learned"
    assert band["mean"] + 0.02 < band["threshold"] < band["mean"] * 5.0
    # One wild day in ten: mean 5%, spread 15%, raw 35% > 5x mean -> ceiling.
    wild = ss.learned_band(_hist(0.0, turns=100, jitter=[0.0] * 9 + [0.5]), k=2.0,
                           min_delta=0.02, ceil_ratio=5.0)
    assert wild["source"] == "ceiling"
    assert abs(wild["threshold"] - wild["mean"] * 5.0) < 1e-5


def test_threshold_never_exceeds_one_and_ignores_empty_days():
    band = ss.learned_band([{"day": 0, "turns": 0, "matches": 0}] + _hist(0.9, jitter=[0.0, 0.1]),
                           k=10.0, min_delta=0.02, ceil_ratio=5.0)
    assert band["threshold"] <= 1.0
    assert band["n_days"] == 28


def test_min_samples_apply_on_both_sides():
    hist = _hist(0.04)
    assert ss.detect_shift({"turns": 10, "matches": 5}, hist, min_short=30, min_history=200) is None
    assert ss.detect_shift({"turns": 40, "matches": 10}, _hist(0.04, days=3),
                           min_short=30, min_history=200) is None
    hit = ss.detect_shift({"turns": 40, "matches": 10}, hist, min_short=30, min_history=200)
    assert hit and hit["rate_during"] == 0.25 and hit["n_before"] == 560
    assert hit["threshold_source"] in ("floor", "learned", "ceiling")


def test_inside_the_band_is_not_a_shift():
    assert ss.detect_shift({"turns": 100, "matches": 5}, _hist(0.04),
                           min_short=30, min_history=200) is None


def test_env_defaults_are_read():
    assert ss.MIN_SHORT == int(os.environ.get("CLAWMETRY_SHIFT_MIN_SHORT", "30"))
    assert ss.MIN_HISTORY == int(os.environ.get("CLAWMETRY_SHIFT_MIN_HISTORY", "200"))
    assert ss.K == float(os.environ.get("CLAWMETRY_SHIFT_K", "2.0"))


# ── breakdown ───────────────────────────────────────────────────────────────

def _rows(sid, model, period, n, version="1.0"):
    return {"session_id": sid, "model": model, "runtime_version": version, "period": period, "n": n}


def test_breakdown_ranks_the_value_that_got_worse():
    # Model A: 4% before -> 30% during. Model B: 4% before -> 4% during but 3x busier.
    turns = [_rows("a1", "model-a", "before", 500), _rows("a1", "model-a", "during", 50),
             _rows("b1", "model-b", "before", 500), _rows("b1", "model-b", "during", 150)]
    matches = [_rows("a1", "model-a", "before", 20), _rows("a1", "model-a", "during", 15),
               _rows("b1", "model-b", "before", 20), _rows("b1", "model-b", "during", 6)]
    bd = ss.rank_breakdown(turns, matches, cwd_of={"a1": "/home/me/repo-a", "b1": "/home/me/repo-b"},
                           tool_of={"a1": "Bash", "b1": "Edit"})
    assert bd["model"][0]["value"] == "model-a"
    assert bd["model"][0]["share"] > 0.9
    assert bd["model"][1]["share"] < 0.1
    assert bd["cwd"][0]["value"] == "repo-a"
    assert bd["tool"][0]["value"] == "Bash"
    assert bd["top"]["value"] in ("model-a", "repo-a", "Bash")
    for dim in ss.BREAKDOWN_DIMENSIONS:
        assert dim in bd and len(bd[dim]) <= ss.BREAKDOWN_TOP_N


def test_breakdown_handles_empty_input():
    bd = ss.rank_breakdown([], [])
    assert bd["top"] is None and all(bd[d] == [] for d in ss.BREAKDOWN_DIMENSIONS)


# ── plain words ─────────────────────────────────────────────────────────────

def _issue(**kw):
    base = {"id": "si_1", "signal": "user_frustration", "agent_type": "cursor", "status": "open",
            "opened_at": int(time.time() * 1000) - 2 * _DAY, "rate_before": 0.04,
            "rate_during": 0.11, "n_before": 900, "n_during": 60, "reopen_count": 0,
            "breakdown": {"top": {"dim": "model", "value": "claude-x", "share": 0.8,
                                  "rate_before": 0.04, "rate_during": 0.2}}}
    base.update(kw)
    return base


def test_headline_is_plain_words_without_em_dash():
    h = ss.issue_headline(_issue())
    assert h.startswith("Frustration on Cursor jumped from 4% to 11% since ")
    assert h.endswith(", mostly on claude-x.")
    assert "—" not in h and " -- " not in h
    assert "today" in ss.issue_headline(_issue(opened_at=int(time.time() * 1000)))
    # A weak breakdown is not claimed.
    weak = _issue(breakdown={"top": {"dim": "model", "value": "m", "share": 0.05}})
    assert "mostly" not in ss.issue_headline(weak)


def test_alert_payload_names_the_numbers_and_never_text():
    m = ss.shift_alert_match(_issue(), node_id="n1", link="http://localhost:8900/#signals")
    assert m["rule"]["id"] == "builtin:signal_shift:user_frustration:cursor"
    assert m["rule"]["condition_json"]["type"] == "signal_shift"
    assert m["rule"]["condition_json"]["cooldown_sec"] == ss.SHIFT_ALERT_COOLDOWN_SEC
    md = m["metadata"]
    for k in ("signal", "runtime", "rate_before", "rate_during", "n_before", "n_during",
              "top_breakdown", "link", "issue_id"):
        assert k in md, k
    assert "claude-x" in md["top_breakdown"] and "80%" in md["top_breakdown"]
    assert md["link"].endswith("#signals")
    blob = json.dumps(m)
    for word in ("wtf", "sucks", "phrase", "text"):
        assert word not in blob
    assert ss.shift_alert_match(_issue(), action="reopened")["summary"].startswith("Reopened: ")


# ── store + tick (isolated DuckDB) ─────────────────────────────────────────

@pytest.fixture()
def store(tmp_path, monkeypatch):
    """A direct LocalStore on a per-test DuckDB file. ``DB_PATH`` is resolved
    at connect time from the module global, and conftest has already pinned
    the env var for the whole session, so the global is patched here: one
    file per test, nothing shared, nothing from the developer's store."""
    from pathlib import Path
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "3600")
    from clawmetry import local_store as ls
    monkeypatch.setattr(ls, "DB_PATH", Path(tmp_path / "shifts.duckdb"))
    s = ls.LocalStore()
    yield s
    try:
        s.stop(flush=False)
    except Exception:
        pass


NOW = 1_800_000_000_000  # fixed "now" so day buckets are deterministic


def _seed_shift(store, *, runtime="cursor", hist_rate=0.04, short_rate=0.25,
                hist_days=28, hist_turns=25, short_turns=40, model_during="claude-x"):
    """28 days of user turns at ``hist_rate`` frustration, then a last day
    at ``short_rate``. Turns and matches are written straight into the
    signal tables the way the WO-58 tick does."""
    turns, matches = [], []
    k = 0

    def _emit(ms, n, rate, model, sid):
        nonlocal k
        for i in range(n):
            k += 1
            eid = f"e{k}"
            turns.append({"event_id": eid, "session_id": sid, "agent_type": runtime,
                          "node_id": "n1", "model": model, "runtime_version": "1.0",
                          "side": "user", "turn_ms": ms + i})
            if i < int(round(n * rate)):
                matches.append({"event_id": eid, "signal": "user_frustration", "session_id": sid,
                                "agent_type": runtime, "node_id": "n1", "model": model,
                                "runtime_version": "1.0", "turn_ms": ms + i,
                                "matcher": "swear", "category": "swear"})
    for d in range(1, hist_days + 1):
        _emit(NOW - _HOUR * 24 - d * _DAY + 1000, hist_turns, hist_rate, "claude-old", f"{runtime}:h{d}")
    _emit(NOW - 2 * _HOUR, short_turns, short_rate, model_during, f"{runtime}:s1")
    store.record_signal_turns(turns, matches)
    store.ingest_session({"session_id": f"{runtime}:s1", "agent_type": "openclaw", "node_id": "n1",
                          "title": "seed", "started_at": "2027-01-01T00:00:00+00:00",
                          "cwd": "/home/me/repo-x"})
    store.flush()


def test_tick_opens_once_then_updates(store):
    _seed_shift(store)
    delivered = []
    s1 = ss.run_shift_tick(store, now_ms=NOW, deliver=delivered.append, node_id="n1")
    assert s1["opened"] == 1 and s1["reopened"] == 0, s1
    assert len(delivered) == 1
    m = delivered[0]
    assert m["metadata"]["signal"] == "user_frustration" and m["metadata"]["runtime"] == "cursor"
    assert m["metadata"]["rate_during"] == 0.25
    assert m["metadata"]["n_before"] == 700 and m["metadata"]["n_during"] == 40
    assert m["metadata"]["rate_before"] == 0.04
    s2 = ss.run_shift_tick(store, now_ms=NOW + 60_000, deliver=delivered.append)
    assert s2["opened"] == 0 and s2["updated"] == 1
    assert len(delivered) == 1, "an open issue is refreshed, never re-delivered"
    issues = store.query_signal_issues(status="open")
    assert len(issues) == 1
    it = issues[0]
    # The second tick's history window slid one minute, so the oldest day
    # may have aged out; the during side and the rate are what is pinned.
    assert it["n_during"] == 40 and it["rate_during"] == 0.25 and 600 <= it["n_before"] <= 700
    assert it["breakdown"]["model"][0]["value"] == "claude-x"
    assert it["breakdown"]["cwd"][0]["value"] == "repo-x"
    assert it["breakdown"]["threshold_source"] in ("floor", "learned", "ceiling")


def test_no_shift_below_min_samples(store):
    _seed_shift(store, short_turns=10)
    s = ss.run_shift_tick(store, now_ms=NOW, deliver=lambda m: None)
    assert s["checked"] >= 1 and s["opened"] == 0
    assert store.query_signal_issues(status="open") == []


def test_resolved_reopens_after_the_window_not_before(store):
    _seed_shift(store)
    delivered = []
    ss.run_shift_tick(store, now_ms=NOW, deliver=delivered.append)
    iid = store.query_signal_issues(status="open")[0]["id"]
    store.set_signal_issue_status(issue_id=iid, status="resolved", now_ms=NOW + 1000)
    # Same shift window, one minute later: stays resolved, nothing sent.
    s = ss.run_shift_tick(store, now_ms=NOW + 60_000, deliver=delivered.append)
    assert s["reopened"] == 0 and len(delivered) == 1
    assert store.query_signal_issues(status="resolved")[0]["id"] == iid
    # The window aged out and the rate is still up: reopen the SAME row.
    later = NOW + ss.SHORT_HOURS * _HOUR + 60_000
    _seed_shift_more(store, later)
    s = ss.run_shift_tick(store, now_ms=later, deliver=delivered.append)
    assert s["reopened"] == 1 and s["opened"] == 0
    assert len(delivered) == 2 and delivered[-1]["summary"].startswith("Reopened: ")
    all_issues = store.query_signal_issues(status="all")
    assert len(all_issues) == 1, "reopen must not duplicate"
    assert all_issues[0]["id"] == iid and all_issues[0]["status"] == "open"
    assert all_issues[0]["reopen_count"] == 1 and all_issues[0]["resolved_at"] is None


def _seed_shift_more(store, now_ms):
    turns, matches = [], []
    for i in range(40):
        eid = f"late{i}"
        turns.append({"event_id": eid, "session_id": "cursor:s2", "agent_type": "cursor",
                      "node_id": "n1", "model": "claude-x", "runtime_version": "1.0",
                      "side": "user", "turn_ms": now_ms - _HOUR + i})
        if i < 10:
            matches.append({"event_id": eid, "signal": "user_frustration", "session_id": "cursor:s2",
                            "agent_type": "cursor", "node_id": "n1", "model": "claude-x",
                            "runtime_version": "1.0", "turn_ms": now_ms - _HOUR + i,
                            "matcher": "swear", "category": "swear"})
    store.record_signal_turns(turns, matches)


def test_ignored_stays_silent_until_the_operator_reopens(store):
    _seed_shift(store)
    delivered = []
    ss.run_shift_tick(store, now_ms=NOW, deliver=delivered.append)
    iid = store.query_signal_issues(status="open")[0]["id"]
    store.set_signal_issue_status(issue_id=iid, status="ignored")
    later = NOW + 2 * ss.SHORT_HOURS * _HOUR
    _seed_shift_more(store, later)
    s = ss.run_shift_tick(store, now_ms=later, deliver=delivered.append)
    assert s["ignored"] == 1 and s["opened"] == 0 and s["reopened"] == 0
    assert len(delivered) == 1
    assert store.query_signal_issues(status="open") == []
    back = store.set_signal_issue_status(issue_id=iid, status="open")
    assert back["status"] == "open" and back["resolved_at"] is None
    assert store.set_signal_issue_status(issue_id=iid, status="bogus") is None
    assert store.set_signal_issue_status(issue_id="nope", status="open") is None


def test_tick_never_raises_on_a_broken_store():
    class Broken:
        def query_signal_shift_inputs(self, **kw):
            raise RuntimeError("boom")
    s = ss.run_shift_tick(Broken(), now_ms=NOW)
    assert s["errors"] == 1 and s["opened"] == 0


# ── routes ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(store, monkeypatch):
    from flask import Flask
    import routes.signals as rs
    monkeypatch.setattr(rs, "_ls_call",
                        lambda method, **kw: getattr(store, method)(**kw))
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(rs.bp_signals)
    return app.test_client()


def test_issue_routes(client, store):
    _seed_shift(store)
    ss.run_shift_tick(store, now_ms=NOW, deliver=lambda m: None)
    r = client.get("/api/signals/issues")
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 1 and body["status"] == "open"
    it = body["issues"][0]
    assert it["headline"].startswith("Frustration on Cursor jumped from 4% to 25%")
    assert "min_samples" in body and body["min_samples"]["short"] == ss.MIN_SHORT
    assert client.get("/api/signals/issues?runtime=claude_code").get_json()["count"] == 0
    assert client.get("/api/signals/issues?runtime=cursor").get_json()["count"] == 1
    assert "wtf" not in r.get_data(as_text=True)

    r = client.post(f"/api/signals/issues/{it['id']}/status", json={"status": "resolved"})
    assert r.status_code == 200 and r.get_json()["issue"]["status"] == "resolved"
    assert client.get("/api/signals/issues").get_json()["count"] == 0
    assert client.get("/api/signals/issues?status=all").get_json()["count"] == 1
    assert client.get("/api/signals/issues?status=resolved").get_json()["count"] == 1
    r = client.post(f"/api/signals/issues/{it['id']}/status", json={"status": "nonsense"})
    assert r.status_code == 400
    assert client.post("/api/signals/issues/nope/status", json={"status": "open"}).status_code == 404
    r = client.post(f"/api/signals/issues/{it['id']}/status", json={"status": "open"},
                    headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


# ── snapshot + daemon wiring ───────────────────────────────────────────────

def test_snapshot_slice_shape_and_no_sessions(store):
    _seed_shift(store)
    ss.run_shift_tick(store, now_ms=NOW, deliver=lambda m: None)
    slice_ = ss.build_snapshot_slice(store)
    assert set(slice_) >= {"issues", "open", "resolved", "ignored", "generated_at"}
    assert slice_["open"] == 1 and slice_["issues"][0]["headline"]
    blob = json.dumps(slice_)
    assert "cursor:s1" not in blob and "wtf" not in blob
    assert ss.build_snapshot_slice(object()) == {}


def test_sync_emits_the_slice_and_runs_the_pass():
    src = open(os.path.join(ROOT, "clawmetry", "sync.py"), encoding="utf-8").read()
    assert '"signalIssues": _signal_issues_slice,' in src
    assert "build_snapshot_slice(" in src
    assert "_signal_shift_pass(store_for_sig, config, state)" in src
    assert "_briefs_mod.start_scheduler(" in src


def test_daemon_allowlist_names_every_store_method():
    from routes.local_query import _DAEMON_METHODS
    for m in ("query_signal_shift_inputs", "query_signal_shift_breakdown", "upsert_signal_issue",
              "get_signal_issue", "query_signal_issues", "set_signal_issue_status",
              "list_briefs", "get_brief", "upsert_brief", "delete_brief", "mark_brief_run"):
        assert m in _DAEMON_METHODS, m


def test_signals_tab_has_issues_and_briefs_surfaces_without_em_dashes():
    tab = open(os.path.join(ROOT, "clawmetry", "templates", "tabs", "signals.html"),
               encoding="utf-8").read()
    for el in ("signals-issues-card", "signals-issues-body", "signals-briefs-card",
               "signals-briefs-body", "signals-brief-form"):
        assert f'id="{el}"' in tab, el
    js = open(os.path.join(ROOT, "clawmetry", "static", "js", "app.js"), encoding="utf-8").read()
    for fn in ("function loadSignalsIssues", "function signalsSetIssueStatus",
               "function loadSignalsBriefs", "function signalsRunBrief", "function signalsEnableDigest"):
        assert fn in js, fn
    sec = js[js.index("Signal shifts: open issues (WO-62)"):]
    assert "—" not in sec and " -- " not in sec and "—" not in tab and " -- " not in tab
    assert "'&runtime=' + encodeURIComponent(rt)" in sec, "issues respect the runtime switcher"
