"""
Tests for multi-profile OpenClaw workspace discovery (issue #950).

Builds a tmpdir as a fake $HOME containing three workspaces in the patterns
clawmetry should detect:

  - $HOME/.openclaw                  (canonical default)
  - $HOME/.openclaw-personal         (suffix-style profile)
  - $HOME/.openclaw/profiles/exp     (profiles/ convention)

Plus negative cases (symlink, non-workspace dir) to confirm safety.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from clawmetry.sync import discover_workspaces


def _make_ws(path: Path, agents=("main",)) -> None:
    """Create a directory that looks like a real OpenClaw workspace."""
    path.mkdir(parents=True, exist_ok=True)
    (path / "SOUL.md").write_text("# fake workspace\n")
    for agent in agents:
        sd = path / "agents" / agent / "sessions"
        sd.mkdir(parents=True, exist_ok=True)
        # touch a session file so last_active_ts is non-zero
        (sd / "fake.jsonl").write_text("{}\n")


@pytest.fixture
def fake_home(tmp_path):
    """Yield a tmpdir we can treat as $HOME."""
    return tmp_path


def test_discover_three_workspace_patterns(fake_home):
    _make_ws(fake_home / ".openclaw")
    _make_ws(fake_home / ".openclaw-personal")
    _make_ws(fake_home / ".openclaw" / "profiles" / "exp")

    found = discover_workspaces(home=fake_home)
    names = {w["name"] for w in found}
    paths = {w["path"] for w in found}

    assert len(found) >= 3, f"expected 3 workspaces, got {found}"
    assert "default" in names
    assert "personal" in names
    assert "exp" in names
    assert str((fake_home / ".openclaw").resolve()) in paths
    assert str((fake_home / ".openclaw-personal").resolve()) in paths
    assert str((fake_home / ".openclaw" / "profiles" / "exp").resolve()) in paths


def test_single_workspace_zero_config(fake_home):
    """Zero-config: one workspace must still be detected."""
    _make_ws(fake_home / ".openclaw")
    found = discover_workspaces(home=fake_home)
    assert len(found) == 1
    assert found[0]["name"] == "default"


def test_no_workspaces_returns_empty(fake_home):
    """No openclaw dirs anywhere — empty list, no crash."""
    found = discover_workspaces(home=fake_home)
    assert found == []


def test_ignores_symlinks(fake_home):
    """Symlinked profile dirs should be skipped (security guard)."""
    real = fake_home / "elsewhere"
    _make_ws(real)
    link = fake_home / ".openclaw-evil"
    try:
        os.symlink(str(real), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    found = discover_workspaces(home=fake_home)
    names = {w["name"] for w in found}
    assert "evil" not in names


def test_ignores_random_dotdir(fake_home):
    """A random dir without OpenClaw markers shouldn't be claimed."""
    (fake_home / ".openclaw-junk").mkdir()
    (fake_home / ".openclaw-junk" / "README").write_text("not a workspace")
    found = discover_workspaces(home=fake_home)
    names = {w["name"] for w in found}
    assert "junk" not in names


def test_curated_workspaces_json(fake_home):
    """~/.clawmetry/workspaces.json adds user-curated entries."""
    custom = fake_home / "my-bot"
    _make_ws(custom, agents=("main", "research"))
    cfg_dir = fake_home / ".clawmetry"
    cfg_dir.mkdir()
    (cfg_dir / "workspaces.json").write_text(
        json.dumps({"workspaces": [{"name": "bot", "path": str(custom)}]})
    )
    found = discover_workspaces(home=fake_home)
    names = {w["name"] for w in found}
    assert "bot" in names
    bot = next(w for w in found if w["name"] == "bot")
    assert bot["agent_count"] == 2


def test_agent_count_and_last_active(fake_home):
    """Workspace metadata reports agent count + a non-zero activity ts."""
    ws = fake_home / ".openclaw"
    _make_ws(ws, agents=("main", "scheduler"))
    found = discover_workspaces(home=fake_home)
    assert len(found) == 1
    entry = found[0]
    assert entry["agent_count"] == 2
    assert entry["last_active_ts"] > 0


def test_sorted_by_last_active_desc(fake_home, monkeypatch):
    """Most-recently-active workspace surfaces first."""
    old = fake_home / ".openclaw-old"
    new = fake_home / ".openclaw"
    _make_ws(old)
    _make_ws(new)
    # Backdate the old workspace's session file by 1 day.
    stale_file = old / "agents" / "main" / "sessions" / "fake.jsonl"
    backdated = stale_file.stat().st_mtime - 86400
    os.utime(stale_file, (backdated, backdated))
    found = discover_workspaces(home=fake_home)
    assert found[0]["name"] == "default"  # ~/.openclaw (newest)
