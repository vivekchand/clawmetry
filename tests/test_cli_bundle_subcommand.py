"""Tests for the ``clawmetry bundle`` CLI subcommand.

Aggregate CLI sibling of ``clawmetry {runtimes,features,channels,nodes,
retention}`` -- each of those folds ONE entitlement axis in isolation,
``bundle`` folds a mixed 5-axis bundle into ONE ``required_tier`` +
``affordable_tiers`` ladder. The command wraps
:func:`clawmetry.entitlements.min_tier_for_all` /
:func:`affordable_tiers` (and their ``_at`` perspective siblings) so
these tests pin CLI -> helper delegation, the never-crash contract, the
``--json`` shape, the ``--tier`` perspective-independent parity, and the
subparser/dispatch registration.
"""
from __future__ import annotations

import argparse
import json

import pytest


@pytest.fixture
def cli_mod(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so
    the bundle fold is rendered against the OSS-free default and never
    against a license that happens to live on the host."""
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
    defaults = dict(
        features=None,
        runtimes=None,
        channels=None,
        retention_days=None,
        nodes=None,
        perspective=None,
        as_json=False,
    )
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def test_bundle_empty_bundle_reports_no_constraints(cli_mod, capsys):
    """No axes supplied → required_tier=None + explanatory line, never a stack."""
    cli_mod._cmd_bundle(_ns())
    out = capsys.readouterr().out
    assert "ClawMetry Bundle" in out
    assert "no constraints supplied" in out
    # The affordable-tiers table must not render when there is no floor.
    assert "★ minimum" not in out
    assert "qualifies" not in out


def test_bundle_empty_bundle_json_shape(cli_mod, capsys):
    """JSON payload for the empty-bundle path is the documented shape."""
    import clawmetry.entitlements as ent

    cli_mod._cmd_bundle(_ns(as_json=True))
    payload = json.loads(capsys.readouterr().out)
    assert payload["tier"] == ent.TIER_OSS
    assert payload["grace"] is True
    assert payload["enforced"] is False
    assert payload["perspective"] is None
    assert payload["required_tier"] is None
    assert payload["required_tier_label"] is None
    assert payload["required_tier_rank"] is None
    assert payload["affordable_tiers"] == []
    assert payload["constraints"] == {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
    }
    assert "error" not in payload


def test_bundle_delegates_to_min_tier_for_all(cli_mod, capsys):
    """CLI answer matches :func:`min_tier_for_all` byte-for-byte on the fold."""
    import clawmetry.entitlements as ent

    kwargs = dict(
        features=["anomaly_detection", "self_evolve"],
        runtimes=["claude_code", "cursor"],
        channels=10,
        retention_days=30,
        nodes=3,
    )
    expected = ent.min_tier_for_all(**kwargs)
    expected_ladder = ent.affordable_tiers(**kwargs)

    cli_mod._cmd_bundle(_ns(
        as_json=True,
        features="anomaly_detection,self_evolve",
        runtimes="claude_code,cursor",
        channels="10",
        retention_days="30",
        nodes="3",
    ))
    payload = json.loads(capsys.readouterr().out)
    assert payload["required_tier"] == expected
    assert payload["affordable_tiers"] == expected_ladder
    assert payload["constraints"] == {
        "features": ["anomaly_detection", "self_evolve"],
        "runtimes": ["claude_code", "cursor"],
        "channels": 10,
        "retention_days": 30,
        "nodes": 3,
    }


def test_bundle_human_table_lists_ladder(cli_mod, capsys):
    """The human table renders every qualifying tier row and marks the minimum."""
    cli_mod._cmd_bundle(_ns(
        features="anomaly_detection",
        channels="10",
    ))
    out = capsys.readouterr().out
    assert "Required tier:" in out
    assert "★ minimum" in out
    # The minimum row must appear exactly once.
    assert out.count("★ minimum") == 1


def test_bundle_perspective_matches_bare(cli_mod, capsys):
    """The ``_at`` perspective must NOT shape the answer (parity guarantee)."""
    import clawmetry.entitlements as ent

    perspective_answers: list[dict] = []
    for perspective in ent._TIER_ORDER:
        cli_mod._cmd_bundle(_ns(
            as_json=True,
            features="anomaly_detection",
            channels="25",
            perspective=perspective,
        ))
        perspective_answers.append(json.loads(capsys.readouterr().out))

    cli_mod._cmd_bundle(_ns(
        as_json=True,
        features="anomaly_detection",
        channels="25",
    ))
    bare = json.loads(capsys.readouterr().out)

    for row in perspective_answers:
        assert row["required_tier"] == bare["required_tier"]
        assert row["affordable_tiers"] == bare["affordable_tiers"]
        # The perspective is echoed on the payload but must not change the fold.
        assert row["perspective"] in ent._TIER_ORDER


def test_bundle_unknown_perspective_is_surfaced_not_crashed(cli_mod, capsys):
    """An unknown ``--tier`` renders an error line and empty required_tier."""
    cli_mod._cmd_bundle(_ns(
        features="anomaly_detection",
        perspective="not_a_tier",
    ))
    out = capsys.readouterr().out
    assert "unknown perspective tier: not_a_tier" in out
    # JSON path is also graceful and carries the ``error`` key.
    cli_mod._cmd_bundle(_ns(
        as_json=True,
        features="anomaly_detection",
        perspective="not_a_tier",
    ))
    payload = json.loads(capsys.readouterr().out)
    assert payload["required_tier"] is None
    assert payload["affordable_tiers"] == []
    assert "unknown perspective tier: not_a_tier" in payload["error"]
    assert payload["perspective"] == "not_a_tier"


def test_bundle_non_int_capacity_axis_collapses_not_crashes(cli_mod, capsys):
    """A typo like ``--channels abc`` must collapse the axis to ``None`` and
    never crash -- per the never-raise contract on :func:`get_entitlement`."""
    cli_mod._cmd_bundle(_ns(
        as_json=True,
        features="anomaly_detection",
        channels="abc",
        retention_days="not_a_number",
        nodes="",
    ))
    payload = json.loads(capsys.readouterr().out)
    # The non-int values collapsed to None so only the features axis contributes.
    assert payload["constraints"]["channels"] is None
    assert payload["constraints"]["retention_days"] is None
    assert payload["constraints"]["nodes"] is None
    # A single axis still resolves an answer -- min_tier_for_all wins on features alone.
    import clawmetry.entitlements as ent
    assert payload["required_tier"] == ent.min_tier_for_all(features=["anomaly_detection"])


def test_bundle_falls_back_when_resolver_errors(cli_mod, capsys, monkeypatch):
    """A poisoned :func:`min_tier_for_all` must not crash the CLI."""
    import clawmetry.entitlements as ent

    def _boom(**_kwargs):
        raise RuntimeError("synthetic bundle failure")

    monkeypatch.setattr(ent, "min_tier_for_all", _boom)
    cli_mod._cmd_bundle(_ns(
        as_json=True,
        features="anomaly_detection",
    ))
    payload = json.loads(capsys.readouterr().out)
    assert payload["required_tier"] is None
    assert payload["affordable_tiers"] == []
    assert "synthetic bundle failure" in payload["error"]


def test_bundle_grace_and_enforce_yield_identical_fold(cli_mod, capsys, monkeypatch):
    """The ``bundle`` answer is decoupled from the resolved entitlement -- it
    walks the static per-tier caps -- so grace vs enforce must yield the
    same required_tier and ladder for a given bundle."""
    import clawmetry.entitlements as ent

    cli_mod._cmd_bundle(_ns(
        as_json=True,
        features="anomaly_detection",
        channels="10",
    ))
    grace = json.loads(capsys.readouterr().out)

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cli_mod._cmd_bundle(_ns(
        as_json=True,
        features="anomaly_detection",
        channels="10",
    ))
    enforce = json.loads(capsys.readouterr().out)

    assert grace["required_tier"] == enforce["required_tier"]
    assert grace["affordable_tiers"] == enforce["affordable_tiers"]
    assert grace["enforced"] is False
    assert enforce["enforced"] is True


def test_bundle_subcommand_is_registered():
    """The subparser + dispatch table must list ``bundle`` so it is reachable
    from the CLI entry point."""
    import inspect

    import clawmetry.cli as cli

    src = inspect.getsource(cli.main)
    assert '"bundle"' in src
    assert "_cmd_bundle" in src
