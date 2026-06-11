"""Regression guard for SSRF via alert webhooks + the gw/config exemption
(cloud #1574).

Webhook URLs were POSTed to with no validation (blind SSRF to 169.254.169.254,
the local gateway, internal hosts). And /api/gw/config was auth-exempt for ALL
callers while opening an outbound connection to a caller-supplied URL.
"""
import importlib
import socket

dashboard = importlib.import_module("dashboard")


def test_url_safe_rejects_internal_and_bad_schemes():
    bad = [
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata
        "http://127.0.0.1:18789/",                    # local gateway
        "http://localhost/x",
        "http://10.0.0.5/x",                          # private
        "http://192.168.1.1/x",                       # private
        "https://[::1]/x",                            # loopback v6
        "ftp://example.com/x",                        # non-http scheme
        "file:///etc/passwd",
        "http://0.0.0.0/x",                           # unspecified
    ]
    for u in bad:
        ok, _ = dashboard._url_safe_for_external_request(u)
        assert ok is False, u


def test_url_safe_allows_external(monkeypatch):
    # Force a public resolution so the test is offline-stable.
    monkeypatch.setattr(socket, "getaddrinfo",
                        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))])
    ok, _ = dashboard._url_safe_for_external_request("https://hooks.slack.com/services/x")
    assert ok is True


def test_gw_config_remote_requires_token(monkeypatch):
    monkeypatch.setattr(dashboard, "GATEWAY_TOKEN", "tok", raising=False)
    # Non-loopback caller: must be rejected (was unconditionally exempt).
    with dashboard.app.test_request_context(
        "/api/gw/config", method="POST", environ_base={"REMOTE_ADDR": "203.0.113.5"}
    ):
        rv = dashboard._check_auth()
        assert rv is not None and rv[1] == 401
    # Loopback caller: still allowed without a token (local setup).
    with dashboard.app.test_request_context(
        "/api/gw/config", method="POST", environ_base={"REMOTE_ADDR": "127.0.0.1"}
    ):
        assert dashboard._check_auth() is None
