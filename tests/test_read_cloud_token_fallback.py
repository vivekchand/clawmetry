"""Audit P0 #5 — `_read_cloud_token` falls back to the daemon's own config.

Before this fix, ``dashboard._read_cloud_token`` only looked at
``~/.openclaw/openclaw.json:clawmetry.cloudToken`` (written by
``clawmetry connect``). On machines where the daemon was paired via
``python -m clawmetry.sync`` (which writes ``~/.clawmetry/config.json``)
the dashboard never saw the bearer and the entire Alerts UI 401'd via
``/api/cloud-proxy/*`` even though cloud sync was live.

These three cases lock in the new resolution order:

  1. OpenClaw sidecar present → preferred (legacy explicit-connect win).
  2. Only the daemon config present → fallback returns its ``api_key``.
  3. Neither present → returns falsy (caller renders Cloud-CTA).
"""

from __future__ import annotations

import importlib
import json

import pytest


@pytest.fixture
def reload_dashboard(tmp_path, monkeypatch):
    """Point HOME at a clean tmpdir + reimport dashboard so the path
    helpers in ``_read_cloud_token`` resolve there. Yields the freshly
    reloaded ``dashboard`` module."""
    monkeypatch.setenv("HOME", str(tmp_path))
    # On macOS some libs read $USER's home via pwd; HOME-based expansion
    # is what os.path.expanduser uses, which is all we care about here.
    import dashboard
    importlib.reload(dashboard)
    yield dashboard


def _write_openclaw(home, token):
    p = home / ".openclaw"
    p.mkdir(parents=True, exist_ok=True)
    (p / "openclaw.json").write_text(
        json.dumps({"clawmetry": {"cloudToken": token}})
    )


def _write_daemon(home, api_key):
    p = home / ".clawmetry"
    p.mkdir(parents=True, exist_ok=True)
    (p / "config.json").write_text(json.dumps({"api_key": api_key}))


def test_openclaw_sidecar_only_present(tmp_path, reload_dashboard):
    """Legacy path still works: when only the OpenClaw sidecar config
    is present, its ``cloudToken`` is returned untouched."""
    _write_openclaw(tmp_path, "openclaw-sidecar-token-xyz")
    assert reload_dashboard._read_cloud_token() == "openclaw-sidecar-token-xyz"


def test_clawmetry_config_only_present(tmp_path, reload_dashboard):
    """Audit P0 #5 — daemon-only paired machine now resolves to the
    ``api_key`` instead of returning None and trapping the Alerts UI."""
    _write_daemon(tmp_path, "cm_551daemonkey")
    assert reload_dashboard._read_cloud_token() == "cm_551daemonkey"


def test_neither_present_returns_falsy(tmp_path, reload_dashboard):
    """No config at all → falsy so cloud-proxy returns 401 and the UI
    renders the cloud-CTA panel as designed."""
    assert not reload_dashboard._read_cloud_token()


def test_openclaw_wins_when_both_present(tmp_path, reload_dashboard):
    """If both sources exist, the OpenClaw sidecar token wins so an
    explicit ``clawmetry connect`` write isn't shadowed by the daemon
    pairing key."""
    _write_openclaw(tmp_path, "openclaw-wins")
    _write_daemon(tmp_path, "cm_should-not-be-used")
    assert reload_dashboard._read_cloud_token() == "openclaw-wins"


def test_daemon_key_must_have_cm_prefix(tmp_path, reload_dashboard):
    """A malformed ``api_key`` (no ``cm_`` prefix) is rejected so we
    don't pass garbage strings as the bearer."""
    _write_daemon(tmp_path, "garbage-no-prefix")
    assert not reload_dashboard._read_cloud_token()
