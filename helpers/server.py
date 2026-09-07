"""Server-startup helpers for dashboard.py."""

import ipaddress


def is_loopback_host(host):
    """True only when ``host`` binds the loopback interface alone.

    Decides whether Flask's interactive debugger is safe to switch on.
    Fails closed: anything we cannot positively prove is loopback -- an
    empty value, a hostname we do not resolve, an unparseable literal --
    reads as remote and turns the debugger off.

    Note: ``0.0.0.0`` and ``::`` are NOT loopback; they are wildcard binds
    that include every routable interface on the machine.
    """
    if not host:
        return False
    candidate = str(host).strip()
    if candidate.lower() in ("localhost", "localhost.localdomain"):
        return True
    # An IPv6 literal may arrive bracketed, as [::1].
    if candidate.startswith("[") and candidate.endswith("]"):
        candidate = candidate[1:-1]
    # ...and may carry a zone id, as fe80::1%eth0.
    candidate = candidate.split("%", 1)[0]
    try:
        return ipaddress.ip_address(candidate).is_loopback
    except ValueError:
        # Not an IP literal. We do not resolve hostnames here: a name that
        # resolves to loopback today can resolve elsewhere tomorrow, and DNS
        # is not a thing to trust when the answer decides whether to expose
        # an eval console.
        return False
