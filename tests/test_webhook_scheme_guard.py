"""Every webhook dispatch path must reject a non-HTTP scheme.

``urllib.request.urlopen`` opens ``file://`` and ``ftp://`` as well as HTTP,
and it serves a ``file://`` URL even when the ``Request`` carries a ``data=``
body -- so "POST the alert JSON to this webhook" against
``file:///etc/passwd`` read the file and reported success.

``dashboard._url_safe_for_external_request`` has encoded that rule since
cloud #1574, but nothing ever called it: the three functions that actually
build the request passed the configured URL straight to ``urlopen``. Its own
test (tests/test_ssrf_guard.py) checked the predicate in isolation and is
registered in no workflow, so neither CI nor the test suite noticed.

These tests are deliberately written against the DISPATCH FUNCTIONS rather
than the predicate: the bug was never that the check was wrong, it was that
nothing invoked it. A test that only exercises ``is_http_url`` would pass
again on the day someone drops the call.
"""
import importlib
import urllib.request

import pytest

from clawmetry import url_guard


BAD_URLS = [
    "file:///etc/passwd",
    "ftp://example.invalid/x",
    "data:text/plain,hello",
    "gopher://example.invalid/1",
    "http:///no-host",
    "",
]


def test_is_http_url_table():
    for url in BAD_URLS:
        assert url_guard.is_http_url(url) is False, url
    for url in ("http://127.0.0.1:9000/hook",
                "https://hooks.slack.com/services/x",
                "  https://example.com/x  ",
                "HTTPS://example.com/x"):
        assert url_guard.is_http_url(url) is True, url
    # Never raises on junk input.
    for url in (None, 0, object(), "https://[::1/x"):
        assert url_guard.is_http_url(url) is False


@pytest.fixture
def no_urlopen(monkeypatch):
    """Make any urlopen call a hard failure, and record that it happened."""
    calls = []

    def _boom(*a, **k):
        calls.append(a[0] if a else None)
        raise AssertionError("urlopen was called for a rejected URL")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    return calls


@pytest.mark.parametrize("url", BAD_URLS)
def test_daemon_local_alert_webhook_rejects(url, no_urlopen):
    sync = importlib.import_module("clawmetry.sync")
    assert sync._post_local_alert_webhook(url, {"a": 1}) is False
    assert no_urlopen == []


@pytest.mark.parametrize("url", BAD_URLS)
def test_incident_alerts_post_json_rejects(url, no_urlopen):
    ia = importlib.import_module("clawmetry.incident_alerts")
    assert ia._post_json(url, {"a": 1}) is False
    assert no_urlopen == []


@pytest.mark.parametrize("url", BAD_URLS)
def test_dashboard_send_webhook_alert_rejects(url, no_urlopen):
    d = importlib.import_module("dashboard")
    # Returns None either way (best-effort sender); the assertion that matters
    # is that urlopen was never reached.
    d._send_webhook_alert(url, {"message": "x", "type": "test"},
                          payload_type="generic")
    assert no_urlopen == []


def test_http_url_still_reaches_urlopen(monkeypatch):
    """Positive control: the guard must not block a real webhook.

    Without this, a guard that rejected everything would pass every test
    above.
    """
    seen = []

    class _Resp:
        status = 200

        def read(self):
            return b"{}"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _ok(req, *a, **k):
        seen.append(getattr(req, "full_url", req))
        return _Resp()

    monkeypatch.setattr(urllib.request, "urlopen", _ok)

    sync = importlib.import_module("clawmetry.sync")
    assert sync._post_local_alert_webhook(
        "https://hooks.example.com/x", {"a": 1}) is True

    ia = importlib.import_module("clawmetry.incident_alerts")
    assert ia._post_json("https://hooks.example.com/y", {"a": 1}) is True

    assert len(seen) == 2
