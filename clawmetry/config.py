"""
ClawMetry configuration dataclass.
Phase 2: defines the Config structure that will replace global variables in Phase 3.
Currently used for type hints and documentation. dashboard.py globals remain unchanged.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field


# ── DuckDB local-store fast-path feature gate ──────────────────────────────
# Default flipped to ON in 0.12.174 (see PR feat/duckdb-default-on-2026-05-13).
# Prior to that release every route's DuckDB fast path was opt-in via
# CLAWMETRY_LOCAL_STORE_READ=1, which no installer/plist set, so 100% of users
# silently fell through to the legacy gateway/JSONL paths. Default-on is safe
# because every fast path is wrapped in try/except and falls through to the
# legacy code path on any miss (daemon down, query fails, no rows, etc).

# Disable values are checked case-insensitively after .strip(). Empty string
# is treated as disable so ``CLAWMETRY_LOCAL_STORE_READ=`` behaves the same
# as explicitly setting it to 0 (matches the task spec for the flip PR).
_LOCAL_STORE_DISABLE_VALUES = frozenset({"0", "false", "no", "off", ""})


def is_local_store_read_enabled() -> bool:
    """Return True unless explicitly disabled via CLAWMETRY_LOCAL_STORE_READ=0.

    Defaults to ON since 0.12.174. Set ``CLAWMETRY_LOCAL_STORE_READ=0`` (or
    ``false`` / ``no`` / ``off``) to force the legacy gateway/JSONL path —
    useful for A/B comparisons or to bypass a corrupt local store.

    Fast paths fall through to the legacy path on any miss, so default-on is
    safe even when the daemon isn't running. See routes/*.py — every caller
    of this helper wraps its DuckDB read in try/except + None-on-failure.
    """
    # Default "1" so unset env → enabled. Pre-flip behaviour (default OFF)
    # required CLAWMETRY_LOCAL_STORE_READ=1, which no installer set.
    return os.environ.get("CLAWMETRY_LOCAL_STORE_READ", "1").strip().lower() \
        not in _LOCAL_STORE_DISABLE_VALUES


# ── ClawMetry-internal session filter ──────────────────────────────────────
# Sessions ClawMetry itself spawns to drive OpenClaw (Self-Evolve, Fix-with-AI,
# memory probes, …) all use a "clawmetry-" session-id prefix. They are our own
# plumbing, not the user's agent activity, so user-facing views (transcripts,
# brain feed, stuck-session alerts) hide them by default. Set
# CLAWMETRY_SHOW_INTERNAL_SESSIONS=1 to surface them (debugging ClawMetry itself).
CLAWMETRY_INTERNAL_SESSION_PREFIX = "clawmetry-"
_SHOW_INTERNAL_ENABLE_VALUES = frozenset({"1", "true", "yes", "on"})


def is_clawmetry_internal_session(session_id) -> bool:
    """True for sessions ClawMetry spawns to invoke OpenClaw (clawmetry-fix,
    clawmetry-selfevolve, clawmetry-mem-probe, …).

    Matches both the bare id (``clawmetry-fix``) and the full OpenClaw
    session-id form (``agent:main:explicit:clawmetry-fix``), where the base id
    is the last ``:``-delimited segment. Without the segment check the full
    form leaked into user-facing views: the cloud Embodied list showed it as a
    ghost session with an empty transcript (cloud-side fix landed in #1063),
    and ``_check_stuck_sessions`` fired nuisance stuck-session alerts for the
    helpers themselves (#1954).
    """
    if not session_id:
        return False
    sid = str(session_id)
    return sid.startswith(CLAWMETRY_INTERNAL_SESSION_PREFIX) or (
        ":" + CLAWMETRY_INTERNAL_SESSION_PREFIX
    ) in sid


def hide_clawmetry_session(session_id) -> bool:
    """Whether to hide ``session_id`` from user-facing views because it's
    ClawMetry's own plumbing. Override with CLAWMETRY_SHOW_INTERNAL_SESSIONS=1."""
    if not is_clawmetry_internal_session(session_id):
        return False
    return os.environ.get("CLAWMETRY_SHOW_INTERNAL_SESSIONS", "").strip().lower() \
        not in _SHOW_INTERNAL_ENABLE_VALUES


# ── Local-only mode (cloud sync opt-out) ───────────────────────────────────
# Persistent opt-out from cloud sync. Two equivalent triggers — either one
# turns it on; both survive updates:
#   * CLAWMETRY_NO_CLOUD=1 (env)
#   * ~/.clawmetry/nocloud  (marker file written by `clawmetry disconnect`)
# When set, the sync daemon STILL ingests OpenClaw events into the local
# DuckDB store (so the localhost dashboard keeps showing fresh data), but
# skips every cloud-side call: no heartbeat, no encrypted snapshot push,
# no cache_push, no /ingest/* POSTs, no `clawmetry connect` auto-prompt.
# Background: GitHub #1937 — users want a real "local only, never phone
# home" mode that updates can't silently re-enable.
NOCLOUD_MARKER_PATH = os.path.expanduser("~/.clawmetry/nocloud")
_NO_CLOUD_ENABLE_VALUES = frozenset({"1", "true", "yes", "on"})


def is_cloud_disabled() -> bool:
    """True when the user has opted out of cloud sync via env or marker file.

    Either CLAWMETRY_NO_CLOUD=1 (1/true/yes/on, case-insensitive) or the
    presence of ``~/.clawmetry/nocloud`` flips the daemon into local-only
    mode. The marker file is the persistent path (survives updates and
    daemon restarts); the env var is for one-off / containerised use.
    """
    env = os.environ.get("CLAWMETRY_NO_CLOUD", "").strip().lower()
    if env in _NO_CLOUD_ENABLE_VALUES:
        return True
    try:
        return os.path.isfile(NOCLOUD_MARKER_PATH)
    except Exception:
        return False


def cloud_egress_enabled(config: dict = None) -> bool:
    """Cloud egress is OPT-IN — True only when the user explicitly linked an
    account AND has not opted out.

    Product rule (founder, 2026-07-31): a default install is SELF-HOSTED —
    nothing leaves the machine until the user runs `clawmetry login` /
    `clawmetry connect` (or picks the managed/cloud onboarding path), all of
    which persist an ``api_key``. Before this, gating was opt-OUT only
    (the nocloud marker), so a self-hosted node with a license key but no
    account heart-beat ``X-Api-Key: ""`` to ingest every cycle and logged a
    wall of 401 warnings (found live on a Windows node, 2026-07-31).

    The nocloud marker / CLAWMETRY_NO_CLOUD still hard-disable egress even
    when a key exists.
    """
    if is_cloud_disabled():
        return False
    return bool((config or {}).get("api_key"))


def enable_cloud() -> bool:
    """Clear the local-only marker so the daemon resumes cloud sync.

    A local-only install (or `clawmetry disconnect`) writes the
    ``~/.clawmetry/nocloud`` marker, which `is_cloud_disabled()` honours. Any
    explicit opt-in to cloud (the dashboard "Enable Cloud Sync" CTA,
    `clawmetry connect`) MUST call this, or the connect silently no-ops: the
    token is written but the daemon keeps running local-only and never pushes.
    Returns True if a marker was present and removed. Note: this does NOT
    override the env var ``CLAWMETRY_NO_CLOUD`` (that is an explicit per-run
    opt-out the operator set on purpose).
    """
    try:
        if os.path.isfile(NOCLOUD_MARKER_PATH):
            os.remove(NOCLOUD_MARKER_PATH)
            return True
    except Exception:
        pass
    return False


def disable_cloud() -> bool:
    """Write the ``~/.clawmetry/nocloud`` marker so the daemon pauses cloud
    sync on the next iteration. Mirror of :func:`enable_cloud`; used by the
    dashboard header's sync toggle so users can pause sync without dropping
    to the CLI. The marker survives updates and daemon restarts.

    Returns True if a marker was newly written; False if one already
    existed or if the write failed (best-effort, never raises).

    Does NOT alter the ``CLAWMETRY_NO_CLOUD`` env var — that stays whatever
    the operator set it to. The marker is persistent local state; the env
    var is per-run/container config; either one activates local-only mode.
    """
    try:
        if os.path.isfile(NOCLOUD_MARKER_PATH):
            return False
        os.makedirs(os.path.dirname(NOCLOUD_MARKER_PATH), exist_ok=True)
        with open(NOCLOUD_MARKER_PATH, "w") as f:
            f.write("")
        return True
    except Exception:
        return False


# ── The cm_ cloud bearer: where it lives ───────────────────────────────────
# It lives in ClawMetry's OWN config, ``~/.clawmetry/config.json`` → ``api_key``
# (the same file the sync daemon writes via ``sync.save_config``).
#
# It used to *also* be mirrored into OpenClaw's config file as
# ``~/.openclaw/openclaw.json`` → ``clawmetry.cloudToken``. That mirror is
# retired: ``clawmetry`` is not a key in OpenClaw's schema, so every write
# left OpenClaw's own config failing validation. OpenClaw's next CLI run then
# fires ``doctor --fix``, which restores the last-known-good config and
# restarts the gateway — killing the user's active session and rotating the
# gateway token out from under our WS tap. Field report 2026-09-09 (Steven M.
# Alper): that happened at least twice on one machine, and the user's own
# agent correctly diagnosed it as "ClawMetry should store its config in its
# own file, not piggyback on OpenClaw's config".
#
# So: we never write that key again. We still READ it (an install that
# predates this change has the token only there) and, on first read,
# migrate it into our own config and strip it from OpenClaw's — which also
# un-corrupts the file for anyone already affected.
#
# Sign-out / uninstall must still clear BOTH: the E2E workspace key may be
# mirrored into the OS keychain, and neither the keychain entry nor the
# legacy OpenClaw key lives under ~/.clawmetry, so `clawmetry disconnect` /
# `clawmetry uninstall` / the desktop uninstaller clear them explicitly or a
# later install silently re-adopts the old account identity (founder report
# 2026-08-10: a fresh desktop install landed signed-in with zero login
# because the surviving cloudToken was the first source `_read_cloud_token`
# checks).

OPENCLAW_CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")

#: ClawMetry's own config — the ONLY file we write the cm_ bearer to.
CLAWMETRY_CONFIG_PATH = os.path.expanduser("~/.clawmetry/config.json")


def _load_json(path: str) -> dict:
    """Best-effort dict read. Returns {} for missing/garbage/non-dict."""
    import json as _json

    try:
        with open(path) as f:
            data = _json.load(f)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _atomic_write_json(path: str, data: dict) -> bool:
    """Write ``data`` to ``path`` via a temp file + rename. Never raises."""
    import json as _json

    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            _json.dump(data, f, indent=2)
        os.replace(tmp, path)
        return True
    except Exception:
        return False


def write_cloud_token(token: str) -> bool:
    """Persist the cm_ bearer to ``~/.clawmetry/config.json`` → ``api_key``.

    Merges into the existing config so the daemon's ``node_id`` /
    ``encryption_key`` survive. Returns True on success; never raises.

    Deliberately does NOT touch ``~/.openclaw/openclaw.json`` — see the
    module comment above. Writing there corrupted OpenClaw's config.
    """
    if not token:
        return False
    data = _load_json(CLAWMETRY_CONFIG_PATH)
    if data.get("api_key") == token:
        return True
    data["api_key"] = token
    return _atomic_write_json(CLAWMETRY_CONFIG_PATH, data)


def read_cloud_token() -> str:
    """Return the cm_ bearer, '' when this machine isn't paired.

    Our own config wins. Falls back to the retired OpenClaw mirror and, when
    it finds one there, migrates it: copies the value into our config and
    strips the ``clawmetry`` key out of OpenClaw's file. That heals a machine
    that was corrupted by an older ClawMetry without asking the user to do
    anything. Best-effort — a failed migration still returns the token.
    """
    own = _load_json(CLAWMETRY_CONFIG_PATH).get("api_key") or ""
    # The daemon only ever writes cm_ keys here; anything else is garbage we
    # must not hand to the cloud as a Bearer (audit P0 #5 kept this guard).
    if isinstance(own, str) and own.startswith("cm_"):
        # Our config is authoritative; still clean up a stale legacy mirror
        # so OpenClaw's config stops failing its own schema validation.
        migrate_legacy_cloud_token()
        return own
    legacy = read_legacy_cloud_token()
    if legacy:
        migrate_legacy_cloud_token()
    return legacy


def read_legacy_cloud_token() -> str:
    """Read ``~/.openclaw/openclaw.json`` → ``clawmetry.cloudToken``, '' if absent."""
    section = _load_json(OPENCLAW_CONFIG_PATH).get("clawmetry")
    if not isinstance(section, dict):
        return ""
    token = section.get("cloudToken") or ""
    return token if isinstance(token, str) else ""


#: Set once we have confirmed OpenClaw's config carries no ``clawmetry`` key,
#: so the migration check stops re-reading that file on every cloud-proxy
#: request. Only this process ever writes the key (and after this change, it
#: never does), so a one-shot memo is safe. ``reset_legacy_migration_memo``
#: exists for tests, which point the paths at a tmp_path per case.
_LEGACY_MIGRATION_DONE = False


def reset_legacy_migration_memo() -> None:
    """Forget that the legacy-key check already ran. For tests."""
    global _LEGACY_MIGRATION_DONE
    _LEGACY_MIGRATION_DONE = False


def migrate_legacy_cloud_token() -> bool:
    """Move a legacy ``clawmetry.cloudToken`` out of OpenClaw's config.

    Copies the token into ``~/.clawmetry/config.json`` when we don't already
    have one, then deletes the whole ``clawmetry`` section from
    ``~/.openclaw/openclaw.json``. Idempotent: a no-op (returning False) once
    the key is gone, so calling it from a read path costs one small file read
    — and after the first clean check, nothing at all.

    Returns True only when it actually removed the key.
    """
    global _LEGACY_MIGRATION_DONE
    if _LEGACY_MIGRATION_DONE:
        return False
    legacy = read_legacy_cloud_token()
    if legacy and not (_load_json(CLAWMETRY_CONFIG_PATH).get("api_key") or ""):
        # Adopt it first. If the strip below fails we must not lose the token.
        write_cloud_token(legacy)
    removed = clear_cloud_token()
    if not removed:
        # Nothing there (or the file is unwritable). Either way, stop paying
        # for this check on every read.
        _LEGACY_MIGRATION_DONE = True
    return removed


def clear_cloud_token() -> bool:
    """Remove ONLY the ``clawmetry`` section from ``~/.openclaw/openclaw.json``.

    The file belongs to OpenClaw — never delete it or touch other keys.
    Returns True when a token/section was present and removed; False when
    there was nothing to clear or on any failure (best-effort, never raises).
    """
    import json as _json

    try:
        with open(OPENCLAW_CONFIG_PATH) as f:
            data = _json.load(f)
    except Exception:
        return False
    if not isinstance(data, dict) or "clawmetry" not in data:
        return False
    try:
        del data["clawmetry"]
        tmp = OPENCLAW_CONFIG_PATH + ".tmp"
        with open(tmp, "w") as f:
            _json.dump(data, f, indent=2)
        os.replace(tmp, OPENCLAW_CONFIG_PATH)
        return True
    except Exception:
        return False


def delete_workspace_keychain_entry(node_id: str) -> bool:
    """Best-effort removal of the OS-keychain copy of the E2E workspace key
    (service ``clawmetry``, account ``workspace-key:<node_id>`` — the mirror
    written by the connect flow). Returns True when an entry was deleted;
    False when keyring is unavailable, no entry exists, or deletion failed.
    Never raises.
    """
    if not node_id:
        return False
    try:
        import keyring  # optional dependency; absent on minimal installs

        keyring.delete_password("clawmetry", f"workspace-key:{node_id}")
        return True
    except Exception:
        return False


@dataclass
class ClawMetryConfig:
    """
    Unified configuration for ClawMetry.

    In Phase 3, this will replace the module-level globals in dashboard.py:
    WORKSPACE, SESSIONS_DIR, LOG_DIR, MEMORY_DIR, METRICS_FILE, etc.
    """

    # Paths
    workspace: str = ""
    sessions_dir: str = ""
    log_dir: str = ""
    memory_dir: str = ""
    metrics_file: str = ""
    fleet_db: str = ""

    # Gateway
    gateway_url: str = ""
    gateway_token: str = ""
    gateway_port: int = 18789

    # Runtime
    model: str = ""
    provider: str = ""
    channels: list[str] = field(default_factory=list)
    host: str = "127.0.0.1"
    port: int = 8900
    debug: bool = False

    # Auth
    auth_token: str | None = None

    def from_globals(self, _dashboard_module=None) -> "ClawMetryConfig":
        """
        Populate from dashboard.py module-level globals (migration bridge).

        Args:
            _dashboard_module: Optional dashboard module to use instead of importing.
                             If None, will attempt to import dashboard dynamically.

        This method uses a lazy import pattern to avoid circular dependencies.
        The dashboard module is only imported when this method is called, not at
        module load time.
        """
        try:
            if _dashboard_module is not None:
                d = _dashboard_module
            else:
                import importlib
                import sys

                for mod in list(sys.modules.keys()):
                    if mod == "dashboard" or mod.startswith("dashboard."):
                        d = sys.modules[mod]
                        break
                else:
                    d = importlib.import_module("dashboard")

            self.workspace = getattr(d, "WORKSPACE", "") or ""
            self.sessions_dir = getattr(d, "SESSIONS_DIR", "") or ""
            self.log_dir = getattr(d, "LOG_DIR", "") or ""
            self.memory_dir = getattr(d, "MEMORY_DIR", "") or ""
            self.metrics_file = getattr(d, "METRICS_FILE", "") or ""
            self.gateway_token = getattr(d, "_AUTH_TOKEN", "") or ""
        except (ImportError, AttributeError):
            pass
        return self
