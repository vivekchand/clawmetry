"""
clawmetry.net — outbound TLS + proxy bootstrap for enterprise networks.

Enterprise Windows machines commonly sit behind TLS-intercepting proxies
(Zscaler, Netskope, Palo Alto, …) that re-sign HTTPS with an internal root
CA. That CA lives in the OS trust store but not in certifi's bundle, and on
Python 3.13+ ``VERIFY_X509_STRICT`` (default-on) additionally rejects
corporate MITM CAs that lack the keyUsage extension. Result: every POST to
ingest.clawmetry.com dies with CERTIFICATE_VERIFY_FAILED.

Every outbound HTTPS call in this package goes through
``urllib.request.urlopen`` with the process-default opener, so one
``configure_outbound_network()`` call at process start fixes all of them:

1. ``truststore.inject_into_ssl()`` — validate against the OS trust store
   (Windows CryptoAPI / macOS Security.framework / Linux CA dir) instead of
   only certifi. Guarded: falls back to stock OpenSSL trust when the
   package is missing (Python < 3.10) or injection fails.
2. Clear ``VERIFY_X509_STRICT`` on the context we install — hostname
   checking and chain validation stay ON.
3. Load an extra CA bundle from CLAWMETRY_CA_BUNDLE / config ``ca_bundle``
   / SSL_CERT_FILE / REQUESTS_CA_BUNDLE (first match wins, env before
   config).
4. Install a global urllib opener whose ProxyHandler snapshots
   HTTPS_PROXY / HTTP_PROXY / NO_PROXY *now* — the daemon is started by
   launchd/systemd/Task Scheduler, not the user's shell, so the env must
   be read at daemon start rather than assumed inherited.
5. Last-resort escape hatch: config ``tls_verify: false`` or
   CLAWMETRY_TLS_NO_VERIFY=1 disables verification entirely, with a loud
   warning on every start. Pilot use only.

See docs/enterprise-networking.md and ``clawmetry doctor``.
"""
from __future__ import annotations

import json
import logging
import os
import ssl
import urllib.request

log = logging.getLogger("clawmetry.net")

_TRUTHY = frozenset({"1", "true", "yes", "on"})

CONFIG_PATH = os.path.expanduser("~/.clawmetry/config.json")

# Set by configure_outbound_network() so `clawmetry doctor` / `clawmetry
# status` can report which trust source is active.
_STATE = {
    "configured": False,
    "truststore": False,
    "ca_bundle": None,
    "verify_disabled": False,
}


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def _load_config_file() -> dict:
    """Best-effort read of ~/.clawmetry/config.json. Never raises."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def tls_verify_disabled(config: dict = None) -> bool:
    """True when the operator explicitly opted out of TLS verification.

    Env CLAWMETRY_TLS_NO_VERIFY=1 or config ``tls_verify: false``. This is
    the last-resort escape hatch for pilots stuck behind an interception
    proxy whose root CA can't be exported yet — NOT a recommended mode.
    """
    if _env_truthy("CLAWMETRY_TLS_NO_VERIFY"):
        return True
    if config is None:
        config = _load_config_file()
    return config.get("tls_verify") is False


def ca_bundle_path(config: dict = None) -> str:
    """Resolve the extra CA bundle to load, or "" when none is configured.

    Precedence: CLAWMETRY_CA_BUNDLE > config ``ca_bundle`` > SSL_CERT_FILE
    > REQUESTS_CA_BUNDLE. A configured-but-missing file is logged and
    skipped so a stale path can't take the daemon offline.
    """
    if config is None:
        config = _load_config_file()
    candidates = (
        ("CLAWMETRY_CA_BUNDLE (env)", os.environ.get("CLAWMETRY_CA_BUNDLE", "")),
        ("ca_bundle (config)", str(config.get("ca_bundle") or "")),
        ("SSL_CERT_FILE (env)", os.environ.get("SSL_CERT_FILE", "")),
        ("REQUESTS_CA_BUNDLE (env)", os.environ.get("REQUESTS_CA_BUNDLE", "")),
    )
    for source, path in candidates:
        path = os.path.expanduser(path.strip()) if path else ""
        if not path:
            continue
        if os.path.isfile(path):
            return path
        log.warning("CA bundle from %s does not exist, skipping: %s", source, path)
    return ""


def relax_strict_verification(ctx: "ssl.SSLContext") -> "ssl.SSLContext":
    """Clear VERIFY_X509_STRICT (Python 3.13 default-on) on ``ctx``.

    Corporate interception CAs frequently lack the keyUsage extension the
    strict profile requires ("CA cert does not include key usage
    extension"). Hostname checking and chain validation are untouched.
    hasattr-guarded: the flag exists back to 3.4 but only defaults on in
    3.13, and some vendored ssl builds omit it.
    """
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        try:
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        except Exception as e:
            log.debug("could not clear VERIFY_X509_STRICT: %s", e)
    return ctx


def inject_truststore() -> bool:
    """Swap ssl.SSLContext for the OS-trust-store-backed one. Never raises."""
    try:
        import truststore  # type: ignore

        truststore.inject_into_ssl()
        _STATE["truststore"] = True
        log.info("TLS: using OS trust store via truststore")
        return True
    except ImportError:
        log.info(
            "TLS: truststore not available (needs Python 3.10+); "
            "falling back to Python's default certifi/OpenSSL trust"
        )
    except Exception as e:
        log.warning(
            "TLS: truststore.inject_into_ssl() failed (%s); "
            "falling back to Python's default certifi/OpenSSL trust", e
        )
    return False


def build_ssl_context(config: dict = None, allow_insecure: bool = True) -> "ssl.SSLContext":
    """Build the SSL context used for all outbound HTTPS.

    OS-store-backed when truststore is injected, strict flag cleared,
    extra CA bundle loaded on top. ``allow_insecure=False`` ignores the
    tls_verify escape hatch (doctor uses that to test the real posture).
    """
    if config is None:
        config = _load_config_file()
    ctx = ssl.create_default_context()
    relax_strict_verification(ctx)
    bundle = ca_bundle_path(config)
    if bundle:
        try:
            ctx.load_verify_locations(cafile=bundle)
            _STATE["ca_bundle"] = bundle
            log.info("TLS: loaded extra CA bundle %s", bundle)
        except Exception as e:
            log.warning("TLS: failed to load CA bundle %s: %s", bundle, e)
    if allow_insecure and tls_verify_disabled(config):
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        _STATE["verify_disabled"] = True
        log.warning(
            "!!! TLS CERTIFICATE VERIFICATION IS DISABLED "
            "(tls_verify:false / CLAWMETRY_TLS_NO_VERIFY=1). Traffic to "
            "clawmetry.com can be read or tampered with in transit. This "
            "is for temporary pilot use ONLY — export your corporate root "
            "CA and set CLAWMETRY_CA_BUNDLE instead (see `clawmetry "
            "doctor` and docs/enterprise-networking.md)."
        )
    return ctx


def configure_outbound_network(config: dict = None, role: str = "") -> "ssl.SSLContext":
    """Process-wide outbound TLS/proxy bootstrap. Call once at startup.

    Installs a global urllib opener so every ``urllib.request.urlopen``
    call in the process (heartbeat, snapshot push, telemetry, license,
    update check, …) validates against the OS trust store, honors the
    proxy env vars, and tolerates 3.13 strict-mode corporate CAs.
    Never raises — a broken TLS bootstrap must not stop the daemon from
    ingesting locally.
    """
    try:
        inject_truststore()
        ctx = build_ssl_context(config)
        opener = urllib.request.build_opener(
            # ProxyHandler() reads HTTPS_PROXY/HTTP_PROXY/NO_PROXY at
            # construction — i.e. at daemon start, not the parent shell.
            urllib.request.ProxyHandler(),
            urllib.request.HTTPSHandler(context=ctx),
        )
        urllib.request.install_opener(opener)
        _STATE["configured"] = True
        proxies = urllib.request.getproxies()
        if proxies:
            log.info(
                "%soutbound proxy config: %s",
                (role + ": ") if role else "",
                {k: v for k, v in proxies.items() if k in ("http", "https", "no")},
            )
        return ctx
    except Exception as e:
        log.warning("outbound network bootstrap failed (%s); using stdlib defaults", e)
        try:
            return ssl.create_default_context()
        except Exception:
            return None


def state() -> dict:
    """Snapshot of the active trust configuration (for doctor/status)."""
    return dict(_STATE)
