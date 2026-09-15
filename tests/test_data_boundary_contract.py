"""Data-boundary contract v1: what leaves a machine in each deployment mode.

docs/EGRESS.md is the wire inventory. Public pages summarise it, and in
September 2026 they summarised it wrongly in three ways that each read as a
privacy promise (vivekchand/clawmetry-landing#744):

1. "Cloud off: no network destination." Turning cloud sync off
   (``CLAWMETRY_NO_CLOUD=1``, ``clawmetry onboard --local``) stops uploads and
   nothing else. The install ping, the field-failure report and the PyPI
   version check still run. Only the egress gate turns them off.
2. A telemetry opt-out is not an update-check opt-out. ``DO_NOT_TRACK=1``
   silences the install ping and the failure report; PyPI is still asked.
3. ``CLAWMETRY_OFFLINE=1`` is the one switch that stops every discretionary
   request.

Plus the sealed-content invariant every mode leans on (no key, no content
upload) and the contract version EGRESS.md must carry, so a doc edit that
drops the distinction fails here instead of on a customer's packet capture.

Everything is exercised with the network layer replaced by a function that
fails the test if it is reached, except the one path whose POINT is that it
is reached (the update check on a cloud-sync-off install).
"""
from __future__ import annotations

import os

import pytest

from clawmetry import endpoints

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_ENV_KEYS = (
    "CLAWMETRY_ENDPOINT", "CLAWMETRY_INGEST_URL", "CLAWMETRY_APP_BASE",
    "SELF_HOSTED", "CLAWMETRY_SELF_HOSTED", "CLAWMETRY_OFFLINE",
    "CLAWMETRY_TELEMETRY_URL", "CLAWMETRY_NO_CLOUD", "CLAWMETRY_NO_TELEMETRY",
    "DO_NOT_TRACK", "CLAWMETRY_AUTO_UPDATE", "CI", "GITHUB_ACTIONS",
)


@pytest.fixture(autouse=True)
def _managed_default(monkeypatch, tmp_path):
    """A managed-cloud default install with no markers and no user config."""
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(endpoints, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(endpoints, "_cfg_cache", None)
    from clawmetry import config, telemetry

    monkeypatch.setattr(config, "NOCLOUD_MARKER_PATH", str(tmp_path / "nocloud"))
    monkeypatch.setattr(telemetry, "OPTOUT_MARKER", tmp_path / "notelemetry")
    yield


def _no_network(monkeypatch, what):
    def _fail(*a, **kw):  # pragma: no cover - reaching it is the failure
        raise AssertionError(f"{what} made a network call")

    monkeypatch.setattr("urllib.request.urlopen", _fail)


def _reached_update_check(monkeypatch):
    import routes.update_check as update_check

    reached = []

    def _record(*a, **kw):
        reached.append(a)
        raise RuntimeError("stop here: reaching the call is the assertion")

    monkeypatch.setattr("urllib.request.urlopen", _record)
    update_check._check_for_update()
    return bool(reached)


# ── 1. cloud sync off is not offline ────────────────────────────────────────

def test_cloud_sync_off_stops_uploads(monkeypatch):
    from clawmetry import config, sync

    monkeypatch.setenv("CLAWMETRY_NO_CLOUD", "1")
    assert config.is_cloud_disabled() is True
    _no_network(monkeypatch, "an upload with cloud sync off")
    out = sync._post("/ingest/heartbeat", {"node_id": "n"}, "cm_test")
    assert out.get("_cloud_disabled") is True


def test_cloud_sync_off_still_sends_the_discretionary_requests(monkeypatch):
    """The sentence a public page must not write: 'cloud off, no network destination'."""
    from clawmetry import field_report, telemetry

    monkeypatch.setenv("CLAWMETRY_NO_CLOUD", "1")
    assert endpoints.egress_suppressed() is False
    assert telemetry._resolve_telemetry_url() == telemetry.TELEMETRY_URL_DEFAULT
    assert field_report._suppressed() == ""
    assert _reached_update_check(monkeypatch), "cloud sync off must not be mistaken for offline"


# ── 2. telemetry opt-out stops pings, not the update check ─────────────────

@pytest.mark.parametrize("env", [{"DO_NOT_TRACK": "1"}, {"CLAWMETRY_NO_TELEMETRY": "1"}])
def test_telemetry_optout_stops_the_ping_and_failure_report_only(monkeypatch, env):
    from clawmetry import field_report, telemetry

    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert telemetry._is_optout() is True
    _no_network(monkeypatch, "the install ping after an opt-out")
    assert telemetry.maybe_ping("0.0.1") is None
    assert field_report._suppressed() == "telemetry_optout"
    assert endpoints.egress_suppressed() is False
    assert _reached_update_check(monkeypatch), "an opt-out is documented as not stopping the PyPI check"


# ── 3. explicit offline stops every discretionary request ──────────────────

def test_offline_stops_every_discretionary_request(monkeypatch):
    from clawmetry import cli, field_report, telemetry
    import routes.update_check as update_check

    monkeypatch.setenv("CLAWMETRY_OFFLINE", "1")
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "1")
    _no_network(monkeypatch, "an offline install")
    assert endpoints.egress_suppressed() is True
    assert telemetry._resolve_telemetry_url() == ""
    assert field_report._suppressed() == "egress_suppressed"
    assert update_check._check_for_update() is None
    target, _reason = cli._unattended_update_target("0.0.1")
    assert target is None


# ── sealed content needs a key, in every managed mode ──────────────────────

def test_sealed_content_is_never_uploaded_without_a_key():
    from clawmetry import sync

    for path in ("/ingest/events", "/ingest/logs", "/ingest/memory", "/ingest/stream"):
        assert sync.content_egress_permitted(None, path) is False
        assert sync.content_egress_permitted("", path) is False


# ── the document carries the contract ──────────────────────────────────────

def test_egress_doc_declares_the_contract():
    with open(os.path.join(_REPO, "docs", "EGRESS.md"), encoding="utf-8") as fh:
        doc = fh.read()
    assert "Data-boundary contract version: 1" in doc
    assert "not offline" in doc, "EGRESS.md must say cloud sync off is not offline"
    assert "CLAWMETRY_OFFLINE=1" in doc and "DO_NOT_TRACK=1" in doc
    assert "tests/test_data_boundary_contract.py" in doc
    # The browser, a paired device and a dashboard rotation all receive the
    # encryption key; "never leaves your machine" is the sentence that was false.
    assert "the key never leaves your machine" not in doc.lower()
    assert "rotat" in doc
