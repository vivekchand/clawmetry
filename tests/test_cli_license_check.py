"""Tests for the ``clawmetry license check`` subcommand — dry-run license
verify with no side effects on disk or on the entitlement cache.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key, so nothing depends on the
real production signing key.
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


def _payload(tier="pro", nodes=10, exp_delta=365 * 86400):
    now = int(time.time())
    return {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
        "features": ["runtimes", "alerts", "fleet"],
    }


@pytest.fixture
def cli_ctx(monkeypatch, tmp_path):
    import clawmetry.license as L

    priv, pub_pem = _keypair()
    monkeypatch.setattr(L, "_PUBLIC_KEY_PEM", pub_pem)
    monkeypatch.setattr(L, "LICENSE_PATH", str(tmp_path / "license.key"))
    monkeypatch.setattr(L, "_CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.delenv("CLAWMETRY_LICENSE_SERVER", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    return SimpleNamespace(L=L, priv=priv)


# ── happy path ────────────────────────────────────────────────────────────────


def test_check_valid_pro_key_prints_summary(cli_ctx, capsys):
    from clawmetry import cli

    tok = cli_ctx.L._encode_token(_payload("pro", nodes=8), cli_ctx.priv)
    args = SimpleNamespace(license_action="check", license_key=tok)
    cli._cmd_license(args)
    out = capsys.readouterr().out
    assert "Pro" in out
    assert "8" in out  # nodes
    assert "VALID" in out
    assert "no changes made" in out


def test_check_valid_enterprise_key(cli_ctx, capsys):
    from clawmetry import cli

    tok = cli_ctx.L._encode_token(_payload("enterprise", nodes=50), cli_ctx.priv)
    args = SimpleNamespace(license_action="check", license_key=tok)
    cli._cmd_license(args)
    out = capsys.readouterr().out
    assert "Enterprise" in out
    assert "50" in out
    assert "VALID" in out


def test_check_surfaces_account_subject(cli_ctx, capsys):
    from clawmetry import cli

    tok = cli_ctx.L._encode_token(_payload("pro"), cli_ctx.priv)
    args = SimpleNamespace(license_action="check", license_key=tok)
    cli._cmd_license(args)
    out = capsys.readouterr().out
    assert "acct_test" in out  # subject claim is printed for support flows


# ── failure paths ────────────────────────────────────────────────────────────


def test_check_with_no_key_exits_nonzero(cli_ctx, capsys):
    from clawmetry import cli

    args = SimpleNamespace(license_action="check", license_key=None)
    with pytest.raises(SystemExit) as excinfo:
        cli._cmd_license(args)
    assert excinfo.value.code == 1
    out = capsys.readouterr().out
    assert "Usage" in out


def test_check_invalid_signature_exits_nonzero(cli_ctx, capsys):
    from clawmetry import cli

    args = SimpleNamespace(license_action="check", license_key="CLAW1.not.real")
    with pytest.raises(SystemExit) as excinfo:
        cli._cmd_license(args)
    assert excinfo.value.code == 1
    out = capsys.readouterr().out
    assert "invalid" in out.lower()


def test_check_forged_signature_exits_nonzero(cli_ctx, capsys):
    from clawmetry import cli

    other_priv, _ = _keypair()
    tok = cli_ctx.L._encode_token(_payload("pro"), other_priv)
    args = SimpleNamespace(license_action="check", license_key=tok)
    with pytest.raises(SystemExit) as excinfo:
        cli._cmd_license(args)
    assert excinfo.value.code == 1


def test_check_expired_key_exits_nonzero(cli_ctx, capsys):
    from clawmetry import cli

    tok = cli_ctx.L._encode_token(_payload("pro", exp_delta=-86400), cli_ctx.priv)
    args = SimpleNamespace(license_action="check", license_key=tok)
    with pytest.raises(SystemExit) as excinfo:
        cli._cmd_license(args)
    assert excinfo.value.code == 1
    out = capsys.readouterr().out
    assert "EXPIRED" in out
    # tier is still shown so the operator sees WHICH key expired:
    assert "Pro" in out


# ── no side effects on disk or on the entitlement cache ──────────────────────


def test_check_does_not_create_license_file(cli_ctx, capsys):
    import os
    from clawmetry import cli

    tok = cli_ctx.L._encode_token(_payload("pro", nodes=3), cli_ctx.priv)
    args = SimpleNamespace(license_action="check", license_key=tok)
    cli._cmd_license(args)
    assert not os.path.isfile(cli_ctx.L.LICENSE_PATH)
    capsys.readouterr()  # drain


def test_check_does_not_flip_resolved_entitlement(cli_ctx, monkeypatch, capsys, tmp_path):
    """A dry-run check must not move the resolver off OSS-free, even under
    enforce mode."""
    import clawmetry.entitlements as e
    from clawmetry import cli

    monkeypatch.setattr(e, "_LICENSE_PATH", cli_ctx.L.LICENSE_PATH)
    # Pin the cloud-plan cache to an empty tmp path so a sibling test that
    # reloaded entitlements with a patched HOME cannot leak a cached plan in.
    monkeypatch.setattr(e, "_CLOUD_PLAN_CACHE", str(tmp_path / "cloud_plan.json"))
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    e.invalidate()
    assert e.get_entitlement(force=True).tier == e.TIER_OSS

    tok = cli_ctx.L._encode_token(_payload("pro", nodes=2), cli_ctx.priv)
    args = SimpleNamespace(license_action="check", license_key=tok)
    cli._cmd_license(args)
    capsys.readouterr()

    after = e.get_entitlement(force=True)
    assert after.tier == e.TIER_OSS  # unchanged
