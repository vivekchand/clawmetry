"""Guard for the one-click cloud-sync OAuth CTA.

The local "Enable Cloud Sync" modal must offer GitHub/Google one-click sign-up
(not just email OTP). The bug this guards: the modal exposed only an email field,
and there was no backend bridge to mint + persist a cm_ key via OAuth.

Covers:
  - POST /api/cloud-cta/oauth-start rejects unknown providers (400) and returns
    {ok, url} for github/google.
  - GET /api/cloud-cta/oauth-status reports the bridge state shape the modal polls.
  - dashboard._start_oauth_bridge validates the provider and primes _OAUTH_BRIDGE.
  - dashboard._full_connect_with_key writes ~/.clawmetry/config.json with the
    api_key + an encryption key (so the node actually syncs after OAuth).
"""

from __future__ import annotations

import json

import pytest
from flask import Flask


@pytest.fixture
def cta_app(monkeypatch):
    import routes.overview as ov

    app = Flask(__name__)
    app.register_blueprint(ov.bp_overview)
    return app


def test_oauth_start_rejects_bad_provider(cta_app):
    c = cta_app.test_client()
    r = c.post("/api/cloud-cta/oauth-start", json={"provider": "myspace"})
    assert r.status_code == 400
    assert r.get_json()["ok"] is False


def test_oauth_start_returns_url_for_valid_provider(cta_app, monkeypatch):
    import dashboard as _d

    monkeypatch.setattr(
        _d, "_start_oauth_bridge",
        lambda provider: "https://app.clawmetry.com/api/oauth/%s/start?cli_port=51234" % provider,
    )
    c = cta_app.test_client()
    for provider in ("github", "google"):
        r = c.post("/api/cloud-cta/oauth-start", json={"provider": provider})
        assert r.status_code == 200, r.data
        body = r.get_json()
        assert body["ok"] is True
        assert provider in body["url"]
        assert "cli_port=" in body["url"]


def test_oauth_status_shape(cta_app, monkeypatch):
    import dashboard as _d

    monkeypatch.setattr(
        _d, "_OAUTH_BRIDGE",
        {"status": "connected", "provider": "github", "node_id": "host-1",
         "enc_key": "abc123", "error": ""},
    )
    c = cta_app.test_client()
    r = c.get("/api/cloud-cta/oauth-status")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "connected"
    assert body["node_id"] == "host-1"
    assert body["enc_key"] == "abc123"


def test_start_oauth_bridge_rejects_bad_provider():
    import dashboard as _d

    assert _d._start_oauth_bridge("nope") is None
    assert _d._OAUTH_BRIDGE["status"] == "error"


def test_full_connect_writes_config_and_clears_nocloud(tmp_path, monkeypatch):
    """Connecting must (a) write config and (b) clear the local-only marker.

    The 'enabled Cloud Sync but 0 nodes' bug: a local-only install leaves
    ~/.clawmetry/nocloud in place, so the daemon never pushes. Connect must
    remove it.
    """
    import dashboard as _d
    from clawmetry import sync as _sync
    from clawmetry import config as _cfg

    home = tmp_path / "home"
    (home / ".clawmetry").mkdir(parents=True)
    nocloud = home / ".clawmetry" / "nocloud"
    nocloud.write_text("")  # simulate a local-only install
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(_d.os.path, "expanduser",
                        lambda p: p.replace("~", str(home)))

    monkeypatch.setattr(_sync, "CONFIG_DIR", home / ".clawmetry")
    monkeypatch.setattr(_sync, "CONFIG_FILE", home / ".clawmetry" / "config.json")
    monkeypatch.setattr(_sync, "validate_key", lambda *a, **k: {"node_id": "node-xyz"})
    monkeypatch.setattr(_cfg, "NOCLOUD_MARKER_PATH", str(nocloud))
    monkeypatch.setattr(_d, "_write_cloud_token", lambda tok: None)
    monkeypatch.setattr(_d, "_is_sync_running", lambda: True)
    # Neutralize the daemon (re)start side effect in tests.
    monkeypatch.setattr(_d, "_is_macos", lambda: False)
    monkeypatch.setattr(_d, "_is_linux", lambda: False)
    monkeypatch.setattr(_d, "_start_daemon_background", lambda: None)

    node_id, enc_key = _d._full_connect_with_key("cm_testkey123")
    assert node_id == "node-xyz"
    assert enc_key  # auto-generated

    cfg = json.loads((home / ".clawmetry" / "config.json").read_text())
    assert cfg["api_key"] == "cm_testkey123"
    assert cfg["node_id"] == "node-xyz"
    assert cfg["encryption_key"] == enc_key
    assert not nocloud.exists(), "connect must clear the local-only nocloud marker"


def test_enable_cloud_removes_marker(tmp_path, monkeypatch):
    from clawmetry import config as _cfg

    marker = tmp_path / "nocloud"
    marker.write_text("")
    monkeypatch.setattr(_cfg, "NOCLOUD_MARKER_PATH", str(marker))
    monkeypatch.delenv("CLAWMETRY_NO_CLOUD", raising=False)

    assert _cfg.is_cloud_disabled() is True
    assert _cfg.enable_cloud() is True
    assert _cfg.is_cloud_disabled() is False
    assert _cfg.enable_cloud() is False  # idempotent: nothing left to remove
