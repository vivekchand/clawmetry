"""Guard for the weak passphrase KDF (cloud #1573).

A typed custom passphrase used to be stored RAW and turned into the AES key via
unsalted single-pass SHA-256 (instant offline brute-force + a global rainbow
table works against everyone who picked the same passphrase). Now a passphrase
is run through scrypt with a random salt at setup and we store the DERIVED key
(never the passphrase). Existing installs that stored a raw passphrase keep
working via the legacy SHA-256 path in _normalize_encryption_key.
"""
import base64
import hashlib
import pathlib
import sys

# Import the repo's clawmetry, not a separately-installed copy that may shadow it
# on a dev box (the daemon installs clawmetry into its own venv). In CI the repo
# is the only clawmetry, so this is a no-op there.
_ROOT = str(pathlib.Path(__file__).resolve().parents[1])
if sys.path[:1] != [_ROOT]:
    sys.path.insert(0, _ROOT)
for _m in [m for m in list(sys.modules) if m == "clawmetry" or m.startswith("clawmetry.")]:
    del sys.modules[_m]
import clawmetry.sync as sync  # noqa: E402


def _is_32b_key(s):
    return len(base64.urlsafe_b64decode(s + "==")) == 32


def test_passphrase_is_scrypt_derived_not_stored_raw():
    k = sync._derive_key_for_storage("hunter2")
    assert k != "hunter2", "raw passphrase must never be persisted"
    assert _is_32b_key(k), "must store a real 32-byte key"


def test_passphrase_derivation_is_salted():
    # The old unsalted SHA-256 made the same passphrase -> the same key on every
    # machine (rainbow-table-able). Salting makes two derivations differ.
    a = sync._derive_key_for_storage("hunter2")
    b = sync._derive_key_for_storage("hunter2")
    assert a != b


def test_real_key_passed_through_unchanged():
    key = sync.generate_encryption_key()
    assert sync._derive_key_for_storage(key) == key


def test_legacy_raw_passphrase_still_sha256():
    # Existing configs stored a raw passphrase; _normalize_encryption_key must
    # keep deriving it the old way so their already-encrypted data decrypts.
    expect = base64.urlsafe_b64encode(hashlib.sha256(b"hunter2").digest()).decode().rstrip("=")
    assert sync._normalize_encryption_key("hunter2") == expect


def test_derived_key_roundtrips_through_encrypt():
    k = sync._derive_key_for_storage("a weak passphrase")
    blob = sync.encrypt_payload({"x": 1, "secret": "abc"}, k)
    assert sync.decrypt_payload(blob, k) == {"x": 1, "secret": "abc"}
