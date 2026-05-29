# Per-tier event retention

The DuckDB `events` table grows linearly with agent activity. ClawMetry
caps it two ways:

1. **Size-based** (`LocalStore.vacuum`): deletes oldest events when the
   on-disk file exceeds `LOCAL_MAX_BYTES`. Always on. Already shipped.
2. **Age-based** (`LocalStore.prune_events_by_age`): deletes events
   inserted longer ago than the install's tier allows. New in this PR.

Both run; whichever is stricter wins.

## Tier limits

| Tier | Retention |
|---|---|
| Free / OSS | 7 days |
| Starter / Trial | 30 days |
| Pro / Self-hosted Pro | 90 days |
| Enterprise | Unlimited (no prune) |

Values come from `Entitlement.event_retention_days()`. See
`/pricing` on clawmetry.com.

## How the daemon enforces it

A background thread in `clawmetry/sync.py` (`retention-prune`) wakes every
hour, reads the entitlement, and calls
`LocalStore.prune_events_by_age(days)`:

```python
days = get_entitlement().event_retention_days()
if days:
    store.prune_events_by_age(days)
```

The thread is automatic. No config needed. Initial run waits 90s after
daemon start so the backfill thread finishes before pruning.

## Tuning

| Env var | Default | Description |
|---|---|---|
| `CLAWMETRY_RETENTION_INTERVAL_HOURS` | 1 | Tick cadence |
| `CLAWMETRY_RETENTION_DAYS` | (unset) | Voluntary tighter limit; never expands past the tier cap |

Setting `CLAWMETRY_RETENTION_DAYS=3` on a Free install caps at 3 days
(stricter than the 7-day tier limit). Setting it to 30 on the same Free
install still caps at 7 because the tier wins.

## What gets pruned

Only the `events` table. Sessions, channels, crons, memory, heartbeats,
audit chain, and the integrity chain are not touched. The audit chain in
particular is required to stay intact; if a customer needs longer retention
for compliance, that's an Enterprise tier conversation.

## Time math

`prune_events_by_age` uses the `created_at` BIGINT column (millis-since-
epoch at ingest time), not the `ts` VARCHAR (ISO event timestamp). This
means a backfilled JSONL imported today won't disappear tomorrow even if
its event `ts` is 6 months old; it ages out N days after import.
That's intentional. Surprising users with "I just installed and my
events are gone" would be a worse outcome than a one-time post-backfill
delay.

## Verifying

Tail the daemon log; the prune logs only when it actually deleted rows:

```
2026-05-29 14:00:00 INFO retention prune: deleted 1240 events older
  than 7 days (before=8432 after=7192)
```

For a manual run from a shell:

```python
from clawmetry import local_store as ls
from clawmetry import entitlements as ent
days = ent.get_entitlement().event_retention_days()
print(ls.get_store().prune_events_by_age(days))
# {'deleted_rows': 1240, 'before_rows': 8432, 'after_rows': 7192, 'cutoff_ts': ...}
```
