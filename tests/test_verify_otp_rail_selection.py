"""`/api/cloud-cta/verify-otp` must not flip egress on by itself.

Identity and egress are separate choices — `_selfhost_intent()` says so in
its own docstring, and the OAuth twin (`/api/cloud-cta/oauth-start`) has
honoured it since the 2026-08-09 founder report. The OTP path did not: it
called `_full_connect_with_key()` unconditionally, and that calls
`enable_cloud()`. So a self-hosted machine — one whose whole promise is that
nothing leaves the device — started pushing snapshots the moment somebody
signed back in with an emailed code.

These tests pin the three cases: explicit selfhost, explicit managed, and the
omitted mode following the install's recorded intent.
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


class _FakeResp:
    """Cloud /api/otp/verify answering with a good token."""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return json.dumps({"ok": True, "token": "cm_from_otp"}).encode()


@pytest.fixture
def rails(monkeypatch):
    """Record which pairing helper ran, and stub both so nothing touches disk."""
    import dashboard as _d

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: _FakeResp())
    seen = {}

    def _full(tok):
        seen["rail"] = "managed"
        seen["key"] = tok
        return "n2", "enc", "active"

    def _selfhost(tok):
        seen["rail"] = "selfhost"
        seen["key"] = tok
        return "n2", "active"

    monkeypatch.setattr(_d, "_full_connect_with_key", _full)
    monkeypatch.setattr(_d, "_selfhost_signin_with_key", _selfhost)
    return seen


@pytest.fixture
def client():
    import routes.overview as _ov

    app = Flask(__name__)
    app.register_blueprint(_ov.bp_overview)
    return app.test_client()


def _verify(client, **extra):
    return client.post(
        "/api/cloud-cta/verify-otp",
        json=dict({"email": "user@test.com", "code": "123456"}, **extra),
    )


def test_explicit_selfhost_keeps_egress_off(rails, client):
    body = _verify(client, mode="selfhost").get_json()
    assert body["ok"] is True
    assert body["mode"] == "selfhost"
    assert body["trial"] == "active", "the self-host rail mints the same trial"
    assert rails["rail"] == "selfhost", (
        "mode=selfhost must take the identity-only rail — _full_connect_with_key "
        "calls enable_cloud() and would start pushing snapshots"
    )


def test_explicit_managed_connects_and_syncs(rails, client):
    body = _verify(client, mode="managed").get_json()
    assert body["ok"] is True and body["mode"] == "managed"
    assert rails["rail"] == "managed"
    assert rails["key"] == "cm_from_otp"


def test_omitted_mode_follows_the_installs_recorded_intent(rails, client, monkeypatch):
    """A local-only install signing back in must stay local-only even when the
    caller says nothing — old clients send no mode at all."""
    import dashboard as _d

    monkeypatch.setattr(_d, "_selfhost_intent", lambda: True)
    assert _verify(client).get_json()["mode"] == "selfhost"
    assert rails["rail"] == "selfhost"

    monkeypatch.setattr(_d, "_selfhost_intent", lambda: False)
    assert _verify(client).get_json()["mode"] == "managed"
    assert rails["rail"] == "managed"


def test_unknown_mode_is_rejected(rails, client):
    resp = _verify(client, mode="sideways")
    assert resp.status_code == 400
    assert "rail" not in rails, "a bad mode must pair nothing"
