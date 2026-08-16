"""clawmetry/attention_hook.py — the `clawmetry hook attention` client.

Backs the one line a user adds to a runtime's own hook config to upgrade its
needs-you badge from "Maybe waiting" (inferred) to "Waiting for you"
(reported by the runtime):

    clawmetry hook attention --runtime qwen_code

It reads the runtime's hook payload from stdin, forwards it to the local
dashboard's ``/api/hooks/attention`` receiver, and exits. Replaces a
multi-line ``curl`` in every wiring snippet, which people get wrong.

Three properties this MUST have, because it runs inside somebody's agent at
the moment that agent is asking a human for permission:

* **It never fails.** Always exit 0, print nothing. A hook that errors or
  writes to stdout can change what the runtime does next; a hook that hangs
  stalls the turn. Nothing about a badge justifies either.
* **It never blocks for long.** A short timeout, and a failed POST is simply
  dropped — the daemon's inference pass still covers the session, so the cost
  of losing this is precision, not the feature.
* **It never decides anything.** This tells ClawMetry that a prompt is open.
  It does not answer the prompt, and shares no code path with the approvals
  gate. Observation and decision stay separate on purpose.

Stdlib only: the hook process starts and dies on every permission prompt, so
its import cost is paid over and over.
"""
from __future__ import annotations

import json
import sys

#: Deliberately short. The receiver does its own write off-thread, so it
#: answers immediately; anything slower than this means something is wrong
#: and waiting longer only makes the agent wait longer too.
_TIMEOUT_S = 3.0


def _arg(argv: list, flag: str, default: str = "") -> str:
    if flag in argv:
        try:
            return argv[argv.index(flag) + 1]
        except IndexError:
            return default
    return default


def attention_main(argv: "list | None" = None) -> int:
    """Entry point for ``clawmetry hook attention``. ALWAYS returns 0.

    Flags:
      ``--runtime <id>``  which runtime is reporting (required)
      ``--base <url>``    dashboard base; discovered when omitted
      ``--event <name>``  ``waiting`` (default) or ``resolved``
    """
    argv = list(argv or [])
    runtime = _arg(argv, "--runtime").strip().lower()
    if not runtime:
        return 0  # nothing we can attribute — stay silent, never complain

    event = (_arg(argv, "--event", "waiting") or "waiting").strip().lower()

    base = _arg(argv, "--base").rstrip("/")
    if not base:
        try:
            from clawmetry.claude_code_gate import dashboard_base
            base = dashboard_base()
        except Exception:
            base = "http://127.0.0.1:8900"

    # The runtime's payload, forwarded unmodified — the receiver knows how to
    # read every spelling of session id and tool name, so this stays dumb.
    try:
        raw = sys.stdin.read()
        body = json.loads(raw) if raw.strip() else {}
        if not isinstance(body, dict):
            body = {}
    except Exception:
        body = {}

    url = (f"{base}/api/hooks/attention"
           f"?runtime={runtime}&event={event}")
    try:
        import urllib.request

        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S):
            pass
    except Exception:
        pass  # dashboard down, wrong port, anything — inference still covers it
    return 0
