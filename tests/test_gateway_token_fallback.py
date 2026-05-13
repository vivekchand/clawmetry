"""Tests for dashboard._detect_gateway_token fallback hierarchy.

Covers issue #1127: OpenClaw stores the gateway auth token under different
JSON paths depending on install age / schema. The reader must try
``gateway.auth.token`` first (current schema) and fall back to top-level
``auth.token`` (older / alternate schema) before giving up.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import dashboard  # noqa: E402


@pytest.fixture
def isolated_openclaw_dir(tmp_path, monkeypatch):
    """Point dashboard at a clean tmp openclaw dir and strip the env var."""
    monkeypatch.delenv("OPENCLAW_GATEWAY_TOKEN", raising=False)
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path))
    # Block the running-process path (Linux /proc) from leaking a token.
    monkeypatch.setattr(
        dashboard.os, "environ", dict(os.environ), raising=False
    )
    return tmp_path


def _write_cfg(path: Path, cfg: dict):
    path.write_text(json.dumps(cfg))


def test_env_var_wins(isolated_openclaw_dir, monkeypatch):
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", "env-token")
    _write_cfg(
        isolated_openclaw_dir / "openclaw.json",
        {"gateway": {"auth": {"token": "config-token"}}},
    )
    assert dashboard._detect_gateway_token() == "env-token"


def test_nested_gateway_auth_token(isolated_openclaw_dir):
    """Current OpenClaw schema: cfg.gateway.auth.token."""
    _write_cfg(
        isolated_openclaw_dir / "openclaw.json",
        {"gateway": {"auth": {"token": "nested-token"}}},
    )
    assert dashboard._detect_gateway_token() == "nested-token"


def test_top_level_auth_token_fallback(isolated_openclaw_dir):
    """Older / alternate schema: cfg.auth.token at top level."""
    _write_cfg(
        isolated_openclaw_dir / "openclaw.json",
        {"auth": {"token": "top-level-token"}},
    )
    assert dashboard._detect_gateway_token() == "top-level-token"


def test_nested_preferred_over_top_level(isolated_openclaw_dir):
    """When both exist, the gateway-nested path wins (matches current OpenClaw)."""
    _write_cfg(
        isolated_openclaw_dir / "openclaw.json",
        {
            "gateway": {"auth": {"token": "nested-wins"}},
            "auth": {"token": "top-level-loses"},
        },
    )
    assert dashboard._detect_gateway_token() == "nested-wins"


def test_returns_none_when_no_token_present(isolated_openclaw_dir):
    _write_cfg(
        isolated_openclaw_dir / "openclaw.json",
        {"gateway": {"port": 18789}, "auth": {"profiles": {}}},
    )
    assert dashboard._detect_gateway_token() is None


def test_returns_none_when_config_missing(isolated_openclaw_dir):
    # No openclaw.json written.
    assert dashboard._detect_gateway_token() is None


def test_skips_malformed_json(isolated_openclaw_dir):
    (isolated_openclaw_dir / "openclaw.json").write_text("{not json")
    assert dashboard._detect_gateway_token() is None


def test_empty_token_falls_through(isolated_openclaw_dir):
    """An empty-string token should not be returned — keep looking."""
    _write_cfg(
        isolated_openclaw_dir / "openclaw.json",
        {
            "gateway": {"auth": {"token": ""}},
            "auth": {"token": "real-token"},
        },
    )
    # Empty gateway token must fall through to top-level auth.token.
    assert dashboard._detect_gateway_token() == "real-token"
