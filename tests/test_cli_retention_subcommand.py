"""Tests for the ``clawmetry retention`` CLI subcommand.

The subcommand is a thin read of :meth:`Entitlement.event_retention_days`
/ :meth:`Entitlement.effective_retention_days` and must never crash --
even when the entitlement resolver fails. Mirrors
``tests/test_cli_channels_subcommand.py`` so the CLI capacity trio
(channels / retention / nodes) is covered by the same shape of test.

The retention axis is capacity-scoped -- every event-store feature is
FREE at every tier; what upgrades unlock is a longer history window. So
``clawmetry retention --why N`` answers "what tier admits N-day
retention?" instead of "why is <feature> locked?". Payload shape must
match the shared lock-reason envelope so a wrapper script written
against the runtime / feature / channels variants also works here.
"""
from __future__ import annotations

import argparse
import json

import pytest


@pytest.fixture
def cli_mod(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so
    the resolver renders against the OSS-free default and never against a
    license that happens to live on the host. Also scrubs the retention
    override env var so its default (unset) is deterministic."""
    import importlib

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.delenv("CLAWMETRY_RETENTION_DAYS", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    import clawmetry.entitlements as ent

    importlib.reload(ent)
    ent.invalidate()

    import clawmetry.cli as cli  # imported after entitlements is rebuilt

    yield cli
    ent.invalidate()


def _ns(**kw) -> argparse.Namespace:
    kw.setdefault("as_json", False)
    kw.setdefault("why", None)
    return argparse.Namespace(**kw)


_WHY_EXPECTED_KEYS = {
    "key",
    "kind",
    "reason",
    "locked",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "upgrade_required",
}


# ── header block ───────────────────────────────────────────────────────────

def test_retention_header_advertises_tier_cap(cli_mod, capsys):
    cli_mod._cmd_retention(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "ClawMetry Retention" in out
    # OSS free cap is 7 days -- header must surface that so the operator
    # sees the axis the tier upgrade would extend.
    assert "Retention cap:   7 days" in out
    assert "Effective:       7 days" in out
    # In grace mode enforcement is off.
    assert "Enforcement:     off (grace)" in out


def test_retention_header_shows_env_override_when_set(cli_mod, capsys, monkeypatch):
    """A finite override below the tier cap must surface in the human
    block so operators can spot a retention downgrade coming from env."""
    monkeypatch.setenv("CLAWMETRY_RETENTION_DAYS", "3")
    cli_mod._cmd_retention(_ns(as_json=False))
    out = capsys.readouterr().out
    # Env row echoes the raw override value verbatim.
    assert "CLAWMETRY_RETENTION_DAYS: 3" in out
    # The effective cap is min(override, tier_cap) = min(3, 7) = 3.
    assert "Effective:       3 days" in out
    # The tier ceiling itself is unchanged.
    assert "Retention cap:   7 days" in out


def test_retention_header_env_row_reads_unset(cli_mod, capsys):
    cli_mod._cmd_retention(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "CLAWMETRY_RETENTION_DAYS: (unset)" in out


# ── JSON envelope ──────────────────────────────────────────────────────────

def test_retention_json_is_machine_readable(cli_mod, capsys):
    import clawmetry.entitlements as ent

    cli_mod._cmd_retention(_ns(as_json=True))
    payload = json.loads(capsys.readouterr().out)
    assert payload["tier"] == ent.TIER_OSS
    assert payload["grace"] is True
    assert payload["enforced"] is False
    assert payload["retention_days"] == 7
    assert payload["effective_retention_days"] == 7
    assert payload["override_env_name"] == "CLAWMETRY_RETENTION_DAYS"
    assert payload["override_env_value"] is None


def test_retention_json_reflects_env_override(cli_mod, capsys, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_RETENTION_DAYS", "3")
    cli_mod._cmd_retention(_ns(as_json=True))
    payload = json.loads(capsys.readouterr().out)
    assert payload["override_env_value"] == "3"
    assert payload["retention_days"] == 7
    # Effective cap = min(override, tier_cap).
    assert payload["effective_retention_days"] == 3


def test_retention_json_survives_broken_resolver(cli_mod, capsys, monkeypatch):
    """A poisoned :func:`get_entitlement` must produce a parseable payload
    with the fields collapsed to safe defaults -- not a stack trace."""
    import clawmetry.entitlements as ent

    def _boom():
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    cli_mod._cmd_retention(_ns(as_json=True))
    payload = json.loads(capsys.readouterr().out)
    assert payload["tier"] == "oss"
    assert payload["grace"] is True
    assert payload["enforced"] is False
    assert payload["retention_days"] is None
    assert payload["effective_retention_days"] is None


# ── enforcement ────────────────────────────────────────────────────────────

def test_retention_enforced_oss_still_shows_numeric_cap(
    cli_mod, capsys, monkeypatch
):
    """Enforced OSS installs still surface the numeric retention cap
    (7 days for the free tier). Only the enforcement label changes."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    import clawmetry.entitlements as ent

    ent.invalidate()
    cli_mod._cmd_retention(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "Enforcement:     on" in out
    assert "Retention cap:   7 days" in out


# ── --why (lock-reason payload) ────────────────────────────────────────────

def test_why_retention_json_matches_shared_envelope(cli_mod, capsys):
    """--why JSON must expose the same keys as the runtime / feature /
    channels variants so scripts written against either surface work
    interchangeably."""
    cli_mod._cmd_retention(_ns(as_json=True, why="30"))
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == _WHY_EXPECTED_KEYS
    assert payload["kind"] == "retention_days"
    assert payload["key"] == "30"


def test_why_retention_grace_reports_upgrade_target(cli_mod, capsys):
    """In grace mode, a window above the free cap must still surface the
    tier that would unlock it (locked=False but required_tier=cloud_starter
    + upgrade_required=True), matching the channels/runtime/feature preview
    behaviour. That's the guarantee the CLI can preview the upgrade ladder
    without flipping the enforce gate."""
    import clawmetry.entitlements as ent

    cli_mod._cmd_retention(_ns(as_json=True, why="30"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["locked"] is False  # grace mode
    assert payload["reason"] is None
    assert payload["current_tier"] == ent.TIER_OSS
    assert payload["required_tier"] == ent.TIER_CLOUD_STARTER
    assert payload["upgrade_required"] is True


def test_why_retention_under_free_cap_reports_no_upgrade(cli_mod, capsys):
    """A window that fits under the OSS free cap (7 days) resolves to
    required_tier=oss and upgrade_required=False even under grace so the
    CLI never dangles an upgrade CTA for a request the free floor already
    covers."""
    cli_mod._cmd_retention(_ns(as_json=True, why="7"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["locked"] is False
    assert payload["upgrade_required"] is False


def test_why_retention_enforce_locks_over_cap(cli_mod, capsys, monkeypatch):
    """With CLAWMETRY_ENFORCE=1, asking for more retention days than the
    OSS cap admits reports a real lock with a non-empty reason string and
    the upgrade CTA."""
    import clawmetry.entitlements as ent

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cli_mod._cmd_retention(_ns(as_json=True, why="30"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["locked"] is True
    assert payload["reason"], "reason string must be non-empty when locked"
    assert payload["required_tier"] == ent.TIER_CLOUD_STARTER
    assert payload["upgrade_required"] is True


def test_why_retention_non_int_returns_parseable_fallback(cli_mod, capsys):
    """A typo like ``--why abc`` must not crash and must not dangle an
    upgrade CTA -- otherwise a shell wrapper mistakes a typo for
    "no lock, all good"."""
    cli_mod._cmd_retention(_ns(as_json=True, why="abc"))
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == _WHY_EXPECTED_KEYS
    assert payload["kind"] == "retention_days"
    assert payload["locked"] is False
    assert payload["reason"] is None
    assert payload["required_tier"] is None
    assert payload["upgrade_required"] is False


def test_why_retention_human_block_uses_capacity_phrasing(
    cli_mod, capsys, monkeypatch
):
    """The non-JSON --why path uses a capacity-scoped header ("what tier
    unlocks N-day event retention?") since the key is a count, not an
    event-store id."""
    import clawmetry.entitlements as ent

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cli_mod._cmd_retention(_ns(as_json=False, why="30"))
    out = capsys.readouterr().out
    assert "what tier unlocks 30-day event retention?" in out
    assert "Kind:" in out and "retention_days" in out
    assert "Locked:" in out and "yes" in out
    assert "Reason:" in out
    assert "Required tier:" in out
    assert "clawmetry license activate <KEY>" in out


def test_why_retention_survives_broken_resolver(cli_mod, capsys, monkeypatch):
    """A poisoned :func:`get_entitlement` must produce the OSS-free fallback
    shape, not a stack trace."""
    import clawmetry.entitlements as ent

    def _boom():
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    cli_mod._cmd_retention(_ns(as_json=True, why="30"))
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == _WHY_EXPECTED_KEYS
    assert payload["kind"] == "retention_days"
    assert payload["current_tier"] == "oss"
    assert payload["locked"] is False
    assert payload["reason"] is None


# ── registration ───────────────────────────────────────────────────────────

def test_retention_subcommand_is_registered():
    """The subparser + dispatch table must list `retention` so it is
    reachable from the CLI entry point."""
    import inspect

    import clawmetry.cli as cli

    src = inspect.getsource(cli.main)
    assert '"retention"' in src
    assert "_cmd_retention" in src
