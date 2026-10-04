"""Scheme guard for outbound, user-configured URLs.

``urllib.request.urlopen`` speaks more than HTTP. It also opens ``file://``
and ``ftp://``, and -- this is the part that surprises people -- a ``file://``
URL is served even when the ``Request`` carries a ``data=`` body, so a
"POST the alert JSON to this webhook" call against ``file:///etc/passwd``
reads the file and reports success. Every webhook URL in ClawMetry comes from
configuration a user (or anything that can reach ``/api/alerts/webhook``)
supplies, so the scheme is untrusted input and has to be checked before the
request is built.

``dashboard._url_safe_for_external_request`` is the fuller policy: it rejects
non-HTTP schemes AND resolves the host to reject loopback / link-local /
private / reserved addresses. This module deliberately carries only the scheme
half, for two reasons:

1. The daemon cannot use the dashboard's copy. ``clawmetry/sync.py`` and
   ``clawmetry/incident_alerts.py`` dispatch webhooks from the sync daemon,
   which never imports the Flask app; a guard they can both reach has to be a
   module with no Flask (and no network) dependency.
2. The address half is not safe to switch on unilaterally. ClawMetry is
   local-first, and pointing a webhook at ``127.0.0.1`` or an internal host is
   a legitimate self-hosted setup -- enforcing the address half here would
   break those users silently. That decision needs an operator-facing switch,
   not a default flip.

Rejecting a non-HTTP scheme breaks nothing real: no webhook receiver has ever
been reachable over ``file://`` or ``ftp://``, so a URL with one of those
schemes was already a misconfiguration at best.
"""

from urllib.parse import urlparse

# The only two schemes a webhook receiver can be reached over.
ALLOWED_SCHEMES = ("http", "https")


def is_http_url(url):
    """Return True only for an ``http://`` / ``https://`` URL with a host.

    Never raises: anything unparseable, empty, non-string, or carrying another
    scheme is False. A missing host is rejected too, since ``http:///x``
    parses but names no receiver.
    """
    try:
        parsed = urlparse(str(url or "").strip())
    except Exception:
        return False
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False
    try:
        return bool(parsed.hostname)
    except Exception:
        # A malformed authority (e.g. a bad IPv6 literal) raises on .hostname.
        return False
