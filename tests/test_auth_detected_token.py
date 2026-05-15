"""Tests for the /api/auth/detected-token bootstrap endpoint.

Issue #1356 (PR-B). The dashboard JS needs the gateway token before it
can authenticate, but the token lives in OpenClaw's config files. This
endpoint exposes the locally-detected token to the loopback caller so
the page can self-bootstrap, while refusing to leak the token off-box.

Security invariants exercised here:

  * 200 + token only when ``request.remote_addr`` is loopback AND no
    ``X-Forwarded-For`` / ``X-Real-IP`` header is present.
  * 403 ``localhost only`` for any non-loopback ``remote_addr``.
  * 403 ``localhost only`` even on loopback when the request is
    proxied (proxy headers present), since the original peer could be
    anywhere.
  * 404 ``no token detected`` when ``dashboard.GATEWAY_TOKEN`` is
    unset, regardless of who asked.

Tests use Flask's test_client + ``environ_overrides`` to spoof
``REMOTE_ADDR`` and the proxy headers — same pattern other route-level
unit tests in this suite use.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import dashboard  # noqa: E402  (import registers shared module state)
from routes.meta import bp_auth  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def app(monkeypatch):
    """Minimal Flask app with only the auth blueprint mounted.

    Each test gets its own app so blueprint registration never collides;
    ``GATEWAY_TOKEN`` is set per-test via ``monkeypatch.setattr`` so we
    never mutate dashboard module state across tests.
    """
    monkeypatch.setattr(dashboard, "GATEWAY_TOKEN", "deadbeef" * 6, raising=False)
    a = Flask(__name__)
    a.register_blueprint(bp_auth)
    return a


@pytest.fixture
def client(app):
    return app.test_client()


# ─────────────────────────────────────────────────────────────────────────────
# happy path: loopback peer, token set
# ─────────────────────────────────────────────────────────────────────────────


def test_returns_token_for_loopback_ipv4(client):
    """127.0.0.1 with no proxy headers gets the token + a source label."""
    r = client.get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
    )
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body["token"] == "deadbeef" * 6
    # source is informational; route must always populate it with one of
    # the known labels.
    assert body["source"] in {"openclaw.json", "env", "process"}


def test_returns_token_for_loopback_ipv6(client):
    """::1 (IPv6 loopback) is also accepted."""
    r = client.get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "::1"},
    )
    assert r.status_code == 200
    assert r.get_json()["token"]


def test_source_label_env_when_env_var_matches(client, monkeypatch):
    """If OPENCLAW_GATEWAY_TOKEN matches GATEWAY_TOKEN, source=='env'."""
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", "deadbeef" * 6)
    r = client.get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
    )
    assert r.status_code == 200
    assert r.get_json()["source"] == "env"


# ─────────────────────────────────────────────────────────────────────────────
# 403: non-loopback peer
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "remote_addr",
    [
        "10.0.0.5",         # private LAN
        "192.168.1.42",     # home router LAN
        "8.8.8.8",          # public IP
        "172.16.0.1",       # RFC1918
        "2001:db8::1",      # public IPv6
        "",                 # empty / unknown peer
    ],
)
def test_rejects_non_loopback_remote_addr(client, remote_addr):
    r = client.get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": remote_addr},
    )
    assert r.status_code == 403, (remote_addr, r.get_data(as_text=True))
    assert r.get_json() == {"error": "localhost only"}


# ─────────────────────────────────────────────────────────────────────────────
# 403: proxy headers present (even on loopback)
# ─────────────────────────────────────────────────────────────────────────────


def test_rejects_loopback_with_x_forwarded_for(client):
    """A loopback peer carrying X-Forwarded-For means the request was
    proxied — the original client could be anywhere on the internet.
    Refuse to hand out the token."""
    r = client.get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
        headers={"X-Forwarded-For": "203.0.113.45"},
    )
    assert r.status_code == 403
    assert r.get_json() == {"error": "localhost only"}


def test_rejects_loopback_with_x_real_ip(client):
    """X-Real-IP triggers the same defence as X-Forwarded-For."""
    r = client.get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "::1"},
        headers={"X-Real-IP": "198.51.100.7"},
    )
    assert r.status_code == 403
    assert r.get_json() == {"error": "localhost only"}


# ─────────────────────────────────────────────────────────────────────────────
# 404: no token configured
# ─────────────────────────────────────────────────────────────────────────────


def test_returns_404_when_gateway_token_unset(monkeypatch):
    """When dashboard.GATEWAY_TOKEN is None, even loopback gets 404."""
    monkeypatch.setattr(dashboard, "GATEWAY_TOKEN", None, raising=False)
    a = Flask(__name__)
    a.register_blueprint(bp_auth)
    r = a.test_client().get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
    )
    assert r.status_code == 404
    assert r.get_json() == {"error": "no token detected"}


def test_returns_404_when_gateway_token_empty_string(monkeypatch):
    """Empty-string token is treated as unset (mirrors _detect_gateway_token)."""
    monkeypatch.setattr(dashboard, "GATEWAY_TOKEN", "", raising=False)
    a = Flask(__name__)
    a.register_blueprint(bp_auth)
    r = a.test_client().get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
    )
    assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# auth-free guarantee
# ─────────────────────────────────────────────────────────────────────────────


def test_endpoint_does_not_require_authorization_header(client):
    """The whole point of this endpoint is bootstrapping — it MUST NOT
    require a pre-existing Authorization header (chicken-and-egg)."""
    r = client.get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
        # no Authorization header at all
    )
    assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# 403: DNS-rebinding defence (Host header check)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "host_header",
    [
        "evil.com",
        "evil.com:8900",
        "internal.corp",
        "192.168.1.5:8900",   # LAN IP via DNS
    ],
)
def test_rejects_non_loopback_host_header(client, host_header):
    """DNS rebinding: attacker resolves evil.com -> 127.0.0.1 in the
    victim's browser. remote_addr is loopback, but the JS origin is
    evil.com — so the page that reads the response is hostile. The
    Host header still says 'evil.com', which is what we reject on."""
    r = client.get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1", "HTTP_HOST": host_header},
    )
    assert r.status_code == 403, (host_header, r.get_data(as_text=True))
    assert r.get_json() == {"error": "localhost only"}


@pytest.mark.parametrize(
    "host_header",
    [
        "localhost",
        "localhost:8900",
        "127.0.0.1",
        "127.0.0.1:8900",
        "[::1]",
        "[::1]:8900",
    ],
)
def test_accepts_loopback_host_header_variants(client, host_header):
    """All standard loopback Host header forms (with and without port)
    must be accepted — otherwise we'd lock out the common case."""
    r = client.get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1", "HTTP_HOST": host_header},
    )
    assert r.status_code == 200, (host_header, r.get_data(as_text=True))


# ─────────────────────────────────────────────────────────────────────────────
# 403: Forwarded header (RFC 7239) defence
# ─────────────────────────────────────────────────────────────────────────────


def test_rejects_loopback_with_rfc7239_forwarded_header(client):
    """RFC 7239 Forwarded: header is the canonical proxy marker; defend
    against it as well as the legacy X-Forwarded-For."""
    r = client.get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
        headers={"Forwarded": "for=203.0.113.5;proto=https"},
    )
    assert r.status_code == 403
    assert r.get_json() == {"error": "localhost only"}


# ─────────────────────────────────────────────────────────────────────────────
# 403: dashboard bound to non-loopback host (--host 0.0.0.0)
# ─────────────────────────────────────────────────────────────────────────────


def test_rejects_when_server_bound_to_wildcard_host(monkeypatch, app):
    """When the operator passed --host 0.0.0.0 (LAN exposure), refuse
    to hand out the token at all. We can't tell from a single request
    whether the browser is on this box or on the same Wi-Fi network."""
    monkeypatch.setattr(dashboard, "_SERVER_HOST", "0.0.0.0", raising=False)
    r = app.test_client().get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
    )
    assert r.status_code == 403, r.get_data(as_text=True)
    assert r.get_json() == {"error": "localhost only"}


def test_accepts_when_server_bound_to_loopback(monkeypatch, app):
    """Explicit --host 127.0.0.1 (default) keeps the endpoint open."""
    monkeypatch.setattr(dashboard, "_SERVER_HOST", "127.0.0.1", raising=False)
    r = app.test_client().get(
        "/api/auth/detected-token",
        environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
    )
    assert r.status_code == 200
