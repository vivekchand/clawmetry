# ClawMetry Agent CLI

Everything the dashboard shows, readable from a terminal. Built for three
consumers: humans debugging an agent, CI gating on agent health, and AI
agents reading their own telemetry to improve themselves mid-task.

Phase 1 ships the self-improve loop core. Setup/ops commands
(`clawmetry status`, `connect`, `sync`, `proxy`, ...) are listed by
`clawmetry --help` and in [DEVELOPMENT.md](DEVELOPMENT.md); this page covers
the observability reads.

## Commands

| Command | What it answers |
|---|---|
| `clawmetry sessions` | What sessions ran? `sessions <SID> --transcript/--cost/--errors/--lineage/--journey` drills in. |
| `clawmetry activity` | What is the agent doing right now? (`--follow` streams; `--type`, `--session` filter) |
| `clawmetry waste` | Which files did the agent pay to re-read? (the re-read tax) |
| `clawmetry progress` | Is the agent making forward progress or spinning? (+ loop signals) |
| `clawmetry usage` | Tokens and cost. `--by model\|day\|team`, `--efficiency` for the A-F grade. |
| `clawmetry selfevolve` | [pro] Analyze and apply agent improvements. OSS prints the upgrade path (exit 4). |

## Interface contract

- **stdout is data, stderr is decoration.** Row counts, hints, and source
  notes go to stderr so `clawmetry sessions | awk '{print $1}'` just works.
- **`--json`** emits one JSON object: the same rows the local read API
  serves, no envelope.
- **`--follow`** (on `activity`) emits NDJSON: a `{"type":"_meta",...}`
  first line, one event per line, and a final
  `{"type":"_end","reason":...,"next_cursor":...}` so a consumer can resume
  exactly where it stopped. It never hangs: `--idle-timeout` (default 300s),
  `--max-events`, and Ctrl-C all end the stream cleanly with `_end`.
- **Time windows**: `--since`/`--until` take ISO-8601 or relative
  (`90s`, `15m`, `6h`, `7d`); `--last 24h` is sugar for `--since 24h`.
- **Runtime scoping**: `--runtime claude_code` (same ids as the dashboard
  runtime switcher: `openclaw`, `claude_code`, `codex`, `cursor`, ...).

### Exit codes (stable)

| Code | Meaning |
|---|---|
| 0 | Success (including empty results) |
| 1 | Internal error |
| 2 | Usage error |
| 3 | No data source answered (no daemon, no local store); retryable |
| 4 | Entitlement-gated (the CLI's 402; stderr carries the JSON upgrade body) |
| 5 | Auth failure |
| 6 | Not found (unknown session id) |

Errors print a one-line human sentence plus a JSON body on stderr:
`{"error":{"code":"...","message":"...", ...}}`.

## Transport (invisible)

Reads go through the sync daemon's local query server when the daemon is
running (the daemon owns the DuckDB writer lock), and fall back to a direct
read-only DuckDB open on single-process installs. No dashboard process is
required for any read, including `activity --follow`. Every JSON payload
carries a `source` field (`daemon` or `direct`) so consumers know which rung
answered.

## The self-improve loop

An agent finds its own session, checks what it wasted, and verifies the fix:

```bash
# 1. Find myself (newest active session for my runtime)
SID=$(clawmetry sessions --runtime claude_code --active --json \
      | python3 -c "import json,sys; print(json.load(sys.stdin)['sessions'][0]['session_id'])")

# 2. What am I wasting?
clawmetry waste --session "$SID" --json
# → {"top":[{"file_path":"routes/sessions.py","reads":14,"wasted_reads":13}], ...}

# 3. Am I spinning?
clawmetry progress "$SID" --json
# → {"sessions":[{"ratio":48210, ...}], "loop_signals":[...]}

# 4. Act: stop re-reading that file (keep notes), change strategy if looping.
# 5. Verify next turn: wasted_reads flat, ratio down, grade up:
clawmetry usage --efficiency
```

CI health gate example:

```bash
clawmetry progress --since 1h --json | python3 -c "
import json,sys
d = json.load(sys.stdin)
spinning = [s for s in d['sessions'] if s['ratio'] > 100000]
sys.exit(1 if spinning or d['loop_signals'] else 0)"
```

### Drop-in agent instructions

Paste into your project's `AGENTS.md` / `CLAUDE.md` on machines running
ClawMetry:

> This machine runs ClawMetry (agent observability). Before finishing a
> task, run `clawmetry waste --since 6h --json` and
> `clawmetry progress --json`. If a file shows repeated re-reads, stop
> re-reading it and keep notes instead. If forward-progress ratio is high or
> loop signals fire, stop brute-forcing and change approach. Check spend
> with `clawmetry usage --json`. All commands exit 3 when ClawMetry isn't
> running (safe to skip), and are read-only.
