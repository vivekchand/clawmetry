# Agent Observability - How ClawMetry Sees Inside Your Agent

> Full visibility into channel routing, LLM context construction, skill invocation, tool execution, and sub-agent orchestration.

## Overview

ClawMetry gives you X-ray vision into what your AI agent is actually doing. Not just "what happened" but "why it happened" - which channel a message came from, what context the LLM received, which skills were invoked, how tools executed, and what sub-agents did.

```
What you see today          What ClawMetry shows you
without observability       with agent observability
                           
"The agent replied"    -->  Message from Telegram group "AI Chat"
                            --> routed to session agent:main:telegram:group:-100123
                            --> context built: 82K tokens
                                (system prompt 12K + history 43K + tools 27K)
                            --> LLM call #1: claude-opus-4-6 (2.3s)
                            --> tool: exec("git status") (0.3s)
                            --> tool: read("deploy.sh") (0.1s)  
                            --> LLM call #2: claude-opus-4-6 (2.8s)
                            --> response: "Deployed successfully" (5.6s total)
                            --> skill used: healthcheck
                            --> cost: $0.12
```

## Architecture - What ClawMetry Observes

ClawMetry maps directly to OpenClaw's 3-layer architecture:

```
                         LAYER 1: CONNECTORS
  +-----------+  +-----------+  +-----------+  +-----------+
  | Telegram  |  | WhatsApp  |  |  Discord  |  |  <plugin> |
  |  3 groups |  |  1 chat   |  | 2 channels|  |           |
  |  1 DM     |  |           |  |           |  |           |
  +-----+-----+  +-----+-----+  +-----+-----+  +-----+-----+
        |              |              |              |
        v              v              v              v
  +------------------------------------------------------------------+
  |                  LAYER 2: GATEWAY CONTROLLER                      |
  |                                                                    |
  |  +--------+ +--------+ +--------+ +--------+ +--------+          |
  |  | Main   | |  TG:   | |  TG:   | |  WA:   | |  DC:   |  ...    |
  |  |Session | | group1 | | group2 | | chat1  | | chan1  |          |
  |  +--------+ +--------+ +--------+ +--------+ +--------+          |
  |       Sessions (each with own JSONL transcript)                    |
  |                                                                    |
  |  +-------------+  +------------------+  +---------------+         |
  |  | Cron Manager|  |Memory Management |  |  Session DB   |         |
  |  +-------------+  +------------------+  +---------------+         |
  +------------------------------------------------------------------+
        |
        v
  +------------------------------------------------------------------+
  |                  LAYER 3: AGENT RUNTIME                           |
  |                                                                    |
  |  Environment        Providers         Tools          Skills       |
  |  +-----------+    +------------+    +---------+    +---------+    |
  |  |Claude Code|    |claude-opus |<-- |web_search|   |weather  |    |
  |  |GCP        |    |  (primary) |    |read_file |   |gh-issues|    |
  |  |exe.dev    |    |gpt-5.4    |    |exec      |   |tmux     |    |
  |  |+ anything |    | (fallback)|    |<plugin>  |   |<plugin> |    |
  |  +-----------+    +------------+    +---------+    +---------+    |
  +------------------------------------------------------------------+
```

ClawMetry observes all three layers:
- **Layer 1**: Which connector delivered each message, per-channel session routing
- **Layer 2**: Session lifecycle, cron execution, memory state
- **Layer 3**: LLM calls (model, tokens, cost), tool execution, skill invocation, sub-agents


## Channel Session Routing

Every message is routed to a specific session based on its channel and chat context.

### Session Key Format

```
agent:<agentId>:<channel>:<chatType>:<chatId>

Examples:
  agent:main:main                              --> CLI / main session
  agent:main:telegram:direct:1532693273        --> Telegram DM with user 1532693273
  agent:main:telegram:group:-1001234567890     --> Telegram group
  agent:main:whatsapp:group:120363...@g.us     --> WhatsApp group
  agent:main:discord:channel:222222222222      --> Discord channel
  agent:main:cron:b8714377-...:run:540a9b9b    --> Cron job run
```

### How ClawMetry Shows This

In the **Brain tab**, every event shows which channel it came from:

```
18:12:50  USER   main   [Telegram]   [cron:health-check] Run a health check...
18:04:50  USER   main   [WhatsApp]   Hey can you check the deployment?
17:30:58  EXEC   main   [CLI]        git status
```

**Channel filter chips** let you isolate one channel:

```
[All channels] [Telegram (264)] [CLI (43)] [Cron (12)]
```

### Data Flow

```
sessions.json (on disk)          ClawMetry Brain API            Browser
+-------------------------+      +---------------------+      +----------------+
| "agent:main:telegram:   |      | Parse session key   |      | Channel badge  |
|   group:-100123": {     | ---> | Extract "telegram"  | ---> | [Telegram]     |
|   "sessionId": "02a2.." |      | Match to event src  |      | Filter chips   |
|   "chatType": "group"   |      | Enrich all events   |      |                |
| }                       |      +---------------------+      +----------------+
+-------------------------+
```


## LLM Context Construction

Every turn, OpenClaw assembles a context from multiple layers before calling the LLM.

### System Prompt Structure

```
+------------------------------------------------------------------+
|                     SYSTEM PROMPT                                  |
|                                                                    |
|  ## Tooling                                          ~3,000 tokens |
|    Tool list + descriptions + runtime guidance                     |
|                                                                    |
|  ## Safety                                             ~120 tokens |
|    No self-preservation, no power-seeking                          |
|                                                                    |
|  ## Skills                                      ~1,500 tokens (N)  |
|    Compact headers of all installed skills                         |
|    (always loaded - tells agent WHEN to use each skill)            |
|                                                                    |
|  ## Memories                                           ~200 tokens |
|    Guidance for memory_search and memory_get tools                 |
|                                                                    |
|  ## Workspace                                          ~150 tokens |
|    Working directory path + docs location                          |
|                                                                    |
|  ## Heartbeats                                          ~80 tokens |
|    Heartbeat prompt when enabled                                   |
|                                                                    |
|  ## Sandbox Information                                ~200 tokens |
|    Current date, timezone, host info                               |
+------------------------------------------------------------------+
|                   BOOTSTRAP FILES (injected)                       |
|                                                                    |
|  SOUL.md          ~750 tokens   Agent identity + personality       |
|  AGENTS.md        ~500 tokens   Workspace configuration            |
|  TOOLS.md         ~400 tokens   Custom tool instructions           |
|  USER.md          ~200 tokens   About the human operator           |
|  IDENTITY.md      ~200 tokens   Name, role                         |
|  MEMORY.md      ~1,000 tokens   Persistent agent memory            |
|  HEARTBEAT.md     ~200 tokens   Status tracking                    |
+------------------------------------------------------------------+
|                   TOOL SCHEMAS (JSON, invisible)                    |
|                                                                    |
|  Built-in tools (read, exec, browser...)          ~7,000 tokens    |
|  Plugin tools                                     varies           |
|  (counted in context window even though not visible as text)       |
+------------------------------------------------------------------+
|                   CONVERSATION HISTORY                              |
|                                                                    |
|  Compacted summary (older turns)                  varies           |
|  Recent messages (last N turns)                   varies           |
|  Tool call results                                varies           |
+------------------------------------------------------------------+
```

### Context Window Management

```
Context tokens
     ^
     |
200K |.................................................. context window
     |
160K |-----.------------------------------------------- compaction threshold
     |      \
     |       \  compaction event
     |        \  (summarize old turns)
     |         \
 80K |          '--------.
     |                    \
     |                     '---------.
 40K |                                \
     |                                 '----.
     |                                       \
   0 +-----|-----|-----|-----|-----|-----|------> turns
     1     5    10    15    20    25    30
```

When context exceeds ~80% of the window, OpenClaw auto-compacts:
1. Older turns are summarized into a compact entry
2. Recent messages are kept intact
3. Tool call/result pairs are preserved together
4. Summary saved in the session transcript

### How ClawMetry Shows This

The **Context tab** shows:

```
Context Window Usage
[================================----------] 82,000 / 200,000 (41%)
                                        ^ compaction at ~160K

Context Composition
  ## Tooling          [========--------]   3.0K tokens
  ## Safety           [==--------------]   120 tokens
  ## Skills           [=====-----------]   1.5K tokens (12 headers)
  Bootstrap: SOUL.md  [=====-----------]   750 tokens
  Bootstrap: MEMORY.md[========--------]   1.0K tokens
  Tool schemas (JSON) [==========-----]   7.0K tokens
  Conversation hist.  [===============]  38.5K tokens
```


## Skill Invocation

Skills are the primary way to customize agent behavior. They have 3 fidelity levels:

```
your-skill-name/
  SKILL.md              <-- Header: always in system context (~3-4 lines)
  |                         Body: fetched on-demand (rest of file)
  |
  +-- scripts/          <-- Linked Files: fetched when acting
  |     process_data.py
  |     validate.sh
  |
  +-- references/       <-- Documentation for the skill
  |     api-guide.md
  |
  +-- assets/           <-- Templates, configs, etc.
        report-template.md

Fidelity levels:
  1. Header  --> always loaded (tells agent WHEN to use)     ~50 tokens
  2. Body    --> loaded on-demand (tells WHAT and HOW)       ~500 tokens  
  3. Linked  --> loaded when acting (auxiliary files)         varies
```

### How ClawMetry Shows This

**Brain tab** - skill badges on events:

```
18:12:50  EXEC   main  [Telegram]  [healthcheck]  python3 healthcheck.py
18:04:50  READ   main  [CLI]       [gh-issues]    ~/.openclaw/skills/gh-issues/SKILL.md
```

**Skills tab** - file browser (click any skill to explore):

```
+------------------+------------------------------------------+
| EXPLORER         | SKILL.md                                 |
|                  |                                           |
| > healthcheck    | # Healthcheck                            |
|   SKILL.md       |                                           |
|   scripts/       | Run health checks on ClawMetry Cloud     |
|     check.py     | production endpoints and alert via        |
| > gh-issues      | Telegram if any fail.                    |
|   SKILL.md       |                                           |
| > weather        | ## When to use                           |
|   SKILL.md       | User asks for a health check, or this    |
|   scripts/       | is triggered by a cron job.              |
|     fetch.sh     |                                           |
+------------------+------------------------------------------+
```

**Skills fidelity stats:**

```
Skill         Status    Header    Body fetches (7d)   Last used
healthcheck   healthy   52 tok    8 times             2h ago
gh-issues     healthy   48 tok    3 times             1d ago
weather       unused    35 tok    0 times             --
old-plugin    dead      120 tok   0 times             never (30d+)
```


## Agent Runtime Timeline

Every user message triggers a multi-step execution sequence. ClawMetry shows the full trace.

### Single Turn Execution

```
Time        Step          Detail                              Duration
--------    ----------    ---------------------------------   --------
18:12:50    USER          "deploy to prod"                    
18:12:50    CONTEXT       Built 82K tokens                    0.05s
18:12:50    LLM #1        claude-opus-4-6 (streaming)         2.3s
18:12:52    EXEC          git status                          0.3s
18:12:52    READ          deploy.sh                           0.1s
18:12:53    LLM #2        claude-opus-4-6 (streaming)         2.8s
18:12:55    AGENT         "Deployed successfully to prod"     
                                                              ------
                          Total: 82K in / 2.1K out            5.6s
                          Cost: $0.12
```

### How ClawMetry Shows This

Click any **USER** event in the Brain tab to expand the turn:

```
18:12:50  USER  main  [Telegram]  "deploy to prod"
  [5 steps] [2 LLM] [2 tools] [5.6s]              <-- summary badges
  |
  +-- 18:12:52  EXEC   git status                  <-- expandable timeline
  +-- 18:12:52  READ   deploy.sh
  +-- 18:12:53  THINK  Checking deployment config...
  +-- 18:12:55  AGENT  Deployed successfully to prod
```


## Sub-Agent (ACP) Visibility

When the agent spawns sub-agents (via ACP - Agent Communication Protocol), each sub-agent gets its own session with full transcript visibility.

### What ClawMetry Can See

```
Parent session (agent:main:main)
  |
  |-- USER: "fix the failing test"
  |-- THINK: "I'll spawn a sub-agent for this"
  |-- SPAWN: sub-agent a5e2943d
  |     |
  |     |   Sub-agent session (agent:main:subagent:a5e2943d)
  |     |   +-- READ   tests/test_auth.py
  |     |   +-- THINK  "The assertion on line 47 is wrong"
  |     |   +-- WRITE  auth.py (line 47)
  |     |   +-- EXEC   pytest tests/test_auth.py
  |     |   +-- AGENT  "Fixed assertion error, all tests pass"
  |     |
  |-- AGENT: "Test fixed, all 47 tests passing now"
```

### Visibility Boundaries

```
+-------------------------------+----------------------------+
| Full visibility               | Black box (I/O only)       |
+-------------------------------+----------------------------+
| OpenClaw sub-agents           | Claude Code (ACP tool)     |
|   - own JSONL transcript      |   - see tool_call input    |
|   - all tool calls visible    |   - see tool_result output |
|   - token tracking            |   - internal LLM calls     |
|   - parent session link       |     are not visible        |
|                               |                            |
| Cron job sessions             | exe.dev                    |
|   - own session per run       |   - see invocation + result|
|   - full execution trace      |                            |
+-------------------------------+----------------------------+
```

### How ClawMetry Shows This

Sub-agent events appear as **nested groups** in the runtime timeline:

```
18:12:50  USER  main  "fix the failing test"
  [8 steps] [2 LLM] [3 tools] [1 sub-agent] [12s]
  |
  +-- 18:12:52  THINK  Analyzing the test failure...
  |
  +-- Sub-agent: a5e2943d (4 steps)                 <-- nested group
  |   +-- 18:12:53  READ   tests/test_auth.py
  |   +-- 18:12:53  WRITE  auth.py
  |   +-- 18:12:54  EXEC   pytest tests/
  |   +-- 18:12:56  AGENT  Fixed assertion error
  |
  +-- 18:12:57  AGENT  Test fixed, all passing
```


## Multi-LLM Provider Stack

OpenClaw supports multiple LLM providers with automatic fallback.

```
Agent Runtime
+------------------------------------------+
|  Providers                                |
|                                           |
|  [*] claude-opus-4-6    <-- primary       |
|      Auth: OAuth                          |
|                                           |
|  [ ] gpt-5.4            <-- fallback 1   |
|                                           |
|  [ ] claude-sonnet-4-6  <-- fallback 2   |
|                                           |
+------------------------------------------+

When primary is rate-limited or errors:
  primary (rate limited) --> fallback 1 --> fallback 2
```

### How ClawMetry Shows This

The **Flow tab** Brain node shows the active provider with a green dot:

```
+-------------------------+
|    Agent Runtime        |
|                         |
|  (*) claude-opus-4-6   |  <-- green dot = active
|      gpt-5.4           |  <-- gray = standby
|      claude-sonnet-4-6 |  <-- gray = standby
|                         |
|  Auth: OAuth            |
+-------------------------+
```


## Cloud Sync Pipeline

ClawMetry Cloud receives data from the OSS sync daemon running on the agent's machine.

```
Agent Machine                          ClawMetry Cloud
+----------------------+               +----------------------+
|                      |    E2E        |                      |
| Session JSONL files  | encrypted     | Cloud SQL (Postgres) |
|   +-- events     ----+--AES-256---->-+---> events table     |
|   +-- sessions   ----+--GCM-------->-+---> sessions table   |
|   +-- memory     ----+-------------->-+---> encrypted blobs  |
|   +-- crons      ----+-------------->-+---> cron_state       |
|   +-- security   ----+-------------->-+---> security_posture |
|                      |               |                      |
| Event Streamer       |    1-2s       | Browser              |
| (watches file sizes, |   latency     | (polls /api/cloud/   |
|  pushes on change)   |               |  brain every 2s,     |
|                      |               |  decrypts client-    |
| Sync daemon          |    15s        |  side with AES key)  |
| (catch-all backup)   |   interval    |                      |
+----------------------+               +----------------------+
```

### Real-Time Event Streamer

The sync daemon includes a dedicated event streamer thread that watches session JSONL files for changes:

1. Checks file sizes every 1 second (just stat() - no API call)
2. If a file grew, reads only the new lines
3. Encrypts and pushes immediately
4. No wasted API calls when idle (like Dropbox sync)

End-to-end latency: **1-3 seconds** from agent action to cloud Brain tab.


## Dashboard Tabs Reference

| Tab | What it shows | Data source |
|-----|---------------|-------------|
| Flow | Architecture diagram with animated message particles, provider stack, skills | Gateway WebSocket + /api/overview |
| Brain | Unified event stream with channel badges, skill badges, per-turn drill-down, sub-agent nesting | /api/brain-history (sessions + logs) |
| Overview | Model, tokens, sessions, spending, active tasks, heartbeat | /api/overview + system snapshot |
| Approvals | Policy rules, integration setup, pending decisions | /api/cloud/policies + /api/cloud/approvals |
| Skills | Skill list with fidelity stats + file browser | /api/skills + /api/skills/<name>/file |
| Context | LLM context window usage, composition breakdown, compaction history | /api/overview + /api/brain-history + /api/skills |
| Tokens | Daily/weekly/monthly token usage, cost breakdown, model attribution | /api/usage |
| Crons | Scheduled job list, run history, health summary | /api/crons + gateway RPC |
| Memory | E2E encrypted file explorer (AES-256-GCM decrypt in browser) | /api/cloud/memory-files |


## API Endpoints for Observability

```
Brain & Timeline
  GET /api/brain-history         Event stream with channel + skill enrichment
  GET /api/brain-stream          SSE for live brain events

Context
  GET /api/overview              Model, tokens, context window, session count
  GET /api/skills                Installed skills with fidelity stats

Channel Sessions  
  GET /api/sessions              Active sessions with channel metadata

Skills
  GET /api/skills                List all with status (healthy/dead/stuck/unused)
  GET /api/skills/<name>         Detail + file tree
  GET /api/skills/<name>/file    File content with language detection
```
