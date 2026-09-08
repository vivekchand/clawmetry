"""Guard: the desktop shell's onboarding stamp also unblocks the
dashboard's onboarding gate.

Bug pinned here (founder live-hit 2026-08-12): a user completed the
desktop shell's own onboarding pane (OAuth + chose Self-Host), the
daemon started, the dashboard loaded — and then the dashboard's own
onboarding gate re-showed the "Self-Host / Sign in for a free 7-day
Pro trial that unlocks every runtime" modal ON TOP of the welcome view,
asking the user to onboard AGAIN.

Root cause: two stamp files in two locations.

  * Shell stamp   ~/Library/Application Support/ClawMetry/runtime/onboarding-completed.json
                  (checked by ``is_first_launch``, gates the shell's own pane)
  * Dashboard stamp ~/.clawmetry/onboarding.json
                    (checked by ``routes/onboarding.py::_STATE_PATH``,
                    gates the browser onboarding modal)

The shell wrote only its own stamp. The dashboard's gate falls through
to ``_license_state()`` and ``_cloud_connected()``, and self-host with
a nocloud marker plus a trial mint that hasn't landed on disk yet leaves
both empty, so ``_resolve_state()`` returns ``{required: True}``.

These tests pin that the shell now writes BOTH files when the user
completed onboarding with a known mode.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from desktop import onboarding as desk_onb  # noqa: E402


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Redirect ``~`` to a tmp dir for the module's dashboard-gate write."""
    monkeypatch.setattr(
        desk_onb, "_DASHBOARD_GATE_STATE_PATH",
        tmp_path / ".clawmetry" / "onboarding.json",
    )
    return tmp_path


def _read_dashboard_gate(fake_home: Path) -> dict:
    p = fake_home / ".clawmetry" / "onboarding.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _read_shell_stamp(runtime: Path) -> dict:
    p = runtime / desk_onb.ONBOARDING_STAMP_NAME
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def test_selfhost_signed_in_writes_both_stamps(tmp_path, fake_home):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    desk_onb.mark_onboarding_completed(
        runtime,
        signed_in=True,
        provider="github",
        email="user@example.com",
        mode="selfhost",
    )
    shell = _read_shell_stamp(runtime)
    assert shell["signed_in"] is True
    assert shell["mode"] == "selfhost"

    gate = _read_dashboard_gate(fake_home)
    assert gate.get("choice") == "selfhost_trial", (
        "Self-host onboarding must record selfhost_trial in the dashboard "
        "gate file — otherwise /api/onboarding/state re-prompts on next load."
    )
    assert gate.get("source") == "desktop_shell"
    assert isinstance(gate.get("completed_at"), int)


def test_cloud_signed_in_writes_managed_choice(tmp_path, fake_home):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    desk_onb.mark_onboarding_completed(
        runtime, signed_in=True, provider="google",
        email="user@example.com", mode="cloud",
    )
    gate = _read_dashboard_gate(fake_home)
    assert gate.get("choice") == "managed"


def test_skipped_auth_writes_only_shell_stamp(tmp_path, fake_home):
    """User dismissed the pane without authenticating: the shell stamps
    itself so it won't re-prompt, but the dashboard gate MUST still show
    a choice (this install owes one). Do not write the gate file."""
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    desk_onb.mark_onboarding_completed(
        runtime, signed_in=False, provider="", email="", mode="",
    )
    assert _read_shell_stamp(runtime) != {}
    assert not (fake_home / ".clawmetry" / "onboarding.json").exists(), (
        "A skipped-auth stamp must not lie to the dashboard gate — "
        "the user still owes a choice there."
    )


def test_signed_in_without_mode_does_not_write_gate(tmp_path, fake_home):
    """Legacy callers not passing mode should not silently record a wrong
    choice. The gate stays empty until we know the mode."""
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    desk_onb.mark_onboarding_completed(
        runtime, signed_in=True, provider="github", email="", mode="",
    )
    assert not (fake_home / ".clawmetry" / "onboarding.json").exists()


def test_unknown_mode_is_ignored(tmp_path, fake_home):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    desk_onb.mark_onboarding_completed(
        runtime, signed_in=True, provider="github", email="",
        mode="something-else",
    )
    assert not (fake_home / ".clawmetry" / "onboarding.json").exists()


def test_gate_choice_matches_routes_onboarding_schema(tmp_path, fake_home):
    """Pin the exact schema ``routes/onboarding.py::_resolve_state`` reads.
    If either side drifts (key rename, tighter parsing) the dashboard's
    gate silently re-prompts again — same failure mode as the bug this
    test guards, and hard to notice without an end-to-end launch."""
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    desk_onb.mark_onboarding_completed(
        runtime, signed_in=True, provider="github", email="",
        mode="selfhost",
    )
    gate = _read_dashboard_gate(fake_home)
    # routes/onboarding.py::_CHOICES = ("managed", "selfhost_license", "selfhost_trial")
    assert gate["choice"] in {"managed", "selfhost_license", "selfhost_trial"}
    # routes/onboarding.py::_read_choice_file returns the JSON dict as-is;
    # _resolve_state reads ``recorded.get("choice", "")``. Keeping the key
    # name pinned means this stays a one-file contract.
    assert "choice" in gate


def test_write_failure_does_not_raise(tmp_path, monkeypatch):
    """Boot must never crash on a stamp failure — a re-shown pane is
    annoying, a crashed shell is broken."""
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    # Point the gate at an unwriteable path (a directory where a file is
    # expected) and confirm we swallow the OSError.
    bad = tmp_path / "readonly-dir-in-place-of-file"
    bad.mkdir()
    monkeypatch.setattr(desk_onb, "_DASHBOARD_GATE_STATE_PATH", bad)
    # Should not raise.
    desk_onb.mark_onboarding_completed(
        runtime, signed_in=True, provider="github", email="",
        mode="selfhost",
    )


def test_dashboard_gate_state_path_is_stable():
    """The dashboard gate reads a hard-coded path
    (``~/.clawmetry/onboarding.json``, see ``routes/onboarding.py``).
    If we move ours, we resurrect the bug — pin the path shape here so
    a rename is loud."""
    assert desk_onb._DASHBOARD_GATE_STATE_PATH.name == "onboarding.json"
    assert desk_onb._DASHBOARD_GATE_STATE_PATH.parent.name == ".clawmetry"
