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
``clawmetry activate`` does one online call BY DEFAULT (to the production
license server at ``ingest.clawmetry.com``, overridable via
``CLAWMETRY_LICENSE_SERVER`` / ``CLAWMETRY_INGEST_URL``) to register this node
against the key's node count and fetch the clawmetry-pro wheel; after that the
node runs offline until the license expires. Set ``CLAWMETRY_OFFLINE=1`` to
skip the phone-home entirely (air-gapped installs) — key VERIFICATION is
always offline either way, and a failed/skipped phone-home never fails
activation.

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

# The license key is a bearer secret — anyone holding the file can present it as
# valid to the offline verifier — so on POSIX it must not be group/world
# readable. The bits we tolerate on the file (0o600) and parent dir (0o700).
_LICENSE_FILE_MODE = 0o600
_LICENSE_DIR_MODE = 0o700
_POSIX_GROUP_OTHER_BITS = 0o077  # any of these set on the file = unsafe


def _secure_write(path: str, content: str) -> None:
    """Write ``content`` to ``path`` with 0o600 mode on POSIX.

    Uses ``os.open`` with the mode arg so the file is created with the right
    bits even when the user's umask would otherwise widen them (default umask
    022 leaves a fresh file world-readable as 0o644 — bad for a key file).
    Also chmods after write so an existing file written under the old code
    path gets tightened on the next ``activate``. On Windows ``os.chmod``
    only toggles read-only and ``os.open`` ignores POSIX mode, so this is a
    safe no-op there — Windows' default ACLs already restrict the file to
    the owning user.
    """
    data = content.encode("utf-8")
    flags = os.O_CREAT | os.O_TRUNC | os.O_WRONLY
    fd = os.open(path, flags, _LICENSE_FILE_MODE)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    try:
        os.chmod(path, _LICENSE_FILE_MODE)
    except OSError:
        # Windows / weird filesystem: best-effort, never fail activation.
        pass


def _file_permissions_safe(path: str) -> bool:
    """True if ``path`` has no group/world bits set (POSIX) or doesn't exist.
    Always True on Windows (POSIX mode bits don't apply). Never raises."""
    try:
        if os.name != "posix":
            return True
        if not os.path.isfile(path):
            return True
        mode = os.stat(path).st_mode & 0o777
        return (mode & _POSIX_GROUP_OTHER_BITS) == 0
    except Exception:
        return True


def _b64u_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _load_public_key():
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    return load_pem_public_key(_PUBLIC_KEY_PEM)


def pubkey_fingerprint() -> str | None:
    """SHA-256 hex digest of the embedded Ed25519 verification key.

    The fingerprint is computed over the key's DER-encoded SubjectPublicKeyInfo
    bytes, so it is independent of PEM whitespace/line-ending noise and stable
    across reformatting. An operator can compare it against the canonical
    fingerprint published at ``https://clawmetry.com/security`` to confirm their
    OSS install carries the genuine trust anchor — i.e. that nobody has swapped
    ``_PUBLIC_KEY_PEM`` for an attacker-controlled key that would let them mint
    "valid" Pro/Enterprise license tokens against this node.

    Returns the hex string (lowercase, 64 chars) or ``None`` if the embedded
    PEM cannot be parsed (would indicate a tampered or corrupt install).
    Never raises.
    """
    try:
        import hashlib
        from cryptography.hazmat.primitives import serialization

        der = _load_public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return hashlib.sha256(der).hexdigest()
    except Exception as exc:
        logger.warning("license: pubkey fingerprint failed: %s", exc)
        return None


def pubkey_info() -> dict:
    """Operator-facing description of the embedded license verification key.

    Used by the ``/api/license/pubkey`` route and the ``clawmetry license
    fingerprint`` CLI subcommand. Never raises — on parse failure the
    fingerprint field is ``None`` and ``valid`` is ``False``."""
    fp = pubkey_fingerprint()
    pem_text = ""
    try:
        pem_text = _PUBLIC_KEY_PEM.decode("ascii").strip()
    except Exception:
        pem_text = ""
    return {
        "algorithm": "ed25519",
        "format": "SubjectPublicKeyInfo (DER, SHA-256)",
        "fingerprint_sha256": fp,
        "fingerprint_short": fp[:16] if fp else None,
        "pem": pem_text,
        "valid": fp is not None,
    }


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
        if tier_in == "enterprise":
            tier = _ent.TIER_ENTERPRISE
        elif tier_in == "starter":
            # Self-hosted Starter keys ($90/node/yr) issued by the cloud.
            tier = _ent.TIER_CLOUD_STARTER
        elif tier_in == "trial":
            # Local-trial keys (7 days, minted by /api/license/trial after
            # email verification). MUST map to TIER_TRIAL explicitly: the
            # forward-compat fallback below coerces unknown tiers to Pro,
            # which would silently turn every time-boxed trial into a full
            # Pro entitlement.
            tier = _ent.TIER_TRIAL
        else:
            # Unknown tiers still default to Pro (forward compatibility).
            tier = _ent.TIER_PRO
        return _ent._build(
            tier,
            "license",
            node_limit=int(payload.get("nodes", 1) or 1),
            expiry=payload.get("exp"),
        )
    except Exception as exc:
        logger.warning("license: entitlement build failed: %s", exc)
        return None


_warned_perms_for: set[str] = set()


def load_license(path: str = LICENSE_PATH):
    """Load + verify the on-disk license, returning an Entitlement or None.
    This is the hook :mod:`clawmetry.entitlements` calls."""
    try:
        if not os.path.isfile(path):
            return None
        # Surface (once per path) a warning if the key file is group/world
        # readable — older activate() runs wrote it with the default umask
        # (0o644 on most Linux). Re-running ``clawmetry activate`` tightens it.
        if not _file_permissions_safe(path) and path not in _warned_perms_for:
            _warned_perms_for.add(path)
            try:
                mode = os.stat(path).st_mode & 0o777
                logger.warning(
                    "license: %s has loose permissions (%o); "
                    "re-run `clawmetry activate <KEY>` to rewrite it 0600",
                    path, mode,
                )
            except Exception:
                pass
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


def _offline_mode() -> bool:
    """True when ``CLAWMETRY_OFFLINE`` is truthy ("1"/"true"/"yes") — the
    explicit opt-out that keeps ``clawmetry activate`` fully local (no node
    registration, no clawmetry-pro download). Never raises."""
    return os.environ.get("CLAWMETRY_OFFLINE", "").strip().lower() in (
        "1", "true", "yes",
    )


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


def _ver_tuple(v) -> tuple:
    """Parse a version string into a comparable int tuple ('0.3.4' -> (0,3,4))."""
    try:
        return tuple(int(x) for x in str(v).split("+")[0].split(".")[:4])
    except Exception:
        return (0,)


def _wheel_file_version(wheel_path: str) -> str | None:
    """Read the version from a wheel's dist-info/METADATA (reliable regardless
    of the on-disk filename). Used to decide whether the server's wheel is newer
    than what's installed. Never raises."""
    try:
        import zipfile

        with zipfile.ZipFile(wheel_path) as z:
            for n in z.namelist():
                if n.endswith(".dist-info/METADATA"):
                    for line in z.read(n).decode("utf-8", "replace").splitlines():
                        if line.startswith("Version:"):
                            return line.split(":", 1)[1].strip()
    except Exception:
        return None
    return None


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
            cdisp = resp.headers.get("Content-Disposition", "") or ""
        if not data:
            return None
        # Keep the REAL PEP-427 wheel filename (NAME-VER-PY-ABI-PLAT.whl) from
        # Content-Disposition, in a temp DIR. A random mkstemp name like
        # `clawmetry_pro-ab12.whl` is rejected by pip as "not a valid wheel
        # filename" -- which silently broke EVERY wheel re-download/upgrade.
        import re as _re

        m = _re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+\.whl)"?', cdisp)
        fname = os.path.basename(m.group(1)) if m else "clawmetry_pro-0-py3-none-any.whl"
        if not fname.endswith(".whl") or "/" in fname or "\\" in fname:
            fname = "clawmetry_pro-0-py3-none-any.whl"
        d = tempfile.mkdtemp(prefix="cmpro-")
        path = os.path.join(d, fname)
        with open(path, "wb") as fh:
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
    # Re-validate against the server EVERY time: download the (small ~140KB)
    # wheel and install it ONLY when it is strictly newer than what's installed.
    # The old code returned here whenever pro was importable, so an installed
    # pro NEVER upgraded -- rolling a new wheel to the cloud reached nobody (the
    # claude_code ai-title fix in 0.3.4 sat unused because every node kept the
    # installed 0.3.3). Keeping the current version on a download/check failure
    # means a transient outage never strands a working node.
    already = _pro_installed_version()
    wheel = _download_wheel(download_url, headers=headers)
    if not wheel:
        if already:
            return f"clawmetry-pro {already} already installed (server check failed; kept)"
        return "clawmetry-pro wheel unavailable (will retry on next connect)"
    if already:
        avail = _wheel_file_version(wheel)
        if avail and _ver_tuple(avail) <= _ver_tuple(already):
            try:
                os.unlink(wheel)
            except Exception:
                pass
            _write_pro_marker({"node_id": node_id, "source": "already_current"})
            return f"clawmetry-pro {already} already installed (latest is {avail})"
        # else: a newer wheel is available -> fall through and install it.
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

    This phones home BY DEFAULT: the server is resolved via :func:`_cloud_base`
    (``CLAWMETRY_LICENSE_SERVER``, else ``CLAWMETRY_INGEST_URL``, else the
    production cloud at ``ingest.clawmetry.com``) — the plain ``clawmetry
    activate <KEY>`` from the license email gets the pro wheel with zero extra
    configuration. Setting ``CLAWMETRY_OFFLINE=1`` (air-gapped installs) skips
    the phone-home entirely; the verified license is already saved on disk and
    unlocks entitlements offline, and the wheel can be fetched later. Key
    verification never involves the network either way, and a failed
    registration/download NEVER fails activation. Returns a human status
    string. Never raises."""
    if _offline_mode():
        return (
            "offline mode: skipping node registration and clawmetry-pro "
            "install (set CLAWMETRY_LICENSE_SERVER to your license server, "
            "or unset CLAWMETRY_OFFLINE)"
        )
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
        # install_id links this activation to the cloud install registry
        # (best-effort; server ignores unknown fields on older deploys).
        try:
            from clawmetry.telemetry import _ensure_install_id
            install_id = _ensure_install_id() or ""
        except Exception:
            install_id = ""
        body = json.dumps(
            {"key": token, "node_id": node_id, "install_id": install_id}
        ).encode()
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
    if so, download+install the wheel so the node gets all 14 runtimes.

    HARD RULES enforced here:
      * Pro is installed ONLY for an entitled plan (Starter/Pro/Trial/
        Enterprise). A FREE account returns (False, "") and installs NOTHING.
      * NEVER raises / NEVER blocks connect — any failure returns (False, msg)
        and the node continues on the free runtimes.
      * Idempotent — skips the download when clawmetry-pro is already current.
      * The wheel is fetched only from our own HTTPS /api/license/download.
      * ``CLAWMETRY_OFFLINE=1`` skips the entitlement probe AND the wheel
        download — no outbound network is touched. Symmetric with
        :func:`_download_and_install_pro` (the signed-license path); without
        this, the module docstring's "air-gapped install" claim was only
        half-true, since ``clawmetry connect`` and the sync-daemon watchers
        would still phone home to ``/api/license/entitlement`` and pull the
        closed-source wheel behind the operator's back.

    Returns (installed, status_message). ``installed`` is True only when the
    pro wheel is now present (newly installed or already there for an entitled
    account)."""
    try:
        key = (api_key or "").strip()
        if not key.startswith("cm_"):
            return False, ""
        if _offline_mode():
            return False, (
                "offline mode: skipping clawmetry-pro auto-provision "
                "(unset CLAWMETRY_OFFLINE to fetch the pro wheel)"
            )
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


def _audit_license_event(
    action: str,
    *,
    result: str,
    actor: str = "",
    payload: dict | None = None,
    detail: str = "",
) -> None:
    """Record a license state-change to the Enterprise audit log.

    Never raises — a failed audit write must never block the activate /
    deactivate path. The raw license key is NEVER recorded; only the
    non-secret claims (tier, nodes, sub, exp) and the outcome are kept."""
    try:
        from clawmetry import audit as _audit

        meta: dict = {}
        if isinstance(payload, dict):
            for k in ("tier", "nodes", "exp"):
                if k in payload:
                    meta[k] = payload[k]
        if detail:
            meta["detail"] = detail[:256]
        target = ""
        if isinstance(payload, dict):
            target = str(payload.get("sub", "") or "")
        _audit.audit_event(
            action,
            actor=actor or "",
            target=target,
            result=result,
            source="license",
            metadata=meta,
        )
    except Exception:
        pass


def activate(key: str, node_id: str | None = None, actor: str = "") -> tuple[bool, str]:
    """Verify ``key`` offline, persist it, and (best-effort) register the node
    + install clawmetry-pro. Returns (ok, message). Never raises.

    ``actor`` is an optional human/system identifier folded into the audit
    log entry; routes pass the X-Actor header (or remote address). Defaults
    to empty (the CLI path)."""
    payload = verify_token(key)
    if payload is None:
        _audit_license_event(
            "license.activate", result="invalid_key", actor=actor,
            detail="signature failed or key unparseable",
        )
        return False, "Invalid or unrecognized license key."
    import time as _t

    exp = payload.get("exp")
    if isinstance(exp, (int, float)) and _t.time() > exp:
        _audit_license_event(
            "license.activate", result="expired_key", actor=actor, payload=payload,
        )
        return False, "This license key has expired."
    try:
        lic_dir = os.path.dirname(LICENSE_PATH)
        os.makedirs(lic_dir, exist_ok=True)
        # Tighten the parent dir too — a 0o755 dir leaks the key's existence /
        # listing even if the file itself is 0o600. Best-effort; some shared
        # setups (e.g. NFS home dirs) refuse chmod and that must not block
        # activation.
        try:
            if os.name == "posix":
                os.chmod(lic_dir, _LICENSE_DIR_MODE)
        except OSError:
            pass
        _secure_write(LICENSE_PATH, key.strip() + "\n")
    except Exception as exc:
        _audit_license_event(
            "license.activate", result="write_error", actor=actor, payload=payload,
            detail=str(exc),
        )
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
    _audit_license_event(
        "license.activate", result="activated", actor=actor, payload=payload,
    )
    return True, f"Activated {tier} license for {nodes} node(s). {install_status}"


def deactivate(actor: str = "") -> tuple[bool, bool]:
    """Remove the on-disk license file and invalidate the entitlement cache.

    Returns ``(ok, removed)`` — ``removed`` is False when no key was
    installed (idempotent). Records a ``license.deactivate`` audit entry
    with the prior tier/sub when the key parsed; never raises."""
    prior_payload: dict | None = None
    try:
        if os.path.isfile(LICENSE_PATH):
            with open(LICENSE_PATH, "r", encoding="utf-8") as fh:
                prior_payload = verify_token(fh.read().strip())
    except Exception:
        prior_payload = None
    removed = False
    try:
        if os.path.isfile(LICENSE_PATH):
            os.remove(LICENSE_PATH)
            removed = True
    except Exception as exc:
        _audit_license_event(
            "license.deactivate", result="remove_error", actor=actor,
            payload=prior_payload, detail=str(exc),
        )
        return False, False
    try:
        from clawmetry import entitlements as _ent

        _ent.invalidate()
    except Exception:
        pass
    _audit_license_event(
        "license.deactivate",
        result="removed" if removed else "noop",
        actor=actor,
        payload=prior_payload,
    )
    return True, removed


def inspect_key(key: str) -> dict | None:
    """Verify ``key`` OFFLINE and return what it would unlock — without writing
    anything to disk. The dry-run counterpart of :func:`activate`.

    Use cases:
      * Support: "paste your key, let's see what tier/exp it carries" without
        having the customer mutate their install.
      * Pre-flight from the CLI / dashboard before clicking *Activate*.
      * Air-gap: validate a key on a staging box before transporting it.

    Returns a dict with the same field set as :func:`current_license_info` (so
    the UI can render the two the same way, and a support script can jq the
    same keys off either) — or ``None`` if the signature is bogus or the token
    is malformed. An EXPIRED but otherwise-valid token returns a dict with
    ``valid=False`` + ``status="expired"`` so the caller can still show what
    the (now-stale) key was for.

    ``pubkey_fingerprint_sha256`` carries the payload-independent trust anchor
    identity so a support call ("does the key you're pasting verify against
    the fingerprint we ship?") can be answered off the same envelope. The two
    on-disk-only fields — ``permissions_safe`` and ``file_mode`` — collapse to
    ``None`` on a dry-run since there is no file to stat yet; the keys are
    kept for shape parity with :func:`current_license_info` so a UI branching
    on either envelope never has to check for missing keys.

    Never raises, never touches disk."""
    import time as _t

    try:
        payload = verify_token(key)
        if payload is None:
            return None
        exp = payload.get("exp")
        days_left = None
        expired = False
        if isinstance(exp, (int, float)):
            days_left = int((exp - _t.time()) // 86400)
            expired = _t.time() > exp
        tier_in = str(payload.get("tier", "pro")).strip().lower()
        # Mirror parse_license: known tiers render as-is, unknown -> pro.
        tier = tier_in if tier_in in ("enterprise", "starter") else "pro"
        iat = payload.get("iat")
        issued_at = int(iat) if isinstance(iat, (int, float)) else None
        return {
            "valid": not expired,
            "status": "expired" if expired else "active",
            "tier": tier,
            "nodes": int(payload.get("nodes", 1) or 1),
            "sub": str(payload.get("sub", "")),
            "exp": exp,
            "issued_at": issued_at,
            "days_left": days_left,
            # Trust-anchor identity is payload-independent — same value as
            # current_license_info() populates on every file-exists branch, so
            # a UI can render either envelope through one code path.
            "pubkey_fingerprint_sha256": pubkey_fingerprint(),
            # On-disk fields are meaningless on a dry-run (no file exists yet);
            # kept in the envelope with None so the shape matches
            # current_license_info() exactly.
            "permissions_safe": None,
            "file_mode": None,
        }
    except Exception as exc:  # never raise from a dry-run inspector
        logger.warning("license: inspect_key failed: %s", exc)
        return None


def current_license_info() -> dict | None:
    """Human-readable summary of the installed license, or None if there is no
    valid one. Never raises.

    Returns ``None`` only when no license file is on disk. When a file exists,
    every branch — active / expired / invalid-signature — returns the SAME
    field set so a UI can render all three uniformly without special-casing
    which keys are present. On the invalid-signature branch the payload cannot
    be trusted (an attacker could stuff any tier/nodes into an unsigned body),
    so ``tier``/``nodes``/``sub``/``exp``/``days_left`` collapse to ``None``;
    the trust-anchor (``pubkey_fingerprint_sha256``) and on-disk permission
    fields (``permissions_safe``, ``file_mode``) DO get populated in every
    file-exists branch — those are exactly the operator-debug fields most
    useful when a license file has been corrupted or tampered with.
    """
    import time as _t

    try:
        if not os.path.isfile(LICENSE_PATH):
            return None
        with open(LICENSE_PATH, "r", encoding="utf-8") as fh:
            payload = verify_token(fh.read().strip())
        # Trust-anchor + on-disk state are independent of the token payload,
        # so we resolve them up-front and reuse across every branch below.
        # ``permissions_safe`` is True on Windows (mode bits don't apply) and
        # True when no group/world bits are set on the file. The UI can use
        # this to surface a "tighten file permissions" affordance without
        # parsing octal modes itself.
        perms_safe = _file_permissions_safe(LICENSE_PATH)
        try:
            mode = os.stat(LICENSE_PATH).st_mode & 0o777 if os.name == "posix" else None
        except Exception:
            mode = None
        # Trust-anchor identity: a Pro/Enterprise license is only as
        # trustworthy as the embedded public key that signed it, so we
        # surface its fingerprint here for operator audits.
        pubkey_fp = pubkey_fingerprint()
        file_mode = f"{mode:04o}" if mode is not None else None

        if payload is None:
            # File exists but signature is bogus (bit-flip, tamper, key rotated
            # server-side, wrong-environment key…). Never surface tier/nodes
            # from an unverified body — they'd let a forger claim any tier — but
            # keep the shape uniform so a UI can render this row like the
            # others and lean on ``permissions_safe`` / ``file_mode`` to
            # explain WHY (e.g. loose perms may indicate corruption).
            return {
                "valid": False,
                "status": "invalid",
                "tier": None,
                "nodes": None,
                "sub": None,
                "exp": None,
                "issued_at": None,
                "days_left": None,
                "pubkey_fingerprint_sha256": pubkey_fp,
                "permissions_safe": perms_safe,
                "file_mode": file_mode,
            }
        exp = payload.get("exp")
        days_left = None
        expired = False
        if isinstance(exp, (int, float)):
            days_left = int((exp - _t.time()) // 86400)
            expired = _t.time() > exp
        iat = payload.get("iat")
        issued_at = int(iat) if isinstance(iat, (int, float)) else None
        return {
            "valid": not expired,
            "status": "expired" if expired else "active",
            "tier": payload.get("tier", "pro"),
            "nodes": payload.get("nodes", 1),
            "sub": payload.get("sub", ""),
            "exp": exp,
            "issued_at": issued_at,
            "days_left": days_left,
            "pubkey_fingerprint_sha256": pubkey_fp,
            "permissions_safe": perms_safe,
            "file_mode": file_mode,
        }
    except Exception as exc:
        logger.warning("license: info read failed: %s", exc)
        return None


def days_until_expiry() -> int | None:
    """Scalar view onto the installed license's ``exp`` claim -- for renewal
    banners / countdown badges that want ONE number rather than the whole
    :func:`current_license_info` envelope.

    Returns:
      * ``None`` when there is nothing meaningful to count down against:
        no license file, an invalid signature, or a valid license whose
        payload carries no ``exp`` claim (perpetual license).
      * A signed integer number of days otherwise. Zero on the day of
        expiry, negative once the license has expired -- a renewal UI can
        distinguish "expires today" from "expired 3 days ago" by sign
        without a second call to :func:`current_license_info`.

    Days are floor-divided from seconds (``(exp - now) // 86400``), matching
    the ``days_left`` field already surfaced by
    :func:`current_license_info` / :func:`inspect_key` so the scalar
    endpoint and the full-envelope endpoint never disagree at the day
    boundary.

    Never raises. Any exception under the hood degrades to ``None`` so a
    UI tile bound to this helper never breaks on a partial install.
    """
    try:
        info = current_license_info()
    except Exception as exc:
        logger.debug("license: days_until_expiry underlying read failed: %s", exc)
        return None
    if not isinstance(info, dict):
        return None
    days = info.get("days_left")
    return days if isinstance(days, int) else None


def is_expiring_within(days: int) -> bool:
    """Boolean gate for "should I show a renewal warning?" UIs.

    Returns ``True`` iff a license is installed AND its ``exp`` claim is
    within ``days`` days of now AND it has NOT already expired. An
    already-expired license returns ``False`` on purpose -- the caller
    wants to distinguish "renewal window" (warn) from "already expired"
    (a different, louder banner driven off :func:`current_license_info`'s
    ``status`` field). Perpetual licenses (no ``exp`` claim) and the
    no-license path both return ``False``: nothing to warn about.

    ``days`` is coerced through ``int()``; negative or non-numeric input
    collapses to ``False`` (nothing "expires within -5 days"). Never
    raises; every underlying failure returns ``False`` so a scheduled
    reminder job never crashes on a bad install.
    """
    try:
        threshold = int(days)
    except (TypeError, ValueError):
        return False
    if threshold < 0:
        return False
    remaining = days_until_expiry()
    if remaining is None:
        return False
    return 0 <= remaining <= threshold


def license_expires_at() -> int | None:
    """Scalar view onto the installed license's ``exp`` claim -- the epoch
    timestamp the key expires at -- for a "license expires: <date>" row
    that wants ONE integer rather than the whole
    :func:`current_license_info` envelope.

    Returns:
      * ``None`` when there is nothing meaningful to surface: no license
        file on disk, an invalid signature (the payload can't be trusted
        -- an attacker could stuff any ``exp`` into an unsigned body), OR
        a signed payload whose ``exp`` claim is absent / non-numeric
        (perpetual license). A caller distinguishes "perpetual" from "no
        license" via :func:`is_perpetual` + :func:`has_license`.
      * A positive epoch integer otherwise -- the exact timestamp carried
        by the signed payload, unmodified.

    Deliberately lenient on expiry, mirroring :func:`license_issued_at`:
    an expired-but-signature-valid key still carries a meaningful ``exp``
    (support scenario: "when did this lapsed key expire?") and callers
    would otherwise have to fall back to ``/api/license/status``. The
    :func:`is_expired` / :func:`days_until_expiry` helpers independently
    carry the "past-expiry" signal for callers that DO want to hide the
    row on lapsed keys.

    Pairs with :func:`days_until_expiry` the way :func:`license_issued_at`
    pairs with :func:`license_age_days` -- this scalar surfaces the raw
    epoch for an audit row, that one answers the caller-friendly "how
    many days left" without either side having to do the arithmetic. The
    two are floor-divided from the same ``exp`` so they never disagree at
    the day boundary.

    Never raises. Any exception under the hood degrades to ``None`` so a
    UI tile bound to this helper never breaks on a partial install.
    """
    try:
        info = current_license_info()
    except Exception as exc:
        logger.debug("license: license_expires_at underlying read failed: %s", exc)
        return None
    if not isinstance(info, dict):
        return None
    if info.get("status") == "invalid":
        # Invalid-signature branch: payload cannot be trusted, refuse to
        # surface any payload-derived claim (mirrors the issued_at scalar).
        # Expired-but-signed keys still carry a meaningful ``exp`` so we
        # do NOT refuse them here.
        return None
    exp = info.get("exp")
    return int(exp) if isinstance(exp, (int, float)) else None


def is_expiring_at(epoch: int) -> bool:
    """Boolean gate for "does the installed license expire at THIS exact
    epoch?" UIs -- e.g. a "we noticed your key expires <date>" tile that
    binds a specific ``exp`` value and wants to detect renewal (the on-
    disk key no longer matches the value it was rendered with).

    Returns ``True`` iff a license is installed, signature-valid, NOT
    expired, carries an ``exp`` claim, AND that claim matches ``epoch``
    exactly. Perpetual licenses (no ``exp``) and the no-license path both
    return ``False``: nothing to compare against.

    ``epoch`` is coerced through ``int()``; a non-numeric value collapses
    to ``False`` so a caller cannot silently mis-gate on a typo. Never
    raises; every underlying failure returns ``False`` so a scheduled
    reminder job never crashes on a bad install.

    Deliberately strict on validity, unlike the underlying
    :func:`license_expires_at` scalar (which is lenient on expiry so a
    support tile can render "expired 12 days ago"). A predicate that
    fired ``True`` on an already-lapsed key would push callers to gate
    renewal UI on a value that no longer implies the customer is
    entitled.
    """
    try:
        wanted = int(epoch)
    except (TypeError, ValueError):
        return False
    try:
        info = current_license_info()
    except Exception as exc:
        logger.debug("license: is_expiring_at underlying read failed: %s", exc)
        return False
    if not isinstance(info, dict):
        return False
    if not info.get("valid"):
        return False
    exp = info.get("exp")
    if not isinstance(exp, (int, float)):
        return False
    return int(exp) == wanted


def days_until_expiry_at(epoch: int) -> int | None:
    """Scalar view of "how many days from ``epoch`` until the installed
    license's ``exp`` claim?" for a perspective-epoch audit tile that
    wants to answer "was the license in the renewal window on <date>?"
    without the caller having to compute ``(exp - epoch) // 86400`` at
    every call site.

    Returns:
      * ``None`` when there is nothing meaningful to compute against: no
        license file on disk, an invalid signature (the payload can't be
        trusted -- an attacker could stuff any ``exp`` into an unsigned
        body), a signed payload whose ``exp`` claim is absent
        (perpetual license -- nothing to count down to), OR a non-numeric
        / bool ``epoch`` argument.
      * A signed integer number of days otherwise. Zero when ``epoch``
        falls on the day of expiry; negative when ``epoch`` is after
        ``exp`` (support scenario: "how many days past expiry was
        <date>?"); positive when ``epoch`` is before ``exp``. A caller
        distinguishes "expires that day" from "expired 3 days before
        then" by sign without a second call to
        :func:`current_license_info`.

    Days are floor-divided from seconds ``(exp - epoch) // 86400``,
    matching how :func:`days_until_expiry` derives its "now" counterpart
    from the same claim so the two scalars never disagree at the day
    boundary when ``epoch`` equals the current time.

    ``epoch`` is coerced through ``int()``; ``bool`` is explicitly
    refused despite being an ``int`` subclass so a caller that passes
    ``True`` / ``False`` gets ``None`` rather than a spurious "days
    until epoch 1" number. A non-numeric value collapses to ``None`` so
    a caller cannot silently miscount on a typo.

    Deliberately lenient on expiry, mirroring :func:`days_until_expiry`:
    an expired-but-signature-valid key still carries a meaningful ``exp``
    (support scenario: "when did this lapsed key expire, evaluated as
    of last Friday?") and callers would otherwise have to fall back to
    ``current_license_info``. The :func:`is_expired` /
    :func:`is_expiring_at` helpers independently carry the "past-expiry"
    / "exact-match" signals for callers that DO want to hide the row on
    lapsed keys.

    Pairs with :func:`license_expires_at` the way
    :func:`days_until_expiry` pairs with :func:`license_expires_at`:
    both derive from the same ``exp`` claim so they cannot disagree at
    the day boundary. The perspective-epoch flavour lets a scheduled
    audit tile answer "would we have warned yesterday? last week?"
    without having to snapshot the license state at those times.

    Never raises. Any exception under the hood degrades to ``None`` so a
    scheduled audit job never crashes on a bad install.
    """
    if isinstance(epoch, bool):
        # ``bool`` is a subclass of ``int``; refuse it explicitly so a
        # caller that passes ``True`` doesn't silently ask "days until
        # epoch 1?" and get a very negative number back.
        return None
    try:
        wanted = int(epoch)
    except (TypeError, ValueError):
        return None
    try:
        exp = license_expires_at()
    except Exception as exc:
        logger.debug("license: days_until_expiry_at underlying read failed: %s", exc)
        return None
    if not isinstance(exp, int):
        return None
    try:
        return (exp - wanted) // 86400
    except Exception as exc:
        logger.debug("license: days_until_expiry_at arithmetic failed: %s", exc)
        return None


def is_expiring_within_at(days: int, epoch: int) -> bool:
    """Boolean gate for "would we have shown a renewal warning as of
    ``epoch``?" -- the perspective-epoch flavour of
    :func:`is_expiring_within`, for a scheduled-audit / retrospective
    tile that wants to answer "was the license inside the ``days``-day
    renewal window on <date>?" without having to snapshot the license
    state at that time.

    Returns ``True`` iff a license is installed, signature-valid,
    carries an ``exp`` claim, AND the days from ``epoch`` until ``exp``
    fall between 0 and ``days`` inclusive. An already-lapsed-at-epoch
    key returns ``False`` on purpose -- the caller wants to distinguish
    "renewal window" (warn) from "already expired at that time" (a
    different, louder banner), and :func:`days_until_expiry_at` /
    :func:`is_expired_at` independently carry those signals for callers
    that DO want to distinguish them. Perpetual licenses (no ``exp``
    claim) and the no-license path both return ``False``: nothing to
    warn about.

    ``days`` is coerced through ``int()``; negative or non-numeric input
    collapses to ``False`` (nothing "expires within -5 days"). ``epoch``
    is coerced through ``int()``; ``bool`` is explicitly refused despite
    being an ``int`` subclass so a caller that passes ``True`` doesn't
    silently ask "is this expiring within N days as of epoch 1?" and
    get an ancient-history answer. A non-numeric ``epoch`` collapses to
    ``False`` so a caller cannot silently mis-gate on a typo.

    Days are floor-divided from seconds ``(exp - epoch) // 86400``,
    matching :func:`days_until_expiry_at` so the two helpers cannot
    disagree at the day boundary for the same install / epoch. When
    ``epoch`` equals the current time, this predicate must agree with
    :func:`is_expiring_within` at that day boundary (+/- 1 for the
    fractional-second drift between the two calls: the bare helper reads
    ``time.time()`` inside :func:`current_license_info` with sub-second
    precision, while the perspective helper receives an already-
    truncated integer).

    Never raises; every underlying failure returns ``False`` so a
    scheduled audit job never crashes on a bad install.
    """
    try:
        threshold = int(days)
    except (TypeError, ValueError):
        return False
    if threshold < 0:
        return False
    if isinstance(epoch, bool):
        return False
    try:
        int(epoch)
    except (TypeError, ValueError):
        return False
    try:
        remaining = days_until_expiry_at(epoch)
    except Exception as exc:
        logger.debug("license: is_expiring_within_at underlying read failed: %s", exc)
        return False
    if remaining is None:
        return False
    return 0 <= remaining <= threshold


def license_tier() -> str | None:
    """Scalar view onto the installed license's ``tier`` claim -- for a
    paywall tile / tier badge that wants ONE string rather than the whole
    :func:`current_license_info` envelope.

    Returns:
      * ``None`` when there is nothing trustworthy to surface:
        no license file on disk, an invalid signature (the payload
        can't be trusted -- an attacker could stuff any tier into an
        unsigned body), OR a signed payload whose ``tier`` claim is
        absent / non-string / an empty string after strip.
      * A lowercased, whitespace-stripped tier string otherwise
        (typically ``"pro"``, ``"enterprise"``, or ``"trial"``, but the
        helper is deliberately open-ended so a future tier lands
        without a code change).

    Casing is normalised so a caller can compare against a hard-coded
    ``"pro"`` without a ``.lower()`` on every read; the raw claim from
    :func:`current_license_info` is preserved separately for UIs that
    want the operator-visible form.

    Never raises. Any exception under the hood degrades to ``None`` so a
    UI tile bound to this helper never breaks on a partial install.
    """
    try:
        info = current_license_info()
    except Exception as exc:
        logger.debug("license: license_tier underlying read failed: %s", exc)
        return None
    if not isinstance(info, dict):
        return None
    if not info.get("valid"):
        # Invalid-signature / expired branches: current_license_info() may
        # still surface ``tier`` on the expired branch (the signature was
        # good at signing time, only the ``exp`` claim has passed), but a
        # tier scalar for gating paywall UI should refuse expired keys the
        # same way it refuses unsigned ones -- otherwise a lapsed Pro
        # customer keeps rendering as "Pro" until they re-activate.
        return None
    tier = info.get("tier")
    if not isinstance(tier, str):
        return None
    normalized = tier.strip().lower()
    return normalized or None


def is_tier(tier: str) -> bool:
    """Boolean gate for "am I on tier <X>?" UIs.

    Returns ``True`` iff a license is installed, signature-valid, NOT
    expired, and its normalised ``tier`` claim exactly matches ``tier``
    (case-insensitive, whitespace-stripped). Every other state returns
    ``False``: no license, invalid signature, expired key, missing/empty
    ``tier`` claim, or a live tier that simply differs from the request.

    ``tier`` is coerced through ``str()`` and normalised the same way
    :func:`license_tier` normalises the stored claim, so a caller can
    pass ``"Pro"``, ``"pro"``, or ``"  PRO "`` and get the same answer.
    Non-string / empty input collapses to ``False`` (nothing "is tier
    empty-string"). Never raises; every underlying failure returns
    ``False`` so a scheduled paywall renderer never crashes on a bad
    install.
    """
    try:
        requested = str(tier).strip().lower()
    except Exception:
        return False
    if not requested:
        return False
    actual = license_tier()
    if actual is None:
        return False
    return actual == requested


def license_tier_at(epoch: int) -> str | None:
    """Perspective-epoch flavour of :func:`license_tier` -- "what tier
    would :func:`license_tier` have returned evaluated as of ``epoch``?"
    -- for a scheduled-audit / retrospective badge that wants to answer
    "what tier was this node on <date>?" without the caller having to
    snapshot the license state at that time or compare ``exp`` to a
    caller-supplied epoch themselves.

    Returns:
      * ``None`` when there is nothing trustworthy to surface AS OF
        ``epoch``: no license file on disk, an invalid signature (an
        attacker could stuff any tier into an unsigned body -- refused
        for every perspective), a signed key whose ``exp`` claim has
        already passed at ``epoch`` (retrospective on a lapsed key when
        ``epoch`` equals "now"; prospective on an active key when
        ``epoch`` is in the future beyond ``exp``), OR a signed payload
        whose ``tier`` claim is absent / non-string / empty after strip.
      * A lowercased, whitespace-stripped tier string otherwise. Casing
        is normalised the same way :func:`license_tier` normalises it,
        so a caller comparing against a hard-coded ``"pro"`` gets the
        same answer whichever helper it binds.

    ``epoch`` is coerced through ``int()``; ``bool`` is explicitly
    refused despite being an ``int`` subclass so a caller that passes
    ``True`` / ``False`` gets ``None`` back rather than a spurious "was
    the tier X at epoch 1?" classification. A non-numeric value
    collapses to ``None`` so a caller cannot silently mis-gate on a
    typo -- the conservative fallback since ``None`` implies no
    entitlement, matching the never-mis-gate posture of the
    surrounding ``_at`` family.

    When ``epoch`` equals "now", this scalar must agree with
    :func:`license_tier` for the same install -- both derive from the
    same signed ``tier`` claim, refuse the invalid-signature branch,
    and use the same ``exp <= cutoff`` boundary via
    :func:`license_state_at` / the current-time ``valid`` classifier,
    so the two scalars cannot disagree at the boundary. On any other
    epoch this helper answers the retrospective / prospective question
    :func:`license_tier` cannot -- e.g. "was this node Pro last
    Friday?" (``None`` on a key that has since been renewed but was
    already expired then) or "will this node still be Pro at our next
    quarterly audit?" (``None`` on an active key whose ``exp`` falls
    before the audit date).

    Never raises. Any underlying introspection failure (import error,
    corrupt install, cryptography-lib mismatch) collapses to ``None``
    -- same fallback as :func:`license_tier` -- so a scheduled audit
    tile bound to this helper never breaks on a partial install.

    Pairs with the sibling ``_at`` scalars
    (:func:`license_state_at`, :func:`is_expired_at`,
    :func:`days_until_expiry_at`, :func:`is_expiring_within_at`) at
    the row level: for the same ``epoch``, a caller can zip the five
    responses index-for-index and get the whole entitlement row for
    one install without the scalars catching each other disagreeing
    on the perspective-epoch classification.
    """
    if isinstance(epoch, bool):
        return None
    try:
        wanted = int(epoch)
    except (TypeError, ValueError):
        return None
    try:
        info = current_license_info()
    except Exception as exc:
        logger.debug("license: license_tier_at underlying read failed: %s", exc)
        return None
    if not isinstance(info, dict):
        return None
    status = info.get("status")
    if status == "invalid":
        # Signature-bogus branch: an unsigned body is untrusted whatever
        # the perspective, so the classification is time-independent.
        # Mirrors :func:`license_tier` -- payload-derived claims never
        # get to influence the answer here.
        return None
    exp = info.get("exp")
    if isinstance(exp, (int, float)) and int(exp) <= wanted:
        # Signed key that has already lapsed AS OF ``epoch`` -- refuse
        # for the same reason :func:`license_tier` refuses the expired
        # branch at "now": a lapsed Pro customer must stop rendering
        # as "Pro" once the perspective epoch is past ``exp``.
        return None
    tier = info.get("tier")
    if not isinstance(tier, str):
        return None
    normalized = tier.strip().lower()
    return normalized or None


def is_expired() -> bool:
    """True iff an installed, signature-valid license has an ``exp`` claim in
    the past.

    The boolean "already expired" gate that pairs with ``is_expiring_within``
    (renewal-window warning) and complements the loud red banner a UI might
    render off ``current_license_info().status == "expired"``: bind a paywall
    tile directly to this scalar without threading the full license envelope
    into the component.

    Returns ``False`` for every state that is not "installed, signed, past
    ``exp``": no license file, invalid signature (an attacker could stuff any
    ``exp`` into an unsigned body, so we refuse to trust it), perpetual /
    no-``exp`` keys, and active / future-``exp`` keys.

    Never raises. Any underlying introspection failure (import error,
    corrupt install, cryptography-lib mismatch) collapses to ``False`` so a
    caller can bind this into a boolean AND-chain without a try/except.
    """
    try:
        info = current_license_info()
        if not info:
            return False
        return info.get("status") == "expired"
    except Exception as exc:
        logger.warning("license: is_expired failed: %s", exc)
        return False



def is_expired_at(epoch: int) -> bool:
    """Boolean gate for "was the installed license expired evaluated as of
    ``epoch``?" -- the perspective-epoch flavour of :func:`is_expired`, for
    a scheduled-audit tile that wants to answer "would we have shown the
    expired banner on <date>?" without the caller having to snapshot the
    license state at that time or compare ``exp`` to a caller-supplied
    epoch themselves.

    Returns ``True`` iff a license is installed, signature-valid, carries
    an ``exp`` claim, AND ``exp <= epoch``. Returns ``False`` for every
    other state: no license file, invalid signature (an attacker could
    stuff any ``exp`` into an unsigned body, so we refuse to trust it),
    perpetual / no-``exp`` keys (nothing to compare against), and any
    ``exp`` value strictly greater than ``epoch``.

    When ``epoch`` equals "now", this predicate must agree with
    :func:`is_expired` for the same install -- both derive from the same
    signed ``exp`` claim and use the same ``<=`` cutoff, so the two
    scalars cannot disagree at the boundary. On any other epoch this
    helper answers the retrospective question that :func:`is_expired`
    cannot -- e.g. "was this key already expired last Friday?" (positive
    signal even on a key that has since been renewed) or "will this key
    be expired at our next quarterly audit?" (positive signal on an
    active key whose ``exp`` falls before the audit date).

    Deliberately lenient on expiry NOW, unlike :func:`is_expiring_at`
    (which refuses lapsed keys because a renewal-window predicate on a
    lapsed key would push callers to gate the WRONG UI). A retrospective
    "was this expired on <date>?" tile absolutely should keep firing
    ``True`` on a lapsed key -- that is the entire support scenario --
    so the "signature-valid" check here does NOT roll in the "not
    expired now" clause the sibling :func:`is_expiring_at` uses.

    ``epoch`` is coerced through ``int()``; ``bool`` is explicitly
    refused despite being an ``int`` subclass so a caller that passes
    ``True`` / ``False`` gets ``False`` back rather than a spurious
    "was the key expired at epoch 1?" answer. A non-numeric value
    collapses to ``False`` so a caller cannot silently mis-gate on a
    typo.

    Never raises. Any underlying introspection failure (import error,
    corrupt install, cryptography-lib mismatch) collapses to ``False``
    so a scheduled audit job never crashes on a bad install.
    """
    if isinstance(epoch, bool):
        # ``bool`` is a subclass of ``int``; refuse it explicitly so a
        # caller that passes ``True`` doesn't silently ask "was the key
        # expired at epoch 1?" and get a positive answer back.
        return False
    try:
        wanted = int(epoch)
    except (TypeError, ValueError):
        return False
    try:
        exp = license_expires_at()
    except Exception as exc:
        logger.debug("license: is_expired_at underlying read failed: %s", exc)
        return False
    if not isinstance(exp, int):
        # ``license_expires_at`` returns None for no-license, invalid-
        # signature, and perpetual branches. Nothing to compare against
        # in any of those cases.
        return False
    return exp <= wanted


def is_perpetual() -> bool:
    """True iff an installed, signature-valid license carries no ``exp`` claim.

    A "lifetime" key never expires, so a paywall UI wants to hide the renewal
    counter and render a "Lifetime" badge instead of "Expires in N days".
    This scalar answers that gate directly without the caller having to check
    ``current_license_info()["exp"] is None`` AND rule out the invalid /
    no-license branches (both of which also collapse ``exp`` to ``None`` but
    aren't perpetual -- they're *no trustworthy license at all*).

    Returns ``False`` for: no license file, invalid signature (untrusted body
    -- we don't infer "perpetual" from an unsigned payload), and any signed
    key that carries an ``exp`` claim regardless of active-vs-expired.

    Never raises. Any underlying introspection failure collapses to ``False``.
    """
    try:
        info = current_license_info()
        if not info:
            return False
        # The invalid-signature branch of ``current_license_info`` collapses
        # ``exp`` to ``None`` on purpose (we don't trust an unsigned body), so
        # a naive ``exp is None`` check would misfire and label a *forged*
        # license as "perpetual". Rule the invalid branch out explicitly.
        if info.get("status") == "invalid":
            return False
        return info.get("exp") is None
    except Exception as exc:
        logger.warning("license: is_perpetual failed: %s", exc)
        return False


def pro_installed_version() -> str | None:
    """Public alias for :func:`_pro_installed_version` -- the on-disk
    ``clawmetry-pro`` package version, or ``None`` if the paid wheel is
    not importable.

    Kept as a thin wrapper so external callers (routes, CLI, dashboards)
    can bind to a stable public name without reaching into the underscore
    helper. The underlying reader is idempotent (pure ``importlib.metadata``
    lookup) and never raises; this wrapper preserves both properties.
    """
    try:
        return _pro_installed_version()
    except Exception as exc:
        logger.debug("license: pro_installed_version wrapper failed: %s", exc)
        return None


def pro_installed() -> bool:
    """Scalar gate for "is the paid wheel actually importable right now?"

    Returns ``True`` iff :func:`pro_installed_version` returns a non-empty
    version string. Every other state -- wheel never provisioned, wheel
    unpacked but ``importlib.metadata`` can't see it, transient
    introspection failure -- collapses to ``False`` so a paywall renderer
    or a health tile bound to this helper never crashes on a partial
    install.

    Complements :func:`is_tier` / :func:`license_tier` (which read the
    license *claim*): a healthy Pro install must have both a signed
    Pro-tier claim AND the wheel on-disk. Splitting the two lets an
    operator diagnose "activated but wheel missing" (download failed,
    ``CLAWMETRY_OFFLINE=1`` on a fresh install, air-gapped node) from
    "wheel installed but license expired" (paid feature stops unlocking
    on renewal lapse).

    Never raises.
    """
    return bool(pro_installed_version())


def pro_installation_info() -> dict:
    """Operator-facing description of the ``clawmetry-pro`` install state.

    Combines the two independent facts a paywall / install-health UI
    typically wants together:

    * ``installed`` / ``version`` -- can Python actually import
      ``clawmetry-pro`` right now? (Live ``importlib.metadata`` probe.)
    * ``marker`` -- the ``~/.clawmetry/pro_installed.json`` sidecar written
      by :func:`_write_pro_marker` at provision time
      (``installed_at`` unix seconds, ``source``, ``node_id``, the
      ``version`` recorded at write time). ``{}`` when the marker file is
      missing or unreadable.

    The two can disagree in normal operation (marker present but wheel
    was pip-uninstalled; wheel present but marker never written on a
    pre-marker install), and that disagreement is exactly what an
    operator debugging a paywall glitch needs to see, so both are
    surfaced side-by-side rather than collapsed.

    Never raises -- any underlying failure degrades to
    ``{installed: False, version: None, marker: {}}`` so a UI bound to
    this helper never breaks on a partial install."""
    try:
        version = pro_installed_version()
    except Exception as exc:
        logger.debug("license: pro_installation_info version read failed: %s", exc)
        version = None
    try:
        marker = _read_pro_marker()
    except Exception as exc:
        logger.debug("license: pro_installation_info marker read failed: %s", exc)
        marker = {}
    if not isinstance(marker, dict):
        marker = {}
    return {
        "installed": bool(version),
        "version": version,
        "marker": marker,
    }


def pro_installed_at() -> int | None:
    """Scalar view onto the ``installed_at`` field of the ``clawmetry-pro``
    provisioning marker (``~/.clawmetry/pro_installed.json``) -- the epoch
    timestamp the paid wheel was first laid down on this node -- for a
    "pro installed: <date>" row that wants ONE integer rather than the
    whole :func:`pro_installation_info` envelope.

    Returns:
      * ``None`` when there is nothing meaningful to surface: the marker
        file is missing (wheel was never provisioned OR was provisioned by
        a pre-marker version of ClawMetry), the marker exists but has no
        ``installed_at`` key, or the value carried by the marker is
        non-numeric / negative.
      * A positive epoch integer otherwise -- the exact timestamp written
        by :func:`_write_pro_marker` at provision time.

    Deliberately independent of ``importlib.metadata`` -- an operator can
    have the marker on disk (wheel was provisioned yesterday) even when
    Python cannot currently import ``clawmetry-pro`` (wheel was pip-
    uninstalled since). That disagreement is exactly what a paywall-
    debugging tile wants to see, so this scalar answers "when was the
    marker last written?" without collapsing to :func:`pro_installed`.

    Pairs with :func:`pro_install_age_days` the way
    :func:`license_issued_at` pairs with :func:`license_age_days`: this
    getter surfaces the raw epoch for a debug row, that helper answers the
    "how old" derived integer without the caller having to compute
    ``(now - installed_at) // 86400`` themselves.

    Never raises. Any exception under the hood degrades to ``None`` so a
    UI tile bound to this helper never breaks on a partial install.
    """
    try:
        marker = _read_pro_marker()
    except Exception as exc:
        logger.debug("license: pro_installed_at marker read failed: %s", exc)
        return None
    if not isinstance(marker, dict):
        return None
    installed_at = marker.get("installed_at")
    if not isinstance(installed_at, (int, float)):
        return None
    if isinstance(installed_at, bool):
        # ``bool`` is a subclass of ``int``; refuse it explicitly so a
        # marker that somehow contains ``{"installed_at": true}`` collapses
        # to ``None`` rather than surfacing as epoch 1.
        return None
    if installed_at <= 0:
        return None
    return int(installed_at)


def pro_install_age_days() -> int | None:
    """Scalar view onto how long ago the ``clawmetry-pro`` wheel was
    provisioned on this node -- days since the ``installed_at`` field of
    the provisioning marker -- for a support/audit tile that wants ONE
    integer rather than computing ``(now - installed_at) // 86400`` at
    every call site.

    Returns:
      * ``None`` when there is nothing meaningful to derive: no marker
        file, a marker with no ``installed_at`` key, or a marker whose
        ``installed_at`` value is non-numeric / non-positive.
      * A non-negative integer number of days otherwise. Zero on the day
        of provisioning; grows monotonically thereafter.

    Days are floor-divided from seconds ``(now - installed_at) // 86400``,
    matching how :func:`license_age_days` derives its counterpart from the
    signed ``iat`` claim so the two scalars never disagree at the day
    boundary. Clamped to ``max(0, ...)`` to guard against clock skew (an
    ``installed_at`` in the future would otherwise render as a negative
    age and break ``f"{age} days old"`` formatting).

    Pairs with :func:`pro_installed_at` the way :func:`license_age_days`
    pairs with :func:`license_issued_at`: raw epoch for the debug row,
    derived integer for the display tile, both reading the same marker so
    a UI binding both cannot catch them disagreeing on the same install.

    Never raises. Any exception under the hood degrades to ``None`` so a
    scheduled audit tile never crashes on a bad install.
    """
    import time as _t

    try:
        installed = pro_installed_at()
    except Exception as exc:
        logger.debug("license: pro_install_age_days underlying read failed: %s", exc)
        return None
    if not isinstance(installed, int):
        return None
    try:
        age = int((_t.time() - installed) // 86400)
    except Exception as exc:
        logger.debug("license: pro_install_age_days arithmetic failed: %s", exc)
        return None
    return age if age >= 0 else 0


def pro_install_age_days_at(epoch: int) -> int | None:
    """Scalar view of "how many days from ``installed_at`` to ``epoch``?" --
    the perspective-epoch flavour of :func:`pro_install_age_days`, for a
    scheduled-audit / retrospective tile that wants to answer "how old
    was the ``clawmetry-pro`` install as of <date>?" without the caller
    having to snapshot the marker state at that time or compute
    ``(epoch - installed_at) // 86400`` at every call site.

    Returns:
      * ``None`` when there is nothing meaningful to derive: no marker
        file on disk, a marker with no ``installed_at`` key, a marker
        whose ``installed_at`` value is non-numeric / non-positive, OR
        a non-numeric / bool ``epoch`` argument.
      * A signed integer number of days otherwise. Zero when ``epoch``
        equals the ``installed_at`` second; positive when ``epoch`` is
        after ``installed_at`` (the normal case -- "N days old as of
        <date>"); negative when ``epoch`` is BEFORE ``installed_at``
        (support scenario: "the operator rolled a machine back to a
        pre-provisioning timestamp -- how far before install were we?").

    Deliberately NOT clamped to ``max(0, ...)`` -- unlike the "now"
    flavour :func:`pro_install_age_days`, which clamps because clock-
    skew is the only way ``installed_at`` can be in the future when
    reading against ``time.time()``. Here the caller EXPLICITLY passes
    a perspective epoch, so a negative result is a real, actionable
    signal (they asked a question that only makes sense pre-install),
    not clock skew to be hidden. Mirrors the signed-integer posture of
    :func:`license_age_days_at`, which returns negative days when the
    perspective epoch is before ``iat``.

    Days are floor-divided from seconds ``(epoch - installed_at) //
    86400``, matching how :func:`pro_install_age_days` derives its
    "now" counterpart from ``(now - installed_at)`` so the two scalars
    never disagree at the day boundary when ``epoch`` equals the
    current time.

    ``epoch`` is coerced through ``int()``; ``bool`` is explicitly
    refused despite being an ``int`` subclass so a caller that passes
    ``True`` / ``False`` gets ``None`` rather than a spurious "days
    from installed_at to epoch 1" number. A non-numeric value collapses
    to ``None`` so a caller cannot silently miscount on a typo.

    Pairs with :func:`pro_installed_at` the way
    :func:`license_age_days_at` pairs with :func:`license_issued_at`:
    both derive from the same marker so they cannot disagree at the
    day boundary. The perspective-epoch flavour lets a scheduled audit
    tile answer "how old was the pro wheel when we shipped that build
    last Friday?" without having to snapshot the marker state at those
    times.

    Independent of live importability -- an operator can have the
    marker on disk (wheel was provisioned yesterday) even when Python
    cannot currently import ``clawmetry-pro`` (wheel was pip-
    uninstalled since), and the age still refers to the marker. Use
    :func:`pro_installed` alongside this scalar for the live-import
    signal.

    Never raises. Any exception under the hood degrades to ``None`` so
    a scheduled audit job never crashes on a bad install.
    """
    if isinstance(epoch, bool):
        # ``bool`` is a subclass of ``int``; refuse it explicitly so a
        # caller that passes ``True`` doesn't silently ask "days from
        # installed_at to epoch 1?" and get a very negative number back.
        return None
    try:
        wanted = int(epoch)
    except (TypeError, ValueError):
        return None
    try:
        installed = pro_installed_at()
    except Exception as exc:
        logger.debug("license: pro_install_age_days_at underlying read failed: %s", exc)
        return None
    if not isinstance(installed, int):
        return None
    try:
        return (wanted - installed) // 86400
    except Exception as exc:
        logger.debug("license: pro_install_age_days_at arithmetic failed: %s", exc)
        return None


def license_nodes() -> int | None:
    """Scalar view onto the installed license's ``nodes`` claim -- the paid
    node-coverage count -- for a fleet/capacity tile that wants ONE integer
    rather than the whole :func:`current_license_info` envelope.

    Returns:
      * ``None`` when there is nothing trustworthy to surface:
        no license file on disk, an invalid signature (the payload can't
        be trusted -- an attacker could stuff any ``nodes`` count into an
        unsigned body), an expired license (a lapsed customer must not
        keep rendering as "5 nodes covered"), OR a signed payload whose
        ``nodes`` claim is absent / non-numeric / less than 1.
      * A positive integer otherwise -- the covered node count.

    Mirrors the "refuse expired keys" posture already used by
    :func:`license_tier`, so a fleet capacity tile bound to this scalar
    cannot keep rendering the paid coverage on a lapsed install. A caller
    who wants the CLAIM even on an expired key (support: "how many nodes
    was this key SUPPOSED to cover?") should keep reading
    :func:`current_license_info` directly and pull ``nodes`` there.

    Never raises. Any exception under the hood degrades to ``None`` so a
    dashboard tile bound to this helper never breaks on a partial install.
    """
    try:
        info = current_license_info()
    except Exception as exc:
        logger.debug("license: license_nodes underlying read failed: %s", exc)
        return None
    if not isinstance(info, dict):
        return None
    if not info.get("valid"):
        # invalid-signature and expired branches both collapse to None on
        # purpose -- see docstring for the fleet-tile rationale.
        return None
    nodes = info.get("nodes")
    try:
        n = int(nodes)
    except (TypeError, ValueError):
        return None
    return n if n >= 1 else None


def is_within_node_limit(nodes: int) -> bool:
    """Boolean gate for "does connecting the Nth node fit under my license?"

    Returns ``True`` iff a license is installed, signature-valid, NOT
    expired, its ``nodes`` claim resolves to a positive integer, AND the
    caller's ``nodes`` value is between 1 and that limit inclusive. Every
    other state returns ``False``: no license, invalid signature, expired
    key, missing/non-numeric ``nodes`` claim, ``nodes<=0``, or a live limit
    that simply does not cover the caller's count.

    ``nodes`` is coerced through ``int()``; non-numeric input, zero, or a
    negative count collapses to ``False`` (a fleet of "connect -5 nodes"
    never fits any coverage). Never raises; every underlying failure
    returns ``False`` so a scheduled fleet-capacity check never crashes
    on a bad install.

    Pairs with :func:`license_nodes` the way :func:`is_expiring_within`
    pairs with :func:`days_until_expiry` -- the scalar reports the raw
    number for tiles, this bool answers the yes/no question a gate needs
    without the caller having to compare against the limit themselves.
    """
    try:
        requested = int(nodes)
    except (TypeError, ValueError):
        return False
    if requested < 1:
        return False
    limit = license_nodes()
    if limit is None:
        return False
    return requested <= limit


def has_license() -> bool:
    """True iff a license file exists on disk at :data:`LICENSE_PATH`.

    The bare install-state gate: answers "does this operator have ANY
    license file at all?" without caring whether the signature verifies,
    whether the ``exp`` claim is in the past, or whether the payload
    tier/nodes are anything reasonable. A dashboard that wants to render
    a subtly-different empty state for "Free (never activated)" vs
    "Free (license expired / broken)" binds to this scalar; a paywall
    tile that only cares about entitlement should use
    :func:`is_license_valid` instead.

    Complements :func:`license_tier` / :func:`is_tier`, which both
    collapse to ``None`` / ``False`` on the invalid-signature and
    expired branches -- callers wanting to distinguish "has a broken
    file" from "has nothing" need this presence gate as a separate
    signal.

    Never raises. Any underlying filesystem failure (perms, race with
    a concurrent ``deactivate``) collapses to ``False`` so a paywall
    renderer bound to this scalar never crashes on a partial install.
    """
    try:
        return os.path.isfile(LICENSE_PATH)
    except Exception as exc:
        logger.debug("license: has_license failed: %s", exc)
        return False


def is_license_valid() -> bool:
    """True iff a license is installed, signature-valid, AND not expired.

    The single boolean gate every paywall tile actually wants: "is this
    node entitled right now?". Pairs with :func:`has_license` -- the
    presence gate answers "does a file exist?", this one answers "is
    the file trustworthy AND live?". A UI wanting to distinguish "no
    license" from "broken license" from "lapsed license" from "live
    license" reads both scalars together (plus :func:`is_expired` /
    :func:`current_license_info().status` for the specific broken /
    lapsed reason).

    Returns ``False`` on every one of:

    * No license file on disk (:func:`has_license` is ``False``).
    * File exists but signature does not verify (an attacker could
      stuff any tier/nodes/exp into an unsigned body, so we treat the
      whole install as untrusted).
    * File exists, signature verifies, but ``exp`` is in the past.

    Returns ``True`` iff the ``current_license_info().valid`` flag is
    truthy for the installed file -- which is the same source of truth
    :func:`license_tier` / :func:`is_tier` / :func:`license_nodes`
    already use to gate their entitlement scalars, so a UI binding all
    four sees a consistent snapshot.

    Never raises. Any underlying introspection failure collapses to
    ``False`` so a scheduled paywall renderer never crashes on a bad
    install.
    """
    try:
        info = current_license_info()
    except Exception as exc:
        logger.warning("license: is_license_valid failed: %s", exc)
        return False
    if not isinstance(info, dict):
        return False
    return bool(info.get("valid"))


def is_license_valid_at(epoch: int) -> bool:
    """Boolean gate for "would the installed license have been valid
    evaluated as of ``epoch``?" -- the perspective-epoch flavour of
    :func:`is_license_valid`, for a scheduled-audit / retrospective
    paywall tile that wants to answer "would this node have been
    entitled on <date>?" without the caller having to snapshot the
    license state at that time or fold the ``exp`` claim against a
    caller-supplied epoch themselves.

    Returns ``True`` iff a license is installed, signature-valid, AND
    either carries no ``exp`` claim (perpetual key) OR ``exp > epoch``.
    Returns ``False`` for every other state: no license file, invalid
    signature (an attacker could stuff any tier/nodes/exp into an
    unsigned body, so we refuse to trust it), and any signed key whose
    ``exp`` value is at or before ``epoch``.

    Semantics rest on :func:`license_state_at` -- ``"active"`` at the
    perspective epoch means exactly "signature-valid AND (perpetual OR
    ``exp > epoch``)", which is the whole is-this-entitled question this
    predicate answers. So per-value parity with the sibling ``_at``
    trio (:func:`is_expired_at`, :func:`license_state_at`,
    :func:`days_until_expiry_at`) is guaranteed at the row level: a UI
    can zip the four responses index-for-index without ever catching
    them disagreeing on the same epoch for the same install.

    When ``epoch`` equals "now", this predicate must agree with
    :func:`is_license_valid` for the same install -- both derive from
    the same signed ``exp`` claim and share the same signature-check
    path via :func:`current_license_info`, so the two scalars cannot
    disagree at the boundary. On any other epoch this helper answers
    the retrospective / prospective question :func:`is_license_valid`
    cannot -- e.g. "was this key entitled last Friday?" (positive
    signal even on a key that has since lapsed) or "will this key be
    entitled at our next quarterly audit?" (negative signal on an
    active key whose ``exp`` falls before the audit date).

    ``epoch`` is coerced through ``int()``; ``bool`` is explicitly
    refused despite being an ``int`` subclass so a caller that passes
    ``True`` / ``False`` gets ``False`` back rather than a spurious
    "was the key valid at epoch 1?" answer. A non-numeric value
    collapses to ``False`` -- the conservative "no entitlement"
    fallback, matching the never-mis-gate posture of the surrounding
    ``_at`` family: a mis-typed epoch cannot silently unlock a Pro
    feature.

    Never raises. Any underlying introspection failure (import error,
    corrupt install, cryptography-lib mismatch) collapses to ``False``
    so a scheduled audit job never crashes on a bad install AND never
    falsely asserts entitlement it can't verify.

    Pairs with :func:`is_expired_at` at the singular level -- the two
    are complementary on a signature-valid, non-perpetual key
    (``is_expired_at(e) == not is_license_valid_at(e)``) but diverge on
    the invalid-signature and no-license branches: those collapse BOTH
    to ``False`` on purpose, because "not expired" on an unsigned body
    is not the same as "still entitled". A UI wanting to distinguish
    "no license" / "broken license" / "lapsed at that time" / "valid
    at that time" reads this helper together with :func:`is_expired_at`
    and :func:`license_state_at`.
    """
    if isinstance(epoch, bool):
        # ``bool`` is a subclass of ``int``; refuse it explicitly so a
        # caller that passes ``True`` doesn't silently ask "was the key
        # valid at epoch 1?" and get a positive answer back.
        return False
    try:
        wanted = int(epoch)
    except (TypeError, ValueError):
        return False
    try:
        state = license_state_at(wanted)
    except Exception as exc:
        logger.debug(
            "license: is_license_valid_at underlying read failed: %s", exc
        )
        return False
    return state == "active"


def license_subject() -> str | None:
    """Scalar view onto the installed license's ``sub`` claim -- the customer
    identifier the license was issued to (typically an account id or a
    contact email) -- for a "Licensed to <X>" badge / support-context tile
    that wants ONE string rather than the whole :func:`current_license_info`
    envelope.

    Returns:
      * ``None`` when there is nothing trustworthy to surface:
        no license file on disk, an invalid signature (the payload can't
        be trusted -- an attacker could stuff any ``sub`` string into an
        unsigned body and impersonate a real customer), an expired license
        (a lapsed customer must not keep rendering as the account holder
        for gating / audit purposes), OR a signed payload whose ``sub``
        claim is absent / non-string / an empty string after strip.
      * The stripped subject string otherwise -- the operator-visible
        identifier bound to the current license.

    Casing is preserved: subjects are typically email addresses / account
    ids where case can matter for exact-match comparisons, so a UI badge
    renders the customer-facing form verbatim. :func:`is_subject` handles
    case-insensitive matching on top for callers that want it.

    Mirrors the "refuse expired keys" posture already used by
    :func:`license_tier` / :func:`license_nodes`, so a support tile bound
    to this scalar cannot keep rendering the paid customer on a lapsed
    install. A caller who wants the CLAIM even on an expired key (support:
    "who was this key issued to?") should keep reading
    :func:`current_license_info` directly and pull ``sub`` there.

    Never raises. Any exception under the hood degrades to ``None`` so a
    dashboard tile bound to this helper never breaks on a partial install.
    """
    try:
        info = current_license_info()
    except Exception as exc:
        logger.debug("license: license_subject underlying read failed: %s", exc)
        return None
    if not isinstance(info, dict):
        return None
    if not info.get("valid"):
        # invalid-signature and expired branches both collapse to None on
        # purpose -- see docstring for the support-tile rationale.
        return None
    sub = info.get("sub")
    if not isinstance(sub, str):
        return None
    stripped = sub.strip()
    return stripped or None


def is_subject(subject: str) -> bool:
    """Boolean gate for "is this license issued to subject <X>?" UIs.

    Returns ``True`` iff a license is installed, signature-valid, NOT
    expired, its ``sub`` claim resolves to a non-empty string, AND that
    string matches ``subject`` (case-insensitive, whitespace-stripped on
    both sides). Every other state returns ``False``: no license, invalid
    signature, expired key, missing/empty ``sub`` claim, or a live
    subject that simply differs from the request.

    ``subject`` is coerced through ``str()`` and normalised the same way
    the stored claim is normalised, so a caller can pass ``"acct_test"``,
    ``"  acct_test "``, or ``"ACCT_TEST"`` and get the same answer.
    Non-string / empty input collapses to ``False`` (nothing "is subject
    empty-string"). Never raises; every underlying failure returns
    ``False`` so a scheduled paywall / audit check never crashes on a
    bad install.

    Pairs with :func:`license_subject` the way :func:`is_tier` pairs
    with :func:`license_tier` -- the scalar reports the raw string for a
    badge tile, this bool answers the yes/no question a multi-tenant
    dispatcher or a license-transfer detector needs without the caller
    having to normalise the string themselves.
    """
    try:
        requested = str(subject).strip().lower()
    except Exception:
        return False
    if not requested:
        return False
    actual = license_subject()
    if actual is None:
        return False
    return actual.lower() == requested


def license_permissions_safe() -> bool | None:
    """Scalar view onto the installed license file's on-disk permission
    hygiene -- for a security-posture tile that wants ONE tri-state
    rather than the whole :func:`current_license_info` envelope.

    The license key is a bearer secret: anyone holding the file can
    present it to the offline verifier. On POSIX the file must not be
    group/world readable; a 0o644 (default umask) key file is a
    silently-leaked bearer credential.

    Returns:
      * ``None`` when there is no license file on disk -- nothing to
        check, and a UI tile bound to this scalar should render as
        "not applicable" rather than "safe" (a Free install has no
        credential to protect).
      * ``True`` when the file exists AND has no group/world mode bits
        set (POSIX), OR when running on Windows where POSIX mode bits
        do not apply and the default ACL restricts the file to the
        owning user.
      * ``False`` when the file exists on POSIX AND has any of the
        group/other bits set (``0o077``) -- exactly the state a
        "tighten file permissions" affordance should highlight.

    Deliberately orthogonal to signature validity: a tampered or expired
    license file still has meaningful hygiene state (in fact, MORE
    urgent to surface -- a loose-permission key file may indicate the
    same corruption that broke the signature). So the return value
    depends only on existence + POSIX mode, never on the payload
    branches that :func:`license_tier` / :func:`license_subject` gate
    themselves on.

    Never raises. Any exception under the hood degrades to ``None`` so
    a scheduled security-posture check never crashes on a bad install.
    """
    try:
        if not os.path.isfile(LICENSE_PATH):
            return None
        return _file_permissions_safe(LICENSE_PATH)
    except Exception as exc:
        logger.debug("license: license_permissions_safe read failed: %s", exc)
        return None


def license_file_mode() -> str | None:
    """Scalar view onto the installed license file's POSIX mode -- for a
    security-posture / debug tile that wants the raw octal (e.g.
    ``"0644"``) rather than the whole :func:`current_license_info`
    envelope.

    Returns:
      * ``None`` when there is nothing meaningful to surface: no
        license file on disk, OR running on Windows where POSIX mode
        bits do not apply.
      * A four-character octal string like ``"0600"`` (safe),
        ``"0644"`` (world-readable), or ``"0666"`` (world-writable)
        otherwise. Format is stable and matches ``chmod`` -- the same
        digits an operator would pass to ``chmod 0600 <path>`` to fix
        an unsafe key file.

    Deliberately orthogonal to signature validity: the on-disk mode is
    a file-hygiene fact, not a license-payload fact, so the return
    value depends only on existence + platform, never on the payload
    branches that :func:`license_tier` / :func:`license_subject` gate
    themselves on. Pairs with :func:`license_permissions_safe` the way
    :func:`license_nodes` pairs with :func:`is_within_node_limit` --
    this scalar surfaces the raw mode for a debug row, that bool
    answers the yes/no question a security tile needs without the
    caller having to parse octal themselves.

    Never raises. Any exception under the hood degrades to ``None`` so
    a scheduled hygiene check never crashes on a stat() failure.
    """
    try:
        if os.name != "posix":
            return None
        if not os.path.isfile(LICENSE_PATH):
            return None
        mode = os.stat(LICENSE_PATH).st_mode & 0o777
        return f"{mode:04o}"
    except Exception as exc:
        logger.debug("license: license_file_mode read failed: %s", exc)
        return None


def license_issued_at() -> int | None:
    """Scalar view onto the installed license's ``iat`` claim -- the epoch
    timestamp the key was signed at -- for a "license issued: <date>" row
    that wants ONE integer rather than the whole
    :func:`current_license_info` envelope.

    Returns:
      * ``None`` when there is nothing trustworthy to surface: no license
        file on disk, an invalid signature (the payload can't be trusted --
        an attacker could stuff any ``iat`` into an unsigned body), OR a
        signed payload whose ``iat`` claim is absent / non-numeric.
      * A positive epoch integer otherwise -- the exact timestamp carried
        by the signed payload, unmodified.

    Deliberately lenient on expiry, unlike :func:`license_tier` /
    :func:`license_nodes` / :func:`license_subject`: an expired but
    signature-valid key still carries a meaningful ``iat`` (support
    scenario: "how old is this lapsed key?") and callers would otherwise
    have to fall back to ``/api/license/status``. Mirrors the "works on
    expired keys" posture of :func:`days_until_expiry`, which continues to
    return signed integer days past expiry so a UI can render "expired 12
    days ago" without special-casing.

    Never raises. Any exception under the hood degrades to ``None`` so a
    UI tile bound to this helper never breaks on a partial install.
    """
    try:
        info = current_license_info()
    except Exception as exc:
        logger.debug("license: license_issued_at underlying read failed: %s", exc)
        return None
    if not isinstance(info, dict):
        return None
    if info.get("status") == "invalid":
        # Invalid-signature branch: payload cannot be trusted, refuse to
        # surface any payload-derived claim (mirrors the tier / nodes /
        # subject scalars). Expired-but-signed keys still carry a
        # meaningful ``iat`` so we do NOT refuse them here.
        return None
    issued = info.get("issued_at")
    return int(issued) if isinstance(issued, int) else None


def is_pubkey_fingerprint(fp: str) -> bool:
    """Boolean gate for "is this install verifying against pubkey <FP>?" UIs.

    Returns ``True`` iff :func:`pubkey_fingerprint` resolves to a non-empty
    SHA-256 hex string AND ``fp`` matches it under a tolerant normalisation:

      * whitespace stripped on both sides,
      * lowercased (SHA-256 hex is case-insensitive),
      * ``:`` separators removed -- many display formats print
        fingerprints as ``ab:cd:ef:...`` and an operator comparing a
        pasted string against the canonical one should not have to strip
        colons themselves,
      * short-form (16-char, matching :func:`pubkey_info`'s
        ``fingerprint_short``) also matches if it is a prefix of the
        full digest, so a UI can accept either the full digest or the
        short-form printed on ``/api/license/pubkey``.

    Every other state returns ``False``: unparseable embedded PEM
    (fingerprint helper collapses to ``None``), non-string / empty input,
    or a normalised digest that simply differs from the trust anchor.
    Never raises; every underlying failure returns ``False`` so a
    scheduled trust-anchor audit never crashes on a bad install.

    Pairs with :func:`pubkey_fingerprint` the way :func:`is_subject`
    pairs with :func:`license_subject` -- the scalar reports the raw
    hex digest for a badge tile, this bool answers the yes/no question
    a supply-chain / trust-anchor audit needs without the caller having
    to normalise the string themselves.
    """
    try:
        requested = str(fp).strip().lower().replace(":", "")
    except Exception:
        return False
    if not requested:
        return False
    # Only hex is valid -- reject accidental non-hex input up-front so
    # ``is_pubkey_fingerprint("not a fingerprint")`` collapses to ``False``
    # instead of doing a full comparison against the real digest.
    if not all(c in "0123456789abcdef" for c in requested):
        return False
    try:
        actual = pubkey_fingerprint()
    except Exception:
        return False
    if not isinstance(actual, str) or not actual:
        return False
    actual_norm = actual.strip().lower()
    if len(requested) == 64:
        return actual_norm == requested
    if len(requested) == 16:
        return actual_norm.startswith(requested)
    return False


def license_age_days() -> int | None:
    """Scalar view onto the installed license's age -- days since the
    ``iat`` claim -- for a support/audit tile that wants ONE integer
    rather than computing ``(now - iat) // 86400`` at every call site.

    Returns:
      * ``None`` when there is nothing meaningful to derive: no license
        file, an invalid signature, or a signed payload whose ``iat``
        claim is absent / non-numeric.
      * A non-negative integer number of days otherwise. Zero on the day
        of issuance; grows monotonically thereafter.

    Days are floor-divided from seconds (``(now - iat) // 86400``),
    matching how :func:`days_until_expiry` derives its counterpart from
    ``(exp - now)`` so the two scalars never disagree at the day
    boundary. Clamped to ``max(0, ...)`` to guard against clock skew
    (``iat`` in the future would otherwise render as a negative age).

    Pairs with :func:`license_issued_at` the way :func:`days_until_expiry`
    pairs with the raw ``exp`` claim on :func:`current_license_info` --
    the raw scalar surfaces the epoch, this one surfaces the caller-
    friendly derived integer without either side having to do the arithmetic.

    Never raises. Any exception under the hood degrades to ``None`` so a
    scheduled audit tile never crashes on a bad install.
    """
    import time as _t

    try:
        issued = license_issued_at()
    except Exception as exc:
        logger.debug("license: license_age_days underlying read failed: %s", exc)
        return None
    if not isinstance(issued, int):
        return None
    try:
        age = int((_t.time() - issued) // 86400)
    except Exception as exc:
        logger.debug("license: license_age_days arithmetic failed: %s", exc)
        return None
    return age if age >= 0 else 0


def license_age_days_at(epoch: int) -> int | None:
    """Scalar view of "how many days from ``iat`` to ``epoch``?" -- the
    perspective-epoch flavour of :func:`license_age_days`, for a
    scheduled-audit / retrospective tile that wants to answer "how old
    was the license as of <date>?" without the caller having to snapshot
    the license state at that time or compute ``(epoch - iat) // 86400``
    at every call site.

    Returns:
      * ``None`` when there is nothing meaningful to derive: no license
        file on disk, an invalid signature (the payload can't be trusted
        -- an attacker could stuff any ``iat`` into an unsigned body), a
        signed payload whose ``iat`` claim is absent / non-numeric, OR a
        non-numeric / bool ``epoch`` argument.
      * A signed integer number of days otherwise. Zero when ``epoch``
        equals the ``iat`` second; positive when ``epoch`` is after
        ``iat`` (the normal case -- "N days old as of <date>"); negative
        when ``epoch`` is BEFORE ``iat`` (support scenario: "the operator
        rolled a machine back to a pre-issuance timestamp -- how far
        before issuance were we?").

    Deliberately NOT clamped to ``max(0, ...)`` -- unlike the "now"
    flavour :func:`license_age_days`, which clamps because clock-skew is
    the only way ``iat`` can be in the future when reading against
    ``time.time()``. Here the caller EXPLICITLY passes a perspective
    epoch, so a negative result is a real, actionable signal (they asked
    a question that only makes sense pre-issuance), not clock skew to be
    hidden. Mirrors the signed-integer posture of
    :func:`days_until_expiry_at`, which returns negative days when the
    perspective epoch is past ``exp``.

    Days are floor-divided from seconds ``(epoch - iat) // 86400``,
    matching how :func:`license_age_days` derives its "now" counterpart
    from ``(now - iat)`` so the two scalars never disagree at the day
    boundary when ``epoch`` equals the current time.

    ``epoch`` is coerced through ``int()``; ``bool`` is explicitly
    refused despite being an ``int`` subclass so a caller that passes
    ``True`` / ``False`` gets ``None`` rather than a spurious "days
    from iat to epoch 1" number. A non-numeric value collapses to
    ``None`` so a caller cannot silently miscount on a typo.

    Deliberately lenient on expiry, mirroring :func:`license_age_days`:
    an expired-but-signature-valid key still carries a meaningful
    ``iat`` (support scenario: "how old was this lapsed key evaluated
    as of last Friday?") and callers would otherwise have to fall back
    to :func:`current_license_info`. The :func:`is_expired` /
    :func:`is_expiring_at` helpers independently carry the "past-
    expiry" signals for callers that DO want to hide the row on lapsed
    keys.

    Pairs with :func:`license_issued_at` the way
    :func:`days_until_expiry_at` pairs with :func:`license_expires_at`:
    both derive from the same ``iat`` claim so they cannot disagree at
    the day boundary. The perspective-epoch flavour lets a scheduled
    audit tile answer "how old was the key when we shipped that build
    last Friday?" without having to snapshot the license state at
    those times.

    Never raises. Any exception under the hood degrades to ``None`` so a
    scheduled audit job never crashes on a bad install.
    """
    if isinstance(epoch, bool):
        # ``bool`` is a subclass of ``int``; refuse it explicitly so a
        # caller that passes ``True`` doesn't silently ask "days from
        # iat to epoch 1?" and get a very negative number back.
        return None
    try:
        wanted = int(epoch)
    except (TypeError, ValueError):
        return None
    try:
        issued = license_issued_at()
    except Exception as exc:
        logger.debug("license: license_age_days_at underlying read failed: %s", exc)
        return None
    if not isinstance(issued, int):
        return None
    try:
        return (wanted - issued) // 86400
    except Exception as exc:
        logger.debug("license: license_age_days_at arithmetic failed: %s", exc)
        return None


# Canonical set of values :func:`license_state` may return. Kept in a frozenset
# so a caller (`if state in LICENSE_STATES: ...`) never accidentally accepts a
# typo like ``"actiev"`` as a valid state, and so :func:`is_state` can normalise
# / validate its input against the same source of truth the getter uses.
LICENSE_STATES = frozenset({"active", "expired", "invalid", "no_license"})


def license_state() -> str:
    """Scalar view onto the installed license's high-level lifecycle state --
    for a status badge / audit row that wants ONE string rather than the
    whole :func:`current_license_info` envelope.

    Returns one of :data:`LICENSE_STATES` -- never ``None``. Unlike the
    tier / nodes / subject scalars, "no license installed" is a real answer
    here (``"no_license"``), not a missing answer, so callers can bind a
    switch without a ``None`` branch:

      * ``"active"``   -- signature-valid AND not expired.
      * ``"expired"``  -- signature-valid but past its ``exp`` claim.
      * ``"invalid"``  -- file exists but signature is bogus (bit-flip,
        tamper, key rotated server-side, wrong-environment key).
      * ``"no_license"`` -- no license file on disk (the OSS-free branch).

    Mirrors the ``status`` field carried by :func:`current_license_info`
    exactly for the three file-exists branches, and adds ``"no_license"``
    for the None-info branch so the caller never has to translate
    ``current_license_info() is None`` themselves. On any introspection
    failure (import error, corrupt install, cryptography-lib mismatch) the
    helper degrades to ``"no_license"`` -- same fallback as
    :func:`has_license` -- so a UI tile bound to this helper never breaks
    on a partial install.

    Never raises. Pairs with :func:`is_state` the way :func:`license_tier`
    pairs with :func:`is_tier`: this getter surfaces the string for a
    display row, that matcher answers the "am I in state <X> right now?"
    gate without the caller having to string-compare themselves.
    """
    try:
        info = current_license_info()
    except Exception as exc:
        logger.debug("license: license_state underlying read failed: %s", exc)
        return "no_license"
    if info is None:
        return "no_license"
    if not isinstance(info, dict):
        return "no_license"
    status = info.get("status")
    if isinstance(status, str) and status in LICENSE_STATES:
        return status
    # Defensive: an unexpected status string (future refactor, downstream
    # patch) must never leak through as a bogus state -- collapse to
    # ``"invalid"`` since the file exists but we cannot classify it.
    return "invalid"


def is_state(state: str) -> bool:
    """Boolean gate for "is the installed license in state <X> right now?"

    Compares :func:`license_state` case-insensitively (after strip) to the
    supplied ``state``. Missing / empty / non-string input degrades to
    ``False`` -- matches the never-raise posture of :func:`is_tier` /
    :func:`is_subject` / :func:`is_within_node_limit`.

    Only values in :data:`LICENSE_STATES` can ever return ``True``; a
    typo like ``"actiev"`` collapses to ``False`` so a caller cannot
    silently mis-gate on a mis-spelled state name. Callers wanting to
    validate their input up-front can ``if requested in LICENSE_STATES:``
    against the same source of truth.

    Never raises. Any underlying failure of :func:`license_state`
    collapses this to ``False`` -- a UI tile bound to this gate stays
    "unclaimed" rather than falsely asserting an entitlement it can't
    verify.
    """
    try:
        requested = str(state).strip().lower() if state is not None else ""
    except Exception:
        return False
    if not requested or requested not in LICENSE_STATES:
        return False
    try:
        current = license_state()
    except Exception as exc:
        logger.debug("license: is_state underlying read failed: %s", exc)
        return False
    return current == requested


def license_state_at(epoch: int) -> str:
    """Perspective-epoch flavour of :func:`license_state` -- "what state
    would the installed license have reported evaluated as of ``epoch``?"
    -- for a scheduled-audit / retrospective status tile that wants to
    answer "would we have shown the expired banner on <date>?" without
    the caller having to snapshot the license state at that time or
    compare ``exp`` to a caller-supplied epoch themselves.

    Returns one of :data:`LICENSE_STATES` -- never ``None``. Like
    :func:`license_state`, "no license installed" is a real answer here
    (``"no_license"``), not a missing answer, so callers can bind a
    switch without a ``None`` branch:

      * ``"active"``   -- signature-valid AND (perpetual OR ``exp > epoch``).
      * ``"expired"``  -- signature-valid, carries an ``exp`` claim, AND
        ``exp <= epoch``. Retrospective on a lapsed key when ``epoch``
        equals "now"; prospective on an active key when ``epoch`` is in
        the future beyond ``exp``.
      * ``"invalid"``  -- file exists but signature is bogus (time-
        independent: the classification never changes with epoch, since
        an unsigned body is untrusted whatever the perspective).
      * ``"no_license"`` -- no license file on disk (also time-
        independent). Missing / non-numeric / bool ``epoch`` also
        degrades to ``"no_license"`` so a UI switch bound to a typo cannot
        silently mis-render as ``"active"``.

    When ``epoch`` equals "now", this scalar must agree with
    :func:`license_state` for the same install -- both derive from the
    same signed ``exp`` claim and use the same ``exp <= cutoff``
    boundary, so the two scalars cannot disagree. On any other epoch
    this helper answers the retrospective / prospective question
    :func:`license_state` cannot -- e.g. "was this key already expired
    last Friday?" (``"expired"`` even on a key that has since been
    renewed) or "will this key be expired at our next quarterly audit?"
    (``"expired"`` on an active key whose ``exp`` falls before the audit
    date).

    ``epoch`` is coerced through ``int()``; ``bool`` is explicitly
    refused despite being an ``int`` subclass so a caller that passes
    ``True`` / ``False`` gets ``"no_license"`` back rather than a
    spurious "was the key expired at epoch 1?" classification. A non-
    numeric value collapses to ``"no_license"`` so a caller cannot
    silently mis-gate on a typo -- the conservative fallback since
    ``"no_license"`` implies no entitlement, matching the never-mis-gate
    posture of the surrounding ``_at`` family.

    Never raises. Any underlying introspection failure (import error,
    corrupt install, cryptography-lib mismatch) collapses to
    ``"no_license"`` -- same fallback as :func:`license_state` -- so a
    scheduled audit tile bound to this helper never breaks on a partial
    install.

    Pairs with :func:`is_state_at` the way :func:`license_state` pairs
    with :func:`is_state`: this getter surfaces the perspective-epoch
    state string for an audit row, that matcher answers the "was the
    install in state <X> at <date>?" gate without the caller having to
    string-compare themselves.
    """
    if isinstance(epoch, bool):
        return "no_license"
    try:
        wanted = int(epoch)
    except (TypeError, ValueError):
        return "no_license"
    try:
        info = current_license_info()
    except Exception as exc:
        logger.debug("license: license_state_at underlying read failed: %s", exc)
        return "no_license"
    if info is None:
        return "no_license"
    if not isinstance(info, dict):
        return "no_license"
    status = info.get("status")
    if status == "invalid":
        # Signature-bogus branch: an unsigned body is untrusted whatever
        # the perspective, so the classification is time-independent.
        # Mirrors :func:`license_state` -- payload-derived claims never
        # get to influence the answer here.
        return "invalid"
    exp = info.get("exp")
    if not isinstance(exp, (int, float)):
        # Perpetual (no ``exp``) signed key -- never expires, so always
        # ``"active"`` regardless of epoch. Matches how
        # :func:`current_license_info` sets ``status="active"`` for a
        # perpetual key at "now".
        return "active"
    return "expired" if int(exp) <= wanted else "active"


def is_state_at(state: str, epoch: int) -> bool:
    """Perspective-epoch flavour of :func:`is_state` -- "was the installed
    license in state <X> evaluated as of ``epoch``?" -- for a scheduled-
    audit tile that wants to answer "would we have shown the expired
    banner on <date>?" without the caller having to snapshot the license
    state at that time.

    Compares :func:`license_state_at` case-insensitively (after strip)
    to the supplied ``state``. Missing / empty / non-string input
    degrades to ``False`` -- matches the never-raise posture of
    :func:`is_state` / :func:`is_expired_at`.

    Only values in :data:`LICENSE_STATES` can ever return ``True``; a
    typo like ``"actiev"`` collapses to ``False`` so a caller cannot
    silently mis-gate on a mis-spelled state name. Callers wanting to
    validate their input up-front can ``if requested in LICENSE_STATES:``
    against the same source of truth.

    ``epoch`` is coerced through :func:`license_state_at`; ``bool`` and
    non-numeric epochs are refused there and collapse this predicate to
    ``False`` (unless the caller also asked ``state="no_license"``, in
    which case the answer is truthfully ``True``: the perspective is
    unusable so we cannot claim any richer state -- exactly matching the
    conservative "no entitlement" fallback of :func:`license_state_at`).

    When ``epoch`` equals "now", this predicate must agree with
    :func:`is_state` for the same install and the same requested
    ``state`` -- both derive from the same signed ``exp`` claim and use
    the same ``<=`` cutoff via :func:`license_state_at` /
    :func:`license_state`, so the two scalars cannot disagree at the
    boundary. On any other epoch this helper answers the retrospective /
    prospective question :func:`is_state` cannot.

    Never raises. Any underlying failure of :func:`license_state_at`
    collapses this to ``False`` -- a scheduled audit job bound to this
    gate stays "unclaimed" rather than falsely asserting an entitlement
    it can't verify.
    """
    try:
        requested = str(state).strip().lower() if state is not None else ""
    except Exception:
        return False
    if not requested or requested not in LICENSE_STATES:
        return False
    try:
        current = license_state_at(epoch)
    except Exception as exc:
        logger.debug("license: is_state_at underlying read failed: %s", exc)
        return False
    return current == requested


def _license_epoch_batch_keys(epochs):
    """Shared iterable-of-epochs pre-parser for the ``_at_batch`` license
    helpers below.

    Yields ``(raw, key, parsed)`` triples where:

      * ``raw`` is the original input token (preserved so callers can
        identify the offending entry in error rows without a re-scan of
        their own list).
      * ``key`` is the normalisation key used for de-dup: ``str(parsed)``
        for a successfully parsed int, or ``("__bad__", repr(raw))`` for
        anything ``license_state_at`` / ``is_expired_at`` /
        :func:`days_until_expiry_at` would refuse. Splitting bad rows
        into their own key namespace stops a caller supplying ``[True,
        True]`` from collapsing to a single "bad" row -- each bogus
        input keeps its own slot so the output length still matches N
        for a batch that renders one row per input.
      * ``parsed`` is the coerced ``int`` (only meaningful when the row
        is well-formed; ``None`` for the bad-input path).

    Rejects ``bool`` explicitly (subclass of ``int`` -- would silently
    ask "epoch 1?") matching the scalar ``_at`` family's stance, and
    treats ``None`` / non-numeric strings the same way ``int()`` refuses
    them: as bad input. Preserves first-seen order of the good rows and
    of the ordered bad-input entries so the output is byte-stable across
    calls (the batch tests pin ``list(...) == list(...)`` on the same
    input).
    """
    seen = set()
    if epochs is None:
        return
    try:
        iterator = iter(epochs)
    except TypeError:
        return
    for raw in iterator:
        if isinstance(raw, bool):
            key = ("__bad__", repr(raw), id(raw))
            if key in seen:
                continue
            seen.add(key)
            yield raw, key, None
            continue
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            key = ("__bad__", repr(raw), id(raw))
            if key in seen:
                continue
            seen.add(key)
            yield raw, key, None
            continue
        key = str(parsed)
        if key in seen:
            continue
        seen.add(key)
        yield raw, key, parsed


def license_state_at_batch(epochs) -> list[dict]:
    """Per-value perspective-epoch license-state ladder for N epochs in
    ONE round-trip.

    Per-value axis batch sibling of :func:`license_state_at`. Fills the
    ``_at_batch`` slot on the license-state axis alongside the singular
    :func:`license_state_at` and the "now" flavour :func:`license_state`,
    so a scheduled-audit tile that wants to render a per-epoch state
    timeline ("was the key active at each of these audit dates?") stops
    fanning out N calls to :func:`license_state_at`.

    Each item in ``epochs`` may be:

      * an int (or int-parseable string) -- a perspective epoch. The
        emitted row's ``state`` is what :func:`license_state_at` would
        return for that epoch alone.
      * ``bool`` (subclass of ``int``) or any non-int-parseable value
        (``None``, empty string, non-numeric string) -- collapses to a
        row with ``state="no_license"``, matching the never-mis-gate
        posture :func:`license_state_at` uses for the same inputs. The
        raw stringified token surfaces in ``epoch`` so a caller can
        still identify the offending entry.

    Row shape::

        {
          "epoch":  <int> | "<raw>",
          "state":  "active" | "expired" | "invalid" | "no_license",
        }

    Duplicates by normalised int key (or by ``repr(raw)`` for bad
    inputs) are dropped preserving first-seen order so the output is
    byte-stable across calls.

    ``epochs is None`` or non-iterable -- returns ``[]``. Never raises:
    per-row failures short-circuit to ``state="no_license"`` so the
    batch keeps building. Pairs with :func:`is_expired_at_batch` and
    :func:`days_until_expiry_at_batch` the way the scalar ``_at``
    trio pairs at the singular level so a caller can hydrate a whole
    audit row in three round-trips instead of ``3 * N`` calls.
    """
    out: list[dict] = []
    for raw, _key, parsed in _license_epoch_batch_keys(epochs):
        if parsed is None:
            try:
                token = str(raw)
            except Exception:
                token = repr(raw)
            out.append({"epoch": token, "state": "no_license"})
            continue
        try:
            state = license_state_at(parsed)
        except Exception as exc:
            logger.debug(
                "license: license_state_at_batch per-row failed: %s", exc
            )
            state = "no_license"
        out.append({"epoch": parsed, "state": state})
    return out


def is_state_at_batch(state, epochs) -> list[dict]:
    """Per-value perspective-epoch "was the license in state <X> at each
    of these epochs?" gate for N epochs in ONE round-trip.

    Shared-threshold sibling of :func:`is_state_at`. Where the singular
    scalar folds ONE ``(state, epoch)`` pair to ONE bool, this preserves
    per-value rows for a fixed ``state`` and a sequence of perspective
    epochs so a scheduled-audit tile that wants to answer "would we have
    shown the <state> banner on each of these audit dates?" (e.g.
    "expired on any of my quarterly review dates?") hydrates the whole
    column in ONE round-trip instead of fanning out N calls to the
    scalar. Same "shared threshold applied to EVERY row, per-row epoch"
    shape as :func:`is_expiring_within_at_batch` -- both take one gate
    parameter plus a batch of epochs.

    ``state`` is compared case-insensitively (after strip) against
    :data:`LICENSE_STATES`. A typo like ``"actiev"`` -- or ``None`` /
    empty / non-string -- collapses EVERY row to ``is_state=False``
    while preserving row slots so the output length still matches N. A
    caller cannot silently mis-gate on a mis-spelled state name, and
    the batch matches the "unknown state -> always False" posture of
    the scalar.

    Row shape::

        {
          "epoch":     <int> | "<raw>",
          "is_state":  <bool>,
        }

    Semantics per row mirror :func:`is_state_at`: ``True`` iff the
    perspective-epoch state byte-equals the (normalised, canonical)
    ``state`` requested. Note the ``"no_license"`` branch: for a bad
    epoch token (``bool`` / non-numeric / ``None``) the scalar
    collapses ``license_state_at`` to ``"no_license"`` -- so a batch
    caller asking ``state="no_license"`` truthfully sees ``True`` for
    those rows, mirroring the conservative "no entitlement" fallback
    of :func:`license_state_at`; any other requested ``state`` sees
    ``False``. Row shape mirrors :func:`is_expired_at_batch` /
    :func:`is_expiring_at_batch` so a caller assembling an audit
    timeline can zip the responses index-for-index.

    Duplicates by normalised int key (or ``repr(raw)`` for bad inputs)
    are dropped preserving first-seen order for byte-stable output.
    ``epochs is None`` or non-iterable -- returns ``[]``. Never raises:
    per-row failures short-circuit to ``is_state=False`` so the batch
    keeps building. Matches the never-mis-gate posture used by
    :func:`is_state_at` -- a bad row cannot silently claim a state
    that would grant unearned entitlement.

    When any row's ``epoch`` equals "now" and ``state`` is a canonical
    value, this predicate must agree with :func:`is_state` for the
    same install and the same requested ``state`` at that row -- both
    derive from the same signed ``exp`` claim via
    :func:`license_state_at` / :func:`license_state`, so a caller
    binding both the singular and the batch cannot catch them
    disagreeing at the boundary.
    """
    try:
        requested = str(state).strip().lower() if state is not None else ""
    except Exception:
        requested = ""
    valid_state = bool(requested) and requested in LICENSE_STATES
    out: list[dict] = []
    for raw, _key, parsed in _license_epoch_batch_keys(epochs):
        if parsed is None:
            try:
                token = str(raw)
            except Exception:
                token = repr(raw)
            match = bool(valid_state and requested == "no_license")
            out.append({"epoch": token, "is_state": match})
            continue
        if not valid_state:
            out.append({"epoch": parsed, "is_state": False})
            continue
        try:
            matched = is_state_at(requested, parsed)
        except Exception as exc:
            logger.debug(
                "license: is_state_at_batch per-row failed: %s", exc
            )
            matched = False
        out.append({"epoch": parsed, "is_state": bool(matched)})
    return out


def is_expired_at_batch(epochs) -> list[dict]:
    """Per-value perspective-epoch "was the license expired?" gate for
    N epochs in ONE round-trip.

    Per-value axis batch sibling of :func:`is_expired_at`. Fills the
    ``_at_batch`` slot on the expiry-boolean axis alongside the singular
    :func:`is_expired_at` and the "now" flavour :func:`is_expired`, so a
    scheduled-audit tile can hydrate an "was it expired at each of these
    dates?" column in one call.

    Row shape::

        {
          "epoch":   <int> | "<raw>",
          "expired": <bool>,
        }

    Semantics mirror :func:`is_expired_at` per row: signature-valid with
    an ``exp`` claim AND ``exp <= epoch`` -> ``True``; every other state
    (no license, invalid signature, perpetual key, ``exp > epoch``,
    ``bool`` / non-numeric epoch) -> ``False``. Row shape mirrors
    :func:`license_state_at_batch` so a caller assembling a timeline can
    zip the two responses index-for-index.

    Duplicates by normalised int key (or ``repr(raw)`` for bad inputs)
    are dropped preserving first-seen order for byte-stable output.
    ``epochs is None`` or non-iterable -- returns ``[]``. Never raises:
    per-row failures short-circuit to ``expired=False`` so the batch
    keeps building.
    """
    out: list[dict] = []
    for raw, _key, parsed in _license_epoch_batch_keys(epochs):
        if parsed is None:
            try:
                token = str(raw)
            except Exception:
                token = repr(raw)
            out.append({"epoch": token, "expired": False})
            continue
        try:
            expired = is_expired_at(parsed)
        except Exception as exc:
            logger.debug(
                "license: is_expired_at_batch per-row failed: %s", exc
            )
            expired = False
        out.append({"epoch": parsed, "expired": bool(expired)})
    return out


def is_expiring_at_batch(epochs) -> list[dict]:
    """Per-value perspective-epoch "does the installed key's ``exp``
    claim equal this epoch?" gate for N epochs in ONE round-trip.

    Per-value axis batch sibling of :func:`is_expiring_at`. Rounds out
    the expiry axis alongside :func:`license_state_at_batch`,
    :func:`is_expired_at_batch` and :func:`days_until_expiry_at_batch`:
    where those three batches answer "was the key active / expired /
    how many days remaining at each of these dates?", this one answers
    "does the on-disk ``exp`` still equal each of these values?" so a
    renewal-reminder tile that binds several cached ``exp`` candidates
    (e.g. "we warned about <date>; then <date>; then <date>") can
    detect a renewal on the on-disk key in ONE round-trip instead of
    fanning out N calls to :func:`is_expiring_at`.

    Row shape::

        {
          "epoch":        <int> | "<raw>",
          "is_expiring":  <bool>,
        }

    Semantics per row mirror :func:`is_expiring_at`: ``True`` iff a
    license is installed, signature-valid, NOT expired NOW, carries an
    ``exp`` claim, AND that claim matches ``epoch`` exactly. Every
    other state (no license, invalid signature, currently-expired key,
    perpetual key with no ``exp`` to compare, ``bool`` / non-numeric
    epoch, mismatched ``exp``) -> ``False``. Row shape mirrors
    :func:`is_expired_at_batch` so a caller assembling a renewal
    timeline can zip the two responses index-for-index.

    Duplicates by normalised int key (or ``repr(raw)`` for bad inputs)
    are dropped preserving first-seen order for byte-stable output.
    ``epochs is None`` or non-iterable -- returns ``[]``. Never raises:
    per-row failures short-circuit to ``is_expiring=False`` so the
    batch keeps building. Matches the never-mis-gate posture used by
    :func:`is_expiring_at` -- a bad row cannot silently fire a renewal
    prompt.
    """
    out: list[dict] = []
    for raw, _key, parsed in _license_epoch_batch_keys(epochs):
        if parsed is None:
            try:
                token = str(raw)
            except Exception:
                token = repr(raw)
            out.append({"epoch": token, "is_expiring": False})
            continue
        try:
            matched = is_expiring_at(parsed)
        except Exception as exc:
            logger.debug(
                "license: is_expiring_at_batch per-row failed: %s", exc
            )
            matched = False
        out.append({"epoch": parsed, "is_expiring": bool(matched)})
    return out


def is_expiring_within_at_batch(days: int, epochs) -> list[dict]:
    """Per-value perspective-epoch "would we have shown a renewal warning
    as of this epoch?" gate for N epochs in ONE round-trip.

    Per-value axis batch sibling of :func:`is_expiring_within_at`. Fills
    the ``_at_batch`` slot on the renewal-window axis alongside the
    existing ``exp``-derived batches (:func:`is_expired_at_batch`,
    :func:`is_expiring_at_batch`, :func:`days_until_expiry_at_batch`) so
    a scheduled-audit tile that wants to render "would the renewal
    banner have fired on each of these dates?" across a sequence of
    perspective epochs hydrates the whole column in ONE call instead of
    fanning out N calls to :func:`is_expiring_within_at`.

    ``days`` is the renewal-window threshold. It is applied to EVERY
    row -- callers wanting per-row thresholds should call the singular
    scalar N times. The threshold is coerced through ``int()`` once at
    the top of the call, matching the scalar helper. A ``bool`` /
    non-numeric / negative ``days`` collapses to ``is_expiring_within=
    False`` on every row (the scalar collapses to ``False`` on the same
    inputs, so the batch cannot silently diverge from a full N-call
    fan-out).

    Row shape::

        {
          "epoch":                <int> | "<raw>",
          "is_expiring_within":   <bool>,
        }

    Semantics per row mirror :func:`is_expiring_within_at`: ``True``
    iff a license is installed, signature-valid, carries an ``exp``
    claim, AND the days from ``epoch`` until ``exp`` fall between 0 and
    ``days`` inclusive. An already-lapsed-at-epoch key returns
    ``False`` on purpose -- the caller wants to distinguish "renewal
    window" (warn) from "already expired at that time" (a different,
    louder banner), and :func:`is_expired_at_batch` /
    :func:`days_until_expiry_at_batch` independently carry those
    signals index-for-index for callers that DO want to distinguish
    them. Perpetual licenses (no ``exp`` claim) and the no-license path
    both yield ``False`` on every row: nothing to warn about.

    Row shape mirrors :func:`is_expired_at_batch` /
    :func:`is_expiring_at_batch` per-row so a caller assembling a full
    renewal timeline can zip the batches index-for-index.

    Duplicates by normalised int key (or ``repr(raw)`` for bad inputs)
    are dropped preserving first-seen order for byte-stable output.
    ``epochs is None`` or non-iterable -- returns ``[]``. Never raises:
    per-row failures short-circuit to ``is_expiring_within=False`` so
    the batch keeps building. Matches the never-mis-gate posture used
    by :func:`is_expiring_within_at` -- a bad row cannot silently fire
    a renewal prompt.
    """
    if isinstance(days, bool):
        threshold_ok = False
        threshold = 0
    else:
        try:
            threshold = int(days)
            threshold_ok = threshold >= 0
        except (TypeError, ValueError):
            threshold = 0
            threshold_ok = False
    out: list[dict] = []
    for raw, _key, parsed in _license_epoch_batch_keys(epochs):
        if parsed is None:
            try:
                token = str(raw)
            except Exception:
                token = repr(raw)
            out.append({"epoch": token, "is_expiring_within": False})
            continue
        if not threshold_ok:
            out.append({"epoch": parsed, "is_expiring_within": False})
            continue
        try:
            matched = is_expiring_within_at(threshold, parsed)
        except Exception as exc:
            logger.debug(
                "license: is_expiring_within_at_batch per-row failed: %s", exc
            )
            matched = False
        out.append(
            {"epoch": parsed, "is_expiring_within": bool(matched)}
        )
    return out


def _license_days_batch_keys(days_list):
    """Shared iterable-of-``days`` pre-parser for the days-axis batch
    helpers below.

    Mirrors :func:`_license_epoch_batch_keys` but yields the coerced
    ``days`` thresholds a caller wants to fan a single perspective epoch
    across (e.g. "would the renewal banner fire at 7 / 14 / 30 / 60
    days?"). Preserves per-token slots so a row's ``days`` label matches
    the input token even when parsing fails, and dedupes by parsed int
    key preserving first-seen order for byte-stable output.

    Yields ``(raw, key, parsed)`` triples where:

      * ``raw`` is the original input token, preserved so the batch can
        surface it in the row label without a re-scan.
      * ``key`` is the normalisation key used for de-dup: ``str(parsed)``
        for a successfully parsed int, or ``("__bad__", repr(raw),
        id(raw))`` for anything the scalar
        :func:`is_expiring_within_at` would refuse -- each bogus input
        keeps its own slot so the output length still matches N.
      * ``parsed`` is the coerced ``int`` (only meaningful when the row
        is well-formed; ``None`` for the bad-input path).

    Rejects ``bool`` explicitly (subclass of ``int`` -- would silently
    ask "days=1?") matching the scalar's stance, and treats ``None`` /
    non-numeric strings / negative ints as bad input so a caller cannot
    silently mis-gate on a typo.
    """
    seen = set()
    if days_list is None:
        return
    try:
        iterator = iter(days_list)
    except TypeError:
        return
    for raw in iterator:
        if isinstance(raw, bool):
            key = ("__bad__", repr(raw), id(raw))
            if key in seen:
                continue
            seen.add(key)
            yield raw, key, None
            continue
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            key = ("__bad__", repr(raw), id(raw))
            if key in seen:
                continue
            seen.add(key)
            yield raw, key, None
            continue
        if parsed < 0:
            key = ("__bad__", repr(raw), id(raw))
            if key in seen:
                continue
            seen.add(key)
            yield raw, key, None
            continue
        key = str(parsed)
        if key in seen:
            continue
        seen.add(key)
        yield raw, key, parsed


def is_expiring_within_days_at_batch(days_list, epoch: int) -> list[dict]:
    """Per-value renewal-window "would we have shown a renewal warning
    at ``epoch`` for THIS days threshold?" gate for N thresholds in ONE
    round-trip.

    Days-axis batch sibling of :func:`is_expiring_within_at`. Where the
    existing epochs-axis batch :func:`is_expiring_within_at_batch` fans a
    single ``days`` threshold across N perspective epochs, this fans N
    ``days`` thresholds across a SINGLE perspective epoch -- the natural
    shape for a "renewal urgency" tile that wants to fire at multiple
    thresholds (7 / 14 / 30 / 60 days) off ONE hydration. The two
    batches are complements on orthogonal axes of the same scalar; a
    caller wanting a full grid still calls one per epoch (or the scalar
    N * M times), but the common cases (fixed threshold across dates,
    fixed date across thresholds) each hit ONE round-trip instead of N.

    ``epoch`` is the perspective epoch (Unix seconds) applied to EVERY
    row. It is coerced through ``int()``; ``bool`` is explicitly refused
    (would silently ask "as of epoch 1?"), and a non-numeric ``epoch``
    collapses every row to ``is_expiring_within=False`` while preserving
    row slots so the output length still matches N (matches the
    never-mis-gate posture of the sibling batch on the ``days`` axis
    when ``epochs`` is bad).

    Row shape::

        {
          "days":                <int> | "<raw>",
          "is_expiring_within":  <bool>,
        }

    Semantics per row mirror :func:`is_expiring_within_at`: ``True`` iff
    a license is installed, signature-valid, carries an ``exp`` claim,
    AND the days from ``epoch`` until ``exp`` fall between 0 and
    ``days`` inclusive. An already-lapsed-at-epoch install collapses
    every row to ``False`` (negative remaining doesn't sit inside any
    threshold >= 0; a different, louder ``is_expired_at`` banner
    covers that state). Perpetual licenses (no ``exp`` claim) and the
    no-license path both yield ``False`` on every row: nothing to warn
    about.

    Duplicates by normalised int key (or ``repr(raw)`` for bad inputs)
    are dropped preserving first-seen order for byte-stable output.
    ``days_list is None`` or non-iterable -- returns ``[]``. Never
    raises: per-row failures short-circuit to
    ``is_expiring_within=False`` so the batch keeps building. Matches
    the never-mis-gate posture used by :func:`is_expiring_within_at` --
    a bad row cannot silently fire a renewal prompt.
    """
    if isinstance(epoch, bool):
        epoch_ok = False
        parsed_epoch = 0
    else:
        try:
            parsed_epoch = int(epoch)
            epoch_ok = True
        except (TypeError, ValueError):
            parsed_epoch = 0
            epoch_ok = False
    out: list[dict] = []
    for raw, _key, parsed in _license_days_batch_keys(days_list):
        if parsed is None:
            try:
                token = str(raw)
            except Exception:
                token = repr(raw)
            out.append({"days": token, "is_expiring_within": False})
            continue
        if not epoch_ok:
            out.append({"days": parsed, "is_expiring_within": False})
            continue
        try:
            matched = is_expiring_within_at(parsed, parsed_epoch)
        except Exception as exc:
            logger.debug(
                "license: is_expiring_within_days_at_batch per-row failed: %s",
                exc,
            )
            matched = False
        out.append(
            {"days": parsed, "is_expiring_within": bool(matched)}
        )
    return out


def days_until_expiry_at_batch(epochs) -> list[dict]:
    """Per-value perspective-epoch "days until expiry" scalar for N
    epochs in ONE round-trip.

    Per-value axis batch sibling of :func:`days_until_expiry_at`. Fills
    the ``_at_batch`` slot on the days-remaining axis alongside the
    singular :func:`days_until_expiry_at` and the "now" flavour
    :func:`days_until_expiry`, so a scheduled-audit tile that wants
    to plot a countdown across a sequence of perspective dates hydrates
    the full column in one call.

    Row shape::

        {
          "epoch": <int> | "<raw>",
          "days":  <int> | None,
        }

    Semantics per row mirror :func:`days_until_expiry_at`: a signed
    integer number of days (positive when ``epoch`` is before ``exp``,
    zero on the day of, negative when ``epoch`` is after ``exp``);
    ``None`` for no license, invalid signature, perpetual key (no
    ``exp`` to count down to), and ``bool`` / non-numeric epochs. Row
    shape mirrors :func:`license_state_at_batch` /
    :func:`is_expired_at_batch` so a caller assembling an audit timeline
    can zip all three responses index-for-index.

    Duplicates by normalised int key (or ``repr(raw)`` for bad inputs)
    are dropped preserving first-seen order for byte-stable output.
    ``epochs is None`` or non-iterable -- returns ``[]``. Never raises:
    per-row failures short-circuit to ``days=None`` so the batch keeps
    building.
    """
    out: list[dict] = []
    for raw, _key, parsed in _license_epoch_batch_keys(epochs):
        if parsed is None:
            try:
                token = str(raw)
            except Exception:
                token = repr(raw)
            out.append({"epoch": token, "days": None})
            continue
        try:
            days = days_until_expiry_at(parsed)
        except Exception as exc:
            logger.debug(
                "license: days_until_expiry_at_batch per-row failed: %s", exc
            )
            days = None
        out.append(
            {"epoch": parsed, "days": int(days) if isinstance(days, int) else None}
        )
    return out



def license_age_days_at_batch(epochs) -> list[dict]:
    """Per-value perspective-epoch "how old was the license?" scalar for
    N epochs in ONE round-trip.

    Per-value axis batch sibling of :func:`license_age_days_at`. Fills
    the ``_at_batch`` slot on the license-age axis alongside the
    singular :func:`license_age_days_at` and the "now" flavour
    :func:`license_age_days`, so a scheduled-audit / retrospective tile
    that wants to plot age across a sequence of perspective dates (e.g.
    "how old was the key when we shipped each of these builds?")
    renders off ONE call instead of fanning out N calls to the scalar.

    Pairs on the ``iat``-derived axis the way
    :func:`days_until_expiry_at_batch` pairs on the ``exp``-derived
    axis: both walk the same epochs list and derive a signed integer
    day count against a claim on the on-disk key. A caller assembling
    an audit timeline can zip the two responses index-for-index to
    render "on <date>, the license was N days old and had M days
    remaining".

    Row shape::

        {
          "epoch": <int> | "<raw>",
          "days":  <int> | None,
        }

    Semantics per row mirror :func:`license_age_days_at`: a signed
    integer number of days (zero when ``epoch == iat``; positive when
    ``epoch`` is after ``iat`` -- the normal "N days old as of <date>"
    case; negative when ``epoch`` is BEFORE ``iat`` -- support
    scenario for pre-issuance perspectives); ``None`` for no license,
    invalid signature, a signed payload with no ``iat`` claim, and
    ``bool`` / non-numeric epochs. Row shape mirrors
    :func:`days_until_expiry_at_batch` so a caller assembling a
    timeline can zip the two responses index-for-index.

    Deliberately NOT clamped to ``max(0, ...)`` -- unlike the "now"
    flavour :func:`license_age_days`, which clamps because clock-skew
    is the only way ``iat`` can be in the future when reading against
    ``time.time()``. Here the caller EXPLICITLY passes perspective
    epochs, so a negative row is a real, actionable signal (they asked
    a question that only makes sense pre-issuance), not clock skew to
    be hidden.

    Duplicates by normalised int key (or ``repr(raw)`` for bad inputs)
    are dropped preserving first-seen order for byte-stable output.
    ``epochs is None`` or non-iterable -- returns ``[]``. Never raises:
    per-row failures short-circuit to ``days=None`` so the batch keeps
    building.

    Deliberately lenient on expiry, mirroring :func:`license_age_days_at`:
    a signed-but-lapsed key still carries a meaningful ``iat`` and
    callers would otherwise have to fall back to
    :func:`current_license_info`. The :func:`is_expired` /
    :func:`is_expiring_at` helpers independently carry the "past-
    expiry" signals for callers that DO want to hide the row on
    lapsed keys.
    """
    out: list[dict] = []
    for raw, _key, parsed in _license_epoch_batch_keys(epochs):
        if parsed is None:
            try:
                token = str(raw)
            except Exception:
                token = repr(raw)
            out.append({"epoch": token, "days": None})
            continue
        try:
            days = license_age_days_at(parsed)
        except Exception as exc:
            logger.debug(
                "license: license_age_days_at_batch per-row failed: %s", exc
            )
            days = None
        out.append(
            {"epoch": parsed, "days": int(days) if isinstance(days, int) else None}
        )
    return out


def pro_install_age_days_at_batch(epochs) -> list[dict]:
    """Per-value perspective-epoch "how old was the ``clawmetry-pro``
    install at this epoch?" scalar for N epochs in ONE round-trip.

    Per-value axis batch sibling of :func:`pro_install_age_days_at`. Fills
    the ``_at_batch`` slot on the pro-install-age axis alongside the
    singular :func:`pro_install_age_days_at` and the "now" flavour
    :func:`pro_install_age_days`, so a scheduled-audit tile that wants to
    plot the install-age across a sequence of perspective dates ("how old
    was the pro wheel at each of these build timestamps?") hydrates the
    full column in one call.

    Twin of :func:`license_age_days_at_batch` for the ``installed_at`` axis
    -- one derives from the signed ``iat`` claim, this one from the
    on-disk provisioning marker -- so a caller assembling an install +
    entitlement timeline can zip the two batch responses index-for-index.
    Callers wanting the "N days old, still valid for M more days" pair for
    the same sequence of epochs zip this with
    :func:`days_until_expiry_at_batch`.

    Row shape::

        {
          "epoch":    <int> | "<raw>",
          "age_days": <int> | None,
        }

    Semantics per row mirror :func:`pro_install_age_days_at`: a signed
    integer number of days (positive when ``epoch`` is after
    ``installed_at`` -- the normal "N days old as of <date>" case, zero on
    the day of provisioning, negative when ``epoch`` is BEFORE
    ``installed_at`` -- the operator asked a pre-install question and the
    negative is a real signal, not clock skew to be hidden); ``None`` when
    there is no marker on disk, when the marker has no ``installed_at``
    key, when ``installed_at`` is non-numeric / non-positive, or for
    ``bool`` / non-numeric epochs.

    Row shape mirrors :func:`license_age_days_at_batch` so a caller
    assembling a two-axis age timeline (marker vs signed iat) can zip the
    two responses index-for-index.

    Duplicates by normalised int key (or ``repr(raw)`` for bad inputs)
    are dropped preserving first-seen order for byte-stable output.
    ``epochs is None`` or non-iterable -- returns ``[]``. Never raises:
    per-row failures short-circuit to ``age_days=None`` so the batch keeps
    building. Deliberately independent of live importability -- a marker
    on disk yields an age even when Python cannot currently import
    ``clawmetry-pro`` (wheel was pip-uninstalled since); pair with
    :func:`pro_installed` for the live-import signal.
    """
    out: list[dict] = []
    for raw, _key, parsed in _license_epoch_batch_keys(epochs):
        if parsed is None:
            try:
                token = str(raw)
            except Exception:
                token = repr(raw)
            out.append({"epoch": token, "age_days": None})
            continue
        try:
            age = pro_install_age_days_at(parsed)
        except Exception as exc:
            logger.debug(
                "license: pro_install_age_days_at_batch per-row failed: %s", exc
            )
            age = None
        out.append(
            {"epoch": parsed, "age_days": int(age) if isinstance(age, int) else None}
        )
    return out


def is_license_valid_at_batch(epochs) -> list[dict]:
    """Per-value perspective-epoch "would the installed license have been
    valid at each of these epochs?" gate for N epochs in ONE round-trip.

    Per-value axis batch sibling of :func:`is_license_valid_at`. Fills
    the ``_at_batch`` slot on the entitlement-boolean axis alongside the
    singular :func:`is_license_valid_at` and the "now" flavour
    :func:`is_license_valid`, so a scheduled-audit tile that wants to
    render "was this node entitled on each of these audit dates?" across
    a sequence of perspective epochs hydrates the whole column in ONE
    call instead of fanning out N calls to :func:`is_license_valid_at`.

    Row shape::

        {
          "epoch":    <int> | "<raw>",
          "is_valid": <bool>,
        }

    Semantics per row mirror :func:`is_license_valid_at`: ``True`` iff a
    license is installed, signature-valid, AND either carries no ``exp``
    claim (perpetual) OR ``exp > epoch``. Every other state -- no
    license, invalid signature, ``exp <= epoch``, ``bool`` / non-numeric
    epoch -- yields ``False``. Row shape mirrors
    :func:`is_expired_at_batch` / :func:`is_state_at_batch` so a caller
    assembling an entitlement timeline can zip the responses index-for-
    index; per-row ``is_valid`` is exactly the complement of the
    matching :func:`is_expired_at_batch` ``expired`` field on a
    signature-valid, non-perpetual key, and both collapse to ``False``
    together on the no-license / invalid-signature branches.

    Duplicates by normalised int key (or ``repr(raw)`` for bad inputs)
    are dropped preserving first-seen order for byte-stable output.
    ``epochs is None`` or non-iterable -- returns ``[]``. Never raises:
    per-row failures short-circuit to ``is_valid=False`` so the batch
    keeps building. Matches the never-mis-gate posture used by
    :func:`is_license_valid_at` -- a bad row cannot silently unlock a
    Pro feature retroactively.
    """
    out: list[dict] = []
    for raw, _key, parsed in _license_epoch_batch_keys(epochs):
        if parsed is None:
            try:
                token = str(raw)
            except Exception:
                token = repr(raw)
            out.append({"epoch": token, "is_valid": False})
            continue
        try:
            valid = is_license_valid_at(parsed)
        except Exception as exc:
            logger.debug(
                "license: is_license_valid_at_batch per-row failed: %s", exc
            )
            valid = False
        out.append({"epoch": parsed, "is_valid": bool(valid)})
    return out


def license_tier_at_batch(epochs) -> list[dict]:
    """Per-value perspective-epoch license-tier scalar for N epochs in
    ONE round-trip.

    Per-value axis batch sibling of :func:`license_tier_at`. Fills the
    ``_at_batch`` slot on the license-tier axis alongside the singular
    :func:`license_tier_at` and the "now" flavour :func:`license_tier`,
    so a scheduled-audit / retrospective tile that wants to plot tier
    across a sequence of perspective dates ("what tier was this node
    on each of these audit dates?") renders off ONE call instead of
    fanning out N calls to the scalar.

    Each item in ``epochs`` may be:

      * an int (or int-parseable string) -- a perspective epoch. The
        emitted row's ``tier`` is what :func:`license_tier_at` would
        return for that epoch alone.
      * ``bool`` (subclass of ``int``) or any non-int-parseable value
        (``None``, empty string, non-numeric string) -- collapses to a
        row with ``tier=None``, matching the never-mis-gate posture
        :func:`license_tier_at` uses for the same inputs. The raw
        stringified token surfaces in ``epoch`` so a caller can still
        identify the offending entry.

    Row shape::

        {
          "epoch": <int> | "<raw>",
          "tier":  <str> | None,
        }

    Semantics per row mirror :func:`license_tier_at`: a lowercased,
    whitespace-stripped tier string when the license is signature-
    valid, carries a string ``tier`` claim, AND (perpetual OR
    ``exp > epoch``); ``None`` for no license, invalid signature, an
    ``exp`` claim that has already lapsed at ``epoch``, a signed
    payload with a missing / non-string / empty ``tier``, and
    ``bool`` / non-numeric epochs.

    Duplicates by normalised int key (or ``repr(raw)`` for bad inputs)
    are dropped preserving first-seen order for byte-stable output.
    ``epochs is None`` or non-iterable -- returns ``[]``. Never raises:
    per-row failures short-circuit to ``tier=None`` so the batch keeps
    building. Matches the never-mis-gate posture used by
    :func:`license_tier_at` -- a bad row cannot silently claim a tier
    that would grant unearned entitlement.

    When any row's ``epoch`` equals "now", the row's ``tier`` field
    must byte-equal :func:`license_tier` for the same install -- both
    derive from the same signed ``tier`` claim via
    :func:`license_tier_at` / :func:`license_tier`, so a caller
    binding both cannot catch them disagreeing at the boundary.

    Pairs with :func:`license_state_at_batch` /
    :func:`is_expired_at_batch` / :func:`days_until_expiry_at_batch`
    on the row-shape axis: for the same epochs list, a caller can zip
    the responses index-for-index and hydrate a whole entitlement
    timeline row for one install in a handful of round-trips instead
    of ``N * M`` calls to the scalar surface.
    """
    out: list[dict] = []
    for raw, _key, parsed in _license_epoch_batch_keys(epochs):
        if parsed is None:
            try:
                token = str(raw)
            except Exception:
                token = repr(raw)
            out.append({"epoch": token, "tier": None})
            continue
        try:
            tier = license_tier_at(parsed)
        except Exception as exc:
            logger.debug(
                "license: license_tier_at_batch per-row failed: %s", exc
            )
            tier = None
        out.append(
            {"epoch": parsed, "tier": tier if isinstance(tier, str) else None}
        )
    return out


def license_features() -> list[str] | None:
    """Scalar accessor for the ``features`` claim on the installed license.

    Thin scalar-shape helper for callers (an operator entitlement-diagnostic
    tile, a "features unlocked by your key" chip row, a fleet-node column
    that only needs the string list) that want the features list on its
    own and don't want to unpack the full :func:`current_license_info`
    envelope OR re-implement the "don't trust an unsigned body" rule
    client-side.

    Returns a sorted, deduplicated, normalised (lower-cased, whitespace-
    stripped) ``list[str]`` of feature ids on a signature-valid,
    non-expired license. Returns ``None`` in every other branch:

      * no license file on disk (OSS free)
      * file exists but signature is bogus (an attacker who could edit
        the payload could otherwise smuggle any ``features`` list into
        an unsigned body -- we never surface it)
      * signed-but-lapsed key (a gate binding this helper cannot silently
        keep granting features on an expired key)
      * any per-row failure inside the underlying read path

    An empty list (``[]``) means the license IS valid but its payload
    carries no explicit ``features`` claim (or the claim is present but
    holds no usable string ids). ``[]`` is deliberately DISTINCT from
    ``None``:

      * ``[]``   -> "valid license, zero features itemised on the token"
                    (the tier still grants coverage; the license just
                    doesn't spell out per-feature entitlement)
      * ``None`` -> "no valid license at all"

    A caller binding this scalar to a "features unlocked" UI must render
    both branches -- ``None`` -> "no license", ``[]`` -> "no features
    itemised" -- without collapsing them, or a valid-key-with-empty-list
    user will silently get the same "unlicensed" copy as an OSS install.

    Note: the ``features`` claim is a SUPPLEMENTAL string list carried
    on the license token; it is NOT the canonical open-core feature
    catalogue. For the resolved feature set actually enforced by gates,
    callers should read :func:`clawmetry.entitlements.get_entitlement`
    (which layers this claim on top of the FREE-tier baseline). This
    scalar surfaces the claim exactly as written on the token, so
    operator diagnostics can distinguish "gate says X is unlocked
    because the key claims it" from "gate says X is unlocked because
    the tier grants it by default".

    Mirrors the "refuse expired keys" posture already used by
    :func:`license_tier` / :func:`license_nodes`: a lapsed key must not
    keep rendering as "features unlocked". A caller wanting to surface
    the CLAIM even on an expired key (support: "what features was this
    key SUPPOSED to grant?") should re-verify the token directly with
    :func:`verify_token`.

    Never raises. Any exception under the hood degrades to ``None`` so a
    diagnostic tile bound to this helper never breaks on a partial or
    corrupt install.
    """
    try:
        info = current_license_info()
    except Exception as exc:
        logger.debug("license: license_features underlying read failed: %s", exc)
        return None
    if not isinstance(info, dict):
        return None
    if not info.get("valid"):
        # Invalid-signature and signed-but-lapsed branches both collapse
        # to None on purpose -- see docstring for the never-mis-gate
        # rationale. Neither branch may surface a features list.
        return None
    # ``current_license_info`` does not surface the ``features`` claim in
    # its envelope (kept intentionally narrow -- see its docstring), so
    # re-open the license file and re-verify to pull the field. The
    # ``valid`` gate above proves the file is on disk AND its signature
    # verified once this call, so this second read cannot admit an
    # unsigned body: any tamper between the two reads still fails
    # ``verify_token``.
    try:
        if not os.path.isfile(LICENSE_PATH):
            return None
        with open(LICENSE_PATH, "r", encoding="utf-8") as fh:
            payload = verify_token(fh.read().strip())
    except Exception as exc:
        logger.debug(
            "license: license_features token re-read failed: %s", exc
        )
        return None
    if not isinstance(payload, dict):
        return None
    raw = payload.get("features")
    # A missing / non-list ``features`` claim collapses to the empty list
    # (valid license, zero features itemised) -- distinct from ``None``
    # which means no valid license at all. See docstring.
    if not isinstance(raw, (list, tuple)):
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            # Ignore non-string entries defensively. An attacker who
            # can't forge the signature also can't smuggle a non-string
            # feature id past ``json.loads`` here, but a legit server-
            # side typo (e.g. an integer feature id) shouldn't blow up
            # the tile -- skip it and keep going.
            continue
        norm = item.strip().lower()
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(norm)
    out.sort()
    return out


def license_features_at(epoch: int) -> list[str] | None:
    """Perspective-epoch flavour of :func:`license_features` -- "what
    features would :func:`license_features` have surfaced evaluated as of
    ``epoch``?" -- for a scheduled-audit / retrospective diagnostic tile
    that wants to answer "which paid features was this node entitled to
    on <date>?" without the caller having to snapshot the license state
    at that time or compare ``exp`` to a caller-supplied epoch
    themselves.

    Returns:
      * ``None`` when there is nothing trustworthy to surface AS OF
        ``epoch``: no license file on disk, an invalid signature (an
        attacker could stuff any ``features`` list into an unsigned body
        -- refused for every perspective), a signed key whose ``exp``
        claim has already lapsed at ``epoch`` (retrospective on a lapsed
        key when ``epoch`` equals "now"; prospective on an active key
        when ``epoch`` is in the future beyond ``exp``), OR a per-row
        introspection failure. Matches the never-mis-gate posture of
        :func:`license_features`: a lapsed key must not keep rendering
        as "features unlocked" from ANY perspective epoch.
      * ``[]`` when the license IS valid AS OF ``epoch`` but its payload
        carries no explicit ``features`` claim (or the claim is present
        but holds no usable string ids). Distinct from ``None``: a UI
        binding this helper must render both branches -- ``None`` -> "no
        entitlement at that time", ``[]`` -> "entitled but no features
        itemised" -- without collapsing them, or a valid-key-with-empty-
        list user will silently render as "unlicensed" for the audit
        row.
      * A sorted, deduplicated, normalised (lower-cased, whitespace-
        stripped) ``list[str]`` of feature ids otherwise. Normalisation
        matches :func:`license_features` byte-for-byte so a caller
        zipping the two lists (perspective-at vs current-now) can't
        catch them disagreeing on casing.

    ``epoch`` is coerced through ``int()``; ``bool`` is explicitly
    refused despite being an ``int`` subclass so a caller that passes
    ``True`` / ``False`` gets ``None`` back rather than a spurious "was
    feature X entitled at epoch 1?" classification. A non-numeric value
    collapses to ``None`` so a caller cannot silently mis-gate on a
    typo -- the conservative fallback since ``None`` implies no
    entitlement, matching the never-mis-gate posture of the surrounding
    ``_at`` family.

    When ``epoch`` equals "now", this scalar must agree with
    :func:`license_features` for the same install -- both derive from
    the same signed ``features`` claim, refuse the invalid-signature
    branch, and use the same ``exp <= cutoff`` boundary via
    :func:`license_state_at` / the current-time ``valid`` classifier,
    so the two scalars cannot disagree at the boundary. On any other
    epoch this helper answers the retrospective / prospective question
    :func:`license_features` cannot -- e.g. "which features was this
    node entitled to last quarter?" (``None`` on a key that has since
    been renewed but was already expired then) or "which features will
    this node still have at our next audit?" (``None`` on an active key
    whose ``exp`` falls before the audit date).

    Never raises. Any underlying introspection failure (import error,
    corrupt install, cryptography-lib mismatch) collapses to ``None``
    -- same fallback as :func:`license_features` -- so a scheduled
    audit tile bound to this helper never breaks on a partial install.

    Note: the ``features`` claim is a SUPPLEMENTAL string list carried
    on the license token; it is NOT the canonical open-core feature
    catalogue. This helper surfaces the claim exactly as written on the
    token (with the perspective-epoch validity gate on top), so
    operator diagnostics can distinguish "feature X was entitled on
    <date> because the key claimed it" from "feature X was entitled on
    <date> because the tier granted it by default".

    Pairs with the sibling ``_at`` scalars
    (:func:`license_state_at`, :func:`license_tier_at`,
    :func:`is_expired_at`, :func:`days_until_expiry_at`) at the row
    level: for the same ``epoch``, a caller can zip the responses
    index-for-index and hydrate the whole entitlement row for one
    install without the scalars catching each other disagreeing on the
    perspective-epoch classification.
    """
    if isinstance(epoch, bool):
        return None
    try:
        wanted = int(epoch)
    except (TypeError, ValueError):
        return None
    try:
        info = current_license_info()
    except Exception as exc:
        logger.debug(
            "license: license_features_at underlying read failed: %s", exc
        )
        return None
    if not isinstance(info, dict):
        return None
    status = info.get("status")
    if status == "invalid":
        # Signature-bogus branch: an unsigned body is untrusted whatever
        # the perspective, so the classification is time-independent.
        # Mirrors :func:`license_features` -- payload-derived claims
        # never get to influence the answer here.
        return None
    exp = info.get("exp")
    if isinstance(exp, (int, float)) and int(exp) <= wanted:
        # Signed key that has already lapsed AS OF ``epoch`` -- refuse
        # for the same reason :func:`license_features` refuses the
        # expired branch at "now": a lapsed customer must stop rendering
        # as "features unlocked" once the perspective epoch is past
        # ``exp``.
        return None
    # ``current_license_info`` does not surface the ``features`` claim
    # in its envelope (kept intentionally narrow -- see its docstring),
    # so re-open the license file and re-verify to pull the field. The
    # gates above prove the file is on disk AND its signature verified
    # once this call, so this second read cannot admit an unsigned
    # body: any tamper between the two reads still fails
    # :func:`verify_token`. Mirrors the same re-read pattern used by
    # :func:`license_features`.
    try:
        if not os.path.isfile(LICENSE_PATH):
            return None
        with open(LICENSE_PATH, "r", encoding="utf-8") as fh:
            payload = verify_token(fh.read().strip())
    except Exception as exc:
        logger.debug(
            "license: license_features_at token re-read failed: %s", exc
        )
        return None
    if not isinstance(payload, dict):
        return None
    raw = payload.get("features")
    # A missing / non-list ``features`` claim collapses to the empty
    # list (valid license, zero features itemised) -- distinct from
    # ``None`` which means no valid license at all. See docstring.
    if not isinstance(raw, (list, tuple)):
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            # Ignore non-string entries defensively. An attacker who
            # can't forge the signature also can't smuggle a non-string
            # feature id past ``json.loads`` here, but a legit server-
            # side typo (e.g. an integer feature id) shouldn't blow up
            # the tile -- skip it and keep going.
            continue
        norm = item.strip().lower()
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(norm)
    out.sort()
    return out


def license_features_at_batch(epochs) -> list[dict]:
    """Per-value perspective-epoch license-features scalar for N epochs
    in ONE round-trip.

    Per-value axis batch sibling of :func:`license_features_at`. Fills
    the ``_at_batch`` slot on the license-features axis alongside the
    singular :func:`license_features_at` and the "now" flavour
    :func:`license_features`, so a scheduled-audit / retrospective tile
    that wants to plot the ``features`` claim across a sequence of
    perspective dates ("which features was this node entitled to on
    each of these audit dates?") renders off ONE call instead of
    fanning out N calls to the scalar.

    Each item in ``epochs`` may be:

      * an int (or int-parseable string) -- a perspective epoch. The
        emitted row's ``features`` field is what
        :func:`license_features_at` would return for that epoch alone.
      * ``bool`` (subclass of ``int``) or any non-int-parseable value
        (``None``, empty string, non-numeric string) -- collapses to a
        row with ``features=None``, matching the never-mis-gate posture
        :func:`license_features_at` uses for the same inputs. The raw
        stringified token surfaces in ``epoch`` so a caller can still
        identify the offending entry.

    Row shape::

        {
          "epoch":    <int> | "<raw>",
          "features": [<id>, ...] | None,
        }

    Semantics per row mirror :func:`license_features_at`:

      * ``None`` on no license, invalid signature, an ``exp`` claim
        that has already lapsed at ``epoch``, and ``bool`` / non-
        numeric epochs.
      * ``[]`` on a signature-valid license AS OF ``epoch`` whose
        payload carries no explicit ``features`` claim (or holds no
        usable string ids). Distinct from ``None``.
      * A sorted, deduplicated, normalised (lower/strip) ``list[str]``
        of feature ids on a signature-valid, non-expired-at-``epoch``
        key that carries a well-formed ``features`` claim.

    Duplicates by normalised int key (or ``repr(raw)`` for bad inputs)
    are dropped preserving first-seen order for byte-stable output.
    ``epochs is None`` or non-iterable -- returns ``[]``. Never raises:
    per-row failures short-circuit to ``features=None`` so the batch
    keeps building. Matches the never-mis-gate posture used by
    :func:`license_features_at` -- a bad row cannot silently claim a
    features list that would grant unearned entitlement.

    When any row's ``epoch`` equals "now", the row's ``features`` field
    must byte-equal :func:`license_features` for the same install --
    both derive from the same signed ``features`` claim via
    :func:`license_features_at` / :func:`license_features`, so a caller
    binding both cannot catch them disagreeing at the boundary.

    Pairs with :func:`license_state_at_batch` /
    :func:`is_expired_at_batch` / :func:`days_until_expiry_at_batch` /
    :func:`license_tier_at_batch` on the row-shape axis: for the same
    epochs list, a caller can zip the responses index-for-index and
    hydrate a whole entitlement timeline row for one install in a
    handful of round-trips instead of ``N * M`` calls to the scalar
    surface.
    """
    out: list[dict] = []
    for raw, _key, parsed in _license_epoch_batch_keys(epochs):
        if parsed is None:
            try:
                token = str(raw)
            except Exception:
                token = repr(raw)
            out.append({"epoch": token, "features": None})
            continue
        try:
            feats = license_features_at(parsed)
        except Exception as exc:
            logger.debug(
                "license: license_features_at_batch per-row failed: %s", exc
            )
            feats = None
        if feats is not None and not isinstance(feats, list):
            # Defensive: the scalar contract is list[str] | None, but a
            # future change that ever emitted a non-list would silently
            # break the per-row parity guarantee. Collapse to None.
            feats = None
        out.append({"epoch": parsed, "features": feats})
    return out
