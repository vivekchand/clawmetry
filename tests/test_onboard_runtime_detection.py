"""Tests for onboarding runtime detection (#3917, founder request).

A machine full of Cursor/Claude Code sessions used to onboard with no hint
that ClawMetry could watch them, no mention that the free tier covers only
OpenClaw + NVIDIA NemoClaw, and no pointer to the license key or Cloud
signup. runtime_probe supplies presence-only probes (no parsing, no gated
behaviour) and pure rendering; the onboard wizard prints them.
"""

import os

import pytest

from clawmetry import runtime_probe
from clawmetry.entitlements import get_entitlement  # noqa: F401 (import parity canary)
from clawmetry.runtime_probe import (
    FREE_RUNTIMES,
    RUNTIME_PROBES,
    probe_runtimes,
    render_detection_lines,
)


def test_probe_catalogue_covers_all_supported_runtimes():
    """One probe per supported runtime, ids unique, free set exact."""
    ids = [p.id for p in RUNTIME_PROBES]
    assert len(ids) == len(set(ids))
    assert len(ids) == 14
    assert FREE_RUNTIMES == {"openclaw", "nemoclaw"}
    for rt in ("claude_code", "cursor", "codex", "qwen_code", "picoclaw"):
        assert rt in ids


def test_probe_found_via_planted_path(monkeypatch, tmp_path):
    """A runtime's default data dir existing flips found=True (both env
    vars set: Windows expanduser ignores HOME, clawmetry#3850)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    (tmp_path / ".qwen" / "projects").mkdir(parents=True)

    results = {p["id"]: p for p in probe_runtimes()}
    assert results["qwen_code"]["found"] is True
    assert results["goose"]["found"] is False
    assert results["qwen_code"]["free"] is False


def test_probe_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    hermes_home = tmp_path / "custom-hermes"
    hermes_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    results = {p["id"]: p for p in probe_runtimes()}
    assert results["hermes"]["found"] is True


def test_render_free_only_machine_has_no_pro_cta():
    probes = [
        {"id": "openclaw", "label": "OpenClaw", "free": True, "found": True},
        {"id": "cursor", "label": "Cursor", "free": False, "found": False},
    ]
    lines = render_detection_lines(probes)
    joined = "\n".join(lines)
    assert "OpenClaw" in joined
    assert "Free forever" in joined
    assert "license key" not in joined
    assert "Cursor" not in joined


def test_render_paid_detected_names_runtime_and_both_paths():
    """The founder's exact ask: show detections, state the free tier,
    offer the license key AND the cloud signup for the rest."""
    probes = [
        {"id": "claude_code", "label": "Claude Code", "free": False, "found": True},
        {"id": "cursor", "label": "Cursor", "free": False, "found": True},
        {"id": "openclaw", "label": "OpenClaw", "free": True, "found": False},
    ]
    lines = render_detection_lines(probes)
    joined = "\n".join(lines)
    assert "Claude Code" in joined and "Cursor" in joined
    assert "Free forever: OpenClaw and NVIDIA NemoClaw." in joined
    assert "clawmetry activate" in joined
    assert "Cloud" in joined
    # The em-dash/double-dash ban applies to user-facing copy.
    assert "—" not in joined and "--" not in joined


def test_render_nothing_detected_is_silent():
    probes = [
        {"id": "openclaw", "label": "OpenClaw", "free": True, "found": False},
    ]
    assert render_detection_lines(probes) == []


def test_probes_never_raise_when_probe_explodes(monkeypatch):
    """A single broken probe answers found=False; the sweep never raises."""
    monkeypatch.setattr(
        runtime_probe.RuntimeProbe,
        "found",
        lambda self: (_ for _ in ()).throw(OSError("boom")),
    )
    results = probe_runtimes()
    assert len(results) == 14
    assert all(p["found"] is False for p in results)
