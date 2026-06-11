"""Tests for license-file permission hardening.

The license key is a bearer secret: anyone holding the file verifies
offline against the embedded public key, so the on-disk file must not be
group/world readable. These tests cover:

* ``_secure_write`` creates a 0o600 file regardless of umask.
* ``activate`` writes the license key 0o600 (and tightens the parent dir).
* ``_file_permissions_safe`` flags world/group-readable files.
* ``current_license_info`` surfaces ``permissions_safe`` and ``file_mode``.
* ``load_license`` still loads a (legacy) loose-permission file and logs a
  warning rather than refusing to read it (no backward-compat break).

POSIX-only — the permission bits don't exist on Windows.
"""
from __future__ import annotations

import os
import sys
import time
from types import SimpleNamespace

import pytest


pytestmark = pytest.mark.skipif(
    sys.platform.startswith("win") or os.name != "posix",
    reason="POSIX file mode bits do not apply on Windows",
)


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
        "sub": "acct_perms",
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
    monkeypatch.setattr(L, "_CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.delenv("CLAWMETRY_LICENSE_SERVER", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    # Skip the (offline) wheel-install side effect of activate().
    monkeypatch.setattr(L, "_download_and_install_pro", lambda payload: "")
    # Reset the once-per-path warning latch.
    L._warned_perms_for.clear()
    return SimpleNamespace(L=L, priv=priv, tmp_path=tmp_path)


def _mode(path: str) -> int:
    return os.stat(path).st_mode & 0o777


def test_secure_write_creates_0o600_under_loose_umask(lic, monkeypatch):
    """A fresh write respects 0o600 even when the caller's umask is wide."""
    path = str(lic.tmp_path / "fresh.key")
    old = os.umask(0o000)  # widest possible — every fresh file would be 0o666
    try:
        lic.L._secure_write(path, "hello\n")
    finally:
        os.umask(old)
    assert os.path.isfile(path)
    assert _mode(path) == 0o600
    with open(path, "r", encoding="utf-8") as fh:
        assert fh.read() == "hello\n"


def test_secure_write_tightens_existing_loose_file(lic):
    """An existing 0o644 file is rewritten and chmodded to 0o600."""
    path = str(lic.tmp_path / "old.key")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("legacy\n")
    os.chmod(path, 0o644)
    assert _mode(path) == 0o644
    lic.L._secure_write(path, "new\n")
    assert _mode(path) == 0o600
    with open(path, "r", encoding="utf-8") as fh:
        assert fh.read() == "new\n"


def test_activate_writes_license_0o600(lic):
    token = lic.L._encode_token(_payload(), lic.priv)
    ok, _msg = lic.L.activate(token)
    assert ok
    assert os.path.isfile(lic.L.LICENSE_PATH)
    assert _mode(lic.L.LICENSE_PATH) == 0o600


def test_activate_tightens_parent_dir_to_0o700(lic):
    token = lic.L._encode_token(_payload(), lic.priv)
    ok, _msg = lic.L.activate(token)
    assert ok
    parent = os.path.dirname(lic.L.LICENSE_PATH)
    # Some filesystems / mounts (NFS, FAT) refuse chmod; in those cases
    # activate's best-effort tighten is a no-op and that's fine. Where it
    # *can* chmod, we expect 0o700.
    if os.access(parent, os.W_OK):
        assert _mode(parent) == 0o700


def test_file_permissions_safe_flags_world_readable(lic):
    path = str(lic.tmp_path / "world.key")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("x\n")
    os.chmod(path, 0o644)
    assert lic.L._file_permissions_safe(path) is False
    os.chmod(path, 0o600)
    assert lic.L._file_permissions_safe(path) is True


def test_file_permissions_safe_flags_group_readable(lic):
    path = str(lic.tmp_path / "group.key")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("x\n")
    os.chmod(path, 0o640)
    assert lic.L._file_permissions_safe(path) is False


def test_file_permissions_safe_true_when_missing(lic):
    """A missing file is vacuously safe — nothing to leak."""
    assert lic.L._file_permissions_safe(str(lic.tmp_path / "nope.key")) is True


def test_current_license_info_surfaces_permissions_safe(lic):
    token = lic.L._encode_token(_payload(), lic.priv)
    ok, _msg = lic.L.activate(token)
    assert ok
    info = lic.L.current_license_info()
    assert info is not None
    assert info["permissions_safe"] is True
    assert info["file_mode"] == "0600"


def test_current_license_info_flags_loose_legacy_file(lic):
    """A pre-existing 0o644 license file (older clawmetry write) shows as
    unsafe in current_license_info — the UI can render a 'fix me' affordance
    without parsing octal."""
    token = lic.L._encode_token(_payload(), lic.priv)
    # Simulate the legacy write path: plain open(...,'w') under default umask.
    os.makedirs(os.path.dirname(lic.L.LICENSE_PATH), exist_ok=True)
    with open(lic.L.LICENSE_PATH, "w", encoding="utf-8") as fh:
        fh.write(token + "\n")
    os.chmod(lic.L.LICENSE_PATH, 0o644)
    info = lic.L.current_license_info()
    assert info is not None
    assert info["valid"] is True
    assert info["permissions_safe"] is False
    assert info["file_mode"] == "0644"


def test_load_license_still_reads_loose_file_and_warns(lic, caplog):
    """A legacy loose-permission file must still load (no backward-compat
    break) but a warning must be logged once."""
    import logging

    token = lic.L._encode_token(_payload(), lic.priv)
    os.makedirs(os.path.dirname(lic.L.LICENSE_PATH), exist_ok=True)
    with open(lic.L.LICENSE_PATH, "w", encoding="utf-8") as fh:
        fh.write(token + "\n")
    os.chmod(lic.L.LICENSE_PATH, 0o644)

    with caplog.at_level(logging.WARNING, logger="clawmetry.license"):
        ent1 = lic.L.load_license(lic.L.LICENSE_PATH)
        ent2 = lic.L.load_license(lic.L.LICENSE_PATH)
    assert ent1 is not None
    assert ent2 is not None
    warnings = [r for r in caplog.records if "loose permissions" in r.getMessage()]
    # Warn-once latch: one warning across two loads.
    assert len(warnings) == 1


def test_activate_rewrites_tightens_existing_loose_file(lic):
    """Re-running ``clawmetry activate`` over a legacy 0o644 file fixes it."""
    token = lic.L._encode_token(_payload(), lic.priv)
    os.makedirs(os.path.dirname(lic.L.LICENSE_PATH), exist_ok=True)
    with open(lic.L.LICENSE_PATH, "w", encoding="utf-8") as fh:
        fh.write("stale\n")
    os.chmod(lic.L.LICENSE_PATH, 0o644)
    assert _mode(lic.L.LICENSE_PATH) == 0o644
    ok, _msg = lic.L.activate(token)
    assert ok
    assert _mode(lic.L.LICENSE_PATH) == 0o600
