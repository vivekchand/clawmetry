"""Tests for the ``clawmetry <features|runtimes> --why <id>`` diagnostic.

Sibling of ``tests/test_cli_features_subcommand.py`` and
``tests/test_cli_runtimes_subcommand.py``. The ``--why`` flag is a thin read
of :meth:`Entitlement.lock_reason` + :func:`min_tier_for_feature` /
:func:`min_tier_for_runtime` and must never crash. It answers the operator
question "why is X locked?" from the shell without hitting the HTTP API —
so the JSON shape has to match ``/api/entitlement/lock-reason``.
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


# ── payload shape ──────────────────────────────────────────────────────────

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


def test_why_json_matches_http_lock_reason_shape(cli_mod, capsys):
    """The CLI --why JSON must expose the same keys as
    ``GET /api/entitlement/lock-reason`` so scripts written against either
    surface work interchangeably."""
    cli_mod._cmd_runtimes(_ns(as_json=True, why="claude_code"))
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == _EXPECTED_KEYS
    assert payload["key"] == "claude_code"
    assert payload["kind"] == "runtime"


def test_why_grace_reports_no_lock(cli_mod, capsys):
    """In the default OSS-free + grace posture, ``lock_reason`` returns
    None and the payload must report locked=False even for a paid runtime.
    This is the guarantee that wiring the CLI is behaviour-neutral before
    enforcement flips on."""
    cli_mod._cmd_runtimes(_ns(as_json=True, why="claude_code"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["locked"] is False
    assert payload["reason"] is None
    assert payload["current_tier"] == "oss"
    # required_tier is still meaningful — it's the tier that would unlock
    # this runtime once enforcement is on — so the operator can preview the
    # upgrade target without flipping the enforce gate.
    assert payload["required_tier"] is not None
    assert payload["upgrade_required"] is True


def test_why_enforce_reports_locked_paid_runtime(cli_mod, capsys, monkeypatch):
    """With CLAWMETRY_ENFORCE=1, a paid runtime resolves as locked and the
    upgrade CTA fires."""
    import clawmetry.entitlements as ent

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cli_mod._cmd_runtimes(_ns(as_json=True, why="claude_code"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["locked"] is True
    assert payload["reason"], "reason string must be non-empty when locked"
    assert payload["upgrade_required"] is True
    assert payload["required_tier"]


def test_why_free_runtime_never_locks(cli_mod, capsys, monkeypatch):
    """openclaw is FREE — enforcement or not, it never locks and no CTA
    shows. Guards against a regression that would gate the free runtime."""
    import clawmetry.entitlements as ent

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cli_mod._cmd_runtimes(_ns(as_json=True, why="openclaw"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["locked"] is False
    assert payload["reason"] is None
    assert payload["upgrade_required"] is False


def test_why_unknown_id_returns_parseable_fallback(cli_mod, capsys):
    """A typo on --why must not crash and must not dangle an upgrade CTA —
    otherwise a shell wrapper mistakes a typo for "no lock, all good"."""
    cli_mod._cmd_runtimes(_ns(as_json=True, why="not-a-real-runtime"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["locked"] is False
    assert payload["reason"] is None
    assert payload["required_tier"] is None
    assert payload["upgrade_required"] is False


def test_why_human_block_renders_reason(cli_mod, capsys, monkeypatch):
    """The non-JSON path prints a compact aligned block a shell operator can
    read at a glance. Under enforcement the reason string surfaces verbatim."""
    import clawmetry.entitlements as ent

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    ent.invalidate()
    cli_mod._cmd_runtimes(_ns(as_json=False, why="claude_code"))
    out = capsys.readouterr().out
    assert 'why is "claude_code" locked?' in out
    assert "Kind:" in out and "runtime" in out
    assert "Locked:" in out and "yes" in out
    assert "Reason:" in out
    assert "Required tier:" in out
    assert "clawmetry license activate <KEY>" in out


def test_why_features_dispatch_uses_feature_kind(cli_mod, capsys):
    """`clawmetry features --why <id>` routes through the same helper but
    with kind='feature' so the payload reflects feature semantics, not
    runtime semantics."""
    # Pick a known paid feature so the required_tier is populated even in
    # grace mode.
    import clawmetry.entitlements as ent

    paid_feature = next(iter(ent.PAID_FEATURES))
    cli_mod._cmd_features(_ns(as_json=True, why=paid_feature))
    payload = json.loads(capsys.readouterr().out)
    assert payload["kind"] == "feature"
    assert payload["key"] == paid_feature
    # In grace: not locked, but the tier that would unlock it is still known.
    assert payload["locked"] is False
    assert payload["required_tier"] is not None


def test_why_survives_broken_resolver(cli_mod, capsys, monkeypatch):
    """A poisoned :func:`get_entitlement` must produce the OSS-free fallback
    shape, not a stack trace. Matches the never-crash contract."""
    import clawmetry.entitlements as ent

    def _boom():
        raise RuntimeError("synthetic resolver failure")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    cli_mod._cmd_runtimes(_ns(as_json=True, why="claude_code"))
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == _EXPECTED_KEYS
    assert payload["current_tier"] == "oss"
    assert payload["locked"] is False
    assert payload["reason"] is None


def test_why_subparser_flags_registered():
    """Both `runtimes --why` and `features --why` must be reachable from the
    top-level parser — otherwise the human-facing docs promise a flag that
    argparse rejects at runtime."""
    import inspect

    import clawmetry.cli as cli

    src = inspect.getsource(cli.main)
    # Only one occurrence of `"--why"` is enough — both subparsers add it
    # inline in `main`, so grep the source for the flag name and its metavar.
    assert '"--why"' in src
    assert "metavar=\"ID\"" in src
