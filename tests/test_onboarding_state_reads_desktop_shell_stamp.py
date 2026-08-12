"""Guard: the dashboard's onboarding gate recognises the desktop shell's
own onboarding stamp — regardless of installer age.

Bug pinned here (founder live-hit 2026-08-12, second failure of the
same day): after fixing #4758 (shell writes ~/.clawmetry/onboarding.json
when it completes onboarding), the founder reopened the .dmg they
already had installed and STILL saw the "Welcome to ClawMetry / Where
should ClawMetry keep an eye on your agents?" gate — because the .dmg
they had was pre-#4758, so the shell never wrote the browser gate's
file. The pip wheel auto-updates every 6h; the .app bundle only
updates when the user redownloads. Any fix that lives only in
``desktop/`` reaches users days late.

This test pins the dashboard-side fix: ``_resolve_state()`` also reads
the desktop shell's ``onboarding-completed.json`` (the file the shell
has always written, from every .dmg version). That fix rides the pip
wheel and reaches every install on the next auto-update.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """Fresh module import + tmp paths for the browser gate file, the
    desktop shell stamp, and the nocloud marker."""
    from routes import onboarding as m

    # Redirect the browser gate's own state file into tmp.
    gate_state = tmp_path / "browser_gate" / "onboarding.json"
    monkeypatch.setattr(m, "_STATE_PATH", str(gate_state))

    # Redirect the desktop shell's runtime dir into tmp.
    shell_runtime = tmp_path / "shell_runtime"
    shell_runtime.mkdir()
    monkeypatch.setattr(m, "_desktop_shell_runtime_dir",
                        lambda: shell_runtime)

    # By default: no license, no cloud token, cloud enabled (no nocloud).
    monkeypatch.setattr(m, "_license_state", lambda: "")
    monkeypatch.setattr(m, "_cloud_connected", lambda: False)

    yield m, gate_state, shell_runtime


def _write_shell_stamp(shell_runtime: Path, payload: dict) -> None:
    (shell_runtime / "onboarding-completed.json").write_text(
        json.dumps(payload)
    )


def _write_gate_choice(gate_state: Path, choice: str) -> None:
    gate_state.parent.mkdir(parents=True, exist_ok=True)
    gate_state.write_text(json.dumps({"choice": choice, "completed_at": 1}))


# ── Baseline: no stamps anywhere → gate prompts (unchanged behavior) ──

def test_no_stamps_gate_required(isolated):
    m, gate_state, shell_runtime = isolated
    assert m._resolve_state() == {
        "required": True, "state": "none", "source": "none",
    }


# ── The bug: shell stamped selfhost, dashboard now recognises it ──

def test_new_dmg_selfhost_stamp_is_recognized(isolated):
    """New .dmg (post-#4758) writes explicit mode=selfhost. Dashboard
    treats it as selfhost_trial without touching the gate file."""
    m, gate_state, shell_runtime = isolated
    _write_shell_stamp(shell_runtime, {
        "completed": True, "signed_in": True,
        "provider": "github", "email": "u@example.com",
        "mode": "selfhost",
    })
    result = m._resolve_state()
    assert result == {
        "required": False, "state": "selfhost_trial",
        "source": "desktop_shell",
    }
    assert not gate_state.exists(), (
        "The dashboard-side fix must not write the gate file — that "
        "would race with #4758's shell-side write."
    )


def test_new_dmg_cloud_stamp_is_recognized(isolated):
    m, gate_state, shell_runtime = isolated
    _write_shell_stamp(shell_runtime, {
        "completed": True, "signed_in": True,
        "provider": "google", "email": "u@example.com",
        "mode": "cloud",
    })
    result = m._resolve_state()
    assert result["required"] is False
    assert result["state"] == "managed"
    assert result["source"] == "desktop_shell"


# ── Old .dmg (pre-#4758) has no mode field. Infer from nocloud marker. ──

def test_old_dmg_no_mode_with_nocloud_marker_is_selfhost(isolated, monkeypatch):
    """Pre-#4758 stamp has no mode. Nocloud marker present (shell ran
    `clawmetry connect --keep-local`) — self-host was the intent."""
    m, gate_state, shell_runtime = isolated
    _write_shell_stamp(shell_runtime, {
        "completed": True, "signed_in": True,
        "provider": "github", "email": "u@example.com",
    })
    monkeypatch.setattr(
        "clawmetry.config.is_cloud_disabled", lambda: True,
    )
    result = m._resolve_state()
    assert result == {
        "required": False, "state": "selfhost_trial",
        "source": "desktop_shell",
    }


def test_old_dmg_no_mode_without_nocloud_is_managed(isolated, monkeypatch):
    """Pre-#4758 stamp, no nocloud marker → managed onboarding."""
    m, gate_state, shell_runtime = isolated
    _write_shell_stamp(shell_runtime, {
        "completed": True, "signed_in": True,
        "provider": "google", "email": "u@example.com",
    })
    monkeypatch.setattr(
        "clawmetry.config.is_cloud_disabled", lambda: False,
    )
    result = m._resolve_state()
    assert result["state"] == "managed"
    assert result["source"] == "desktop_shell"


# ── Dismissed shell pane MUST still prompt the browser gate ──

def test_shell_stamp_without_signed_in_does_not_bypass_gate(isolated):
    """User dismissed the shell pane without signing in. Shell stamps
    signed_in=False so it doesn't re-prompt itself, but the dashboard
    MUST still show the gate — the user owes a choice."""
    m, gate_state, shell_runtime = isolated
    _write_shell_stamp(shell_runtime, {
        "completed": True, "signed_in": False,
        "provider": "", "email": "", "mode": "",
    })
    result = m._resolve_state()
    assert result["required"] is True


def test_shell_stamp_without_completed_is_ignored(isolated):
    m, gate_state, shell_runtime = isolated
    _write_shell_stamp(shell_runtime, {
        "completed": False, "signed_in": True, "mode": "selfhost",
    })
    result = m._resolve_state()
    assert result["required"] is True


# ── Non-desktop install: no stamp file, no change to existing behavior ──

def test_pip_install_no_desktop_falls_through(isolated):
    """User did `pip install clawmetry && clawmetry` without ever
    touching the .app. No shell stamp exists → gate check runs the old
    flow (this test is the same as the baseline; kept explicit so a
    future refactor that reorders _resolve_state doesn't accidentally
    require a shell dir)."""
    m, gate_state, shell_runtime = isolated
    result = m._resolve_state()
    assert result["required"] is True


# ── Precedence: license and browser-gate file still win ──

def test_browser_gate_file_still_wins_over_shell_stamp(isolated):
    """If the user goes through the BROWSER gate after the shell pane
    (say they clicked something in the dashboard), the browser file is
    the more recent explicit choice and must take precedence."""
    m, gate_state, shell_runtime = isolated
    _write_shell_stamp(shell_runtime, {
        "completed": True, "signed_in": True, "mode": "selfhost",
    })
    _write_gate_choice(gate_state, "managed")
    result = m._resolve_state()
    assert result["state"] == "managed"
    assert result["source"] == "gate"


def test_local_license_still_wins_over_shell_stamp(isolated, monkeypatch):
    """An active local license reflects the user's ACTUAL entitlement,
    which is a stronger signal than the historical shell choice — a
    trial-then-paid user's state should be their license, not the trial
    stamp from months ago."""
    m, gate_state, shell_runtime = isolated
    _write_shell_stamp(shell_runtime, {
        "completed": True, "signed_in": True, "mode": "selfhost",
    })
    monkeypatch.setattr(m, "_license_state", lambda: "selfhost_license")
    result = m._resolve_state()
    assert result["state"] == "selfhost_license"
    assert result["source"] == "license"


# ── Robustness ──

def test_corrupt_shell_stamp_falls_through(isolated):
    m, gate_state, shell_runtime = isolated
    (shell_runtime / "onboarding-completed.json").write_text("not-json{")
    result = m._resolve_state()
    assert result["required"] is True


def test_shell_stamp_wrong_shape_falls_through(isolated):
    m, gate_state, shell_runtime = isolated
    (shell_runtime / "onboarding-completed.json").write_text('"a string"')
    result = m._resolve_state()
    assert result["required"] is True


def test_unknown_mode_infers_from_environment(isolated, monkeypatch):
    m, gate_state, shell_runtime = isolated
    _write_shell_stamp(shell_runtime, {
        "completed": True, "signed_in": True, "mode": "banana",
    })
    monkeypatch.setattr(
        "clawmetry.config.is_cloud_disabled", lambda: True,
    )
    # Unknown mode falls into the "infer" path, which returns
    # selfhost_trial when nocloud is set.
    assert m._resolve_state()["state"] == "selfhost_trial"


# ── The shell-stamp-path shape is pinned so a rename is loud ──

def test_shell_stamp_lives_under_ClawMetry_runtime():
    """Path shape must stay in sync with
    ``desktop/app.py::_runtime_dir`` — if the shell moves its stamp,
    this test flags the rename before the fix silently stops firing."""
    from routes import onboarding as m
    p = m._desktop_shell_runtime_dir()
    assert p.name == "runtime"
    assert p.parent.name == "ClawMetry"


# ── Revert-guard: the shell-stamp branch is actually WIRED into
#    _resolve_state (not just present as a dead helper) ──

def test_shell_stamp_branch_is_reachable_in_resolve_state(isolated):
    """If a future refactor accidentally drops the ``_shell_stamp_choice``
    call from ``_resolve_state``, this test goes red before the bug
    ships. Contrived setup that only ``_shell_stamp_choice`` can
    satisfy: no gate file, no license, no cloud, only a shell stamp."""
    m, gate_state, shell_runtime = isolated
    _write_shell_stamp(shell_runtime, {
        "completed": True, "signed_in": True, "mode": "cloud",
    })
    result = m._resolve_state()
    assert result["required"] is False, (
        "_resolve_state stopped consulting _shell_stamp_choice — the "
        "onboarding gate will re-prompt users who already completed "
        "shell onboarding. See #4758 and the follow-up dashboard-side "
        "fix."
    )
