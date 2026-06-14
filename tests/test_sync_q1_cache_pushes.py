"""Tests for Query Spine P4 — per-method q/1 proactive cache pushes.

Covers:
- CI guard: e2e-classed methods are NEVER pushed without an encryption key.
- Plaintext methods produce base64url JSON blobs (no encryption key required).
- E2e methods produce encrypted blobs when an encryption key is present.
- Cache key follows ``q1:{shape}:{owner_hash}:{node_id}`` pattern.
- Methods with required args are skipped (no pre-push without entity lookup).
- Feature flag off (default): no pushes emitted.
- Per-method debounce: second call within the window returns nothing.
- _PENDING_SHAPES includes all live q/1 shapes (P4 expansion).
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry.query_contract import QUERY_CONTRACT, TRUST_E2E, TRUST_PLAINTEXT, STATUS_LIVE


# ── helpers ──────────────────────────────────────────────────────────────────

_FAKE_CONFIG = {
    "api_key": "cm_testtoken",
    "node_id": "node_abc",
    "encryption_key": None,
}

_FAKE_CONFIG_WITH_KEY = {
    **_FAKE_CONFIG,
    "encryption_key": "c2VjcmV0a2V5c2VjcmV0a2V5c2VjcmV0a2U=",  # 32-byte base64
}


def _fake_encrypt(data: dict, key: str) -> str:
    """Stub for encrypt_payload — returns a deterministic fake encrypted blob."""
    return "FAKEBLOB_" + base64.urlsafe_b64encode(
        json.dumps(data, default=str).encode()
    ).rstrip(b"=").decode()


def _import_sync():
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as s
    return s


def _fake_dispatch(shape, args):
    return {"rows": [], "count": 0, "_shape": shape, "_via": "test"}


def _patch_dispatch(monkeypatch):
    """Patch dispatch at both the fallback slot and the importable routes module."""
    s = _import_sync()
    monkeypatch.setattr(s, "_local_dispatch_fallback", _fake_dispatch)
    try:
        from routes import local_query as lq  # type: ignore
        monkeypatch.setattr(lq, "_dispatch", _fake_dispatch, raising=False)
    except Exception:
        pass
    return s


# ── CI guard: no e2e push without enc_key ────────────────────────────────────

def test_e2e_shapes_never_pushed_without_enc_key(monkeypatch):
    """Hard guard: e2e-classed shapes must not appear in push list when no key."""
    monkeypatch.setenv("CLAWMETRY_QUERY_CACHE_PUSH", "1")
    s = _patch_dispatch(monkeypatch)
    monkeypatch.setattr(s, "_Q1_LAST_PUSH", {})

    e2e_shapes = {n for n, spec in QUERY_CONTRACT.items() if spec["trust"] == TRUST_E2E}
    config_no_key = {**_FAKE_CONFIG, "encryption_key": None}
    pushes = s._build_q1_cache_pushes(config_no_key)

    pushed_shapes = {p["key"].split(":")[1] for p in pushes}
    leaked = pushed_shapes & e2e_shapes
    assert not leaked, (
        f"e2e shapes {leaked} were pushed without an encryption key — "
        "trust-class contract violation"
    )


# ── Feature flag off by default ──────────────────────────────────────────────

def test_flag_off_returns_empty(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_QUERY_CACHE_PUSH", raising=False)
    s = _patch_dispatch(monkeypatch)
    monkeypatch.setattr(s, "encrypt_payload", _fake_encrypt)
    monkeypatch.setattr(s, "_Q1_LAST_PUSH", {})
    assert s._build_q1_cache_pushes(_FAKE_CONFIG_WITH_KEY) == []


# ── Cache key pattern ────────────────────────────────────────────────────────

def test_cache_key_follows_q1_pattern(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_QUERY_CACHE_PUSH", "1")
    s = _patch_dispatch(monkeypatch)
    monkeypatch.setattr(s, "encrypt_payload", _fake_encrypt)
    monkeypatch.setattr(s, "_Q1_LAST_PUSH", {})

    pushes = s._build_q1_cache_pushes(_FAKE_CONFIG_WITH_KEY)
    assert pushes, "expected at least one push with enc_key set"
    for push in pushes:
        parts = push["key"].split(":")
        assert parts[0] == "q1", f"key prefix must be 'q1', got {parts[0]!r}"
        assert len(parts) == 4, f"key must have 4 segments, got {push['key']!r}"
        assert parts[2] and parts[3], "owner_hash and node_id must be non-empty"


# ── Plaintext blobs are unencrypted base64url JSON ───────────────────────────

def test_plaintext_shapes_produce_readable_blobs(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_QUERY_CACHE_PUSH", "1")
    s = _patch_dispatch(monkeypatch)
    monkeypatch.setattr(s, "_Q1_LAST_PUSH", {})

    plaintext_shapes = {
        n for n, spec in QUERY_CONTRACT.items()
        if spec["status"] == STATUS_LIVE
        and spec["trust"] == TRUST_PLAINTEXT
        and not any(v.get("required") for v in spec.get("args", {}).values())
    }
    config_no_enc = {**_FAKE_CONFIG, "encryption_key": None}
    pushes = s._build_q1_cache_pushes(config_no_enc)
    pushed = {p["key"].split(":")[1]: p["blob"] for p in pushes}

    for shape in plaintext_shapes:
        if shape not in pushed:
            continue
        blob = pushed[shape]
        # Must be valid base64url-decodable JSON (no encryption)
        padded = blob + "=" * (4 - len(blob) % 4) if len(blob) % 4 else blob
        decoded = json.loads(base64.urlsafe_b64decode(padded))
        assert "_shape" in decoded


# ── Required-arg methods are skipped ─────────────────────────────────────────

def test_required_arg_methods_are_not_pushed(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_QUERY_CACHE_PUSH", "1")
    s = _patch_dispatch(monkeypatch)
    monkeypatch.setattr(s, "encrypt_payload", _fake_encrypt)
    monkeypatch.setattr(s, "_Q1_LAST_PUSH", {})

    required_arg_shapes = {
        n for n, spec in QUERY_CONTRACT.items()
        if spec["status"] == STATUS_LIVE
        and any(v.get("required") for v in spec.get("args", {}).values())
    }
    pushes = s._build_q1_cache_pushes(_FAKE_CONFIG_WITH_KEY)
    pushed_shapes = {p["key"].split(":")[1] for p in pushes}
    assert not (pushed_shapes & required_arg_shapes), (
        f"methods with required args should not be pre-pushed: "
        f"{pushed_shapes & required_arg_shapes}"
    )


# ── Debounce: second call within window returns nothing ──────────────────────

def test_debounce_suppresses_second_call(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_QUERY_CACHE_PUSH", "1")
    s = _patch_dispatch(monkeypatch)
    monkeypatch.setattr(s, "encrypt_payload", _fake_encrypt)
    monkeypatch.setattr(s, "_Q1_LAST_PUSH", {})

    first = s._build_q1_cache_pushes(_FAKE_CONFIG_WITH_KEY)
    assert first, "first call should produce pushes"
    second = s._build_q1_cache_pushes(_FAKE_CONFIG_WITH_KEY)
    assert second == [], "second call within debounce window must return nothing"


# ── _PENDING_SHAPES includes new P4 shapes ───────────────────────────────────

def test_pending_shapes_includes_p4_live_shapes():
    """All live q/1 no-required-arg shapes must appear in _PENDING_SHAPES."""
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as s
    live_no_required = {
        n for n, spec in QUERY_CONTRACT.items()
        if spec["status"] == STATUS_LIVE
        and not any(v.get("required") for v in spec.get("args", {}).values())
    }
    missing = live_no_required - s._PENDING_SHAPES
    assert not missing, (
        f"_PENDING_SHAPES is missing live no-required-arg shapes: {missing}. "
        "Add them so cloud-requested on-demand queries can also fetch these shapes."
    )
