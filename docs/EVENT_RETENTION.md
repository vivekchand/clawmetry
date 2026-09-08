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

The tier value is the **ceiling**, not the setting. Values come from
`Entitlement.event_retention_days()`. See `/pricing` on clawmetry.com.

## The operator can shorten it (Security tab)

"How long do you keep my data, and can I change it?" is the first question a
security reviewer asks. The Security tab shows the current window, says what
is setting it, and lets the operator shorten it:

```
GET  /api/security/retention    -> {effective_days, cap_days, configured_days,
                                    env_days, source, tier, explanation}
POST /api/security/retention    <- {"days": 3}    set
POST /api/security/retention    <- {"days": null} back to the plan default
```

The choice is stored on the node (`node_settings.retention_days` in DuckDB),
so the daemon that actually prunes and the dashboard that renders the control
read the same value, and it survives a restart or a reinstall.

**Shrink-only, by construction.** `clawmetry/retention.py::resolve()` takes the
SMALLEST of the tier cap, the operator's setting, and the env var. A setting
above the cap is stored as asked but resolves down to the cap, and the response
returns both numbers so nobody concludes they bought more retention by typing a
bigger one. That is what makes the control safe to expose: the worst a mistake
can do is delete the operator's own data sooner.

A value that is not a positive whole number is rejected rather than clamped —
reading `0` or `-5` as "some default" is how a control ends up keeping MORE
than the operator asked for.

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
| `CLAWMETRY_RETENTION_DAYS` | (unset) | Voluntary tighter limit; never expands past the tier cap. Still honoured for scripted and fleet installs, and reported as `source: "env"`. The Security-tab setting is the same kind of constraint, and whichever is smaller wins. |

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
