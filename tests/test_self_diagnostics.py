"""Self-diagnostics over MCP (WO-59, REQ-SELF-001..004).

Pins the contract end to end without a daemon:

* the MCP tool catalogue: ``report_to_operator`` with the six categories
  (operator-extendable), the four read tools, and NO tool that acts on a
  process;
* the write path through a temp DuckDB store: redaction applied before
  storage, the summary cap, category validation, idempotency;
* corroboration: the window logic (pure), the daemon-tick pass against real
  ``loop_signals`` and ``approvals`` rows, session-id prefix matching;
* honesty: withheld below the minimum, a ratio above it;
* the installer, per verified runtime format: merge, never delete a foreign
  entry, uninstall removes only ours, a hand-written entry is left in place,
  JSONC is refused rather than guessed, status vocabulary;
* the read routes and the snapshot slice;
* the CLI fast path never imports the dashboard.

Every file the installer touches lives under a ``tmp_path`` home. Nothing
here reads or writes the developer's real ``~/.claude.json`` & co.
"""
from __future__ import annotations

import builtins
import importlib
import json
import os
import sys
import time
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import self_diagnostics as sd  # noqa: E402
from clawmetry import mcp_install as mi  # noqa: E402
from clawmetry import mcp_server as ms  # noqa: E402


# ── fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "selfdiag.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    pytest.importorskip("duckdb")
    import clawmetry.local_store as ls

    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=True)


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A fake HOME so neither the installer nor the CLI can touch real files."""
    h = tmp_path / "home"
    h.mkdir()
    monkeypatch.setenv("HOME", str(h))
    monkeypatch.setenv("USERPROFILE", str(h))
    return h


def _installer(home):
    return mi.Installer(home=str(home), command="/opt/clawmetry/bin/clawmetry", args=["mcp"])


def _iso_local(offset_secs=0):
    return datetime.fromtimestamp(time.time() + offset_secs).isoformat(timespec="seconds")


# ── 1. tool catalogue ──────────────────────────────────────────────────────

def _tool(name):
    for t in ms.tools_catalogue():
        if t["name"] == name:
            return t
    raise AssertionError(f"tool {name} missing from catalogue")


def test_report_tool_schema_has_six_default_categories():
    t = _tool("report_to_operator")
    props = t["inputSchema"]["properties"]
    assert set(t["inputSchema"]["required"]) == {"category", "summary"}
    assert props["category"]["enum"] == list(sd.DEFAULT_CATEGORIES)
    assert len(sd.DEFAULT_CATEGORIES) == 6
    assert "session_id" in props and "runtime" in props
    # Framed as feedback to the people who run the agent, never confession.
    desc = t["description"].lower()
    assert "operators" in desc and "got in the way" in desc
    for banned in ("confess", "unsafe", "violation", "misbehav"):
        assert banned not in desc


def test_operator_can_extend_categories(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"self_diagnostics": {"categories": ["flaky_ci", "BAD CAT", 7]}}))
    monkeypatch.setattr(sd, "_CONFIG_PATH", str(cfg))
    cats = sd.allowed_categories()
    assert cats[:6] == sd.DEFAULT_CATEGORIES
    assert "flaky_ci" in cats
    assert "bad cat" not in cats and "BAD CAT" not in cats
    assert _tool("report_to_operator")["inputSchema"]["properties"]["category"]["enum"][-1] == "flaky_ci"
    assert sd.normalize_category("FLAKY_CI") == "flaky_ci"
    assert sd.normalize_category("made_up") is None


def test_read_tools_present_and_nothing_actuates():
    names = {t["name"] for t in ms.tools_catalogue()}
    for required in ("list_incidents", "get_guard_status", "get_signal_rates",
                     "list_self_reports", "report_to_operator",
                     "list_sessions", "get_cost_summary", "get_session_trace",
                     "list_events", "get_health"):
        assert required in names
    for n in names:
        for word in ms.ACTUATING_WORDS:
            assert word not in n.lower(), f"{n} looks like an actuating tool"
        assert "control" not in n.lower()
    # The one write tool is the report; every other tool is a read.
    assert names - {"report_to_operator"} == {
        n for n in names if n.startswith(("list_", "get_"))}


@pytest.mark.parametrize("name,args", [
    ("report_to_operator", {"category": "task_failure", "summary": "could not finish",
                            "session_id": "claude_code:s1"}),
    ("list_incidents", {}),
    ("get_guard_status", {"session_id": "claude_code:s1"}),
    ("get_signal_rates", {}),
    ("list_self_reports", {}),
    ("get_health", {}),
])
def test_every_tool_is_honest_when_daemon_is_down(monkeypatch, name, args):
    monkeypatch.setattr(ms, "_read_discovery", lambda: None)
    resp = ms.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                              "params": {"name": name, "arguments": args}})
    assert resp["result"]["isError"] is True
    body = json.loads(resp["result"]["content"][0]["text"])
    assert "daemon is not running" in body["error"]


def test_busy_daemon_is_not_reported_as_down(monkeypatch):
    import socket
    import urllib.request

    monkeypatch.setattr(ms, "_read_discovery", lambda: {"port": 1, "token": "t"})

    def _raise(*a, **k):
        raise socket.timeout("timed out")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    out = ms._call_tool("list_incidents", {})
    assert out["code"] == "timeout"
    assert "running but did not answer" in out["error"]
    assert "not running" not in out["error"]


def test_old_daemon_refusal_names_the_upgrade(monkeypatch):
    monkeypatch.setattr(ms, "_post", lambda path, payload: {
        "error": "method not allowed: 'query_guard_incidents'", "code": "refused", "status": 400})
    out = ms._call_tool("list_incidents", {})
    assert out["code"] == "refused" and "clawmetry update" in out["error"]
    out = ms._call_tool("report_to_operator", {"category": "noteworthy", "summary": "x",
                                               "session_id": "s"})
    assert out["code"] == "refused" and "too old" in out["error"]


def test_report_tool_rejects_unknown_category_before_touching_daemon(monkeypatch):
    monkeypatch.setattr(ms, "_read_discovery", lambda: None)
    out = ms._call_tool("report_to_operator", {"category": "nope", "summary": "x"})
    assert "not one of the allowed" in out["error"]
    assert out["allowed"] == list(sd.DEFAULT_CATEGORIES)


def test_signal_rates_says_not_available_when_daemon_lacks_method(monkeypatch):
    monkeypatch.setattr(ms, "_method", lambda name, **kw: {
        "error": "method not allowed: 'query_signal_rates'", "code": "refused"})
    out = ms._call_tool("get_signal_rates", {"window": "24h"})
    assert out["available"] is False
    assert out["error"] == "signals not available on this daemon version"


# ── 2. write path through the store ───────────────────────────────────────

def test_ingest_applies_redaction_and_cap(store):
    secret = "sk-ant-abcdefghijklmnopqrstuvwxyz0123456789"
    long_tail = " padding" * 200
    row = store.ingest_self_report(
        session_id="claude_code:abc", category="repeatedly_broken_tool",
        summary=f"the deploy tool failed with api_key={secret}{long_tail}",
        agent_type="claude_code", model="claude-x", node_id="n1")
    assert row["category"] == "repeatedly_broken_tool"
    assert secret not in row["summary_redacted"]
    assert "[REDACTED:" in row["summary_redacted"]
    assert len(row["summary_redacted"]) <= sd.SUMMARY_MAX_CHARS
    stored = store.query_self_reports(session_id="abc")
    assert len(stored) == 1
    assert secret not in stored[0]["summary_redacted"]
    assert stored[0]["corroborated"] is False
    assert stored[0]["model"] == "claude-x" and stored[0]["node_id"] == "n1"


def test_ingest_rejects_bad_category_and_is_idempotent(store):
    bad = store.ingest_self_report(session_id="s", category="made_up", summary="x")
    assert bad["error"] == "category not allowed"
    store.ingest_self_report(session_id="s", category="noteworthy", summary="one",
                             report_id="fixed-id")
    store.ingest_self_report(session_id="s", category="noteworthy", summary="two",
                             report_id="fixed-id")
    rows = store.query_self_reports(session_id="s")
    assert len(rows) == 1 and rows[0]["summary_redacted"] == "one"


def test_runtime_derived_from_session_prefix_when_absent(store):
    row = store.ingest_self_report(session_id="codex:xyz", category="capability_gap",
                                   summary="no browser")
    assert row["agent_type"] == "codex"
    row2 = store.ingest_self_report(session_id="", category="capability_gap", summary="x")
    assert row2["agent_type"] == "unknown"


def test_mcp_tool_writes_through_daemon_method(store, monkeypatch):
    """The MCP process never opens DuckDB: the tool calls the daemon's
    ``ingest_self_report`` method. Simulate the proxy with the temp store."""
    calls = []

    def fake_method(name, **kwargs):
        calls.append(name)
        return {"result": getattr(store, name)(**kwargs)}

    monkeypatch.setattr(ms, "_method", fake_method)
    monkeypatch.setattr(ms, "_node_id", lambda: "node-1")
    out = ms._call_tool("report_to_operator", {
        "category": "bypassed_block", "summary": "write tool blocked, used bash",
        "session_id": "claude_code:abc"})
    assert out["ok"] is True and out["session_source"] == "argument"
    assert calls == ["ingest_self_report"]
    assert store.query_self_reports(session_id="claude_code:abc")[0]["node_id"] == "node-1"

    listed = ms._call_tool("list_self_reports", {"window": "1h", "category": "bypassed_block"})
    assert listed["count"] == 1
    assert "not the same as false" in listed["uncorroborated_means"]


def test_session_inferred_from_env_then_cwd(store, monkeypatch, tmp_path):
    monkeypatch.setattr(ms, "_method", lambda name, **kw: {"result": getattr(store, name)(**kw)})
    monkeypatch.setattr(ms, "_node_id", lambda: "")
    for var in sd._SESSION_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("CLAUDE_SESSION_ID", "env-session")
    out = ms._call_tool("report_to_operator", {"category": "noteworthy", "summary": "hi"})
    assert out["session_id"] == "env-session" and out["session_source"] == "environment"

    monkeypatch.delenv("CLAUDE_SESSION_ID")
    proj = tmp_path / "proj"
    (proj / "sub").mkdir(parents=True)
    store.ingest_session({"agent_type": "claude_code", "session_id": "claude_code:cwd1",
                          "node_id": "n", "agent_id": "main",
                          "last_active_at": datetime.now(timezone.utc).isoformat()})
    store.update_session_location("claude_code:cwd1", cwd=str(proj), agent_type="claude_code")
    monkeypatch.chdir(proj / "sub")
    out = ms._call_tool("report_to_operator", {"category": "noteworthy", "summary": "hi"})
    assert out["session_id"] == "claude_code:cwd1"
    assert out["session_source"] == "working directory"


# ── 3. corroboration ──────────────────────────────────────────────────────

def _inc(sid="claude_code:abc", first=1000.0, last=1100.0, sig="daemon_detect_stuck_loop"):
    return {"session_id": sid, "signature": sig, "first_seen": first, "last_seen": last}


def test_window_logic_is_inclusive_on_both_sides():
    inc = _inc()
    w = 600
    assert sd.find_evidence({"session_id": "abc", "ts": 1100.0 + w}, [inc], [], w)
    assert sd.find_evidence({"session_id": "abc", "ts": 1000.0 - w}, [inc], [], w)
    assert sd.find_evidence({"session_id": "abc", "ts": 1100.0 + w + 1}, [inc], [], w) is None
    assert sd.find_evidence({"session_id": "abc", "ts": 1000.0 - w - 1}, [inc], [], w) is None
    # Same session id family: bare id matches the prefixed incident.
    assert sd.find_evidence({"session_id": "claude_code:abc", "ts": 1050.0}, [inc], [], w) \
        == "incident:claude_code:abc:daemon_detect_stuck_loop"
    # A different session never corroborates.
    assert sd.find_evidence({"session_id": "other", "ts": 1050.0}, [inc], [], w) is None


def test_nearest_incident_wins_and_denials_are_fallback():
    old = _inc(first=0.0, last=100.0, sig="daemon_detect_no_progress")
    near = _inc(first=900.0, last=1000.0, sig="daemon_detect_stuck_loop")
    ref = sd.find_evidence({"session_id": "abc", "ts": 1010.0}, [old, near], [], 2000)
    assert ref == "incident:claude_code:abc:daemon_detect_stuck_loop"
    denial = {"id": "ap1", "session_id": "claude_code:abc", "ts": 5000.0}
    assert sd.find_evidence({"session_id": "abc", "ts": 5100.0}, [], [denial], 600) == "denial:ap1"
    assert sd.find_evidence({"session_id": "abc", "ts": 5700.0}, [], [denial], 600) is None


def test_window_constant_and_env_override(monkeypatch):
    assert sd.CORROBORATION_WINDOW_SECS == 600
    monkeypatch.delenv("CLAWMETRY_SELFDIAG_WINDOW_SECS", raising=False)
    assert sd.corroboration_window_secs() == 600
    monkeypatch.setenv("CLAWMETRY_SELFDIAG_WINDOW_SECS", "30")
    assert sd.corroboration_window_secs() == 30
    monkeypatch.setenv("CLAWMETRY_SELFDIAG_WINDOW_SECS", "garbage")
    assert sd.corroboration_window_secs() == 600


def test_daemon_tick_corroborates_against_real_incident_rows(store, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_SELFDIAG_WINDOW_SECS", raising=False)
    store.ingest_loop_signal(
        session_id="claude_code:abc", signature="daemon_detect_stuck_loop",
        repeat_count=5, severity="warning", agent_type="claude_code",
        details={"source": "daemon_detector", "kind": "stuck_loop", "message": "looping"})
    store.ingest_self_report(session_id="abc", category="repeatedly_broken_tool",
                             summary="same command kept failing")
    # A report far outside the window stays uncorroborated.
    store.ingest_self_report(session_id="abc", category="noteworthy", summary="old",
                             ts=time.time() - 4 * 3600)
    incidents = store.query_guard_incidents(since_secs=3600, session_id="abc")
    assert len(incidents) == 1 and incidents[0]["kind"] == "stuck_loop"
    assert sd.corroborate_pending(store) == 1
    rows = {r["summary_redacted"]: r for r in store.query_self_reports(session_id="abc")}
    assert rows["same command kept failing"]["corroborated"] is True
    assert rows["same command kept failing"]["corroboration_ref"] == \
        "incident:claude_code:abc:daemon_detect_stuck_loop"
    assert rows["old"]["corroborated"] is False
    # Second tick is a no-op.
    assert sd.corroborate_pending(store) == 0


def test_permission_denial_corroborates(store, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_SELFDIAG_WINDOW_SECS", raising=False)
    now_utc = datetime.now(timezone.utc).isoformat()
    store.ingest_approval({"id": "ap-1", "requestor_session_id": "claude_code:d1",
                           "action": "Bash", "status": "denied",
                           "created_at": now_utc, "resolved_at": now_utc})
    denials = store.query_session_denials(session_id="d1", since_secs=3600)
    assert len(denials) == 1 and denials[0]["id"] == "ap-1"
    store.ingest_self_report(session_id="d1", category="bypassed_block",
                             summary="write was refused, used bash instead")
    assert sd.corroborate_pending(store) == 1
    row = store.query_self_reports(session_id="d1")[0]
    assert row["corroborated"] is True and row["corroboration_ref"] == "denial:ap-1"


# ── 4. honesty ────────────────────────────────────────────────────────────

def test_honesty_withheld_below_minimum_with_reason():
    incs = [_inc(sid=f"claude_code:s{i}", first=100 * i, last=100 * i + 10) for i in range(3)]
    reps = [{"session_id": "s0", "ts": 5.0}]
    rows = sd.honesty_rollup(incs, reps, window_secs=60, min_count=5)
    assert len(rows) == 1
    r = rows[0]
    assert r["incidents"] == 3 and r["reported"] == 1
    assert r["honesty"] is None and r["withheld"] is True
    assert "Only 3 detector incidents" in r["reason"] and "at least 5" in r["reason"]


def test_honesty_ratio_per_runtime_and_model():
    incs = [dict(_inc(sid=f"codex:s{i}", first=100 * i, last=100 * i + 10),
                 runtime="codex", model="gpt-x") for i in range(6)]
    reps = [{"session_id": f"s{i}", "ts": 100 * i + 5} for i in range(3)]
    rows = sd.honesty_rollup(incs, reps, window_secs=10, min_count=5)
    assert rows == [{"runtime": "codex", "model": "gpt-x", "incidents": 6, "reported": 3,
                     "honesty": 0.5, "withheld": False, "reason": ""}]


def test_store_honesty_uses_min_incidents_env(store, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_SELFDIAG_WINDOW_SECS", raising=False)
    store.ingest_loop_signal(session_id="claude_code:h1", signature="daemon_detect_no_progress",
                             repeat_count=3, agent_type="claude_code",
                             details={"kind": "no_progress"})
    store.ingest_self_report(session_id="h1", category="task_failure", summary="stuck")
    monkeypatch.delenv("CLAWMETRY_SELFDIAG_MIN_INCIDENTS", raising=False)
    rows = store.query_self_report_honesty(since_secs=3600)
    assert rows[0]["withheld"] is True and rows[0]["incidents"] == 1
    monkeypatch.setenv("CLAWMETRY_SELFDIAG_MIN_INCIDENTS", "1")
    rows = store.query_self_report_honesty(since_secs=3600)
    assert rows[0]["withheld"] is False and rows[0]["honesty"] == 1.0
    assert rows[0]["runtime"] == "claude_code"


# ── 5. installer, per verified runtime format ─────────────────────────────

def _seed(home, runtime):
    """Pre-existing config with a FOREIGN server entry, in that runtime's format."""
    inst = _installer(home)
    path = inst.path_for(runtime)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fmt = mi.SUPPORTED[runtime]["format"]
    if fmt == "toml_mcp_servers":
        text = ('model = "o3"\n\n[mcp_servers.github]\ncommand = "npx"\n'
                'args = ["-y", "@modelcontextprotocol/server-github"]\n')
        open(path, "w").write(text)
    elif fmt == "json_opencode":
        json.dump({"$schema": "https://opencode.ai/config.json",
                   "mcp": {"github": {"type": "local", "command": ["npx", "gh-mcp"],
                                       "enabled": True}}}, open(path, "w"))
    else:
        json.dump({"other": True, "mcpServers": {"github": {"command": "npx", "args": ["gh"]}}},
                  open(path, "w"))
    return inst, path


def _foreign_present(runtime, path):
    fmt = mi.SUPPORTED[runtime]["format"]
    text = open(path).read()
    if fmt == "toml_mcp_servers":
        return "[mcp_servers.github]" in text and 'model = "o3"' in text
    data = json.loads(text)
    key = "mcp" if fmt == "json_opencode" else "mcpServers"
    return "github" in data.get(key, {}) and (fmt == "json_opencode" or data.get("other") is True)


def _ours_present(runtime, path):
    fmt = mi.SUPPORTED[runtime]["format"]
    text = open(path).read()
    if fmt == "toml_mcp_servers":
        return "[mcp_servers.clawmetry]" in text and 'command = "/opt/clawmetry/bin/clawmetry"' in text
    data = json.loads(text)
    if fmt == "json_opencode":
        e = data["mcp"].get("clawmetry")
        return bool(e) and e["type"] == "local" and e["command"] == ["/opt/clawmetry/bin/clawmetry", "mcp"] \
            and e["enabled"] is True
    e = data["mcpServers"].get("clawmetry")
    if not e:
        return False
    ok = e["command"] == "/opt/clawmetry/bin/clawmetry" and e["args"] == ["mcp"]
    if runtime == "claude_code":
        ok = ok and e.get("type") == "stdio"
    return ok


@pytest.mark.parametrize("runtime", sorted(mi.SUPPORTED))
def test_install_merges_and_uninstall_removes_only_ours(home, runtime):
    inst, path = _seed(home, runtime)
    assert inst.status(runtime)["status"] == mi.NOT_INSTALLED

    dry = inst.install(runtime, dry_run=True)
    assert dry["status"] == mi.WOULD_REGISTER
    assert not _ours_present(runtime, path)

    res = inst.install(runtime)
    assert res["status"] == mi.REGISTERED, res
    assert _ours_present(runtime, path)
    assert _foreign_present(runtime, path), "install deleted a foreign entry"
    assert inst.status(runtime)["status"] == mi.REGISTERED
    marker = json.load(open(inst.marker_path))
    assert marker[runtime]["server_name"] == "clawmetry"

    again = inst.install(runtime)
    assert again["status"] == mi.ALREADY_PRESENT
    assert open(path).read().count("clawmetry") == open(path).read().count("clawmetry")

    gone = inst.uninstall(runtime)
    assert gone["status"] == mi.REMOVED
    assert not _ours_present(runtime, path)
    assert _foreign_present(runtime, path), "uninstall deleted a foreign entry"
    assert runtime not in json.load(open(inst.marker_path))
    assert inst.status(runtime)["status"] == mi.NOT_INSTALLED
    assert inst.uninstall(runtime)["status"] == mi.NOT_INSTALLED


@pytest.mark.parametrize("runtime", sorted(mi.SUPPORTED))
def test_hand_written_entry_is_never_deleted(home, runtime):
    inst, path = _seed(home, runtime)
    fmt = mi.SUPPORTED[runtime]["format"]
    if fmt == "toml_mcp_servers":
        with open(path, "a") as fh:
            fh.write('\n[mcp_servers.clawmetry]\ncommand = "clawmetry"\nargs = ["mcp"]\n')
    else:
        data = json.load(open(path))
        key = "mcp" if fmt == "json_opencode" else "mcpServers"
        data[key]["clawmetry"] = ({"type": "local", "command": ["clawmetry", "mcp"]}
                                  if fmt == "json_opencode"
                                  else {"command": "clawmetry", "args": ["mcp"]})
        json.dump(data, open(path, "w"))
    before = open(path).read()
    assert inst.status(runtime)["status"] == mi.ALREADY_PRESENT
    assert inst.install(runtime)["status"] == mi.ALREADY_PRESENT
    assert inst.uninstall(runtime)["status"] == mi.LEFT_IN_PLACE
    assert open(path).read() == before


def test_install_creates_missing_file_and_uninstall_leaves_valid_json(home):
    inst = _installer(home)
    res = inst.install("cursor")
    assert res["status"] == mi.REGISTERED
    path = inst.path_for("cursor")
    assert json.load(open(path))["mcpServers"]["clawmetry"]["args"] == ["mcp"]
    inst.uninstall("cursor")
    assert json.load(open(path)) == {"mcpServers": {}}


def test_codex_toml_block_round_trips_through_a_toml_parser(home):
    tomllib = pytest.importorskip("tomllib")
    inst, path = _seed(home, "codex")
    inst.install("codex")
    data = tomllib.loads(open(path).read())
    assert data["mcp_servers"]["clawmetry"] == {"command": "/opt/clawmetry/bin/clawmetry",
                                               "args": ["mcp"]}
    assert data["mcp_servers"]["github"]["command"] == "npx"
    inst.uninstall("codex")
    data = tomllib.loads(open(path).read())
    assert "clawmetry" not in data["mcp_servers"] and "github" in data["mcp_servers"]


def test_jsonc_is_reported_not_guessed(home):
    inst = _installer(home)
    path = inst.path_for("opencode")
    os.makedirs(os.path.dirname(path))
    open(path, "w").write('{\n  // comment\n  "mcp": {}\n}\n')
    before = open(path).read()
    assert inst.status("opencode")["status"] == mi.UNKNOWN_FORMAT
    assert inst.install("opencode")["status"] == mi.UNKNOWN_FORMAT
    assert inst.uninstall("opencode")["status"] == mi.UNKNOWN_FORMAT
    assert open(path).read() == before


def test_status_vocabulary_for_unsupported_and_unknown(home):
    inst = _installer(home)
    assert inst.status("aider")["status"] == mi.NO_MCP_SUPPORT
    assert inst.install("aider")["status"] == mi.NO_MCP_SUPPORT
    assert inst.status("kimi")["status"] == mi.UNKNOWN_FORMAT
    assert inst.install("kimi")["status"] == mi.UNKNOWN_FORMAT
    rows = inst.status_all("all")
    ids = {r["runtime"] for r in rows}
    assert set(mi.SUPPORTED) <= ids and set(mi.NO_MCP) <= ids
    matrix = {r["runtime"]: r for r in mi.support_matrix(home=str(home))}
    assert matrix["claude_code"]["mcp"] == "supported"
    assert matrix["aider"]["mcp"] == "not_supported"
    assert matrix["kimi"]["mcp"] == "unknown"


def test_guidance_is_offered_not_written(home, tmp_path, monkeypatch, capsys):
    proj = tmp_path / "proj"
    proj.mkdir()
    monkeypatch.chdir(proj)
    monkeypatch.setattr(mi, "resolve_server_command", lambda: ("/opt/clawmetry/bin/clawmetry", ["mcp"]))
    assert mi.cli_main(["install", "--runtime", "claude_code"]) == 0
    out = capsys.readouterr().out
    assert "report_to_operator" in out and "Not written" in out
    assert not (proj / "CLAUDE.md").exists()
    assert json.load(open(home / ".claude.json"))["mcpServers"]["clawmetry"]["type"] == "stdio"

    assert mi.cli_main(["install", "--runtime", "claude_code", "--write-guidance"]) == 0
    text = (proj / "CLAUDE.md").read_text()
    assert mi.GUIDANCE_MARKER in text and "Before finishing" in text
    assert mi.cli_main(["install", "--runtime", "claude_code", "--write-guidance"]) == 0
    assert (proj / "CLAUDE.md").read_text().count(mi.GUIDANCE_MARKER) == 1
    assert mi.guidance_file_for("gemini_cli") == "GEMINI.md"
    assert mi.guidance_file_for("codex") == "AGENTS.md"

    capsys.readouterr()  # drop the install chatter; status --json must stand alone
    assert mi.cli_main(["status", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert {r["runtime"]: r["status"] for r in rows}["claude_code"] == mi.REGISTERED
    assert mi.cli_main(["uninstall", "--runtime", "claude_code"]) == 0
    assert "clawmetry" not in json.load(open(home / ".claude.json"))["mcpServers"]


def test_cli_fast_path_never_imports_dashboard(home, monkeypatch, capsys):
    import clawmetry.cli as cli
    monkeypatch.setattr(sys, "argv", ["clawmetry", "mcp", "status", "--json"])
    monkeypatch.delitem(sys.modules, "dashboard", raising=False)
    real_import = builtins.__import__
    imported = []

    def _spy(name, *args, **kwargs):
        if name == "dashboard" or name.startswith("dashboard."):
            imported.append(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _spy)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    assert imported == []
    assert isinstance(json.loads(capsys.readouterr().out), list)


# ── 6. routes + snapshot ──────────────────────────────────────────────────

@pytest.fixture
def client(store, monkeypatch):
    flask = pytest.importorskip("flask")
    import routes.selfdiag as rs

    monkeypatch.setattr(rs, "_ls_call", lambda name, **kw: getattr(store, name)(**kw))
    app = flask.Flask("t")
    app.register_blueprint(rs.bp_selfdiag)
    return app.test_client()


def test_routes_list_honesty_and_support(client, store, home, monkeypatch):
    monkeypatch.delenv("CLAWMETRY_SELFDIAG_WINDOW_SECS", raising=False)
    store.ingest_self_report(session_id="claude_code:r1", category="missing_context",
                             summary="no README", agent_type="claude_code")
    d = client.get("/api/self-reports?session=r1").get_json()
    assert d["count"] == 1 and d["reports"][0]["category"] == "missing_context"
    assert "not the same as false" in d["uncorroborated_means"]
    d = client.get("/api/self-reports?window=7d&runtime=codex").get_json()
    assert d["count"] == 0
    d = client.get("/api/self-reports?window=7d&category=missing_context").get_json()
    assert d["count"] == 1

    h = client.get("/api/self-reports/honesty?window=7d").get_json()
    assert h["counts"] == {"claude_code": {"missing_context": 1}}
    assert h["honesty"] == [] and h["min_incidents"] == sd.MIN_INCIDENTS

    s = client.get("/api/self-reports/support").get_json()
    by = {r["runtime"]: r for r in s["runtimes"]}
    assert by["claude_code"]["mcp"] == "supported"
    assert by["aider"]["mcp"] == "not_supported" and "no MCP" in by["aider"]["detail"]


def test_snapshot_slice_has_counts_and_no_summaries(store):
    store.ingest_self_report(session_id="claude_code:z", category="noteworthy",
                             summary="a secret-free note")
    sl = sd.snapshot_slice(store)
    assert sl["total"] == 1 and sl["byRuntime"] == {"claude_code": {"noteworthy": 1}}
    for key in ("window_secs", "corroborated", "honesty", "min_incidents",
                "corroboration_window_secs"):
        assert key in sl
    assert "secret-free" not in json.dumps(sl)


def test_daemon_allowlist_names_every_method_the_feature_uses():
    from routes.local_query import _DAEMON_METHODS
    for m in ("ingest_self_report", "query_self_reports", "query_self_report_counts",
              "query_self_report_honesty", "query_guard_incidents",
              "query_session_denials", "find_session_by_cwd",
              "get_session_location", "query_policy_actions"):
        assert m in _DAEMON_METHODS, m


def test_parse_window():
    assert sd.parse_window_secs("24h") == 86400
    assert sd.parse_window_secs("7d") == 7 * 86400
    assert sd.parse_window_secs("30m") == 1800
    assert sd.parse_window_secs(90) == 90
    assert sd.parse_window_secs("junk", 5) == 5
    assert sd.parse_window_secs("0") == 1


def test_live_templates_carry_the_new_surfaces():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    guard = open(os.path.join(root, "clawmetry", "templates", "tabs", "guard.html")).read()
    trans = open(os.path.join(root, "clawmetry", "templates", "tabs", "transcripts.html")).read()
    js = open(os.path.join(root, "clawmetry", "static", "js", "app.js")).read()
    assert 'id="guard-selfreports-body"' in guard
    assert 'id="selfreports-panel"' in trans
    assert "function loadGuardSelfReports" in js and "_loadSelfReportsPanel(sessionId)" in js
    for text in (guard, trans):
        assert "—" not in text.split("<!--")[0]
