"""Protection reports must describe their evidence without inventing enforcement.
AC-GOV-SBG-004.1: each protection layer reports its own source and status.
AC-GOV-SBG-004.2: missing independent isolation and scanner evidence stays unknown.
AC-GOV-SBG-004.3: scoped source/result records survive local and hosted row transport.
"""
import json
from datetime import datetime, timezone

import pytest


def _row():
    return {"session_id": "claude_code:s1", "runtime": "claude_code",
            "agent_id": "main", "status": "running"}


def test_missing_independent_evidence_is_unknown():
    """AC-GOV-SBG-004.1 AC-GOV-SBG-004.2"""
    from clawmetry.protection_evidence import build
    evidence = build(_row(), now=1000)
    assert evidence["isolation"]["state"] == "unknown"
    assert evidence["code_validation"]["state"] == "unknown"
    assert evidence["pre_tool"]["configuration"]["state"] == "unknown"
    assert evidence["pre_tool"]["last_decision"] is None
    assert evidence["pre_tool"]["execution_verified"] is False
    assert evidence["containment"]["state"] == "unknown"


def test_installation_does_not_establish_execution_or_subprocess_isolation():
    """AC-GOV-SBG-004.1 AC-GOV-SBG-004.2 AC-GOV-SBG-004.4"""
    from clawmetry.protection_evidence import build
    hooks = {"checked_at": 1000000, "runtimes": {"claude_code": {
        "state": "configured", "events": ["PreToolUse"], "matchers": ["Bash"],
        "source": "runtime_hook_configuration"}}}
    evidence = build(_row(), hooks=hooks, now=1000)
    gate = evidence["pre_tool"]
    assert gate["configuration"]["state"] == "configured"
    assert gate["configuration"]["matchers"] == ["Bash"]
    assert gate["last_decision"] is None
    assert gate["execution_verified"] is False
    assert evidence["isolation"]["state"] == "unknown"
    assert gate["initial_service_failure"] == "not_verified"


def _approval(sid="claude_code:s1", runtime="claude_code", source="pretooluse-hook",
              status="denied", kind=None):
    return {"id": "approval-1", "requestor_session_id": sid, "status": status,
            "created_at": "2026-10-26T12:00:00Z", "resolved_at": "2026-10-26T12:00:02Z",
            "args": {"runtime": runtime, "source": source, "kind": kind,
                     "tool_input": {"token": "SECRET-NOT-FOR-COVERAGE", "path": "/Users/customer/secret"}}}


def test_bound_local_decision_is_evidence_of_review_not_actual_execution():
    """AC-GOV-SBG-004.1 AC-GOV-SBG-004.3 AC-GOV-SBG-004.4"""
    from clawmetry.protection_evidence import build
    now = datetime(2026, 10, 26, 12, 0, 5, tzinfo=timezone.utc).timestamp()
    evidence = build(_row(), approvals=[_approval()], now=now)
    decision = evidence["pre_tool"]["last_decision"]
    assert decision["record_id"] == "approval-1"
    assert decision["result"] == "denied"
    assert decision["source"] == "local_pre_tool_approval"
    assert decision["recent"] is True
    assert evidence["pre_tool"]["execution_verified"] is False
    assert "SECRET-NOT-FOR-COVERAGE" not in json.dumps(evidence)
    assert "/Users/customer" not in json.dumps(evidence)


@pytest.mark.parametrize("row", [
    _approval(sid="claude_code:s2"),
    _approval(runtime="copilot"),
    _approval(source="agent_report"),
    _approval(source="permissionrequest-hook", kind="permission_prompt"),
    _approval(kind="question_set"),
    _approval(status="simulated"),
])
def test_unrelated_or_agent_supplied_rows_cannot_verify_a_gate(row):
    """AC-GOV-SBG-004.1 AC-GOV-SBG-004.3"""
    from clawmetry.protection_evidence import build
    assert build(_row(), approvals=[row])["pre_tool"]["last_decision"] is None


def test_stale_configuration_is_not_current():
    """AC-GOV-SBG-004.1"""
    from clawmetry.protection_evidence import build
    hooks = {"checked_at": 1000000, "runtimes": {"claude_code": {
        "state": "configured", "events": ["PreToolUse"]}}}
    assert build(_row(), hooks=hooks, now=1300)["pre_tool"]["configuration"]["state"] == "stale"
    assert build(_row(), hooks=hooks, now=900)["pre_tool"]["configuration"]["state"] == "unknown"


def test_sandbox_configuration_is_scoped_and_never_execution_proof():
    """AC-GOV-SBG-004.2 AC-GOV-SBG-004.3"""
    from clawmetry.protection_evidence import build
    policies = [{"agent_id": "main", "sandbox_mode": "all", "observed_at": 1000000}]
    row = {**_row(), "runtime": "openclaw", "session_id": "s1"}
    evidence = build(row, tool_policies=policies, now=1000)
    assert evidence["isolation"]["state"] == "configured"
    assert evidence["isolation"]["execution_verified"] is False
    assert build(_row(), tool_policies=policies, now=1000)["isolation"]["state"] == "unknown"
    assert build({**row, "agent_id": "other"}, tool_policies=policies, now=1000)["isolation"]["state"] == "unknown"


def test_control_capability_does_not_claim_containment_succeeded():
    """AC-GOV-SBG-004.1 AC-GOV-SBG-004.2"""
    from clawmetry.protection_evidence import build
    evidence = build({**_row(), "controllable": True, "control_actions": ["pause", "stop"]})
    assert evidence["containment"]["state"] == "available"
    assert evidence["containment"]["execution_verified"] is False
    assert evidence["containment"]["actions"] == ["pause", "stop"]


def test_capture_checks_actual_configuration_and_never_executes(tmp_path, monkeypatch):
    """AC-GOV-SBG-004.1 AC-GOV-SBG-004.4"""
    from clawmetry.protection_capture import capture_hook_configuration
    from clawmetry import hook_ownership
    monkeypatch.setattr(hook_ownership, "command_binary_exists", lambda cmd: True)
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": "clawmetry hook claude-code --base http://127.0.0.1:8900"}]}]}}))
    value = capture_hook_configuration(paths={"claude_code": str(path)}, now=1000)
    row = value["runtimes"]["claude_code"]
    assert row["state"] == "configured"
    assert row["matchers"] == ["Selected tools"]
    assert row["events"] == ["PreToolUse"]
    assert str(tmp_path) not in json.dumps(value)
    path.unlink()
    assert capture_hook_configuration(paths={"claude_code": str(path)})["runtimes"]["claude_code"]["state"] == "not_configured"


def test_mirror_and_agent_metadata_do_not_establish_pretool_coverage(tmp_path):
    """AC-GOV-SBG-004.2 AC-GOV-SBG-004.3"""
    from clawmetry.protection_capture import capture_hook_configuration
    from clawmetry.protection_evidence import build
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"hooks": {"PreToolUse": [{"hooks": [
        {"command": "clawmetry hook claude-code-permission"}]}]}}))
    value = capture_hook_configuration(paths={"claude_code": str(path)}, now=1000)
    assert value["runtimes"]["claude_code"]["state"] == "not_configured"
    row = {**_row(), "metadata": {"sandbox_verified": True, "code_scan_passed": True}}
    evidence = build(row, hooks=value, now=1000)
    assert evidence["isolation"]["state"] == "unknown"
    assert evidence["code_validation"]["state"] == "unknown"


def test_oversized_or_invalid_configuration_remains_unknown(tmp_path):
    """AC-GOV-SBG-004.1"""
    from clawmetry.protection_capture import capture_hook_configuration
    path = tmp_path / "settings.json"
    path.write_bytes(b" " * 1_048_577)
    value = capture_hook_configuration(paths={"claude_code": str(path)})
    assert value["runtimes"]["claude_code"]["state"] == "unknown"
    path.write_text("{invalid")
    value = capture_hook_configuration(paths={"claude_code": str(path)})
    assert value["runtimes"]["claude_code"]["state"] == "unknown"


@pytest.mark.parametrize("status,expected", [
    ({"status": "inspected", "last_pass_ms": 1000000, "page_full": True}, "backlog"),
    ({"status": "partial", "last_pass_ms": 1000000, "unscoped": 2}, "partial"),
    ({"status": "unavailable", "last_pass_ms": 1000000}, "unavailable"),
    ({"status": "inspected", "last_pass_ms": 1000}, "stale"),
    ({"status": "inspected", "last_pass_ms": 2000000}, "unknown"),
])
def test_node_inspection_never_turns_missing_or_partial_evidence_into_clean(status, expected):
    """AC-GOV-SBG-004.1 AC-GOV-SBG-004.4"""
    from clawmetry.protection_evidence import build
    evidence = build(_row(), inspection=status, now=1000)["node_inspection"]
    assert evidence["scope"] == "node"
    assert evidence["state"] == expected
    assert "clean" not in evidence


def test_exported_session_cannot_inherit_local_hook_or_sandbox_evidence():
    """AC-GOV-SBG-004.1 AC-GOV-SBG-004.3"""
    from clawmetry.protection_evidence import build
    row = {**_row(), "observation": {"prevented": False}}
    evidence = build(row, approvals=[_approval()], hooks={"checked_at": 1000000,
        "runtimes": {"claude_code": {"state": "configured", "supported": True}}}, now=1000)
    assert evidence["pre_tool"]["last_decision"] is None
    assert evidence["pre_tool"]["configuration"]["state"] == "unknown"
    assert evidence["observation"]["source"] == "exported_telemetry"


def test_guard_builder_batches_evidence_and_preserves_runtime_scope(monkeypatch):
    """AC-GOV-SBG-004.1 AC-GOV-SBG-004.3 AC-GOV-SBG-004.4"""
    from routes import guard
    from clawmetry.protection_evidence import HOOK_SETTING, SECURITY_STATUS_SETTING
    monkeypatch.setattr(guard, "_live_only_rows", lambda rows: [])
    monkeypatch.setattr(guard, "_session_runtime", lambda sid, agent: sid.split(":")[0])
    monkeypatch.setattr(guard, "_runtime_supports_signals", lambda *args: {"controllable": False})
    calls = []
    def call(method, **kwargs):
        calls.append(method)
        if method == "query_sessions_table":
            return [{**_row(), "agent_type": "claude_code"},
                    {**_row(), "session_id": "copilot:s1", "agent_type": "copilot"}]
        if method == "query_approvals":
            return [{**row, "created_at": "2026-01-01T00:00:00Z", "resolved_at": "2026-01-01T00:00:02Z"}
                    for row in (_approval(), _approval(sid="copilot:s1", runtime="copilot"))]
        if method == "list_node_settings":
            return {HOOK_SETTING: json.dumps({"checked_at": 1000000, "runtimes": {}}),
                    SECURITY_STATUS_SETTING: json.dumps({"last_pass_ms": 1000000, "status": "partial", "unscoped": 1})}
        return []
    body = guard.build_guard_sessions_body(call=call, runtime_filter="copilot")
    assert len(body["sessions"]) == 1
    row = body["sessions"][0]
    assert row["runtime"] == "copilot"
    assert row["protection"]["node_inspection"]["scope"] == "node"
    assert row["protection"]["pre_tool"]["last_decision"]["source"] == "local_pre_tool_approval"
    assert calls.count("query_approvals") == 1
    assert calls.count("query_tool_policy") == 1
    assert calls.count("list_node_settings") == 1
    assert "SECRET-NOT-FOR-COVERAGE" not in json.dumps(body)


def test_protection_evidence_renderer_behavior():
    """AC-GOV-SBG-004.1 AC-GOV-SBG-004.2 AC-GOV-SBG-004.3 AC-GOV-SBG-004.4"""
    import shutil
    import subprocess
    from pathlib import Path
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is unavailable for the JavaScript behavior check")
    result = subprocess.run([node, str(Path(__file__).with_name("test_protection_evidence_js.js"))],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS protection evidence rendering" in result.stdout


def test_guard_finding_projection_binds_node_and_runtime(monkeypatch):
    """AC-GOV-SBG-004.3: a colliding session ID cannot inherit another node's finding."""
    from routes import guard
    monkeypatch.setattr(guard, "_live_only_rows", lambda rows: [])
    monkeypatch.setattr(guard, "_session_runtime", lambda sid, agent: "claude_code")
    monkeypatch.setattr(guard, "_runtime_supports_signals", lambda *args: {"controllable": False})
    rows = [{**_row(), "node_id": node, "agent_type": "claude_code"} for node in ("node-a", "node-b")]
    signals = [{"session_id": "claude_code:s1", "agent_type": "claude_code", "severity": "critical",
                "details": {"node_id": "node-b", "kind": "credential_access", "message": "Only on node B"}}]
    def call(method, **kwargs):
        return rows if method == "query_sessions_table" else signals if method == "query_recent_loop_signals" else []
    body = guard.build_guard_sessions_body(call=call)
    by_node = {r["node_id"]: r for r in body["sessions"]}
    assert by_node["node-a"]["incident"] is None
    assert by_node["node-b"]["incident"]["node_id"] == "node-b"
    signals[0]["agent_type"] = "copilot"
    assert all(r["incident"] is None for r in guard.build_guard_sessions_body(call=call)["sessions"])


def test_unscoped_legacy_signal_does_not_choose_among_colliding_nodes(monkeypatch):
    """AC-GOV-SBG-004.3: missing scope cannot be treated as a wildcard."""
    from routes import guard
    monkeypatch.setattr(guard, "_live_only_rows", lambda rows: [])
    monkeypatch.setattr(guard, "_session_runtime", lambda sid, agent: "claude_code")
    monkeypatch.setattr(guard, "_runtime_supports_signals", lambda *args: {"controllable": False})
    rows = [{**_row(), "node_id": node, "agent_type": "claude_code"} for node in ("node-a", "node-b")]
    signals = [{"session_id": "claude_code:s1", "agent_type": "claude_code", "severity": "critical",
                "details": {"kind": "credential_access"}}]
    def call(method, **kwargs):
        return rows if method == "query_sessions_table" else signals if method == "query_recent_loop_signals" else []
    assert all(r["incident"] is None for r in guard.build_guard_sessions_body(call=call)["sessions"])


def test_history_gap_is_preserved_as_missing_evidence():
    """AC-GOV-SBG-004.1 AC-GOV-SBG-004.3"""
    from clawmetry.protection_evidence import build
    evidence = build(_row(), inspection={"status": "partial", "last_pass_ms": 1000000,
        "history_gap": True, "unscoped": 0, "page_full": False}, now=1000)["node_inspection"]
    assert evidence["state"] == "partial"
    assert evidence["history_gap"] is True


@pytest.mark.parametrize("nested", [False, True])
def test_truncated_hook_search_cannot_establish_absence(nested, monkeypatch):
    """AC-GOV-SBG-004.1/.2: bounded config evidence never invents absence."""
    from clawmetry.protection_capture import _inspect
    from clawmetry import hook_ownership
    monkeypatch.setattr(hook_ownership, "command_binary_exists", lambda cmd: True)
    owned = {"command": "clawmetry hook claude-code"}
    others = [{"command": "echo harmless"} for _ in range(100)]
    entries = [{"hooks": others + [owned]}] if nested else others + [owned]
    result = _inspect({"hooks": {"Before": entries}}, "ok",
                      [("Before", ("clawmetry hook claude-code",), nested, "Tool calls")])
    assert result["state"] == "unknown"
    assert result["inspection_complete"] is False
    assert result["events"] == []


def test_truncated_hook_search_preserves_positive_configuration_only(monkeypatch):
    """AC-GOV-SBG-004.1: a bounded positive hit is configuration evidence."""
    from clawmetry.protection_capture import _inspect
    from clawmetry import hook_ownership
    monkeypatch.setattr(hook_ownership, "command_binary_exists", lambda cmd: True)
    entries = [{"command": "clawmetry hook claude-code"}] * 101
    result = _inspect({"hooks": {"Before": entries}}, "ok",
                      [("Before", ("clawmetry hook claude-code",), False, "Tool calls")])
    assert result["state"] == "configured"
    assert result["inspection_complete"] is False
    assert "execution_verified" not in result


def test_priority_inspection_discloses_pending_history_and_bounded_progress():
    """AC-GOV-SBG-002.1/.3 AC-GOV-SBG-004.1: current work does not certify history."""
    from clawmetry.protection_evidence import build
    value = build(_row(), inspection={"status": "inspected", "last_pass_ms": 1000000,
        "backfill_pending": True, "priority_processed": 3, "processed": 128}, now=1000)["node_inspection"]
    assert value["state"] == "partial"
    assert value["backfill_pending"] is True
    assert value["priority_processed"] == 3
    assert value["processed"] == 128
    assert "clean" not in value


@pytest.mark.parametrize("pending,count", [("true", True), (1, -1), (None, 1000001)])
def test_priority_inspection_rejects_malformed_progress(pending, count):
    """AC-GOV-SBG-004.1: absent or invalid progress stays unknown."""
    from clawmetry.protection_evidence import build
    value = build(_row(), inspection={"status": "partial", "last_pass_ms": 1000000,
        "backfill_pending": pending, "priority_processed": count}, now=1000)["node_inspection"]
    assert value["backfill_pending"] is None
    assert value["priority_processed"] is None
