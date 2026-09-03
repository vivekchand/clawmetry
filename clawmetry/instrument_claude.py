"""``clawmetry instrument claude`` — turn on Claude Code's own OpenTelemetry
exporter and point it at the local ClawMetry receiver (WO-57).

Claude Code ships an OTel exporter that is OFF by default and has NO default
protocol, so a user who wants the signals the transcript never carries
(permission decisions, permission-mode changes, API refusals and errors, MCP
connection health, time blocked on a human, per-skill / per-agent cost) has
to hand-set seven variables. This command writes them into the ``env`` object
of Claude Code's own settings file, which every launch path (terminal, IDE,
desktop) reads at startup.

Ownership contract (same spirit as ``hooks_claude_code``): merge into the
existing ``env`` object, never overwrite a key we did not write, record
exactly which keys we wrote in the marker file, and on uninstall remove only
those keys whose value is still what we set. A key already present with a
different value is a CONFLICT: reported, left alone.

Content flags (``OTEL_LOG_USER_PROMPTS`` / ``OTEL_LOG_TOOL_DETAILS`` /
``OTEL_LOG_TOOL_CONTENT``) are OFF unless ``--content`` is passed — the
transcript already holds that text locally, and the default must not widen
what leaves the process. ``OTEL_LOG_RAW_API_BODIES`` is never written.

Stdlib-only: dispatched from the CLI fast path before the dashboard import.
"""
from __future__ import annotations

import json
import os
import platform
import sys
import time
import urllib.request

_SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")
_PROJECT_SETTINGS_PATH = os.path.join(".claude", "settings.json")
# Shared with hooks_claude_code; this module owns the ``claude_code_otel`` key.
_MARKER_PATH = os.path.expanduser("~/.clawmetry/hooks_installed.json")
_MARKER_KEY = "claude_code_otel"

# Where Claude Code reads MANAGED settings, which override the user's file.
# An admin who pinned the OTLP destination there has decided where telemetry
# goes; we refuse rather than write a block the runtime will ignore.
_MANAGED_SETTINGS_PATHS = {
    "Darwin": ["/Library/Application Support/ClaudeCode/managed-settings.json"],
    "Linux": ["/etc/claude-code/managed-settings.json"],
    "Windows": [os.path.join(os.environ.get("ProgramData", r"C:\ProgramData"),
                             "ClaudeCode", "managed-settings.json")],
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
    }


CONTENT_ENV = {
    "OTEL_LOG_USER_PROMPTS": "1",
    "OTEL_LOG_TOOL_DETAILS": "1",
    "OTEL_LOG_TOOL_CONTENT": "1",
}


# ── settings + marker I/O ───────────────────────────────────────────────────

def _read_json(path: str) -> dict:
    try:
        with open(path) as f:
            txt = f.read().strip()
        data = json.loads(txt) if txt else {}
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}


def _write_json(path: str, data: dict) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def _read_marker(marker_path: str | None = None) -> dict:
    data = _read_json(marker_path or _MARKER_PATH)
    m = data.get(_MARKER_KEY)
    return m if isinstance(m, dict) else {}


def _write_marker(entry: dict | None, marker_path: str | None = None) -> None:
    path = marker_path or _MARKER_PATH
    try:
        data = _read_json(path)
        if entry is None:
            data.pop(_MARKER_KEY, None)
        else:
            data[_MARKER_KEY] = entry
        _write_json(path, data)
    except Exception:
        pass


# ── receiver probe + managed lock ───────────────────────────────────────────

def _url_alive(base: str, timeout: float = _PROBE_TIMEOUT_S) -> bool:
    """True when an OTLP receiver answers at ``base`` (its status probe)."""
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


def managed_lock(paths: list | None = None) -> dict | None:
    """The managed settings file, if it pins any OTLP destination key.
    Returns ``{"path", "keys"}`` or ``None``."""
    candidates = paths
    if candidates is None:
        candidates = _MANAGED_SETTINGS_PATHS.get(platform.system(), [])
    for path in candidates:
        try:
            if not os.path.isfile(path):
                continue
            env = _read_json(path).get("env") or {}
            locked = [k for k in _LOCKED_KEYS if k in env]
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
    # Absolute, so the marker written here still resolves from a process
    # with a different cwd (the dashboard answering /api/otel-status).
    path = os.path.abspath(settings_path or _SETTINGS_PATH)
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

        settings = _read_json(path)
        env = settings.get("env")
        created_env = not isinstance(env, dict)
        if created_env:
            env = {}
            settings["env"] = env

        wanted = base_env(target)
        if content:
            wanted.update(CONTENT_ENV)

        prior = _read_marker(marker_path)
        prior_keys = prior.get("keys") or {}
        if prior_keys and os.path.abspath(str(prior.get("settings_path") or "")) == path:
            # A re-run finds the ``env`` object WE created last time; keep
            # remembering that, or uninstall would leave an empty ``env``.
            created_env = bool(prior.get("created_env"))
        written, present, conflicts = {}, [], []
        for k, v in wanted.items():
            cur = env.get(k)
            if cur is None:
                env[k] = v
                written[k] = v
            elif str(cur) == str(v):
                # Either we wrote it before, or the user already had this
                # exact value. Track it as ours only if the marker says so
                # or nobody else could have (a fresh install of the same
                # value is indistinguishable, so we do NOT claim it).
                if k in prior_keys:
                    written[k] = v
                else:
                    present.append(k)
            else:
                if k in prior_keys and str(cur) == str(prior_keys[k]):
                    # Ours from a previous run with a different endpoint /
                    # protocol: update, and keep ownership.
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

        changed = bool(written) or bool(removed)
        # Did anything on disk actually change? Compare against the file.
        before = _read_json(path)
        if before != settings:
            _write_json(path, settings)
            file_changed = True
        else:
            file_changed = False

        _write_marker({
            "settings_path": path,
            "keys": written,
            "created_env": bool(created_env),
            "endpoint": target,
            "content": bool(content),
            "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, marker_path)

        status = "installed" if file_changed else "already_present"
        return {
            "status": status, "path": path, "endpoint": target,
            "receiver_listening": probe.get("listening"),
            "receiver_via": probe.get("via"),
            "written": sorted(written), "present": present,
            "removed": removed, "conflicts": conflicts,
            "content": bool(content), "changed": changed,
            "note": ("Running Claude Code sessions keep their old "
                     "configuration until restarted."),
        }
    except Exception as e:
        return {"status": "error", "path": path, "error": str(e)}


def uninstall(settings_path: str | None = None, *,
              marker_path: str | None = None) -> dict:
    """Remove only the keys we wrote, and only where the value is still ours."""
    prior = _read_marker(marker_path)
    path = os.path.abspath(settings_path or prior.get("settings_path") or _SETTINGS_PATH)
    try:
        keys = prior.get("keys") or {}
        if not keys:
            return {"status": "not_installed", "path": path, "removed": [],
                    "kept": []}
        settings = _read_json(path)
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
        if removed or (isinstance(env, dict) and not env):
            _write_json(path, settings)
        _write_marker(None, marker_path)
        return {"status": "uninstalled", "path": path,
                "removed": sorted(removed), "kept": kept,
                "note": ("Running Claude Code sessions keep exporting until "
                         "restarted.")}
    except Exception as e:
        return {"status": "error", "path": path, "error": str(e)}


def status(settings_path: str | None = None, *, marker_path: str | None = None,
           probe: bool = True) -> dict:
    """What is on disk right now, and whether a receiver is listening."""
    prior = _read_marker(marker_path)
    path = os.path.abspath(settings_path or prior.get("settings_path") or _SETTINGS_PATH)
    env = _read_json(path).get("env") or {}
    ours = prior.get("keys") or {}
    in_place = [k for k, v in ours.items() if str(env.get(k)) == str(v)]
    drifted = [k for k in ours if k in env and str(env[k]) != str(ours[k])]
    missing = [k for k in ours if k not in env]
    configured = bool(ours) and not missing and not drifted
    out = {
        "configured": configured,
        "installed_at": prior.get("installed_at"),
        "settings_path": path if ours else None,
        "endpoint": env.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        if env.get("CLAUDE_CODE_ENABLE_TELEMETRY") else None,
        "telemetry_enabled": str(env.get("CLAUDE_CODE_ENABLE_TELEMETRY")) == "1",
        "protocol": env.get("OTEL_EXPORTER_OTLP_PROTOCOL"),
        "content": any(str(env.get(k)) == "1" for k in CONTENT_ENV),
        "ours": sorted(ours), "in_place": sorted(in_place),
        "drifted": sorted(drifted), "missing": sorted(missing),
    }
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
            "Prompt/tool content stays off unless --content is given.\n")
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
                print("Nothing to remove: clawmetry never wrote a telemetry "
                      "block here.")
            elif res["status"] == "uninstalled":
                print(f"Removed {len(res['removed'])} key(s) from {res['path']}.")
                for k in res.get("kept") or []:
                    print(f"  kept {k['key']} (value changed since we wrote it)")
                print(res["note"])
            else:
                print(f"Error: {res.get('error')}")
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
        print(f"  managed settings: {res.get('managed_path')}")
        print(f"  locked keys:      {', '.join(res.get('locked_keys') or [])}")
        return
    if st == "error":
        print(f"Error: {res.get('error')}")
        return
    verb = "Wrote" if st == "installed" else "Already present in"
    print(f"{verb} {res['path']}")
    print(f"  endpoint: {res['endpoint']}"
          + ("" if res.get("receiver_listening") else
             "  (no receiver answering there right now; start `clawmetry`)"))
    print(f"  protocol: http/json   content: {'ON' if res.get('content') else 'off'}")
    for c in res.get("conflicts") or []:
        print(f"  left alone {c['key']}={c['current']!r} (wanted {c['wanted']!r})")
    for k in res.get("removed") or []:
        print(f"  removed {k} (content flag; pass --content to keep it)")
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
    for k in res.get("drifted") or []:
        print(f"  drifted: {k}")
    for k in res.get("missing") or []:
        print(f"  missing: {k}")
    rc = res.get("receiver") or {}
    if rc:
        print(f"  receiver: {rc['endpoint']} "
              f"{'listening' if rc.get('listening') else 'NOT listening'}")
