---
name: agent-kill-switch
description: Give the human an off switch and a cost meter for the coding agents on this machine, using ClawMetry. Use when the user asks to stop or kill a runaway agent, see what an agent is doing or spending, cap agent spend, gate risky tool calls behind approval, or "set up a kill switch" for Claude Code, Codex, Cursor, Gemini CLI, OpenClaw, Goose, Aider and similar runtimes.
license: MIT
metadata:
  author: vivekchand
  homepage: https://clawmetry.com
  source: https://github.com/vivekchand/clawmetry
---

# Agent kill switch

An agent that loops, re-reads the same files, or shells out to something it
should not is expensive by the minute. This skill wires up
[ClawMetry](https://github.com/vivekchand/clawmetry), a local, read-only
dashboard that reads the session logs the runtimes already write on disk, and
uses it for three things: see what is running, stop one session, and hold
risky tool calls until a human says yes.

Nothing here modifies the agent. Observation is read-only. Every control
below is opt-in and stated as what it does, so tell the user exactly which
ones you enabled.

## 1. Install and start

```bash
pip install clawmetry && clawmetry
```

The dashboard is at `http://localhost:8900`. It auto-detects the runtimes on
the machine (Claude Code, Codex, Cursor, Gemini CLI, OpenClaw, Goose, Aider,
Cline, OpenCode and others); no config. Confirm it is up:

```bash
curl -s http://localhost:8900/api/overview | head -c 400
```

If the port is taken: `clawmetry --port 8901` and use that port below.

## 2. See what is running and what it costs

```bash
curl -s http://localhost:8900/api/sessions      # live and recent sessions, ids look like claude_code:<uuid>
curl -s http://localhost:8900/api/usage         # tokens and cache-aware cost per model and per session
```

Tell the user in plain words: which sessions are active, which one is
spending the most, and whether any is showing loop signs. The dashboard's
Sessions tab shows the full transcript and every tool call for a session.

## 3. Stop one session (the off switch)

```bash
curl -s -X POST http://localhost:8900/api/sessions/<session_id>/stop
```

- `200` with `"ok": true` and a `pid`: the session's process received SIGTERM.
- `409` with `"ok": false`: ClawMetry could not identify a process for that
  session, for example a Cursor editor conversation, which shares the IDE
  process. Say so instead of claiming it was stopped.

Never call this on your own initiative. Only when the user asks to stop a
session, and confirm which session id first.

## 4. Hold risky tool calls until a human approves (Claude Code)

```bash
clawmetry hooks install      # adds a PreToolUse hook to ~/.claude/settings.json, idempotent
clawmetry hooks status
```

Then one policy gates everything ClawMetry scores `high` or `critical`
(recursive deletes, force pushes, sudo, credential files, reverse shells,
cloud metadata endpoints):

```yaml
# ~/.clawmetry/policies.yml
- name: 'Require approval for high-risk actions'
  min_risk: 'high'
  action: 'require_approval'
  timeout: 604800
  on_timeout: 'deny'
```

A deny blocks that one call; the agent keeps its session. Approvals can be
answered from the Approvals tab or, with cloud sync, from a phone push.
Undo with `clawmetry hooks uninstall` (removes only ClawMetry's entries).

## 5. Cap spend for agents that call the API with a key

```bash
clawmetry proxy start --daily-budget 10
export ANTHROPIC_BASE_URL=http://localhost:4100/v1   # or OPENAI_BASE_URL for OpenAI-backed agents
```

When the cap is hit the proxy returns `BUDGET_EXCEEDED` instead of forwarding
the request. It also detects repeated near-identical requests (loops). This
only covers agents whose traffic you route through it; say that.

## Honest limits

- OpenClaw and NemoClaw are free in the open-source app. The other runtimes,
  and the approvals feature, need ClawMetry Cloud or a self-hosted Pro
  license after the trial. Tell the user before enabling those.
- The stop in step 3 is SIGTERM to a process ClawMetry can identify. It is
  not a guarantee for every runtime; the `409` is the honest answer.
- Data stays on the machine unless the user runs `clawmetry connect`, which
  enables end-to-end encrypted cloud sync.

## Remove

```bash
clawmetry hooks uninstall
clawmetry proxy stop
pip uninstall clawmetry
```
