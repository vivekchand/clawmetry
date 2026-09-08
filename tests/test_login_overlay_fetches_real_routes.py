"""Every relative URL ``auth-bootstrap.js`` fetches must be a real route.

The login overlay's "Continue with email" button POSTed to
``/api/auth/email-otp`` for months. That path exists — on
``https://ingest.clawmetry.com``, where the CLI and the desktop pane call
it. Written as a relative URL in browser JS it resolved against the local
dashboard, which serves no such route, so Flask returned a 404 HTML page,
``r.json()`` threw, and the ``.catch`` painted "Network error. Try again."
Email sign-in was dead on every install and nothing objected, because no
test connects the frontend's URLs to the backend's ``url_map``.

This canary closes that loop for the file that carries the whole sign-in
wall. It is static: no server, no fixtures, just the JS source and the
blueprints that own the routes it calls.
"""

from __future__ import annotations

import os
import re
import sys

from flask import Flask

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_JS = os.path.join(_REPO_ROOT, "clawmetry", "static", "js", "auth-bootstrap.js")

#: Blueprints that own the routes auth-bootstrap.js calls. Registering the
#: real ones (rather than hardcoding a path list) keeps the assertion honest
#: when a route is renamed or moved.
_BLUEPRINT_IMPORTS = (
    ("routes.meta", "bp_auth"),
    ("routes.meta", "bp_version"),
    ("routes.overview", "bp_overview"),
)

#: fetch('/api/…') with a single- or double-quoted literal first argument.
#: Template-built URLs (backticks, concatenation) are skipped — this checks
#: the constant paths, which is where the 404 lived.
_FETCH_RE = re.compile(r"""fetch\(\s*(['"])(/[^'"]*)\1""")


def _served_rules() -> set[str]:
    app = Flask(__name__)
    for module, name in _BLUEPRINT_IMPORTS:
        mod = __import__(module, fromlist=[name])
        app.register_blueprint(getattr(mod, name))
    return {str(r.rule) for r in app.url_map.iter_rules()}


def test_every_literal_fetch_path_is_registered():
    src = open(_JS, encoding="utf-8").read()
    # Strip the query string: '/api/auth/check' is fetched as
    # '/api/auth/check' + '?token=…', so the literal is already bare, but a
    # future caller may inline one.
    paths = {m.group(2).split("?", 1)[0] for m in _FETCH_RE.finditer(src)}
    assert paths, "no literal fetch() paths found — did the regex go stale?"

    served = _served_rules()
    missing = sorted(p for p in paths if p not in served)
    assert not missing, (
        "auth-bootstrap.js fetches paths the dashboard does not serve: "
        f"{missing}. Either the route is missing, or it lives on a blueprint "
        "not listed in _BLUEPRINT_IMPORTS (add it), or the JS meant to call "
        "a CLOUD endpoint and must use an absolute URL / a local proxy."
    )


def _fn(src: str, name: str) -> str:
    """Source of one top-level function in the JS file."""
    start = src.index("function %s(" % name)
    return src[start:src.index("\nfunction ", start + 1)]


def test_email_signin_uses_the_local_cloud_cta_proxy():
    """Regression pin: the email flow must go through the local proxy pair,
    not straight at the cloud. /api/cloud-cta/verify-otp persists the cm_ key
    and pairs the machine; a direct browser call to the cloud would set a
    cookie and leave this machine unpaired."""
    src = open(_JS, encoding="utf-8").read()
    assert "/api/cloud-cta/send-otp" in _fn(src, "clawmetryEmailOtpSend")
    assert "/api/cloud-cta/verify-otp" in _fn(src, "clawmetryEmailOtpVerify")
    assert "/api/auth/email-otp" not in _fn(src, "clawmetryEmailOtpSend"), (
        "/api/auth/email-otp is a cloud-only route; it 404s on the local "
        "dashboard and surfaces as a bogus 'Network error'."
    )


def test_email_signin_probes_the_rail_before_pairing():
    """Signing in must not flip cloud egress on by itself.

    /api/cloud-cta/verify-otp pairs the machine, and its managed rail calls
    enable_cloud(). The OAuth button on the same card already probes
    /api/cloud-cta/status and sends mode=selfhost on a local-only machine;
    the email path has to make the same probe or a self-hosted install that
    signs back in starts pushing snapshots.
    """
    body = _fn(open(_JS, encoding="utf-8").read(), "clawmetryEmailOtpVerify")
    assert "/api/cloud-cta/status" in body
    assert "'selfhost'" in body and "'managed'" in body


def test_email_signin_never_opens_a_blocking_dialog():
    """The steps render inside the card. window.prompt() freezes the whole
    pywebview shell, which has no browser chrome to recover with, and asking
    a first-time user for their email in a raw JS dialog is not a thing we
    do."""
    src = open(_JS, encoding="utf-8").read()
    for name in ("clawmetryEmailOtpStart", "clawmetryEmailOtpSend",
                 "clawmetryEmailOtpVerify"):
        assert "prompt(" not in _fn(src, name), name


def test_card_carries_the_elements_the_flow_drives():
    """The JS reaches for these ids by hand; a rename in the template with no
    matching rename here is a silently dead button."""
    html = open(
        os.path.join(_REPO_ROOT, "clawmetry", "templates", "partials",
                     "overlays.html"),
        encoding="utf-8",
    ).read()
    for el in ("login-choices", "login-email-step", "login-email-input",
               "login-email-send", "login-otp-step", "login-otp-input",
               "login-otp-verify", "login-otp-sent", "login-email-back",
               "login-error", "login-local-btn"):
        assert 'id="%s"' % el in html, el
