"""Fresh scoped policy evidence for initial outages, AC-GOV-SBG-001.2/.3."""
from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest


@pytest.fixture
def cache(tmp_path, monkeypatch):
    from clawmetry import approvals, entitlements, gate_policy_cache
    monkeypatch.setattr(gate_policy_cache, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(entitlements, "get_entitlement", lambda: SimpleNamespace(
        source="test", allows_feature=lambda key: True))
    policies = [approvals._compile_policy({"name": "review delete", "runtime": "claude_code",
        "tool": "exec", "action": "require_approval", "pattern_type": "command_regex",
        "pattern": r"rm -rf", "timeout": 60})]
    return gate_policy_cache, policies


def test_fresh_snapshot_only_protects_matching_scoped_calls(cache):
    module, policies = cache
    module.capture("claude_code", policies, now=100)
    assert module.protects("claude_code", {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}}, now=110)
    assert not module.protects("claude_code", {"tool_name": "Bash", "tool_input": {"command": "git status"}}, now=110)
    assert not module.protects("copilot", {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}}, now=110)
    assert not module.protects("claude_code", {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}}, now=200)


@pytest.mark.parametrize("entitlement", [False, "error", "resolver_error"])
def test_current_entitlement_failure_prevents_cached_blocking(cache, entitlement, monkeypatch):
    from clawmetry import entitlements
    module, policies = cache
    module.capture("claude_code", policies, now=100)

    def current():
        if entitlement == "error":
            raise OSError("license unavailable")
        return SimpleNamespace(source="resolver_error" if entitlement == "resolver_error" else "test",
                               allows_feature=lambda key: entitlement is not False)

    monkeypatch.setattr(entitlements, "get_entitlement", current)
    assert not module.protects("claude_code", {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}}, now=110)


def test_removing_policy_removes_fallback_authority(cache):
    module, policies = cache
    module.capture("claude_code", policies, now=100)
    module.capture("claude_code", [], now=101)
    assert not module.protects("claude_code", {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}}, now=110)


def test_explicit_allow_wins_over_cached_protection(cache):
    from clawmetry import approvals
    module, policies = cache
    policies.append(approvals._compile_policy({"name": "allow temp cleanup", "tool": "exec", "action": "approve",
        "pattern_type": "command_regex", "pattern": r"^rm -rf /tmp/x$"}))
    module.capture("claude_code", policies, now=100)
    assert not module.protects("claude_code", {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}}, now=110)


@pytest.mark.parametrize("runtime", ["claude-code", "cursor", "copilot"])
def test_initial_outage_denies_only_fresh_matched_policy(runtime, monkeypatch, capsys):
    from clawmetry import claude_code_gate as cc, runtime_gates as rt, gate_policy_cache
    module = cc if runtime == "claude-code" else rt
    monkeypatch.setattr(gate_policy_cache, "protects", lambda runtime, payload: True)
    monkeypatch.setattr(module, "_post_json", lambda *a: None)
    monkeypatch.setattr(module.time, "sleep", lambda _: None)
    event = ({"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}} if runtime == "claude-code" else
             {"command": "rm -rf /tmp/x"} if runtime == "cursor" else
             {"toolName": "shell", "toolArgs": {"command": "rm -rf /tmp/x"}})
    monkeypatch.setattr(module.sys, "stdin", io.StringIO(json.dumps(event)))
    assert module.hook_main([runtime]) == 0
    out = json.loads(capsys.readouterr().out)
    decision = out.get("permission") or out.get("permissionDecision") or out["hookSpecificOutput"]["permissionDecision"]
    assert decision == "deny"
