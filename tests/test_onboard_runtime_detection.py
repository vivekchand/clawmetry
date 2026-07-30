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
    assert "license key" not in joined, "a free-only machine gets no upsell line"
    assert "Cursor" not in joined


def test_render_paid_detected_names_runtime_and_both_paths():
    """The founder's exact ask: show detections, state the free tier,
    offer sign-in (trial) AND the license key for the rest."""
    probes = [
        {"id": "claude_code", "label": "Claude Code", "free": False, "found": True},
        {"id": "cursor", "label": "Cursor", "free": False, "found": True},
        {"id": "openclaw", "label": "OpenClaw", "free": True, "found": False},
    ]
    lines = render_detection_lines(probes)
    joined = "\n".join(lines)
    assert "Claude Code" in joined and "Cursor" in joined
    assert "sign in below" in joined and "7-day Pro trial" in joined
    assert "license key" in joined
    # The em-dash/double-dash ban applies to user-facing copy.
    assert "—" not in joined and "--" not in joined


def test_render_grid_compact_no_per_line_tier_labels():
    """Ten detections read as a 3-per-row checkmark grid; the tier story is
    told once in the summary lines, not as nine "(Pro)" labels (#4216)."""
    labels = [
        "OpenClaw", "Claude Code", "Codex", "Cursor", "Aider",
        "Goose", "opencode", "Qwen Code", "Hermes", "PicoClaw",
    ]
    probes = [
        {"id": lbl.lower().replace(" ", "_"), "label": lbl,
         "free": lbl == "OpenClaw", "found": True}
        for lbl in labels
    ]
    lines = render_detection_lines(probes)
    joined = "\n".join(lines)
    assert "(Pro)" not in joined and "(free)" not in joined
    grid = [ln for ln in lines if "[x]" in ln]
    assert len(grid) == 4  # 3 + 3 + 3 + 1
    assert grid[0].count("[x]") == 3
    assert "Detected 10 AI agent runtimes" in lines[0]
    assert "unlocks the other 9" in joined


def test_render_single_paid_runtime_named_in_unlock_line():
    probes = [
        {"id": "cursor", "label": "Cursor", "free": False, "found": True},
    ]
    joined = "\n".join(render_detection_lines(probes))
    assert "unlocks Cursor too" in joined
    assert "sign in below" in joined and "license key" in joined


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
