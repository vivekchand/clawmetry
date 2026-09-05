"""The gate must recognise its own hook when the launcher path is quoted.

Both of ClawMetry's shipped installs put the launcher under a path with a
space in it — ``~/Library/Application Support/ClawMetry/runtime/venv/bin``
on the macOS desktop app, ``C:\\Program Files\\...`` on Windows — so the
command we write quotes it. The ownership markers were matched against the
raw command string, where that quote sits exactly where the marker expects
a space, and the consequences were the two worst ones available:

* install could not see its OWN previous entry, so it appended a new one on
  every pass. A real machine reached 4,955 PreToolUse entries and a 1.6 MB
  settings.json;
* uninstall could not see it either, so it survived pointing at a deleted
  binary, erroring on every tool call.
"""
import json
import os

import pytest

from clawmetry import hook_ownership

QUOTED = ("'/Users/me/Library/Application Support/ClawMetry/runtime/venv/"
          "bin/clawmetry' hook claude-code --base http://127.0.0.1:8900")
PLAIN = "/Users/me/.clawmetry/bin/clawmetry hook claude-code --base http://x"
WINDOWS = ('"C:\\Program Files\\ClawMetry\\venv\\Scripts\\clawmetry.exe" '
           'hook claude-code --base http://127.0.0.1:8900')
LEGACY = ("'/Users/me/Application Support/venv/bin/python' -m clawmetry "
          "hook claude-code --base http://127.0.0.1:8900")

MARKER = "clawmetry hook claude-code"


@pytest.mark.parametrize("cmd", [QUOTED, PLAIN, WINDOWS, LEGACY])
def test_quoted_launcher_is_still_recognised_as_ours(cmd):
    assert hook_ownership.hook_is_ours({"command": cmd}, (MARKER,))


def test_foreign_hook_is_never_claimed():
    for cmd in ("/Users/me/.arize/harness/venv/bin/arize-hook-pre-tool-use",
                "'/opt/gk/bin/gk' ai hook claude-code",
                "my-linter --fix"):
        assert not hook_ownership.hook_is_ours({"command": cmd}, (MARKER,))


def test_command_binary_survives_a_space_in_the_path(tmp_path):
    d = tmp_path / "Application Support" / "bin"
    d.mkdir(parents=True)
    exe = d / "clawmetry"
    exe.write_text("#!/bin/sh\n")
    exe.chmod(0o755)
    cmd = f"'{exe}' hook claude-code --base http://x"
    # cmd.split()[0] would answer "'<tmp>/Application" — a path that does
    # not exist, so every staleness test on it was inverted.
    assert hook_ownership.command_binary(cmd) == str(exe)
    assert hook_ownership.command_binary_exists(cmd)
    exe.unlink()
    assert not hook_ownership.command_binary_exists(cmd)


def _gate(tmp_path, monkeypatch, launcher):
    """Point the gate at a throwaway HOME with *launcher* as its binary."""
    from clawmetry import claude_code_gate as g
    settings = tmp_path / "settings.json"
    monkeypatch.setattr(g, "_settings_path", lambda: str(settings))
    monkeypatch.setattr(g, "_STATE_PATH", str(tmp_path / "gate.json"))
    monkeypatch.setattr(g, "_MARKER_PATH", str(tmp_path / "marker.json"))
    monkeypatch.setattr(g, "_launcher_prefix", lambda: f"'{launcher}'")
    monkeypatch.setattr(g, "dashboard_base", lambda: "http://127.0.0.1:8900")
    return g, settings


def _spaced_launcher(tmp_path):
    d = tmp_path / "Application Support" / "ClawMetry" / "bin"
    d.mkdir(parents=True)
    exe = d / "clawmetry"
    exe.write_text("#!/bin/sh\n")
    exe.chmod(0o755)
    return exe


def _pretool(settings):
    return json.loads(settings.read_text())["hooks"]["PreToolUse"]


@pytest.mark.skipif(os.name == "nt", reason="POSIX quoting")
def test_install_is_idempotent_under_a_quoted_launcher(tmp_path, monkeypatch):
    """The regression itself: N installs must leave exactly ONE entry."""
    exe = _spaced_launcher(tmp_path)
    g, settings = _gate(tmp_path, monkeypatch, exe)
    for _ in range(5):
        g._install([])
    assert len(_pretool(settings)) == 1


@pytest.mark.skipif(os.name == "nt", reason="POSIX quoting")
def test_install_preserves_a_co_resident_writer(tmp_path, monkeypatch):
    exe = _spaced_launcher(tmp_path)
    g, settings = _gate(tmp_path, monkeypatch, exe)
    settings.write_text(json.dumps({"hooks": {"PreToolUse": [
        {"matcher": "Bash", "hooks": [
            {"type": "command", "command": "/opt/arize/hook-pre-tool-use"}]},
    ]}}))
    g._install([])
    g._install([])
    cmds = [h["command"] for e in _pretool(settings) for h in e["hooks"]]
    assert "/opt/arize/hook-pre-tool-use" in cmds
    assert sum("hook claude-code" in c for c in cmds) == 1


@pytest.mark.skipif(os.name == "nt", reason="POSIX quoting")
def test_uninstall_removes_the_quoted_entry(tmp_path, monkeypatch):
    exe = _spaced_launcher(tmp_path)
    g, settings = _gate(tmp_path, monkeypatch, exe)
    g._install([])
    assert _pretool(settings)
    g._uninstall()
    assert "PreToolUse" not in json.loads(settings.read_text()).get("hooks", {})


@pytest.mark.skipif(os.name == "nt", reason="POSIX quoting")
def test_stale_entry_is_swept_when_our_state_is_gone(tmp_path, monkeypatch):
    """The desktop-app case: the .app (and our state) is deleted, leaving an
    entry naming a binary that no longer exists. Nothing but this sweep will
    ever remove it, so an uninstall with no state must still do it — while
    leaving a foreign hook, and a LIVE ClawMetry hook, alone."""
    exe = _spaced_launcher(tmp_path)
    g, settings = _gate(tmp_path, monkeypatch, exe)
    g._install([])
    exe.unlink()                       # the .app went to the Trash
    os.remove(tmp_path / "gate.json")  # ~/.clawmetry was purged
    settings_data = json.loads(settings.read_text())
    settings_data["hooks"]["PreToolUse"].append(
        {"matcher": "Bash", "hooks": [
            {"type": "command", "command": "/opt/arize/hook-pre-tool-use"}]})
    settings.write_text(json.dumps(settings_data))

    g._uninstall()

    cmds = [h["command"] for e in _pretool(settings) for h in e["hooks"]]
    assert cmds == ["/opt/arize/hook-pre-tool-use"]


@pytest.mark.skipif(os.name == "nt", reason="POSIX quoting")
def test_stateless_uninstall_leaves_a_live_hook_alone(tmp_path, monkeypatch):
    """Counterpart to the sweep above: with no state proving we installed
    it, a hook whose binary still runs may be the operator's own manual
    install, and is not ours to delete."""
    exe = _spaced_launcher(tmp_path)
    g, settings = _gate(tmp_path, monkeypatch, exe)
    g._install([])
    os.remove(tmp_path / "gate.json")

    g._uninstall()

    cmds = [h["command"] for e in _pretool(settings) for h in e["hooks"]]
    assert any("hook claude-code" in c for c in cmds)
