"""clawmetry/telemetry.py — anonymous, opt-out, install-lifecycle pings.

What we send (one POST per lifecycle event — ``install`` once ever,
``update`` at most once per new version, ``onboarded`` once per explicit
onboarding choice):

  {
    "install_id":  "<random uuid4 stored in ~/.clawmetry/install_id>",
    "event":       "install" | "update" | "onboarded",
    "version":     "0.12.167",
    "os":          "Darwin",       # platform.system()
    "os_version":  "25.3.0",       # platform.release()
    "python":      "3.11.15",      # platform.python_version()
    "agent":       "openclaw" | "nemoclaw" | "hermes" | "none",
    "is_ci":       true / false,
    "ci_provider": "github_actions" | "gitlab_ci" | …  (only if is_ci)
    "onboarding_state": "managed" | "selfhost_license" | "selfhost_trial"
                                   (only on event="onboarded")
  }

What we DO NOT send: hostname, username, IP (cloud derives country from
the request IP and discards the IP itself), api_key, email, workspace
path, file contents, anything PII or workspace-specific.

Opt-out (any one disables this module):
  - export CLAWMETRY_NO_TELEMETRY=1
  - export DO_NOT_TRACK=1                  (industry standard)
  - touch ~/.clawmetry/notelemetry         (file marker for shared envs)

The ping is fire-and-forget on a daemon thread with a 3s timeout. A
network failure, DNS hijack, or the cloud being down NEVER affects
``clawmetry`` startup or surfaces an error to the user.

Why first-run instead of pip-install: PyPI removed install hooks years
ago for supply-chain safety, so ``pip install clawmetry`` cannot phone
home directly. We instead fire on ``clawmetry`` CLI / daemon startup,
deduped through ``~/.clawmetry/telemetry_state.json`` (the last version
we reported): a restart on an already-reported version sends nothing, a
version change sends one ``update``.
"""
from __future__ import annotations

import json
import logging
import os
import platform
import threading
import time
import urllib.request
import uuid
from pathlib import Path

log = logging.getLogger(__name__)

TELEMETRY_URL_DEFAULT = "https://app.clawmetry.com/api/install"
TELEMETRY_TIMEOUT_SEC = 3
CONFIG_DIR = Path.home() / ".clawmetry"
INSTALL_ID_FILE = CONFIG_DIR / "install_id"
OPTOUT_MARKER = CONFIG_DIR / "notelemetry"
STATE_FILE = CONFIG_DIR / "telemetry_state.json"

# CI env-var → provider name. Order matters when more than one is set
# (some providers leave others' vars in for back-compat); pick the most
# specific. ``CI=true`` is a generic last-resort signal.
_CI_PROVIDERS = (
    ("GITHUB_ACTIONS",       "github_actions"),
    ("GITLAB_CI",            "gitlab_ci"),
    ("CIRCLECI",             "circleci"),
    ("TRAVIS",               "travis"),
    ("BUILDKITE",            "buildkite"),
    ("JENKINS_URL",          "jenkins"),
    ("TEAMCITY_VERSION",     "teamcity"),
    ("BITBUCKET_BUILD_NUMBER","bitbucket"),
    ("CODEBUILD_BUILD_ID",   "aws_codebuild"),
    ("DRONE",                "drone"),
    ("AGENT_NAME",           "azure_pipelines"),  # Azure Pipelines
    ("CI",                   "generic"),
)

# Heuristic agent detection: existence of a per-agent state directory.
# The Hermes adapter PR (#708) and ongoing multi-agent work add new
# agents — keep this list synced with clawmetry/adapters/.
_AGENT_DIRS = (
    ("openclaw", Path.home() / ".openclaw"),
    ("nemoclaw", Path.home() / ".nemoclaw"),
    ("hermes",   Path.home() / ".hermes"),
)


def _is_optout() -> bool:
    """Honour both the env var and the file marker. Either disables.

    DO_NOT_TRACK is the W3C-style cross-tool convention; we honour it
    out of respect even though it's not a perfect fit for OSS install
    counters.
    """
    if os.environ.get("CLAWMETRY_NO_TELEMETRY", "").strip() not in ("", "0", "false", "False"):
        return True
    if os.environ.get("DO_NOT_TRACK", "").strip() not in ("", "0", "false", "False"):
        return True
    if OPTOUT_MARKER.exists():
        return True
    return False


def _detect_ci() -> tuple[bool, str | None]:
    """Return (is_ci, provider_name_or_None).

    Walks the ``_CI_PROVIDERS`` list in priority order; first hit wins.
    "Hit" is any non-empty value, since some providers set the var to
    things other than ``true``.
    """
    for env_var, name in _CI_PROVIDERS:
        if os.environ.get(env_var, "").strip():
            return True, name
    return False, None


def _detect_agent() -> str:
    """Return one of openclaw / nemoclaw / hermes / none.

    Order in ``_AGENT_DIRS`` matters when a host has multiple agents
    (rare but possible) — first match wins. We pick OpenClaw first since
    that's our primary integration; users with multi-agent setups still
    show up under the agent they paired most recently.
    """
    for name, p in _AGENT_DIRS:
        if p.exists():
            return name
    return "none"


def _ensure_install_id() -> str | None:
    """Read existing install_id, or create one and persist.

    Returns ``None`` if we can't write to ``CONFIG_DIR`` (e.g. read-only
    filesystem). In that case we silently skip telemetry rather than
    pollute logs every time.
    """
    try:
        if INSTALL_ID_FILE.exists():
            txt = INSTALL_ID_FILE.read_text(encoding="utf-8").strip()
            # Sanity-check it's a UUID-shaped thing; otherwise regenerate.
            if 16 < len(txt) <= 64 and all(c in "0123456789abcdef-" for c in txt):
                return txt
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        new = str(uuid.uuid4())
        INSTALL_ID_FILE.write_text(new + "\n", encoding="utf-8")
        return new
    except Exception as e:
        log.debug("telemetry: cannot persist install_id: %s", e)
        return None


def _build_payload(version: str, event: str = "install", extra: dict | None = None) -> dict:
    """Assemble the JSON body. Pure function — no I/O — so tests can
    stub the small helpers and assert the shape independently."""
    is_ci, ci_provider = _detect_ci()
    payload = {
        "install_id":  _ensure_install_id() or "",
        "event":       event,
        "version":     version,
        "os":          platform.system() or "unknown",
        "os_version":  platform.release() or "",
        "python":      platform.python_version(),
        "agent":       _detect_agent(),
        "is_ci":       is_ci,
        "ci_provider": ci_provider,
    }
    if extra:
        payload.update(extra)
    return payload


_SSL_CTX = None


def _ssl_context():
    """An SSLContext that can verify public certs wherever we run.

    The stdlib default trusts whatever OpenSSL finds on the box, which is
    nothing at all inside a frozen bundle and nothing on a python.org
    interpreter whose certificate installer was never run. Both cases
    fail closed with CERTIFICATE_VERIFY_FAILED, and because this module
    swallows every error by design, they fail SILENTLY: the ping simply
    never arrives. Same ladder the desktop shell uses (OS trust store,
    then certifi's bundle, then the default), cached because building it
    parses a PEM. Never raises; the last rung is the old behaviour.
    """
    global _SSL_CTX
    if _SSL_CTX is not None:
        return _SSL_CTX
    import ssl
    try:
        import truststore  # type: ignore
        _SSL_CTX = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return _SSL_CTX
    except Exception:
        pass
    try:
        import certifi  # type: ignore
        _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
        return _SSL_CTX
    except Exception:
        pass
    _SSL_CTX = ssl.create_default_context()
    return _SSL_CTX


def _post(payload: dict, url: str, api_key: str = "") -> None:
    """Fire-and-forget POST. Swallows every exception by design — any
    failure here must NEVER surface to the user.

    ``api_key`` is only ever set by the desktop ping below, and only so
    the machine can be listed under "Desktop apps" in its own owner's
    account. The anonymous install ping never sends it."""
    try:
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent":   f"clawmetry/{payload.get('version','?')} install-telemetry",
        }
        if api_key.startswith("cm_"):
            headers["Authorization"] = f"Bearer {api_key}"
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers=headers,
        )
        ctx = _ssl_context() if url.lower().startswith("https://") else None
        with urllib.request.urlopen(req, timeout=TELEMETRY_TIMEOUT_SEC, context=ctx) as r:
            r.read()  # drain so the connection releases cleanly
    except Exception as e:
        log.debug("telemetry: post failed: %s", e)


def _read_state() -> dict:
    """Lifecycle state: {install_id, first_version, last_version,
    first_ts, last_ts}. Empty dict when absent/corrupt — never raises."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_state(state: dict) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    except Exception as e:
        log.debug("telemetry: cannot persist state: %s", e)


def _derive_event(install_id: str, version: str) -> str | None:
    """What (if anything) to report for this startup.

    - state file says we already reported this version  → nothing
    - state file has a different version                → "update"
    - no state file, but the legacy ``.pinged`` marker  → "update"
      (an existing install that just upgraded onto the first version
      that ships lifecycle state — its first_run row is already in the
      cloud, so "install" would double-count it)
    - nothing on disk at all                            → "install"
    """
    state = _read_state()
    last = state.get("last_version")
    if last == version:
        return None
    if last:
        return "update"
    if _has_pinged_this_install(install_id):
        return "update"
    return "install"


def _record_reported(install_id: str, version: str, event: str) -> None:
    """Persist that ``version`` has been reported, after a post attempt.
    Also writes the legacy ``.pinged`` marker so a downgrade to an older
    clawmetry (which only knows the marker) stays silent."""
    state = _read_state()
    now = int(time.time())
    if not state.get("first_version"):
        state["first_version"] = version
        state["first_ts"] = now
    state["install_id"] = install_id
    state["last_version"] = version
    state["last_ts"] = now
    state["last_event"] = event
    _write_state(state)
    _mark_pinged(install_id)


def _has_pinged_this_install(install_id: str) -> bool:
    """A side marker file ``install_id.pinged`` records that we already
    posted for this install_id. Cloud also dedups via UNIQUE constraint;
    this just spares the network roundtrip on every cold start."""
    if not install_id:
        return False
    try:
        marker = INSTALL_ID_FILE.with_suffix(".pinged")
        return marker.exists()
    except Exception:
        return False


def _mark_pinged(install_id: str) -> None:
    if not install_id:
        return
    try:
        marker = INSTALL_ID_FILE.with_suffix(".pinged")
        marker.write_text(str(int(time.time())), encoding="utf-8")
    except Exception:
        pass


def _resolve_telemetry_url() -> str:
    """Telemetry URL to post to, or "" when pings must not fire.

    A custom endpoint (self-hosted / enterprise, see clawmetry.endpoints)
    means data stays inside the deployment: skip the managed-cloud install
    pings entirely unless CLAWMETRY_TELEMETRY_URL is explicitly set."""
    url = os.environ.get("CLAWMETRY_TELEMETRY_URL", "")
    if url:
        return url
    try:
        # egress_suppressed(), not is_custom_endpoint(): a self-hosted SERVER
        # container does not necessarily set CLAWMETRY_ENDPOINT, because it IS
        # the endpoint. Keying only off the endpoint left that process pinging
        # the managed cloud on startup even with SELF_HOSTED=true. Also covers
        # CLAWMETRY_OFFLINE (air-gapped), where the call can only ever hang.
        from clawmetry.endpoints import egress_suppressed
        if egress_suppressed():
            return ""
    except Exception:
        # Fail closed. A missing or older endpoints module must not result in
        # an unexpected phone-home from a customer's network.
        return ""
    return TELEMETRY_URL_DEFAULT


def _send_in_background(version: str) -> None:
    """Worker that runs on the daemon thread. Fully isolated — no
    raised exception can bubble back to the caller."""
    try:
        if _is_optout():
            return
        install_id = _ensure_install_id()
        if not install_id:
            return
        event = _derive_event(install_id, version)
        if event is None:
            return
        payload = _build_payload(version, event=event)
        url = _resolve_telemetry_url()
        if not url:
            return
        _post(payload, url)
        _record_reported(install_id, version, event)
    except Exception as e:
        log.debug("telemetry: background failure: %s", e)


def _send_event_in_background(event: str, version: str, extra: dict | None) -> None:
    """Worker for explicit lifecycle events (e.g. ``onboarded``).
    No version-dedup — the caller decides when the event happened; the
    cloud's UNIQUE(install_id, event, version) still absorbs repeats."""
    try:
        if _is_optout():
            return
        install_id = _ensure_install_id()
        if not install_id:
            return
        payload = _build_payload(version, event=event, extra=extra)
        url = _resolve_telemetry_url()
        if not url:
            return
        _post(payload, url)
    except Exception as e:
        log.debug("telemetry: event background failure: %s", e)


def maybe_ping(version: str = "unknown") -> threading.Thread | None:
    """Public entry point. Call once on CLI startup.

    Returns the thread for testing convenience; ``None`` if telemetry
    is opt-out (caller doesn't need to do anything either way).

    The thread is daemon=True so it never blocks process exit. If the
    user runs ``clawmetry --version`` and exits in 50ms, the post
    silently goes nowhere — that's by design; we'd rather miss a count
    than slow down a CLI invocation.
    """
    if _is_optout():
        return None
    t = threading.Thread(
        target=_send_in_background,
        args=(version,),
        daemon=True,
        name="clawmetry-telemetry",
    )
    t.start()
    return t


def ping_event(event: str, version: str = "unknown",
               extra: dict | None = None) -> threading.Thread | None:
    """Fire one explicit lifecycle event (e.g. ``onboarded`` with
    ``extra={"onboarding_state": "managed"}``). Same opt-out and
    fire-and-forget contract as :func:`maybe_ping`."""
    if _is_optout():
        return None
    t = threading.Thread(
        target=_send_event_in_background,
        args=(event, version, extra),
        daemon=True,
        name="clawmetry-telemetry-event",
    )
    t.start()
    return t


# ── Desktop app: per-open telemetry (daemon stage) ───────────────────────────
# The .app/.exe shell pings ``/api/desktop/open`` the moment its window
# appears (see desktop/app.py) — that stage fires even when the Python
# bootstrap never completes. This is the second stage: once the daemon is
# actually running we report what the shell could not know — which agent
# runtimes this machine has data for, whether the install syncs to cloud or
# stays local, and which node it is. Correlated with the shell ping by
# ``session_id``, so "opened but never reached a working daemon" is a
# subtraction rather than a guess.
#
# Fires ONLY when launched by the desktop shell (CLAWMETRY_LAUNCHER=desktop);
# a plain ``pip install clawmetry && clawmetry`` never sends this.
#
# Same privacy contract as the install ping above: no hostname, username,
# IP (the server derives a country and drops the IP), workspace path, or
# transcript content. The one addition is the cm_ key, sent as a bearer
# header purely so the machine shows up under "Desktop apps" in its own
# owner's account; without a paired key the ping stays anonymous.
DESKTOP_PING_PATH = "/api/desktop/open"
# Runtime detection walks the home dir (~3s) and a freshly-claimed account
# key can land seconds after boot — both settle inside this delay.
DESKTOP_PING_DELAY_SEC = 10.0
CONFIG_JSON = CONFIG_DIR / "config.json"
NOCLOUD_MARKER = CONFIG_DIR / "nocloud"


def _read_config() -> dict:
    try:
        data = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _sync_mode(cfg: dict) -> str:
    """cloud | local | selfhosted | unknown — how this install is wired.

    ``local`` is the ``clawmetry disconnect`` state: the daemon runs and
    keeps everything on the machine. ``selfhosted`` means an enterprise
    endpoint is configured (and, per the contract above, we never get
    here — those installs don't ping the managed cloud at all)."""
    try:
        from clawmetry.endpoints import is_custom_endpoint
        if is_custom_endpoint():
            return "selfhosted"
    except Exception:
        pass
    try:
        if NOCLOUD_MARKER.exists():
            return "local"
    except Exception:
        pass
    if cfg.get("local_only"):
        return "local"
    if str(cfg.get("api_key") or "").startswith("cm_"):
        return "cloud"
    return "unknown"


def _monitored_runtimes() -> list:
    """Runtime ids with data on this machine, e.g.
    ``["openclaw", "claude_code", "cursor"]``. Ids only — no paths, no
    session contents, no counts."""
    out = []
    for name, p in _AGENT_DIRS:
        try:
            if p.exists():
                out.append(name)
        except Exception:
            pass
    try:
        from clawmetry.sync import _detect_runtimes_lite
        for r in (_detect_runtimes_lite() or []):
            rid = str((r or {}).get("id") or "").strip()
            if rid and rid not in out:
                out.append(rid)
    except Exception:
        pass
    return out[:40]


def _build_desktop_payload(version: str) -> dict:
    cfg = _read_config()
    try:
        open_count = int(os.environ.get("CLAWMETRY_DESKTOP_OPEN_COUNT", "") or 0)
    except ValueError:
        open_count = 0
    runtimes = _monitored_runtimes()
    return {
        "install_id":      _ensure_install_id() or "",
        "event":           "desktop_ready",
        "stage":           "daemon",
        "session_id":      os.environ.get("CLAWMETRY_DESKTOP_SESSION", "")[:64],
        "open_count":      open_count,
        "first_open":      open_count == 1,
        "desktop_version": os.environ.get("CLAWMETRY_DESKTOP_VERSION", "")[:32],
        "version":         version,
        "os":              platform.system() or "unknown",
        "os_version":      platform.release() or "",
        "arch":            platform.machine() or "",
        "python":          platform.python_version(),
        "mode":            _sync_mode(cfg),
        "runtimes":        runtimes,
        "runtime_count":   len(runtimes),
        "node_id":         str(cfg.get("node_id") or "")[:64],
    }


def _send_desktop_ping(version: str) -> None:
    """Worker body. Sleeps out the settle delay, then posts once.
    Swallows everything — telemetry never surfaces to the user."""
    try:
        time.sleep(DESKTOP_PING_DELAY_SEC)
        if _is_optout():
            return
        payload = _build_desktop_payload(version)
        if not payload.get("install_id"):
            return
        url = os.environ.get("CLAWMETRY_DESKTOP_PING_URL", "").strip()
        if not url:
            try:
                from clawmetry.endpoints import is_custom_endpoint, app_url
                if is_custom_endpoint():
                    # Enterprise deployment — its data stays inside it.
                    return
                base = app_url()
            except Exception:
                base = "https://app.clawmetry.com"
            url = base.rstrip("/") + DESKTOP_PING_PATH
        api_key = str(_read_config().get("api_key") or "")
        _post(payload, url, api_key=api_key)
    except Exception as e:
        log.debug("telemetry: desktop ping failed: %s", e)


def maybe_desktop_ping(version: str = "unknown") -> threading.Thread | None:
    """Public entry point, called once on CLI startup alongside
    :func:`maybe_ping`. No-ops unless the desktop shell launched us.

    Returns the thread for tests; ``None`` when it does not apply."""
    if os.environ.get("CLAWMETRY_LAUNCHER", "").strip().lower() != "desktop":
        return None
    if _is_optout():
        return None
    t = threading.Thread(
        target=_send_desktop_ping,
        args=(version,),
        daemon=True,
        name="clawmetry-desktop-ping",
    )
    t.start()
    return t
