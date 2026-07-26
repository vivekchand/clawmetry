"""Claude Code hooks → ClawMetry: pre-execution gate + phone push.

Covers clawmetry/hooks_claude_code.py and its approvals.py integration:
fail-open contract, deny-one-call (kill_on_deny=False), explicit allow on
human approval, installer idempotency/merging, uninstall, Notification
pushes, the disk policy cache, and the watcher runtime-skip guard.
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import clawmetry.approvals as ap
from clawmetry import hooks_claude_code as h


RAW_POLICY = {"name": "Block destructive deletes", "tool": "exec",
              "pattern_type": "command_regex", "pattern": r"rm -rf",
              "action": "require_approval", "timeout": 60,
              "on_timeout": "deny"}


def _policies():
    return [ap._compile_policy(dict(RAW_POLICY))]


def _evt(cmd="rm -rf /tmp/x", tool="Bash"):
    return {"hook_event_name": "PreToolUse", "tool_name": tool,
            "tool_input": {"command": cmd}, "session_id": "claude_code:abc",
            "tool_use_id": "tu_1"}


def _wire(monkeypatch, decision, policy="Block destructive deletes",
          capture=None):
    monkeypatch.setattr(h, "_load_api_key", lambda: "cm_x")
    monkeypatch.setattr(h, "_node_id", lambda: "n1")
    monkeypatch.setattr(h, "_load_policies_fast", lambda k: _policies())

    def fake_process(**kw):
        if capture is not None:
            capture.update(kw)
        return {"decision": decision, "policy": policy, "killed": False}

    monkeypatch.setattr(ap, "process_tool_call", fake_process)


# ── evaluate(): decision mapping ─────────────────────────────────────────

def test_no_api_key_allows(monkeypatch):
    monkeypatch.setattr(h, "_load_api_key", lambda: "")
    assert h.evaluate(_evt()) is None


def test_no_policies_fast_path_skips_engine(monkeypatch):
    monkeypatch.setattr(h, "_load_api_key", lambda: "cm_x")
    monkeypatch.setattr(h, "_load_policies_fast", lambda k: [])

    def boom(**kw):
        raise AssertionError("process_tool_call must not run with no policies")

    monkeypatch.setattr(ap, "process_tool_call", boom)
    assert h.evaluate(_evt()) is None


def test_policy_miss_skips_engine(monkeypatch):
    capture = {}
    _wire(monkeypatch, "denied", capture=capture)
    assert h.evaluate(_evt(cmd="ls -la")) is None  # doesn't match rm -rf
    assert capture == {}, "engine must not be invoked on a policy miss"


def test_denied_produces_deny_payload_without_kill(monkeypatch):
    capture = {}
    _wire(monkeypatch, "denied", capture=capture)
    p = h.evaluate(_evt())
    assert p["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert p["decision"] == "block"  # legacy fallback for old builds
    assert "Block destructive deletes" in p["reason"]
    # THE parity fix: hook denies one call; the session must survive.
    assert capture["kill_on_deny"] is False


def test_approved_produces_explicit_allow(monkeypatch):
    """Approve on the phone must SKIP Claude Code's own prompt — returning
    no opinion would make the user answer twice."""
    _wire(monkeypatch, "approved")
    p = h.evaluate(_evt())
    assert p["hookSpecificOutput"]["permissionDecision"] == "allow"
    assert p["decision"] == "approve"


def test_on_timeout_raw_strings_map_correctly(monkeypatch):
    _wire(monkeypatch, "deny")     # on_timeout leaves raw "deny"
    assert h.evaluate(_evt())["decision"] == "block"
    _wire(monkeypatch, "approve")  # on_timeout: approve
    assert h.evaluate(_evt())["decision"] == "approve"


def test_error_and_monitored_have_no_opinion(monkeypatch):
    for decision in ("error", "monitored", "no_policy"):
        _wire(monkeypatch, decision)
        assert h.evaluate(_evt()) is None


def test_engine_exception_fails_open(monkeypatch):
    monkeypatch.setattr(h, "_load_api_key", lambda: "cm_x")
    monkeypatch.setattr(h, "_load_policies_fast", lambda k: _policies())

    def boom(**kw):
        raise RuntimeError("cloud down")

    monkeypatch.setattr(ap, "process_tool_call", boom)
    assert h.evaluate(_evt()) is None


def test_wrong_event_name_allows(monkeypatch):
    monkeypatch.setattr(h, "_load_api_key", lambda: "cm_x")
    assert h.evaluate({"hook_event_name": "PostToolUse", "tool_name": "Bash",
                       "tool_input": {}}) is None


# ── main_pretooluse(): wire protocol ─────────────────────────────────────

def test_pretooluse_deny_exits_2_with_stderr(monkeypatch):
    _wire(monkeypatch, "denied", policy="P")
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_evt())))
    out, err = io.StringIO(), io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    monkeypatch.setattr("sys.stderr", err)
    rc = h.main_pretooluse()
    assert rc == 2, "deny must exit 2 (the universal block)"
    assert "P" in err.getvalue()
    body = json.loads(out.getvalue())
    assert body["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pretooluse_approve_exits_0_with_allow_json(monkeypatch):
    _wire(monkeypatch, "approved")
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_evt())))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    rc = h.main_pretooluse()
    assert rc == 0
    body = json.loads(out.getvalue())
    assert body["hookSpecificOutput"]["permissionDecision"] == "allow"


def test_pretooluse_garbage_stdin_allows(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json {"))
    assert h.main_pretooluse() == 0


# ── installer ────────────────────────────────────────────────────────────

def test_install_idempotent_and_correct_timeouts(monkeypatch, tmp_path):
    monkeypatch.setattr(h, "_MARKER_PATH", str(tmp_path / "marker.json"))
    sp = str(tmp_path / "settings.json")
    r1 = h.install(settings_path=sp)
    assert r1["status"] == "installed"
    assert sorted(r1["added"]) == ["Notification", "PreToolUse"]
    r2 = h.install(settings_path=sp)
    assert r2["status"] == "already_present"
    s = json.load(open(sp))
    pre = s["hooks"]["PreToolUse"]
    assert len(pre) == 1, "must not duplicate on re-install"
    hk = pre[0]["hooks"][0]
    assert hk["command"] == "clawmetry hooks run pretooluse"
    # Load-bearing: must exceed policy timeouts (presets 60-300s) or Claude
    # Code times the hook out before the human decides.
    assert hk["timeout"] == 900
    assert s["hooks"]["Notification"][0]["hooks"][0]["command"] == \
        "clawmetry hooks run notification"
    marker = json.load(open(str(tmp_path / "marker.json")))
    assert "PreToolUse" in marker["claude_code"]["events"]


def test_install_preserves_existing_settings(monkeypatch, tmp_path):
    monkeypatch.setattr(h, "_MARKER_PATH", str(tmp_path / "marker.json"))
    sp = str(tmp_path / "settings.json")
    json.dump({"model": "opus",
               "hooks": {"PostToolUse": [{"matcher": "Bash"}]}},
              open(sp, "w"))
    h.install(settings_path=sp)
    s = json.load(open(sp))
    assert s["model"] == "opus"
    assert "PostToolUse" in s["hooks"]
    assert "PreToolUse" in s["hooks"]


def test_uninstall_removes_only_ours(monkeypatch, tmp_path):
    monkeypatch.setattr(h, "_MARKER_PATH", str(tmp_path / "marker.json"))
    sp = str(tmp_path / "settings.json")
    h.install(settings_path=sp)
    # Simulate a user-authored unrelated hook alongside ours.
    s = json.load(open(sp))
    s["hooks"]["PreToolUse"].append(
        {"matcher": "Bash", "hooks": [{"type": "command", "command": "my-linter"}]})
    json.dump(s, open(sp, "w"))
    r = h.uninstall(settings_path=sp)
    assert r["status"] == "uninstalled"
    s = json.load(open(sp))
    assert s["hooks"]["PreToolUse"][0]["hooks"][0]["command"] == "my-linter"
    assert "Notification" not in s["hooks"]
    marker = json.load(open(str(tmp_path / "marker.json")))
    assert "claude_code" not in marker


# ── Notification hook → phone push ───────────────────────────────────────

def test_notification_permission_prompt_pushes(monkeypatch):
    calls = []
    monkeypatch.setattr(h, "_load_api_key", lambda: "cm_x")
    monkeypatch.setattr(h, "_push_notify",
                        lambda k, kind, title, body: calls.append((kind, title, body)))
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
        {"hook_event_name": "Notification",
         "notification_type": "permission_prompt",
         "message": "Claude needs permission to run rm"})))
    assert h.main_notification() == 0
    assert calls and calls[0][0] == "input"
    assert "rm" in calls[0][2]


def test_notification_idle_prompt_pushes_stop(monkeypatch):
    calls = []
    monkeypatch.setattr(h, "_load_api_key", lambda: "cm_x")
    monkeypatch.setattr(h, "_push_notify",
                        lambda k, kind, title, body: calls.append(kind))
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
        {"notification_type": "idle_prompt", "message": "done"})))
    assert h.main_notification() == 0
    assert calls == ["stop"]


def test_notification_other_types_and_no_key_are_silent(monkeypatch):
    calls = []
    monkeypatch.setattr(h, "_push_notify",
                        lambda *a: calls.append(a))
    monkeypatch.setattr(h, "_load_api_key", lambda: "cm_x")
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
        {"notification_type": "auth_success", "message": "x"})))
    assert h.main_notification() == 0
    monkeypatch.setattr(h, "_load_api_key", lambda: "")
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
        {"notification_type": "permission_prompt", "message": "x"})))
    assert h.main_notification() == 0
    assert calls == []


# ── policy disk cache ────────────────────────────────────────────────────

def test_policy_cache_stale_fallback_on_fetch_failure(monkeypatch, tmp_path):
    cache = tmp_path / "cache.json"
    json.dump({"policies": [dict(RAW_POLICY)]}, open(cache, "w"))
    old = time.time() - 3600
    os.utime(cache, (old, old))  # stale — forces a fetch attempt
    monkeypatch.setattr(h, "_POLICY_CACHE_PATH", str(cache))

    def boom(api_key):
        raise RuntimeError("cloud down")

    monkeypatch.setattr(ap, "_fetch_cloud_policies", boom)
    monkeypatch.setattr(ap, "POLICIES_PATH", tmp_path / "nope.yml")
    policies = h._load_policies_fast("cm_x")
    assert len(policies) == 1
    assert policies[0]["name"] == "Block destructive deletes"


# ── watcher skip guard ───────────────────────────────────────────────────

def test_watcher_skips_hook_covered_runtimes(monkeypatch, tmp_path):
    marker = tmp_path / "hooks_installed.json"
    json.dump({"claude_code": {"events": ["PreToolUse", "Notification"]}},
              open(marker, "w"))
    monkeypatch.setattr(ap, "_HOOKS_MARKER_PATH", marker)
    monkeypatch.setattr(ap, "_hooks_marker_cache", (0.0, frozenset()))
    covered = ap._hook_covered_runtimes()
    assert "claude_code" in covered
    assert ap._session_runtime("claude_code:abc") in covered
    assert ap._session_runtime("codex:abc") not in covered


def test_watcher_guard_empty_without_marker(monkeypatch, tmp_path):
    monkeypatch.setattr(ap, "_HOOKS_MARKER_PATH", tmp_path / "absent.json")
    monkeypatch.setattr(ap, "_hooks_marker_cache", (0.0, frozenset()))
    assert ap._hook_covered_runtimes() == frozenset()
