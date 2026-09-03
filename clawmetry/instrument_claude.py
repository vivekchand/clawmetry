"""``clawmetry instrument claude`` — turn on Claude Code's own OpenTelemetry
exporter and point it at the local ClawMetry receiver (WO-57).

Claude Code ships an OTel exporter that is OFF by default and has NO default
protocol, so a user who wants the signals the transcript never carries
(permission decisions, permission-mode changes, API refusals and errors, MCP
connection health, time blocked on a human, per-skill / per-agent cost)
has to hand-set seven variables. This command writes them into the ``env``
object of Claude Code's own settings file, which every launch path (terminal,
IDE, desktop) reads at startup.

Ownership contract (same spirit as ``hooks_claude_code``): merge into the
existing ``env`` object, never overwrite a key we did not write, record
exactly which keys we wrote PER SETTINGS FILE in the marker, and on uninstall
remove only those keys whose value is still what we set. A key already
present with a different value is a CONFLICT: reported, left alone. A user
level install and a ``--project`` install coexist; each has its own record.

Content flags (``OTEL_LOG_USER_PROMPTS`` / ``OTEL_LOG_TOOL_DETAILS`` /
``OTEL_LOG_TOOL_CONTENT``) are OFF unless ``--content`` is passed: the
transcript already holds that text locally, and the default must not widen
what leaves the process. ``OTEL_LOG_RAW_API_BODIES`` is never written.

Stdlib-only: dispatched from the CLI fast path before the dashboard import.
"""
from __future__ import annotations

import glob
import json
import os
import platform
import sys
import time
import urllib.request

_SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")
_PROJECT_SETTINGS_PATH = os.path.join(".claude", "settings.json")
# Shared with hooks_claude_code; this module owns the ``claude_code_otel``
# key, whose value is ``{<settings path>: <record>}``.
_MARKER_PATH = os.path.expanduser("~/.clawmetry/hooks_installed.json")
_MARKER_KEY = "claude_code_otel"

# Where Claude Code reads MANAGED settings, which override the user's file
# (code.claude.com/docs/en/managed-settings). An admin who pinned the OTLP
# destination there has decided where telemetry goes; we refuse rather than
# write a block the runtime will ignore. Only FILE-based policy is checked:
# the macOS plist, the Windows registry and server-managed settings are not
# readable from here, and the output says so.
_MANAGED_SETTINGS_DIRS = {
    "Darwin": ["/Library/Application Support/ClaudeCode"],
    "Linux": ["/etc/claude-code"],
    "Windows": [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "ClaudeCode"),
        # Legacy location; Claude Code no longer reads it, kept so a stale
        # deployment still surfaces as "an admin configured this machine".
        os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"), "ClaudeCode"),
    ],
}
_LOCKED_KEYS = ("OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_EXPORTER_OTLP_HEADERS",
                "OTEL_EXPORTER_OTLP_PROTOCOL", "CLAUDE_CODE_ENABLE_TELEMETRY")

# The compat listener (#4780) and the dashboard port. Probed in this order.
_COMPAT_PORT = 4318
_DEFAULT_DASHBOARD_PORT = 8900
_PROBE_TIMEOUT_S = 1.0


def base_env(endpoint: str) -> dict:
    """The block written on every install. Claude Code has NO default OTLP
    protocol, so the protocol key is never optional. ``http/json`` works on a
    vanilla ``pip install clawmetry`` through the stdlib decoder."""
    return {
        "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
        "OTEL_LOGS_EXPORTER": "otlp",
        "OTEL_METRICS_EXPORTER": "otlp",
        "OTEL_TRACES_EXPORTER": "otlp",
        "CLAUDE_CODE_ENHANCED_TELEMETRY_BETA": "1",
        "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
        "OTEL_EXPORTER_OTLP_ENDPOINT": endpoint,
        # Claude Code's default, pinned: a cumulative preference would make
        # every export re-send running totals the receiver must not add.
        "OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE": "delta",
    }


CONTENT_ENV = {
    "OTEL_LOG_USER_PROMPTS": "1",
    "OTEL_LOG_TOOL_DETAILS": "1",
    "OTEL_LOG_TOOL_CONTENT": "1",
}


# ── paths, settings + marker I/O ────────────────────────────────────────────

def _norm(path: str) -> str:
    """One canonical key per settings file: absolute, symlinks resolved, so a
    marker written from one cwd resolves from another and a dotfiles symlink
    is written THROUGH rather than replaced."""
    return os.path.realpath(os.path.abspath(os.path.expanduser(path)))


class SettingsUnreadable(ValueError):
    """The file exists but is not a JSON object. Never overwrite such a file."""


def _read_json_strict(path: str) -> dict:
    """``{}`` when absent; raises :class:`SettingsUnreadable` on bad JSON or a
    non-object top level."""
    try:
        with open(path) as f:
            txt = f.read().strip()
    except FileNotFoundError:
        return {}
    except OSError as e:
        raise SettingsUnreadable(f"{path}: {e}")
    if not txt:
        return {}
    try:
        data = json.loads(txt)
    except ValueError as e:
        raise SettingsUnreadable(f"{path}: not valid JSON ({e})")
    if not isinstance(data, dict):
        raise SettingsUnreadable(f"{path}: top level is not an object")
    return data


def _read_json(path: str) -> dict:
    """Tolerant read for status paths: anything unreadable is ``{}``."""
    try:
        return _read_json_strict(path)
    except (OSError, ValueError):
        return {}


def _write_json(path: str, data: dict) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    # No lock: Claude Code rewrites its own settings file, so a save that
    # races this write can be lost. The window is one JSON dump; accepted.
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def _read_marker_all(marker_path: str | None = None) -> dict:
    """``{settings path: record}`` for every install we made."""
    data = _read_json(marker_path or _MARKER_PATH)
    m = data.get(_MARKER_KEY)
    if not isinstance(m, dict):
        return {}
    # Only per-path records are ours; ignore any other shape quietly.
    return {k: v for k, v in m.items() if isinstance(v, dict) and "keys" in v}


def _read_marker(path: str, marker_path: str | None = None) -> dict:
    return _read_marker_all(marker_path).get(path, {})


def _write_marker(path: str, entry: dict | None,
                  marker_path: str | None = None) -> None:
    mp = marker_path or _MARKER_PATH
    try:
        data = _read_json(mp)
        block = data.get(_MARKER_KEY)
        if not isinstance(block, dict):
            block = {}
        if entry is None:
            block.pop(path, None)
        else:
            block[path] = entry
        if block:
            data[_MARKER_KEY] = block
        else:
            data.pop(_MARKER_KEY, None)
        _write_json(mp, data)
    except Exception:
        pass


# ── receiver probe + managed lock ───────────────────────────────────────────

def _url_alive(base: str, timeout: float = _PROBE_TIMEOUT_S) -> bool:
    """True when a ClawMetry OTLP receiver answers at ``base``."""
    try:
        req = urllib.request.Request(
            base.rstrip("/") + "/api/otel-status",
            headers={"User-Agent": "clawmetry-instrument"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


def _port_alive(port: int, timeout: float = _PROBE_TIMEOUT_S) -> bool:
    return _url_alive(f"http://127.0.0.1:{port}", timeout)


def probe_receiver(dashboard_port: int | None = None) -> dict:
    """Which local receiver is live right now. The compat listener steps
    aside when 4318 is taken by a user's own collector, so we must ask
    rather than assume."""
    port = dashboard_port or int(os.environ.get("CLAWMETRY_PORT")
                                 or _DEFAULT_DASHBOARD_PORT)
    if _port_alive(_COMPAT_PORT):
        return {"endpoint": f"http://127.0.0.1:{_COMPAT_PORT}",
                "port": _COMPAT_PORT, "listening": True, "via": "compat_4318"}
    if _port_alive(port):
        return {"endpoint": f"http://127.0.0.1:{port}",
                "port": port, "listening": True, "via": "dashboard"}
    return {"endpoint": f"http://127.0.0.1:{port}",
            "port": port, "listening": False, "via": "dashboard"}


def managed_candidates(system: str | None = None) -> list:
    """Every managed-settings file Claude Code would read on this platform:
    ``managed-settings.json`` plus ``managed-settings.d/*.json``."""
    out = []
    for d in _MANAGED_SETTINGS_DIRS.get(system or platform.system(), []):
        out.append(os.path.join(d, "managed-settings.json"))
        try:
            out.extend(sorted(glob.glob(os.path.join(d, "managed-settings.d", "*.json"))))
        except Exception:
            pass
    return out


def managed_lock(paths: list | None = None) -> dict | None:
    """The managed settings file, if one pins an OTLP destination key.
    Returns ``{"path", "keys"}`` or ``None``."""
    candidates = managed_candidates() if paths is None else paths
    for path in candidates:
        try:
            if not os.path.isfile(path):
                continue
            env = _read_json(path).get("env") or {}
            locked = [k for k in _LOCKED_KEYS if isinstance(env, dict) and k in env]
            if locked:
                return {"path": path, "keys": locked}
        except Exception:
            continue
    return None


# ── install / uninstall / status ────────────────────────────────────────────

def install(settings_path: str | None = None, *, content: bool = False,
            endpoint: str | None = None, probe: dict | None = None,
            managed: dict | None = None, marker_path: str | None = None,
            managed_paths: list | None = None) -> dict:
    """Write the telemetry ``env`` block. Idempotent; merges; never clobbers.

    ``probe`` / ``managed`` / ``managed_paths`` exist so tests can inject the
    receiver answer and the lock state without a network or root paths.
    """
    path = _norm(settings_path or _SETTINGS_PATH)
    try:
        lock = managed if managed is not None else managed_lock(managed_paths)
        if lock:
            return {"status": "refused", "path": path,
                    "reason": "managed_settings_lock",
                    "managed_path": lock["path"], "locked_keys": lock["keys"],
                    "message": ("Claude Code managed settings pin the OTLP "
                                "destination; a user-level block would be "
                                "ignored. Ask your administrator.")}
        if probe is None:
            if endpoint:
                probe = {"endpoint": endpoint, "via": "explicit",
                         "listening": _url_alive(endpoint)}
            else:
                probe = probe_receiver()
        target = endpoint or probe["endpoint"]

        try:
            settings = _read_json_strict(path)
        except SettingsUnreadable as e:
            return {"status": "error", "path": path, "reason": "settings_unreadable",
                    "error": str(e),
                    "message": ("The settings file is not valid JSON; nothing "
                                "was written. Fix the file and run again.")}
        env = settings.get("env")
        if "env" in settings and not isinstance(env, dict):
            return {"status": "refused", "path": path, "reason": "env_not_object",
                    "message": ("`env` in the settings file is not an object; "
                                "not touched.")}
        prior = _read_marker(path, marker_path)
        prior_keys = prior.get("keys") or {}
        created_env = env is None
        if created_env and prior_keys:
            # A re-run after the user deleted the whole block: the object we
            # create now is still ours.
            created_env = True
        elif not created_env and prior_keys:
            # The env object exists and we have a record for THIS file: keep
            # remembering whether we created it, or uninstall would leave
            # an empty ``env`` behind.
            created_env = bool(prior.get("created_env"))
        if env is None:
            env = {}
            settings["env"] = env

        wanted = base_env(target)
        if content:
            wanted.update(CONTENT_ENV)

        written, present, conflicts = {}, [], []
        for k, v in wanted.items():
            cur = env.get(k)
            if cur is None:
                env[k] = v
                written[k] = v
            elif str(cur) == str(v):
                # Ours from a previous run, or the user already had this
                # exact value. Claim it only when our record for this file
                # says so; a coincidence is not ownership.
                if k in prior_keys:
                    written[k] = v
                else:
                    present.append(k)
            else:
                if k in prior_keys and str(cur) == str(prior_keys[k]):
                    # Still our previous value (endpoint moved, protocol
                    # changed): update, keep ownership.
                    env[k] = v
                    written[k] = v
                else:
                    conflicts.append({"key": k, "current": cur, "wanted": v})

        # Content flags a previous run wrote but this run did not ask for:
        # remove them (still ours, still our value) so ``instrument claude``
        # without --content reverts to the conservative default.
        removed = []
        if not content:
            for k in CONTENT_ENV:
                if k in prior_keys and str(env.get(k)) == str(prior_keys[k]):
                    env.pop(k, None)
                    removed.append(k)

        before = _read_json(path)
        file_changed = before != settings
        if file_changed:
            _write_json(path, settings)

        _write_marker(path, {
            "keys": written,
            "created_env": bool(created_env),
            "endpoint": target,
            "content": bool(content),
            "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, marker_path)

        return {
            "status": "installed" if file_changed else "already_present",
            "path": path, "endpoint": target,
            "receiver_listening": probe.get("listening"),
            "receiver_via": probe.get("via"),
            "written": sorted(written), "present": present,
            "removed": removed, "conflicts": conflicts,
            "content": bool(content), "changed": bool(written or removed),
            "managed_checked": "file-based managed settings only",
            "note": ("Running Claude Code sessions keep their old "
                     "configuration until restarted."),
        }
    except Exception as e:
        return {"status": "error", "path": path, "error": str(e)}


def uninstall(settings_path: str | None = None, *,
              marker_path: str | None = None) -> dict:
    """Remove only the keys we wrote to THIS file, and only where the value is
    still ours. Refuses (``not_installed``) for a file we have no record of."""
    path = _norm(settings_path or _SETTINGS_PATH)
    try:
        prior = _read_marker(path, marker_path)
        keys = prior.get("keys") or {}
        if not keys:
            others = sorted(p for p in _read_marker_all(marker_path) if p != path)
            return {"status": "not_installed", "path": path, "removed": [],
                    "kept": [], "other_installs": others,
                    "note": ("clawmetry has no record of writing a telemetry "
                             "block to this file.")}
        try:
            settings = _read_json_strict(path)
        except SettingsUnreadable as e:
            return {"status": "error", "path": path, "reason": "settings_unreadable",
                    "error": str(e), "removed": [], "kept": []}
        env = settings.get("env")
        removed, kept = [], []
        if isinstance(env, dict):
            for k, v in keys.items():
                if k in env:
                    if str(env[k]) == str(v):
                        env.pop(k)
                        removed.append(k)
                    else:
                        kept.append({"key": k, "current": env[k], "ours": v})
            if not env and prior.get("created_env"):
                settings.pop("env", None)
        if _read_json(path) != settings:
            _write_json(path, settings)
        _write_marker(path, None, marker_path)
        return {"status": "uninstalled", "path": path,
                "removed": sorted(removed), "kept": kept,
                "note": ("Running Claude Code sessions keep exporting until "
                         "restarted.")}
    except Exception as e:
        return {"status": "error", "path": path, "error": str(e)}


def _status_for(path: str, marker: dict) -> dict:
    ours = (marker.get(path) or {}).get("keys") or {}
    unreadable = None
    try:
        env = _read_json_strict(path).get("env")
    except SettingsUnreadable as e:
        env, unreadable = None, str(e)
    env = env if isinstance(env, dict) else {}
    in_place = [k for k, v in ours.items() if str(env.get(k)) == str(v)]
    drifted = [k for k in ours if k in env and str(env[k]) != str(ours[k])]
    missing = [k for k in ours if k not in env]
    enabled = str(env.get("CLAUDE_CODE_ENABLE_TELEMETRY")) == "1"
    return {
        "settings_path": path,
        "configured": bool(ours) and not missing and not drifted,
        "installed_at": (marker.get(path) or {}).get("installed_at"),
        "telemetry_enabled": enabled,
        "endpoint": env.get("OTEL_EXPORTER_OTLP_ENDPOINT") if enabled else None,
        "protocol": env.get("OTEL_EXPORTER_OTLP_PROTOCOL") if enabled else None,
        "content": any(str(env.get(k)) == "1" for k in CONTENT_ENV),
        "ours": sorted(ours), "in_place": sorted(in_place),
        "drifted": sorted(drifted), "missing": sorted(missing),
        "unreadable": unreadable,
    }


def status(settings_path: str | None = None, *, marker_path: str | None = None,
           probe: bool = True) -> dict:
    """What is on disk right now, and whether a receiver is listening.

    With no path: the user-level file first, then every project file we have
    a record of. ``configured`` is true when ANY recorded install is intact;
    the top-level fields describe the first intact one (user level wins).
    """
    marker = _read_marker_all(marker_path)
    if settings_path:
        paths = [_norm(settings_path)]
    else:
        user = _norm(_SETTINGS_PATH)
        paths = [user] + sorted(p for p in marker if p != user)
    installs = [_status_for(p, marker) for p in paths]
    primary = next((i for i in installs if i["configured"]), None) or installs[0]
    out = dict(primary)
    out["configured"] = any(i["configured"] for i in installs)
    out["settings_path"] = primary["settings_path"] if primary["ours"] else None
    out["installs"] = [{"settings_path": i["settings_path"],
                        "configured": i["configured"],
                        "drifted": i["drifted"], "missing": i["missing"],
                        "unreadable": i["unreadable"]} for i in installs if i["ours"]]
    if probe:
        out["receiver"] = probe_receiver()
    return out


# ── CLI ─────────────────────────────────────────────────────────────────────

_USAGE = ("usage: clawmetry instrument claude [--project] [--content] "
          "[--endpoint URL] [--uninstall | --status] [--json]\n")


def cli_main(argv: list | None = None) -> int:
    argv = list(sys.argv[2:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        sys.stdout.write(_USAGE)
        sys.stdout.write(
            "\nTurns on Claude Code's own OpenTelemetry exporter and points it\n"
            "at the local ClawMetry receiver by writing an `env` block into\n"
            "~/.claude/settings.json (or .claude/settings.json with --project).\n"
            "Prompt/tool content stays off unless --content is given; with it,\n"
            "prompt and tool text also land in the local events table.\n")
        return 0
    target = argv[0]
    if target != "claude":
        sys.stderr.write(f"clawmetry instrument: unsupported target {target!r} "
                         "(supported: claude)\n")
        return 2
    flags = argv[1:]
    as_json = "--json" in flags
    path = _PROJECT_SETTINGS_PATH if "--project" in flags else None
    endpoint = None
    if "--endpoint" in flags:
        try:
            endpoint = flags[flags.index("--endpoint") + 1]
        except IndexError:
            sys.stderr.write("--endpoint needs a URL\n")
            return 2

    if "--status" in flags:
        res = status(path)
        if as_json:
            print(json.dumps(res, indent=2))
        else:
            _print_status(res)
        return 0
    if "--uninstall" in flags:
        res = uninstall(path)
        if as_json:
            print(json.dumps(res, indent=2))
        else:
            if res["status"] == "not_installed":
                print(f"Nothing to remove: clawmetry never wrote a telemetry "
                      f"block to {res['path']}.")
                for o in res.get("other_installs") or []:
                    print(f"  (there is one in {o}; pass --project from that "
                          f"directory, or run from the user level)")
            elif res["status"] == "uninstalled":
                print(f"Removed {len(res['removed'])} key(s) from {res['path']}.")
                for k in res.get("kept") or []:
                    print(f"  kept {k['key']} (value changed since we wrote it)")
                print(res["note"])
            else:
                print(f"Error: {res.get('message') or res.get('error')}")
        return 0 if res["status"] != "error" else 1

    res = install(path, content="--content" in flags, endpoint=endpoint)
    if as_json:
        print(json.dumps(res, indent=2))
    else:
        _print_install(res)
    return 0 if res["status"] in ("installed", "already_present") else 1


def _print_install(res: dict) -> None:
    st = res.get("status")
    if st == "refused":
        print("Refused: " + res.get("message", ""))
        if res.get("managed_path"):
            print(f"  managed settings: {res.get('managed_path')}")
            print(f"  locked keys:      {', '.join(res.get('locked_keys') or [])}")
        return
    if st == "error":
        print(f"Error: {res.get('message') or res.get('error')}")
        return
    verb = "Wrote" if st == "installed" else "Already present in"
    print(f"{verb} {res['path']}")
    line = f"  endpoint: {res['endpoint']}"
    if not res.get("receiver_listening"):
        if res.get("receiver_via") == "explicit":
            line += "  (could not confirm a ClawMetry receiver at that URL)"
        else:
            line += "  (no receiver answering there right now; start `clawmetry`)"
    print(line)
    print(f"  protocol: http/json   content: {'ON' if res.get('content') else 'off'}")
    for c in res.get("conflicts") or []:
        print(f"  left alone {c['key']}={c['current']!r} (wanted {c['wanted']!r})")
    for k in res.get("removed") or []:
        print(f"  removed {k} (content flag; pass --content to keep it)")
    print("  checked: file-based managed settings only (plist, registry and "
          "server-managed policy are not visible from here)")
    print(res["note"])


def _print_status(res: dict) -> None:
    if res.get("configured"):
        print(f"Claude Code telemetry: configured ({res['settings_path']})")
    elif res.get("telemetry_enabled"):
        print("Claude Code telemetry: enabled, but not by clawmetry "
              "(or the block drifted)")
    else:
        print("Claude Code telemetry: not configured "
              "(run `clawmetry instrument claude`)")
    if res.get("endpoint"):
        print(f"  endpoint: {res['endpoint']}  protocol: {res.get('protocol')}"
              f"  content: {'ON' if res.get('content') else 'off'}")
    if res.get("unreadable"):
        print(f"  unreadable: {res['unreadable']}")
    for k in res.get("drifted") or []:
        print(f"  drifted: {k}")
    for k in res.get("missing") or []:
        print(f"  missing: {k}")
    for i in res.get("installs") or []:
        if i["settings_path"] != res.get("settings_path"):
            state = "ok" if i["configured"] else "drifted/missing"
            print(f"  also: {i['settings_path']} ({state})")
    rc = res.get("receiver") or {}
    if rc:
        print(f"  receiver: {rc['endpoint']} "
              f"{'listening' if rc.get('listening') else 'NOT listening'}")
