# PRD: NanoClaw Runtime Support

**Status:** Adapter validated against real captured session SQLite
**Owner:** ClawMetry runtime-compat
**Tracking issue:** #956 (supersedes the "shares OpenClaw layout" assumption in PR #1981)
**Last verified:** 2026-05-25 (cloned NanoClaw v2.0.69, provisioned sessions via its own runtime code, captured + validated)

> ## Verified by running its own code
> We cloned NanoClaw v2.0.69, built it, and provisioned real sessions by calling
> NanoClaw's OWN `ensureSchema()` / `insertMessage()` (and the container's
> `writeMessageOut()` SQL), so the captured SQLite is authentic, not hand-rolled.
> The DBs are committed under `tests/fixtures/runtimes/nanoclaw/REAL/` (see
> `PROVENANCE.md`) and the adapter is tested against those exact bytes: it opens
> them read-only + immutable (mtime unchanged after reads), every column it
> SELECTs exists, and it merge-sorts inbound + outbound by `seq`. A full live LLM
> turn needs Docker + Anthropic creds and was not run; the schema + content
> shapes are real regardless.
>
> Running it corrected two assumptions synthetic work had baked in:
> 1. **Data dir is CWD-relative** (`<checkout>/data/v2-sessions`). NanoClaw has
>    NO `~/.nanoclaw`, NO `NANOCLAW_HOME`, and NO `DATA_DIR` env var. The adapter
>    now discovers the dir from common checkout locations plus a ClawMetry-side
>    `CLAWMETRY_NANOCLAW_DIR` override, instead of guessing a home path.
> 2. **Usage is unrecoverable host-side** (confirmed definitively): the SDK
>    transcript that carries tokens lives INSIDE the container and is
>    rotated/deleted; `claude.ts translateEvents()` keeps only the result text +
>    session id. So `model=""` / tokens=0 / no-COST is correct, not a stopgap.

---

## 1. Summary

Make ClawMetry observe **NanoClaw** (`github.com/nanocoai/nanoclaw`) the way it observes OpenClaw.
NanoClaw is a TypeScript runtime (29.4K stars) that runs each agent in an isolated container for
security and runs on Anthropic's Agents SDK. Operators are asking whether ClawMetry covers it.

**The headline correction:** issue #956 / PR #1981 assumed NanoClaw "shares the OpenClaw on-disk
session layout exactly." **That is false.** NanoClaw stores sessions as **per-session SQLite
databases**, not JSONL. There are no `.jsonl` session files for ClawMetry's existing reader to find,
so the "Verified" badge PR #1981 adds is not earned. This PRD specifies the SQLite reader adapter
required to earn it.

## 2. Problem

ClawMetry's read path walks a directory for `*.jsonl` and parses OpenClaw v3 records. Pointed at a real
NanoClaw install it finds **zero** session files and returns an empty list. NanoClaw support therefore
requires a brand-new SQLite-reader adapter, not a path/format tweak.

## 3. Verified findings (source of truth)

Verified 2026-05-25 via the GitHub API and direct reads of `nanocoai/nanoclaw` (`docs/db-session.md`,
`docs/db.md`, `src/db/schema.ts`, `src/session-manager.ts`).

### 3.1 On-disk layout
Per-session folder, two SQLite files (single-writer rule, cross-mount RO visibility):

```
data/v2-sessions/<agent_group_id>/<session_id>/
  inbound.db    # host writes, container reads (read-only mount)
  outbound.db   # container writes, host reads (read-only open)
  .heartbeat    # mtime touched by container
  inbox/<message_id>/   outbox/<message_id>/   # attachments
```

The `<agent_group_id>` parent also holds shared per-group state (`.claude-shared/`,
`agent-runner-src/`). Path helpers: `sessionDir()`, `inboundDbPath()`, `outboundDbPath()`.

### 3.2 Schema (the read contract)
- **`inbound.db` -> `messages_in`** (host-written, even `seq`): `id TEXT PK, seq INTEGER UNIQUE,
  kind TEXT, timestamp TEXT, status TEXT, process_after TEXT, recurrence TEXT (cron), series_id TEXT,
  tries INT, trigger INT, platform_id TEXT, channel_type TEXT, thread_id TEXT, content TEXT (JSON;
  shape depends on kind), source_session_id TEXT, on_wake INT`.
- **`outbound.db` -> `messages_out`** (container-written, odd `seq`): `id TEXT PK, seq INTEGER UNIQUE,
  in_reply_to TEXT, timestamp TEXT, deliver_after TEXT, recurrence TEXT, kind TEXT (chat|chat-sdk|
  system|...), platform_id TEXT, ...`; plus `session_state` (KV), `processing_ack`, and host-side
  `delivered` / `destinations` / `session_routing`.
- **Ordering invariant:** `seq` is unique within a session **across both tables**; host writes even,
  container writes odd. To reconstruct a transcript, read both tables and **merge-sort by `seq`**
  (fallback `timestamp`). Parity is the agent-facing message id (used by edit/react), so it is stable.
- **`content` is JSON whose shape depends on `kind`.** Parse defensively: `json.loads`, extract the
  text/body, fall back to the raw string.

### 3.3 What is NOT in the schema
There are **no documented model / token / cost columns** in the message tables. Usage/cost almost
certainly lives in the Agent SDK's own events, not these DBs (see Open Question Q1). So a first-cut
adapter surfaces **transcripts + message counts + timestamps**, with **model unknown and tokens/cost
0/unknown** — and says so honestly.

### 3.4 Other facts
- Runtime: hosted Claude via the Anthropic Agents SDK (pluggable: `/add-codex`, `/add-opencode`,
  `/add-ollama-provider`). Config is conversational (`/customize`) — there is no session config file to
  parse.
- A `.claude/skills/migrate-from-openclaw/` exists, confirming NanoClaw deliberately departs from the
  OpenClaw layout rather than inheriting it.

## 4. Goals / non-goals

**Goals (this PRD):**
- A `NanoClawAdapter` that opens the per-session `inbound.db`/`outbound.db` **read-only** and returns
  unified `Session`/`Event` objects (merged transcript, message counts, timestamps).
- Detection of `~/.nanoclaw/data/v2-sessions` (data-dir location to confirm — Q2).
- Honest capabilities (`{SESSIONS, EVENTS}`), model unknown, tokens/cost not fabricated.
- SQLite fixtures + CI unit tests built from the verified schema.

**Non-goals (deferred):**
- Model / token / cost (not in the message tables; depends on Q1 — likely an Agent-SDK-events reader).
- Sub-agent / agent-to-agent graph (NanoClaw routes via `source_session_id` + `destinations`; phase 2).
- Cron/recurring tasks (the `recurrence` column exists; phase 2).
- DuckDB ingest + cloud snapshot rendering (phase 3).
- Container introspection / live heartbeat off `.heartbeat` mtime (phase 2).

## 5. Design

### Phase 1 — Read adapter (this PR)
`clawmetry/adapters/nanoclaw.py` — `NanoClawAdapter(AgentAdapter)`:
- `data_dir` default `~/.nanoclaw/data/v2-sessions`, overridable for tests.
- **Read-only opens only:** `sqlite3.connect("file:{path}?mode=ro&immutable=1", uri=True)`, always
  closed, everything wrapped in try/except. We must never lock or mutate the runtime's DBs (the
  runtime enforces a single-writer rule; ClawMetry is read-only by charter).
- `detect()` cheap + never-raises: detected when `data_dir` has at least one
  `<group>/<session>/inbound.db`; `session_count` = folder count (no DB opens).
- `list_sessions()`: one Session per folder. `message_count` = COUNT across both tables,
  `started_at`/`ended_at` = min/max `timestamp`, `model=""`, `total_tokens=0`, `cost_usd=None`.
- `list_events()`: open both DBs RO, select rows, merge-sort by `seq` then `timestamp`, map to unified
  Events (inbound chat -> role user, outbound chat/chat-sdk -> role assistant, system kinds -> system),
  parsing `content` JSON for text; `parent_id` = `in_reply_to`.
- `capabilities()` = `{SESSIONS, EVENTS}` only.
- Registered in `dashboard.py detect_config()` only when `~/.nanoclaw` exists.

### Phase 2 — Routing graph + crons + liveness
- Build the agent-to-agent / sub-agent relationships from `source_session_id` + `destinations`.
- Surface `recurrence` rows as crons.
- Use `.heartbeat` mtime for a live/idle indicator.

### Phase 3 — Usage + daemon ingest + cloud parity
- Resolve Q1 (usage source); add a reader for whatever records model/tokens (likely Agent-SDK events).
- Sync daemon ingests into DuckDB with `agent_type="openclaw"` + `data._runtime="nanoclaw"`, and a
  node-level `runtimeInfo.items[]` entry `{"label":"Runtime","value":"NanoClaw"}` so the cloud Runtime
  popup labels it with no cloud-side code change.

## 6. Open questions
- **Q1 (RESOLVED):** model/token/cost are NOT on the host disk. The SDK transcript that carries usage
  lives inside the container and is rotated/deleted; the host-visible message tables have no such
  columns. Surfaced as unavailable, never fabricated.
- **Q2 (RESOLVED):** `data/` is CWD-relative (`path.resolve(process.cwd(),'data')/v2-sessions`); there
  is no `~/.nanoclaw`, no `NANOCLAW_HOME`, no `DATA_DIR` override. Detection now scans common checkout
  locations + `CLAWMETRY_NANOCLAW_DIR`. Remaining: how reliably can we locate an arbitrary checkout
  dir zero-config? (The override + CWD covers the documented `./nanoclaw.sh`-from-checkout flow.)
- **Q3 (partly resolved):** real `content` shapes seen: `{"text":...}`, `{"text":...,"files":[...]}`,
  `{"operation":"edit",...,"text":...}`, `{"operation":"reaction","emoji":...}` (no text -> summarised).
  Enumerate any remaining kinds (card, question, agent-to-agent) from a richer real capture.
- **Q4 (RESOLVED):** durable session DBs live host-side under `data/v2-sessions/`; ClawMetry never
  enters a container.

## 7. Verification plan
- **Phase 1 (now):** `pytest tests/test_nanoclaw_adapter.py -v` against SQLite fixtures generated by
  `tests/fixtures/runtimes/nanoclaw/_make_sqlite_fixtures.py` (real schema): detect + session_count,
  merged inbound+outbound transcript in `seq` order with correct roles + `parent_id`, `model==""`,
  `total_tokens==0`, never-raise on a corrupt/missing DB. Read-only-open assertion (no writer lock).
  In CI (#956 criterion (e)).
- **Phase 3 (needs a real capture):** install NanoClaw, run a session, point ClawMetry with no flags,
  confirm the session + transcript render and the Runtime popup says "NanoClaw"; decrypt the live cloud
  snapshot; screenshot the tab. Do not stamp "Verified" until a real capture passes a NanoClaw SQLite
  fixture.

## 8. Risks
- Marketing-credibility: the current README/docs "Verified" badge for NanoClaw is unearned (no real
  NanoClaw data path exists yet). Downgraded to honest status until a real capture passes.
- Read-only safety: opening the runtime's SQLite files incorrectly (RW, or without `immutable=1`) could
  contend with the single-writer rule. The adapter MUST open RO/immutable and close promptly.
- Schema drift: NanoClaw is young; pin the verified commit in the fixture generator and let CI catch
  divergence.

## Sources
- `github.com/nanocoai/nanoclaw`: `docs/db-session.md`, `docs/db.md`, `src/db/schema.ts`,
  `src/session-manager.ts`, `src/db/session-db.ts`.
- ClawMetry: `clawmetry/adapters/` (base + claude_code precedent), `dashboard.py` detection,
  `clawmetry/local_store.py`, `clawmetry/sync.py`.
