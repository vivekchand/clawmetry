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
        lambda provider, mode="managed":
            "https://app.clawmetry.com/api/oauth/%s/start?cli_port=51234" % provider,
    )
    c = cta_app.test_client()
    for provider in ("github", "google"):
        r = c.post("/api/cloud-cta/oauth-start", json={"provider": provider})
        assert r.status_code == 200, r.data
        body = r.get_json()
        assert body["ok"] is True
        assert provider in body["url"]
        assert "cli_port=" in body["url"]


def test_oauth_start_rejects_bad_mode(cta_app):
    c = cta_app.test_client()
    r = c.post("/api/cloud-cta/oauth-start",
               json={"provider": "github", "mode": "sideways"})
    assert r.status_code == 400
    assert r.get_json()["ok"] is False


def test_oauth_start_passes_mode_to_bridge(cta_app, monkeypatch):
    import dashboard as _d

    seen = {}

    def _fake(provider, mode="managed"):
        seen["provider"], seen["mode"] = provider, mode
        return "https://app.clawmetry.com/api/oauth/%s/start?cli_port=51234" % provider

    monkeypatch.setattr(_d, "_start_oauth_bridge", _fake)
    c = cta_app.test_client()
    r = c.post("/api/cloud-cta/oauth-start",
               json={"provider": "github", "mode": "selfhost"})
    assert r.status_code == 200, r.data
    assert seen == {"provider": "github", "mode": "selfhost"}
    # Callers that omit mode (the existing cloud modal) stay managed.
    c.post("/api/cloud-cta/oauth-start", json={"provider": "google"})
    assert seen["mode"] == "managed"


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


def test_oauth_status_includes_mode_and_trial(cta_app, monkeypatch):
    import dashboard as _d

    monkeypatch.setattr(
        _d, "_OAUTH_BRIDGE",
        {"status": "connected", "provider": "github", "mode": "selfhost",
         "node_id": "host-1", "enc_key": "", "trial": "active", "error": ""},
    )
    c = cta_app.test_client()
    body = c.get("/api/cloud-cta/oauth-status").get_json()
    assert body["mode"] == "selfhost"
    assert body["trial"] == "active"
    assert body["enc_key"] == ""


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


# ── Self-host OAuth rail (identity + trial, egress stays off) ──────────────

class _FakeResp:
    def __init__(self, payload):
        self._data = json.dumps(payload).encode()

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _selfhost_env(tmp_path, monkeypatch):
    """Common monkeypatching for _selfhost_signin_with_key tests."""
    import urllib.request as _ur

    import dashboard as _d
    from clawmetry import config as _cfg
    from clawmetry import license as _lic
    from clawmetry import sync as _sync

    home = tmp_path / "home"
    (home / ".clawmetry").mkdir(parents=True)
    nocloud = home / ".clawmetry" / "nocloud"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(_d.os.path, "expanduser",
                        lambda p: p.replace("~", str(home)))
    monkeypatch.setattr(_sync, "CONFIG_DIR", home / ".clawmetry")
    monkeypatch.setattr(_sync, "CONFIG_FILE", home / ".clawmetry" / "config.json")
    monkeypatch.setattr(_sync, "validate_key",
                        lambda *a, **k: {"node_id": "node-sh"})
    monkeypatch.setattr(_cfg, "NOCLOUD_MARKER_PATH", str(nocloud))
    monkeypatch.setattr(_d, "_write_cloud_token", lambda tok: None)
    monkeypatch.setattr(_lic, "_node_id", lambda: "node-sh")
    import routes.trial as _rt
    monkeypatch.setattr(_rt, "_ensure_local_daemon", lambda: None)
    return _d, _lic, _ur, home, nocloud


def test_selfhost_signin_keeps_marker_and_activates_trial(tmp_path, monkeypatch):
    """The self-host OAuth rail must never enable egress: the nocloud marker
    is written before the key is persisted (the daemon must not observe a
    cm_ key without it), and the account's trial is minted server-side then
    activated locally — same rail as `clawmetry connect` keep-local."""
    _d, _lic, _ur, home, nocloud = _selfhost_env(tmp_path, monkeypatch)

    activated = {}

    def _fake_activate(key, node_id=None, **k):
        activated["key"] = key
        return True, "ok"

    monkeypatch.setattr(_lic, "activate", _fake_activate)
    monkeypatch.setattr(_lic, "_cloud_base", lambda: "https://ingest.example")
    monkeypatch.setattr(
        _ur, "urlopen",
        lambda req, timeout=0: _FakeResp(
            {"ok": True, "key": "CLAW1.test.key", "expires_at": 9999999999}),
    )

    node_id, trial = _d._selfhost_signin_with_key("cm_selfhost123")
    assert node_id == "node-sh"
    assert trial == "active"
    assert activated["key"] == "CLAW1.test.key"
    assert nocloud.exists(), \
        "self-host sign-in must keep egress off (nocloud marker)"
    cfg = json.loads((home / ".clawmetry" / "config.json").read_text())
    assert cfg["api_key"] == "cm_selfhost123"
    assert cfg["node_id"] == "node-sh"


def test_selfhost_signin_expired_trial_never_activates(tmp_path, monkeypatch):
    _d, _lic, _ur, home, nocloud = _selfhost_env(tmp_path, monkeypatch)

    def _boom(*a, **k):
        raise AssertionError("expired trial must not call license.activate")

    monkeypatch.setattr(_lic, "activate", _boom)
    monkeypatch.setattr(_lic, "_cloud_base", lambda: "https://ingest.example")
    monkeypatch.setattr(
        _ur, "urlopen",
        lambda req, timeout=0: _FakeResp({"ok": True, "expired": True}),
    )

    node_id, trial = _d._selfhost_signin_with_key("cm_selfhost123")
    assert trial == "expired"
    assert nocloud.exists()
    # Identity still persisted: the user is signed in even without a trial.
    cfg = json.loads((home / ".clawmetry" / "config.json").read_text())
    assert cfg["api_key"] == "cm_selfhost123"


def test_selfhost_signin_survives_trial_server_outage(tmp_path, monkeypatch):
    """A trial-mint outage must not lose the sign-in: identity persists,
    egress stays off, trial reports 'unavailable'."""
    _d, _lic, _ur, home, nocloud = _selfhost_env(tmp_path, monkeypatch)

    monkeypatch.setattr(_lic, "_cloud_base", lambda: "https://ingest.example")

    def _down(req, timeout=0):
        raise OSError("connection refused")

    monkeypatch.setattr(_ur, "urlopen", _down)

    node_id, trial = _d._selfhost_signin_with_key("cm_selfhost123")
    assert trial == "unavailable"
    assert nocloud.exists()
    cfg = json.loads((home / ".clawmetry" / "config.json").read_text())
    assert cfg["api_key"] == "cm_selfhost123"


# ── Account email resolution (profile menu "who am I") ─────────────────────────
# Bug this guards: a GitHub-OAuth cloud account holds no local license, so the
# profile menu's identity (license `sub`) was empty and the header said
# "Not signed in" on a fully signed-in, cloud-connected node (2026-08-09).


def _email_env(tmp_path, monkeypatch):
    import dashboard as _d

    home = tmp_path / "home"
    (home / ".clawmetry").mkdir(parents=True)
    monkeypatch.setattr(_d.os.path, "expanduser",
                        lambda p: p.replace("~", str(home)))
    monkeypatch.setattr(
        _d, "_ACCOUNT_EMAIL_CACHE",
        {"token": "", "email": "", "fail_at": 0.0})
    return _d, home


def test_account_email_prefers_matching_config(tmp_path, monkeypatch):
    _d, home = _email_env(tmp_path, monkeypatch)
    (home / ".clawmetry" / "config.json").write_text(json.dumps(
        {"api_key": "cm_abc", "account_email": "dev@example.com"}))
    assert _d._account_email_for_token("cm_abc") == "dev@example.com"


def test_account_email_ignores_stale_config_and_falls_back_to_cloud(
        tmp_path, monkeypatch):
    """config.json written under a PREVIOUS key must not leak its email."""
    import urllib.request as _ur

    _d, home = _email_env(tmp_path, monkeypatch)
    (home / ".clawmetry" / "config.json").write_text(json.dumps(
        {"api_key": "cm_old", "account_email": "old@example.com"}))
    monkeypatch.setattr(
        _ur, "urlopen",
        lambda url, timeout=0: _FakeResp({"email": "new@example.com"}))
    assert _d._account_email_for_token("cm_new") == "new@example.com"
    # Stale-keyed config must NOT be overwritten with the other key's email.
    cfg = json.loads((home / ".clawmetry" / "config.json").read_text())
    assert cfg["account_email"] == "old@example.com"


def test_account_email_hides_placeholder_accounts(tmp_path, monkeypatch):
    """agent+<hash>@clawmetry.auto/.linked are internal pre-claim identities,
    never something to show a human."""
    import urllib.request as _ur

    _d, home = _email_env(tmp_path, monkeypatch)
    monkeypatch.setattr(
        _ur, "urlopen",
        lambda url, timeout=0: _FakeResp(
            {"email": "agent+deadbeef@clawmetry.auto"}))
    assert _d._account_email_for_token("cm_abc") == ""


def test_account_email_offline_degrades_to_empty(tmp_path, monkeypatch):
    import urllib.request as _ur

    _d, home = _email_env(tmp_path, monkeypatch)

    def _down(url, timeout=0):
        raise OSError("connection refused")

    monkeypatch.setattr(_ur, "urlopen", _down)
    assert _d._account_email_for_token("cm_abc") == ""
    assert _d._account_email_for_token("") == ""


def test_cloud_cta_status_reports_account_email(cta_app, monkeypatch):
    import dashboard as _d

    monkeypatch.setattr(_d, "_read_cloud_token", lambda: "cm_abc")
    monkeypatch.setattr(
        _d, "_account_email_for_token",
        lambda tok: "dev@example.com" if tok == "cm_abc" else "")
    body = cta_app.test_client().get("/api/cloud-cta/status").get_json()
    assert body["account_linked"] is True
    assert body["account_email"] == "dev@example.com"


def test_cloud_cta_status_signed_out_has_no_email(cta_app, monkeypatch):
    import dashboard as _d

    monkeypatch.setattr(_d, "_read_cloud_token", lambda: None)
    body = cta_app.test_client().get("/api/cloud-cta/status").get_json()
    assert body["account_linked"] is False
    assert body["account_email"] == ""
