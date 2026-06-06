"""Regression: distinguish native OpenClaw tool-search builds from plain
OpenClaw (#2732), without losing the existing NemoClaw-patch detection (#2683).

Before the fix, ``_nemoclaw_tool_catalog_state()`` was the only signal: it
scanned ``selection-*.js`` only for the NemoClaw patch marker and returned
``None`` for native-tool-search builds, leaving ``nemoclawToolCatalogEnabled``
unset and indistinguishable from "no catalog at all". The new
``_openclaw_tool_catalog_kind()`` helper closes the obs-gap by also returning
``"native"`` when the dist ships the three tool-search symbols.
"""
from __future__ import annotations

import pytest

import clawmetry.adapters.openclaw as oc


PATCH_MARKER = b"/* nemoclaw compact tool catalog (#2600) */\nexport const x = 1;\n"
NATIVE_BLOB = (
    b"export function applyToolSearchCatalog(){}\n"
    b"export function buildToolSearchRunPlan(){}\n"
    b"export const uncompactedEffectiveTools = [];\n"
)
PARTIAL_NATIVE_BLOB = (
    # Only two of three symbols -> NOT a native build per the patch script's
    # NATIVE_TOOL_SEARCH_PATTERNS contract.
    b"export function applyToolSearchCatalog(){}\n"
    b"export function buildToolSearchRunPlan(){}\n"
)


def _make_dist(tmp_path, blob: bytes, filename: str = "selection-abc.js"):
    home = tmp_path / ".openclaw"
    dist = home / "node_modules" / "openclaw" / "dist"
    dist.mkdir(parents=True)
    (dist / filename).write_bytes(blob)
    return home


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    # Strip env-var signals so the on-disk scan is the only input.
    monkeypatch.delenv("NEMOCLAW_TOOL_CATALOG", raising=False)
    # Default OPENCLAW_HOME to a non-existent dir; each test overrides.
    monkeypatch.setenv("OPENCLAW_HOME", "/nonexistent-openclaw-home-for-tests")


def test_plain_openclaw_returns_none(monkeypatch, tmp_path):
    home = tmp_path / ".openclaw"
    home.mkdir()
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert oc._nemoclaw_tool_catalog_state() is None
    assert oc._openclaw_tool_catalog_kind() is None


def test_native_tool_search_build_detected(monkeypatch, tmp_path):
    home = _make_dist(tmp_path, NATIVE_BLOB)
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    # Existing nemoclaw signal stays None (patch is not applied).
    assert oc._nemoclaw_tool_catalog_state() is None
    # NEW: native build is no longer indistinguishable from no catalog.
    assert oc._openclaw_tool_catalog_kind() == "native"


def test_nemoclaw_patch_wins_over_native(monkeypatch, tmp_path):
    home = _make_dist(tmp_path, PATCH_MARKER + NATIVE_BLOB)
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert oc._nemoclaw_tool_catalog_state() is True
    assert oc._openclaw_tool_catalog_kind() == "nemoclaw"


def test_partial_native_symbols_not_treated_as_native(monkeypatch, tmp_path):
    home = _make_dist(tmp_path, PARTIAL_NATIVE_BLOB)
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert oc._openclaw_tool_catalog_kind() is None


def test_nemoclaw_patch_only(monkeypatch, tmp_path):
    home = _make_dist(tmp_path, PATCH_MARKER)
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert oc._nemoclaw_tool_catalog_state() is True
    assert oc._openclaw_tool_catalog_kind() == "nemoclaw"


def test_env_var_disables_nemoclaw_but_kind_still_reports_provenance(monkeypatch, tmp_path):
    home = _make_dist(tmp_path, PATCH_MARKER)
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    monkeypatch.setenv("NEMOCLAW_TOOL_CATALOG", "0")
    # State reports False (disabled) per the harness gate.
    assert oc._nemoclaw_tool_catalog_state() is False
    # Kind still surfaces "nemoclaw" — the patched wrapper is on disk
    # regardless of the runtime gate.
    assert oc._openclaw_tool_catalog_kind() == "nemoclaw"


def test_env_var_without_dist_marker_keeps_state_but_no_kind(monkeypatch, tmp_path):
    home = tmp_path / ".openclaw"
    home.mkdir()
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    monkeypatch.setenv("NEMOCLAW_TOOL_CATALOG", "1")
    # Env-only signal: existing API still returns True (#2683 contract).
    assert oc._nemoclaw_tool_catalog_state() is True
    # But there's no on-disk wrapper, so no provenance to stamp.
    assert oc._openclaw_tool_catalog_kind() is None
