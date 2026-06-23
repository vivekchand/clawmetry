"""Regression: a local-only config (no api_key) must not crash the daemon.

The install fork (#3281) added a [1] Local only onboard path that writes a
config WITHOUT an api_key. The daemon startup path subscripts
config["api_key"] (start_log_streamer + ~12 sites), so loading such a config
KeyError-crashed run_daemon on every boot in 0.12.526, leaving the local store
empty (no OpenClaw sessions ingested). load_config() now normalizes the shape.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_load_config_fills_missing_api_key(tmp_path, monkeypatch):
    import clawmetry.sync as sync

    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"node_id": "box-1", "local_only": True}))
    monkeypatch.setattr(sync, "CONFIG_FILE", cfg)

    data = sync.load_config()
    assert data["api_key"] == "", "missing api_key must normalize to '' not KeyError"
    assert data["node_id"] == "box-1"
    # The subscript that crashed the daemon must now succeed.
    assert data["api_key"] == ""  # config["api_key"] style access is safe


def test_load_config_defaults_node_id_when_absent(tmp_path, monkeypatch):
    import clawmetry.sync as sync

    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"local_only": True}))  # neither api_key nor node_id
    monkeypatch.setattr(sync, "CONFIG_FILE", cfg)

    data = sync.load_config()
    assert data["api_key"] == ""
    assert data["node_id"], "node_id must default to a non-empty hostname"


def test_load_config_preserves_existing_values(tmp_path, monkeypatch):
    import clawmetry.sync as sync

    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"api_key": "cm_real", "node_id": "n9", "encryption_key": "k"}))
    monkeypatch.setattr(sync, "CONFIG_FILE", cfg)

    data = sync.load_config()
    assert data["api_key"] == "cm_real"  # do not clobber a real key
    assert data["node_id"] == "n9"
    assert data["encryption_key"] == "k"
