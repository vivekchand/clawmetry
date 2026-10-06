"""
routes/support.py — "Report a bug" intake for the local dashboard.

The same URL exists on both surfaces so the frontend has ONE code path:

  * localhost  — this module. It collects the environment facts a bug
    report is useless without (version, OS, Python, which runtimes are
    installed, whether the daemon is alive), then forwards the report to
    ClawMetry Cloud over HTTPS and hands back the ticket id.
  * app.clawmetry.com — the cloud serves its own ``/api/bug-report``
    (clawmetry-cloud ``routes/support.py``), which writes the row,
    emails the founder and acknowledges the reporter. The browser code
    cannot tell the difference, and neither can the user.

Why forward rather than file from here: the ticket, the GitHub issue and
the status emails all need credentials that must never ship inside a pip
package. The local dashboard sends a plain POST and stays credential-free.

Nothing is sent until the user presses Send. The report body, the
reporter's email and the diagnostics block are all shown in the dialog
before it goes, because "attached automatically" should never mean
"attached invisibly".

Blueprint: bp_support
"""
from __future__ import annotations

import json
import logging
import os
import platform
import re
import sys
import urllib.error
import urllib.request

from flask import Blueprint, jsonify, request

log = logging.getLogger(__name__)

bp_support = Blueprint("support", __name__)

# Where reports go. Override for a self-hosted intake, or set to an empty
# string to disable the feature entirely on a locked-down install.
CLOUD_INTAKE_URL = os.environ.get(
    "CLAWMETRY_SUPPORT_URL", "https://app.clawmetry.com/api/bug-report"
).strip()

_TIMEOUT = 12

_ALLOWED_SCHEMES = ("https://", "http://")


def _intake_url_ok(url: str) -> bool:
    """True when the configured intake is an http(s) URL.

    CLAWMETRY_SUPPORT_URL is operator-settable and urlopen honours any
    scheme it is handed, so a stray ``file://`` would turn a bug report
    into a local file read. Checked at every use, not just at import,
    because the module constant can be monkeypatched in tests.
    """
    return isinstance(url, str) and url.startswith(_ALLOWED_SCHEMES)

MAX_TITLE = 160
MAX_BODY = 5000
SEVERITIES = ("blocking", "major", "normal", "minor")

# A screenshot rides along as a data URL. The browser already downscales it;
# this is the backstop for a caller that is not our dialog. 2.6 MB of base64
# is ~1.9 MB of image, which is a generous full-window retina screenshot.
MAX_SCREENSHOT_CHARS = 2_600_000
_TICKET_RE = re.compile(r"^CM-[0-9A-HJ-NP-Z]{8}$")

_SCREENSHOT_PREFIX = re.compile(r"^data:image/(png|jpeg|webp);base64,[A-Za-z0-9+/=\s]+$")

# Human sentences for every failure path. The user never sees a status
# code or an exception string (FLYWHEEL: "no raw error string").
ERR_OFFLINE = ("We could not reach ClawMetry just now, so nothing was sent. "
               "Check your connection and press Send again, or email the "
               "report to hello@clawmetry.com.")
ERR_DISABLED = ("Bug reporting is turned off on this install "
                "(CLAWMETRY_SUPPORT_URL is empty). Email hello@clawmetry.com "
                "and we will pick it up there.")
ERR_MISCONFIGURED = ("This install points bug reports somewhere we cannot "
                     "reach (CLAWMETRY_SUPPORT_URL is not an http address), so "
                     "nothing was sent. Email hello@clawmetry.com and we will "
                     "pick it up there.")


def _version() -> str:
    try:
        import dashboard as _d
        return str(getattr(_d, "__version__", "") or "")
    except Exception:
        return ""


def _node_identity() -> dict:
    """node_id / install_id from ~/.clawmetry, when this install has them.

    Both are random ids with no link to a name or an email. They let us
    tie a report to the install's own telemetry and, for a cloud user, to
    the node whose snapshot already shows the symptom.
    """
    out = {"node_id": "", "install_id": "", "cloud_connected": False}
    try:
        cfg_path = os.path.expanduser("~/.clawmetry/config.json")
        with open(cfg_path, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
        if isinstance(cfg, dict):
            out["node_id"] = str(cfg.get("node_id") or "")[:80]
            out["cloud_connected"] = bool(cfg.get("api_key"))
    except Exception:
        pass
    try:
        with open(os.path.expanduser("~/.clawmetry/install_id"), "r",
                  encoding="utf-8") as fh:
            out["install_id"] = fh.read().strip()[:80]
    except Exception:
        pass
    return out


def _runtimes() -> list:
    """Names of the agent runtimes detected on this machine (cheap probe)."""
    try:
        from clawmetry.adapters import registry
        return sorted(
            str(getattr(r, "name", "") or getattr(r, "runtime", ""))
            for r in registry.detect_all()
            if getattr(r, "detected", False)
        )[:40]
    except Exception:
        return []


def _daemon_alive() -> bool:
    """True when the sync daemon answers on its localhost query port.

    "Is the daemon running?" is the first question we ask about half the
    reports we get, so it rides along instead of starting an email thread.
    The daemon writes ~/.clawmetry/local_query.json with its port;
    ``local_server.is_running()`` only knows about its OWN process, so the
    dashboard (a different process) has to probe the socket.
    """
    try:
        from clawmetry.local_server import DISCOVERY_PATH
        with open(DISCOVERY_PATH, "r", encoding="utf-8") as fh:
            port = int((json.load(fh) or {}).get("port") or 0)
    except Exception:
        return False
    if not port:
        return False
    try:
        import socket
        with socket.create_connection(("127.0.0.1", port), timeout=0.4):
            return True
    except Exception:
        return False


def collect_diagnostics(client: dict = None) -> dict:
    """The environment block attached to a report.

    Facts about the machine and the install, never about the work: no
    prompts, no transcripts, no file contents, no paths. The dialog shows
    this verbatim before anything is sent.
    """
    client = client if isinstance(client, dict) else {}
    ident = _node_identity()
    diag = {
        "clawmetry_version": _version(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "runtimes_detected": _runtimes(),
        "daemon_running": _daemon_alive(),
        "cloud_connected": ident["cloud_connected"],
        "surface": "local",
    }
    # Browser-side context the server cannot see.
    for key, limit in (("page", 200), ("tab", 80), ("user_agent", 300),
                       ("viewport", 40), ("locale", 20), ("theme", 20)):
        val = client.get(key)
        if val:
            diag[key] = str(val)[:limit]
    errors = client.get("console_errors")
    if isinstance(errors, list) and errors:
        diag["console_errors"] = [str(e)[:300] for e in errors[:10]]
    return diag


def _post_to_cloud(payload: dict) -> tuple[dict, int]:
    """POST the report to the intake. Returns (body, http_status)."""
    if not _intake_url_ok(CLOUD_INTAKE_URL):
        log.error("[bug-report] refusing a non-http(s) intake URL")
        return {}, 0
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        CLOUD_INTAKE_URL, data=data,
        headers={"Content-Type": "application/json",
                 "User-Agent": f"clawmetry/{_version() or 'dev'}"},
        method="POST")
    try:
        # CLOUD_INTAKE_URL is checked above to be http(s) and is never built
        # from request data.
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # nosec B310
            body = json.loads(resp.read().decode("utf-8") or "{}")
            return (body if isinstance(body, dict) else {}), resp.status
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8") or "{}")
        except Exception:
            body = {}
        return (body if isinstance(body, dict) else {}), int(exc.code or 502)
    except Exception as exc:
        log.warning("[bug-report] forward failed: %s", exc)
        return {}, 0


@bp_support.route("/api/bug-report", methods=["POST"])
def api_bug_report():
    """Take a bug report from the dashboard and forward it to the intake."""
    data = request.get_json(silent=True) or {}
    title = str(data.get("title") or "").strip()[:MAX_TITLE]
    body = str(data.get("body") or data.get("description") or "").strip()[:MAX_BODY]
    if not title:
        return jsonify({"ok": False,
                        "error": "Please add one line saying what went wrong."}), 400

    severity = str(data.get("severity") or "normal").strip().lower()
    if severity not in SEVERITIES:
        severity = "normal"

    if not CLOUD_INTAKE_URL:
        return jsonify({"ok": False, "error": ERR_DISABLED}), 503
    if not _intake_url_ok(CLOUD_INTAKE_URL):
        log.error("[bug-report] CLAWMETRY_SUPPORT_URL is not an http(s) URL")
        return jsonify({"ok": False, "error": ERR_MISCONFIGURED}), 503

    ident = _node_identity()
    payload = {
        "idem_key": str(data.get("idem_key") or "")[:64],
        "title": title,
        "body": body,
        "severity": severity,
        "email": str(data.get("email") or "").strip()[:300],
        "source": "local",
        "surface": str(data.get("surface") or data.get("tab") or "")[:80],
        "version": _version(),
        "runtime": str(data.get("runtime") or "")[:60],
        "platform": platform.platform()[:120],
        "python_version": platform.python_version(),
        "node_id": ident["node_id"],
        "install_id": ident["install_id"],
        "diagnostics": collect_diagnostics(data.get("client")),
    }

    shot = data.get("screenshot")
    if shot:
        shot = str(shot)
        if len(shot) > MAX_SCREENSHOT_CHARS:
            return jsonify({"ok": False,
                            "error": "That screenshot is too large to send. A "
                                     "picture of just the part that is wrong "
                                     "will do."}), 413
        if not _SCREENSHOT_PREFIX.match(shot):
            return jsonify({"ok": False,
                            "error": "We could not read that image. PNG, JPEG "
                                     "or WebP work."}), 400
        payload["screenshot"] = shot
        payload["screenshot_name"] = str(data.get("screenshot_name") or "")[:80]

    body_out, status = _post_to_cloud(payload)
    if status == 0:
        return jsonify({"ok": False, "error": ERR_OFFLINE, "retryable": True}), 503
    if status == 429:
        return jsonify({"ok": False,
                        "error": body_out.get("error")
                        or "That is a lot of reports in one hour. Email "
                           "hello@clawmetry.com and we will pick it up there."}), 429
    if status >= 400 or not body_out.get("ok"):
        return jsonify({"ok": False,
                        "error": body_out.get("error")
                        or "We could not file that just now, so nothing was "
                           "sent. Press Send again in a minute, or email "
                           "hello@clawmetry.com.",
                        "retryable": True}), 502
    return jsonify(body_out)


@bp_support.route("/api/bug-report/<ticket>", methods=["GET"])
def api_bug_report_status(ticket):
    """Look up a ticket's status through the intake, so the local dashboard
    can show "Fixed in 0.12.9xx" next to a report the user filed weeks ago."""
    ticket = (ticket or "").strip().upper()[:20]
    if not _TICKET_RE.match(ticket):
        return jsonify({"ok": False,
                        "error": "That does not look like a ticket id. They "
                                 "look like CM-4F2K9Q1X."}), 400
    if not CLOUD_INTAKE_URL:
        return jsonify({"ok": False, "error": ERR_DISABLED}), 503
    if not _intake_url_ok(CLOUD_INTAKE_URL):
        return jsonify({"ok": False, "error": ERR_MISCONFIGURED}), 503
    url = CLOUD_INTAKE_URL.rstrip("/") + "/" + ticket
    req = urllib.request.Request(
        url, headers={"User-Agent": f"clawmetry/{_version() or 'dev'}"})
    try:
        # nosec B310 - same checked http(s) base; the ticket is matched
        # against the ticket pattern before it reaches the path.
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # nosec B310
            body = json.loads(resp.read().decode("utf-8") or "{}")
            return jsonify(body if isinstance(body, dict) else {})
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8") or "{}")
        except Exception:
            body = {}
        return jsonify(body or {
            "ok": False,
            "error": "We could not find that report. Check the id in your "
                     "confirmation email."}), int(exc.code or 502)
    except Exception:
        return jsonify({"ok": False,
                        "error": "We could not reach the tracker just now. "
                                 "Your report is safe; try again in a minute."}), 503


@bp_support.route("/api/bug-report/diagnostics", methods=["GET"])
def api_bug_report_diagnostics():
    """What the dialog shows under "what gets attached", before sending."""
    return jsonify({"ok": True, "diagnostics": collect_diagnostics()})
