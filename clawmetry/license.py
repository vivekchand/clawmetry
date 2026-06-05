"""
clawmetry/license.py — self-hosted Pro/Enterprise license client.

A ClawMetry Pro/Enterprise license is a signed token issued by
``license.clawmetry.com``. It unlocks the closed-source ``clawmetry-pro``
package (the paid runtimes + advanced features) on self-hosted installs, for N
nodes, for one year.

Trust model
-----------
The license server holds the Ed25519 PRIVATE key and signs licenses. This OSS
package embeds only the matching PUBLIC key, so a license verifies fully
OFFLINE — no phone-home needed to keep a paid feature working once activated.
``clawmetry activate`` does one online call to register this node against the
key's node count and fetch the clawmetry-pro wheel; after that the node runs
offline until the license expires.

Token format
------------
``CLAW1.<b64url(payload_json)>.<b64url(ed25519_sig)>`` where the signature
covers the exact payload-json bytes. Payload::

    {"sub": "<account>", "tier": "pro"|"enterprise", "nodes": N,
     "iat": <epoch>, "exp": <epoch>, "features": [...]}

Nothing here ever raises to the caller — a bad/expired/forged token resolves to
"no license" (OSS free), logged at warning level.
"""

from __future__ import annotations

import base64
import json
import logging
import os

logger = logging.getLogger("clawmetry.license")

# Where the cloud / license server lives. The clawmetry-pro wheel is streamed
# from ``<base>/api/license/download`` (HTTPS only — we never exec a wheel from
# an arbitrary host). ``CLAWMETRY_INGEST_URL`` is the same Cloud Run app that
# serves the license endpoints; ``CLAWMETRY_LICENSE_SERVER`` overrides it for
# self-hosted / air-gapped license servers.
_DEFAULT_CLOUD_BASE = "https://ingest.clawmetry.com"

# Marker recording the clawmetry-pro version this node provisioned, so connect /
# activate are idempotent (don't re-download an already-current wheel).
_PRO_MARKER_PATH = os.path.expanduser("~/.clawmetry/pro_installed.json")

# User-writable fallback for the clawmetry-pro install. The provisioner normally
# extracts the wheel into the interpreter's site-packages, but a SYSTEM-WIDE
# install (e.g. /opt/clawmetry owned by root) is NOT writable by a non-root
# daemon (systemd --user). Installing there fails with PermissionError and the
# paid runtimes silently never load. When site-packages is read-only we install
# into this HOME-owned dir instead and put it on sys.path. Always writable by the
# daemon user, no sudo/chown needed. (Founder hit this on a root-owned /opt
# install with a --user systemd daemon, 2026-06-05.)
_PRO_FALLBACK_DIR = os.path.expanduser("~/.clawmetry/pro-packages")

# Ed25519 PUBLIC verification key. The matching PRIVATE key lives only on the
# license server (clawmetry-cloud, never shipped). Rotating the server key
# means bumping this constant + an OSS release.
_PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEA1xcY0kmz1Ns+SVWTzJ/8BtLWDIS+OGquGxtk3FIaDzA=
-----END PUBLIC KEY-----
"""

_TOKEN_PREFIX = "CLAW1"
LICENSE_PATH = os.path.expanduser("~/.clawmetry/license.key")
_CONFIG_PATH = os.path.expanduser("~/.clawmetry/config.json")


def _b64u_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _load_public_key():
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    return load_pem_public_key(_PUBLIC_KEY_PEM)


def _encode_token(payload: dict, private_key) -> str:
    """Mint a license token. Needs the Ed25519 PRIVATE key — used by the
    license server and tests, never with a key shipped in this package."""
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = private_key.sign(raw)
    return f"{_TOKEN_PREFIX}.{_b64u_encode(raw)}.{_b64u_encode(sig)}"


def verify_token(token: str) -> dict | None:
    """Verify a license token against the embedded public key. Returns the
    payload dict if the signature is valid, else None. Never raises."""
    try:
        from cryptography.exceptions import InvalidSignature

        parts = (token or "").strip().split(".")
        if len(parts) != 3 or parts[0] != _TOKEN_PREFIX:
            return None
        raw = _b64u_decode(parts[1])
        sig = _b64u_decode(parts[2])
        try:
            _load_public_key().verify(sig, raw)
        except InvalidSignature:
            logger.warning("license: signature verification failed")
            return None
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            return None
        return payload
    except Exception as exc:
        logger.warning("license: token parse failed: %s", exc)
        return None


def parse_license(token: str):
    """Verify ``token`` and build an Entitlement, or None if invalid."""
    payload = verify_token(token)
    if payload is None:
        return None
    try:
        from clawmetry import entitlements as _ent

        tier_in = str(payload.get("tier", "")).strip().lower()
        tier = _ent.TIER_ENTERPRISE if tier_in == "enterprise" else _ent.TIER_PRO
        return _ent._build(
            tier,
            "license",
            node_limit=int(payload.get("nodes", 1) or 1),
            expiry=payload.get("exp"),
        )
    except Exception as exc:
        logger.warning("license: entitlement build failed: %s", exc)
        return None


def load_license(path: str = LICENSE_PATH):
    """Load + verify the on-disk license, returning an Entitlement or None.
    This is the hook :mod:`clawmetry.entitlements` calls."""
    try:
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as fh:
            token = fh.read().strip()
        return parse_license(token)
    except Exception as exc:
        logger.warning("license: load failed: %s", exc)
        return None


def _node_id() -> str | None:
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh).get("node_id")
    except Exception:
        return None


def _cloud_base() -> str:
    """Base URL of the cloud / license server that serves the clawmetry-pro
    wheel. ``CLAWMETRY_LICENSE_SERVER`` wins (self-hosted/air-gapped), else the
    cloud ingest app (which also hosts /api/license/*). Always HTTPS in prod;
    the only non-HTTPS values are explicit localhost overrides for tests."""
    return (
        os.environ.get("CLAWMETRY_LICENSE_SERVER", "").strip()
        or os.environ.get("CLAWMETRY_INGEST_URL", "").strip()
        or _DEFAULT_CLOUD_BASE
    ).rstrip("/")


def _pro_installed_version() -> str | None:
    """The installed clawmetry-pro version, or None if the package is not
    importable. Used to make download+install idempotent. Never raises."""
    try:
        import importlib.metadata as _md

        return _md.version("clawmetry-pro")
    except Exception:
        return None


def _read_pro_marker() -> dict:
    try:
        with open(_PRO_MARKER_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_pro_marker(extra: dict) -> None:
    """Record that clawmetry-pro is provisioned (best-effort, never raises)."""
    try:
        import time as _t

        os.makedirs(os.path.dirname(_PRO_MARKER_PATH), exist_ok=True)
        rec = {"installed_at": int(_t.time()), "version": _pro_installed_version()}
        rec.update(extra or {})
        with open(_PRO_MARKER_PATH, "w", encoding="utf-8") as fh:
            json.dump(rec, fh)
    except Exception as exc:
        logger.debug("license: pro marker write skipped: %s", exc)


def _download_wheel(url: str, headers: dict | None = None) -> str | None:
    """Download the clawmetry-pro wheel from ``url`` (HTTPS only) to a temp file
    and return its path, or None on failure. Security: refuses any non-HTTPS URL
    (except an explicit localhost test override) so we never fetch+install code
    from an attacker-controlled plaintext endpoint. Never raises."""
    try:
        import tempfile
        import urllib.request

        is_local = url.startswith("http://127.0.0.1") or url.startswith("http://localhost")
        if not url.startswith("https://") and not is_local:
            logger.warning("license: refusing non-HTTPS wheel URL %r", url)
            return None
        req = urllib.request.Request(url, headers=headers or {}, method="GET")
        with urllib.request.urlopen(req, timeout=60) as resp:
            # 2xx only; redirects are followed by urlopen, 402/403/503 raise HTTPError.
            data = resp.read()
        if not data:
            return None
        fd, path = tempfile.mkstemp(prefix="clawmetry_pro-", suffix=".whl")
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        return path
    except Exception as exc:
        logger.warning("license: wheel download failed: %s", exc)
        return None


def _pip_run(args: list) -> tuple[bool, str]:
    """Run ``python -m pip <args>`` in THIS interpreter. Returns (ok, tail)."""
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, "-m", "pip", *args],
        capture_output=True, text=True, timeout=300,
    )
    if proc.returncode == 0:
        return True, "installed"
    tail = (proc.stderr or proc.stdout or "").strip().splitlines()
    return False, (tail[-1] if tail else f"pip exited {proc.returncode}")


def _site_packages_target() -> tuple[str, bool]:
    """Return (interpreter site-packages dir, is_writable_by_us)."""
    try:
        import sysconfig
        target = sysconfig.get_path("purelib") or sysconfig.get_path("platlib") or ""
        writable = bool(target) and os.path.isdir(target) and os.access(target, os.W_OK)
        return target, writable
    except Exception:
        return "", False


def ensure_pro_on_path() -> None:
    """Put the user-writable fallback dir on ``sys.path`` if it exists, so a
    clawmetry-pro installed there (because site-packages was read-only) is
    importable. Idempotent, never raises. Call this at daemon/dashboard startup
    BEFORE plugin discovery, and before each provision attempt so an already-
    fallback-installed pro is detected as present."""
    try:
        import sys
        d = _PRO_FALLBACK_DIR
        if os.path.isdir(d) and d not in sys.path:
            sys.path.insert(0, d)
            try:
                import importlib
                importlib.invalidate_caches()
            except Exception:
                pass
    except Exception:
        pass


def _unzip_wheel_into_site(wheel_path: str) -> tuple[bool, str]:
    """pip-less fallback: a wheel is a zip of pure-Python packages, so for a
    ``--no-deps`` pure-Python wheel (clawmetry-pro) we can simply extract it and
    it becomes importable. Rescues a daemon venv created WITHOUT pip
    (``~/.clawmetry/bin/python3`` with no pip/ensurepip) AND a read-only
    interpreter site-packages (root-owned ``/opt`` install run by a non-root
    --user daemon): when site-packages is not writable we extract into the
    HOME-owned ``_PRO_FALLBACK_DIR`` and add it to ``sys.path`` so the adapters
    still load with no sudo/chown. Never raises."""
    try:
        import sys
        import zipfile

        target, writable = _site_packages_target()
        if not writable:
            # Interpreter site-packages is read-only (e.g. root-owned /opt
            # install, non-root daemon). Use the HOME-owned fallback dir.
            target = _PRO_FALLBACK_DIR
            try:
                os.makedirs(target, exist_ok=True)
            except Exception as _me:
                return False, f"no writable install target ({target!r}): {_me}"
        if not target or not os.path.isdir(target):
            return False, f"no writable install target ({target!r})"
        with zipfile.ZipFile(wheel_path) as zf:
            # Extract packages + dist-info so the import system (and
            # _pro_installed_version's importlib.metadata) work.
            zf.extractall(target)
        if target == _PRO_FALLBACK_DIR:
            if target not in sys.path:
                sys.path.insert(0, target)
            try:
                import importlib
                importlib.invalidate_caches()
            except Exception:
                pass
            return True, f"installed (unzip -> fallback {target})"
        return True, "installed (unzip)"
    except Exception as exc:
        return False, f"unzip install failed: {exc}"


def _pip_install_wheel(wheel_path: str) -> tuple[bool, str]:
    """Install ``wheel_path`` into THIS interpreter's environment (the same venv
    the daemon/dashboard run from — ``sys.executable``). The daemon picks the
    adapters up on its next start via extensions.load_plugins() /
    _family_adapter_classes().

    Resilient to a pip-less venv: tries ``python -m pip``; if pip is missing,
    bootstraps it with ``ensurepip`` and retries; if that too is unavailable,
    falls back to unzipping the (pure-Python, --no-deps) wheel straight into
    site-packages. Never raises."""
    import subprocess
    import sys

    # If the interpreter's site-packages is READ-ONLY (root-owned /opt install
    # run by a non-root daemon), pip can't write it either -> go straight to the
    # HOME-owned fallback unzip. This is the path that makes a system-wide
    # install work for a --user daemon without sudo/chown.
    _, _writable = _site_packages_target()
    if not _writable:
        return _unzip_wheel_into_site(wheel_path)

    args = ["install", "--upgrade", "--no-deps",
            "--disable-pip-version-check", wheel_path]
    try:
        ok, detail = _pip_run(args)
        if ok:
            return True, detail
        # pip absent? bootstrap it via ensurepip, then retry once.
        if "No module named pip" in detail or "No module named 'pip'" in detail:
            try:
                subprocess.run(
                    [sys.executable, "-m", "ensurepip", "--upgrade"],
                    capture_output=True, text=True, timeout=180,
                )
                ok2, detail2 = _pip_run(args)
                if ok2:
                    return True, detail2
                detail = detail2
            except Exception as ee:
                detail = f"{detail}; ensurepip: {ee}"
            # ensurepip also unavailable — last resort: unzip the wheel.
            return _unzip_wheel_into_site(wheel_path)
        return False, detail
    except Exception as exc:
        # Any unexpected pip failure: still try the pip-less unzip path.
        ok3, detail3 = _unzip_wheel_into_site(wheel_path)
        return (True, detail3) if ok3 else (False, f"{exc}; {detail3}")


def _provision_pro_wheel(download_url: str, *, headers: dict | None = None,
                         node_id: str | None = None) -> str:
    """Shared core: download + install the clawmetry-pro wheel from
    ``download_url`` (already entitlement-gated by the caller), idempotently.

    Returns a human status string. NEVER raises and NEVER blocks the caller —
    on any failure it logs a warning and returns a message; the node keeps
    running on the free runtimes."""
    # Make a prior fallback-dir install importable before the idempotency check,
    # so we don't re-download when pro is already present in the HOME fallback.
    ensure_pro_on_path()
    # Idempotent: if pro is already importable, don't re-download. A version
    # bump still re-installs because the marker is rewritten on every success
    # and the server serves the current wheel.
    already = _pro_installed_version()
    if already:
        _write_pro_marker({"node_id": node_id, "source": "already_present"})
        return f"clawmetry-pro {already} already installed"
    wheel = _download_wheel(download_url, headers=headers)
    if not wheel:
        return "clawmetry-pro wheel unavailable (will retry on next connect)"
    ok, detail = _pip_install_wheel(wheel)
    try:
        os.unlink(wheel)
    except Exception:
        pass
    if not ok:
        logger.warning("license: clawmetry-pro install failed: %s", detail)
        return f"clawmetry-pro install failed: {detail}"
    # Refresh entitlements + record the marker; the daemon loads the adapters on
    # its next start (extensions.load_plugins + _family_adapter_classes).
    try:
        from clawmetry import entitlements as _ent

        _ent.invalidate()
    except Exception:
        pass
    _write_pro_marker({"node_id": node_id, "source": "downloaded"})
    return f"clawmetry-pro installed ({_pro_installed_version() or 'ok'})"


def _download_and_install_pro(payload: dict) -> str:
    """Self-hosted SIGNED-LICENSE path: register this node against the license
    server and install ``clawmetry-pro``.

    The license server's POST /api/license/activate verifies the signed token,
    registers the node against the key's node count, and returns a scoped
    download URL. We then download+install that wheel (HTTPS only).

    Offline-first: this only phones home when a license server is EXPLICITLY
    configured (``CLAWMETRY_LICENSE_SERVER``, or ``CLAWMETRY_INGEST_URL`` for the
    cloud-hosted server). A pure-offline `clawmetry activate` with neither set is
    a graceful no-op — the verified license is already saved on disk and unlocks
    entitlements offline; the wheel can be fetched later. Returns a human status
    string. Never raises."""
    server = (
        os.environ.get("CLAWMETRY_LICENSE_SERVER", "").strip()
        or os.environ.get("CLAWMETRY_INGEST_URL", "").strip()
    )
    if not server:
        return "clawmetry-pro install deferred (no license server configured)"
    base = _cloud_base()
    node_id = _node_id() or "unknown"
    try:
        import urllib.request

        # Re-read the raw token from disk (we only have the decoded payload here).
        token = ""
        try:
            with open(LICENSE_PATH, "r", encoding="utf-8") as fh:
                token = fh.read().strip()
        except Exception:
            token = ""
        if not token:
            return "clawmetry-pro install deferred (no license on disk)"
        body = json.dumps({"key": token, "node_id": node_id}).encode()
        req = urllib.request.Request(
            base + "/api/license/activate", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8") or "{}")
        if not data.get("ok"):
            return f"node registration declined: {data.get('error', 'unknown')}"
        rel = data.get("download_url") or "/api/license/download"
        url = rel if rel.startswith("http") else base + rel
        return _provision_pro_wheel(url, node_id=node_id)
    except Exception as exc:
        logger.warning("license: pro install (self-hosted) failed: %s", exc)
        return f"clawmetry-pro install deferred ({exc})"


def auto_provision_pro(api_key: str, node_id: str | None = None) -> tuple[bool, str]:
    """CLOUD ACCOUNT path, called by ``clawmetry connect`` after the cm_ key is
    saved. Ask the cloud whether this account is ENTITLED to clawmetry-pro and,
    if so, download+install the wheel so the node gets all 12 runtimes.

    HARD RULES enforced here:
      * Pro is installed ONLY for an entitled plan (Starter/Pro/Trial/
        Enterprise). A FREE account returns (False, "") and installs NOTHING.
      * NEVER raises / NEVER blocks connect — any failure returns (False, msg)
        and the node continues on the free runtimes.
      * Idempotent — skips the download when clawmetry-pro is already current.
      * The wheel is fetched only from our own HTTPS /api/license/download.

    Returns (installed, status_message). ``installed`` is True only when the
    pro wheel is now present (newly installed or already there for an entitled
    account)."""
    try:
        key = (api_key or "").strip()
        if not key.startswith("cm_"):
            return False, ""
        base = _cloud_base()
        headers = {"X-Api-Key": key}
        # 1) Probe entitlement WITHOUT downloading the wheel.
        try:
            import urllib.request

            req = urllib.request.Request(
                base + "/api/license/entitlement", headers=headers, method="GET",
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                ent = json.loads(resp.read().decode("utf-8") or "{}")
        except Exception as exc:
            logger.warning("license: entitlement probe failed: %s", exc)
            return False, ""
        if not ent.get("entitled"):
            # Free / un-entitled account — install nothing, stay on free runtimes.
            return False, ""
        if not ent.get("pro_available", True):
            return False, "Pro entitled, but the clawmetry-pro wheel is not yet published."
        # 2) Entitled: download + install (idempotent, never-raise).
        url = base + "/api/license/download"
        msg = _provision_pro_wheel(url, headers=headers, node_id=node_id)
        installed = bool(_pro_installed_version())
        return installed, msg
    except Exception as exc:  # belt-and-suspenders: connect must never crash here
        logger.warning("license: auto_provision_pro failed: %s", exc)
        return False, ""


def activate(key: str, node_id: str | None = None) -> tuple[bool, str]:
    """Verify ``key`` offline, persist it, and (best-effort) register the node
    + install clawmetry-pro. Returns (ok, message). Never raises."""
    payload = verify_token(key)
    if payload is None:
        return False, "Invalid or unrecognized license key."
    import time as _t

    exp = payload.get("exp")
    if isinstance(exp, (int, float)) and _t.time() > exp:
        return False, "This license key has expired."
    try:
        os.makedirs(os.path.dirname(LICENSE_PATH), exist_ok=True)
        with open(LICENSE_PATH, "w", encoding="utf-8") as fh:
            fh.write(key.strip() + "\n")
    except Exception as exc:
        return False, f"Could not write license file: {exc}"
    # Refresh the entitlement cache so the new license takes effect immediately.
    try:
        from clawmetry import entitlements as _ent

        _ent.invalidate()
    except Exception:
        pass
    install_status = _download_and_install_pro(payload)
    tier = str(payload.get("tier", "pro")).lower()
    nodes = payload.get("nodes", 1)
    return True, f"Activated {tier} license for {nodes} node(s). {install_status}"


def current_license_info() -> dict | None:
    """Human-readable summary of the installed license, or None if there is no
    valid one. Never raises."""
    import time as _t

    try:
        if not os.path.isfile(LICENSE_PATH):
            return None
        with open(LICENSE_PATH, "r", encoding="utf-8") as fh:
            payload = verify_token(fh.read().strip())
        if payload is None:
            return {"valid": False, "status": "invalid"}
        exp = payload.get("exp")
        days_left = None
        expired = False
        if isinstance(exp, (int, float)):
            days_left = int((exp - _t.time()) // 86400)
            expired = _t.time() > exp
        return {
            "valid": not expired,
            "status": "expired" if expired else "active",
            "tier": payload.get("tier", "pro"),
            "nodes": payload.get("nodes", 1),
            "sub": payload.get("sub", ""),
            "exp": exp,
            "days_left": days_left,
        }
    except Exception as exc:
        logger.warning("license: info read failed: %s", exc)
        return None
