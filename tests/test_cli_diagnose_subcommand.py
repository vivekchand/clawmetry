"""Tests for the `clawmetry diagnose` CLI subcommand.

The subcommand is a thin read of
``clawmetry.entitlements.resolution_diagnostic()`` and must never crash --
even when the resolver itself blows up. Mirrors
``tests/test_cli_channels_subcommand.py`` /
``tests/test_cli_features_subcommand.py`` /
``tests/test_cli_runtimes_subcommand.py`` so the CLI diagnostic quartet
(tier / runtimes / features / channels / diagnose) is covered by the
same shape of test.

The diagnose surface is not tier-gated -- it emits the *inputs* the
resolver consulted (license file present, cloud plan cached, enforce
env, cache age/ttl), not the tier grants themselves -- so a Free install
sees the same shape a Pro install does. What flips between installs is
whether the license/cloud rows are populated, and whether the enforce
env is set.
"""
from __future__ import annotations

import argparse
import json

import pytest


@pytest.fixture
def cli_mod(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so
    the diagnostic block is rendered against the OSS-free default and
    never against a license that happens to live on the host."""
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


def test_diagnose_block_surfaces_resolver_inputs(cli_mod, capsys):
    cli_mod._cmd_diagnose(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "ClawMetry Diagnose" in out
    # The four resolver inputs the diagnostic exists to answer for.
    assert "License file:" in out
    assert "Cloud plan cache:" in out
    assert "Enforce env:" in out
    assert "Cache TTL (s):" in out
    # Default (empty) install is grace mode with no license and no cloud
    # plan cache -- both rows must render "no", not silently disappear.
    assert "no" in out.split("License file:", 1)[1].split("\n", 1)[0]
    assert "no" in out.split("Cloud plan cache:", 1)[1].split("\n", 1)[0]
    # Grace surfaces as "no (grace)" on the Enforced row.
    assert "no (grace)" in out


def test_diagnose_json_is_machine_readable(cli_mod, capsys):
    cli_mod._cmd_diagnose(_ns(as_json=True))
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    # The JSON payload IS resolution_diagnostic() verbatim -- the CLI
    # must never re-shape the dict, since scripts pin the keys.
    for key in (
        "license_path",
        "license_present",
        "license_size_bytes",
        "cloud_plan_path",
        "cloud_plan_present",
        "cloud_plan_size_bytes",
        "enforce_env",
        "is_enforced",
        "cache_age_seconds",
        "cache_ttl_seconds",
        "cache_hit_next_call",
        "cache_cached_tier",
        "retention_override_env_name",
        "retention_override_env_value",
    ):
        assert key in payload, key
    # Default install: no license, no cloud plan, no enforce env.
    assert payload["license_present"] is False
    assert payload["cloud_plan_present"] is False
    assert payload["is_enforced"] is False


def test_diagnose_enforced_env_flips_is_enforced(cli_mod, capsys, monkeypatch):
    """Setting CLAWMETRY_ENFORCE=1 must flip the ``is_enforced`` bit AND
    surface the raw env value on the ``enforce_env`` key so an operator
    debugging "why is enforce on?" sees both signals."""
    import clawmetry.entitlements as ent

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cli_mod._cmd_diagnose(_ns(as_json=True))
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["enforce_env"] == "1"
    assert payload["is_enforced"] is True


def test_diagnose_reflects_license_file_present(cli_mod, capsys, tmp_path):
    """When ~/.clawmetry/license.key exists, ``license_present`` flips
    to True and ``license_size_bytes`` reports the file size. The
    resolver contract only depends on file presence + size for this
    surface; whether the key is valid is a separate concern the
    diagnostic does NOT try to answer."""
    import os

    import clawmetry.entitlements as ent

    lic_dir = tmp_path / ".clawmetry"
    lic_dir.mkdir(parents=True, exist_ok=True)
    lic_file = lic_dir / "license.key"
    lic_file.write_bytes(b"stub-license-payload")
    # The module already snapshotted _LICENSE_PATH from HOME -- monkeypatch
    # it so the stat() in resolution_diagnostic() reaches the file we just
    # wrote regardless of when the module was reloaded relative to HOME.
    ent._LICENSE_PATH = str(lic_file)

    cli_mod._cmd_diagnose(_ns(as_json=True))
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["license_present"] is True
    assert payload["license_size_bytes"] == os.path.getsize(str(lic_file))


def test_diagnose_falls_back_when_resolver_errors(cli_mod, capsys, monkeypatch):
    """A poisoned resolution_diagnostic() must not crash the CLI -- both
    the human and JSON paths degrade to a parseable shape."""
    import clawmetry.entitlements as ent

    def _boom():
        raise RuntimeError("synthetic diagnostic failure")

    monkeypatch.setattr(ent, "resolution_diagnostic", _boom)

    # Human path: warning + inline "diagnostic error" line, no traceback.
    cli_mod._cmd_diagnose(_ns(as_json=False))
    captured = capsys.readouterr()
    assert "synthetic diagnostic failure" in captured.err
    assert "diagnostic error" in captured.out

    # JSON path: empty payload with an ``error`` key surfaced so the
    # wrapper script sees the failure without a shell exit code trap.
    cli_mod._cmd_diagnose(_ns(as_json=True))
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload.get("error") == "synthetic diagnostic failure"


def test_diagnose_subcommand_is_registered():
    """The subparser + dispatch table must list ``diagnose`` so the
    subcommand is reachable from the CLI entry point (and so the
    single-token dispatch in ``main()`` recognises it as a subcommand,
    not a dashboard flag)."""
    import inspect

    import clawmetry.cli as cli

    src = inspect.getsource(cli.main)
    assert '"diagnose"' in src
    assert "_cmd_diagnose" in src
