"""The Werkzeug debugger may only come up on a loopback bind.

## The exposure (pre-fix)

``dashboard.py::main`` ran ``app.run(..., debug=True, ...)`` whenever
``args.debug`` was set — and ``--debug`` **defaults to True** (opt out with
``--no-debug``). ``--host`` defaults to ``127.0.0.1``, so the common case was
fine, but nothing tied the two together. A user who passed ``--host 0.0.0.0``
to reach the dashboard from another machine — which the startup banner
actively advertises, printing both a LAN and a "Public" URL — also published
Flask's interactive debugger to every interface.

That page hands any client that triggers an unhandled exception the full
traceback, the source around each frame, and every local variable in scope,
plus a PIN-gated eval console. The PIN keeps it from being trivial remote
code execution, but the source and locals disclosure needs no PIN at all,
and neither is something a user asked for by typing ``--host``.

## The fix (this PR)

``_is_loopback_host`` decides whether the bind is loopback-only, and the
debugger is enabled only when it is. The reloader — the part dev mode is
actually wanted for — stays on either way, so ``--host 0.0.0.0`` keeps
working exactly as before minus the debugger, and prints a note saying so.

The helper fails closed: anything it cannot prove is loopback counts as
remote. It deliberately does not resolve hostnames — a name that points at
loopback today can point elsewhere tomorrow, and DNS should not be what
decides whether an eval console is reachable.

## Scenarios

1. Loopback literals and ``localhost`` → debugger allowed.
2. Wildcard binds (``0.0.0.0``, ``::``) → debugger refused. This is the
   regression that matters: a wildcard is not loopback.
3. Routable addresses and hostnames → debugger refused.
4. Junk, empty, and ``None`` → debugger refused (fail closed).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dashboard  # noqa: E402


LOOPBACK = [
    "127.0.0.1",
    "127.0.0.53",  # the whole 127/8 block is loopback, not just .1
    "localhost",
    "LocalHost",  # case must not matter
    "  127.0.0.1  ",  # surrounding whitespace must not matter
    "::1",
    "[::1]",  # bracketed IPv6 literal
    "::1%lo0",  # zone id
]

NOT_LOOPBACK = [
    "0.0.0.0",  # wildcard — every interface, the actual exposure
    "::",  # IPv6 wildcard
    "[::]",
    "192.168.1.10",  # LAN
    "10.0.0.5",
    "203.0.113.7",  # routable
    "example.com",  # hostname — never resolved, always refused
    "localhost.evil.test",  # must not match on a "localhost" prefix
    "not-an-ip",
    "",
    "   ",
    None,
]


@pytest.mark.parametrize("host", LOOPBACK)
def test_loopback_hosts_allow_debugger(host):
    assert dashboard._is_loopback_host(host) is True, (
        f"{host!r} is loopback; the debugger should be allowed"
    )


@pytest.mark.parametrize("host", NOT_LOOPBACK)
def test_non_loopback_hosts_refuse_debugger(host):
    assert dashboard._is_loopback_host(host) is False, (
        f"{host!r} is not loopback; the debugger must stay off"
    )


def test_wildcard_bind_is_not_loopback():
    """The specific case this change exists for.

    ``--host 0.0.0.0`` with the default ``--debug`` used to serve the
    debugger on every interface.
    """
    assert dashboard._is_loopback_host("0.0.0.0") is False


def test_helper_never_raises_on_hostile_input():
    """Bad input must fail closed, not crash the server on startup."""
    for junk in ["", "   ", None, "::::::", "999.999.999.999", "[", "]", "%", 12345]:
        assert dashboard._is_loopback_host(junk) is False
