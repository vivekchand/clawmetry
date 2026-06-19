"""Tests for the ``clawmetry features`` CLI subcommand.

Sibling of ``tests/test_cli_runtimes_subcommand.py``: the subcommand is a thin
read of :func:`clawmetry.entitlements.feature_catalog` and must never crash --
even when the entitlement read itself fails. These tests cover the human
table, ``--json``, the locked-row CTA, the alias-row filter, and the OSS-free
fallback.
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


def test_features_table_lists_every_known_canonical_feature(cli_mod, capsys):
    import clawmetry.entitlements as ent

    cli_mod._cmd_features(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "ClawMetry Features" in out
    # Every non-alias feature in the catalogue surfaces -- no silent drops.
    for f in ent.ALL_FEATURES:
        if f in ent._ALIAS_FEATURES:
            continue
        assert f in out, f
    # Alias rows are hidden from the human table so the upgrade copy stays
    # scoped to the canonical names shown on /pricing.
    for alias in ent._ALIAS_FEATURES:
        assert alias not in out, alias
    # Default install is in grace mode → no lock affordance is shown yet.
    assert "Enforcement: off (grace)" in out
    assert "🔒 locked" not in out


def test_features_json_is_machine_readable(cli_mod, capsys):
    import clawmetry.entitlements as ent

    cli_mod._cmd_features(_ns(as_json=True))
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload["tier"] == ent.TIER_OSS
    assert payload["grace"] is True
    assert payload["enforced"] is False
    ids = {row["id"] for row in payload["features"]}
    # JSON path keeps the full catalogue (including aliases) so scripts
    # consuming the API shape don't see the rows disappear.
    assert ids == set(ent.ALL_FEATURES)
    for row in payload["features"]:
        assert {"id", "label", "tier", "free", "allowed", "locked"} <= set(row)


def test_features_enforced_oss_shows_paid_features_locked(
    cli_mod, capsys, monkeypatch
):
    import clawmetry.entitlements as ent

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cli_mod._cmd_features(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "Enforcement: on" in out
    # The CTA fires only when at least one row is locked.
    assert "clawmetry license activate <KEY>" in out
    # Free features never lock.
    for f in ent.FREE_FEATURES:
        line = next(ln for ln in out.splitlines() if ln.strip().startswith(f))
        assert "available" in line, f


def test_features_falls_back_when_catalog_errors(cli_mod, capsys, monkeypatch):
    """A poisoned feature_catalog() must not crash the CLI."""
    import clawmetry.entitlements as ent

    def _boom():
        raise RuntimeError("synthetic catalog failure")

    monkeypatch.setattr(ent, "feature_catalog", _boom)
    cli_mod._cmd_features(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "synthetic catalog failure" in out
    # JSON path also stays graceful.
    cli_mod._cmd_features(_ns(as_json=True))
    out_json = capsys.readouterr().out.strip()
    payload = json.loads(out_json)
    assert payload["features"] == []
    assert "synthetic catalog failure" in payload["error"]


def test_features_subcommand_is_registered():
    """The subparser + dispatch table must list `features` so it is reachable
    from the CLI entry point."""
    import inspect

    import clawmetry.cli as cli

    src = inspect.getsource(cli.main)
    assert '"features"' in src
    assert "_cmd_features" in src
