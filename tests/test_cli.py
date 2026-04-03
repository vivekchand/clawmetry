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

    cli._print_nemoclaw_preset_hint(
        lambda text: text, lambda text: text, lambda text: text
    )

    out = capsys.readouterr().out
    assert "NemoClaw detected" in out
    assert "allow your NemoClaw sandboxes to reach ClawMetry Cloud" in out
    assert helper in out


def test_verify_key_ownership_does_not_disclose_email(monkeypatch, capsys):
    """Masked email must not be displayed to prevent information disclosure."""
    import io

    fake_tty = io.StringIO()
    fake_tty.write("123456\n")
    fake_tty.seek(0)

    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    monkeypatch.setattr(
        "builtins.open",
        lambda path, mode: fake_tty if path == "/dev/tty" else open(path, mode),
    )
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout=None: io.BytesIO(b'{"masked_email": "j***@gmail.com"}'),
    )

    cli._verify_key_ownership("test_key")

    out = capsys.readouterr().out
    assert "j***@gmail.com" not in out, "masked email must not appear in output"
