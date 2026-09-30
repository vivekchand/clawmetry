"""Reconcile derived family-runtime usage without changing transcript identity.

Transcript delivery is append-only. Session usage is a changing measurement:
the next $12 lifetime estimate replaces $10, it does not add another $12.
Only the daemon calls this module, using its existing DuckDB writer handle.
"""
from __future__ import annotations

import math


def allocate_usage(rows, session):
    """Prefer timestamped native usage; retain the legacy session fallback."""
    native = [r for r in rows
              if (r.get("data", {}).get("extra") or {}).get("usageBasis") == "per_call"]
    if native:
        for row in rows:
            extra = row.get("data", {}).get("extra") or {}
            # Native usage rows own the cost. Transcript rows must not also
            # receive the session total (including old terminal allocations).
            row["cost_usd"] = extra.get("costUsd", 0.0)
            if extra.get("usageBasis") == "per_call":
                row["model"] = extra.get("model") or None
            else:
                row["token_count"] = 0
        return
    cost = getattr(session, "cost_usd", None)
    if cost is None or not math.isfinite(float(cost)) or float(cost) < 0:
        return
    total = sum(int(r.get("token_count") or 0) for r in rows)
    if total:
        for row in rows:
            row["cost_usd"] = round(float(cost) * row["token_count"] / total, 8)
    elif rows:
        for row in rows:
            row["cost_usd"] = 0.0
        rows[-1]["cost_usd"] = float(cost)
        rows[-1]["token_count"] = int(getattr(session, "total_tokens", 0) or 0)


def reconcile(store, session_id, rows):
    """Replace derived metrics and adjust affected rollups in one transaction.

    The indexed session read is bounded by this session, and only changed
    metric cells are written. Neither transcript data nor any field covered
    by the integrity chain is altered. A failed transaction leaves the old
    metrics and rollups together, and the caller retries before its watermark.
    """
    from clawmetry import local_store as ls

    if store._read_only:
        raise RuntimeError("family usage reconciliation requires the daemon writer")
    if not session_id or ":" not in session_id:
        raise ValueError("family usage requires a namespaced session")
    if any(r.get("session_id") != session_id for r in rows):
        raise ValueError("family usage rows must belong to the selected session")
    if not rows:
        return 0
    wanted = {r["id"]: ls._extract_event_usage(r) for r in rows}
    # Drain queued transcript inserts before reading their existing metrics.
    # _flush_lock serializes this with the background flusher; _write_lock
    # prevents reads from seeing corrected events with stale rollups.
    with store._flush_lock:
        store._flush_now_locked()
        with store._write_lock:
            existing = store._conn.execute(
                "SELECT id, agent_type, session_id, ts, cost_usd, token_count, model, event_type "
                "FROM events WHERE session_id = ?", [session_id],
            ).fetchall()
            # Fetch blobs only for split/model corrections. A normal sync
            # reads a narrow metric projection, never every transcript body.
            split_ids = [row[0] for row in existing
                if (row[0] in wanted and wanted[row[0]]["model"] != row[6])
                or (row[7] == "usage" and row[0] not in wanted and row[5])]
            blobs = {}
            for offset in range(0, len(split_ids), 200):
                ids = split_ids[offset:offset + 200]
                blobs.update(store._conn.execute(
                    "SELECT id, data FROM events WHERE id IN (" +
                    ",".join("?" for _ in ids) + ")", ids).fetchall())
            changes = []
            before, after = [], []
            for eid, atype, sid, ts, cost, tokens, model, event_type in existing:
                desired = wanted.get(eid)
                if desired is None and event_type == "usage":
                    # Native records supersede legacy snapshots. Keep the
                    # immutable row but retire its old derived allocation.
                    desired = {"cost": 0.0, "tokens": 0, "model": model}
                if desired is None:
                    continue
                new = (desired["cost"], desired["tokens"], desired["model"])
                if new == (cost, tokens, model):
                    continue
                if new[0] is not None and (not math.isfinite(float(new[0])) or new[0] < 0):
                    raise ValueError("family usage cost must be finite and non-negative")
                if new[1] is not None and new[1] < 0:
                    raise ValueError("family usage tokens must be non-negative")
                changes.append((eid, *new))
                event = {"agent_type": atype, "session_id": sid, "ts": ts}
                # Splits/data are unchanged; only cost, total tokens and the
                # model attribution differ. Counts cancel for the same model.
                splits = {"tokens_in": 0, "tokens_out": 0, "cache_read": 0, "cache_write": 0}
                retired = event_type == "usage" and desired["tokens"] == 0 and desired["cost"] == 0
                if model != new[2] or retired:
                    decoded = ls._decode_data_blob_rows([(blobs.get(eid),)], ["data"])[0]
                    splits.update(ls._extract_event_usage(dict(decoded, cost_usd=cost,
                        token_count=tokens, model=model, event_type=event_type)))
                before.append((event, dict(splits, cost=cost, tokens=tokens, model=model)))
                after_splits = ({"tokens_in": 0, "tokens_out": 0, "cache_read": 0, "cache_write": 0}
                                if retired else splits)
                after.append((event, dict(after_splits, cost=new[0], tokens=new[1], model=new[2])))
            if not changes:
                ls.invalidate_aggregate_cache()
                return 0
            old_m, old_r = ls._rollup_deltas(before)
            new_m, new_r = ls._rollup_deltas(after)
            for old, new in ((old_m, new_m), (old_r, new_r)):
                for key, vals in old.items():
                    dst = new.setdefault(key, [0] * len(vals))
                    for i, value in enumerate(vals):
                        dst[i] -= value
            with ls._txn(store._conn):
                for offset in range(0, len(changes), 200):
                    chunk = changes[offset:offset + 200]
                    store._conn.execute(
                        "UPDATE events SET cost_usd = CAST(v.cost AS DOUBLE), "
                        "token_count = CAST(v.tokens AS BIGINT), model = v.model "
                        "FROM (VALUES " + ",".join("(?,?,?,?)" for _ in chunk) +
                        ") AS v(id, cost, tokens, model) WHERE events.id = v.id",
                        [value for change in chunk for value in change],
                    )
                store._apply_rollup_deltas_locked(new_m, new_r)
    ls.invalidate_aggregate_cache()
    return len(changes)
