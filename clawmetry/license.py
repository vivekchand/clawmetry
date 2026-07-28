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
