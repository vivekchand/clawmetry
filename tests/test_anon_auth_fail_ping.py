"""Tests for the /api/anon-auth-fail-ping endpoint (issue #1365).

The OSS dashboard fires an anonymous funnel-loss ping when /api/auth/check
rejects on first page load. The typo regression in PR #1357 was invisible
to us because no such ping existed; this endpoint is the early-warning
canary for the next regression of that class.

Invariants exercised:
  * Happy path: valid {event, version, user_agent_class} → 200 + line on disk.
  * Strict allowlist on event + UA class + version length → 400 otherwise.
  * PII defence: any token/auth/ip field in the body → 400 *before* the
    record is persisted (regression-test the "never leak" promise).
  * Server stamps ts (no client clock pollution).
  * Cloud-forward failure is swallowed → endpoint still 200s.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import dashboard  # noqa: E402  (registers shared module state)
from routes import meta as meta_mod  # noqa: E402
from routes.meta import bp_auth  # noqa: E402


@pytest.fixture
def log_path(tmp_path, monkeypatch):
    """Redirect the JSONL log to a tmp dir so tests can read it back."""
    p = tmp_path / "anon_events.jsonl"
    monkeypatch.setattr(meta_mod, "_ANON_LOG_PATH", str(p), raising=False)
    return p


@pytest.fixture
def client(monkeypatch, log_path):
    """Flask app with bp_auth + cloud-forward stubbed to a no-op."""
    monkeypatch.setattr(meta_mod, "_anon_forward_cloud", lambda payload: None)
    a = Flask(__name__)
    a.register_blueprint(bp_auth)
    return a.test_client()


def _read_lines(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


# ── happy path + server-stamped ts ─────────────────────────────────────────

def test_happy_path_persists_and_stamps_ts(client, log_path):
    r = client.post(
        "/api/anon-auth-fail-ping",
        json={
            "event": "auth_fail_first_load",
            "version": "0.12.238",
            "user_agent_class": "chrome",
        },
    )
    assert r.status_code == 200, r.get_data(as_text=True)
    assert r.get_json() == {"ok": True}
    lines = _read_lines(log_path)
    assert len(lines) == 1
    rec = lines[0]
    assert rec == {
        "ts": rec["ts"],  # server-stamped; verified below
        "event": "auth_fail_first_load",
        "version": "0.12.238",
        "user_agent_class": "chrome",
    }
    assert isinstance(rec["ts"], int) and rec["ts"] > 0
    # No client-side fields snuck through.
    assert "client_ts" not in rec


# ── strict allowlist on event + UA class + version ─────────────────────────

@pytest.mark.parametrize("body,reason", [
    ({"event": "auth_fail_session_timeout", "version": "0.12.238",
      "user_agent_class": "chrome"}, "unknown event"),
    ({"event": "auth_fail_first_load", "version": "0.12.238",
      "user_agent_class": "opera"}, "unknown UA bucket"),
    ({"event": "auth_fail_first_load", "version": "",
      "user_agent_class": "chrome"}, "missing version"),
    ({"event": "auth_fail_first_load", "version": "x" * 200,
      "user_agent_class": "chrome"}, "oversize version"),
])
def test_rejects_invalid_payloads(client, log_path, body, reason):
    r = client.post("/api/anon-auth-fail-ping", json=body)
    assert r.status_code == 400, f"{reason}: {r.get_data(as_text=True)}"
    assert _read_lines(log_path) == [], reason


def test_rejects_non_object_body(client, log_path):
    r = client.post(
        "/api/anon-auth-fail-ping",
        data=json.dumps([1, 2, 3]),
        content_type="application/json",
    )
    assert r.status_code == 400


# ── PII defence — the "never leak" backstop ────────────────────────────────

@pytest.mark.parametrize("field", [
    "token", "Token", "authorization", "bearer", "password", "ip",
    "remote_addr", "user_id", "email", "session_id", "cookie",
])
def test_rejects_pii_fields(client, log_path, field):
    """If anything ever tries to sneak a token-like field past us, the
    endpoint must 400 *before* persisting the record. Defence in depth
    for the "anonymous only" invariant — the schema check could one day
    silently strip the field; this guarantees it never does."""
    r = client.post(
        "/api/anon-auth-fail-ping",
        json={
            "event": "auth_fail_first_load",
            "version": "0.12.238",
            "user_agent_class": "chrome",
            field: "would-be-leak",
        },
    )
    assert r.status_code == 400, f"field={field} should be rejected"
    assert _read_lines(log_path) == [], f"field={field} leaked to disk"


# ── fail-silent on cloud-forward error ─────────────────────────────────────

def test_cloud_forward_failure_does_not_break_endpoint(monkeypatch, log_path):
    """If cloud endpoint 5xxs / times out / raises, the OSS endpoint must
    still return 200 and still persist the local record. The durable
    signal is the local JSONL; cloud is best-effort display layer."""
    monkeypatch.setattr(
        meta_mod, "_anon_forward_cloud",
        lambda payload: (_ for _ in ()).throw(RuntimeError("cloud is on fire")),
    )
    a = Flask(__name__)
    a.register_blueprint(bp_auth)
    client = a.test_client()
    r = client.post(
        "/api/anon-auth-fail-ping",
        json={
            "event": "auth_fail_first_load",
            "version": "0.12.238",
            "user_agent_class": "chrome",
        },
    )
    assert r.status_code == 200
    assert len(_read_lines(log_path)) == 1
