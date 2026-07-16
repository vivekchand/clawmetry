"""Tests for the license.activate / license.deactivate audit producers.

Pins the contract that every license state change records an entry in
``clawmetry.audit``:

* a successful activation records ``license.activate`` with ``result=activated``
* an invalid / expired / write-failed activation records the failure
* a deactivation records ``license.deactivate`` with prior tier/sub metadata
* the raw license key is NEVER written to the audit log
* an audit-write failure NEVER breaks the activate / deactivate path

Hermetic: each test uses an ephemeral Ed25519 keypair (so the embedded
production public key is never trusted) and points ``CLAWMETRY_AUDIT_DB``
at a tmp_path file, so no real filesystem state is touched.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest


def _keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    priv = Ed25519PrivateKey.generate()
    pub_pem = priv.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv, pub_pem


def _payload(tier="pro", nodes=4, exp_delta=365 * 86400, sub="acct_test"):
    now = int(time.time())
    return {
        "sub": sub,
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
        "features": ["runtimes"],
    }


@pytest.fixture
def lic(monkeypatch, tmp_path):
    """Hermetic license fixture: ephemeral keypair, tmp license path, tmp
    audit DB. Mirrors the fixture in test_license.py / test_license_api.py
    so behavioural pins stay symmetric.

    Also isolates the entitlements module's resolver state -- some other
    tests in the suite ``importlib.reload(clawmetry.entitlements)`` after
    pointing ``HOME`` at a tmp_path and write a ``cloud_plan.json`` into
    it. pytest keeps the last few tmp_path roots, so the module-level
    ``_CLOUD_PLAN_CACHE`` constant can still resolve to a real file with
    a paid ``plan`` value when this fixture runs later in the session.
    Anchoring it (and ``_LICENSE_PATH``) at the per-test tmp_path makes
    deactivate-then-resolve correctly fall back to OSS regardless of
    cross-test leakage, and the in-process resolver cache is busted both
    on entry and exit."""
    import clawmetry.license as L
    import clawmetry.audit as A
    import clawmetry.entitlements as e

    priv, pub_pem = _keypair()
    monkeypatch.setattr(L, "_PUBLIC_KEY_PEM", pub_pem)
    monkeypatch.setattr(L, "LICENSE_PATH", str(tmp_path / "license.key"))
    monkeypatch.setattr(L, "_CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.delenv("CLAWMETRY_LICENSE_SERVER", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    # activate() phones home to the default cloud base now — keep audit tests
    # hermetic (no network) via the explicit offline opt-out.
    monkeypatch.setenv("CLAWMETRY_OFFLINE", "1")
    # Point the entitlements resolver at the same tmp paths so a leaked
    # cloud_plan.json from another test can't override the deactivate path.
    monkeypatch.setattr(e, "_LICENSE_PATH", str(tmp_path / "license.key"))
    monkeypatch.setattr(e, "_CLOUD_PLAN_CACHE", str(tmp_path / "cloud_plan.json"))
    e.invalidate()
    # Point the audit DB at a per-test file and reset the "initialised" guard
    # so the schema is rebuilt against the fresh DB.
    monkeypatch.setenv("CLAWMETRY_AUDIT_DB", str(tmp_path / "audit.db"))
    A._initialised.clear()
    yield SimpleNamespace(L=L, A=A, priv=priv)
    e.invalidate()


def _audit_rows(A, event_type: str | None = None) -> list[dict]:
    return A.read_audit_log(limit=50, event_type=event_type)


# ── activate audit producer ────────────────────────────────────────────────────


def test_activate_success_records_audit(lic):
    tok = lic.L._encode_token(_payload("pro", nodes=11, sub="acct_42"), lic.priv)
    ok, _msg = lic.L.activate(tok)
    assert ok is True

    rows = _audit_rows(lic.A, "license.activate")
    assert len(rows) == 1
    r = rows[0]
    assert r["event_type"] == "license.activate"
    assert r["target"] == "acct_42"
    assert r["details"]["result"] == "activated"
    assert r["details"]["source"] == "license"
    assert r["details"]["tier"] == "pro"
    assert r["details"]["nodes"] == 11
    assert "exp" in r["details"]


def test_activate_invalid_key_records_audit(lic):
    ok, _msg = lic.L.activate("CLAW1.not.a.real.token")
    assert ok is False

    rows = _audit_rows(lic.A, "license.activate")
    assert len(rows) == 1
    assert rows[0]["details"]["result"] == "invalid_key"
    # No payload claims surface for an unverifiable key — only the failure.
    assert "tier" not in rows[0]["details"]


def test_activate_expired_key_records_audit(lic):
    tok = lic.L._encode_token(
        _payload(exp_delta=-3600, sub="acct_expired"), lic.priv,
    )
    ok, _msg = lic.L.activate(tok)
    assert ok is False

    rows = _audit_rows(lic.A, "license.activate")
    assert len(rows) == 1
    assert rows[0]["details"]["result"] == "expired_key"
    # Expired keys still verified — non-secret claims surface so the operator
    # can see WHICH key expired (audit log doesn't depend on the file write).
    assert rows[0]["target"] == "acct_expired"
    assert rows[0]["details"]["tier"] == "pro"


def test_activate_does_not_log_raw_key(lic):
    """The CLAW1.…sig… token MUST NOT appear anywhere in the audit details."""
    tok = lic.L._encode_token(_payload("pro", sub="acct_secret"), lic.priv)
    ok, _msg = lic.L.activate(tok)
    assert ok is True

    rows = _audit_rows(lic.A, "license.activate")
    assert len(rows) == 1
    import json as _json
    blob = _json.dumps(rows[0])
    assert "CLAW1" not in blob
    assert tok not in blob
    # Best-effort: also assert the b64 signature segment isn't accidentally logged.
    _prefix, _body, sig_seg = tok.split(".")
    assert sig_seg not in blob


def test_activate_records_actor_when_provided(lic):
    tok = lic.L._encode_token(_payload(), lic.priv)
    ok, _msg = lic.L.activate(tok, actor="alice@example.com")
    assert ok is True

    rows = _audit_rows(lic.A, "license.activate")
    assert len(rows) == 1
    assert rows[0]["actor"] == "alice@example.com"


def test_activate_audit_failure_does_not_break_activation(lic, monkeypatch):
    """If audit_event throws, activate() MUST still succeed — the audit
    write is best-effort and never load-bearing for the entitlement flow."""
    import clawmetry.audit as A

    def _explode(*_a, **_kw):
        raise RuntimeError("audit DB unreachable")

    monkeypatch.setattr(A, "audit_event", _explode)

    tok = lic.L._encode_token(_payload(), lic.priv)
    ok, msg = lic.L.activate(tok)
    assert ok is True
    assert "pro" in msg.lower()


# ── deactivate audit producer ──────────────────────────────────────────────────


def test_deactivate_removes_and_records_audit(lic):
    tok = lic.L._encode_token(_payload("pro", nodes=2, sub="acct_dx"), lic.priv)
    lic.L.activate(tok)

    # Reset the audit DB read so the deactivate event is the only row.
    lic.A._initialised.clear()
    import os
    if os.path.isfile(os.environ["CLAWMETRY_AUDIT_DB"]):
        os.remove(os.environ["CLAWMETRY_AUDIT_DB"])
    lic.A._initialised.clear()

    ok, removed = lic.L.deactivate()
    assert ok is True
    assert removed is True
    assert not os.path.isfile(lic.L.LICENSE_PATH)

    rows = _audit_rows(lic.A, "license.deactivate")
    assert len(rows) == 1
    r = rows[0]
    assert r["details"]["result"] == "removed"
    assert r["details"]["source"] == "license"
    # Prior tier/sub surface so the audit reader knows WHICH license was removed.
    assert r["target"] == "acct_dx"
    assert r["details"]["tier"] == "pro"
    assert r["details"]["nodes"] == 2


def test_deactivate_noop_when_no_license(lic):
    ok, removed = lic.L.deactivate()
    assert ok is True
    assert removed is False

    rows = _audit_rows(lic.A, "license.deactivate")
    assert len(rows) == 1
    assert rows[0]["details"]["result"] == "noop"
    # No prior license, so no tier/sub surfaces.
    assert rows[0]["target"] == ""
    assert "tier" not in rows[0]["details"]


def test_deactivate_records_actor(lic):
    tok = lic.L._encode_token(_payload(), lic.priv)
    lic.L.activate(tok)

    ok, removed = lic.L.deactivate(actor="cli")
    assert ok is True
    assert removed is True

    rows = _audit_rows(lic.A, "license.deactivate")
    assert len(rows) == 1
    assert rows[0]["actor"] == "cli"


def test_deactivate_audit_failure_does_not_break_removal(lic, monkeypatch):
    import clawmetry.audit as A
    import os

    tok = lic.L._encode_token(_payload(), lic.priv)
    lic.L.activate(tok)

    def _explode(*_a, **_kw):
        raise RuntimeError("audit DB unreachable")

    monkeypatch.setattr(A, "audit_event", _explode)

    ok, removed = lic.L.deactivate()
    assert ok is True
    assert removed is True
    assert not os.path.isfile(lic.L.LICENSE_PATH)


def test_deactivate_clears_entitlement_cache(lic, monkeypatch):
    """The deactivate path MUST invalidate() the entitlement cache so the
    Free fallback takes effect on the next request — equivalent to the
    behaviour the pre-refactor route had inline."""
    import clawmetry.entitlements as e

    monkeypatch.setattr(e, "_LICENSE_PATH", lic.L.LICENSE_PATH)
    tok = lic.L._encode_token(_payload("pro"), lic.priv)
    lic.L.activate(tok)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    e.invalidate()
    assert e.get_entitlement(force=True).is_paid is True

    lic.L.deactivate()
    # Cache must have been busted — the next read resolves to OSS-free.
    assert e.get_entitlement().is_paid is False
