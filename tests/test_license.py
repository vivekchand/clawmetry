"""Tests for clawmetry/license.py — Ed25519 self-hosted license client.

Hermetic: each test mints tokens with its own ephemeral keypair and
monkeypatches the module's embedded public key, so nothing depends on the real
production signing key. Covers signature verification (valid/forged/tampered),
expiry, entitlement mapping, file load, the activate flow, and the integration
back into clawmetry.entitlements.
"""
from __future__ import annotations

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


def _payload(tier="pro", nodes=10, exp_delta=365 * 86400):
    now = int(time.time())
    return {
        "sub": "acct_test",
        "tier": tier,
        "nodes": nodes,
        "iat": now,
        "exp": now + exp_delta,
        "features": ["runtimes", "alerts", "fleet"],
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
    # `activate` phones home to the production cloud BY DEFAULT now, so unit
    # tests opt out via CLAWMETRY_OFFLINE. The phone-home tests below delete
    # this and stub urllib themselves — nothing here may touch the network.
    monkeypatch.setenv("CLAWMETRY_OFFLINE", "1")
    return SimpleNamespace(L=L, priv=priv, pub_pem=pub_pem)


# ── signature verification ────────────────────────────────────────────────────


def test_valid_token_verifies(lic):
    tok = lic.L._encode_token(_payload(), lic.priv)
    payload = lic.L.verify_token(tok)
    assert payload is not None
    assert payload["tier"] == "pro"
    assert payload["nodes"] == 10


def test_forged_token_rejected(lic):
    other_priv, _ = _keypair()  # signed by a DIFFERENT key
    tok = lic.L._encode_token(_payload(), other_priv)
    assert lic.L.verify_token(tok) is None


def test_tampered_payload_rejected(lic):
    tok = lic.L._encode_token(_payload(nodes=1), lic.priv)
    prefix, body, sig = tok.split(".")
    # swap in a different (validly-signed-elsewhere) body but keep the old sig
    forged_body = lic.L._b64u_encode(b'{"tier":"enterprise","nodes":9999}')
    assert lic.L.verify_token(f"{prefix}.{forged_body}.{sig}") is None


@pytest.mark.parametrize("bad", ["", "garbage", "NOPE.a.b", "CLAW1.only-two"])
def test_malformed_tokens_rejected(lic, bad):
    assert lic.L.verify_token(bad) is None


# ── entitlement mapping ────────────────────────────────────────────────────────


def test_parse_license_pro(lic):
    import clawmetry.entitlements as e

    tok = lic.L._encode_token(_payload("pro", nodes=42), lic.priv)
    en = lic.L.parse_license(tok)
    assert en is not None
    assert en.tier == e.TIER_PRO
    assert en.source == "license"
    assert en.node_limit == 42
    assert en.is_paid is True


def test_parse_license_enterprise(lic):
    import clawmetry.entitlements as e

    tok = lic.L._encode_token(_payload("enterprise", nodes=5), lic.priv)
    en = lic.L.parse_license(tok)
    assert en.tier == e.TIER_ENTERPRISE


def test_parse_license_starter(lic):
    """Self-hosted 'starter' keys ($90/node/yr) map to TIER_CLOUD_STARTER —
    a paid tier with the Starter feature set, not a silent Pro upgrade."""
    import clawmetry.entitlements as e

    tok = lic.L._encode_token(_payload("starter", nodes=1), lic.priv)
    en = lic.L.parse_license(tok)
    assert en is not None
    assert en.tier == e.TIER_CLOUD_STARTER
    assert en.source == "license"
    assert en.node_limit == 1
    assert en.is_paid is True
    # Starter carries the Starter feature set (not Pro's) + paid runtimes.
    assert e.STARTER_FEATURES <= en.features
    assert "claude_code" in en.runtimes


def test_parse_license_unknown_tier_defaults_to_pro(lic):
    """Forward compatibility: a tier this OSS build doesn't know still
    resolves to Pro rather than bricking the license."""
    import clawmetry.entitlements as e

    tok = lic.L._encode_token(_payload("mega_future_tier"), lic.priv)
    en = lic.L.parse_license(tok)
    assert en is not None and en.tier == e.TIER_PRO


def test_invalid_token_parses_to_none(lic):
    assert lic.L.parse_license("CLAW1.bogus.bogus") is None


# ── file load + activate ───────────────────────────────────────────────────────


def test_load_license_from_file(lic):
    tok = lic.L._encode_token(_payload(), lic.priv)
    with open(lic.L.LICENSE_PATH, "w") as fh:
        fh.write(tok)
    en = lic.L.load_license(lic.L.LICENSE_PATH)
    assert en is not None and en.is_paid


def test_load_missing_file_returns_none(lic):
    assert lic.L.load_license(lic.L.LICENSE_PATH) is None


def test_activate_valid_key(lic):
    import os

    tok = lic.L._encode_token(_payload("pro", nodes=7), lic.priv)
    ok, msg = lic.L.activate(tok)
    assert ok is True
    assert "pro" in msg.lower()
    assert os.path.isfile(lic.L.LICENSE_PATH)
    # offline-mode skip message when CLAWMETRY_OFFLINE is set (the fixture
    # default) — no node registration, no wheel download, activation still ok.
    assert "offline mode" in msg.lower()


def test_activate_invalid_key(lic):
    ok, msg = lic.L.activate("CLAW1.not.real")
    assert ok is False
    assert not __import__("os").path.isfile(lic.L.LICENSE_PATH)


def test_activate_expired_key(lic):
    tok = lic.L._encode_token(_payload(exp_delta=-3600), lic.priv)  # already expired
    ok, msg = lic.L.activate(tok)
    assert ok is False
    assert "expired" in msg.lower()


# ── activation phone-home (default server / offline opt-out) ─────────────────
#
# `clawmetry activate <KEY>` registers the node + fetches the clawmetry-pro
# wheel from the DEFAULT cloud base when nothing is configured — the license
# email says only `clawmetry activate <token>`, so the default must work.
# CLAWMETRY_OFFLINE=1 is the explicit opt-out. Every test here stubs urllib:
# no test may ever touch the real network.


def _stub_registration(monkeypatch, L):
    """Stub urllib.request.urlopen for the node-registration POST and capture
    the URL _provision_pro_wheel would be handed. Returns the capture dict."""
    import io
    import json as _j
    import urllib.request

    seen: dict = {"register_urls": [], "wheel_url": None}

    class _Resp(io.BytesIO):
        headers: dict = {}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _fake_urlopen(req, timeout=0):
        url = req.full_url
        seen["register_urls"].append(url)
        assert "/api/license/activate" in url, f"unexpected URL {url}"
        return _Resp(_j.dumps({"ok": True, "download_url": "/api/license/download"}).encode())

    def _fake_provision(url, headers=None, node_id=None):
        seen["wheel_url"] = url
        return "clawmetry-pro installed (test)"

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    monkeypatch.setattr(L, "_provision_pro_wheel", _fake_provision)
    return seen


def test_activate_no_env_phones_home_to_default_server(lic, monkeypatch):
    """No env vars at all -> registration + wheel download go to the
    production cloud base (this was the bug: it early-returned 'deferred'
    and paying customers never got the pro wheel)."""
    monkeypatch.delenv("CLAWMETRY_OFFLINE", raising=False)
    seen = _stub_registration(monkeypatch, lic.L)
    tok = lic.L._encode_token(_payload("pro", nodes=2), lic.priv)
    ok, msg = lic.L.activate(tok)
    assert ok is True
    assert seen["register_urls"] == ["https://ingest.clawmetry.com/api/license/activate"]
    assert seen["wheel_url"] == "https://ingest.clawmetry.com/api/license/download"
    assert "installed" in msg


def test_activate_license_server_env_still_wins(lic, monkeypatch):
    """CLAWMETRY_LICENSE_SERVER beats both CLAWMETRY_INGEST_URL and the
    default cloud base (self-hosted / air-gapped license servers)."""
    monkeypatch.delenv("CLAWMETRY_OFFLINE", raising=False)
    monkeypatch.setenv("CLAWMETRY_LICENSE_SERVER", "https://lic.example.test/")
    monkeypatch.setenv("CLAWMETRY_INGEST_URL", "https://ingest.other.test")
    seen = _stub_registration(monkeypatch, lic.L)
    tok = lic.L._encode_token(_payload(), lic.priv)
    ok, _msg = lic.L.activate(tok)
    assert ok is True
    assert seen["register_urls"] == ["https://lic.example.test/api/license/activate"]
    assert seen["wheel_url"] == "https://lic.example.test/api/license/download"


@pytest.mark.parametrize("truthy", ["1", "true", "YES"])
def test_activate_offline_env_skips_phone_home(lic, monkeypatch, truthy):
    """CLAWMETRY_OFFLINE (any truthy spelling) keeps activation fully local:
    no network call, clear skip message, license still active on disk."""
    import os
    import urllib.request

    monkeypatch.setenv("CLAWMETRY_OFFLINE", truthy)

    def _no_network(*a, **k):
        raise AssertionError("network touched in offline mode")

    monkeypatch.setattr(urllib.request, "urlopen", _no_network)
    tok = lic.L._encode_token(_payload("pro", nodes=3), lic.priv)
    ok, msg = lic.L.activate(tok)
    assert ok is True
    assert "offline mode" in msg
    assert "skipping node registration" in msg
    assert "CLAWMETRY_LICENSE_SERVER" in msg  # tells the operator the way out
    assert os.path.isfile(lic.L.LICENSE_PATH)
    en = lic.L.load_license(lic.L.LICENSE_PATH)
    assert en is not None and en.is_paid  # entitlements unlocked offline


def test_activate_survives_unreachable_default_server(lic, monkeypatch):
    """A failed phone-home NEVER fails activation: the key is verified
    offline and saved; the wheel install is deferred with a message."""
    import os
    import urllib.error
    import urllib.request

    monkeypatch.delenv("CLAWMETRY_OFFLINE", raising=False)

    def _down(req, timeout=0):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", _down)
    tok = lic.L._encode_token(_payload("pro", nodes=2), lic.priv)
    ok, msg = lic.L.activate(tok)
    assert ok is True
    assert "deferred" in msg.lower()
    assert os.path.isfile(lic.L.LICENSE_PATH)
    en = lic.L.load_license(lic.L.LICENSE_PATH)
    assert en is not None and en.is_paid


def test_inspect_key_valid_returns_summary(lic):
    """inspect_key returns the unlock summary for a valid key WITHOUT writing."""
    import os

    tok = lic.L._encode_token(_payload("pro", nodes=11), lic.priv)
    info = lic.L.inspect_key(tok)
    assert info is not None
    assert info["valid"] is True
    assert info["status"] == "active"
    assert info["tier"] == "pro"
    assert info["nodes"] == 11
    assert info["days_left"] is not None and info["days_left"] > 300
    # critical contract: dry-run never touches disk
    assert not os.path.isfile(lic.L.LICENSE_PATH)


def test_inspect_key_enterprise_tier(lic):
    tok = lic.L._encode_token(_payload("enterprise", nodes=99), lic.priv)
    info = lic.L.inspect_key(tok)
    assert info is not None and info["tier"] == "enterprise"
    assert info["nodes"] == 99


def test_inspect_key_starter_tier(lic):
    tok = lic.L._encode_token(_payload("starter", nodes=1), lic.priv)
    info = lic.L.inspect_key(tok)
    assert info is not None and info["tier"] == "starter"


def test_current_license_info_starter(lic):
    """`clawmetry license` status renders a starter key as 'starter'."""
    tok = lic.L._encode_token(_payload("starter", nodes=1), lic.priv)
    ok, _ = lic.L.activate(tok)
    assert ok
    info = lic.L.current_license_info()
    assert info["valid"] is True
    assert info["tier"] == "starter"


def test_inspect_key_invalid_returns_none(lic):
    """Bogus / forged tokens return None — no partial info leaked."""
    import os

    other_priv, _ = _keypair()
    forged = lic.L._encode_token(_payload(), other_priv)
    assert lic.L.inspect_key(forged) is None
    assert lic.L.inspect_key("CLAW1.garbage.garbage") is None
    assert lic.L.inspect_key("") is None
    assert not os.path.isfile(lic.L.LICENSE_PATH)


def test_inspect_key_expired_marks_invalid_but_returns_payload(lic):
    """Expired-but-parseable keys come back with valid=False + status='expired'
    so support can still confirm what the (now-stale) key was for."""
    tok = lic.L._encode_token(_payload("pro", nodes=4, exp_delta=-7200), lic.priv)
    info = lic.L.inspect_key(tok)
    assert info is not None
    assert info["valid"] is False
    assert info["status"] == "expired"
    assert info["tier"] == "pro"
    assert info["nodes"] == 4
    assert info["days_left"] is not None and info["days_left"] <= 0


def test_inspect_key_never_touches_disk_or_cache(lic, monkeypatch):
    """Hardens the no-side-effects contract: a verify must NOT invalidate the
    entitlement cache (activate does that; verify must not)."""
    import os

    import clawmetry.entitlements as e

    monkeypatch.setattr(e, "_LICENSE_PATH", lic.L.LICENSE_PATH)
    called = {"invalidate": 0}
    real_invalidate = e.invalidate
    monkeypatch.setattr(
        e, "invalidate", lambda: called.__setitem__("invalidate", called["invalidate"] + 1) or real_invalidate()
    )
    tok = lic.L._encode_token(_payload(), lic.priv)
    lic.L.inspect_key(tok)
    assert not os.path.isfile(lic.L.LICENSE_PATH)
    assert called["invalidate"] == 0


def test_current_license_info(lic):
    tok = lic.L._encode_token(_payload("pro", nodes=3), lic.priv)
    lic.L.activate(tok)
    info = lic.L.current_license_info()
    assert info["valid"] is True
    assert info["tier"] == "pro"
    assert info["nodes"] == 3
    assert info["days_left"] > 300


# ── current_license_info: uniform shape across active/expired/invalid ─────────
#
# When a license file exists, EVERY branch must return the same field set so
# a UI can render the row without special-casing which keys are present.

_EXPECTED_FILE_EXISTS_KEYS = frozenset({
    "valid", "status", "tier", "nodes", "sub", "exp", "days_left",
    "pubkey_fingerprint_sha256", "permissions_safe", "file_mode",
})


def test_current_license_info_missing_file_returns_none(lic):
    import os

    assert not os.path.isfile(lic.L.LICENSE_PATH)
    assert lic.L.current_license_info() is None


def test_current_license_info_invalid_signature_matches_full_shape(lic):
    """A file with a bogus signature returns the same field set as an active
    or expired license, so a UI never has to branch on which keys exist."""
    import os

    other_priv, _ = _keypair()
    forged = lic.L._encode_token(_payload(), other_priv)
    os.makedirs(os.path.dirname(lic.L.LICENSE_PATH), exist_ok=True)
    with open(lic.L.LICENSE_PATH, "w", encoding="utf-8") as fh:
        fh.write(forged + "\n")

    info = lic.L.current_license_info()
    assert info is not None
    assert set(info.keys()) == _EXPECTED_FILE_EXISTS_KEYS
    assert info["valid"] is False
    assert info["status"] == "invalid"
    # Untrusted payload fields must NOT leak — an attacker could put any tier
    # into an unsigned body, so treat them as unknown.
    assert info["tier"] is None
    assert info["nodes"] is None
    assert info["sub"] is None
    assert info["exp"] is None
    assert info["days_left"] is None
    # Trust anchor + on-disk state are payload-independent and must be filled.
    assert isinstance(info["pubkey_fingerprint_sha256"], str)
    assert len(info["pubkey_fingerprint_sha256"]) == 64
    assert info["permissions_safe"] in (True, False)


def test_current_license_info_expired_matches_full_shape(lic):
    """activate() refuses expired keys, so simulate the on-disk state
    directly — this pins the 'expired-but-signature-verifies' branch of
    current_license_info(), which is the state a live install reaches when
    a valid key ages past its exp."""
    import os

    tok = lic.L._encode_token(_payload("pro", nodes=4, exp_delta=-7200), lic.priv)
    os.makedirs(os.path.dirname(lic.L.LICENSE_PATH), exist_ok=True)
    with open(lic.L.LICENSE_PATH, "w", encoding="utf-8") as fh:
        fh.write(tok + "\n")

    info = lic.L.current_license_info()
    assert info is not None
    assert set(info.keys()) == _EXPECTED_FILE_EXISTS_KEYS
    assert info["valid"] is False
    assert info["status"] == "expired"
    assert info["tier"] == "pro"
    assert info["nodes"] == 4
    assert info["days_left"] is not None and info["days_left"] <= 0


def test_current_license_info_active_matches_full_shape(lic):
    tok = lic.L._encode_token(_payload("pro", nodes=3), lic.priv)
    lic.L.activate(tok)
    info = lic.L.current_license_info()
    assert info is not None
    assert set(info.keys()) == _EXPECTED_FILE_EXISTS_KEYS
    assert info["valid"] is True
    assert info["status"] == "active"


def test_current_license_info_garbage_file_returns_uniform_invalid_shape(lic):
    """Not even a well-formed CLAW1 token — just random bytes — still gets the
    full shape back so a UI's 'invalid license' row renders identically."""
    import os

    os.makedirs(os.path.dirname(lic.L.LICENSE_PATH), exist_ok=True)
    with open(lic.L.LICENSE_PATH, "w", encoding="utf-8") as fh:
        fh.write("not-even-a-token\n")

    info = lic.L.current_license_info()
    assert info is not None
    assert set(info.keys()) == _EXPECTED_FILE_EXISTS_KEYS
    assert info["valid"] is False
    assert info["status"] == "invalid"
    assert info["tier"] is None


# ── integration with entitlements ──────────────────────────────────────────────


def test_activate_then_entitlement_resolves_pro(lic, monkeypatch):
    import clawmetry.entitlements as e

    monkeypatch.setattr(e, "_LICENSE_PATH", lic.L.LICENSE_PATH)
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")  # enforce so grace can't mask it
    e.invalidate()

    tok = lic.L._encode_token(_payload("pro", nodes=42), lic.priv)
    ok, _ = lic.L.activate(tok)
    assert ok

    en = e.get_entitlement(force=True)
    assert en.tier == e.TIER_PRO
    assert en.node_limit == 42
    assert en.allows_runtime("claude_code") is True  # paid runtime unlocked
    assert en.grace is False


# ── auto-provision-on-connect (cloud cm_ account path) ──────────────────────────


@pytest.fixture
def prov(lic, monkeypatch, tmp_path):
    """license module with the pro marker redirected to a temp file + the cloud
    base pointed at a fake server, and no real pro package present."""
    monkeypatch.setattr(lic.L, "_PRO_MARKER_PATH", str(tmp_path / "pro.json"))
    monkeypatch.setenv("CLAWMETRY_INGEST_URL", "https://fake.clawmetry.test")
    monkeypatch.setattr(lic.L, "_pro_installed_version", lambda: None)
    return lic


def _fake_entitlement(monkeypatch, L, *, entitled, pro_available=True):
    """Stub urllib so the /api/license/entitlement probe returns a canned body
    and any download attempt is observable."""
    import io
    import json as _j
    import urllib.request

    calls = {"download": 0, "entitlement": 0}

    class _Resp(io.BytesIO):
        # urllib's real HTTPResponse always exposes .headers; the wheel
        # downloader reads Content-Disposition to keep the PEP-427 filename.
        headers: dict = {}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _fake_urlopen(req, timeout=0):
        url = req.full_url
        if "/api/license/entitlement" in url:
            calls["entitlement"] += 1
            assert req.headers.get("X-api-key", "").startswith("cm_")
            return _Resp(_j.dumps({"entitled": entitled, "plan": "cloud_pro" if entitled else "free", "pro_available": pro_available}).encode())
        if "/api/license/download" in url:
            calls["download"] += 1
            return _Resp(b"PK\x03\x04fake-wheel-bytes")
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    return calls


def test_auto_provision_free_account_installs_nothing(prov, monkeypatch):
    L = prov.L
    calls = _fake_entitlement(monkeypatch, L, entitled=False)
    installed, msg = L.auto_provision_pro("cm_freeuser", node_id="n1")
    assert installed is False
    assert msg == ""  # free accounts produce no user-facing message
    assert calls["entitlement"] == 1
    assert calls["download"] == 0  # NEVER downloads the wheel for a free account


def test_auto_provision_entitled_account_downloads_and_installs(prov, monkeypatch):
    L = prov.L
    calls = _fake_entitlement(monkeypatch, L, entitled=True)
    # Pro absent at probe time, present after the (stubbed) pip install — this
    # exercises the real download + install branch end to end.
    _state = {"v": None}
    monkeypatch.setattr(L, "_pro_installed_version", lambda: _state["v"])

    def _fake_pip(path):
        assert path and path.endswith(".whl")
        _state["v"] = "0.2.0"
        return True, "installed"

    monkeypatch.setattr(L, "_pip_install_wheel", _fake_pip)
    installed, msg = L.auto_provision_pro("cm_prouser", node_id="n1")
    assert installed is True
    assert calls["entitlement"] == 1
    assert calls["download"] == 1  # actually fetched the wheel
    assert "installed" in msg.lower()


def test_auto_provision_non_cm_key_is_noop(prov):
    installed, msg = prov.L.auto_provision_pro("not-a-key", node_id="n1")
    assert installed is False and msg == ""


def test_auto_provision_never_raises_on_install_failure(prov, monkeypatch):
    L = prov.L
    _fake_entitlement(monkeypatch, L, entitled=True)
    monkeypatch.setattr(L, "_pip_install_wheel", lambda p: (False, "pip blew up"))
    # download succeeds, install fails -> installed=False, message, no raise.
    installed, msg = L.auto_provision_pro("cm_prouser", node_id="n1")
    assert installed is False
    assert "failed" in msg.lower()


def test_auto_provision_idempotent_when_pro_present(prov, monkeypatch):
    """When the installed pro version is >= the wheel the server is serving,
    no re-install happens. The wheel itself is still downloaded every time --
    that re-validate-on-every-connect policy is intentional (see the comment
    on ``_provision_pro_wheel``: an installed pro never used to upgrade, so a
    fix in 0.3.4 sat unused on nodes still pinned to 0.3.3)."""
    L = prov.L
    calls = _fake_entitlement(monkeypatch, L, entitled=True)
    monkeypatch.setattr(L, "_pro_installed_version", lambda: "0.2.0")
    # Pin the wheel's advertised version <= the installed version so
    # _provision_pro_wheel short-circuits before re-installing. We have to
    # stub the parser because the fake `PK\x03\x04fake-wheel-bytes` body
    # isn't a real PEP-427 wheel and would otherwise parse to None.
    monkeypatch.setattr(L, "_wheel_file_version", lambda _path: "0.2.0")
    installed, msg = L.auto_provision_pro("cm_prouser", node_id="n1")
    assert installed is True
    assert calls["download"] == 1  # re-validates with the server every call
    assert "already installed" in msg


def test_download_wheel_refuses_non_https(prov):
    assert prov.L._download_wheel("http://evil.example.com/x.whl") is None


# ── pip-less venv install (the ~/.clawmetry/bin/python3 "No module named pip"
# bug: the daemon venv has no pip, so `python -m pip install` fails forever and
# the paid runtimes never provision). The installer must fall back to unzipping
# the (pure-Python, --no-deps) wheel straight into site-packages. ──────────────

def _make_fake_wheel(tmp_path):
    """Build a minimal pure-Python wheel zip: one package + a .dist-info."""
    import zipfile
    wheel = tmp_path / "clawfake-1.2.3-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as zf:
        zf.writestr("clawfake/__init__.py", "VERSION = '1.2.3'\n")
        zf.writestr("clawfake-1.2.3.dist-info/METADATA",
                    "Metadata-Version: 2.1\nName: clawfake\nVersion: 1.2.3\n")
        zf.writestr("clawfake-1.2.3.dist-info/RECORD", "")
    return wheel


def test_unzip_wheel_into_site_extracts_importably(prov, tmp_path, monkeypatch):
    L = prov.L
    import sysconfig
    site = tmp_path / "site"
    site.mkdir()
    monkeypatch.setattr(sysconfig, "get_path",
                        lambda name: str(site) if name in ("purelib", "platlib") else None)
    wheel = _make_fake_wheel(tmp_path)
    ok, detail = L._unzip_wheel_into_site(str(wheel))
    assert ok, detail
    # package + dist-info landed in site-packages
    assert (site / "clawfake" / "__init__.py").is_file()
    assert (site / "clawfake-1.2.3.dist-info" / "METADATA").is_file()


def test_pip_install_falls_back_to_unzip_when_pip_missing(prov, tmp_path, monkeypatch):
    """Simulate a pip-less venv: `python -m pip` reports 'No module named pip'
    and ensurepip can't bootstrap it. The installer must still install via the
    unzip fallback rather than failing the whole provision."""
    L = prov.L
    import sysconfig
    import subprocess
    site = tmp_path / "site"
    site.mkdir()
    monkeypatch.setattr(sysconfig, "get_path",
                        lambda name: str(site) if name in ("purelib", "platlib") else None)
    # pip is absent every time it's invoked.
    monkeypatch.setattr(L, "_pip_run",
                        lambda args: (False, "No module named pip"))
    # ensurepip is a no-op (still no pip afterwards) — covers venvs without it.
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: __import__("types").SimpleNamespace(returncode=1, stdout="", stderr=""))
    wheel = _make_fake_wheel(tmp_path)
    ok, detail = L._pip_install_wheel(str(wheel))
    assert ok, detail
    assert "unzip" in detail
    assert (site / "clawfake" / "__init__.py").is_file()


def test_pip_install_prefers_pip_when_available(prov, tmp_path, monkeypatch):
    """When pip works AND site-packages is writable, we use it and DON'T touch
    site-packages directly (pip is skipped only when site-packages is read-only,
    where it would fail anyway -> HOME fallback)."""
    L = prov.L
    monkeypatch.setattr(L, "_site_packages_target", lambda: ("/writable/site", True))
    monkeypatch.setattr(L, "_pip_run", lambda args: (True, "installed"))
    called = {"unzip": False}
    monkeypatch.setattr(L, "_unzip_wheel_into_site",
                        lambda p: (called.__setitem__("unzip", True), (True, "x"))[1])
    ok, detail = L._pip_install_wheel(str(tmp_path / "any.whl"))
    assert ok and detail == "installed"
    assert called["unzip"] is False  # never fell back
