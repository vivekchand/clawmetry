"""Regression: distinguish native OpenClaw tool-search builds from plain
OpenClaw (#2732), without losing the existing NemoClaw-patch detection (#2683).
Also distinguishes basic-native (3 infrastructure symbols) from full-native
(all 5 NATIVE_TOOL_SEARCH_PATTERNS including enforcement signals) (#2877).

Before the #2732 fix, ``_nemoclaw_tool_catalog_state()`` was the only signal;
it returned ``None`` for native builds, leaving them indistinguishable from "no
catalog at all". After #2877, ``_openclaw_tool_catalog_kind()`` returns
``"native-full"`` for builds that also carry ``visibleAllowedToolNames`` /
``replayAllowedToolNames`` (enforcement active), and ``"native"`` for builds
with only the three base infrastructure symbols.
"""
from __future__ import annotations

import pytest

import clawmetry.adapters.openclaw as oc


PATCH_MARKER = b"/* nemoclaw compact tool catalog (#2600) */\nexport const x = 1;\n"
NATIVE_BLOB = (
    # Three base infrastructure symbols -> basic-native build ("native").
    b"export function applyToolSearchCatalog(){}\n"
    b"export function buildToolSearchRunPlan(){}\n"
    b"export const uncompactedEffectiveTools = [];\n"
)
FULL_NATIVE_BLOB = (
    # All five NATIVE_TOOL_SEARCH_PATTERNS: base + enforcement -> "native-full".
    b"export function applyToolSearchCatalog(){}\n"
    b"export function buildToolSearchRunPlan(){}\n"
    b"export const uncompactedEffectiveTools = [];\n"
    b"export const visibleAllowedToolNames = [];\n"
    b"export const replayAllowedToolNames = [];\n"
)
PARTIAL_NATIVE_BLOB = (
    # Only two of three base symbols -> NOT a native build per the patch script's
    # NATIVE_TOOL_SEARCH_PATTERNS contract.
    b"export function applyToolSearchCatalog(){}\n"
    b"export function buildToolSearchRunPlan(){}\n"
)
ENFORCEMENT_ONLY_BLOB = (
    # Enforcement symbols without the catalog infrastructure -> NOT native.
    # Enforcement only counts when it builds on the native catalog symbols.
    b"toolSearchRunPlan.visibleAllowedToolNames\n"
    b"toolSearchRunPlan.replayAllowedToolNames\n"
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


def test_full_native_enforcement_build_detected(monkeypatch, tmp_path):
    home = _make_dist(tmp_path, FULL_NATIVE_BLOB)
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert oc._nemoclaw_tool_catalog_state() is None
    assert oc._openclaw_tool_catalog_kind() == "native-full"


def test_full_native_build_scan_returns_enforcement_flag(monkeypatch, tmp_path):
    # All 5 NATIVE_TOOL_SEARCH_PATTERNS: scan must return native=True, enforcement=True.
    home = _make_dist(tmp_path, FULL_NATIVE_BLOB)
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert oc._openclaw_tool_catalog_kind() == "native-full"
    _patched, native, enforcement = oc._scan_openclaw_selection_runtime()
    assert native is True
    assert enforcement is True


def test_basic_native_build_is_not_enforced(monkeypatch, tmp_path):
    # 3 infrastructure symbols only -> native but enforcement absent.
    home = _make_dist(tmp_path, NATIVE_BLOB)
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert oc._openclaw_tool_catalog_kind() == "native"
    _patched, native, enforcement = oc._scan_openclaw_selection_runtime()
    assert native is True
    assert enforcement is False


def test_enforcement_symbols_without_infrastructure_not_native(monkeypatch, tmp_path):
    # Stray allow-list symbols with no catalog build -> no native signal.
    home = _make_dist(tmp_path, ENFORCEMENT_ONLY_BLOB)
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert oc._openclaw_tool_catalog_kind() is None
    _patched, native, enforcement = oc._scan_openclaw_selection_runtime()
    assert native is False
    assert enforcement is False


def test_nemoclaw_patch_wins_over_native(monkeypatch, tmp_path):
    home = _make_dist(tmp_path, PATCH_MARKER + NATIVE_BLOB)
    monkeypatch.setenv("OPENCLAW_HOME", str(home))
    assert oc._nemoclaw_tool_catalog_state() is True
    assert oc._openclaw_tool_catalog_kind() == "nemoclaw"


def test_nemoclaw_patch_wins_over_full_native(monkeypatch, tmp_path):
    # NemoClaw patch still wins even over a full-native (enforcement-active) build.
    home = _make_dist(tmp_path, PATCH_MARKER + FULL_NATIVE_BLOB)
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
