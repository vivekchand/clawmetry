# Harness observability audit

Keeps ClawMetry's coverage current as the agent runtimes it monitors evolve. Every
day it syncs each harness's upstream source, asks Claude to compare what the
harness **exposes** (sessions, events, tool calls, cost/tokens, cache, telemetry,
new features) against what our adapter **captures**, and files a GitHub issue for
each gap — so "new things to observe" get picked up instead of silently drifting.

## Pieces
- **`manifest.json`** — single source of truth: each monitored runtime → its
  upstream repo + the ClawMetry adapter that observes it. `repo: null` = no public
  source (audited from on-disk format instead).
- **`sync.sh`** — clones/pulls every harness with a repo into `../harness/<runtime>`
  (override with `HARNESS_DIR`). Idempotent, shallow by default.
- **`audit.py`** — for each runtime, builds the harness's observable surface +
  the adapter source + the `Capability` enum, asks Claude for grounded gaps, and
  files deduplicated issues (`harness-gap`, `runtime:<rt>`, `severity:<s>`).
  Dry-run by default; `--file-issues` to open them. `--runtime <rt>` for one.
- **`.github/workflows/harness-observability-audit.yml`** — runs it daily
  (06:00 UTC) + on demand. Needs `CLAUDE_CODE_OAUTH_TOKEN` (model pass) and
  optionally `CLOUD_REPO_PAT` (to read the closed `clawmetry-pro` adapters).

## Monitored runtimes (12)
Public source synced: **openclaw, nemoclaw, claude_code, codex, goose, aider,
opencode, qwen_code, hermes, nanoclaw, cursor** (cursor = its `agent-trace` format).
Needs a repo URL: **picoclaw** (set `repo` in `manifest.json` when known).

## Add / fix a runtime
Edit `manifest.json` — set `repo` to the verified GitHub URL (HTTP-check it; never
guess), `adapter` to the ClawMetry adapter path, `adapter_repo` to `clawmetry` or
`clawmetry-pro`. The sync + audit pick it up automatically next run.

## Run locally
```bash
scripts/harness/sync.sh                                  # clone/pull all
python3 scripts/harness/audit.py --runtime goose         # dry-run one
CLAUDE_CODE_OAUTH_TOKEN=… python3 scripts/harness/audit.py --file-issues   # all, file issues
```
