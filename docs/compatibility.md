# Runtime / Agent Compatibility

ClawMetry observes many AI-agent runtimes, not just OpenClaw. Each runtime that
isn't OpenClaw ships a dedicated reader adapter (`clawmetry/adapters/`) that
translates its native session format into ClawMetry's unified Session/Event
shapes; the daemon then ingests them into the same local DuckDB store and cloud
snapshot, tagged with the runtime. When more than one runtime is present on a
node, the Session replay tab shows a **runtime switcher** (All / per runtime).
This page tracks each one's real status, honestly.

> New to NanoClaw / PicoClaw? See [`RUNTIME_FAMILY.md`](RUNTIME_FAMILY.md) for a
> primer on the OpenClaw-family runtimes specifically.

| Runtime / Agent | Status         | Session store                          | Notes |
| --------------- | -------------- | -------------------------------------- | ----- |
| OpenClaw    | Native         | v3 JSONL `~/.openclaw/agents/main/sessions/` | Reference runtime; auto-detected. |
| PicoClaw    | Beta adapter   | Flat `providers.Message` JSONL `~/.picoclaw/workspace/sessions/` | Transcripts, model, tool calls. Tokens/cost not on disk. |
| NanoClaw    | Beta adapter   | Per-session SQLite `data/v2-sessions/<group>/<session>/{inbound,outbound}.db` | Transcripts. Model/tokens/cost not on disk. |
| Hermes      | Beta adapter   | SQLite `~/.hermes/state.db` (sessions + messages) | Transcripts, model, pre-computed tokens/cost. |
| Claude Code | Beta adapter   | JSONL `~/.claude/projects/<cwd>/<id>.jsonl` (v-type lines) | Transcripts, model, tool calls + thinking, token usage. |
| Codex       | Beta adapter   | "rollout" JSONL `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` | Transcripts, model, tool calls, token usage (from `token_count` events). |
| Cursor      | Beta adapter   | SQLite `state.vscdb` (`cursorDiskKV` / `ItemTable`, global + per-workspace) | Chat/composer transcripts, model. No billed cost on disk (server-side). |
| Aider       | Beta adapter   | Markdown `.aider.chat.history.md` per project dir (+ `.aider.input.history`) | Transcripts, model, token counts. Per-project history (set `AIDER_HISTORY_DIRS`). |
| Goose       | Beta adapter   | SQLite `~/.local/share/goose/sessions/sessions.db` (`sessions` + `messages`) | Transcripts, model, tool calls, real token totals. |
| ZeroClaw / TrustClaw / Nanobot | Not yet | unverified | Open an issue with a real session capture. |

## What "Beta adapter" means (and what it does not)

A **Beta adapter** means ClawMetry ships a reader for that runtime's *real*
on-disk format, validated against a session captured from a **real install** of
that runtime (we installed and ran both, see
`tests/fixtures/runtimes/<runtime>/REAL/PROVENANCE.md`), with fixture-backed CI
tests that fail if the parse path regresses. It is **not** the same as the
earlier "Verified" claim, which was withdrawn: that had been based on fixtures
that were actually OpenClaw v3 records relabeled, and so proved only that
ClawMetry parses OpenClaw's shape. Running the real runtimes caught real bugs
the relabeled fixtures could never have (PicoClaw's nested tool-call shape and
Go's trailing-zero timestamps; NanoClaw's CWD-relative data dir).

PicoClaw and NanoClaw do **not** share OpenClaw's layout (verified 2026-05-25
against the real sources):

- **PicoClaw** (`github.com/sipeed/picoclaw`, Go) writes a flat
  `providers.Message` per JSONL line (fields `role`, `content` as a string,
  `model_name`, `created_at`, `tool_calls`, ...), under
  `$PICOCLAW_HOME/workspace/sessions/<key>.jsonl` with a `<key>.meta.json`
  sidecar. There is **no token/cost field on disk**, so ClawMetry shows
  transcripts, model, and tool calls but reports tokens/cost as unavailable.
  See [`PRD_PICOCLAW.md`](PRD_PICOCLAW.md).
- **NanoClaw** (`github.com/nanocoai/nanoclaw`, TypeScript) stores each session
  as a pair of SQLite files (`inbound.db` / `outbound.db`) under
  `data/v2-sessions/<agent_group_id>/<session_id>/`. The message tables carry
  **no model/token/cost columns**, so ClawMetry shows transcripts and message
  counts but reports model/tokens/cost as unavailable. See
  [`PRD_NANOCLAW.md`](PRD_NANOCLAW.md).

A "Verified" badge will be restored per runtime only after a session captured
from a **real install** of that runtime passes its adapter test, and the live
end-to-end path (dashboard + cloud snapshot) is confirmed.

### Cloud runtime label (live-verified)

The sync daemon detects PicoClaw / NanoClaw installs (via each adapter's
`detect()`) and ships a runtime label in the encrypted snapshot, both as
`runtimeInfo.items[]` rows and a small top-level `detectedRuntimes` summary
(`{name, displayName, sessionCount, workspace}`). The cloud Runtime panel
renders these alongside OpenClaw with no cloud code change. This was verified by
decrypting the live cloud snapshot of a real node, which showed
`PicoClaw: detected (1 session)` and `NanoClaw: detected (2 sessions)`. Pure
detection only: no DuckDB access and no writer lock are involved.

## Pointing ClawMetry at PicoClaw or NanoClaw

When a runtime's home directory exists, its adapter registers automatically and
appears in the multi-agent view:

```bash
# PicoClaw: adapter auto-registers when ~/.picoclaw exists (or PICOCLAW_HOME set)
export PICOCLAW_HOME=~/.picoclaw      # only if you use a non-default home
clawmetry

# NanoClaw: adapter auto-registers when ~/.nanoclaw exists (or NANOCLAW_HOME set).
# NanoClaw resolves its data dir relative to where it was launched
# (process.cwd()/data), so if your install keeps data elsewhere, point at it:
export NANOCLAW_HOME=/path/to/nanoclaw   # expects <NANOCLAW_HOME>/data/v2-sessions
clawmetry
```

These adapters read their runtime's files strictly read-only (NanoClaw's SQLite
is opened `mode=ro&immutable=1`), consistent with ClawMetry's read-only charter.

## Adding a new runtime

1. Capture a **real** session from the runtime and confirm its on-disk format
   (path, file type, wire shape). Do not assume it matches OpenClaw.
2. If it writes OpenClaw v3 JSONL under `agents/main/sessions/`, it works
   already; add a fixture + a row here.
3. If it uses its own format, add a reader adapter under `clawmetry/adapters/`
   (subclass `AgentAdapter`, translate the native format into the unified
   `Session`/`Event` shapes), with fixture-backed tests, and register it in
   `dashboard.py` gated on the runtime's home directory.
4. Be honest in `capabilities()` and in this matrix: only advertise what the
   on-disk data actually supports.

## What "shared OpenClaw layout" means

A runtime works with zero adapter code only if it writes session files matching
all of:

- One JSONL per session, named `<session_id>.jsonl`
- Located under `<root>/agents/<agent_id>/sessions/`
- First line is a `{"type": "session", "version": 3, ...}` record
- Assistant turns carry `message.usage.totalTokens` and (optionally)
  `message.usage.cost.total`
- Model identity via `model_change` events and/or `message.model`

Runtimes that diverge from this (PicoClaw's flat JSONL, NanoClaw's SQLite) need
the dedicated adapter described above.
