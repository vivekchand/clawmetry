"""Is the DuckDB this process can open actually *a node's* store?

The hosted container ships the same OSS route modules as a laptop install,
and ``clawmetry.local_store.get_store()`` happily opens a DuckDB file there
— an **empty** one, because no daemon ever ingested into it. Every reader
that treats "the open succeeded" as "the answer is authoritative" therefore
reports the container's emptiness as a fact about the user's machine.

That is not a hypothetical. It is the same defect three times:

  * 2026-09-14 — the hosted Guard tab said "No sessions running right now"
    beside a node running dozens. Fixed by serving ``guardSessions`` from
    the snapshot (cloud ``cm-cloud-guard``).
  * 2026-09-14 — the Signals drill-down said "No sessions".
  * 2026-10-06 — the Overview hero said **"It's idle right now."** on
    app.clawmetry.com while localhost:8900, reading the same node, said
    "It's working right now." ``/api/live-sessions`` answered
    ``{"available": true, "counts": {"working": 0}}`` from the container's
    empty store, and ``available: true`` is the hero's licence to state the
    negative as fact.

The shape of the bug is always "an empty success outranks a real signal".
The cure is to stop any such reader from *claiming* authority it does not
have: when this returns False, answer "unknown", never "zero".

``CLAWMETRY_CLOUD=1`` is set by the hosted image (clawmetry-cloud
``Dockerfile``), and ``CLOUD_MODE`` by its ``config.py``; both spellings
were already being probed ad hoc in ``routes/quality.py``,
``routes/readiness.py``, ``routes/improve.py`` and ``routes/onboarding.py``.
This module is the one place that knows them, so a fifth caller cannot
invent a sixth spelling.
"""

from __future__ import annotations

import os
import sys

_TRUTHY = {"1", "true", "yes", "on"}


def running_in_cloud() -> bool:
    """True when this process is the hosted dashboard, not a node install.

    Checks every spelling the hosted image has ever used. Cheap enough to
    call per request (two env reads and two ``sys.modules`` lookups); no
    caching, so a test can flip the env var without reloading the module.
    """
    if (os.environ.get("CLAWMETRY_CLOUD", "") or "").strip():
        return True
    if (os.environ.get("CLOUD_MODE", "") or "").strip().lower() in _TRUTHY:
        return True
    for mod in ("dashboard", "config"):
        if getattr(sys.modules.get(mod), "CLOUD_MODE", False):
            return True
    return False


def store_is_authoritative() -> bool:
    """May a reader state this store's emptiness as a fact about the node?

    False in the hosted container, where an open DuckDB proves nothing. The
    hosted UI has a real answer for these surfaces — the daemon's E2E
    snapshot — and reaches it through the ``cm-cloud-*`` interceptors; a
    route that returns "unknown" here lets that answer win, where a route
    that returns "zero" overrides it with a lie.
    """
    return not running_in_cloud()
