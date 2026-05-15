"""Tests for the CLI startup banner — one-click /auth?token URL (#1356 PR-D).

The dashboard's `_run_server` foreground banner should print a
clickable /auth?token=... URL when ``GATEWAY_TOKEN`` was successfully
detected, and stay silent (preserving the legacy banner) when it was not.

We test the small extracted helper ``dashboard._print_login_url_banner``
directly so the tests don't have to spin up the whole Flask server.
"""
import os
import sys

import pytest

# Ensure repo root is importable when pytest is invoked from anywhere.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import dashboard  # noqa: E402


def test_login_url_printed_when_token_set(capsys):
    """When GATEWAY_TOKEN is detected, banner prints /auth?token=... URL."""
    dashboard._print_login_url_banner(8900, "127.0.0.1", "63d3b12b" + "a" * 56)
    out = capsys.readouterr().out
    assert "/auth?token=63d3b12b" in out
    assert "http://127.0.0.1:8900/auth?token=" in out
    assert "one-click sign-in" in out


def test_no_url_printed_when_token_missing(capsys):
    """No GATEWAY_TOKEN -> no login URL line (preserves legacy behavior)."""
    dashboard._print_login_url_banner(8900, "127.0.0.1", None)
    dashboard._print_login_url_banner(8900, "127.0.0.1", "")
    out = capsys.readouterr().out
    assert "/auth?token" not in out
    assert out == ""


def test_public_bind_shows_localhost_for_safety(capsys):
    """--host 0.0.0.0 still prints a URL, but framed as localhost so the
    one-click link only works from the local machine (not the LAN)."""
    dashboard._print_login_url_banner(8900, "0.0.0.0", "secret-token-xyz")
    out = capsys.readouterr().out
    assert "http://localhost:8900/auth?token=secret-token-xyz" in out
    assert "0.0.0.0" not in out


def test_bare_token_never_printed_alone(capsys):
    """Defense-in-depth: the bare token MUST always appear inside the URL,
    never on its own line. Shoulder-surfing screenshots are easier to
    parse when a token sits alone."""
    token = "supersecrettokenvalue1234567890"
    dashboard._print_login_url_banner(8900, "127.0.0.1", token)
    out = capsys.readouterr().out
    # Token appears exactly once, embedded in the URL query string.
    assert out.count(token) == 1
    assert f"token={token}" in out
    # And there is no naked line that is just the token.
    for line in out.splitlines():
        assert line.strip() != token


def test_custom_port_respected(capsys):
    """Banner uses the actual port the dashboard is bound to."""
    dashboard._print_login_url_banner(9000, "localhost", "abc123")
    out = capsys.readouterr().out
    assert "http://localhost:9000/auth?token=abc123" in out


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
