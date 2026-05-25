# The OpenClaw runtime family: OpenClaw vs NanoClaw vs PicoClaw

A short primer for understanding the three OpenClaw-family agent runtimes ClawMetry
observes, and how they differ. Written for someone who knows OpenClaw and wants to
place NanoClaw and PicoClaw next to it. Facts here were verified by reading each
project's source and (for NanoClaw / PicoClaw) by actually installing and running
them; see `tests/fixtures/runtimes/<rt>/REAL/PROVENANCE.md`.

## One line each

- **OpenClaw**: the original "personal AI assistant, any OS, any platform." The
  reference runtime; everything else in the family is a re-imagining of it.
- **NanoClaw**: "OpenClaw, but each agent runs in its own container for security."
  Same messaging-assistant idea, hardened isolation, built on Anthropic's Agents SDK.
- **PicoClaw**: "OpenClaw, but tiny and deployable anywhere." A single Go binary
  small enough to run on a $10 board (Raspberry-Pi-class), with 30+ LLM providers.

## At a glance

| | **OpenClaw** | **NanoClaw** | **PicoClaw** |
| --- | --- | --- | --- |
| Repo | [openclaw/openclaw](https://github.com/openclaw/openclaw) | [nanocoai/nanoclaw](https://github.com/nanocoai/nanoclaw) | [sipeed/picoclaw](https://github.com/sipeed/picoclaw) |
| Site | [openclaw.ai](https://openclaw.ai) | [nanoclaw.dev](https://nanoclaw.dev) | [picoclaw.io](https://picoclaw.io) |
| Stars (2026-05-25) | ~374K | ~29K | ~29K |
| Language | TypeScript | TypeScript | Go |
| License | MIT | MIT | MIT |
| Pitch | Reference assistant | Container isolation | Tiny / runs anywhere |
| Isolation | App-level permission checks | OS-level Docker container per agent | Workspace path restriction |
| Default model | Hosted (Anthropic, etc.) | Hosted Claude via Agents SDK | Pluggable; ships hosted default, local (Ollama) opt-in |
| Best for | Daily driver on a real machine | Security-sensitive / multi-agent | Edge / low-power / cheap hardware |

## How they store a session (the part that matters most)

This is where they genuinely diverge, and it is why ClawMetry needs a separate
reader for each. "Shares the OpenClaw layout" is a myth: only OpenClaw uses the
OpenClaw layout.

### OpenClaw: v3 JSONL, one file per session
```
~/.openclaw/agents/main/sessions/<session_id>.jsonl
```
Each line is a v3 event envelope: `{"type":"message","message":{"role","model",
"usage":{"totalTokens",...,"cost":{"total"}}, "content":[ blocks ]}}`, plus
`session`, `model_change`, `tool_use_result` lines. Tokens and pre-computed cost
are written to disk. Gateway: WebSocket JSON-RPC on port **18789**.

### PicoClaw: flat JSONL, OpenAI-style messages
```
~/.picoclaw/workspace/sessions/<key>.jsonl   (+ <key>.meta.json sidecar)
```
Each line is a flat `providers.Message`: `{"role","content" (a string),
"model_name","created_at","tool_calls":[{"function":{"name","arguments"}}]}`.
No `type`, no `message` wrapper, tool calls are OpenAI-nested, and **no token or
cost field is written to disk**. Crons live in `workspace/cron/jobs.json`
(`schedule.{kind,expr}`). Gateway on port **18790**. Home is `$PICOCLAW_HOME`
(default `~/.picoclaw`).

### NanoClaw: per-session SQLite, two databases
```
<checkout>/data/v2-sessions/<agent_group_id>/<session_id>/
    inbound.db    (host writes, container reads)
    outbound.db   (container writes, host reads)
```
Not JSONL at all. `inbound.db` holds `messages_in`, `outbound.db` holds
`messages_out` + `session_state`. A transcript is the two tables merge-sorted by a
shared `seq` (host writes even, container writes odd). The data dir is relative to
where NanoClaw was launched (its README clones to e.g. `~/nanoclaw-v2` and runs
from there), so there is no `~/.nanoclaw` and no env var. **No model / token / cost
columns**: usage lives in the Agent SDK transcript inside the container, which is
summarized then rotated, so it never lands on the host disk.

## What this means for cost/token visibility

- **OpenClaw**: full token + cost per turn (on disk). ClawMetry shows everything.
- **PicoClaw**: transcripts, model, and tool calls, but tokens/cost are not on
  disk, so ClawMetry honestly reports them as unavailable. (Local Ollama models are
  genuinely $0/token anyway; you pay in hardware + power.)
- **NanoClaw**: transcripts and message counts; model/tokens/cost are not on the
  host, so they show as unavailable until a future reader taps the SDK event log.

## Try it yourself (what we did)

- **PicoClaw** (easiest full run): `brew install go`, clone `sipeed/picoclaw`,
  `make build`, point it at a local Ollama model (`ollama run llama3.2` first), and
  `picoclaw agent -m "..."`. Sessions appear under `~/.picoclaw/workspace/sessions/`.
  `go install` does not work (the module pins a fork via a `replace` directive), so
  build from source.
- **NanoClaw**: clone `nanocoai/nanoclaw`, `npm install && npm run build`, follow
  its README (`./nanoclaw.sh`); it provisions per-session SQLite under
  `data/v2-sessions/`. A full live agent turn needs Docker + an Anthropic key.

## How ClawMetry observes them

ClawMetry ships a dedicated reader adapter per runtime
(`clawmetry/adapters/{openclaw,picoclaw,nanoclaw}.py`) that translates each native
format into one unified session/event shape, so the dashboard treats them
uniformly. When a runtime's data is present on a node, the sync daemon detects it
and the cloud Runtime panel labels the node with its runtime alongside OpenClaw.
See `docs/compatibility.md`, `docs/PRD_PICOCLAW.md`, and `docs/PRD_NANOCLAW.md` for
the support matrix and the per-runtime deep dives.
