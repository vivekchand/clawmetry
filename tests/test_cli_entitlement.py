"""Tests for the ``clawmetry entitlement`` CLI subcommand.

Mirrors the assertions in ``tests/test_entitlements.py`` for the HTTP route, but
exercises the operator-facing CLI surface that prints the resolved entitlement
to stdout. Headline invariants:

* No license + no cloud cache + no ``CLAWMETRY_ENFORCE`` => OSS-free in grace,
  human-readable output mentions ``Tier: oss`` and ``Grace: on``.
* ``--json`` emits a parseable object whose keys match the
  :func:`clawmetry.entitlements.Entitlement.to_dict` shape served at
  ``GET /api/entitlement``, so scripts and the HTTP route are
  interchangeable for operator tooling.
* The handler never raises: a broken entitlements module still produces an
  OSS-free fallback (matching the route's behaviour) plus a ``Note:`` line
  in the human-readable rendering.
"""
from __future__ import annotations

import importlib
import io
import json
from contextlib import redirect_stdout

import pytest

import clawmetry.cli as cli


@pytest.fixture
def fresh_entitlements(monkeypatch, tmp_path):
    """Re-import :mod:`clawmetry.entitlements` against an empty HOME so no real
    ``~/.clawmetry/license.key`` or ``cloud_plan.json`` leaks into the test."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as ent

    importlib.reload(ent)
    ent.invalidate()
    yield ent
    ent.invalidate()


class _Args:
    """Minimal stand-in for the argparse Namespace the dispatcher passes."""

    def __init__(self, as_json: bool = False):
        self.as_json = as_json


def _run(as_json: bool = False) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        cli._cmd_entitlement(_Args(as_json=as_json))
    return buf.getvalue()


# ── human-readable output ────────────────────────────────────────────────────


def test_oss_free_default(fresh_entitlements):
    out = _run()
    assert "ClawMetry Entitlement" in out
    assert "Tier:        oss" in out
    assert "Source:      oss" in out
    assert "Paid:        no" in out
    assert "Grace:       on" in out
    assert "Enforced:    no" in out


def test_lists_free_runtimes(fresh_entitlements):
    out = _run()
    # OpenClaw + NemoClaw are the two free agent runtimes.
    assert "openclaw" in out
    assert "nemoclaw" in out
    # Paid runtimes must not appear in the free entitlement runtime list.
    assert "claude_code" not in out
    assert "codex" not in out


def test_lists_free_features(fresh_entitlements):
    out = _run()
    # A representative slice from FREE_FEATURES — the wrap logic might split
    # the list across lines, so we just check membership.
    for feat in ("sessions", "transcripts", "usage", "brain", "flow"):
        assert feat in out


# ── --json mode ──────────────────────────────────────────────────────────────


def test_json_mode_emits_valid_json(fresh_entitlements):
    out = _run(as_json=True)
    data = json.loads(out)  # raises on garbage
    assert isinstance(data, dict)


def test_json_shape_matches_route(fresh_entitlements):
    """The CLI's JSON object must be a superset of what /api/entitlement
    returns — operator tooling that consumes one should work with the other."""
    data = json.loads(_run(as_json=True))
    for key in (
        "tier", "source", "node_limit", "expiry", "expired", "is_paid",
        "grace", "enforced", "runtimes", "features",
    ):
        assert key in data, f"missing key {key!r}"
    assert data["tier"] == "oss"
    assert data["source"] == "oss"
    assert data["grace"] is True
    assert data["enforced"] is False
    assert data["is_paid"] is False
    assert "openclaw" in data["runtimes"]
    assert "nemoclaw" in data["runtimes"]


# ── enforce-flag observability ───────────────────────────────────────────────


def test_enforce_flips_human_output(fresh_entitlements, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    fresh_entitlements.invalidate()
    out = _run()
    assert "Grace:       off" in out
    assert "Enforced:    yes" in out


def test_enforce_flips_json_output(fresh_entitlements, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    fresh_entitlements.invalidate()
    data = json.loads(_run(as_json=True))
    assert data["grace"] is False
    assert data["enforced"] is True


# ── never-raise contract ─────────────────────────────────────────────────────


def test_fallback_on_resolution_error(monkeypatch):
    """If :mod:`clawmetry.entitlements` somehow blows up, the handler must
    still print an OSS-free entitlement (matching the HTTP route fallback) and
    surface the error via a ``Note:`` line — never raise to the operator."""
    import clawmetry.entitlements as ent

    def _boom(*_a, **_k):
        raise RuntimeError("simulated breakage")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    out = _run()
    assert "Tier:        oss" in out
    assert "Grace:       on" in out
    assert "Note:" in out
    assert "simulated breakage" in out


def test_fallback_on_resolution_error_json(monkeypatch):
    import clawmetry.entitlements as ent

    def _boom(*_a, **_k):
        raise RuntimeError("simulated breakage")

    monkeypatch.setattr(ent, "get_entitlement", _boom)
    data = json.loads(_run(as_json=True))
    assert data["tier"] == "oss"
    assert data["grace"] is True
    assert data["enforced"] is False
    assert "openclaw" in data["runtimes"]
    assert data.get("error") == "simulated breakage"
