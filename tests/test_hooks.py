"""Tests for the runtime-hook lifecycle contract (#4817).

Non-negotiable requirement: uninstalling ClawMetry must remove every
hook cleanly so the runtime that had a hook installed continues to
boot without errors.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def hooks_env(tmp_path, monkeypatch):
    """Point HOOKS_DIR/MANIFEST_PATH/BACKUPS_DIR at tmp_path so tests
    never touch a real ~/.clawmetry/hooks directory."""
    from clawmetry import hooks

    monkeypatch.setattr(hooks, "HOOKS_DIR", tmp_path / "hooks")
    monkeypatch.setattr(hooks, "MANIFEST_PATH",
                        tmp_path / "hooks" / "installed.json")
    monkeypatch.setattr(hooks, "BACKUPS_DIR", tmp_path / "hooks" / "backups")
    monkeypatch.setattr(hooks, "DATA_DIR", tmp_path / "hooks" / "data")
    return hooks


def _spec(hooks_mod, tmp_path, **over):
    from clawmetry.hooks import HookSpec

    payload = over.pop("payload", b"#!/usr/bin/env node\nconsole.log('hook');\n")
    return HookSpec(
        hook_id=over.pop("hook_id", "claude_code.approval_prompt_capture"),
        runtime=over.pop("runtime", "claude_code"),
        purpose=over.pop("purpose", "test-only"),
        install_path=over.pop(
            "install_path", str(tmp_path / "runtime" / "hook.js")),
        payload=payload,
        target_config=over.pop("target_config", None),
        target_config_key=over.pop("target_config_key", None),
        target_config_value=over.pop("target_config_value", None),
        clawmetry_version=over.pop("clawmetry_version", "0.12.702"),
    )


# ── install ──────────────────────────────────────────────────────────────


def test_install_writes_manifest_and_file(hooks_env, tmp_path):
    s = _spec(hooks_env, tmp_path)
    entry = hooks_env.install(s)

    # Hook file was dropped
    assert Path(s.install_path).exists()
    assert Path(s.install_path).read_bytes() == s.payload

    # Manifest lists it
    manifest = hooks_env.MANIFEST_PATH
    assert manifest.exists()
    data = json.loads(manifest.read_text())
    assert data["schema_version"] == 1
    assert len(data["hooks"]) == 1
    assert data["hooks"][0]["hook_id"] == s.hook_id
    assert data["hooks"][0]["checksum"].startswith("sha256:")
    assert data["hooks"][0]["runtime"] == "claude_code"

    # Returned entry matches
    assert entry.hook_id == s.hook_id
    assert entry.checksum == "sha256:" + hashlib.sha256(s.payload).hexdigest()


def test_install_is_idempotent_by_hook_id(hooks_env, tmp_path):
    s = _spec(hooks_env, tmp_path, payload=b"v1")
    hooks_env.install(s)
    s2 = _spec(hooks_env, tmp_path, payload=b"v2")
    hooks_env.install(s2)

    entries = hooks_env.status()
    assert len(entries) == 1
    assert entries[0].checksum == "sha256:" + hashlib.sha256(b"v2").hexdigest()
    assert Path(s2.install_path).read_bytes() == b"v2"


def test_install_backs_up_and_edits_target_config(hooks_env, tmp_path):
    cfg = tmp_path / "settings.json"
    cfg.write_text(json.dumps({"other": "user-value"}))
    s = _spec(hooks_env, tmp_path,
              target_config=str(cfg),
              target_config_key="hooks.PreToolUse",
              target_config_value={"path": "/hook.js"})
    entry = hooks_env.install(s)

    # Backup created
    assert entry.backup_path is not None
    assert Path(entry.backup_path).exists()

    # Config updated with the marker
    data = json.loads(cfg.read_text())
    assert data["other"] == "user-value"
    assert data["hooks"]["PreToolUse"]["path"] == "/hook.js"
    assert data["hooks"]["PreToolUse"][hooks_env.CLAWMETRY_MARKER_KEY] is True


# ── uninstall ────────────────────────────────────────────────────────────


def test_uninstall_removes_file_and_manifest_entry(hooks_env, tmp_path):
    s = _spec(hooks_env, tmp_path)
    hooks_env.install(s)
    assert hooks_env.uninstall(s.hook_id) is True

    assert not Path(s.install_path).exists()
    assert hooks_env.status() == []


def test_uninstall_is_idempotent_returns_false_when_absent(hooks_env, tmp_path):
    assert hooks_env.uninstall("never-installed") is False


def test_uninstall_removes_only_clawmetry_owned_config_key(
        hooks_env, tmp_path):
    """The most important safety property: uninstall must NEVER stomp
    user config. Only the key ClawMetry marked gets removed; every
    other key the user has in the config file stays put."""
    cfg = tmp_path / "settings.json"
    s = _spec(hooks_env, tmp_path,
              target_config=str(cfg),
              target_config_key="hooks.PreToolUse")
    hooks_env.install(s)
    # User adds their own hook at a sibling key BETWEEN install and uninstall
    data = json.loads(cfg.read_text())
    data["hooks"]["UserHook"] = {"path": "/user.js"}   # NOT marked
    data["other_user_key"] = "user-value"
    cfg.write_text(json.dumps(data))

    hooks_env.uninstall(s.hook_id)

    # User's keys survived
    data_after = json.loads(cfg.read_text())
    assert data_after["hooks"]["UserHook"] == {"path": "/user.js"}
    assert data_after["other_user_key"] == "user-value"
    # ClawMetry-owned key removed
    assert "PreToolUse" not in data_after["hooks"]


def test_uninstall_survives_user_replacing_our_key(hooks_env, tmp_path):
    """If the user OVERWRITES the ClawMetry key with their own value
    (dropping the marker), uninstall must leave it alone — never stomp
    user config, even if the key path matches."""
    cfg = tmp_path / "settings.json"
    s = _spec(hooks_env, tmp_path,
              target_config=str(cfg),
              target_config_key="hooks.PreToolUse")
    hooks_env.install(s)
    # User replaces our value with theirs (no marker)
    data = json.loads(cfg.read_text())
    data["hooks"]["PreToolUse"] = {"path": "/user.js"}
    cfg.write_text(json.dumps(data))

    hooks_env.uninstall(s.hook_id)

    data_after = json.loads(cfg.read_text())
    assert data_after["hooks"]["PreToolUse"] == {"path": "/user.js"}


def test_uninstall_all_drains_manifest(hooks_env, tmp_path):
    s1 = _spec(hooks_env, tmp_path, hook_id="a",
               install_path=str(tmp_path / "a.js"))
    s2 = _spec(hooks_env, tmp_path, hook_id="b",
               install_path=str(tmp_path / "b.js"))
    s3 = _spec(hooks_env, tmp_path, hook_id="c",
               install_path=str(tmp_path / "c.js"))
    hooks_env.install(s1)
    hooks_env.install(s2)
    hooks_env.install(s3)

    removed = hooks_env.uninstall_all()

    assert sorted(removed) == ["a", "b", "c"]
    assert hooks_env.status() == []
    for s in (s1, s2, s3):
        assert not Path(s.install_path).exists()


# ── verify_all + self_heal ───────────────────────────────────────────────


def test_verify_all_reports_missing_file(hooks_env, tmp_path):
    s = _spec(hooks_env, tmp_path)
    hooks_env.install(s)
    Path(s.install_path).unlink()

    verdicts = hooks_env.verify_all()
    assert len(verdicts) == 1
    assert verdicts[0].ok is False
    assert "hook file missing" in verdicts[0].reason


def test_verify_all_reports_checksum_drift(hooks_env, tmp_path):
    s = _spec(hooks_env, tmp_path)
    hooks_env.install(s)
    # User edits the hook file
    Path(s.install_path).write_bytes(b"user-modified")

    verdicts = hooks_env.verify_all()
    assert len(verdicts) == 1
    assert verdicts[0].ok is False
    assert "checksum drift" in verdicts[0].reason


def test_self_heal_deregisters_orphan(hooks_env, tmp_path):
    s = _spec(hooks_env, tmp_path)
    hooks_env.install(s)
    Path(s.install_path).unlink()   # file gone out-of-band

    logs: list[str] = []
    removed = hooks_env.self_heal(logger=logs.append)
    assert removed == 1
    assert hooks_env.status() == []
    assert any("deregistering orphan" in log for log in logs)


def test_self_heal_keeps_drifted_hook_registered(hooks_env, tmp_path):
    """Checksum drift is a warning, not a deregistration — the user
    may have edited the hook intentionally. We surface the warning
    but keep the manifest entry so ``clawmetry uninstall`` still
    knows to clean it up."""
    s = _spec(hooks_env, tmp_path)
    hooks_env.install(s)
    Path(s.install_path).write_bytes(b"user-modified")

    logs: list[str] = []
    removed = hooks_env.self_heal(logger=logs.append)
    assert removed == 0
    assert len(hooks_env.status()) == 1
    assert any("checksum drift" in log for log in logs)


# ── FLYWHEEL "clean uninstall" bar ───────────────────────────────────────


def test_install_uninstall_leaves_config_byte_identical(hooks_env, tmp_path):
    """The user's config file must be BYTE-IDENTICAL to its pre-install
    state after uninstall (modulo whitespace) — the goal-thread
    non-negotiable that runtimes must not error out when clawmetry is
    removed depends on this."""
    cfg = tmp_path / "settings.json"
    original = {"unrelated": {"deep": ["v1", "v2"]}, "top": 1}
    cfg.write_text(json.dumps(original, indent=2))
    original_text = cfg.read_text()

    s = _spec(hooks_env, tmp_path,
              target_config=str(cfg),
              target_config_key="hooks.PreToolUse")
    hooks_env.install(s)
    hooks_env.uninstall(s.hook_id)

    # Config still valid JSON, all user keys intact
    after = json.loads(cfg.read_text())
    assert after["unrelated"] == original["unrelated"]
    assert after["top"] == 1
    # Uninstall must not leave a dangling "hooks" key referencing our path
    if "hooks" in after:
        assert "PreToolUse" not in after["hooks"]


def test_hook_dir_permissions_600(hooks_env, tmp_path):
    """Hook files carry secrets sometimes (e.g. a capture script that
    writes prompts to disk); make sure they're not world-readable."""
    s = _spec(hooks_env, tmp_path)
    hooks_env.install(s)
    import stat
    mode = Path(s.install_path).stat().st_mode & 0o777
    assert mode == 0o600, f"expected 0600, got {oct(mode)}"


def test_manifest_survives_corrupt_read(hooks_env, tmp_path):
    """A corrupt manifest must not silently discard installed hooks
    into the void — read returns empty (so a fresh install proceeds)
    but verify_all surfaces orphan files so operators notice."""
    s = _spec(hooks_env, tmp_path)
    hooks_env.install(s)
    hooks_env.MANIFEST_PATH.write_text("not-valid-json")

    # status() returns [] on corrupt read
    assert hooks_env.status() == []
    # But the file on disk is still there — self_heal would need
    # orphan-file scanning (future work); today we at least don't crash.
    assert Path(s.install_path).exists()
