"""The organisation key: the secret that makes a session readable by colleagues.

Every encrypted payload today is sealed with a key belonging to ONE machine and
held in ONE person's browser, which is why a teammate opening a colleague's node
gets the `team_view_locked` terminal state the cloud already ships. The
organisation key is the secret that makes "readable by the people I work with"
expressible without handing the hosted service anything it could read.

The properties worth pinning are the ones whose failure is silent:

* AC-CLOUD-TS-003.3 -- the hosted service never receives the key. Only a
  fingerprint, which identifies and cannot decrypt.
* the key is never accepted on the command line, where it would land in shell
  history and in every `ps` listing on a shared machine.
* a missing key means "do not upload", never "upload in the clear" -- the
  failure this whole area exists to prevent (clawmetry-cloud#2118).
"""

from __future__ import annotations

import json
import os

from clawmetry import org_key


def test_a_generated_key_is_256_bits_and_never_repeats():
    a, b = org_key.generate(), org_key.generate()
    assert a != b
    import base64
    assert len(base64.urlsafe_b64decode(a + "===")) == 32


def test_the_fingerprint_identifies_a_key_without_revealing_it():
    k = org_key.generate()
    fp = org_key.fingerprint(k)
    assert len(fp) == org_key.FINGERPRINT_CHARS
    assert fp == org_key.fingerprint(k), "must be stable"
    assert fp != org_key.fingerprint(org_key.generate())
    assert fp not in k and k not in fp
    assert org_key.fingerprint("") == ""


def test_a_passphrase_and_the_key_it_derives_share_a_fingerprint():
    """Otherwise a colleague who typed the passphrase and one who pasted the
    derived key are told they disagree while holding the same secret."""
    from clawmetry.sync import _normalize_encryption_key

    phrase = "correct horse battery staple"
    assert org_key.fingerprint(phrase) == org_key.fingerprint(
        _normalize_encryption_key(phrase))


def test_content_is_sealed_for_the_organisation_when_one_is_set():
    cfg = {"encryption_key": "NODEKEY", org_key.CONFIG_FIELD: "ORGKEY"}
    assert org_key.content_key(cfg) == "ORGKEY"
    assert org_key.is_org_sealed(cfg) is True


def test_content_falls_back_to_the_node_key_and_never_to_plaintext():
    """A machine with no organisation still seals with its own key. A machine
    with neither must yield "", so a caller cannot mistake "no key" for
    "no encryption needed"."""
    assert org_key.content_key({"encryption_key": "NODEKEY"}) == "NODEKEY"
    assert org_key.is_org_sealed({"encryption_key": "NODEKEY"}) is False
    assert org_key.content_key({}) == ""


def test_the_environment_can_supply_the_key_for_a_container(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ORG_KEY", "FROM-ENV")
    assert org_key.get({org_key.CONFIG_FIELD: "FROM-CONFIG"}) == "FROM-ENV"


def _write_config(tmp_path, extra=None):
    home = tmp_path / "home"
    (home / ".clawmetry").mkdir(parents=True)
    cfg = {"api_key": "cm_test", "node_id": "n1", "encryption_key": "NODEKEY"}
    cfg.update(extra or {})
    (home / ".clawmetry" / "config.json").write_text(json.dumps(cfg))
    return home


def test_the_heartbeat_carries_the_fingerprint_and_never_the_key(tmp_path,
                                                                 monkeypatch):
    """The heartbeat is PLAINTEXT. It must be able to say *which* secret opens
    this machine -- so a member holding the wrong one is told exactly that
    rather than shown an empty screen -- while carrying nothing that opens it.
    """
    secret = org_key.generate()
    home = _write_config(tmp_path, {org_key.CONFIG_FIELD: secret})
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CLAWMETRY_ORG_KEY", raising=False)

    import importlib
    import clawmetry.sync as sync
    importlib.reload(sync)

    meta = sync._build_node_meta()
    assert meta.get("content_key_scope") == "organisation"
    assert meta.get("content_key_fingerprint") == org_key.fingerprint(secret)

    blob = json.dumps(meta)
    assert secret not in blob, "the heartbeat must never carry the key itself"
    assert "NODEKEY" not in blob


def test_a_machine_with_no_organisation_reports_node_scope(tmp_path, monkeypatch):
    home = _write_config(tmp_path)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("CLAWMETRY_ORG_KEY", raising=False)

    import importlib
    import clawmetry.sync as sync
    importlib.reload(sync)

    meta = sync._build_node_meta()
    assert meta.get("content_key_scope") == "node"
    assert "NODEKEY" not in json.dumps(meta)


def test_the_key_is_never_accepted_as_a_command_line_argument():
    """A secret in argv is a secret in shell history and in every `ps` listing.

    This one opens an ORGANISATION's content rather than one machine's, so the
    parser must refuse it outright rather than accept it and warn. Asserted by
    running the real CLI, because the property lives in the parser wiring and
    not in any function this test could call directly.
    """
    import subprocess
    import sys

    import clawmetry.cli as cli

    repo = os.path.dirname(os.path.dirname(os.path.abspath(cli.__file__)))
    r = subprocess.run(
        [sys.executable, "-c",
         "import sys;sys.argv=['clawmetry','team','key','set','LEAKED'];"
         "from clawmetry.cli import main;main()"],
        capture_output=True, text=True, timeout=120,
        env=dict(os.environ, PYTHONPATH=repo),
    )
    combined = r.stdout + r.stderr
    assert r.returncode != 0, "a key on argv must not be accepted"
    assert "unrecognized arguments" in combined
