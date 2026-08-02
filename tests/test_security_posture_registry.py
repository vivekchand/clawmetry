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
    assert checks["hooks_configured"]["status"] == "pass"  # informational
    assert checks["api_key_helper"]["status"] == "pass"  # informational


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
