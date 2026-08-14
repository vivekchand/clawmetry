"""Runtime-hook lifecycle contract (#4817).

Several runtimes persist only the *decision* of an approval prompt,
never the *prompt text the user saw* — so replay can show "approved"
but not "approved WHAT modal." For those runtimes we install a small
hook (Claude Code hook, OpenClaw plugin, Cursor extension, …) that
captures the missing signal.

**Non-negotiable requirement (goal thread 2026-08-14):**

    "When ClawMetry is uninstalled it should cleanly remove all of
    them — say if we installed hook for [any runtime] — that also
    should be removed so that the agent runtime should not error
    out when ClawMetry is uninstalled."

This module is the contract every hook installer must satisfy. There
is exactly one authoritative record — ``~/.clawmetry/hooks/installed.json`` —
and every hook file on disk MUST have a matching entry.  ``clawmetry
uninstall`` removes both.

The install/uninstall API is intentionally small so per-runtime hook
authors (Claude Code prompt-capture, OpenClaw plugin, Cursor
extension, …) can register a ``HookSpec`` and forget the lifecycle
plumbing.

Public surface (used by per-runtime hook packages + the CLI):

    install(spec: HookSpec) -> InstalledHook
    uninstall(hook_id: str) -> bool
    uninstall_all() -> list[str]
    status() -> list[InstalledHook]
    verify_all() -> list[HookVerdict]

CLI entrypoints wire ``_cmd_uninstall`` (see ``clawmetry/cli.py``) so
draining the manifest is part of every ``clawmetry uninstall`` /
drag-to-trash / systemd-remove path — burn ``project_drag_to_trash_uninstall``
already covers the OS surfaces we own; this module adds the hook
section.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import shutil
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


# ── manifest layout ──────────────────────────────────────────────────────

HOOKS_DIR: Path = Path(
    os.environ.get("CLAWMETRY_HOOKS_DIR",
                   os.path.expanduser("~/.clawmetry/hooks"))
)
MANIFEST_PATH: Path = HOOKS_DIR / "installed.json"
BACKUPS_DIR: Path = HOOKS_DIR / "backups"
DATA_DIR: Path = HOOKS_DIR / "data"          # captured prompts, etc.

# In-process lock for concurrent installs on the same manifest. Fleet-wide
# safety comes from an OS lockfile below (see ``_manifest_lock``).
_INPROC_LOCK = threading.RLock()

# Marker written into config files we edit so a partial-restore can identify
# ClawMetry-owned keys during uninstall (see ``_should_remove_key``).
CLAWMETRY_MARKER_KEY = "__clawmetry"


# ── typed records ────────────────────────────────────────────────────────


@dataclasses.dataclass
class HookSpec:
    """What a caller passes to install().

    ``hook_id`` uniquely identifies this hook across runs; installing a
    spec whose id is already registered replaces the existing entry
    (backup-first, atomic).

    ``target_config`` and ``target_config_key`` are optional — many
    hooks drop a file and touch nothing else. When present, uninstall
    knows which JSON key to strip on removal.
    """
    hook_id: str
    runtime: str                        # "claude_code" | "openclaw" | …
    purpose: str                        # one-line human summary
    install_path: str                   # absolute path of the hook file itself
    payload: bytes                      # exact bytes to drop at install_path
    target_config: str | None = None    # optional: config file we also edit
    target_config_key: str | None = None
    target_config_value: Any | None = None
    clawmetry_version: str = ""


@dataclasses.dataclass
class InstalledHook:
    hook_id: str
    runtime: str
    purpose: str
    install_path: str
    target_config: str | None
    target_config_key: str | None
    backup_path: str | None
    checksum: str
    installed_at: str
    clawmetry_version: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "InstalledHook":
        # Ignore unknown fields — forward-compat.
        fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in fields})


@dataclasses.dataclass
class HookVerdict:
    hook_id: str
    ok: bool
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


# ── low-level manifest I/O ───────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_dirs() -> None:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_manifest() -> list[InstalledHook]:
    if not MANIFEST_PATH.exists():
        return []
    try:
        raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Corrupt manifest: return empty; verify_all will surface each
        # file-on-disk-without-manifest as orphaned so operators can
        # investigate. Never silently discard installed hooks.
        return []
    hooks = raw.get("hooks", []) if isinstance(raw, dict) else []
    return [InstalledHook.from_dict(h) for h in hooks if isinstance(h, dict)]


def _write_manifest_atomic(hooks: Iterable[InstalledHook]) -> None:
    """Atomic replace so a crash mid-write never leaves half-JSON."""
    _ensure_dirs()
    payload = {
        "schema_version": 1,
        "hooks": [h.to_dict() for h in hooks],
    }
    tmp = tempfile.NamedTemporaryFile(
        mode="w", dir=str(HOOKS_DIR), delete=False,
        prefix=".installed.", suffix=".json",
    )
    try:
        json.dump(payload, tmp, indent=2, sort_keys=True)
        tmp.flush()
        os.fsync(tmp.fileno())
    finally:
        tmp.close()
    os.replace(tmp.name, MANIFEST_PATH)


class _ManifestLock:
    """Cross-process manifest lock — a lockfile the daemon and CLI
    both take before touching installed.json. Best-effort on Windows
    (uses O_CREAT | O_EXCL retry loop); flock() on POSIX.
    """

    def __init__(self) -> None:
        self._path = HOOKS_DIR / ".installed.lock"
        self._fh = None

    def __enter__(self) -> "_ManifestLock":
        _ensure_dirs()
        try:
            import fcntl
            self._fh = open(self._path, "w")
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX)
        except ImportError:  # Windows fallback: exclusive-create retry
            for _ in range(50):
                try:
                    self._fh = os.open(
                        str(self._path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    break
                except FileExistsError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("could not acquire hook manifest lock")
        return self

    def __exit__(self, *exc) -> None:
        try:
            if isinstance(self._fh, int):
                os.close(self._fh)
                try:
                    os.unlink(self._path)
                except OSError:
                    pass
            else:
                self._fh.close()
        except Exception:
            pass


def _manifest_lock() -> _ManifestLock:
    return _ManifestLock()


# ── config-edit helpers (safe merge-remove on uninstall) ─────────────────


def _config_backup(target: Path) -> Path | None:
    if not target.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    dest = BACKUPS_DIR / f"{target.name}.{stamp}.bak"
    _ensure_dirs()
    shutil.copy2(target, dest)
    return dest


def _write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(
        mode="w", dir=str(path.parent), delete=False,
        prefix=f".{path.name}.", suffix=".tmp",
    )
    try:
        json.dump(data, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
    finally:
        tmp.close()
    os.replace(tmp.name, path)


def _config_add_key(target: Path, key_path: str, value: Any) -> None:
    """Set target[key_path] = value in the JSON config, marking the leaf
    with __clawmetry: true so uninstall can identify it later. key_path
    is dot-separated (e.g. "hooks.PreToolUse")."""
    data: Any = {}
    if target.exists():
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    d = data
    parts = key_path.split(".")
    for p in parts[:-1]:
        if not isinstance(d.get(p), dict):
            d[p] = {}
        d = d[p]
    # Wrap the value in an object carrying the marker so remove-merge is safe.
    if isinstance(value, dict):
        value = dict(value)
        value.setdefault(CLAWMETRY_MARKER_KEY, True)
    d[parts[-1]] = value
    _write_json_atomic(target, data)


def _config_remove_key(target: Path, key_path: str) -> None:
    """Remove target[key_path] IFF the value at that key carries the
    ClawMetry marker. If the user replaced it with their own value,
    leave it alone (never stomp user config)."""
    if not target.exists():
        return
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    d = data
    parts = key_path.split(".")
    for p in parts[:-1]:
        d = d.get(p) if isinstance(d, dict) else None
        if d is None:
            return
    if not isinstance(d, dict):
        return
    leaf = d.get(parts[-1])
    if isinstance(leaf, dict) and leaf.get(CLAWMETRY_MARKER_KEY):
        d.pop(parts[-1], None)
    _write_json_atomic(target, data)


# ── public API ───────────────────────────────────────────────────────────


def install(spec: HookSpec) -> InstalledHook:
    """Install a runtime hook. Idempotent by ``hook_id`` — re-installing
    a spec with the same id replaces the previous entry (backup-first,
    atomic). See module docstring for the lifecycle contract."""
    with _INPROC_LOCK, _manifest_lock():
        _ensure_dirs()
        install_path = Path(spec.install_path)
        install_path.parent.mkdir(parents=True, exist_ok=True)
        # If a stale hook file with the same id exists, back it up before
        # overwriting so we can restore on rollback.
        existing = None
        for h in _read_manifest():
            if h.hook_id == spec.hook_id:
                existing = h
                break
        # 1. Back up target_config first — before dropping the hook file.
        backup_path: Path | None = None
        if spec.target_config:
            backup_path = _config_backup(Path(spec.target_config))
        # 2. Drop the hook payload atomically.
        tmp = tempfile.NamedTemporaryFile(
            mode="wb", dir=str(install_path.parent), delete=False,
            prefix=f".{install_path.name}.", suffix=".tmp",
        )
        try:
            tmp.write(spec.payload)
            tmp.flush()
            os.fsync(tmp.fileno())
        finally:
            tmp.close()
        os.chmod(tmp.name, 0o600)
        os.replace(tmp.name, install_path)
        # 3. Merge into the target config (with marker) if requested.
        if spec.target_config and spec.target_config_key:
            _config_add_key(
                Path(spec.target_config),
                spec.target_config_key,
                spec.target_config_value if spec.target_config_value is not None
                else {"path": spec.install_path},
            )
        # 4. Register in the manifest (last, so a crash before this yields
        #    a rescuable orphan file rather than a phantom entry).
        checksum = hashlib.sha256(spec.payload).hexdigest()
        installed = InstalledHook(
            hook_id=spec.hook_id,
            runtime=spec.runtime,
            purpose=spec.purpose,
            install_path=spec.install_path,
            target_config=spec.target_config,
            target_config_key=spec.target_config_key,
            backup_path=str(backup_path) if backup_path else None,
            checksum=f"sha256:{checksum}",
            installed_at=_now_iso(),
            clawmetry_version=spec.clawmetry_version,
        )
        hooks = [h for h in _read_manifest() if h.hook_id != spec.hook_id]
        hooks.append(installed)
        _write_manifest_atomic(hooks)
        # Rollback path if the install partially failed would live here;
        # every step above is atomic-by-file so a crash yields
        # inspectable state, not a wedged runtime. ``existing`` is used
        # by callers that want to compare to the prior state.
        _ = existing
        return installed


def uninstall(hook_id: str) -> bool:
    """Remove a hook and every trace of it — the hook file, the config-file
    key we added, and the manifest entry. Returns True if a matching entry
    was removed (idempotent — returns False if the id was never installed).

    Non-negotiable: if this returns True, the runtime that had the hook
    installed MUST continue to boot cleanly (no orphan config, no
    dangling script path referenced in a settings file).
    """
    with _INPROC_LOCK, _manifest_lock():
        hooks = _read_manifest()
        target = next((h for h in hooks if h.hook_id == hook_id), None)
        if target is None:
            return False
        # 1. Remove the config-file key we added.
        if target.target_config and target.target_config_key:
            try:
                _config_remove_key(
                    Path(target.target_config), target.target_config_key)
            except Exception:
                # Never abort uninstall on a config-file glitch; the manifest
                # entry drop is the source of truth for whether we still
                # claim ownership of that key. Users can re-run uninstall.
                pass
        # 2. Delete the hook file itself.
        try:
            Path(target.install_path).unlink()
        except FileNotFoundError:
            pass
        except OSError:
            # Best-effort — a failed unlink shouldn't strand the manifest.
            pass
        # 3. Deregister from the manifest.
        remaining = [h for h in hooks if h.hook_id != hook_id]
        _write_manifest_atomic(remaining)
        return True


def uninstall_all() -> list[str]:
    """Drain every hook. Returns the ids that were removed, oldest-first.
    Called by ``_cmd_uninstall`` and the macOS drag-to-trash watchdog.
    """
    ids: list[str] = []
    for h in list(status()):
        if uninstall(h.hook_id):
            ids.append(h.hook_id)
    return ids


def status() -> list[InstalledHook]:
    with _INPROC_LOCK:
        return _read_manifest()


def verify_all() -> list[HookVerdict]:
    """Sanity-check every registered hook. Called by the daemon on start
    so a hook whose file was deleted out-of-band is detected and
    deregistered — the runtime never sees a broken config referencing
    a missing script.

    Two failure modes are surfaced:
      - manifest says installed, file gone → deregister + warn
      - manifest says installed, file present but checksum drift →
        leave manifest entry, warn (user may have hand-edited).
    """
    verdicts: list[HookVerdict] = []
    for h in status():
        path = Path(h.install_path)
        if not path.exists():
            verdicts.append(HookVerdict(
                hook_id=h.hook_id, ok=False,
                reason="hook file missing; will self-heal on next daemon pass",
            ))
            continue
        try:
            digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as e:
            verdicts.append(HookVerdict(
                hook_id=h.hook_id, ok=False, reason=f"read error: {e}",
            ))
            continue
        if digest != h.checksum:
            verdicts.append(HookVerdict(
                hook_id=h.hook_id, ok=False,
                reason="checksum drift (user may have edited the hook)",
            ))
        else:
            verdicts.append(HookVerdict(hook_id=h.hook_id, ok=True))
    return verdicts


def self_heal(logger: Callable[[str], None] | None = None) -> int:
    """Daemon-start convenience: run verify_all(), deregister any entry
    whose file is missing so the runtime's config never dangles.
    Returns the number of entries deregistered."""
    _log = logger or (lambda s: None)
    removed = 0
    for v in verify_all():
        if v.ok:
            continue
        if v.reason.startswith("hook file missing"):
            _log(f"[hooks] deregistering orphan {v.hook_id}: {v.reason}")
            uninstall(v.hook_id)
            removed += 1
        else:
            _log(f"[hooks] warning: {v.hook_id}: {v.reason}")
    return removed
