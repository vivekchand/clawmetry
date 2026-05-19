# Agent Resources (AR) Framework PRD

Status: Draft for greenlight
Owner: Principal Eng V
Epic: #1708 (Wolfgang burnout), gap G4
Building blocks shipped: #1709 (cognitive_loop), #1710 (forward_progress)

---

## What is it?

**HR for AI agents.** ClawMetry already detects unhealthy agent behavior
(cognitive loops, stuck tools, runaway spend). Today the operator only gets a
static alert. With Agent Resources (AR) the operator composes a rule that fires
a real action: pause the agent, kill the loop, downshift the model, or page
oncall. One sentence: **if signal X crosses threshold Y in window Z, do A**.

Concrete day-one use cases:

| Scenario | Trigger | Action |
|---|---|---|
| Wolfgang burnout (overnight validation loop) | `forward_progress = 0` over 50k tokens | `pause_agent` + notify |
| Prompt injection re-prompt loop | same prompt 3 times in 5 min | `kill_agent` |
| Infinite retry on broken tool | `tool_call_stuck` > 3 min | `redirect_to_human` |
| Bill blowup before standup | `daily_cost > $50` | `switch_model_to_cheaper` |
| Cron stampede | `error_rate > 20% over 10m` | `alert_only` to oncall |

---

## Trigger to action grammar

YAML-first, single grammar. The visual builder writes the same YAML the power
user imports.

```yaml
- name: Stop burnout
  trigger:
    signal: forward_progress
    op: equals
    value: 0
    window: 10m
    sample_min_tokens: 50000
  action:
    type: pause_agent
    cooldown: 15m
    notify: [slack, email]
  enabled: true
```

### Canonical triggers (8)

| Signal | Source | Example op + threshold |
|---|---|---|
| `cognitive_loop` | classifier (#1709) | `equals true` |
| `forward_progress` | metric (#1710) | `equals 0`, `sample_min_tokens: 50000` |
| `tool_call_stuck` | classifier (#1671) | `equals true`, `window: 3m` |
| `daily_cost` | usage aggregator | `greater_than 50` (USD) |
| `token_velocity` | usage aggregator | `greater_than 10000` per minute |
| `repeated_prompt` | brain stream hash | `count_at_least 3` in `window: 5m` |
| `error_rate` | brain stream | `greater_than 0.2` over `window: 10m` |
| `time_in_session` | session metadata | `greater_than 4h` |

### Canonical actions (5)

| Action | What it does | Surface |
|---|---|---|
| `alert_only` | sends notification, no agent change | existing alert channels |
| `pause_agent` | sends `pause` RPC to gateway, agent suspends loop | gateway RPC |
| `kill_agent` | sends `terminate` RPC, session ends | gateway RPC |
| `redirect_to_human` | flips session to approval mode | approvals.py |
| `switch_model_to_cheaper` | proxy rewrites model id to fallback list | proxy.py (port 4100) |

All actions accept `cooldown: <duration>` to prevent flap, `notify: [...]` for
side-channel notification, and `dry_run: true` for staging.

---

## Storage and evaluation

**No new infra.** Rules and history live in the existing DuckDB instance,
evaluator runs as a tick inside the existing alert daemon.

### Schema

```sql
CREATE TABLE agent_resources_rules (
  id            UUID PRIMARY KEY,
  name          TEXT NOT NULL,
  trigger_json  JSON NOT NULL,
  action_json   JSON NOT NULL,
  enabled       BOOLEAN NOT NULL DEFAULT true,
  cooldown_until TIMESTAMP,
  created_at    TIMESTAMP NOT NULL DEFAULT now(),
  updated_at    TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE agent_resources_history (
  id          UUID PRIMARY KEY,
  rule_id     UUID NOT NULL,
  session_id  TEXT,
  fired_at    TIMESTAMP NOT NULL DEFAULT now(),
  signal_value JSON,
  action_outcome TEXT,   /* ok | failed | skipped_cooldown | dry_run */
  notes       TEXT
);
```

### Evaluator

Lives in the same alert daemon loop already polling every 15s. Adds one method
`evaluate_ar_rules()` that:

1. Loads enabled rules from DuckDB (cached 60s).
2. Joins each rule trigger to the relevant signal table (usage rollups, brain
   classifier flags, session metadata).
3. For each match, checks `cooldown_until`. If clear, dispatches action,
   updates `cooldown_until`, writes a row to `agent_resources_history`.

Latency target: rule fires within 30s of trigger condition being true.

---

## UI

**Decision: extend the existing Alerts tab, rename it to "Rules."** Rationale:
Alerts is already gated Pro, already has a list view with enable toggles, and
users have learned where to find "the place I configure thresholds." Adding a
second tab fragments the mental model and forces a second paywall conversation.

### Visual rule builder (default)

Per memory `feedback_simple_ui_for_nontechnical.md`: no YAML editor on the
default path. The user composes a rule via:

1. Dropdown: pick a signal (the 8 canonical triggers, labeled in plain English
   like "Agent stops making progress" not `forward_progress`).
2. Slider or number input: threshold.
3. Dropdown: time window.
4. Dropdown: action (the 5 canonical actions, labeled "Pause the agent" etc.).
5. Multiselect: notification channels.
6. Save.

Power users get a "View YAML" toggle and an "Import YAML" button on the rules
list page. Same grammar, no second source of truth.

### Rules list

| Col | Notes |
|---|---|
| Status dot | green = enabled, gray = disabled, yellow = in cooldown |
| Name | inline editable |
| Trigger summary | "Forward progress = 0 over 50k tokens" |
| Action summary | "Pause agent, notify Slack" |
| Fires (24h) | clickable, opens history slideover |
| Toggle | enable / disable |

---

## Tier strategy

Per memory `project_alerts_pro_feature.md` Alerts is Pro-only. AR extends that
boundary with one carve-out so free users see value immediately.

| Tier | What they get |
|---|---|
| OSS / Free | 1 pre-seeded default rule: **Stop burnout** (`forward_progress = 0` over 50k tokens, action `alert_only`). Read-only. "Upgrade to edit or add rules." |
| Cloud Pro | Unlimited custom rules. All 8 triggers, all 5 actions. YAML import/export. History slideover. |

Pre-seeded rule lands on first launch via a one-shot migration; if the user
deletes it on Pro, it stays deleted.

---

## Acceptance criteria (epic-level)

1. YAML grammar finalized and documented in this PRD (frozen at v1 before code).
2. DuckDB schema created via migration. Read + write path covered by 1 unit
   test per table.
3. Evaluator daemon tick added to existing alert loop. No new process, no new
   port, no new datastore.
4. Visual rule builder ships before the YAML editor. YAML view is read-only at
   launch; import lands in a follow-up PR.
5. 1 free-tier default rule pre-seeded (`Stop burnout`).
6. 3 Pro canned examples available as "Add from template":
   - Daily spend kill switch (`daily_cost > 50` then `switch_model_to_cheaper`)
   - Block prompt injection (`repeated_prompt count_at_least 3 in 5m` then
     `kill_agent`)
   - Pause on stuck tool (`tool_call_stuck` then `redirect_to_human`)
7. End-to-end latency: rule fires within 30s of trigger condition true,
   measured by integration test that injects a synthetic signal.
8. History row written on every fire, surfaced in UI slideover.

---

## Out of scope (explicit)

- ML-based intervention timing (e.g. "predict the loop before it starts").
- Cross-account or cross-workspace rules. AR is workspace-local.
- Live-debugger style "step into agent" actions (separate epic, future).
- Custom signals beyond the 8 canonical triggers. Plugin API is a v2 concern.
- Action chaining or rule dependencies (no "if A then B then C").

---

## Open questions for greenlight

1. Tab name: **Rules** (recommended) vs keep **Alerts** with a sub-nav.
2. Should `pause_agent` and `kill_agent` require a confirmation modal the first
   time a user enables them per workspace? (Recommend yes.)
3. Free tier read-only default rule: do we show the upgrade CTA on the rule
   detail view or only on the "Add rule" button? (Recommend both.)
