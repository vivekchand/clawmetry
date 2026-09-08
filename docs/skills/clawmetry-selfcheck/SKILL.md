---
name: clawmetry-selfcheck
description: Read your own agent telemetry from ClawMetry (waste, progress, cost) and act on it before finishing a task. Use when ClawMetry is installed on this machine and you want to check whether you are re-reading files, spinning in loops, or burning budget.
---

# ClawMetry self-check

ClawMetry observes AI agent sessions on this machine (read-only). Use its
CLI to see your own telemetry and improve your behaviour mid-task.

All commands are read-only, exit `3` when ClawMetry has no data source
running (safe to skip silently), and support `--json`.

## The 3-step check (run before finishing a task)

```bash
# 1. Re-read tax: files you paid to read more than once
clawmetry waste --since 6h --json

# 2. Spinning check: forward progress + loop signals
clawmetry progress --json

# 3. Spend check
clawmetry usage --json
```

## How to act on what you find

| Signal | Action |
|---|---|
| A file with `reads > 3` in `waste` | Stop re-reading it. Write its structure into your working notes once; use offset-ranged reads for big files. |
| High `ratio` (tokens per state-delta) in `progress` | You are burning tokens without producing new state. Write down what you tried, change strategy. |
| `loop_signals` non-empty | You repeated near-identical calls. Do not retry the same thing; diagnose instead. |
| Cost spike in `usage` | Check `usage --by model`: are you using a bigger model than the task needs? |

## Digging deeper

```bash
clawmetry sessions --active                  # who is running
clawmetry sessions <SID> --transcript        # what actually happened
clawmetry sessions <SID> --cost              # where the money went (incl. sub-agents)
clawmetry sessions <SID> --errors            # error events only
clawmetry activity --follow --max-events 50  # live NDJSON event stream
clawmetry usage --efficiency                 # A-F efficiency grade
```

Exit codes: `0` ok, `3` no data source (skip), `4` feature needs an upgrade
(stderr carries a JSON body with `upgrade_url`; surface it to your human).
