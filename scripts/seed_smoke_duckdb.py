#!/usr/bin/env python3
"""Seed realistic-shape clawmetry.duckdb for the API-latency smoke gate
(issue #1241). 1k events + 200 heartbeats + 50 memory blobs + 5 sessions
spread across the last 7 days. Reads CLAWMETRY_LOCAL_STORE_PATH."""

from __future__ import annotations

import hashlib
import os
import random
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Make ``clawmetry.local_store`` importable when running from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from clawmetry import local_store  # noqa: E402

NODE = "smoke-ci-node"
N_EVENTS, N_HB, N_MEM, N_SESS = 1000, 200, 50, 5
MODELS = ["claude-sonnet-4-5", "claude-opus-4-5", "gpt-4o", "gpt-4o-mini"]
ETYPES = ["message", "model.completed", "tool.invoked", "tool.completed", "reasoning"]
TOOLS = ["bash", "edit", "read", "grep", "write", "glob"]


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def seed() -> None:
    db_path = os.environ.get("CLAWMETRY_LOCAL_STORE_PATH", "")
    if not db_path:
        raise SystemExit("CLAWMETRY_LOCAL_STORE_PATH must be set.")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    print(f"[seed] target db: {db_path}", flush=True)

    store = local_store.get_store(read_only=False)
    rng = random.Random(42)  # deterministic across runs
    horizon = datetime.now(timezone.utc) - timedelta(days=7)
    span = 7 * 24 * 3600

    sids = [f"smoke-sess-{i:03d}" for i in range(N_SESS)]
    for i, sid in enumerate(sids):
        started = horizon + timedelta(hours=rng.uniform(0, 144))
        store.ingest_session({
            "session_id": sid, "node_id": NODE, "agent_id": "main",
            "title": f"Smoke session {i}",
            "started_at": _iso(started),
            "last_active_at": _iso(started + timedelta(minutes=rng.randint(5, 90))),
            "status": "active" if i == 0 else "ended",
            "total_tokens": rng.randint(1000, 50000),
            "cost_usd": round(rng.uniform(0.05, 4.5), 4),
            "message_count": rng.randint(5, 80),
        })

    for i in range(N_EVENTS):
        etype = rng.choice(ETYPES)
        model = rng.choice(MODELS)
        tokens = rng.randint(50, 4000)
        store.ingest({
            "id": f"smoke-evt-{uuid.uuid4().hex}",
            "node_id": NODE, "agent_id": "main",
            "session_id": rng.choice(sids),
            "event_type": etype,
            "ts": _iso(horizon + timedelta(seconds=rng.uniform(0, span))),
            "data": {
                "model": model,
                "tool": rng.choice(TOOLS) if etype.startswith("tool.") else None,
                "preview": f"smoke event #{i}",
            },
            "cost_usd": round(tokens * 3e-6 + rng.uniform(0, 0.01), 6),
            "token_count": tokens, "model": model,
        })

    step = span / N_HB
    for i in range(N_HB):
        store.ingest_heartbeat({
            "node_id": NODE,
            "ts": _iso(horizon + timedelta(seconds=step * i + rng.uniform(-30, 30))),
            "version": "0.12.237", "e2e": True,
            "size_mb": round(rng.uniform(8, 120), 2),
            "events_total": (i + 1) * 5,
        })

    for i in range(N_MEM):
        body = (f"# memory-{i}\n\n" + ("lorem ipsum dolor sit amet " * 50)).encode()
        store.ingest_memory_blob({
            "agent_type": "openclaw", "agent_id": "main",
            "path": f"~/.openclaw/memory/notes_{i:03d}.md",
            "ts": _iso(horizon + timedelta(seconds=rng.uniform(0, span))),
            "blob": body,
            "sha256": hashlib.sha256(body + str(i).encode()).hexdigest(),
            "size_bytes": len(body),
        })

    print(f"[seed] sessions={N_SESS} events={N_EVENTS} hb={N_HB} mem={N_MEM}", flush=True)

    # Flush + drop writer so the daemon (different process) can grab the lock.
    try:
        store._flush_now()  # noqa: SLF001 — fixture tooling
    except Exception:
        pass
    try:
        store.stop(flush=True)
    except TypeError:
        store.stop()
    except Exception:
        pass
    local_store._reset_singleton_for_tests()


if __name__ == "__main__":
    t0 = time.monotonic()
    seed()
    print(f"[seed] done in {time.monotonic() - t0:.1f}s", flush=True)
