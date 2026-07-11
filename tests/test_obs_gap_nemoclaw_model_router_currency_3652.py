"""Tests for #3652 — NemoClaw model-router install currency/staleness verdict.

Mirrors ``isManagedModelRouterCurrent()`` from harness
``src/lib/onboard/model-router.ts``: a stale model-router (installed from
an old source SHA that no longer matches the expected/current source pin)
must be distinguishable from a current one in ``DetectResult.meta``.
"""
from __future__ import annotations

import pytest

from clawmetry.adapters.openclaw import _model_router_currency

_SHA_A = "git:aaaa111122223333444455556666777788889999"
_SHA_B = "git:bbbb111122223333444455556666777788889999"


def _write_fps(venv_path, installed, expected=None):
    (venv_path / ".nemoclaw-source-fingerprint").write_text(installed)
    if expected is not None:
        (venv_path / ".nemoclaw-expected-fingerprint").write_text(expected)


def test_current_when_fingerprints_match(tmp_path, monkeypatch):
    venv = tmp_path / "mrv"
    venv.mkdir()
    _write_fps(venv, _SHA_A, _SHA_A)
    monkeypatch.setenv("NEMOCLAW_MODEL_ROUTER_VENV", str(venv))
    assert _model_router_currency() == {"modelRouterCurrent": True}


def test_stale_when_fingerprints_differ(tmp_path, monkeypatch):
    venv = tmp_path / "mrv"
    venv.mkdir()
    _write_fps(venv, _SHA_A, _SHA_B)
    monkeypatch.setenv("NEMOCLAW_MODEL_ROUTER_VENV", str(venv))
    assert _model_router_currency() == {"modelRouterCurrent": False}


def test_no_expected_file_returns_empty(tmp_path, monkeypatch):
    """Old installs that pre-date the expected-pin file must return {} (unknown)."""
    venv = tmp_path / "mrv"
    venv.mkdir()
    _write_fps(venv, _SHA_A)
    monkeypatch.setenv("NEMOCLAW_MODEL_ROUTER_VENV", str(venv))
    assert _model_router_currency() == {}


def test_no_venv_returns_empty(tmp_path, monkeypatch):
    """Plain OpenClaw installs (no venv) must return {} silently."""
    monkeypatch.setenv("NEMOCLAW_MODEL_ROUTER_VENV", str(tmp_path / "nope"))
    assert _model_router_currency() == {}


def test_trailing_newline_stripped_before_compare(tmp_path, monkeypatch):
    """Trailing newlines in fingerprint files must not cause false stale verdict."""
    venv = tmp_path / "mrv"
    venv.mkdir()
    _write_fps(venv, _SHA_A + "\n", _SHA_A + "\n")
    monkeypatch.setenv("NEMOCLAW_MODEL_ROUTER_VENV", str(venv))
    assert _model_router_currency() == {"modelRouterCurrent": True}
