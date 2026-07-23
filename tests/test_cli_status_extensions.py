"""Tests for the ``extensions`` block in ``clawmetry status --json``.

Complements ``test_cli_status_json.py``: this suite pins the newly-added
``extensions`` field carrying the output of
:func:`clawmetry.extensions.probe_plugins`, so operators (and wrapper
scripts) can tell from a fresh CLI process whether ``clawmetry-pro``'s
entry point is not just installed on disk (already surfaced by
``runtimes.pro_installed_version``) but also *importable* — the two are
not the same, and a mismatched-core install shows green on the disk
marker while the plugin silently never loads.

Every test is hermetic: entry-point enumeration is monkeypatched, no
network / launchd / systemd calls escape the process.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest


def _ns(**overrides):
    ns = SimpleNamespace(live=False, show_key=False, as_json=True, cmd="status")
    for k, v in overrides.items():
        setattr(ns, k, v)
    return ns


class _FakeEntryPoint:
    def __init__(self, fn, name="fake", value="mod:attr"):
        self._fn = fn
        self.name = name
        self.value = value

    def load(self):
        return self._fn


@pytest.fixture
def stub_home(monkeypatch, tmp_path):
    """Same isolation harness ``test_cli_status_json.py`` uses — no live
    daemon, no live network, no leaks to ``~/.clawmetry``."""
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

    # Reset the extension-loader mirrors so an adjacent suite that populated
    # them can't leak state into the probe under test.
    ext._loaded = False
    with ext._lock:
        ext._loaded_plugins.clear()
        ext._failed_plugins.clear()

    return SimpleNamespace(tmp=tmp_path, plan_path=plan_path)


def _run_and_parse(capsys, args):
    import clawmetry.cli as cli
    cli._cmd_status(args)
    out = capsys.readouterr().out
    return json.loads(out)


# ── envelope ──────────────────────────────────────────────────────────────────


def test_extensions_key_present_on_virgin_install(stub_home, capsys, monkeypatch):
    """No entry points → ``discovered: []`` + zero counts. Every documented
    subkey is present so ``jq .extensions.discovered`` never sees ``null``."""
    import clawmetry.extensions as ext
    monkeypatch.setattr(ext, "_select_entry_points", lambda group: [])

    doc = _run_and_parse(capsys, _ns())
    ext_block = doc["extensions"]
    assert set(ext_block.keys()) == {"discovered", "importable_count", "broken_count"}
    assert ext_block == {
        "discovered": [],
        "importable_count": 0,
        "broken_count": 0,
    }


def test_extensions_reports_importable_pro(stub_home, capsys, monkeypatch):
    """A resolvable ``clawmetry-pro`` entry point shows up under
    ``discovered`` with ``importable: True`` and bumps the counter."""
    import clawmetry.extensions as ext
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: [_FakeEntryPoint(
            lambda: None, name="clawmetry-pro", value="clawmetry_pro.ext:register_all",
        )],
    )

    doc = _run_and_parse(capsys, _ns())
    ext_block = doc["extensions"]
    assert ext_block["importable_count"] == 1
    assert ext_block["broken_count"] == 0
    assert ext_block["discovered"] == [{
        "name": "clawmetry-pro",
        "value": "clawmetry_pro.ext:register_all",
        "importable": True,
        "error": None,
    }]


def test_extensions_reports_broken_pro(stub_home, capsys, monkeypatch):
    """Wheel-on-disk-but-import-fails scenario: entry point fails to load →
    ``importable: False`` + ``error`` populated + ``broken_count`` bumps.
    This is the whole reason the block exists — the disk-marker check
    (``runtimes.pro_installed_version``) shows green in this scenario, but
    the extension probe correctly reports the plugin won't actually load.
    """
    import clawmetry.extensions as ext

    class _BadEP:
        name = "clawmetry-pro"
        value = "clawmetry_pro.ext:register_all"

        def load(self):
            raise ImportError("cannot import 'clawmetry_pro._core'")

    monkeypatch.setattr(ext, "_select_entry_points", lambda group: [_BadEP()])

    doc = _run_and_parse(capsys, _ns())
    ext_block = doc["extensions"]
    assert ext_block["importable_count"] == 0
    assert ext_block["broken_count"] == 1
    row = ext_block["discovered"][0]
    assert row["name"] == "clawmetry-pro"
    assert row["importable"] is False
    assert "cannot import" in row["error"]


def test_extensions_survives_probe_failure(stub_home, capsys, monkeypatch):
    """Probe helper itself blows up → snapshot still emits the zero-shape
    default (no ``null``s, no 5xx). Guards the never-crash contract every
    other CLI diagnostic honours.
    """
    from clawmetry import extensions as _ext

    def _explode():
        raise RuntimeError("probe broke")

    monkeypatch.setattr(_ext, "probe_plugins", _explode)

    doc = _run_and_parse(capsys, _ns())
    assert doc["extensions"] == {
        "discovered": [],
        "importable_count": 0,
        "broken_count": 0,
    }


def test_extensions_does_not_leak_into_loaded_mirror(stub_home, capsys, monkeypatch):
    """Probing from ``clawmetry status`` must NOT populate the in-process
    ``loaded_plugins`` mirror the daemon later relies on. Otherwise a
    status-call-then-start-daemon sequence would show the same plugin in
    both counters, or a probe of a broken plugin would poison
    ``failed_plugins`` for an unrelated pass. Orthogonal by design.
    """
    import clawmetry.extensions as ext
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: [_FakeEntryPoint(
            lambda: None, name="clawmetry-pro", value="pkg:reg",
        )],
    )

    _run_and_parse(capsys, _ns())

    assert ext.loaded_plugins() == []
    assert ext.failed_plugins() == []
    assert ext._loaded is False


# ── human path ───────────────────────────────────────────────────────────────


def test_extensions_human_path_shows_importable_row(stub_home, capsys, monkeypatch):
    """Without ``--json`` the human path renders an ✅ row per importable
    plugin. Absence would leave operators with no in-``status`` signal that
    the paid package is wired in — the whole triage question this feature
    answers."""
    import clawmetry.extensions as ext
    monkeypatch.setattr(
        ext, "_select_entry_points",
        lambda group: [_FakeEntryPoint(
            lambda: None, name="clawmetry-pro", value="pkg:reg",
        )],
    )

    import clawmetry.cli as cli
    cli._cmd_status(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "Extensions:" in out
    assert "clawmetry-pro" in out
    assert "importable" in out


def test_extensions_human_path_shows_broken_row(stub_home, capsys, monkeypatch):
    """A broken plugin renders an ❌ row with the error text so the operator
    can act without spelunking daemon logs."""
    import clawmetry.extensions as ext

    class _BadEP:
        name = "clawmetry-pro"
        value = "pkg:reg"

        def load(self):
            raise ImportError("cannot import 'clawmetry_pro._core'")

    monkeypatch.setattr(ext, "_select_entry_points", lambda group: [_BadEP()])

    import clawmetry.cli as cli
    cli._cmd_status(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "Extensions:" in out
    assert "clawmetry-pro" in out
    assert "cannot import" in out
    assert "will NOT load" in out


def test_extensions_human_path_omits_block_when_empty(stub_home, capsys, monkeypatch):
    """Zero discovered plugins → no ``Extensions:`` header. A fresh install
    should not paint an empty section that adds no information — the OSS
    core has no entry points of its own, so silence is the right default
    (matches the runtimes block's ``NemoClaw`` treatment above)."""
    import clawmetry.extensions as ext
    monkeypatch.setattr(ext, "_select_entry_points", lambda group: [])

    import clawmetry.cli as cli
    cli._cmd_status(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "Extensions:" not in out
