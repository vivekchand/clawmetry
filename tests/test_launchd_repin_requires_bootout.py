"""A rewritten LaunchAgent plist only takes effect after bootout → bootstrap.

``launchctl bootstrap`` fails when the label is already registered, and the
legacy ``load -w`` fallback fails too *while still exiting 0*. So the old
registration path wrote a corrected plist to disk, failed to load it, and
printed "Running in the background. Your data is syncing to the cloud."
over a daemon launchd was still crash-looping from the stale definition.

That is not hypothetical: on 2026-10-14 a node's pinned interpreter lost the
``clawmetry`` package, the daemon died, and `clawmetry sync --restart` could
not repair it — the dashboard sat on "Step: starting" for ~5h.

``kickstart -k`` is NOT a fix: it restarts the job definition launchd already
holds in memory, so a changed ``ProgramArguments`` is still never re-read.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

import pytest

from clawmetry.cli import _launchd_reload, _register_launchd


class _Recorder:
    """Stands in for subprocess.run, recording the launchctl verbs used."""

    def __init__(self, rc_for):
        self.rc_for = rc_for
        self.verbs: list[str] = []

    def __call__(self, cmd, *a, **kw):
        self.verbs.append(cmd[1])
        return subprocess.CompletedProcess(cmd, self.rc_for(cmd[1]))


def _patch(monkeypatch, rc_for):
    rec = _Recorder(rc_for)
    monkeypatch.setattr("subprocess.run", rec)
    monkeypatch.setattr("time.sleep", lambda *_: None)
    return rec


def test_bootout_runs_before_bootstrap(monkeypatch, tmp_path):
    """The whole point: without the bootout, launchd keeps the old plist."""
    rec = _patch(monkeypatch, lambda verb: 0)
    plist = tmp_path / "com.clawmetry.sync.plist"
    plist.write_text("<plist/>")

    assert _launchd_reload(plist, "com.clawmetry.sync") is True
    assert "bootout" in rec.verbs, rec.verbs
    assert rec.verbs.index("bootout") < rec.verbs.index("bootstrap"), rec.verbs


def test_kickstart_is_not_used_as_the_fallback(monkeypatch, tmp_path):
    """kickstart -k restarts the STALE definition — it can never re-pin."""
    rec = _patch(monkeypatch, lambda verb: 0 if verb == "bootout" else 1)
    plist = tmp_path / "p.plist"
    plist.write_text("<plist/>")

    _launchd_reload(plist, "com.clawmetry.sync")
    assert "kickstart" not in rec.verbs, rec.verbs


def test_load_exiting_zero_is_not_trusted(monkeypatch, tmp_path):
    """`launchctl load -w` prints "Load failed" and still exits 0, so the
    result must be confirmed with a real lookup, not a returncode."""

    def rc_for(verb):
        if verb == "load":
            return 0  # the lie
        if verb == "print":
            return 1  # the truth: not registered
        return 1

    _patch(monkeypatch, rc_for)
    plist = tmp_path / "p.plist"
    plist.write_text("<plist/>")

    assert _launchd_reload(plist, "com.clawmetry.sync") is False


def test_registered_when_lookup_confirms_it(monkeypatch, tmp_path):
    _patch(monkeypatch, lambda verb: 0 if verb in ("load", "print") else 1)
    plist = tmp_path / "p.plist"
    plist.write_text("<plist/>")

    assert _launchd_reload(plist, "com.clawmetry.sync") is True


def test_register_launchd_never_claims_success_when_launchd_refused(
    monkeypatch, tmp_path, capsys
):
    """No "Running in the background" over a daemon that never came up."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setattr("clawmetry.cli._launchd_reload", lambda *a, **k: False)

    assert _register_launchd({"node_id": "n1"}) is False
    out = capsys.readouterr().out
    assert "Running in the background" not in out, out
    assert "syncing to the cloud" not in out, out
    assert "clawmetry sync --restart" in out, out
    # The reload unloaded the old job before failing to load the new one,
    # so nothing is registered at this moment. The old code could not make
    # things worse because it never unloaded; this one can, so say it.
    assert "registered right now" in out, out


def test_register_launchd_reports_success_when_it_took(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setattr("clawmetry.cli._launchd_reload", lambda *a, **k: True)

    assert _register_launchd({"node_id": "n1"}) is True
    assert "Running in the background" in capsys.readouterr().out


def test_plist_is_written_with_the_running_interpreter(monkeypatch, tmp_path):
    """The re-pin itself: the plist must carry sys.executable, which by
    definition can import clawmetry (it is running it)."""
    import sys

    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    monkeypatch.setattr("clawmetry.cli._launchd_reload", lambda *a, **k: True)
    _register_launchd({"node_id": "n1"})

    plist = (tmp_path / "Library" / "LaunchAgents"
             / "com.clawmetry.sync.plist").read_text()
    assert f"<string>{sys.executable}</string>" in plist


def test_cmd_sync_exits_nonzero_when_the_daemon_did_not_start():
    """A failed restart must not exit 0 — scripts and the installer branch
    on it, and `clawmetry status` is the only other signal the user gets."""
    src = pathlib.Path(__file__).resolve().parents[1].joinpath(
        "clawmetry", "cli.py").read_text()
    m = re.search(r"ok = _start_daemon\(config, args\)\s*\n\s*if not ok:\s*\n\s*sys\.exit\(1\)", src)
    assert m, "_cmd_sync must propagate _start_daemon failure"


def test_sandbox_registrar_keeps_its_bootout():
    """The NemoClaw sandbox registrar already did this correctly; make sure
    a future refactor does not drop it there either."""
    src = pathlib.Path(__file__).resolve().parents[1].joinpath(
        "clawmetry", "cli.py").read_text()
    assert src.count('"bootout"') >= 2, "a launchd registrar lost its bootout"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
