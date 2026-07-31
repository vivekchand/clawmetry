"""
clawmetry.endpoints — single source of truth for cloud endpoint resolution.

Every daemon/CLI/dashboard network call that targets ClawMetry Cloud must
resolve its base URL through this module so that a self-hosted ClawMetry
Enterprise deployment can repoint the whole client with one setting.

Resolution order for the ingest base (first non-empty wins):

    1. CLAWMETRY_ENDPOINT        (env — the enterprise knob)
    2. CLAWMETRY_INGEST_URL      (env — legacy, kept for back-compat)
    3. "endpoint" key in ~/.clawmetry/config.json
    4. https://ingest.clawmetry.com

The app base (OAuth pages, dashboard links, account/claim side-channels)
follows the same custom endpoint when one is set — a self-hosted server is
single-host — and only falls back to app.clawmetry.com for the managed cloud:

    1. CLAWMETRY_APP_BASE        (env — legacy, explicit split override)
    2. CLAWMETRY_ENDPOINT / CLAWMETRY_INGEST_URL (env)
    3. "endpoint" key in ~/.clawmetry/config.json
    4. https://app.clawmetry.com

Note: several modules snapshot these values into module-level constants at
import time (clawmetry.sync.INGEST_URL and friends). Changing the env vars
after import does not repoint an already-running process — restart the
daemon/dashboard after changing endpoint configuration. Tests should call
these functions directly (they re-read env + config on every call).
"""
from __future__ import annotations

import json
import os
from urllib.parse import urlparse

DEFAULT_INGEST_URL = "https://ingest.clawmetry.com"
DEFAULT_APP_URL = "https://app.clawmetry.com"

CONFIG_PATH = os.path.expanduser("~/.clawmetry/config.json")

# (mtime, endpoint-value) cache so hot paths (heartbeat every 3s) don't
# re-parse the config file on every call.
_cfg_cache: tuple[float, str] | None = None


def _config_endpoint() -> str:
    """The ``endpoint`` key from ~/.clawmetry/config.json, or "". Never raises."""
    global _cfg_cache
    try:
        mtime = os.stat(CONFIG_PATH).st_mtime
    except OSError:
        return ""
    if _cfg_cache is not None and _cfg_cache[0] == mtime:
        return _cfg_cache[1]
    value = ""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            value = str(data.get("endpoint") or "").strip()
    except Exception:
        value = ""
    _cfg_cache = (mtime, value)
    return value


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def ingest_url() -> str:
    """Base URL for the ingest/data-plane API (/auth, /ingest/*, /api/*)."""
    return (
        _env("CLAWMETRY_ENDPOINT")
        or _env("CLAWMETRY_INGEST_URL")
        or _config_endpoint()
        or DEFAULT_INGEST_URL
    ).rstrip("/")


def app_url() -> str:
    """Base URL for app-side calls (OAuth start, account lookup, dashboard links).

    When a custom endpoint is configured, app-side traffic goes to the same
    host — a self-hosted deployment is one server. CLAWMETRY_APP_BASE remains
    an explicit override for split cloud deployments.
    """
    return (
        _env("CLAWMETRY_APP_BASE")
        or _env("CLAWMETRY_ENDPOINT")
        or _env("CLAWMETRY_INGEST_URL")
        or _config_endpoint()
        or DEFAULT_APP_URL
    ).rstrip("/")


def is_custom_endpoint() -> bool:
    """True when traffic is repointed away from the managed ClawMetry cloud.

    Used to suppress cloud-only phone-homes (install telemetry, anonymous
    funnel analytics) so a self-hosted deployment's data never leaves it.
    """
    return ingest_url() != DEFAULT_INGEST_URL


def endpoint_hosts() -> set[str]:
    """Hostnames of the configured endpoints (for interceptor self-exclusion)."""
    hosts = set()
    for url in (ingest_url(), app_url()):
        try:
            host = urlparse(url).hostname
            if host:
                hosts.add(host)
        except Exception:
            continue
    return hosts
