"""Tests for the ``Plan:`` line in ``clawmetry status`` (human, non-JSON
output).

Before this, ``clawmetry status`` only printed a ``License:`` line, and ONLY
when a local signed-license FILE existed on disk -- a cloud-only Free or
Trial account (no `~/.clawmetry/license.key`) showed nothing about its plan
at all. ``Plan:`` is unconditional and maps the resolved
``clawmetry.entitlements.Entitlement`` (the same resolver the runtime gate
and the dashboard use) onto exactly the five states requested: Free, Trial,
Trial Expired, Starter, Pro. "Trial Expired" is a real, distinct case (not
just "fell through to Free") because the resolver preserves an expired
trial's tier + expiry rather than silently discarding it.

Hermetic: same isolation harness as test_cli_status_extensions.py /
test_cli_status_license.py, but ``get_entitlement`` is stubbed directly so
each test targets one resolved state without needing a real license file.
"""
from __future__ import annotations

import time
from types import SimpleNamespace

import pytest


def _ns(**overrides):
    ns = SimpleNamespace(live=False, show_key=False, as_json=False, cmd="status")
    for k, v in overrides.items():
        setattr(ns, k, v)
    return ns


@pytest.fixture
def stub_home(monkeypatch, tmp_path):
    """Same isolation harness the neighbouring status test suites use — no
    live daemon, no live network, no leaks to ``~/.clawmetry``."""
    import clawmetry.sync as _sync
    import clawmetry.cli as cli
    import clawmetry.extensions as ext

    monkeypatch.setattr(_sync, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(_sync, "STATE_FILE", tmp_path / "sync-state.json")
    monkeypatch.setattr(_sync, "LOG_FILE", tmp_path / "sync.log")

    plan_path = tmp_path / "cloud_plan.json"

    import os as _os
    import os.path as _op
    real_expanduser = _op.expanduser

    def _fake_expand(p):
        if p == "~/.clawmetry/cloud_plan.json":
            return str(plan_path)
        return real_expanduser(p)

    monkeypatch.setattr(_op, "expanduser", _fake_expand)
    monkeypatch.setattr(_os.path, "expanduser", _fake_expand)

    monkeypatch.setattr(cli, "_resolve_account_email", lambda _k: (None, None))
    monkeypatch.setattr(cli, "_is_sync_running", lambda: False)

    import platform as _platform
    monkeypatch.setattr(_platform, "system", lambda: "Linux")

    monkeypatch.setattr(
        "clawmetry.sync._detect_family_runtimes", lambda: [], raising=False,
    )
    monkeypatch.setattr(
        "clawmetry.license._pro_installed_version", lambda: None, raising=False,
    )

    ext._loaded = False
    with ext._lock:
        ext._loaded_plugins.clear()
        ext._failed_plugins.clear()

    return SimpleNamespace(tmp=tmp_path, plan_path=plan_path)


def _plan_line(out: str) -> str:
    for line in out.splitlines():
        if line.strip().startswith("Plan:"):
            return line
    return ""


def _run_with_entitlement(capsys, monkeypatch, ent):
    import clawmetry.entitlements as entmod
    monkeypatch.setattr(entmod, "get_entitlement", lambda force=False: ent)
    import clawmetry.cli as cli
    cli._cmd_status(_ns())
    return capsys.readouterr().out


def test_plan_line_free(stub_home, capsys, monkeypatch):
    from clawmetry.entitlements import Entitlement, TIER_OSS
    ent = Entitlement(tier=TIER_OSS, source="oss", node_limit=1, expiry=None, grace=True)
    out = _run_with_entitlement(capsys, monkeypatch, ent)
    assert "Free" in _plan_line(out)


def test_plan_line_active_trial(stub_home, capsys, monkeypatch):
    from clawmetry.entitlements import Entitlement, TIER_TRIAL
    ent = Entitlement(
        tier=TIER_TRIAL, source="license", node_limit=1,
        expiry=time.time() + 3 * 86400, grace=True,
    )
    out = _run_with_entitlement(capsys, monkeypatch, ent)
    line = _plan_line(out)
    assert "Trial" in line and "Expired" not in line


def test_plan_line_trial_expired(stub_home, capsys, monkeypatch):
    from clawmetry.entitlements import Entitlement, TIER_TRIAL
    ent = Entitlement(
        tier=TIER_TRIAL, source="license", node_limit=1,
        expiry=time.time() - 86400, grace=True,
    )
    out = _run_with_entitlement(capsys, monkeypatch, ent)
    line = _plan_line(out)
    assert "Trial Expired" in line
    assert "pricing" in line  # unmissable upgrade CTA, not just a label


def test_plan_line_starter(stub_home, capsys, monkeypatch):
    from clawmetry.entitlements import Entitlement, TIER_CLOUD_STARTER
    ent = Entitlement(
        tier=TIER_CLOUD_STARTER, source="cloud", node_limit=5,
        expiry=None, grace=True,
    )
    out = _run_with_entitlement(capsys, monkeypatch, ent)
    assert "Starter" in _plan_line(out)


def test_plan_line_pro(stub_home, capsys, monkeypatch):
    from clawmetry.entitlements import Entitlement, TIER_PRO
    ent = Entitlement(
        tier=TIER_PRO, source="license", node_limit=10,
        expiry=None, grace=True,
    )
    out = _run_with_entitlement(capsys, monkeypatch, ent)
    assert "Pro" in _plan_line(out)
