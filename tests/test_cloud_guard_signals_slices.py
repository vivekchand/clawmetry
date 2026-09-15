"""The hosted Guard and Signals tabs render from slices the daemon builds.

Field report 2026-09-14: on app.clawmetry.com the Guard tab said "No sessions
running right now" while the same node's local dashboard listed 39, and a
Signals "Sessions" click said "No sessions matched in this window" beside a
rate that counted two. The cloud container has no store, so both needed a
snapshot slice, and both renderers read an unreadable list as an empty one.

These pin the daemon half: ``build_guard_sessions_body`` answers from the
store handle it is given (the daemon's own, never a proxy round-trip into
itself), and ``build_session_slice`` lists sessions per runtime, window and
signal for exactly the signals that matched.
"""
import json
from pathlib import Path

import routes.guard as guard
from clawmetry import behaviour_signals as bs

ROOT = Path(__file__).resolve().parent.parent


def test_guard_builder_uses_the_call_it_is_given(monkeypatch):
    def _proxy(*a, **k):
        raise AssertionError("the daemon must not go through _ls_call")

    monkeypatch.setattr(guard, "_ls_call", _proxy)
    monkeypatch.setattr(guard, "_live_only_rows", lambda rows: [])
    monkeypatch.setattr(guard, "_session_runtime", lambda sid, a: "claude_code")
    monkeypatch.setattr(guard, "_runtime_supports_signals",
                        lambda rt, sid, cwd: {"controllable": True,
                                              "actions": ["pause", "stop", "kill"]})
    seen = []

    def _call(method, **kw):
        seen.append(method)
        if method == "query_sessions_table":
            return [{"session_id": "claude_code:abc", "status": "running",
                     "title": "t", "cost_usd": 2.5, "metadata": {}}]
        return []

    body = guard.build_guard_sessions_body(50, call=_call)
    assert seen == ["query_sessions_table", "query_recent_loop_signals"]
    assert body["count"] == 1 and body["flagged"] == 0
    row = body["sessions"][0]
    assert row["session_id"] == "claude_code:abc"
    assert row["controllable"] is True
    json.dumps(body)  # the slice must serialise


class _Store:
    def __init__(self):
        self.calls = []

    def query_signal_sessions(self, *, signal, since_ms, runtime=None, limit=50):
        self.calls.append((signal, runtime))
        return [{"session_id": "claude_code:s1", "runtime": "claude_code",
                 "model": "m", "matches": 2, "last_match_ts": None,
                 "title": "Explainer video", "started": None, "cost_usd": 1.0}]


def _rates(counts):
    return {"signals": {name: {"count": n} for name, n in counts.items()}}


def test_signal_session_slice_lists_only_signals_that_matched():
    node = {"7d": _rates({"user_praise": 2, "user_frustration": 0}), "coverage": {}}
    per_rt = {"claude_code": {"7d": _rates({"user_praise": 2})},
              "codex": {"7d": _rates({"user_praise": 0})}}
    store = _Store()
    out = bs.build_session_slice(store, node, per_rt)

    by = out["byRuntime"]
    assert by["all"]["7d"]["user_praise"][0]["session_id"] == "claude_code:s1"
    assert by["claude_code"]["7d"]["user_praise"][0]["matches"] == 2
    assert "user_frustration" not in by["all"].get("7d", {})
    assert by["codex"] == {}, "a runtime with no matches gets its own empty bucket"
    assert sorted(store.calls, key=str) == [("user_praise", "claude_code"),
                                            ("user_praise", None)]
    json.dumps(out)


def test_signal_session_slice_never_raises():
    class Broken:
        def query_signal_sessions(self, **kw):
            raise RuntimeError("store gone")

    assert bs.build_session_slice(Broken(), {"7d": _rates({"user_praise": 1})}, {}) == {}


def test_snapshot_payload_carries_both_slices():
    src = (ROOT / "clawmetry" / "sync.py").read_text(encoding="utf-8")
    assert '"guardSessions": _guard_sessions_slice' in src
    assert '"signalSessions": _signal_sessions_slice' in src


def test_renderers_show_the_reason_instead_of_a_false_empty():
    js = (ROOT / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    guard_fn = js[js.index("function loadGuardSessions()"):]
    guard_fn = guard_fn[:guard_fn.index("\n}\n")]
    assert "d.available === false && d.reason" in guard_fn
    sig_fn = js[js.index("'/api/signals/' + encodeURIComponent(name) + '/sessions"):]
    sig_fn = sig_fn[:sig_fn.index("html += '</tbody></table>'")]
    assert "d.available === false && d.reason" in sig_fn
