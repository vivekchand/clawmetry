"""Tests for the ``clawmetry nodes`` subcommand.

Capacity-axis sibling of ``tests/test_cli_channels_subcommand.py`` for the
``nodes`` axis. The subcommand surfaces the resolved node-count cap plus a
``--why N`` diagnostic that answers "what tier admits N registered nodes?"
using the same lock-reason payload ``clawmetry channels --why N`` emits, so
a wrapper script written against either surface works interchangeably.

The header / ``--why`` output must match ``GET /api/entitlement`` (for the
node cap) and ``GET /api/entitlement/lock-reason?nodes=N`` (for the
diagnostic) byte-for-byte so the CLI and HTTP surfaces cannot drift.
"""
from __future__ import annotations

import argparse
import json

import pytest


@pytest.fixture
def cli_mod(monkeypatch, tmp_path):
    """Fresh entitlements module with HOME pointed at an empty tmp dir so the
    resolver renders against the OSS-free default and never against a license
    that happens to live on the host.
    """
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
    kw.setdefault("as_json", False)
    kw.setdefault("why", None)
    return argparse.Namespace(**kw)


# ── default (no --why) header block ─────────────────────────────────────────


def test_default_json_shape(cli_mod, capsys):
    """The default ``--json`` output exposes exactly the four documented
    keys (tier / grace / enforced / node_limit) so a wrapper script can
    parse the response without special-casing which keys are present."""
    cli_mod._cmd_nodes(_ns(as_json=True))
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {"tier", "grace", "enforced", "node_limit"}


def test_default_grace_reports_oss_free_cap(cli_mod, capsys):
    """The OSS-free default resolves to tier=oss with node_limit=1 (the
    per-tier floor) and grace=True, enforced=False."""
    cli_mod._cmd_nodes(_ns(as_json=True))
    payload = json.loads(capsys.readouterr().out)
    assert payload["tier"] == "oss"
    assert payload["grace"] is True
    assert payload["enforced"] is False
    assert payload["node_limit"] == 1


def test_default_human_block_prints_header(cli_mod, capsys):
    """The non-JSON path prints an aligned header block matching the
    ``clawmetry channels`` layout so shell operators recognise the
    layout across capacity-axis subcommands."""
    cli_mod._cmd_nodes(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "ClawMetry Nodes" in out
    assert "Tier:" in out
    assert "Enforcement:" in out and "off (grace)" in out
    assert "Node cap:" in out
    # The free-tier OSS cap is 1 node; surface it verbatim.
    assert "1" in out


def test_default_survives_broken_resolver(cli_mod, capsys, monkeypatch):
    """A poisoned :func:`get_entitlement` must produce the OSS-free
    fallback shape, not a stack trace. Matches the never-crash contract."""
    import clawmetry.entitlements as ent

    def _boom():
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    cli_mod._cmd_nodes(_ns(as_json=True))
    payload = json.loads(capsys.readouterr().out)
    # Fallback shape includes an ``error`` key so a shell wrapper never
    # mistakes a broken resolver for a successful all-clear.
    assert set(payload) == {"tier", "grace", "enforced", "node_limit", "error"}
    assert payload["tier"] == "oss"
    assert payload["node_limit"] is None
    assert "synthetic" in payload["error"]


# ── --why N (lock-reason payload) ──────────────────────────────────────────
#
# The ``--why`` payload shape must match the shared envelope emitted by
# ``clawmetry {runtimes,features,channels} --why`` so a script written
# against any axis works here interchangeably. The nodes axis is
# capacity-scoped (N is a count, not an id), so behaviour mirrors the
# channels ``--why`` branch: non-int input falls to the grace-shape
# fallback, and the human header phrases the capacity question naturally.


_EXPECTED_KEYS = {
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


def test_why_json_matches_shared_envelope(cli_mod, capsys):
    """The nodes --why JSON must expose the same keys as the runtime /
    feature / channels variants so a script written against any axis works
    here interchangeably."""
    cli_mod._cmd_nodes(_ns(as_json=True, why="5"))
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == _EXPECTED_KEYS
    assert payload["kind"] == "nodes"
    assert payload["key"] == "5"


def test_why_grace_reports_upgrade_target(cli_mod, capsys):
    """In grace mode, a count above the free OSS floor of 1 must still
    surface the tier that would unlock it (locked=False but
    required_tier=cloud_starter + upgrade_required=True), matching the
    channels ``--why`` preview behaviour. This is the guarantee that the
    CLI can preview the upgrade ladder without flipping the enforce gate."""
    import clawmetry.entitlements as ent

    cli_mod._cmd_nodes(_ns(as_json=True, why="5"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["locked"] is False  # grace mode
    assert payload["reason"] is None
    assert payload["current_tier"] == ent.TIER_OSS
    assert payload["required_tier"] == ent.TIER_CLOUD_STARTER
    assert payload["upgrade_required"] is True


def test_why_under_free_cap_reports_no_upgrade(cli_mod, capsys):
    """A count that fits under the OSS free cap (1) resolves to
    required_tier=oss and upgrade_required=False even under grace so the
    CLI never dangles an upgrade CTA for a request the free floor
    already covers."""
    cli_mod._cmd_nodes(_ns(as_json=True, why="1"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["locked"] is False
    assert payload["upgrade_required"] is False


def test_why_enforce_locks_over_cap(cli_mod, capsys, monkeypatch):
    """With CLAWMETRY_ENFORCE=1, asking for more registered nodes than
    the OSS cap admits reports a real lock with a non-empty reason string
    and the upgrade CTA."""
    import clawmetry.entitlements as ent

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cli_mod._cmd_nodes(_ns(as_json=True, why="5"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["locked"] is True
    assert payload["reason"], "reason string must be non-empty when locked"
    assert payload["required_tier"] == ent.TIER_CLOUD_STARTER
    assert payload["upgrade_required"] is True


def test_why_non_int_returns_parseable_fallback(cli_mod, capsys):
    """A typo like ``--why abc`` must not crash and must not dangle an
    upgrade CTA -- otherwise a shell wrapper mistakes a typo for
    "no lock, all good"."""
    cli_mod._cmd_nodes(_ns(as_json=True, why="abc"))
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == _EXPECTED_KEYS
    assert payload["kind"] == "nodes"
    assert payload["locked"] is False
    assert payload["reason"] is None
    assert payload["required_tier"] is None
    assert payload["upgrade_required"] is False


def test_why_key_canonicalised(cli_mod, capsys):
    """A caller passing ``05`` or ``5`` sees the same canonical ``"5"``
    string back in the payload -- matches the channels ``--why``
    canonicalisation posture so scripts can key on ``payload["key"]``."""
    cli_mod._cmd_nodes(_ns(as_json=True, why="05"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["key"] == "5"


def test_why_human_block_uses_capacity_phrasing(cli_mod, capsys, monkeypatch):
    """The non-JSON path for nodes uses a capacity-scoped header
    ("what tier unlocks N nodes?") since the key is a count, not an
    adapter id. Under enforcement the reason string surfaces verbatim
    alongside the aligned two-column block."""
    import clawmetry.entitlements as ent

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cli_mod._cmd_nodes(_ns(as_json=False, why="5"))
    out = capsys.readouterr().out
    assert "what tier unlocks 5 nodes?" in out
    assert "Kind:" in out and "nodes" in out
    assert "Locked:" in out and "yes" in out
    assert "Reason:" in out
    assert "Required tier:" in out
    assert "clawmetry license activate <KEY>" in out


def test_why_survives_broken_resolver(cli_mod, capsys, monkeypatch):
    """A poisoned :func:`get_entitlement` must produce the OSS-free
    fallback shape, not a stack trace -- same never-crash contract as
    the runtime / feature / channels variants."""
    import clawmetry.entitlements as ent

    def _boom():
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    cli_mod._cmd_nodes(_ns(as_json=True, why="5"))
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == _EXPECTED_KEYS
    assert payload["kind"] == "nodes"
    assert payload["current_tier"] == "oss"
    assert payload["locked"] is False
    assert payload["reason"] is None


# ── subparser wiring ───────────────────────────────────────────────────────


def test_subparser_flags_registered():
    """`nodes --why` and `nodes --json` must be reachable from the top-level
    parser -- otherwise the human-facing docs promise flags that argparse
    rejects at runtime."""
    import inspect

    import clawmetry.cli as cli

    src = inspect.getsource(cli.main)
    # The subparser is named `p_nodes` in main(); grep for both the
    # subcommand name and its documented flag help so a rename or a
    # dropped flag surfaces here rather than at first-run.
    assert '"nodes"' in src
    assert "Show the resolved node-count cap" in src
    assert "GET /api/entitlement/lock-reason?nodes=N" in src


def test_nodes_dispatch_wired():
    """The top-level `args.cmd == "nodes"` branch must dispatch to
    :func:`_cmd_nodes` -- otherwise the subparser accepts the command but
    the runtime silently falls through to the dashboard fallback."""
    import inspect

    import clawmetry.cli as cli

    src = inspect.getsource(cli.main)
    assert 'args.cmd == "nodes"' in src
    assert "_cmd_nodes(args)" in src
