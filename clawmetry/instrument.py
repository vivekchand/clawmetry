"""``clawmetry instrument <runtime>`` — switch a runtime's own OpenTelemetry
exporter on and point it at the local ClawMetry receiver (WO-57).

Generic mechanics live here; per-runtime values (which file, which keys,
where managed policy lives) arrive through an ``OtelRuntimeProfile``
registered in ``clawmetry.otel_profiles`` (free runtimes from this repo,
paid runtimes from ``clawmetry-pro`` via the ``clawmetry.extensions`` entry
point, exactly like their transcript adapters).

:class:`JsonEnvBlockInstrumenter` covers every runtime whose exporter is
configured by an ``env`` object in a JSON settings file. Ownership contract
(same spirit as ``hooks_claude_code``): merge into the existing object,
never overwrite a key we did not write, record exactly which keys we wrote
PER FILE in the marker, and on uninstall remove only those keys whose value
is still what we set. A key already present with a different value is a
CONFLICT: reported, left alone. User-level and ``--project`` installs
coexist; each has its own record.

Content flags are OFF unless ``--content`` is passed: the transcript already
holds that text locally, and the default must not widen what leaves the
process. No profile may write raw request/response body flags.

Stdlib-only apart from the plugin load in ``cli_main``.
"""
from __future__ import annotations

import glob
import json
import os
import platform
import sys
import time
import urllib.request
from typing import Callable, Dict, Optional

# Shared with hooks_claude_code; each instrumenter owns one key in it, whose
# value is ``{<settings path>: <record>}``.
_MARKER_PATH = os.path.expanduser("~/.clawmetry/hooks_installed.json")

# The compat listener (#4780) and the dashboard port. Probed in this order.
_COMPAT_PORT = 4318
_DEFAULT_DASHBOARD_PORT = 8900
_PROBE_TIMEOUT_S = 1.0

# Never written by any profile, whatever it asks for.
FORBIDDEN_KEYS = ("OTEL_LOG_RAW_API_BODIES",)


# ── paths, settings + marker I/O ────────────────────────────────────────────

def _norm(path: str) -> str:
    """One canonical key per settings file: absolute, symlinks resolved, so a
    marker written from one cwd resolves from another and a dotfiles symlink
    is written THROUGH rather than replaced."""
    return os.path.realpath(os.path.abspath(os.path.expanduser(path)))


class SettingsUnreadable(ValueError):
    """The file exists but is not a JSON object. Never overwrite such a file."""


def _read_json_strict(path: str) -> dict:
    """``{}`` when absent; raises :class:`SettingsUnreadable` on bad JSON, a
    non-object top level, or an unreadable file."""
    try:
        with open(path) as f:
            txt = f.read().strip()
    except FileNotFoundError:
        return {}
    except OSError as e:
        raise SettingsUnreadable(f"{path}: cannot read ({e.strerror or e})")
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
    # No lock: the runtime rewrites its own settings file, so a save that
    # races this write can be lost. The window is one JSON dump; accepted.
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def _read_marker_all(marker_key: str, marker_path: str | None = None) -> dict:
    """``{settings path: record}`` for every install this instrumenter made."""
    data = _read_json(marker_path or _MARKER_PATH)
    m = data.get(marker_key)
    if not isinstance(m, dict):
        return {}
    return {k: v for k, v in m.items() if isinstance(v, dict) and "keys" in v}


def _read_marker(marker_key: str, path: str, marker_path: str | None = None) -> dict:
    return _read_marker_all(marker_key, marker_path).get(path, {})


def _write_marker(marker_key: str, path: str, entry: dict | None,
                  marker_path: str | None = None) -> bool:
    """True when the ownership record was written. A False from install is
    surfaced: without the record, uninstall cannot know what is ours."""
    mp = marker_path or _MARKER_PATH
    try:
        data = _read_json(mp)
        block = data.get(marker_key)
        if not isinstance(block, dict):
            block = {}
        if entry is None:
            block.pop(path, None)
        else:
            block[path] = entry
        if block:
            data[marker_key] = block
        else:
            data.pop(marker_key, None)
        _write_json(mp, data)
        return True
    except Exception:
        return False


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


def managed_candidates(dirs_by_system: dict, system: str | None = None) -> list:
    """Every managed-settings file a runtime would read on this platform:
    ``managed-settings.json`` plus ``managed-settings.d/*.json`` under each
    directory the profile names for the OS. Only FILE-based policy is
    visible from here; the output says so."""
    out = []
    for d in (dirs_by_system or {}).get(system or platform.system(), []):
        out.append(os.path.join(d, "managed-settings.json"))
        try:
            out.extend(sorted(glob.glob(os.path.join(d, "managed-settings.d", "*.json"))))
        except Exception:
            pass
    return out


def managed_lock(paths: list, locked_keys: tuple) -> dict | None:
    """The managed settings file, if one pins a destination key.
    Returns ``{"path", "keys"}`` or ``None``."""
    for path in paths or []:
        try:
            if not os.path.isfile(path):
                continue
            env = _read_json(path).get("env") or {}
            locked = [k for k in locked_keys if isinstance(env, dict) and k in env]
            if locked:
                return {"path": path, "keys": locked}
        except Exception:
            continue
    return None


# ── the generic instrumenter ────────────────────────────────────────────────

class JsonEnvBlockInstrumenter:
    """Install / uninstall / status for a runtime configured by an ``env``
    object in a JSON settings file.

    Parameters are the whole vendor surface:

    * ``runtime``: ClawMetry runtime id (marker key is ``<runtime>_otel``).
    * ``settings_path`` / ``project_settings_path``: user-level file and the
      cwd-relative project file.
    * ``base_env(endpoint) -> dict``: the block written on every install.
    * ``content_env``: keys added only with ``--content``.
    * ``managed_dirs``: ``{platform.system(): [dir, ...]}`` where the runtime
      reads managed policy; ``locked_keys`` are the destination keys whose
      presence there refuses the install.
    * ``upgrade_hint``: printed when ``allowed`` is False.
    """

    def __init__(self, *, runtime: str, settings_path: str,
                 project_settings_path: str,
                 base_env: Callable[[str], Dict[str, str]],
                 content_env: Optional[Dict[str, str]] = None,
                 managed_dirs: Optional[dict] = None,
                 locked_keys: tuple = ("OTEL_EXPORTER_OTLP_ENDPOINT",
                                       "OTEL_EXPORTER_OTLP_HEADERS",
                                       "OTEL_EXPORTER_OTLP_PROTOCOL"),
                 upgrade_hint: str = "",
                 label: str = ""):
        self.runtime = runtime
        self.label = label or runtime
        self.marker_key = f"{runtime}_otel"
        self.settings_path = settings_path
        self.project_settings_path = project_settings_path
        self._base_env = base_env
        self.content_env = dict(content_env or {})
        self.managed_dirs = dict(managed_dirs or {})
        self.locked_keys = tuple(locked_keys)
        self.upgrade_hint = upgrade_hint

    # -- values -------------------------------------------------------------

    def base_env(self, endpoint: str) -> Dict[str, str]:
        env = {k: str(v) for k, v in self._base_env(endpoint).items()}
        for k in FORBIDDEN_KEYS:
            env.pop(k, None)
        return env

    def managed_candidates(self, system: str | None = None) -> list:
        return managed_candidates(self.managed_dirs, system)

    # -- install ------------------------------------------------------------

    def install(self, settings_path: str | None = None, *, content: bool = False,
                endpoint: str | None = None, probe: dict | None = None,
                managed: dict | None = None, marker_path: str | None = None,
                managed_paths: list | None = None,
                allowed: bool = True) -> dict:
        """Write the ``env`` block. Idempotent; merges; never clobbers.

        ``probe`` / ``managed`` / ``managed_paths`` / ``allowed`` exist so
        tests can inject the receiver answer, the lock state and the
        entitlement without a network, root paths or a licence.
        """
        path = _norm(settings_path or self.settings_path)
        try:
            if not allowed:
                return {"status": "upgrade_required", "path": path,
                        "reason": "runtime_not_entitled", "runtime": self.runtime,
                        "message": self.upgrade_hint or
                        f"{self.label} is a paid runtime on this plan."}
            if managed is not None:
                lock = managed or None
            else:
                lock = managed_lock(
                    self.managed_candidates() if managed_paths is None else managed_paths,
                    self.locked_keys)
            if lock:
                return {"status": "refused", "path": path,
                        "reason": "managed_settings_lock",
                        "managed_path": lock["path"], "locked_keys": lock["keys"],
                        "message": (f"{self.label} managed settings pin the OTLP "
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
                        "message": ("The settings file could not be read as a JSON "
                                    "object; nothing was written. " + str(e))}
            env = settings.get("env")
            if "env" in settings and not isinstance(env, dict):
                return {"status": "refused", "path": path, "reason": "env_not_object",
                        "message": "`env` in the settings file is not an object; not touched."}
            prior = _read_marker(self.marker_key, path, marker_path)
            prior_keys = prior.get("keys") or {}
            created_env = env is None
            if not created_env and prior_keys:
                # The env object exists and we have a record for THIS file:
                # keep remembering whether we created it, or uninstall would
                # leave an empty ``env`` behind.
                created_env = bool(prior.get("created_env"))
            if env is None:
                env = {}
                settings["env"] = env

            wanted = self.base_env(target)
            if content:
                wanted.update({k: str(v) for k, v in self.content_env.items()
                               if k not in FORBIDDEN_KEYS})

            written, present, conflicts = {}, [], []
            for k, v in wanted.items():
                cur = env.get(k)
                if cur is None:
                    env[k] = v
                    written[k] = v
                elif str(cur) == str(v):
                    # Claim it only when our record for this file says so;
                    # a coincidence is not ownership.
                    if k in prior_keys:
                        written[k] = v
                    else:
                        present.append(k)
                else:
                    if k in prior_keys and str(cur) == str(prior_keys[k]):
                        env[k] = v
                        written[k] = v
                    else:
                        conflicts.append({"key": k, "current": cur, "wanted": v})

            removed = []
            if not content:
                for k in self.content_env:
                    if k in prior_keys and str(env.get(k)) == str(prior_keys[k]):
                        env.pop(k, None)
                        removed.append(k)

            before = _read_json(path)
            file_changed = before != settings
            if file_changed:
                _write_json(path, settings)

            marker_written = _write_marker(self.marker_key, path, {
                "keys": written,
                "created_env": bool(created_env),
                "endpoint": target,
                "content": bool(content),
                "installed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }, marker_path)

            return {
                "status": "installed" if file_changed else "already_present",
                "runtime": self.runtime, "marker_written": marker_written,
                "path": path, "endpoint": target,
                "receiver_listening": probe.get("listening"),
                "receiver_via": probe.get("via"),
                "written": sorted(written), "present": present,
                "removed": removed, "conflicts": conflicts,
                "content": bool(content), "changed": bool(written or removed),
                "managed_checked": "file-based managed settings only",
                "note": (f"Running {self.label} sessions keep their old "
                         "configuration until restarted."),
            }
        except Exception as e:
            return {"status": "error", "path": path, "error": str(e)}

    # -- uninstall ----------------------------------------------------------

    def uninstall(self, settings_path: str | None = None, *,
                  marker_path: str | None = None) -> dict:
        """Remove only the keys we wrote to THIS file, and only where the
        value is still ours. ``not_installed`` for a file we have no record
        of. Never asks for an entitlement: removing our own keys must always
        be possible."""
        path = _norm(settings_path or self.settings_path)
        try:
            prior = _read_marker(self.marker_key, path, marker_path)
            keys = prior.get("keys") or {}
            if not keys:
                others = sorted(p for p in _read_marker_all(self.marker_key, marker_path)
                                if p != path)
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
            _write_marker(self.marker_key, path, None, marker_path)
            return {"status": "uninstalled", "path": path,
                    "removed": sorted(removed), "kept": kept,
                    "note": (f"Running {self.label} sessions keep exporting "
                             "until restarted.")}
        except Exception as e:
            return {"status": "error", "path": path, "error": str(e)}

    # -- status -------------------------------------------------------------

    def _status_for(self, path: str, marker: dict) -> dict:
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
        # "telemetry on" = the first key of the base block is set to its value.
        first = next(iter(self.base_env("http://127.0.0.1:0")), None)
        enabled = bool(first) and str(env.get(first)) == str(self.base_env("x")[first])
        return {
            "runtime": self.runtime,
            "settings_path": path,
            "configured": bool(ours) and not missing and not drifted,
            "installed_at": (marker.get(path) or {}).get("installed_at"),
            "telemetry_enabled": enabled,
            "endpoint": env.get("OTEL_EXPORTER_OTLP_ENDPOINT") if enabled else None,
            "protocol": env.get("OTEL_EXPORTER_OTLP_PROTOCOL") if enabled else None,
            "content": any(str(env.get(k)) == str(v) for k, v in self.content_env.items()),
            "ours": sorted(ours), "in_place": sorted(in_place),
            "drifted": sorted(drifted), "missing": sorted(missing),
            "unreadable": unreadable,
        }

    def status(self, settings_path: str | None = None, *,
               marker_path: str | None = None, probe: bool = True) -> dict:
        """What is on disk right now. With no path: the user-level file
        first, then every project file we have a record of. ``configured``
        is true when ANY recorded install is intact; the top-level fields
        describe the first intact one (user level wins)."""
        marker = _read_marker_all(self.marker_key, marker_path)
        if settings_path:
            paths = [_norm(settings_path)]
        else:
            user = _norm(self.settings_path)
            paths = [user] + sorted(p for p in marker if p != user)
        installs = [self._status_for(p, marker) for p in paths]
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


# ── profile lookup + entitlement ────────────────────────────────────────────

def _load_profiles() -> None:
    """Plugins register their profiles at load; the CLI fast path has not
    loaded them yet. Never raises."""
    try:
        from clawmetry import extensions
        extensions.load_plugins()
    except Exception:
        pass


def resolve(runtime: str):
    """The registered profile for a CLI target (id or alias), or ``None``."""
    from clawmetry import otel_profiles
    prof = otel_profiles.by_runtime(runtime)
    if prof is None:
        _load_profiles()
        prof = otel_profiles.by_runtime(runtime)
    return prof


def runtime_allowed(runtime: str) -> bool:
    """The runtime entitlement (grace-permissive). Fails closed."""
    try:
        from clawmetry.entitlements import get_entitlement
        return bool(get_entitlement().allows_runtime(runtime))
    except Exception:
        return False


def status_all(*, probe: bool = False) -> dict:
    """``{runtime: status}`` for every registered profile with an
    instrumenter. Used by ``clawmetry status`` and ``/api/otel-status``."""
    from clawmetry import otel_profiles
    _load_profiles()
    out = {}
    for prof in otel_profiles.all_profiles():
        inst = prof.instrumenter
        if inst is None:
            continue
        try:
            st = inst.status(probe=probe)
            st["entitled"] = runtime_allowed(prof.runtime)
            st["label"] = prof.label or prof.runtime
            out[prof.runtime] = st
        except Exception as e:
            out[prof.runtime] = {"runtime": prof.runtime, "error": str(e)}
    return out


# ── CLI ─────────────────────────────────────────────────────────────────────

_USAGE = ("usage: clawmetry instrument <runtime> [--project] [--content] "
          "[--endpoint URL] [--uninstall | --status] [--json]\n")


def cli_main(argv: list | None = None) -> int:
    argv = list(sys.argv[2:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        sys.stdout.write(_USAGE)
        _load_profiles()
        from clawmetry import otel_profiles
        names = sorted(p.runtime for p in otel_profiles.all_profiles() if p.instrumenter)
        sys.stdout.write(
            "\nTurns on a runtime's own OpenTelemetry exporter and points it at\n"
            "the local ClawMetry receiver by writing its settings file (or the\n"
            "project-level file with --project). Prompt/tool content stays off\n"
            "unless --content is given; with it, that text also lands in the\n"
            "local events table.\n"
            f"\nRuntimes available here: {', '.join(names) or '(none)'}\n"
            "Paid runtimes appear once the clawmetry-pro wheel is installed.\n")
        return 0
    target = argv[0]
    prof = resolve(target)
    if prof is None or prof.instrumenter is None:
        sys.stderr.write(
            f"clawmetry instrument: no exporter profile for {target!r}. Paid "
            "runtimes need the clawmetry-pro wheel (run `clawmetry license`); "
            "run `clawmetry instrument --help` to list what is available.\n")
        return 2
    inst = prof.instrumenter
    flags = argv[1:]
    as_json = "--json" in flags
    path = inst.project_settings_path if "--project" in flags else None
    endpoint = None
    if "--endpoint" in flags:
        try:
            endpoint = flags[flags.index("--endpoint") + 1]
        except IndexError:
            sys.stderr.write("--endpoint needs a URL\n")
            return 2

    if "--status" in flags:
        res = inst.status(path)
        res["entitled"] = runtime_allowed(prof.runtime)
        if as_json:
            print(json.dumps(res, indent=2))
        else:
            _print_status(prof.label or prof.runtime, res)
        return 0
    if "--uninstall" in flags:
        res = inst.uninstall(path)
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

    res = inst.install(path, content="--content" in flags, endpoint=endpoint,
                       allowed=runtime_allowed(prof.runtime))
    if as_json:
        print(json.dumps(res, indent=2))
    else:
        _print_install(res)
    return 0 if res["status"] in ("installed", "already_present") else 1


def _print_install(res: dict) -> None:
    st = res.get("status")
    if st == "upgrade_required":
        print("Not available on this plan: " + res.get("message", ""))
        return
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
    print(f"  content: {'ON' if res.get('content') else 'off'}")
    for c in res.get("conflicts") or []:
        print(f"  left alone {c['key']}={c['current']!r} (wanted {c['wanted']!r})")
    for k in res.get("removed") or []:
        print(f"  removed {k} (content flag; pass --content to keep it)")
    if res.get("marker_written") is False:
        print(f"  WARNING: could not record what was written (is "
              f"{os.path.dirname(_MARKER_PATH)} writable?); --uninstall "
              f"will not know these keys are ours")
    print("  checked: file-based managed settings only (plist, registry and "
          "server-managed policy are not visible from here)")
    print(res["note"])


def _print_status(label: str, res: dict) -> None:
    if res.get("configured"):
        print(f"{label} telemetry: configured ({res['settings_path']})")
    elif res.get("telemetry_enabled"):
        print(f"{label} telemetry: enabled, but not by clawmetry (or the block drifted)")
    elif res.get("entitled") is False:
        print(f"{label} telemetry: not available on this plan "
              "(paid runtime; see clawmetry.com/pricing)")
    else:
        print(f"{label} telemetry: not configured "
              f"(run `clawmetry instrument {res.get('runtime') or label}`)")
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
