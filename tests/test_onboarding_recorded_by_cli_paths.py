"""Every onboarding path records the browser gate's choice file.

Regression (founder live-hit 2026-08-22): a machine onboarded with
``clawmetry connect`` — paying ``cloud_pro`` account, later switched to
local-only — opened http://localhost:8900 and was shown the first-run
"Welcome to ClawMetry" gate again, asking it to choose a hosting mode and
sign in a SECOND time, while ``clawmetry status`` on the same machine
printed the linked account and plan. One install, two disagreeing views:
the CLI onboarding paths never wrote ``~/.clawmetry/onboarding.json``, and
the gate's fallbacks all missed a cloud-plan-only entitlement.

Two halves are pinned here:
  1. Writers  — connect / onboard / license-activate / desktop shell all
     record a choice through ``clawmetry.onboarding_state``.
  2. Reader   — ``_resolve_state`` honours ``selfhost_free`` and treats a
     resolved PAID entitlement (the cloud plan cache, which no local
     ``license.key`` mirrors) as onboarding already done.
"""
from __future__ import annotations

import importlib
import inspect
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def home(monkeypatch, tmp_path):
    """Point the writer at a temp HOME. ``state_path()`` resolves per call
    precisely so this works."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(os.path, "expanduser",
                        lambda p: p.replace("~", str(tmp_path), 1)
                        if p.startswith("~") else p)
    return tmp_path


def _recorded(home_dir):
    path = home_dir / ".clawmetry" / "onboarding.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


# ── the writer itself ──────────────────────────────────────────────────

def test_record_and_read_roundtrip(home):
    from clawmetry import onboarding_state as obs

    assert obs.read_choice() == ""
    assert obs.record_choice("managed", source="cli:connect") is True
    assert _recorded(home)["choice"] == "managed"
    assert _recorded(home)["source"] == "cli:connect"
    assert obs.read_choice() == "managed"


def test_unknown_choice_is_refused_not_written(home):
    from clawmetry import onboarding_state as obs

    assert obs.record_choice("definitely-not-a-choice") is False
    assert _recorded(home) is None


def test_write_is_atomic_and_leaves_no_temp_file(home):
    from clawmetry import onboarding_state as obs

    obs.record_choice("selfhost_trial")
    leftovers = list((home / ".clawmetry").glob("onboarding.json.tmp*"))
    assert leftovers == [], f"temp file left behind: {leftovers}"


def test_corrupt_file_reads_as_no_choice(home):
    """Fail toward asking, never toward silently skipping the gate."""
    from clawmetry import onboarding_state as obs

    d = home / ".clawmetry"
    d.mkdir(parents=True, exist_ok=True)
    (d / "onboarding.json").write_text("{not json")
    assert obs.read_choice() == ""


def test_unwritable_home_never_raises(monkeypatch, tmp_path):
    """A failed write means the gate re-prompts; it must not break the
    onboarding command that called it."""
    from clawmetry import onboarding_state as obs

    monkeypatch.setattr(obs, "state_path",
                        lambda: str(tmp_path / "nope" / "x" / "onboarding.json"))
    monkeypatch.setattr(obs.os, "makedirs",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("read-only fs")))
    assert obs.record_choice("managed") is False


# ── the CLI writers ────────────────────────────────────────────────────

def test_onboard_wizard_helper_records_free_local_choice(home):
    """`clawmetry onboard` → "[0] local only, no account" is a real answer:
    the browser gate must not re-ask it."""
    from clawmetry import cli

    cli._record_gate_choice("selfhost_free")
    assert _recorded(home)["choice"] == "selfhost_free"


def test_connect_records_both_hosting_modes():
    """Contract test: ``_cmd_connect`` is far too large (and too network-
    bound) to drive end to end here, so pin that the recording call sits in
    it and covers BOTH branches — plain connect is managed, the keep-local
    sign-in is self-host."""
    from clawmetry import cli

    src = inspect.getsource(cli._cmd_connect)
    assert "record_choice" in src, "connect no longer records the gate choice"
    assert "managed" in src and "selfhost_trial" in src
    assert "_keep_local_signin" in src.split("record_choice", 1)[1][:200], (
        "connect must pick the choice from the keep-local flag, not hardcode one"
    )


def test_onboard_records_at_every_terminal_branch():
    """Failed sign-in fallbacks deliberately record NOTHING (the gate is the
    user's second chance); the three deliberate self-host endings do."""
    from clawmetry import cli

    src = inspect.getsource(cli._cmd_onboard)
    assert src.count("_record_gate_choice(") == 3, (
        "expected exactly the three explicit self-host/free endings to record"
    )
    for marker in ("No account connected. Running local-only",
                   "No account connected. Running the free plan"):
        tail = src.split(marker, 1)[1][:400]
        assert "_record_gate_choice" not in tail, (
            "a failed sign-in must leave the browser gate open"
        )


def test_license_activation_records_selfhost(home, monkeypatch):
    """`clawmetry activate` / `license activate` / the wizard's key branch
    all funnel through license.activate — recorded once, there."""
    import clawmetry.license as lic

    monkeypatch.setattr(lic, "verify_token", lambda key: {"tier": "pro", "nodes": 3})
    monkeypatch.setattr(lic, "_secure_write", lambda path, data: None)
    monkeypatch.setattr(lic, "_download_and_install_pro", lambda payload: "")
    monkeypatch.setattr(lic, "_audit_license_event", lambda *a, **k: None)
    monkeypatch.setattr(lic, "LICENSE_PATH", str(home / ".clawmetry" / "license.key"))

    ok, _msg = lic.activate("CLAW1.x.y", actor="test")
    assert ok
    assert _recorded(home)["choice"] == "selfhost_license"


def test_license_activation_writes_beside_the_license_not_the_real_home(
    monkeypatch, tmp_path
):
    """The gate file must follow LICENSE_PATH, or every existing unit test
    that activates a fake key scribbles into the developer's / CI runner's
    real ~/.clawmetry (hit for real while writing this suite)."""
    import clawmetry.license as lic

    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    monkeypatch.setattr(lic, "verify_token", lambda key: {"tier": "pro", "nodes": 1})
    monkeypatch.setattr(lic, "_secure_write", lambda path, data: None)
    monkeypatch.setattr(lic, "_download_and_install_pro", lambda payload: "")
    monkeypatch.setattr(lic, "_audit_license_event", lambda *a, **k: None)
    monkeypatch.setattr(lic, "LICENSE_PATH", str(sandbox / "license.key"))

    ok, _msg = lic.activate("CLAW1.x.y", actor="test")
    assert ok
    assert json.loads((sandbox / "onboarding.json").read_text())["choice"] \
        == "selfhost_license"


def test_trial_key_activation_records_trial(home, monkeypatch):
    import clawmetry.license as lic

    monkeypatch.setattr(lic, "verify_token", lambda key: {"tier": "trial", "nodes": 1})
    monkeypatch.setattr(lic, "_secure_write", lambda path, data: None)
    monkeypatch.setattr(lic, "_download_and_install_pro", lambda payload: "")
    monkeypatch.setattr(lic, "_audit_license_event", lambda *a, **k: None)
    monkeypatch.setattr(lic, "LICENSE_PATH", str(home / ".clawmetry" / "license.key"))

    ok, _msg = lic.activate("CLAW1.x.y", actor="test")
    assert ok
    assert _recorded(home)["choice"] == "selfhost_trial"


def test_desktop_shell_uses_the_shared_writer(home, monkeypatch, tmp_path):
    """The .app's pane and the CLI must not drift into two schemas — and
    the shared writer must still honour the shell's own path constant, or
    adopting it would make the shell (and its tests) write to the real
    home directory."""
    desk = importlib.import_module("desktop.onboarding")
    dest = tmp_path / "shell-home" / ".clawmetry" / "onboarding.json"
    monkeypatch.setattr(desk, "_DASHBOARD_GATE_STATE_PATH", dest)

    desk._record_dashboard_gate_choice("cloud")
    rec = json.loads(dest.read_text())
    assert rec["choice"] == "managed"
    assert rec["source"] == "desktop_shell"
    assert _recorded(home) is None, "must not also write the default path"


# ── the reader ─────────────────────────────────────────────────────────

@pytest.fixture
def gate(monkeypatch, tmp_path):
    import routes.onboarding as mod
    importlib.reload(mod)
    monkeypatch.setattr(mod, "_STATE_PATH", str(tmp_path / "onboarding.json"))
    monkeypatch.setattr(mod, "_license_state", lambda: "")
    monkeypatch.setattr(mod, "_cloud_connected", lambda: False)
    monkeypatch.setattr(mod, "_paid_entitlement_state", lambda: "")
    shell_dir = tmp_path / "shell"
    shell_dir.mkdir()
    monkeypatch.setattr(mod, "_desktop_shell_runtime_dir", lambda: shell_dir)
    return mod


def test_free_local_choice_closes_the_gate(gate, tmp_path):
    """`selfhost_free` is recordable by the CLI even though no browser flow
    can POST it."""
    (tmp_path / "onboarding.json").write_text('{"choice": "selfhost_free"}')
    assert gate._resolve_state() == {
        "required": False, "state": "selfhost_free", "source": "gate"}


def test_free_local_choice_is_not_postable(gate):
    """...and the gate still refuses to let a POST claim it, since nothing
    would be backing the claim."""
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(gate.bp_onboarding)
    r = app.test_client().post("/api/onboarding/complete",
                               json={"choice": "selfhost_free"})
    assert r.status_code == 400


def test_paid_cloud_plan_closes_the_gate(monkeypatch):
    """THE regression: paid account, no license.key, local-only marker set."""
    import routes.onboarding as mod

    class _Ent:
        is_paid = True
        expired = False
        tier = "cloud_pro"

    import clawmetry.entitlements as _ent
    monkeypatch.setattr(_ent, "get_entitlement", lambda *a, **k: _Ent())
    import clawmetry.config as _cfg
    monkeypatch.setattr(_cfg, "is_cloud_disabled", lambda: True)

    assert mod._paid_entitlement_state() == "selfhost_license"


def test_free_entitlement_still_requires_a_choice(monkeypatch):
    """The "linked account, plan free, trial mint failed" limbo must still
    be asked — that is the case _cloud_connected() was hardened for."""
    import routes.onboarding as mod

    class _Ent:
        is_paid = False
        expired = False
        tier = "oss"

    import clawmetry.entitlements as _ent
    monkeypatch.setattr(_ent, "get_entitlement", lambda *a, **k: _Ent())
    assert mod._paid_entitlement_state() == ""


def test_expired_paid_entitlement_still_requires_a_choice(monkeypatch):
    import routes.onboarding as mod

    class _Ent:
        is_paid = True
        expired = True
        tier = "trial"

    import clawmetry.entitlements as _ent
    monkeypatch.setattr(_ent, "get_entitlement", lambda *a, **k: _Ent())
    assert mod._paid_entitlement_state() == ""


def test_entitlement_probe_never_raises(monkeypatch):
    import routes.onboarding as mod
    import clawmetry.entitlements as _ent

    def _boom(*a, **k):
        raise RuntimeError("plan cache on fire")

    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    assert mod._paid_entitlement_state() == ""
