"""Field-failure reports from the sync daemon.

Requirement: Daemon Field-Failure Reporting (AC-FFR-005), a child of Field
Failure Reporting and Auto-Triage, whose pipeline this joins as its second
producer.

We already run this loop end to end for ONE class of failure. The desktop
shell classifies a bootstrap that never completed, posts an aggregate ping,
the cloud sink counts signatures at ``/api/desktop/_failures``, and
``field-failure-issues.yml`` files one deduped GitHub issue per signature for
the hourly fixer routine to pick up. It works: a Windows machine on a blocked
index showed up as ``no_distribution / Windows / 3.11`` without anybody
reporting it.

That pipeline had exactly one producer, and it was the installer. The daemon,
which runs on every node and is the single point of failure for all of a
customer's data, reported nothing at all when it could not run.

Burned 2026-09-08: a Pro node's daemon was locked out of its own pid lock and
retried every 30 seconds for twelve hours. It exited 0 each time, so launchd
recorded successes; the DuckDB error handler and the auto-updater both
initialise AFTER the lock is claimed, so neither ever ran; and with no daemon
there was no heartbeat, so the node simply went quiet, and quiet is not an
event. The failure existed in one place on Earth: a log file on the customer's
laptop. He mailed us a screenshot. That is the monitoring system we shipped.

This module is the daemon's producer for that same pipeline.

**Privacy contract, identical to the shell's** (AC-FFR-001.1): a closed dict
of aggregate facts, the failure family, the platform, the interpreter and the
version that failed. No paths, no usernames, no hostnames, no node id, no log
text, ever. The diagnostics stay in ``sync.log`` on the machine. The payload
builder is pure so the contract is testable key by key.

**Same opt-outs as every other ping** (``CLAWMETRY_NO_TELEMETRY``,
``DO_NOT_TRACK``, ``~/.clawmetry/notelemetry``) and the same egress gate every
other discretionary call honours, ``endpoints.egress_suppressed()``. That gate,
not the narrower ``is_custom_endpoint()``, is the one that matters here: an
air-gapped node (``CLAWMETRY_OFFLINE=1``) and a self-hosted server (which IS
the endpoint, so it never sets ``CLAWMETRY_ENDPOINT``) must both send nothing,
and a report about a broken daemon is exactly the kind of well-meant call that
gets shipped past an air gap.
"""
from __future__ import annotations

import json
import logging
import os
import platform
import threading
import time
from pathlib import Path

log = logging.getLogger("clawmetry-sync")

# The closed enum, mirrored by ``_FAILURE_CLASSES`` in the cloud sink
# (clawmetry-cloud ``routes/desktop.py``). A value outside it is coerced to
# "unknown" there, so adding a class here alone loses the signature: both
# repos, or neither.
FAILURE_CLASSES = frozenset({
    # The daemon could not claim its own lock while nothing was ingesting.
    # Not the same as "another instance is running", which is the normal and
    # frequent outcome of a double start.
    "daemon_lock_refused",
    # The daemon is alive and its watchdog thread is scheduling, but no sync
    # cycle has completed in a long time. Our own no-progress detector,
    # pointed at ourselves.
    "daemon_ingest_stalled",
})

# The wire stage. The sink already knows ``shell`` (the app window appeared)
# and ``daemon`` (the daemon came up healthy); this is the third: the daemon
# could not do its job.
STAGE = "daemon_failed"

PING_PATH = "/api/desktop/open"

# One report per class per window. The issue-filing workflow runs every 6
# hours and dedupes to one open issue per signature, so a faster cadence buys
# nothing and a launchd restart loop retrying every 30 seconds would otherwise
# post thousands of times a day.
DEDUPE_SECS = 6 * 3600

# The failing path exits the process immediately after reporting, so the POST
# cannot be handed to a daemon thread: the interpreter would exit before it
# ran, and the report would be as silent as the failure it describes. It is
# sent inline with a short timeout instead.
BLOCKING_TIMEOUT_SEC = 5.0


def _config_dir() -> Path:
    return Path(os.path.expanduser("~/.clawmetry"))


def _dedupe_file(failure_class: str) -> Path:
    safe = "".join(c for c in str(failure_class) if c.isalnum() or c == "_")[:40]
    return _config_dir() / f"field_report_{safe}.stamp"


def _recently_reported(failure_class: str, now: float = None) -> bool:
    """True when this class was reported inside :data:`DEDUPE_SECS`.

    Deliberately a file stamp rather than process state: the restart-loop case
    is a NEW process every 30 seconds, so in-memory throttling would not
    throttle anything.
    """
    try:
        age = (now if now is not None else time.time()) - \
            _dedupe_file(failure_class).stat().st_mtime
        return 0 <= age < DEDUPE_SECS
    except OSError:
        return False


def _stamp_reported(failure_class: str) -> None:
    try:
        f = _dedupe_file(failure_class)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(str(int(time.time())))
    except OSError as e:
        log.debug("field report: stamp not written: %s", e)


def last_sync_age_secs():
    """Seconds since the daemon last COMPLETED a sync cycle, or None.

    None means "no idea", never "fine": a node that has never synced has no
    timestamp, and a fresh install must not be reported as broken.
    """
    try:
        from clawmetry.sync import STATE_FILE

        raw = json.loads(STATE_FILE.read_text()).get("last_sync")
        if not raw:
            return None
        import datetime as _dt

        ts = _dt.datetime.fromisoformat(str(raw).strip().replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=_dt.timezone.utc)
        age = _dt.datetime.now(_dt.timezone.utc).timestamp() - ts.timestamp()
        return age if age >= 0 else None
    except Exception:  # noqa: BLE001 - missing, unreadable, unparseable
        return None


def daemon_failure_payload(failure_class: str, version: str = "") -> dict:
    """The COMPLETE report. Pure, so the privacy contract is testable key by
    key: every value here is an aggregate over a closed enum, a platform name,
    or a version string.

    ``bootstrap_python`` and ``desktop_version`` keep the sink's existing
    column names (the aggregate groups by them) and carry the daemon's own
    interpreter and wheel version, which is exactly the diagnostic those
    columns exist to give.
    """
    fc = str(failure_class or "").strip().lower()[:40]
    if fc not in FAILURE_CLASSES:
        fc = "unknown"
    pyver = platform.python_version()
    return {
        "install_id": _install_id(),
        "stage": STAGE,
        # The sink's event log is keyed UNIQUE (install_id, session_id, stage)
        # with ON CONFLICT DO NOTHING, so a fixed value would record the first
        # daemon failure this install ever had and silently discard every one
        # after it: last_seen would freeze and a second failure class would
        # never appear at all. Derived, coarse and non-identifying, this makes
        # the server-side key "one row per class per install per day", which is
        # real dedupe rather than a permanent mute, and it holds even when the
        # local throttle stamp is gone (a wiped home, a fresh container).
        "session_id": f"{fc}-{time.strftime('%Y%m%d', time.gmtime())}"[:64],
        "failure_class": fc,
        "bootstrap_python": ".".join(pyver.split(".")[:2])[:8],
        "desktop_version": str(version or "")[:32],
        "os": platform.system() or "unknown",
        "os_version": platform.release() or "",
        "arch": platform.machine() or "",
    }


def _install_id() -> str:
    try:
        from clawmetry import telemetry as _t

        return _t._ensure_install_id() or ""
    except Exception:  # noqa: BLE001
        return ""


def _suppressed() -> str:
    """Why we must not send, or "" when we may.

    A custom endpoint is an enterprise deployment: its failures are its own
    and never reach the managed cloud, the same carve-out the desktop ping
    makes.
    """
    try:
        from clawmetry import telemetry as _t

        if _t._is_optout():
            return "telemetry_optout"
    except Exception:  # noqa: BLE001
        return "telemetry_unavailable"
    try:
        from clawmetry.endpoints import egress_suppressed

        if egress_suppressed():
            return "egress_suppressed"
    except Exception:  # noqa: BLE001
        pass
    return ""


def _ping_url() -> str:
    override = os.environ.get("CLAWMETRY_DESKTOP_PING_URL", "").strip()
    if override:
        return override
    try:
        from clawmetry.endpoints import app_url

        base = app_url()
    except Exception:  # noqa: BLE001
        base = "https://app.clawmetry.com"
    return base.rstrip("/") + PING_PATH


def _send(payload: dict) -> None:
    try:
        from clawmetry import telemetry as _t

        _t._post(payload, _ping_url())
    except Exception as e:  # noqa: BLE001 - a report must never raise
        log.debug("field report: post failed: %s", e)


def report_daemon_failure(failure_class: str, version: str = "",
                          blocking: bool = False) -> bool:
    """Report that the daemon could not do its job. Returns whether a report
    was sent.

    Never raises and never blocks for more than
    :data:`BLOCKING_TIMEOUT_SEC`, because every caller is already having a bad
    day. ``blocking`` is for callers that exit immediately afterwards: a
    background thread would be killed by the interpreter shutting down and the
    report would never leave the machine.
    """
    if _suppressed():
        return False
    if _recently_reported(failure_class):
        return False
    payload = daemon_failure_payload(failure_class, version)
    if not payload.get("install_id"):
        return False
    # Stamped before the send, not after: a POST that hangs for its full
    # timeout must not let the next restart 30 seconds later try again.
    _stamp_reported(failure_class)
    log.warning("reporting field failure: %s (aggregate only, no paths or ids)",
                payload["failure_class"])
    if blocking:
        t = threading.Thread(target=_send, args=(payload,), daemon=True,
                             name="clawmetry-field-report")
        t.start()
        t.join(BLOCKING_TIMEOUT_SEC)
        return True
    threading.Thread(target=_send, args=(payload,), daemon=True,
                     name="clawmetry-field-report").start()
    return True
