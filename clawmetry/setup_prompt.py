"""clawmetry/setup_prompt.py -- the copy-paste prompt you hand your agent.

Why this exists
---------------
ClawMetry's users delegate work to coding agents by definition -- that is
what the product observes. Yet the only setup paths shipped were "run the
installer" and "read a doc", neither of which is aimed at the thing the
user actually drives.

So: a prompt per runtime, written for the agent, that gets telemetry
flowing in one attempt.

Generated, not written
----------------------
Every endpoint, header, content type and cap here comes from
``clawmetry.ingest_contract``, the same declaration the server validates
against. A hand-written prompt drifts the first time a header is renamed,
and a drifted setup prompt is worse than none: the agent writes the wrong
header confidently and the request fails somewhere the user cannot see.

Half of it is negative space
----------------------------
The instructive part of a good setup prompt is what it forbids. Coding
agents reliably: mis-substitute secrets (dropping characters, wrapping
them in quotes, or leaving the literal placeholder in place); "correct" a
content type that was already right; and invent config keys, env-var
names and endpoint paths that look plausible and do not exist. Each of
those gets a line, because an unstated constraint is one the agent will
violate helpfully.

The seam
--------
This module names no runtime and hardcodes no vendor value. Where a
runtime has registered an OTel profile (``clawmetry.otel_profiles``, which
paid runtimes populate from clawmetry-pro), its label and its
``clawmetry instrument`` support are read from that profile at render
time. A free install renders the generic OTLP prompt, which works.
"""

from __future__ import annotations

import re
from typing import Optional

from clawmetry.ingest_contract import (
    CONTRACT_VERSION,
    HEADER_ENV,
    HEADER_KEY,
    HEADER_RUNTIME,
    MAX_BODY_BYTES,
)

#: Shown where a real key is not available to substitute. Deliberately
#: ugly and obviously not a key, so an agent leaving it in place produces
#: a 401 with a clear message rather than something that looks plausible.
KEY_PLACEHOLDER = "PASTE_YOUR_CLAWMETRY_KEY_HERE"

DEFAULT_LOCAL_ENDPOINT = "http://localhost:8900"

#: Same shape the ingest gate accepts, so a runtime this renders a prompt
#: for is a runtime the server will take the header for.
VALID_RUNTIME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")


def _profile(runtime: str):
    """The registered OTel profile for ``runtime``, or None. Never raises."""
    try:
        from clawmetry import otel_profiles

        return otel_profiles.by_runtime(runtime)
    except Exception:
        return None


def render(
    runtime: str = "",
    *,
    endpoint: str = "",
    key: Optional[str] = None,
    include_verification: bool = True,
) -> str:
    """The prompt text for ``runtime``.

    ``key`` is substituted when given; otherwise the placeholder is used
    and the prompt tells the agent to ask for the real one rather than
    invent it.
    """
    rt = (runtime or "").strip().lower()
    base = (endpoint or DEFAULT_LOCAL_ENDPOINT).rstrip("/")
    secret = key or KEY_PLACEHOLDER
    prof = _profile(rt) if rt else None
    label = (getattr(prof, "label", "") or rt or "this agent")
    mb = MAX_BODY_BYTES // (1024 * 1024)

    out: list = []
    a = out.append

    a(f"Set up ClawMetry observability for {label}.")
    a("")
    a("ClawMetry watches AI agents: what they did, what it cost, and")
    a("whether they got stuck. It already detects agents running on the")
    a("same machine as ClawMetry itself, with no configuration. This task")
    a("is the other case -- pointing an agent that runs somewhere else at")
    a("it.")
    a("")
    a(f"Contract version: {CONTRACT_VERSION}")
    a("")

    a("## What to do")
    a("")
    a("Configure this agent's OpenTelemetry exporter to send OTLP over")
    a("HTTP to ClawMetry:")
    a("")
    a(f"  Endpoint:  {base}/v1/traces   (also /v1/logs and /v1/metrics)")
    a(f"  Header:    {HEADER_KEY}: {secret}")
    if rt:
        a(f"  Header:    {HEADER_RUNTIME}: {rt}")
    a(f"  Header:    {HEADER_ENV}: <environment, e.g. production>   (optional)")
    a("")
    a("If the agent or its framework already exports OpenTelemetry, change")
    a("its exporter endpoint and headers rather than adding a second")
    a("exporter. If it does not, use the OpenTelemetry SDK for its")
    a("language.")
    a("")

    if prof is not None and getattr(prof, "instrumenter", None) is not None:
        a("This runtime has a native exporter ClawMetry can configure for")
        a("you. Try this first, and only fall back to manual setup if it")
        a("reports that it cannot:")
        a("")
        a(f"  clawmetry instrument {rt}")
        a("")

    a("## Rules -- these are the ones that get this wrong")
    a("")
    a(f"1. The key goes in the `{HEADER_KEY}` header. Not in a query")
    a("   parameter, not in `Authorization: Bearer`, not in the body.")
    if key:
        a("2. The key above is real. Copy it exactly -- do not re-wrap it in")
        a("   quotes, do not shorten it, do not regenerate it.")
    else:
        a(f"2. `{KEY_PLACEHOLDER}` is a placeholder, not a key. Ask the")
        a("   person who gave you this prompt for the real one. Do NOT")
        a("   invent a key, and do not leave the placeholder in place.")
    a("3. Both `application/x-protobuf` and `application/json` are")
    a("   accepted, and gzip is accepted on either. If the exporter")
    a("   already produces one of those, leave it alone -- there is")
    a("   nothing to fix.")
    a("4. Use only the header names, endpoints and settings written above.")
    a("   If a config key you want is not in this prompt, it does not")
    a("   exist. Do not guess one that looks plausible.")
    a("5. Do not modify anything about how the agent itself behaves. This")
    a("   is observability: it watches, it does not change what runs.")
    a(f"6. Keep request bodies under {mb} MB. The exporter's default")
    a("   batching handles this; do not raise a batch size to 'improve")
    a("   throughput'.")
    a("")

    if include_verification:
        a("## Then verify, and report back")
        a("")
        a("Do not report success because the config was written. Confirm")
        a("that data actually arrived:")
        a("")
        a("  1. Make the agent do one small thing that calls a model.")
        a(f"  2. curl -s {base}/api/otel-status")
        a("  3. Tell the user the counts you got back.")
        a("")
        a("If the counts are zero, the setup did not work. Say so plainly")
        a("and report the exact error, rather than describing the")
        a("configuration you wrote.")
        a("")
        a("Common causes, in the order worth checking:")
        a("  - a 401 means the key is wrong or was not sent;")
        a("  - a 403 means the key is real but cannot push -- it needs the")
        a("    write:ingest scope;")
        a("  - a 400 names what it could not decode;")
        a("  - nothing at all usually means the exporter was configured")
        a("    but the process was never restarted.")
        a("")

    return "\n".join(out)
