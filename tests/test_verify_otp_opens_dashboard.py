"""A correct emailed code must open the local dashboard, not loop back to the wall.

Customer report 2026-09-12: "I enter my email address, a code is issued via
email, I enter the code, and I get the 'Sign in to open the dashboard.'"

The login wall (`auth-bootstrap.js::checkAuth`) accepts ONLY the gateway
token. Email sign-in proved identity to the cloud but handed the page no
credential: it cleared a marker and reloaded, hoping the zero-click
`/api/auth/detected-token` would supply one. That endpoint refuses unless
every strict loopback check passes (REMOTE_ADDR, Host header, no proxy
headers, loopback bind). When one of them fails on a machine, zero-click
fails on every load, and a successful email sign-in reloads into the same
wall forever.

`verify-otp` now returns the gateway token as `dashboard_token` when
  * the request passes the same strict loopback check, or
  * the account that just verified is the account this machine is already
    linked to (proving it needed the owner's inbox), so a Host/proxy quirk
    can no longer lock the owner out.
Anyone else gets no token, and the page says why instead of reloading.
"""

from __future__ import annotations

import json
import os
import sys

import pytest
from flask import Flask

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

GW = "gw_secret_token"
KEY = "cm_from_otp"


class _FakeResp:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return json.dumps({"ok": True, "api_key": KEY}).encode()


@pytest.fixture
def env(monkeypatch):
    import dashboard as _d

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: _FakeResp())
    monkeypatch.setattr(_d, "_selfhost_signin_with_key", lambda tok: ("n1", "active"))
    monkeypatch.setattr(_d, "_full_connect_with_key", lambda tok: ("n1", "enc", "active"))
    monkeypatch.setattr(_d, "GATEWAY_TOKEN", GW)
    monkeypatch.setattr(_d, "_SERVER_HOST", "127.0.0.1", raising=False)
    return _d


@pytest.fixture
def client():
    import routes.overview as _ov

    app = Flask(__name__)
    app.register_blueprint(_ov.bp_overview)
    return app.test_client()


def _verify(client, base_url="http://localhost:8900", headers=None):
    return client.post(
        "/api/cloud-cta/verify-otp",
        json={"email": "owner@test.com", "code": "123456", "mode": "selfhost"},
        base_url=base_url,
        headers=headers or {},
    ).get_json()


def test_strict_loopback_signin_gets_the_dashboard_token(env, client, monkeypatch):
    monkeypatch.setattr(env, "_read_cloud_token", lambda: None)
    body = _verify(client)
    assert body["ok"] is True
    assert body["dashboard_token"] == GW


def test_owner_signin_opens_dashboard_even_when_loopback_check_fails(env, client, monkeypatch):
    """The reported loop: zero-click is refused (here: a proxy header), but the
    person who verified is the machine's own linked account."""
    monkeypatch.setattr(env, "_read_cloud_token", lambda: KEY)
    body = _verify(client, headers={"X-Forwarded-For": "127.0.0.1"})
    assert body["ok"] is True
    assert body["dashboard_token"] == GW


def test_owner_signin_via_non_loopback_host_name(env, client, monkeypatch):
    monkeypatch.setattr(env, "_read_cloud_token", lambda: KEY)
    body = _verify(client, base_url="http://studio.local:8900")
    assert body["dashboard_token"] == GW


def test_other_account_off_strict_loopback_gets_no_token(env, client, monkeypatch):
    """A DNS-rebound or proxied page signing in with its OWN email must not be
    handed this machine's gateway token."""
    monkeypatch.setattr(env, "_read_cloud_token", lambda: "cm_the_real_owner")
    body = _verify(client, base_url="http://evil.example:8900")
    assert body["ok"] is False
    assert "dashboard_token" not in body


def test_unlinked_machine_off_strict_loopback_gets_no_token(env, client, monkeypatch):
    monkeypatch.setattr(env, "_read_cloud_token", lambda: None)
    body = _verify(client, headers={"X-Forwarded-For": "10.0.0.9"})
    assert "dashboard_token" not in body


def test_login_card_stores_the_token_and_never_reloads_blind():
    path = os.path.join(_REPO_ROOT, "clawmetry", "static", "js", "auth-bootstrap.js")
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    start = src.index("function clawmetryEmailOtpVerify")
    body = src[start:src.index("\nfunction ", start + 1)]
    assert "dashboard_token" in body, "the verify handler must use the token verify-otp returns"
    assert "localStorage.setItem('clawmetry-token'" in body, (
        "without storing a credential the reload lands on the same login wall"
    )
