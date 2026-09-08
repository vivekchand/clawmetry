"""Regression coverage for the desktop shell's TLS trust bootstrap.

The desktop shell runs as a PyInstaller-frozen binary, so its bundled
Python cannot find a CA bundle unless we ship one. Support screenshot
2026-08-12: "Send code" showed
``[SSL: CERTIFICATE_VERIFY_FAILED] unable to get local issuer
certificate (_ssl.c:1006)`` because ``urllib.request.urlopen`` was
called without an explicit context.

These tests pin the three fallback layers so a future edit to
``desktop/onboarding.py::_ssl_context`` can't silently regress
back to the default-context path that caused the bug.
"""

from __future__ import annotations

import importlib
import ssl
import sys
from pathlib import Path

import pytest


# desktop/ isn't a proper package on the test path (setup.py doesn't
# ship it); make it importable directly.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "desktop") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "desktop"))


@pytest.fixture(autouse=True)
def _reset_ssl_cache():
    """The context is cached at module scope; clear it between tests
    so each one exercises the resolver from scratch."""
    import onboarding  # type: ignore

    onboarding._SSL_CTX = None
    yield
    onboarding._SSL_CTX = None


def test_ssl_context_returns_a_real_context():
    """Whatever fallback path wins, we must return an SSLContext that
    urllib can pass to urlopen — not None, not raising."""
    import onboarding  # type: ignore

    ctx = onboarding._ssl_context()
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_ssl_context_prefers_truststore_when_available(monkeypatch):
    """If truststore is importable, we use it. Prevents a
    "fell through to certifi" regression on Python 3.10+ builds where
    truststore would give us OS trust (incl. enterprise CAs) for free."""
    import onboarding  # type: ignore

    fake_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    class _FakeTruststoreCtx:
        def __new__(cls, *_a, **_kw):
            return fake_ctx

    fake_module = type(sys)("truststore")
    fake_module.SSLContext = _FakeTruststoreCtx  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "truststore", fake_module)

    ctx = onboarding._ssl_context()
    assert ctx is fake_ctx


def test_ssl_context_falls_back_to_certifi_when_no_truststore(monkeypatch):
    """No truststore → we must load certifi's bundle explicitly. A
    context built via ``ssl.create_default_context(cafile=…)`` has
    ``ca_certs`` (via ``get_ca_certs`` — non-empty) sourced from that
    file. This is the guaranteed-frozen-bundle path."""
    import onboarding  # type: ignore

    # Guarantee truststore is not resolvable.
    monkeypatch.setitem(sys.modules, "truststore", None)

    ctx = onboarding._ssl_context()
    assert isinstance(ctx, ssl.SSLContext)
    # Fresh context should have loaded at least one CA.
    assert ctx.get_ca_certs(), "certifi bundle should populate ca_certs"


def test_ssl_context_is_cached(monkeypatch):
    """Two calls return the same object — every OTP request would
    otherwise re-parse the PEM file. Micro-perf that also serves as
    a canary if someone forgets the module-level cache."""
    import onboarding  # type: ignore

    a = onboarding._ssl_context()
    b = onboarding._ssl_context()
    assert a is b


def test_post_email_otp_uses_ssl_context_on_https(monkeypatch):
    """The bug this whole module exists for: the OTP POST must go out
    with an explicit context, not None. Mocks the urlopen boundary so
    we don't touch the network."""
    import onboarding  # type: ignore

    captured: dict = {}

    class _FakeResp:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def read(self): return b'{"ok": true}'

    def _fake_urlopen(req, timeout=None, context=None):
        captured["url"] = req.full_url
        captured["context"] = context
        return _FakeResp()

    monkeypatch.setattr(onboarding.urllib.request, "urlopen", _fake_urlopen)

    ok, msg, raw = onboarding._post_email_otp(
        "send",
        {"email": "someone@example.com"},
        app_base="https://app.example.com",
    )
    assert ok is True
    assert msg == ""
    assert captured["url"].startswith("https://")
    assert isinstance(captured["context"], ssl.SSLContext), (
        "urlopen was called without an SSLContext — the exact bug this "
        "fix exists to prevent"
    )


def test_post_email_otp_skips_context_on_http_loopback(monkeypatch):
    """A self-hosted user pointed at a loopback dev endpoint over
    plain HTTP shouldn't have us build/pass an SSL context (SSL onto
    http:// is a coding error). Verifies the http:// guard rather than
    always attaching a context."""
    import onboarding  # type: ignore

    captured: dict = {}

    class _FakeResp:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def read(self): return b'{"ok": true}'

    def _fake_urlopen(req, timeout=None, context=None):
        captured["url"] = req.full_url
        captured["context"] = context
        return _FakeResp()

    monkeypatch.setattr(onboarding.urllib.request, "urlopen", _fake_urlopen)

    onboarding._post_email_otp(
        "send",
        {"email": "someone@example.com"},
        app_base="http://127.0.0.1:8080",
    )
    assert captured["url"].startswith("http://")
    assert captured["context"] is None
