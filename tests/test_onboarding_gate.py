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
    monkeypatch.setattr(mod, "_ping_onboarded", lambda choice: None)
    monkeypatch.setattr(mod, "_apply_marker_semantics", lambda choice: None)
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
