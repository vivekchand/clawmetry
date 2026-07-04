"""Tests for issue #3524 — openclaw: ClawRouter provider plugin not surfaced.

Verifies that _clawrouter_detect() reads config.json and quota.json from
~/.openclaw/clawrouter/ (or OPENCLAW_CLAWROUTER_HOME) and surfaces
credential-scoped model catalog, transport list, and budget/quota data.

Fingerprint: hgap-90b7f3ec9b
"""
from __future__ import annotations

import importlib
import json
import os


def _reload_adapter():
    import clawmetry.adapters.openclaw as oc_mod
    importlib.reload(oc_mod)
    return oc_mod


def test_config_and_quota_both_present(tmp_path):
    """Full config + quota: all keys surfaced."""
    cr_home = tmp_path / "clawrouter"
    cr_home.mkdir()
    config = {
        "enabled": True,
        "version": "0.3.1",
        "transports": ["openai-compatible", "anthropic-native", "gemini-native"],
        "models": [
            {"name": "claude-sonnet-5"},
            {"name": "gpt-4o"},
            "gemini-2.5-pro",
        ],
    }
    quota = {
        "totalBudgetUsd": 50.0,
        "credentials": [{"id": "cred-a"}, {"id": "cred-b"}],
    }
    (cr_home / "config.json").write_text(json.dumps(config))
    (cr_home / "quota.json").write_text(json.dumps(quota))

    os.environ["OPENCLAW_CLAWROUTER_HOME"] = str(cr_home)
    try:
        oc = _reload_adapter()
        result = oc._clawrouter_detect()
    finally:
        del os.environ["OPENCLAW_CLAWROUTER_HOME"]

    assert result["clawRouterEnabled"] is True
    assert result["clawRouterVersion"] == "0.3.1"
    assert result["clawRouterTransports"] == [
        "openai-compatible", "anthropic-native", "gemini-native"
    ]
    assert result["clawRouterModels"] == ["claude-sonnet-5", "gpt-4o", "gemini-2.5-pro"]
    assert result["clawRouterBudgetUsd"] == 50.0
    assert result["clawRouterQuotaCredentials"] == 2


def test_absent_home_returns_empty_dict():
    """No ~/.openclaw/clawrouter/ → returns {} (plugin not installed)."""
    os.environ["OPENCLAW_CLAWROUTER_HOME"] = "/nonexistent/path/clawrouter"
    try:
        oc = _reload_adapter()
        result = oc._clawrouter_detect()
    finally:
        del os.environ["OPENCLAW_CLAWROUTER_HOME"]
    assert result == {}


def test_config_only_no_quota(tmp_path):
    """Config present but no quota file: config keys extracted, no budget keys."""
    cr_home = tmp_path / "clawrouter"
    cr_home.mkdir()
    (cr_home / "config.json").write_text(json.dumps({
        "enabled": False,
        "transports": ["openai-compatible"],
    }))
    os.environ["OPENCLAW_CLAWROUTER_HOME"] = str(cr_home)
    try:
        oc = _reload_adapter()
        result = oc._clawrouter_detect()
    finally:
        del os.environ["OPENCLAW_CLAWROUTER_HOME"]
    assert result["clawRouterEnabled"] is False
    assert result["clawRouterTransports"] == ["openai-compatible"]
    assert "clawRouterBudgetUsd" not in result
    assert "clawRouterQuotaCredentials" not in result


def test_malformed_config_json_quota_still_read(tmp_path):
    """Malformed config.json is silently skipped; quota data still extracted."""
    cr_home = tmp_path / "clawrouter"
    cr_home.mkdir()
    (cr_home / "config.json").write_text("not-valid-json{{{")
    (cr_home / "quota.json").write_text(json.dumps({
        "budgetUsd": 10.5,
        "credentialScopes": [{"id": "cred-x"}],
    }))
    os.environ["OPENCLAW_CLAWROUTER_HOME"] = str(cr_home)
    try:
        oc = _reload_adapter()
        result = oc._clawrouter_detect()
    finally:
        del os.environ["OPENCLAW_CLAWROUTER_HOME"]
    assert "clawRouterEnabled" not in result
    assert result["clawRouterBudgetUsd"] == 10.5
    assert result["clawRouterQuotaCredentials"] == 1


def test_empty_models_and_transports_not_surfaced(tmp_path):
    """Empty lists for models/transports are omitted from the result."""
    cr_home = tmp_path / "clawrouter"
    cr_home.mkdir()
    (cr_home / "config.json").write_text(json.dumps({
        "enabled": True,
        "transports": [],
        "models": [],
    }))
    os.environ["OPENCLAW_CLAWROUTER_HOME"] = str(cr_home)
    try:
        oc = _reload_adapter()
        result = oc._clawrouter_detect()
    finally:
        del os.environ["OPENCLAW_CLAWROUTER_HOME"]
    assert result.get("clawRouterEnabled") is True
    assert "clawRouterTransports" not in result
    assert "clawRouterModels" not in result
