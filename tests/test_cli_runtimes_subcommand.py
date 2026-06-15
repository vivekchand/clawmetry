"""Tests for the `clawmetry runtimes` CLI subcommand.

The subcommand is a thin read of clawmetry.entitlements.runtime_catalog() and
must never crash — even when the entitlement read itself fails. These tests
cover the human table, --json, the locked-row CTA, and the OSS-free fallback.
"""
from __future__ import annotations

import argparse
import json

import pytest


@pytest.fixture
def cli_mod(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so the
    table is rendered against the OSS-free default and never against a license
    that happens to live on the host."""
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


def test_runtimes_table_lists_every_known_runtime(cli_mod, capsys):
    import clawmetry.entitlements as ent

    cli_mod._cmd_runtimes(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "ClawMetry Runtimes" in out
    # Every runtime in the catalogue surfaces — no silent drops.
    for rt in ent.ALL_RUNTIMES:
        assert rt in out, rt
    # Default install is in grace mode → no lock affordance is shown yet.
    assert "Enforcement: off (grace)" in out
    assert "🔒 locked" not in out


def test_runtimes_json_is_machine_readable(cli_mod, capsys):
    import clawmetry.entitlements as ent

    cli_mod._cmd_runtimes(_ns(as_json=True))
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload["tier"] == ent.TIER_OSS
    assert payload["grace"] is True
    assert payload["enforced"] is False
    ids = {row["id"] for row in payload["runtimes"]}
    assert ids == set(ent.ALL_RUNTIMES)
    for row in payload["runtimes"]:
        assert {"id", "label", "free", "allowed", "locked"} <= set(row)


def test_runtimes_enforced_oss_shows_paid_runtimes_locked(cli_mod, capsys, monkeypatch):
    import clawmetry.entitlements as ent

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cli_mod._cmd_runtimes(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "Enforcement: on" in out
    # The CTA fires only when at least one row is locked.
    assert "clawmetry license activate <KEY>" in out
    # Free runtimes never lock.
    for rt in ent.FREE_RUNTIMES:
        # Find the line for this id and confirm it is marked available.
        line = next(ln for ln in out.splitlines() if ln.strip().startswith(rt))
        assert "available" in line, rt


def test_runtimes_falls_back_when_catalog_errors(cli_mod, capsys, monkeypatch):
    """A poisoned runtime_catalog() must not crash the CLI."""
    import clawmetry.entitlements as ent

    def _boom():
        raise RuntimeError("synthetic catalog failure")

    monkeypatch.setattr(ent, "runtime_catalog", _boom)
    cli_mod._cmd_runtimes(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "synthetic catalog failure" in out
    # JSON path also stays graceful.
    cli_mod._cmd_runtimes(_ns(as_json=True))
    out_json = capsys.readouterr().out.strip()
    payload = json.loads(out_json)
    assert payload["runtimes"] == []
    assert "synthetic catalog failure" in payload["error"]


def test_runtimes_subcommand_is_registered():
    """The subparser + dispatch table must list `runtimes` so it is reachable
    from the CLI entry point."""
    import inspect

    import clawmetry.cli as cli

    src = inspect.getsource(cli.main)
    assert '"runtimes"' in src
    assert "_cmd_runtimes" in src
