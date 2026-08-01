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
