"""Skills tab must walk every candidate skill directory.

The previous ``_get_skills_dir`` returned the FIRST candidate that
existed and stopped, so ``~/.openclaw/plugin-skills/`` (which OpenClaw
plugins like ``browser-automation`` symlink into) was invisible to the
dashboard on any host that hadn't also created ``~/.openclaw/skills/``.

This test pins:
  1. ``_get_skills_dirs`` returns every existing candidate
  2. ``_find_skill_dir`` resolves a name from ANY candidate
  3. ``/api/skills`` lists skills found in ``plugin-skills/``
  4. ``/api/skills/<name>`` returns 200 for a plugin skill
"""

from __future__ import annotations

import os

import pytest
from flask import Flask


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Point HOME + WORKSPACE at an isolated tmp dir so the skills
    helpers don't pick up real ~/.openclaw content during the test."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("OPENCLAW_HOME", str(tmp_path / "workspace"))
    return tmp_path


def _make_skill(base, name, body="Header line.\nMore body."):
    sk = base / name
    sk.mkdir(parents=True, exist_ok=True)
    (sk / "SKILL.md").write_text(
        "---\nname: " + name + "\ndescription: test skill\n---\n" + body
    )
    return sk


def _client(fake_home):
    # Ensure dashboard module's WORKSPACE matches HOME so the workspace
    # branch of the candidate list resolves cleanly.
    import dashboard as _d
    _d.WORKSPACE = str(fake_home / "workspace")

    app = Flask(__name__)
    from routes.skills import bp_skills
    app.register_blueprint(bp_skills)
    return app.test_client()


def test_plugin_skills_dir_is_enumerated(fake_home):
    plugin_dir = fake_home / ".openclaw" / "plugin-skills"
    _make_skill(plugin_dir, "browser-automation")

    from routes.skills import _get_skills_dirs
    dirs = _get_skills_dirs()
    assert any("plugin-skills" in d for d in dirs), (
        "expected plugin-skills/ in candidate list, got " + repr(dirs)
    )


def test_find_skill_resolves_from_plugin_dir(fake_home):
    _make_skill(fake_home / ".openclaw" / "plugin-skills", "browser-automation")
    from routes.skills import _find_skill_dir
    p = _find_skill_dir("browser-automation")
    assert p is not None
    assert p.endswith("/plugin-skills/browser-automation")


def test_user_skill_shadows_plugin_skill_on_name_collision(fake_home):
    """If both ``skills/`` and ``plugin-skills/`` ship a skill with the
    same name the user-installed copy must win (matches the gateway's
    import-resolution order)."""
    _make_skill(fake_home / ".openclaw" / "skills", "shared")
    _make_skill(fake_home / ".openclaw" / "plugin-skills", "shared")

    from routes.skills import _find_skill_dir
    p = _find_skill_dir("shared")
    assert p is not None
    assert "/skills/shared" in p and "plugin-skills" not in p


def test_api_skills_lists_plugin_skill(fake_home):
    _make_skill(fake_home / ".openclaw" / "plugin-skills", "browser-automation")

    client = _client(fake_home)
    resp = client.get("/api/skills")
    assert resp.status_code == 200
    data = resp.get_json()
    names = [s["name"] for s in (data.get("skills") or [])]
    assert "browser-automation" in names
    assert data["summary"]["total_installed"] == 1


def test_api_skill_detail_returns_200_for_plugin_skill(fake_home):
    _make_skill(fake_home / ".openclaw" / "plugin-skills", "browser-automation")

    client = _client(fake_home)
    resp = client.get("/api/skills/browser-automation")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "browser-automation"
    assert "/plugin-skills/browser-automation" in data["skill_dir"]
