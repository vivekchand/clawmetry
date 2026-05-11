"""clawmetry/telemetry.py — anonymous, opt-out, first-run install ping.

What we send (one POST, max once per install):

  {
    "install_id":  "<random uuid4 stored in ~/.clawmetry/install_id>",
    "event":       "first_run",
    "version":     "0.12.167",
    "os":          "Darwin",       # platform.system()
    "os_version":  "25.3.0",       # platform.release()
    "python":      "3.11.15",      # platform.python_version()
    "agent":       "openclaw" | "nemoclaw" | "hermes" | "none",
    "is_ci":       true / false,
    "ci_provider": "github_actions" | "gitlab_ci" | …  (only if is_ci)
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
home directly. We instead fire on first ``clawmetry`` CLI invocation,
gated by ``~/.clawmetry/install_id`` so subsequent runs are silent.
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
from typing import Optional, Tuple

log = logging.getLogger(__name__)

TELEMETRY_URL_DEFAULT = "https://app.clawmetry.com/api/install"
TELEMETRY_TIMEOUT_SEC = 3
CONFIG_DIR = Path.home() / ".clawmetry"
INSTALL_ID_FILE = CONFIG_DIR / "install_id"
OPTOUT_MARKER = CONFIG_DIR / "notelemetry"

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


def _detect_ci() -> Tuple[bool, Optional[str]]:
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


def _ensure_install_id() -> Optional[str]:
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


def _build_payload(version: str) -> dict:
    """Assemble the JSON body. Pure function — no I/O — so tests can
    stub the small helpers and assert the shape independently."""
    is_ci, ci_provider = _detect_ci()
    return {
        "install_id":  _ensure_install_id() or "",
        "event":       "first_run",
        "version":     version,
        "os":          platform.system() or "unknown",
        "os_version":  platform.release() or "",
        "python":      platform.python_version(),
        "agent":       _detect_agent(),
        "is_ci":       is_ci,
        "ci_provider": ci_provider,
    }


def _post(payload: dict, url: str) -> None:
    """Fire-and-forget POST. Swallows every exception by design — any
    failure here must NEVER surface to the user."""
    try:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent":   f"clawmetry/{payload.get('version','?')} install-telemetry",
            },
        )
        with urllib.request.urlopen(req, timeout=TELEMETRY_TIMEOUT_SEC) as r:
            r.read()  # drain so the connection releases cleanly
    except Exception as e:
        log.debug("telemetry: post failed: %s", e)


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


def _send_in_background(version: str) -> None:
    """Worker that runs on the daemon thread. Fully isolated — no
    raised exception can bubble back to the caller."""
    try:
        if _is_optout():
            return
        payload = _build_payload(version)
        if not payload.get("install_id"):
            return
        if _has_pinged_this_install(payload["install_id"]):
            return
        url = os.environ.get("CLAWMETRY_TELEMETRY_URL", TELEMETRY_URL_DEFAULT)
        _post(payload, url)
        _mark_pinged(payload["install_id"])
    except Exception as e:
        log.debug("telemetry: background failure: %s", e)


def maybe_ping(version: str = "unknown") -> Optional[threading.Thread]:
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
