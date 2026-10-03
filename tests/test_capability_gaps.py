"""Opt-in capability-gap export (#5412).

Pins the contract end to end without a daemon process:

* the classifier: one fixture per emitted code, precedence between codes,
  successful results and plain text turns are never gaps, declared-only
  codes are never emitted, and a record carries exactly the fixed fields
  with a marker from our own tables, never a slice of the output;
* the exporter: nothing is written while ``CLAWMETRY_CAPGAP_EXPORT_DIR`` is
  unset, append-only JSONL when it is set, dedup inside a process and
  across a restart through the seen file, 0600 files;
* the daemon hook: ``_emit_detector_incidents`` writes the file only when
  the variable is set and leaves the detector pass unchanged otherwise;
* the read route: records, counts and the contract from store rows through
  ``_ls_call``, honest ``store_available: false`` when the store is away.
"""
from __future__ import annotations

import json
import os
import stat
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import capability_gaps as cg  # noqa: E402

ENV = cg.EXPORT_DIR_ENV


def _ev(eid, et, data, ts="2026-10-02T23:00:00Z", sid="codex:s1"):
    return {"id": eid, "event_type": et, "ts": ts, "session_id": sid, "data": data}


@pytest.fixture(autouse=True)
def _no_export_env(monkeypatch):
    monkeypatch.delenv(ENV, raising=False)


# ── classifier ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("data, code, marker", [
    ({"tool": "Bash", "is_error": True, "output": "zsh: command not found: terraform"},
     "E01_NO_MATCH", "command not found"),
    ({"tool": "mcp__x", "error": {"type": "tool_not_found", "message": "no tool x"}},
     "E01_NO_MATCH", "error_type:tool_not_found"),
    ({"tool": "Bash", "exit_code": 1, "stderr": "EACCES: permission denied, open '/etc/x'"},
     "E02_NO_ACCESS", "permission denied"),
    ({"tool": "Bash", "is_error": True,
      "content": [{"type": "text", "text": "Permission to use Bash has been denied."}]},
     "E02_NO_ACCESS", "has been denied"),
    ({"tool": "WebFetch", "is_error": True, "status": 403, "output": "nope"},
     "E02_NO_ACCESS", "status:403"),
    ({"tool": "WebFetch", "is_error": True, "content": "Request timed out after 30s"},
     "E05_CAPACITY_GAP", "timed out"),
    ({"tool": "Bash", "is_error": True, "output": "curl: (22) HTTP error 429"},
     "E05_CAPACITY_GAP", "429"),
    ({"tool": "Bash", "is_error": True, "output": "Daily budget reached. Halting agent."},
     "E08_CAPITAL_NEED", "budget reached"),
])
def test_tool_result_failures_map_to_the_four_emitted_codes(data, code, marker):
    recs = cg.classify_events([_ev("e1", "tool_result", data)], runtime="codex")
    assert len(recs) == 1
    rec = recs[0]
    assert rec["code"] == code
    assert rec["marker"] == marker
    assert rec["source"] == "tool_result"
    assert rec["runtime"] == "codex"
    assert rec["session_id"] == "codex:s1"
    assert rec["event_id"] == "e1"


@pytest.mark.parametrize("data, code, marker, status", [
    ({"error": {"type": "rate_limit_error", "message": "Too many requests"}, "status": 429},
     "E05_CAPACITY_GAP", "status:429", 429),
    ({"error": {"type": "overloaded_error", "message": "Overloaded"}},
     "E05_CAPACITY_GAP", "error_type:overloaded_error", None),
    ({"error": {"type": "authentication_error", "message": "invalid x-api-key"}, "status": 401},
     "E02_NO_ACCESS", "status:401", 401),
    ({"error": {"type": "budget_exceeded", "message": "Daily budget reached."},
      "code": "BUDGET_EXCEEDED"},
     "E08_CAPITAL_NEED", "error_type:budget_exceeded", None),
    ({"error": {"type": "invalid_request_error",
                "message": "Your credit balance is too low to access the API."}},
     "E08_CAPITAL_NEED", "credit balance is too low", None),
    ({"error": {"type": "not_found_error", "message": "model: claude-9 not found"}, "status": 404},
     "E01_NO_MATCH", "status:404", 404),
])
def test_api_error_rows_map_with_status_and_error_type(data, code, marker, status):
    recs = cg.classify_events([_ev("e2", "api.error", data)])
    assert [(r["code"], r["marker"], r["http_status"], r["source"]) for r in recs] == [
        (code, marker, status, "api_error")]


def test_budget_wins_over_capacity_wins_over_access():
    # A 402 that also says "rate limit" is a billing boundary first.
    data = {"error": {"type": "rate_limit_error", "message": "payment required, rate limit"},
            "status": 402}
    (rec,) = cg.classify_events([_ev("p", "error", data)])
    assert rec["code"] == "E08_CAPITAL_NEED"
    data = {"tool": "Bash", "is_error": True,
            "output": "permission denied: request timed out"}
    (rec,) = cg.classify_events([_ev("q", "tool_result", data)])
    assert rec["code"] == "E05_CAPACITY_GAP"


def test_successful_results_and_text_turns_are_never_gaps():
    evs = [
        # A success that mentions a 429 in its output is not a gap.
        _ev("ok", "tool_result", {"tool": "Bash", "is_error": False,
                                  "output": "HTTP 429 seen in logs, retried fine"}),
        # An assistant text turn is never classified, whatever it says.
        _ev("txt", "assistant", {"message": {"content": [
            {"type": "text", "text": "permission denied, command not found, 429"}]}}),
        # A plain failure with no mapped marker is a failure, not a gap.
        _ev("plain", "tool_result", {"tool": "Read", "is_error": True,
                                     "content": "File does not exist."}),
        # Junk never raises.
        {"id": "junk", "event_type": "tool_result", "data": "{not json"},
        "not a dict",
    ]
    assert cg.classify_events(evs) == []


def test_declared_only_codes_are_never_emitted_and_contract_says_so():
    desc = cg.describe()
    assert set(desc["mapped_codes"]) == set(cg.MAPPED_CODES)
    assert set(desc["declared_only_codes"]) == {
        "E03_NO_FIT", "E04_NEED_ALTERNATIVE", "E06_RIGHTS_GAP", "E07_EVIDENCE_GAP"}
    assert set(desc["taxonomy"]) == set(cg.TAXONOMY) and len(cg.TAXONOMY) == 8
    emitted = {code for code, _m, _s, _e in cg._RULES}
    assert emitted == set(cg.MAPPED_CODES)
    assert desc["export"]["enabled"] is False and desc["export"]["path"] is None


def test_record_has_only_the_fixed_fields_and_no_content():
    secret_output = "Traceback: KeyError 'sk-ant-SECRET'; permission denied for /Users/me/x"
    (rec,) = cg.classify_events([_ev("r", "tool_result", {
        "tool": "Bash" * 100, "is_error": True, "output": secret_output,
        "args": {"cmd": "cat ~/.aws/credentials"}})])
    assert tuple(sorted(rec)) == tuple(sorted(cg.RECORD_FIELDS))
    assert rec["v"] == cg.RECORD_VERSION and rec["taxonomy"] == "MIX-E01-E08"
    flat = json.dumps(rec)
    assert "SECRET" not in flat and "Traceback" not in flat and "credentials" not in flat
    assert rec["marker"] in cg.E02_MARKERS
    assert len(rec["tool"]) == 120


def test_denied_approvals_are_e02_and_other_decisions_are_not():
    rows = [
        {"id": "a1", "decision": "denied", "requestor_session_id": "cc:1", "action": "Bash",
         "created_at": "2026-10-02T22:00:00Z", "args": {"cmd": "rm -rf /"}},
        {"id": "a2", "decision": "approved", "requestor_session_id": "cc:1", "action": "Bash"},
        {"id": "a3", "status": "pending", "requestor_session_id": "cc:2", "action": "Edit"},
    ]
    recs = cg.classify_approvals(rows)
    assert [(r["event_id"], r["code"], r["source"], r["marker"], r["tool"]) for r in recs] == [
        ("a1", "E02_NO_ACCESS", "approval", "approval:denied", "Bash")]
    assert "rm -rf" not in json.dumps(recs)


# ── exporter ─────────────────────────────────────────────────────────────────

def test_exporter_is_none_when_env_unset_and_writes_nothing(tmp_path, monkeypatch):
    assert cg.Exporter.from_env() is None
    assert cg.export_enabled() is False
    monkeypatch.setenv(ENV, "   ")
    assert cg.Exporter.from_env() is None
    assert list(tmp_path.iterdir()) == []


def test_exporter_appends_jsonl_dedups_and_survives_restart(tmp_path, monkeypatch):
    out = tmp_path / "gaps"
    monkeypatch.setenv(ENV, str(out))
    exp = cg.Exporter.from_env()
    assert exp is not None and exp.directory == str(out)
    evs = [
        _ev("e1", "tool_result", {"tool": "Bash", "is_error": True, "output": "command not found"}),
        _ev("e2", "api.error", {"error": {"type": "rate_limit_error"}, "status": 429}),
    ]
    assert exp.observe_events("codex:s1", "codex", evs) == 2
    assert exp.observe_events("codex:s1", "codex", evs) == 0, "same events, same tick"
    assert exp.flush() == 2
    assert exp.flush() == 0

    path = out / cg.EXPORT_FILENAME
    lines = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]
    assert [l["code"] for l in lines] == ["E01_NO_MATCH", "E05_CAPACITY_GAP"]
    assert all(tuple(sorted(l)) == tuple(sorted(cg.RECORD_FIELDS)) for l in lines)
    if os.name != "nt":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert stat.S_IMODE((out / cg.SEEN_FILENAME).stat().st_mode) == 0o600

    # A fresh exporter (daemon restart) replays the detector window and
    # must not append the same records again.
    again = cg.Exporter.from_env()
    assert again.observe_events("codex:s1", "codex", evs) == 0
    assert again.flush() == 0
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2

    # A new failure appends; the file is never truncated.
    evs.append(_ev("e3", "error", {"error": {"type": "budget_exceeded"}}))
    assert again.observe_events("codex:s1", "codex", evs) == 1
    assert again.flush() == 1
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3 and json.loads(lines[-1])["code"] == "E08_CAPITAL_NEED"


def test_exporter_ignores_records_without_an_event_id(tmp_path, monkeypatch):
    monkeypatch.setenv(ENV, str(tmp_path))
    exp = cg.Exporter.from_env()
    assert exp.observe_events("s", "codex", [
        {"event_type": "tool_result", "data": {"is_error": True, "output": "command not found"}}
    ]) == 0
    assert exp.flush() == 0
    assert not (tmp_path / cg.EXPORT_FILENAME).exists()


def test_exporter_write_failure_keeps_the_queue(tmp_path, monkeypatch):
    blocker = tmp_path / "file-not-dir"
    blocker.write_text("x")
    monkeypatch.setenv(ENV, str(blocker))
    exp = cg.Exporter.from_env()
    exp.observe_events("s", "codex", [
        _ev("e1", "tool_result", {"is_error": True, "output": "command not found"})])
    assert exp.flush() == 0
    assert len(exp._pending) == 1, "nothing is dropped on a failed write"


# ── daemon hook ──────────────────────────────────────────────────────────────

class _FakeStore:
    def __init__(self, sessions, events_by_sid, denied=()):
        self._sessions = sessions
        self._events = events_by_sid
        self._denied = list(denied)
        self.loop_signals: list = []

    def query_sessions_table(self, *, agent_type=None, limit=200):
        return list(self._sessions)[:limit]

    def query_events(self, *, session_id=None, limit=500, **kw):
        return list(reversed(self._events.get(session_id, [])))[:limit]

    def query_approvals(self, *, status=None, limit=200, **kw):
        return [r for r in self._denied if status in (None, r.get("decision"))][:limit]

    def ingest_loop_signal(self, **kw):
        self.loop_signals.append(kw)

    def list_node_settings(self):
        return {}


def _active(sid):
    from datetime import datetime
    now = datetime.now().isoformat()
    return {"session_id": sid, "status": "active", "ended_at": None,
            "started_at": now, "last_active_at": now}


def _fake_store():
    sid = "codex:gaps"
    chrono = [
        _ev("c1", "tool_call", {"tool": "Bash", "args": {"cmd": "terraform plan"}},
            ts="2026-10-02T23:00:00Z", sid=sid),
        _ev("c2", "tool_result", {"tool": "Bash", "is_error": True,
                                  "output": "zsh: command not found: terraform"},
            ts="2026-10-02T23:00:01Z", sid=sid),
        _ev("c3", "api.error", {"error": {"type": "rate_limit_error"}, "status": 429},
            ts="2026-10-02T23:00:02Z", sid=sid),
    ]
    denied = [{"id": "ap1", "decision": "denied", "requestor_session_id": sid,
               "action": "Bash", "created_at": "2026-10-02T23:00:03Z"}]
    return _FakeStore([_active(sid)], {sid: chrono}, denied)


def test_detector_pass_exports_only_when_the_env_is_set(tmp_path, monkeypatch):
    import clawmetry.sync as sync

    store = _fake_store()
    sync._emit_detector_incidents(store, {})
    assert list(tmp_path.iterdir()) == [], "unset env: nothing is written anywhere"

    out = tmp_path / "export"
    monkeypatch.setenv(ENV, str(out))
    sync._emit_detector_incidents(store, {})
    path = out / cg.EXPORT_FILENAME
    assert path.exists()
    lines = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]
    assert sorted((l["code"], l["event_id"], l["source"]) for l in lines) == [
        ("E01_NO_MATCH", "c2", "tool_result"),
        ("E02_NO_ACCESS", "ap1", "approval"),
        ("E05_CAPACITY_GAP", "c3", "api_error"),
    ]
    # The next tick sees the same window and appends nothing.
    sync._emit_detector_incidents(store, {})
    assert len(path.read_text(encoding="utf-8").splitlines()) == 3


def test_detector_pass_survives_an_unwritable_export_dir(tmp_path, monkeypatch):
    import clawmetry.sync as sync

    blocker = tmp_path / "not-a-dir"
    blocker.write_text("x")
    monkeypatch.setenv(ENV, str(blocker))
    # Must not raise into the daemon loop.
    sync._emit_detector_incidents(_fake_store(), {})


# ── read route ───────────────────────────────────────────────────────────────

@pytest.fixture
def client(monkeypatch):
    flask = pytest.importorskip("flask")
    import routes.capability_gaps as rc

    calls: list = []
    rows = [
        _ev("e1", "tool_result", {"tool": "Bash", "is_error": True, "output": "command not found"},
            ts="2026-10-02T23:00:01Z", sid="codex:s1"),
        _ev("e2", "api.error", {"error": {"type": "rate_limit_error"}, "status": 429},
            ts="2026-10-02T23:00:02Z", sid="claude_code:s2"),
        _ev("e3", "tool_result", {"tool": "Read", "is_error": False, "output": "ok"},
            ts="2026-10-02T23:00:03Z", sid="codex:s1"),
    ]

    def fake_ls_call(name, **kw):
        calls.append((name, kw))
        if name != "query_events":
            return None
        out = rows
        if kw.get("session_id"):
            out = [r for r in out if r["session_id"] == kw["session_id"]]
        return list(out)

    monkeypatch.setattr(rc, "_ls_call", fake_ls_call)
    app = flask.Flask("t")
    app.register_blueprint(rc.bp_capability_gaps)
    c = app.test_client()
    c.calls = calls
    return c


def test_route_returns_records_counts_and_contract(client):
    d = client.get("/api/capability-gaps?window=1h").get_json()
    assert d["count"] == 2 and d["_source"] == "local_store"
    assert d["store_available"] is True and d["truncated"] is False
    assert [g["code"] for g in d["gaps"]] == ["E05_CAPACITY_GAP", "E01_NO_MATCH"], "newest first"
    assert d["by_code"] == {"E05_CAPACITY_GAP": 1, "E01_NO_MATCH": 1}
    assert d["window_secs"] == 3600 and d["scanned_rows"] == 3
    assert d["mapped_codes"] == list(cg.MAPPED_CODES)
    assert set(d["taxonomy"]) == set(cg.TAXONOMY)
    assert d["export"]["enabled"] is False
    name, kw = client.calls[0]
    assert name == "query_events" and kw["exclude_daemon"] is True
    assert "since" in kw and kw["limit"] == 5000


def test_route_filters_by_session_code_and_limit(client):
    d = client.get("/api/capability-gaps?session=codex:s1").get_json()
    assert [g["event_id"] for g in d["gaps"]] == ["e1"]
    assert client.calls[-1][1]["session_id"] == "codex:s1"
    assert "since" not in client.calls[-1][1], "one session is read whole"
    d = client.get("/api/capability-gaps?code=e05_capacity_gap").get_json()
    assert [g["code"] for g in d["gaps"]] == ["E05_CAPACITY_GAP"]
    d = client.get("/api/capability-gaps?limit=1").get_json()
    assert d["count"] == 1 and d["truncated"] is True
    d = client.get("/api/capability-gaps?runtime=codex").get_json()
    assert client.calls[-1][1]["runtime"] == "codex"
    assert all(g["runtime"] == "codex" for g in d["gaps"])


def test_route_is_honest_when_the_store_is_away(client, monkeypatch):
    import routes.capability_gaps as rc
    monkeypatch.setattr(rc, "_ls_call", lambda name, **kw: None)
    r = client.get("/api/capability-gaps")
    assert r.status_code == 200
    d = r.get_json()
    assert d["gaps"] == [] and d["count"] == 0 and d["store_available"] is False


def test_route_reports_the_export_path_when_enabled(client, monkeypatch, tmp_path):
    monkeypatch.setenv(ENV, str(tmp_path))
    d = client.get("/api/capability-gaps").get_json()
    assert d["export"]["enabled"] is True
    assert d["export"]["path"] == os.path.join(str(tmp_path), cg.EXPORT_FILENAME)
    assert d["export"]["env"] == ENV
