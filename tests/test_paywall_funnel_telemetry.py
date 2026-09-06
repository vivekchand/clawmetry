"""The two conversion surfaces we were blind on, and the escape from the gate.

Both changes here exist because of one prod pull on 2026-09-06:

  * 798 first launches in 30 days produced 38 completed onboarding choices
    (4.8%). Both cards on the gate demand an identity, including from users
    whose only runtimes are the three that are free forever.
  * ``hard_block_view`` / ``hard_block_checkout_click`` had ZERO rows in
    cloud analytics, ever. The overlay wrote them to an in-process store on
    the user's own machine and nothing forwarded them, so the one surface
    where a user looks straight at a price reported nothing at all.

The regressions these guard are all silent: a renamed JS beacon, a gate
button nobody wired, a choice the recorder refuses. None of them would turn
anything red without a test.
"""
from __future__ import annotations

import importlib
import json
import os
import re
import sys

import pytest
from flask import Flask

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── the gate's free-runtimes escape ──────────────────────────────────────────

@pytest.fixture
def ob(monkeypatch, tmp_path):
    import routes.onboarding as mod
    importlib.reload(mod)
    monkeypatch.setattr(mod, "_STATE_PATH", str(tmp_path / "onboarding.json"))
    monkeypatch.setattr(mod, "_ping_onboarded", lambda choice: None)
    monkeypatch.setattr(mod, "_apply_marker_semantics", lambda choice: None)
    # Never register or spawn a real background daemon from a unit test.
    monkeypatch.setattr(mod, "_ensure_daemon_for_choice", lambda choice: None)
    return mod


@pytest.fixture
def client(ob):
    app = Flask(__name__)
    app.register_blueprint(ob.bp_onboarding)
    return app.test_client()


def test_free_only_records_the_choice_and_flips_free_mode(ob, client, monkeypatch, tmp_path):
    from clawmetry import trial_enforcement as te
    marker = tmp_path / "free_only.marker"
    monkeypatch.setattr(te, "_FREE_ONLY_MARKER", str(marker))

    r = client.post("/api/onboarding/free-only")
    assert r.status_code == 200
    assert r.get_json() == {"ok": True, "state": "selfhost_free"}

    # Free-only mode is what actually keeps OpenClaw/NemoClaw/Goose working
    # while paid runtimes stay locked. Without the marker the choice would be
    # a recorded preference with nothing enforcing it.
    assert marker.is_file()
    assert te.free_only_mode_enabled() is True

    recorded = json.loads((tmp_path / "onboarding.json").read_text())
    assert recorded["choice"] == "selfhost_free"


def test_free_only_closes_the_gate(ob, client, monkeypatch, tmp_path):
    """The whole point: after choosing free, the gate must stop asking."""
    from clawmetry import trial_enforcement as te
    monkeypatch.setattr(te, "_FREE_ONLY_MARKER", str(tmp_path / "free_only.marker"))
    monkeypatch.setattr(ob, "_license_state", lambda: "")
    monkeypatch.setattr(ob, "_cloud_connected", lambda: False)
    monkeypatch.setattr(ob, "_paid_entitlement_state", lambda: "")
    monkeypatch.setattr(ob, "_ping_gate_shown", lambda: None)
    _shell = tmp_path / "shell"
    _shell.mkdir()
    monkeypatch.setattr(ob, "_desktop_shell_runtime_dir", lambda: _shell)
    for k in ("CLAWMETRY_CLOUD", "CLAWMETRY_SKIP_ONBOARDING", "CI",
              "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI", "TRAVIS", "BUILDKITE",
              "JENKINS_URL", "TEAMCITY_VERSION", "BITBUCKET_BUILD_NUMBER",
              "CODEBUILD_BUILD_ID", "DRONE", "AGENT_NAME"):
        monkeypatch.delenv(k, raising=False)

    assert client.get("/api/onboarding/state").get_json()["required"] is True
    client.post("/api/onboarding/free-only")
    assert client.get("/api/onboarding/state").get_json()["required"] is False


def test_selfhost_free_is_recordable_but_still_not_postable_to_complete(ob, client):
    """The dedicated endpoint is the flow; /complete must stay closed.

    ``selfhost_free`` is deliberately absent from the generic POST body
    allowlist so a caller cannot claim it with no local configuration behind
    it. Adding the escape must not have widened that hole.
    """
    from clawmetry import onboarding_state as obs
    assert "selfhost_free" in obs.RECORDED_CHOICES
    assert "selfhost_free" not in obs.CHOICES
    r = client.post("/api/onboarding/complete", json={"choice": "selfhost_free"})
    assert r.status_code == 400


def test_gate_offers_the_free_escape_and_wires_it():
    """Markup + handler + endpoint must agree; any one alone is a dead link."""
    html = open(os.path.join(_ROOT, "clawmetry/templates/partials/onboarding-modal.html"),
                encoding="utf-8").read()
    js = open(os.path.join(_ROOT, "clawmetry/static/js/onboarding.js"),
              encoding="utf-8").read()
    assert 'id="obg-free-btn"' in html
    # The three free runtimes are the offer; naming them is the whole reason
    # a user takes this path instead of bouncing.
    for name in ("OpenClaw", "NemoClaw", "Goose"):
        assert name in html, name
    assert "obg-free-btn" in js
    assert "/api/onboarding/free-only" in js


# ── paywall beacons reaching the cloud funnel ────────────────────────────────

def test_paywall_beacons_are_forwarded_as_lifecycle_events(monkeypatch):
    import routes.entitlement as ent
    sent = []
    import clawmetry.telemetry as telemetry
    monkeypatch.setattr(telemetry, "ping_once",
                        lambda event, version="unknown", extra=None: sent.append(event))

    ent._ping_paywall_lifecycle({"event": "hard_block_view"})
    ent._ping_paywall_lifecycle({"event": "hard_block_checkout_click"})
    assert sent == ["paywall_view", "paywall_checkout_click"]


def test_unrelated_paywall_events_are_not_forwarded(monkeypatch):
    """Only the two funnel beacons leave the machine; nothing else does."""
    import routes.entitlement as ent
    sent = []
    import clawmetry.telemetry as telemetry
    monkeypatch.setattr(telemetry, "ping_once",
                        lambda event, version="unknown", extra=None: sent.append(event))

    for body in ({"event": "some_other_beacon"}, {}, {"event": ""}, {"harness": "cursor"}):
        ent._ping_paywall_lifecycle(body)
    assert sent == []


def test_beacon_names_match_what_the_overlay_actually_posts():
    """The silent-failure guard.

    The forwarder keys off the literal ``event`` strings app.js posts. Rename
    one there and the telemetry stops with no error anywhere, which is
    precisely how these two beacons came to have zero rows in the first
    place.
    """
    import routes.entitlement as ent
    js = open(os.path.join(_ROOT, "clawmetry/static/js/app.js"), encoding="utf-8").read()
    posted = set(re.findall(r"event:\s*'(hard_block_[a-z_]+)'", js))
    assert posted, "app.js no longer posts any hard_block_* paywall beacon"
    assert posted <= set(ent._PAYWALL_LIFECYCLE_EVENTS), (
        "app.js posts paywall beacons the forwarder does not map: "
        f"{sorted(posted - set(ent._PAYWALL_LIFECYCLE_EVENTS))}"
    )


def test_forwarding_never_breaks_the_beacon(monkeypatch):
    """A telemetry failure must not change the 204 the beacon returns."""
    import routes.entitlement as ent
    import clawmetry.telemetry as telemetry

    def _boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(telemetry, "ping_once", _boom)
    ent._ping_paywall_lifecycle({"event": "hard_block_view"})  # must not raise
