"""The gateway WS tap recovers from a rotated gateway token, by itself.

Field report 2026-09-09 (Steven M. Alper): after a gateway restart the tap
logged `token_mismatch` "every minute indefinitely" and the user expected to
have to reinstall. Cause: ``clawmetry/gateway_tap.py`` resolved the token once
in ``start()``, cached it on the ``GatewayTap`` instance, and ``_run_once``
replayed that dead credential on every reconnect. Nothing ever re-read the
config. The 60s cadence is ``_BACKOFF_MAX_SEC``. Only a *daemon* restart
re-read the file, which is why "the restart didn't fix it" — restarting the
app does not restart the daemon.

Deliberately separate from ``tests/test_gateway_tap.py``: that suite drives a
real DuckDB store, so it needs duckdb and it is sensitive to what other suites
did to ``local_store`` first. Nothing here writes a row, so a tiny fake store
is enough and this file runs in the lint job — fast, hermetic, order-independent.

The two rejection payloads below were captured VERBATIM off a live OpenClaw
gateway on 127.0.0.1:18789 (2026-09-10), not invented. That matters: for a bad
token the top-level ``code`` is the generic ``INVALID_REQUEST``, and the
machine-readable reason sits one level down in ``error.details``. Classifying
on the prose alone works today and breaks the first time upstream rewords it.
"""

from __future__ import annotations

import importlib
import json
import logging
import sys

import pytest


@pytest.fixture
def gw(tmp_path, monkeypatch):
    """Freshly-imported tap module pointed at a private fake ~/.openclaw."""
    oc_home = tmp_path / "openclaw"
    oc_home.mkdir()
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(oc_home))
    monkeypatch.delenv("OPENCLAW_GATEWAY_TOKEN", raising=False)
    monkeypatch.delenv("OPENCLAW_GATEWAY_PORT", raising=False)

    import clawmetry.gateway_tap as gateway_tap
    importlib.reload(gateway_tap)
    gateway_tap._oc_home = oc_home  # convenience handle for the tests
    return gateway_tap


class _NullStore:
    """The tap only ever writes through these two; nothing here writes."""

    def ingest_events(self, *a, **k):
        pass

    def ingest_channel_message(self, *a, **k):
        pass


def _write_gw_config(oc_home, token, port=18789):
    (oc_home / "openclaw.json").write_text(json.dumps({
        "gateway": {"port": port, "auth": {"token": token}},
    }))


def _tap(gw, token="cached-at-daemon-start", url="ws://127.0.0.1:18789"):
    return gw.GatewayTap(url=url, token=token, store=_NullStore(), node_id="n")


# ── Captured off the live gateway ───────────────────────────────────────

#: `connect` with a wrong token.
_LIVE_BAD_TOKEN_ERROR = {
    "code": "INVALID_REQUEST",
    "message": (
        "unauthorized: gateway token mismatch (use this gateway's "
        "gateway.auth.token or pair the device)"
    ),
    "details": {
        "code": "AUTH_TOKEN_MISMATCH",
        "authReason": "token_mismatch",
        "canRetryWithDeviceToken": False,
        "recommendedNextStep": "update_auth_credentials",
    },
}

#: `connect` with no `auth` block at all.
_LIVE_NO_TOKEN_ERROR = {
    "code": "NOT_PAIRED",
    "message": "device identity required",
    "details": {"code": "DEVICE_IDENTITY_REQUIRED"},
}


# ── 1. Classification ───────────────────────────────────────────────────


def test_auth_rejection_is_classified_from_the_real_wire(gw):
    """The live gateway's bad-token rejection must read as a credential
    failure — and must do so on `details`, not on the prose."""
    assert gw._is_auth_rejection(_LIVE_BAD_TOKEN_ERROR)
    assert gw._is_auth_rejection(_LIVE_NO_TOKEN_ERROR)

    details_only = {
        "code": "INVALID_REQUEST",
        "details": dict(_LIVE_BAD_TOKEN_ERROR["details"]),
    }
    assert gw._is_auth_rejection(details_only), (
        "classification must not depend on the human-readable sentence"
    )

    # Older builds / other gateways: prose, no details.
    assert gw._is_auth_rejection({"message": "Token mismatch"})
    assert gw._is_auth_rejection({"code": "UNAUTHORIZED"})
    assert gw._is_auth_rejection({"message": "invalid token supplied"})


def test_a_busy_gateway_is_not_an_auth_failure(gw):
    """If everything counted as a credential failure we would re-read the
    config on every ordinary blip and reset the backoff, hammering a
    gateway that is merely unhealthy."""
    assert not gw._is_auth_rejection({"code": "protocol-mismatch"})
    assert not gw._is_auth_rejection({"message": "server is shutting down"})
    assert not gw._is_auth_rejection({})
    assert not gw._is_auth_rejection(None)


def test_we_quote_the_gateways_own_next_step(gw):
    """The gateway tells us what to do (`recommendedNextStep`). Quoting it
    beats inventing our own advice in a log line."""
    assert gw._auth_next_step(_LIVE_BAD_TOKEN_ERROR) == "update_auth_credentials"
    assert gw._auth_next_step(
        {"details": {"authReason": "token_mismatch"}}
    ) == "token_mismatch"
    assert gw._auth_next_step(_LIVE_NO_TOKEN_ERROR) == ""
    assert gw._auth_next_step({}) == ""
    assert gw._auth_next_step(None) == ""


# ── 2. Credential refresh ───────────────────────────────────────────────


def test_refresh_picks_up_a_rotated_token(gw):
    """The core fix: a token rotated on disk is adopted."""
    oc_home = gw._oc_home
    _write_gw_config(oc_home, "old-token")
    tap = _tap(gw, token="old-token")

    assert tap._refresh_credentials() is False, "unchanged token → no churn"

    _write_gw_config(oc_home, "new-token")
    assert tap._refresh_credentials() is True
    assert tap.token == "new-token"
    assert tap.token_reloads == 1


def test_refresh_follows_a_moved_port(gw):
    """A gateway that comes back on a different port is followed too."""
    _write_gw_config(gw._oc_home, "t", port=19999)
    tap = _tap(gw)
    assert tap._refresh_credentials() is True
    assert tap.url == "ws://127.0.0.1:19999"


def test_refresh_never_clears_a_working_token(gw):
    """`openclaw doctor --fix` swaps the config file out from under us; a
    read landing mid-swap must not downgrade a working tap to anonymous —
    that turns a recoverable blip into a silent permanent degrade."""
    tap = _tap(gw, token="still-good")
    # No config file at all → _detect_gateway_endpoint returns (None, None).
    assert tap._refresh_credentials() is False
    assert tap.token == "still-good"


# ── 3. The loop ─────────────────────────────────────────────────────────


class _RejectingWS:
    """Answers every `connect` with the live gateway's bad-token error."""

    def __init__(self, seen=None):
        self.sent = []
        self.seen = seen if seen is not None else []

    def settimeout(self, _t):
        pass

    def send(self, payload):
        self.sent.append(payload)

    def recv(self):
        if not self.sent:
            raise ConnectionError("stub: nothing sent yet")
        msg = json.loads(self.sent[-1])
        self.seen.append((msg.get("params", {}).get("auth") or {}).get("token"))
        return json.dumps({
            "type": "res", "id": msg["id"], "ok": False,
            "error": _LIVE_BAD_TOKEN_ERROR,
        })

    def close(self):
        pass


def _install_fake_websocket(monkeypatch, factory):
    class _Mod:
        def create_connection(self, _url, timeout=None):
            return factory()

    monkeypatch.setitem(sys.modules, "websocket", _Mod())


def test_connect_rejection_raises_gateway_auth_error(gw, monkeypatch):
    """A rejected connect that blames the token surfaces as
    ``GatewayAuthError`` so ``_run`` knows re-reading the config could help.
    A plain RuntimeError would just sleep and replay the dead credential."""
    _install_fake_websocket(monkeypatch, _RejectingWS)
    tap = _tap(gw, token="stale")
    with pytest.raises(gw.GatewayAuthError) as excinfo:
        tap._run_once()
    # The message must carry the gateway's own remediation, not ours.
    assert "update_auth_credentials" in str(excinfo.value)


def test_the_loop_recovers_when_the_token_rotates(gw, monkeypatch):
    """End to end for the reported bug: the tap holds a dead token, the
    user's config now carries the new one — it must adopt it and present it
    WITHOUT a daemon restart."""
    _write_gw_config(gw._oc_home, "rotated-token")
    presented: list[str] = []

    class _ScriptedWS(_RejectingWS):
        def recv(self):
            if not self.sent:
                raise ConnectionError("stub: nothing sent yet")
            msg = json.loads(self.sent[-1])
            token = (msg.get("params", {}).get("auth") or {}).get("token")
            presented.append(token)
            if token != "rotated-token":
                return json.dumps({
                    "type": "res", "id": msg["id"], "ok": False,
                    "error": _LIVE_BAD_TOKEN_ERROR,
                })
            raise ConnectionError("accepted, then the stub closes")

    _install_fake_websocket(monkeypatch, _ScriptedWS)
    tap = _tap(gw, token="dead-token")
    try:
        tap._run_once()
    except Exception:  # noqa: BLE001 — the stub closes to end the attempt
        pass

    assert presented and presented[-1] == "rotated-token", (
        "the tap must present the token currently on disk, not the one it "
        "cached at daemon start — otherwise the user reinstalls to recover"
    )
    assert tap.token == "rotated-token"
    assert tap.token_reloads == 1


def test_a_repeating_rejection_is_stated_once_not_every_minute(gw, monkeypatch, caplog):
    """The user-visible half of the report: "misfiring every minute". The
    first rejection is a loud, actionable WARNING; identical repeats drop to
    DEBUG so the daemon log stays readable."""
    _write_gw_config(gw._oc_home, "same-stale-token")
    tap = _tap(gw, token="same-stale-token")
    calls = {"n": 0}

    def _always_reject():
        calls["n"] += 1
        if calls["n"] > 3:
            tap._stop.set()
            return
        raise gw.GatewayAuthError("gateway connect rejected: token_mismatch")

    monkeypatch.setattr(tap, "_run_once", _always_reject)
    monkeypatch.setattr(gw, "_BACKOFF_INITIAL_SEC", 0.0)
    monkeypatch.setattr(gw, "_BACKOFF_MAX_SEC", 0.0)

    with caplog.at_level(logging.DEBUG, logger="clawmetry-sync"):
        tap._run()

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1, (
        "expected exactly one WARNING for a repeating rejection, got "
        f"{[r.getMessage() for r in warnings]}"
    )
    assert "no reinstall needed" in warnings[0].getMessage()
    assert tap.auth_failures == 3


def test_a_successful_connect_resets_the_failure_counter(gw, monkeypatch):
    """So the NEXT outage gets its own loud warning rather than inheriting
    the previous one's silence."""
    tap = _tap(gw)
    tap.auth_failures = 7

    class _AcceptingWS(_RejectingWS):
        def recv(self):
            if not self.sent:
                raise ConnectionError("stub: nothing sent yet")
            msg = json.loads(self.sent[-1])
            if msg.get("method") == "connect":
                return json.dumps({
                    "type": "res", "id": msg["id"], "ok": True,
                    "payload": {"auth": {"scopes": ["operator.read"]}},
                })
            raise ConnectionError("stub: end of script")

    _install_fake_websocket(monkeypatch, _AcceptingWS)
    try:
        tap._run_once()
    except Exception:  # noqa: BLE001 — the stub closes to end the attempt
        pass
    assert tap.auth_failures == 0
