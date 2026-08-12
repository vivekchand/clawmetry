"""Regression coverage for the "drag-to-trash → auto-login on reinstall"
bug (support 2026-08-12).

Three things must hold for the fix to work:

  1. ``clawmetry uninstall`` strips the ``clawmetry`` key from
     ``~/.openclaw/openclaw.json``, leaving other OpenClaw keys intact.
     Without this, a stale cloud token silently signs the user back in.

  2. The ``clawmetry uninstall --dry-run`` output lists the desktop
     runtime dir under ``~/Library/Application Support/ClawMetry`` (the
     thin-shell venv, bootstrap.log, onboarding-completed.json). This
     was the piece drag-to-trash left behind pre-fix.

  3. The macOS app-vanished LaunchAgent plist is valid XML/plist and
     its shell command is well-formed sh (so plutil/launchd accept it
     when we drop it during desktop bootstrap).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _reload_cli(monkeypatch, home: Path):
    """Re-import the CLI with HOME pointed at a fresh tmp dir so
    ``Path.home()`` inside module-level constants (CONFIG_FILE etc.)
    resolves under the tmpdir, not the developer's real home."""
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))  # Windows shim
    sys.modules.pop("clawmetry.cli", None)
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.cli as cli
    return cli


def test_strip_clawmetry_from_openclaw_json_preserves_other_keys(
    tmp_path, monkeypatch
):
    home = tmp_path / "home"
    (home / ".openclaw").mkdir(parents=True)
    p = home / ".openclaw" / "openclaw.json"
    p.write_text(
        json.dumps(
            {
                "clawmetry": {"cloudToken": "cm_deadbeef"},
                "chat": {"provider": "telegram"},
                "gateway": {"token": "keep-me"},
            }
        )
    )

    cli = _reload_cli(monkeypatch, home)
    changed, path = cli._strip_clawmetry_from_openclaw_json()

    assert changed is True
    assert path == str(p)
    remaining = json.loads(p.read_text())
    assert "clawmetry" not in remaining
    assert remaining["chat"]["provider"] == "telegram"
    assert remaining["gateway"]["token"] == "keep-me"


def test_strip_deletes_openclaw_json_when_our_key_was_the_only_content(
    tmp_path, monkeypatch
):
    home = tmp_path / "home"
    (home / ".openclaw").mkdir(parents=True)
    p = home / ".openclaw" / "openclaw.json"
    p.write_text(json.dumps({"clawmetry": {"cloudToken": "cm_solo"}}))

    cli = _reload_cli(monkeypatch, home)
    changed, _ = cli._strip_clawmetry_from_openclaw_json()

    assert changed is True
    # Nothing else was in the file, so we clean up the stub rather than
    # leaving a `{}` behind for OpenClaw to trip on later.
    assert not p.exists()


def test_strip_is_noop_when_key_absent(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".openclaw").mkdir(parents=True)
    p = home / ".openclaw" / "openclaw.json"
    p.write_text(json.dumps({"chat": {"provider": "signal"}}))

    cli = _reload_cli(monkeypatch, home)
    changed, _ = cli._strip_clawmetry_from_openclaw_json()

    assert changed is False
    # File untouched.
    assert json.loads(p.read_text()) == {"chat": {"provider": "signal"}}


def test_dry_run_lists_desktop_runtime_dir(tmp_path, monkeypatch, capsys):
    """The drag-to-trash bug's root cause: this directory used to
    survive an uninstall. The dry-run should now enumerate it so users
    (and the fix's future maintainers) can see it will be removed."""
    home = tmp_path / "home"
    runtime = home / "Library" / "Application Support" / "ClawMetry"
    runtime.mkdir(parents=True)
    (runtime / "runtime").mkdir()
    (runtime / "runtime" / "bootstrap.log").write_text("hello")

    cli = _reload_cli(monkeypatch, home)

    class _Args:
        yes = False
        unattended = False
        keep_data = False
        dry_run = True

    cli._cmd_uninstall(_Args())
    out = capsys.readouterr().out
    assert "Desktop runtime dir" in out
    assert str(runtime) in out


def test_dry_run_lists_openclaw_token_strip_when_present(
    tmp_path, monkeypatch, capsys
):
    home = tmp_path / "home"
    (home / ".openclaw").mkdir(parents=True)
    (home / ".openclaw" / "openclaw.json").write_text(
        json.dumps({"clawmetry": {"cloudToken": "cm_x"}, "chat": {}})
    )

    cli = _reload_cli(monkeypatch, home)

    class _Args:
        yes = False
        unattended = False
        keep_data = False
        dry_run = True

    cli._cmd_uninstall(_Args())
    out = capsys.readouterr().out
    assert "Strip clawmetry.cloudToken" in out


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only watchdog")
def test_watchdog_plist_is_valid_plist_and_shell_syntax(tmp_path):
    from clawmetry.watchdog import _render_plist

    runtime = tmp_path / "runtime"
    runtime.mkdir()
    xml = _render_plist(
        app_path=Path("/Applications/ClawMetry.app"),
        runtime_dir=runtime,
        venv_clawmetry=runtime / "venv" / "bin" / "clawmetry",
    )
    plist = tmp_path / "wd.plist"
    plist.write_text(xml)

    # plutil ships with every macOS.
    r = subprocess.run(
        ["plutil", "-lint", str(plist)], capture_output=True, text=True
    )
    assert r.returncode == 0, r.stdout + r.stderr

    # The `sh` shipped with the plist has to be well-formed too.
    # Extract the third ProgramArgument (the -c payload) via plutil.
    cmd = subprocess.check_output(
        ["plutil", "-extract", "ProgramArguments.2", "raw", str(plist)],
        text=True,
    ).strip()
    r2 = subprocess.run(
        ["sh", "-n", "-c", cmd], capture_output=True, text=True
    )
    assert r2.returncode == 0, r2.stderr


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only watchdog")
def test_watchdog_install_is_noop_in_dev_mode(tmp_path, monkeypatch):
    """Dev launches (``python desktop/app.py`` with sys.frozen unset)
    must not drop a plist. A dev-machine plist would keep pointing at
    the developer's checkout venv forever."""
    from clawmetry import watchdog

    monkeypatch.setattr(sys, "frozen", False, raising=False)
    # Redirect LaunchAgents dir into tmp so we don't scribble on the
    # real one even if the guard breaks.
    monkeypatch.setenv("HOME", str(tmp_path))

    installed = watchdog.ensure_app_watchdog_installed(
        runtime_dir=tmp_path / "runtime",
        venv_clawmetry=tmp_path / "runtime" / "venv" / "bin" / "clawmetry",
    )
    assert installed is False
    assert not (
        tmp_path / "Library" / "LaunchAgents"
        / f"{watchdog.LABEL}.plist"
    ).exists()
