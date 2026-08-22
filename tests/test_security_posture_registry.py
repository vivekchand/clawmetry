"""Security posture registry tests (Workstream C — runtime feature parity).

Covers clawmetry/security_posture.py:

  - unknown runtime            -> honest `not_available` envelope (200 path)
  - openclaw provider          -> full legacy scan envelope (moved out of
                                  dashboard.py, same math / same keys)
  - claude_code provider       -> every check branch against a crafted
                                  CLAUDE_CONFIG_DIR
  - codex provider             -> config.toml approval/sandbox branches
  - /api/security/posture      -> ?runtime dispatch, default = openclaw
"""

from __future__ import annotations

import json
import os

import pytest
from flask import Flask

import clawmetry.security_posture as sp


# ── envelope helpers ───────────────────────────────────────────────────────


def _assert_scored_envelope(d, runtime):
    for key in (
        "score", "score_label", "score_color", "score_pct", "checks",
        "passed", "failed", "warnings", "total", "scanned_at",
    ):
        assert key in d, f"missing {key}"
    assert d["runtime"] == runtime
    assert d["status"] == "ok"
    assert d["total"] == len(d["checks"])
    assert d["passed"] + d["failed"] + d["warnings"] == d["total"]
    for c in d["checks"]:
        assert c["status"] in ("pass", "warn", "fail")
        for key in ("id", "label", "detail", "severity", "weight"):
            assert key in c


def _by_id(d):
    return {c["id"]: c for c in d["checks"]}


# ── registry dispatch ──────────────────────────────────────────────────────


def test_unknown_runtime_not_available():
    d = sp.get_posture("some_unregistered_runtime")
    assert d["runtime"] == "some_unregistered_runtime"
    assert d["status"] == "not_available"
    assert d["checks"] == []
    assert "No security posture checks implemented" in d["detail"]
    assert d["score"] == "U"


def test_register_and_replace_provider():
    sp.register_posture_provider("testrt", lambda: {"checks": [], "score": "A"})
    try:
        d = sp.get_posture("testrt")
        assert d["score"] == "A"
        assert d["runtime"] == "testrt"  # injected default
        assert d["status"] == "ok"  # injected default
    finally:
        with sp._lock:
            sp._providers.pop("testrt", None)


# ── openclaw provider (moved legacy scan) ──────────────────────────────────


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Point ~ at tmp_path (the pattern test_pid_liveness_windows.py uses)."""
    real_expanduser = os.path.expanduser
    monkeypatch.setattr(
        os.path,
        "expanduser",
        lambda p: p.replace("~", str(tmp_path), 1) if p.startswith("~")
        else real_expanduser(p),
    )
    return tmp_path


def test_openclaw_provider_full_scan(fake_home, monkeypatch):
    monkeypatch.delenv("OPENCLAW_AUTH_TOKEN", raising=False)
    oc = fake_home / ".openclaw"
    oc.mkdir()
    oc.chmod(0o700)
    (oc / "openclaw.json").write_text(json.dumps({
        "gateway": {
            "auth": {"token": "a-strong-random-token-0123456789"},
            "host": "127.0.0.1",
        },
        "tools": {"exec": {"security": "allowlist"}},
        "plugins": {"entries": {"telegram": {"token": "$TELEGRAM_TOKEN"}}},
        "nodes": {"autoApprove": False},
    }))
    d = sp.get_posture("openclaw")
    _assert_scored_envelope(d, "openclaw")
    checks = _by_id(d)
    assert checks["config_found"]["status"] == "pass"
    assert checks["auth_enabled"]["status"] == "pass"
    assert checks["auth_strength"]["status"] == "pass"
    assert checks["bind_address"]["status"] == "pass"
    assert checks["exec_permissions"]["status"] == "pass"
    assert checks["tls_enabled"]["status"] == "pass"
    assert checks["secrets_in_config"]["status"] == "pass"
    assert checks["node_auto_approve"]["status"] == "pass"
    assert checks["elevated_exec"]["status"] == "pass"
    assert d["score"] in ("A", "B")
    assert d["is_docker"] is False


def test_openclaw_provider_missing_config_unknown_score(fake_home, monkeypatch):
    monkeypatch.delenv("OPENCLAW_AUTH_TOKEN", raising=False)
    # Docker probe must not find a live daemon's containers: neuter PATH.
    monkeypatch.setenv("PATH", str(fake_home))
    d = sp.get_posture("openclaw")
    assert d["runtime"] == "openclaw"
    assert d["score"] == "U"
    assert d["failed"] == 1 and d["total"] == 1
    assert "No openclaw.json found" in d["checks"][0]["detail"]


# ── claude_code provider ───────────────────────────────────────────────────


def test_claude_code_no_settings_fail(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "empty"))
    d = sp.get_posture("claude_code")
    assert d["runtime"] == "claude_code"
    assert d["score"] == "U"
    assert d["checks"][0]["id"] == "config_found"
    assert d["checks"][0]["status"] == "fail"


def test_claude_code_hardened_settings_all_branches(tmp_path, monkeypatch):
    cfg = tmp_path / "claude"
    cfg.mkdir()
    (cfg / "settings.json").write_text(json.dumps({
        "permissions": {
            "allow": ["Bash(npm run test:*)"],
            "deny": ["Read(.env)", "Bash(rm -rf*)"],
        },
        "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": []}]},
        "apiKeyHelper": "/usr/local/bin/key.sh",
    }))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    d = sp.get_posture("claude_code")
    _assert_scored_envelope(d, "claude_code")
    checks = _by_id(d)
    assert checks["config_found"]["status"] == "pass"
    assert checks["permissions_present"]["status"] == "pass"
    assert checks["deny_rules"]["status"] == "pass"
    assert checks["hooks_configured"]["status"] == "pass"
    assert "PreToolUse" in checks["hooks_configured"]["detail"]
    assert checks["mcp_auto_trust"]["status"] == "pass"
    assert checks["api_key_helper"]["status"] == "pass"
    assert "key.sh" in checks["api_key_helper"]["detail"]
    assert checks["wildcard_allow"]["status"] == "pass"
    assert d["score"] == "A"


def test_claude_code_risky_settings_warn_branches(tmp_path, monkeypatch):
    cfg = tmp_path / "claude"
    cfg.mkdir()
    (cfg / "settings.json").write_text(json.dumps({
        "permissions": {"allow": ["Bash(*)"], "defaultMode": "bypassPermissions"},
        "enableAllProjectMcpServers": True,
    }))
    # local overlay contributes its rules to the union
    (cfg / "settings.local.json").write_text(json.dumps({
        "permissions": {"allow": ["WebFetch"]},
    }))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    d = sp.get_posture("claude_code")
    _assert_scored_envelope(d, "claude_code")
    checks = _by_id(d)
    assert "settings.json + settings.local.json" in checks["config_found"]["detail"]
    assert checks["permissions_present"]["status"] == "pass"  # allow rules exist
    assert checks["deny_rules"]["status"] == "warn"  # no deny list
    assert checks["mcp_auto_trust"]["status"] == "warn"  # auto-trust on
    assert checks["wildcard_allow"]["status"] == "warn"
    assert "Bash(*)" in checks["wildcard_allow"]["detail"]
    assert "bypassPermissions" in checks["wildcard_allow"]["detail"]


def test_claude_code_empty_settings_warns_on_permissions(tmp_path, monkeypatch):
    cfg = tmp_path / "claude"
    cfg.mkdir()
    (cfg / "settings.json").write_text("{}")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    d = sp.get_posture("claude_code")
    checks = _by_id(d)
    assert checks["permissions_present"]["status"] == "warn"
    # No hooks means nothing inspects a tool call before it runs — that is a
    # real gap, not an informational note. It used to pass on every code path,
    # which handed the grade 5 free weight it had not measured.
    assert checks["hooks_configured"]["status"] == "warn"
    assert checks["hooks_configured"]["remediation"]
    # apiKeyHelper genuinely cannot fail (both states are legitimate), so it
    # stays visible but must carry ZERO weight rather than inflating the score.
    assert checks["api_key_helper"]["status"] == "pass"
    assert checks["api_key_helper"]["weight"] == 0


def test_empty_config_does_not_score_an_a(tmp_path, monkeypatch):
    """An unconfigured runtime must not read as "Excellent".

    Founder-reported 2026-08-15: the Security tab showed "A · Excellent ·
    94.4%" for a Claude Code install with NO deny rules, because two of the
    seven checks (``hooks_configured``, ``api_key_helper``) passed on every
    code path and donated 10 weight of unearned credit. An empty config is an
    unmeasured config; the grade has to say so.
    """
    cfg = tmp_path / "claude"
    cfg.mkdir()
    (cfg / "settings.json").write_text("{}")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    d = sp.get_posture("claude_code")
    assert d["score"] != "A", (
        "an empty settings.json scored {} ({}%) — padding is back".format(
            d["score"], d.get("score_pct")
        )
    )


def test_codex_empty_config_does_not_score_an_a(tmp_path, monkeypatch):
    """Same class of bug on the Codex provider.

    Both of its risk checks (``approval_policy``, ``sandbox_mode``) used to
    ``pass`` when the key was ABSENT, so a zero-byte config.toml scored an A
    while the sandbox state was entirely unverified.
    """
    home = tmp_path / "codex"
    home.mkdir()
    (home / "config.toml").write_text("")
    monkeypatch.setenv("CODEX_HOME", str(home))
    d = sp.get_posture("codex")
    assert d["status"] == "ok"
    assert d["score"] != "A", (
        "an empty config.toml scored {} ({}%)".format(d["score"], d.get("score_pct"))
    )
    checks = _by_id(d)
    assert checks["sandbox_mode"]["status"] == "warn"
    assert checks["approval_policy"]["status"] == "warn"


# ── codex provider ─────────────────────────────────────────────────────────


def test_codex_no_config_not_available(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    d = sp.get_posture("codex")
    assert d["status"] == "not_available"
    assert "config.toml" in d["detail"]


def test_codex_dangerous_config(tmp_path, monkeypatch):
    home = tmp_path / "codex"
    home.mkdir()
    (home / "config.toml").write_text(
        'model = "gpt-5"\n'
        'approval_policy = "never"\n'
        'sandbox_mode = "danger-full-access"\n'
        "\n[sandbox_workspace_write]\nnetwork_access = true\n"
    )
    monkeypatch.setenv("CODEX_HOME", str(home))
    d = sp.get_posture("codex")
    _assert_scored_envelope(d, "codex")
    checks = _by_id(d)
    assert checks["approval_policy"]["status"] == "warn"
    assert checks["sandbox_mode"]["status"] == "fail"


def test_codex_safe_config(tmp_path, monkeypatch):
    home = tmp_path / "codex"
    home.mkdir()
    (home / "config.toml").write_text(
        'approval_policy = "on-request"\nsandbox_mode = "workspace-write"\n'
    )
    monkeypatch.setenv("CODEX_HOME", str(home))
    d = sp.get_posture("codex")
    checks = _by_id(d)
    assert checks["approval_policy"]["status"] == "pass"
    assert checks["sandbox_mode"]["status"] == "pass"
    assert d["score"] == "A"


# ── route dispatch ─────────────────────────────────────────────────────────


@pytest.fixture
def client():
    import routes.infra as infra

    app = Flask(__name__)
    app.register_blueprint(infra.bp_security)
    return app.test_client()


def test_route_unknown_runtime_200_not_available(client):
    r = client.get("/api/security/posture?runtime=antigravity")
    assert r.status_code == 200
    d = r.get_json()
    assert d["status"] == "not_available"
    assert d["runtime"] == "antigravity"


def test_route_claude_code_dispatch(client, tmp_path, monkeypatch):
    cfg = tmp_path / "claude"
    cfg.mkdir()
    (cfg / "settings.json").write_text(json.dumps({
        "permissions": {"allow": ["Bash(ls*)"], "deny": ["Read(.env)"]},
    }))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg))
    r = client.get("/api/security/posture?runtime=claude_code")
    assert r.status_code == 200
    d = r.get_json()
    assert d["runtime"] == "claude_code"
    assert d["status"] == "ok"
    assert any(c["id"] == "config_found" for c in d["checks"])


def test_route_default_runtime_is_openclaw(client, fake_home, monkeypatch):
    monkeypatch.delenv("OPENCLAW_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("PATH", str(fake_home))  # keep docker probe inert
    r = client.get("/api/security/posture")
    assert r.status_code == 200
    d = r.get_json()
    assert d["runtime"] == "openclaw"


# ── cursor + copilot providers ─────────────────────────────────────────────
# Both runtimes are CLOSED SOURCE, so no check here may FAIL on the strength
# of a documented setting alone: only filesystem facts earn a fail. The
# governing near-miss (2026-08-18): a proposed Cline check keyed on
# `executeAllCommands`, a field that runtime's code never reads, would have
# failed every clean install. A check that fails on a healthy machine teaches
# the operator to ignore the grade, which is worse than shipping no check.


def _cursor_home(tmp_path, monkeypatch):
    home = tmp_path / "cursor"
    home.mkdir()
    monkeypatch.setenv("CURSOR_HOME", str(home))
    return home


def _copilot_home(tmp_path, monkeypatch):
    home = tmp_path / "copilot"
    home.mkdir()
    monkeypatch.setenv("COPILOT_HOME", str(home))
    return home


def test_cursor_absent_is_not_available(tmp_path, monkeypatch):
    monkeypatch.setenv("CURSOR_HOME", str(tmp_path / "nope"))
    assert sp.get_posture("cursor")["status"] == "not_available"


def test_copilot_absent_is_not_available(tmp_path, monkeypatch):
    monkeypatch.setenv("COPILOT_HOME", str(tmp_path / "nope"))
    assert sp.get_posture("copilot")["status"] == "not_available"


def test_clean_install_never_fails(tmp_path, monkeypatch):
    """THE rule for both providers: a bare, untouched install produces zero
    failures. Warnings are fine; a red X on a clean machine is not."""
    _cursor_home(tmp_path, monkeypatch)
    _copilot_home(tmp_path, monkeypatch)
    for rt in ("cursor", "copilot"):
        d = sp.get_posture(rt)
        assert d["status"] == "ok", (rt, d)
        assert d["failed"] == 0, (rt, [c for c in d["checks"] if c["status"] == "fail"])


def test_cursor_unmeasurable_auto_run_carries_no_weight(tmp_path, monkeypatch):
    """Cursor's auto-run level has no documented on-disk key. We report that
    honestly rather than inventing one, and it must not move the grade."""
    _cursor_home(tmp_path, monkeypatch)
    check = _by_id(sp.get_posture("cursor"))["auto_run_level"]
    assert check["weight"] == 0
    assert "cannot be verified" in check["detail"]


def test_cursor_flags_secret_written_into_mcp_config(tmp_path, monkeypatch):
    home = _cursor_home(tmp_path, monkeypatch)
    (home / "mcp.json").write_text(json.dumps({"mcpServers": {
        "gh": {"env": {"GITHUB_TOKEN": "ghp_realsecretvalue123456"}},
        "ok": {"env": {"API_KEY": "$FROM_ENV"}},
    }}))
    c = _by_id(sp.get_posture("cursor"))["mcp_secrets_inline"]
    assert c["status"] == "fail"
    assert "gh.env.GITHUB_TOKEN" in c["detail"]
    # The $-reference form is a reference, not a secret, and must not be named.
    assert "ok.env.API_KEY" not in c["detail"]


def test_cursor_flags_invisible_unicode_in_rules(tmp_path, monkeypatch):
    home = _cursor_home(tmp_path, monkeypatch)
    rules = home / "rules"
    rules.mkdir()
    # A Unicode tag character: invisible in every editor, still read by the model.
    (rules / "team.mdc").write_text("Be helpful.\U000E0041\n")
    (rules / "clean.mdc").write_text("Be concise.\n")
    c = _by_id(sp.get_posture("cursor"))["rules_invisible_unicode"]
    assert c["status"] == "fail"
    assert "team.mdc" in c["detail"]
    assert "clean.mdc" not in c["detail"]


def test_cursor_hooks_present_passes(tmp_path, monkeypatch):
    home = _cursor_home(tmp_path, monkeypatch)
    (home / "hooks.json").write_text(json.dumps(
        {"hooks": {"beforeShellExecution": [{"command": "numbat"}]}, "version": 1}))
    assert _by_id(sp.get_posture("cursor"))["pre_exec_hooks"]["status"] == "pass"


def test_cursor_empty_hooks_object_warns(tmp_path, monkeypatch):
    """An empty `hooks: {}` is the shape a reset leaves behind. It reads as
    configured to a naive check, but nothing inspects anything."""
    home = _cursor_home(tmp_path, monkeypatch)
    (home / "hooks.json").write_text(json.dumps({"hooks": {}, "version": 1}))
    assert _by_id(sp.get_posture("cursor"))["pre_exec_hooks"]["status"] == "warn"


def test_cursor_sandbox_never_fails_on_closed_source(tmp_path, monkeypatch):
    """insecure_none is the documented no-sandbox value, but we cannot read
    the code that honours it, so it warns and never fails."""
    home = _cursor_home(tmp_path, monkeypatch)
    (home / "sandbox.json").write_text(json.dumps({"type": "insecure_none"}))
    assert _by_id(sp.get_posture("cursor"))["sandbox_mode"]["status"] == "warn"


def test_copilot_blanket_write_grant_warns_but_home_wide_fails(tmp_path, monkeypatch):
    """A standing write grant is documented, not observable, so it warns. A
    grant over the whole home directory is indefensible whatever the client
    does with it, so that one fails."""
    home = _copilot_home(tmp_path, monkeypatch)
    (home / "permissions-config.json").write_text(json.dumps({"locations": {
        "/Users/someone/projects/app": {"tool_approvals": [{"kind": "write"}]}}}))
    assert _by_id(sp.get_posture("copilot"))["blanket_write_grant"]["status"] == "warn"

    (home / "permissions-config.json").write_text(json.dumps({"locations": {
        os.path.expanduser("~"): {"tool_approvals": [{"kind": "write"}]}}}))
    c = _by_id(sp.get_posture("copilot"))["blanket_write_grant"]
    assert c["status"] == "fail"


def test_copilot_relative_path_grant_warns(tmp_path, monkeypatch):
    """Documented footgun: a relative path matches by trailing components, so
    a grant for `.env` covers a file of that name in any directory."""
    home = _copilot_home(tmp_path, monkeypatch)
    (home / "permissions-config.json").write_text(json.dumps({"locations": {
        "/p": {"tool_approvals": [{"kind": "write", "paths": [".env"]}]}}}))
    assert _by_id(sp.get_posture("copilot"))["relative_path_grants"]["status"] == "warn"


def test_copilot_root_trusted_folder_fails(tmp_path, monkeypatch):
    home = _copilot_home(tmp_path, monkeypatch)
    (home / "config.json").write_text(json.dumps({"trustedFolders": ["/"]}))
    assert _by_id(sp.get_posture("copilot"))["trusted_folders"]["status"] == "fail"


def test_copilot_jsonc_config_is_parsed(tmp_path, monkeypatch):
    """Copilot ships config.json with // comments. A strict json.loads returns
    None and every downstream check silently reads an empty config."""
    home = _copilot_home(tmp_path, monkeypatch)
    (home / "config.json").write_text(
        "// User settings belong in settings.json.\n"
        "// This file is managed automatically.\n"
        '{"trustedFolders": ["/tmp/proj"]}\n')
    d = sp.get_posture("copilot")
    assert "config.json" in _by_id(d)["config_found"]["detail"]
    assert _by_id(d)["trusted_folders"]["status"] == "pass"


def test_copilot_allow_all_in_shell_profile_fails(tmp_path, monkeypatch):
    """Text in a file is a fact, so this one earns a fail. Commented-out lines
    must not count."""
    _copilot_home(tmp_path, monkeypatch)
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    (fake_home / ".zshrc").write_text("# COPILOT_ALLOW_ALL=1 was here\nexport PATH=$PATH\n")
    monkeypatch.setenv("HOME", str(fake_home))
    assert _by_id(sp.get_posture("copilot"))["allow_all_switch"]["status"] == "pass"

    (fake_home / ".zshrc").write_text("export COPILOT_ALLOW_ALL=1\n")
    c = _by_id(sp.get_posture("copilot"))["allow_all_switch"]
    assert c["status"] == "fail"
    assert ".zshrc" in c["detail"]
