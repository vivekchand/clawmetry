# ClawMetry — OpenClaw Observability Plugin

**ClawMetry** is the observability dashboard for OpenClaw AI agents. It gives you real-time visibility into token usage, API costs, tool calls, session timelines, memory, and cron jobs — all in a local dashboard at `http://localhost:8900`.

Zero configuration required. ClawMetry auto-detects your OpenClaw setup and starts streaming live telemetry the moment it starts.

## Install

### Via ClawHub (recommended)

```bash
openclaw plugins install clawmetry
```

### Via curl

```bash
curl -fsSL https://clawmetry.com/install.sh | bash
```

### Via pip (standalone)

```bash
pip install clawmetry && clawmetry
```

## How it works

When installed as an OpenClaw plugin, ClawMetry:

1. **Subscribes to diagnostic events** — model usage, tool calls, session lifecycle, message flow
2. **Manages the dashboard process** — auto-starts with OpenClaw, auto-stops on shutdown
3. **Buffers and forwards telemetry** — batched HTTP delivery to the local dashboard
4. **Ships a bundled skill** — teaches agents to be cost-aware and reference the dashboard

### Plugin hooks used

| Hook | Purpose |
|---|---|
| `onDiagnosticEvent` | Token usage, costs, session state, heartbeats |
| `registerLogTransport` | Gateway log forwarding to dashboard log viewer |

### Dashboard features

- **Overview** — active sessions, total costs, token usage, system health
- **Sessions** — per-session breakdown with transcript viewer
- **Brain** — live feed of every LLM call (model, tokens, latency)
- **Flow** — animated architecture diagram showing real-time data flow
- **Memory** — workspace memory file viewer
- **Crons** — scheduled job status and history
- **Usage** — per-model cost tracking over time
- **Alerts** — budget alerts and anomaly detection

## Configuration

In your OpenClaw config (`~/.openclaw/openclaw.json`):

```json
{
  "plugins": {
    "allow": ["clawmetry"],
    "entries": {
      "clawmetry": {
        "enabled": true,
        "port": 8900,
        "host": "127.0.0.1",
        "autoStart": true,
        "cloudSync": false,
        "apiKey": "cm-..."
      }
    }
  }
}
```

### Options

| Option | Default | Description |
|---|---|---|
| `port` | `8900` | Dashboard port |
| `host` | `127.0.0.1` | Bind address (`0.0.0.0` for LAN access) |
| `autoStart` | `true` | Start dashboard with OpenClaw |
| `cloudSync` | `false` | Enable encrypted sync to clawmetry.com |
| `apiKey` | — | ClawMetry Cloud API key (optional) |

## Cloud Sync

Optional E2E encrypted sync to [clawmetry.com](https://clawmetry.com) for remote monitoring:

```bash
clawmetry connect
```

Your encryption key never leaves your machine. Data is AES-256-GCM encrypted before transmission.

## Standalone usage

ClawMetry also works without the plugin — as a standalone `pip install`:

```bash
pip install clawmetry
clawmetry
```

In standalone mode, it reads OpenClaw's JSONL session files and logs directly from the filesystem. The plugin mode adds real-time diagnostic event streaming for richer telemetry.

## Links

- **Homepage:** [clawmetry.com](https://clawmetry.com)
- **GitHub:** [github.com/vivekchand/clawmetry](https://github.com/vivekchand/clawmetry)
- **PyPI:** [pypi.org/project/clawmetry](https://pypi.org/project/clawmetry/)
- **ClawHub:** `openclaw plugins install clawmetry`

## License

MIT
