"""Tests for the ``license`` block in ``clawmetry status --json``.

Sibling of ``test_cli_status_extensions.py``: this suite pins the newly-added
``license`` field carrying the output of
:func:`clawmetry.license.current_license_info`, so operators (and wrapper
scripts) can tell from a fresh CLI process whether the self-hosted Pro /
Enterprise license key at ``~/.clawmetry/license.key`` is present, valid,
expired, or malformed — without needing a second ``clawmetry license --json``
call.

The block complements the two neighbouring diagnostics that already exist:

* ``runtimes.pro_installed_version`` — is the paid wheel on disk?
* ``extensions.discovered``           — does the paid wheel actually import?
* ``license``                        — is a valid signed key on disk?

Together they cover every failure mode an operator hits when Pro doesn't
turn on.

Every test is hermetic: an ephemeral Ed25519 keypair replaces the embedded
production public key, and ``LICENSE_PATH`` is repointed into ``tmp_path`` so
a developer's real key file is never read or written.
"""
from __future__ import annotations

import json
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


def _payload(tier="pro", nodes=5, sub="acct_test", exp_delta=365 * 86400):
    now = int(time.time())
    return {
        "sub": sub,
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
    }


def _ns(**overrides):
    ns = SimpleNamespace(live=False, show_key=False, as_json=True, cmd="status")
    for k, v in overrides.items():
        setattr(ns, k, v)
    return ns


@pytest.fixture
def stub_home(monkeypatch, tmp_path):
    """Same isolation harness ``test_cli_status_json.py`` uses, plus an
    ephemeral Ed25519 keypair for the license module so nothing under test
    depends on the real production signing key or on the operator's home."""
    import clawmetry.sync as _sync
    import clawmetry.cli as cli
    import clawmetry.extensions as ext
    import clawmetry.license as _lic

    monkeypatch.setattr(_sync, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(_sync, "STATE_FILE", tmp_path / "sync-state.json")
    monkeypatch.setattr(_sync, "LOG_FILE", tmp_path / "sync.log")

    plan_path = tmp_path / "cloud_plan.json"

    import os as _os
    import os.path as _op
    real_expanduser = _op.expanduser

    def _fake_expand(p):
        if p == "~/.clawmetry/cloud_plan.json":
            return str(plan_path)
        return real_expanduser(p)

    monkeypatch.setattr(_op, "expanduser", _fake_expand)
    monkeypatch.setattr(_os.path, "expanduser", _fake_expand)

    monkeypatch.setattr(cli, "_resolve_account_email", lambda _k: (None, None))
    monkeypatch.setattr(cli, "_is_sync_running", lambda: False)

    import platform as _platform
    monkeypatch.setattr(_platform, "system", lambda: "Linux")

    monkeypatch.setattr(
        "clawmetry.sync._detect_family_runtimes", lambda: [], raising=False,
    )
    monkeypatch.setattr(
        "clawmetry.license._pro_installed_version", lambda: None, raising=False,
    )

    # Ephemeral trust anchor + on-disk key path so no test can leak into
    # ``~/.clawmetry/license.key`` on the developer's machine.
    priv, pub_pem = _keypair()
    monkeypatch.setattr(_lic, "_PUBLIC_KEY_PEM", pub_pem)
    monkeypatch.setattr(_lic, "LICENSE_PATH", str(tmp_path / "license.key"))

    # Reset the extension-loader mirrors so an adjacent suite that populated
    # them cannot leak state into a probe run under this fixture.
    ext._loaded = False
    with ext._lock:
        ext._loaded_plugins.clear()
        ext._failed_plugins.clear()

    return SimpleNamespace(tmp=tmp_path, plan_path=plan_path, priv=priv)


def _run_and_parse(capsys, args):
    import clawmetry.cli as cli
    cli._cmd_status(args)
    out = capsys.readouterr().out
    return json.loads(out)


def _write_license(stub_home, **overrides):
    """Mint a token with the fixture's ephemeral key and drop it at
    ``LICENSE_PATH`` so ``current_license_info`` sees it."""
    import clawmetry.license as _lic
    payload = _payload(**overrides)
    token = _lic._encode_token(payload, stub_home.priv)
    with open(_lic.LICENSE_PATH, "w", encoding="utf-8") as fh:
        fh.write(token)
    return payload, token


# ── envelope ──────────────────────────────────────────────────────────────────


def test_license_key_present_on_virgin_install(stub_home, capsys):
    """No license file on disk → ``installed=False``, ``status="none"``,
    every optional field ``null``. All documented subkeys are always
    populated so ``jq .license.installed`` never sees a missing field."""
    doc = _run_and_parse(capsys, _ns())
    lic_block = doc["license"]
    assert set(lic_block.keys()) == {
        "installed", "valid", "status", "tier", "nodes", "sub",
        "days_left", "pubkey_fingerprint_sha256",
        "permissions_safe", "file_mode",
    }
    assert lic_block == {
        "installed": False,
        "valid": False,
        "status": "none",
        "tier": None,
        "nodes": None,
        "sub": None,
        "days_left": None,
        "pubkey_fingerprint_sha256": None,
        "permissions_safe": None,
        "file_mode": None,
    }


def test_license_reports_active_pro(stub_home, capsys):
    """A valid, non-expired Pro key with 10 nodes surfaces as ``valid=True``
    / ``status="active"`` / ``tier="pro"`` / ``nodes=10`` — the shape
    ``clawmetry license status --json`` already returns, folded into the
    composite snapshot so a wrapper script needs one CLI invocation."""
    _write_license(stub_home, tier="pro", nodes=10, sub="acct-pro")

    doc = _run_and_parse(capsys, _ns())
    lic_block = doc["license"]
    assert lic_block["installed"] is True
    assert lic_block["valid"] is True
    assert lic_block["status"] == "active"
    assert lic_block["tier"] == "pro"
    assert lic_block["nodes"] == 10
    assert lic_block["sub"] == "acct-pro"
    assert isinstance(lic_block["days_left"], int)
    assert lic_block["days_left"] > 300  # 1-year token minted just now
    # Trust anchor comes from the ephemeral pub key, so we cannot assert an
    # exact value — but the field must populate to a hex-shaped string so
    # audit scripts can compare it against ``clawmetry license fingerprint``.
    fp = lic_block["pubkey_fingerprint_sha256"]
    assert isinstance(fp, str) and len(fp) == 64 and all(
        c in "0123456789abcdef" for c in fp
    )


def test_license_reports_expired_key(stub_home, capsys):
    """An otherwise-valid key that is past its ``exp`` surfaces as
    ``valid=False`` / ``status="expired"`` with ``days_left`` negative, so
    a wrapper can still tell operators *what* the (now-stale) key was
    for. Complements the ``status="invalid"`` case below."""
    _write_license(stub_home, tier="enterprise", nodes=20, exp_delta=-3600)

    doc = _run_and_parse(capsys, _ns())
    lic_block = doc["license"]
    assert lic_block["installed"] is True
    assert lic_block["valid"] is False
    assert lic_block["status"] == "expired"
    # Payload is still parseable — the tier / nodes come through so the UI
    # can render "your Enterprise license expired X days ago".
    assert lic_block["tier"] == "enterprise"
    assert lic_block["nodes"] == 20
    assert isinstance(lic_block["days_left"], int) and lic_block["days_left"] <= 0


def test_license_reports_invalid_signature(stub_home, capsys):
    """A tampered / wrong-key-signed license file surfaces as
    ``valid=False`` / ``status="invalid"`` with ``tier`` / ``nodes`` /
    ``sub`` ALL NULL — never surface a claimed tier from an unverified
    body, or a forger could stuff arbitrary values into the envelope.
    The on-disk diagnostic fields (``permissions_safe``, ``file_mode``)
    still populate so the operator has debug context."""
    import clawmetry.license as _lic
    # Write a token signed by a DIFFERENT keypair than the one the fixture
    # installed as the trust anchor — signature verify fails.
    other_priv, _other_pub = _keypair()
    forged = _lic._encode_token(_payload(tier="pro", nodes=999), other_priv)
    with open(_lic.LICENSE_PATH, "w", encoding="utf-8") as fh:
        fh.write(forged)

    doc = _run_and_parse(capsys, _ns())
    lic_block = doc["license"]
    assert lic_block["installed"] is True
    assert lic_block["valid"] is False
    assert lic_block["status"] == "invalid"
    # Never surface an attacker-chosen tier / nodes / sub from an
    # unverified payload — the whole point of the signature check.
    assert lic_block["tier"] is None
    assert lic_block["nodes"] is None
    assert lic_block["sub"] is None
    assert lic_block["days_left"] is None
    # Trust anchor + on-disk fields are payload-independent — still populate.
    assert lic_block["pubkey_fingerprint_sha256"] is not None


def test_license_survives_helper_failure(stub_home, capsys, monkeypatch):
    """``current_license_info`` itself blows up → snapshot still emits the
    zero-shape default (no ``null``s, no 5xx). Guards the never-crash
    contract every other CLI diagnostic honours — a badly-timed
    ``KeyboardInterrupt`` or an ``OSError`` from a failing disk read must
    not take out ``clawmetry status --json``."""
    import clawmetry.license as _lic

    def _explode():
        raise RuntimeError("license read broke")

    monkeypatch.setattr(_lic, "current_license_info", _explode)

    doc = _run_and_parse(capsys, _ns())
    # Falls back to the default zero-shape from ``snap`` initialisation.
    assert doc["license"] == {
        "installed": False,
        "valid": False,
        "status": "none",
        "tier": None,
        "nodes": None,
        "sub": None,
        "days_left": None,
        "pubkey_fingerprint_sha256": None,
        "permissions_safe": None,
        "file_mode": None,
    }


def test_license_key_present_in_envelope_top_level(stub_home, capsys):
    """The envelope contract check pins that ``license`` is now a
    top-level key on every ``clawmetry status --json`` payload — same
    guarantee ``test_cli_status_json`` gives for ``runtimes`` /
    ``extensions`` etc. Wrapper scripts that iterate over documented
    top-level keys keep working."""
    doc = _run_and_parse(capsys, _ns())
    assert "license" in doc


# ── human path ───────────────────────────────────────────────────────────────


def test_license_human_path_shows_active_row(stub_home, capsys):
    """Without ``--json`` the human path renders a ✅ row when a valid
    license is on disk. Absence would leave operators with no in-``status``
    signal that the self-hosted key is installed and healthy."""
    _write_license(stub_home, tier="pro", nodes=10)

    import clawmetry.cli as cli
    cli._cmd_status(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "License:" in out
    assert "Pro" in out or "pro" in out
    # ``expires in Nd`` hint so an operator can see at a glance how much
    # runway they have before the key stops verifying.
    assert "expires in" in out


def test_license_human_path_shows_expired_row(stub_home, capsys):
    """An expired key renders a ⚠️ row pointing to ``clawmetry license``
    for the full detail — same triage-hint policy the extensions block
    uses (don't reprint the full envelope in the composite view)."""
    _write_license(stub_home, tier="pro", exp_delta=-3600)

    import clawmetry.cli as cli
    cli._cmd_status(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "License:" in out
    assert "expired" in out
    assert "clawmetry license" in out


def test_license_human_path_omits_block_when_absent(stub_home, capsys):
    """No license file → no ``License:`` header. A fresh OSS install
    should not paint an empty section that adds no information — the
    default state is "no key", and silence is the right default
    (same as the extensions block on installs with no plugins)."""
    import clawmetry.cli as cli
    cli._cmd_status(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "License:" not in out
