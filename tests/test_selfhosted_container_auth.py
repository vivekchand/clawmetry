"""Self-hosted admin APIs work from outside a container, and data survives a restart.

Reproduced on 2026-09-14 against main: a self-hosted server called from any
non-loopback address answered HTTP 401 "Gateway token not configured" on
/api/selfhosted/status and /api/export/events, even with valid admin
credentials, while /ingest/events and /selfhosted answered 200. Every request
that reaches a container through a published port is non-loopback, so the
deployment guide's own verification step failed in the deployment it
documents. The dashboard's gateway-token gate ran before the self-hosted views
could check their own credentials.

These tests drive the REAL gate (``dashboard._check_auth``) and the REAL
self-hosted blueprint with a bridge-network client address, and run the HTTP
half of scripts/verify_selfhosted_image.py against a live server that is
stopped and started again on the same store.

AC-OBS-SHI-004.1 -- self-hosted routes accept their own credentials from a
  non-loopback caller:
  ``test_admin_status_answers_admin_credentials_from_a_container_bridge``,
  ``test_export_returns_an_event_ingested_from_outside``.
AC-OBS-SHI-004.2 -- nothing else is opened, and uncredentialed calls are
  still refused:
  ``test_every_exempted_view_refuses_a_remote_caller_without_credentials``,
  ``test_every_selfhosted_api_view_is_a_deliberate_decision``,
  ``test_other_api_routes_keep_the_gateway_rule``,
  ``test_exemption_is_off_outside_self_hosted_mode``.
AC-OBS-SHI-002.2 -- an event sent from outside survives a restart and the
  export still refuses no credentials:
  ``test_verifier_persistence_check_passes_across_a_restart``,
  ``test_verifier_persistence_check_fails_when_the_store_was_lost``.
"""
from __future__ import annotations

import base64
import importlib
import importlib.util
import os
import re
import threading

import pytest

flask = pytest.importorskip("flask")
from werkzeug.serving import make_server  # noqa: E402

dashboard = importlib.import_module("dashboard")
from clawmetry import selfhosted  # noqa: E402
from routes import selfhosted_ingest as shi  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = "cm_container_auth_token"
ADMIN = ("admin", "container-pw")
BRIDGE = {"REMOTE_ADDR": "172.17.0.1"}


def _load_verifier():
    path = os.path.join(REPO_ROOT, "scripts", "verify_selfhosted_image.py")
    spec = importlib.util.spec_from_file_location("verify_selfhosted_image", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _basic(user: str, password: str) -> dict:
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()}


@pytest.fixture
def sh_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SELF_HOSTED", "true")
    monkeypatch.setenv("CLAWMETRY_API_TOKENS", TOKEN)
    monkeypatch.setenv("CLAWMETRY_ADMIN_USER", ADMIN[0])
    monkeypatch.setenv("CLAWMETRY_ADMIN_PASSWORD", ADMIN[1])
    monkeypatch.delenv("CLAWMETRY_SELF_HOSTED_E2E", raising=False)
    monkeypatch.setenv("CLAWMETRY_SELF_HOSTED_DB", str(tmp_path / "selfhosted.db"))
    # The container case: no local gateway token was ever configured.
    monkeypatch.setattr(dashboard, "GATEWAY_TOKEN", None)
    shi._reset_for_tests()
    yield tmp_path
    shi._reset_for_tests()


def _app():
    """A server wired the way dashboard.py wires self-hosted mode: gate first."""
    app = flask.Flask("selfhosted-container-auth")
    app.before_request(dashboard._check_auth)
    app.register_blueprint(shi.bp_selfhosted)

    @app.route("/api/some-dashboard-route")
    def _dashboard_route():
        return flask.jsonify({"ok": True})

    return app


def _concrete(rule) -> tuple:
    url = re.sub(r"<[^>]+>", "x", rule.rule)
    method = sorted((rule.methods or set()) - {"HEAD", "OPTIONS"})[0]
    return url, method


# ── AC-OBS-SHI-004.1 ────────────────────────────────────────────────────────


def test_admin_status_answers_admin_credentials_from_a_container_bridge(sh_env):
    client = _app().test_client()
    resp = client.get("/api/selfhosted/status", headers=_basic(*ADMIN), environ_base=BRIDGE)
    assert resp.status_code == 200, (
        f"HTTP {resp.status_code} {resp.get_json()}: valid admin credentials from a "
        "container port were refused by the gateway-token gate"
    )
    assert resp.get_json()["self_hosted"] is True


def test_export_returns_an_event_ingested_from_outside(sh_env):
    client = _app().test_client()
    ingest = client.post(
        "/ingest/events",
        json={"node_id": "n-remote", "events": [{"id": "evt-remote", "event_type": "x"}]},
        headers={"X-Api-Key": TOKEN},
        environ_base=BRIDGE,
    )
    assert ingest.status_code == 200
    export = client.get("/api/export/events", headers=_basic(*ADMIN), environ_base=BRIDGE)
    assert export.status_code == 200, export.get_data(as_text=True)
    assert "evt-remote" in export.get_data(as_text=True)
    nodes = client.get("/api/selfhosted/nodes", headers={"X-Api-Key": TOKEN}, environ_base=BRIDGE)
    assert nodes.status_code == 200


# ── AC-OBS-SHI-004.2 ────────────────────────────────────────────────────────


def test_every_exempted_view_refuses_a_remote_caller_without_credentials(sh_env):
    app = _app()
    client = app.test_client()
    checked = 0
    for rule in app.url_map.iter_rules():
        if rule.endpoint not in selfhosted.SELF_AUTHENTICATING_ENDPOINTS:
            continue
        url, method = _concrete(rule)
        resp = client.open(url, method=method, json={}, environ_base=BRIDGE)
        assert resp.status_code in (401, 403), (
            f"{method} {url} answered HTTP {resp.status_code} to a remote caller with "
            "no credentials; a view may only skip the gateway gate if it refuses those"
        )
        checked += 1
    assert checked == len(selfhosted.SELF_AUTHENTICATING_ENDPOINTS)


def test_every_selfhosted_api_view_is_a_deliberate_decision(sh_env):
    app = _app()
    api_views = {
        r.endpoint for r in app.url_map.iter_rules()
        if r.endpoint.startswith("selfhosted_ingest.") and r.rule.startswith("/api/")
    }
    not_exempt = api_views - selfhosted.SELF_AUTHENTICATING_ENDPOINTS
    assert not_exempt == {"selfhosted_ingest.sh_policies"}, (
        f"new self-hosted /api view(s) {sorted(not_exempt)}: decide whether each "
        "authenticates its caller (then add it to SELF_AUTHENTICATING_ENDPOINTS) "
        "or keep it behind the gateway gate and list it here"
    )
    assert selfhosted.SELF_AUTHENTICATING_ENDPOINTS <= api_views, "stale endpoint names"
    # The one uncredentialed stub keeps the dashboard rule.
    resp = app.test_client().get("/api/cloud/policies", environ_base=BRIDGE)
    assert resp.status_code == 401


def test_other_api_routes_keep_the_gateway_rule(sh_env):
    client = _app().test_client()
    remote = client.get("/api/some-dashboard-route", headers=_basic(*ADMIN), environ_base=BRIDGE)
    assert remote.status_code == 401, "admin credentials must not open non-self-hosted routes"
    local = client.get("/api/some-dashboard-route", environ_base={"REMOTE_ADDR": "127.0.0.1"})
    assert local.status_code == 200


def test_exemption_is_off_outside_self_hosted_mode(monkeypatch):
    monkeypatch.delenv("SELF_HOSTED", raising=False)
    monkeypatch.delenv("CLAWMETRY_SELF_HOSTED", raising=False)
    assert selfhosted.route_carries_own_auth("selfhosted_ingest.sh_status") is False
    monkeypatch.setenv("SELF_HOSTED", "true")
    assert selfhosted.route_carries_own_auth("selfhosted_ingest.sh_status") is True
    assert selfhosted.route_carries_own_auth("selfhosted_ingest.sh_policies") is False
    assert selfhosted.route_carries_own_auth(None) is False


# ── AC-OBS-SHI-002.2 (the verifier's HTTP half, against a live server) ──────


class _Bridge:
    """WSGI wrapper: every request arrives from the container bridge address."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ["REMOTE_ADDR"] = BRIDGE["REMOTE_ADDR"]
        return self.app(environ, start_response)


class _LiveServer:
    def __init__(self):
        shi._reset_for_tests()
        self.server = make_server("127.0.0.1", 0, _Bridge(_app()), threaded=True)
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def test_verifier_persistence_check_passes_across_a_restart(sh_env):
    verifier = _load_verifier()
    first = _LiveServer()
    try:
        verifier.wait_ready(first.base, ADMIN, timeout=10)
        verifier.send_event(first.base, TOKEN, "node-restart", "event-restart")
    finally:
        first.stop()
    second = _LiveServer()  # same store on disk, fresh process state
    try:
        verifier.wait_ready(second.base, ADMIN, timeout=10)
        verifier.assert_persisted(second.base, ADMIN, "node-restart", "event-restart")
    finally:
        second.stop()


def test_verifier_persistence_check_fails_when_the_store_was_lost(sh_env, monkeypatch, tmp_path):
    verifier = _load_verifier()
    first = _LiveServer()
    try:
        verifier.send_event(first.base, TOKEN, "node-lost", "event-lost")
    finally:
        first.stop()
    monkeypatch.setenv("CLAWMETRY_SELF_HOSTED_DB", str(tmp_path / "a-fresh-volume.db"))
    second = _LiveServer()
    try:
        with pytest.raises(verifier.VerifyError, match="not in the audit export"):
            verifier.assert_persisted(second.base, ADMIN, "node-lost", "event-lost")
    finally:
        second.stop()
