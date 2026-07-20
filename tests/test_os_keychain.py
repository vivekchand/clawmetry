"""OS keychain helpers for workspace enc_key (#1523).

Tests cover:
- round-trip set/get with a mocked keyring
- graceful no-op when keyring raises ImportError
- _keychain_get returns '' when keyring.get_password returns None
- _keychain_set silently swallows arbitrary exceptions
"""

import sys
import types
import pytest


# ---------------------------------------------------------------------------
# Helpers — isolated imports so real `keyring` is never required at test time
# ---------------------------------------------------------------------------

def _import_helpers():
    """Import _keychain_get and _keychain_set from clawmetry.cli."""
    from clawmetry import cli
    return cli._keychain_get, cli._keychain_set


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

class _FakeKeyring:
    """Minimal in-memory keyring shim."""

    def __init__(self):
        self._store: dict = {}

    def set_password(self, service: str, account: str, password: str) -> None:
        self._store[(service, account)] = password

    def get_password(self, service: str, account: str):
        return self._store.get((service, account))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_keychain_round_trip(monkeypatch):
    """set then get returns the stored key."""
    fake = _FakeKeyring()
    monkeypatch.setitem(sys.modules, "keyring", fake)

    _keychain_get, _keychain_set = _import_helpers()
    node = "test-node-abc"
    _keychain_set(node, "supersecretkey123")
    assert _keychain_get(node) == "supersecretkey123"


def test_keychain_get_missing_key_returns_empty(monkeypatch):
    """_keychain_get returns '' when the key was never stored."""
    fake = _FakeKeyring()
    monkeypatch.setitem(sys.modules, "keyring", fake)

    _keychain_get, _ = _import_helpers()
    assert _keychain_get("unknown-node") == ""


def test_keychain_get_none_from_keyring_returns_empty(monkeypatch):
    """get_password returning None maps to ''."""
    fake = _FakeKeyring()
    monkeypatch.setitem(sys.modules, "keyring", fake)

    _keychain_get, _ = _import_helpers()
    # Nothing stored → get_password returns None → helper must return ''
    result = _keychain_get("node-xyz")
    assert result == ""


def test_keychain_get_import_error_returns_empty(monkeypatch):
    """_keychain_get returns '' when keyring is not installed."""
    monkeypatch.setitem(sys.modules, "keyring", None)

    _keychain_get, _ = _import_helpers()
    assert _keychain_get("any-node") == ""


def test_keychain_set_import_error_is_silent(monkeypatch):
    """_keychain_set does not raise when keyring is not installed."""
    monkeypatch.setitem(sys.modules, "keyring", None)

    _, _keychain_set = _import_helpers()
    _keychain_set("any-node", "somekey")  # must not raise


def test_keychain_set_exception_is_silent(monkeypatch):
    """_keychain_set swallows arbitrary keyring errors."""
    class _BrokenKeyring:
        def set_password(self, *a, **kw):
            raise RuntimeError("keyring daemon unavailable")

        def get_password(self, *a, **kw):
            raise RuntimeError("keyring daemon unavailable")

    monkeypatch.setitem(sys.modules, "keyring", _BrokenKeyring())

    _keychain_get, _keychain_set = _import_helpers()
    _keychain_set("node", "key")   # must not raise
    assert _keychain_get("node") == ""


def test_keychain_overwrite(monkeypatch):
    """Calling set twice replaces the value."""
    fake = _FakeKeyring()
    monkeypatch.setitem(sys.modules, "keyring", fake)

    _keychain_get, _keychain_set = _import_helpers()
    node = "node-overwrite"
    _keychain_set(node, "first")
    _keychain_set(node, "second")
    assert _keychain_get(node) == "second"


def test_keychain_isolated_by_node_id(monkeypatch):
    """Different node_ids get independent keychain slots."""
    fake = _FakeKeyring()
    monkeypatch.setitem(sys.modules, "keyring", fake)

    _keychain_get, _keychain_set = _import_helpers()
    _keychain_set("node-A", "key-for-A")
    _keychain_set("node-B", "key-for-B")
    assert _keychain_get("node-A") == "key-for-A"
    assert _keychain_get("node-B") == "key-for-B"
