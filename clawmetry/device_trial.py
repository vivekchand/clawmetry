"""clawmetry/device_trial.py — the 7-day Pro trial that starts without an account.

Why this exists. The 7-day full-Pro trial has been free and automatic since
2026-07-30, but it is minted by ``/api/license/trial/signup`` for an ACCOUNT,
so it reaches an install only after the user signs in. Roughly nine in ten
installs never do (June 2026 admin funnel: ~1,100 installs a month became
~120 sign-ups), so on most machines that run Claude Code, Cursor or Codex
the dashboard shows the free runtimes and a locked card, and the runtime the
user actually came for is never observed. That is the conversion moment
spent on a sign-in form.

What this does. When a paid runtime is present on disk and the install
holds no entitlement at all (no license file, no cloud plan), the daemon
asks the license server for a DEVICE trial: a signed ``tier="trial"`` key
bound to this install's anonymous ``install_id`` (the same id the install
ping uses) and this machine's ``node_id``. The key is activated exactly the
way a pasted key is (written to ``~/.clawmetry/license.key``, node
registered, closed-source wheel installed), so every runtime is observed on
day 0. Signing in is asked for on day 3, from inside a dashboard that is
already showing the user's own data (``routes/trial.py`` publishes the nudge;
``static/js/trial-pill.js`` renders it). A sign-in later mints the account's
own trial through the existing path, so identity still unlocks the runtimes
past day 7; the device trial only moves the ask.

Rules, in the order they are checked by :func:`maybe_start`:

* ``CLAWMETRY_DEVICE_TRIAL=0`` (or ``false`` / ``no`` / ``off``) disables it.
* ``CLAWMETRY_OFFLINE=1`` disables it (the server is never contacted).
* Telemetry opt-out does NOT disable it: the trial is a product action,
  not a measurement. The request carries the same anonymous ``install_id``
  the install ping carries and nothing else about the machine besides
  ``node_id`` and the ids of the runtimes found.
* The install must resolve to the plain OSS tier: any license (live or
  lapsed) or any cloud plan means an account or key already speaks for this
  machine, and the account's own trial rules apply.
* At least one PAID runtime must be present on disk (``runtime_probe``).
* One attempt per install. The outcome is recorded in
  ``~/.clawmetry/device_trial.json`` (``started`` / ``expired`` / ``refused``
  / ``error``); a network or server error is retried at most once a day.

Failure posture matches the rest of the entitlement engine: every function
is defensive and never raises; a failure leaves the install exactly as it
was, on the free runtimes.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import time

logger = logging.getLogger("clawmetry.device_trial")

CONFIG_DIR = os.path.expanduser("~/.clawmetry")
MARKER_PATH = os.path.join(CONFIG_DIR, "device_trial.json")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

ENV_SWITCH = "CLAWMETRY_DEVICE_TRIAL"
_OFF_VALUES = {"0", "false", "no", "off"}

# The license server endpoint. Relative to ``license._cloud_base()`` so a
# self-hosted license server (``CLAWMETRY_LICENSE_SERVER``) is honoured.
ENDPOINT = "/api/license/trial/device"
TIMEOUT_SEC = 20
# A failed attempt (network, 5xx) is retried no sooner than this.
ERROR_RETRY_SECS = 24 * 3600
# The sign-in ask starts this many days before expiry (a 7-day trial asks
# from day 3 onward).
SIGNIN_NUDGE_DAYS_LEFT = 4


def enabled() -> bool:
    """False when the operator switched the device trial off or the install
    is air-gapped. Read at call time so a change takes effect without a
    restart."""
    val = os.environ.get(ENV_SWITCH, "").strip().lower()
    if val in _OFF_VALUES:
        return False
    try:
        from clawmetry.license import _offline_mode

        if _offline_mode():
            return False
    except Exception:
        pass
    return True


# ── marker ────────────────────────────────────────────────────────────────


def read_marker() -> dict:
    """The recorded outcome for this install, ``{}`` when none."""
    try:
        with open(MARKER_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_marker(data: dict) -> None:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = MARKER_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, MARKER_PATH)
    except Exception as exc:
        logger.debug("device_trial: marker write failed: %s", exc)


# ── machine identity ──────────────────────────────────────────────────────


def _read_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _node_id() -> str:
    """The node id the daemon will use, persisted so the activation the
    license server records matches the id every later call presents.

    The daemon defaults a missing ``node_id`` to the hostname on its own
    start (``sync.load_config``); doing the same here, before activation,
    is what keeps ``refresh_pro_from_license`` from asking the server about
    a node it never registered."""
    cfg = _read_config()
    nid = str(cfg.get("node_id") or "").strip()
    if nid:
        return nid
    nid = socket.gethostname() or "local"
    try:
        cfg["node_id"] = nid
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = CONFIG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2)
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, CONFIG_PATH)
    except Exception as exc:
        logger.debug("device_trial: node_id persist failed: %s", exc)
    return nid


def _install_id() -> str:
    try:
        from clawmetry.telemetry import _ensure_install_id

        return _ensure_install_id() or ""
    except Exception:
        return ""


# ── eligibility ───────────────────────────────────────────────────────────


def detected_paid_runtimes() -> list:
    """Ids of PAID runtimes present on this machine, catalogue order.
    Presence checks only (``runtime_probe``): no session is read."""
    try:
        from clawmetry.runtime_probe import probe_runtimes

        return [p["id"] for p in probe_runtimes() if p.get("found") and not p.get("free")]
    except Exception:
        return []


def _holds_entitlement() -> bool:
    """True when a license file or a cloud plan already speaks for this
    install. Deliberately includes an EXPIRED license: a lapsed trial or
    subscription is the account's own history, and the device trial must
    not be a way around the one-trial rule."""
    try:
        from clawmetry import entitlements as _ent

        if _ent._read_local_license() is not None:
            return True
        if _ent._read_cloud_plan() is not None:
            return True
        if _ent._account_is_linked():
            return True
    except Exception as exc:
        # Cannot tell: fail SAFE for the seller, do not mint.
        logger.debug("device_trial: entitlement read failed (%s); not eligible", exc)
        return True
    return False


def eligible() -> tuple[bool, str]:
    """Whether :func:`maybe_start` would contact the server, and why not."""
    if not enabled():
        return False, "disabled"
    marker = read_marker()
    status = str(marker.get("status") or "")
    if status in ("started", "expired", "refused"):
        return False, status
    if status == "error":
        try:
            if time.time() - float(marker.get("attempted_at") or 0) < ERROR_RETRY_SECS:
                return False, "error_backoff"
        except Exception:
            pass
    if _holds_entitlement():
        return False, "entitled"
    if not detected_paid_runtimes():
        return False, "no_paid_runtime"
    if not _install_id():
        return False, "no_install_id"
    return True, "eligible"


# ── the request ───────────────────────────────────────────────────────────


def _request_device_trial(install_id: str, node_id: str, runtimes: list) -> dict:
    """POST to the license server. Returns the decoded body, or a dict with
    ``_error`` set. Never raises."""
    import urllib.error
    import urllib.request

    try:
        from clawmetry.license import _cloud_base

        base = _cloud_base()
    except Exception as exc:
        return {"_error": f"no license server: {exc}"}
    body = json.dumps(
        {"install_id": install_id, "node_id": node_id, "runtimes": runtimes[:40]}
    ).encode("utf-8")
    req = urllib.request.Request(
        base + ENDPOINT, data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            data = json.loads(resp.read().decode("utf-8") or "{}")
        return data if isinstance(data, dict) else {"_error": "malformed response"}
    except urllib.error.HTTPError as exc:
        # 4xx is a decision (refused, rate limited, unknown install); read
        # the body so the marker can carry the server's reason.
        try:
            data = json.loads(exc.read().decode("utf-8") or "{}")
        except Exception:
            data = {}
        data = data if isinstance(data, dict) else {}
        data["_status"] = int(getattr(exc, "code", 0) or 0)
        # A decision is final; anything that reads "not here yet" is retried
        # daily. 404 / 405 / 501 mean a license server that predates this
        # endpoint (the OSS wheel can ship ahead of the cloud deploy, and a
        # self-hosted server may never grow it); marking those refused would
        # lock every such install out of the trial for good.
        if data["_status"] in (400, 403, 409, 410):
            data.setdefault("_refused", True)
        else:
            data["_error"] = f"HTTP {data['_status']}"
        return data
    except Exception as exc:
        return {"_error": str(exc)}


def _activate_key(key: str) -> tuple[bool, str]:
    """Persist the signed key, register the node and install the pro wheel.

    Mirrors ``license.activate`` minus one thing: it does NOT record an
    onboarding choice. The device trial is something the product did, not
    something the user chose, so the first-run gate keeps its contract
    (it fires only for an install that genuinely made no choice) and the
    user still gets to pick managed or self-host from the browser."""
    try:
        from clawmetry import license as _lic

        payload = _lic.verify_token(key)
        if payload is None:
            return False, "invalid key"
        exp = payload.get("exp")
        if isinstance(exp, (int, float)) and time.time() > exp:
            return False, "expired key"
        lic_dir = os.path.dirname(_lic.LICENSE_PATH)
        os.makedirs(lic_dir, exist_ok=True)
        _lic._secure_write(_lic.LICENSE_PATH, key.strip() + "\n")
        try:
            from clawmetry import entitlements as _ent

            _ent.invalidate()
        except Exception:
            pass
        status = _lic._download_and_install_pro(payload)
        try:
            _lic._audit_license_event(
                "license.activate", result="activated", actor="device_trial",
                payload=payload, detail="account-free device trial",
            )
        except Exception:
            pass
        return True, status
    except Exception as exc:
        return False, str(exc)


def maybe_start(source: str = "daemon") -> dict:
    """Start the device trial if this install is eligible. Returns a dict
    with ``status`` in ``started`` / ``expired`` / ``refused`` / ``error`` /
    ``skipped`` (plus ``reason`` for skipped), and never raises.

    ``source`` names the caller (``daemon``, ``onboard``) for the marker and
    the telemetry event."""
    try:
        ok, why = eligible()
        if not ok:
            return {"status": "skipped", "reason": why}
        runtimes = detected_paid_runtimes()
        install_id = _install_id()
        node_id = _node_id()
        now = int(time.time())
        resp = _request_device_trial(install_id, node_id, runtimes)

        marker = {
            "attempted_at": now,
            "source": source,
            "runtimes": runtimes,
            "node_id": node_id,
        }
        if resp.get("_error"):
            marker.update(status="error", error=str(resp["_error"])[:200])
            _write_marker(marker)
            logger.info("device_trial: not started (%s)", marker["error"])
            return {"status": "error", "error": marker["error"]}
        if resp.get("_refused") or (resp.get("ok") is False and not resp.get("expired")):
            marker.update(status="refused",
                          error=str(resp.get("error") or resp.get("_status") or "refused")[:200])
            _write_marker(marker)
            logger.info("device_trial: refused by server (%s)", marker["error"])
            return {"status": "refused", "error": marker["error"]}
        if resp.get("expired"):
            marker.update(status="expired", expires_at=resp.get("expires_at"))
            _write_marker(marker)
            return {"status": "expired", "expires_at": resp.get("expires_at")}
        key = str(resp.get("key") or "").strip()
        if not key:
            marker.update(status="error", error="no key in response")
            _write_marker(marker)
            return {"status": "error", "error": "no key in response"}
        activated, msg = _activate_key(key)
        if not activated:
            marker.update(status="error", error=f"activation failed: {msg}"[:200])
            _write_marker(marker)
            return {"status": "error", "error": marker["error"]}
        marker.update(
            status="started",
            started_at=now,
            expires_at=resp.get("expires_at"),
            license_id=resp.get("license_id"),
            install_status=str(msg)[:200],
        )
        _write_marker(marker)
        logger.info("device_trial: started for %s (%s)", ", ".join(runtimes), source)
        _ping("device_trial_started", {"runtimes": runtimes, "source": source})
        return {
            "status": "started",
            "runtimes": runtimes,
            "expires_at": resp.get("expires_at"),
            "install_status": msg,
        }
    except Exception as exc:  # never let the trial break a caller
        logger.debug("device_trial: maybe_start failed: %s", exc)
        return {"status": "error", "error": str(exc)}


def _ping(event: str, extra: dict) -> None:
    """One-shot install-registry event (honours the telemetry opt-out)."""
    try:
        from clawmetry.telemetry import ping_once

        try:
            import importlib.metadata as _md

            version = _md.version("clawmetry")
        except Exception:
            version = "unknown"
        ping_once(event, version, extra)
    except Exception:
        pass


# ── status for the dashboard and the CLI ──────────────────────────────────


def status() -> dict:
    """What the dashboard needs to render the pill and the sign-in ask:

    ``active``        the device trial is what currently entitles this install
    ``days_left``     whole days until it expires (0 on the last day)
    ``expires_at``    epoch seconds
    ``signed_in``     an account key is present (the ask is answered)
    ``signin_nudge``  active, not signed in, and inside the nudge window
    ``runtimes``      the paid runtime ids the trial was started for
    """
    out = {
        "active": False, "days_left": None, "expires_at": None,
        "signed_in": False, "signin_nudge": False, "runtimes": [],
        "status": "",
    }
    try:
        marker = read_marker()
        out["status"] = str(marker.get("status") or "")
        out["runtimes"] = list(marker.get("runtimes") or [])
        if out["status"] != "started":
            return out
        try:
            from clawmetry import entitlements as _ent

            ent = _ent.get_entitlement()
            tier = str(getattr(ent, "tier", "") or "")
            source = str(getattr(ent, "source", "") or "")
            expiry = getattr(ent, "expiry", None)
        except Exception:
            tier, source, expiry = "", "", None
        if tier != "trial" or source != "license":
            # Something stronger took over (a cloud plan, a paid key) or the
            # trial lapsed: the device trial no longer describes this install.
            return out
        if expiry is None:
            expiry = marker.get("expires_at")
        try:
            expiry_f = float(expiry)
        except Exception:
            expiry_f = 0.0
        if expiry_f and time.time() > expiry_f:
            return out
        out["active"] = True
        out["expires_at"] = int(expiry_f) if expiry_f else None
        if expiry_f:
            out["days_left"] = max(0, int((expiry_f - time.time()) // 86400))
        out["signed_in"] = bool(str(_read_config().get("api_key") or "").startswith("cm_"))
        out["signin_nudge"] = (
            not out["signed_in"]
            and out["days_left"] is not None
            and out["days_left"] <= SIGNIN_NUDGE_DAYS_LEFT
        )
        return out
    except Exception as exc:
        logger.debug("device_trial: status failed: %s", exc)
        return out


def onboarding_lines(result: dict) -> list:
    """Plain-words lines for the CLI wizard after :func:`maybe_start`.
    Empty when nothing happened worth saying."""
    st = str((result or {}).get("status") or "")
    if st == "started":
        rts = list(result.get("runtimes") or [])
        try:
            from clawmetry.runtime_probe import RUNTIME_PROBES

            labels = {p.id: p.label for p in RUNTIME_PROBES}
        except Exception:
            labels = {}
        names = ", ".join(labels.get(r, r) for r in rts[:4])
        if len(rts) > 4:
            names += f" and {len(rts) - 4} more"
        return [
            f"Your 7-day Pro trial started on this machine: {names} now observed.",
            "No account needed. Sign in any time to keep every runtime after the",
            "trial and to see this dashboard from your phone: clawmetry connect",
        ]
    if st == "expired":
        return [
            "This machine's 7-day Pro trial has ended. Sign in for your account's",
            "trial, or get a key: https://clawmetry.com/pricing?deploy=self",
        ]
    return []
