"""Tests for the runtime-hook lifecycle contract (#4817).

Non-negotiable requirement: uninstalling ClawMetry must remove every
hook cleanly so the runtime that had a hook installed continues to
boot without errors, and installing one must never drop a hook the
user or another tool already registered.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


@pytest.fixture
def hooks_env(tmp_path, monkeypatch):
    """Point the manifest, backups and lock at tmp_path so tests never
    touch a real ~/.clawmetry/hooks directory."""
    from clawmetry import hooks

    root = tmp_path / "hooks"
    monkeypatch.setattr(hooks, "_MANIFEST_DIR", root)
    monkeypatch.setattr(hooks, "_MANIFEST_PATH", root / "installed.json")
    monkeypatch.setattr(hooks, "_BACKUP_DIR", root / "backups")
    monkeypatch.setattr(hooks, "_LOCK_PATH", root / ".manifest.lock")
    return hooks


OUR_ENTRY = {"matcher": "*", "hooks": [{"type": "command", "command": "ours"}]}
USER_ENTRY = {"matcher": "Bash", "hooks": [{"type": "command", "command": "theirs"}]}


def _spec(tmp_path, **over):
    from clawmetry.hooks import HookSpec

    return HookSpec(
        id=over.pop("id", "claude_code.approval_prompt_capture"),
        runtime=over.pop("runtime", "claude_code"),
        purpose=over.pop("purpose", "test-only"),
        install_path=over.pop(
            "install_path", str(tmp_path / "runtime" / "hook.js")),
        hook_content=over.pop("hook_content", "console.log('hook');\n"),
        target_config=over.pop("target_config", None),
        target_config_key=over.pop("target_config_key", None),
        target_config_value=over.pop("target_config_value", None),
        clawmetry_version=over.pop("clawmetry_version", "0.12.906"),
    )


def _config_spec(tmp_path, cfg, **over):
    over.setdefault("target_config", str(cfg))
    over.setdefault("target_config_key", "hooks.PreToolUse")
    over.setdefault("target_config_value", [OUR_ENTRY])
    return _spec(tmp_path, **over)


def _manifest(hooks_mod):
    return json.loads(hooks_mod._MANIFEST_PATH.read_text())["hooks"]


# ── install ──────────────────────────────────────────────────────────────

def test_install_writes_manifest_and_file(hooks_env, tmp_path):
    s = _spec(tmp_path)
    hooks_env.install(s)

    assert Path(s.install_path).read_text() == s.hook_content
    (entry,) = _manifest(hooks_env)
    assert entry["id"] == s.id
    assert entry["checksum"].startswith("sha256:")
    (st,) = hooks_env.status()
    assert st.file_present and st.checksum_ok
    assert st.hook_id == st.id == s.id


def test_install_is_idempotent_by_hook_id(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    s = _config_spec(tmp_path, cfg)
    hooks_env.install(s)
    hooks_env.install(s)

    assert len(_manifest(hooks_env)) == 1
    assert json.loads(cfg.read_text())["hooks"]["PreToolUse"] == [OUR_ENTRY]


def test_install_appends_to_hooks_already_registered(hooks_env, tmp_path):
    """Installing must not replace the list a user's own hook lives in."""
    cfg = tmp_path / "settings.json"
    cfg.write_text(json.dumps({
        "model": "opus",
        "hooks": {"PreToolUse": [USER_ENTRY], "Stop": [USER_ENTRY]},
    }))
    hooks_env.install(_config_spec(tmp_path, cfg))

    data = json.loads(cfg.read_text())
    assert data["hooks"]["PreToolUse"] == [USER_ENTRY, OUR_ENTRY]
    assert data["hooks"]["Stop"] == [USER_ENTRY]
    assert data["model"] == "opus"


def test_install_adds_nothing_but_its_value_to_the_config(hooks_env, tmp_path):
    """A runtime may reject keys it does not know, so no marker is written."""
    cfg = tmp_path / "settings.json"
    hooks_env.install(_config_spec(tmp_path, cfg))

    assert json.loads(cfg.read_text()) == {"hooks": {"PreToolUse": [OUR_ENTRY]}}


def test_install_backs_up_target_config(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    original = json.dumps({"hooks": {"PreToolUse": [USER_ENTRY]}})
    cfg.write_text(original)
    hooks_env.install(_config_spec(tmp_path, cfg))

    (entry,) = _manifest(hooks_env)
    assert Path(entry["backup_path"]).read_text() == original


def test_install_refuses_a_config_it_cannot_parse(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    cfg.write_text("{ not json")
    s = _config_spec(tmp_path, cfg)

    with pytest.raises(RuntimeError):
        hooks_env.install(s)

    assert cfg.read_text() == "{ not json"
    assert not Path(s.install_path).exists()
    assert hooks_env.status() == []


def test_install_refuses_a_non_object_parent(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    original = json.dumps({"hooks": "disabled"})
    cfg.write_text(original)

    with pytest.raises(RuntimeError):
        hooks_env.install(_config_spec(tmp_path, cfg))

    assert cfg.read_text() == original


@pytest.mark.skipif(os.name == "nt", reason="POSIX file modes")
def test_install_keeps_the_config_file_mode(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    cfg.write_text("{}")
    cfg.chmod(0o644)
    hooks_env.install(_config_spec(tmp_path, cfg))

    assert cfg.stat().st_mode & 0o777 == 0o644


# ── uninstall ────────────────────────────────────────────────────────────

def test_uninstall_removes_file_and_manifest_entry(hooks_env, tmp_path):
    s = _spec(tmp_path)
    hooks_env.install(s)
    hooks_env.uninstall(s.id)

    assert not Path(s.install_path).exists()
    assert hooks_env.status() == []


def test_uninstall_of_unknown_hook_is_a_no_op(hooks_env, tmp_path):
    hooks_env.uninstall("never-installed")
    assert hooks_env.status() == []


def test_install_uninstall_leaves_config_byte_identical(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    original = b'{"hooks":{"PreToolUse":[{"matcher":"Bash"}]},\n\t"x": 1}'
    cfg.write_bytes(original)
    s = _config_spec(tmp_path, cfg)
    hooks_env.install(s)
    assert cfg.read_bytes() != original
    hooks_env.uninstall(s.id)

    assert cfg.read_bytes() == original


def test_uninstall_deletes_a_config_that_install_created(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    s = _config_spec(tmp_path, cfg)
    hooks_env.install(s)
    hooks_env.uninstall(s.id)

    assert not cfg.exists()


def test_uninstall_keeps_edits_made_after_install(hooks_env, tmp_path):
    """The most important safety property: uninstall must never roll the
    config back over changes the user made since install."""
    cfg = tmp_path / "settings.json"
    cfg.write_text(json.dumps({"hooks": {"PreToolUse": [USER_ENTRY]}}))
    s = _config_spec(tmp_path, cfg)
    hooks_env.install(s)

    data = json.loads(cfg.read_text())
    later = {"matcher": "Edit", "hooks": [{"type": "command", "command": "later"}]}
    data["hooks"]["PreToolUse"].append(later)
    data["hooks"]["Stop"] = [USER_ENTRY]
    data["model"] = "sonnet"
    cfg.write_text(json.dumps(data))

    hooks_env.uninstall(s.id)

    assert json.loads(cfg.read_text()) == {
        "hooks": {"PreToolUse": [USER_ENTRY, later], "Stop": [USER_ENTRY]},
        "model": "sonnet",
    }


def test_uninstall_prunes_only_the_keys_install_created(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    s = _config_spec(tmp_path, cfg)
    hooks_env.install(s)
    data = json.loads(cfg.read_text())
    data["model"] = "sonnet"
    cfg.write_text(json.dumps(data))

    hooks_env.uninstall(s.id)

    assert json.loads(cfg.read_text()) == {"model": "sonnet"}


def test_uninstall_leaves_an_identical_hook_the_user_already_had(
        hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    cfg.write_text(json.dumps({"hooks": {"PreToolUse": [OUR_ENTRY]}}))
    s = _config_spec(tmp_path, cfg)
    hooks_env.install(s)
    data = json.loads(cfg.read_text())
    assert data["hooks"]["PreToolUse"] == [OUR_ENTRY]
    data["model"] = "sonnet"
    cfg.write_text(json.dumps(data))

    hooks_env.uninstall(s.id)

    assert json.loads(cfg.read_text())["hooks"]["PreToolUse"] == [OUR_ENTRY]


def test_uninstall_survives_user_replacing_our_scalar(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    cfg.write_text(json.dumps({"statusLine": "theirs"}))
    s = _config_spec(tmp_path, cfg, target_config_key="statusLine",
                     target_config_value="ours")
    hooks_env.install(s)
    assert json.loads(cfg.read_text())["statusLine"] == "ours"
    cfg.write_text(json.dumps({"statusLine": "newer"}))

    hooks_env.uninstall(s.id)

    assert json.loads(cfg.read_text()) == {"statusLine": "newer"}


def test_uninstall_restores_a_scalar_it_replaced(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    cfg.write_text(json.dumps({"statusLine": "theirs"}))
    s = _config_spec(tmp_path, cfg, target_config_key="statusLine",
                     target_config_value="ours")
    hooks_env.install(s)
    cfg.write_text(json.dumps({"statusLine": "ours", "model": "sonnet"}))

    hooks_env.uninstall(s.id)

    assert json.loads(cfg.read_text()) == {"statusLine": "theirs", "model": "sonnet"}


def test_uninstall_leaves_an_unparsable_config_alone(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    s = _config_spec(tmp_path, cfg)
    hooks_env.install(s)
    cfg.write_text("{ broken by hand")

    hooks_env.uninstall(s.id)

    assert cfg.read_text() == "{ broken by hand"
    assert not Path(s.install_path).exists()
    assert hooks_env.status() == []


def test_uninstall_all_drains_manifest_and_restores_shared_config(
        hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    original = json.dumps({"hooks": {"PreToolUse": [USER_ENTRY]}})
    cfg.write_text(original)
    other = {"matcher": "*", "hooks": [{"type": "command", "command": "ours-2"}]}
    s1 = _config_spec(tmp_path, cfg, id="a",
                      install_path=str(tmp_path / "runtime" / "a.js"))
    s2 = _config_spec(tmp_path, cfg, id="b", target_config_value=[other],
                      install_path=str(tmp_path / "runtime" / "b.js"))
    hooks_env.install(s1)
    hooks_env.install(s2)
    assert json.loads(cfg.read_text())["hooks"]["PreToolUse"] == [
        USER_ENTRY, OUR_ENTRY, other]

    assert sorted(hooks_env.uninstall_all()) == ["a", "b"]

    assert cfg.read_text() == original
    assert hooks_env.status() == []
    assert not Path(s1.install_path).exists()
    assert not Path(s2.install_path).exists()


def test_uninstalling_the_older_of_two_hooks_keeps_the_newer(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    other = {"matcher": "*", "hooks": [{"type": "command", "command": "ours-2"}]}
    s1 = _config_spec(tmp_path, cfg, id="a",
                      install_path=str(tmp_path / "runtime" / "a.js"))
    s2 = _config_spec(tmp_path, cfg, id="b", target_config_value=[other],
                      install_path=str(tmp_path / "runtime" / "b.js"))
    hooks_env.install(s1)
    hooks_env.install(s2)

    hooks_env.uninstall("a")

    assert json.loads(cfg.read_text()) == {"hooks": {"PreToolUse": [other]}}
    # "b" inherits the keys "a" created, so nothing empty is left behind.
    hooks_env.uninstall("b")
    assert json.loads(cfg.read_text()) == {}


def test_entry_without_a_recorded_change_falls_back_to_the_backup(
        hooks_env, tmp_path):
    """Manifest entries written before changes were recorded."""
    cfg = tmp_path / "settings.json"
    cfg.write_text('{"a": 1}')
    s = _config_spec(tmp_path, cfg)
    hooks_env.install(s)
    manifest = json.loads(hooks_env._MANIFEST_PATH.read_text())
    for key in ("config_change", "config_existed", "config_checksum"):
        manifest["hooks"][0].pop(key)
    hooks_env._MANIFEST_PATH.write_text(json.dumps(manifest))

    hooks_env.uninstall(s.id)

    assert cfg.read_text() == '{"a": 1}'


# ── status / verify ──────────────────────────────────────────────────────

def test_verify_all_reports_missing_file(hooks_env, tmp_path):
    s = _spec(tmp_path)
    hooks_env.install(s)
    Path(s.install_path).unlink()

    (v,) = hooks_env.verify_all()
    assert not v.ok
    assert "missing" in v.issues[0]


def test_verify_all_reports_checksum_drift(hooks_env, tmp_path):
    s = _spec(tmp_path)
    hooks_env.install(s)
    Path(s.install_path).write_text("tampered")

    (v,) = hooks_env.verify_all()
    assert not v.ok
    assert "modified" in v.issues[0]


def test_verify_all_reports_a_config_entry_removed_by_hand(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    cfg.write_text(json.dumps({"hooks": {"PreToolUse": [USER_ENTRY]}}))
    s = _config_spec(tmp_path, cfg)
    hooks_env.install(s)
    (st,) = hooks_env.status()
    assert st.config_present
    assert hooks_env.verify_all()[0].ok

    cfg.write_text(json.dumps({"hooks": {"PreToolUse": [USER_ENTRY]}}))

    (st,) = hooks_env.status()
    assert not st.config_present
    (v,) = hooks_env.verify_all()
    assert not v.ok
    assert any("runtime config" in i for i in v.issues)


def test_hook_without_a_config_is_not_flagged_for_one(hooks_env, tmp_path):
    hooks_env.install(_spec(tmp_path))

    (v,) = hooks_env.verify_all()
    assert v.ok


def test_manifest_survives_corrupt_read(hooks_env, tmp_path):
    hooks_env._MANIFEST_DIR.mkdir(parents=True)
    hooks_env._MANIFEST_PATH.write_text("{ not json")

    assert hooks_env.status() == []
    hooks_env.install(_spec(tmp_path))
    assert len(hooks_env.status()) == 1
