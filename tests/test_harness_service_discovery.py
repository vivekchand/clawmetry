"""Background services must find the same native Claude install as a terminal."""
import json
from types import SimpleNamespace

import pytest

from clawmetry import harness
from routes import advisor
from clawmetry import assistant_service as assistant


@pytest.fixture
def service(monkeypatch, tmp_path):
    for key in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("PATH", str(tmp_path / "empty-path"))
    original_expanduser = harness.os.path.expanduser
    monkeypatch.setattr(harness.os.path, "expanduser", lambda path: str(tmp_path / path[2:])
                        if path.startswith("~/") else original_expanduser(path))
    monkeypatch.setattr(advisor, "_read_anthropic_key_from_openclaw_config", lambda: None)
    binary = tmp_path / ".local" / "bin" / "claude"
    binary.parent.mkdir(parents=True)
    return tmp_path, binary


def test_native_harness_is_found_authenticated_and_executed_without_shell_path(service, monkeypatch):
    home, binary = service
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o700)
    (home / ".claude.json").write_text(json.dumps({"oauthAccount": {"emailAddress": "test@example.test"}}))
    assert assistant._provider() == ("claude_cli", str(binary))
    seen = {}
    def run(argv, **kwargs):
        seen.update(argv=argv, **kwargs)
        return SimpleNamespace(returncode=0, stdout='{"result":"verified"}')
    monkeypatch.setattr(assistant.subprocess, "run", run)
    assert assistant._generate("claude_cli", "/untrusted", "system", "question") == "verified"
    assert seen["argv"][0] == str(binary)
    assert seen["input"] == "question"
    assert "--safe-mode" in seen["argv"]
    assert not seen.get("shell")


def test_native_binary_without_login_does_not_enable_automatic_provider(service):
    _, binary = service
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o700)
    assert advisor._load_anthropic_auth() == (None, None)


def test_dives_executes_the_discovered_harness_path(monkeypatch):
    from routes import dives
    import clawmetry.dives_prompt as prompts
    seen = {}
    monkeypatch.setattr(advisor, "_load_anthropic_auth", lambda: ("claude_cli", "/native/claude"))
    monkeypatch.setattr(prompts, "build_dives_prompt", lambda *args, **kwargs: {"user": "question", "system": "system"})
    def call(binary, prompt, **kwargs):
        seen["binary"] = binary
        spec = {"sql": "SELECT COUNT(*) AS total FROM sessions", "chart_type": "number",
                "x": "total", "y": "total", "title": "Sessions", "description": "Recorded sessions"}
        return {"content": [{"type": "text", "text": json.dumps(spec)}]}
    monkeypatch.setattr(advisor, "_call_via_claude_cli", call)
    assert dives._call_llm_for_sql("question", object())["title"] == "Sessions"
    assert seen["binary"] == "/native/claude"


@pytest.mark.parametrize("kind", ["missing", "not_executable", "directory", "broken_link"])
def test_unusable_native_install_is_unavailable(service, kind):
    _, binary = service
    if kind == "not_executable":
        binary.write_text("not executable")
        binary.chmod(0o600)
    elif kind == "directory":
        binary.mkdir()
    elif kind == "broken_link":
        binary.symlink_to(binary.parent / "missing")
    assert harness.find_claude_cli() is None


def test_explicit_path_keeps_precedence(service, monkeypatch):
    monkeypatch.setattr(harness.shutil, "which", lambda name: "/custom/claude")
    assert harness.find_claude_cli() == "/custom/claude"


def test_native_windows_executable_name(monkeypatch):
    monkeypatch.setattr(harness.shutil, "which", lambda name: None)
    # A module-local OS facade models Windows without changing pathlib's OS.
    path = SimpleNamespace(join=lambda *parts: "/".join(parts), expanduser=lambda path: path,
                           isfile=lambda path: path == "~/.local/bin/claude.exe")
    monkeypatch.setattr(harness, "os", SimpleNamespace(name="nt", path=path, X_OK=1,
                                                     access=lambda path, mode: True))
    assert harness.find_claude_cli() == "~/.local/bin/claude.exe"
