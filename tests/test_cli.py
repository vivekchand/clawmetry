from pathlib import Path

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


def test_print_nemoclaw_preset_hint_emits_command(monkeypatch, capsys):
    helper = "/tmp/add-nemoclaw-clawmetry-preset.sh"
    monkeypatch.setattr(cli, "_get_nemoclaw_preset_script", lambda: helper)

    cli._print_nemoclaw_preset_hint(lambda text: text, lambda text: text, lambda text: text)

    out = capsys.readouterr().out
    assert "NemoClaw detected" in out
    assert "allow your NemoClaw sandboxes to reach ClawMetry Cloud" in out
    assert helper in out
