"""RFC 9116 security contact must be served, and must not be expired.

Served by the dashboard itself, not only the marketing site, so an on-prem or
self-hosted instance can answer "who do I report this to?" — the deployment
where a finder is least likely to know who runs it.
"""
import datetime
import os
import re

import pytest

import clawmetry

SECURITY_TXT = os.path.join(
    os.path.dirname(os.path.abspath(clawmetry.__file__)),
    "static", ".well-known", "security.txt",
)


def _body():
    with open(SECURITY_TXT, encoding="utf-8") as fh:
        return fh.read()


def test_file_ships_with_the_package():
    """Must resolve through the installed package, not a repo-relative path."""
    assert os.path.isfile(SECURITY_TXT)


@pytest.mark.parametrize("field", ["Contact:", "Expires:", "Policy:", "Canonical:"])
def test_required_fields_present(field):
    assert field in _body()


def test_contact_is_reachable_looking():
    """RFC 9116 requires at least one Contact, and it must be a URI."""
    contacts = re.findall(r"^Contact:\s*(\S+)", _body(), re.M)
    assert contacts
    assert all(c.startswith(("mailto:", "https://", "tel:")) for c in contacts)


def test_not_expired():
    """RFC 9116: a security.txt past its Expires must be treated as invalid.

    This test is the renewal alarm. When it fails, bump Expires — do not
    delete the test.
    """
    raw = re.search(r"^Expires:\s*(\S+)", _body(), re.M).group(1)
    expires = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    assert expires > now, f"security.txt expired on {expires.date()} — bump Expires"


def test_expiry_is_not_unreasonably_far_out():
    """An Expires decades away defeats the point of the field."""
    raw = re.search(r"^Expires:\s*(\S+)", _body(), re.M).group(1)
    expires = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    assert (expires - now).days <= 400, "Expires should be within ~a year"


@pytest.fixture(scope="module")
def client():
    """detect_config() registers the blueprints onto the module-level app.

    Same pattern as tests/test_cache_trends.py — the app is not assembled at
    import time, so a bare `dashboard.app.test_client()` sees zero routes.
    """
    import argparse

    import dashboard as _d

    already = any(
        "well-known" in str(rule) for rule in _d.app.url_map.iter_rules()
    )
    if not already:
        # Every attribute detect_config() reads off the namespace; a missing
        # one raises AttributeError rather than defaulting.
        _d.detect_config(
            argparse.Namespace(
                name=None,
                workspace=None,
                openclaw_dir=None,
                data_dir=None,
                log_dir=None,
                sessions_dir=None,
            )
        )
    _d.app.config["TESTING"] = True
    return _d.app.test_client()


def test_served_over_http(client):
    """Unauthenticated by design — a vulnerability reporter has no credential."""
    resp = client.get("/.well-known/security.txt")

    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("text/plain")
    assert "Contact:" in resp.get_data(as_text=True)
