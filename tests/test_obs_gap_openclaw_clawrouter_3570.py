"""Tests for issue #3570 — openclaw: ClawHub promotional model offers not surfaced.

Verifies that _clawrouter_detect() reads promos.json from
~/.openclaw/clawrouter/ (or OPENCLAW_CLAWROUTER_HOME) and surfaces
active promo state, count, and model ref alongside the existing config/quota data.

Fingerprint: hgap-966f276123
"""
from __future__ import annotations

import importlib
import json
import os


def _reload_adapter():
    import clawmetry.adapters.openclaw as oc_mod
    importlib.reload(oc_mod)
    return oc_mod


def test_active_list_format_promos_surfaced(tmp_path):
    """List-format promos with active claims: all keys surfaced."""
    cr_home = tmp_path / "clawrouter"
    cr_home.mkdir()
    promos = {
        "claimedPromos": [
            {"id": "promo-abc", "modelRef": "claude-sonnet-5", "active": True},
            {"id": "promo-xyz", "modelRef": "gpt-4o", "active": True},
        ]
    }
    (cr_home / "promos.json").write_text(json.dumps(promos))
    os.environ["OPENCLAW_CLAWROUTER_HOME"] = str(cr_home)
    try:
        oc = _reload_adapter()
        result = oc._clawrouter_detect()
    finally:
        del os.environ["OPENCLAW_CLAWROUTER_HOME"]

    assert result["clawRouterPromoActive"] is True
    assert result["clawRouterPromoCount"] == 2
    assert result["clawRouterPromoModel"] == "claude-sonnet-5"


def test_no_promos_file_no_promo_keys(tmp_path):
    """Missing promos.json: no promo keys in result (no regression)."""
    cr_home = tmp_path / "clawrouter"
    cr_home.mkdir()
    # Write config so the function has something to return
    (cr_home / "config.json").write_text(json.dumps({"enabled": True}))
    os.environ["OPENCLAW_CLAWROUTER_HOME"] = str(cr_home)
    try:
        oc = _reload_adapter()
        result = oc._clawrouter_detect()
    finally:
        del os.environ["OPENCLAW_CLAWROUTER_HOME"]

    assert "clawRouterPromoActive" not in result
    assert "clawRouterPromoCount" not in result
    assert "clawRouterPromoModel" not in result
    assert result.get("clawRouterEnabled") is True


def test_malformed_promos_json_silently_skipped(tmp_path):
    """Malformed promos.json is silently ignored; other data still extracted."""
    cr_home = tmp_path / "clawrouter"
    cr_home.mkdir()
    (cr_home / "config.json").write_text(json.dumps({"enabled": True, "version": "0.3.1"}))
    (cr_home / "promos.json").write_text("not-valid-json{{{")
    os.environ["OPENCLAW_CLAWROUTER_HOME"] = str(cr_home)
    try:
        oc = _reload_adapter()
        result = oc._clawrouter_detect()
    finally:
        del os.environ["OPENCLAW_CLAWROUTER_HOME"]

    assert "clawRouterPromoActive" not in result
    assert result["clawRouterEnabled"] is True
    assert result["clawRouterVersion"] == "0.3.1"


def test_single_promo_active_format(tmp_path):
    """Single-promo format with active=True: flag and model surfaced."""
    cr_home = tmp_path / "clawrouter"
    cr_home.mkdir()
    promos = {"active": True, "modelRef": "gemini-2.5-pro", "promoId": "clawhub-summer"}
    (cr_home / "promos.json").write_text(json.dumps(promos))
    os.environ["OPENCLAW_CLAWROUTER_HOME"] = str(cr_home)
    try:
        oc = _reload_adapter()
        result = oc._clawrouter_detect()
    finally:
        del os.environ["OPENCLAW_CLAWROUTER_HOME"]

    assert result["clawRouterPromoActive"] is True
    assert result["clawRouterPromoModel"] == "gemini-2.5-pro"
    assert "clawRouterPromoCount" not in result


def test_single_promo_inactive_not_surfaced(tmp_path):
    """Single-promo format with active=False: no promo keys emitted."""
    cr_home = tmp_path / "clawrouter"
    cr_home.mkdir()
    promos = {"active": False, "modelRef": "claude-sonnet-5", "promoId": "clawhub-old"}
    (cr_home / "promos.json").write_text(json.dumps(promos))
    os.environ["OPENCLAW_CLAWROUTER_HOME"] = str(cr_home)
    try:
        oc = _reload_adapter()
        result = oc._clawrouter_detect()
    finally:
        del os.environ["OPENCLAW_CLAWROUTER_HOME"]

    assert "clawRouterPromoActive" not in result
    assert "clawRouterPromoModel" not in result
