"""Headless OAuth paste-code path for `clawmetry connect`.

The loopback OAuth callback can't reach a CLI on a remote/headless box (the
browser opens on the user's laptop). These pin the headless paste-code fork:
the CLI must use cli_paste mode (not cli_port), redeem via api_call, and never
hang on a timed wait. Desktop loopback must stay unchanged.
"""
import itertools

import pytest

import clawmetry.cli as cli


# ── _is_headless ────────────────────────────────────────────────────────────

def test_is_headless_forced(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_NO_BROWSER", "1")
    assert cli._is_headless() is True


def test_is_headless_false_on_mac(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_NO_BROWSER", raising=False)
    monkeypatch.setattr(cli.sys, "platform", "darwin")
    assert cli._is_headless() is False


def test_is_headless_true_on_linux_ssh(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_NO_BROWSER", raising=False)
    monkeypatch.setattr(cli.sys, "platform", "linux")
    monkeypatch.setenv("SSH_CONNECTION", "1.2.3.4 5 6.7.8.9 22")
    monkeypatch.setenv("DISPLAY", ":0")  # SSH still counts even with a display
    assert cli._is_headless() is True


def test_is_headless_true_on_linux_no_display(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_NO_BROWSER", raising=False)
    monkeypatch.delenv("SSH_CONNECTION", raising=False)
    monkeypatch.delenv("SSH_TTY", raising=False)
    monkeypatch.delenv("SSH_CLIENT", raising=False)
    monkeypatch.setattr(cli.sys, "platform", "linux")
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    assert cli._is_headless() is True


# ── headless paste path ─────────────────────────────────────────────────────

def test_headless_paste_returns_key_uses_cli_paste(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_NO_BROWSER", "1")
    opened = {}
    monkeypatch.setattr("webbrowser.open", lambda u: opened.setdefault("url", u))
    exchanged = {}

    def _api(path, body):
        exchanged["path"] = path
        exchanged["body"] = body
        return {"ok": True, "api_key": "cm_headlesskey0001", "is_new": True}

    key = cli._oauth_browser_login("google", input_fn=lambda _p: "PASTECODE", api_call=_api)
    assert key == "cm_headlesskey0001"
    assert "cli_paste=1" in opened["url"] and "cc=" in opened["url"]
    assert "cli_port" not in opened["url"]
    assert exchanged["path"] == "/api/oauth/cli/exchange"
    assert exchanged["body"]["code"] == "PASTECODE"
    # The verifier sent to exchange must hash to the challenge in the URL (PKCE).
    import hashlib, base64, urllib.parse as up
    cc = up.parse_qs(opened["url"].split("?", 1)[1])["cc"][0]
    v = exchanged["body"]["verifier"]
    recomputed = base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b"=").decode()
    assert recomputed == cc


def test_headless_empty_paste_returns_empty(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_NO_BROWSER", "1")
    monkeypatch.setattr("webbrowser.open", lambda u: None)
    key = cli._oauth_browser_login("github", input_fn=lambda _p: "", api_call=lambda p, b: {})
    assert key == ""  # empty paste -> caller drops to email OTP


def test_headless_bad_code_returns_empty(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_NO_BROWSER", "1")
    monkeypatch.setattr("webbrowser.open", lambda u: None)
    key = cli._oauth_browser_login(
        "github", input_fn=lambda _p: "WRONG",
        api_call=lambda p, b: {"ok": False, "error": "invalid or used code"})
    assert key == ""


# ── desktop loopback unchanged ──────────────────────────────────────────────

def test_desktop_uses_cli_port_not_paste(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_NO_BROWSER", raising=False)
    monkeypatch.setattr(cli, "_is_headless", lambda: False)
    opened = {}
    monkeypatch.setattr("webbrowser.open", lambda u: opened.setdefault("url", u))
    # Make the loopback wait exit immediately (no 180s hang, no token captured).
    ticks = itertools.chain([0.0], itertools.repeat(1e9))
    monkeypatch.setattr("time.time", lambda: next(ticks))
    key = cli._oauth_browser_login("google", input_fn=lambda _p: "", api_call=lambda p, b: {})
    assert key == ""  # no token captured -> falls back to email
    assert "cli_port=" in opened["url"]
    assert "cli_paste" not in opened["url"]


def test_loopback_bind_failure_falls_to_paste(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_NO_BROWSER", raising=False)
    monkeypatch.setattr(cli, "_is_headless", lambda: False)
    import http.server

    def _boom(*a, **k):
        raise OSError("cannot bind")

    monkeypatch.setattr(http.server, "HTTPServer", _boom)
    opened = {}
    monkeypatch.setattr("webbrowser.open", lambda u: opened.setdefault("url", u))
    key = cli._oauth_browser_login(
        "google", input_fn=lambda _p: "CODE",
        api_call=lambda p, b: {"api_key": "cm_fallbackkey", "is_new": False})
    assert key == "cm_fallbackkey"
    assert "cli_paste=1" in opened["url"]  # fell through to the paste path


def test_no_emdash_in_oauth_copy():
    import inspect
    src = inspect.getsource(cli._oauth_browser_login)
    assert "—" not in src and "–" not in src
