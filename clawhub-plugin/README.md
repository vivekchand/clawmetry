# ClawMetry — OpenClaw Observability Plugin

**ClawMetry** is a real-time observability dashboard for OpenClaw AI agents. Install it as a ClawHub plugin to get instant visibility into your agent's token usage, API costs, memory consumption, tool calls, and session timelines — all in a beautiful local dashboard at `http://localhost:8900`. Zero configuration required: ClawMetry auto-detects your OpenClaw setup and starts streaming live data from your `~/.openclaw/` session files the moment it starts.

## Install via ClawHub

```
openclaw plugins install clawmetry
```

## Manual Install

```bash
curl -fsSL https://clawmetry.com/install.sh | bash
```

## Configuration

In your OpenClaw config, you can optionally set:

```json5
{
  "plugins": {
    "entries": {
      "clawmetry": {
        "port": 8900,
        "host": "127.0.0.1",
        "autoStart": true
      }
    }
  }
}
```

## Zero-Config HTTP Interceptor

To auto-track LLM costs without any code changes, add one line to your project:

```python
import clawmetry.interceptor  # patches httpx + requests automatically
```

Or set `CLAWMETRY_INTERCEPT=1` in your environment to activate globally.

## Links

- **Homepage:** https://clawmetry.com
- **GitHub:** https://github.com/vivekchand/clawmetry
- **npm:** (ClawHub registry listing pending)
