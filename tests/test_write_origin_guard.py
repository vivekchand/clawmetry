"""The local write API must refuse cross-origin writes (finding 12).

``_check_auth`` trusts any loopback caller with no credential — the right
posture for a local tool, but on its own it means any page the user has open in
another tab can drive this API. A cross-origin ``<form method=post>`` needs no
CORS permission to *arrive*; the browser only stops the attacker reading the
reply, so the side effect still lands.

The endpoints that need no request body were the exposed ones: rotate the E2E
key (making everything already synced undecryptable to its owner), stop the
agents, kill every cron, deactivate the licence.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dashboard  # noqa: E402


# Routes are registered inside dashboard.detect_config(), not at import time.
# Without this the url_map is empty and every route test below is vacuous —
# exactly the "green but hollow" shape this review found twice.
_REGISTERED = False


def _registered_app():
    global _REGISTERED
    if not _REGISTERED:
        try:
            dashboard.detect_config()
        except Exception:
            pass
        _REGISTERED = True
    return dashboard.app


@pytest.fixture()
def client(monkeypatch):
    app = _registered_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


def _rules_with_write_methods():
    seen = []
    for rule in _registered_app().url_map.iter_rules():
        if not (rule.rule.startswith("/api/") or rule.rule.startswith("/v1/")):
            continue
        if "<" in rule.rule:  # skip converters — no safe value to substitute
            continue
        methods = set(rule.methods or ()) & set(WRITE_METHODS)
        if methods:
            seen.append((rule.rule, sorted(methods)[0]))
    return seen


def test_the_app_actually_has_write_endpoints_to_guard():
    """If this ever returns nothing the parametrised test below is vacuous."""
    assert len(_rules_with_write_methods()) > 20


@pytest.mark.parametrize("path,method", _rules_with_write_methods())
def test_write_endpoints_reject_a_foreign_origin(client, path, method):
    resp = client.open(
        path, method=method, headers={"Origin": "https://evil.example"}
    )
    assert resp.status_code == 403, (
        f"{method} {path} accepted a write from another origin"
    )
    assert (resp.get_json() or {}).get("crossOriginBlocked") is True


@pytest.mark.parametrize(
    "path",
    [
        "/api/local/e2e-key/regenerate",
        "/api/emergency-stop",
        "/api/cron/kill-all",
    ],
)
def test_the_named_body_less_sinks_are_covered(client, path):
    """Spelled out separately so the specific exposures stay named in the
    suite even if the route map is refactored."""
    resp = client.post(path, headers={"Origin": "https://evil.example"})
    assert resp.status_code == 403


def test_reads_are_never_blocked(client):
    """This is CSRF defence, not CORS — a cross-origin GET is unaffected."""
    resp = client.get("/api/auth/check", headers={"Origin": "https://evil.example"})
    assert resp.status_code != 403


def test_requests_without_an_origin_still_work(client):
    """curl, the CLI, the desktop shell and OTLP exporters send no Origin.
    Browsers always send one on a non-GET, so absence means "not a browser"."""
    assert dashboard._cross_origin_write_blocked.__doc__
    with _registered_app().test_request_context("/api/emergency-stop", method="POST"):
        assert dashboard._cross_origin_write_blocked() is False


def test_same_origin_writes_are_allowed():
    with _registered_app().test_request_context(
        "/api/emergency-stop",
        method="POST",
        headers={"Origin": "http://localhost:8900", "Host": "localhost:8900"},
    ):
        assert dashboard._cross_origin_write_blocked() is False


def test_an_unparseable_origin_fails_closed():
    with _registered_app().test_request_context(
        "/api/emergency-stop", method="POST", headers={"Origin": "not a url"}
    ):
        assert dashboard._cross_origin_write_blocked() is True


def test_the_escape_hatch_works(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ALLOW_CROSS_ORIGIN_WRITES", "1")
    with _registered_app().test_request_context(
        "/api/emergency-stop", method="POST", headers={"Origin": "https://evil.example"}
    ):
        assert dashboard._cross_origin_write_blocked() is False


def test_e2e_key_is_not_served_over_a_get(client):
    """Finding 8: the plaintext key used to come back in a GET body, readable
    by every local process."""
    resp = client.get("/api/local/e2e-key")
    body = resp.get_json() or {}
    assert "key" not in body, "the GET must report only whether a key is set"
    assert "configured" in body
