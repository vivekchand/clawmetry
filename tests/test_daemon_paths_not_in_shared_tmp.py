"""The dashboard daemon's pid file and log must not live in the shared /tmp.

Both used to sit at a fixed, predictable name in the shared temp directory:
``/tmp/clawmetry.pid`` and ``/tmp/clawmetry.log``. On a multi-user POSIX
machine /tmp is world-writable, so any other local account can pre-create
either name -- or leave a symlink standing in for it -- and this user's write
then follows that symlink back out of /tmp under this user's own privileges.

The pid write is one integer. The log is worse: ``_build_plist`` aimed BOTH
``StandardOutPath`` and ``StandardErrorPath`` at it, and its one caller never
passed the argument, so the shared-temp default was the path launchd actually
used. A symlink planted there is an append primitive against any file this
user can write, for as long as the daemon runs.

Both now resolve under ``~/.clawmetry/``, which the user owns, matching where
``clawmetry/proxy.py`` already keeps ``proxy.pid``. The legacy paths stay
READABLE so an instance started by an older build is still discoverable by
``status``/``stop`` and by the stale-instance reclaim -- nothing writes them.
"""
from __future__ import annotations

import ast
import os
import pathlib

import pytest

_DASHBOARD = pathlib.Path(__file__).resolve().parent.parent / "dashboard.py"
_SOURCE = _DASHBOARD.read_text(encoding="utf-8")
_TREE = ast.parse(_SOURCE)


def _assign(name):
    """The source text of the module-level assignment to `name`."""
    for node in _TREE.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return ast.get_source_segment(_SOURCE, node.value) or ""
    raise AssertionError("no module-level assignment to %s" % name)


def _funcdef(name):
    for node in ast.walk(_TREE):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError("no function %s" % name)


def test_pid_and_log_paths_derive_from_the_user_home():
    """Neither path may be built from the shared temp directory."""
    for const in ("PID_FILE", "DAEMON_LOG_FILE"):
        src = _assign(const)
        assert "_DAEMON_DIR" in src, "%s should sit under ~/.clawmetry: %r" % (const, src)
        assert "gettempdir" not in src, "%s must not use the shared temp dir" % const
        assert "/tmp/" not in src, "%s must not hardcode a /tmp path" % const
    home = _assign("_DAEMON_DIR")
    assert "expanduser" in home and ".clawmetry" in home, home


def test_build_plist_has_no_shared_tmp_default():
    """The default launchd log path was the one actually used."""
    fn = _funcdef("_build_plist")
    defaults = [ast.get_source_segment(_SOURCE, d) or "" for d in fn.args.defaults]
    for d in defaults:
        assert "/tmp/" not in d, "_build_plist default must not point into /tmp: %r" % d


def test_legacy_pid_locations_are_read_only():
    """The /tmp path may survive only as a read fallback, never a write target."""
    legacy = _assign("_LEGACY_PID_FILES")
    assert "/tmp/clawmetry.pid" in legacy, "legacy read fallback was dropped"
    write = _funcdef("_write_pid")
    written = ast.dump(ast.Module(body=write.body, type_ignores=[]))
    assert "_LEGACY_PID_FILES" not in written, "_write_pid must never write a legacy path"
    read = ast.dump(ast.Module(body=_funcdef("_read_pid").body, type_ignores=[]))
    assert "_LEGACY_PID_FILES" in read, "_read_pid lost the legacy fallback"


def test_no_shared_tmp_clawmetry_path_is_opened_anywhere():
    """A /tmp/clawmetry* literal may appear in prose, not in live code."""
    offenders = []
    for node in ast.walk(_TREE):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.startswith("/tmp/clawmetry"):
                offenders.append((node.lineno, node.value))
    # Only the declared read-only legacy pid path is allowed to remain.
    unexpected = [o for o in offenders if o[1] != "/tmp/clawmetry.pid"]
    assert not unexpected, "unexpected shared-temp literals: %r" % (unexpected,)


@pytest.mark.parametrize("const", ["PID_FILE", "DAEMON_LOG_FILE"])
def test_runtime_paths_are_under_the_home_directory(const, tmp_path, monkeypatch):
    """Imported for real, both paths resolve inside the user's own directory."""
    pytest.importorskip("flask")
    monkeypatch.setenv("HOME", str(tmp_path))
    dashboard = pytest.importorskip("dashboard")
    value = getattr(dashboard, const)
    assert ".clawmetry" in value, value
    assert not value.startswith("/tmp/clawmetry"), value
    assert os.path.basename(os.path.dirname(value)) == ".clawmetry", value


def test_read_pid_falls_back_to_a_legacy_file(tmp_path, monkeypatch):
    """An instance started by an older build stays discoverable."""
    pytest.importorskip("flask")
    dashboard = pytest.importorskip("dashboard")
    new_pid = tmp_path / ".clawmetry" / "clawmetry.pid"
    legacy = tmp_path / "legacy.pid"
    monkeypatch.setattr(dashboard, "_DAEMON_DIR", str(new_pid.parent))
    monkeypatch.setattr(dashboard, "PID_FILE", str(new_pid))
    monkeypatch.setattr(dashboard, "_LEGACY_PID_FILES", (str(legacy),))

    assert dashboard._read_pid() is None

    legacy.write_text("777\n")
    assert dashboard._read_pid() == 777, "legacy pid file was not read"

    dashboard._write_pid(1111)
    assert new_pid.read_text().strip() == "1111"
    assert legacy.read_text().strip() == "777", "_write_pid wrote a legacy path"
    assert dashboard._read_pid() == 1111, "the current path must win"

    new_pid.write_text("not-a-pid")
    legacy.unlink()
    assert dashboard._read_pid() is None, "unreadable pid must read as nothing"
