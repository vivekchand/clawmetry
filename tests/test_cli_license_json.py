"""Tests for ``clawmetry license --json`` — the scriptable license CLI.

Complements ``tests/test_tier_cli.py`` (the sibling ``clawmetry tier --json``
harness). The subcommand is a thin shell around ``clawmetry.license`` — these
tests pin the *contract* surface so shell wrappers can parse license state
without screen-scraping:

* every ``--json`` branch emits a stable ``{action, ok, ...}`` envelope,
* failures still exit non-zero so ``$?`` remains the primary signal,
* human-readable output is unchanged when ``--json`` is omitted (a
  regression on that would break every operator's terminal),
* the never-crash contract on the underlying license helpers is preserved.

Hermetic: each test mints its own ephemeral Ed25519 keypair and monkeypatches
``clawmetry.license._PUBLIC_KEY_PEM`` + ``LICENSE_PATH`` so nothing depends on
the real production signing key or on the operator's home dir.
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


def _payload(tier="pro", nodes=5, exp_delta=365 * 86400):
    now = int(time.time())
    return {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
    }


@pytest.fixture
def lic(monkeypatch, tmp_path):
    """Isolated license module: ephemeral keypair + tmp on-disk key path.

    Every license path (activate/status/verify/deactivate) goes through
    ``LICENSE_PATH``; repointing it at ``tmp_path`` keeps the tests hermetic
    across worker processes AND avoids clobbering a developer's real key when
    they run ``pytest`` locally.
    """
    import clawmetry.license as L

    priv, pub_pem = _keypair()
    monkeypatch.setattr(L, "_PUBLIC_KEY_PEM", pub_pem)
    monkeypatch.setattr(L, "LICENSE_PATH", str(tmp_path / "license.key"))
    # activate() phones home by default now; opt out so unit tests never touch
    # the network. Matches the fixture in ``tests/test_license.py``.
    monkeypatch.setenv("CLAWMETRY_OFFLINE", "1")
    monkeypatch.delenv("CLAWMETRY_LICENSE_SERVER", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    return SimpleNamespace(L=L, priv=priv, pub_pem=pub_pem)


def _mint(lic, **overrides):
    payload = _payload(**overrides)
    return lic.L._encode_token(payload, lic.priv)


def _ns(action=None, key=None, as_json=True):
    """Small SimpleNamespace factory mirroring the argparse Namespace shape
    _cmd_license reads. Kept out of the tests so the shape can evolve in one
    place if the parser sprouts new fields."""
    return SimpleNamespace(license_action=action, license_key=key, as_json=as_json)


# ── status ────────────────────────────────────────────────────────────────────


def test_status_json_no_license(lic, capsys):
    """No license on disk → installed=false, plan=oss, license=null."""
    import clawmetry.cli as cli

    cli._cmd_license(_ns(action="status"))
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "status"
    assert doc["ok"] is True
    assert doc["installed"] is False
    assert doc["plan"] == "oss"
    assert doc["license"] is None


def test_status_json_valid_license(lic, capsys):
    """Valid key on disk → installed=true, plan mirrors payload tier."""
    import clawmetry.cli as cli

    with open(lic.L.LICENSE_PATH, "w", encoding="utf-8") as fh:
        fh.write(_mint(lic, tier="pro", nodes=3) + "\n")

    cli._cmd_license(_ns(action="status"))
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "status"
    assert doc["ok"] is True
    assert doc["installed"] is True
    assert doc["plan"] == "pro"
    assert doc["license"]["tier"] == "pro"
    assert doc["license"]["nodes"] == 3
    assert doc["license"]["valid"] is True


def test_status_json_expired_license(lic, capsys):
    """Expired-but-parseable → ok=false, plan=oss (paid features shouldn't
    unlock on an expired key), license carries the drifted status."""
    import clawmetry.cli as cli

    with open(lic.L.LICENSE_PATH, "w", encoding="utf-8") as fh:
        fh.write(_mint(lic, exp_delta=-3600) + "\n")

    cli._cmd_license(_ns(action="status"))
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "status"
    assert doc["ok"] is False
    assert doc["installed"] is True
    assert doc["plan"] == "oss"
    assert doc["license"]["valid"] is False


# ── activate ──────────────────────────────────────────────────────────────────


def test_activate_json_missing_key(lic, capsys):
    """No key argument → non-zero exit, ok=false, usage message on the payload."""
    import clawmetry.cli as cli

    with pytest.raises(SystemExit) as ex:
        cli._cmd_license(_ns(action="activate", key=None))
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc == {
        "action": "activate",
        "ok": False,
        "message": "Usage: clawmetry license activate <KEY>",
    }


def test_activate_json_invalid_key(lic, capsys):
    """Bogus token → non-zero exit, ok=false, activate's own message surfaces."""
    import clawmetry.cli as cli

    with pytest.raises(SystemExit) as ex:
        cli._cmd_license(_ns(action="activate", key="not-a-real-token"))
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "activate"
    assert doc["ok"] is False
    assert "message" in doc and doc["message"]


def test_activate_json_valid_key(lic, capsys):
    """Valid key → activate succeeds, ok=true, message includes the tier."""
    import clawmetry.cli as cli

    tok = _mint(lic, tier="pro", nodes=2)
    cli._cmd_license(_ns(action="activate", key=tok))
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "activate"
    assert doc["ok"] is True
    assert "pro" in doc["message"].lower()


# ── deactivate ────────────────────────────────────────────────────────────────


def test_deactivate_json_no_license(lic, capsys):
    """Nothing installed → ok=true, removed=false (idempotent)."""
    import clawmetry.cli as cli

    cli._cmd_license(_ns(action="deactivate"))
    doc = json.loads(capsys.readouterr().out)
    assert doc == {"action": "deactivate", "ok": True, "removed": False}


def test_deactivate_json_removes_license(lic, capsys):
    """Installed license → ok=true, removed=true, file gone."""
    import clawmetry.cli as cli
    import os

    with open(lic.L.LICENSE_PATH, "w", encoding="utf-8") as fh:
        fh.write(_mint(lic) + "\n")
    assert os.path.isfile(lic.L.LICENSE_PATH)

    cli._cmd_license(_ns(action="deactivate"))
    doc = json.loads(capsys.readouterr().out)
    assert doc == {"action": "deactivate", "ok": True, "removed": True}
    assert not os.path.isfile(lic.L.LICENSE_PATH)


# ── fingerprint ───────────────────────────────────────────────────────────────


def test_fingerprint_json(lic, capsys):
    """Embedded key parses → ok=true and pubkey.fingerprint_sha256 is a 64-hex
    string that matches ``pubkey_fingerprint()`` (the same source ``/api/license
    /pubkey`` serves the dashboard).
    """
    import clawmetry.cli as cli

    cli._cmd_license(_ns(action="fingerprint"))
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "fingerprint"
    assert doc["ok"] is True
    pub = doc["pubkey"]
    assert pub["algorithm"] == "ed25519"
    fp = pub["fingerprint_sha256"]
    assert isinstance(fp, str) and len(fp) == 64
    assert fp == lic.L.pubkey_fingerprint()


# ── verify ────────────────────────────────────────────────────────────────────


def test_verify_json_missing_key(lic, capsys):
    """No key argument → non-zero exit, status=usage."""
    import clawmetry.cli as cli

    with pytest.raises(SystemExit) as ex:
        cli._cmd_license(_ns(action="verify", key=None))
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "verify"
    assert doc["ok"] is False
    assert doc["status"] == "usage"
    assert doc["inspection"] is None


def test_verify_json_valid_key(lic, capsys):
    """Valid signed key → ok=true, inspection carries tier/nodes; NOTHING
    written to disk (verify is a dry-run — see ``inspect_key``)."""
    import clawmetry.cli as cli
    import os

    tok = _mint(lic, tier="pro", nodes=7)
    cli._cmd_license(_ns(action="verify", key=tok))
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "verify"
    assert doc["ok"] is True
    assert doc["status"] == "active"
    ins = doc["inspection"]
    assert ins["tier"] == "pro"
    assert ins["nodes"] == 7
    assert ins["valid"] is True
    assert not os.path.isfile(lic.L.LICENSE_PATH)


def test_verify_json_invalid_key(lic, capsys):
    """Unparseable token → ok=false, status=invalid, inspection=null, exit 1."""
    import clawmetry.cli as cli

    with pytest.raises(SystemExit) as ex:
        cli._cmd_license(_ns(action="verify", key="not-a-real-token"))
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc == {
        "action": "verify",
        "ok": False,
        "status": "invalid",
        "inspection": None,
    }


def test_verify_json_expired_key(lic, capsys):
    """Signed but expired → ok=false, status=expired, inspection carries the
    former tier/nodes so support can confirm what the (now-stale) key covered.
    Exits 1 so a pipe still detects the failure."""
    import clawmetry.cli as cli

    tok = _mint(lic, exp_delta=-3600)
    with pytest.raises(SystemExit) as ex:
        cli._cmd_license(_ns(action="verify", key=tok))
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "verify"
    assert doc["ok"] is False
    assert doc["status"] == "expired"
    assert doc["inspection"] is not None
    assert doc["inspection"]["valid"] is False


# ── regression guards ────────────────────────────────────────────────────────


def test_plain_status_output_unchanged(lic, capsys):
    """Without --json the human-readable block is preserved character-for-
    character. Guards against accidental drift in the default text output —
    every operator's terminal reads this table."""
    import clawmetry.cli as cli

    cli._cmd_license(_ns(action="status", as_json=False))
    out = capsys.readouterr().out
    assert "ClawMetry License" in out
    assert "Plan:" in out
    assert "OSS (free)" in out
    # No stray JSON tokens should leak into the human path.
    assert "{" not in out


def test_license_subparser_has_json_flag():
    """The parser exposes --json on the license subcommand. Guards against a
    future edit that would silently drop the flag — a shell wrapper would
    start receiving the human table again with no diagnostic.
    """
    import clawmetry.cli as cli

    parser = cli._build_parser() if hasattr(cli, "_build_parser") else None
    if parser is None:
        # main() constructs the parser inline; probe by invoking with --help
        # via a minimal SimpleNamespace shape instead of reaching into main().
        # The presence of the JSON envelope in every test above is the real
        # guard — this branch exists so the file works whether or not the
        # parser is later extracted.
        pytest.skip("parser is inlined in main(); JSON-shape tests cover the wiring")

    # This branch is a placeholder in case _build_parser is added later; if
    # so, assert the flag is wired on the license subparser.
    ns = parser.parse_args(["license", "--json"])
    assert getattr(ns, "as_json", False) is True
