# ClawMetry Upcoming Features

*Features we're building next. Star the [repo](https://github.com/vivekchand/clawmetry) to stay updated.*

## Coming Soon

### Budget Controls & Spending Alerts
- Set daily, weekly, monthly spending limits
- Alert rules with Telegram/email notifications
- Auto-pause gateway when budget exceeded
- Spending history and trend charts

### Cron Job Management (CRUD)
- Create, edit, delete, enable/disable cron jobs from the dashboard
- Run jobs on demand
- View execution history and logs per job

### Session Explorer
- Click into any session to view full conversation history
- Token usage breakdown per session
- Session timeline with tool calls visualized

### History & Time-Series Analytics
- Historical token usage, cost trends, model mix over time
- SQLite-backed local time-series database
- Export to CSV for external analysis
- Configurable retention periods

### OTLP / OpenTelemetry Integration
- Receive traces and metrics from OpenClaw gateway
- Visualize request lifecycle: message in, model call, tool calls, response out
- Span waterfall view for debugging latency

## Planned

### Multi-Agent Dashboard
- Monitor multiple OpenClaw instances from one dashboard
- Aggregate spending across agents
- Fleet health overview

### Smart Alerts
- Anomaly detection on token usage (sudden spikes)
- Dead cron job detection
- Disk space warnings with auto-cleanup suggestions
- Sub-agent failure rate monitoring

### Cost Optimizer
- Model usage recommendations (e.g., "Switch to Haiku for these cron jobs")
- Token waste detection (repeated tool calls, large context windows)
- Monthly cost projection based on current trends

### Mobile-Friendly UI
- Responsive layout for phone/tablet
- PWA support for home screen install

### Plugin System
- Custom dashboard panels via plugins
- Community-contributed widgets
- Webhook integrations (Slack, Discord, PagerDuty)

### Team Features
- Multi-user access with roles
- Shared dashboards
- Audit log for config changes

## Inspiration
- [Langfuse](https://langfuse.com) - LLM observability (tracing, evals, prompt management)
- [Helicone](https://helicone.ai) - LLM monitoring (cost tracking, caching, rate limiting)
- [Portkey](https://portkey.ai) - AI gateway (routing, fallbacks, guardrails)
- [Langsmith](https://smith.langchain.com) - LangChain tracing and debugging

## Contributing
Feature requests? Open an [issue](https://github.com/vivekchand/clawmetry/issues) or PR!
