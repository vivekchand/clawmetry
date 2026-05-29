# PagerDuty + OpsGenie alert sinks

ClawMetry's alerting layer (`/api/alerts/*`) fans out to whichever
outbound sinks the operator configures. As of `feat/pd-opsgenie-sinks`
the supported list is:

| Sink | Config key | Notes |
|---|---|---|
| Generic JSON webhook | `webhook_url` | Body = the raw alert dict |
| Slack incoming webhook | `slack_webhook_url` | Attachment with severity color |
| Discord webhook | `discord_webhook_url` | Embed with severity color |
| **PagerDuty Events API v2** | `pagerduty_routing_key` | Fixed endpoint, `event_action: trigger` |
| **OpsGenie createAlert** | `opsgenie_api_key`, `opsgenie_api_url` (optional EU) | `Authorization: GenieKey <key>` header |

**Tier:** Pro (entitlement key `custom_webhooks`).

## Configure

```bash
curl -XPOST http://localhost:8900/api/alert-channels \
  -H 'content-type: application/json' \
  -d '{
    "pagerduty_routing_key": "0123456789abcdef0123456789abcdef",
    "opsgenie_api_key":      "abcd1234-5678-90ab-cdef-1234567890ab"
  }'
```

EU OpsGenie customers also set `opsgenie_api_url` to
`https://api.eu.opsgenie.com/v2/alerts`. The default (`api.opsgenie.com`)
covers US.

## Test fire

```bash
curl -XPOST http://localhost:8900/api/alerts/webhook/test \
  -H 'content-type: application/json' \
  -d '{"target": "pagerduty"}'
# -> {"ok": true, "sent": ["pagerduty"]}

curl -XPOST http://localhost:8900/api/alerts/webhook/test \
  -d '{"target": "opsgenie"}'
# -> {"ok": true, "sent": ["opsgenie"]}

curl -XPOST http://localhost:8900/api/alerts/webhook/test \
  -d '{"target": "all"}'
# -> {"ok": true, "sent": ["generic", "slack", "discord", "pagerduty", "opsgenie"]}
```

## Severity mapping

| ClawMetry severity | PagerDuty | OpsGenie priority |
|---|---|---|
| `info` | `info` | `P5` |
| `warning` (default) | `warning` | `P3` |
| `error` | `error` | `P2` |
| `critical` | `critical` | `P1` |

## Dedup / alias

PagerDuty: `dedup_key = "clawmetry:<agent>:<alert_type>"` so repeated
firings of the same logical incident coalesce into one PD incident.

OpsGenie: `alias = "clawmetry:<agent>:<alert_type>"` for the same reason.

## Payload fields

### PagerDuty
```json
{
  "routing_key":  "...",
  "event_action": "trigger",
  "dedup_key":    "clawmetry:main:cost_spike",
  "payload": {
    "summary":   "Cost crossed $50 in 5 min",
    "severity":  "critical",
    "source":    "clawmetry",
    "component": "main",
    "group":     "clawmetry-alerts",
    "class":     "cost_spike",
    "custom_details": { "cost_usd": 53.12, "threshold": 50, ... }
  }
}
```

### OpsGenie
```json
{
  "message":     "Error rate >20% on scout",
  "alias":       "clawmetry:scout:agent_error_rate",
  "description": "...",
  "priority":    "P2",
  "source":      "clawmetry",
  "tags":        ["clawmetry", "agent_error_rate"],
  "details":     { ... }
}
```

`message` is capped at 130 chars (OpsGenie limit); summary is capped at
1024 (PagerDuty limit).

## Security

- The PD routing key and OpsGenie API key live only in
  `~/.clawmetry/alerts.json` on the box that runs the daemon; they are
  never forwarded to generic / Slack / Discord webhook bodies (tested).
- `_send_webhook_alert` swallows all per-sink errors so a flaky vendor
  cannot break the fan-out to others.
