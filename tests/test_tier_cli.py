"""Tests for ``clawmetry tier`` — the scriptable entitlement read-out.

The CLI subcommand is a thin shell around :func:`clawmetry.entitlements.get_entitlement`,
so these tests pin the *contract* surface:

* a default (no-flag) invocation prints a human-readable block,
* ``--json`` emits parseable JSON whose top-level keys mirror
  ``Entitlement.to_dict()``,
* the command never raises — a broken resolver still produces a usable
  OSS-free fallback so shell wrappers see a valid response,
* the subparser is wired and ``tier`` is in the dispatcher's allowlist.

It does not assert specific tier *values* beyond OSS-free, because the
resolver's tier set is the domain of ``tests/test_entitlements.py`` and
other parallel PRs are extending it.
"""
from __future__ import annotations

import importlib
import json
import sys
from types import SimpleNamespace

import pytest

import clawmetry.cli as cli


@pytest.fixture
def grace_oss(monkeypatch, tmp_path):
    """Force a clean OSS-free / grace-mode resolver across the test.

    Mirrors the fixture in ``tests/test_entitlements.py``: blow away any
    inherited license / cloud plan by repointing ``$HOME`` at an empty dir,
    drop ``CLAWMETRY_ENFORCE`` and reload :mod:`clawmetry.entitlements` so its
    expanded paths use the patched home. The cache is invalidated on entry
    and exit so neighbouring tests can't poison this one.
    """
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── plain-text mode ──────────────────────────────────────────────────────────


def test_cmd_tier_plain_output(grace_oss, capsys):
    """Default output is the human-readable block used by ``clawmetry tier``."""
    cli._cmd_tier(SimpleNamespace(as_json=False))
    out = capsys.readouterr().out
    assert "ClawMetry Tier" in out
    assert "Tier:" in out
    assert "Mode:" in out
    # OSS-free + grace is the headline default-install state.
    assert "OSS" in out
    assert "grace" in out


def test_cmd_tier_plain_lists_free_runtimes(grace_oss, capsys):
    """The Runtimes line surfaces every free runtime in the catalog."""
    cli._cmd_tier(SimpleNamespace(as_json=False))
    out = capsys.readouterr().out
    for free_rt in grace_oss.FREE_RUNTIMES:
        assert free_rt in out


# ── --json mode ──────────────────────────────────────────────────────────────


def test_cmd_tier_json_is_parseable(grace_oss, capsys):
    """``clawmetry tier --json`` emits the full Entitlement.to_dict()."""
    cli._cmd_tier(SimpleNamespace(as_json=True))
    out = capsys.readouterr().out
    doc = json.loads(out)
    # Cover the keys the resolver's contract has *always* exposed; new keys
    # added by parallel PRs (retention_days, locked_*, …) are not asserted
    # here so this test does not fight them.
    for key in ("tier", "source", "grace", "enforced", "runtimes", "features"):
        assert key in doc, f"missing key in --json output: {key!r}"
    assert doc["tier"] == grace_oss.TIER_OSS
    assert doc["grace"] is True
    assert doc["enforced"] is False
    # Free runtimes show up unconditionally; paid runtimes show up too while
    # grace is on (the grace contract: nothing disappears pre-enforce).
    assert set(grace_oss.FREE_RUNTIMES).issubset(set(doc["runtimes"]))


def test_cmd_tier_json_never_raises_on_resolver_error(monkeypatch, capsys):
    """If the resolver explodes (broken install), the command still emits a
    valid OSS-free JSON document so a piped shell wrapper keeps working."""

    def _boom(*_a, **_kw):
        raise RuntimeError("entitlement resolver exploded")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", _boom)
    cli._cmd_tier(SimpleNamespace(as_json=True))
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert doc["tier"] == "oss"
    assert doc["grace"] is True


# ── subparser wiring ─────────────────────────────────────────────────────────


def test_tier_subcommand_is_registered(monkeypatch):
    """``parser.parse_args(['tier'])`` succeeds (subparser exists + the
    handler is dispatchable). We exercise the parser-construction path that
    ``main()`` uses without actually running the dashboard fallback."""
    # Rebuild the same parser shape main() builds. The exact construction is
    # internal to main(), so we just sanity-check that ``--help`` lists tier.
    monkeypatch.setattr(sys, "argv", ["clawmetry", "tier", "--help"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0


def test_tier_json_flag_is_accepted(monkeypatch, capsys, grace_oss):
    """``clawmetry tier --json`` reaches ``_cmd_tier`` and prints JSON.

    We swap ``argv`` and let ``main()`` route to the dispatcher; an empty
    capsys means routing dropped the command on the floor.
    """
    monkeypatch.setattr(sys, "argv", ["clawmetry", "tier", "--json"])
    cli.main()
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert doc["tier"] == grace_oss.TIER_OSS
