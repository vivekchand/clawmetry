"""clawmetry secure — one-command numbat (Perplexity agent-EDR) setup.

``clawmetry secure enable`` downloads the numbat binary (checksum-verified
from its GitHub release), installs its agent hooks in monitor-only mode with
ClawMetry as the sink, and leaves the durable file sink on so the sync
daemon's tail (sync_numbat_events) ingests findings even when the dashboard
is down. ``status`` shows per-agent hook wiring plus ingested-finding counts;
``disable`` uninstalls the hooks.

Design constraints honored:
- stdlib only (urllib, tarfile/zipfile, hashlib) — no new dependencies.
- Loud consent before touching agent configs: hook install MODIFIES each
  harness's own settings (Claude settings.json, Codex hooks.json, …), which
  crosses ClawMetry's read-only default. Interactive confirm unless --yes.
- Monitor-only: we never pass --enforce. Blocking stays an explicit operator
  decision made with numbat's own tooling.
- Never wire `numbat collect` — its OTLP receiver contends with ClawMetry's
  own /v1/logs on the :4318 convention (docs/NUMBAT.md).
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

NUMBAT_REPO = "perplexityai/numbat"
_API_LATEST = f"https://api.github.com/repos/{NUMBAT_REPO}/releases/latest"
_UA = {"User-Agent": "clawmetry-secure"}

BIN_DIR = Path(os.path.expanduser("~/.clawmetry/bin"))


# ── release asset resolution (pure; unit-tested) ───────────────────────────

def release_asset_name(version: str, system: str | None = None,
                       machine: str | None = None) -> str:
    """Map (os, arch) onto numbat's release asset naming:
    numbat_<ver>_<os>_<arch>.tar.gz (zip on Windows). Raises on
    unsupported platforms rather than guessing."""
    sysname = (system or platform.system()).lower()
    mach = (machine or platform.machine()).lower()
    if mach in ("arm64", "aarch64"):
        arch = "arm64"
    elif mach in ("x86_64", "amd64"):
        arch = "amd64"
    else:
        raise RuntimeError(f"numbat has no release for architecture {mach!r}")
    if sysname == "darwin":
        osname, ext = "darwin", "tar.gz"
    elif sysname == "linux":
        osname, ext = "linux", "tar.gz"
    elif sysname == "windows":
        osname, ext = "windows", "zip"
    else:
        raise RuntimeError(f"numbat has no release for OS {sysname!r}")
    ver = version.lstrip("v")
    return f"numbat_{ver}_{osname}_{arch}.{ext}"


def parse_checksums(text: str) -> dict:
    """Parse a `sha256  filename` checksums.txt into {filename: sha256}."""
    out = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 64:
            out[parts[1].lstrip("*")] = parts[0].lower()
    return out


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_hook_install_cmd(numbat: str, port: int, emit: str,
                           agents: str = "all") -> list:
    """The exact hook-install invocation (pure; unit-tested). File sink is
    numbat's default and its only durable path; the HTTP sink adds
    low-latency delivery to the dashboard. Loopback needs no numbat auth
    flags. Deliberately no --enforce (monitor-only)."""
    return [
        numbat, "hook", "install",
        "--agent", agents,
        "--emit", emit,
        "--output", "file",
        "--output", "http",
        "--http-url", f"http://127.0.0.1:{port}/api/numbat/ingest",
    ]


# ── binary install ─────────────────────────────────────────────────────────

def numbat_binary_path() -> Path:
    name = "numbat.exe" if platform.system().lower() == "windows" else "numbat"
    return BIN_DIR / name


def find_numbat() -> str | None:
    """Managed install first, then PATH (user may have installed numbat
    themselves — reuse it rather than shadowing)."""
    managed = numbat_binary_path()
    if managed.exists():
        return str(managed)
    return shutil.which("numbat")


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def install_numbat(force: bool = False) -> str:
    """Download the latest numbat release for this platform, verify its
    SHA-256 against the release's checksums.txt, and install the binary to
    ~/.clawmetry/bin. Returns the binary path."""
    existing = find_numbat()
    if existing and not force:
        return existing

    print("→ Resolving latest numbat release…")
    rel = json.loads(_http_get(_API_LATEST).decode("utf-8"))
    version = rel.get("tag_name") or ""
    assets = {a["name"]: a["browser_download_url"] for a in rel.get("assets", [])}
    asset = release_asset_name(version)
    if asset not in assets:
        raise RuntimeError(
            f"release {version} has no asset {asset!r} (found: {sorted(assets)})"
        )
    if "checksums.txt" not in assets:
        raise RuntimeError(f"release {version} ships no checksums.txt")

    sums = parse_checksums(_http_get(assets["checksums.txt"]).decode("utf-8"))
    expected = sums.get(asset)
    if not expected:
        raise RuntimeError(f"checksums.txt has no entry for {asset}")

    print(f"→ Downloading {asset} ({version})…")
    with tempfile.TemporaryDirectory(prefix="clawmetry-numbat-") as td:
        archive = Path(td) / asset
        archive.write_bytes(_http_get(assets[asset]))
        actual = sha256_file(archive)
        if actual != expected:
            raise RuntimeError(
                f"SHA-256 mismatch for {asset}: expected {expected}, got {actual}"
            )
        print("→ Checksum verified.")

        bin_name = "numbat.exe" if asset.endswith(".zip") else "numbat"
        extract_dir = Path(td) / "x"
        extract_dir.mkdir()
        if asset.endswith(".zip"):
            import zipfile
            with zipfile.ZipFile(archive) as z:
                z.extract(bin_name, extract_dir)
        else:
            import tarfile
            with tarfile.open(archive, "r:gz") as t:
                t.extract(bin_name, extract_dir)

        BIN_DIR.mkdir(parents=True, exist_ok=True)
        dest = numbat_binary_path()
        shutil.move(str(extract_dir / bin_name), str(dest))
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"→ Installed numbat to {dest}")
    return str(dest)


# ── subcommands ────────────────────────────────────────────────────────────

def _confirm(prompt: str) -> bool:
    if not sys.stdin.isatty():
        print("Refusing to modify agent configs without a TTY. "
              "Re-run with --yes to confirm non-interactively.")
        return False
    try:
        return input(f"{prompt} [y/N] ").strip().lower() in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def _dashboard_port(args) -> int:
    try:
        return int(getattr(args, "port", None) or 8900)
    except (TypeError, ValueError):
        return 8900


def cmd_enable(args) -> int:
    port = _dashboard_port(args)
    emit = "all" if getattr(args, "emit_all", False) else "findings"
    print("clawmetry secure — numbat (Perplexity agent-EDR) setup")
    print()
    print("This will:")
    print("  1. Install the numbat binary to ~/.clawmetry/bin (SHA-256 verified)")
    print("  2. Install numbat's MONITOR-ONLY hooks into your agent configs")
    print("     (Claude Code settings.json, Codex hooks.json, … — numbat edits")
    print("     each harness's own hook config; undo with `clawmetry secure disable`)")
    print(f"  3. Point findings at this dashboard (port {port}) + the durable")
    print("     file sink ~/.numbat/findings.ndjson (the daemon tails both)")
    print()
    print("Nothing is ever blocked: enforce mode stays off.")
    print()
    if not getattr(args, "yes", False) and not _confirm("Install numbat hooks?"):
        print("Aborted — nothing changed.")
        return 1

    try:
        numbat = install_numbat(force=getattr(args, "reinstall", False))
    except Exception as e:
        print(f"✗ numbat install failed: {e}")
        return 1

    cmd = build_hook_install_cmd(numbat, port, emit)
    print(f"→ {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    sys.stdout.write(proc.stdout or "")
    sys.stderr.write(proc.stderr or "")
    if proc.returncode != 0:
        print(f"✗ numbat hook install exited {proc.returncode}")
        return proc.returncode

    print()
    print("✓ numbat hooks installed (monitor-only).")
    print("  Findings will appear in the Security surface and can drive the")
    print("  opt-in 'numbat security finding' alert rule (Alerts tab).")
    if Path(os.path.expanduser("~/.openclaw")).is_dir():
        print()
        print("  ⚠ OpenClaw note: if your config pins plugins.allow, it is an")
        print("    EXCLUSIVE allowlist — make sure it contains BOTH 'numbat'")
        print("    and ClawMetry's plugin id, then restart the gateway and run")
        print("    `openclaw plugins inspect numbat --runtime --json`.")
    print()
    print("  Next: clawmetry secure status")
    return 0


def cmd_status(args) -> int:
    numbat = find_numbat()
    if not numbat:
        print("numbat: not installed — run `clawmetry secure enable`")
        return 1
    ver = subprocess.run([numbat, "version"], capture_output=True, text=True,
                         timeout=30)
    print(f"numbat: {numbat}")
    print(f"        {(ver.stdout or '').strip()}")
    print()
    proc = subprocess.run([numbat, "agents", "--format", "json"],
                          capture_output=True, text=True, timeout=60)
    rows = []
    try:
        data = json.loads(proc.stdout or "[]")
        rows = data if isinstance(data, list) else data.get("agents", [])
    except Exception:
        pass
    if rows:
        # Real v0.1.2 JSON keys: agent, at_rest, hook, wired (+present/
        # detected/setup_hint). Older guesses kept as fallbacks.
        print(f"{'AGENT':<26} {'ARTIFACTS':<28} {'LIVE':<8} WIRED")
        for a in rows:
            if not isinstance(a, dict):
                continue
            name = str(a.get("agent") or a.get("name") or "?")
            arts = str(a.get("at_rest") or a.get("artifacts") or "-")[:28]
            live = str(a.get("hook") or a.get("live") or "-")[:8]
            wired = str(a.get("wired") or "-")
            print(f"{name:<26} {arts:<28} {live:<8} {wired}")
    else:
        # Fall back to numbat's own table output.
        sys.stdout.write(proc.stdout or "")

    # Ingested findings, via the daemon proxy (never open DuckDB here).
    try:
        from routes.local_query import local_store_via_daemon
        found = local_store_via_daemon("query_security_events", limit=1000) or []
        numbat_rows = [r for r in found
                       if str(r.get("id", "")).startswith("numbat_")]
        print()
        print(f"findings ingested by ClawMetry: {len(numbat_rows)}"
              f"{'+' if len(found) == 1000 else ''}")
    except Exception:
        pass
    findings_file = Path(os.path.expanduser("~/.numbat/findings.ndjson"))
    if findings_file.exists():
        print(f"file sink: {findings_file} "
              f"({findings_file.stat().st_size // 1024} KiB; daemon tails it)")
    return 0


def cmd_disable(args) -> int:
    numbat = find_numbat()
    if not numbat:
        print("numbat: not installed — nothing to disable")
        return 0
    proc = subprocess.run([numbat, "hook", "uninstall", "--agent", "all"],
                          capture_output=True, text=True, timeout=120)
    sys.stdout.write(proc.stdout or "")
    sys.stderr.write(proc.stderr or "")
    if proc.returncode == 0:
        print("✓ numbat hooks removed from agent configs.")
        print("  The binary and ~/.numbat/findings.ndjson were left in place;")
        print("  delete them manually if you want a full clean-up.")
    return proc.returncode


def cmd_secure(args) -> int:
    action = getattr(args, "secure_cmd", None) or "enable"
    if action == "enable":
        return cmd_enable(args)
    if action == "status":
        return cmd_status(args)
    if action == "disable":
        return cmd_disable(args)
    print(f"unknown secure subcommand: {action}")
    return 2
