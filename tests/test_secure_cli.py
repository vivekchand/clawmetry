"""Tests for `clawmetry secure` (clawmetry/secure.py) — the numbat installer
CLI. Pure-helper coverage only: asset-name mapping across OS/arch, checksum
parsing/verification, and the exact hook-install invocation (monitor-only,
never --enforce, never `numbat collect`). Network/subprocess paths are
covered by the release E2E, not unit tests.
"""

from __future__ import annotations

import hashlib

import pytest

from clawmetry import secure


# ── release_asset_name ─────────────────────────────────────────────────────

@pytest.mark.parametrize("system,machine,expected", [
    ("Darwin", "arm64", "numbat_0.1.2_darwin_arm64.tar.gz"),
    ("Darwin", "x86_64", "numbat_0.1.2_darwin_amd64.tar.gz"),
    ("Linux", "aarch64", "numbat_0.1.2_linux_arm64.tar.gz"),
    ("Linux", "amd64", "numbat_0.1.2_linux_amd64.tar.gz"),
    ("Windows", "AMD64", "numbat_0.1.2_windows_amd64.zip"),
    ("Windows", "ARM64", "numbat_0.1.2_windows_arm64.zip"),
])
def test_asset_name_matches_real_release_assets(system, machine, expected):
    # Names pinned against the actual v0.1.2 release asset list.
    assert secure.release_asset_name("v0.1.2", system, machine) == expected


def test_asset_name_strips_v_prefix_and_rejects_unknown():
    assert "0.1.2" in secure.release_asset_name("v0.1.2", "Linux", "x86_64")
    with pytest.raises(RuntimeError):
        secure.release_asset_name("v0.1.2", "SunOS", "x86_64")
    with pytest.raises(RuntimeError):
        secure.release_asset_name("v0.1.2", "Linux", "riscv64")


# ── checksums ──────────────────────────────────────────────────────────────

def test_parse_checksums_handles_real_format():
    sha_a = "a" * 64
    sha_b = "B" * 64  # upper-case hex must normalize
    text = (
        f"{sha_a}  numbat_0.1.2_darwin_arm64.tar.gz\n"
        f"{sha_b} *numbat_0.1.2_windows_amd64.zip\n"
        "not a checksum line\n"
        "deadbeef  short-hash-skipped\n"
    )
    sums = secure.parse_checksums(text)
    assert sums["numbat_0.1.2_darwin_arm64.tar.gz"] == sha_a
    assert sums["numbat_0.1.2_windows_amd64.zip"] == "b" * 64
    assert len(sums) == 2


def test_sha256_file_roundtrip(tmp_path):
    p = tmp_path / "blob"
    p.write_bytes(b"clawmetry+numbat")
    assert secure.sha256_file(p) == hashlib.sha256(b"clawmetry+numbat").hexdigest()


# ── hook install command ───────────────────────────────────────────────────

def test_hook_install_cmd_is_monitor_only_with_both_sinks():
    cmd = secure.build_hook_install_cmd("/x/numbat", 8900, "findings")
    assert cmd[:3] == ["/x/numbat", "hook", "install"]
    assert "--enforce" not in cmd            # monitor-only, always
    assert "collect" not in cmd              # never wire the OTLP receiver
    assert cmd.count("--output") == 2        # file (durable) + http (live)
    assert "file" in cmd and "http" in cmd
    assert "http://127.0.0.1:8900/api/numbat/ingest" in cmd
    i = cmd.index("--emit")
    assert cmd[i + 1] == "findings"


def test_hook_install_cmd_custom_port_and_emit_all():
    cmd = secure.build_hook_install_cmd("numbat", 9001, "all")
    assert "http://127.0.0.1:9001/api/numbat/ingest" in cmd
    assert cmd[cmd.index("--emit") + 1] == "all"


# ── hook uninstall / clawmetry-uninstall drain ─────────────────────────────

def test_hook_uninstall_cmd_mirrors_install_scope():
    cmd = secure.build_hook_uninstall_cmd("/x/numbat")
    assert cmd == ["/x/numbat", "hook", "uninstall", "--agent", "all"]


def test_managed_numbat_only_matches_our_install(monkeypatch, tmp_path):
    monkeypatch.setattr(secure, "BIN_DIR", tmp_path)
    # PATH-installed numbat must NOT count as managed.
    monkeypatch.setattr(secure.shutil, "which", lambda _n: "/usr/local/bin/numbat")
    assert secure.managed_numbat() is None
    binary = secure.numbat_binary_path()
    binary.write_bytes(b"#!fake")
    assert secure.managed_numbat() == str(binary)


def test_drain_noops_without_managed_binary(monkeypatch, tmp_path):
    monkeypatch.setattr(secure, "BIN_DIR", tmp_path)
    monkeypatch.setattr(secure.shutil, "which", lambda _n: "/usr/local/bin/numbat")

    def _boom(*a, **k):  # pragma: no cover - must never be reached
        raise AssertionError("drain must not touch a user-installed numbat")

    monkeypatch.setattr(secure.subprocess, "run", _boom)
    assert secure.drain_hooks_for_uninstall() == (False, "")


def test_drain_runs_hook_uninstall_on_managed_binary(monkeypatch, tmp_path):
    monkeypatch.setattr(secure, "BIN_DIR", tmp_path)
    binary = secure.numbat_binary_path()
    binary.write_bytes(b"#!fake")
    calls = []

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(secure.subprocess, "run",
                        lambda cmd, **k: calls.append(cmd) or _Proc())
    acted, msg = secure.drain_hooks_for_uninstall()
    assert acted is True and "removed" in msg
    assert calls == [[str(binary), "hook", "uninstall", "--agent", "all"]]


def test_drain_failure_reports_manual_command_and_never_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(secure, "BIN_DIR", tmp_path)
    secure.numbat_binary_path().write_bytes(b"#!fake")

    class _Proc:
        returncode = 3
        stdout = ""
        stderr = "config locked\n"

    monkeypatch.setattr(secure.subprocess, "run", lambda *a, **k: _Proc())
    acted, msg = secure.drain_hooks_for_uninstall()
    assert acted is False
    assert "config locked" in msg and "hook uninstall --agent all" in msg

    def _raise(*a, **k):
        raise OSError("exec format error")

    monkeypatch.setattr(secure.subprocess, "run", _raise)
    acted, msg = secure.drain_hooks_for_uninstall()
    assert acted is False and "exec format error" in msg
