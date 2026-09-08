"""
Stale-CLI detection (clawmetry/installs.py).

Guards the 2026-07-31 founder live-hit: a pre-venv ``pip install --user``
copy shadowed ``~/.clawmetry/bin`` on PATH, so ``clawmetry --version`` /
``status`` reported 0.12.601 while the daemon's auto-updated venv ran
0.12.606 — which read as "auto-update is broken". The fix is detection +
an honest warning; these tests pin every branch of that detection.

Pure unit tests: temp dirs only, no network, no running server.
"""
import io
import os
import sys

import pytest

from clawmetry import installs


def _mk_daemon_home(tmp_path, version="0.12.606", layout="posix", extra=()):
    """Fake ``~/.clawmetry`` venv with a clawmetry dist-info of ``version``."""
    home = tmp_path / ".clawmetry"
    if layout == "posix":
        sp = home / "lib" / "python3.12" / "site-packages"
        (home / "bin").mkdir(parents=True)
    else:
        sp = home / "Lib" / "site-packages"
        (home / "Scripts").mkdir(parents=True)
    sp.mkdir(parents=True, exist_ok=True)
    for v in (version, *extra):
        (sp / "clawmetry-{0}.dist-info".format(v)).mkdir()
    return home


# ── version parsing / comparison ─────────────────────────────────────────────

def test_version_gt_basic():
    assert installs.version_gt("0.12.606", "0.12.601")
    assert not installs.version_gt("0.12.601", "0.12.606")
    assert not installs.version_gt("0.12.606", "0.12.606")
    # multi-digit segments compare numerically, not lexically
    assert installs.version_gt("0.12.610", "0.12.69")


def test_parse_version_tolerates_garbage():
    assert installs.parse_version(None) == (0,)
    assert installs.parse_version("0.12.5rc1") == (0, 12, 5)


# ── daemon env discovery ─────────────────────────────────────────────────────

def test_daemon_env_version_posix_layout(tmp_path):
    home = _mk_daemon_home(tmp_path, "0.12.606", layout="posix")
    assert installs.daemon_env_version(home) == "0.12.606"


def test_daemon_env_version_windows_layout(tmp_path):
    home = _mk_daemon_home(tmp_path, "0.12.606", layout="windows")
    assert installs.daemon_env_version(home) == "0.12.606"


def test_daemon_env_version_picks_newest_of_debris(tmp_path):
    home = _mk_daemon_home(tmp_path, "0.12.606", extra=("0.12.599",))
    assert installs.daemon_env_version(home) == "0.12.606"


def test_daemon_env_version_ignores_pro_wheel_and_debris(tmp_path):
    home = _mk_daemon_home(tmp_path, "0.12.606")
    sp = next(home.glob("lib/python*/site-packages"))
    # clawmetry_pro must not match; ~lawmetry debris must not match
    (sp / "clawmetry_pro-0.5.0.dist-info").mkdir()
    (sp / "~lawmetry").mkdir()
    assert installs.daemon_env_version(home) == "0.12.606"


def test_daemon_env_version_absent(tmp_path):
    assert installs.daemon_env_version(tmp_path / "nope") is None


# ── stale detection ──────────────────────────────────────────────────────────

def test_snapshot_flags_stale_cli(tmp_path, monkeypatch):
    home = _mk_daemon_home(tmp_path, "0.12.606")
    monkeypatch.setattr(installs, "cli_version", lambda: "0.12.601")
    monkeypatch.setattr(installs, "running_in_daemon_env", lambda home=None: False)
    snap = installs.installs_snapshot(home)
    assert snap["stale_cli"] is True
    assert snap["daemon_env"]["version"] == "0.12.606"
    assert snap["cli"]["version"] == "0.12.601"


def test_snapshot_not_stale_when_versions_match(tmp_path, monkeypatch):
    home = _mk_daemon_home(tmp_path, "0.12.606")
    monkeypatch.setattr(installs, "cli_version", lambda: "0.12.606")
    monkeypatch.setattr(installs, "running_in_daemon_env", lambda home=None: False)
    assert installs.installs_snapshot(home)["stale_cli"] is False


def test_snapshot_not_stale_inside_daemon_env(tmp_path, monkeypatch):
    """The daemon venv's own CLI is never 'stale' even mid-upgrade."""
    home = _mk_daemon_home(tmp_path, "0.12.606")
    monkeypatch.setattr(installs, "cli_version", lambda: "0.12.601")
    monkeypatch.setattr(installs, "running_in_daemon_env", lambda home=None: True)
    assert installs.installs_snapshot(home)["stale_cli"] is False


def test_snapshot_not_stale_without_daemon_env(tmp_path, monkeypatch):
    """Single-environment installs (no ~/.clawmetry venv) never warn."""
    monkeypatch.setattr(installs, "cli_version", lambda: "0.12.601")
    snap = installs.installs_snapshot(tmp_path / "absent")
    assert snap["stale_cli"] is False
    assert snap["daemon_env"]["present"] is False


def test_snapshot_not_stale_when_cli_newer(tmp_path, monkeypatch):
    """A dev checkout newer than the venv is fine — only OLDER warns."""
    home = _mk_daemon_home(tmp_path, "0.12.606")
    monkeypatch.setattr(installs, "cli_version", lambda: "0.13.0")
    monkeypatch.setattr(installs, "running_in_daemon_env", lambda home=None: False)
    assert installs.installs_snapshot(home)["stale_cli"] is False


def test_running_in_daemon_env_detects_prefix(tmp_path, monkeypatch):
    home = _mk_daemon_home(tmp_path, "0.12.606")
    monkeypatch.setattr(installs.sys, "prefix", str(home))
    assert installs.running_in_daemon_env(home) is True
    monkeypatch.setattr(installs.sys, "prefix", str(tmp_path / "other"))
    assert installs.running_in_daemon_env(home) is False


# ── warning output ───────────────────────────────────────────────────────────

def test_warning_prints_versions_and_fix(tmp_path, monkeypatch):
    home = _mk_daemon_home(tmp_path, "0.12.606")
    monkeypatch.setattr(installs, "cli_version", lambda: "0.12.601")
    monkeypatch.setattr(installs, "running_in_daemon_env", lambda home=None: False)
    monkeypatch.setattr(installs, "daemon_home", lambda: home)
    buf = io.StringIO()
    assert installs.maybe_warn_stale_cli(stream=buf) is True
    text = buf.getvalue()
    assert "0.12.601" in text and "0.12.606" in text
    assert "pip install" in text
    # user-facing copy rule: no em-dashes
    assert "—" not in text


def test_warning_silent_when_current(tmp_path, monkeypatch):
    home = _mk_daemon_home(tmp_path, "0.12.606")
    monkeypatch.setattr(installs, "cli_version", lambda: "0.12.606")
    monkeypatch.setattr(installs, "daemon_home", lambda: home)
    buf = io.StringIO()
    assert installs.maybe_warn_stale_cli(stream=buf) is False
    assert buf.getvalue() == ""


def test_warning_env_kill_switch(tmp_path, monkeypatch):
    home = _mk_daemon_home(tmp_path, "0.12.606")
    monkeypatch.setattr(installs, "cli_version", lambda: "0.12.601")
    monkeypatch.setattr(installs, "running_in_daemon_env", lambda home=None: False)
    monkeypatch.setattr(installs, "daemon_home", lambda: home)
    monkeypatch.setenv("CLAWMETRY_NO_STALE_WARN", "1")
    buf = io.StringIO()
    assert installs.maybe_warn_stale_cli(stream=buf) is False
    assert buf.getvalue() == ""


# ── PATH census ──────────────────────────────────────────────────────────────

@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX exec bits")
def test_path_executables_dedups_symlinks(tmp_path, monkeypatch):
    d1 = tmp_path / "bin1"
    d2 = tmp_path / "bin2"
    d1.mkdir()
    d2.mkdir()
    real = d1 / "clawmetry"
    real.write_text("#!/bin/sh\necho clawmetry 0.0.1\n")
    real.chmod(0o755)
    (d2 / "clawmetry").symlink_to(real)
    monkeypatch.setenv("PATH", os.pathsep.join([str(d1), str(d2)]))
    exes = installs.path_executables()
    assert len(exes) == 1
    assert exes[0] == real


@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX shebang")
def test_executable_version_parses_output(tmp_path):
    exe = tmp_path / "clawmetry"
    exe.write_text("#!/bin/sh\necho 'clawmetry 0.12.601'\n")
    exe.chmod(0o755)
    assert installs.executable_version(exe) == "0.12.601"
    assert installs.executable_version(tmp_path / "missing") is None


# ── doctor census never breaks connectivity checks ───────────────────────────

def test_doctor_check_installs_never_raises(monkeypatch):
    from clawmetry import doctor
    monkeypatch.setattr(installs, "installs_snapshot",
                        lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    lines = []
    # Must swallow the error and return, not raise.
    doctor.check_installs(out=lines.append)
    assert any("skipped" in ln for ln in lines)


def test_doctor_census_flags_stale_path_copy(tmp_path, monkeypatch):
    """End-to-end census: stale PATH copy + current daemon env -> WARN + fix."""
    from clawmetry import doctor
    home = _mk_daemon_home(tmp_path, "0.12.606")
    bin_dir = tmp_path / "userbin"
    bin_dir.mkdir()
    exe = bin_dir / "clawmetry"
    exe.write_text("#!/bin/sh\necho 'clawmetry 0.12.601'\n")
    exe.chmod(0o755)
    monkeypatch.setattr(installs, "daemon_home", lambda: home)
    monkeypatch.setenv("PATH", str(bin_dir))
    lines = []
    warnings = doctor.check_installs(out=lines.append)
    text = "\n".join(lines)
    if not sys.platform.startswith("win"):
        assert warnings >= 1
        assert "STALE" in text
        assert "pip install" in text
    assert "0.12.606" in text  # daemon env always reported
