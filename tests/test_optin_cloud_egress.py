"""
Opt-in-only cloud egress (founder rule 2026-07-31).

Default install = SELF-HOSTED: nothing leaves the machine until the user
explicitly links an account (`clawmetry login` / `connect` / the managed
onboarding path), which persists an api_key. Previously gating was
opt-OUT only (the nocloud marker), so a self-hosted node with no account
POSTed X-Api-Key:"" heartbeats every ~55s and logged endless 401
warnings (found live on a Windows node).

These tests are the regression guard: with an empty api_key, _post() and
send_heartbeat() must return without ever touching the network. The
network-off proof is a monkeypatched urlopen that fails the test if
called — on the un-fixed code these tests go red (revert-proven).
"""
from __future__ import annotations

import urllib.request

import pytest

from clawmetry import config as cm_config
from clawmetry import sync as cm_sync


@pytest.fixture(autouse=True)
def _no_network(monkeypatch, tmp_path):
    """Fail loudly if anything tries real network; isolate the marker."""
    def _boom(*a, **kw):
        raise AssertionError("network egress attempted despite empty api_key")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    monkeypatch.setattr(cm_config, "NOCLOUD_MARKER_PATH",
                        str(tmp_path / "nocloud"))
    monkeypatch.delenv("CLAWMETRY_NO_CLOUD", raising=False)
    yield


def test_post_without_api_key_is_silent():
    resp = cm_sync._post("/ingest/heartbeat", {"node_id": "n1"}, api_key="")
    assert resp.get("_no_account") is True
    assert resp.get("sync_allowed") is False


def test_post_with_api_key_still_reaches_network(monkeypatch):
    """The gate must not swallow legitimate opted-in traffic."""
    calls = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"ok": true}'

    def _fake_urlopen(req, timeout=None):
        calls["url"] = req.full_url
        calls["key"] = req.headers.get("X-api-key")
        return _Resp()

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    resp = cm_sync._post("/ingest/heartbeat", {"node_id": "n1"}, api_key="cm_k")
    assert resp == {"ok": True}
    assert calls["key"] == "cm_k"


def test_heartbeat_without_api_key_is_silent():
    assert cm_sync.send_heartbeat({"node_id": "n1", "api_key": ""}) is False
    assert cm_sync.send_heartbeat({"node_id": "n1"}) is False


def test_cloud_egress_enabled_truth_table(tmp_path):
    assert cm_config.cloud_egress_enabled({}) is False
    assert cm_config.cloud_egress_enabled({"api_key": ""}) is False
    assert cm_config.cloud_egress_enabled({"api_key": "cm_k"}) is True
    # nocloud marker hard-disables even with a key
    marker = tmp_path / "nocloud"
    marker.write_text("x")
    orig = cm_config.NOCLOUD_MARKER_PATH
    cm_config.NOCLOUD_MARKER_PATH = str(marker)
    try:
        assert cm_config.cloud_egress_enabled({"api_key": "cm_k"}) is False
    finally:
        cm_config.NOCLOUD_MARKER_PATH = orig


def test_startup_banner_has_selfhosted_branch():
    """The one-line startup notice replaced the per-cycle 401 warning wall —
    keep it (and its login pointer) from silently disappearing."""
    import inspect

    src = inspect.getsource(cm_sync.run_daemon)
    assert "SELF-HOSTED: no cloud account linked" in src
    assert "clawmetry login" in src
