"""Bounded polling observations. Private fingerprints never enter public payloads."""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import logging
import math
import os
import platform
import selectors
import socket
import stat
import subprocess
import time
import weakref
from pathlib import Path

log = logging.getLogger("clawmetry.node_activity")
DEFAULT_PREFERENCES = {"enabled": True, "processes": True, "listeners": True,
                       "sensitive_files": True, "rule_new_listener": True,
                       "rule_sensitive_change": True}
MAX_PROCESSES = 512
MAX_PROCESS_CANDIDATES = 4096
MAX_LISTENERS = 256
MAX_LOGINS = 64
MAX_FILE_BYTES = 1024 * 1024
UNKNOWN_ACTOR = {"kind": "unknown", "label": "Unattributed"}
_CPU_WARMED = weakref.WeakSet()
_PROCESS_CPU_SAMPLES = weakref.WeakKeyDictionary()
MAX_LSOF_BYTES = 256 * 1024
LSOF_TIMEOUT_SECONDS = 0.75
SUMMARY_KEYS = ("cpu_percent", "memory_used_bytes", "memory_total_bytes",
                "process_count", "listening_port_count")


def clean(value, limit=100):
    return " ".join("".join(c for c in str(value or "") if c.isprintable()).split())[:limit]


def number(value, integer=False):
    try:
        out = float(value)
        return (int(out) if integer else out) if math.isfinite(out) and out >= 0 else None
    except (ValueError, TypeError, OverflowError):
        return None


def identity(*values):
    return hashlib.sha256("\0".join(str(v) for v in values).encode()).hexdigest()[:32]


def validate_preferences(value):
    if (not isinstance(value, dict) or not value or
            set(value) - set(DEFAULT_PREFERENCES) or
            any(type(v) is not bool for v in value.values())):
        raise ValueError("Choose known monitoring options and use on or off.")
    return dict(value)


def unavailable(reason="No stored observations are available."):
    return {"schema_version": 1, "available": False, "reason": reason, "scope": "node",
            "node": {"id": "", "hostname": "", "platform": ""}, "collected_at": None,
            "stale_after_seconds": 120, "summary": dict.fromkeys(SUMMARY_KEYS),
            "samples": [], "processes": [], "listeners": [], "sensitive_files": [],
            "logins": [], "events": [], "coverage": {},
            "preferences": dict(DEFAULT_PREFERENCES), "truncated": False,
            "retention": {"hours": 24, "event_limit": 2000, "sample_limit": 120}}


def _namespace():
    """Describe only the namespace visible to this daemon, never promise host access."""
    scope = "unknown"
    tokens = []
    if platform.system() == "Linux":
        try:
            tokens = [os.readlink("/proc/self/ns/" + name) for name in ("pid", "net", "mnt")]
        except OSError:
            pass
        if Path("/.dockerenv").exists() or Path("/run/.containerenv").exists():
            scope = "container"
    uid = os.geteuid() if hasattr(os, "geteuid") else "account"
    return scope, identity(platform.node(), uid, *tokens)


def _coverage(source, scope, now, state="complete", reason="", count=0, truncated=False):
    return {"source": source, "state": state, "method": "polling", "scope": scope,
            "observed_at": now, "reason": reason or "Limited to this account and visible namespace.",
            "count": count, "truncated": truncated}


def _process_cpu(counters, previous, measured_at):
    """One core is 100%; cumulative inputs remain only in daemon memory."""
    user = number(getattr(counters, "user", None))
    system = number(getattr(counters, "system", None))
    result = {"cpu_percent": None, "cpu_interval_seconds": None,
              "cpu_reason": "CPU starts after the next measurement."}
    if user is None or system is None:
        result["cpu_reason"] = "CPU counters are unavailable for this process."
        return result, None
    current = (user, system, measured_at)
    if previous is not None:
        elapsed = measured_at - previous[2]
        if not 0.1 <= elapsed <= 120:
            result["cpu_reason"] = "Waiting for a new CPU sample after a collection delay."
        elif user < previous[0] or system < previous[1]:
            result["cpu_reason"] = "CPU counters changed; a new interval is needed."
        else:
            measured = number(100 * ((user - previous[0]) + (system - previous[1])) / elapsed)
            if measured is not None:
                result.update(cpu_percent=measured, cpu_interval_seconds=elapsed, cpu_reason="")
    return result, current


def _clawmetry_launch_role(argv, cwd=None):
    """Recognize entry points, never arbitrary argument substrings.

    Arguments stay transient: only the fixed role is persisted. psutil supplies
    this metadata on Linux, macOS and Windows; denial means unknown software.
    """
    if not isinstance(argv, (list, tuple)) or not argv or len(argv) > 256:
        return None
    if any(not isinstance(arg, str) for arg in argv):
        return None
    def basename(value):
        return value.replace("\\", "/").rsplit("/", 1)[-1].lower()
    args = list(argv)
    executable = basename(args.pop(0))
    if executable in ("clawmetry", "clawmetry.exe"):
        pass
    elif executable.startswith("python"):
        while args and args[0] in ("-u", "-B", "-E", "-s", "-S", "-I", "-O", "-OO"):
            args.pop(0)
        if len(args) >= 2 and args[0] == "-m":
            module = args[1]
            args = args[2:]
            if module == "clawmetry.sync":
                return "collector"
            if module not in ("clawmetry", "clawmetry.cli"):
                return None
        elif args and basename(args[0]) in ("clawmetry", "clawmetry.exe"):
            args.pop(0)
        elif args:
            # Only this installation's scripts, never an unrelated dashboard.py.
            script = args.pop(0)
            root = Path(__file__).resolve().parent
            if os.path.isabs(script) or cwd:
                path = (Path(cwd) / script if cwd else Path(script)).resolve()
                if path == root / "sync.py":
                    return "collector"
                if path == root.parent / "dashboard.py":
                    return "dashboard"
                if path == root.parent / "desktop" / "app.py":
                    return "desktop"
            return None
        else:
            return None
    else:
        return None
    return "collector" if args and args[0] == "sync" else "cli" if args and not args[0].startswith("-") else "dashboard"


def _process_role(proc, info):
    if info.get("pid") == os.getpid():
        return "collector"
    name = str(info.get("name") or "").lower()
    if not name.startswith(("python", "clawmetry")):
        return None
    try:
        argv = proc.cmdline()
        role = _clawmetry_launch_role(argv)
        return role or _clawmetry_launch_role(argv, cwd=proc.cwd())
    except Exception:  # noqa: BLE001 - optional platform metadata must not discard a process
        # AccessDenied/NoSuchProcess must not discard readable resource data.
        return None


def _read_lsof(deadline):
    """Read a fixed local command with bounded memory and lifetime, without a shell."""
    deadline = min(deadline, time.monotonic() + LSOF_TIMEOUT_SECONDS)
    if deadline <= time.monotonic():
        raise TimeoutError()
    child = subprocess.Popen(
        ["/usr/sbin/lsof", "-nP", "-a", "-iTCP", "-sTCP:LISTEN", "-F0pftnT"],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        shell=False, env={"LC_ALL": "C"},
    )
    data, limited = bytearray(), False
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    limited = True
                    break
                chunk = os.read(child.stdout.fileno(), min(16384, MAX_LSOF_BYTES + 1 - len(data)))
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > MAX_LSOF_BYTES:
                    del data[MAX_LSOF_BYTES:]
                    limited = True
                    break
        if not limited:
            try:
                code = child.wait(timeout=max(0.001, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                limited = True
            else:
                # lsof also returns one when no selected files were found.
                if code not in (0, 1):
                    raise OSError("Listener command failed")
        return bytes(data), limited
    finally:
        if child.poll() is None:
            child.kill()  # Only the subprocess created above, never an observed process.
            try:
                child.wait(timeout=0.1)
            except subprocess.TimeoutExpired:
                log.warning("Node listener helper did not exit within its cleanup budget")
        child.stdout.close()


def _lsof_listeners(data, source_identity, cap):
    """NUL fields, newline-delimited process/file sets; accept complete TCP sets only."""
    rows, seen, pid, malformed, truncated = [], set(), None, False, False
    for line in data.splitlines(keepends=True):
        if not line.endswith(b"\0\n"):
            malformed = True
            pid = None
            continue
        fields = [item for item in line[:-1].split(b"\0") if item]
        if not fields:
            continue
        if fields[0].startswith(b"p"):
            value = fields[0][1:]
            pid = int(value) if len(fields) == 1 and value.isdigit() and len(value) <= 12 else None
            malformed |= not pid
            continue
        if not fields[0].startswith(b"f"):
            pid, malformed = None, True
            continue
        values = {}
        duplicate = False
        for field in fields:
            if field[:1] == b"T" and not field.startswith(b"TST="):
                continue
            if field[:1] in values:
                duplicate = True
            values[field[:1]] = field[1:]
        try:
            if (duplicate or not pid or not values.get(b"f", b"").isdigit() or
                    values.get(b"t") not in (b"IPv4", b"IPv6") or
                    values.get(b"T") != b"ST=LISTEN"):
                raise ValueError()
            endpoint = values[b"n"].decode("ascii")
            address, port_text = endpoint.rsplit(":", 1)
            if not port_text.isdigit() or len(port_text) > 5 or not 0 < int(port_text) <= 65535:
                raise ValueError()
            if address.startswith("[") and address.endswith("]") and values[b"t"] == b"IPv6":
                address = address[1:-1]
            elif "[" in address or "]" in address or (values[b"t"] == b"IPv6" and address != "*"):
                raise ValueError()
            exposure = "unknown"
            if address != "*":
                parsed = ipaddress.ip_address(address)
                if parsed.version != (4 if values[b"t"] == b"IPv4" else 6):
                    raise ValueError()
                exposure = "loopback" if parsed.is_loopback else "nonloopback"
            key = identity(source_identity, address, int(port_text), pid, "tcp", values[b"t"])
            if key in seen:
                continue
            if len(rows) >= cap:
                truncated = True
                break
            seen.add(key)
            rows.append({"id": key, "pid": pid, "process_id": None,
                         "address": clean(address), "port": int(port_text), "protocol": "tcp",
                         "exposure": exposure, "actor": dict(UNKNOWN_ACTOR)})
        except (ValueError, KeyError, UnicodeError):
            malformed = True
    return rows, malformed, truncated


def collect_node_activity(*, preferences=None, node_id="", now=None, psutil_module=None,
                          fingerprint_key=None, home=None, budget_seconds=3.0, resources_only=False):
    """Return public metadata plus private source state for the daemon writer.

    No command line, environment, file content or file digest is public. Polling
    misses short-lived activity. psutil calls themselves cannot be interrupted;
    iteration and file work stop at the shared budget.
    """
    now = int((time.time() if now is None else now) * 1000)
    prefs = dict(DEFAULT_PREFERENCES)
    prefs.update(preferences or {})
    public = unavailable()
    public.update(available=True, reason="", collected_at=now, preferences=prefs,
                  node={"id": clean(node_id, 256), "hostname": clean(platform.node()),
                        "platform": platform.system()})
    out = {"public": public, "sources": {}}
    if not prefs["enabled"]:
        _PROCESS_CPU_SAMPLES.clear()
        for source in ("resources", "processes", "listeners", "logins", "sensitive_files"):
            public["coverage"][source] = _coverage(source, "unknown", now, "disabled", "Monitoring is disabled.")
            out["sources"][source] = {"identity": "disabled", "rows": []}
        return out
    scope, namespace = _namespace()
    deadline = time.monotonic() + max(0.01, budget_seconds)
    try:
        if psutil_module is None:
            import psutil as psutil_module
        sensor = psutil_module
        try:
            boot = sensor.boot_time()
        except Exception:
            boot = "unknown"
    except Exception as exc:
        sensor, boot = None, "unknown"
        log.warning("Node polling library unavailable: %s", type(exc).__name__)
    source_identity = identity(node_id, namespace, boot)
    if sensor is None or not prefs["processes"]:
        _PROCESS_CPU_SAMPLES.clear()

    def save(name, rows, state="complete", reason="", truncated=False):
        public["coverage"][name] = _coverage(name, scope, now, state, reason, len(rows), truncated)
        out["sources"][name] = {"identity": source_identity, "rows": rows}
        public["truncated"] |= truncated

    enabled = prefs["enabled"]
    # Resources are measurements, not entity differences.
    if enabled and sensor is not None:
        failures = []
        try:
            measured = number(sensor.cpu_percent(interval=None))
            if sensor in _CPU_WARMED:
                public["summary"]["cpu_percent"] = measured
            else:
                _CPU_WARMED.add(sensor)
                failures.append("CPU warm-up")
        except Exception:
            failures.append("CPU")
        try:
            mem = sensor.virtual_memory()
            public["summary"].update(memory_used_bytes=number(mem.used, True),
                                     memory_total_bytes=number(mem.total, True))
        except Exception:
            failures.append("memory")
        save("resources", [], "partial" if failures else "complete",
             "CPU needs a second observation." if failures == ["CPU warm-up"] else
             "Some resource measurements are unavailable." if failures else "")
    else:
        save("resources", [], "disabled" if not enabled else "unavailable")

    pid_ids = {}
    for source, cap in (("processes", MAX_PROCESSES), ("listeners", MAX_LISTENERS),
                        ("logins", MAX_LOGINS)):
        if (resources_only and source != "processes") or not enabled or (source != "logins" and not prefs[source]):
            save(source, [], "disabled")
            continue
        if sensor is None:
            save(source, [], "unavailable", "The host polling library is unavailable.")
            continue
        rows, partial, truncated = [], False, False
        try:
            if source == "processes":
                # psutil retains Process objects and their cached creation
                # times across iterations. Refresh before checking PID reuse.
                process_iter = sensor.process_iter
                clear_cache = getattr(process_iter, "cache_clear", None)
                if callable(clear_cache):
                    clear_cache()
                cpu_state = _PROCESS_CPU_SAMPLES.get(sensor, {})
                previous_cpu = cpu_state.get("samples", {}) if cpu_state.get("source") == source_identity else {}
                current_cpu = {}
                process_deadline = min(deadline - 0.75, time.monotonic() + 1.5)
                attrs = ["pid", "ppid", "name", "create_time", "memory_info", "cpu_times"]
                # Sample our own PID before a large/partial enumeration. Retain
                # it within the same cap and CPU sampler, not in a new poller.
                def candidates_iter(attrs=attrs, process_iter=process_iter):
                    nonlocal partial
                    try:
                        own = sensor.Process(os.getpid())
                        yield own, own.as_dict(attrs=attrs, ad_value=None)
                    except Exception as exc:  # noqa: BLE001 - enumeration may still provide our PID
                        log.debug("Node collector process lookup unavailable: %s", type(exc).__name__)
                    try:
                        for process in process_iter(attrs, ad_value=None):
                            yield process, None
                    except Exception as exc:  # noqa: BLE001 - preserve positive evidence after a failed scan
                        partial = True
                        log.debug("Node process enumeration incomplete: %s", type(exc).__name__)
                candidates, seen = 0, set()
                for proc, info in candidates_iter():
                    if cap <= 0 or candidates >= MAX_PROCESS_CANDIDATES or time.monotonic() > process_deadline:
                        truncated = True
                        break
                    candidates += 1
                    try:
                        if info is None:
                            info = proc.info
                        started = number(info.get("create_time"))
                        if started is None or not info.get("pid"):
                            partial = True
                            continue
                        pid = int(info["pid"])
                        key = identity(source_identity, pid, started)
                        if key in seen:
                            continue
                        seen.add(key)
                        pid_ids[pid] = key
                        mem = info.get("memory_info")
                        cpu, sample = _process_cpu(info.get("cpu_times"), previous_cpu.get(key), time.monotonic())
                        if sample is not None:
                            current_cpu[key] = sample
                        row = {"id": key, "pid": pid, "parent_pid": info.get("ppid"),
                                     "name": clean(info.get("name")) or "Process name unavailable",
                                     "started_at": int(started * 1000), **cpu,
                                     "memory_bytes": number(getattr(mem, "rss", None), True),
                                     "actor": dict(UNKNOWN_ACTOR)}
                        role = _process_role(proc, info)
                        if role:
                            row["clawmetry_role"] = role
                        rows.append(row)
                        partial |= info.get("ppid") is None or info.get("name") is None
                    except Exception:
                        partial = True
                # Prefer recent processes with measurable memory. A cap on
                # ascending PID enumeration would hide the user's new work.
                rows.sort(key=lambda row: (row.get("clawmetry_role") == "collector",
                                           bool(row.get("clawmetry_role")),
                                           row["memory_bytes"] is not None, row["started_at"]), reverse=True)
                truncated |= len(rows) > cap
                rows = rows[:cap]
                _PROCESS_CPU_SAMPLES[sensor] = {"source": source_identity,
                                               "samples": {row["id"]: current_cpu[row["id"]]
                                                           for row in rows if row["id"] in current_cpu}}
                pid_ids = {row["pid"]: row["id"] for row in rows}
                public["processes"] = rows
                public["summary"]["process_count"] = len(rows) if not (partial or truncated) else None
            elif source == "listeners":
                if time.monotonic() > deadline - 0.35:
                    raise TimeoutError()
                for conn in sensor.net_connections(kind="inet"):
                    if conn.type != socket.SOCK_STREAM or conn.status != "LISTEN":
                        continue
                    if len(rows) >= cap or time.monotonic() > deadline - 0.35:
                        truncated = True
                        break
                    address, port = conn.laddr[0], int(conn.laddr[1])
                    try:
                        exposure = "loopback" if ipaddress.ip_address(address).is_loopback else "nonloopback"
                    except ValueError:
                        exposure = "unknown"
                    # A listener is the observed endpoint and reported owner PID.
                    # Optional verified process enrichment must not change its ID.
                    owner = pid_ids.get(conn.pid)
                    key = identity(source_identity, address, port, conn.pid, "tcp")
                    rows.append({"id": key, "process_id": owner, "pid": conn.pid,
                                 "address": clean(address), "port": port, "protocol": "tcp",
                                 "exposure": exposure, "actor": dict(UNKNOWN_ACTOR)})
                public["listeners"] = rows
                # Linux may silently omit sockets inaccessible to this account.
                partial = platform.system() == "Linux" and hasattr(os, "geteuid") and os.geteuid() != 0
                public["summary"]["listening_port_count"] = len(rows) if not (partial or truncated) else None
            else:
                if time.monotonic() > deadline - 0.35:
                    raise TimeoutError()
                for login in sensor.users():
                    if len(rows) >= cap:
                        truncated = True
                        break
                    rows.append({"id": identity(source_identity, login.name, login.terminal, login.started),
                                 "account": clean(login.name), "terminal": clean(login.terminal),
                                 "started_at": int(login.started * 1000),
                                 "actor": dict(UNKNOWN_ACTOR)})
                public["logins"] = rows
            save(source, rows, "partial" if partial or truncated else "complete",
                 "Only accessible sockets are shown. Other sockets may be omitted for this account."
                 if source == "listeners" and partial else
                 "Some records may be inaccessible or outside the scan budget." if partial or truncated else "", truncated)
        except Exception as exc:
            if source == "processes":
                _PROCESS_CPU_SAMPLES.pop(sensor, None)
            if (source == "listeners" and platform.system() == "Darwin" and
                    (isinstance(exc, (PermissionError, NotImplementedError)) or type(exc).__name__ == "AccessDenied")):
                listener_identity = identity(source_identity, "lsof_tcp_listen")
                try:
                    data, limited = _read_lsof(deadline - 0.35)
                    rows, malformed, row_limit = _lsof_listeners(data, listener_identity, cap)
                    limited |= row_limit
                    public["listeners"] = rows
                    save(source, rows, "partial" if rows or not limited else "unavailable",
                         "Only accessible TCP listeners are shown using lsof; other listeners may be omitted."
                         + (" The scan was interrupted or bounded." if limited else "")
                         + (" Some records could not be parsed." if malformed else ""), limited)
                except Exception as fallback_error:
                    save(source, [], "unavailable", "Accessible TCP listeners could not be read using lsof: "
                         + ("the tool is unavailable." if isinstance(fallback_error, FileNotFoundError) else
                            "the scan budget was exhausted." if isinstance(fallback_error, TimeoutError) else
                            "permission or collection failed."))
                    log.warning("Node listener fallback unavailable: %s", type(fallback_error).__name__)
                public["coverage"][source]["method"] = "lsof_polling"
                out["sources"][source]["identity"] = listener_identity
            else:
                save(source, rows, "unsupported" if isinstance(exc, NotImplementedError)
                     else "partial" if rows else "unavailable",
                     "This source is not supported on this platform." if isinstance(exc, NotImplementedError)
                     else "Permission denied." if type(exc).__name__ in ("AccessDenied", "PermissionError")
                     else "The source could not be read within this scan.")
            log.debug("Node %s scan incomplete: %s", source, type(exc).__name__)

    if resources_only or not enabled or not prefs["sensitive_files"]:
        save("sensitive_files", [], "disabled")
    elif not fingerprint_key:
        save("sensitive_files", [], "unavailable", "The private comparison key is unavailable.")
    else:
        root = Path(home) if home else Path.home()
        specs = (("ssh_authorized_keys", root / ".ssh/authorized_keys", "SSH authorized keys"),
                 ("ssh_config", root / ".ssh/config", "SSH settings"),
                 ("claude_settings", root / ".claude/settings.json", "Claude Code settings"),
                 ("codex_config", root / ".codex/config.toml", "Codex settings"),
                 ("openclaw_config", root / ".openclaw/openclaw.json", "OpenClaw settings"))
        rows, partial = [], False
        for key, path, label in specs:
            if time.monotonic() > deadline:
                partial = True
                break
            row = {"id": key, "label": label, "present": False, "permissions": None}
            try:
                meta = path.lstat()
                if not stat.S_ISREG(meta.st_mode) or meta.st_size > MAX_FILE_BYTES:
                    partial = True
                    continue
                # Do not follow links to arbitrary files; recheck after opening.
                fd = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
                with os.fdopen(fd, "rb") as handle:
                    current = os.fstat(handle.fileno())
                    if (current.st_ino, current.st_dev) != (meta.st_ino, meta.st_dev):
                        partial = True
                        continue
                    data = handle.read(MAX_FILE_BYTES + 1)
                    after = os.fstat(handle.fileno())
                if len(data) > MAX_FILE_BYTES or (current.st_size, current.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    partial = True
                    continue
                row.update(present=True, permissions=oct(stat.S_IMODE(meta.st_mode)),
                           _fingerprint=hmac.new(fingerprint_key, data, hashlib.sha256).hexdigest())
            except FileNotFoundError:
                pass
            except OSError:
                partial = True
                continue
            rows.append(row)
        public["sensitive_files"] = [{k: v for k, v in row.items() if not k.startswith("_")} for row in rows]
        save("sensitive_files", rows, "partial" if partial else "complete",
             "Some selected files could not be compared." if partial else "Selected settings only. Contents and fingerprints are private.")
        out["sources"]["sensitive_files"]["identity"] = identity(source_identity, os.path.abspath(str(root)), fingerprint_key.hex())
    return out
