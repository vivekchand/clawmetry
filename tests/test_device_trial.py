"""Tests for clawmetry/device_trial.py — the account-free 7-day Pro trial.

Why these exist: the trial has been free and automatic since 2026-07-30,
but only after a sign-in, and most installs never sign in. The device trial
moves the sign-in ask to day 3. Every failure mode here is silent (a trial
that never starts, a trial minted for an install that already has a plan, a
retry storm against the license server), so each rule is pinned:

  * it never contacts the server when a license, a plan or an account key
    already speaks for the install, or when no paid runtime is present;
  * it honours the kill switch and offline mode;
  * one attempt per install, network errors retried daily, refusals final;
  * a minted key is activated (written 0600, node registered) WITHOUT
    recording an onboarding choice;
  * status() reports the sign-in nudge from day 3 and only while the trial
    is what actually entitles the install;
  * the install ping carries runtime ids / paid count / signed_in and
    nothing else new;
  * /api/trial/status carries the device_trial block.

Hermetic: tmp home, ephemeral keypair, no network.
"""
from __future__ import annotations

import importlib
import json
import os
import time
import urllib.error
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


def _mint(priv, exp_delta=7 * 86400, tier="trial"):
    from clawmetry import license as lic

    now = int(time.time())
    payload = {"jti": "lic_device", "sub": "device:x", "tier": tier,
               "nodes": 1, "iat": now, "exp": now + exp_delta}
    return lic._encode_token(payload, priv)


@pytest.fixture
def home(monkeypatch, tmp_path):
    """Point every ~/.clawmetry consumer at a tmp dir and reload the modules
    that snapshot paths at import time."""
    cfg_dir = tmp_path / ".clawmetry"
    cfg_dir.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_DEVICE_TRIAL", raising=False)
    monkeypatch.delenv("CLAWMETRY_OFFLINE", raising=False)
    monkeypatch.delenv("CLAWMETRY_NO_TELEMETRY", raising=False)
    monkeypatch.delenv("DO_NOT_TRACK", raising=False)

    from clawmetry import license as lic
    from clawmetry import entitlements as ent
    from clawmetry import telemetry as tel
    from clawmetry import device_trial as dt

    monkeypatch.setattr(lic, "LICENSE_PATH", str(cfg_dir / "license.key"))
    monkeypatch.setattr(lic, "_CONFIG_PATH", str(cfg_dir / "config.json"), raising=False)
    monkeypatch.setattr(ent, "_CLOUD_PLAN_CACHE", str(cfg_dir / "cloud_plan.json"))
    monkeypatch.setattr(ent, "_CONNECT_CONFIG_PATH", str(cfg_dir / "config.json"))
    monkeypatch.setattr(ent, "_LICENSE_PATH", str(cfg_dir / "license.key"), raising=False)
    monkeypatch.setattr(tel, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(tel, "INSTALL_ID_FILE", cfg_dir / "install_id")
    monkeypatch.setattr(tel, "OPTOUT_MARKER", cfg_dir / "notelemetry")
    monkeypatch.setattr(tel, "STATE_FILE", cfg_dir / "telemetry_state.json")
    monkeypatch.setattr(tel, "CONFIG_JSON", cfg_dir / "config.json", raising=False)
    monkeypatch.setattr(dt, "CONFIG_DIR", str(cfg_dir))
    monkeypatch.setattr(dt, "MARKER_PATH", str(cfg_dir / "device_trial.json"))
    monkeypatch.setattr(dt, "CONFIG_PATH", str(cfg_dir / "config.json"))
    # The pro wheel download is network; stub the whole activation tail.
    monkeypatch.setattr(lic, "_download_and_install_pro", lambda payload: "stubbed install")
    monkeypatch.setattr(lic, "_audit_license_event", lambda *a, **k: None)
    ent.invalidate()
    return SimpleNamespace(dir=cfg_dir, lic=lic, ent=ent, tel=tel, dt=dt)


def _paid_present(monkeypatch, home, ids=("claude_code",)):
    """Make the runtime probe report the given paid runtimes as found."""
    from clawmetry import runtime_probe as rp

    def fake_probe():
        out = []
        for p in rp.RUNTIME_PROBES:
            out.append({"id": p.id, "label": p.label,
                        "free": p.id in rp.FREE_RUNTIMES, "found": p.id in ids})
        return out

    monkeypatch.setattr(rp, "probe_runtimes", fake_probe)


def _server(monkeypatch, home, response=None, http_status=None, raise_exc=None):
    """Capture the POST the module makes and answer it."""
    calls = []

    class _Resp:
        def __init__(self, body):
            self._b = json.dumps(body).encode()

        def read(self):
            return self._b

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=0):
        calls.append(json.loads(req.data.decode()))
        if raise_exc:
            raise raise_exc
        if http_status:
            import io

            raise urllib.error.HTTPError(
                req.full_url, http_status, "x", {}, io.BytesIO(json.dumps(response or {}).encode())
            )
        return _Resp(response or {})

    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(home.lic, "_cloud_base", lambda: "https://license.test")
    return calls


# ── eligibility ───────────────────────────────────────────────────────────


def test_not_eligible_without_a_paid_runtime(monkeypatch, home):
    _paid_present(monkeypatch, home, ids=("openclaw",))
    ok, why = home.dt.eligible()
    assert (ok, why) == (False, "no_paid_runtime")


def test_not_eligible_when_a_license_exists_even_if_lapsed(monkeypatch, home):
    priv, pub = _keypair()
    monkeypatch.setattr(home.lic, "_load_public_key", lambda: __import__(
        "cryptography.hazmat.primitives.serialization", fromlist=["x"]).load_pem_public_key(pub))
    (home.dir / "license.key").write_text(_mint(priv, exp_delta=-3600) + "\n")
    home.ent.invalidate()
    _paid_present(monkeypatch, home)
    ok, why = home.dt.eligible()
    assert (ok, why) == (False, "entitled"), "a lapsed trial is the account's history; never a second trial"


def test_not_eligible_when_a_cloud_plan_is_cached(monkeypatch, home):
    (home.dir / "cloud_plan.json").write_text(json.dumps({"plan": "cloud_free"}))
    _paid_present(monkeypatch, home)
    assert home.dt.eligible() == (False, "entitled")


def test_not_eligible_when_an_account_key_is_present(monkeypatch, home):
    (home.dir / "config.json").write_text(json.dumps({"api_key": "cm_abc", "node_id": "n1"}))
    _paid_present(monkeypatch, home)
    assert home.dt.eligible() == (False, "entitled")


def test_kill_switch_and_offline(monkeypatch, home):
    _paid_present(monkeypatch, home)
    monkeypatch.setenv("CLAWMETRY_DEVICE_TRIAL", "0")
    assert home.dt.eligible() == (False, "disabled")
    monkeypatch.delenv("CLAWMETRY_DEVICE_TRIAL")
    monkeypatch.setenv("CLAWMETRY_OFFLINE", "1")
    assert home.dt.eligible() == (False, "disabled")


def test_eligible_on_a_fresh_install_with_claude_code(monkeypatch, home):
    _paid_present(monkeypatch, home)
    assert home.dt.eligible() == (True, "eligible")


# ── the request and activation ────────────────────────────────────────────


def test_start_mints_activates_and_records_without_onboarding_choice(monkeypatch, home):
    priv, pub = _keypair()
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    monkeypatch.setattr(home.lic, "_load_public_key", lambda: load_pem_public_key(pub))
    _paid_present(monkeypatch, home, ids=("claude_code", "cursor"))
    key = _mint(priv)
    calls = _server(monkeypatch, home, response={
        "ok": True, "key": key, "license_id": "lic_device",
        "expires_at": int(time.time()) + 7 * 86400, "expired": False,
    })
    pings = []
    monkeypatch.setattr(home.tel, "ping_once", lambda ev, ver, extra=None: pings.append((ev, extra)))

    res = home.dt.maybe_start("daemon")

    assert res["status"] == "started", res
    assert res["runtimes"] == ["claude_code", "cursor"]
    # One request, carrying only install_id / node_id / runtime ids.
    assert len(calls) == 1
    assert set(calls[0]) == {"install_id", "node_id", "runtimes"}
    assert calls[0]["runtimes"] == ["claude_code", "cursor"]
    assert calls[0]["install_id"] == (home.dir / "install_id").read_text().strip()
    # Key on disk, 0600, resolves to a trial from the license source.
    lic_path = home.dir / "license.key"
    assert lic_path.read_text().strip() == key
    if os.name == "posix":
        assert (lic_path.stat().st_mode & 0o777) == 0o600
    home.ent.invalidate()
    ent = home.ent.get_entitlement(force=True)
    assert ent.tier == "trial" and ent.source == "license"
    # node_id persisted so later activations name the same node.
    cfg = json.loads((home.dir / "config.json").read_text())
    assert cfg["node_id"] == calls[0]["node_id"] and cfg["node_id"]
    assert "api_key" not in cfg or not cfg["api_key"]
    # No onboarding choice was recorded: the first-run gate still asks.
    assert not (home.dir / "onboarding.json").exists()
    # Marker + telemetry.
    marker = json.loads((home.dir / "device_trial.json").read_text())
    assert marker["status"] == "started" and marker["runtimes"] == ["claude_code", "cursor"]
    assert pings and pings[0][0] == "device_trial_started"
    assert pings[0][1]["runtimes"] == ["claude_code", "cursor"]
    # Second call is a no-op: one attempt per install (the marker is checked
    # before the entitlement, so the reason names the recorded outcome).
    assert home.dt.maybe_start("daemon") == {"status": "skipped", "reason": "started"}
    assert len(calls) == 1


def test_expired_answer_is_recorded_and_never_retried(monkeypatch, home):
    _paid_present(monkeypatch, home)
    calls = _server(monkeypatch, home, response={"ok": True, "expired": True, "expires_at": 1})
    res = home.dt.maybe_start("onboard")
    assert res["status"] == "expired"
    assert home.dt.read_marker()["status"] == "expired"
    assert home.dt.maybe_start("onboard") == {"status": "skipped", "reason": "expired"}
    assert len(calls) == 1
    assert not (home.dir / "license.key").exists()


def test_refusal_is_final(monkeypatch, home):
    _paid_present(monkeypatch, home)
    calls = _server(monkeypatch, home, response={"ok": False, "error": "too many trials"}, http_status=429 + 0)
    # 429 is a throttle, not a decision: treated as an error (retried later).
    res = home.dt.maybe_start("daemon")
    assert res["status"] == "error"
    (home.dir / "device_trial.json").unlink()
    calls[:] = []
    _server(monkeypatch, home, response={"ok": False, "error": "no"}, http_status=403)
    res = home.dt.maybe_start("daemon")
    assert res["status"] == "refused" and "no" in res["error"]
    assert home.dt.maybe_start("daemon") == {"status": "skipped", "reason": "refused"}


def test_a_server_without_the_endpoint_is_retried_not_refused(monkeypatch, home):
    """The OSS wheel can reach a machine before the cloud deploy that serves
    the endpoint, and a self-hosted license server may never serve it. A
    404 there must be a daily retry, never a permanent refusal."""
    _paid_present(monkeypatch, home)
    calls = _server(monkeypatch, home, response={}, http_status=404)
    res = home.dt.maybe_start("daemon")
    assert res["status"] == "error", res
    assert home.dt.read_marker()["status"] == "error"
    assert home.dt.maybe_start("daemon") == {"status": "skipped", "reason": "error_backoff"}
    assert len(calls) == 1


def test_network_error_backs_off_for_a_day(monkeypatch, home):
    _paid_present(monkeypatch, home)
    calls = _server(monkeypatch, home, raise_exc=OSError("dns"))
    assert home.dt.maybe_start("daemon")["status"] == "error"
    assert home.dt.maybe_start("daemon") == {"status": "skipped", "reason": "error_backoff"}
    assert len(calls) == 1
    # A day later it tries again.
    m = home.dt.read_marker()
    m["attempted_at"] = time.time() - home.dt.ERROR_RETRY_SECS - 1
    home.dt._write_marker(m)
    assert home.dt.maybe_start("daemon")["status"] == "error"
    assert len(calls) == 2


def test_a_bad_key_from_the_server_is_not_activated(monkeypatch, home):
    _paid_present(monkeypatch, home)
    _server(monkeypatch, home, response={"ok": True, "key": "CLAW1.garbage.sig", "expires_at": 1})
    res = home.dt.maybe_start("daemon")
    assert res["status"] == "error" and "activation failed" in res["error"]
    assert not (home.dir / "license.key").exists()


def test_maybe_start_never_raises(monkeypatch, home):
    monkeypatch.setattr(home.dt, "eligible", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert home.dt.maybe_start("daemon")["status"] == "error"


# ── status() and the sign-in nudge ────────────────────────────────────────


def _activate_device_key(monkeypatch, home, exp_delta):
    priv, pub = _keypair()
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    monkeypatch.setattr(home.lic, "_load_public_key", lambda: load_pem_public_key(pub))
    key = _mint(priv, exp_delta=exp_delta)
    (home.dir / "license.key").write_text(key + "\n")
    home.dt._write_marker({"status": "started", "runtimes": ["claude_code"],
                           "expires_at": int(time.time()) + exp_delta})
    home.ent.invalidate()


def test_status_nudges_from_day_three(monkeypatch, home):
    _activate_device_key(monkeypatch, home, exp_delta=6 * 86400 + 3600)
    st = home.dt.status()
    assert st["active"] and st["days_left"] == 6 and st["signin_nudge"] is False
    _activate_device_key(monkeypatch, home, exp_delta=4 * 86400 + 3600)
    st = home.dt.status()
    assert st["active"] and st["days_left"] == 4 and st["signin_nudge"] is True
    assert st["signed_in"] is False and st["runtimes"] == ["claude_code"]


def test_status_stops_nudging_once_signed_in(monkeypatch, home):
    _activate_device_key(monkeypatch, home, exp_delta=2 * 86400)
    (home.dir / "config.json").write_text(json.dumps({"api_key": "cm_abc", "node_id": "n"}))
    st = home.dt.status()
    assert st["active"] and st["signed_in"] is True and st["signin_nudge"] is False


def test_status_inactive_when_something_stronger_resolves(monkeypatch, home):
    _activate_device_key(monkeypatch, home, exp_delta=2 * 86400)
    (home.dir / "cloud_plan.json").write_text(json.dumps({"plan": "cloud_pro"}))
    (home.dir / "license.key").unlink()
    home.ent.invalidate()
    st = home.dt.status()
    assert st["active"] is False and st["signin_nudge"] is False


def test_status_inactive_after_expiry(monkeypatch, home):
    _activate_device_key(monkeypatch, home, exp_delta=-60)
    assert home.dt.status()["active"] is False


def test_trial_status_route_carries_the_block(monkeypatch, home):
    _activate_device_key(monkeypatch, home, exp_delta=3 * 86400)
    from flask import Flask
    import routes.trial as rt

    app = Flask(__name__)
    app.register_blueprint(rt.bp_trial)
    with app.test_client() as c:
        body = c.get("/api/trial/status").get_json()
    assert "device_trial" in body
    assert body["device_trial"]["active"] is True
    assert body["device_trial"]["signin_nudge"] is True


# ── the install ping ──────────────────────────────────────────────────────


def test_install_ping_carries_runtime_ids_and_signed_in(monkeypatch, home):
    _paid_present(monkeypatch, home, ids=("openclaw", "claude_code", "codex"))
    p = home.tel._build_payload("1.2.3")
    assert p["runtimes"] == ["openclaw", "claude_code", "codex"]
    assert p["paid_runtimes"] == 2
    assert p["signed_in"] is False
    (home.dir / "config.json").write_text(json.dumps({"api_key": "cm_secret", "node_id": "n"}))
    p = home.tel._build_payload("1.2.3")
    assert p["signed_in"] is True
    assert "cm_secret" not in json.dumps(p)


def test_onboarding_lines_name_the_runtimes():
    from clawmetry import device_trial as dt

    lines = dt.onboarding_lines({"status": "started", "runtimes": ["claude_code", "cursor"]})
    assert lines and "Claude Code" in lines[0] and "Cursor" in lines[0]
    assert any("clawmetry connect" in ln for ln in lines)
    assert dt.onboarding_lines({"status": "skipped"}) == []
