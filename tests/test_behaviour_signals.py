"""Behaviour Signals (WO-58): matchers, tick, store, routes, alert rule, snapshot.

Requirement b6f32656-7433-4340-9e7f-7f17198283e5 (REQ-SIG-001..005).

What is pinned here, and why each pin exists:

* Matcher precision on fixtures, including the negatives the requirement
  calls out ("kill the process" is not frustration, "not bad" is not
  frustration, "no thanks" is not praise, a technical "I can't find the file"
  is not a refusal). A keyword matcher with no negative fixtures drifts into
  noise the first time someone widens a list.
* Idempotence: re-running the tick over the same rows never double counts
  (REQ-SIG-001). The PK on (event_id, signal) is the mechanism; this proves it.
* No text is stored (REQ-SIG-001): the match table has no text column and
  the sessions endpoint never returns a phrase.
* Coverage inference + adapter override precedence (REQ-SIG-003).
* Route shapes (REQ-SIG-002) through the Flask test client against an
  isolated DuckDB file. Never the live ~/.clawmetry store.
* The ``signal_rate_above`` alert rule (REQ-SIG-004): fires above threshold
  with enough turns, holds below the sample floor, payload carries signal /
  rate / window / runtime / model and nothing textual.
* Snapshot slice keys (REQ-SIG-002): ``signals`` + ``signalsByRuntime``.
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from clawmetry import behaviour_signals as bs  # noqa: E402
from clawmetry import alert_evaluator as ae  # noqa: E402

pytest.importorskip("duckdb")


# ── matchers ──────────────────────────────────────────────────────────────────────

FRUSTRATED = [
    "wtf why did you delete the whole file",
    "this sucks, it still doesn't work",
    "that's not what I asked for",
    "you're wrong, the test was passing before",
    "stop it, stop changing the config",
    "ugh. still broken.",
    "I already told you twice, use the venv",
    "STOP",
    "what the hell happened to our app ??",
    "shit revert to what was earlier",
]
NOT_FRUSTRATED = [
    "kill the process on port 8900 and restart it",
    "not bad, this looks fine",
    "this doesn't suck at all, nice",
    "pretty damn good work",
    "add a stop button to the guard tab so we can stop it later",
    "please write a function that stops the timer",
    "the error says 'no such file'; can you fix it",
    "the useless variable can go, it is never read",
    "kill -9 the stuck worker",
    "we would need stop / kill as well, and be able to stop it from the UI",
]
PRAISE = ["thanks, that worked", "perfect!", "great job on the refactor", "nice",
          "works perfectly now, much better"]
NOT_PRAISE = ["no thanks, leave it", "not perfect yet, the test still fails",
              "this is not great", "kill the process"]
REFUSAL = ["I can't help with that request.", "As an AI language model I cannot do this.",
           "I must decline to write that.", "I won't do that."]
NOT_REFUSAL = ["I can't find the file you mentioned, can you check the path?",
               "I'm unable to reproduce the failure locally, so I added logging.",
               "Here is the fix you asked for."]
LAZY = ["You can implement the remaining endpoints yourself.",
        "The rest is left as an exercise.",
        "I'll leave the rest to you.",
        "# TODO: implement the actual logic here",
        "You will need to manually update the other files."]
NOT_LAZY = ["I implemented every endpoint and ran the tests; all green.",
            "You can run `make test` to confirm.",
            "Done. The TODO in the old file is removed."]
FAILED = ["I was unable to complete the migration.",
          "I couldn't get this working after several attempts.",
          "I give up on this approach; it needs a different design.",
          "Unfortunately, I could not resolve the failing test."]
NOT_FAILED = ["I completed the migration and the tests pass.",
              "I was unable to find a bug in the first file, so I checked the second and fixed it there.",
              "Done."]


@pytest.mark.parametrize("text", FRUSTRATED)
def test_frustration_matches(text):
    assert bs.match_text("user_frustration", text), text


@pytest.mark.parametrize("text", NOT_FRUSTRATED)
def test_frustration_negatives(text):
    """AC: 'kill the process' is not frustration; negation and positive
    context are honoured; an instruction ABOUT stopping is not an order."""
    assert bs.match_text("user_frustration", text) is None, text


@pytest.mark.parametrize("text", PRAISE)
def test_praise_matches(text):
    assert bs.match_text("user_praise", text), text


@pytest.mark.parametrize("text", NOT_PRAISE)
def test_praise_negatives(text):
    assert bs.match_text("user_praise", text) is None, text


@pytest.mark.parametrize("text", REFUSAL)
def test_refusal_matches(text):
    assert bs.match_text("assistant_refusal", text), text


@pytest.mark.parametrize("text", NOT_REFUSAL)
def test_refusal_negatives(text):
    assert bs.match_text("assistant_refusal", text) is None, text


@pytest.mark.parametrize("text", LAZY)
def test_laziness_matches(text):
    assert bs.match_text("assistant_laziness", text), text


@pytest.mark.parametrize("text", NOT_LAZY)
def test_laziness_negatives(text):
    assert bs.match_text("assistant_laziness", text) is None, text


@pytest.mark.parametrize("text", FAILED)
def test_task_failure_matches(text):
    assert bs.match_text("task_failure", text), text


@pytest.mark.parametrize("text", NOT_FAILED)
def test_task_failure_negatives(text):
    assert bs.match_text("task_failure", text) is None, text


def test_code_fences_and_quotes_are_not_scanned():
    assert bs.match_text("user_frustration", "```\nthis sucks\n```\nplease run it") is None
    assert bs.match_text("user_frustration", "> wtf\nok thanks") is None
    assert bs.match_text("user_frustration", "the log says `wtf` in it") is None


def test_front_only_rule_for_corrections_in_long_pastes():
    long = "please look at this incident brief. " + ("x " * 400) + "it is still broken there"
    assert bs.match_text("user_frustration", long) is None
    assert bs.match_text("user_frustration", "still broken after the last change")


def test_every_match_carries_a_category_and_matcher():
    for sig, text in (("user_frustration", "wtf"), ("user_praise", "thanks"),
                      ("assistant_refusal", "As an AI I cannot"),
                      ("assistant_laziness", "left as an exercise"),
                      ("task_failure", "I give up")):
        m = bs.match_text(sig, text)
        assert m and m[0] and m[1], (sig, m)


def test_side_routing_never_crosses():
    """A refusal phrase in a USER turn is not an assistant refusal, and a
    swear in an ASSISTANT turn is not user frustration."""
    assert [s for s, _, _ in bs.match_turn("user", "I can't help with that")] == []
    assert [s for s, _, _ in bs.match_turn("assistant", "wtf this sucks")] == []


def test_retry_jaccard():
    prev = bs.tokens_of("please fix the failing test in routes/usage.py now")
    assert bs.retry_match(prev, bs.tokens_of("please fix the failing test in routes/usage.py now"))
    assert bs.retry_match(prev, bs.tokens_of("please fix the failing test in routes/usage.py"))
    assert bs.retry_match(prev, bs.tokens_of("now write the docs")) is None
    assert bs.retry_match(bs.tokens_of("ok"), bs.tokens_of("ok")) is None, "acks are not retries"
    assert bs.retry_match(None, bs.tokens_of("anything at all here")) is None


# ── turn classification across both dialects ───────────────────────────────────────────

def _row(i, sid, role=None, text="", et="message", ts=None, model="claude-x",
         created=None, extra=None):
    data = {"role": role, "content": text}
    if extra:
        data.update(extra)
    return {
        "id": f"e{i}", "agent_type": "openclaw", "node_id": "n1", "agent_id": "main",
        "session_id": sid, "workspace_id": "", "event_type": et,
        "ts": ts or "2026-09-03T10:00:00+00:00", "data": json.dumps(data),
        "cost_usd": 0.0, "token_count": 0, "model": model,
        "created_at": created or int(time.time() * 1000),
    }


def test_classify_family_and_v3_dialects():
    side, text, model, ver = bs.classify_turn(_row(1, "claude_code:a", "user", "hi"))
    assert (side, text, model) == ("user", "hi", "claude-x")
    v3 = _row(2, "abc", None, "", et="prompt.submitted", model=None,
               extra={"finalPromptText": "why did you do that"})
    assert bs.classify_turn(v3)[0] == "user"
    v3a = _row(3, "abc", None, "", et="model.completed", model=None,
               extra={"completionText": "I can't help with that", "modelId": "m1"})
    side, text, model, _ = bs.classify_turn(v3a)
    assert (side, model) == ("assistant", "m1")
    assert bs.classify_turn(_row(4, "x", "tool", "output")) is None
    assert bs.classify_turn(_row(5, "x", "user", "")) is None


def test_injected_user_turns_are_not_human():
    for t in ("<task-notification>done</task-notification>", "[Image: original]",
              "[Request interrupted by user]", "Stop hook feedback: keep going",
              "A session-scoped Stop hook is now active with condition: wtf"):
        assert not bs.is_human_prompt(t), t
    assert bs.is_human_prompt("wtf why")


def test_runtime_resolves_from_prefix_not_agent_type():
    assert bs.resolve_runtime("claude_code:123", {}, "openclaw") == "claude_code"
    assert bs.resolve_runtime("plain-uuid", {"_runtime": "hermes"}, "openclaw") == "hermes"
    assert bs.resolve_runtime("plain-uuid", {}, "") == "openclaw"


def test_evaluate_rows_records_no_text():
    rows = [_row(1, "claude_code:s1", "user", "wtf this sucks"),
            _row(2, "claude_code:s1", "assistant", "I give up."),
            _row(3, "claude_code:s1", "user", "wtf this sucks")]
    turns, matches = bs.evaluate_rows(rows, {})
    assert len(turns) == 3
    sigs = sorted((m["event_id"], m["signal"]) for m in matches)
    assert ("e1", "user_frustration") in sigs
    assert ("e2", "task_failure") in sigs
    assert ("e3", "user_retry") in sigs
    for m in matches:
        assert set(m) <= {"session_id", "agent_type", "node_id", "model",
                          "runtime_version", "turn_ts", "turn_ms", "event_id",
                          "side", "signal", "matcher", "category"}
        assert "wtf" not in json.dumps(m)


# ── store + tick (isolated DuckDB) ────────────────────────────────────────────────────

@pytest.fixture()
def store(tmp_path, monkeypatch):
    db = tmp_path / "signals.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    from clawmetry import local_store as ls
    from pathlib import Path
    monkeypatch.setattr(ls, "DB_PATH", Path(str(db)))
    monkeypatch.setattr(ls, "_writer_owner", True)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass
    s = ls.get_store()
    yield s
    try:
        s.stop()
    except Exception:
        pass
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass


def _seed(store, n_frustrated=3, n_calm=5, sid="claude_code:s1", ts=None):
    ts = ts or time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    evs = []
    i = 0
    for _ in range(n_frustrated):
        i += 1
        evs.append(_row(i, sid, "user", f"wtf number {i} this sucks", ts=ts))
        i += 1
        evs.append(_row(i, sid, "assistant", f"Fixed {i}.", ts=ts))
    for _ in range(n_calm):
        i += 1
        evs.append(_row(i, sid, "user", f"please add test {i}", ts=ts))
        i += 1
        evs.append(_row(i, sid, "assistant", f"Added {i}.", ts=ts))
    for e in evs:
        e["data"] = json.loads(e["data"])
        store.ingest(e)
    store.ingest_session({"session_id": sid, "agent_type": "openclaw", "node_id": "n1",
                          "title": "seed", "started_at": ts, "cost_usd": 1.5})
    # flush synchronously
    for _ in range(50):
        try:
            if store._conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] >= len(evs):
                break
        except Exception:
            pass
        time.sleep(0.05)
    return evs


def test_tick_is_idempotent_and_tables_hold_no_text(store):
    _seed(store)
    state: dict = {}
    n1 = bs.run_tick(store, state)
    assert n1 >= 3
    counts = store._conn.execute("SELECT COUNT(*) FROM signal_matches").fetchone()[0]
    turns = store._conn.execute("SELECT COUNT(*) FROM signal_turns").fetchone()[0]
    assert turns == 16
    # Second pass over the same rows: watermark advanced, nothing new.
    n2 = bs.run_tick(store, state)
    assert n2 == 0
    assert store._conn.execute("SELECT COUNT(*) FROM signal_matches").fetchone()[0] == counts
    # Forced re-evaluation of the same rows (watermark reset): PK dedupes.
    state["behaviour_signals"]["created_at"] = 0
    state["behaviour_signals"]["after_id"] = None
    bs.run_tick(store, state)
    assert store._conn.execute("SELECT COUNT(*) FROM signal_matches").fetchone()[0] == counts
    assert store._conn.execute("SELECT COUNT(*) FROM signal_turns").fetchone()[0] == 16
    cols = {r[0] for r in store._conn.execute("DESCRIBE signal_matches").fetchall()}
    assert cols == {"event_id", "signal", "session_id", "agent_type", "node_id", "model",
                    "runtime_version", "turn_ts", "turn_ms", "matcher", "category",
                    "created_at"}, "no text column, ever"


def test_grouped_rates_and_coverage(store):
    _seed(store)
    bs.run_tick(store, {})
    rep = bs.full_report(store, 7, None)
    fr = rep["signals"]["user_frustration"]
    assert fr["eligible"] == 8 and fr["count"] == 3
    assert fr["rate"] == pytest.approx(0.375)
    assert fr["by_model"]["claude-x"]["count"] == 3
    assert "unknown" in fr["by_runtime_version"]
    assert fr["by_runtime"]["claude_code"]["eligible"] == 8
    assert len(fr["per_day"]) == 7
    assert rep["coverage"]["claude_code"]["state"] == "user_text+assistant_text"
    assert rep["headline"]["text"]
    scoped = bs.full_report(store, 7, "claude_code")
    assert scoped["signals"]["user_frustration"]["count"] == 3
    other = bs.full_report(store, 7, "codex")
    assert other["signals"]["user_frustration"]["eligible"] == 0
    assert other["runtime_coverage"]["state"] == "unknown"


def test_coverage_inference_and_adapter_override():
    inferred = {"claude_code": {"user_turns": 5, "assistant_turns": 9},
                "cursor": {"user_turns": 0, "assistant_turns": 4},
                "devin": {"user_turns": 0, "assistant_turns": 0}}
    cov = bs.shape_coverage(inferred, {"cursor": {"user_text": False, "assistant_text": False}})
    assert cov["claude_code"]["state"] == "user_text+assistant_text"
    assert cov["cursor"]["state"] == "none" and cov["cursor"]["source"] == "adapter"
    assert cov["devin"]["state"] == "none" and cov["devin"]["source"] == "inferred"


def test_headline_plain_words_no_em_dash():
    rates = bs.shape_rates(
        [{"agent_type": "cursor", "side": "user", "model": "m", "runtime_version": None,
          "day": d, "n": 10} for d in range(20000, 20014)],
        [{"agent_type": "cursor", "signal": "user_frustration", "model": "m",
          "runtime_version": None, "day": d, "n": (4 if d >= 20007 else 1)}
         for d in range(20000, 20014)],
        window_days=7, now_ms=20013 * 86400 * 1000 + 1000, runtime="cursor")
    h = bs.headline(rates)
    assert h["signal"] == "user_frustration" and h["direction"] == "up"
    assert "Frustration is up on Cursor" in h["text"]
    assert "—" not in h["text"] and " -- " not in h["text"]


def test_sessions_query_lists_sessions_not_phrases(store):
    _seed(store)
    bs.run_tick(store, {})
    rows = store.query_signal_sessions(signal="user_frustration",
                                       since_ms=int(time.time() * 1000) - 7 * 86400000)
    assert rows and rows[0]["session_id"] == "claude_code:s1"
    assert rows[0]["matches"] == 3 and rows[0]["runtime"] == "claude_code"
    assert rows[0]["cost_usd"] == 1.5
    assert "wtf" not in json.dumps(rows)


# ── routes ───────────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(store):
    """A bare Flask app with only the signals blueprint, the way
    ``test_guard_control_route.py`` does it: no auth gate, no daemon, reads
    fall through ``_ls_call`` to the isolated store above."""
    from flask import Flask
    from routes.signals import bp_signals
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(bp_signals)
    return app.test_client()


def test_routes_shapes(client, store):
    _seed(store)
    bs.run_tick(store, {})
    r = client.get("/api/signals?window=7d")
    assert r.status_code == 200
    body = r.get_json()
    for k in ("window", "signals", "coverage", "headline", "eligible_turns", "store"):
        assert k in body, k
    assert set(body["signals"]) == set(bs.SIGNALS)
    s = body["signals"]["user_frustration"]
    for k in ("rate", "count", "eligible", "trend", "per_day", "by_model", "by_runtime_version"):
        assert k in s, k
    assert body["window"] == "7d"
    r = client.get("/api/signals?window=bogus&runtime=claude_code")
    assert r.status_code == 200 and r.get_json()["window"] == "7d"
    assert r.get_json()["runtime"] == "claude_code"
    r = client.get("/api/signals/coverage")
    assert r.status_code == 200 and "claude_code" in r.get_json()["coverage"]
    r = client.get("/api/signals/user_frustration/sessions?window=7d")
    assert r.status_code == 200
    sess = r.get_json()
    assert sess["count"] >= 1 and sess["sessions"][0]["session_id"] == "claude_code:s1"
    assert "wtf" not in r.get_data(as_text=True)
    assert client.get("/api/signals/not_a_signal/sessions").status_code == 404


# ── alert rule ────────────────────────────────────────────────────────────────────

def _rule(threshold=10, signal="user_frustration", runtime=None, min_turns=None):
    cond = {"alert_type": "signal_rate_above", "threshold_value": threshold,
            "signal": signal, "window_minutes": 60}
    if runtime:
        cond["runtime"] = runtime
    if min_turns is not None:
        cond["min_turns"] = min_turns
    return {"id": "r1", "name": "frustration", "enabled": True, "condition_json": cond}


def test_signal_rate_rule_fires_and_holds():
    win = {"signal": "user_frustration", "rate": 0.25, "matches": 5, "turns": 20,
           "window_minutes": 60, "runtime": "all", "top_model": "claude-x"}
    out = ae.evaluate([_rule()], [], {}, signals={"r1": win})
    assert len(out) == 1
    meta = out[0]["metadata"]
    for k in ("signal", "rate", "window", "runtime", "model"):
        assert k in meta, k
    assert meta["signal"] == "user_frustration" and meta["rate"] == 0.25
    assert "wtf" not in json.dumps(out[0])
    # Below the sample floor: hold.
    low = dict(win, turns=3, matches=1, rate=0.33)
    assert ae.evaluate([_rule(min_turns=5)], [], {}, signals={"r1": low}) == []
    # Below threshold: hold.
    calm = dict(win, rate=0.05)
    assert ae.evaluate([_rule()], [], {}, signals={"r1": calm}) == []
    # No slice fetched: hold, never crash.
    assert ae.evaluate([_rule()], [], {}) == []
    # Scoped rule reads only its runtime's slice.
    assert ae.evaluate([_rule(runtime="cursor")], [], {}, signals={"r1": win}) == []
    assert len(ae.evaluate([_rule(runtime="cursor")], [], {},
                           signals_by_runtime={"cursor": {"r1": win}})) == 1


def test_signal_rule_fields_accept_percent_and_fraction():
    assert ae.signal_rule_fields({"threshold": 20, "condition": {"signal": "user_praise"}})["threshold"] == 0.2
    assert ae.signal_rule_fields({"threshold": 0.2, "condition": {"signal": "user_praise"}})["threshold"] == 0.2
    assert ae.signal_rule_fields({"condition": {}})["min_turns"] == ae.DEFAULT_SIGNAL_MIN_TURNS


def test_alert_route_registers_signal_rule_type():
    from routes import alerts as ra
    assert "signal_rate_above" in ra._EVALUATOR_ONLY
    assert "signal_rate_above" in ae.SIGNAL_RULE_TYPES
    assert ae._LEGACY_ALERT_TYPE_MAP["signal_rate_above"] == "signal_rate_above"


def test_store_rate_window(store):
    _seed(store)
    bs.run_tick(store, {})
    w = store.query_signal_rate_window(signal="user_frustration", window_minutes=60)
    assert w["turns"] == 8 and w["matches"] == 3 and w["rate"] == pytest.approx(0.375)
    assert store.query_signal_rate_window(signal="nope", window_minutes=60) == {}


# ── snapshot slice ──────────────────────────────────────────────────────────────────

def test_snapshot_slices_keys_and_no_sessions(store):
    _seed(store)
    bs.run_tick(store, {})
    node, per_rt = bs.build_snapshot_slices(store)
    assert set(node) == {"1d", "7d", "30d", "coverage"}
    assert set(per_rt) == {"claude_code"} and set(per_rt["claude_code"]) == {"1d", "7d", "30d"}
    assert node["7d"]["signals"]["user_frustration"]["count"] == 3
    assert per_rt["claude_code"]["7d"]["signals"]["user_frustration"]["count"] == 3
    assert per_rt["claude_code"]["7d"]["runtime_coverage"]["state"] == "user_text+assistant_text"
    blob = json.dumps({"signals": node, "signalsByRuntime": per_rt})
    assert "claude_code:s1" not in blob, "no per-session data rides the snapshot"
    assert "wtf" not in blob
    assert len(blob) < 200_000


def test_sync_snapshot_emits_both_keys():
    src = open(os.path.join(ROOT, "clawmetry", "sync.py"), encoding="utf-8").read()
    assert '"signals": _signals_slice,' in src
    assert '"signalsByRuntime": _signals_by_rt,' in src
    assert "build_snapshot_slices" in src


def test_daemon_allowlist_names_every_store_method():
    from routes.local_query import _DAEMON_METHODS
    for m in ("record_signal_turns", "query_signal_grouped", "query_signal_coverage",
              "query_signal_sessions", "query_signal_rate_window"):
        assert m in _DAEMON_METHODS, m
