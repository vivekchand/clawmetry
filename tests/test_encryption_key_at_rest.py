"""
Test that encryption_key is stored encrypted at rest.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest


def test_encryption_key_not_plaintext_in_config(tmp_path, monkeypatch):
    """
    Verify that encryption_key is NOT stored in plaintext in config.json.

    The encryption_key should be encrypted using a machine-derived key before
    being stored in the config file, so that reading the raw config file
    does not reveal the encryption key.
    """
    from clawmetry.sync import save_config, load_config, CONFIG_FILE, CONFIG_DIR

    # Use a temp config directory to avoid interfering with real config
    monkeypatch.setattr("clawmetry.sync.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("clawmetry.sync.CONFIG_FILE", tmp_path / "config.json")

    test_config = {
        "api_key": "test_api_key_12345",
        "node_id": "test_node_id",
        "platform": "test_platform",
        "connected_at": "2024-01-01T00:00:00",
        "encryption_key": "super_secret_encryption_key_base64url_12345",
    }

    # Save config with encryption_key
    save_config(test_config)

    # Read the raw config file
    raw_config_path = tmp_path / "config.json"
    raw_content = raw_config_path.read_text()
    raw_data = json.loads(raw_content)

    # The raw file should NOT contain the plaintext encryption key
    assert (
        raw_data.get("encryption_key") != "super_secret_encryption_key_base64url_12345"
    ), "encryption_key is stored in plaintext! It should be encrypted at rest."

    # Additionally, it should NOT be possible to find the plaintext key in the raw file
    assert "super_secret_encryption_key_base64url_12345" not in raw_content, (
        "Plaintext encryption key found in config file! Key must be encrypted at rest."
    )

    # Verify that loading the config returns the original key
    loaded_config = load_config()
    assert (
        loaded_config["encryption_key"] == "super_secret_encryption_key_base64url_12345"
    ), "Loaded encryption_key does not match the original!"
