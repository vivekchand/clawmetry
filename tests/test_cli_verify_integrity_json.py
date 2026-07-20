"""Tests for ``clawmetry verify-integrity --json`` — scriptable hash-chain verify.

Companion to ``tests/test_verify_integrity_cli_proxy.py`` (the human-path
harness). Together they pin both surfaces so a wrapper script can consume
the outcome without screen-scraping AND the operator's terminal keeps
rendering the human table when ``--json`` is omitted.

Contract this file pins:

* every branch of :func:`clawmetry.cli._cmd_verify_integrity` emits a
  stable JSON envelope with the same six keys the store returns
  (``status``/``node_id``/``checked``/``pre_chain``/``broken_at``/``error``),
* exit codes match the human path (0 for ``valid``/``empty``, 1 for
  ``invalid``/``store_open_failed``/``error``, 2 for ``daemon_too_old``)
  so a shell wrapper's ``$?`` remains the primary signal,
* two synthetic statuses cover the environment errors that today only
  surfaced via exit code + text (``store_open_failed`` and
  ``daemon_too_old``) — without them a script could not distinguish
  "chain broken" from "cannot open store" from "daemon proxy is old",
* the parser wires ``--json`` on the ``verify-integrity`` subcommand so
  a future edit that silently drops the flag is caught before ship,
* the human path is unchanged (regression guard on the default output).

Sibling of ``tests/test_cli_license_json.py`` /
``tests/test_cli_diagnose_subcommand.py`` — the CLI diagnostic quartet
(``tier`` / ``runtimes`` / ``features`` / ``channels`` / ``diagnose`` /
``license`` / ``verify-integrity``) stays uniformly scriptable.
"""
from __future__ import annotations

import argparse
import json

import pytest


def _args(node_id=None, as_json=True):
    return argparse.Namespace(node_id=node_id, as_json=as_json)


# ── happy path: JSON payload shape ────────────────────────────────────────────


def test_json_valid_emits_store_shape_and_exits_zero(monkeypatch, capsys):
    """A ``valid`` result must round-trip the store's six keys unchanged and
    exit 0 so the shell pipe treats it as success."""
    from clawmetry import cli

    class _ValidStore:
        def verify_integrity(self, node_id=None):
            assert node_id is None
            return {
                "status": "valid",
                "node_id": "all",
                "checked": 42,
                "pre_chain": 3,
                "broken_at": None,
                "error": None,
            }

    monkeypatch.setattr(
        "clawmetry.local_store.get_store",
        lambda read_only=True: _ValidStore(),
    )

    cli._cmd_verify_integrity(_args())
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "status": "valid",
        "node_id": "all",
        "checked": 42,
        "pre_chain": 3,
        "broken_at": None,
        "error": None,
    }


def test_json_empty_shape_and_exits_zero(monkeypatch, capsys):
    """``empty`` (no stamped events) is a success outcome, not a failure —
    exit 0 matches the human path and lets scripts branch on ``status``
    instead of ``$?``."""
    from clawmetry import cli

    class _EmptyStore:
        def verify_integrity(self, node_id=None):
            return {
                "status": "empty",
                "node_id": "all",
                "checked": 0,
                "pre_chain": 0,
                "broken_at": None,
                "error": None,
            }

    monkeypatch.setattr(
        "clawmetry.local_store.get_store",
        lambda read_only=True: _EmptyStore(),
    )

    cli._cmd_verify_integrity(_args())
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "empty"
    assert payload["checked"] == 0


def test_json_invalid_carries_broken_at_and_exits_one(monkeypatch, capsys):
    """A broken chain must exit 1 AND surface ``broken_at`` + ``error`` so a
    wrapper script has enough context to fire an alert without a re-read."""
    from clawmetry import cli

    class _BrokenStore:
        def verify_integrity(self, node_id=None):
            return {
                "status": "invalid",
                "node_id": "all",
                "checked": 5,
                "pre_chain": 0,
                "broken_at": "evt-6",
                "error": "chain break at event evt-6 (node node-a)",
            }

    monkeypatch.setattr(
        "clawmetry.local_store.get_store",
        lambda read_only=True: _BrokenStore(),
    )

    with pytest.raises(SystemExit) as ei:
        cli._cmd_verify_integrity(_args())
    assert ei.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "invalid"
    assert payload["broken_at"] == "evt-6"
    assert "chain break" in payload["error"]


def test_json_node_id_scopes_are_threaded_through(monkeypatch, capsys):
    """``--node-id NODE`` is forwarded to ``verify_integrity`` and echoed
    back on the payload's ``node_id`` field so scripts running per-node
    verifications can key their state map off the payload directly."""
    from clawmetry import cli

    seen: dict = {}

    class _Store:
        def verify_integrity(self, node_id=None):
            seen["node_id"] = node_id
            return {
                "status": "valid",
                "node_id": node_id or "all",
                "checked": 1,
                "pre_chain": 0,
                "broken_at": None,
                "error": None,
            }

    monkeypatch.setattr(
        "clawmetry.local_store.get_store",
        lambda read_only=True: _Store(),
    )

    cli._cmd_verify_integrity(_args(node_id="node-42"))
    payload = json.loads(capsys.readouterr().out)
    assert seen["node_id"] == "node-42"
    assert payload["node_id"] == "node-42"


# ── environment / failure envelopes ──────────────────────────────────────────


def test_json_daemon_too_old_returns_status_and_exit_two(monkeypatch, capsys):
    """Old-daemon scenario: the proxy returns None. Under ``--json`` this must
    surface as ``status=daemon_too_old`` with exit code 2 so a wrapper can
    distinguish "verifier reachable but broken chain" from "verifier
    unreachable"."""
    from clawmetry import cli

    class _NoneStore:
        def verify_integrity(self, node_id=None):  # noqa: ARG002
            return None

    monkeypatch.setattr(
        "clawmetry.local_store.get_store",
        lambda read_only=True: _NoneStore(),
    )

    with pytest.raises(SystemExit) as ei:
        cli._cmd_verify_integrity(_args())
    assert ei.value.code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "daemon_too_old"
    assert payload["checked"] == 0
    assert "Restart the sync daemon" in payload["error"]


def test_json_store_open_failure_returns_status_and_exit_one(monkeypatch, capsys):
    """A raised ``get_store`` must not crash the CLI. Under ``--json`` it
    surfaces as ``status=store_open_failed`` with the underlying exception
    string preserved so operators can see why."""
    from clawmetry import cli

    def _raiser(read_only=True):  # noqa: ARG001
        raise RuntimeError("duckdb: writer lock held by another process")

    monkeypatch.setattr("clawmetry.local_store.get_store", _raiser)

    with pytest.raises(SystemExit) as ei:
        cli._cmd_verify_integrity(_args())
    assert ei.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "store_open_failed"
    assert "writer lock" in payload["error"]


def test_json_verify_call_raising_returns_status_error(monkeypatch, capsys):
    """A raised ``verify_integrity`` (bad DuckDB state, schema drift, …) must
    surface as ``status=error`` with the exception string preserved. Exit 1
    matches the human path."""
    from clawmetry import cli

    class _RaisingStore:
        def verify_integrity(self, node_id=None):  # noqa: ARG002
            raise RuntimeError("chain_hash column missing")

    monkeypatch.setattr(
        "clawmetry.local_store.get_store",
        lambda read_only=True: _RaisingStore(),
    )

    with pytest.raises(SystemExit) as ei:
        cli._cmd_verify_integrity(_args())
    assert ei.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "chain_hash column missing" in payload["error"]


def test_json_unexpected_shape_degrades_to_error_envelope(monkeypatch, capsys):
    """If the store's return shape ever changes to something non-dict the CLI
    must not crash. Falls back to ``status=error`` with a self-describing
    ``error`` message so the wrapper still has something parseable."""
    from clawmetry import cli

    class _WeirdStore:
        def verify_integrity(self, node_id=None):  # noqa: ARG002
            return "not-a-dict"

    monkeypatch.setattr(
        "clawmetry.local_store.get_store",
        lambda read_only=True: _WeirdStore(),
    )

    with pytest.raises(SystemExit) as ei:
        cli._cmd_verify_integrity(_args())
    assert ei.value.code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "unexpected shape" in payload["error"]


# ── regression guards ────────────────────────────────────────────────────────


def test_default_human_output_is_unchanged(monkeypatch, capsys):
    """Without ``--json`` the human header + result lines are preserved so
    every operator's terminal still reads the same table. Guards against
    accidental drift in the default output when the JSON branch is added."""
    from clawmetry import cli

    class _ValidStore:
        def verify_integrity(self, node_id=None):  # noqa: ARG002
            return {
                "status": "valid",
                "node_id": "all",
                "checked": 7,
                "pre_chain": 0,
                "broken_at": None,
                "error": None,
            }

    monkeypatch.setattr(
        "clawmetry.local_store.get_store",
        lambda read_only=True: _ValidStore(),
    )

    cli._cmd_verify_integrity(_args(as_json=False))
    out = capsys.readouterr().out
    assert "ClawMetry Integrity Verify" in out
    assert "Scope:" in out
    assert "Checked:" in out
    assert "VALID" in out
    # The header block MUST NOT leak JSON tokens onto the human path.
    assert "{" not in out


def test_verify_integrity_subcommand_is_registered():
    """The subparser + dispatch table must list ``verify-integrity`` so the
    subcommand is reachable from the CLI entry point (and so the
    single-token dispatch in ``main()`` recognises it as a subcommand,
    not a dashboard flag)."""
    import inspect

    import clawmetry.cli as cli

    src = inspect.getsource(cli.main)
    assert '"verify-integrity"' in src
    assert "_cmd_verify_integrity" in src
    # And ``--json`` is threaded onto the subparser so a shell wrapper can
    # rely on ``clawmetry verify-integrity --json`` being a stable contract.
    assert '"--json"' in src
