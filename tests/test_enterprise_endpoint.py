"""Endpoint resolution order for enterprise self-hosting (clawmetry/endpoints.py).

Contract: env CLAWMETRY_ENDPOINT > env CLAWMETRY_INGEST_URL (legacy) >
config-file "endpoint" key > managed cloud default. App-side calls follow a
custom endpoint (single self-hosted host), with CLAWMETRY_APP_BASE as an
explicit split override.
"""
import json

import pytest

from clawmetry import endpoints

_ENV_VARS = ("CLAWMETRY_ENDPOINT", "CLAWMETRY_INGEST_URL", "CLAWMETRY_APP_BASE")


@pytest.fixture
def clean_endpoints(monkeypatch, tmp_path):
    """No env overrides, config path sandboxed to tmp, resolver cache reset."""
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    cfg = tmp_path / "config.json"
    monkeypatch.setattr(endpoints, "CONFIG_PATH", str(cfg))
    monkeypatch.setattr(endpoints, "_cfg_cache", None)
    return cfg


def _write_cfg(cfg_path, data):
    cfg_path.write_text(json.dumps(data), encoding="utf-8")
    # Bust the mtime-keyed cache (same-second writes on coarse filesystems).
    endpoints._cfg_cache = None


def test_default_is_managed_cloud(clean_endpoints):
    assert endpoints.ingest_url() == "https://ingest.clawmetry.com"
    assert endpoints.app_url() == "https://app.clawmetry.com"
    assert endpoints.is_custom_endpoint() is False


def test_config_key_overrides_default(clean_endpoints):
    _write_cfg(clean_endpoints, {"endpoint": "https://cm.corp.example/"})
    assert endpoints.ingest_url() == "https://cm.corp.example"
    # App-side traffic follows the single self-hosted host.
    assert endpoints.app_url() == "https://cm.corp.example"
    assert endpoints.is_custom_endpoint() is True


def test_legacy_ingest_env_beats_config(clean_endpoints, monkeypatch):
    _write_cfg(clean_endpoints, {"endpoint": "https://from-config.example"})
    monkeypatch.setenv("CLAWMETRY_INGEST_URL", "https://from-legacy-env.example")
    assert endpoints.ingest_url() == "https://from-legacy-env.example"


def test_endpoint_env_beats_everything(clean_endpoints, monkeypatch):
    _write_cfg(clean_endpoints, {"endpoint": "https://from-config.example"})
    monkeypatch.setenv("CLAWMETRY_INGEST_URL", "https://from-legacy-env.example")
    monkeypatch.setenv("CLAWMETRY_ENDPOINT", "https://from-env.example/")
    assert endpoints.ingest_url() == "https://from-env.example"
    assert endpoints.app_url() == "https://from-env.example"


def test_app_base_env_is_explicit_split_override(clean_endpoints, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENDPOINT", "https://ingest.corp.example")
    monkeypatch.setenv("CLAWMETRY_APP_BASE", "https://app.corp.example")
    assert endpoints.ingest_url() == "https://ingest.corp.example"
    assert endpoints.app_url() == "https://app.corp.example"


def test_blank_config_key_falls_through(clean_endpoints):
    _write_cfg(clean_endpoints, {"endpoint": "  "})
    assert endpoints.ingest_url() == "https://ingest.clawmetry.com"


def test_missing_or_broken_config_never_raises(clean_endpoints):
    # Missing file
    assert endpoints.ingest_url() == "https://ingest.clawmetry.com"
    # Broken JSON
    clean_endpoints.write_text("{not json", encoding="utf-8")
    endpoints._cfg_cache = None
    assert endpoints.ingest_url() == "https://ingest.clawmetry.com"


def test_endpoint_hosts_for_interceptor_exclusion(clean_endpoints, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENDPOINT", "https://cm.corp.example:8443/base")
    hosts = endpoints.endpoint_hosts()
    assert "cm.corp.example" in hosts


def test_sync_module_constant_uses_resolver(clean_endpoints, monkeypatch):
    """sync.INGEST_URL snapshots the resolver at import — re-importing under a
    custom env must repoint it (this is what a daemon restart does)."""
    import importlib

    import clawmetry.sync as sync_mod

    monkeypatch.setenv("CLAWMETRY_ENDPOINT", "https://reimport.example")
    try:
        importlib.reload(sync_mod)
        assert sync_mod.INGEST_URL == "https://reimport.example"
    finally:
        monkeypatch.delenv("CLAWMETRY_ENDPOINT")
        importlib.reload(sync_mod)
        assert sync_mod.INGEST_URL == "https://ingest.clawmetry.com"
