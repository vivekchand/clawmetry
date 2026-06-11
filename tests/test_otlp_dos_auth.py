"""Regression guard for the unauthenticated-OTLP + gzip-bomb DoS (cloud #1567).

Two bugs:
 1. `_check_auth` early-returned for any non-`/api/` path, so the OTLP receivers
    at `/v1/metrics|traces|logs` skipped auth entirely -> anyone reachable could
    poison cost/usage analytics.
 2. `_otlp_decode` did unbounded `gzip.decompress`, and the app set no
    `MAX_CONTENT_LENGTH` -> a few-KB gzip bomb OOM'd the daemon.

Fix: gate `/v1/*` like `/api/*` (loopback trusted, non-loopback needs the
gateway token, opt out with CLAWMETRY_OTLP_ALLOW_UNAUTH=1); bound gzip output
with `_gunzip_bounded`; set `MAX_CONTENT_LENGTH`.
"""
import gzip
import importlib
import io

import pytest

dashboard = importlib.import_module("dashboard")


def _gz(b):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as f:
        f.write(b)
    return buf.getvalue()


# ── gzip-bomb bound ────────────────────────────────────────────────────────

def test_gunzip_bounded_allows_normal_payload():
    raw = b"hello world " * 100
    assert dashboard._gunzip_bounded(_gz(raw)) == raw


def test_gunzip_bounded_rejects_bomb():
    bomb = _gz(b"\x00" * (4 * 1024 * 1024))  # 4 MB decompressed from a tiny blob
    with pytest.raises(ValueError):
        dashboard._gunzip_bounded(bomb, limit=64 * 1024)  # 64 KB cap


def test_max_content_length_is_capped():
    mcl = dashboard.app.config.get("MAX_CONTENT_LENGTH")
    assert mcl and mcl > 0


# ── OTLP auth gate ─────────────────────────────────────────────────────────

def test_otlp_rejected_from_network_without_token(monkeypatch):
    monkeypatch.setattr(dashboard, "GATEWAY_TOKEN", "secret-token", raising=False)
    monkeypatch.delenv("CLAWMETRY_OTLP_ALLOW_UNAUTH", raising=False)
    with dashboard.app.test_request_context(
        "/v1/metrics", method="POST", environ_base={"REMOTE_ADDR": "203.0.113.9"}
    ):
        rv = dashboard._check_auth()
        assert rv is not None, "OTLP from the network must not be allowed unauthenticated"
        assert rv[1] == 401


def test_otlp_allowed_from_loopback(monkeypatch):
    monkeypatch.setattr(dashboard, "GATEWAY_TOKEN", "secret-token", raising=False)
    with dashboard.app.test_request_context(
        "/v1/metrics", method="POST", environ_base={"REMOTE_ADDR": "127.0.0.1"}
    ):
        assert dashboard._check_auth() is None  # zero-config local exporters keep working


def test_otlp_allowed_with_explicit_optout(monkeypatch):
    monkeypatch.setattr(dashboard, "GATEWAY_TOKEN", "secret-token", raising=False)
    monkeypatch.setenv("CLAWMETRY_OTLP_ALLOW_UNAUTH", "1")
    with dashboard.app.test_request_context(
        "/v1/metrics", method="POST", environ_base={"REMOTE_ADDR": "203.0.113.9"}
    ):
        assert dashboard._check_auth() is None


def test_otlp_allowed_from_network_with_valid_token(monkeypatch):
    monkeypatch.setattr(dashboard, "GATEWAY_TOKEN", "secret-token", raising=False)
    monkeypatch.delenv("CLAWMETRY_OTLP_ALLOW_UNAUTH", raising=False)
    with dashboard.app.test_request_context(
        "/v1/metrics", method="POST",
        headers={"Authorization": "Bearer secret-token"},
        environ_base={"REMOTE_ADDR": "203.0.113.9"},
    ):
        assert dashboard._check_auth() is None
