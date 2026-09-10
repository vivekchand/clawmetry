"""Where the cm_ cloud bearer lives, and how a legacy install is healed.

ClawMetry's own config (``~/.clawmetry/config.json`` → ``api_key``) is the
one place the bearer is written. It used to *also* be mirrored into
OpenClaw's own config as ``~/.openclaw/openclaw.json`` → ``clawmetry
.cloudToken``, and for a while that mirror was read FIRST.

That mirror is retired (field report 2026-09-09): ``clawmetry`` is not a key
in OpenClaw's schema, so every write left OpenClaw's config failing its own
validation, and OpenClaw's next CLI run fired ``doctor --fix`` — restoring the
last-known-good config and restarting the gateway mid-session.

These cases lock in the resolution order and the one-way migration:

  1. Only our config → returned (the normal, post-fix machine).
  2. Only the legacy mirror → still returned, so an install that predates
     the fix does not get logged out...
  3. ...and reading it MIGRATES: the token lands in our config and the
     ``clawmetry`` key is stripped out of OpenClaw's file, leaving every
     other OpenClaw key untouched.
  4. Both present → ours wins (the legacy copy can be arbitrarily stale).
  5. Neither → falsy, so cloud-proxy 401s and the UI renders the Cloud CTA.
"""

from __future__ import annotations

import importlib
import json

import pytest


@pytest.fixture
def reload_dashboard(tmp_path, monkeypatch):
    """Point HOME at a clean tmpdir and reimport both ``clawmetry.config``
    (which resolves its two config paths at import time) and ``dashboard``,
    so the helpers under test read/write inside the tmpdir."""
    monkeypatch.setenv("HOME", str(tmp_path))
    from clawmetry import config as cm_config
    importlib.reload(cm_config)
    cm_config.reset_legacy_migration_memo()
    import dashboard
    importlib.reload(dashboard)
    yield dashboard


def _write_openclaw(home, token, extra=None):
    p = home / ".openclaw"
    p.mkdir(parents=True, exist_ok=True)
    data = dict(extra or {})
    data["clawmetry"] = {"cloudToken": token}
    (p / "openclaw.json").write_text(json.dumps(data))


def _read_openclaw(home):
    return json.loads((home / ".openclaw" / "openclaw.json").read_text())


def _write_daemon(home, api_key):
    p = home / ".clawmetry"
    p.mkdir(parents=True, exist_ok=True)
    (p / "config.json").write_text(json.dumps({"api_key": api_key}))


def _read_daemon(home):
    return json.loads((home / ".clawmetry" / "config.json").read_text())


def test_clawmetry_config_is_the_source_of_truth(tmp_path, reload_dashboard):
    """The normal machine: the daemon's own config holds the bearer."""
    _write_daemon(tmp_path, "cm_551daemonkey")
    assert reload_dashboard._read_cloud_token() == "cm_551daemonkey"


def test_legacy_openclaw_mirror_is_still_read(tmp_path, reload_dashboard):
    """An install that predates the fix keeps working — we do not log a
    paired user out just because we stopped writing to that file."""
    _write_openclaw(tmp_path, "cm_openclaw_sidecar_token")
    assert reload_dashboard._read_cloud_token() == "cm_openclaw_sidecar_token"


def test_reading_the_legacy_mirror_migrates_and_uncorrupts(
    tmp_path, reload_dashboard
):
    """Reading the legacy mirror moves the token into our own config AND
    removes the offending key from OpenClaw's — healing the config that
    made ``openclaw doctor --fix`` restart the gateway. Every other
    OpenClaw key survives."""
    _write_openclaw(
        tmp_path, "cm_legacy_token", extra={"gateway": {"port": 18789}}
    )
    assert reload_dashboard._read_cloud_token() == "cm_legacy_token"

    assert _read_daemon(tmp_path)["api_key"] == "cm_legacy_token"
    after = _read_openclaw(tmp_path)
    assert "clawmetry" not in after, (
        "the key OpenClaw's schema rejects must be gone after a read"
    )
    assert after["gateway"] == {"port": 18789}, (
        "migration must never touch keys that belong to OpenClaw"
    )


def test_our_config_wins_and_still_strips_the_stale_mirror(
    tmp_path, reload_dashboard
):
    """When both exist ours wins — the legacy copy can be arbitrarily
    stale — and the stale copy is stripped so OpenClaw stops failing
    validation on it."""
    _write_openclaw(tmp_path, "cm_stale_do_not_use")
    _write_daemon(tmp_path, "cm_current")
    assert reload_dashboard._read_cloud_token() == "cm_current"
    assert "clawmetry" not in _read_openclaw(tmp_path)
    assert _read_daemon(tmp_path)["api_key"] == "cm_current"


def test_neither_present_returns_falsy(tmp_path, reload_dashboard):
    """No config at all → falsy so cloud-proxy returns 401 and the UI
    renders the cloud-CTA panel as designed."""
    assert not reload_dashboard._read_cloud_token()


def test_daemon_key_must_have_cm_prefix(tmp_path, reload_dashboard):
    """A malformed ``api_key`` (no ``cm_`` prefix) is rejected so we
    don't pass garbage strings as the bearer."""
    _write_daemon(tmp_path, "garbage-no-prefix")
    assert not reload_dashboard._read_cloud_token()


def test_write_never_touches_openclaws_config(tmp_path, reload_dashboard):
    """The whole point of the fix: persisting the bearer leaves
    ``~/.openclaw/openclaw.json`` byte-identical."""
    oc = tmp_path / ".openclaw"
    oc.mkdir(parents=True, exist_ok=True)
    original = json.dumps({"gateway": {"port": 18789}, "chat": {}}, indent=2)
    (oc / "openclaw.json").write_text(original)

    reload_dashboard._write_cloud_token("cm_freshly_paired")

    assert (oc / "openclaw.json").read_text() == original
    assert _read_daemon(tmp_path)["api_key"] == "cm_freshly_paired"


def test_write_preserves_the_daemons_other_config_keys(
    tmp_path, reload_dashboard
):
    """``node_id`` / ``encryption_key`` live in the same file — a token
    write must merge, not clobber, or the node loses its identity and
    every already-pushed snapshot becomes undecryptable."""
    p = tmp_path / ".clawmetry"
    p.mkdir(parents=True, exist_ok=True)
    (p / "config.json").write_text(json.dumps({
        "api_key": "cm_old",
        "node_id": "node-42",
        "encryption_key": "deadbeef",
    }))

    reload_dashboard._write_cloud_token("cm_new")

    data = _read_daemon(tmp_path)
    assert data["api_key"] == "cm_new"
    assert data["node_id"] == "node-42"
    assert data["encryption_key"] == "deadbeef"
