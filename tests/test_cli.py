from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

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


def test_pod_name_xml_escaping():
    from xml.sax.saxutils import escape

    malicious_pod = "test-pod&injection</string><string>attacker"
    pod_xml = escape(malicious_pod)
    docker_path = "/usr/bin/docker"
    cluster = "openshell-cluster"
    sync_script = "/usr/local/lib/python3.11/dist-packages/clawmetry/sync.py"
    label = f"com.clawmetry.sandbox.{escape(malicious_pod)}"

    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>             <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{docker_path}</string>
        <string>exec</string>
        <string>{cluster}</string>
        <string>kubectl</string>
        <string>exec</string>
        <string>-n</string>
        <string>openshell</string>
        <string>{pod_xml}</string>
        <string>--</string>
        <string>python3</string>
        <string>{sync_script}</string>
    </array>
    <key>RunAtLoad</key>         <true/>
    <key>KeepAlive</key>         <true/>
    <key>ThrottleInterval</key>  <integer>30</integer>
    <key>StandardOutPath</key>   <string>/tmp/clawmetry-{pod_xml}.log</string>
    <key>StandardErrorPath</key>  <string>/tmp/clawmetry-{pod_xml}.log</string>
</dict>
</plist>"""

    ET.fromstring(plist)
