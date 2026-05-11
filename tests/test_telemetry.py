"""Tests for clawmetry/telemetry.py — first-run anonymous install ping.

These tests stub the network layer entirely so nothing actually leaves
the box. The telemetry module is intentionally fault-tolerant, so we
also test the failure paths (network down, can't write install_id,
opt-out) all stay silent.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def telemetry(monkeypatch, tmp_path):
    """Reload telemetry with CONFIG_DIR pointed at a tmp path so the
    test never touches the user's real ~/.clawmetry/."""
    from clawmetry import telemetry as t
    importlib.reload(t)
    monkeypatch.setattr(t, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(t, "INSTALL_ID_FILE", tmp_path / "install_id")
    monkeypatch.setattr(t, "OPTOUT_MARKER", tmp_path / "notelemetry")
    # Strip any CI env vars the test runner might have set so detection
    # tests aren't poisoned by GitHub Actions itself.
    for k in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI", "TRAVIS",
              "BUILDKITE", "JENKINS_URL", "TEAMCITY_VERSION",
              "BITBUCKET_BUILD_NUMBER", "CODEBUILD_BUILD_ID", "DRONE",
              "AGENT_NAME", "CLAWMETRY_NO_TELEMETRY", "DO_NOT_TRACK"):
        monkeypatch.delenv(k, raising=False)
    return t


def test_optout_via_env(telemetry, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_NO_TELEMETRY", "1")
    assert telemetry._is_optout() is True
    assert telemetry.maybe_ping("0.0.0") is None


def test_optout_via_do_not_track(telemetry, monkeypatch):
    """W3C-style cross-tool opt-out should also disable us."""
    monkeypatch.setenv("DO_NOT_TRACK", "1")
    assert telemetry._is_optout() is True


def test_optout_env_falsy_values_are_off(telemetry, monkeypatch):
    """Empty / 0 / false should NOT be treated as opt-out."""
    for val in ("", "0", "false", "False"):
        monkeypatch.setenv("CLAWMETRY_NO_TELEMETRY", val)
        assert telemetry._is_optout() is False, f"unexpected opt-out for {val!r}"


def test_optout_via_marker_file(telemetry):
    telemetry.OPTOUT_MARKER.touch()
    assert telemetry._is_optout() is True


def test_install_id_persisted_and_reused(telemetry):
    a = telemetry._ensure_install_id()
    b = telemetry._ensure_install_id()
    assert a == b, "second call must return the same id"
    assert telemetry.INSTALL_ID_FILE.exists()


def test_install_id_regenerated_if_corrupted(telemetry):
    """A garbage install_id file should be replaced, not crash."""
    telemetry.INSTALL_ID_FILE.write_text("not-a-uuid! has spaces and bangs\n")
    new = telemetry._ensure_install_id()
    assert new and len(new) > 16
    assert " " not in new


def test_ci_detection_priority(telemetry, monkeypatch):
    """When multiple CI vars are set, the more-specific one wins."""
    # Some providers leave CI=true set even when running in a different
    # provider's environment; the specific provider should be picked.
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    is_ci, name = telemetry._detect_ci()
    assert is_ci is True
    assert name == "github_actions"


def test_ci_detection_none(telemetry):
    is_ci, name = telemetry._detect_ci()
    assert is_ci is False
    assert name is None


def test_agent_detection_openclaw(telemetry, tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (fake_home / ".openclaw").mkdir()
    monkeypatch.setattr(telemetry, "_AGENT_DIRS",
                        (("openclaw", fake_home / ".openclaw"),))
    assert telemetry._detect_agent() == "openclaw"


def test_agent_detection_none(telemetry, tmp_path, monkeypatch):
    monkeypatch.setattr(telemetry, "_AGENT_DIRS",
                        (("openclaw", tmp_path / "nope"),))
    assert telemetry._detect_agent() == "none"


def test_payload_shape(telemetry):
    p = telemetry._build_payload("9.9.9")
    # Required fields
    assert set(p) == {"install_id", "event", "version", "os", "os_version",
                      "python", "agent", "is_ci", "ci_provider"}
    assert p["event"] == "first_run"
    assert p["version"] == "9.9.9"
    assert p["os"]  # platform.system() always returns something
    # PII NOT in payload
    payload_str = json.dumps(p).lower()
    import getpass, socket
    assert getpass.getuser().lower() not in payload_str
    assert socket.gethostname().lower() not in payload_str


def test_post_swallows_network_error(telemetry):
    """A 500 / DNS failure / timeout must NEVER raise."""
    def boom(*a, **kw):
        raise OSError("network down")
    with patch("urllib.request.urlopen", side_effect=boom):
        # Should not raise.
        telemetry._post({"install_id": "x", "version": "1.0.0"},
                        "http://example.invalid/api/install")


def test_pinged_marker_prevents_double_post(telemetry):
    """Once we've successfully pinged, subsequent _send_in_background
    calls must be no-ops to avoid hammering the cloud."""
    install_id = telemetry._ensure_install_id()
    assert telemetry._has_pinged_this_install(install_id) is False
    telemetry._mark_pinged(install_id)
    assert telemetry._has_pinged_this_install(install_id) is True


def test_maybe_ping_optout_returns_none(telemetry, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_NO_TELEMETRY", "1")
    with patch("urllib.request.urlopen") as urlopen:
        result = telemetry.maybe_ping("0.0.0")
        # No thread spawned, no network call.
        assert result is None
        urlopen.assert_not_called()


def test_maybe_ping_spawns_daemon_thread(telemetry):
    """Happy path: thread is started, daemon=True, won't block exit."""
    with patch("urllib.request.urlopen"):
        t = telemetry.maybe_ping("0.0.0")
        assert t is not None
        assert t.daemon is True
        t.join(timeout=5)


def test_payload_omits_ci_provider_when_not_ci(telemetry):
    """ci_provider should be None when is_ci is False — server filters
    these out of the 'CI installs' table."""
    p = telemetry._build_payload("0.0.0")
    if not p["is_ci"]:
        assert p["ci_provider"] is None
