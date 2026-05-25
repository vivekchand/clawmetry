"""Phase-3 daemon tests: family-runtime detection in the cloud snapshot.

The sync daemon labels which OpenClaw-family runtime (PicoClaw / NanoClaw) a
node is running so the cloud can show it. This is pure detection via the
adapters (no DuckDB, no writer lock). These tests point the adapters at the
committed fixtures via env overrides and assert the snapshot carries the
runtime label + the tiny `detectedRuntimes` summary.
"""
from __future__ import annotations

import os

import pytest

import clawmetry.sync as sync

_FIX = os.path.join(os.path.dirname(__file__), "fixtures", "runtimes")
_PICO_HOME = os.path.join(_FIX, "picoclaw")  # has workspace/sessions/*.jsonl
_NANO_DIR = os.path.join(_FIX, "nanoclaw", "REAL")  # has <group>/<session>/*.db


def test_no_family_runtimes_when_absent(monkeypatch, tmp_path):
    """No PicoClaw/NanoClaw on the host -> empty list, never raises."""
    monkeypatch.setenv("PICOCLAW_HOME", str(tmp_path / "nope-pico"))
    monkeypatch.setenv("CLAWMETRY_NANOCLAW_DIR", str(tmp_path / "nope-nano"))
    # Also keep discovery from finding a real checkout under $HOME.
    monkeypatch.setenv("HOME", str(tmp_path))
    assert sync._detect_family_runtimes() == []


def test_detects_picoclaw(monkeypatch):
    monkeypatch.setenv("PICOCLAW_HOME", _PICO_HOME)
    monkeypatch.delenv("CLAWMETRY_NANOCLAW_DIR", raising=False)
    rts = {r["name"]: r for r in sync._detect_family_runtimes()}
    assert "picoclaw" in rts
    assert rts["picoclaw"]["displayName"] == "PicoClaw"
    # The synthetic fixture has two sessions under workspace/sessions/.
    assert rts["picoclaw"]["sessionCount"] == 2


def test_detects_nanoclaw(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_NANOCLAW_DIR", _NANO_DIR)
    rts = {r["name"]: r for r in sync._detect_family_runtimes()}
    assert "nanoclaw" in rts
    assert rts["nanoclaw"]["displayName"] == "NanoClaw"
    assert rts["nanoclaw"]["sessionCount"] == 2


def test_runtime_info_includes_runtime_rows(monkeypatch):
    monkeypatch.setenv("PICOCLAW_HOME", _PICO_HOME)
    monkeypatch.setenv("CLAWMETRY_NANOCLAW_DIR", _NANO_DIR)
    info = sync._build_runtime_info()
    labels = {i["label"]: i["value"] for i in info["items"]}
    assert "PicoClaw" in labels
    assert "NanoClaw" in labels
    assert "session" in labels["PicoClaw"]


def test_runtime_info_never_raises_and_has_base_items(monkeypatch, tmp_path):
    """Base runtime rows (Python/OS) survive even with no family runtimes."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PICOCLAW_HOME", str(tmp_path / "nope"))
    monkeypatch.setenv("CLAWMETRY_NANOCLAW_DIR", str(tmp_path / "nope2"))
    info = sync._build_runtime_info()
    labels = [i["label"] for i in info["items"]]
    assert "Python" in labels
    assert "PicoClaw" not in labels
