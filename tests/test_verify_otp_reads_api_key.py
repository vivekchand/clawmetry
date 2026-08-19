"""`/api/cloud-cta/verify-otp` must read the field the cloud actually sends.

The cloud's `api_otp_verify` (clawmetry-cloud routes/auth.py) answers a good
code with `{'ok': True, 'api_key': 'cm_…', 'email': …, 'plan': …}` — the same
`api_key` the CLI and the desktop pane read. This proxy looked only for
`token`, so a SUCCESSFUL verify fell through to the error branch and rendered
"Invalid code" — after the cloud had already run `_otp_db_delete(email)`.

Every valid code was reported as invalid AND consumed, so retrying could not
work either: the user had to request a fresh code to fail again. Two live
codes were burned this way while verifying the fix (2026-08-19).

A wrong code is a 401 with `{'error': …}`, which is a different branch. These
tests pin both, plus the unknown-shape case that must never blame the user's
code for a response we did not understand.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error

import pytest
from flask import Flask

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def _resp(payload: dict):
    class _R:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(payload).encode()

    return _R()


@pytest.fixture
def client():
    import routes.overview as _ov

    app = Flask(__name__)
    app.register_blueprint(_ov.bp_overview)
    return app.test_client()


@pytest.fixture
def paired(monkeypatch):
    """Capture the key handed to the pairing helper."""
    import dashboard as _d

    seen = {}
    monkeypatch.setattr(
        _d, "_full_connect_with_key",
        lambda tok: (seen.setdefault("key", tok), ("n1", "enc", "active"))[1],
    )
    monkeypatch.setattr(
        _d, "_selfhost_signin_with_key",
        lambda tok: (seen.setdefault("key", tok), ("n1", "active"))[1],
    )
    return seen


def _verify(client, **extra):
    return client.post(
        "/api/cloud-cta/verify-otp",
        json=dict({"email": "u@test.com", "code": "123456", "mode": "managed"}, **extra),
    )


def test_api_key_is_the_field_the_cloud_sends(monkeypatch, client, paired):
    """The real success shape, copied from the cloud handler."""
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *a, **k: _resp({"ok": True, "api_key": "cm_real", "email": "u@test.com",
                               "plan": "free"}),
    )
    body = _verify(client).get_json()
    assert body["ok"] is True, (
        "a good code must not report failure — the cloud has already deleted "
        "the OTP by this point, so the user cannot simply retry"
    )
    assert body["token"] == "cm_real"
    assert paired["key"] == "cm_real", "the machine must actually be paired"


@pytest.mark.parametrize("field", ["api_key", "token", "key"])
def test_every_name_the_cloud_has_used_is_accepted(monkeypatch, client, paired, field):
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *a, **k: _resp({"ok": True, field: "cm_x"}),
    )
    assert _verify(client).get_json()["token"] == "cm_x"


def test_wrong_code_surfaces_the_cloud_message_and_status(monkeypatch, client):
    """A rejected code is a 401 with the cloud's own wording, not a 502."""
    def _raise(*a, **k):
        raise urllib.error.HTTPError(
            "u", 401, "Unauthorized", {},
            __import__("io").BytesIO(json.dumps({"error": "Invalid code"}).encode()),
        )

    monkeypatch.setattr("urllib.request.urlopen", _raise)
    resp = _verify(client)
    assert resp.status_code == 401, "a wrong code is not a gateway failure"
    assert resp.get_json()["error"] == "Invalid code"


def test_unknown_shape_does_not_blame_the_users_code(monkeypatch, client):
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: _resp({"ok": True}))
    body = _verify(client).get_json()
    assert body["ok"] is False
    assert "Invalid code" not in body["error"], (
        "the code was fine; we just did not recognise the response"
    )
