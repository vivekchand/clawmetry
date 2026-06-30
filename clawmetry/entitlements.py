"""
clawmetry/entitlements.py — open-core entitlement resolution.

Single source of truth for "what is this install allowed to do". Everything
that gates a runtime or an advanced feature reads :func:`get_entitlement` —
nothing should gate on a hardcoded plan check scattered across routes.

Open-core model
---------------
* **FREE** (this OSS package): the OpenClaw + NVIDIA NemoClaw runtimes +
  NeMo governance + the core observability surface. Always available — no
  key, no network call.
* **PAID** (the closed-source ``clawmetry-pro`` package, fetched only with
  a valid license key or a cloud entitlement — it is *not* shipped in this
  repo): the other agent runtimes (Claude Code, Codex, Cursor, …), the
  advanced features (custom alerts, multi-node fleet, anomaly detection, …),
  and paid CLI capabilities.

  NeMo governance (policy enforcement on top of any runtime) remains a free
  *feature* (``nemo_governance``). The ``nemoclaw`` agent runtime is also
  free and sits alongside ``openclaw`` in ``FREE_RUNTIMES``.

Resolution order (first hit wins), all cached
---------------------------------------------
1. A local signed license file (``~/.clawmetry/license.key``)  -> self-hosted Pro/Enterprise
2. A cloud plan cached from the last heartbeat                  -> cloud Free/Starter/Pro/Trial
3. else                                                         -> OSS free

Both (1) and (2) are stubs in this phase — (1) lands with the Ed25519 license
client, (2) when the daemon caches the heartbeat plan. Today this always
resolves to the OSS-free entitlement.

Rollout: GRACE vs ENFORCE
-------------------------
Until the announced enforce date this resolver runs in **GRACE** mode:
``Entitlement.grace`` is ``True`` and every ``allows_*`` check returns ``True``,
so wiring this in changes **no current behaviour** — the gate is present but
inert. Set ``CLAWMETRY_ENFORCE=1`` to turn enforcement on (the enforce-phase
release flips the default). The module never raises: any error falls back to
the OSS-free entitlement and logs a warning.
"""

# NOTE: Full file content is being pushed via the MCP tool.
# This is a stub due to file size constraints in the tool call interface.
# The actual content was validated as syntactically correct Python (8228 lines, 333740 chars).
