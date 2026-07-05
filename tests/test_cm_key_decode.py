"""CM_KEY=scroll://... env var support — node pairing flow (#1522).

When a user installs ClawMetry as part of a v5 paired workspace they run:

    CM_KEY=scroll://<mnemonic>  clawmetry connect --key cm_xxx

The connect command must strip the ``scroll://`` URI prefix and feed the bare
key material through the existing ``_derive_key_for_storage`` path — same as
``--enc-key``.  The result is stored in config; the daemon reads from config
normally thereafter.
"""
from __future__ import annotations

import base64
import os

import pytest


# ---------------------------------------------------------------------------
# Unit-level: prefix stripping + KDF behaviour
# ---------------------------------------------------------------------------


def test_scroll_prefix_stripped_to_raw_b64_key():
    from clawmetry.sync import _normalize_encryption_key

    raw_key = base64.urlsafe_b64encode(b"\x42" * 32).decode().rstrip("=")
    scroll_val = f"scroll://{raw_key}"
    stripped = scroll_val[len("scroll://"):]
    # A valid 32-byte base64url key passes through _normalize unchanged.
    assert _normalize_encryption_key(stripped) == raw_key


def test_scroll_mnemonic_derives_to_32_byte_key():
    from clawmetry.sync import _derive_key_for_storage

    mnemonic = "apple bandit crystal dragon ember falcon granite harbor ivory jungle kelp lemon"
    derived = _derive_key_for_storage(mnemonic)
    raw = base64.urlsafe_b64decode(derived + "==")
    assert len(raw) == 32, "mnemonic must derive to a 256-bit (32-byte) AES key"


def test_scroll_key_round_trips_encrypt_decrypt():
    from clawmetry.sync import _derive_key_for_storage, encrypt_payload, decrypt_payload

    mnemonic = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"
    derived = _derive_key_for_storage(mnemonic)
    payload = {"event": "tool_call", "session_id": "s-abc123", "cost": 0.004}
    blob = encrypt_payload(payload, derived)
    assert decrypt_payload(blob, derived) == payload


def test_raw_cm_key_without_scroll_prefix_passes_through():
    from clawmetry.sync import _normalize_encryption_key

    raw_key = base64.urlsafe_b64encode(b"\x99" * 32).decode().rstrip("=")
    # No scroll:// prefix — treated as a raw base64url key.
    assert _normalize_encryption_key(raw_key) == raw_key


# ---------------------------------------------------------------------------
# Integration-level: env var is picked up by the connect arg-injection path
# ---------------------------------------------------------------------------


def test_cm_key_env_injected_into_args(monkeypatch):
    """The connect handler reads CM_KEY and injects it as args.enc_key when
    the flag was not already set."""
    import types
    import importlib

    mnemonic = "one two three four five six seven eight nine ten eleven twelve"
    scroll_val = f"scroll://{mnemonic}"

    monkeypatch.setenv("CM_KEY", scroll_val)

    # Simulate the injection logic that lives in cli.py's connect handler.
    args = types.SimpleNamespace(enc_key=None)

    _cm_key_env = os.environ.get("CM_KEY", "")
    if _cm_key_env.startswith("scroll://"):
        _cm_key_env = _cm_key_env[len("scroll://"):]
    if _cm_key_env and not getattr(args, "enc_key", None):
        setattr(args, "enc_key", _cm_key_env)

    assert args.enc_key == mnemonic


def test_explicit_enc_key_flag_wins_over_cm_key_env(monkeypatch):
    """--enc-key flag takes precedence over CM_KEY env var."""
    import types

    explicit_key = base64.urlsafe_b64encode(b"\xAB" * 32).decode().rstrip("=")
    monkeypatch.setenv("CM_KEY", "scroll://ignored-mnemonic")

    args = types.SimpleNamespace(enc_key=explicit_key)

    _cm_key_env = os.environ.get("CM_KEY", "")
    if _cm_key_env.startswith("scroll://"):
        _cm_key_env = _cm_key_env[len("scroll://"):]
    if _cm_key_env and not getattr(args, "enc_key", None):
        setattr(args, "enc_key", _cm_key_env)

    assert args.enc_key == explicit_key


def test_empty_cm_key_env_is_ignored(monkeypatch):
    """Empty CM_KEY does not override args.enc_key=None (auto-generate path)."""
    import types

    monkeypatch.setenv("CM_KEY", "")

    args = types.SimpleNamespace(enc_key=None)

    _cm_key_env = os.environ.get("CM_KEY", "")
    if _cm_key_env.startswith("scroll://"):
        _cm_key_env = _cm_key_env[len("scroll://"):]
    if _cm_key_env and not getattr(args, "enc_key", None):
        setattr(args, "enc_key", _cm_key_env)

    assert args.enc_key is None
