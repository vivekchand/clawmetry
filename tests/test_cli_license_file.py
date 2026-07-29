"""Tests for ``--file <path>`` on ``clawmetry activate`` and
``clawmetry license <activate|verify>``.

Rationale
---------
The positional key path (``clawmetry activate CLAW1…``) works, but pasting a
long token on the command line leaks the raw material into:

* the operator's shell history file (``~/.bash_history`` / zsh),
* the ``ps`` process listing during the ~10 ms the CLI is up,
* any centralised process-audit log the operator's team runs.

``--file <path>`` reads the token from a file instead. This test file pins the
contract on that flag for BOTH spellings so a future refactor that broke one
would be caught immediately:

* ``clawmetry activate --file <path>`` (the top-level shortcut)
* ``clawmetry license activate --file <path>`` (the long form)
* ``clawmetry license verify --file <path>`` (dry-run)

Hermetic per the sibling fixture in ``tests/test_cli_license_json.py``: each
test mints its own ephemeral Ed25519 keypair and repoints ``LICENSE_PATH`` at
``tmp_path`` so no real key is ever written on the developer's box.

Contract we pin (all three subcommands share the same reader
``_read_key_from_file``, so the assertions are symmetric):

* happy path: a file containing a valid signed token activates / verifies
  identically to passing the token on the command line — the JSON envelope
  is byte-identical apart from any status/inspection carry the underlying
  helper adds;
* trailing whitespace / newline in the file is stripped before verification
  (this is the common shape when a customer saves the key with a text
  editor — the trailing ``\\n`` would otherwise flip a valid key to
  ``ok=false``);
* mutually exclusive: ``--file`` + positional ``<KEY>`` = ok=false with a
  usage message that names both spellings;
* missing file / directory / empty file / no permission all collapse to
  ``ok=false`` + non-zero exit, without ever raising a traceback;
* neither ``--file`` nor positional key = ok=false + usage message that
  DOES mention ``--file`` (so an operator who forgot the arg discovers the
  new spelling from the error line itself).
"""
from __future__ import annotations

import json
import os
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


def _payload(tier="pro", nodes=3, exp_delta=365 * 86400):
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

    Mirrors the fixture in ``tests/test_cli_license_json.py`` so the two
    files can be read as a single harness.
    """
    import clawmetry.license as L

    priv, pub_pem = _keypair()
    monkeypatch.setattr(L, "_PUBLIC_KEY_PEM", pub_pem)
    monkeypatch.setattr(L, "LICENSE_PATH", str(tmp_path / "license.key"))
    monkeypatch.setenv("CLAWMETRY_OFFLINE", "1")
    monkeypatch.delenv("CLAWMETRY_LICENSE_SERVER", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    return SimpleNamespace(L=L, priv=priv, pub_pem=pub_pem)


def _mint(lic, **overrides):
    return lic.L._encode_token(_payload(**overrides), lic.priv)


def _shortcut_ns(*, key=None, file=None, as_json=True):
    """Argparse Namespace shape for the top-level ``clawmetry activate``
    subcommand. Keeps the field names in one place so the parser can grow
    without every test having to update its SimpleNamespace call."""
    return SimpleNamespace(key=key, file=file, as_json=as_json)


def _license_ns(*, action, key=None, file=None, as_json=True):
    """Argparse Namespace shape for ``clawmetry license <action>``."""
    return SimpleNamespace(
        license_action=action,
        license_key=key,
        file=file,
        as_json=as_json,
    )


# ── _read_key_from_file: the shared reader ──────────────────────────────────


def test_read_key_from_file_trims_trailing_newline(lic, tmp_path):
    """Text-editor-saved keys usually have a trailing ``\\n``. If the reader
    kept it, ``verify_token`` would refuse the key on shape mismatch — so
    the trim has to happen INSIDE the reader, not just at the CLI edge."""
    import clawmetry.cli as cli

    tok = _mint(lic)
    kf = tmp_path / "key.txt"
    kf.write_text(tok + "\n")
    ok, key, msg = cli._read_key_from_file(str(kf))
    assert ok is True
    assert key == tok
    assert msg == ""


def test_read_key_from_file_trims_surrounding_whitespace(lic, tmp_path):
    """Leading spaces / tabs / a CRLF are all stripped — same behavior as
    the CLI's ``key.strip()`` when the key was passed positionally."""
    import clawmetry.cli as cli

    tok = _mint(lic)
    kf = tmp_path / "key.txt"
    kf.write_text("  \t" + tok + " \r\n")
    ok, key, _ = cli._read_key_from_file(str(kf))
    assert ok is True and key == tok


def test_read_key_from_file_missing_returns_error(tmp_path):
    """Missing file → ok=false, message includes the path so the operator can
    fix the typo without reaching for strace. Never raises."""
    import clawmetry.cli as cli

    ok, key, msg = cli._read_key_from_file(str(tmp_path / "nope.key"))
    assert ok is False and key == ""
    assert "not found" in msg and "nope.key" in msg


def test_read_key_from_file_empty_returns_error(tmp_path):
    """Empty file → ok=false. Silently activating an empty key would surface
    downstream as a signature-verify failure with no hint the file was blank."""
    import clawmetry.cli as cli

    kf = tmp_path / "blank.key"
    kf.write_text("")
    ok, key, msg = cli._read_key_from_file(str(kf))
    assert ok is False and key == ""
    assert "empty" in msg


def test_read_key_from_file_whitespace_only_returns_error(tmp_path):
    """A file that has only whitespace is functionally empty — same envelope
    as the empty-file branch so the operator sees "is empty", not the
    downstream "signature failed" that a trimmed-to-'' key would produce."""
    import clawmetry.cli as cli

    kf = tmp_path / "spaces.key"
    kf.write_text("   \n\t \n")
    ok, key, msg = cli._read_key_from_file(str(kf))
    assert ok is False and key == ""
    assert "empty" in msg


def test_read_key_from_file_is_directory_returns_error(tmp_path):
    """Passing a directory path (typo) → ok=false, distinct message so the
    operator does not chase a "corrupt key file" ghost."""
    import clawmetry.cli as cli

    d = tmp_path / "keydir"
    d.mkdir()
    ok, key, msg = cli._read_key_from_file(str(d))
    assert ok is False and key == ""
    assert "directory" in msg.lower()


def test_read_key_from_file_empty_path_returns_error():
    """``--file ""`` (or ``--file`` with no argument coerced to '') → clean
    ok=false, no ``open("")`` traceback."""
    import clawmetry.cli as cli

    ok, key, msg = cli._read_key_from_file("")
    assert ok is False and key == "" and msg


# ── clawmetry activate --file <path> (shortcut) ──────────────────────────────


def test_shortcut_activate_from_file_valid_key(lic, tmp_path, capsys):
    """``clawmetry activate --file <path>`` = same success envelope as passing
    the key on the CLI. This is the whole point of the flag — a wrapper that
    already parses the shortcut envelope MUST NOT have to branch on which
    input source was used."""
    import clawmetry.cli as cli

    tok = _mint(lic, tier="pro", nodes=2)
    kf = tmp_path / "key.txt"
    kf.write_text(tok + "\n")

    cli._cmd_activate(_shortcut_ns(file=str(kf)))
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "activate"
    assert doc["ok"] is True
    assert "pro" in doc["message"].lower()
    # The activation actually wrote the license file — confirming the file
    # branch drives the same activate() path the positional branch does.
    assert os.path.isfile(lic.L.LICENSE_PATH)


def test_shortcut_activate_from_file_matches_positional_envelope(lic, tmp_path, capsys):
    """Envelope keys and value types for the ``--file`` branch match the
    positional branch. This is the wrapper-facing contract we cannot break."""
    import clawmetry.cli as cli

    tok = _mint(lic, tier="pro")
    # Positional first.
    cli._cmd_activate(_shortcut_ns(key=tok))
    positional = json.loads(capsys.readouterr().out)

    # Reset the license file so the --file path activates from a fresh state.
    if os.path.isfile(lic.L.LICENSE_PATH):
        os.unlink(lic.L.LICENSE_PATH)

    kf = tmp_path / "key.txt"
    kf.write_text(tok)
    cli._cmd_activate(_shortcut_ns(file=str(kf)))
    from_file = json.loads(capsys.readouterr().out)

    assert set(positional.keys()) == set(from_file.keys())
    assert positional["action"] == from_file["action"] == "activate"
    assert positional["ok"] is from_file["ok"] is True


def test_shortcut_activate_from_file_missing_exits_one(lic, tmp_path, capsys):
    """Nonexistent file → non-zero exit, ok=false, message names the path."""
    import clawmetry.cli as cli

    with pytest.raises(SystemExit) as ex:
        cli._cmd_activate(_shortcut_ns(file=str(tmp_path / "nope")))
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "activate"
    assert doc["ok"] is False
    assert "not found" in doc["message"] and "nope" in doc["message"]
    assert not os.path.isfile(lic.L.LICENSE_PATH)


def test_shortcut_activate_both_key_and_file_refused(lic, tmp_path, capsys):
    """Passing BOTH positional key AND --file is refused. A silent preference
    would let a script that changed input mode silently ignore the other."""
    import clawmetry.cli as cli

    tok = _mint(lic)
    kf = tmp_path / "key.txt"
    kf.write_text(tok)

    with pytest.raises(SystemExit) as ex:
        cli._cmd_activate(_shortcut_ns(key=tok, file=str(kf)))
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["ok"] is False
    assert "not both" in doc["message"].lower()
    # The refusal fires BEFORE activate() runs — nothing hits disk.
    assert not os.path.isfile(lic.L.LICENSE_PATH)


def test_shortcut_activate_neither_key_nor_file_mentions_file(lic, capsys):
    """No key AND no --file → ok=false; the message MUST mention --file so an
    operator who forgot the argument discovers the new spelling from the
    error line itself instead of the docs."""
    import clawmetry.cli as cli

    with pytest.raises(SystemExit) as ex:
        cli._cmd_activate(_shortcut_ns())
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["ok"] is False
    assert "--file" in doc["message"]


def test_shortcut_activate_from_file_human_output(lic, tmp_path, capsys):
    """Human (non-JSON) branch still prints the ✅ block on success and does
    NOT surface the file path (the tick line, not the file, is what the
    operator wants to see)."""
    import clawmetry.cli as cli

    tok = _mint(lic)
    kf = tmp_path / "key.txt"
    kf.write_text(tok)

    cli._cmd_activate(_shortcut_ns(file=str(kf), as_json=False))
    out = capsys.readouterr().out
    assert "✅" in out


# ── clawmetry license activate --file <path> (long form) ────────────────────


def test_license_activate_from_file_valid_key(lic, tmp_path, capsys):
    """Long-form activate consumes ``--file`` the same way the shortcut does."""
    import clawmetry.cli as cli

    tok = _mint(lic, tier="pro", nodes=4)
    kf = tmp_path / "key.txt"
    kf.write_text(tok + "\n")

    cli._cmd_license(_license_ns(action="activate", file=str(kf)))
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "activate"
    assert doc["ok"] is True
    assert os.path.isfile(lic.L.LICENSE_PATH)


def test_license_activate_from_file_matches_shortcut(lic, tmp_path, capsys):
    """The long-form ``--file`` envelope matches the shortcut ``--file``
    envelope key-for-key. This is a wrapper compatibility guarantee."""
    import clawmetry.cli as cli

    tok = _mint(lic, tier="pro")
    kf = tmp_path / "key.txt"
    kf.write_text(tok)

    cli._cmd_license(_license_ns(action="activate", file=str(kf)))
    long_form = json.loads(capsys.readouterr().out)

    if os.path.isfile(lic.L.LICENSE_PATH):
        os.unlink(lic.L.LICENSE_PATH)

    cli._cmd_activate(_shortcut_ns(file=str(kf)))
    short_form = json.loads(capsys.readouterr().out)

    assert set(long_form.keys()) == set(short_form.keys())
    assert long_form["action"] == short_form["action"] == "activate"
    assert long_form["ok"] is short_form["ok"] is True


def test_license_activate_from_file_missing_exits_one(lic, tmp_path, capsys):
    import clawmetry.cli as cli

    with pytest.raises(SystemExit) as ex:
        cli._cmd_license(
            _license_ns(action="activate", file=str(tmp_path / "absent"))
        )
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "activate"
    assert doc["ok"] is False
    assert "not found" in doc["message"]
    assert not os.path.isfile(lic.L.LICENSE_PATH)


def test_license_activate_both_key_and_file_refused(lic, tmp_path, capsys):
    import clawmetry.cli as cli

    tok = _mint(lic)
    kf = tmp_path / "key.txt"
    kf.write_text(tok)

    with pytest.raises(SystemExit) as ex:
        cli._cmd_license(
            _license_ns(action="activate", key=tok, file=str(kf))
        )
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["ok"] is False
    assert "not both" in doc["message"].lower()
    assert not os.path.isfile(lic.L.LICENSE_PATH)


def test_license_activate_neither_mentions_file(lic, capsys):
    import clawmetry.cli as cli

    with pytest.raises(SystemExit) as ex:
        cli._cmd_license(_license_ns(action="activate"))
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["ok"] is False
    assert "--file" in doc["message"]


# ── clawmetry license verify --file <path> (dry-run) ────────────────────────


def test_license_verify_from_file_valid_key(lic, tmp_path, capsys):
    """Verify is a dry-run — must NOT write anything, even when the file
    branch is used. This is the whole point of ``verify`` vs ``activate``."""
    import clawmetry.cli as cli

    tok = _mint(lic, tier="pro", nodes=6)
    kf = tmp_path / "key.txt"
    kf.write_text(tok + "\n")

    cli._cmd_license(_license_ns(action="verify", file=str(kf)))
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "verify"
    assert doc["ok"] is True
    assert doc["status"] == "active"
    ins = doc["inspection"]
    assert ins["tier"] == "pro" and ins["nodes"] == 6
    # Dry-run invariant: verify NEVER writes the license file.
    assert not os.path.isfile(lic.L.LICENSE_PATH)


def test_license_verify_from_file_missing_matches_shape(lic, tmp_path, capsys):
    """Unreadable file on ``verify`` still emits the full verify envelope
    (``action``/``ok``/``status``/``inspection`` all present) so a UI
    binding those four fields does not have to special-case the read-error
    branch."""
    import clawmetry.cli as cli

    with pytest.raises(SystemExit) as ex:
        cli._cmd_license(
            _license_ns(action="verify", file=str(tmp_path / "absent"))
        )
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "verify"
    assert doc["ok"] is False
    assert doc["status"] == "usage"
    assert doc["inspection"] is None
    assert "not found" in doc["message"]


def test_license_verify_both_key_and_file_refused(lic, tmp_path, capsys):
    import clawmetry.cli as cli

    tok = _mint(lic)
    kf = tmp_path / "key.txt"
    kf.write_text(tok)

    with pytest.raises(SystemExit) as ex:
        cli._cmd_license(
            _license_ns(action="verify", key=tok, file=str(kf))
        )
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["ok"] is False
    assert "not both" in doc["message"].lower()


def test_license_verify_from_file_expired_key_still_dry_run(lic, tmp_path, capsys):
    """An expired-but-signed key read from a file surfaces the same
    ``status=expired`` + ``ok=false`` envelope the positional branch does,
    and STILL does not write to disk. Regression guard: an early return that
    bailed out of the read branch on expiry would break support's
    "verify this expired key so we can see the old tier" flow."""
    import clawmetry.cli as cli

    tok = _mint(lic, exp_delta=-3600)
    kf = tmp_path / "key.txt"
    kf.write_text(tok)

    with pytest.raises(SystemExit) as ex:
        cli._cmd_license(_license_ns(action="verify", file=str(kf)))
    assert ex.value.code == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["action"] == "verify"
    assert doc["ok"] is False
    assert doc["status"] == "expired"
    assert doc["inspection"] is not None
    assert doc["inspection"]["valid"] is False
    assert not os.path.isfile(lic.L.LICENSE_PATH)


# ── regression guards ───────────────────────────────────────────────────────


def test_positional_key_still_works_after_flag_added(lic, capsys):
    """The old positional shape is untouched. This is the whole
    backwards-compat guarantee — no existing script that spells
    ``clawmetry activate CLAW1…`` regresses."""
    import clawmetry.cli as cli

    tok = _mint(lic)
    cli._cmd_activate(_shortcut_ns(key=tok))
    doc = json.loads(capsys.readouterr().out)
    assert doc["ok"] is True
    assert os.path.isfile(lic.L.LICENSE_PATH)


def test_resolve_activate_key_prefers_file_over_positional_absence(lic, tmp_path):
    """Direct unit-test of the resolver: file present + no positional → the
    file wins and the positional stays absent. Complements the handler-level
    happy-path test by pinning the resolver's own contract."""
    import clawmetry.cli as cli

    tok = _mint(lic)
    kf = tmp_path / "key.txt"
    kf.write_text(tok)
    args = _shortcut_ns(file=str(kf))
    ok, key, msg = cli._resolve_activate_key(args)
    assert ok is True
    assert key == tok
    assert msg == ""
