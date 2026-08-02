"""Tests for the runtime pre-tool gate seam + the Claude Code local gate.

Covers the four Workstream-B deliverable surfaces:

  1. GATE_HANDLERS registry + ``sync_runtime_gates`` dispatch (per-runtime
     want computation, openclaw's exec-only predicate preserved, handler
     exceptions swallowed).
  2. ``GET/PUT /api/approvals/policies`` — the local YAML round-trip the
     Approvals tab's rules panel now drives (validation failure → 400 and
     NO write).
  3. ``POST /api/hooks/claude-code/pretooluse`` — allow-when-no-policy,
     deny-after-human-decision (row flipped from a thread), the pending/
     resume protocol, and on_timeout mapping (deny→deny, allow→allow).
  4. ``clawmetry/claude_code_gate.py`` installer — non-destructive
     settings.json merge on a temp CLAUDE_CONFIG_DIR (foreign hooks
     preserved, idempotent refresh, uninstall removes only ours, manual
     `clawmetry hooks install` entries never stacked on) — and the CLI
     client's fail-open contract against an unreachable server.
"""
from __future__ import annotations

import importlib
import io
import json
import os
import sys
import threading
import time

import pytest
from flask import Flask

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── shared fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Fresh DuckDB LocalStore against a tmp file (same pattern as
    tests/test_approvals_local_blocking.py)."""
    # Isolate HOME: on a dev machine a REAL sync daemon may have written
    # ~/.clawmetry/local_query.json, which flips get_store() into daemon-
    # proxy mode (and would forward test traffic to the live daemon).
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    yield ls
    try:
        ls.get_store().stop(flush=False)
    except Exception:
        pass


def _pin_entitlement(monkeypatch, *, features=("approval_queue",),
                     grace=False, tier="pro"):
    import clawmetry.entitlements as ent
    e = ent.Entitlement(
        tier=tier, source="test", grace=grace,
        features=frozenset(features), runtimes=frozenset(),
    )
    monkeypatch.setattr(ent, "get_entitlement", lambda force=False: e)
    return e


@pytest.fixture
def approvals_mod(tmp_path, monkeypatch):
    import clawmetry.approvals as ap
    monkeypatch.setattr(ap, "POLICIES_PATH", tmp_path / "policies.yml")
    return ap


def _no_daemon_proxy(monkeypatch):
    """Force the routes' store ladder onto the direct (in-process) branch."""
    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon",
                        lambda *a, **k: None)


# ── 1. GATE_HANDLERS registry + sync_runtime_gates ─────────────────────────


def _policy(ap, *, tool="exec", runtime="", action="require_approval",
            name="p1", timeout=60, on_timeout="deny", pattern=".*"):
    c = ap._compile_policy({
        "name": name, "tool": tool, "runtime": runtime,
        "pattern_type": "command_regex", "pattern": pattern,
        "action": action, "timeout": timeout, "on_timeout": on_timeout,
    })
    assert c is not None
    return c


def test_sync_runtime_gates_dispatches_per_runtime_want(approvals_mod,
                                                        monkeypatch):
    ap = approvals_mod
    calls = {}
    monkeypatch.setattr(ap, "_default_gates_registered", True)
    monkeypatch.setattr(ap, "GATE_HANDLERS", {}, raising=True)
    monkeypatch.setattr(ap, "GATE_WANT_PREDICATES", {}, raising=True)
    ap.register_gate_handler(
        "openclaw", lambda want, pols: calls.__setitem__("openclaw", want),
        want_fn=ap._policies_want_exec_gate)
    ap.register_gate_handler(
        "claude_code", lambda want, pols: calls.__setitem__("cc", want))

    # runtime-unset exec policy → BOTH runtimes gated.
    ap.sync_runtime_gates([_policy(ap, tool="exec")])
    assert calls == {"openclaw": True, "cc": True}

    # claude_code-scoped policy → openclaw NOT gated.
    calls.clear()
    ap.sync_runtime_gates([_policy(ap, runtime="claude_code")])
    assert calls == {"openclaw": False, "cc": True}

    # write-tool policy, runtime unset: claude_code gates (any
    # require_approval), openclaw does not (exec-only predicate).
    calls.clear()
    ap.sync_runtime_gates([_policy(ap, tool="write")])
    assert calls == {"openclaw": False, "cc": True}

    # no require_approval policies → nobody gates.
    calls.clear()
    ap.sync_runtime_gates([_policy(ap, action="monitor")])
    assert calls == {"openclaw": False, "cc": False}


def test_sync_runtime_gates_swallows_handler_errors(approvals_mod,
                                                    monkeypatch):
    ap = approvals_mod
    seen = []
    monkeypatch.setattr(ap, "_default_gates_registered", True)
    monkeypatch.setattr(ap, "GATE_HANDLERS", {}, raising=True)
    monkeypatch.setattr(ap, "GATE_WANT_PREDICATES", {}, raising=True)

    def _boom(want, pols):
        raise RuntimeError("bad plugin")
    ap.register_gate_handler("broken", _boom)
    ap.register_gate_handler("ok", lambda want, pols: seen.append(want))
    ap.sync_runtime_gates([_policy(ap)])  # must not raise
    assert seen == [True]


def test_compile_policy_carries_runtime(approvals_mod):
    ap = approvals_mod
    c = ap._compile_policy({"name": "x", "tool": "exec",
                            "runtime": "Claude_Code"})
    assert c["runtime"] == "claude_code"
    assert ap._compile_policy({"name": "y", "tool": "exec"})["runtime"] == ""


# ── 2. GET/PUT /api/approvals/policies ─────────────────────────────────────


@pytest.fixture
def policy_app(approvals_mod, monkeypatch):
    _pin_entitlement(monkeypatch)
    from routes.policy import bp_policy
    app = Flask(__name__)
    app.register_blueprint(bp_policy)
    return app.test_client()


def test_policies_get_empty_then_put_roundtrip(policy_app, approvals_mod):
    ap = approvals_mod
    r = policy_app.get("/api/approvals/policies")
    assert r.status_code == 200
    assert r.get_json() == {"policies": [], "compiled": [],
                            "path": str(ap.POLICIES_PATH), "exists": False}

    rules = [
        {"name": "Block force pushes", "tool": "exec",
         "pattern_type": "command_regex",
         "pattern": r"git\s+push.*--force", "action": "require_approval",
         "timeout": 120, "on_timeout": "deny", "preset_key": "force_push"},
        {"name": "cc write gate", "tool": "write", "runtime": "claude_code",
         "action": "require_approval", "timeout": 60,
         "on_timeout": "approve"},
    ]
    r = policy_app.put("/api/approvals/policies",
                       json={"policies": rules})
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["ok"] is True and body["count"] == 2
    names = [c["name"] for c in body["compiled"]]
    assert names == ["Block force pushes", "cc write gate"]
    assert body["compiled"][1]["runtime"] == "claude_code"
    assert body["compiled"][0]["command_regex"] == r"git\s+push.*--force"

    # File round-trips through the engine's own loader.
    assert ap.POLICIES_PATH.exists()
    loaded = ap.load_policies()
    assert [p["name"] for p in loaded] == ["Block force pushes",
                                           "cc write gate"]
    assert loaded[0]["command_regex"].search("git push origin --force")

    # GET reflects the write.
    r = policy_app.get("/api/approvals/policies")
    got = r.get_json()
    assert got["exists"] is True
    assert [p["name"] for p in got["policies"]] == [
        "Block force pushes", "cc write gate"]
    assert got["policies"][0]["preset_key"] == "force_push"


def test_policies_put_validation_failure_writes_nothing(policy_app,
                                                        approvals_mod):
    ap = approvals_mod
    # Seed a good file first, then try to clobber it with a bad list.
    ok = policy_app.put("/api/approvals/policies", json={"policies": [
        {"name": "good", "tool": "exec", "pattern_type": "command_regex",
         "pattern": "rm", "action": "require_approval"}]})
    assert ok.status_code == 200
    before = ap.POLICIES_PATH.read_text()

    bad = [
        {"name": "bad regex", "tool": "exec",
         "pattern_type": "command_regex", "pattern": "rm(("},
        {"name": "bad action", "tool": "exec", "action": "require_aproval"},
        {"name": "bad timeout", "tool": "exec", "timeout": "soon"},
    ]
    r = policy_app.put("/api/approvals/policies", json={"policies": bad})
    assert r.status_code == 400
    errs = " | ".join(r.get_json()["errors"])
    assert "bad regex" in errs and "action must be one of" in errs \
        and "timeout must be an integer" in errs
    # And the previous file survived untouched.
    assert ap.POLICIES_PATH.read_text() == before

    r = policy_app.put("/api/approvals/policies", json={})
    assert r.status_code == 400
    r = policy_app.put("/api/approvals/policies",
                       json={"policies": "not-a-list"})
    assert r.status_code == 400


# ── 3. POST /api/hooks/claude-code/pretooluse ──────────────────────────────


@pytest.fixture
def hooks_app(fresh_store, approvals_mod, monkeypatch):
    _pin_entitlement(monkeypatch)
    _no_daemon_proxy(monkeypatch)
    import routes.hooks as rh
    from routes.hooks import bp_hooks
    app = Flask(__name__)
    app.register_blueprint(bp_hooks)
    return app.test_client(), rh, fresh_store, approvals_mod


def _write_policy_yaml(ap, *, tool="exec", pattern="rm", timeout=2,
                       on_timeout="deny", name="block-rm"):
    ap.POLICIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    ap.POLICIES_PATH.write_text(
        f"- name: '{name}'\n"
        f"  tool: '{tool}'\n"
        f"  pattern_type: 'command_regex'\n"
        f"  pattern: '{pattern}'\n"
        f"  action: 'require_approval'\n"
        f"  timeout: {timeout}\n"
        f"  on_timeout: '{on_timeout}'\n"
    )


def test_hook_receiver_allows_when_no_policy(hooks_app):
    client, rh, ls, ap = hooks_app
    r = client.post("/api/hooks/claude-code/pretooluse", json={
        "tool_name": "Bash", "tool_input": {"command": "ls"},
        "session_id": "s1", "cwd": "/tmp"})
    assert r.status_code == 200
    hso = r.get_json()["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "allow"
    assert "no matching policy" in hso["permissionDecisionReason"]
    # Nothing parked in the queue.
    assert ls.get_store().query_approvals(status="pending", limit=10) == []


def test_hook_receiver_deny_after_human_decision(hooks_app):
    client, rh, ls, ap = hooks_app
    _write_policy_yaml(ap, timeout=30)

    def _flip():
        deadline = time.time() + 10
        while time.time() < deadline:
            rows = ls.get_store().query_approvals(status="pending", limit=10)
            if rows:
                ls.get_store().update_approval_decision(
                    rows[0]["id"], "deny", "local", "not on prod")
                return
            time.sleep(0.1)
    t = threading.Thread(target=_flip, daemon=True)
    t.start()
    r = client.post("/api/hooks/claude-code/pretooluse", json={
        "tool_name": "Bash", "tool_input": {"command": "rm -rf /data"},
        "session_id": "sess-42", "cwd": "/tmp", "tool_use_id": "tu-1"})
    t.join(timeout=15)
    assert r.status_code == 200
    body = r.get_json()
    hso = body["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny"
    assert "block-rm" in hso["permissionDecisionReason"]
    assert "not on prod" in hso["permissionDecisionReason"]
    # The row is the SAME one the Approvals tab queue serves, resolved.
    rows = ls.get_store().query_approvals(limit=10)
    assert len(rows) == 1
    assert rows[0]["status"] == "denied"
    assert rows[0]["requestor_session_id"] == "claude_code:sess-42"
    assert rows[0]["args"]["source"] == "pretooluse-hook"
    assert rows[0]["args"]["runtime"] == "claude_code"


def test_hook_receiver_pending_resume_and_approve(hooks_app, monkeypatch):
    client, rh, ls, ap = hooks_app
    monkeypatch.setattr(rh, "_WAIT_SLICE_S", 0.3)
    _write_policy_yaml(ap, timeout=60)
    r = client.post("/api/hooks/claude-code/pretooluse", json={
        "tool_name": "Bash", "tool_input": {"command": "rm -rf x"},
        "session_id": "s9", "tool_use_id": "tu-9"})
    body = r.get_json()
    assert body["status"] == "pending"
    aid = body["approval_id"]
    assert aid

    # A duplicate first-POST (client-side timeout retry, no approval_id)
    # must reuse the parked row via tool_use_id, not file a second one.
    monkeypatch.setattr(rh, "_WAIT_SLICE_S", 0.1)
    r2 = client.post("/api/hooks/claude-code/pretooluse", json={
        "tool_name": "Bash", "tool_input": {"command": "rm -rf x"},
        "session_id": "s9", "tool_use_id": "tu-9"})
    assert r2.get_json()["approval_id"] == aid
    assert len(ls.get_store().query_approvals(limit=10)) == 1

    ls.get_store().update_approval_decision(aid, "approve", "local", None)
    r3 = client.post("/api/hooks/claude-code/pretooluse", json={
        "approval_id": aid, "tool_name": "Bash"})
    hso = r3.get_json()["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    assert "Approved by the human" in hso["permissionDecisionReason"]


@pytest.mark.parametrize("on_timeout,expected", [
    ("deny", "deny"), ("kill", "deny"), ("allow", "allow"),
    ("approve", "allow"), ("ask", "ask"),
])
def test_hook_receiver_timeout_mapping(hooks_app, on_timeout, expected):
    client, rh, ls, ap = hooks_app
    _write_policy_yaml(ap, timeout=1, on_timeout=on_timeout,
                       name=f"t-{on_timeout}")
    r = client.post("/api/hooks/claude-code/pretooluse", json={
        "tool_name": "Bash", "tool_input": {"command": "rm -rf y"},
        "session_id": "s1"})
    hso = r.get_json()["hookSpecificOutput"]
    assert hso["permissionDecision"] == expected
    assert "timed out" in hso["permissionDecisionReason"]
    # Row left the pending queue (timeout resolution recorded).
    assert ls.get_store().query_approvals(status="pending", limit=10) == []


def test_hook_receiver_rejects_non_loopback(hooks_app):
    client, rh, ls, ap = hooks_app
    r = client.post("/api/hooks/claude-code/pretooluse", json={},
                    environ_overrides={"REMOTE_ADDR": "10.0.0.9"})
    assert r.status_code == 403


def test_hook_receiver_unentitled_is_explicit_allow(hooks_app, monkeypatch):
    client, rh, ls, ap = hooks_app
    _pin_entitlement(monkeypatch, features=())  # approval_queue NOT allowed
    _write_policy_yaml(ap)
    r = client.post("/api/hooks/claude-code/pretooluse", json={
        "tool_name": "Bash", "tool_input": {"command": "rm -rf /"}})
    hso = r.get_json()["hookSpecificOutput"]
    assert hso["permissionDecision"] == "allow"
    assert "not entitled" in hso["permissionDecisionReason"]


# ── 4. claude_code_gate installer + CLI client ─────────────────────────────


@pytest.fixture
def cc_gate(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
    monkeypatch.setenv("CLAWMETRY_DASHBOARD_BASE", "http://127.0.0.1:8900")
    import clawmetry.claude_code_gate as ccg
    monkeypatch.setattr(ccg, "_STATE_PATH",
                        str(tmp_path / "claude_code_gate.json"))
    monkeypatch.setattr(ccg, "_SERVER_INFO_PATH",
                        str(tmp_path / "server.json"))
    monkeypatch.setattr(ccg, "_MARKER_PATH",
                        str(tmp_path / "hooks_installed.json"))
    return ccg, tmp_path / "claude" / "settings.json"


def _seed_settings(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


_FOREIGN = {
    "model": "opus",
    "hooks": {
        "PreToolUse": [
            {"matcher": "Bash",
             "hooks": [{"type": "command", "command": "my-linter"}]},
        ],
        "Stop": [{"hooks": [{"type": "command", "command": "notify-send"}]}],
    },
}


def test_cc_gate_install_merges_and_uninstall_removes_only_ours(cc_gate):
    ccg, settings_path = cc_gate
    _seed_settings(settings_path, _FOREIGN)
    pol = [{"name": "p", "tool": "exec", "action": "require_approval",
            "timeout": 120, "on_timeout": "deny"}]

    ccg.gate_handler(True, pol)
    s = json.loads(settings_path.read_text())
    pre = s["hooks"]["PreToolUse"]
    assert len(pre) == 2
    assert pre[0]["hooks"][0]["command"] == "my-linter"  # foreign preserved
    ours = pre[1]
    assert ours["matcher"] == "Bash"
    cmd = ours["hooks"][0]["command"]
    assert ccg.HOOK_CMD_MARKER in cmd
    assert "--base http://127.0.0.1:8900" in cmd
    assert cmd.startswith(sys.executable)
    assert ours["hooks"][0]["timeout"] == 120 + 60  # policy + buffer
    assert s["model"] == "opus"                     # rest of file untouched
    st = json.loads(open(ccg._STATE_PATH).read())
    assert st["installed"] is True
    # Marker tells the reactive watcher claude_code is now hook-covered
    # (approvals._hook_covered_runtimes) — no double-gating.
    marker = json.loads(open(ccg._MARKER_PATH).read())
    assert "PreToolUse" in marker["claude_code"]["events"]
    assert marker["claude_code"]["via"] == "gate"

    # Idempotent: second sync is a byte-for-byte no-op.
    before = settings_path.read_text()
    ccg.gate_handler(True, pol)
    assert settings_path.read_text() == before

    # Policy set changes → OUR entry is refreshed in place, still one copy.
    pol2 = [{"name": "p", "tool": "write", "action": "require_approval",
             "timeout": 60, "on_timeout": "deny"}]
    ccg.gate_handler(True, pol2)
    s = json.loads(settings_path.read_text())
    ours = [e for e in s["hooks"]["PreToolUse"]
            if ccg._entry_is_ours(e)]
    assert len(ours) == 1
    assert ours[0]["matcher"] == "Write|Edit|MultiEdit|NotebookEdit"

    # No policy wants the gate → only ours removed; foreign + Stop intact.
    ccg.gate_handler(False, [])
    s = json.loads(settings_path.read_text())
    assert s["hooks"]["PreToolUse"] == _FOREIGN["hooks"]["PreToolUse"]
    assert s["hooks"]["Stop"] == _FOREIGN["hooks"]["Stop"]
    assert not os.path.exists(ccg._STATE_PATH)
    # Marker entry removed with it — reactive watcher resumes coverage.
    assert "claude_code" not in json.loads(open(ccg._MARKER_PATH).read())

    # Uninstall again (no state) → no-op, never raises.
    ccg.gate_handler(False, [])


def test_cc_gate_does_not_stack_on_manual_cloud_hook(cc_gate):
    ccg, settings_path = cc_gate
    manual = {"hooks": {"PreToolUse": [
        {"matcher": "*",
         "hooks": [{"type": "command",
                    "command": "clawmetry hooks run pretooluse",
                    "timeout": 605100}]}]}}
    _seed_settings(settings_path, manual)
    # Simulate the manual install's marker (owned by the user, no via tag).
    with open(ccg._MARKER_PATH, "w") as f:
        json.dump({"claude_code": {"events": ["PreToolUse", "Notification",
                                              "Stop"]}}, f)
    before = settings_path.read_text()
    marker_before = open(ccg._MARKER_PATH).read()
    ccg.gate_handler(True, [{"name": "p", "tool": "exec",
                             "action": "require_approval"}])
    assert settings_path.read_text() == before  # no second gate stacked
    assert open(ccg._MARKER_PATH).read() == marker_before  # theirs, untouched
    # And a later "no gate wanted" must NOT strip the manual hook/marker.
    ccg.gate_handler(False, [])
    assert settings_path.read_text() == before
    assert open(ccg._MARKER_PATH).read() == marker_before


def test_cc_gate_matcher_and_timeout_derivation(cc_gate):
    ccg, _ = cc_gate
    P = lambda **kw: dict({"action": "require_approval"}, **kw)
    assert ccg._matcher_from_policies([P(tool="exec")]) == "Bash"
    assert ccg._matcher_from_policies([P(tool="")]) == "Bash"
    assert ccg._matcher_from_policies([P(tool="shell")]) == "Bash"
    assert ccg._matcher_from_policies([]) == "Bash"
    assert ccg._matcher_from_policies(
        [P(tool="exec"), P(tool="web")]) == "Bash|WebFetch|WebSearch"
    # Unknown explicit tool name passes through verbatim (MCP tools).
    assert ccg._matcher_from_policies(
        [P(tool="mcp__github__push")]) == "mcp__github__push"
    # approve/monitor rules don't widen the matcher.
    assert ccg._matcher_from_policies(
        [P(tool="web", action="monitor"), P(tool="exec")]) == "Bash"
    assert ccg._timeout_from_policies(
        [P(timeout=30), P(timeout=90)]) == 90 + 60
    assert ccg._timeout_from_policies([]) == 604800 + 60


def test_cc_gate_dashboard_base_discovery(cc_gate, monkeypatch):
    ccg, _ = cc_gate
    assert ccg.dashboard_base() == "http://127.0.0.1:8900"
    monkeypatch.delenv("CLAWMETRY_DASHBOARD_BASE")
    with open(ccg._SERVER_INFO_PATH, "w") as f:
        json.dump({"port": 9123, "pid": 1}, f)
    assert ccg.dashboard_base() == "http://127.0.0.1:9123"
    os.remove(ccg._SERVER_INFO_PATH)
    assert ccg.dashboard_base() == "http://127.0.0.1:8900"  # default


def test_cli_hook_fail_open_on_unreachable_server(cc_gate, monkeypatch,
                                                  capsys):
    ccg, _ = cc_gate
    monkeypatch.setattr(ccg, "_MAX_TRANSIENT_FAILURES", 2)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(json.dumps({"tool_name": "Bash",
                                "tool_input": {"command": "rm -rf /"},
                                "session_id": "s", "cwd": "/tmp"})))
    # Port 9 (discard) on localhost: nothing listens there.
    rc = ccg.hook_main(["claude-code", "--base", "http://127.0.0.1:9"])
    out = capsys.readouterr().out
    assert rc == 0
    assert out == ""  # NO output = no opinion = fail-open


def test_cli_hook_garbage_stdin_fails_open(cc_gate, monkeypatch, capsys):
    ccg, _ = cc_gate
    monkeypatch.setattr("sys.stdin", io.StringIO("not json {"))
    rc = ccg.hook_main(["claude-code", "--base", "http://127.0.0.1:9"])
    assert rc == 0
    assert capsys.readouterr().out == ""


def test_cli_hook_prints_server_decision(cc_gate, monkeypatch, capsys):
    ccg, _ = cc_gate
    responses = [
        {"status": "pending", "approval_id": "a1", "retry_after_ms": 1},
        {"status": "decided",
         "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                "permissionDecision": "deny",
                                "permissionDecisionReason": "nope"}},
    ]
    posted = []

    def _fake_post(url, payload, timeout):
        posted.append(dict(payload))
        return responses.pop(0)
    monkeypatch.setattr(ccg, "_post_json", _fake_post)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(json.dumps({"tool_name": "Bash",
                                "tool_input": {"command": "rm -rf /"}})))
    rc = ccg.hook_main(["claude-code", "--base", "http://x"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    # Resume POST carried the approval_id (no duplicate row server-side).
    assert posted[1]["approval_id"] == "a1"
