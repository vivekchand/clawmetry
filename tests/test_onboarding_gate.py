"""First-run onboarding gate (routes/onboarding.py + the overlay partial).

Route logic runs against a minimal Flask app with the license/cloud/
telemetry helpers monkeypatched; the wiring checks assert the partial and
script land in the LIVE (second) DASHBOARD_HTML, per the dead-UI rule.
"""
from __future__ import annotations

import importlib
import json
import os
import sys

import pytest
from flask import Flask

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def ob(monkeypatch, tmp_path):
    import routes.onboarding as mod
    importlib.reload(mod)
    monkeypatch.setattr(mod, "_STATE_PATH", str(tmp_path / "onboarding.json"))
    monkeypatch.setattr(mod, "_license_state", lambda: "")
    monkeypatch.setattr(mod, "_cloud_connected", lambda: False)
    # Isolate the desktop shell stamp path too: on a dev box with the
    # real .app installed, ``_desktop_shell_stamp`` would read the real
    # user's onboarding-completed.json and the fresh-install tests here
    # would falsely see the machine as already-onboarded.
    _shell_dir = tmp_path / "desktop-shell-runtime"
    _shell_dir.mkdir()
    monkeypatch.setattr(mod, "_desktop_shell_runtime_dir", lambda: _shell_dir)
    monkeypatch.setattr(mod, "_ping_onboarded", lambda choice: None)
    monkeypatch.setattr(mod, "_apply_marker_semantics", lambda choice: None)
    # Must never actually register/spawn a real daemon during a unit test —
    # see test_ensure_daemon_for_choice_* below for the real coverage.
    monkeypatch.setattr(mod, "_ensure_daemon_for_choice", lambda choice: None)
    # Strip every env that legitimately suppresses the gate — including
    # the CI vars GitHub Actions itself sets, or the "fresh install
    # requires onboarding" tests would pass locally and fail in CI.
    for k in ("CLAWMETRY_CLOUD", "CLAWMETRY_SKIP_ONBOARDING", "CI",
              "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI", "TRAVIS",
              "BUILDKITE", "JENKINS_URL", "TEAMCITY_VERSION",
              "BITBUCKET_BUILD_NUMBER", "CODEBUILD_BUILD_ID", "DRONE",
              "AGENT_NAME"):
        monkeypatch.delenv(k, raising=False)
    return mod


@pytest.fixture
def client(ob):
    app = Flask(__name__)
    app.register_blueprint(ob.bp_onboarding)
    return app.test_client()


def test_fresh_install_requires_onboarding(client):
    d = client.get("/api/onboarding/state").get_json()
    assert d["required"] is True and d["state"] == "none"


def test_license_derives_completion(ob, client, monkeypatch):
    monkeypatch.setattr(ob, "_license_state", lambda: "selfhost_trial")
    d = client.get("/api/onboarding/state").get_json()
    assert d == {"required": False, "state": "selfhost_trial", "source": "license"}


def test_cloud_token_derives_managed(ob, client, monkeypatch):
    monkeypatch.setattr(ob, "_cloud_connected", lambda: True)
    d = client.get("/api/onboarding/state").get_json()
    assert d == {"required": False, "state": "managed", "source": "cloud"}


def test_cloud_mode_never_gates(client, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_CLOUD", "1")
    d = client.get("/api/onboarding/state").get_json()
    assert d["required"] is False and d["source"] == "cloud_mode"


def test_env_skip_never_gates(client, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_SKIP_ONBOARDING", "1")
    d = client.get("/api/onboarding/state").get_json()
    assert d["required"] is False and d["source"] == "env_skip"


def test_ci_never_gates(client, monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    d = client.get("/api/onboarding/state").get_json()
    assert d["required"] is False and d["source"] == "ci"


def test_complete_managed_requires_cloud_connection(client):
    r = client.post("/api/onboarding/complete", json={"choice": "managed"})
    assert r.status_code == 409


def test_complete_selfhost_requires_license(client):
    r = client.post("/api/onboarding/complete", json={"choice": "selfhost_trial"})
    assert r.status_code == 409


def test_complete_unknown_choice_rejected(client):
    r = client.post("/api/onboarding/complete", json={"choice": "yolo"})
    assert r.status_code == 400


def test_complete_records_choice_and_markers(ob, client, monkeypatch):
    monkeypatch.setattr(ob, "_cloud_connected", lambda: True)
    markers = []
    pings = []
    monkeypatch.setattr(ob, "_apply_marker_semantics", markers.append)
    monkeypatch.setattr(ob, "_ping_onboarded", pings.append)
    r = client.post("/api/onboarding/complete", json={"choice": "managed"})
    assert r.get_json() == {"ok": True, "state": "managed"}
    assert markers == ["managed"] and pings == ["managed"]
    with open(ob._STATE_PATH, encoding="utf-8") as fh:
        assert json.load(fh)["choice"] == "managed"
    # The gate must not re-appear after the choice is recorded.
    d = client.get("/api/onboarding/state").get_json()
    assert d == {"required": False, "state": "managed", "source": "gate"}


def test_activate_license_rejects_non_claw_keys(client):
    r = client.post("/api/onboarding/activate-license", json={"key": "hunter2"})
    assert r.status_code == 400


def test_activate_license_happy_path(ob, client, monkeypatch):
    import types
    fake_lic = types.SimpleNamespace(
        activate=lambda key, actor="": (True, "activated"))
    monkeypatch.setitem(sys.modules, "clawmetry.license", fake_lic)
    # `from clawmetry import license` prefers the package attribute once the
    # real module has been imported anywhere in the session, so shim both.
    import clawmetry
    monkeypatch.setattr(clawmetry, "license", fake_lic, raising=False)
    monkeypatch.setattr(ob, "_license_state", lambda: "selfhost_license")
    pings = []
    monkeypatch.setattr(ob, "_ping_onboarded", pings.append)
    r = client.post("/api/onboarding/activate-license",
                    json={"key": "CLAW1.aaa.bbb"})
    d = r.get_json()
    assert d["ok"] is True and d["state"] == "selfhost_license"
    assert pings == ["selfhost_license"]


def test_state_endpoint_fails_open(ob, client, monkeypatch):
    def boom():
        raise RuntimeError("disk on fire")
    monkeypatch.setattr(ob, "_resolve_state", boom)
    d = client.get("/api/onboarding/state").get_json()
    assert d["required"] is False, "gate plumbing failure must never brick the dashboard"


# ── Wiring: the gate exists in the SERVED artifact, not just in routes ──────

def _dash_src():
    return open(os.path.join(_ROOT, "dashboard.py"), encoding="utf-8").read()


def test_gate_partial_and_js_are_in_live_dashboard_html():
    src = _dash_src()
    live = src.rfind("DASHBOARD_HTML = ")
    assert src.find("partials/onboarding-modal.html", live) > live, \
        "gate partial missing from the LIVE (second) DASHBOARD_HTML"
    assert src.find("js/onboarding.js", live) > live, \
        "onboarding.js script tag missing from the LIVE DASHBOARD_HTML"
    assert "app.register_blueprint(bp_onboarding)" in src


def test_gate_partial_renders():
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(
        os.path.join(_ROOT, "clawmetry", "templates")))
    html = env.get_template("partials/onboarding-modal.html").render()
    assert 'id="onboarding-gate-overlay"' in html
    assert "Managed cloud" in html and "Self-host" in html
    # Hard gate: the overlay ships no close/skip affordance (no close
    # button glyph, no dismiss id, no overlay-click handler).
    assert "&times;" not in html and "×" not in html
    assert "obg-close" not in html and "skip" not in html.lower()
    assert "onclick" not in html.split("<style>")[0] + html.split("</style>")[1]


def test_gate_js_is_hard_gate_and_cloud_safe():
    js = open(os.path.join(
        _ROOT, "clawmetry", "static", "js", "onboarding.js"),
        encoding="utf-8").read()
    assert "window.CLOUD_MODE" in js, "hosted dashboard must never gate"
    assert "/api/onboarding/state" in js
    assert "/api/trial/activate" in js
    assert "/api/onboarding/activate-license" in js
    assert "openCloudModal" in js


def test_selfhost_modal_offers_oauth_email_and_license():
    """The self-host side mirrors the cloud side: one button on the gate
    card opens a modal offering GitHub/Google OAuth (mode=selfhost bridge),
    email OTP, and a license key. The gate card itself must stay a single
    button — the options live in the modal, not the card."""
    js = open(os.path.join(
        _ROOT, "clawmetry", "static", "js", "onboarding.js"),
        encoding="utf-8").read()
    assert "mode: 'selfhost'" in js, "self-host OAuth must use the selfhost bridge mode"
    assert "/api/cloud-cta/oauth-start" in js
    assert "openSelfhostModal" in js and "closeSelfhostModal" in js
    for fn in ("shmOauth", "shmSendOtp", "shmVerifyOtp", "shmActivateLicense"):
        assert fn in js, "modal driver %s missing from onboarding.js" % fn

    card = open(os.path.join(
        _ROOT, "clawmetry", "templates", "partials", "onboarding-modal.html"),
        encoding="utf-8").read()
    assert 'id="obg-selfhost-btn"' in card, "gate card needs its single button"
    assert "obg-oauth-github" not in card, \
        "OAuth buttons moved to the self-host modal; the card is one button"

    modal = open(os.path.join(
        _ROOT, "clawmetry", "templates", "partials", "selfhost-modal.html"),
        encoding="utf-8").read()
    assert 'id="selfhost-modal-overlay"' in modal
    for probe in ("shmOauth('github')", "shmOauth('google')", "shmSendOtp()",
                  "shmActivateLicense()", 'id="shm-step-wait"',
                  'id="shm-step-ended"'):
        assert probe in modal, "self-host modal missing %s" % probe


def test_selfhost_modal_is_in_live_dashboard_html():
    """The modal partial must be included OUTSIDE #zoom-wrapper in the LIVE
    (second) DASHBOARD_HTML, next to cloud-modal (the #4386 overlay rule)."""
    src = _dash_src()
    live = src.rfind("DASHBOARD_HTML = ")
    idx = src.find("partials/selfhost-modal.html", live)
    assert idx > live, "selfhost-modal partial missing from the LIVE DASHBOARD_HTML"
    wrapper_end = src.find("end zoom-wrapper", live)
    assert wrapper_end != -1 and idx > wrapper_end, \
        "selfhost-modal must be included after #zoom-wrapper closes (fixed overlay rule)"


# ── _cloud_connected() must not confuse identity-linking with "chose managed" ──
#
# Live-hit 2026-08-06: the self-host Google/GitHub sign-in flow
# (_selfhost_signin_with_key in dashboard.py) writes the SAME cloud token as
# the managed-connect flow purely to carry identity into the trial-signup
# call, and touches the nocloud marker FIRST. When the trial-signup half of
# that flow then failed silently, the account was linked (token on disk) but
# no license/trial was ever activated -- yet _cloud_connected() only checked
# whether a token existed, so _resolve_state() reported the install as
# already onboarded ("managed") on every later page load, with no license
# and everything locked, and no way to see an error or retry the trial.

def test_cloud_connected_ignores_token_under_nocloud_marker(monkeypatch, tmp_path):
    import routes.onboarding as mod
    from clawmetry import config as _cfg

    marker = tmp_path / "nocloud"
    marker.write_text("")
    monkeypatch.setattr(_cfg, "NOCLOUD_MARKER_PATH", str(marker))
    monkeypatch.delenv("CLAWMETRY_NO_CLOUD", raising=False)

    import dashboard as _d
    monkeypatch.setattr(_d, "_read_cloud_token", lambda: "cm_faketoken")

    assert mod._cloud_connected() is False, (
        "a cloud token written under self-host intent (nocloud marker set) "
        "must not be read as 'chose managed' -- it strands a failed trial "
        "attempt on a permanently-skipped onboarding gate"
    )


def test_cloud_connected_true_without_nocloud_marker(monkeypatch, tmp_path):
    import routes.onboarding as mod
    from clawmetry import config as _cfg

    marker = tmp_path / "nocloud-not-written"
    monkeypatch.setattr(_cfg, "NOCLOUD_MARKER_PATH", str(marker))
    monkeypatch.delenv("CLAWMETRY_NO_CLOUD", raising=False)

    import dashboard as _d
    monkeypatch.setattr(_d, "_read_cloud_token", lambda: "cm_faketoken")

    assert mod._cloud_connected() is True, (
        "a real managed-connect token (no self-host marker) must still "
        "satisfy the gate -- this is the grandfather path for pre-gate "
        "managed installs"
    )


def test_marker_semantics_selfhost_writes_nocloud(monkeypatch, tmp_path):
    """NOCLOUD_MARKER_PATH is a plain str; the old .parent/.touch calls
    raised AttributeError into the broad except, so the marker was silently
    never written for self-host choices (identity risked becoming an
    unasked-for upload once a cm_ key landed on disk)."""
    import routes.onboarding as mod
    from clawmetry import config as _cfg

    marker = tmp_path / "clawmetry-home" / "nocloud"
    monkeypatch.setattr(_cfg, "NOCLOUD_MARKER_PATH", str(marker))
    mod._apply_marker_semantics("selfhost_trial")
    assert marker.exists(), "self-host choice must write the nocloud marker"


def test_marker_semantics_managed_clears_nocloud(monkeypatch, tmp_path):
    import routes.onboarding as mod
    from clawmetry import config as _cfg

    marker = tmp_path / "nocloud"
    marker.write_text("")
    monkeypatch.setattr(_cfg, "NOCLOUD_MARKER_PATH", str(marker))
    monkeypatch.delenv("CLAWMETRY_NO_CLOUD", raising=False)
    mod._apply_marker_semantics("managed")
    assert not marker.exists()


# ── Persistent daemon registration on onboarding completion ────────────────
#
# Root cause: this gate is the DEFAULT onboarding path (browser, since the
# 2026-07-31 hard-gate rollout) and used to complete a choice without ever
# starting/registering a background sync daemon -- only the CLI paths
# (`clawmetry connect` / `clawmetry onboard`) did that. Only the in-process
# dashboard thread was left polling PyPI, which stops the moment that one
# process exits. These tests pin that both completion endpoints now always
# attempt daemon registration, and that _ensure_daemon_for_choice never lets
# a registration failure break onboarding completion itself.

def test_complete_managed_registers_persistent_daemon(ob, client, monkeypatch):
    monkeypatch.setattr(ob, "_cloud_connected", lambda: True)
    calls = []
    monkeypatch.setattr(ob, "_ensure_daemon_for_choice", calls.append)
    r = client.post("/api/onboarding/complete", json={"choice": "managed"})
    assert r.get_json()["ok"] is True
    assert calls == ["managed"]


def test_complete_selfhost_registers_persistent_daemon(ob, client, monkeypatch):
    monkeypatch.setattr(ob, "_license_state", lambda: "selfhost_trial")
    calls = []
    monkeypatch.setattr(ob, "_ensure_daemon_for_choice", calls.append)
    r = client.post("/api/onboarding/complete", json={"choice": "selfhost_trial"})
    assert r.get_json()["ok"] is True
    assert calls == ["selfhost_trial"]


def test_activate_license_registers_persistent_daemon(ob, client, monkeypatch):
    import types
    fake_lic = types.SimpleNamespace(
        activate=lambda key, actor="": (True, "activated"))
    monkeypatch.setitem(sys.modules, "clawmetry.license", fake_lic)
    import clawmetry
    monkeypatch.setattr(clawmetry, "license", fake_lic, raising=False)
    monkeypatch.setattr(ob, "_license_state", lambda: "selfhost_license")
    calls = []
    monkeypatch.setattr(ob, "_ensure_daemon_for_choice", calls.append)
    r = client.post("/api/onboarding/activate-license",
                    json={"key": "CLAW1.aaa.bbb"})
    assert r.get_json()["ok"] is True
    assert calls == ["selfhost_license"]


class _SyncThread:
    """Runs the target immediately on .start() instead of on a real thread,
    so tests can assert on _run()'s side effects deterministically -- the
    production code dispatches via threading.Thread on purpose (see
    _ensure_daemon_for_choice's docstring: onboarding-complete must never
    block the HTTP response on a slow/hanging systemctl/launchctl/schtasks
    call), but that async dispatch is exactly what these tests don't want."""

    def __init__(self, target, daemon=True):
        self._target = target

    def start(self):
        self._target()


def test_ensure_daemon_for_choice_calls_shared_registration(monkeypatch):
    """selfhost_* choices must register a LOCAL-ONLY daemon (no cloud
    egress), managed must not."""
    import routes.onboarding as mod
    import clawmetry.daemon_registration as dreg

    monkeypatch.setattr(mod.threading, "Thread", _SyncThread)
    calls = []
    monkeypatch.setattr(dreg, "ensure_persistent_daemon", lambda cfg: calls.append(cfg))
    mod._ensure_daemon_for_choice("selfhost_trial")
    assert calls == [{"local_only": True}]

    calls.clear()
    mod._ensure_daemon_for_choice("managed")
    assert calls == [{"local_only": False}]


def test_ensure_daemon_for_choice_never_raises(monkeypatch):
    """A registration failure (no systemd, schtasks unavailable, sandboxed
    environment, ...) must never break onboarding completion."""
    import routes.onboarding as mod
    import clawmetry.daemon_registration as dreg

    monkeypatch.setattr(mod.threading, "Thread", _SyncThread)

    def boom(cfg):
        raise RuntimeError("no supervisor available here")
    monkeypatch.setattr(dreg, "ensure_persistent_daemon", boom)
    mod._ensure_daemon_for_choice("selfhost_license")  # must not raise


def test_ensure_daemon_for_choice_dispatches_off_request_thread(monkeypatch):
    """The real regression this closes (2026-08-06 CI): registration used to
    run synchronously inside the onboarding-complete handler, so a hanging
    systemctl/launchctl call blocked the HTTP response the browser's init
    sequence was waiting on (visible as the dashboard stuck forever on
    "Initializing ClawMetry"). Must be dispatched via threading.Thread, not
    called inline."""
    import routes.onboarding as mod

    calls = []
    monkeypatch.setattr(
        mod.threading, "Thread",
        lambda target, daemon=True: calls.append((target, daemon)) or _SyncThread(target),
    )
    mod._ensure_daemon_for_choice("selfhost_trial")
    assert len(calls) == 1
    assert calls[0][1] is True, "must be a daemon thread so it never blocks process exit"
