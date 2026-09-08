"""Claude Code lifecycle hooks (WO-61, REQ-HOOK-001 / REQ-HOOK-002).

Install merges seven observe-only events beside the existing three and
never deletes a foreign hook; uninstall removes only ours; events a build
does not fire are skipped with a note; each handler maps its payload to one
typed event with a deterministic id; the intake writes through the daemon;
instructions are capped, hashed and redacted; and every runtime id has a
declared coverage entry.

Every test uses a temp settings path and a temp store: nothing here may
touch ~/.claude/settings.json or the developer's DuckDB.
"""
from __future__ import annotations

import hashlib
import importlib
import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import hook_ownership  # noqa: E402
from clawmetry import hooks_claude_code as h  # noqa: E402
from clawmetry import lifecycle_coverage as lc  # noqa: E402

ALL_SUPPORTED = {ev: True for ev in h.LIFECYCLE_EVENTS}
OUR_MARKERS = h._HOOK_CMD_MARKERS


@pytest.fixture
def paths(tmp_path, monkeypatch):
    monkeypatch.setattr(h, "_MARKER_PATH", str(tmp_path / "marker.json"))
    return str(tmp_path / "settings.json"), str(tmp_path / "marker.json")


# ── install / uninstall ──────────────────────────────────────────────────

def test_install_registers_all_ten_events_async_for_lifecycle(paths):
    sp, mp = paths
    res = h.install(settings_path=sp, probe=ALL_SUPPORTED)
    assert res["status"] == "installed"
    assert res["skipped"] == [] and res["notes"] == []
    s = json.load(open(sp))["hooks"]
    for ev in ("PreToolUse", "Notification", "Stop", *h.LIFECYCLE_EVENTS):
        assert ev in s, ev
    for ev in h.LIFECYCLE_EVENTS:
        hk = s[ev][0]["hooks"][0]
        assert hk["command"] == f"clawmetry hooks run {ev.lower()}"
        assert hk["async"] is True, "non-gating hooks must not block the agent"
        assert hk["timeout"] <= 10
    # The gate stays synchronous: it decides, it cannot be backgrounded.
    assert "async" not in s["PreToolUse"][0]["hooks"][0]
    marker = json.load(open(mp))["claude_code"]
    assert set(h.LIFECYCLE_EVENTS) <= set(marker["events"])
    assert marker["skipped"] == []


def test_install_is_idempotent(paths):
    sp, _ = paths
    h.install(settings_path=sp, probe=ALL_SUPPORTED)
    r2 = h.install(settings_path=sp, probe=ALL_SUPPORTED)
    assert r2["status"] == "already_present"
    s = json.load(open(sp))["hooks"]
    assert all(len(s[ev]) == 1 for ev in h.LIFECYCLE_EVENTS)


def test_install_merges_and_foreign_hooks_survive_both_shapes(paths):
    sp, _ = paths
    # Separate-entry shape (numbat) AND merged-entry shape (gk --force):
    # a foreign command inside the entry that will also hold ours.
    json.dump({"hooks": {
        "SubagentStop": [{"matcher": "Explore",
                          "hooks": [{"type": "command", "command": "numbat notify"}]}],
        "PostCompact": [{"hooks": [{"type": "command", "command": "gk ai hook"}]}],
    }}, open(sp, "w"))
    before = {ev: hook_ownership.foreign_hook_count(v, OUR_MARKERS)
              for ev, v in json.load(open(sp))["hooks"].items()}
    h.install(settings_path=sp, probe=ALL_SUPPORTED)
    s = json.load(open(sp))["hooks"]
    for ev, n in before.items():
        assert hook_ownership.foreign_hook_count(s[ev], OUR_MARKERS) == n, ev
    assert any("numbat" in hk["command"] for e in s["SubagentStop"] for hk in e["hooks"])
    assert any("gk ai hook" in hk["command"] for e in s["PostCompact"] for hk in e["hooks"])


def test_uninstall_removes_only_ours_at_hook_granularity(paths):
    sp, mp = paths
    h.install(settings_path=sp, probe=ALL_SUPPORTED)
    s = json.load(open(sp))
    # Merge a foreign hook INTO our PermissionDenied entry (the --force shape).
    s["hooks"]["PermissionDenied"][0]["hooks"].append(
        {"type": "command", "command": "my-audit-logger"})
    s["hooks"]["SessionStart"].append(
        {"matcher": "startup", "hooks": [{"type": "command", "command": "my-banner"}]})
    json.dump(s, open(sp, "w"))
    res = h.uninstall(settings_path=sp)
    assert res["status"] == "uninstalled"
    s = json.load(open(sp))["hooks"]
    assert [hk["command"] for e in s["PermissionDenied"] for hk in e["hooks"]] == ["my-audit-logger"]
    assert [hk["command"] for e in s["SessionStart"] for hk in e["hooks"]] == ["my-banner"]
    for ev in ("PostToolUseFailure", "SubagentStart", "SubagentStop",
               "PostCompact", "InstructionsLoaded", "PreToolUse", "Notification", "Stop"):
        assert ev not in s, ev
    assert "claude_code" not in json.load(open(mp))


def test_events_the_build_does_not_fire_are_skipped_with_a_note(paths, capsys):
    sp, mp = paths
    probe = dict(ALL_SUPPORTED)
    probe["InstructionsLoaded"] = False
    probe["PermissionDenied"] = False
    res = h.install(settings_path=sp, probe=probe)
    assert res["status"] == "installed"
    assert res["skipped"] == ["PermissionDenied", "InstructionsLoaded"]
    assert any("InstructionsLoaded" in n and "skipped" in n for n in res["notes"])
    s = json.load(open(sp))["hooks"]
    assert "InstructionsLoaded" not in s and "PermissionDenied" not in s
    assert "PostCompact" in s
    marker = json.load(open(mp))["claude_code"]
    assert marker["skipped"] == ["PermissionDenied", "InstructionsLoaded"]
    assert "InstructionsLoaded" not in marker["events"]


def test_unlocatable_binary_installs_everything_and_says_so(paths):
    sp, _ = paths
    res = h.install(settings_path=sp, probe={ev: None for ev in h.LIFECYCLE_EVENTS})
    assert res["skipped"] == []
    assert any("not found" in n for n in res["notes"])
    assert set(h.LIFECYCLE_EVENTS) <= set(json.load(open(sp))["hooks"])


def test_probe_reads_event_names_out_of_the_binary(tmp_path):
    fake = tmp_path / "claude"
    fake.write_bytes(b"\x00junk PostToolUseFailure\x00SessionStart\x00PostCompact\x00")
    res = h.probe_claude_events(binaries=[str(fake)])
    assert res["PostToolUseFailure"] is True and res["SessionStart"] is True
    assert res["InstructionsLoaded"] is False and res["PermissionDenied"] is False
    assert h.probe_claude_events(binaries=[]) == {ev: None for ev in h.LIFECYCLE_EVENTS}
    assert h.probe_claude_events(binaries=[str(tmp_path / "missing")]) == \
        {ev: None for ev in h.LIFECYCLE_EVENTS}


def test_run_dispatch_knows_every_lifecycle_event(monkeypatch):
    seen = []
    monkeypatch.setattr(h, "main_lifecycle", lambda ev: seen.append(ev) or 0)
    for ev in h.LIFECYCLE_EVENTS:
        assert h.cli_main(["run", ev.lower()]) == 0
    assert seen == list(h.LIFECYCLE_EVENTS)
    assert h.cli_main(["run", "nosuchevent"]) == 1


# ── payload mapping ──────────────────────────────────────────────────────

BASE = {"session_id": "abc123", "transcript_path": "/t.jsonl", "cwd": "/w",
        "permission_mode": "default", "prompt_id": "p1", "effort": {"level": "high"}}


def _one(ev, **fields):
    out = h.map_lifecycle_event(ev, dict(BASE, hook_event_name=ev, **fields), ts="2026-09-03T10:00:00.000Z")
    assert len(out) == 1, out
    return out[0]


def test_tool_failed_mapping():
    e = _one("PostToolUseFailure", tool_name="Bash", tool_use_id="toolu_1",
             tool_input={"command": "npm test"}, tool_error="timed out",
             brand_new_field={"x": 1})
    assert e["event_type"] == "tool.failed" and e["session_id"] == "abc123"
    d = e["data"]
    assert d["tool_name"] == "Bash" and d["tool_use_id"] == "toolu_1"
    assert d["error"] == "timed out" and d["source"] == "hook"
    assert d["unknown_fields"] == ["brand_new_field"]
    assert "tool_input" not in d


def test_subagent_mappings():
    s = _one("SubagentStart", agent_id="sub_1", agent_type="Explore", agent_instructions="go")
    t = _one("SubagentStop", agent_id="sub_1", agent_type="Explore", last_assistant_message="done!")
    assert s["event_type"] == "subagent.started" and t["event_type"] == "subagent.stopped"
    assert s["data"]["agent_id"] == "sub_1" and t["data"]["last_message_chars"] == 5
    assert "agent_instructions" not in s["data"] and "last_assistant_message" not in t["data"]
    assert s["id"] != t["id"]


def test_permission_denied_carries_tool_and_reason_but_never_arguments():
    e = _one("PermissionDenied", tool_name="Bash", tool_use_id="toolu_9",
             tool_input={"command": "rm -rf /"}, denial_reason="Destructive command blocked")
    assert e["event_type"] == "permission.denied"
    assert e["data"]["tool_name"] == "Bash" and e["data"]["reason"] == "Destructive command blocked"
    assert "rm -rf" not in json.dumps(e)


def test_compaction_and_session_start_mappings():
    c = _one("PostCompact", trigger="auto")
    assert c["event_type"] == "context.compacted" and c["data"]["trigger"] == "auto"
    s = _one("SessionStart", start_reason="resume", model="claude-opus-5")
    assert s["event_type"] == "session.started"
    assert s["data"]["start_reason"] == "resume" and s["data"]["model"] == "claude-opus-5"


def test_no_session_id_means_nothing_to_record():
    assert h.map_lifecycle_event("PostCompact", {"trigger": "auto"}) == []
    assert h.map_lifecycle_event("PostCompact", "not a dict") == []
    assert h.map_lifecycle_event("NoSuchEvent", dict(BASE)) == []


def test_ids_are_deterministic_per_fact():
    a = _one("PostToolUseFailure", tool_name="Bash", tool_use_id="toolu_1", tool_error="x")
    b = h.map_lifecycle_event("PostToolUseFailure",
                              dict(BASE, tool_name="Bash", tool_use_id="toolu_1", tool_error="x"),
                              ts="2026-09-03T11:59:59.000Z")[0]
    assert a["id"] == b["id"], "same fact, later arrival -> same id -> no-op"
    c = _one("PostToolUseFailure", tool_name="Bash", tool_use_id="toolu_2", tool_error="x")
    assert c["id"] != a["id"]
    assert h.lifecycle_event_id("s", "tool.failed", "k") == h.lifecycle_event_id("s", "tool.failed", "k")
    assert len(a["id"]) == 32


def test_instructions_loaded_reads_the_file_caps_and_hashes(tmp_path):
    body = ("# rules\n" + "x" * (h.INSTRUCTIONS_CAP_BYTES + 500)).encode()
    f = tmp_path / "CLAUDE.md"
    f.write_bytes(body)
    e = _one("InstructionsLoaded", instruction_path=str(f), instruction_type="claude_md",
             load_reason="session_start")
    assert e["event_type"] == "instructions.loaded"
    info = e["instructions"]
    assert info["sha256"] == hashlib.sha256(body).hexdigest()
    assert info["bytes"] == len(body) and info["truncated"] is True
    assert len(info["content"].encode()) == h.INSTRUCTIONS_CAP_BYTES
    assert e["data"]["sha256"] == info["sha256"] and e["data"]["readable"] is True


def test_instructions_loaded_unreadable_path_still_records_the_fact(tmp_path):
    e = _one("InstructionsLoaded", instruction_path=str(tmp_path / "nope.md"),
             instruction_type="rules", load_reason="path_glob_match")
    assert e["data"]["readable"] is False and "instructions" not in e


def test_session_start_falls_back_to_claude_md_chain_only_when_event_is_unavailable(tmp_path, monkeypatch):
    proj = tmp_path / "proj" / "sub"
    proj.mkdir(parents=True)
    (tmp_path / "proj" / "CLAUDE.md").write_text("project rules")
    (proj / ".claude").mkdir()
    (proj / ".claude" / "CLAUDE.md").write_text("nested rules")
    payload = dict(BASE, cwd=str(proj), start_reason="startup")
    monkeypatch.setattr(h, "_lifecycle_skipped_events", lambda: set())
    assert [e["event_type"] for e in h.map_lifecycle_event("SessionStart", payload)] == ["session.started"]
    monkeypatch.setattr(h, "_lifecycle_skipped_events", lambda: {"InstructionsLoaded"})
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path / "nohome"))
    out = h.map_lifecycle_event("SessionStart", payload)
    types = [e["event_type"] for e in out]
    assert types[0] == "session.started" and types.count("instructions.loaded") == 2
    paths = {e["data"]["instruction_path"] for e in out[1:]}
    assert str(proj / ".claude" / "CLAUDE.md") in paths and str(tmp_path / "proj" / "CLAUDE.md") in paths
    assert all(e["data"]["load_reason"] == "session_start_fallback" for e in out[1:])


# ── handler process: stdin -> post, never blocks, always exit 0 ──────────

def test_main_lifecycle_posts_mapped_events(monkeypatch):
    sent = []
    monkeypatch.setattr(h, "post_lifecycle", lambda evs, **kw: sent.append(evs) or True)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
        dict(BASE, hook_event_name="PostCompact", trigger="manual"))))
    assert h.main_lifecycle("PostCompact") == 0
    assert sent and sent[0][0]["event_type"] == "context.compacted"


def test_main_lifecycle_survives_garbage_and_failure(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("{not json"))
    assert h.main_lifecycle("PostCompact") == 0
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(dict(BASE, trigger="auto"))))
    monkeypatch.setattr(h, "post_lifecycle", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert h.main_lifecycle("PostCompact") == 0


def test_post_lifecycle_never_raises_on_a_dead_dashboard():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    ok = h.post_lifecycle([{"id": "x"}], base=f"http://127.0.0.1:{port}", timeout=0.5)
    assert ok is False
    assert h.post_lifecycle([]) is False


# ── intake route -> daemon write ─────────────────────────────────────────

@pytest.fixture
def client(monkeypatch):
    from flask import Flask
    import routes.hooks as rh
    app = Flask(__name__)
    app.register_blueprint(rh.bp_hooks)
    calls = []

    def fake_write(method_name, **kwargs):
        calls.append((method_name, kwargs))
        return True

    monkeypatch.setattr(rh, "_ls_write", fake_write)
    monkeypatch.setattr(rh, "_lifecycle_node_id", lambda: "node-1")
    return app.test_client(), calls


def test_intake_writes_through_the_daemon(client):
    c, calls = client
    ev = _one("PermissionDenied", tool_name="Bash", tool_use_id="toolu_9", denial_reason="no")
    r = c.post("/api/hooks/claude-code/lifecycle", json={"events": [ev]},
               environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert r.status_code == 200
    assert r.get_json() == {"ok": True, "accepted": 1, "stored": True}
    assert calls and calls[0][0] == "ingest_lifecycle_events"
    kw = calls[0][1]
    assert kw["node_id"] == "node-1" and kw["agent_type"] == "claude_code"
    assert kw["events"][0]["id"] == ev["id"] and kw["events"][0]["event_type"] == "permission.denied"


def test_intake_upserts_instructions_alongside_the_event(client, tmp_path):
    c, calls = client
    f = tmp_path / "CLAUDE.md"
    f.write_text("rules for alice@example.com")
    ev = _one("InstructionsLoaded", instruction_path=str(f), instruction_type="claude_md",
              load_reason="session_start")
    r = c.post("/api/hooks/claude-code/lifecycle", json={"events": [ev]},
               environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert r.get_json()["accepted"] == 1
    names = [m for m, _ in calls]
    assert names == ["ingest_lifecycle_events", "upsert_session_instructions"]
    row = calls[1][1]["row"]
    assert row["instruction_path"] == str(f) and row["sha256"] == ev["instructions"]["sha256"]


def test_intake_rejects_off_box_callers_and_bad_shapes(client):
    c, calls = client
    r = c.post("/api/hooks/claude-code/lifecycle", json={"events": []},
               environ_base={"REMOTE_ADDR": "10.0.0.9"})
    assert r.status_code == 403
    r = c.post("/api/hooks/claude-code/lifecycle", json={"events": "nope"},
               environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert r.status_code == 200 and r.get_json()["ok"] is False
    r = c.post("/api/hooks/claude-code/lifecycle",
               json={"events": [{"event_type": "made.up", "session_id": "s", "id": "x"}]},
               environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert r.get_json() == {"ok": True, "accepted": 0, "stored": False}
    assert calls == []


def test_intake_reports_a_write_that_did_not_land(client, monkeypatch):
    import routes.hooks as rh
    c, _ = client
    monkeypatch.setattr(rh, "_ls_write", lambda *a, **k: False)
    ev = _one("PostCompact", trigger="auto")
    r = c.post("/api/hooks/claude-code/lifecycle", json={"events": [ev]},
               environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert r.get_json()["stored"] is False, "an older daemon must not look like success"


def test_coverage_route_serves_the_declaration(client):
    c, _ = client
    r = c.get("/api/lifecycle/coverage?runtime=cursor")
    d = r.get_json()
    assert d["runtime"] == "cursor"
    assert "Permission denials: not exposed by cursor" in d["lines"]
    r = c.get("/api/lifecycle/coverage")
    d = r.get_json()
    assert set(d["runtimes"]) == set(lc.all_runtimes())
    assert d["facts"] == list(lc.FACTS)


# ── store: real DuckDB, dedupe + instructions redaction ──────────────────

@pytest.fixture
def store(tmp_path, monkeypatch):
    pytest.importorskip("duckdb")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "wo61.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    st = ls.get_store()
    yield st, ls
    try:
        st.stop(flush=True)
    except Exception:
        pass


def test_store_dedupes_the_same_fact_and_prefixes_the_session(store):
    st, _ = store
    ev = _one("PermissionDenied", tool_name="Bash", tool_use_id="toolu_9", denial_reason="no")
    assert st.ingest_lifecycle_events([ev], node_id="n1") == 1
    assert st.ingest_lifecycle_events([ev, ev], node_id="n1") == 2
    st.flush()
    rows = st.query_lifecycle_events("abc123", event_type="permission.denied")
    assert len(rows) == 1, "second arrival of the same fact is a no-op"
    assert rows[0]["session_id"] == "claude_code:abc123"
    assert rows[0]["data"]["source"] == "hook" and rows[0]["data"]["tool_name"] == "Bash"
    assert st.query_lifecycle_events("claude_code:abc123") == rows
    bad = {"id": "x", "session_id": "abc123", "event_type": "made.up", "ts": "t"}
    assert st.ingest_lifecycle_events([bad], node_id="n1") == 0


def test_store_keeps_instructions_capped_hashed_and_redacted(store, monkeypatch):
    st, _ = store
    monkeypatch.delenv("CLAWMETRY_REDACT", raising=False)
    monkeypatch.delenv("CLAWMETRY_REDACT_PII", raising=False)
    body = "contact alice@example.com token sk-ant-abcdefghijklmnopqrstuvwx\n" + "y" * (40 * 1024)
    ok = st.upsert_session_instructions({
        "session_id": "abc123", "instruction_path": "/w/CLAUDE.md",
        "instruction_type": "claude_md", "load_reason": "session_start",
        "sha256": "deadbeef", "bytes": len(body), "truncated": False,
        "content": body, "loaded_at": "2026-09-03T10:00:00Z"})
    assert ok is True
    rows = st.get_session_instructions("abc123")
    assert len(rows) == 1
    row = rows[0]
    assert row["sha256"] == "deadbeef" and row["byte_len"] == len(body)
    assert row["truncated"] is True and len(row["content"].encode()) <= 32 * 1024
    assert "alice@example.com" not in row["content"] and "[email]" in row["content"]
    assert "sk-ant-abcdefghijklmnopqrstuvwx" not in row["content"]
    # The same delivery twice (same load time, same hash) is one load; a
    # genuine re-load replaces the row and counts.
    st.upsert_session_instructions({"session_id": "abc123", "instruction_path": "/w/CLAUDE.md",
                                    "sha256": "deadbeef", "content": body,
                                    "loaded_at": "2026-09-03T10:00:00Z"})
    assert st.get_session_instructions("abc123")[0]["loads"] == 1
    st.upsert_session_instructions({"session_id": "abc123", "instruction_path": "/w/CLAUDE.md",
                                    "sha256": "cafe", "content": "new", "loaded_at": "t2"})
    rows = st.get_session_instructions("claude_code:abc123")
    assert len(rows) == 1 and rows[0]["sha256"] == "cafe" and rows[0]["loads"] == 2


def test_instructions_endpoint_reads_the_store(monkeypatch):
    from flask import Flask
    import routes.hooks as rh
    app = Flask(__name__)
    app.register_blueprint(rh.bp_hooks)
    monkeypatch.setattr(rh, "_ls_read", lambda m, **kw: [{"instruction_path": "/w/CLAUDE.md", "sha256": "abc"}]
                        if m == "get_session_instructions" else None)
    d = app.test_client().get("/api/sessions/abc123/instructions").get_json()
    assert d["session_id"] == "abc123" and d["instructions"][0]["sha256"] == "abc"
    assert d["cap_bytes"] == 32 * 1024


def test_daemon_proxy_allowlists_the_lifecycle_methods():
    from routes.local_query import _DAEMON_METHODS
    for m in ("ingest_lifecycle_events", "upsert_session_instructions",
              "get_session_instructions", "query_lifecycle_events"):
        assert m in _DAEMON_METHODS, m


# ── per-runtime coverage declaration ─────────────────────────────────────

def test_every_runtime_declares_every_fact():
    from clawmetry import entitlements as ent
    table = lc.coverage_table()
    assert set(table) == set(ent.FREE_RUNTIMES | ent.PAID_RUNTIMES)
    for rt, facts in table.items():
        assert tuple(facts) == lc.FACTS, rt
        for fact, row in facts.items():
            assert row["verdict"] in lc.VERDICTS, (rt, fact)
            assert row["note"].strip(), (rt, fact)
            for banned in ("—", " -- "):
                assert banned not in row["note"], (rt, fact)


def test_claude_code_is_full_and_unverified_runtimes_are_none_not_invented():
    cc = lc.coverage_for("claude_code")
    assert all(cc[f]["verdict"] == "full" for f in lc.FACTS)
    kimi = lc.coverage_for("kimi")
    assert kimi["permission_denied"]["verdict"] == "none"
    assert "not verified" in kimi["tool_failed"]["note"]
    assert lc.explain("cursor", "permission_denied") == "Permission denials: not exposed by cursor"
    assert lc.explain("claude_code", "permission_denied") == ""
    s = lc.summarise("cursor")
    assert "permission_denied" in s["none"] and s["lines"]


def test_compaction_verdict_follows_the_context_coverage_denylist():
    from clawmetry import context_coverage as cc
    for rt in lc.all_runtimes():
        row = lc.coverage_for(rt)["context_compacted"]
        if rt in lc._DECLARED:
            continue
        expected = "partial" if cc.declared_support(rt, "compaction") else "none"
        assert row["verdict"] == expected, rt


def test_event_types_match_the_store_and_the_intake():
    import routes.hooks as rh
    from clawmetry.local_store import LocalStore
    assert set(lc.EVENT_TYPES.values()) == set(rh._LIFECYCLE_TYPES) == set(LocalStore.LIFECYCLE_EVENT_TYPES)
    assert set(lc.EVENT_TYPES.values()) == set(h.LIFECYCLE_EVENT_TYPES.values())


def test_posture_surface_carries_the_redaction_line(monkeypatch):
    from clawmetry import security_posture as sp
    env = sp.get_posture("no-such-runtime-xyz")
    ids = [c["id"] for c in env["checks"]]
    assert "pii_redaction" in ids
    assert env["total"] >= 1
