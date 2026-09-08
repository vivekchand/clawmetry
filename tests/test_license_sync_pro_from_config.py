"""`clawmetry.license.sync_pro_from_config()` — the one place that reconciles
the paid-adapter wheel with the core (2026-08-28).

clawmetry-pro ships on its own cadence, so every path that upgrades the core
(`clawmetry update`, the dashboard's "Update now", the daemon auto-updater,
install.sh) has to reconcile pro too or an entitled node ends up running a
current core against months-old adapters.

The contract these tests pin:
  * a node with no cloud key does not phone home and claims nothing;
  * a moved wheel is reported as ``updated`` (the caller owes a restart);
  * an unreachable license server never turns an installed wheel into a
    "current" claim -- it reports ``kept``;
  * nothing here ever raises, whatever the provisioner does.
"""

from __future__ import annotations

import json

import pytest

from clawmetry import license as lic


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    cfg_dir = tmp_path / ".clawmetry"
    cfg_dir.mkdir()
    monkeypatch.setattr(lic, "_CONFIG_PATH", str(cfg_dir / "config.json"))
    monkeypatch.delenv("CLAWMETRY_API_KEY", raising=False)
    return cfg_dir


def _write_config(cfg_dir, payload):
    (cfg_dir / "config.json").write_text(json.dumps(payload))


def _stub_provision(monkeypatch, *, versions, ok, msg=""):
    """``versions`` is a list popped by each _pro_installed_version() call."""
    seq = list(versions)
    monkeypatch.setattr(lic, "ensure_pro_on_path", lambda: None)
    monkeypatch.setattr(lic, "_pro_installed_version", lambda: seq.pop(0))
    calls = []

    def _prov(key, node_id=None):
        calls.append((key, node_id))
        return ok, msg

    monkeypatch.setattr(lic, "auto_provision_pro", _prov)
    return calls


def test_no_cloud_key_never_phones_home(fake_home, monkeypatch):
    _write_config(fake_home, {"node_id": "box"})
    calls = _stub_provision(monkeypatch, versions=["0.7.1", "0.7.1"], ok=True)
    assert lic.sync_pro_from_config() == ("none", "", "", "")
    assert calls == [], "no account on this machine must mean no entitlement probe"


def test_self_hosted_license_key_is_not_a_cloud_key(fake_home, monkeypatch):
    """A signed license (CLAW1.…) is provisioned by `clawmetry license
    activate`; it must never be sent to the cloud entitlement endpoint."""
    _write_config(fake_home, {"api_key": "CLAW1.abcdef", "node_id": "box"})
    calls = _stub_provision(monkeypatch, versions=["", ""], ok=True)
    state, _, _, _ = lic.sync_pro_from_config()
    assert state == "none"
    assert calls == []


def test_newer_wheel_reports_updated(fake_home, monkeypatch):
    _write_config(fake_home, {"api_key": "cm_live_1", "node_id": "box"})
    _stub_provision(monkeypatch, versions=["0.7.15", "0.7.16"], ok=True, msg="installed")
    assert lic.sync_pro_from_config()[:3] == ("updated", "0.7.15", "0.7.16")


def test_first_install_reports_updated_with_empty_before(fake_home, monkeypatch):
    _write_config(fake_home, {"api_key": "cm_live_1", "node_id": "box"})
    _stub_provision(monkeypatch, versions=[None, "0.7.16"], ok=True, msg="installed")
    assert lic.sync_pro_from_config()[:3] == ("updated", "", "0.7.16")


def test_same_version_reports_current(fake_home, monkeypatch):
    _write_config(fake_home, {"api_key": "cm_live_1", "node_id": "box"})
    _stub_provision(monkeypatch, versions=["0.7.16", "0.7.16"], ok=True, msg="already")
    assert lic.sync_pro_from_config()[:3] == ("current", "0.7.16", "0.7.16")


def test_unreachable_server_keeps_the_installed_wheel(fake_home, monkeypatch):
    """auto_provision_pro returns (False, "") for a free account AND for a
    failed probe. With pro on disk, "kept" is the only honest answer —
    reporting "current" would claim a check we never completed."""
    _write_config(fake_home, {"api_key": "cm_live_1", "node_id": "box"})
    _stub_provision(monkeypatch, versions=["0.7.15", "0.7.15"], ok=False, msg="")
    assert lic.sync_pro_from_config()[:3] == ("kept", "0.7.15", "0.7.15")


def test_free_account_with_no_pro_installs_nothing(fake_home, monkeypatch):
    _write_config(fake_home, {"api_key": "cm_live_1", "node_id": "box"})
    _stub_provision(monkeypatch, versions=[None, None], ok=False, msg="")
    assert lic.sync_pro_from_config()[:3] == ("none", "", "")


def test_provisioner_exception_never_propagates(fake_home, monkeypatch):
    _write_config(fake_home, {"api_key": "cm_live_1", "node_id": "box"})
    monkeypatch.setattr(lic, "ensure_pro_on_path", lambda: None)
    monkeypatch.setattr(lic, "_pro_installed_version", lambda: "0.7.15")

    def _boom(key, node_id=None):
        raise RuntimeError("network exploded")

    monkeypatch.setattr(lic, "auto_provision_pro", _boom)
    state, _, _, msg = lic.sync_pro_from_config()
    assert state == "none"
    assert "network exploded" in msg


def test_explicit_config_argument_skips_the_disk_read(fake_home, monkeypatch):
    """Callers that already hold the node config (the sync daemon) can pass it
    in rather than re-reading it."""
    calls = _stub_provision(monkeypatch, versions=["0.7.15", "0.7.16"], ok=True)
    state, _, _, _ = lic.sync_pro_from_config({"api_key": "cm_live_2", "node_id": "n2"})
    assert state == "updated"
    assert calls == [("cm_live_2", "n2")]
