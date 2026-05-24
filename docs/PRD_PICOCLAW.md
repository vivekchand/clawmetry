# PRD: PicoClaw Runtime Support

**Status:** Draft / in progress
**Owner:** ClawMetry runtime-compat
**Tracking issue:** #956 (supersedes the "shares OpenClaw layout" assumption in PR #1981)
**Last verified against source:** 2026-05-25

---

## 1. Summary

Make ClawMetry observe **PicoClaw** (`github.com/sipeed/picoclaw`) the way it observes OpenClaw:
zero-config auto-detection plus a real read path for PicoClaw's native session format.
PicoClaw is a tiny single-binary Go runtime (29.1K stars) that runs "anywhere" including
Raspberry-Pi-class hardware. Operators running it are asking whether ClawMetry monitors them.

**The headline correction:** the premise of issue #956 / PR #1981 was that PicoClaw "shares the
OpenClaw on-disk session layout exactly." **That is false.** PicoClaw writes a *different path* and a
*different wire format*. The synthetic fixtures in PR #1981 are relabeled OpenClaw v3 records, so the
"Verified" badge is not earned. This PRD specifies the real adapter required to earn it.

## 2. Problem

ClawMetry's file read path (`dashboard.py:_get_sessions_from_files` / `_scan_session_aggregates`) only
understands OpenClaw's v3 JSONL envelope (`{"type":"message","message":{"usage":{"totalTokens":...}}}`)
under `~/.<runtime>/agents/main/sessions/`. Pointed at a real PicoClaw install it would:

- find **zero** session files (wrong directory), and
- even with the right directory, parse **zero** sessions (wrong wire format -> no `type` field, no
  `message` envelope -> every line skipped), reporting model `unknown` and 0 tokens.

So PicoClaw support is not a "add a candidate path" change. It needs a format-aware adapter.

## 3. Verified findings (source of truth)

Verified 2026-05-25 via the GitHub API and direct source reads of `sipeed/picoclaw` (Go, MIT).

### 3.1 On-disk layout
- **Home:** `$PICOCLAW_HOME` if set, else `~/.picoclaw` (`pkg/config/envkeys.go`, `EnvHome="PICOCLAW_HOME"`).
- **Workspace:** `$PICOCLAW_HOME/workspace` (default `~/.picoclaw/workspace`).
- **Sessions:** `<workspace>/sessions/<key>.jsonl` (append-only) + a `<key>.meta.json` sidecar.
  **NOT** `agents/main/sessions/`. Key sanitization replaces `:` `/` `\` with `_`
  (`pkg/memory/jsonl.go`).
- **Crons:** `<workspace>/cron/jobs.json` (a JSON file, not gateway-RPC). Schedule types are
  `at_seconds` / `every_seconds` / `cron_expr` (distinct from OpenClaw's `expr`).
- **Config:** `$PICOCLAW_HOME/config.json`. Default model in `config.example.json` is `gpt-5.4`
  (hosted); provider is empty by default (user picks). "PicoClaw == local Ollama" is an *assumption*;
  Ollama is opt-in.
- **Gateway/daemon ports:** HTTP gateway **18790**, WebUI launcher **18800** (OpenClaw uses 18789).

### 3.2 Session wire format (`pkg/providers/protocoltypes/types.go` `Message`)
Each `.jsonl` line is a flat `providers.Message`, **not** an OpenClaw envelope:

```jsonc
{
  "role": "assistant",                 // user | assistant | tool | system
  "content": "Working on it.",         // a STRING, not a block array
  "model_name": "ollama/llama3.1:8b",  // "<protocol>/<model>"; or hosted e.g. "gpt-5.4"
  "created_at": "2026-05-12T22:35:31Z",// RFC3339, omitempty
  "tool_calls": [{"id":"call_1","name":"bash","arguments":"{\"command\":\"echo hi\"}"}],
  "tool_call_id": "call_1",            // on tool-result lines
  "reasoning_content": "..."           // optional
}
```

`<key>.meta.json` = `SessionMeta`: `{key, summary, skip, count, created_at, updated_at, scope, aliases}`.

**Critical:** the `Message` struct has **no usage / token / cost field**. On-disk PicoClaw JSONL
carries **no token counts and no cost**. ClawMetry can show PicoClaw transcripts, model, and tool
calls, but **token/cost is unavailable from the session files** (see Open Question Q1).

### 3.3 What this breaks vs OpenClaw (each is a real parser failure)
1. No `type` field -> our `type=="message"` filter skips every line.
2. Flat shape, no `message` sub-object -> `message.usage.totalTokens` / `message.model` absent.
3. `content` is a string, not `[{type:"text"}]` blocks.
4. Model field is `model_name`, not `model` / `modelId`.
5. No `usage`, no `cost` object (OpenClaw writes already-priced `usage.cost.total`; PicoClaw never does).
6. Cost for local models: `providers_pricing.py` has no `ollama`/local entry, so `get_cost()` returns
   0.0 via the default branch (correct value, wrong reason).

## 4. Goals / non-goals

**Goals (this PRD):**
- A `PicoClawAdapter` that reads the native flat-JSONL format into ClawMetry's unified
  `Session`/`Event` shapes (transcripts, model, tool calls).
- Zero-config detection of `~/.picoclaw/workspace/sessions` (respecting `PICOCLAW_HOME`).
- Honest capability + cost surfacing (tokens/cost shown as unavailable, not fabricated).
- Correct-shape fixtures + CI unit tests that fail if the parser regresses.
- A `providers_pricing.py` `ollama`/local-model entry so cost-0 is intentional.

**Non-goals (deferred, tracked below):**
- On-disk token/cost (PicoClaw does not persist it; depends on Q1).
- Live gateway ingest on port 18790.
- PicoClaw cron file ingestion into the Crons tab (phase 2; format known).
- Pi hardware metrics (temp/voltage/throttle) — PicoClaw does not emit them; ClawMetry would read
  host sysfs/`vcgencmd` on the node. Separate roadmap.
- Full DuckDB ingest via the sync daemon + cloud snapshot rendering (phase 3).

## 5. Design

### Phase 1 — Read adapter (this PR)
`clawmetry/adapters/picoclaw.py` — `PicoClawAdapter(AgentAdapter)` (subclass `AgentAdapter` directly;
the format differs from OpenClaw, so it does NOT subclass `OpenClawAdapter`):
- `sessions_dir` from `PICOCLAW_HOME`/`~/.picoclaw` + `workspace/sessions`, overridable for tests.
- `detect()` cheap + never-raises: detected when the sessions dir (or `~/.picoclaw`) exists.
- `list_sessions()` reads each `<key>.jsonl` + `.meta.json`, derives `model` from the last
  `model_name` (provider prefix kept in `extra`, stripped for display), `message_count` from meta
  `count` or line count, timestamps from meta/file mtime. `total_tokens=0`, `cost_usd=None`.
- `list_events()` maps each Message -> unified Event (message / tool_call / tool_result / thinking).
- `capabilities()` = `{SESSIONS, EVENTS}` only (no COST claim).
- Registered in `dashboard.py detect_config()` only when `~/.picoclaw` exists (gated, like the family
  detection pattern) so an absent runtime never clutters the chip bar.

### Phase 2 — Auto-detect + crons
- Add `~/.picoclaw/workspace/sessions` to `detect_config()` SESSIONS_DIR candidates and `~/.picoclaw`
  to `_auto_detect_data_dir()` (both dual copies, kept in sync). Note: precedence keeps OpenClaw/
  clawdbot first; PicoClaw is selected when those are absent.
- `providers_pricing.py`: add explicit `ollama` / local provider -> 0.0 so attribution buckets
  correctly instead of falling through the default branch.
- Cron reader for `workspace/cron/jobs.json` mapping `at_seconds`/`every_seconds`/`cron_expr` to the
  Crons tab shape.

### Phase 3 — Daemon ingest + cloud parity
- Sync daemon discovers `~/.picoclaw/workspace/sessions`, ingests via a PicoClaw-shaped parser into
  DuckDB with `agent_type="openclaw"` (so default UI views show them) and `data._runtime="picoclaw"`
  for labeling. Add a node-level `runtimeInfo.items[]` entry `{"label":"Runtime","value":"PicoClaw"}`
  so the cloud Runtime popup labels it with no cloud code change (the field already renders).

## 6. Open questions (confirm before "Verified")
- **Q1 (highest priority):** does PicoClaw persist per-message usage tokens anywhere on disk (a `usage`
  line, a separate file), or is `UsageInfo` runtime-only? Determines whether token/cost is ever
  showable. Until answered, surface tokens/cost as "not reported by PicoClaw," never 0-as-if-measured.
- **Q2:** confirm sessions are exactly `<workspace>/sessions/<key>.jsonl` across PicoClaw versions
  (some may nest per-agent).
- **Q3:** is `content` always a string, including for tool calls/results, across versions?
- **Q4:** for live data, do we want gateway ingest on 18790? (out of scope now)

## 7. Verification plan
- **Phase 1 (now):** `pytest tests/test_picoclaw_adapter.py -v` against correct-shape fixtures
  (`tests/fixtures/runtimes/picoclaw/workspace/sessions/`): detect, model parse, tool-call events,
  `total_tokens==0`, never-raise on garbage. In CI (see #956 acceptance criterion (e)).
- **Phase 2/3 (needs a real capture):** install PicoClaw, run a session, point ClawMetry with no flags,
  confirm `/api/sessions` shows the PicoClaw session + model and the Runtime popup says "PicoClaw";
  decrypt the live cloud snapshot and confirm the runtime label + transcripts; screenshot the tab.
  Do not stamp "Verified" until a real capture passes a PicoClaw-shaped fixture.

## 8. Risks
- Marketing-credibility: shipping "Verified" on relabeled OpenClaw fixtures (the current README/docs
  state) is exactly the risk #956 set out to retire. The badge is downgraded to honest status until a
  real capture passes.
- Format drift: PicoClaw is young and actively developed; pin the verified commit in fixtures and let
  CI catch divergence.

## Sources
- `github.com/sipeed/picoclaw`: `pkg/providers/protocoltypes/types.go`, `pkg/memory/jsonl.go`,
  `pkg/config/envkeys.go`, `pkg/agent/instance.go`, `docs/architecture/session-system.md`,
  `docs/guides/session-guide.md`, `docs/reference/cron.md`.
- ClawMetry: `dashboard.py` (`_get_sessions_from_files`, `_scan_session_aggregates`,
  `_auto_detect_data_dir`, `detect_config`), `clawmetry/local_store.py`, `clawmetry/providers_pricing.py`,
  `clawmetry/adapters/`.
