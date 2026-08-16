# Needs-you: knowing which agent is waiting on you

ClawMetry shows, above everything else on the Overview page, whether any of
your agents has stopped and is waiting for a human. It answers the question
people actually open the dashboard with.

There are two ways it can know, and the dashboard says which one it used.

| | What you see | How we know |
|---|---|---|
| **Confirmed** | "Waiting for you" (filled dot) | The runtime fired a hook the moment it opened a prompt. Not a guess. |
| **Inferred** | "Maybe waiting" / "Looks like it's waiting" (half dot) | A tool call has been open for 45s with no result and nothing after it. Usually a prompt; occasionally a slow tool. |

Inference works everywhere with no setup. Confirmation needs one line of
config in the runtime, and this document is that line.

Two more states exist and are deliberately distinct from "nothing waiting":

- **"Can't tell right now"** — ClawMetry has not heard from your machine
  recently. An empty list from a detector that is not running must never read
  as all-clear.
- **"This runtime doesn't ask"** — some runtimes have no per-tool approval
  gate at all (Pi is one). There is nothing to detect, so claiming "none
  waiting" would imply we looked.

## Wiring a runtime for confirmed signals

Every runtime posts the same way. Send its own hook payload, unmodified, to:

```
POST http://127.0.0.1:8900/api/hooks/attention?runtime=<runtime>
```

The receiver reads the session id and tool name from whatever the runtime
calls them (`session_id`, `sessionId`, `tool_name`, `toolName`, …), so no
per-runtime translation is needed. Add `&event=resolved` to clear.

It **observes only**: it records and returns immediately, never answers the
prompt, never blocks your agent, and cannot return an error that would make a
runtime hesitate. The response includes `"stored": true|false` so you can
tell a wired hook from a silent one.

### Claude Code — already automatic

Nothing to do. ClawMetry installs a `PermissionRequest` hook itself
(`clawmetry/claude_code_gate.py`) and stamps the badge when it fires. This is
the only runtime confirmed end to end today.

### Qwen Code

`~/.qwen/settings.json` — Qwen ships a Claude-Code-style hook set including
`PermissionRequest`:

```json
{ "hooks": { "PermissionRequest": [ { "hooks": [ { "type": "command",
  "command": "curl -s -X POST -H 'Content-Type: application/json' --data-binary @- 'http://127.0.0.1:8900/api/hooks/attention?runtime=qwen_code'"
} ] } ] } }
```

### Gemini CLI

`~/.gemini/settings.json` — use the `Notification` event, which fires when
the agent requires user attention:

```json
{ "hooks": { "Notification": [ { "hooks": [ { "type": "command",
  "command": "curl -s -X POST -H 'Content-Type: application/json' --data-binary @- 'http://127.0.0.1:8900/api/hooks/attention?runtime=gemini_cli'"
} ] } ] } }
```

### GitHub Copilot

`.github/hooks/*.json` — Copilot fires `PermissionRequest` when the CLI shows
a permission prompt. Note that its hook exit code is meaningful to Copilot;
`curl -s` exiting 0 leaves the normal prompt flow untouched, which is what
you want here.

### Antigravity

Global or workspace hooks JSON, on the before-tool-execution event.

### Codex, Grok Build, DeepSeek Harness, opencode

These cannot take a per-invocation hook. Running them under a config home
that symlinks the real one is the known approach (see
[captain-miao](https://github.com/hyperlogue/captain-miao), which ships it
for all four). ClawMetry does not automate this yet; inference covers them in
the meantime.

### Aider

No hooks, but `--notifications-command` runs when the LLM finishes and is
waiting for you — which is exactly this signal:

```
aider --notifications --notifications-command "curl -s -X POST -H 'Content-Type: application/json' -d '{\"session_id\":\"$AIDER_SESSION\",\"tool_name\":\"\"}' 'http://127.0.0.1:8900/api/hooks/attention?runtime=aider'"
```

### n8n

No hook needed: a paused execution sits in `waiting` status and is readable
from n8n's REST API. Not yet wired.

## Verification status

Be aware of what has actually been proven:

| Runtime | Status |
|---|---|
| Claude Code | Confirmed end to end |
| Everything else | Wiring derived from vendor documentation; **not yet run against a live binary** |

The generic endpoint itself is tested. The per-runtime snippets above are our
current best reading of each runtime's documentation, and any of them may be
wrong in detail. If one does not work, the badge simply falls back to
inference — you lose precision, not the feature. Reports welcome.

## Troubleshooting

**`"stored": false` in the response.** The write did not persist. The usual
cause is a ClawMetry daemon older than this feature: the dashboard cannot
write to DuckDB while a daemon owns the writer lock, so it proxies, and an
older daemon's allowlist has no `set_session_attention`. Upgrade and restart
the daemon.

**Badge never appears, `"stored": true`.** Check the session id matches one
ClawMetry knows. Family runtimes are stored namespaced (`qwen_code:<id>`);
the endpoint adds the prefix if you send a bare id, but only if the id
otherwise matches.

**Badge appears and never clears.** Send `&event=resolved` when the prompt is
answered. Failing that, hook rows age out after two hours, or as soon as the
session ends.

## Tuning

| Variable | Default | Meaning |
|---|---|---|
| `CLAWMETRY_ATTENTION_PENDING_SECONDS` | `45` | How long a tool call must hang before inference calls it waiting. |
| `CLAWMETRY_ATTENTION_RECENT_MINUTES` | `180` | Past this, a session is abandoned rather than waiting. |
| `CLAWMETRY_ATTENTION_HOOK_MAX_AGE` | `7200` | How long a confirmed prompt may stand before being aged out. |
