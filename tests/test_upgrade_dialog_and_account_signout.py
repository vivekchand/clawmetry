"""Expired-trial upgrade dialog + account sign-out.

Two founder reports, 2026-08-18, both about the same dead end: an install
whose 7-day trial has ended shows the self-host modal with a single "See
pricing" link to the public site, and no way to reach an account whose Pro
licence lives on a different email.

  1. The modal now sells in place — interval x tier picker, the annual
     device perk, and a POST to /api/trial/checkout that mints a Stripe
     session scoped to the account already on disk.
  2. POST /api/account/signout forgets that account (licence, cm_ key, both
     onboarding stamps) so the gate can be answered with a different one.

Route logic runs against a minimal Flask app with every filesystem path
redirected into tmp_path; the UI checks read the shipped static/template
files (no build step, so the files ARE the app).
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest
from flask import Flask

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*parts: str) -> str:
    with open(os.path.join(_ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


# ── POST /api/account/signout ──────────────────────────────────────────────

class _SyncThread:
    """Run the "background" work inline so the test can assert on it."""

    def __init__(self, target=None, daemon=True):
        self._target = target
        self.daemon = daemon

    def start(self):
        if self._target:
            self._target()


@pytest.fixture
def signout(monkeypatch, tmp_path):
    """A signed-in machine: licence + cm_ key + both onboarding stamps."""
    import routes.onboarding as mod
    importlib.reload(mod)

    home = tmp_path / "clawmetry-home"
    home.mkdir()
    state_path = home / "onboarding.json"
    state_path.write_text('{"choice": "selfhost_trial"}')
    config_file = home / "config.json"
    config_file.write_text('{"api_key": "cm_old_account"}')
    sync_state = home / "state.json"
    sync_state.write_text("{}")
    shell_dir = tmp_path / "desktop-shell-runtime"
    shell_dir.mkdir()
    (shell_dir / "onboarding-completed.json").write_text(
        '{"completed": true, "signed_in": true, "mode": "selfhost"}')
    marker = home / "nocloud"

    monkeypatch.setattr(mod, "_STATE_PATH", str(state_path))
    monkeypatch.setattr(mod, "_desktop_shell_runtime_dir", lambda: shell_dir)
    # The handler resolves the stale sync-progress file off Path.home(), so
    # the fake HOME has to carry a real ~/.clawmetry to find it in.
    monkeypatch.setattr(mod.Path, "home", staticmethod(lambda: tmp_path))
    (tmp_path / ".clawmetry").mkdir()
    progress = tmp_path / ".clawmetry" / "sync_progress.json"
    progress.write_text("{}")
    monkeypatch.setattr(mod, "_license_state", lambda: "")
    monkeypatch.setattr(mod, "_cloud_connected", lambda: False)
    monkeypatch.setattr(mod.threading, "Thread", _SyncThread)
    monkeypatch.delenv("CLAWMETRY_CLOUD", raising=False)

    import clawmetry.sync as _sync
    monkeypatch.setattr(_sync, "CONFIG_FILE", config_file, raising=False)
    monkeypatch.setattr(_sync, "STATE_FILE", sync_state, raising=False)

    import clawmetry.config as _cfg
    monkeypatch.setattr(_cfg, "NOCLOUD_MARKER_PATH", str(marker))

    import clawmetry.license as _lic
    licence = home / "license.key"
    licence.write_text("header.payload.signature")
    removed = {"called": False}

    def _fake_deactivate(actor=""):
        removed["called"] = True
        licence.unlink()
        return True, True
    monkeypatch.setattr(_lic, "deactivate", _fake_deactivate)

    restarts = []
    import dashboard as _d
    monkeypatch.setattr(_d, "_restart_sync_daemon", lambda: restarts.append(1))

    app = Flask(__name__)
    app.register_blueprint(mod.bp_onboarding)
    return {
        "mod": mod,
        "client": app.test_client(),
        "licence": licence,
        "config": config_file,
        "sync_state": sync_state,
        "progress": progress,
        "choice": state_path,
        "shell_stamp": shell_dir / "onboarding-completed.json",
        "marker": marker,
        "restarts": restarts,
        "deactivated": removed,
    }


def test_signout_clears_every_piece_of_identity(signout):
    """Miss ANY one of the four and the user is still stuck: a surviving
    licence keeps the old entitlement, a surviving cm_ key lets the daemon
    re-install it from the next heartbeat, and either onboarding stamp keeps
    the gate closed so there is nowhere to sign in again."""
    d = signout["client"].post("/api/account/signout").get_json()
    assert d["ok"] is True
    assert d["cleared"] == {"license": True, "cloud": True, "choice": True}
    assert signout["deactivated"]["called"] is True
    assert not signout["licence"].exists()
    assert not signout["config"].exists()
    assert not signout["sync_state"].exists()
    assert not signout["progress"].exists()
    assert not signout["choice"].exists()
    assert not signout["shell_stamp"].exists()


def test_signout_reopens_the_gate(signout):
    d = signout["client"].post("/api/account/signout").get_json()
    assert d["state"]["required"] is True


def test_signout_restarts_the_daemon(signout):
    """run_daemon() reads config.json ONCE at startup and holds the api_key in
    memory for the life of the process, so deleting the file is not enough --
    a still-running daemon keeps heart-beating as the signed-out account and
    _maybe_install_license_from_heartbeat writes its licence straight back."""
    signout["client"].post("/api/account/signout")
    assert signout["restarts"] == [1]


def test_signout_stops_egress(signout):
    """Nobody is signed in, so nothing may leave the machine until somebody
    chooses again. Sign-in re-clears (managed) or re-writes (self-host) the
    marker, so this never blocks the next account."""
    signout["client"].post("/api/account/signout")
    assert signout["marker"].exists()


def test_signout_is_idempotent(signout):
    signout["client"].post("/api/account/signout")
    d = signout["client"].post("/api/account/signout").get_json()
    assert d["ok"] is True
    assert d["cleared"]["cloud"] is False and d["cleared"]["choice"] is False


def test_signout_refuses_on_hosted_cloud(signout, monkeypatch):
    """Hosted accounts have no on-disk identity to clear; deleting files there
    would be someone else's container, not the caller's machine."""
    monkeypatch.setenv("CLAWMETRY_CLOUD", "1")
    r = signout["client"].post("/api/account/signout")
    assert r.status_code == 400
    assert r.get_json()["ok"] is False
    assert signout["config"].exists(), "must not touch disk in cloud mode"


def test_signout_survives_a_broken_license_layer(signout, monkeypatch):
    """A licence file we cannot parse or delete must not strand the user on
    the account -- the rest of the sign-out still has to land."""
    import clawmetry.license as _lic

    def boom(actor=""):
        raise RuntimeError("corrupt key")
    monkeypatch.setattr(_lic, "deactivate", boom)
    d = signout["client"].post("/api/account/signout").get_json()
    assert d["ok"] is True and d["cleared"]["license"] is False
    assert not signout["config"].exists() and not signout["choice"].exists()


# ── Trial-enforcement allowlist ────────────────────────────────────────────

def test_signout_and_gate_reachable_while_hard_blocked():
    """The hard block exists to force a payment decision. Both ways OUT of it
    -- pay, or sign in as the account that already paid -- have to answer
    while it is up, or the block is a trap rather than a paywall."""
    from clawmetry import trial_enforcement as _te

    for path in ("/api/account/signout", "/api/onboarding/state",
                 "/api/onboarding/activate-license", "/api/cloud-cta/send-otp",
                 "/api/cloud-cta/oauth-status", "/api/trial/checkout"):
        assert _te.allowlisted_path(path), "%s must survive the hard block" % path
    assert not _te.allowlisted_path("/api/usage"), "allowlist must stay tiny"


# ── The upgrade dialog (static files ARE the app: no build step) ───────────

def test_expired_trial_step_sells_in_place():
    modal = _read("clawmetry", "templates", "partials", "selfhost-modal.html")
    assert "clawmetry.com/pricing" not in modal, \
        "expired trial must not bounce the user to the public pricing page"
    for probe in ("shmSetInterval('month')", "shmSetInterval('year')",
                  "shmSetTier('starter')", "shmSetTier('pro')",
                  "shmCheckout()", 'id="shm-price-starter"',
                  'id="shm-price-pro"', 'id="shm-device"'):
        assert probe in modal, "upgrade dialog missing %s" % probe


def test_annual_device_perk_is_offered():
    """Annual bundles the $149 desk device (the cloud collects a shipping
    address on annual checkouts and ships on the first PAID invoice)."""
    modal = _read("clawmetry", "templates", "partials", "selfhost-modal.html")
    assert "$149" in modal
    js = _read("clawmetry", "static", "js", "onboarding.js")
    assert "_shmInterval === 'year'" in js, "device perk must be annual-only"


def test_checkout_posts_tier_and_interval():
    js = _read("clawmetry", "static", "js", "onboarding.js")
    assert "'/api/trial/checkout'" in js
    assert "tier: _shmTier" in js
    assert "plan: _shmInterval === 'year' ? 'yearly' : 'monthly'" in js


def test_prices_come_from_one_table():
    """Two hardcoded price ladders is how a reprice ships half-done: the
    hard-block overlay publishes window.CM_PLANS and this modal reads it."""
    app_js = _read("clawmetry", "static", "js", "app.js")
    assert "window.CM_PLANS" in app_js
    ob_js = _read("clawmetry", "static", "js", "onboarding.js")
    assert "window.CM_PLANS" in ob_js


def test_expired_step_polls_so_a_paying_account_is_let_in():
    """Signing in as an account that already pays lands on this step too --
    the self-host rail reports "trial expired" because the trial is spent,
    while the real licence arrives on the daemon's next heartbeat. Without a
    poll the customer is sold a plan they already own."""
    js = _read("clawmetry", "static", "js", "onboarding.js")
    body = js[js.index("function _shmStep("):js.index("function _shmStopPoll(")]
    assert "_shmPollForLicense()" in body, \
        "the expired-trial step must poll for a licence, not only after checkout"
    assert "'/api/onboarding/state'" in js


def test_trial_promise_is_hidden_once_the_trial_is_gone():
    """The modal's tagline promises a free 7-day trial. Two lines above "Your
    7-day trial has ended" that is a contradiction, not an offer."""
    modal = _read("clawmetry", "templates", "partials", "selfhost-modal.html")
    assert 'id="shm-tagline"' in modal
    js = _read("clawmetry", "static", "js", "onboarding.js")
    assert "$('shm-tagline')" in js


def test_switch_account_is_offered_in_both_places():
    """At the gate (where a blocked user is) and in the profile menu (where a
    signed-in user is)."""
    modal = _read("clawmetry", "templates", "partials", "selfhost-modal.html")
    assert "shmSignOut()" in modal
    ob_js = _read("clawmetry", "static", "js", "onboarding.js")
    assert "'/api/account/signout'" in ob_js
    gw = _read("clawmetry", "static", "js", "gw-setup.js")
    assert "cmAccountSignOut" in gw and "'/api/account/signout'" in gw
