"""Exact approval identity and protected waits (AC-GOV-SBG-001.1/.2/.3).

AC-GOV-SBG-004.4: these regressions exercise substituted actions and service
interruption without executing any tool or signaling a live session.

AC-GOV-SBG-001.1: resume and dedupe reject complete-action substitution.
AC-GOV-SBG-001.2: protected pending calls deny on failed persistence or transport.
AC-GOV-SBG-001.3: absent authority preserves native permission checks.
"""
from __future__ import annotations

import copy
import io
import json
from types import SimpleNamespace

import pytest
from flask import Flask


@pytest.fixture
def receiver(monkeypatch):
    import routes.hooks as hooks
    from clawmetry import approval_events, approvals, entitlements

    rows = {}
    monkeypatch.setattr(entitlements, "get_entitlement", lambda: SimpleNamespace(
        allows_feature=lambda key: True))
    monkeypatch.setattr(approvals, "load_policies", lambda: [approvals._compile_policy({
        "name": "Review commands", "tool": "", "pattern": ".*",
        "action": "require_approval", "timeout": 60, "on_timeout": "deny"})])
    monkeypatch.setattr(hooks, "_WAIT_SLICE_S", 0)
    monkeypatch.setattr(hooks, "_audit", lambda *a, **kw: None)
    monkeypatch.setattr(hooks, "_page_human", lambda *a, **kw: None)
    monkeypatch.setattr(hooks, "_mark_waiting", lambda *a: None)
    monkeypatch.setattr(hooks, "_clear_waiting", lambda *a: None)
    monkeypatch.setattr(approval_events, "mirror_wanted", lambda runtime: True)
    monkeypatch.setattr(approval_events, "mirror_window_s", lambda runtime: 60)
    monkeypatch.setattr(hooks, "_find_approval", lambda aid: copy.deepcopy(rows.get(aid)))
    monkeypatch.setattr(hooks, "_ls_read", lambda method, **kw: [
        copy.deepcopy(row) for row in rows.values()
        if not kw.get("status") or row["status"] == kw["status"]])

    def write(method, **kw):
        if method == "ingest_approval":
            row = copy.deepcopy(kw["approval"])
            rows[row["id"]] = row
        elif method == "update_approval_decision":
            row = rows[kw["approval_id"]]
            row["status"] = {"approve": "approved", "deny": "denied"}.get(
                kw["decision"], kw["decision"])
        return True

    monkeypatch.setattr(hooks, "_ls_write", write)
    app = Flask(__name__)
    app.register_blueprint(hooks.bp_hooks)
    return app.test_client(), hooks, rows


def payload(**changes):
    return {"tool_name": "Bash", "tool_input": {"command": "echo reviewed", "env": {"A": "one"}},
            "session_id": "s1", "tool_use_id": "call1", "cwd": "/workspace", **changes}


def verdict(response):
    body = response.get_json()
    if body.get("status") == "no_op":
        assert "hookSpecificOutput" not in body
        return "no_op"
    out = body["hookSpecificOutput"]
    return out.get("permissionDecision") or out.get("decision")


@pytest.mark.parametrize("mirror", [False, True])
@pytest.mark.parametrize("change", [
    {"session_id": "another"}, {"tool_name": "Write"},
    {"tool_input": {"command": "echo replaced", "env": {"A": "one"}}},
    {"tool_input": {"command": "echo reviewed", "env": {"A": "two"}}},
    {"cwd": "/another"}, {"tool_use_id": "another-call"},
])
def test_resume_rejects_action_substitution(receiver, mirror, change):
    """AC-GOV-SBG-001.1: a human verdict belongs to the complete invocation."""
    client, _, rows = receiver
    path = "/api/hooks/claude-code/" + ("permissionrequest" if mirror else "pretooluse")
    initial = client.post(path, json=payload()).get_json()
    aid = initial["approval_id"]
    rows[aid]["status"] = "approved"
    assert verdict(client.post(path, json=payload(approval_id=aid))) == "allow"
    assert verdict(client.post(path, json=payload(approval_id=aid, **change))) != "allow"


def test_resume_cannot_cross_runtime_or_approval_kind(receiver):
    client, _, rows = receiver
    aid = client.post("/api/hooks/claude-code/pretooluse", json=payload()).get_json()["approval_id"]
    rows[aid]["status"] = "approved"
    assert verdict(client.post("/api/hooks/copilot/pretooluse", json=payload(approval_id=aid))) == "deny"
    assert verdict(client.post("/api/hooks/claude-code/permissionrequest", json=payload(approval_id=aid))) != "allow"


@pytest.mark.parametrize("mirror", [False, True])
@pytest.mark.parametrize("change", [
    {"session_id": "another"}, {"tool_input": {"command": "changed"}}, {"cwd": "/another"},
])
def test_pending_dupe_requires_complete_identity(receiver, mirror, change):
    client, _, _ = receiver
    path = "/api/hooks/claude-code/" + ("permissionrequest" if mirror else "pretooluse")
    aid = client.post(path, json=payload()).get_json()["approval_id"]
    response = client.post(path, json=payload(**change)).get_json()
    assert response.get("approval_id") != aid


def test_distinct_invocations_without_native_ids_do_not_share_review(receiver):
    client, _, rows = receiver
    path = "/api/hooks/copilot/pretooluse"
    first = payload(tool_use_id="", invocation_id="process-one")
    aid = client.post(path, json=first).get_json()["approval_id"]
    assert client.post(path, json=first).get_json()["approval_id"] == aid
    other = dict(first, invocation_id="process-two")
    assert client.post(path, json=other).get_json()["approval_id"] != aid
    rows[aid]["status"] = "approved"
    assert verdict(client.post(path, json=dict(other, approval_id=aid))) == "deny"


def test_matched_policy_store_failure_denies(receiver, monkeypatch):
    """AC-GOV-SBG-001.2: a declared protection survives persistence failure."""
    client, hooks, _ = receiver
    monkeypatch.setattr(hooks, "_ls_write", lambda *a, **kw: False)
    assert verdict(client.post("/api/hooks/claude-code/pretooluse", json=payload())) == "deny"


def test_missing_pending_row_never_allows(receiver):
    client, _, _ = receiver
    assert verdict(client.post("/api/hooks/claude-code/pretooluse", json=payload(approval_id="gone"))) == "deny"


@pytest.mark.parametrize("invalid", ["reviewed action", ["one"], None, 1])
@pytest.mark.parametrize("mirror", [False, True])
def test_invalid_arguments_cannot_collapse_into_an_empty_object(receiver, invalid, mirror):
    client, _, rows = receiver
    path = "/api/hooks/claude-code/" + ("permissionrequest" if mirror else "pretooluse")
    response = client.post(path, json=payload(tool_input=invalid))
    assert verdict(response) == ("ask" if mirror else "deny")
    assert not rows
    aid = client.post(path, json=payload(tool_input={})).get_json()["approval_id"]
    rows[aid]["status"] = "approved"
    assert verdict(client.post(path, json=payload(approval_id=aid, tool_input=invalid))) != "allow"


@pytest.mark.parametrize("failure", ["exception", "resolver_error"])
@pytest.mark.parametrize("mirror", [False, True])
def test_entitlement_failure_does_not_create_authority(receiver, monkeypatch, failure, mirror):
    """AC-GOV-SBG-001.3: preserve the existing entitlement fallback."""
    from clawmetry import entitlements
    client, hooks, _ = receiver
    if failure == "exception":
        monkeypatch.setattr(entitlements, "get_entitlement", lambda: (_ for _ in ()).throw(OSError()))
    else:
        monkeypatch.setattr(entitlements, "get_entitlement", lambda: SimpleNamespace(
            source="resolver_error", allows_feature=lambda key: True))
    monkeypatch.setattr(hooks, "_ls_write", lambda *a, **kw: False)
    path = "/api/hooks/claude-code/" + ("permissionrequest" if mirror else "pretooluse")
    assert verdict(client.post(path, json=payload())) == ("ask" if mirror else "no_op")


@pytest.mark.parametrize("mode", ["no_policy", "unentitled", "monitor"])
def test_observation_does_not_override_native_permissions(receiver, monkeypatch, mode):
    """AC-GOV-SBG-001.3: no policy authority means neither deny nor allow."""
    from clawmetry import approvals, entitlements
    client, _, _ = receiver
    if mode == "no_policy":
        monkeypatch.setattr(approvals, "load_policies", lambda: [])
    elif mode == "unentitled":
        monkeypatch.setattr(entitlements, "get_entitlement", lambda: SimpleNamespace(
            allows_feature=lambda key: False))
    else:
        monkeypatch.setattr(approvals, "load_policies", lambda: [approvals._compile_policy({
            "name": "watch", "action": "monitor"})])
    assert verdict(client.post("/api/hooks/claude-code/pretooluse", json=payload())) == "no_op"


@pytest.mark.parametrize("tool,a,b", [
    ("Write", {"file_path": "/w/auth.py", "content": "reviewed"},
     {"file_path": "/w/auth.py", "content": "replacement"}),
    ("Bash", {"command": "./deploy", "cwd": "/dev"}, {"command": "./deploy", "cwd": "/prod"}),
])
def test_remembered_grant_binds_full_arguments(tool, a, b, tmp_path, monkeypatch):
    from clawmetry import approvals
    monkeypatch.setattr(approvals, "_SESSION_ALLOW_PATH", tmp_path / "allows.json")
    approvals.add_session_allow("claude_code:s", tool, a)
    assert approvals.check_session_allow("claude_code:s", tool, a)
    assert not approvals.check_session_allow("claude_code:s", tool, b)


@pytest.mark.parametrize("runtime", ["claude-code", "cursor", "copilot"])
@pytest.mark.parametrize("failure", [None, {}, {"hookSpecificOutput": {"permissionDecision": "bogus"}}])
def test_pending_transport_failure_denies(runtime, failure, monkeypatch, capsys):
    """AC-GOV-SBG-001.2: interruption cannot silently release a protected call."""
    from clawmetry import claude_code_gate as cc, runtime_gates as rt
    module = cc if runtime == "claude-code" else rt
    event = payload() if runtime == "claude-code" else (
        {"command": "echo reviewed", "conversation_id": "s1"} if runtime == "cursor" else
        {"toolName": "shell", "toolArgs": {"command": "echo reviewed"}, "sessionId": "s1"})
    responses = iter([{"status": "pending", "approval_id": "a1", "retry_after_ms": 1, "wait_budget_s": 60},
                      failure, failure, failure])
    monkeypatch.setattr(module, "_post_json", lambda *a: next(responses))
    monkeypatch.setattr(module.time, "sleep", lambda _: None)
    monkeypatch.setattr(module.sys, "stdin", io.StringIO(json.dumps(event)))
    assert module.hook_main([runtime, "--base", "http://127.0.0.1:9999"]) == 0
    out = json.loads(capsys.readouterr().out)
    decision = out.get("permission") or out.get("permissionDecision") or out["hookSpecificOutput"]["permissionDecision"]
    assert decision == "deny"


def test_digest_preserves_json_types_order_and_context():
    from clawmetry.approval_binding import action_digest
    args = {"a": [1, True, "x"], "b": {"x": None}}
    first = action_digest("r", "s", "Write", args, "/w", "call")
    assert first == action_digest("r", "s", "Write", {"b": {"x": None}, "a": [1, True, "x"]}, "/w", "call")
    for replacement in ({"a": [True, 1, "x"], "b": {"x": None}},
                        {"a": [1, True, "x"], "b": {"x": "None"}}):
        assert first != action_digest("r", "s", "Write", replacement, "/w", "call")
    assert first != action_digest("r", "s", "Edit", args, "/w", "call")


@pytest.mark.parametrize("args", [
    {"x": float("nan")}, {"x": float("inf")}, {"x": (1, 2)}, {1: "value"},
    {"x": object()}, {"x": "z" * (1024 * 1024 + 1)},
])
def test_uninspectable_arguments_never_yield_a_grant(args, tmp_path, monkeypatch):
    from clawmetry import approvals
    from clawmetry.approval_binding import action_digest
    monkeypatch.setattr(approvals, "_SESSION_ALLOW_PATH", tmp_path / "allows.json")
    assert action_digest("r", "s", "Write", args) is None
    assert approvals.add_session_allow("r:s", "Write", args) == ""
    assert not approvals.check_session_allow("r:s", "Write", args)


def test_aggregate_input_budget_rejects_before_serialization(monkeypatch):
    from clawmetry import approval_binding

    def serialize(*a, **kw):
        raise AssertionError("Oversized aggregate must not reach serialization")

    monkeypatch.setattr(approval_binding.json, "dumps", serialize)
    assert approval_binding.action_digest("r", "s", "Write", {"a": "x" * 600000, "b": "y" * 600000}) is None


def test_separate_cwd_and_exact_tool_name_bound_in_remembered_grant(tmp_path, monkeypatch):
    from clawmetry import approvals
    monkeypatch.setattr(approvals, "_SESSION_ALLOW_PATH", tmp_path / "allows.json")
    args = {"command": "./deploy"}
    approvals.add_session_allow("r:s", "Bash", args, cwd="/dev")
    assert approvals.check_session_allow("r:s", "Bash", args, cwd="/dev")
    assert not approvals.check_session_allow("r:s", "Bash", args, cwd="/prod")
    assert not approvals.check_session_allow("r:s", "exec", args, cwd="/dev")


@pytest.mark.parametrize("mirror", [False, True])
def test_native_review_interruption_returns_ask(mirror, monkeypatch, capsys):
    from clawmetry import claude_code_gate as cc
    event = payload(tool_name="Bash" if mirror else "AskUserQuestion")
    responses = iter([{"status": "pending", "approval_id": "a1", "wait_budget_s": 60}, None])
    monkeypatch.setattr(cc, "_post_json", lambda *a: next(responses))
    monkeypatch.setattr(cc.time, "sleep", lambda _: None)
    monkeypatch.setattr(cc.sys, "stdin", io.StringIO(json.dumps(event)))
    target = "claude-code-permission" if mirror else "claude-code"
    assert cc.hook_main([target]) == 0
    out = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert out.get("decision") == "ask" if mirror else out["permissionDecision"] == "ask"


@pytest.mark.parametrize("runtime", ["claude-code", "cursor", "copilot"])
def test_pending_budget_emits_deny_before_native_timeout(runtime, monkeypatch, capsys):
    from clawmetry import claude_code_gate as cc, runtime_gates as rt
    module = cc if runtime == "claude-code" else rt
    ticks = {"now": 100.0}
    monkeypatch.setattr(module.time, "monotonic", lambda: ticks["now"])
    monkeypatch.setattr(module.time, "sleep", lambda seconds: ticks.update(now=ticks["now"] + seconds))
    monkeypatch.setattr(module.sys, "stdin", io.StringIO(json.dumps(payload())))
    requests = []

    def post(url, args, timeout):
        requests.append(timeout)
        return {"status": "pending", "approval_id": "a1", "wait_budget_s": 1, "retry_after_ms": 2000}

    monkeypatch.setattr(module, "_post_json", post)
    assert module.hook_main([runtime]) == 0
    out = json.loads(capsys.readouterr().out)
    decision = out.get("permission") or out.get("permissionDecision") or out["hookSpecificOutput"]["permissionDecision"]
    assert decision == "deny"
    assert ticks["now"] == 101.0
    assert len(requests) == 1


def test_cursor_mcp_json_parameters_survive_normalization():
    from clawmetry.runtime_gates import _cursor_payload
    event = {"tool_name": "mcp__server__send", "tool_input": '{"destination":"reviewed","body":"one"}'}
    assert _cursor_payload(event)["tool_input"] == {"destination": "reviewed", "body": "one"}
    event["tool_input"] = "malformed-json"
    assert _cursor_payload(event)["tool_input"] == "malformed-json"
    assert _cursor_payload(event)["tool_input"] != _cursor_payload(dict(
        event, tool_input={"raw": "malformed-json"}))["tool_input"]


@pytest.mark.parametrize("budget", [None, 0, -1, float("nan"), float("inf"), "bad"])
def test_invalid_pending_budget_cannot_wait_until_native_timeout(budget):
    from clawmetry.approval_binding import pending_deadline
    assert pending_deadline({"wait_budget_s": budget}, 100, None, 60) == 100


def test_pending_budget_cannot_exceed_installed_timeout():
    from clawmetry.approval_binding import pending_deadline
    assert pending_deadline({"wait_budget_s": 10 ** 100}, 100, None, 55) == 155
    assert pending_deadline({"wait_budget_s": 10 ** 100}, 100, 120, 55) == 120


@pytest.mark.parametrize("runtime", ["claude-code", "cursor", "copilot"])
def test_no_op_response_emits_no_native_permission_override(runtime, monkeypatch, capsys):
    from clawmetry import claude_code_gate as cc, runtime_gates as rt
    module = cc if runtime == "claude-code" else rt
    monkeypatch.setattr(module, "_post_json", lambda *a: {"status": "no_op", "reason": "No policy matched."})
    monkeypatch.setattr(module.sys, "stdin", io.StringIO(json.dumps(payload())))
    assert module.hook_main([runtime]) == 0
    assert capsys.readouterr().out == ""


def test_hook_http_has_separate_connect_and_read_timeouts(monkeypatch):
    import http.client
    from clawmetry import claude_code_gate as cc
    observed = {}

    class Connection:
        sock = SimpleNamespace(settimeout=lambda seconds: observed.update(read_timeout=seconds))

        def __init__(self, host, port, timeout):
            observed.update(connect_timeout=timeout)

        def connect(self):
            pass

        def request(self, *a, **kw):
            pass

        def getresponse(self):
            return SimpleNamespace(status=200, read=lambda cap: b'{"status":"pending"}')

        def close(self):
            observed["closed"] = True

    monkeypatch.setattr(http.client, "HTTPConnection", Connection)
    assert cc._post_json("http://127.0.0.1:9999/pretool", {}, 45) == {"status": "pending"}
    assert observed["connect_timeout"] == 3
    assert 44 <= observed["read_timeout"] <= 45
    assert observed["closed"] is True


def test_slow_response_cannot_extend_the_hook_read_deadline():
    import http.server
    import threading
    import time
    from clawmetry import claude_code_gate as cc

    class SlowReply(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            try:
                for part in b'{"status":"pending"}':
                    self.wfile.write(bytes([part]))
                    self.wfile.flush()
                    time.sleep(0.02)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), SlowReply)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    started = time.monotonic()
    try:
        assert cc._post_json("http://127.0.0.1:%s/" % server.server_port, {}, 0.08) is None
        assert time.monotonic() - started < 0.4
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def test_legacy_approval_cache_does_not_share_a_call_id_between_actions(monkeypatch):
    from clawmetry import approvals, local_store
    monkeypatch.setattr(approvals, "_in_flight", {})
    monkeypatch.setattr(approvals, "_session_cwd", lambda sid: "")
    monkeypatch.setattr(local_store, "get_store", lambda **kw: SimpleNamespace(ingest_approval=lambda row: None))
    policy = approvals._compile_policy({"name": "explicit allow", "action": "approve", "pattern": ".*"})
    common = dict(api_key="cm-test", node_id="node", tool_call_id="one-call", tool_name="Bash", policies=[policy])
    a = approvals.process_tool_call(session_id="claude_code:one", args={"command": "echo one"}, **common)
    b = approvals.process_tool_call(session_id="claude_code:two", args={"command": "echo one"}, **common)
    c = approvals.process_tool_call(session_id="claude_code:one", args={"command": "echo changed"}, **common)
    assert len({a["approval_id"], b["approval_id"], c["approval_id"]}) == 3


@pytest.mark.parametrize("failure", ["persistence", "cloud", "poll"])
@pytest.mark.parametrize("entitlement", [True, False, "error"])
def test_legacy_protected_hook_failure_respects_entitlement(failure, entitlement, monkeypatch):
    from clawmetry import approvals, approval_events, entitlements, local_store
    monkeypatch.setattr(approvals, "_in_flight", {})
    monkeypatch.setattr(approvals, "_session_cwd", lambda sid: "")
    monkeypatch.setattr(approvals, "_local_blocking_enabled", lambda key: False)
    monkeypatch.setattr(approval_events, "notify_pending", lambda payload: None)

    def entitled():
        if entitlement == "error":
            raise OSError("license unavailable")
        return SimpleNamespace(allows_feature=lambda key: entitlement)

    def persist(row):
        if failure == "persistence":
            raise OSError("store unavailable")

    monkeypatch.setattr(entitlements, "get_entitlement", entitled)
    monkeypatch.setattr(local_store, "get_store", lambda **kw: SimpleNamespace(ingest_approval=persist))
    monkeypatch.setattr(approvals, "_post_approval_request", lambda *a: None if failure != "poll" else {"id": "a"})
    monkeypatch.setattr(approvals, "_poll_decision", lambda *a: "error")
    policy = approvals._compile_policy({"name": "review", "action": "require_approval", "pattern": ".*"})
    out = approvals.process_tool_call(api_key="cm-test", node_id="node", session_id="claude_code:s",
                                     tool_call_id="t", tool_name="Bash", args={"command": "echo reviewed"},
                                     policies=[policy], kill_on_deny=False)
    assert (out["decision"] == "denied") is (entitlement is True)
    assert out["killed"] is False


def test_legacy_duplicate_pending_call_cannot_fall_through(monkeypatch):
    from clawmetry import approvals, entitlements
    from clawmetry.approval_binding import action_digest
    sid, args = "claude_code:s", {"command": "echo reviewed"}
    monkeypatch.setattr(entitlements, "get_entitlement", lambda: SimpleNamespace(
        source="test", allows_feature=lambda key: True))
    key = action_digest(approvals._session_runtime(sid), sid, "Bash", args, "/w", "call", "legacy-hook", "review")
    monkeypatch.setattr(approvals, "_in_flight", {key: {"decision": "pending", "policy": "review", "killed": False}})
    policy = approvals._compile_policy({"name": "review", "action": "require_approval"})
    result = approvals.process_tool_call("cm-test", "node", sid, "call", "Bash", args,
                                         policies=[policy], kill_on_deny=False, cwd="/w")
    assert result["decision"] == "denied"
    assert result["killed"] is False


def test_bound_grant_serialization_fails_safe_on_older_daemons():
    """AC-GOV-SBG-001.1: downgrading cannot discard the exact constraint."""
    from clawmetry import approvals
    from clawmetry.approval_binding import action_digest
    from routes.policy import _serialize_policies_yaml
    tool_input = {'file_path': '/tmp/demo', 'content': 'reviewed'}
    binding = action_digest('claude_code', '', 'Write', tool_input, '/tmp',
                            source='persistent-allow', kind='always')
    raw = {'name': 'exact', 'tool': 'Write', 'runtime': 'claude_code',
           'action': 'approve', 'action_binding': binding}
    serialized = _serialize_policies_yaml([raw])
    reloaded = approvals._load_yaml(serialized)[0]
    assert reloaded['action_binding'] == binding
    assert reloaded['match']['command_regex'] == '(?!)'
    policy = approvals._compile_policy(reloaded)
    assert approvals.match_policy([policy], 'Write', tool_input, runtime='claude_code', cwd='/tmp')
    assert approvals.match_policy([policy], 'Write', {**tool_input, 'content': 'changed'}, runtime='claude_code', cwd='/tmp') is None
    # An older compiler ignores the digest, but its remaining condition is
    # deliberately impossible rather than an accidentally broad allow.
    legacy = {**reloaded, 'match': {k: v for k, v in reloaded['match'].items() if k != 'action_binding'}}
    legacy.pop('action_binding')
    assert approvals.match_policy([approvals._compile_policy(legacy)], 'Write', tool_input) is None


def test_cloud_policy_fetch_advertises_exact_binding_capability(monkeypatch):
    from clawmetry import approvals
    import urllib.request
    requests = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return b'{"policies": []}'
    monkeypatch.setattr(approvals, '_cloud_policies_cache', (0, []))
    monkeypatch.setattr(urllib.request, 'urlopen', lambda request, **kwargs: requests.append(request) or Response())
    assert approvals._fetch_cloud_policies('cm_test') == []
    assert dict((k.lower(), v) for k, v in requests[0].header_items())['x-clawmetry-action-binding'] == 'v1'


def test_session_grants_bind_explicit_runtime_for_native_session_ids(monkeypatch, tmp_path):
    from clawmetry import approvals
    monkeypatch.setattr(approvals, '_SESSION_ALLOW_PATH', tmp_path / 'grants.json')
    args = {'command': 'echo reviewed'}
    approvals.add_session_allow('native-uuid', 'Bash', args, runtime='claude_code')
    assert approvals.check_session_allow('native-uuid', 'Bash', args, runtime='claude_code')
    assert not approvals.check_session_allow('native-uuid', 'Bash', args, runtime='openclaw')


def test_watcher_row_recovers_full_reserved_argument_keys(monkeypatch):
    from clawmetry import approvals, local_store
    from routes.policy import _row_tool_and_args
    rows = []
    monkeypatch.setattr(approvals, '_in_flight', {})
    monkeypatch.setattr(local_store, 'get_store', lambda **kw: SimpleNamespace(ingest_approval=rows.append))
    original = {'command': 'echo reviewed', '_cm_ctx': {'user_field': 'reviewed'}, '_cm_risk': 'original'}
    policy = approvals._compile_policy({'name': 'observe', 'action': 'monitor'})
    approvals.process_tool_call('', 'node', 'native-uuid', 'one', 'Bash', original,
                                policies=[policy], runtime='claude_code', cwd='/workspace')
    tool, recovered = _row_tool_and_args(rows[0])
    assert tool == 'Bash'
    assert recovered == original
