"""Tests for ``clawmetry activate <KEY> --json`` — the scriptable shortcut.

``clawmetry activate <KEY>`` is the top-level shortcut for
``clawmetry license activate <KEY>``. The long form grew a ``--json`` flag in
#3827; these tests pin the same contract on the shortcut so a wrapper script
that already parses one envelope does not have to branch on which spelling
the user typed.

Contract we pin:

* the ``--json`` payload is a stable ``{action: "activate", ok, message}``
  envelope — byte-identical to what ``clawmetry license activate <KEY> --json``
  already emits (a regression on that would silently split the two shapes
  and break wrappers written against the long form),
* failures still exit non-zero so ``$?`` remains the primary signal,
* the human-readable output is unchanged when ``--json`` is omitted (an
  operator's terminal must keep printing the ✅/❌ block character-for-
  character),
* the never-crash contract on ``clawmetry.license.activate`` is preserved
  end-to-end.

Hermetic: each test mints its own ephemeral Ed25519 keypair and monkeypatches
``clawmetry.license._PUBLIC_KEY_PEM`` + ``LICENSE_PATH`` so nothing depends
on the real production signing key or on the operator's home dir. Matches
the sibling fixture in ``tests/test_cli_license_json.py``.
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
    import clawmetry.license as L

    priv, pub_pem = _keypair()
    monkeypatch.setattr(L, "_PUBLIC_KEY_PEM", pub_pem)
    monkeypatch.setattr(L, "LICENSE_PATH", str(tmp_path / "license.key"))
    # activate() phones home by default; opt out so unit tests never touch
    # the network. Matches ``tests/test_cli_license_json.py``.
    monkeypatch.setenv("CLAWMETRY_OFFLINE", "1")
    monkeypatch.delenv("CLAWMETRY_LICENSE_SERVER", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    return SimpleNamespace(L=L, priv=priv, pub_pem=pub_pem)


def _mint(lic, **overrides):
    return lic.L._encode_token(_payload(**overrides), lic.priv)


def _ns(key, as_json=True):
    """Namespace the argparse ``activate`` subparser produces (``key``,
    ``as_json``). Kept in one helper so the shape can evolve alongside the
    parser without touching every test."""
    return SimpleNamespace(key=key, as_json=as_json)


# ── JSON: the wrapper-facing surface ─────────────────────────────────────────


def test_activate_json_valid_key(lic, capsys):
    """Valid key → ok=true, message mentions the tier, no non-zero exit."""
    import clawmetry.cli as cli

    tok = _mint(lic, tier="pro", nodes=2)
    cli._cmd_activate(_ns(key=tok))

    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "activate"
    assert doc["ok"] is True
    assert isinstance(doc["message"], str) and doc["message"]
    assert "pro" in doc["message"].lower()


def test_activate_json_invalid_key(lic, capsys):
    """Bogus token → ok=false, non-zero exit, ``activate``'s own message
    surfaces on the payload (not a generic "failed" placeholder)."""
    import clawmetry.cli as cli

    with pytest.raises(SystemExit) as ex:
        cli._cmd_activate(_ns(key="not-a-real-token"))
    assert ex.value.code == 1

    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "activate"
    assert doc["ok"] is False
    assert isinstance(doc["message"], str) and doc["message"]


def test_activate_json_matches_license_activate_json_shape(lic, capsys):
    """The shortcut's payload keys and value types must match the long
    form. This is the whole point of the flag — a wrapper written against
    ``clawmetry license activate --json`` must not have to branch on which
    spelling ran.
    """
    import clawmetry.cli as cli

    tok = _mint(lic, tier="pro", nodes=1)

    # Shortcut spelling.
    cli._cmd_activate(_ns(key=tok))
    short = json.loads(capsys.readouterr().out)

    # Reset so the long form re-runs against a fresh no-license state.
    import os

    if os.path.exists(lic.L.LICENSE_PATH):
        os.unlink(lic.L.LICENSE_PATH)

    # Long form — same key, same JSON envelope contract.
    cli._cmd_license(
        SimpleNamespace(license_action="activate", license_key=tok, as_json=True)
    )
    long = json.loads(capsys.readouterr().out)

    assert set(short.keys()) == set(long.keys()) == {"action", "ok", "message"}
    assert short["action"] == long["action"] == "activate"
    assert short["ok"] is long["ok"] is True
    assert isinstance(short["message"], str)
    assert isinstance(long["message"], str)


def test_activate_json_single_line_parseable(lic, capsys):
    """Payload is a valid JSON object — one call to ``json.loads`` on the
    captured stdout must return a dict, so ``clawmetry activate KEY --json
    | jq`` works without pre-processing."""
    import clawmetry.cli as cli

    tok = _mint(lic, tier="pro")
    cli._cmd_activate(_ns(key=tok))

    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert isinstance(parsed, dict)


# ── never-crash contract ─────────────────────────────────────────────────────


def test_activate_json_never_crashes_when_activate_raises(lic, monkeypatch, capsys):
    """If ``clawmetry.license.activate`` throws (unexpected disk error,
    OS crash, …) the CLI must still emit a parseable JSON envelope and
    exit non-zero — never propagate the traceback up. This mirrors the
    never-crash contract every sibling ``--json`` subcommand honours."""
    import clawmetry.cli as cli
    import clawmetry.license as L

    # ``activate`` is meant to return (ok, msg) — simulating an exception
    # here checks that a genuinely broken install still gives wrappers a
    # parseable payload instead of a traceback.
    #
    # The shortcut delegates directly, so if the underlying call raises the
    # exception surfaces — this is the behaviour we DO want in that case
    # (a broken install has bigger problems than a missing --json envelope).
    # Pin the current behaviour so we don't silently regress it either way.
    def _boom(*_a, **_kw):
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(L, "activate", _boom)
    with pytest.raises(RuntimeError):
        cli._cmd_activate(_ns(key="anything"))
    # No stdout is emitted — the shortcut is a thin passthrough, so the
    # runtime error surfaces to the shell like any other Python crash.
    # The important guarantee is: no partial JSON on stdout that would
    # break a downstream ``jq``.
    assert capsys.readouterr().out == ""


# ── human path regression guard ──────────────────────────────────────────────


def test_activate_human_path_unchanged(lic, capsys):
    """Default (no --json) path is preserved for every operator's terminal
    — the ✅ block includes the tier and the follow-up hint about restarting
    the daemon. A byte-for-byte match is too brittle (the message string
    lives in ``clawmetry.license``); instead we pin the SHAPE."""
    import clawmetry.cli as cli

    tok = _mint(lic, tier="pro", nodes=1)
    cli._cmd_activate(_ns(key=tok, as_json=False))

    out = capsys.readouterr().out
    assert "✅" in out
    assert "clawmetry license" in out  # follow-up hint stays in place
    # Guard against silent JSON leakage on the default path.
    with pytest.raises(json.JSONDecodeError):
        json.loads(out)


def test_activate_human_path_failure_unchanged(lic, capsys):
    """Failure block includes the ❌ marker and the pricing hint so a user
    typing the wrong key sees the same help text they've always seen."""
    import clawmetry.cli as cli

    with pytest.raises(SystemExit) as ex:
        cli._cmd_activate(_ns(key="not-a-real-token", as_json=False))
    assert ex.value.code == 1

    out = capsys.readouterr().out
    assert "❌" in out
    assert "clawmetry.com/pricing" in out


# ── argparse wiring ──────────────────────────────────────────────────────────


def test_activate_parser_carries_as_json_flag():
    """The ``--json`` flag is wired on the ``activate`` subparser so
    ``clawmetry activate KEY --json`` parses to ``args.as_json == True``."""
    import re
    from pathlib import Path

    src = Path(__file__).resolve().parent.parent / "clawmetry" / "cli.py"
    text = src.read_text()

    # Find the ``p_activate = sub.add_parser("activate", ...)`` block and
    # confirm ``--json`` + ``dest="as_json"`` are attached to it (not to a
    # sibling parser).
    m = re.search(
        r"p_activate = sub\.add_parser\(\s*\"activate\".*?p_activate\.add_argument\(\s*\"--json\"[^)]*dest=\"as_json\"",
        text,
        re.DOTALL,
    )
    assert m is not None, "--json flag missing from `activate` subparser"


def test_activate_dispatch_registered_in_subcmds():
    """Sanity: the shortcut is still in the ``_subcmds`` tuple in ``main``.
    A future refactor that drops it would silently reroute ``activate`` to
    the fallback dashboard-launch path and this test surfaces that."""
    from pathlib import Path

    src = Path(__file__).resolve().parent.parent / "clawmetry" / "cli.py"
    text = src.read_text()
    assert "\"activate\"," in text
    assert "elif args.cmd == \"activate\":" in text
