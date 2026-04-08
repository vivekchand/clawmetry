import os
from pathlib import Path
from unittest.mock import MagicMock

import clawmetry.cli as cli


def test_get_nemoclaw_preset_script_returns_none_without_nemoclaw(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert cli._get_nemoclaw_preset_script() is None


def test_get_nemoclaw_preset_script_returns_local_helper(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    package_dir = repo_root / "clawmetry"
    package_dir.mkdir(parents=True)
    resources_dir = package_dir / "resources"
    resources_dir.mkdir()

    fake_cli = package_dir / "cli.py"
    fake_cli.write_text("# test\n")
    helper = resources_dir / "add-nemoclaw-clawmetry-preset.sh"
    helper.write_text("#!/usr/bin/env bash\n")

    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/nemoclaw")
    monkeypatch.setattr(cli, "__file__", str(fake_cli))

    assert cli._get_nemoclaw_preset_script() == str(helper)


def test_enc_key_masked_in_key_only_output(monkeypatch, capsys):
    import clawmetry.sync as sync_module

    test_key = "abcd1234efgh5678"
    masked_key = test_key[:6] + "…" + test_key[-4:]
    monkeypatch.setattr(cli, "_stop_existing_daemon", lambda: None)
    monkeypatch.setattr(
        sync_module, "validate_key", lambda *a, **kw: {"node_id": "test-node"}
    )
    monkeypatch.setattr(sync_module, "save_config", lambda *a, **kw: None)
    monkeypatch.setattr(cli, "_get_api_key_interactive", lambda: "cm_test12345")
    monkeypatch.setattr(cli, "_verify_key_ownership", lambda *a, **kw: None)
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr("socket.gethostname", lambda: "test-host")
    monkeypatch.setattr(os.path, "exists", lambda p: False)

    class FakeArgs:
        key = "cm_test12345"
        enc_key = test_key
        key_only = True
        no_daemon = True
        custom_node_id = None
        foreground = False

    cli._cmd_connect(FakeArgs())

    out = capsys.readouterr().out
    assert test_key not in out, "enc_key should not appear unmasked in output"
    assert masked_key in out, f"enc_key should be masked like api_key, got: {out}"


def test_print_nemoclaw_preset_hint_emits_command(monkeypatch, capsys):
    helper = "/tmp/add-nemoclaw-clawmetry-preset.sh"
    monkeypatch.setattr(cli, "_get_nemoclaw_preset_script", lambda: helper)

    cli._print_nemoclaw_preset_hint(
        lambda text: text, lambda text: text, lambda text: text
    )

    out = capsys.readouterr().out
    assert "NemoClaw detected" in out
    assert "allow your NemoClaw sandboxes to reach ClawMetry Cloud" in out
    assert helper in out
