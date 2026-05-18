"""Auth resolution for Self-Evolve / Advisor (zero-config key path).

The Advanced > Self-Evolve tab was asking users for an API key on first
load instead of reusing whatever credential the local OpenClaw was
already configured with. ``_load_anthropic_auth`` now walks four
sources in order; this test pins the priority and proves that none of
the lookups leak the key into any public surface.

Priority:
  1. ``ANTHROPIC_API_KEY`` env var
  2. ``anthropic_api_key`` in ``~/.openclaw/.clawmetry/insights_config.json``
  3. ``apiKey``/``api_key``/``key``/``token`` in
     ``~/.openclaw/openclaw.json`` under ``plugins.entries.anthropic``,
     ``providers.anthropic``, or ``auth.profiles."anthropic:api-key"``
  4. ``claude`` CLI binary + OAuth profile in
     ``~/.openclaw/agents/main/agent/auth-profiles.json``
"""

from __future__ import annotations

import importlib
import json
import os


def _fresh_advisor(monkeypatch, tmp_path):
    """Re-import advisor with HOME pointed at an isolated tmp dir so
    none of the four lookups can hit the real user's files."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Make sure `claude` lookup misses unless a test explicitly opts in.
    monkeypatch.setenv("PATH", str(tmp_path / "empty_path"))
    import routes.advisor as advisor
    return importlib.reload(advisor)


def test_no_credentials_returns_none(monkeypatch, tmp_path):
    advisor = _fresh_advisor(monkeypatch, tmp_path)
    assert advisor._load_anthropic_auth() == (None, None)


def test_env_var_wins(monkeypatch, tmp_path):
    advisor = _fresh_advisor(monkeypatch, tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-wins")

    # Even with an insights config key on disk the env var must win.
    cfg_dir = tmp_path / ".openclaw" / ".clawmetry"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "insights_config.json").write_text(
        json.dumps({"anthropic_api_key": "sk-ant-config-loses"})
    )

    mode, cred = advisor._load_anthropic_auth()
    assert mode == "api_key"
    assert cred == "sk-ant-env-wins"


def test_insights_config_key_picked_up(monkeypatch, tmp_path):
    advisor = _fresh_advisor(monkeypatch, tmp_path)

    cfg_dir = tmp_path / ".openclaw" / ".clawmetry"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "insights_config.json").write_text(
        json.dumps({"anthropic_api_key": "sk-ant-from-insights"})
    )

    mode, cred = advisor._load_anthropic_auth()
    assert mode == "api_key"
    assert cred == "sk-ant-from-insights"


def test_openclaw_plugin_key_picked_up(monkeypatch, tmp_path):
    advisor = _fresh_advisor(monkeypatch, tmp_path)

    oc_dir = tmp_path / ".openclaw"
    oc_dir.mkdir(parents=True)
    (oc_dir / "openclaw.json").write_text(json.dumps({
        "plugins": {
            "entries": {
                "anthropic": {"enabled": True, "apiKey": "sk-ant-from-plugin"}
            }
        }
    }))

    mode, cred = advisor._load_anthropic_auth()
    assert mode == "api_key"
    assert cred == "sk-ant-from-plugin"


def test_openclaw_provider_key_picked_up(monkeypatch, tmp_path):
    advisor = _fresh_advisor(monkeypatch, tmp_path)

    oc_dir = tmp_path / ".openclaw"
    oc_dir.mkdir(parents=True)
    (oc_dir / "openclaw.json").write_text(json.dumps({
        "providers": {"anthropic": {"api_key": "sk-ant-from-provider"}}
    }))

    mode, cred = advisor._load_anthropic_auth()
    assert mode == "api_key"
    assert cred == "sk-ant-from-provider"


def test_non_sk_ant_values_ignored(monkeypatch, tmp_path):
    """Defense against an OAuth refresh token (``sk-ant-ort...``) being
    pulled out of a profile blob and silently sent as ``x-api-key``."""
    advisor = _fresh_advisor(monkeypatch, tmp_path)

    oc_dir = tmp_path / ".openclaw"
    oc_dir.mkdir(parents=True)
    # Garbage / clearly-not-a-key values must be skipped, not returned.
    (oc_dir / "openclaw.json").write_text(json.dumps({
        "plugins": {"entries": {"anthropic": {"apiKey": "fake-not-a-key"}}}
    }))

    mode, cred = advisor._load_anthropic_auth()
    assert mode is None
    assert cred is None


def test_status_endpoint_never_leaks_key(monkeypatch, tmp_path):
    """The status endpoint must report availability without echoing the
    key itself — caller-visible /api/* responses stay key-free."""
    advisor = _fresh_advisor(monkeypatch, tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-do-not-leak")

    from flask import Flask
    app = Flask(__name__)
    from routes.selfevolve import bp_selfevolve
    app.register_blueprint(bp_selfevolve)

    with app.test_client() as c:
        resp = c.get("/api/selfevolve/status")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert "sk-ant-do-not-leak" not in body
        data = resp.get_json()
        assert data["available"] is True
        assert data["auth_mode"] == "api_key"
