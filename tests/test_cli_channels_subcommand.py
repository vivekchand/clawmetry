"""Tests for the `clawmetry channels` CLI subcommand.

The subcommand is a thin read of ``clawmetry.entitlements.channel_catalog()``
and must never crash — even when the entitlement or catalog read fails.
Mirrors ``tests/test_cli_runtimes_subcommand.py`` /
``tests/test_cli_features_subcommand.py`` so the CLI trio (runtimes /
features / channels) is covered by the same shape of test.

Every chat-channel adapter is FREE at every tier (the ``channels``
capacity axis governs how many *concurrent* adapters each plan admits, not
which adapters unlock), so the table never shows a locked row. What the
header block advertises is the tier-scoped concurrent-channel cap.
"""
from __future__ import annotations

import argparse
import json

import pytest


@pytest.fixture
def cli_mod(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so the
    table is rendered against the OSS-free default and never against a
    license that happens to live on the host."""
    import importlib

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    import clawmetry.entitlements as ent

    importlib.reload(ent)
    ent.invalidate()

    import clawmetry.cli as cli  # imported after entitlements is rebuilt

    yield cli
    ent.invalidate()


def _ns(**kw) -> argparse.Namespace:
    return argparse.Namespace(**kw)


def test_channels_table_lists_every_known_adapter(cli_mod, capsys):
    import clawmetry.entitlements as ent

    cli_mod._cmd_channels(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "ClawMetry Channels" in out
    # Every adapter in the catalogue surfaces — no silent drops.
    for ch in ent.ALL_CHANNELS:
        assert ch in out, ch
    # Default install is in grace mode → no lock rows exist for channels.
    assert "Enforcement: off (grace)" in out
    assert "🔒 locked" not in out


def test_channels_header_advertises_concurrent_channel_cap(cli_mod, capsys):
    """OSS-free installs cap concurrent channels at 3; the header line must
    surface that so the operator sees the axis the tier upgrade unlocks."""
    cli_mod._cmd_channels(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "Channel cap:" in out
    # In grace mode ``channel_limit()`` returns None → header renders
    # "unlimited". That IS the correct display for grace; the enforced OSS
    # case (below) is where the numeric cap surfaces.
    assert "unlimited" in out


def test_channels_json_is_machine_readable(cli_mod, capsys):
    import clawmetry.entitlements as ent

    cli_mod._cmd_channels(_ns(as_json=True))
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload["tier"] == ent.TIER_OSS
    assert payload["grace"] is True
    assert payload["enforced"] is False
    assert "channel_limit" in payload
    ids = {row["id"] for row in payload["channels"]}
    assert ids == set(ent.ALL_CHANNELS)
    for row in payload["channels"]:
        # Row shape is byte-identical to a ``channel_catalog`` row.
        assert {"id", "label", "free", "allowed", "locked", "entitled"} <= set(row)
        # Every adapter is free at every tier — no paid-channel tier.
        assert row["free"] is True
        assert row["locked"] is False


def test_channels_enforced_oss_shows_numeric_cap(cli_mod, capsys, monkeypatch):
    """Enforced OSS installs surface the numeric concurrent-channel cap
    (3 for the free tier). The table itself stays lock-free because every
    adapter is FREE — only the capacity axis is what upgrades unlock."""
    import clawmetry.entitlements as ent

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cli_mod._cmd_channels(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "Enforcement: on" in out
    # OSS free cap is 3 concurrent adapters.
    assert "Channel cap: 3" in out
    # No adapter row is locked — every channel is free at every tier.
    assert "🔒 locked" not in out


def test_channels_falls_back_when_catalog_errors(cli_mod, capsys, monkeypatch):
    """A poisoned channel_catalog() must not crash the CLI."""
    import clawmetry.entitlements as ent

    def _boom():
        raise RuntimeError("synthetic catalog failure")

    monkeypatch.setattr(ent, "channel_catalog", _boom)
    cli_mod._cmd_channels(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "synthetic catalog failure" in out
    # JSON path also stays graceful.
    cli_mod._cmd_channels(_ns(as_json=True))
    out_json = capsys.readouterr().out.strip()
    payload = json.loads(out_json)
    assert payload["channels"] == []
    assert "synthetic catalog failure" in payload["error"]


def test_channels_subcommand_is_registered():
    """The subparser + dispatch table must list `channels` so it is
    reachable from the CLI entry point."""
    import inspect

    import clawmetry.cli as cli

    src = inspect.getsource(cli.main)
    assert '"channels"' in src
    assert "_cmd_channels" in src
